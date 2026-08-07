"""Conversational Task Control authority boundary for Web-originated work."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Protocol

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)


class EffectClass(str, Enum):
    QUERY = "QUERY"
    COMMAND = "COMMAND"


class TaskState(str, Enum):
    RECEIVED = "RECEIVED"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    RESPONSE_PENDING = "RESPONSE_PENDING"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"
    FAILED = "FAILED"


class ApplicationCallState(str, Enum):
    PREPARED = "PREPARED"
    DISPATCHED = "DISPATCHED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    OUTCOME_PENDING = "OUTCOME_PENDING"
    CANCELED_BEFORE_DISPATCH = "CANCELED_BEFORE_DISPATCH"


@dataclass(frozen=True, slots=True)
class AgentCapability:
    capability_id: str
    contract_version: str
    allowed_use_cases: tuple[str, ...]
    allowed_effect_classes: tuple[EffectClass, ...]
    production_active: bool


@dataclass(frozen=True, slots=True)
class AgentCapabilityCatalog:
    catalog_id: StableId
    revision: Revision
    capabilities: tuple[AgentCapability, ...]
    digest: Digest

    @classmethod
    def create(
        cls, *, catalog_id: StableId, revision: Revision, capabilities: tuple[AgentCapability, ...]
    ) -> "AgentCapabilityCatalog":
        if len({item.capability_id for item in capabilities}) != len(capabilities):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "agent capability IDs must be unique")
        core = {
            "catalog_id": catalog_id.value,
            "revision": revision.value,
            "capabilities": capabilities,
        }
        return cls(catalog_id, revision, capabilities, digest_of(core))


@dataclass(frozen=True, slots=True)
class TaskRequestEnvelope:
    conversation_ref: str
    turn_ref: str
    request_ref: str
    idempotency_key: IdempotencyKey
    original_request: str
    caller_ref: str
    classification: str
    scope_id: StableId
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        conversation_ref: str,
        turn_ref: str,
        request_ref: str,
        idempotency_key: IdempotencyKey,
        original_request: str,
        caller_ref: str,
        classification: str,
        scope_id: StableId,
    ) -> "TaskRequestEnvelope":
        core = {
            "conversation_ref": _text(conversation_ref, "conversation reference"),
            "turn_ref": _text(turn_ref, "turn reference"),
            "request_ref": _text(request_ref, "request reference"),
            "original_request": _text(original_request, "original request"),
            "caller_ref": _text(caller_ref, "caller reference"),
            "classification": _text(classification, "classification"),
            "scope_id": scope_id.value,
        }
        return cls(
            conversation_ref=core["conversation_ref"],
            turn_ref=core["turn_ref"],
            request_ref=core["request_ref"],
            idempotency_key=idempotency_key,
            original_request=core["original_request"],
            caller_ref=core["caller_ref"],
            classification=core["classification"],
            scope_id=scope_id,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class OrchestratorProposal:
    task_kind: str
    capability_id: str
    target_scope_id: StableId
    response_kind: str
    digest: Digest

    @classmethod
    def create(
        cls, *, task_kind: str, capability_id: str, target_scope_id: StableId, response_kind: str
    ) -> "OrchestratorProposal":
        core = {
            "task_kind": _text(task_kind, "task kind"),
            "capability_id": _text(capability_id, "capability ID"),
            "target_scope_id": target_scope_id.value,
            "response_kind": _text(response_kind, "response kind"),
        }
        return cls(
            task_kind=core["task_kind"],
            capability_id=core["capability_id"],
            target_scope_id=target_scope_id,
            response_kind=core["response_kind"],
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class ConversationalTask:
    task_id: StableId
    revision: Revision
    orchestration_revision: Revision
    request_digest: Digest
    conversation_ref: str
    turn_ref: str
    request_ref: str
    original_request: str
    caller_ref: str
    classification: str
    scope_id: StableId
    catalog_id: StableId
    catalog_revision: Revision
    catalog_digest: Digest
    state: TaskState
    selected_capability_id: str | None
    candidate_reference: StableId | None
    created_at: datetime
    revised_at: datetime


@dataclass(frozen=True, slots=True)
class DelegatedApplicationGrant:
    grant_id: StableId
    task_id: StableId
    task_revision: Revision
    capability_id: str
    allowed_use_cases: tuple[str, ...]
    allowed_effect_classes: tuple[EffectClass, ...]
    scope_id: StableId
    classification: str
    digest: Digest


@dataclass(frozen=True, slots=True)
class AgentInvocation:
    invocation_id: StableId
    task_id: StableId
    task_revision: Revision
    capability_id: str
    grant: DelegatedApplicationGrant
    input_digest: Digest
    created_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class ApplicationCallRecord:
    call_id: StableId
    task_id: StableId
    logical_occurrence: str
    invocation_id: StableId
    use_case: str
    effect_class: EffectClass
    request_digest: Digest
    application_idempotency_key: IdempotencyKey
    revision: Revision
    state: ApplicationCallState
    result_reference: str | None
    result_digest: Digest | None


@dataclass(frozen=True, slots=True)
class TaskValidationAssertion:
    assertion_id: StableId
    task_id: StableId
    task_revision: Revision
    orchestration_revision: Revision
    candidate_reference: StableId
    purpose: str
    outcome: str
    classification: str
    issued_at: datetime
    digest: Digest


class TaskControlRepository(Protocol):
    def create_task(
        self,
        *,
        envelope: TaskRequestEnvelope,
        catalog: AgentCapabilityCatalog,
        occurred_at: datetime,
    ) -> ConversationalTask: ...

    def apply_proposal(
        self,
        *,
        task_id: StableId,
        expected_revision: Revision,
        proposal: OrchestratorProposal,
        occurred_at: datetime,
    ) -> ConversationalTask: ...

    def create_invocation(
        self,
        *,
        task: ConversationalTask,
        capability: AgentCapability,
        input_digest: Digest,
        occurred_at: datetime,
    ) -> AgentInvocation: ...

    def create_application_call(
        self,
        *,
        invocation: AgentInvocation,
        logical_occurrence: str,
        use_case: str,
        effect_class: EffectClass,
        request_digest: Digest,
    ) -> ApplicationCallRecord: ...

    def transition_application_call(
        self,
        *,
        call_id: StableId,
        expected_revision: Revision,
        target: ApplicationCallState,
        result_reference: str | None,
        result_digest: Digest | None,
    ) -> ApplicationCallRecord: ...

    def get_application_call(
        self, *, task_id: StableId, logical_occurrence: str
    ) -> ApplicationCallRecord | None: ...

    def bind_candidate(
        self,
        *,
        task_id: StableId,
        expected_revision: Revision,
        candidate_id: StableId,
        occurred_at: datetime,
    ) -> ConversationalTask: ...

    def get_task(self, task_id: StableId) -> ConversationalTask: ...


class ConversationalTaskControl:
    def __init__(
        self,
        repository: TaskControlRepository,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def create_task(
        self, envelope: TaskRequestEnvelope, catalog: AgentCapabilityCatalog
    ) -> ConversationalTask:
        return self._repository.create_task(
            envelope=envelope, catalog=catalog, occurred_at=self._now()
        )

    def accept_orchestrator_proposal(
        self,
        *,
        task_id: StableId,
        expected_revision: Revision,
        proposal: OrchestratorProposal,
        catalog: AgentCapabilityCatalog,
    ) -> ConversationalTask:
        task = self._repository.get_task(task_id)
        if task.catalog_id != catalog.catalog_id or task.catalog_digest != catalog.digest:
            raise DomainError(ErrorCode.REVISION_CONFLICT, "task catalog binding changed")
        capability = next(
            (item for item in catalog.capabilities if item.capability_id == proposal.capability_id),
            None,
        )
        if capability is None or not capability.production_active:
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "agent capability is not active")
        if proposal.target_scope_id != task.scope_id:
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "orchestrator expanded task scope")
        return self._repository.apply_proposal(
            task_id=task_id,
            expected_revision=expected_revision,
            proposal=proposal,
            occurred_at=self._now(),
        )

    def create_invocation(
        self,
        *,
        task_id: StableId,
        input_digest: Digest,
        catalog: AgentCapabilityCatalog,
    ) -> AgentInvocation:
        task = self._repository.get_task(task_id)
        capability = next(
            (item for item in catalog.capabilities if item.capability_id == task.selected_capability_id),
            None,
        )
        if capability is None:
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "task has no selected capability")
        return self._repository.create_invocation(
            task=task, capability=capability, input_digest=input_digest, occurred_at=self._now()
        )

    def prepare_application_call(
        self,
        *,
        invocation: AgentInvocation,
        logical_occurrence: str,
        use_case: str,
        effect_class: EffectClass,
        request_digest: Digest,
    ) -> ApplicationCallRecord:
        if use_case not in invocation.grant.allowed_use_cases:
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "use case is outside delegated grant")
        if effect_class not in invocation.grant.allowed_effect_classes:
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "effect class is outside delegated grant")
        return self._repository.create_application_call(
            invocation=invocation,
            logical_occurrence=_text(logical_occurrence, "logical occurrence"),
            use_case=use_case,
            effect_class=effect_class,
            request_digest=request_digest,
        )

    def transition_application_call(
        self,
        *,
        call_id: StableId,
        expected_revision: Revision,
        target: ApplicationCallState,
        result_reference: str | None = None,
        result_digest: Digest | None = None,
    ) -> ApplicationCallRecord:
        return self._repository.transition_application_call(
            call_id=call_id,
            expected_revision=expected_revision,
            target=target,
            result_reference=result_reference,
            result_digest=result_digest,
        )

    def get_application_call(
        self, *, task_id: StableId, logical_occurrence: str
    ) -> ApplicationCallRecord | None:
        return self._repository.get_application_call(
            task_id=task_id,
            logical_occurrence=_text(logical_occurrence, "logical occurrence"),
        )

    def bind_candidate(
        self,
        *,
        task_id: StableId,
        expected_revision: Revision,
        candidate_id: StableId,
    ) -> ConversationalTask:
        return self._repository.bind_candidate(
            task_id=task_id,
            expected_revision=expected_revision,
            candidate_id=candidate_id,
            occurred_at=self._now(),
        )

    def validate_for_response(
        self,
        *,
        task_id: StableId,
        expected_revision: Revision,
        expected_orchestration_revision: Revision,
        candidate_id: StableId,
        purpose: str,
    ) -> TaskValidationAssertion:
        task = self._repository.get_task(task_id)
        outcome = "ALLOW" if (
            task.revision == expected_revision
            and task.orchestration_revision == expected_orchestration_revision
            and task.candidate_reference == candidate_id
            and task.state is TaskState.RESPONSE_PENDING
        ) else "DENY"
        issued_at = self._now()
        core = {
            "task_id": task_id.value,
            "task_revision": task.revision.value,
            "orchestration_revision": task.orchestration_revision.value,
            "candidate_id": candidate_id.value,
            "purpose": purpose,
            "outcome": outcome,
            "classification": task.classification,
            "issued_at": issued_at,
        }
        digest = digest_of(core)
        return TaskValidationAssertion(
            assertion_id=StableId(f"task_assertion_{digest.value[-32:]}"),
            task_id=task_id,
            task_revision=task.revision,
            orchestration_revision=task.orchestration_revision,
            candidate_reference=candidate_id,
            purpose=purpose,
            outcome=outcome,
            classification=task.classification,
            issued_at=issued_at,
            digest=digest,
        )

    def get_task(self, task_id: StableId) -> ConversationalTask:
        return self._repository.get_task(task_id)

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return an aware datetime")
        return value.astimezone(timezone.utc)


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value
