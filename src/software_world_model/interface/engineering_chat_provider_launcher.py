"""Fixed, non-starting composition root for the routed Engineering Chat.

Preparation validates the exact product, Chat, evidence tools, ordered
execution profiles, per-Provider disclosure authorities, and lazy attempt factory.  It wires
the Browser application but deliberately does not open port 8765, create an
attempt runtime, resolve a credential, read Source, or call a Provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Callable, Sequence

from software_world_model.ai_infrastructure.conversational_engineering_model import (
    EngineeringAgentModelConfiguration,
    EngineeringAgentSessionDisclosureAuthority,
)
from software_world_model.application_services.conversational_engineering_agent import (
    ApplicationOwnedEngineeringAgentTurnExecutor,
    EngineeringAgentDriver,
    EngineeringAgentLoopLimits,
    EngineeringAgentResponseControl,
    EngineeringAgentReviewer,
    EngineeringAgentToolOperation,
    EngineeringAgentToolPort,
    EngineeringAgentWorkStateRepository,
    InMemoryEngineeringAgentWorkStateRepository,
)
from software_world_model.application_services.conversational_engineering_routing import (
    ENGINEERING_PROVIDER_ATTEMPT_COMPONENTS,
    ApplicationOwnedEngineeringProviderRouter,
    EngineeringProviderAttemptAuthority,
    EngineeringProviderAttemptRuntime,
    EngineeringProviderRoutePlan,
    EngineeringProviderRouteRole,
    EngineeringProviderRouteSpec,
    SealedPreDispatchUnavailableAvailabilityBoundary,
)
from software_world_model.application_services.conversational_engineering_tools import (
    EngineeringAgentEvidenceToolConfiguration,
)
from software_world_model.application_services.engineering_conversation import (
    EngineeringChatBinding,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    digest_of,
)

from .engineering_chat_browser import (
    ENGINEERING_CHAT_LOOPBACK_ORIGIN,
    EngineeringChatBrowserApplication,
)
from .engineering_chat_candidate import (
    engineering_chat_product_candidate_digest,
)


ENGINEERING_CHAT_PROVIDER_LAUNCHER_SCHEMA = (
    "SWM-ENGINEERING-CHAT-PROVIDER-LAUNCHER@1"
)
ENGINEERING_CHAT_PROVIDER_LAUNCHER_STATUS = (
    "PROVIDER_ROUTE_COMPOSITION_LOCAL_CANDIDATE"
)
ENGINEERING_CHAT_PROVIDER_LAUNCHER_BLOCKING_GAPS = (
    "REAL_PROVIDER_SOURCE_RUNTIME_AND_CREDENTIAL_NOT_ATTESTED",
    "FIXED_COMMAND_SESSION_NOT_WIRED",
    "LIVE_PROVIDER_AND_BROWSER_NOT_EXECUTED",
)
ENGINEERING_CHAT_PROVIDER_OPERATIONS = (
    EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
    EngineeringAgentToolOperation.SOURCE_SEARCH,
    EngineeringAgentToolOperation.SOURCE_READ,
)


ToolFactory = Callable[[EngineeringProviderAttemptAuthority], EngineeringAgentToolPort]
ResponseControlFactory = Callable[
    [EngineeringProviderAttemptAuthority], EngineeringAgentResponseControl
]


@dataclass(frozen=True, slots=True)
class EngineeringChatProviderAttemptDependencies:
    route_spec_digest: Digest
    provider_configuration_digest: Digest
    session_disclosure_authority_digest: Digest
    model_boundary_ref: str
    model_gateway_repository_ref: str
    disclosure_authorizer_ref: str
    response_control_ref: str
    driver: EngineeringAgentDriver
    reviewer: EngineeringAgentReviewer
    tool_factory: ToolFactory
    response_control_factory: ResponseControlFactory
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        route: EngineeringProviderRouteSpec,
        configuration: EngineeringAgentModelConfiguration,
        session_authority: EngineeringAgentSessionDisclosureAuthority,
        model_boundary_ref: str,
        model_gateway_repository_ref: str,
        disclosure_authorizer_ref: str,
        response_control_ref: str,
        driver: EngineeringAgentDriver,
        reviewer: EngineeringAgentReviewer,
        tool_factory: ToolFactory,
        response_control_factory: ResponseControlFactory,
    ) -> "EngineeringChatProviderAttemptDependencies":
        for value, label in (
            (model_boundary_ref, "model boundary reference"),
            (model_gateway_repository_ref, "Model Gateway repository reference"),
            (disclosure_authorizer_ref, "disclosure authorizer reference"),
            (response_control_ref, "Response Control reference"),
        ):
            _text(value, label)
        if (
            route.execution_profile_digest != configuration.digest
            or route.session_disclosure_authority_digest
            != session_authority.digest
            or session_authority.provider_binding_digest != configuration.digest
            or not callable(getattr(driver, "propose", None))
            or not callable(getattr(reviewer, "review", None))
            or not callable(tool_factory)
            or not callable(response_control_factory)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Provider attempt dependencies do not bind the exact route and model boundary",
            )
        core = {
            "schema": "ENGINEERING_CHAT_PROVIDER_ATTEMPT_DEPENDENCIES@1",
            "route_spec_digest": route.digest.value,
            "provider_configuration_digest": configuration.digest.value,
            "session_disclosure_authority_digest": session_authority.digest.value,
            "model_boundary_ref": model_boundary_ref,
            "model_gateway_repository_ref": model_gateway_repository_ref,
            "disclosure_authorizer_ref": disclosure_authorizer_ref,
            "response_control_ref": response_control_ref,
            "attempt_runtime_creation": "LAZY_ON_LOGICAL_TURN",
            "credential_resolution": "NOT_PERFORMED_BY_PREPARATION",
        }
        return cls(
            route_spec_digest=route.digest,
            provider_configuration_digest=configuration.digest,
            session_disclosure_authority_digest=session_authority.digest,
            model_boundary_ref=model_boundary_ref,
            model_gateway_repository_ref=model_gateway_repository_ref,
            disclosure_authorizer_ref=disclosure_authorizer_ref,
            response_control_ref=response_control_ref,
            driver=driver,
            reviewer=reviewer,
            tool_factory=tool_factory,
            response_control_factory=response_control_factory,
            digest=digest_of(core),
        )


class EngineeringChatProviderAttemptFactory:
    """Lazily create a fresh Application loop and evidence runtime per attempt."""

    def __init__(
        self,
        *,
        plan: EngineeringProviderRoutePlan,
        evidence_tool_configuration_digest: Digest,
        primary: EngineeringChatProviderAttemptDependencies,
        fallback: EngineeringChatProviderAttemptDependencies,
        work_state_repository: EngineeringAgentWorkStateRepository | None = None,
        loop_limits: EngineeringAgentLoopLimits = EngineeringAgentLoopLimits(),
        available_operations: Sequence[EngineeringAgentToolOperation] = (
            ENGINEERING_CHAT_PROVIDER_OPERATIONS
        ),
    ) -> None:
        operations = tuple(available_operations)
        if (
            primary.digest != _attempt_dependencies_digest(primary)
            or fallback.digest != _attempt_dependencies_digest(fallback)
            or primary.route_spec_digest != plan.routes[0].digest
            or fallback.route_spec_digest != plan.routes[1].digest
            or primary.model_boundary_ref == fallback.model_boundary_ref
            or primary.model_gateway_repository_ref
            == fallback.model_gateway_repository_ref
            or primary.disclosure_authorizer_ref
            == fallback.disclosure_authorizer_ref
            or primary.driver is fallback.driver
            or primary.reviewer is fallback.reviewer
            or operations != ENGINEERING_CHAT_PROVIDER_OPERATIONS
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "attempt factory requires distinct exact execution-profile boundaries",
            )
        self.plan = plan
        self.evidence_tool_configuration_digest = (
            evidence_tool_configuration_digest
        )
        self.primary = primary
        self.fallback = fallback
        self.loop_limits = loop_limits
        self.available_operations = operations
        self._work_state_repository = (
            work_state_repository
            if work_state_repository is not None
            else InMemoryEngineeringAgentWorkStateRepository()
        )
        self._lock = Lock()
        self._issued_attempts: set[Digest] = set()
        self._issued_attempt_scoped_objects: list[object] = []
        self.digest = digest_of(
            {
                "schema": "ENGINEERING_CHAT_PROVIDER_ATTEMPT_FACTORY@1",
                "route_plan_digest": plan.digest.value,
                "evidence_tool_configuration_digest": (
                    evidence_tool_configuration_digest.value
                ),
                "primary_dependencies_digest": primary.digest.value,
                "fallback_dependencies_digest": fallback.digest.value,
                "available_operations": tuple(item.value for item in operations),
                "loop_limits": {
                    "maximum_agent_steps": loop_limits.maximum_agent_steps,
                    "maximum_tool_actions": loop_limits.maximum_tool_actions,
                    "maximum_reviews": loop_limits.maximum_reviews,
                    "maximum_consecutive_no_progress": (
                        loop_limits.maximum_consecutive_no_progress
                    ),
                    "maximum_evidence_package_bytes": (
                        loop_limits.maximum_evidence_package_bytes
                    ),
                },
                "model_call_receipts_required": True,
                "tool_authority_receipts_required": True,
                "committed_work_state_repository_shared": True,
                "failed_attempt_intermediate_state_shared": False,
            }
        )

    def create(
        self, authority: EngineeringProviderAttemptAuthority
    ) -> EngineeringProviderAttemptRuntime:
        if authority.route_plan_digest != self.plan.digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "attempt authority does not bind the fixed Provider route",
            )
        dependencies = (
            self.primary
            if authority.role is EngineeringProviderRouteRole.PREFERRED
            else self.fallback
        )
        if dependencies.route_spec_digest != authority.route_spec_digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "attempt dependencies do not bind the selected Provider route",
            )
        with self._lock:
            if authority.digest in self._issued_attempts:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "Provider attempt authority cannot create two runtimes",
                )
            self._issued_attempts.add(authority.digest)
        tool = dependencies.tool_factory(authority)
        response_control = dependencies.response_control_factory(authority)
        if not callable(getattr(tool, "execute", None)) or not callable(
            getattr(response_control, "authorize", None)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "attempt factories returned an invalid tool or Response Control",
            )
        with self._lock:
            if (
                tool is response_control
                or any(
                    tool is item or response_control is item
                    for item in self._issued_attempt_scoped_objects
                )
            ):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "attempt-scoped tool and Response Control objects must be fresh",
                )
            self._issued_attempt_scoped_objects.extend((tool, response_control))
        executor = ApplicationOwnedEngineeringAgentTurnExecutor(
            driver=dependencies.driver,
            tool_port=tool,
            reviewer=dependencies.reviewer,
            response_control=response_control,
            available_operations=self.available_operations,
            limits=self.loop_limits,
            require_tool_authority_receipts=True,
            require_model_call_receipts=True,
            work_state_repository=self._work_state_repository,
        )
        component_bases = {
            "PRIMARY_AGENT_DRIVER": dependencies.model_boundary_ref,
            "EVIDENCE_TOOL_RUNTIME": (
                self.evidence_tool_configuration_digest.value
            ),
            "INDEPENDENT_REVIEWER": dependencies.model_boundary_ref,
            "RESPONSE_CONTROL": dependencies.response_control_ref,
            "MODEL_GATEWAY_REPOSITORY": (
                dependencies.model_gateway_repository_ref
            ),
            "DISCLOSURE_AUTHORIZER": dependencies.disclosure_authorizer_ref,
        }
        component_refs = tuple(
            (
                name,
                f"{authority.attempt_id.value}:{name}:{component_bases[name]}",
            )
            for name in ENGINEERING_PROVIDER_ATTEMPT_COMPONENTS
        )
        return EngineeringProviderAttemptRuntime.create(
            executor=executor,
            authority=authority,
            component_instance_refs=component_refs,
        )


@dataclass(frozen=True, slots=True)
class EngineeringChatProviderLauncherReceipt:
    schema: str
    status: str
    product_revision: str
    product_tree: str
    product_candidate_digest: Digest
    chat_binding_digest: Digest
    evidence_tool_configuration_digest: Digest
    provider_route_ref: str
    route_plan_digest: Digest
    attempt_factory_digest: Digest
    ordered_provider_types: tuple[str, str]
    provider_configuration_digests: tuple[Digest, Digest]
    session_disclosure_authority_digests: tuple[Digest, Digest]
    fixed_origin: str
    maximum_turns: int
    maximum_dispatches_per_turn: int
    maximum_fallback_attempts_per_turn: int
    blocking_gaps: tuple[str, ...]
    ready_for_live: bool
    listener_started: bool
    credential_resolved: bool
    source_read_performed: bool
    provider_dispatch_count: int
    request_retry_allowed: bool
    production_activation: str
    checked_at: datetime
    digest: Digest

    def public_status(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "status": self.status,
            "ready_for_live": self.ready_for_live,
            "product_revision": self.product_revision,
            "product_tree": self.product_tree,
            "product_candidate_digest": self.product_candidate_digest.value,
            "chat_binding_digest": self.chat_binding_digest.value,
            "evidence_tool_configuration_digest": (
                self.evidence_tool_configuration_digest.value
            ),
            "provider_route_ref": self.provider_route_ref,
            "route_plan_digest": self.route_plan_digest.value,
            "attempt_factory_digest": self.attempt_factory_digest.value,
            "ordered_provider_types": self.ordered_provider_types,
            "provider_configuration_digests": tuple(
                item.value for item in self.provider_configuration_digests
            ),
            "session_disclosure_authority_digests": tuple(
                item.value
                for item in self.session_disclosure_authority_digests
            ),
            "fixed_origin": self.fixed_origin,
            "maximum_turns": self.maximum_turns,
            "maximum_dispatches_per_turn": (
                self.maximum_dispatches_per_turn
            ),
            "maximum_fallback_attempts_per_turn": (
                self.maximum_fallback_attempts_per_turn
            ),
            "blocking_gaps": self.blocking_gaps,
            "listener_started": self.listener_started,
            "credential_resolved": self.credential_resolved,
            "source_read_performed": self.source_read_performed,
            "provider_dispatch_count": self.provider_dispatch_count,
            "request_retry_allowed": self.request_retry_allowed,
            "production_activation": self.production_activation,
            "checked_at": self.checked_at.isoformat().replace("+00:00", "Z"),
            "launcher_receipt_digest": self.digest.value,
        }


@dataclass(frozen=True, slots=True)
class PreparedEngineeringChatProviderLauncher:
    application: EngineeringChatBrowserApplication
    service: InMemoryEngineeringConversationService
    router: ApplicationOwnedEngineeringProviderRouter
    route_plan: EngineeringProviderRoutePlan
    attempt_factory: EngineeringChatProviderAttemptFactory
    receipt: EngineeringChatProviderLauncherReceipt


def prepare_engineering_chat_provider_launcher(
    *,
    binding: EngineeringChatBinding,
    product_tree: str,
    evidence_tools: EngineeringAgentEvidenceToolConfiguration,
    primary_configuration: EngineeringAgentModelConfiguration,
    fallback_configuration: EngineeringAgentModelConfiguration,
    primary_session_authority: EngineeringAgentSessionDisclosureAuthority,
    fallback_session_authority: EngineeringAgentSessionDisclosureAuthority,
    route_plan: EngineeringProviderRoutePlan,
    attempt_factory: EngineeringChatProviderAttemptFactory,
    checked_at: datetime,
    required_conversation_turns: int = 5,
    availability_clock: Callable[[], datetime] | None = None,
) -> PreparedEngineeringChatProviderLauncher:
    """Wire the fixed routed Browser application without executing any I/O."""

    current = _aware_utc(checked_at)
    if type(required_conversation_turns) is not int or required_conversation_turns < 1:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "fixed Provider launcher requires a positive Turn count",
        )
    product_candidate_digest = engineering_chat_product_candidate_digest(
        product_revision=binding.product_revision,
        product_tree=product_tree,
    )
    if (
        binding.world_model_status is not RuntimeCapabilityStatus.READY
        or binding.source_access_status is not RuntimeCapabilityStatus.READY
        or binding.provider_status is not RuntimeCapabilityStatus.READY
        or binding.world_model_authority_digest is None
        or binding.source_profile_ref is None
        or route_plan.chat_binding_digest != binding.digest
        or route_plan.provider_route_ref != binding.provider_route_ref
        or attempt_factory.plan.digest != route_plan.digest
        or attempt_factory.evidence_tool_configuration_digest
        != evidence_tools.digest
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "fixed Provider launcher components do not bind the exact Chat route",
        )
    if (
        evidence_tools.project_name != binding.project_name
        or evidence_tools.repository_revision != binding.repository_revision
        or evidence_tools.world_model_read_authority_digest
        != binding.world_model_authority_digest
        or evidence_tools.source_profile_ref != binding.source_profile_ref
        or evidence_tools.provider_disclosure_policy
        != primary_configuration.provider_disclosure_policy_ref
        or evidence_tools.provider_disclosure_policy
        != fallback_configuration.provider_disclosure_policy_ref
        or "src/main/resources" not in binding.excluded_source_paths
        or "src/main/resources" not in evidence_tools.excluded_source_paths
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "fixed Provider launcher evidence boundary drifted",
        )
    configurations = (primary_configuration, fallback_configuration)
    authorities = (primary_session_authority, fallback_session_authority)
    for route, configuration, authority in zip(
        route_plan.routes, configurations, authorities, strict=True
    ):
        configuration.require_current(current)
        authority.require_current(
            configuration=configuration,
            chat_binding_digest=binding.digest,
            at=current,
        )
        if (
            route.execution_profile_digest != configuration.digest
            or route.session_disclosure_authority_digest != authority.digest
            or route.maximum_dispatches_per_turn
            != authority.maximum_dispatches_per_turn
            or authority.product_candidate_digest != product_candidate_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "fixed Provider launcher route, qualification, or session drifted",
            )
    required_dispatches_per_turn = (
        attempt_factory.loop_limits.maximum_agent_steps
        + attempt_factory.loop_limits.maximum_reviews
    )
    required_total = required_conversation_turns * required_dispatches_per_turn
    if any(
        authority.maximum_turns < required_conversation_turns
        or authority.maximum_dispatches_per_turn < required_dispatches_per_turn
        or authority.maximum_total_dispatches < required_total
        for authority in authorities
    ):
        raise DomainError(
            ErrorCode.BUDGET_EXHAUSTED,
            "each Provider route must fund the full bounded five-Turn worst case",
        )
    router = ApplicationOwnedEngineeringProviderRouter(
        plan=route_plan,
        attempt_factory=attempt_factory,
        availability_boundary=(
            SealedPreDispatchUnavailableAvailabilityBoundary(
                clock=availability_clock,
            )
        ),
    )
    service = InMemoryEngineeringConversationService(
        binding,
        turn_executor=router,
    )
    application = EngineeringChatBrowserApplication(service)
    ordered_types = tuple(item.provider_type for item in configurations)
    configuration_digests = tuple(item.digest for item in configurations)
    authority_digests = tuple(item.digest for item in authorities)
    core = {
        "schema": ENGINEERING_CHAT_PROVIDER_LAUNCHER_SCHEMA,
        "status": ENGINEERING_CHAT_PROVIDER_LAUNCHER_STATUS,
        "product_revision": binding.product_revision,
        "product_tree": product_tree,
        "product_candidate_digest": product_candidate_digest.value,
        "chat_binding_digest": binding.digest.value,
        "evidence_tool_configuration_digest": evidence_tools.digest.value,
        "provider_route_ref": route_plan.provider_route_ref,
        "route_plan_digest": route_plan.digest.value,
        "attempt_factory_digest": attempt_factory.digest.value,
        "ordered_provider_types": ordered_types,
        "provider_configuration_digests": tuple(
            item.value for item in configuration_digests
        ),
        "session_disclosure_authority_digests": tuple(
            item.value for item in authority_digests
        ),
        "fixed_origin": ENGINEERING_CHAT_LOOPBACK_ORIGIN,
        "maximum_turns": required_conversation_turns,
        "maximum_dispatches_per_turn": required_dispatches_per_turn,
        "maximum_fallback_attempts_per_turn": 1,
        "blocking_gaps": ENGINEERING_CHAT_PROVIDER_LAUNCHER_BLOCKING_GAPS,
        "ready_for_live": False,
        "listener_started": False,
        "credential_resolved": False,
        "source_read_performed": False,
        "provider_dispatch_count": 0,
        "request_retry_allowed": False,
        "production_activation": "NOT_EXECUTED",
        "checked_at": current.isoformat().replace("+00:00", "Z"),
    }
    receipt = EngineeringChatProviderLauncherReceipt(
        schema=ENGINEERING_CHAT_PROVIDER_LAUNCHER_SCHEMA,
        status=ENGINEERING_CHAT_PROVIDER_LAUNCHER_STATUS,
        product_revision=binding.product_revision,
        product_tree=product_tree,
        product_candidate_digest=product_candidate_digest,
        chat_binding_digest=binding.digest,
        evidence_tool_configuration_digest=evidence_tools.digest,
        provider_route_ref=route_plan.provider_route_ref,
        route_plan_digest=route_plan.digest,
        attempt_factory_digest=attempt_factory.digest,
        ordered_provider_types=(ordered_types[0], ordered_types[1]),
        provider_configuration_digests=(
            configuration_digests[0],
            configuration_digests[1],
        ),
        session_disclosure_authority_digests=(
            authority_digests[0], authority_digests[1]
        ),
        fixed_origin=ENGINEERING_CHAT_LOOPBACK_ORIGIN,
        maximum_turns=required_conversation_turns,
        maximum_dispatches_per_turn=required_dispatches_per_turn,
        maximum_fallback_attempts_per_turn=1,
        blocking_gaps=ENGINEERING_CHAT_PROVIDER_LAUNCHER_BLOCKING_GAPS,
        ready_for_live=False,
        listener_started=False,
        credential_resolved=False,
        source_read_performed=False,
        provider_dispatch_count=0,
        request_retry_allowed=False,
        production_activation="NOT_EXECUTED",
        checked_at=current,
        digest=digest_of(core),
    )
    return PreparedEngineeringChatProviderLauncher(
        application=application,
        service=service,
        router=router,
        route_plan=route_plan,
        attempt_factory=attempt_factory,
        receipt=receipt,
    )


def _aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "fixed Provider launcher time must be timezone-aware",
        )
    return value.astimezone(timezone.utc)


def _attempt_dependencies_digest(
    value: EngineeringChatProviderAttemptDependencies,
) -> Digest:
    for item, label in (
        (value.model_boundary_ref, "model boundary reference"),
        (value.model_gateway_repository_ref, "Model Gateway repository reference"),
        (value.disclosure_authorizer_ref, "disclosure authorizer reference"),
        (value.response_control_ref, "Response Control reference"),
    ):
        _text(item, label)
    if (
        not callable(getattr(value.driver, "propose", None))
        or not callable(getattr(value.reviewer, "review", None))
        or not callable(value.tool_factory)
        or not callable(value.response_control_factory)
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Provider attempt dependency callables are invalid",
        )
    return digest_of(
        {
            "schema": "ENGINEERING_CHAT_PROVIDER_ATTEMPT_DEPENDENCIES@1",
            "route_spec_digest": value.route_spec_digest.value,
            "provider_configuration_digest": (
                value.provider_configuration_digest.value
            ),
            "session_disclosure_authority_digest": (
                value.session_disclosure_authority_digest.value
            ),
            "model_boundary_ref": value.model_boundary_ref,
            "model_gateway_repository_ref": (
                value.model_gateway_repository_ref
            ),
            "disclosure_authorizer_ref": value.disclosure_authorizer_ref,
            "response_control_ref": value.response_control_ref,
            "attempt_runtime_creation": "LAZY_ON_LOGICAL_TURN",
            "credential_resolution": "NOT_PERFORMED_BY_PREPARATION",
        }
    )


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value.strip()


__all__ = [
    "ENGINEERING_CHAT_PROVIDER_LAUNCHER_BLOCKING_GAPS",
    "ENGINEERING_CHAT_PROVIDER_LAUNCHER_SCHEMA",
    "ENGINEERING_CHAT_PROVIDER_LAUNCHER_STATUS",
    "ENGINEERING_CHAT_PROVIDER_OPERATIONS",
    "EngineeringChatProviderAttemptDependencies",
    "EngineeringChatProviderAttemptFactory",
    "EngineeringChatProviderLauncherReceipt",
    "PreparedEngineeringChatProviderLauncher",
    "prepare_engineering_chat_provider_launcher",
]
