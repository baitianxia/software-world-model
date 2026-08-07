"""Frozen capability-evaluation definition for the complete agentic task strategy."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

from software_world_model.application_services import (
    CaseExecutionEvidence,
    EvaluationConclusion,
    EvaluationCaseDefinition,
    EvaluationCaseExecutionRequest,
    EvaluationDefinition,
    NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
    NATURAL_TASK_CAPABILITY_ID,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .agentic_knowledge_strategy import (
    AGENTIC_KNOWLEDGE_STRATEGY_ID,
    AGENTIC_KNOWLEDGE_STRATEGY_VERSION,
    agentic_knowledge_output_contract_digest,
    agentic_knowledge_prompt_program_digest,
    agentic_knowledge_strategy_implementation_digest,
)


AGENTIC_TASK_EVALUATION_ID = "general-software-knowledge-task"
AGENTIC_TASK_PROMPT_PROGRAM_REF = "agentic-eight-call-prompt-program@1"
AGENTIC_TASK_OUTPUT_CONTRACT_REF = "agentic-eight-closed-output-contracts@1"
AGENTIC_TASK_TOOL_POLICY_REF = "model-no-tools-platform-actions-only@1"
AGENTIC_TASK_THRESHOLD_REF = "all-six-role-categories-and-required-cases-pass@1"


class AgenticEvaluationRole(str, Enum):
    REQUIREMENT_FIDELITY = "REQUIREMENT_FIDELITY"
    SOURCE_INVESTIGATION = "SOURCE_INVESTIGATION"
    FORMAL_FACT_GROUNDING = "FORMAL_FACT_GROUNDING"
    NEED_SUFFICIENCY = "NEED_SUFFICIENCY"
    ANSWER_SOURCE_CLOSURE = "ANSWER_SOURCE_CLOSURE"
    ANSWER_SEMANTIC_REVIEW = "ANSWER_SEMANTIC_REVIEW"


@dataclass(frozen=True, slots=True)
class AgenticTaskEvaluationCase:
    role: AgenticEvaluationRole
    case_id: str
    case_version: str
    fixture_ref: str
    fixture_digest: Digest
    oracle_ref: str
    oracle_digest: Digest
    required: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.role, AgenticEvaluationRole):
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "agentic evaluation role is invalid",
            )
        for value, label in (
            (self.case_id, "evaluation case ID"),
            (self.case_version, "evaluation case version"),
            (self.fixture_ref, "evaluation fixture reference"),
            (self.oracle_ref, "evaluation oracle reference"),
        ):
            _text(value, label)

    def freeze(self) -> EvaluationCaseDefinition:
        return EvaluationCaseDefinition(
            case_id=f"{self.role.value.lower()}:{self.case_id}",
            case_version=self.case_version,
            fixture_ref=self.fixture_ref,
            fixture_digest=self.fixture_digest,
            oracle_ref=self.oracle_ref,
            oracle_digest=self.oracle_digest,
            required=self.required,
        )


AGENTIC_TASK_METRIC_CONTRACT = {
    "required_role_categories": tuple(role.value for role in AgenticEvaluationRole),
    "platform_contract_validation": "PASS",
    "independent_oracle_match": "PASS",
    "unauthorized_reference_count": 0,
    "material_omission_count": 0,
    "material_error_count": 0,
    "required_case_policy": "ALL_PASS",
}


@dataclass(frozen=True, slots=True)
class AgenticEvaluationOutput:
    case_id: str
    fixture_digest: Digest
    output_ref: str
    output_digest: Digest
    sink_manifest_ref: str
    sink_manifest_digest: Digest
    generator_origin: str
    actual_model_fingerprint: str
    provider_request_ids: tuple[str, ...]
    input_tokens: int
    output_tokens: int
    usage_complete: bool
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        case_id: str,
        fixture_digest: Digest,
        output_ref: str,
        output_digest: Digest,
        sink_manifest_ref: str,
        sink_manifest_digest: Digest,
        generator_origin: str,
        actual_model_fingerprint: str,
        provider_request_ids: tuple[str, ...],
        input_tokens: int,
        output_tokens: int,
        usage_complete: bool,
    ) -> "AgenticEvaluationOutput":
        values = {
            "case_id": _text(case_id, "evaluation output case ID"),
            "fixture_digest": fixture_digest.value,
            "output_ref": _text(output_ref, "evaluation output reference"),
            "output_digest": output_digest.value,
            "sink_manifest_ref": _text(
                sink_manifest_ref, "evaluation sink manifest reference"
            ),
            "sink_manifest_digest": sink_manifest_digest.value,
            "generator_origin": _text(generator_origin, "output generator origin"),
            "actual_model_fingerprint": _text(
                actual_model_fingerprint, "actual model fingerprint"
            ),
            "provider_request_ids": _text_tuple(
                provider_request_ids, "provider request IDs"
            ),
            "input_tokens": _nonnegative(input_tokens, "input token count"),
            "output_tokens": _nonnegative(output_tokens, "output token count"),
            "usage_complete": _boolean(usage_complete, "usage completeness"),
        }
        return cls(
            case_id=values["case_id"],
            fixture_digest=fixture_digest,
            output_ref=values["output_ref"],
            output_digest=output_digest,
            sink_manifest_ref=values["sink_manifest_ref"],
            sink_manifest_digest=sink_manifest_digest,
            generator_origin=values["generator_origin"],
            actual_model_fingerprint=values["actual_model_fingerprint"],
            provider_request_ids=values["provider_request_ids"],
            input_tokens=values["input_tokens"],
            output_tokens=values["output_tokens"],
            usage_complete=values["usage_complete"],
            digest=digest_of(values),
        )

    def verify_digest(self) -> bool:
        return digest_of(
            {
                "case_id": self.case_id,
                "fixture_digest": self.fixture_digest.value,
                "output_ref": self.output_ref,
                "output_digest": self.output_digest.value,
                "sink_manifest_ref": self.sink_manifest_ref,
                "sink_manifest_digest": self.sink_manifest_digest.value,
                "generator_origin": self.generator_origin,
                "actual_model_fingerprint": self.actual_model_fingerprint,
                "provider_request_ids": self.provider_request_ids,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "usage_complete": self.usage_complete,
            }
        ) == self.digest


@dataclass(frozen=True, slots=True)
class AgenticEvaluationReview:
    review_ref: str
    case_id: str
    output_digest: Digest
    oracle_ref: str
    oracle_digest: Digest
    generator_origin: str
    reviewer_origin: str
    platform_contract_valid: bool
    oracle_match: bool
    unauthorized_reference_count: int
    material_omission_count: int
    material_error_count: int
    findings: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        review_ref: str,
        case_id: str,
        output_digest: Digest,
        oracle_ref: str,
        oracle_digest: Digest,
        generator_origin: str,
        reviewer_origin: str,
        platform_contract_valid: bool,
        oracle_match: bool,
        unauthorized_reference_count: int,
        material_omission_count: int,
        material_error_count: int,
        findings: tuple[str, ...],
    ) -> "AgenticEvaluationReview":
        generator = _text(generator_origin, "output generator origin")
        reviewer = _text(reviewer_origin, "evaluation reviewer origin")
        if generator == reviewer:
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "evaluation reviewer must be independent from the output generator",
            )
        values = {
            "review_ref": _text(review_ref, "evaluation review reference"),
            "case_id": _text(case_id, "evaluation review case ID"),
            "output_digest": output_digest.value,
            "oracle_ref": _text(oracle_ref, "evaluation oracle reference"),
            "oracle_digest": oracle_digest.value,
            "generator_origin": generator,
            "reviewer_origin": reviewer,
            "platform_contract_valid": _boolean(
                platform_contract_valid, "platform contract result"
            ),
            "oracle_match": _boolean(oracle_match, "oracle match result"),
            "unauthorized_reference_count": _nonnegative(
                unauthorized_reference_count, "unauthorized reference count"
            ),
            "material_omission_count": _nonnegative(
                material_omission_count, "material omission count"
            ),
            "material_error_count": _nonnegative(
                material_error_count, "material error count"
            ),
            "findings": _text_tuple(
                findings,
                "evaluation review findings",
                allow_empty=True,
            ),
        }
        passed = (
            values["platform_contract_valid"] is True
            and values["oracle_match"] is True
            and values["unauthorized_reference_count"] == 0
            and values["material_omission_count"] == 0
            and values["material_error_count"] == 0
        )
        if passed and values["findings"]:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "passing evaluation review cannot contain failure findings",
            )
        if not passed and not values["findings"]:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "failing evaluation review requires findings",
            )
        return cls(
            review_ref=values["review_ref"],
            case_id=values["case_id"],
            output_digest=output_digest,
            oracle_ref=values["oracle_ref"],
            oracle_digest=oracle_digest,
            generator_origin=generator,
            reviewer_origin=reviewer,
            platform_contract_valid=values["platform_contract_valid"],
            oracle_match=values["oracle_match"],
            unauthorized_reference_count=values[
                "unauthorized_reference_count"
            ],
            material_omission_count=values["material_omission_count"],
            material_error_count=values["material_error_count"],
            findings=values["findings"],
            digest=digest_of(values),
        )

    @property
    def conclusion(self) -> EvaluationConclusion:
        return (
            EvaluationConclusion.PASS
            if (
                self.platform_contract_valid
                and self.oracle_match
                and self.unauthorized_reference_count == 0
                and self.material_omission_count == 0
                and self.material_error_count == 0
            )
            else EvaluationConclusion.FAIL
        )

    def verify_digest(self) -> bool:
        return digest_of(
            {
                "review_ref": self.review_ref,
                "case_id": self.case_id,
                "output_digest": self.output_digest.value,
                "oracle_ref": self.oracle_ref,
                "oracle_digest": self.oracle_digest.value,
                "generator_origin": self.generator_origin,
                "reviewer_origin": self.reviewer_origin,
                "platform_contract_valid": self.platform_contract_valid,
                "oracle_match": self.oracle_match,
                "unauthorized_reference_count": self.unauthorized_reference_count,
                "material_omission_count": self.material_omission_count,
                "material_error_count": self.material_error_count,
                "findings": self.findings,
            }
        ) == self.digest


def reviewed_agentic_case_evidence(
    *,
    definition: EvaluationDefinition,
    case: EvaluationCaseDefinition,
    output: AgenticEvaluationOutput,
    review: AgenticEvaluationReview,
) -> CaseExecutionEvidence:
    """Convert independently reviewed artifacts into repository evidence."""

    if (
        case not in definition.cases
        or not output.verify_digest()
        or not review.verify_digest()
        or output.case_id != case.case_id
        or output.fixture_digest != case.fixture_digest
        or review.case_id != case.case_id
        or review.output_digest != output.output_digest
        or review.oracle_ref != case.oracle_ref
        or review.oracle_digest != case.oracle_digest
        or review.generator_origin != output.generator_origin
        or review.reviewer_origin == output.generator_origin
        or output.actual_model_fingerprint != definition.model_ref
        or not output.usage_complete
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "reviewed agentic case evidence does not match the frozen definition",
        )
    return CaseExecutionEvidence(
        conclusion=review.conclusion,
        output_ref=output.output_ref,
        output_digest=output.output_digest,
        sink_manifest_ref=output.sink_manifest_ref,
        sink_manifest_digest=output.sink_manifest_digest,
        oracle_ref=case.oracle_ref,
        oracle_digest=case.oracle_digest,
        actual_model_fingerprint=output.actual_model_fingerprint,
        provider_request_id=(
            f"aggregate:{digest_of(output.provider_request_ids).value}"
        ),
        input_tokens=output.input_tokens,
        output_tokens=output.output_tokens,
        usage_complete=True,
    )


class ReviewedAgenticEvaluationCaseExecutor:
    """Feed sealed, independently reviewed case artifacts into the generic runner."""

    def __init__(
        self,
        *,
        definition: EvaluationDefinition,
        outputs: Mapping[str, AgenticEvaluationOutput],
        reviews: Mapping[str, AgenticEvaluationReview],
    ) -> None:
        expected = {case.case_id for case in definition.cases}
        if set(outputs) != expected or set(reviews) != expected:
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "reviewed evaluation artifacts must cover every frozen case exactly",
            )
        self._definition = definition
        self._outputs = dict(outputs)
        self._reviews = dict(reviews)

    def execute(
        self, request: EvaluationCaseExecutionRequest
    ) -> CaseExecutionEvidence:
        if request.definition.digest != self._definition.digest:
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "reviewed evaluation artifacts belong to another definition",
            )
        return reviewed_agentic_case_evidence(
            definition=self._definition,
            case=request.case,
            output=self._outputs[request.case.case_id],
            review=self._reviews[request.case.case_id],
        )


def create_agentic_task_evaluation_definition(
    *,
    evaluation_version: str,
    conformance_result_ref: str,
    provider_configuration_fingerprint: Digest,
    model_ref: str,
    adapter_version: str,
    data_source_revision_ref: str,
    environment_ref: str,
    reference_strategy_ref: str,
    resource_policy_ref: str,
    cases: tuple[AgenticTaskEvaluationCase, ...],
    valid_for_seconds: int,
    design_baseline_ref: str = "SWM-DBM-ITER-001-REV-002",
) -> EvaluationDefinition:
    """Freeze a suite only when every production model role is represented."""

    if not isinstance(cases, tuple) or not cases:
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            "agentic evaluation requires frozen cases",
        )
    required_roles = {case.role for case in cases if case.required}
    missing_roles = set(AgenticEvaluationRole) - required_roles
    if missing_roles:
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            "agentic evaluation does not cover every required model role",
            {"missing_role_count": len(missing_roles)},
        )
    frozen_cases = tuple(case.freeze() for case in cases)
    if len({case.case_id for case in frozen_cases}) != len(frozen_cases):
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            "agentic evaluation case identities must be unique within each role",
        )
    return EvaluationDefinition.create(
        evaluation_id=AGENTIC_TASK_EVALUATION_ID,
        evaluation_version=evaluation_version,
        capability_id=NATURAL_TASK_CAPABILITY_ID,
        capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
        strategy_id=AGENTIC_KNOWLEDGE_STRATEGY_ID,
        strategy_version=AGENTIC_KNOWLEDGE_STRATEGY_VERSION,
        design_baseline_ref=design_baseline_ref,
        implementation_digest=agentic_knowledge_strategy_implementation_digest(),
        conformance_result_ref=conformance_result_ref,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        model_ref=model_ref,
        adapter_version=adapter_version,
        prompt_program_ref=AGENTIC_TASK_PROMPT_PROGRAM_REF,
        prompt_program_digest=agentic_knowledge_prompt_program_digest(),
        output_schema_ref=AGENTIC_TASK_OUTPUT_CONTRACT_REF,
        output_schema_digest=agentic_knowledge_output_contract_digest(),
        tool_policy_ref=AGENTIC_TASK_TOOL_POLICY_REF,
        data_source_revision_ref=data_source_revision_ref,
        environment_ref=environment_ref,
        reference_strategy_ref=reference_strategy_ref,
        resource_policy_ref=resource_policy_ref,
        metric_contract_digest=digest_of(AGENTIC_TASK_METRIC_CONTRACT),
        threshold_ref=AGENTIC_TASK_THRESHOLD_REF,
        cases=frozen_cases,
        valid_for_seconds=valid_for_seconds,
    )


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def _text_tuple(
    value: tuple[str, ...], label: str, *, allow_empty: bool = False
) -> tuple[str, ...]:
    if (
        not isinstance(value, tuple)
        or (not allow_empty and not value)
        or any(
            not isinstance(item, str)
            or not item
            or item != item.strip()
            for item in value
        )
        or len(set(value)) != len(value)
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be unique non-empty text values",
        )
    return value


def _nonnegative(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be a non-negative integer",
        )
    return value


def _boolean(value: bool, label: str) -> bool:
    if not isinstance(value, bool):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be boolean")
    return value
