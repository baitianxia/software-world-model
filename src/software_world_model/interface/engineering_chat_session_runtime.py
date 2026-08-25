"""Non-starting full Session composition for the Engineering Chat Alpha.

This layer joins already prepared Provider model runtimes with the trusted
World Model/Source evidence runtime, fresh attempt-scoped tools and Response
Control, the Ark-to-DeepSeek route, Conversation service, and Browser
application.  It does not load artifact files, read Source, create a Provider
attempt, resolve credentials, dispatch, or open the listener.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from software_world_model.application_services.conversational_engineering_agent import (
    EngineeringAgentLoopLimits,
    SealedEngineeringAgentResponseControl,
)
from software_world_model.application_services.conversational_engineering_routing import (
    EngineeringProviderAttemptAuthority,
    EngineeringProviderRoutePlan,
)
from software_world_model.application_services.conversational_engineering_tools import (
    EngineeringAgentEvidenceToolAdapter,
    EngineeringAgentEvidenceToolConfiguration,
)
from software_world_model.application_services.engineering_conversation import (
    EngineeringChatBinding,
    RuntimeCapabilityStatus,
)
from software_world_model.application_services.engineering_question_answering import (
    RetrievalWorker,
    SourceBroker,
    WorldModelCognitionProjector,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    digest_of,
)

from .engineering_chat_provider_launcher import (
    ENGINEERING_CHAT_PROVIDER_OPERATIONS,
    EngineeringChatProviderAttemptFactory,
    PreparedEngineeringChatProviderLauncher,
    prepare_engineering_chat_provider_launcher,
)
from .engineering_chat_provider_runtime import (
    ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_STATUS,
    EngineeringChatProviderModelRuntime,
)


ENGINEERING_CHAT_SESSION_RUNTIME_SCHEMA = (
    "SWM-ENGINEERING-CHAT-SESSION-RUNTIME@2"
)
ENGINEERING_CHAT_SESSION_RUNTIME_STATUS = (
    "SESSION_RUNTIME_COMPOSITION_LOCAL_CANDIDATE"
)
ENGINEERING_CHAT_ARTIFACT_SESSION_RUNTIME_STATUS = (
    "ARTIFACT_SESSION_COMPOSITION_LOCAL_CANDIDATE"
)
ENGINEERING_CHAT_FIXED_ARTIFACT_SESSION_RUNTIME_STATUS = (
    "ARTIFACT_SESSION_FIXED_COMMAND_LOCAL_CANDIDATE"
)
ENGINEERING_CHAT_SESSION_RUNTIME_BLOCKING_GAPS = (
    "CURRENT_SEALED_ARTIFACT_SESSION_CONFIG_NOT_LOADED",
    "FIXED_COMMAND_NOT_WIRED",
    "LIVE_PROVIDER_AND_BROWSER_NOT_EXECUTED",
)
ENGINEERING_CHAT_ARTIFACT_SESSION_RUNTIME_BLOCKING_GAPS = (
    "FIXED_COMMAND_NOT_WIRED",
    "LIVE_PROVIDER_AND_BROWSER_NOT_EXECUTED",
)
ENGINEERING_CHAT_FIXED_ARTIFACT_SESSION_RUNTIME_BLOCKING_GAPS = (
    "ARK_TRANSPORT_SESSION_AUDIT_NOT_WIRED",
    "LIVE_PROVIDER_AND_BROWSER_NOT_EXECUTED",
)


class EngineeringChatEvidenceToolFactory:
    """Create one fresh evidence adapter for each exact Provider attempt."""

    def __init__(
        self,
        *,
        binding: EngineeringChatBinding,
        configuration: EngineeringAgentEvidenceToolConfiguration,
        cognition_projector: WorldModelCognitionProjector,
        source_broker: SourceBroker,
        retrieval_worker: RetrievalWorker,
    ) -> None:
        if (
            binding.world_model_status is not RuntimeCapabilityStatus.READY
            or binding.source_access_status is not RuntimeCapabilityStatus.READY
            or binding.world_model_authority_digest
            != configuration.world_model_read_authority_digest
            or binding.source_profile_ref != configuration.source_profile_ref
            or binding.project_name != configuration.project_name
            or binding.repository_revision != configuration.repository_revision
            or not set(configuration.excluded_source_paths).issubset(
                binding.excluded_source_paths
            )
            or not callable(getattr(cognition_projector, "project", None))
            or not callable(
                getattr(source_broker, "registered_evidence_classes", None)
            )
            or not callable(getattr(source_broker, "compile", None))
            or not callable(getattr(retrieval_worker, "execute", None))
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Chat evidence runtime does not bind the exact Chat",
            )
        projector_authority = getattr(
            cognition_projector, "read_authority_digest", None
        )
        projector_revision = getattr(cognition_projector, "source_revision", None)
        projector_binding = getattr(cognition_projector, "binding_id", None)
        if (
            projector_authority
            != configuration.world_model_read_authority_digest
            or projector_revision != configuration.repository_revision
            or projector_binding != configuration.binding_id
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Chat cognition projector identity drifted",
            )
        if (
            getattr(source_broker, "binding_id", None)
            != configuration.binding_id
            or getattr(source_broker, "source_profile_ref", None)
            != configuration.source_profile_ref
            or getattr(source_broker, "source_profile_digest", None)
            != configuration.source_profile_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Chat Source Broker identity drifted",
            )
        if (
            getattr(retrieval_worker, "repository_id", None)
            != configuration.repository_id
            or getattr(retrieval_worker, "binding_id", None)
            != configuration.binding_id
            or getattr(retrieval_worker, "source_profile_ref", None)
            != configuration.source_profile_ref
            or getattr(retrieval_worker, "source_profile_digest", None)
            != configuration.source_profile_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Engineering Chat Retrieval Worker identity drifted",
            )
        self.binding = binding
        self.configuration = configuration
        self._cognition_projector = cognition_projector
        self._source_broker = source_broker
        self._retrieval_worker = retrieval_worker
        self._issued_authorities: set[Digest] = set()
        self._created_tools: list[EngineeringAgentEvidenceToolAdapter] = []
        self._lock = Lock()
        self.digest = digest_of(
            {
                "schema": "ENGINEERING_CHAT_EVIDENCE_TOOL_FACTORY@1",
                "chat_binding_digest": binding.digest.value,
                "evidence_tool_configuration_digest": configuration.digest.value,
                "world_model_authority_digest": (
                    configuration.world_model_read_authority_digest.value
                ),
                "source_profile_ref": configuration.source_profile_ref,
                "attempt_tool_lifetime": "FRESH_PER_PROVIDER_ATTEMPT",
                "shared_source_runtime": "READ_ONLY_TRUSTED_CONTROL_PLANE",
                "source_read_performed_at_preparation": False,
            }
        )

    @property
    def created_tool_count(self) -> int:
        with self._lock:
            return len(self._created_tools)

    def __call__(
        self, authority: EngineeringProviderAttemptAuthority
    ) -> EngineeringAgentEvidenceToolAdapter:
        if (
            not isinstance(authority, EngineeringProviderAttemptAuthority)
            or authority.chat_binding_digest != self.binding.digest
            or authority.world_model_cognition_authority_digest
            != self.configuration.world_model_read_authority_digest
            or authority.source_profile_ref != self.configuration.source_profile_ref
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Provider attempt cannot acquire a drifted evidence runtime",
            )
        with self._lock:
            if authority.digest in self._issued_authorities:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "Provider attempt cannot acquire two evidence tool runtimes",
                )
            self._issued_authorities.add(authority.digest)
            tool = EngineeringAgentEvidenceToolAdapter(
                configuration=self.configuration,
                cognition_projector=self._cognition_projector,
                source_broker=self._source_broker,
                retrieval_worker=self._retrieval_worker,
            )
            self._created_tools.append(tool)
            return tool


@dataclass(frozen=True, slots=True)
class EngineeringChatSessionRuntimeReceipt:
    schema: str
    status: str
    chat_binding_digest: Digest
    route_plan_digest: Digest
    evidence_tool_factory_digest: Digest
    primary_provider_runtime_digest: Digest
    fallback_provider_runtime_digest: Digest
    launcher_receipt_digest: Digest
    blocking_gaps: tuple[str, ...]
    artifact_session_config_loaded: bool
    artifact_session_config_digest: Digest | None
    fixed_command_wired: bool
    attempt_runtime_created_at_preparation: bool
    source_read_performed_at_preparation: bool
    credential_resolved_at_preparation: bool
    provider_dispatch_count_at_preparation: int
    listener_started_at_preparation: bool
    request_retry_allowed: bool
    production_activation: str
    checked_at: datetime
    digest: Digest

    def public_status(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "status": self.status,
            "chat_binding_digest": self.chat_binding_digest.value,
            "route_plan_digest": self.route_plan_digest.value,
            "evidence_tool_factory_digest": (
                self.evidence_tool_factory_digest.value
            ),
            "primary_provider_runtime_digest": (
                self.primary_provider_runtime_digest.value
            ),
            "fallback_provider_runtime_digest": (
                self.fallback_provider_runtime_digest.value
            ),
            "launcher_receipt_digest": self.launcher_receipt_digest.value,
            "blocking_gaps": self.blocking_gaps,
            "artifact_session_config_loaded": self.artifact_session_config_loaded,
            "artifact_session_config_digest": (
                self.artifact_session_config_digest.value
                if self.artifact_session_config_digest is not None
                else None
            ),
            "fixed_command_wired": self.fixed_command_wired,
            "attempt_runtime_created_at_preparation": (
                self.attempt_runtime_created_at_preparation
            ),
            "source_read_performed_at_preparation": (
                self.source_read_performed_at_preparation
            ),
            "credential_resolved_at_preparation": (
                self.credential_resolved_at_preparation
            ),
            "provider_dispatch_count_at_preparation": (
                self.provider_dispatch_count_at_preparation
            ),
            "listener_started_at_preparation": (
                self.listener_started_at_preparation
            ),
            "request_retry_allowed": self.request_retry_allowed,
            "production_activation": self.production_activation,
            "checked_at": self.checked_at.isoformat().replace("+00:00", "Z"),
            "session_runtime_receipt_digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class PreparedEngineeringChatSessionRuntime:
    launcher: PreparedEngineeringChatProviderLauncher
    evidence_tool_factory: EngineeringChatEvidenceToolFactory
    attempt_factory: EngineeringChatProviderAttemptFactory
    primary_provider_runtime: EngineeringChatProviderModelRuntime
    fallback_provider_runtime: EngineeringChatProviderModelRuntime
    receipt: EngineeringChatSessionRuntimeReceipt


def prepare_engineering_chat_session_runtime(
    *,
    binding: EngineeringChatBinding,
    product_tree: str,
    evidence_tools: EngineeringAgentEvidenceToolConfiguration,
    cognition_projector: WorldModelCognitionProjector,
    source_broker: SourceBroker,
    retrieval_worker: RetrievalWorker,
    primary_provider_runtime: EngineeringChatProviderModelRuntime,
    fallback_provider_runtime: EngineeringChatProviderModelRuntime,
    route_plan: EngineeringProviderRoutePlan,
    checked_at: datetime,
    loop_limits: EngineeringAgentLoopLimits = EngineeringAgentLoopLimits(),
    required_conversation_turns: int = 5,
    artifact_session_config_digest: Digest | None = None,
    fixed_command_wired: bool = False,
) -> PreparedEngineeringChatSessionRuntime:
    """Join prebuilt exact runtime assets without starting the product."""

    current = _aware_utc(checked_at)
    if artifact_session_config_digest is not None and not isinstance(
        artifact_session_config_digest, Digest
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "artifact Session Configuration digest is invalid",
        )
    if not isinstance(fixed_command_wired, bool) or (
        fixed_command_wired and artifact_session_config_digest is None
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "fixed command wiring requires a loaded artifact Session Configuration",
        )
    artifact_loaded = artifact_session_config_digest is not None
    if fixed_command_wired:
        status = ENGINEERING_CHAT_FIXED_ARTIFACT_SESSION_RUNTIME_STATUS
        blocking_gaps = (
            ENGINEERING_CHAT_FIXED_ARTIFACT_SESSION_RUNTIME_BLOCKING_GAPS
        )
    elif artifact_loaded:
        status = ENGINEERING_CHAT_ARTIFACT_SESSION_RUNTIME_STATUS
        blocking_gaps = ENGINEERING_CHAT_ARTIFACT_SESSION_RUNTIME_BLOCKING_GAPS
    else:
        status = ENGINEERING_CHAT_SESSION_RUNTIME_STATUS
        blocking_gaps = ENGINEERING_CHAT_SESSION_RUNTIME_BLOCKING_GAPS
    primary_route, fallback_route = route_plan.routes
    if (
        primary_provider_runtime.provider_type != "VOLCENGINE_ARK"
        or fallback_provider_runtime.provider_type != "DEEPSEEK"
        or primary_provider_runtime.status
        != ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_STATUS
        or fallback_provider_runtime.status
        != ENGINEERING_CHAT_PROVIDER_MODEL_RUNTIME_STATUS
        or primary_provider_runtime.credential_resolved_at_preparation
        or fallback_provider_runtime.credential_resolved_at_preparation
        or primary_provider_runtime.provider_dispatch_count_at_preparation != 0
        or fallback_provider_runtime.provider_dispatch_count_at_preparation != 0
        or primary_provider_runtime.request_retry_allowed
        or fallback_provider_runtime.request_retry_allowed
        or primary_provider_runtime.production_activation != "NOT_EXECUTED"
        or fallback_provider_runtime.production_activation != "NOT_EXECUTED"
        or primary_provider_runtime.chat_binding_digest != binding.digest
        or fallback_provider_runtime.chat_binding_digest != binding.digest
        or primary_provider_runtime.configuration.digest
        != primary_route.provider_configuration_digest
        or fallback_provider_runtime.configuration.digest
        != fallback_route.provider_configuration_digest
        or primary_provider_runtime.session_authority.digest
        != primary_route.session_disclosure_authority_digest
        or fallback_provider_runtime.session_authority.digest
        != fallback_route.session_disclosure_authority_digest
        or primary_provider_runtime.gateway_repository_ref
        == fallback_provider_runtime.gateway_repository_ref
        or primary_provider_runtime.transport
        is fallback_provider_runtime.transport
        or primary_provider_runtime.model_boundary
        is fallback_provider_runtime.model_boundary
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Chat Session runtimes do not bind two distinct exact routes",
        )
    evidence_factory = EngineeringChatEvidenceToolFactory(
        binding=binding,
        configuration=evidence_tools,
        cognition_projector=cognition_projector,
        source_broker=source_broker,
        retrieval_worker=retrieval_worker,
    )

    def response_control_factory(
        authority: EngineeringProviderAttemptAuthority,
    ) -> SealedEngineeringAgentResponseControl:
        if authority.chat_binding_digest != binding.digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Response Control attempt binds another Chat",
            )
        return SealedEngineeringAgentResponseControl()

    primary_dependencies = primary_provider_runtime.attempt_dependencies(
        route=primary_route,
        tool_factory=evidence_factory,
        response_control_factory=response_control_factory,
        response_control_ref=(
            "engineering-agent-response-control:VOLCENGINE_ARK@1"
        ),
    )
    fallback_dependencies = fallback_provider_runtime.attempt_dependencies(
        route=fallback_route,
        tool_factory=evidence_factory,
        response_control_factory=response_control_factory,
        response_control_ref="engineering-agent-response-control:DEEPSEEK@1",
    )
    attempt_factory = EngineeringChatProviderAttemptFactory(
        plan=route_plan,
        evidence_tool_configuration_digest=evidence_tools.digest,
        primary=primary_dependencies,
        fallback=fallback_dependencies,
        loop_limits=loop_limits,
        available_operations=ENGINEERING_CHAT_PROVIDER_OPERATIONS,
    )
    launcher = prepare_engineering_chat_provider_launcher(
        binding=binding,
        product_tree=product_tree,
        evidence_tools=evidence_tools,
        primary_configuration=primary_provider_runtime.configuration,
        fallback_configuration=fallback_provider_runtime.configuration,
        primary_session_authority=(
            primary_provider_runtime.session_authority
        ),
        fallback_session_authority=(
            fallback_provider_runtime.session_authority
        ),
        route_plan=route_plan,
        attempt_factory=attempt_factory,
        checked_at=current,
        required_conversation_turns=required_conversation_turns,
    )
    core = {
        "schema": ENGINEERING_CHAT_SESSION_RUNTIME_SCHEMA,
        "status": status,
        "chat_binding_digest": binding.digest.value,
        "route_plan_digest": route_plan.digest.value,
        "evidence_tool_factory_digest": evidence_factory.digest.value,
        "primary_provider_runtime_digest": (
            primary_provider_runtime.digest.value
        ),
        "fallback_provider_runtime_digest": (
            fallback_provider_runtime.digest.value
        ),
        "launcher_receipt_digest": launcher.receipt.digest.value,
        "blocking_gaps": blocking_gaps,
        "artifact_session_config_loaded": artifact_loaded,
        "artifact_session_config_digest": (
            artifact_session_config_digest.value
            if artifact_session_config_digest is not None
            else None
        ),
        "fixed_command_wired": fixed_command_wired,
        "attempt_runtime_created_at_preparation": False,
        "source_read_performed_at_preparation": False,
        "credential_resolved_at_preparation": False,
        "provider_dispatch_count_at_preparation": 0,
        "listener_started_at_preparation": False,
        "request_retry_allowed": False,
        "production_activation": "NOT_EXECUTED",
        "checked_at": current.isoformat().replace("+00:00", "Z"),
    }
    receipt = EngineeringChatSessionRuntimeReceipt(
        schema=ENGINEERING_CHAT_SESSION_RUNTIME_SCHEMA,
        status=status,
        chat_binding_digest=binding.digest,
        route_plan_digest=route_plan.digest,
        evidence_tool_factory_digest=evidence_factory.digest,
        primary_provider_runtime_digest=primary_provider_runtime.digest,
        fallback_provider_runtime_digest=fallback_provider_runtime.digest,
        launcher_receipt_digest=launcher.receipt.digest,
        blocking_gaps=blocking_gaps,
        artifact_session_config_loaded=artifact_loaded,
        artifact_session_config_digest=artifact_session_config_digest,
        fixed_command_wired=fixed_command_wired,
        attempt_runtime_created_at_preparation=False,
        source_read_performed_at_preparation=False,
        credential_resolved_at_preparation=False,
        provider_dispatch_count_at_preparation=0,
        listener_started_at_preparation=False,
        request_retry_allowed=False,
        production_activation="NOT_EXECUTED",
        checked_at=current,
        digest=digest_of(core),
    )
    return PreparedEngineeringChatSessionRuntime(
        launcher=launcher,
        evidence_tool_factory=evidence_factory,
        attempt_factory=attempt_factory,
        primary_provider_runtime=primary_provider_runtime,
        fallback_provider_runtime=fallback_provider_runtime,
        receipt=receipt,
    )


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Engineering Chat Session runtime time must be timezone-aware",
        )
    return value.astimezone(timezone.utc)


__all__ = [
    "ENGINEERING_CHAT_ARTIFACT_SESSION_RUNTIME_BLOCKING_GAPS",
    "ENGINEERING_CHAT_ARTIFACT_SESSION_RUNTIME_STATUS",
    "ENGINEERING_CHAT_FIXED_ARTIFACT_SESSION_RUNTIME_BLOCKING_GAPS",
    "ENGINEERING_CHAT_FIXED_ARTIFACT_SESSION_RUNTIME_STATUS",
    "ENGINEERING_CHAT_SESSION_RUNTIME_BLOCKING_GAPS",
    "ENGINEERING_CHAT_SESSION_RUNTIME_SCHEMA",
    "ENGINEERING_CHAT_SESSION_RUNTIME_STATUS",
    "EngineeringChatEvidenceToolFactory",
    "EngineeringChatSessionRuntimeReceipt",
    "PreparedEngineeringChatSessionRuntime",
    "prepare_engineering_chat_session_runtime",
]
