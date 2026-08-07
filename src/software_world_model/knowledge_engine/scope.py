"""KnowledgeScope owner contract and application-independent service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Mapping, Protocol

from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)


class ScopeType(str, Enum):
    SYSTEM = "SYSTEM"
    SHARED_COMPONENT = "SHARED_COMPONENT"
    BUSINESS_DOMAIN = "BUSINESS_DOMAIN"


class ScopeLifecycle(str, Enum):
    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class ScopePurpose(str, Enum):
    BIND_CONFIGURATION = "BIND_CONFIGURATION@1"
    SOURCE_EXECUTION = "SOURCE_EXECUTION@1"
    KNOWLEDGE_UPDATE = "KNOWLEDGE_UPDATE@1"
    SNAPSHOT_PUBLICATION = "SNAPSHOT_PUBLICATION@1"


class AssertionOutcome(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"


Metadata = tuple[tuple[str, str], ...]
_PROHIBITED_METADATA_KEYS = {"api_key", "credential", "password", "secret", "token"}


def _nonempty(value: str, label: str) -> str:
    if not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def normalize_metadata(metadata: Mapping[str, str] | None) -> Metadata:
    if metadata is None:
        return ()
    normalized: list[tuple[str, str]] = []
    for key, value in metadata.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "scope metadata must contain string keys and values")
        clean_key = _nonempty(key, "metadata key")
        if clean_key.casefold() in _PROHIBITED_METADATA_KEYS:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "scope metadata cannot contain credential fields")
        if len(clean_key.encode("utf-8")) > 128 or len(value.encode("utf-8")) > 2048:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "scope metadata exceeds the supported size")
        normalized.append((clean_key, value))
    normalized.sort(key=lambda item: item[0])
    if len({key for key, _ in normalized}) != len(normalized):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "scope metadata keys must be unique")
    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class KnowledgeScope:
    scope_id: StableId
    scope_type: ScopeType
    lifecycle: ScopeLifecycle
    definition_revision: Revision
    metadata: Metadata
    created_at: datetime
    revised_at: datetime
    actor: str
    reason: str
    definition_digest: Digest


@dataclass(frozen=True, slots=True)
class ScopeStateAssertion:
    assertion_id: StableId
    scope_id: StableId
    scope_type: ScopeType
    definition_revision: Revision
    lifecycle: ScopeLifecycle
    purpose: ScopePurpose
    outcome: AssertionOutcome
    caller_ref: str
    request_ref: str
    classification: str
    read_at: datetime
    digest: Digest

    def core(self) -> dict[str, object]:
        return {
            "scope_id": self.scope_id.value,
            "scope_type": self.scope_type.value,
            "definition_revision": self.definition_revision.value,
            "lifecycle": self.lifecycle.value,
            "purpose": self.purpose.value,
            "outcome": self.outcome.value,
            "caller_ref": self.caller_ref,
            "request_ref": self.request_ref,
            "classification": self.classification,
            "read_at": self.read_at,
        }

    def verify_digest(self) -> bool:
        return digest_of(self.core()) == self.digest


@dataclass(frozen=True, slots=True)
class OutboxEvent:
    event_id: StableId
    owner: str
    aggregate_id: StableId
    authority_revision: Revision
    event_type: str
    payload_digest: Digest
    occurred_at: datetime


class KnowledgeScopeRepository(Protocol):
    def create(
        self,
        *,
        scope_type: ScopeType,
        metadata: Metadata,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> KnowledgeScope: ...

    def update_metadata(
        self,
        *,
        scope_id: StableId,
        expected_revision: Revision,
        metadata: Metadata,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> KnowledgeScope: ...

    def retire(
        self,
        *,
        scope_id: StableId,
        expected_revision: Revision,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> KnowledgeScope: ...

    def get(self, scope_id: StableId, revision: Revision | None = None) -> KnowledgeScope: ...

    def read_state_assertion(
        self,
        *,
        scope_id: StableId,
        expected_revision: Revision | None,
        purpose: ScopePurpose,
        caller_ref: str,
        request_ref: str,
        classification: str,
        read_at: datetime,
    ) -> ScopeStateAssertion: ...

    def validate_state_assertion(self, assertion: ScopeStateAssertion) -> bool: ...

    def list_outbox(self) -> tuple[OutboxEvent, ...]: ...


class PublicationActivity(Protocol):
    def has_open_publication(self, scope_id: StableId) -> bool: ...


class NoOpenPublicationActivity:
    """WP-1 policy: publication has not been introduced yet."""

    def has_open_publication(self, scope_id: StableId) -> bool:
        return False


class KnowledgeScopeService:
    def __init__(
        self,
        repository: KnowledgeScopeRepository,
        *,
        publication_activity: PublicationActivity | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._publication_activity = publication_activity or NoOpenPublicationActivity()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def create_scope(
        self,
        *,
        scope_type: ScopeType,
        metadata: Mapping[str, str] | None,
        idempotency_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> KnowledgeScope:
        if not isinstance(scope_type, ScopeType):
            raise DomainError(ErrorCode.INVALID_SCOPE_TYPE, "unsupported scope type")
        clean_metadata = normalize_metadata(metadata)
        actor = _nonempty(actor, "actor")
        reason = _nonempty(reason, "reason")
        request_digest = digest_of(
            {
                "command": "CreateScope@1",
                "scope_type": scope_type.value,
                "metadata": clean_metadata,
                "actor": actor,
                "reason": reason,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.create(
            scope_type=scope_type,
            metadata=clean_metadata,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def update_scope_metadata(
        self,
        *,
        scope_id: StableId,
        expected_revision: Revision,
        metadata: Mapping[str, str],
        idempotency_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> KnowledgeScope:
        clean_metadata = normalize_metadata(metadata)
        actor = _nonempty(actor, "actor")
        reason = _nonempty(reason, "reason")
        request_digest = digest_of(
            {
                "command": "UpdateScopeMetadata@1",
                "scope_id": scope_id.value,
                "expected_revision": expected_revision.value,
                "metadata": clean_metadata,
                "actor": actor,
                "reason": reason,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.update_metadata(
            scope_id=scope_id,
            expected_revision=expected_revision,
            metadata=clean_metadata,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def retire_scope(
        self,
        *,
        scope_id: StableId,
        expected_revision: Revision,
        idempotency_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> KnowledgeScope:
        actor = _nonempty(actor, "actor")
        reason = _nonempty(reason, "reason")
        if self._publication_activity.has_open_publication(scope_id):
            raise DomainError(
                ErrorCode.OPEN_PUBLICATION_ATTEMPT,
                "scope cannot retire while a publication attempt is open",
                {"scope_id": scope_id.value},
            )
        request_digest = digest_of(
            {
                "command": "RetireScope@1",
                "scope_id": scope_id.value,
                "expected_revision": expected_revision.value,
                "actor": actor,
                "reason": reason,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.retire(
            scope_id=scope_id,
            expected_revision=expected_revision,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def get_scope(self, scope_id: StableId, revision: Revision | None = None) -> KnowledgeScope:
        return self._repository.get(scope_id, revision)

    def read_scope_state_assertion(
        self,
        *,
        scope_id: StableId,
        expected_revision: Revision | None,
        purpose: ScopePurpose,
        caller_ref: str,
        request_ref: str,
        classification: str,
    ) -> ScopeStateAssertion:
        return self._repository.read_state_assertion(
            scope_id=scope_id,
            expected_revision=expected_revision,
            purpose=purpose,
            caller_ref=_nonempty(caller_ref, "caller reference"),
            request_ref=_nonempty(request_ref, "request reference"),
            classification=_nonempty(classification, "classification"),
            read_at=self._now(),
        )

    def list_outbox_events(self) -> tuple[OutboxEvent, ...]:
        return self._repository.list_outbox()

    def validate_scope_state_assertion(self, assertion: ScopeStateAssertion) -> bool:
        return self._repository.validate_state_assertion(assertion)

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return a timezone-aware datetime")
        return value.astimezone(timezone.utc)
