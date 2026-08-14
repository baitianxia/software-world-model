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
)
from .versioned_world_model_answer_strategy import (
    IMPLEMENTATION_ANSWER_DRAFTING,
    IMPLEMENTATION_ANSWER_REVIEW,
    IMPLEMENTATION_QUERY_PLANNING,
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
    MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT,
    WorldModelProposalContract,
    java_source_semantics_world_model_output_contract_digest,
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
JAVA_WORLD_MODEL_EVALUATION_ID = (
    "java-snapshot-first-world-model-authority-proposals"
)
JAVA_WORLD_MODEL_EVALUATION_PROMPT_PROGRAM_REF = (
    "java-snapshot-first-world-model-proposal-program@1"
)
JAVA_WORLD_MODEL_EVALUATION_OUTPUT_CONTRACT_REF = (
    "java-snapshot-first-world-model-closed-proposal-outputs@1"
)
JAVA_WORLD_MODEL_EVALUATION_THRESHOLD_REF = (
    "all-eight-java-required-cases-exact-pass@1"
)
JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_ID = (
    "java-source-semantics-world-model-authority-proposals"
)
JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_PROMPT_PROGRAM_REF = (
    "java-source-semantics-world-model-proposal-program@1"
)
JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_OUTPUT_CONTRACT_REF = (
    "java-source-semantics-world-model-closed-proposal-outputs@1"
)
JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_THRESHOLD_REF = (
    "all-twelve-java-source-semantics-required-cases-exact-pass@1"
)


class WorldModelEvaluationRole(str, Enum):
    REQUIREMENT_FIDELITY = REQUIREMENT_FIDELITY
    GENERIC_QUERY_PLANNING = GENERIC_QUERY_PLANNING
    COMPLETE_NEGATIVE_ANSWER = COMPLETE_NEGATIVE_ANSWER
    VIEW_LIMITATION_AND_KNOWLEDGE_GAP = VIEW_LIMITATION_AND_KNOWLEDGE_GAP
    ORDERED_DIFF_EXPRESSION = ORDERED_DIFF_EXPRESSION
    INDEPENDENT_ANSWER_REVIEW = INDEPENDENT_ANSWER_REVIEW
    ENTITY_CANDIDATE_RESOLUTION = ENTITY_CANDIDATE_RESOLUTION


class JavaSourceSemanticsWorldModelEvaluationRole(str, Enum):
    IMPLEMENTATION_QUERY_PLANNING = IMPLEMENTATION_QUERY_PLANNING
    IMPLEMENTATION_ANSWER_DRAFTING = IMPLEMENTATION_ANSWER_DRAFTING
    IMPLEMENTATION_ANSWER_REVIEW = IMPLEMENTATION_ANSWER_REVIEW


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


@dataclass(frozen=True, slots=True)
class JavaSourceSemanticsWorldModelEvaluationCase:
    role: JavaSourceSemanticsWorldModelEvaluationRole
    case_id: str
    case_version: str
    fixture_ref: str
    fixture_digest: Digest
    oracle_ref: str
    oracle_digest: Digest
    required: bool = True

    def __post_init__(self) -> None:
        if not isinstance(
            self.role, JavaSourceSemanticsWorldModelEvaluationRole
        ):
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "Java source-semantics evaluation role is invalid",
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


JAVA_WORLD_MODEL_EVALUATION_METRIC_CONTRACT = {
    **WORLD_MODEL_EVALUATION_METRIC_CONTRACT,
    "required_case_count": 8,
    "required_generic_operation_vocabulary": (
        JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
    ),
    "required_java_planning_cases": (
        "JAVA_METHOD_INVENTORY",
        "JAVA_STATIC_CALL_PATH",
    ),
}


JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_METRIC_CONTRACT = {
    "required_role_categories": tuple(
        role.value for role in JavaSourceSemanticsWorldModelEvaluationRole
    ),
    "required_case_count": 12,
    "projection_exact_json_equality": "PASS",
    "forbidden_event_count": 0,
    "evaluator_origin": "SEPARATE_DETERMINISTIC_PROCESS",
    "evaluator_product_import_count": 0,
    "provider_calls_per_case": 1,
    "hidden_retry_count": 0,
    "required_case_policy": "ALL_PASS",
    "failure_count": 0,
    "unknown_count": 0,
    "required_operation_vocabulary": (
        JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
    ),
    "runtime_call_protocol": (
        "IMPLEMENTATION_QUERY_PLANNING",
        "IMPLEMENTATION_ANSWER_DRAFTING",
        "IMPLEMENTATION_ANSWER_REVIEW",
    ),
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
    return _create_world_model_evaluation_definition(
        evaluation_id=WORLD_MODEL_EVALUATION_ID,
        evaluation_version=evaluation_version,
        conformance_result_ref=conformance_result_ref,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        model_ref=model_ref,
        adapter_version=adapter_version,
        exact_g3a_checkpoint_ref=exact_g3a_checkpoint_ref,
        environment_ref=environment_ref,
        reference_strategy_ref=reference_strategy_ref,
        resource_policy_ref=resource_policy_ref,
        cases=cases,
        valid_for_seconds=valid_for_seconds,
        proposal_contract=MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT,
        prompt_program_ref=WORLD_MODEL_EVALUATION_PROMPT_PROGRAM_REF,
        output_contract_ref=WORLD_MODEL_EVALUATION_OUTPUT_CONTRACT_REF,
        metric_contract=WORLD_MODEL_EVALUATION_METRIC_CONTRACT,
        threshold_ref=WORLD_MODEL_EVALUATION_THRESHOLD_REF,
        required_role_values={item.value for item in WorldModelEvaluationRole},
        output_schema_digest=world_model_answer_output_contract_digest(),
    )


def create_java_world_model_evaluation_definition(
    *,
    evaluation_version: str,
    conformance_result_ref: str,
    provider_configuration_fingerprint: Digest,
    model_ref: str,
    adapter_version: str,
    exact_candidate_checkpoint_ref: str,
    environment_ref: str,
    reference_strategy_ref: str,
    resource_policy_ref: str,
    cases: tuple[WorldModelEvaluationCase, ...],
    valid_for_seconds: int,
) -> EvaluationDefinition:
    if len(cases) != 8:
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            "Java world-model evaluation must contain exactly eight cases",
        )
    return _create_world_model_evaluation_definition(
        evaluation_id=JAVA_WORLD_MODEL_EVALUATION_ID,
        evaluation_version=evaluation_version,
        conformance_result_ref=conformance_result_ref,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        model_ref=model_ref,
        adapter_version=adapter_version,
        exact_g3a_checkpoint_ref=exact_candidate_checkpoint_ref,
        environment_ref=environment_ref,
        reference_strategy_ref=reference_strategy_ref,
        resource_policy_ref=resource_policy_ref,
        cases=cases,
        valid_for_seconds=valid_for_seconds,
        proposal_contract=JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
        prompt_program_ref=JAVA_WORLD_MODEL_EVALUATION_PROMPT_PROGRAM_REF,
        output_contract_ref=JAVA_WORLD_MODEL_EVALUATION_OUTPUT_CONTRACT_REF,
        metric_contract=JAVA_WORLD_MODEL_EVALUATION_METRIC_CONTRACT,
        threshold_ref=JAVA_WORLD_MODEL_EVALUATION_THRESHOLD_REF,
        required_role_values={item.value for item in WorldModelEvaluationRole},
        output_schema_digest=world_model_answer_output_contract_digest(),
    )


def create_java_source_semantics_world_model_evaluation_definition(
    *,
    evaluation_version: str,
    conformance_result_ref: str,
    provider_configuration_fingerprint: Digest,
    model_ref: str,
    adapter_version: str,
    exact_candidate_checkpoint_ref: str,
    environment_ref: str,
    reference_strategy_ref: str,
    resource_policy_ref: str,
    cases: tuple[JavaSourceSemanticsWorldModelEvaluationCase, ...],
    valid_for_seconds: int,
) -> EvaluationDefinition:
    if len(cases) != 12:
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            "Java source-semantics evaluation must contain exactly twelve cases",
        )
    return _create_world_model_evaluation_definition(
        evaluation_id=JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_ID,
        evaluation_version=evaluation_version,
        conformance_result_ref=conformance_result_ref,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        model_ref=model_ref,
        adapter_version=adapter_version,
        exact_g3a_checkpoint_ref=exact_candidate_checkpoint_ref,
        environment_ref=environment_ref,
        reference_strategy_ref=reference_strategy_ref,
        resource_policy_ref=resource_policy_ref,
        cases=cases,
        valid_for_seconds=valid_for_seconds,
        proposal_contract=(
            JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
        ),
        prompt_program_ref=(
            JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_PROMPT_PROGRAM_REF
        ),
        output_contract_ref=(
            JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_OUTPUT_CONTRACT_REF
        ),
        metric_contract=(
            JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_METRIC_CONTRACT
        ),
        threshold_ref=(
            JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_THRESHOLD_REF
        ),
        required_role_values={
            item.value for item in JavaSourceSemanticsWorldModelEvaluationRole
        },
        output_schema_digest=(
            java_source_semantics_world_model_output_contract_digest()
        ),
    )


