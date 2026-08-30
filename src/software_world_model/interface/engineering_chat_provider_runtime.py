"""Credential-lazy live Provider runtimes for the Engineering Chat Agent.

The functions in this module accept already verified Ark or DeepSeek
Conformance qualifications and bind the existing live Adapter, direct HTTPS
transport, Model Gateway, session disclosure authorizer, and conversational
Agent model boundary.  Construction does not resolve a credential, open a
network connection, prepare a Gateway call, read Source, or start a listener.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable

from software_world_model.ai_infrastructure.ark_chat_conformance import (
    ARK_CHAT_CONFORMANCE_FIXTURE_ID,
    ArkChatConformanceQualification,
)
from software_world_model.ai_infrastructure.conversational_engineering_model import (
    EngineeringAgentModelConfiguration,
    EngineeringAgentSessionDisclosureAuthority,
    ModelBackedConversationalEngineeringAgent,
    PolicyEnforcingEngineeringAgentModelGateway,
    SealedEngineeringAgentRoleDisclosureAuthorizer,
    engineering_agent_output_schemas,
)
from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DeepSeekChatCompletionsNoToolsAdapter,
    DeepSeekModelConfiguration,
    PersistentDeepSeekChatTransport,
)
from software_world_model.ai_infrastructure.deepseek_chat_conformance import (
    DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID,
    DeepSeekChatConformanceQualification,
)
from software_world_model.ai_infrastructure.model_gateway import (
    AdapterConformanceLevel,
    ModelGateway,
    ModelExecutionContext,
    ModelGatewayResult,
    ModelGatewayRepository,
)
from software_world_model.ai_infrastructure.provider_http_failure_evidence import (
    ProviderHTTPFailureCapturingAdapter,
    ProviderHTTPFailureEvidenceGateway,
)
from software_world_model.ai_infrastructure.volcengine_ark_chat_adapter import (
    DirectVerifiedVolcengineArkChatTransport,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    digest_of,
)
from software_world_model.application_services.engineering_conversation import (
    EngineeringChatBinding,
    RuntimeCapabilityStatus,
)
from software_world_model.application_services.deepseek_dispatch_admission import (
    DeepSeekDispatchAdmissionController,
)

from .engineering_chat_provider_launcher import (
    EngineeringChatProviderAttemptDependencies,
    ResponseControlFactory,
    ToolFactory,
)


ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_SCHEMA = (
    "SWM-ENGINEERING-CHAT-PROVIDER-MODEL-RUNTIME@1"
)
ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_STATUS = (
    "QUALIFIED_PROVIDER_RUNTIME_BOUND_NOT_DISPATCHED"
)
ENGINEERING_CHAT_ARK_TRANSPORT_REF = (
    "VOLCENGINE_ARK_DIRECT_VERIFIED_HTTPS_NO_RETRY@1"
)
ENGINEERING_CHAT_DEEPSEEK_TRANSPORT_REF = (
    "DEEPSEEK_PERSISTENT_VERIFIED_TLS_HTTP11_NO_RETRY@2"
)


@dataclass(frozen=True, slots=True)
class EngineeringChatProviderModelRuntime:
    """One Provider-scoped model boundary prepared without external I/O."""

    schema: str
    status: str
    provider_type: str
    chat_binding_digest: Digest
    configuration: EngineeringAgentModelConfiguration
    session_authority: EngineeringAgentSessionDisclosureAuthority
    qualification_result_ref: str
    qualification_result_digest: Digest
    gateway_repository_ref: str
    transport_ref: str
    adapter: object
    transport: object
    gateway: object
    authorizer: SealedEngineeringAgentRoleDisclosureAuthorizer
    model_boundary: ModelBackedConversationalEngineeringAgent
    dispatch_admission_controller: DeepSeekDispatchAdmissionController | None
    credential_resolved_at_preparation: bool
    provider_dispatch_count_at_preparation: int
    request_retry_allowed: bool
    production_activation: str
    digest: Digest

    def public_status(self) -> dict[str, object]:
        """Return a credential-reference-free preparation receipt view."""

        return {
            "schema": self.schema,
            "status": self.status,
            "provider_type": self.provider_type,
            "chat_binding_digest": self.chat_binding_digest.value,
            "model_ref": self.configuration.model_ref,
            "provider_configuration_digest": self.configuration.digest.value,
            "session_disclosure_authority_digest": (
                self.session_authority.digest.value
            ),
            "qualification_result_ref": self.qualification_result_ref,
            "qualification_result_digest": self.qualification_result_digest.value,
            "gateway_repository_ref": self.gateway_repository_ref,
            "transport_ref": self.transport_ref,
            "dispatch_admission": (
                self.dispatch_admission_controller.receipt.public_status()
                if self.dispatch_admission_controller is not None
                else None
            ),
            "credential_resolved_at_preparation": (
                self.credential_resolved_at_preparation
            ),
            "provider_dispatch_count_at_preparation": (
                self.provider_dispatch_count_at_preparation
            ),
            "request_retry_allowed": self.request_retry_allowed,
            "production_activation": self.production_activation,
            "runtime_digest": self.digest.value,
        }

    def attempt_dependencies(
        self,
        *,
        route,
        tool_factory: ToolFactory,
        response_control_factory: ResponseControlFactory,
        response_control_ref: str,
    ) -> EngineeringChatProviderAttemptDependencies:
        """Bind this runtime to one exact route and lazy attempt factories."""

        return EngineeringChatProviderAttemptDependencies.create(
            route=route,
            configuration=self.configuration,
            session_authority=self.session_authority,
            model_boundary_ref=(
                f"engineering-agent-model-boundary:{self.digest.value}"
            ),
            model_gateway_repository_ref=self.gateway_repository_ref,
            disclosure_authorizer_ref=(
                "engineering-agent-disclosure-authorizer:"
                + self.session_authority.digest.value
            ),
            response_control_ref=response_control_ref,
            driver=self.model_boundary,
            reviewer=self.model_boundary,
            tool_factory=tool_factory,
            response_control_factory=response_control_factory,
        )


def engineering_chat_ark_model_configuration(
    *,
    provider_configuration: VolcengineArkModelConfiguration,
    qualification: ArkChatConformanceQualification,
    at: datetime,
    maximum_output_tokens: int = 8_192,
    timeout_milliseconds: int = 180_000,
    maximum_calls: int = 75,
) -> EngineeringAgentModelConfiguration:
    """Translate one verified Ark identity into the Agent model contract."""

    return _engineering_agent_model_configuration(
        provider_type=provider_configuration.provider_type,
        adapter_version=provider_configuration.adapter_version,
        endpoint=provider_configuration.endpoint,
        model_ref=provider_configuration.model_ref,
        actual_model_fingerprint=(
            provider_configuration.actual_model_fingerprint
        ),
        provider_configuration_fingerprint=provider_configuration.fingerprint,
        secret_reference=provider_configuration.secret_reference,
        qualification=qualification,
        fixture_id=ARK_CHAT_CONFORMANCE_FIXTURE_ID,
        qualified_model_identities=(
            provider_configuration.qualified_model_identities
        ),
        at=at,
        maximum_output_tokens=maximum_output_tokens,
        timeout_milliseconds=timeout_milliseconds,
        maximum_calls=maximum_calls,
    )


def engineering_chat_deepseek_model_configuration(
    *,
    provider_configuration: DeepSeekModelConfiguration,
    qualification: DeepSeekChatConformanceQualification,
    at: datetime,
    maximum_output_tokens: int = 8_192,
    timeout_milliseconds: int = 180_000,
    maximum_calls: int = 75,
) -> EngineeringAgentModelConfiguration:
    """Translate one verified DeepSeek identity into the Agent model contract."""

    return _engineering_agent_model_configuration(
        provider_type=provider_configuration.provider_type,
        adapter_version=provider_configuration.adapter_version,
        endpoint=provider_configuration.endpoint,
        model_ref=provider_configuration.model_ref,
        actual_model_fingerprint=(
            provider_configuration.actual_model_fingerprint
        ),
        provider_configuration_fingerprint=provider_configuration.fingerprint,
        secret_reference=provider_configuration.secret_reference,
        qualification=qualification,
        fixture_id=DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_ID,
        qualified_model_identities=(
            provider_configuration.qualified_model_identities
        ),
        at=at,
        maximum_output_tokens=maximum_output_tokens,
        timeout_milliseconds=timeout_milliseconds,
        maximum_calls=maximum_calls,
    )


def create_ark_engineering_chat_provider_model_runtime(
    *,
    repository: ModelGatewayRepository,
    gateway_repository_ref: str,
    binding: EngineeringChatBinding,
    provider_configuration: VolcengineArkModelConfiguration,
    qualification: ArkChatConformanceQualification,
    configuration: EngineeringAgentModelConfiguration,
    session_authority: EngineeringAgentSessionDisclosureAuthority,
    at: datetime,
    clock: Callable[[], datetime] | None = None,
) -> EngineeringChatProviderModelRuntime:
    """Prepare the exact Ark live Adapter and transport without dispatch."""

    current = _aware_utc(at)
    expected = engineering_chat_ark_model_configuration(
        provider_configuration=provider_configuration,
        qualification=qualification,
        at=current,
        maximum_output_tokens=configuration.maximum_output_tokens,
        timeout_milliseconds=configuration.timeout_milliseconds,
        maximum_calls=configuration.maximum_calls,
    )
    if configuration != expected:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Engineering Chat Ark model configuration drifted from Conformance",
        )
    transport = DirectVerifiedVolcengineArkChatTransport(
        api_key_resolver=provider_configuration.resolve_api_key
    )
    adapter = VolcengineArkChatCompletionsNoToolsAdapter(
        transport=transport,
        configuration=provider_configuration,
        output_schemas=engineering_agent_output_schemas(),
        live_qualification=qualification,
    )
    return _provider_runtime(
        repository=repository,
        gateway_repository_ref=gateway_repository_ref,
        binding=binding,
        transport_ref=ENGINEERING_CHAT_ARK_TRANSPORT_REF,
        configuration=configuration,
        session_authority=session_authority,
        qualification_result_ref=qualification.result_ref,
        qualification_result_digest=qualification.result_digest,
        adapter=adapter,
        transport=transport,
        dispatch_admission_controller=None,
        at=current,
        clock=clock,
    )


def create_deepseek_engineering_chat_provider_model_runtime(
    *,
    repository: ModelGatewayRepository,
    gateway_repository_ref: str,
    binding: EngineeringChatBinding,
    provider_configuration: DeepSeekModelConfiguration,
    qualification: DeepSeekChatConformanceQualification,
    configuration: EngineeringAgentModelConfiguration,
    session_authority: EngineeringAgentSessionDisclosureAuthority,
    dispatch_admission_controller: DeepSeekDispatchAdmissionController,
    at: datetime,
    clock: Callable[[], datetime] | None = None,
) -> EngineeringChatProviderModelRuntime:
    """Prepare the exact DeepSeek live Adapter and transport without dispatch."""

    current = _aware_utc(at)
    expected = engineering_chat_deepseek_model_configuration(
        provider_configuration=provider_configuration,
        qualification=qualification,
        at=current,
        maximum_output_tokens=configuration.maximum_output_tokens,
        timeout_milliseconds=configuration.timeout_milliseconds,
        maximum_calls=configuration.maximum_calls,
    )
    if configuration != expected:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Engineering Chat DeepSeek model configuration drifted from Conformance",
        )
    transport = PersistentDeepSeekChatTransport(
        api_key_resolver=provider_configuration.resolve_api_key
    )
    adapter = DeepSeekChatCompletionsNoToolsAdapter(
        transport=transport,
        configuration=provider_configuration,
        output_schemas=engineering_agent_output_schemas(),
        live_qualification=qualification,
    )
    return _provider_runtime(
        repository=repository,
        gateway_repository_ref=gateway_repository_ref,
        binding=binding,
        transport_ref=ENGINEERING_CHAT_DEEPSEEK_TRANSPORT_REF,
        configuration=configuration,
        session_authority=session_authority,
        qualification_result_ref=qualification.result_ref,
        qualification_result_digest=qualification.result_digest,
        adapter=adapter,
        transport=transport,
        dispatch_admission_controller=dispatch_admission_controller,
        at=current,
        clock=clock,
    )


def _engineering_agent_model_configuration(
    *,
    provider_type: str,
    adapter_version: str,
    endpoint: str,
    model_ref: str,
    actual_model_fingerprint: str,
    provider_configuration_fingerprint: Digest,
    secret_reference: str,
    qualification,
    fixture_id: str,
    qualified_model_identities: tuple[str, ...],
    at: datetime,
    maximum_output_tokens: int,
    timeout_milliseconds: int,
    maximum_calls: int,
) -> EngineeringAgentModelConfiguration:
    current = _aware_utc(at)
    if (
        qualification.result_ref
        != f"{fixture_id}:{qualification.result_digest.value}"
        or qualification.qualified_model_fingerprints
        != qualified_model_identities
        or qualification.adapter_version != adapter_version
        or qualification.provider_configuration_fingerprint
        != provider_configuration_fingerprint
        or qualification.valid_until.tzinfo is None
        or qualification.valid_until.utcoffset() is None
        or current >= qualification.valid_until.astimezone(timezone.utc)
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Engineering Chat Provider Conformance identity is invalid or stale",
        )
    configuration = EngineeringAgentModelConfiguration(
        provider_type=provider_type,
        adapter_version=adapter_version,
        endpoint=endpoint,
        model_ref=model_ref,
        expected_actual_model_fingerprint=actual_model_fingerprint,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        secret_reference=secret_reference,
        qualification_ref=qualification.result_ref,
        qualification_valid_until=qualification.valid_until,
        maximum_output_tokens=maximum_output_tokens,
        timeout_milliseconds=timeout_milliseconds,
        maximum_calls=maximum_calls,
    )
    configuration.require_current(current)
    return configuration


def _provider_runtime(
    *,
    repository: ModelGatewayRepository,
    gateway_repository_ref: str,
    binding: EngineeringChatBinding,
    transport_ref: str,
    configuration: EngineeringAgentModelConfiguration,
    session_authority: EngineeringAgentSessionDisclosureAuthority,
    qualification_result_ref: str,
    qualification_result_digest: Digest,
    adapter,
    transport,
    dispatch_admission_controller: DeepSeekDispatchAdmissionController | None,
    at: datetime,
    clock: Callable[[], datetime] | None,
) -> EngineeringChatProviderModelRuntime:
    gateway_repository_ref = _text(
        gateway_repository_ref, "Model Gateway repository reference"
    )
    transport_ref = _text(transport_ref, "Provider transport reference")
    for name in (
        "recover",
        "prepare",
        "transition",
        "get",
        "recover_by_id",
        "get_manifest",
    ):
        if not callable(getattr(repository, name, None)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Engineering Chat Provider runtime requires a Model Gateway repository",
            )
    configuration.require_current(at)
    if (
        binding.provider_status is not RuntimeCapabilityStatus.READY
        or binding.world_model_status is not RuntimeCapabilityStatus.READY
        or binding.source_access_status is not RuntimeCapabilityStatus.READY
        or binding.provider_route_ref is None
    ):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Engineering Chat Provider runtime requires one ready exact Chat binding",
        )
    session_authority.require_current(
        configuration=configuration,
        chat_binding_digest=binding.digest,
        at=at,
    )
    if configuration.provider_type == "DEEPSEEK":
        if not isinstance(
            dispatch_admission_controller,
            DeepSeekDispatchAdmissionController,
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "DeepSeek runtime requires a sealed dispatch admission controller",
            )
        admission_plan = dispatch_admission_controller.plan
        if (
            admission_plan.product_revision != binding.product_revision
            or admission_plan.source_revision != binding.repository_revision
            or admission_plan.session_ref != session_authority.session_ref
            or admission_plan.provider_configuration_digest
            != configuration.digest
            or admission_plan.model_ref != configuration.model_ref
            or admission_plan.authorization_message_digest
            != session_authority.authorization_message_digest
            or admission_plan.authorized_at != session_authority.authorized_at
            or admission_plan.expires_at != session_authority.expires_at
            or admission_plan.maximum_calls
            != session_authority.maximum_total_dispatches
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "DeepSeek dispatch admission does not bind the exact runtime Session",
            )
    elif dispatch_admission_controller is not None:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "non-DeepSeek runtime cannot consume DeepSeek dispatch admission",
        )
    capabilities = getattr(adapter, "capabilities", None)
    expected_model_fingerprints = tuple(
        dict.fromkeys(
            (
                configuration.model_ref,
                configuration.expected_actual_model_fingerprint,
            )
        )
    )
    if (
        capabilities is None
        or capabilities.conformance_level is not AdapterConformanceLevel.LIVE_CURRENT
        or capabilities.conformance_result_ref != qualification_result_ref
        or capabilities.qualified_model_fingerprints
        != expected_model_fingerprints
        or not capabilities.no_external_access
        or not capabilities.hidden_context_disabled
        or not capabilities.stateless_session
        or not capabilities.structured_output
        or not capabilities.actual_fingerprint_reported
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Engineering Chat live Adapter capabilities do not match Conformance",
        )
    runtime_clock = clock or (lambda: datetime.now(timezone.utc))
    capturing_adapter = ProviderHTTPFailureCapturingAdapter(adapter)
    raw_gateway = ProviderHTTPFailureEvidenceGateway(
        gateway=ModelGateway(
            repository,
            (capturing_adapter,),
            clock=runtime_clock,
        ),
        adapter=capturing_adapter,
        repository=repository,
    )
    gateway = (
        _DeepSeekAdmissionEnforcingGateway(
            gateway=raw_gateway,
            controller=dispatch_admission_controller,
        )
        if dispatch_admission_controller is not None
        else raw_gateway
    )
    authorizer = SealedEngineeringAgentRoleDisclosureAuthorizer(
        session_authority=session_authority,
        configuration=configuration,
        clock=runtime_clock,
    )
    protected = PolicyEnforcingEngineeringAgentModelGateway(
        gateway=gateway,
        configuration=configuration,
        authorizer=authorizer,
    )
    boundary = ModelBackedConversationalEngineeringAgent(
        gateway=protected,
        configuration=configuration,
        authorizer=authorizer,
        clock=runtime_clock,
    )
    core = {
        "schema": ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_SCHEMA,
        "status": ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_STATUS,
        "provider_type": configuration.provider_type,
        "chat_binding_digest": binding.digest.value,
        "provider_configuration_digest": configuration.digest.value,
        "session_disclosure_authority_digest": session_authority.digest.value,
        "qualification_result_ref": qualification_result_ref,
        "qualification_result_digest": qualification_result_digest.value,
        "gateway_repository_ref": gateway_repository_ref,
        "transport_ref": transport_ref,
        "model_boundary": "MODEL_BACKED_CONVERSATIONAL_ENGINEERING_AGENT@1",
        "dispatch_admission_receipt_digest": (
            dispatch_admission_controller.receipt.digest.value
            if dispatch_admission_controller is not None
            else None
        ),
        "credential_resolved_at_preparation": False,
        "provider_dispatch_count_at_preparation": 0,
        "request_retry_allowed": False,
        "production_activation": "NOT_EXECUTED",
    }
    return EngineeringChatProviderModelRuntime(
        schema=ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_SCHEMA,
        status=ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_STATUS,
        provider_type=configuration.provider_type,
        chat_binding_digest=binding.digest,
        configuration=configuration,
        session_authority=session_authority,
        qualification_result_ref=qualification_result_ref,
        qualification_result_digest=qualification_result_digest,
        gateway_repository_ref=gateway_repository_ref,
        transport_ref=transport_ref,
        adapter=adapter,
        transport=transport,
        gateway=gateway,
        authorizer=authorizer,
        model_boundary=boundary,
        dispatch_admission_controller=dispatch_admission_controller,
        credential_resolved_at_preparation=False,
        provider_dispatch_count_at_preparation=0,
        request_retry_allowed=False,
        production_activation="NOT_EXECUTED",
        digest=digest_of(core),
    )


class _DeepSeekAdmissionEnforcingGateway:
    """Enforce the run receipt before the generic Gateway can reach transport."""

    def __init__(
        self,
        *,
        gateway: object,
        controller: DeepSeekDispatchAdmissionController,
    ) -> None:
        self._gateway = gateway
        self._controller = controller

    def preflight(self, context: ModelExecutionContext) -> None:
        self._gateway.preflight(context)
        if context.provider_type != "DEEPSEEK":
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "DeepSeek admission gateway received another Provider",
            )
        input_token_upper_bound = sum(
            len(item.content.encode("utf-8")) for item in context.manifest.items
        )
        self._controller.authorize_dispatch(
            execution_envelope_ref=context.execution_envelope_ref,
            input_token_upper_bound=max(1, input_token_upper_bound),
            maximum_output_tokens=context.max_output_tokens,
        )

    def invoke(self, context: ModelExecutionContext) -> ModelGatewayResult:
        self.preflight(context)
        self._controller.mark_invoked(context.execution_envelope_ref)
        return self._gateway.invoke(context)


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat Provider runtime time must be timezone-aware",
        )
    return value.astimezone(timezone.utc)


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value.strip()


__all__ = [
    "ENGINEERING_CHAT_ARK_TRANSPORT_REF",
    "ENGINEERING_CHAT_DEEPSEEK_TRANSPORT_REF",
    "ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_SCHEMA",
    "ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_STATUS",
    "EngineeringChatProviderModelRuntime",
    "create_ark_engineering_chat_provider_model_runtime",
    "create_deepseek_engineering_chat_provider_model_runtime",
    "engineering_chat_ark_model_configuration",
    "engineering_chat_deepseek_model_configuration",
]
