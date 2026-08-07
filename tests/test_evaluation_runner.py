from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from software_world_model.ai_infrastructure import (
    agentic_knowledge_strategy_implementation_digest,
)
from software_world_model.application_services import (
    CapabilityEvaluationRunner,
    CapabilityEvaluationService,
    CaseExecutionEvidence,
    EvaluationCaseDefinition,
    EvaluationCaseExecutionFailed,
    EvaluationCaseOutcomeUnknown,
    EvaluationConclusion,
    EvaluationDefinition,
    EvaluationRunState,
    NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
    NATURAL_TASK_CAPABILITY_ID,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    IdempotencyKey,
    DomainError,
    ErrorCode,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteCapabilityEvaluationRepository,
    SqliteDatabase,
)
from software_world_model.interface.agentic_runtime import (
    agentic_task_capability_registry,
    agentic_task_strategy_definition,
)


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 7, 5, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        result = self.value
        self.value += timedelta(microseconds=1)
        return result


class CurrentConformance:
    def validate(self, definition, at) -> bool:
        return (
            at.tzinfo is not None
            and definition.conformance_result_ref == "conformance:current"
        )


class ScriptedExecutor:
    def __init__(self, outcomes) -> None:
        self.outcomes = list(outcomes)
        self.calls = []

    def execute(self, request):
        self.calls.append(request.case.case_id)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return evidence(request.case, outcome)


def evidence(case, conclusion=EvaluationConclusion.PASS):
    return CaseExecutionEvidence(
        conclusion=conclusion,
        output_ref=f"sink-output:{case.case_id}",
        output_digest=digest_of({"output": case.case_id, "result": conclusion.value}),
        sink_manifest_ref=f"sink-manifest:{case.case_id}",
        sink_manifest_digest=digest_of({"manifest": case.case_id}),
        oracle_ref=case.oracle_ref,
        oracle_digest=case.oracle_digest,
        actual_model_fingerprint="fixture-model@1",
        provider_request_id=f"provider:{case.case_id}",
        input_tokens=10,
        output_tokens=5,
        usage_complete=True,
    )


class CapabilityEvaluationRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.clock = StepClock()
        self.repository = SqliteCapabilityEvaluationRepository(self.database)
        self.service = CapabilityEvaluationService(
            self.repository,
            agentic_task_capability_registry(),
            CurrentConformance(),
            clock=self.clock,
        )
        self.runner = CapabilityEvaluationRunner(self.service)
        strategy = agentic_task_strategy_definition()
        cases = tuple(
            EvaluationCaseDefinition(
                case_id=f"general-task-{number}",
                case_version="1.0.0",
                fixture_ref=f"fixture:general-task:{number}",
                fixture_digest=digest_of({"fixture": number}),
                oracle_ref=f"oracle:general-task:{number}",
                oracle_digest=digest_of({"oracle": number}),
            )
            for number in (1, 2)
        )
        self.definition = EvaluationDefinition.create(
            evaluation_id="general-software-task",
            evaluation_version="1.0.0",
            capability_id=NATURAL_TASK_CAPABILITY_ID,
            capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
            strategy_id=strategy.strategy_id,
            strategy_version=strategy.strategy_version,
            design_baseline_ref="design:iteration-001",
            implementation_digest=agentic_knowledge_strategy_implementation_digest(),
            conformance_result_ref="conformance:current",
            provider_configuration_fingerprint=Digest("sha256:" + "1" * 64),
            model_ref="fixture-model@1",
            adapter_version="fixture-no-tools@1",
            prompt_program_ref="agentic-six-role-prompts@1",
            prompt_program_digest=digest_of({"prompts": "all"}),
            output_schema_ref="agentic-eight-closed-schemas@1",
            output_schema_digest=digest_of({"schemas": "all"}),
            tool_policy_ref="no-model-tools-platform-actions-only@1",
            data_source_revision_ref="fixtures:frozen@1",
            environment_ref="isolated-evaluation@1",
            reference_strategy_ref="sealed-independent-oracles@1",
            resource_policy_ref="general-task-evaluation-budget@1",
            metric_contract_digest=digest_of({"required": "all-pass"}),
            threshold_ref="all-required-cases-pass@1",
            cases=cases,
            valid_for_seconds=3600,
        )

    def tearDown(self) -> None:
        self.database.close()

    def run_suite(self, executor):
        return self.runner.run_suite(
            definition=self.definition,
            evaluation_sink_ref="sqlite:evaluation-sink",
            root_allocation_ref="allocation:general-evaluation",
            idempotency_key=IdempotencyKey("general-evaluation-run"),
            executor=executor,
            actor="evaluation-owner",
            correlation_ref=CorrelationRef("general-evaluation"),
            completion_reason="all frozen general cases executed",
        )

    def test_pass_suite_recovers_without_executing_cases_again(self) -> None:
        executor = ScriptedExecutor(
            [EvaluationConclusion.PASS, EvaluationConclusion.PASS]
        )
        first = self.run_suite(executor)
        replay = self.run_suite(executor)

        self.assertEqual(first.run.state, EvaluationRunState.COMPLETED)
        self.assertIsNotNone(first.completion)
        self.assertIsNotNone(first.completion.qualification)
        self.assertEqual(executor.calls, ["general-task-1", "general-task-2"])
        self.assertEqual(replay.completion.result.digest, first.completion.result.digest)
        self.assertEqual(len(replay.attempts), 2)

    def test_semantic_case_failure_seals_fail_without_qualification(self) -> None:
        executor = ScriptedExecutor(
            [EvaluationConclusion.PASS, EvaluationConclusion.FAIL]
        )
        result = self.run_suite(executor)

        self.assertEqual(result.run.state, EvaluationRunState.COMPLETED)
        self.assertEqual(
            result.completion.result.conclusion,
            EvaluationConclusion.FAIL,
        )
        self.assertIsNone(result.completion.qualification)

    def test_unknown_outcome_is_not_redispatched_and_can_be_resolved(self) -> None:
        executor = ScriptedExecutor(
            [EvaluationCaseOutcomeUnknown("provider:unknown")]
        )
        pending = self.run_suite(executor)
        replay = self.run_suite(executor)

        self.assertEqual(pending.run.state, EvaluationRunState.OUTCOME_PENDING)
        self.assertEqual(replay.run.state, EvaluationRunState.OUTCOME_PENDING)
        self.assertEqual(executor.calls, ["general-task-1"])

        self.service.complete_case(
            replay.attempts[0], evidence(self.definition.cases[0])
        )
        executor.outcomes.append(EvaluationConclusion.PASS)
        completed = self.run_suite(executor)
        self.assertEqual(completed.run.state, EvaluationRunState.COMPLETED)
        self.assertEqual(
            executor.calls,
            ["general-task-1", "general-task-2"],
        )

    def test_definitive_infrastructure_failure_stops_without_hidden_retry(self) -> None:
        executor = ScriptedExecutor(
            [EvaluationCaseExecutionFailed("EVALUATION_SINK_WRITE_FAILED")]
        )
        failed = self.run_suite(executor)
        replay = self.run_suite(executor)

        self.assertEqual(failed.run.state, EvaluationRunState.FAILED)
        self.assertEqual(replay.run.state, EvaluationRunState.FAILED)
        self.assertIsNone(failed.completion)
        self.assertEqual(executor.calls, ["general-task-1"])

    def test_domain_contract_failure_is_definitive_and_not_redispatched(self) -> None:
        executor = ScriptedExecutor(
            [DomainError(ErrorCode.ORACLE_UNAVAILABLE, "oracle digest mismatch")]
        )
        failed = self.run_suite(executor)
        replay = self.run_suite(executor)

        self.assertEqual(failed.run.state, EvaluationRunState.FAILED)
        self.assertEqual(replay.attempts[0].failure_code, "DOMAIN_ORACLE_UNAVAILABLE")
        self.assertEqual(executor.calls, ["general-task-1"])


if __name__ == "__main__":
    unittest.main()
