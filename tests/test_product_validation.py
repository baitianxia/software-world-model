from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import replace
import json
import unittest

from software_world_model.ai_infrastructure import (
    agentic_knowledge_strategy_implementation_digest,
)
from software_world_model.application_services import (
    LiveIntegrationPolicy,
    NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
    NATURAL_TASK_CAPABILITY_ID,
    ProductValidatedQualificationVerifier,
    ProductHoldoutCaseComparison,
    ProductValidationService,
    QualificationProof,
    StrategyActivationService,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteProductValidationRepository,
    SqliteStrategyActivationRepository,
)
from software_world_model.interface.agentic_runtime import (
    agentic_task_capability_registry,
    agentic_task_strategy_definition,
)


class MutableClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 7, 4, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value


class ExactEvaluationVerifier:
    def __init__(self, proof: QualificationProof) -> None:
        self.proof = proof
        self.current = True

    def validate(self, proof: QualificationProof) -> bool:
        return self.current and proof == self.proof and proof.verify_digest()


def qualification() -> QualificationProof:
    strategy = agentic_task_strategy_definition()
    core = {
        "proof_ref": "capability-evaluation:general-task:1",
        "capability_id": NATURAL_TASK_CAPABILITY_ID,
        "capability_contract_version": NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
        "strategy_id": strategy.strategy_id,
        "strategy_version": strategy.strategy_version,
        "result_ref": "evaluation-result:general-task:1",
        "validity_ref": "evaluation-validity:general-task:1@1",
        "qualification_kind": "CAPABILITY_EVALUATION",
    }
    return QualificationProof(**core, digest=digest_of(core))


class ProductValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.clock = MutableClock()
        self.proof = qualification()
        self.implementation_digest = (
            agentic_knowledge_strategy_implementation_digest()
        )
        self.repository = SqliteProductValidationRepository(self.database)
        self.service = ProductValidationService(
            self.repository,
            clock=self.clock,
        )
        self.evaluation = ExactEvaluationVerifier(self.proof)
        self.verifier = ProductValidatedQualificationVerifier(
            self.evaluation,
            self.repository,
            self.implementation_digest,
            clock=self.clock,
        )

    def tearDown(self) -> None:
        self.database.close()

    def record(self, **overrides):
        values = {
            "idempotency_key": IdempotencyKey("product-validation:1"),
            "qualification": self.proof,
            "strategy_implementation_digest": self.implementation_digest,
            "holdout_suite_ref": "holdout:new-projects:2026-08-07",
            "holdout_suite_digest": digest_of({"holdout": "new-projects"}),
            "case_ids": ("holdout-1", "holdout-2"),
            "direct_result_digest": digest_of({"direct": "answers"}),
            "world_result_digest": digest_of({"world": "answers"}),
            "comparison_digest": digest_of({"comparison": "independent"}),
            "direct_origin": "codex-direct-answer",
            "world_origin": "volcengine-world-assisted-answer",
            "evaluator_origin": "codex-independent-review",
            "direct_correctness_milli": 800,
            "world_correctness_milli": 850,
            "direct_completion_milli": 750,
            "world_completion_milli": 900,
            "material_error_count": 0,
            "valid_for_seconds": 3600,
        }
        values.update(overrides)
        return self.service.record_pass(**values)

    def comparison(self, case_id: str, **overrides):
        values = {
            "comparison_ref": f"comparison:{case_id}",
            "case_id": case_id,
            "direct_output_ref": f"direct:{case_id}",
            "direct_output_digest": digest_of({"direct": case_id}),
            "world_output_ref": f"world:{case_id}",
            "world_output_digest": digest_of({"world": case_id}),
            "direct_origin": "codex-direct-answer",
            "world_origin": "volcengine-world-assisted-answer",
            "evaluator_origin": "codex-independent-review",
            "direct_model_fingerprint": "glm-5.2",
            "world_model_fingerprint": "glm-5.2",
            "direct_correctness_milli": 800,
            "world_correctness_milli": 850,
            "direct_completion_milli": 750,
            "world_completion_milli": 900,
            "material_error_count": 0,
            "findings": (),
        }
        values.update(overrides)
        return ProductHoldoutCaseComparison.create(**values)

    def test_current_independent_pass_is_replayed_and_accepted(self) -> None:
        recorded = self.record()
        self.clock.value += timedelta(seconds=10)
        replayed = self.record()

        self.assertEqual(replayed, recorded)
        self.assertTrue(recorded.verify_digest())
        self.assertTrue(self.verifier.validate(self.proof))

    def test_evaluator_must_be_independent_from_both_answer_origins(self) -> None:
        for evaluator in (
            "codex-direct-answer",
            "volcengine-world-assisted-answer",
        ):
            with self.subTest(evaluator=evaluator), self.assertRaises(
                DomainError
            ) as raised:
                self.record(evaluator_origin=evaluator)
            self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_world_assisted_result_must_not_regress_from_direct_result(self) -> None:
        with self.assertRaises(DomainError) as raised:
            self.record(world_correctness_milli=799)

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_expiry_or_capability_evaluation_invalidation_closes_gate(self) -> None:
        self.record(valid_for_seconds=10)
        self.assertTrue(self.verifier.validate(self.proof))

        self.clock.value += timedelta(seconds=10)
        self.assertFalse(self.verifier.validate(self.proof))
        self.clock.value -= timedelta(seconds=1)
        self.evaluation.current = False
        self.assertFalse(self.verifier.validate(self.proof))

    def test_idempotency_key_rejects_changed_evidence(self) -> None:
        self.record()

        with self.assertRaises(DomainError) as raised:
            self.record(world_result_digest=digest_of({"world": "changed"}))

        self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

    def test_tampered_authority_record_fails_closed(self) -> None:
        recorded = self.record()
        with self.database.transaction() as connection:
            payload = json.loads(
                connection.execute(
                    """SELECT payload_json
                       FROM app_product_validation_attestations
                       WHERE attestation_id = ?""",
                    (recorded.attestation_id.value,),
                ).fetchone()["payload_json"]
            )
            payload["world_correctness_milli"] = 1000
            connection.execute(
                """UPDATE app_product_validation_attestations
                   SET payload_json = ? WHERE attestation_id = ?""",
                (json.dumps(payload), recorded.attestation_id.value),
            )

        self.assertFalse(self.verifier.validate(self.proof))

    def test_activation_requires_both_evaluation_and_product_pass(self) -> None:
        activation = StrategyActivationService(
            SqliteStrategyActivationRepository(self.database),
            agentic_task_capability_registry(),
            self.verifier,
            live_policy=LiveIntegrationPolicy(
                model_strategy_activation_enabled=True
            ),
            clock=self.clock,
        )
        strategy = agentic_task_strategy_definition()
        arguments = {
            "capability_id": NATURAL_TASK_CAPABILITY_ID,
            "capability_contract_version": NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
            "activation_scope": {"environment": "acceptance"},
            "expected_revision": None,
            "strategy_id": strategy.strategy_id,
            "strategy_version": strategy.strategy_version,
            "qualification": self.proof,
            "idempotency_key": IdempotencyKey("activate:product-validated"),
            "actor": "acceptance-owner",
            "reason": "both validations passed",
            "correlation_ref": CorrelationRef("product-validation-activation"),
        }
        with self.assertRaises(DomainError) as raised:
            activation.activate_strategy(**arguments)
        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

        self.record()
        decision = activation.activate_strategy(**arguments)
        resolved = activation.resolve_strategy(
            capability_id=NATURAL_TASK_CAPABILITY_ID,
            capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
            activation_scope={"environment": "acceptance"},
        )
        self.assertEqual(resolved.decision, decision)

    def test_reviewed_holdout_aggregates_only_after_every_case_passes(self) -> None:
        recorded = self.service.record_reviewed_holdout(
            idempotency_key=IdempotencyKey("product-reviewed-holdout:1"),
            qualification=self.proof,
            strategy_implementation_digest=self.implementation_digest,
            holdout_suite_ref="holdout:new-projects:reviewed",
            holdout_suite_digest=digest_of({"suite": "reviewed"}),
            comparisons=(
                self.comparison("holdout-1"),
                self.comparison(
                    "holdout-2",
                    direct_correctness_milli=700,
                    world_correctness_milli=800,
                ),
            ),
            valid_for_seconds=3600,
        )

        self.assertEqual(recorded.case_ids, ("holdout-1", "holdout-2"))
        self.assertEqual(recorded.direct_correctness_milli, 750)
        self.assertEqual(recorded.world_correctness_milli, 825)
        self.assertTrue(self.verifier.validate(self.proof))

    def test_one_regressing_holdout_case_cannot_be_hidden_by_average(self) -> None:
        comparisons = (
            self.comparison(
                "holdout-1",
                direct_correctness_milli=200,
                world_correctness_milli=1000,
            ),
            self.comparison(
                "holdout-2",
                direct_correctness_milli=900,
                world_correctness_milli=899,
                findings=("world answer missed one required condition",),
            ),
        )

        with self.assertRaises(DomainError) as raised:
            self.service.record_reviewed_holdout(
                idempotency_key=IdempotencyKey("product-reviewed-holdout:regression"),
                qualification=self.proof,
                strategy_implementation_digest=self.implementation_digest,
                holdout_suite_ref="holdout:new-projects:regression",
                holdout_suite_digest=digest_of({"suite": "regression"}),
                comparisons=comparisons,
                valid_for_seconds=3600,
            )

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_reviewed_holdout_rejects_mixed_or_tampered_attestations(self) -> None:
        first = self.comparison("holdout-1")
        mixed = self.comparison(
            "holdout-2",
            evaluator_origin="another-independent-reviewer",
        )
        with self.assertRaises(DomainError) as raised:
            self.service.record_reviewed_holdout(
                idempotency_key=IdempotencyKey("product-reviewed-holdout:mixed"),
                qualification=self.proof,
                strategy_implementation_digest=self.implementation_digest,
                holdout_suite_ref="holdout:new-projects:mixed",
                holdout_suite_digest=digest_of({"suite": "mixed"}),
                comparisons=(first, mixed),
                valid_for_seconds=3600,
            )
        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

        with self.assertRaises(DomainError) as raised:
            self.service.record_reviewed_holdout(
                idempotency_key=IdempotencyKey("product-reviewed-holdout:tampered"),
                qualification=self.proof,
                strategy_implementation_digest=self.implementation_digest,
                holdout_suite_ref="holdout:new-projects:tampered",
                holdout_suite_digest=digest_of({"suite": "tampered"}),
                comparisons=(replace(first, world_correctness_milli=1000),),
                valid_for_seconds=3600,
            )
        self.assertEqual(
            raised.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )

    def test_product_baseline_requires_the_same_model_on_both_paths(self) -> None:
        with self.assertRaises(DomainError) as raised:
            self.comparison(
                "holdout-model-mismatch",
                world_model_fingerprint="another-model",
            )

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)


if __name__ == "__main__":
    unittest.main()
