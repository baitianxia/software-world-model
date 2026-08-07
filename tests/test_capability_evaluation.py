from __future__ import annotations

from datetime import datetime, timedelta, timezone
from dataclasses import replace
import unittest

from software_world_model.application_services import (
    CapabilityDefinition,
    CapabilityEvaluationService,
    CapabilityRegistry,
    CaseExecutionEvidence,
    CurrentEvaluationQualificationVerifier,
    EvaluationCaseDefinition,
    EvaluationConclusion,
    EvaluationQualificationDependencies,
    EvaluationDefinition,
    EvaluationRunState,
    EvaluationValidityStatus,
    LiveIntegrationPolicy,
    StrategyActivationService,
    StrategyDefinition,
    StrategyKind,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteCapabilityEvaluationRepository,
    SqliteDatabase,
    SqliteStrategyActivationRepository,
)


class SequenceIds:
    def __init__(self) -> None:
        self.value = 1

    def new(self, kind: str) -> StableId:
        result = StableId(f"{kind}_{self.value:032x}")
        self.value += 1
        return result


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 6, 9, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        result = self.value
        self.value += timedelta(microseconds=1)
        return result


class DeterministicConformanceVerifier:
    def __init__(self) -> None:
        self.current = True

    def validate(self, definition, at) -> bool:
        return (
            self.current
            and definition.conformance_result_ref.startswith(
                "CC-ARK-CHAT-NO-TOOLS-001:sha256:"
            )
            and definition.model_ref == "glm-5-2-260617"
            and definition.adapter_version == "openai-chat-completions-no-tools@1"
        )


class CapabilityEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.ids = SequenceIds()
        self.clock = StepClock()
        self.registry = CapabilityRegistry()
        self.capability = CapabilityDefinition(
            capability_id="knowledge.jwt-impact",
            contract_version="1.0.0",
            purpose="Evaluate exact commit impact through formal knowledge",
            input_contract_digest=digest_of({"input": "jwt-impact@1"}),
            output_contract_digest=digest_of({"output": "impact-answer@1"}),
        )
        self.strategy = StrategyDefinition(
            strategy_id="jwt-impact-ark-model",
            strategy_version="1.0.0",
            capability_id=self.capability.capability_id,
            capability_contract_version=self.capability.contract_version,
            kind=StrategyKind.MODEL_PRIMARY,
            implementation_digest=digest_of({"implementation": "jwt-model-strategy@1"}),
            requires_model=True,
        )
        self.registry.register_capability(self.capability)
        self.registry.register_strategy(self.strategy)
        self.repository = SqliteCapabilityEvaluationRepository(
            self.database, id_generator=self.ids
        )
        self.conformance = DeterministicConformanceVerifier()
        self.service = CapabilityEvaluationService(
            self.repository,
            self.registry,
            self.conformance,
            clock=self.clock,
        )
        self.definition = EvaluationDefinition.create(
            evaluation_id="CE-JWT-ARK-001",
            evaluation_version="1.0.0",
            capability_id=self.capability.capability_id,
            capability_contract_version=self.capability.contract_version,
            strategy_id=self.strategy.strategy_id,
            strategy_version=self.strategy.strategy_version,
            design_baseline_ref="SWM-DBM-ITER-001-REV-002",
            implementation_digest=self.strategy.implementation_digest,
            conformance_result_ref="CC-ARK-CHAT-NO-TOOLS-001:sha256:" + "a" * 64,
            provider_configuration_fingerprint=digest_of({"configuration": "ark-test"}),
            model_ref="glm-5-2-260617",
            adapter_version="openai-chat-completions-no-tools@1",
            prompt_program_ref="prompt:jwt-impact@1",
            prompt_program_digest=digest_of({"prompt": "jwt-impact@1"}),
            output_schema_ref="schema:jwt-impact-candidate@1",
            output_schema_digest=digest_of({"schema": "jwt-impact-candidate@1"}),
            tool_policy_ref="platform-source-tools-only@1",
            data_source_revision_ref="mall@0504e86",
            environment_ref="local-validation@1",
            reference_strategy_ref="direct-source-investigation@1",
            resource_policy_ref="jwt-capability-budget@1",
            metric_contract_digest=digest_of({"metrics": "claim-conservation@1"}),
            threshold_ref="all-required-cases-pass@1",
            cases=(
                EvaluationCaseDefinition(
                    case_id="CE-JWT-01",
                    case_version="1.0.0",
                    fixture_ref="fixture:jwt-scope",
                    fixture_digest=digest_of({"fixture": 1}),
                    oracle_ref="oracle:jwt-claims-01",
                    oracle_digest=digest_of({"oracle": 1}),
                ),
                EvaluationCaseDefinition(
                    case_id="CE-JWT-02",
                    case_version="1.0.0",
                    fixture_ref="fixture:jwt-answer",
                    fixture_digest=digest_of({"fixture": 2}),
                    oracle_ref="oracle:jwt-claims-02",
                    oracle_digest=digest_of({"oracle": 2}),
                ),
            ),
            valid_for_seconds=3600,
        )
        self.service.register_definition(self.definition)

    def tearDown(self) -> None:
        self.database.close()

    def prepare_started_run(self, key="evaluation-run"):
        prepared = self.service.prepare_run(
            definition=self.definition,
            evaluation_sink_ref=f"evaluation-sink:{key}",
            root_allocation_ref=f"allocation:{key}",
            idempotency_key=IdempotencyKey(key),
            actor="test-operator",
            correlation_ref=CorrelationRef(key),
        )
        replay = self.service.prepare_run(
            definition=self.definition,
            evaluation_sink_ref=f"evaluation-sink:{key}",
            root_allocation_ref=f"allocation:{key}",
            idempotency_key=IdempotencyKey(key),
            actor="test-operator",
            correlation_ref=CorrelationRef(key),
        )
        self.assertEqual(replay, prepared)
        return self.service.start_run(prepared)

    def evidence(self, case_number: int, conclusion=EvaluationConclusion.PASS):
        case = self.definition.cases[case_number - 1]
        return CaseExecutionEvidence(
            conclusion=conclusion,
            output_ref=f"evaluation-output:{case.case_id}",
            output_digest=digest_of({"output": case.case_id}),
            sink_manifest_ref=f"evaluation-sink-manifest:{case.case_id}",
            sink_manifest_digest=digest_of({"sink": case.case_id}),
            oracle_ref=case.oracle_ref,
            oracle_digest=case.oracle_digest,
            actual_model_fingerprint=self.definition.model_ref,
            provider_request_id=f"provider-{case.case_id}",
            input_tokens=10,
            output_tokens=5,
            usage_complete=True,
        )

    def complete_cases(self, run, conclusions=(EvaluationConclusion.PASS, EvaluationConclusion.PASS)):
        for number, conclusion in enumerate(conclusions, start=1):
            run, attempt = self.service.dispatch_case(
                run=run,
                case_id=f"CE-JWT-0{number}",
                attempt_key=f"attempt-{run.run_id.value}-{number}",
                request_digest=digest_of({"case": number}),
            )
            self.service.complete_case(attempt, self.evidence(number, conclusion))
        return run

    def test_pass_result_issues_current_proof_and_allows_explicit_model_activation(self) -> None:
        run = self.complete_cases(self.prepare_started_run())
        completion = self.service.finalize_run(
            run, actor="evaluation-authority", reason="all required gates passed"
        )

        self.assertEqual(completion.run.state, EvaluationRunState.COMPLETED)
        self.assertEqual(completion.result.conclusion, EvaluationConclusion.PASS)
        self.assertEqual(completion.result.input_tokens, 20)
        self.assertEqual(completion.result.output_tokens, 10)
        self.assertIsNotNone(completion.qualification)
        verifier = CurrentEvaluationQualificationVerifier(
            self.repository,
            EvaluationQualificationDependencies.from_definition(self.definition),
            clock=lambda: self.clock.value,
        )
        self.assertTrue(verifier.validate(completion.qualification))
        expected_dependencies = EvaluationQualificationDependencies.from_definition(
            self.definition
        )
        changed_dependencies = (
            replace(
                expected_dependencies,
                strategy_implementation_digest=digest_of(
                    {"implementation": "changed-after-evaluation"}
                ),
            ),
            replace(
                expected_dependencies,
                conformance_result_ref="conformance:another-result",
            ),
            replace(
                expected_dependencies,
                provider_configuration_fingerprint=digest_of(
                    {"configuration": "changed"}
                ),
            ),
            replace(expected_dependencies, model_ref="another-model@1"),
            replace(expected_dependencies, adapter_version="another-adapter@1"),
        )
        for dependencies in changed_dependencies:
            with self.subTest(dependencies=dependencies):
                verifier_for_changed_runtime = (
                    CurrentEvaluationQualificationVerifier(
                        self.repository,
                        dependencies,
                        clock=lambda: self.clock.value,
                    )
                )
                self.assertFalse(
                    verifier_for_changed_runtime.validate(completion.qualification)
                )

        activation_repository = SqliteStrategyActivationRepository(
            self.database, id_generator=self.ids
        )
        activation = StrategyActivationService(
            activation_repository,
            self.registry,
            verifier,
            live_policy=LiveIntegrationPolicy(model_strategy_activation_enabled=True),
            clock=self.clock,
        )
        decision = activation.activate_strategy(
            capability_id=self.capability.capability_id,
            capability_contract_version=self.capability.contract_version,
            activation_scope={"environment": "acceptance"},
            expected_revision=None,
            strategy_id=self.strategy.strategy_id,
            strategy_version=self.strategy.strategy_version,
            qualification=completion.qualification,
            idempotency_key=IdempotencyKey("activate-evaluated-model"),
            actor="test-operator",
            reason="accepted CE evidence",
            correlation_ref=CorrelationRef("activation-after-ce"),
        )
        self.assertEqual(decision.activation_revision, Revision(1))

    def test_fail_and_inconclusive_results_never_issue_activation_proof(self) -> None:
        for index, conclusion in enumerate(
            (EvaluationConclusion.FAIL, EvaluationConclusion.INCONCLUSIVE), start=1
        ):
            run = self.complete_cases(
                self.prepare_started_run(f"non-pass-{index}"),
                (EvaluationConclusion.PASS, conclusion),
            )
            completion = self.service.finalize_run(
                run, actor="evaluation-authority", reason="non-pass evidence"
            )
            self.assertEqual(completion.result.conclusion, conclusion)
            self.assertIsNone(completion.qualification)

    def test_unknown_outcome_blocks_result_until_same_attempt_is_resolved(self) -> None:
        run = self.prepare_started_run("unknown-run")
        run, attempt = self.service.dispatch_case(
            run=run,
            case_id="CE-JWT-01",
            attempt_key="unknown-attempt",
            request_digest=digest_of({"case": "unknown"}),
        )
        unknown = self.service.mark_case_outcome_unknown(attempt, "provider-unknown")
        pending_run = self.service.get_run(run.run_id)
        self.assertEqual(pending_run.state, EvaluationRunState.OUTCOME_PENDING)
        with self.assertRaises(DomainError) as pending:
            self.service.finalize_run(
                pending_run, actor="evaluation-authority", reason="must remain pending"
            )
        self.assertEqual(pending.exception.code, ErrorCode.EVALUATION_OUTCOME_PENDING)

        self.service.complete_case(unknown, self.evidence(1))
        restored = self.service.get_run(run.run_id)
        self.assertEqual(restored.state, EvaluationRunState.RUNNING)

    def test_validity_is_monotonic_and_stale_result_fails_closed(self) -> None:
        run = self.complete_cases(self.prepare_started_run("stale-run"))
        completion = self.service.finalize_run(
            run, actor="evaluation-authority", reason="initial pass"
        )
        proof = completion.qualification
        verifier = CurrentEvaluationQualificationVerifier(
            self.repository,
            EvaluationQualificationDependencies.from_definition(self.definition),
            clock=lambda: self.clock.value,
        )
        self.assertTrue(verifier.validate(proof))

        stale = self.service.invalidate_result(
            result_id=completion.result.result_id,
            expected_validity_revision=Revision(1),
            status=EvaluationValidityStatus.STALE,
            authority="evaluation-authority",
            reason="adapter implementation changed",
        )
        self.assertEqual(stale.revision, Revision(2))
        self.assertFalse(verifier.validate(proof))
        with self.assertRaises(DomainError) as restore:
            self.service.invalidate_result(
                result_id=completion.result.result_id,
                expected_validity_revision=Revision(2),
                status=EvaluationValidityStatus.VALID,
                authority="evaluation-authority",
                reason="invalid restoration",
            )
        self.assertEqual(restore.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_definition_must_match_registered_strategy_implementation(self) -> None:
        mismatched = EvaluationDefinition.create(
            evaluation_id="CE-JWT-ARK-MISMATCH",
            evaluation_version="1.0.0",
            capability_id=self.definition.capability_id,
            capability_contract_version=self.definition.capability_contract_version,
            strategy_id=self.definition.strategy_id,
            strategy_version=self.definition.strategy_version,
            design_baseline_ref=self.definition.design_baseline_ref,
            implementation_digest=digest_of({"implementation": "other"}),
            conformance_result_ref=self.definition.conformance_result_ref,
            provider_configuration_fingerprint=self.definition.provider_configuration_fingerprint,
            model_ref=self.definition.model_ref,
            adapter_version=self.definition.adapter_version,
            prompt_program_ref=self.definition.prompt_program_ref,
            prompt_program_digest=self.definition.prompt_program_digest,
            output_schema_ref=self.definition.output_schema_ref,
            output_schema_digest=self.definition.output_schema_digest,
            tool_policy_ref=self.definition.tool_policy_ref,
            data_source_revision_ref=self.definition.data_source_revision_ref,
            environment_ref=self.definition.environment_ref,
            reference_strategy_ref=self.definition.reference_strategy_ref,
            resource_policy_ref=self.definition.resource_policy_ref,
            metric_contract_digest=self.definition.metric_contract_digest,
            threshold_ref=self.definition.threshold_ref,
            cases=self.definition.cases,
            valid_for_seconds=3600,
        )
        with self.assertRaises(DomainError) as raised:
            self.service.register_definition(mismatched)
        self.assertEqual(raised.exception.code, ErrorCode.STRATEGY_CONTRACT_MISMATCH)

    def test_conformance_is_revalidated_before_result_is_sealed(self) -> None:
        run = self.complete_cases(self.prepare_started_run("stale-conformance"))
        self.conformance.current = False
        with self.assertRaises(DomainError) as raised:
            self.service.finalize_run(
                run, actor="evaluation-authority", reason="must not seal"
            )
        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)
        self.assertEqual(self.service.get_run(run.run_id).state, EvaluationRunState.RUNNING)


if __name__ == "__main__":
    unittest.main()