def _create_world_model_evaluation_definition(
    *,
    evaluation_id: str,
    evaluation_version: str,
    conformance_result_ref: str,
    provider_configuration_fingerprint: Digest,
    model_ref: str,
    adapter_version: str,
    exact_g3a_checkpoint_ref: str,
    environment_ref: str,
    reference_strategy_ref: str,
    resource_policy_ref: str,
    cases: tuple[
        WorldModelEvaluationCase | JavaSourceSemanticsWorldModelEvaluationCase,
        ...,
    ],
    valid_for_seconds: int,
    proposal_contract: WorldModelProposalContract,
    prompt_program_ref: str,
    output_contract_ref: str,
    metric_contract: dict[str, object],
    threshold_ref: str,
    required_role_values: set[str],
    output_schema_digest: Digest,
) -> EvaluationDefinition:
    required_roles = {case.role.value for case in cases if case.required}
    missing = required_role_values - required_roles
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
        evaluation_id=evaluation_id,
        evaluation_version=evaluation_version,
        capability_id=WORLD_MODEL_PROPOSAL_CAPABILITY_ID,
        capability_contract_version=proposal_contract.capability_contract_version,
        strategy_id=WORLD_MODEL_ANSWER_STRATEGY_ID,
        strategy_version=proposal_contract.strategy_version,
        design_baseline_ref="SYS-ADR-014",
        implementation_digest=world_model_answer_strategy_implementation_digest(
            proposal_contract
        ),
        conformance_result_ref=conformance_result_ref,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        model_ref=model_ref,
        adapter_version=adapter_version,
        prompt_program_ref=prompt_program_ref,
        prompt_program_digest=world_model_answer_prompt_program_digest(
            proposal_contract
        ),
        output_schema_ref=output_contract_ref,
        output_schema_digest=output_schema_digest,
        tool_policy_ref=WORLD_MODEL_ANSWER_TOOL_POLICY_REF,
        data_source_revision_ref=exact_g3a_checkpoint_ref,
        environment_ref=environment_ref,
        reference_strategy_ref=reference_strategy_ref,
        resource_policy_ref=resource_policy_ref,
        metric_contract_digest=digest_of(metric_contract),
        threshold_ref=threshold_ref,
        cases=tuple(case.freeze() for case in cases),
        valid_for_seconds=valid_for_seconds,
    )


