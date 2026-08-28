"""Application-owned Ark-primary / DeepSeek-fallback Turn routing.

The router treats one Chat Turn as the immutable logical interaction.  Each
Provider receives a separately authorized, separately constructed full-chain
attempt.  Only the five ADR-017 classifications may start the fallback, and no
primary intermediate object is passed to the fallback factory.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from threading import Lock
from typing import Protocol, Sequence
from urllib.parse import urlsplit

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    StableId,
    Uuid4IdGenerator,
    digest_of,
)

from .engineering_conversation import (
    ConversationMessageKind,
    ConversationTurnState,
    EngineeringChatBinding,
    EngineeringConversationTurnExecutor,
    EngineeringProviderFailureClassification,
    EngineeringTurnExecutionOutcome,
    EngineeringTurnExecutionRequest,
    RuntimeCapabilityStatus,
    validate_engineering_turn_execution_outcome,
)


ENGINEERING_PROVIDER_ROUTE_SCHEMA = "ENGINEERING_PROVIDER_ROUTE_PLAN@1"
ENGINEERING_PROVIDER_ATTEMPT_AUTHORITY_SCHEMA = (
    "ENGINEERING_PROVIDER_ATTEMPT_AUTHORITY@1"
)
ENGINEERING_PROVIDER_ATTEMPT_AUTHORITY_SCHEMA_V2 = (
    "ENGINEERING_PROVIDER_ATTEMPT_AUTHORITY@2"
)
ENGINEERING_PROVIDER_ATTEMPT_RUNTIME_SCHEMA = (
    "ENGINEERING_PROVIDER_ATTEMPT_RUNTIME@1"
)
ENGINEERING_PROVIDER_ATTEMPT_RECEIPT_SCHEMA = (
    "ENGINEERING_PROVIDER_ATTEMPT_RECEIPT@1"
)
ENGINEERING_PROVIDER_ROUTE_RECEIPT_SCHEMA = (
    "ENGINEERING_PROVIDER_ROUTE_RECEIPT@1"
)

ENGINEERING_PROVIDER_ATTEMPT_COMPONENTS = (
    "PRIMARY_AGENT_DRIVER",
    "EVIDENCE_TOOL_RUNTIME",
    "INDEPENDENT_REVIEWER",
    "RESPONSE_CONTROL",
    "MODEL_GATEWAY_REPOSITORY",
    "DISCLOSURE_AUTHORIZER",
)


class EngineeringProviderRouteRole(str, Enum):
    PRIMARY = "PRIMARY"
    FALLBACK = "FALLBACK"


class EngineeringProviderAttemptTerminalState(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    FAILED_BEFORE_EXECUTION = "FAILED_BEFORE_EXECUTION"


class EngineeringProviderLateResultPolicy(str, Enum):
    QUARANTINE_AUDIT_ONLY = "QUARANTINE_AUDIT_ONLY"


def engineering_agent_dual_provider_route_ref(
    *,
    primary_configuration_digest: Digest,
    fallback_configuration_digest: Digest,
) -> str:
    """Create the non-circular route identity used by the Chat binding."""

    route_digest = digest_of(
        [
            "ENGINEERING_AGENT_DUAL_PROVIDER_ROUTE_REF@1",
            (
                ("VOLCENGINE_ARK", primary_configuration_digest.value),
                ("DEEPSEEK", fallback_configuration_digest.value),
            ),
        ]
    )
    return f"engineering-agent-dual-route:{route_digest.value}"


@dataclass(frozen=True, slots=True)
class EngineeringProviderRouteSpec:
    ordinal: int
    role: EngineeringProviderRouteRole
    provider_type: str
    endpoint: str
    model_ref: str
    provider_configuration_digest: Digest
    session_disclosure_authority_digest: Digest
    standing_authority_digest: Digest | None
    qualification_ref: str
    maximum_dispatches_per_turn: int
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        ordinal: int,
        role: EngineeringProviderRouteRole,
        provider_type: str,
        endpoint: str,
        model_ref: str,
        provider_configuration_digest: Digest,
        session_disclosure_authority_digest: Digest,
        standing_authority_digest: Digest | None = None,
        qualification_ref: str,
        maximum_dispatches_per_turn: int,
    ) -> "EngineeringProviderRouteSpec":
        if (
            type(ordinal) is not int
            or ordinal not in {1, 2}
            or not isinstance(role, EngineeringProviderRouteRole)
            or type(maximum_dispatches_per_turn) is not int
            or maximum_dispatches_per_turn < 1
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Provider route ordinal, role, or dispatch fuse is invalid",
            )
        provider_type = _text(provider_type, "Provider type")
        endpoint = _text(endpoint, "Provider endpoint")
        model_ref = _text(model_ref, "Provider model reference")
        qualification_ref = _text(qualification_ref, "Provider qualification")
        if not isinstance(provider_configuration_digest, Digest) or not isinstance(
            session_disclosure_authority_digest, Digest
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Provider route requires exact configuration and disclosure digests",
            )
        if standing_authority_digest is not None and not isinstance(
            standing_authority_digest, Digest
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Provider route standing authority digest is invalid",
            )
        parsed = urlsplit(endpoint)
        if (
            parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Provider route endpoint must be exact credential-free HTTPS",
            )
        core = {
            "schema": "ENGINEERING_PROVIDER_ROUTE_SPEC@1",
            "ordinal": ordinal,
            "role": role.value,
            "provider_type": provider_type,
            "endpoint": endpoint,
            "model_ref": model_ref,
            "provider_configuration_digest": provider_configuration_digest.value,
            "session_disclosure_authority_digest": (
                session_disclosure_authority_digest.value
            ),
            "qualification_ref": qualification_ref,
            "maximum_dispatches_per_turn": maximum_dispatches_per_turn,
            "request_retry_allowed": False,
        }
        if standing_authority_digest is not None:
            core["standing_authority_digest"] = standing_authority_digest.value
        return cls(
            ordinal=ordinal,
            role=role,
            provider_type=provider_type,
            endpoint=endpoint,
            model_ref=model_ref,
            provider_configuration_digest=provider_configuration_digest,
            session_disclosure_authority_digest=(
                session_disclosure_authority_digest
            ),
            standing_authority_digest=standing_authority_digest,
            qualification_ref=qualification_ref,
            maximum_dispatches_per_turn=maximum_dispatches_per_turn,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringProviderRoutePlan:
    schema: str
    chat_binding_digest: Digest
    provider_route_ref: str
    routes: tuple[EngineeringProviderRouteSpec, EngineeringProviderRouteSpec]
    maximum_fallback_attempts: int
    request_retry_count: int
    late_result_policy: EngineeringProviderLateResultPolicy
    primary_intermediate_reuse_allowed: bool
    production_activation: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        binding: EngineeringChatBinding,
        primary: EngineeringProviderRouteSpec,
        fallback: EngineeringProviderRouteSpec,
    ) -> "EngineeringProviderRoutePlan":
        expected_primary = EngineeringProviderRouteSpec.create(
            ordinal=primary.ordinal,
            role=primary.role,
            provider_type=primary.provider_type,
            endpoint=primary.endpoint,
            model_ref=primary.model_ref,
            provider_configuration_digest=primary.provider_configuration_digest,
            session_disclosure_authority_digest=(
                primary.session_disclosure_authority_digest
            ),
            standing_authority_digest=primary.standing_authority_digest,
            qualification_ref=primary.qualification_ref,
            maximum_dispatches_per_turn=primary.maximum_dispatches_per_turn,
        )
        expected_fallback = EngineeringProviderRouteSpec.create(
            ordinal=fallback.ordinal,
            role=fallback.role,
            provider_type=fallback.provider_type,
            endpoint=fallback.endpoint,
            model_ref=fallback.model_ref,
            provider_configuration_digest=fallback.provider_configuration_digest,
            session_disclosure_authority_digest=(
                fallback.session_disclosure_authority_digest
            ),
            standing_authority_digest=fallback.standing_authority_digest,
            qualification_ref=fallback.qualification_ref,
            maximum_dispatches_per_turn=fallback.maximum_dispatches_per_turn,
        )
        expected_ref = engineering_agent_dual_provider_route_ref(
            primary_configuration_digest=primary.provider_configuration_digest,
            fallback_configuration_digest=fallback.provider_configuration_digest,
        )
        if (
            binding.provider_status is not RuntimeCapabilityStatus.READY
            or binding.world_model_status is not RuntimeCapabilityStatus.READY
            or binding.source_access_status is not RuntimeCapabilityStatus.READY
            or binding.provider_route_ref != expected_ref
            or binding.world_model_authority_digest is None
            or binding.source_profile_ref is None
            or primary != expected_primary
            or fallback != expected_fallback
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "dual Provider route requires a fully bound ready Engineering Chat",
            )
        if (
            primary.ordinal != 1
            or primary.role is not EngineeringProviderRouteRole.PRIMARY
            or primary.provider_type != "VOLCENGINE_ARK"
            or fallback.ordinal != 2
            or fallback.role is not EngineeringProviderRouteRole.FALLBACK
            or fallback.provider_type != "DEEPSEEK"
            or primary.provider_configuration_digest
            == fallback.provider_configuration_digest
            or primary.session_disclosure_authority_digest
            == fallback.session_disclosure_authority_digest
            or primary.standing_authority_digest
            != fallback.standing_authority_digest
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "Provider route must be exact distinct VOLCENGINE_ARK then DEEPSEEK",
            )
        routes = (primary, fallback)
        core = {
            "schema": ENGINEERING_PROVIDER_ROUTE_SCHEMA,
            "chat_binding_digest": binding.digest.value,
            "provider_route_ref": expected_ref,
            "route_digests": tuple(item.digest.value for item in routes),
            "maximum_fallback_attempts": 1,
            "request_retry_count": 0,
            "late_result_policy": (
                EngineeringProviderLateResultPolicy.QUARANTINE_AUDIT_ONLY.value
            ),
            "primary_intermediate_reuse_allowed": False,
            "provider_session_reuse_allowed": False,
            "production_activation": "NOT_EXECUTED",
        }
        return cls(
            schema=ENGINEERING_PROVIDER_ROUTE_SCHEMA,
            chat_binding_digest=binding.digest,
            provider_route_ref=expected_ref,
            routes=routes,
            maximum_fallback_attempts=1,
            request_retry_count=0,
            late_result_policy=(
                EngineeringProviderLateResultPolicy.QUARANTINE_AUDIT_ONLY
            ),
            primary_intermediate_reuse_allowed=False,
            production_activation="NOT_EXECUTED",
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringProviderAttemptAuthority:
    schema: str
    attempt_id: StableId
    logical_turn_request_digest: Digest
    original_user_message_digest: Digest
    conversation_context_digest: Digest
    world_model_cognition_authority_digest: Digest
    chat_binding_digest: Digest
    route_plan_digest: Digest
    route_spec_digest: Digest
    ordinal: int
    role: EngineeringProviderRouteRole
    provider_type: str
    provider_configuration_digest: Digest
    session_disclosure_authority_digest: Digest
    standing_authority_digest: Digest | None
    source_profile_ref: str
    retry_count: int
    full_chain_required: bool
    primary_intermediate_reuse_allowed: bool
    provider_session_reuse_allowed: bool
    late_result_policy: EngineeringProviderLateResultPolicy
    production_activation: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        attempt_id: StableId,
        request: EngineeringTurnExecutionRequest,
        plan: EngineeringProviderRoutePlan,
        route: EngineeringProviderRouteSpec,
    ) -> "EngineeringProviderAttemptAuthority":
        if (
            request.binding.digest != plan.chat_binding_digest
            or request.binding.provider_route_ref != plan.provider_route_ref
            or route not in plan.routes
            or request.binding.world_model_authority_digest is None
            or request.binding.source_profile_ref is None
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Provider attempt authority does not bind the logical Turn and route",
            )
        schema = (
            ENGINEERING_PROVIDER_ATTEMPT_AUTHORITY_SCHEMA_V2
            if route.standing_authority_digest is not None
            else ENGINEERING_PROVIDER_ATTEMPT_AUTHORITY_SCHEMA
        )
        core = {
            "schema": schema,
            "attempt_id": attempt_id.value,
            "logical_turn_request_digest": request.request_digest.value,
            "original_user_message_digest": request.user_message.digest.value,
            "conversation_context_digest": (
                request.snapshot_before.context.digest.value
            ),
            "world_model_cognition_authority_digest": (
                request.binding.world_model_authority_digest.value
            ),
            "chat_binding_digest": request.binding.digest.value,
            "route_plan_digest": plan.digest.value,
            "route_spec_digest": route.digest.value,
            "ordinal": route.ordinal,
            "role": route.role.value,
            "provider_type": route.provider_type,
            "provider_configuration_digest": (
                route.provider_configuration_digest.value
            ),
            "session_disclosure_authority_digest": (
                route.session_disclosure_authority_digest.value
            ),
            "source_profile_ref": request.binding.source_profile_ref,
            "input_source": "IMMUTABLE_ORIGINAL_TURN_AND_SEALED_CONTEXT",
            "retry_count": 0,
            "full_chain_required": True,
            "primary_intermediate_reuse_allowed": False,
            "provider_session_reuse_allowed": False,
            "late_result_policy": plan.late_result_policy.value,
            "production_activation": "NOT_EXECUTED",
        }
        if route.standing_authority_digest is not None:
            core["standing_authority_digest"] = (
                route.standing_authority_digest.value
            )
        return cls(
            schema=schema,
            attempt_id=attempt_id,
            logical_turn_request_digest=request.request_digest,
            original_user_message_digest=request.user_message.digest,
            conversation_context_digest=request.snapshot_before.context.digest,
            world_model_cognition_authority_digest=(
                request.binding.world_model_authority_digest
            ),
            chat_binding_digest=request.binding.digest,
            route_plan_digest=plan.digest,
            route_spec_digest=route.digest,
            ordinal=route.ordinal,
            role=route.role,
            provider_type=route.provider_type,
            provider_configuration_digest=route.provider_configuration_digest,
            session_disclosure_authority_digest=(
                route.session_disclosure_authority_digest
            ),
            standing_authority_digest=route.standing_authority_digest,
            source_profile_ref=request.binding.source_profile_ref,
            retry_count=0,
            full_chain_required=True,
            primary_intermediate_reuse_allowed=False,
            provider_session_reuse_allowed=False,
            late_result_policy=plan.late_result_policy,
            production_activation="NOT_EXECUTED",
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringProviderAttemptRuntime:
    executor: EngineeringConversationTurnExecutor
    attempt_authority_digest: Digest
    route_spec_digest: Digest
    component_instance_refs: tuple[tuple[str, str], ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        executor: EngineeringConversationTurnExecutor,
        authority: EngineeringProviderAttemptAuthority,
        component_instance_refs: Sequence[tuple[str, str]],
    ) -> "EngineeringProviderAttemptRuntime":
        components = tuple(
            (_text(name, "attempt component"), _text(ref, "component instance"))
            for name, ref in component_instance_refs
        )
        if (
            not callable(getattr(executor, "execute", None))
            or tuple(name for name, _ in components)
            != ENGINEERING_PROVIDER_ATTEMPT_COMPONENTS
            or len({ref for _, ref in components}) != len(components)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Provider attempt runtime is not a fresh complete Agent chain",
            )
        core = {
            "schema": ENGINEERING_PROVIDER_ATTEMPT_RUNTIME_SCHEMA,
            "attempt_authority_digest": authority.digest.value,
            "route_spec_digest": authority.route_spec_digest.value,
            "component_instance_refs": components,
            "committed_conversation_state_store_shared": True,
            "attempt_intermediate_state_shared": False,
        }
        return cls(
            executor=executor,
            attempt_authority_digest=authority.digest,
            route_spec_digest=authority.route_spec_digest,
            component_instance_refs=components,
            digest=digest_of(core),
        )


class EngineeringProviderAttemptFactory(Protocol):
    def create(
        self, authority: EngineeringProviderAttemptAuthority
    ) -> EngineeringProviderAttemptRuntime: ...


@dataclass(frozen=True, slots=True)
class EngineeringProviderAttemptReceipt:
    schema: str
    attempt_id: StableId
    attempt_authority_digest: Digest
    runtime_digest: Digest | None
    route_spec_digest: Digest
    ordinal: int
    role: EngineeringProviderRouteRole
    provider_type: str
    terminal_state: EngineeringProviderAttemptTerminalState
    outcome_digest: Digest
    failure_code: str | None
    provider_failure_classification: EngineeringProviderFailureClassification | None
    provider_failure_code: str | None
    provider_dispatch_count: int
    model_dispatch_receipt_refs: tuple[str, ...]
    authorized_answer_ref: str | None
    delivery_authorization_ref: str | None
    potential_duplicate_cost_risk: bool
    retry_count: int
    primary_intermediate_exported: bool
    late_result_policy: EngineeringProviderLateResultPolicy
    production_activation: str
    digest: Digest

    @classmethod
    def seal(
        cls,
        *,
        authority: EngineeringProviderAttemptAuthority,
        runtime: EngineeringProviderAttemptRuntime | None,
        outcome: EngineeringTurnExecutionOutcome,
        terminal_state: EngineeringProviderAttemptTerminalState,
    ) -> "EngineeringProviderAttemptReceipt":
        expected_state = (
            EngineeringProviderAttemptTerminalState.SUCCEEDED
            if outcome.state is ConversationTurnState.SUCCEEDED
            else EngineeringProviderAttemptTerminalState.FAILED
        )
        if terminal_state is not expected_state and not (
            terminal_state
            is EngineeringProviderAttemptTerminalState.FAILED_BEFORE_EXECUTION
            and outcome.state is ConversationTurnState.FAILED
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Provider attempt terminal state and Turn outcome disagree",
            )
        if runtime is not None and (
            runtime.attempt_authority_digest != authority.digest
            or runtime.route_spec_digest != authority.route_spec_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Provider attempt runtime does not bind its authority",
            )
        outcome_digest = _execution_outcome_digest(outcome)
        duplicate_risk = (
            outcome.provider_failure_classification
            is EngineeringProviderFailureClassification.PROVIDER_OUTCOME_UNKNOWN
        )
        core = {
            "schema": ENGINEERING_PROVIDER_ATTEMPT_RECEIPT_SCHEMA,
            "attempt_id": authority.attempt_id.value,
            "attempt_authority_digest": authority.digest.value,
            "runtime_digest": runtime.digest.value if runtime else None,
            "route_spec_digest": authority.route_spec_digest.value,
            "ordinal": authority.ordinal,
            "role": authority.role.value,
            "provider_type": authority.provider_type,
            "terminal_state": terminal_state.value,
            "outcome_digest": outcome_digest.value,
            "failure_code": outcome.failure_code,
            "provider_failure_classification": (
                outcome.provider_failure_classification.value
                if outcome.provider_failure_classification is not None
                else None
            ),
            "provider_failure_code": outcome.provider_failure_code,
            "provider_dispatch_count": outcome.provider_dispatch_count,
            "model_dispatch_receipt_refs": outcome.model_dispatch_receipt_refs,
            "authorized_answer_ref": (
                outcome.answer_ref
                if outcome.state is ConversationTurnState.SUCCEEDED
                else None
            ),
            "delivery_authorization_ref": outcome.delivery_authorization_ref,
            "potential_duplicate_cost_risk": duplicate_risk,
            "retry_count": 0,
            "primary_intermediate_exported": False,
            "late_result_policy": authority.late_result_policy.value,
            "production_activation": "NOT_EXECUTED",
        }
        return cls(
            schema=ENGINEERING_PROVIDER_ATTEMPT_RECEIPT_SCHEMA,
            attempt_id=authority.attempt_id,
            attempt_authority_digest=authority.digest,
            runtime_digest=runtime.digest if runtime else None,
            route_spec_digest=authority.route_spec_digest,
            ordinal=authority.ordinal,
            role=authority.role,
            provider_type=authority.provider_type,
            terminal_state=terminal_state,
            outcome_digest=outcome_digest,
            failure_code=outcome.failure_code,
            provider_failure_classification=(
                outcome.provider_failure_classification
            ),
            provider_failure_code=outcome.provider_failure_code,
            provider_dispatch_count=outcome.provider_dispatch_count,
            model_dispatch_receipt_refs=outcome.model_dispatch_receipt_refs,
            authorized_answer_ref=(
                outcome.answer_ref
                if outcome.state is ConversationTurnState.SUCCEEDED
                else None
            ),
            delivery_authorization_ref=outcome.delivery_authorization_ref,
            potential_duplicate_cost_risk=duplicate_risk,
            retry_count=0,
            primary_intermediate_exported=False,
            late_result_policy=authority.late_result_policy,
            production_activation="NOT_EXECUTED",
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringProviderRouteReceipt:
    schema: str
    logical_turn_request_digest: Digest
    route_plan_digest: Digest
    attempt_receipt_refs: tuple[str, ...]
    selected_attempt_receipt_ref: str
    selected_provider_type: str
    state: ConversationTurnState
    fallback_attempt_count: int
    provider_dispatch_count: int
    model_dispatch_receipt_refs: tuple[str, ...]
    duplicate_cost_risk: bool
    retry_count: int
    late_result_policy: EngineeringProviderLateResultPolicy
    production_activation: str
    digest: Digest

    @classmethod
    def seal(
        cls,
        *,
        request: EngineeringTurnExecutionRequest,
        plan: EngineeringProviderRoutePlan,
        attempts: Sequence[EngineeringProviderAttemptReceipt],
        selected_outcome: EngineeringTurnExecutionOutcome,
    ) -> "EngineeringProviderRouteReceipt":
        receipts = tuple(attempts)
        if (
            len(receipts) not in {1, 2}
            or receipts[0].role is not EngineeringProviderRouteRole.PRIMARY
            or receipts[0].ordinal != 1
            or (
                len(receipts) == 2
                and (
                    receipts[1].role
                    is not EngineeringProviderRouteRole.FALLBACK
                    or receipts[1].ordinal != 2
                    or receipts[0].provider_failure_classification is None
                )
            )
            or receipts[-1].outcome_digest
            != _execution_outcome_digest(selected_outcome)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Provider route attempts do not form one ordered logical Turn",
            )
        model_receipts = tuple(
            ref
            for attempt in receipts
            for ref in attempt.model_dispatch_receipt_refs
        )
        if len(model_receipts) != len(set(model_receipts)):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Provider attempts cannot share a model dispatch receipt",
            )
        dispatch_count = sum(item.provider_dispatch_count for item in receipts)
        duplicate_risk = len(receipts) == 2 and (
            receipts[0].provider_failure_classification
            is EngineeringProviderFailureClassification.PROVIDER_OUTCOME_UNKNOWN
        )
        attempt_refs = tuple(item.digest.value for item in receipts)
        core = {
            "schema": ENGINEERING_PROVIDER_ROUTE_RECEIPT_SCHEMA,
            "logical_turn_request_digest": request.request_digest.value,
            "route_plan_digest": plan.digest.value,
            "attempt_receipt_refs": attempt_refs,
            "selected_attempt_receipt_ref": receipts[-1].digest.value,
            "selected_provider_type": receipts[-1].provider_type,
            "state": selected_outcome.state.value,
            "fallback_attempt_count": len(receipts) - 1,
            "provider_dispatch_count": dispatch_count,
            "model_dispatch_receipt_refs": model_receipts,
            "duplicate_cost_risk": duplicate_risk,
            "retry_count": 0,
            "late_result_policy": plan.late_result_policy.value,
            "late_primary_can_overwrite": False,
            "production_activation": "NOT_EXECUTED",
        }
        return cls(
            schema=ENGINEERING_PROVIDER_ROUTE_RECEIPT_SCHEMA,
            logical_turn_request_digest=request.request_digest,
            route_plan_digest=plan.digest,
            attempt_receipt_refs=attempt_refs,
            selected_attempt_receipt_ref=receipts[-1].digest.value,
            selected_provider_type=receipts[-1].provider_type,
            state=selected_outcome.state,
            fallback_attempt_count=len(receipts) - 1,
            provider_dispatch_count=dispatch_count,
            model_dispatch_receipt_refs=model_receipts,
            duplicate_cost_risk=duplicate_risk,
            retry_count=0,
            late_result_policy=plan.late_result_policy,
            production_activation="NOT_EXECUTED",
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringProviderRouteAudit:
    route_receipt: EngineeringProviderRouteReceipt
    attempt_authorities: tuple[EngineeringProviderAttemptAuthority, ...]
    attempt_receipts: tuple[EngineeringProviderAttemptReceipt, ...]


@dataclass(slots=True)
class _AttemptRun:
    authority: EngineeringProviderAttemptAuthority
    runtime: EngineeringProviderAttemptRuntime | None
    outcome: EngineeringTurnExecutionOutcome
    receipt: EngineeringProviderAttemptReceipt


class ApplicationOwnedEngineeringProviderRouter(
    EngineeringConversationTurnExecutor
):
    """Execute one immutable Turn through Ark and at most one DeepSeek chain."""

    def __init__(
        self,
        *,
        plan: EngineeringProviderRoutePlan,
        attempt_factory: EngineeringProviderAttemptFactory,
        id_generator: IdGenerator | None = None,
    ) -> None:
        if not callable(getattr(attempt_factory, "create", None)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Provider router requires an attempt runtime factory",
            )
        self._plan = plan
        self._factory = attempt_factory
        self._ids = id_generator or Uuid4IdGenerator()
        self._lock = Lock()
        self._issued_ids: set[StableId] = set()
        self._executed_requests: set[Digest] = set()
        self._audits: dict[Digest, EngineeringProviderRouteAudit] = {}

    def execute(
        self, request: EngineeringTurnExecutionRequest
    ) -> EngineeringTurnExecutionOutcome:
        try:
            expected_plan = EngineeringProviderRoutePlan.create(
                binding=request.binding,
                primary=self._plan.routes[0],
                fallback=self._plan.routes[1],
            )
        except (DomainError, IndexError):
            expected_plan = None
        if self._plan != expected_plan:
            return _route_failure_outcome(
                request,
                failure_code="PROVIDER_ROUTE_BINDING_MISMATCH",
            )
        with self._lock:
            if request.request_digest in self._executed_requests:
                return _route_failure_outcome(
                    request,
                    failure_code="PROVIDER_ROUTE_REQUEST_REPLAYED",
                )
            self._executed_requests.add(request.request_digest)

        primary = self._execute_attempt(
            request=request,
            route=self._plan.routes[0],
            prior_runtime=None,
        )
        runs = [primary]
        if (
            primary.outcome.state is ConversationTurnState.FAILED
            and primary.outcome.provider_failure_classification is not None
        ):
            fallback = self._execute_attempt(
                request=request,
                route=self._plan.routes[1],
                prior_runtime=primary.runtime,
            )
            runs.append(fallback)

        selected = runs[-1]
        route_receipt = EngineeringProviderRouteReceipt.seal(
            request=request,
            plan=self._plan,
            attempts=tuple(item.receipt for item in runs),
            selected_outcome=selected.outcome,
        )
        routed_outcome = replace(
            selected.outcome,
            provider_dispatch_count=route_receipt.provider_dispatch_count,
            model_dispatch_receipt_refs=(
                route_receipt.model_dispatch_receipt_refs
            ),
            provider_route_receipt_ref=route_receipt.digest.value,
            provider_attempt_receipt_refs=(
                route_receipt.attempt_receipt_refs
            ),
            fallback_provider_attempt_count=(
                route_receipt.fallback_attempt_count
            ),
            provider_duplicate_cost_risk=route_receipt.duplicate_cost_risk,
        )
        validate_engineering_turn_execution_outcome(request, routed_outcome)
        audit = EngineeringProviderRouteAudit(
            route_receipt=route_receipt,
            attempt_authorities=tuple(item.authority for item in runs),
            attempt_receipts=tuple(item.receipt for item in runs),
        )
        with self._lock:
            self._audits[request.request_digest] = audit
        return routed_outcome

    def audit_for(self, request_digest: Digest) -> EngineeringProviderRouteAudit:
        with self._lock:
            audit = self._audits.get(request_digest)
        if audit is None:
            raise LookupError(
                f"Provider route audit {request_digest.value} was not found"
            )
        return audit

    def _execute_attempt(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        route: EngineeringProviderRouteSpec,
        prior_runtime: EngineeringProviderAttemptRuntime | None,
    ) -> _AttemptRun:
        authority = EngineeringProviderAttemptAuthority.create(
            attempt_id=self._new_id("engineering_provider_attempt"),
            request=request,
            plan=self._plan,
            route=route,
        )
        runtime: EngineeringProviderAttemptRuntime | None = None
        terminal_state = EngineeringProviderAttemptTerminalState.FAILED
        try:
            runtime = self._factory.create(authority)
            expected_runtime = EngineeringProviderAttemptRuntime.create(
                executor=runtime.executor,
                authority=authority,
                component_instance_refs=runtime.component_instance_refs,
            )
            if runtime != expected_runtime:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Provider attempt factory returned an inconsistent runtime",
                )
            if prior_runtime is not None and (
                runtime.executor is prior_runtime.executor
                or set(runtime.component_instance_refs)
                & set(prior_runtime.component_instance_refs)
                or {ref for _, ref in runtime.component_instance_refs}
                & {ref for _, ref in prior_runtime.component_instance_refs}
            ):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "fallback attempt reused a primary full-chain component",
                )
        except Exception:
            runtime = None
            outcome = _route_failure_outcome(
                request,
                failure_code="PROVIDER_ATTEMPT_INITIALIZATION_FAILED",
            )
            terminal_state = (
                EngineeringProviderAttemptTerminalState.FAILED_BEFORE_EXECUTION
            )
        else:
            try:
                candidate = runtime.executor.execute(request)
                validate_engineering_turn_execution_outcome(request, candidate)
                if (
                    candidate.provider_route_receipt_ref is not None
                    or candidate.provider_attempt_receipt_refs
                    or candidate.fallback_provider_attempt_count != 0
                    or candidate.provider_duplicate_cost_risk
                ):
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "Provider attempt executor cannot return a nested route",
                    )
            except Exception:
                dispatch_count = _conservative_dispatch_count(
                    locals().get("candidate")
                )
                outcome = _route_failure_outcome(
                    request,
                    failure_code="PROVIDER_ATTEMPT_EXECUTION_FAILED",
                    provider_dispatch_count=dispatch_count,
                )
            else:
                outcome = candidate
                terminal_state = (
                    EngineeringProviderAttemptTerminalState.SUCCEEDED
                    if outcome.state is ConversationTurnState.SUCCEEDED
                    else EngineeringProviderAttemptTerminalState.FAILED
                )
        receipt = EngineeringProviderAttemptReceipt.seal(
            authority=authority,
            runtime=runtime,
            outcome=outcome,
            terminal_state=terminal_state,
        )
        return _AttemptRun(
            authority=authority,
            runtime=runtime,
            outcome=outcome,
            receipt=receipt,
        )

    def _new_id(self, kind: str) -> StableId:
        with self._lock:
            value = self._ids.new(kind)
            if value in self._issued_ids:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Provider router ID generator returned a duplicate",
                )
            self._issued_ids.add(value)
            return value


def _route_failure_outcome(
    request: EngineeringTurnExecutionRequest,
    *,
    failure_code: str,
    provider_dispatch_count: int = 0,
) -> EngineeringTurnExecutionOutcome:
    message = (
        "Provider 路由未能形成一个完整、隔离且可授权的本 Turn 结果；"
        "本 Turn 已失败关闭，Conversation 仍可继续使用。"
    )
    context = request.snapshot_before.context
    return EngineeringTurnExecutionOutcome.failed(
        request_digest=request.request_digest,
        assistant_content=message,
        included_user_message_ids=(
            *context.included_user_message_ids,
            request.user_message.message_id,
        ),
        accepted_correction_message_ids=context.accepted_correction_message_ids,
        reviewed_conclusion_refs=context.reviewed_conclusion_refs,
        superseded_conclusion_refs=context.superseded_conclusion_refs,
        reducer_status="PROVIDER_ROUTE_FAILED_CLOSED",
        work_state_ref=context.work_state_ref,
        work_state_revision=(
            context.work_state_revision if context.work_state_ref else None
        ),
        work_state_digest=context.work_state_digest,
        failure_code=failure_code,
        failure_message=message,
        provider_dispatch_count=provider_dispatch_count,
    )


def _conservative_dispatch_count(value: object) -> int:
    count = getattr(value, "provider_dispatch_count", 0)
    return count if type(count) is int and count >= 0 else 0


def _execution_outcome_digest(outcome: EngineeringTurnExecutionOutcome) -> Digest:
    return digest_of(
        {
            "schema": "ENGINEERING_TURN_ATTEMPT_OUTCOME@1",
            "request_digest": outcome.request_digest.value,
            "state": outcome.state.value,
            "assistant_kind": outcome.assistant_kind.value,
            "assistant_content": outcome.assistant_content,
            "included_user_message_ids": tuple(
                item.value for item in outcome.included_user_message_ids
            ),
            "accepted_correction_message_ids": tuple(
                item.value for item in outcome.accepted_correction_message_ids
            ),
            "reviewed_conclusion_refs": outcome.reviewed_conclusion_refs,
            "superseded_conclusion_refs": outcome.superseded_conclusion_refs,
            "reducer_status": outcome.reducer_status,
            "work_state_ref": outcome.work_state_ref,
            "work_state_revision": (
                outcome.work_state_revision.value
                if outcome.work_state_revision is not None
                else None
            ),
            "work_state_digest": (
                outcome.work_state_digest.value
                if outcome.work_state_digest is not None
                else None
            ),
            "failure_code": outcome.failure_code,
            "failure_message": outcome.failure_message,
            "evidence_package_ref": outcome.evidence_package_ref,
            "answer_ref": outcome.answer_ref,
            "review_ref": outcome.review_ref,
            "delivery_authorization_ref": outcome.delivery_authorization_ref,
            "provider_dispatch_count": outcome.provider_dispatch_count,
            "model_dispatch_receipt_refs": outcome.model_dispatch_receipt_refs,
            "provider_failure_classification": (
                outcome.provider_failure_classification.value
                if outcome.provider_failure_classification is not None
                else None
            ),
            "provider_failure_code": outcome.provider_failure_code,
            "retry_count": outcome.retry_count,
            "quality_status": outcome.quality_status,
        }
    )


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value.strip()


__all__ = [
    "ENGINEERING_PROVIDER_ATTEMPT_COMPONENTS",
    "ENGINEERING_PROVIDER_ATTEMPT_RECEIPT_SCHEMA",
    "ENGINEERING_PROVIDER_ROUTE_RECEIPT_SCHEMA",
    "ENGINEERING_PROVIDER_ROUTE_SCHEMA",
    "ApplicationOwnedEngineeringProviderRouter",
    "EngineeringProviderAttemptAuthority",
    "EngineeringProviderAttemptFactory",
    "EngineeringProviderAttemptReceipt",
    "EngineeringProviderAttemptRuntime",
    "EngineeringProviderAttemptTerminalState",
    "EngineeringProviderLateResultPolicy",
    "EngineeringProviderRouteAudit",
    "EngineeringProviderRoutePlan",
    "EngineeringProviderRouteReceipt",
    "EngineeringProviderRouteRole",
    "EngineeringProviderRouteSpec",
    "engineering_agent_dual_provider_route_ref",
]
