"""Trusted composition for an exactly authorized DeepSeek Engineering QA run.

Construction is credential-lazy: the supplied transport owns late credential
resolution and this module never reads or stores a key.  A caller must first
freeze one immutable Request and its user run-disclosure authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekChatCompletionsNoToolsAdapter,
    DeepSeekChatCompletionsTransport,
    DeepSeekModelConfiguration,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    DeepSeekChatConformanceQualification,
)
from software_world_model.ai_infrastructure.engineering_question_model_source import (
    EngineeringQuestionModelConfiguration,
    EngineeringQuestionModelEgressPolicy,
    EngineeringQuestionRunDisclosureAuthorization,
    ModelBackedEngineeringQuestionStructuredOutputSource,
    PolicyEnforcingEngineeringQuestionModelGateway,
    SealedEngineeringQuestionRoleDisclosureAuthorizer,
)
from software_world_model.ai_infrastructure.engineering_question_strategy import (
    EngineeringQuestionStructuredStrategyBundle,
    engineering_question_output_schemas,
)
from software_world_model.ai_infrastructure.model_gateway import (
    ModelGateway,
    ModelGatewayRepository,
)
from software_world_model.cross_cutting import DomainError, ErrorCode
from software_world_model.application_services.engineering_question_answering import (
    EngineeringQuestionAnsweringService,
    EngineeringQuestionRequest,
    RetrievalWorker,
    SourceBroker,
    WorldModelCognitionProjector,
)
from .engineering_qa_browser import (
    EngineeringQuestionBrowserApplication,
    EngineeringQuestionWebRuntimeStatus,
    ExactAuthorizedEngineeringQuestionRequestFactory,
    InMemoryEngineeringQuestionWebProduct,
)


@dataclass(frozen=True, slots=True)
class DeepSeekEngineeringQuestionRoleRuntime:
    configuration: EngineeringQuestionModelConfiguration
    adapter: DeepSeekChatCompletionsNoToolsAdapter
    gateway: ModelGateway
    policy: EngineeringQuestionModelEgressPolicy
    authorizer: SealedEngineeringQuestionRoleDisclosureAuthorizer
    output_source: ModelBackedEngineeringQuestionStructuredOutputSource
    strategy: EngineeringQuestionStructuredStrategyBundle


@dataclass(frozen=True, slots=True)
class DeepSeekEngineeringQuestionBrowserAssembly:
    role_runtime: DeepSeekEngineeringQuestionRoleRuntime
    service: EngineeringQuestionAnsweringService
    product: InMemoryEngineeringQuestionWebProduct
    application: EngineeringQuestionBrowserApplication


def engineering_question_deepseek_configuration(
    *,
    provider_configuration: DeepSeekModelConfiguration,
    qualification: DeepSeekChatConformanceQualification,
    maximum_output_tokens: int = 4_096,
    timeout_milliseconds: int = 180_000,
    maximum_calls: int = 24,
    at: datetime | None = None,
) -> EngineeringQuestionModelConfiguration:
    current = at or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering QA DeepSeek composition time must be timezone-aware",
        )
    if (
        qualification.adapter_version != provider_configuration.adapter_version
        or qualification.provider_configuration_fingerprint
        != provider_configuration.fingerprint
        or qualification.qualified_model_fingerprints
        != provider_configuration.qualified_model_identities
        or current.astimezone(timezone.utc)
        >= qualification.valid_until.astimezone(timezone.utc)
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek qualification does not bind the exact Engineering QA Provider configuration",
        )
    return EngineeringQuestionModelConfiguration(
        provider_type=provider_configuration.provider_type,
        adapter_version=provider_configuration.adapter_version,
        endpoint=provider_configuration.endpoint,
        model_ref=provider_configuration.model_ref,
        expected_actual_model_fingerprint=(
            provider_configuration.actual_model_fingerprint
        ),
        provider_configuration_fingerprint=provider_configuration.fingerprint,
        secret_reference=provider_configuration.secret_reference,
        qualification_ref=qualification.result_ref,
        qualification_valid_until=qualification.valid_until,
        maximum_output_tokens=maximum_output_tokens,
        timeout_milliseconds=timeout_milliseconds,
        maximum_calls=maximum_calls,
    )


def create_deepseek_engineering_question_role_runtime(
    *,
    repository: ModelGatewayRepository,
    transport: DeepSeekChatCompletionsTransport,
    provider_configuration: DeepSeekModelConfiguration,
    qualification: DeepSeekChatConformanceQualification,
    run_authorization: EngineeringQuestionRunDisclosureAuthorization,
    configuration: EngineeringQuestionModelConfiguration | None = None,
    clock: Callable[[], datetime] | None = None,
) -> DeepSeekEngineeringQuestionRoleRuntime:
    runtime_clock = clock or (lambda: datetime.now(timezone.utc))
    current = runtime_clock()
    expected_configuration = engineering_question_deepseek_configuration(
        provider_configuration=provider_configuration,
        qualification=qualification,
        maximum_output_tokens=(
            configuration.maximum_output_tokens if configuration else 4_096
        ),
        timeout_milliseconds=(
            configuration.timeout_milliseconds if configuration else 180_000
        ),
        maximum_calls=(configuration.maximum_calls if configuration else 24),
        at=current,
    )
    if configuration is not None and configuration != expected_configuration:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Engineering QA model configuration drifts from the exact DeepSeek binding",
        )
    configuration = expected_configuration
    run_authorization.require_current(
        configuration=configuration,
        at=current,
    )
    adapter = DeepSeekChatCompletionsNoToolsAdapter(
        transport=transport,
        configuration=provider_configuration,
        output_schemas=engineering_question_output_schemas(),
        live_qualification=qualification,
    )
    gateway = ModelGateway(repository, (adapter,), clock=runtime_clock)
    policy = EngineeringQuestionModelEgressPolicy(
        run_authorization=run_authorization,
        configuration=configuration,
        clock=runtime_clock,
    )
    protected_gateway = PolicyEnforcingEngineeringQuestionModelGateway(
        gateway=gateway,
        policy=policy,
    )
    authorizer = SealedEngineeringQuestionRoleDisclosureAuthorizer(
        run_authorization=run_authorization,
        configuration=configuration,
        clock=runtime_clock,
    )
    output_source = ModelBackedEngineeringQuestionStructuredOutputSource(
        gateway=protected_gateway,
        configuration=configuration,
        authorizer=authorizer,
        clock=runtime_clock,
    )
    return DeepSeekEngineeringQuestionRoleRuntime(
        configuration=configuration,
        adapter=adapter,
        gateway=gateway,
        policy=policy,
        authorizer=authorizer,
        output_source=output_source,
        strategy=EngineeringQuestionStructuredStrategyBundle.create(output_source),
    )


def create_deepseek_engineering_question_browser_assembly(
    *,
    request: EngineeringQuestionRequest,
    role_runtime: DeepSeekEngineeringQuestionRoleRuntime,
    run_authorization: EngineeringQuestionRunDisclosureAuthorization,
    cognition_projector: WorldModelCognitionProjector,
    source_broker: SourceBroker,
    retrieval_worker: RetrievalWorker,
    at: datetime,
) -> DeepSeekEngineeringQuestionBrowserAssembly:
    run_authorization.require_current(
        configuration=role_runtime.configuration,
        at=at,
    )
    if request.digest != run_authorization.request_digest:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering QA browser Request is not the role runtime's authorized Request",
        )
    strategy = role_runtime.strategy
    service = EngineeringQuestionAnsweringService(
        question_understanding_role=strategy.question_understanding,
        cognition_projector=cognition_projector,
        initial_investigation_role=strategy.initial_investigation,
        verification_investigation_role=strategy.verification_investigation,
        source_broker=source_broker,
        retrieval_worker=retrieval_worker,
        answer_role=strategy.answer,
        reviewer_role=strategy.reviewer,
    )
    request_factory = ExactAuthorizedEngineeringQuestionRequestFactory(
        request=request,
        run_authorization=run_authorization,
    )
    runtime_status = EngineeringQuestionWebRuntimeStatus.authorized(
        request=request,
        configuration=role_runtime.configuration,
        run_authorization=run_authorization,
        at=at,
    )
    product = InMemoryEngineeringQuestionWebProduct(
        service=service,
        request_factory=request_factory,
        runtime_status=runtime_status,
    )
    return DeepSeekEngineeringQuestionBrowserAssembly(
        role_runtime=role_runtime,
        service=service,
        product=product,
        application=EngineeringQuestionBrowserApplication(product),
    )