def world_model_capability_registry() -> CapabilityRegistry:
    return _world_model_capability_registry(MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT)


def java_world_model_capability_registry() -> CapabilityRegistry:
    return _world_model_capability_registry(JAVA_WORLD_MODEL_PROPOSAL_CONTRACT)


def java_source_semantics_world_model_capability_registry() -> CapabilityRegistry:
    return _world_model_capability_registry(
        JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
    )


def _world_model_capability_registry(
    proposal_contract: WorldModelProposalContract,
) -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register_capability(
        CapabilityDefinition(
            capability_id=WORLD_MODEL_PROPOSAL_CAPABILITY_ID,
            contract_version=proposal_contract.capability_contract_version,
            purpose=(
                "Propose Requirement, Query Plan, assessment, draft, and review "
                "values from an exact source-closed WORLD_MODEL read authority"
            ),
            input_contract_digest=_input_contract_digest(proposal_contract),
            output_contract_digest=_output_contract_digest(proposal_contract),
        )
    )
    registry.register_strategy(world_model_strategy_definition(proposal_contract))
    return registry


def world_model_strategy_definition(
    proposal_contract: WorldModelProposalContract = MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT,
) -> StrategyDefinition:
    return StrategyDefinition(
        strategy_id=WORLD_MODEL_ANSWER_STRATEGY_ID,
        strategy_version=proposal_contract.strategy_version,
        capability_id=WORLD_MODEL_PROPOSAL_CAPABILITY_ID,
        capability_contract_version=proposal_contract.capability_contract_version,
        kind=StrategyKind.MODEL_PRIMARY,
        implementation_digest=world_model_answer_strategy_implementation_digest(
            proposal_contract
        ),
        requires_model=True,
    )


