"""Fail-closed composition for the evaluated natural-language task strategy."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Mapping

from software_world_model.ai_infrastructure import (
    AGENTIC_KNOWLEDGE_STRATEGY_ID,
    AGENTIC_KNOWLEDGE_STRATEGY_VERSION,
    AgenticKnowledgeStrategyBundle,
    AgenticModelStrategyConfiguration,
    ModelGateway,
    ModelReviewedFactGroundingVerifier,
    UrllibVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    agentic_knowledge_output_schemas,
    agentic_knowledge_strategy_implementation_digest,
    load_ark_chat_conformance_qualification,
)
from software_world_model.application_services import (
    CapabilityDefinition,
    CapabilityRegistry,
    ConversationalTaskControl,
    CurrentEvaluationQualificationVerifier,
    EvaluationQualificationDependencies,
    KnowledgeUpdateService,
    KnowledgeUseService,
    LiveIntegrationPolicy,
    NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
    NATURAL_TASK_CAPABILITY_ID,
    NaturalLanguageTaskService,
    ProductValidatedQualificationVerifier,
    QualificationProof,
    ResponseControlService,
    StrategyActivationService,
    StrategyDefinition,
    StrategyKind,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    TelemetryRecorder,
    digest_of,
)
from software_world_model.infrastructure import (
    SqliteCapabilityEvaluationRepository,
    SqliteDatabase,
    SqliteFormalKnowledgeRepository,
    SqliteKnowledgeScopeRepository,
    SqliteKnowledgeUpdateRepository,
    SqliteKnowledgeUseRepository,
    SqliteModelGatewayRepository,
    SqliteProductValidationRepository,
    SqliteResponseControlRepository,
    SqliteSourceConfigurationRepository,
    SqliteSourceOperationRepository,
    SqliteStrategyActivationRepository,
    SqliteTaskControlRepository,
    SqliteTelemetryRepository,
)
from software_world_model.knowledge_engine import (
    FormalKnowledgeService,
    KnowledgeScopeService,
)
from software_world_model.source_integration import (
    LocalGitConfigurationProvider,
    ProviderRegistry,
    SourceConfigurationService,
    SourceOperationService,
)

from .runtime import ApplicationRuntime


@dataclass(frozen=True, slots=True)
class AgenticTaskServiceAssembly:
    strategy: AgenticKnowledgeStrategyBundle
    knowledge_updates: KnowledgeUpdateService
    knowledge_use: KnowledgeUseService
    task_control: ConversationalTaskControl
    response_control: ResponseControlService
    natural_tasks: NaturalLanguageTaskService


@dataclass(frozen=True, slots=True)
class ActivatedApplicationAssembly:
    runtime: ApplicationRuntime
    task_services: AgenticTaskServiceAssembly
    provider_configuration: VolcengineArkModelConfiguration
    conformance_result_ref: str
    activation_digest: Digest


CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA = (
    "swm.capability-qualification-proof@1"
)


def agentic_task_capability_registry() -> CapabilityRegistry:
    """Create the exact contract registry shared by evaluation and activation."""

    registry = CapabilityRegistry()
    registry.register_capability(
        CapabilityDefinition(
            capability_id=NATURAL_TASK_CAPABILITY_ID,
            contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
            purpose=(
                "Answer an exact-snapshot software question with optional authorized "
                "knowledge investigation and reviewed source-closed output"
            ),
            input_contract_digest=digest_of(
                {
                    "request": "NaturalLanguageTaskRequest@2",
                    "optional_update": "KnowledgeUpdateRequest@1",
                    "initial_update_policy": "REQUIRED_WHEN_SNAPSHOT_ABSENT@1",
                    "snapshot_policy": "EXACT_CURRENT_FOR_UPDATE@1",
                }
            ),
            output_contract_digest=digest_of(
                {
                    "output": "AuthorizedTaskAnswer@1",
                    "delivery": "NOT_PERFORMED",
                }
            ),
        )
    )
    registry.register_strategy(agentic_task_strategy_definition())
    return registry


def agentic_task_strategy_definition() -> StrategyDefinition:
    return StrategyDefinition(
        strategy_id=AGENTIC_KNOWLEDGE_STRATEGY_ID,
        strategy_version=AGENTIC_KNOWLEDGE_STRATEGY_VERSION,
        capability_id=NATURAL_TASK_CAPABILITY_ID,
        capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
        kind=StrategyKind.MODEL_PRIMARY,
        implementation_digest=agentic_knowledge_strategy_implementation_digest(),
        requires_model=True,
    )


def load_capability_qualification_proof(
    path: str | Path,
) -> QualificationProof:
    """Load the sealed qualification document used for explicit activation."""

    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability qualification proof cannot be read",
        ) from exc
    if (
        not isinstance(document, dict)
        or set(document) != {"schema", "proof", "document_digest"}
        or document.get("schema")
        != CAPABILITY_QUALIFICATION_DOCUMENT_SCHEMA
        or not isinstance(document.get("proof"), dict)
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability qualification proof document is invalid",
        )
    core = {"schema": document["schema"], "proof": document["proof"]}
    if document["document_digest"] != digest_of(core).value:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability qualification proof document digest is invalid",
        )
    raw = document["proof"]
    required = {
        "proof_ref",
        "capability_id",
        "capability_contract_version",
        "strategy_id",
        "strategy_version",
        "result_ref",
        "validity_ref",
        "qualification_kind",
        "digest",
    }
    if set(raw) != required or any(
        not isinstance(raw[key], str) for key in required
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability qualification fields are incomplete",
        )
    proof = QualificationProof(
        proof_ref=raw["proof_ref"],
        capability_id=raw["capability_id"],
        capability_contract_version=raw["capability_contract_version"],
        strategy_id=raw["strategy_id"],
        strategy_version=raw["strategy_version"],
        result_ref=raw["result_ref"],
        validity_ref=raw["validity_ref"],
        qualification_kind=raw["qualification_kind"],
        digest=Digest(raw["digest"]),
    )
    if not proof.verify_digest():
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "capability qualification digest is invalid",
        )
    return proof


def activate_browser_experience(
    *,
    database: SqliteDatabase,
    conformance_result_path: str | Path,
    qualification_proof_path: str | Path,
    environment_name: str,
    actor: str,
    reason: str,
):
    """Explicitly activate the evaluated strategy for one local browser scope."""

    provider_configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
        conformance_result_path,
        provider_configuration,
    )
    proof = load_capability_qualification_proof(qualification_proof_path)
    strategy = agentic_task_strategy_definition()
    evaluation_verifier = CurrentEvaluationQualificationVerifier(
        SqliteCapabilityEvaluationRepository(database),
        EvaluationQualificationDependencies(
            strategy_implementation_digest=(
                agentic_knowledge_strategy_implementation_digest()
            ),
            conformance_result_ref=conformance.result_ref,
            provider_configuration_fingerprint=(
                provider_configuration.fingerprint
            ),
            model_ref=provider_configuration.actual_model_fingerprint,
            adapter_version=provider_configuration.adapter_version,
        ),
    )
    verifier = ProductValidatedQualificationVerifier(
        evaluation_verifier,
        SqliteProductValidationRepository(database),
        agentic_knowledge_strategy_implementation_digest(),
    )
    activation = StrategyActivationService(
        SqliteStrategyActivationRepository(database),
        agentic_task_capability_registry(),
        verifier,
        live_policy=LiveIntegrationPolicy(
            model_strategy_activation_enabled=True
        ),
    )
    return activation.activate_strategy(
        capability_id=NATURAL_TASK_CAPABILITY_ID,
        capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
        activation_scope={"environment": environment_name},
        expected_revision=None,
        strategy_id=strategy.strategy_id,
        strategy_version=strategy.strategy_version,
        qualification=proof,
        idempotency_key=IdempotencyKey(
            "activate-browser:"
            + digest_of(
                {
                    "environment": environment_name,
                    "qualification": proof.digest.value,
                    "implementation": strategy.implementation_digest.value,
                }
            ).value[-32:]
        ),
        actor=actor,
        reason=reason,
        correlation_ref=CorrelationRef(
            f"browser-experience-activation:{environment_name}"
        ),
    )


def assemble_activated_task_services(
    *,
    database: SqliteDatabase,
    gateway: ModelGateway,
    model_configuration: AgenticModelStrategyConfiguration,
    activation: StrategyActivationService,
    activation_scope: Mapping[str, str],
    telemetry: TelemetryRecorder | None = None,
) -> AgenticTaskServiceAssembly:
    """Assemble all six roles; NaturalLanguageTaskService rechecks activation."""

    strategy = AgenticKnowledgeStrategyBundle.create(gateway, model_configuration)
    scopes = KnowledgeScopeService(SqliteKnowledgeScopeRepository(database))
    sources = SourceConfigurationService(
        SqliteSourceConfigurationRepository(database),
        ProviderRegistry((LocalGitConfigurationProvider(),)),
        scopes,
    )
    operations = SourceOperationService(
        SqliteSourceOperationRepository(database),
        sources,
        telemetry=telemetry,
    )
    knowledge = FormalKnowledgeService(
        SqliteFormalKnowledgeRepository(database),
        scopes,
        reviewed_fact_verifier=ModelReviewedFactGroundingVerifier(gateway),
    )
    updates = KnowledgeUpdateService(
        SqliteKnowledgeUpdateRepository(database),
        scopes,
        sources,
        operations,
        knowledge,
        builder=strategy.knowledge_builder,
        planner=strategy.source_planner,
    )
    knowledge_use = KnowledgeUseService(
        SqliteKnowledgeUseRepository(database),
        knowledge,
        evaluator=strategy.sufficiency_evaluator,
    )
    task_control = ConversationalTaskControl(SqliteTaskControlRepository(database))
    response_control = ResponseControlService(
        SqliteResponseControlRepository(database),
        task_control,
        knowledge,
        semantic_reviewer=strategy.answer_reviewer,
    )
    natural_tasks = NaturalLanguageTaskService(
        tasks=task_control,
        knowledge=knowledge,
        knowledge_use=knowledge_use,
        responses=response_control,
        requirement_planner=strategy.requirement_planner,
        answer_planner=strategy.answer_planner,
        activation=activation,
        activation_scope=activation_scope,
        knowledge_updates=updates,
    )
    return AgenticTaskServiceAssembly(
        strategy=strategy,
        knowledge_updates=updates,
        knowledge_use=knowledge_use,
        task_control=task_control,
        response_control=response_control,
        natural_tasks=natural_tasks,
    )


def build_activated_application_runtime(
    *,
    database: SqliteDatabase,
    conformance_result_path: str | Path,
    activation_scope: Mapping[str, str],
    environment: Mapping[str, str] | None = None,
    classification: str = "INTERNAL",
    max_output_tokens: int = 1200,
    timeout_milliseconds: int = 180_000,
) -> ActivatedApplicationAssembly:
    """Build a live runtime only from current conformance, evaluation, and activation."""

    provider_configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
        conformance_result_path,
        provider_configuration,
    )
    registry = agentic_task_capability_registry()
    evaluation_repository = SqliteCapabilityEvaluationRepository(database)
    product_validation_repository = SqliteProductValidationRepository(database)
    evaluation_verifier = CurrentEvaluationQualificationVerifier(
        evaluation_repository,
        EvaluationQualificationDependencies(
            strategy_implementation_digest=(
                agentic_knowledge_strategy_implementation_digest()
            ),
            conformance_result_ref=conformance.result_ref,
            provider_configuration_fingerprint=provider_configuration.fingerprint,
            model_ref=provider_configuration.actual_model_fingerprint,
            adapter_version=provider_configuration.adapter_version,
        ),
    )
    qualification_verifier = ProductValidatedQualificationVerifier(
        evaluation_verifier,
        product_validation_repository,
        agentic_knowledge_strategy_implementation_digest(),
    )
    activation = StrategyActivationService(
        SqliteStrategyActivationRepository(database),
        registry,
        qualification_verifier,
        live_policy=LiveIntegrationPolicy(model_strategy_activation_enabled=True),
    )
    resolved = activation.resolve_strategy(
        capability_id=NATURAL_TASK_CAPABILITY_ID,
        capability_contract_version=NATURAL_TASK_CAPABILITY_CONTRACT_VERSION,
        activation_scope=activation_scope,
    )
    qualification = resolved.decision.qualification
    assert qualification is not None
    environment_values = os.environ if environment is None else environment
    transport = UrllibVolcengineArkChatTransport(
        api_key_resolver=lambda: provider_configuration.resolve_api_key(
            environment_values
        )
    )
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=transport,
        configuration=provider_configuration,
        output_schemas=agentic_knowledge_output_schemas(),
        live_qualification=conformance,
    )
    telemetry = SqliteTelemetryRepository(database)
    gateway = ModelGateway(
        SqliteModelGatewayRepository(database),
        (adapter,),
        telemetry=telemetry,
    )
    model_configuration = AgenticModelStrategyConfiguration(
        provider_type=provider_configuration.provider_type,
        adapter_version=provider_configuration.adapter_version,
        model_ref=provider_configuration.model_ref,
        provider_configuration_fingerprint=provider_configuration.fingerprint,
        qualification_ref=qualification.proof_ref,
        max_output_tokens=max_output_tokens,
        timeout_milliseconds=timeout_milliseconds,
        classification=classification,
    )
    task_services = assemble_activated_task_services(
        database=database,
        gateway=gateway,
        model_configuration=model_configuration,
        activation=activation,
        activation_scope=activation_scope,
        telemetry=telemetry,
    )
    runtime = ApplicationRuntime(
        database,
        telemetry=telemetry,
        natural_task_service=task_services.natural_tasks,
    )
    return ActivatedApplicationAssembly(
        runtime=runtime,
        task_services=task_services,
        provider_configuration=provider_configuration,
        conformance_result_ref=conformance.result_ref,
        activation_digest=resolved.decision.digest,
    )
