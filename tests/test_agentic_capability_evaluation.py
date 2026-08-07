from __future__ import annotations

from dataclasses import replace
import unittest

from software_world_model.ai_infrastructure import (
    AGENTIC_TASK_METRIC_CONTRACT,
    AGENTIC_TASK_OUTPUT_CONTRACT_REF,
    AGENTIC_TASK_PROMPT_PROGRAM_REF,
    AGENTIC_TASK_THRESHOLD_REF,
    AGENTIC_TASK_TOOL_POLICY_REF,
    AgenticEvaluationRole,
    AgenticEvaluationOutput,
    AgenticEvaluationReview,
    AgenticTaskEvaluationCase,
    ReviewedAgenticEvaluationCaseExecutor,
    agentic_knowledge_output_contract_digest,
    agentic_knowledge_prompt_program_digest,
    agentic_knowledge_strategy_implementation_digest,
    create_agentic_task_evaluation_definition,
    reviewed_agentic_case_evidence,
)
from software_world_model.application_services import (
    CapabilityEvaluationRunner,
    CapabilityEvaluationService,
    NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
    NATURAL_TASK_CAPABILITY_ID,
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
    SqliteCapabilityEvaluationRepository,
    SqliteDatabase,
)
from software_world_model.interface.agentic_runtime import (
    agentic_task_capability_registry,
)


def case(role: AgenticEvaluationRole, suffix: str = "primary"):
    return AgenticTaskEvaluationCase(
        role=role,
        case_id=suffix,
        case_version="1.0.0",
        fixture_ref=f"fixture:{role.value.lower()}:{suffix}",
        fixture_digest=digest_of({"fixture": role.value, "suffix": suffix}),
        oracle_ref=f"oracle:{role.value.lower()}:{suffix}",
        oracle_digest=digest_of({"oracle": role.value, "suffix": suffix}),
    )


