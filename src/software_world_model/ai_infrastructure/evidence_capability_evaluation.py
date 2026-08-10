"""Frozen capability-evaluation definition for evidence-first answering."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from software_world_model.application_services import (
    EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION,
    EVIDENCE_ANSWER_CAPABILITY_ID,
    EvaluationCaseDefinition,
    EvaluationDefinition,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .evidence_answer_strategy import (
    EVIDENCE_FIRST_STRATEGY_ID,
    EVIDENCE_FIRST_STRATEGY_VERSION,
    evidence_first_task_output_contract_digest,
    evidence_first_task_prompt_program_digest,
    evidence_first_task_strategy_implementation_digest,
)


EVIDENCE_TASK_EVALUATION_ID = "general-evidence-first-software-answer"
EVIDENCE_TASK_PROMPT_PROGRAM_REF = "evidence-first-reviewed-program@4"
EVIDENCE_TASK_OUTPUT_CONTRACT_REF = "evidence-first-closed-outputs@2"
EVIDENCE_TASK_TOOL_POLICY_REF = "model-no-tools-platform-source-actions-only@1"
EVIDENCE_TASK_THRESHOLD_REF = "all-evidence-role-categories-pass@1"


class EvidenceEvaluationRole(str, Enum):
    QUESTION_FIDELITY = "QUESTION_FIDELITY"
    SOURCE_INVESTIGATION = "SOURCE_INVESTIGATION"
    CITED_ANSWER_GENERATION = "CITED_ANSWER_GENERATION"
    INDEPENDENT_ANSWER_REVIEW = "INDEPENDENT_ANSWER_REVIEW"
    FIXED_PACKET_REWRITE = "FIXED_PACKET_REWRITE"
    EVIDENCE_GAP_CLASSIFICATION = "EVIDENCE_GAP_CLASSIFICATION"
    RESPONSE_LANGUAGE_REVIEW = "RESPONSE_LANGUAGE_REVIEW"
    TEMPORAL_ORDER_REVIEW = "TEMPORAL_ORDER_REVIEW"
    UNSUPPORTED_INTENT_REVIEW = "UNSUPPORTED_INTENT_REVIEW"
    RELEVANCE_READABILITY_REVIEW = "RELEVANCE_READABILITY_REVIEW"


@dataclass(frozen=True, slots=True)
class EvidenceTaskEvaluationCase:
    role: EvidenceEvaluationRole
    case_id: str
    case_version: str
    fixture_ref: str
    fixture_digest: Digest
    oracle_ref: str
    oracle_digest: Digest
    required: bool = True

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


EVIDENCE_TASK_METRIC_CONTRACT = {
    "required_role_categories": tuple(role.value for role in EvidenceEvaluationRole),
    "platform_contract_validation": "PASS",
    "independent_oracle_match": "PASS",
    "unauthorized_reference_count": 0,
    "material_omission_count": 0,
    "material_error_count": 0,
    "required_case_policy": "ALL_PASS",
}


def create_evidence_task_evaluation_definition(
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
    cases: tuple[EvidenceTaskEvaluationCase, ...],
    valid_for_seconds: int,
) -> EvaluationDefinition:
    required_roles = {case.role for case in cases if case.required}
    missing = set(EvidenceEvaluationRole) - required_roles
    if missing:
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            "evidence evaluation does not cover every required model role",
            {"missing_role_count": len(missing)},
        )
    frozen = tuple(case.freeze() for case in cases)
    return EvaluationDefinition.create(
        evaluation_id=EVIDENCE_TASK_EVALUATION_ID,
        evaluation_version=evaluation_version,
        capability_id=EVIDENCE_ANSWER_CAPABILITY_ID,
        capability_contract_version=EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION,
        strategy_id=EVIDENCE_FIRST_STRATEGY_ID,
        strategy_version=EVIDENCE_FIRST_STRATEGY_VERSION,
        design_baseline_ref="SYS-ADR-013",
        implementation_digest=evidence_first_task_strategy_implementation_digest(),
        conformance_result_ref=conformance_result_ref,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        model_ref=model_ref,
        adapter_version=adapter_version,
        prompt_program_ref=EVIDENCE_TASK_PROMPT_PROGRAM_REF,
        prompt_program_digest=evidence_first_task_prompt_program_digest(),
        output_schema_ref=EVIDENCE_TASK_OUTPUT_CONTRACT_REF,
        output_schema_digest=evidence_first_task_output_contract_digest(),
        tool_policy_ref=EVIDENCE_TASK_TOOL_POLICY_REF,
        data_source_revision_ref=data_source_revision_ref,
        environment_ref=environment_ref,
        reference_strategy_ref=reference_strategy_ref,
        resource_policy_ref=resource_policy_ref,
        metric_contract_digest=digest_of(EVIDENCE_TASK_METRIC_CONTRACT),
        threshold_ref=EVIDENCE_TASK_THRESHOLD_REF,
        cases=frozen,
        valid_for_seconds=valid_for_seconds,
    )
