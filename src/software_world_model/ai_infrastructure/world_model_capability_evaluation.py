"""Closed capability-evaluation definition for WORLD_MODEL proposals."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from software_world_model.application_services import (
    CapabilityDefinition,
    CapabilityRegistry,
    EvaluationCaseDefinition,
    EvaluationDefinition,
    StrategyDefinition,
    StrategyKind,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .agentic_capability_evaluation import (
    AgenticEvaluationOutput as WorldModelEvaluationOutput,
    AgenticEvaluationReview as WorldModelEvaluationReview,
    ReviewedAgenticEvaluationCaseExecutor as ReviewedWorldModelEvaluationCaseExecutor,
    reviewed_agentic_case_evidence as reviewed_world_model_case_evidence,
)
from .world_model_answer_strategy import (
    COMPLETE_NEGATIVE_ANSWER,
    ENTITY_CANDIDATE_RESOLUTION,
    GENERIC_QUERY_PLANNING,
    INDEPENDENT_ANSWER_REVIEW,
    ORDERED_DIFF_EXPRESSION,
    REQUIREMENT_FIDELITY,
    VIEW_LIMITATION_AND_KNOWLEDGE_GAP,
    WORLD_MODEL_ANSWER_STRATEGY_ID,
    WORLD_MODEL_ANSWER_STRATEGY_VERSION,
    WORLD_MODEL_ANSWER_TOOL_POLICY_REF,
    WORLD_MODEL_PROPOSAL_CAPABILITY_CONTRACT_VERSION,
    WORLD_MODEL_PROPOSAL_CAPABILITY_ID,
    world_model_answer_output_contract_digest,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
)


WORLD_MODEL_EVALUATION_ID = "snapshot-first-world-model-authority-proposals"
WORLD_MODEL_EVALUATION_PROMPT_PROGRAM_REF = (
    "snapshot-first-world-model-proposal-program@1"
)
WORLD_MODEL_EVALUATION_OUTPUT_CONTRACT_REF = (
    "snapshot-first-world-model-closed-proposal-outputs@1"
)
WORLD_MODEL_EVALUATION_THRESHOLD_REF = "all-seven-required-cases-exact-pass@1"


class WorldModelEvaluationRole(str, Enum):
    REQUIREMENT_FIDELITY = REQUIREMENT_FIDELITY
    GENERIC_QUERY_PLANNING = GENERIC_QUERY_PLANNING
    COMPLETE_NEGATIVE_ANSWER = COMPLETE_NEGATIVE_ANSWER
    VIEW_LIMITATION_AND_KNOWLEDGE_GAP = VIEW_LIMITATION_AND_KNOWLEDGE_GAP
    ORDERED_DIFF_EXPRESSION = ORDERED_DIFF_EXPRESSION
    INDEPENDENT_ANSWER_REVIEW = INDEPENDENT_ANSWER_REVIEW
    ENTITY_CANDIDATE_RESOLUTION = ENTITY_CANDIDATE_RESOLUTION


@dataclass(frozen=True, slots=True)
class WorldModelEvaluationCase:
    role: WorldModelEvaluationRole
    case_id: str
    case_version: str
    fixture_ref: str
    fixture_digest: Digest
    oracle_ref: str
    oracle_digest: Digest
    required: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.role, WorldModelEvaluationRole):
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "world-model evaluation role is invalid",
            )
        for value, label in (
            (self.case_id, "evaluation case ID"),
            (self.case_version, "evaluation case version"),
            (self.fixture_ref, "evaluation fixture reference"),
            (self.oracle_ref, "evaluation oracle reference"),
        ):
            if not isinstance(value, str) or not value or value != value.strip():
                raise DomainError(
                    ErrorCode.EVALUATION_DEFINITION_INVALID,
                    f"{label} must be non-empty",
                )

    def freeze(self) -> EvaluationCaseDefinition:
        return EvaluationCaseDefinition(
            case_id=self.case_id,
            case_version=self.case_version,
            fixture_ref=self.fixture_ref,
            fixture_digest=self.fixture_digest,
            oracle_ref=self.oracle_ref,
            oracle_digest=self.oracle_digest,
            required=self.required,
        )


WORLD_MODEL_EVALUATION_METRIC_CONTRACT = {
    "required_role_categories": tuple(role.value for role in WorldModelEvaluationRole),
    "projection_exact_json_equality": "PASS",
    "forbidden_event_count": 0,
    "evaluator_origin": "SEPARATE_DETERMINISTIC_PROCESS",
    "evaluator_product_import_count": 0,
    "provider_calls_per_case": 1,
    "hidden_retry_count": 0,
    "required_case_policy": "ALL_PASS",
    "failure_count": 0,
    "unknown_count": 0,
}


def create_world_model_evaluation_definition(
    *,
    evaluation_version: str,
    conformance_result_ref: str,
    provider_configuration_fingerprint: Digest,
    model_ref: str,
    adapter_version: str,
    exact_g3a_checkpoint_ref: str,
    environment_ref: str,
    reference_strategy_ref: str,
    resource_policy_ref: str,
    cases: tuple[WorldModelEvaluationCase, ...],
    valid_for_seconds: int,
) -> EvaluationDefinition:
    required_roles = {case.role for case in cases if case.required}
    missing = set(WorldModelEvaluationRole) - required_roles
    if missing:
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            "world-model evaluation does not cover every required role",
            {"missing_role_count": len(missing)},
        )
    identities = [(case.role, case.case_id) for case in cases]
    if len(set(identities)) != len(identities):
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            "world-model evaluation case identity is duplicated",
        )
    return EvaluationDefinition.create(
        evaluation_id=WORLD_MODEL_EVALUATION_ID,
        evaluation_version=evaluation_version,
        capability_id=WORLD_MODEL_PROPOSAL_CAPABILITY_ID,
        capability_contract_version=WORLD_MODEL_PROPOSAL_CAPABILITY_CONTRACT_VERSION,
        strategy_id=WORLD_MODEL_ANSWER_STRATEGY_ID,
        strategy_version=WORLD_MODEL_ANSWER_STRATEGY_VERSION,
        design_baseline_ref="SYS-ADR-014",
        implementation_digest=world_model_answer_strategy_implementation_digest(),
        conformance_result_ref=conformance_result_ref,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        model_ref=model_ref,
        adapter_version=adapter_version,
        prompt_program_ref=WORLD_MODEL_EVALUATION_PROMPT_PROGRAM_REF,
        prompt_program_digest=world_model_answer_prompt_program_digest(),
        output_schema_ref=WORLD_MODEL_EVALUATION_OUTPUT_CONTRACT_REF,
        output_schema_digest=world_model_answer_output_contract_digest(),
        tool_policy_ref=WORLD_MODEL_ANSWER_TOOL_POLICY_REF,
        data_source_revision_ref=exact_g3a_checkpoint_ref,
        environment_ref=environment_ref,
        reference_strategy_ref=reference_strategy_ref,
        resource_policy_ref=resource_policy_ref,
        metric_contract_digest=digest_of(WORLD_MODEL_EVALUATION_METRIC_CONTRACT),
        threshold_ref=WORLD_MODEL_EVALUATION_THRESHOLD_REF,
        cases=tuple(case.freeze() for case in cases),
        valid_for_seconds=valid_for_seconds,
    )


def world_model_capability_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register_capability(
        CapabilityDefinition(
            capability_id=WORLD_MODEL_PROPOSAL_CAPABILITY_ID,
            contract_version=WORLD_MODEL_PROPOSAL_CAPABILITY_CONTRACT_VERSION,
            purpose=(
                "Propose Requirement, Query Plan, assessment, draft, and review "
                "values from an exact source-closed WORLD_MODEL read authority"
            ),
            input_contract_digest=digest_of(
                {
                    "authority": "EXACT_WORLD_MODEL_READ_SET_AND_SEALED_RESULTS@1",
                    "source": "FORBIDDEN",
                    "evidence_payload": "FORBIDDEN",
                    "proposal_only": True,
                }
            ),
            output_contract_digest=world_model_answer_output_contract_digest(),
        )
    )
    registry.register_strategy(world_model_strategy_definition())
    return registry


def world_model_strategy_definition() -> StrategyDefinition:
    return StrategyDefinition(
        strategy_id=WORLD_MODEL_ANSWER_STRATEGY_ID,
        strategy_version=WORLD_MODEL_ANSWER_STRATEGY_VERSION,
        capability_id=WORLD_MODEL_PROPOSAL_CAPABILITY_ID,
        capability_contract_version=WORLD_MODEL_PROPOSAL_CAPABILITY_CONTRACT_VERSION,
        kind=StrategyKind.MODEL_PRIMARY,
        implementation_digest=world_model_answer_strategy_implementation_digest(),
        requires_model=True,
    )


__all__ = [
    "WORLD_MODEL_EVALUATION_ID",
    "WORLD_MODEL_EVALUATION_METRIC_CONTRACT",
    "WORLD_MODEL_EVALUATION_OUTPUT_CONTRACT_REF",
    "WORLD_MODEL_EVALUATION_PROMPT_PROGRAM_REF",
    "WORLD_MODEL_EVALUATION_THRESHOLD_REF",
    "WorldModelEvaluationCase",
    "WorldModelEvaluationOutput",
    "WorldModelEvaluationReview",
    "WorldModelEvaluationRole",
    "ReviewedWorldModelEvaluationCaseExecutor",
    "create_world_model_evaluation_definition",
    "reviewed_world_model_case_evidence",
    "world_model_capability_registry",
    "world_model_strategy_definition",
]
