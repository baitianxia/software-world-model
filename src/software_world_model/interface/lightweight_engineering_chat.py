"""Lazy Provider-attempt composition for the lightweight Agent path."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Callable

from software_world_model.ai_infrastructure.conversational_engineering_model import (
    EngineeringAgentModelConfiguration,
    EngineeringAgentSessionDisclosureAuthority,
)
from software_world_model.application_services.conversational_engineering_agent import (
    EngineeringAgentLoopLimits,
    EngineeringAgentToolOperation,
    EngineeringAgentToolPort,
)
from software_world_model.application_services.conversational_engineering_routing import (
    ENGINEERING_PROVIDER_ATTEMPT_COMPONENTS,
    EngineeringProviderAttemptAuthority,
    EngineeringProviderAttemptRuntime,
    EngineeringProviderRoutePlan,
    EngineeringProviderRouteRole,
    EngineeringProviderRouteSpec,
)
from software_world_model.application_services.lightweight_engineering_agent import (
    ApplicationOwnedLightweightAgentTurnExecutor,
    LightweightAgentTraceStore,
    LightweightEngineeringModel,
    SealedLightweightDeliveryControl,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of
from software_world_model.knowledge_engine.capability_cognition import (
    CapabilityCognitionIndex,
)


LightweightToolFactory = Callable[
    [EngineeringProviderAttemptAuthority], EngineeringAgentToolPort
]


@dataclass(frozen=True, slots=True)
class LightweightProviderAttemptDependencies:
    route_spec_digest: Digest
    provider_configuration_digest: Digest
    session_authority_digest: Digest
    model_boundary_ref: str
    gateway_repository_ref: str
    disclosure_boundary_ref: str
    model: LightweightEngineeringModel
    tool_factory: LightweightToolFactory
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        route: EngineeringProviderRouteSpec,
        configuration: EngineeringAgentModelConfiguration,
        session_authority: EngineeringAgentSessionDisclosureAuthority,
        model: LightweightEngineeringModel,
        gateway_repository_ref: str,
        disclosure_boundary_ref: str,
        tool_factory: LightweightToolFactory,
    ) -> "LightweightProviderAttemptDependencies":
        model_ref = _text(model.instance_ref, "lightweight model boundary reference")
        gateway_ref = _text(gateway_repository_ref, "Gateway repository reference")
        disclosure_ref = _text(
            disclosure_boundary_ref, "disclosure boundary reference"
        )
        if (
            route.execution_profile_digest != configuration.digest
            or route.session_disclosure_authority_digest
            != session_authority.digest
            or session_authority.provider_binding_digest != configuration.digest
            or not callable(getattr(model, "decide", None))
            or not callable(getattr(model, "review", None))
            or not callable(tool_factory)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "lightweight dependencies do not bind the exact Provider route",
            )
        core = {
            "schema": "SWM-LIGHTWEIGHT-PROVIDER-DEPENDENCIES@1",
            "route_spec_digest": route.digest.value,
            "provider_configuration_digest": configuration.digest.value,
            "session_authority_digest": session_authority.digest.value,
            "model_boundary_ref": model_ref,
            "gateway_repository_ref": gateway_ref,
            "disclosure_boundary_ref": disclosure_ref,
            "source_access": "READ_ONLY_APPLICATION_PORT",
            "attempt_creation": "LAZY_PER_LOGICAL_TURN",
        }
        return cls(
            route_spec_digest=route.digest,
            provider_configuration_digest=configuration.digest,
            session_authority_digest=session_authority.digest,
            model_boundary_ref=model_ref,
            gateway_repository_ref=gateway_ref,
            disclosure_boundary_ref=disclosure_ref,
            model=model,
            tool_factory=tool_factory,
            digest=digest_of(core),
        )


class LightweightEngineeringChatProviderAttemptFactory:
    """Create a fresh tool/delivery chain while sharing committed Chat state."""

    def __init__(
        self,
        *,
        plan: EngineeringProviderRoutePlan,
        evidence_tool_configuration_digest: Digest,
        primary: LightweightProviderAttemptDependencies,
        fallback: LightweightProviderAttemptDependencies,
        dispatch_budget_digest: Digest,
        capability_cognition: CapabilityCognitionIndex | None = None,
        loop_limits: EngineeringAgentLoopLimits = EngineeringAgentLoopLimits(),
        trace_store: LightweightAgentTraceStore | None = None,
    ) -> None:
        if (
            primary.route_spec_digest != plan.routes[0].digest
            or fallback.route_spec_digest != plan.routes[1].digest
            or primary.model is fallback.model
            or primary.model_boundary_ref == fallback.model_boundary_ref
            or primary.gateway_repository_ref == fallback.gateway_repository_ref
            or primary.disclosure_boundary_ref == fallback.disclosure_boundary_ref
            or (
                capability_cognition is not None
                and not isinstance(capability_cognition, CapabilityCognitionIndex)
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "lightweight attempt factory requires two distinct exact routes",
            )
        self.plan = plan
        self.evidence_tool_configuration_digest = evidence_tool_configuration_digest
        self.primary = primary
        self.fallback = fallback
        self.loop_limits = loop_limits
        self.capability_cognition = capability_cognition
        self.available_operations = (
            EngineeringAgentToolOperation.SOURCE_SEARCH,
            EngineeringAgentToolOperation.SOURCE_READ,
        )
        self.trace_store = trace_store or LightweightAgentTraceStore()
        self._dispatch_budget_digest = dispatch_budget_digest
        self._issued: set[Digest] = set()
        self._attempt_objects: list[object] = []
        self._lock = Lock()
        self.digest = digest_of(
            {
                "schema": "SWM-LIGHTWEIGHT-ATTEMPT-FACTORY@2",
                "route_plan_digest": plan.digest.value,
                "evidence_tool_configuration_digest": (
                    evidence_tool_configuration_digest.value
                ),
                "primary_dependencies_digest": primary.digest.value,
                "fallback_dependencies_digest": fallback.digest.value,
                "dispatch_budget_digest": dispatch_budget_digest.value,
                "operations": tuple(item.value for item in self.available_operations),
                "cognition_operations": (
                    (
                        "SEARCH_COGNITION",
                        "TRAVERSE_RELATIONS",
                        "RETRIEVE_COGNITION_DETAIL",
                    )
                    if capability_cognition is not None
                    else ()
                ),
                "capability_cognition_digest": (
                    capability_cognition.snapshot.digest.value
                    if capability_cognition is not None
                    else None
                ),
                "maximum_steps": loop_limits.maximum_agent_steps,
                "maximum_tool_actions": loop_limits.maximum_tool_actions,
                "maximum_reviews": loop_limits.maximum_reviews,
                "request_retry_allowed": False,
            }
        )

    def create(
        self, authority: EngineeringProviderAttemptAuthority
    ) -> EngineeringProviderAttemptRuntime:
        if authority.route_plan_digest != self.plan.digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "lightweight attempt authority binds another route plan",
            )
        dependencies = (
            self.primary
            if authority.role is EngineeringProviderRouteRole.PREFERRED
            else self.fallback
        )
        if dependencies.route_spec_digest != authority.route_spec_digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "lightweight attempt dependencies bind another route",
            )
        with self._lock:
            if authority.digest in self._issued:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "lightweight attempt authority cannot be consumed twice",
                )
            self._issued.add(authority.digest)
        tool = dependencies.tool_factory(authority)
        delivery = SealedLightweightDeliveryControl()
        if not callable(getattr(tool, "execute", None)):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "lightweight attempt did not receive a read-only tool runtime",
            )
        with self._lock:
            if any(tool is item or delivery is item for item in self._attempt_objects):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "lightweight attempt-scoped controls must be fresh",
                )
            self._attempt_objects.extend((tool, delivery))
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=dependencies.model,
            tool_port=tool,
            delivery_control=delivery,
            trace_store=self.trace_store,
            attempt_ref=authority.attempt_id.value,
            capability_cognition=self.capability_cognition,
            limits=self.loop_limits,
        )
        component_bases = {
            "PRIMARY_AGENT_DRIVER": dependencies.model_boundary_ref,
            "EVIDENCE_TOOL_RUNTIME": self.evidence_tool_configuration_digest.value,
            "INDEPENDENT_REVIEWER": dependencies.model_boundary_ref,
            "RESPONSE_CONTROL": "sealed-lightweight-delivery-control",
            "MODEL_GATEWAY_REPOSITORY": dependencies.gateway_repository_ref,
            "DISCLOSURE_AUTHORIZER": dependencies.disclosure_boundary_ref,
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


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value.strip()


__all__ = [
    "LightweightEngineeringChatProviderAttemptFactory",
    "LightweightProviderAttemptDependencies",
]
