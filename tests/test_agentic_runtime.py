from __future__ import annotations

import unittest

from software_world_model.ai_infrastructure import (
    AgenticModelStrategyConfiguration,
    agentic_knowledge_strategy_implementation_digest,
    evidence_first_task_strategy_implementation_digest,
)
from software_world_model.application_services import (
    EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION,
    EVIDENCE_ANSWER_CAPABILITY_ID,
    LiveIntegrationPolicy,
    NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
    NATURAL_TASK_CAPABILITY_ID,
    QualificationProof,
    StrategyActivationService,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteStrategyActivationRepository,
)
from software_world_model.interface.agentic_runtime import (
    agentic_task_capability_registry,
    agentic_task_strategy_definition,
    assemble_activated_evidence_services,
    assemble_activated_task_services,
    evidence_task_capability_registry,
    evidence_task_strategy_definition,
)


class AcceptCurrentEvaluation:
    def validate(self, proof: QualificationProof) -> bool:
        return proof.qualification_kind == "CAPABILITY_EVALUATION"


class NeverInvokedGateway:
    def invoke(self, context):
        raise AssertionError(f"unexpected model call: {context.execution_envelope_ref}")


def qualification() -> QualificationProof:
    strategy = agentic_task_strategy_definition()
    core = {
        "proof_ref": "evaluation-proof:agentic-task:1",
        "capability_id": NATURAL_TASK_CAPABILITY_ID,
        "capability_contract_version": NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
        "strategy_id": strategy.strategy_id,
        "strategy_version": strategy.strategy_version,
        "result_ref": "evaluation-result:agentic-task:1",
        "validity_ref": "evaluation-validity:agentic-task:1",
        "qualification_kind": "CAPABILITY_EVALUATION",
    }
    return QualificationProof(**core, digest=digest_of(core))


class AgenticRuntimeCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.registry = agentic_task_capability_registry()
        self.activation_scope = {"environment": "test"}
        self.activation = StrategyActivationService(
            SqliteStrategyActivationRepository(self.database),
            self.registry,
            AcceptCurrentEvaluation(),
            live_policy=LiveIntegrationPolicy(model_strategy_activation_enabled=True),
        )
        strategy = agentic_task_strategy_definition()
        self.proof = qualification()
        self.activation.activate_strategy(
            capability_id=NATURAL_TASK_CAPABILITY_ID,
            capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
            activation_scope=self.activation_scope,
            expected_revision=None,
            strategy_id=strategy.strategy_id,
            strategy_version=strategy.strategy_version,
            qualification=self.proof,
            idempotency_key=IdempotencyKey("activate:agentic-runtime"),
            actor="test",
            reason="composition test",
            correlation_ref=CorrelationRef("agentic-runtime-test"),
        )

    def tearDown(self) -> None:
        self.database.close()

    def configuration(self, *, qualification_ref: str | None = None):
        return AgenticModelStrategyConfiguration(
            provider_type="TEST_NO_TOOLS",
            adapter_version="1",
            model_ref="fixture@1",
            provider_configuration_fingerprint=Digest("sha256:" + "0" * 64),
            qualification_ref=qualification_ref or self.proof.proof_ref,
            classification="INTERNAL",
        )

    def test_registry_uses_the_exact_six_role_implementation_digest(self) -> None:
        strategy = self.registry.resolve_strategy(
            agentic_task_strategy_definition().strategy_id,
            agentic_task_strategy_definition().strategy_version,
        )

        self.assertEqual(
            strategy.implementation_digest,
            agentic_knowledge_strategy_implementation_digest(),
        )
        self.assertTrue(strategy.requires_model)

    def test_assembly_binds_every_service_to_one_active_proof(self) -> None:
        assembly = assemble_activated_task_services(
            database=self.database,
            gateway=NeverInvokedGateway(),
            model_configuration=self.configuration(),
            activation=self.activation,
            activation_scope=self.activation_scope,
        )

        self.assertEqual(
            assembly.strategy.implementation_digest,
            assembly.knowledge_updates.strategy_implementation_digest,
        )
        self.assertEqual(
            assembly.knowledge_use.strategy_qualification_ref,
            self.proof.proof_ref,
        )
        self.assertEqual(
            assembly.response_control.strategy_classification,
            "INTERNAL",
        )

    def test_assembly_rejects_components_bound_to_another_evaluation(self) -> None:
        with self.assertRaises(DomainError) as raised:
            assemble_activated_task_services(
                database=self.database,
                gateway=NeverInvokedGateway(),
                model_configuration=self.configuration(
                    qualification_ref="evaluation-proof:other"
                ),
                activation=self.activation,
                activation_scope=self.activation_scope,
            )

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)


class EvidenceRuntimeCompositionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.registry = evidence_task_capability_registry()
        self.activation_scope = {"environment": "evidence-test"}
        self.activation = StrategyActivationService(
            SqliteStrategyActivationRepository(self.database),
            self.registry,
            AcceptCurrentEvaluation(),
            live_policy=LiveIntegrationPolicy(model_strategy_activation_enabled=True),
        )
        strategy = evidence_task_strategy_definition()
        core = {
            "proof_ref": "evaluation-proof:evidence-task:1",
            "capability_id": EVIDENCE_ANSWER_CAPABILITY_ID,
            "capability_contract_version": (
                EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION
            ),
            "strategy_id": strategy.strategy_id,
            "strategy_version": strategy.strategy_version,
            "result_ref": "evaluation-result:evidence-task:1",
            "validity_ref": "evaluation-validity:evidence-task:1",
            "qualification_kind": "CAPABILITY_EVALUATION",
        }
        self.proof = QualificationProof(**core, digest=digest_of(core))
        self.activation.activate_strategy(
            capability_id=EVIDENCE_ANSWER_CAPABILITY_ID,
            capability_contract_version=(
                EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION
            ),
            activation_scope=self.activation_scope,
            expected_revision=None,
            strategy_id=strategy.strategy_id,
            strategy_version=strategy.strategy_version,
            qualification=self.proof,
            idempotency_key=IdempotencyKey("activate:evidence-runtime"),
            actor="test",
            reason="composition test",
            correlation_ref=CorrelationRef("evidence-runtime-test"),
        )

    def tearDown(self) -> None:
        self.database.close()

    def configuration(self, qualification_ref=None):
        return AgenticModelStrategyConfiguration(
            provider_type="TEST_NO_TOOLS",
            adapter_version="1",
            model_ref="fixture@1",
            provider_configuration_fingerprint=Digest("sha256:" + "2" * 64),
            qualification_ref=qualification_ref or self.proof.proof_ref,
            classification="INTERNAL",
        )

    def test_registry_binds_only_the_evidence_first_strategy(self) -> None:
        strategy = self.registry.resolve_strategy(
            evidence_task_strategy_definition().strategy_id,
            evidence_task_strategy_definition().strategy_version,
        )

        self.assertEqual(
            strategy.implementation_digest,
            evidence_first_task_strategy_implementation_digest(),
        )

    def test_evidence_assembly_rechecks_activation_on_each_use(self) -> None:
        assembly = assemble_activated_evidence_services(
            database=self.database,
            gateway=NeverInvokedGateway(),
            model_configuration=self.configuration(),
            activation=self.activation,
            activation_scope=self.activation_scope,
        )

        self.assertTrue(assembly.evidence_answering.is_currently_active())
        current = self.activation.resolve_strategy(
            capability_id=EVIDENCE_ANSWER_CAPABILITY_ID,
            capability_contract_version=EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION,
            activation_scope=self.activation_scope,
        )
        self.activation.deactivate_strategy(
            capability_id=EVIDENCE_ANSWER_CAPABILITY_ID,
            capability_contract_version=EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION,
            activation_scope=self.activation_scope,
            expected_revision=current.decision.activation_revision,
            idempotency_key=IdempotencyKey("deactivate:evidence-runtime"),
            actor="test",
            reason="verify runtime fence",
            correlation_ref=CorrelationRef("evidence-runtime-test"),
        )
        self.assertFalse(assembly.evidence_answering.is_currently_active())

    def test_evidence_assembly_rejects_another_qualification(self) -> None:
        with self.assertRaises(DomainError) as raised:
            assemble_activated_evidence_services(
                database=self.database,
                gateway=NeverInvokedGateway(),
                model_configuration=self.configuration("evaluation-proof:other"),
                activation=self.activation,
                activation_scope=self.activation_scope,
            )

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)


if __name__ == "__main__":
    unittest.main()