def java_world_model_strategy_definition() -> StrategyDefinition:
    return world_model_strategy_definition(JAVA_WORLD_MODEL_PROPOSAL_CONTRACT)


def java_source_semantics_world_model_strategy_definition() -> StrategyDefinition:
    return world_model_strategy_definition(
        JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
    )


def _output_contract_digest(
    proposal_contract: WorldModelProposalContract,
) -> Digest:
    return (
        java_source_semantics_world_model_output_contract_digest()
        if proposal_contract
        == JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
        else world_model_answer_output_contract_digest()
    )


def _input_contract_digest(
    proposal_contract: WorldModelProposalContract,
) -> Digest:
    core: dict[str, object] = {
        "authority": "EXACT_WORLD_MODEL_READ_SET_AND_SEALED_RESULTS@1",
        "source": "FORBIDDEN",
        "evidence_payload": "FORBIDDEN",
        "proposal_only": True,
    }
    if proposal_contract != MAVEN_WORLD_MODEL_PROPOSAL_CONTRACT:
        core.update(
            {
                "proposal_vocabulary_ref": (
                    proposal_contract.proposal_vocabulary_ref
                ),
                "available_operations": proposal_contract.available_operations,
            }
        )
    return digest_of(core)


__all__ = [
    "JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_ID",
    "JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_METRIC_CONTRACT",
    "JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_OUTPUT_CONTRACT_REF",
    "JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_PROMPT_PROGRAM_REF",
    "JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_THRESHOLD_REF",
    "WORLD_MODEL_EVALUATION_ID",
    "WORLD_MODEL_EVALUATION_METRIC_CONTRACT",
    "WORLD_MODEL_EVALUATION_OUTPUT_CONTRACT_REF",
    "WORLD_MODEL_EVALUATION_PROMPT_PROGRAM_REF",
    "WORLD_MODEL_EVALUATION_THRESHOLD_REF",
    "JAVA_WORLD_MODEL_EVALUATION_ID",
    "JAVA_WORLD_MODEL_EVALUATION_METRIC_CONTRACT",
    "JAVA_WORLD_MODEL_EVALUATION_OUTPUT_CONTRACT_REF",
    "JAVA_WORLD_MODEL_EVALUATION_PROMPT_PROGRAM_REF",
    "JAVA_WORLD_MODEL_EVALUATION_THRESHOLD_REF",
    "WorldModelEvaluationCase",
    "JavaSourceSemanticsWorldModelEvaluationCase",
    "JavaSourceSemanticsWorldModelEvaluationRole",
    "WorldModelEvaluationOutput",
    "WorldModelEvaluationReview",
    "WorldModelEvaluationRole",
    "ReviewedWorldModelEvaluationCaseExecutor",
    "create_world_model_evaluation_definition",
    "create_java_world_model_evaluation_definition",
    "create_java_source_semantics_world_model_evaluation_definition",
    "java_world_model_capability_registry",
    "java_source_semantics_world_model_capability_registry",
    "java_world_model_strategy_definition",
    "java_source_semantics_world_model_strategy_definition",
    "reviewed_world_model_case_evidence",
    "world_model_capability_registry",
    "world_model_strategy_definition",
]