class AgenticCapabilityEvaluationDefinitionTests(unittest.TestCase):
    def cases(self):
        return tuple(case(role) for role in AgenticEvaluationRole)

    def create(self, cases=None):
        return create_agentic_task_evaluation_definition(
            evaluation_version="1.0.0",
            conformance_result_ref="conformance:ark-current",
            provider_configuration_fingerprint=Digest("sha256:" + "2" * 64),
            model_ref="glm-5-2-260617",
            adapter_version="openai-chat-completions-no-tools@1",
            data_source_revision_ref="evaluation-projects:frozen@1",
            environment_ref="isolated-local-evaluation@1",
            reference_strategy_ref="independently-sealed-role-oracles@1",
            resource_policy_ref="general-task-role-budget@1",
            cases=self.cases() if cases is None else cases,
            valid_for_seconds=3600,
        )

    def reviewed_artifacts(
        self,
        definition,
        *,
        oracle_match=True,
        findings=(),
        usage_complete=True,
    ):
        frozen_case = definition.cases[0]
        output = AgenticEvaluationOutput.create(
            case_id=frozen_case.case_id,
            fixture_digest=frozen_case.fixture_digest,
            output_ref="evaluation-output:requirement-primary",
            output_digest=digest_of({"output": "requirement-primary"}),
            sink_manifest_ref="evaluation-sink:requirement-primary",
            sink_manifest_digest=digest_of({"sink": "requirement-primary"}),
            generator_origin="volcengine-model-output",
            actual_model_fingerprint=definition.model_ref,
            provider_request_ids=("provider-request-1", "provider-request-2"),
            input_tokens=100,
            output_tokens=50,
            usage_complete=usage_complete,
        )
        review = AgenticEvaluationReview.create(
            review_ref="independent-review:requirement-primary",
            case_id=frozen_case.case_id,
            output_digest=output.output_digest,
            oracle_ref=frozen_case.oracle_ref,
            oracle_digest=frozen_case.oracle_digest,
            generator_origin=output.generator_origin,
            reviewer_origin="codex-independent-review",
            platform_contract_valid=True,
            oracle_match=oracle_match,
            unauthorized_reference_count=0,
            material_omission_count=0,
            material_error_count=0,
            findings=findings,
        )
        return frozen_case, output, review

    def test_definition_binds_all_six_roles_and_exact_runtime_contracts(self) -> None:
        definition = self.create()

        self.assertEqual(definition.capability_id, NATURAL_TASK_CAPABILITY_ID)
        self.assertEqual(
            definition.capability_contract_version,
            NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
        )
        self.assertEqual(
            definition.implementation_digest,
            agentic_knowledge_strategy_implementation_digest(),
        )
        self.assertEqual(
            definition.prompt_program_digest,
            agentic_knowledge_prompt_program_digest(),
        )
        self.assertEqual(
            definition.output_schema_digest,
            agentic_knowledge_output_contract_digest(),
        )
        self.assertEqual(definition.prompt_program_ref, AGENTIC_TASK_PROMPT_PROGRAM_REF)
        self.assertEqual(definition.output_schema_ref, AGENTIC_TASK_OUTPUT_CONTRACT_REF)
        self.assertEqual(definition.tool_policy_ref, AGENTIC_TASK_TOOL_POLICY_REF)
        self.assertEqual(definition.threshold_ref, AGENTIC_TASK_THRESHOLD_REF)
        self.assertEqual(
            definition.metric_contract_digest,
            digest_of(AGENTIC_TASK_METRIC_CONTRACT),
        )
        self.assertEqual(len(definition.cases), 6)
        self.assertEqual(
            {item.case_id.split(":", 1)[0] for item in definition.cases},
            {role.value.lower() for role in AgenticEvaluationRole},
        )

    def test_missing_required_role_cannot_form_an_overall_definition(self) -> None:
        incomplete = tuple(
            case(role)
            for role in AgenticEvaluationRole
            if role is not AgenticEvaluationRole.ANSWER_SEMANTIC_REVIEW
        )

        with self.assertRaises(DomainError) as raised:
            self.create(incomplete)

        self.assertEqual(
            raised.exception.code,
            ErrorCode.EVALUATION_DEFINITION_INVALID,
        )

    def test_optional_case_does_not_satisfy_required_role_coverage(self) -> None:
        values = list(self.cases())
        last = values[-1]
        values[-1] = AgenticTaskEvaluationCase(
            role=last.role,
            case_id=last.case_id,
            case_version=last.case_version,
            fixture_ref=last.fixture_ref,
            fixture_digest=last.fixture_digest,
            oracle_ref=last.oracle_ref,
            oracle_digest=last.oracle_digest,
            required=False,
        )

        with self.assertRaises(DomainError) as raised:
            self.create(tuple(values))

        self.assertEqual(
            raised.exception.code,
            ErrorCode.EVALUATION_DEFINITION_INVALID,
        )

    def test_duplicate_identity_inside_one_role_is_rejected(self) -> None:
        values = self.cases() + (
            case(AgenticEvaluationRole.REQUIREMENT_FIDELITY),
        )

        with self.assertRaises(DomainError) as raised:
            self.create(values)

        self.assertEqual(
            raised.exception.code,
            ErrorCode.EVALUATION_DEFINITION_INVALID,
        )

    def test_independent_review_creates_exact_case_evidence(self) -> None:
        definition = self.create()
        frozen_case, output, review = self.reviewed_artifacts(definition)

        evidence = reviewed_agentic_case_evidence(
            definition=definition,
            case=frozen_case,
            output=output,
            review=review,
        )

        self.assertEqual(evidence.conclusion.value, "PASS")
        self.assertEqual(evidence.output_digest, output.output_digest)
        self.assertEqual(evidence.oracle_digest, frozen_case.oracle_digest)
        self.assertEqual(evidence.input_tokens, 100)
        self.assertTrue(evidence.provider_request_id.startswith("aggregate:sha256:"))

    def test_independent_review_failure_becomes_case_failure(self) -> None:
        definition = self.create()
        frozen_case, output, review = self.reviewed_artifacts(
            definition,
            oracle_match=False,
            findings=("one required condition is absent",),
        )

        evidence = reviewed_agentic_case_evidence(
            definition=definition,
            case=frozen_case,
            output=output,
            review=review,
        )

        self.assertEqual(evidence.conclusion.value, "FAIL")

    def test_same_origin_or_tampered_review_cannot_be_evidence(self) -> None:
        definition = self.create()
        frozen_case, output, review = self.reviewed_artifacts(definition)
        with self.assertRaises(DomainError) as raised:
            AgenticEvaluationReview.create(
                review_ref="review:same-origin",
                case_id=frozen_case.case_id,
                output_digest=output.output_digest,
                oracle_ref=frozen_case.oracle_ref,
                oracle_digest=frozen_case.oracle_digest,
                generator_origin=output.generator_origin,
                reviewer_origin=output.generator_origin,
                platform_contract_valid=True,
                oracle_match=True,
                unauthorized_reference_count=0,
                material_omission_count=0,
                material_error_count=0,
                findings=(),
            )
        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

        with self.assertRaises(DomainError) as raised:
            reviewed_agentic_case_evidence(
                definition=definition,
                case=frozen_case,
                output=output,
                review=replace(review, oracle_match=False),
            )
        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_incomplete_usage_cannot_enter_capability_result(self) -> None:
        definition = self.create()
        frozen_case, output, review = self.reviewed_artifacts(
            definition,
            usage_complete=False,
        )

        with self.assertRaises(DomainError) as raised:
            reviewed_agentic_case_evidence(
                definition=definition,
                case=frozen_case,
                output=output,
                review=review,
            )

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_reviewed_six_role_artifacts_run_through_generic_authority(self) -> None:
        definition = self.create()
        outputs = {}
        reviews = {}
        for index, frozen_case in enumerate(definition.cases, start=1):
            output = AgenticEvaluationOutput.create(
                case_id=frozen_case.case_id,
                fixture_digest=frozen_case.fixture_digest,
                output_ref=f"evaluation-output:{index}",
                output_digest=digest_of({"output": index}),
                sink_manifest_ref=f"evaluation-sink:{index}",
                sink_manifest_digest=digest_of({"sink": index}),
                generator_origin="volcengine-model-output",
                actual_model_fingerprint=definition.model_ref,
                provider_request_ids=(f"provider-request-{index}",),
                input_tokens=100,
                output_tokens=50,
                usage_complete=True,
            )
            review = AgenticEvaluationReview.create(
                review_ref=f"independent-review:{index}",
                case_id=frozen_case.case_id,
                output_digest=output.output_digest,
                oracle_ref=frozen_case.oracle_ref,
                oracle_digest=frozen_case.oracle_digest,
                generator_origin=output.generator_origin,
                reviewer_origin="codex-independent-review",
                platform_contract_valid=True,
                oracle_match=True,
                unauthorized_reference_count=0,
                material_omission_count=0,
                material_error_count=0,
                findings=(),
            )
            outputs[frozen_case.case_id] = output
            reviews[frozen_case.case_id] = review
        executor = ReviewedAgenticEvaluationCaseExecutor(
            definition=definition,
            outputs=outputs,
            reviews=reviews,
        )

        class CurrentConformance:
            def validate(self, candidate, at):
                return (
                    candidate.conformance_result_ref
                    == definition.conformance_result_ref
                    and at.tzinfo is not None
                )

        with SqliteDatabase() as database:
            service = CapabilityEvaluationService(
                SqliteCapabilityEvaluationRepository(database),
                agentic_task_capability_registry(),
                CurrentConformance(),
            )
            result = CapabilityEvaluationRunner(service).run_suite(
                definition=definition,
                evaluation_sink_ref="sqlite:isolated-six-role-sink",
                root_allocation_ref="allocation:six-role-evaluation",
                idempotency_key=IdempotencyKey("six-role-evaluation"),
                executor=executor,
                actor="evaluation-owner",
                correlation_ref=CorrelationRef("six-role-evaluation"),
                completion_reason="all independently reviewed cases passed",
            )

        self.assertIsNotNone(result.completion)
        self.assertIsNotNone(result.completion.qualification)
        self.assertEqual(len(result.attempts), 6)


if __name__ == "__main__":
    unittest.main()
