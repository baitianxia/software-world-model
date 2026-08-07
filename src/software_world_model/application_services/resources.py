"""Application-owned hierarchical Resource Allocation contract."""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Protocol

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


@dataclass(frozen=True, slots=True)
class ResourceLimits:
    calls: int = 0
    tokens: int = 0
    duration_ms: int = 0
    result_bytes: int = 0
    cost_microunits: int = 0

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field.name} must be a non-negative integer")

    def fits_within(self, other: "ResourceLimits") -> bool:
        return all(
            getattr(self, field.name) <= getattr(other, field.name) for field in fields(self)
        )

    def add(self, other: "ResourceLimits") -> "ResourceLimits":
        return ResourceLimits(
            **{
                field.name: getattr(self, field.name) + getattr(other, field.name)
                for field in fields(self)
            }
        )

    def subtract(self, other: "ResourceLimits") -> "ResourceLimits":
        if not other.fits_within(self):
            raise ValueError("resource subtraction would become negative")
        return ResourceLimits(
            **{
                field.name: getattr(self, field.name) - getattr(other, field.name)
                for field in fields(self)
            }
        )

    def unused_after(self, charged: "ResourceLimits") -> "ResourceLimits":
        return ResourceLimits(
            **{
                field.name: max(getattr(self, field.name) - getattr(charged, field.name), 0)
                for field in fields(self)
            }
        )

    def excess_over(self, reserved: "ResourceLimits") -> "ResourceLimits":
        return ResourceLimits(
            **{
                field.name: max(getattr(self, field.name) - getattr(reserved, field.name), 0)
                for field in fields(self)
            }
        )

    def max_with(self, other: "ResourceLimits") -> "ResourceLimits":
        return ResourceLimits(
            **{
                field.name: max(getattr(self, field.name), getattr(other, field.name))
                for field in fields(self)
            }
        )

    def subtract_floor(self, other: "ResourceLimits") -> "ResourceLimits":
        return ResourceLimits(
            **{
                field.name: max(getattr(self, field.name) - getattr(other, field.name), 0)
                for field in fields(self)
            }
        )

    def is_zero(self) -> bool:
        return all(getattr(self, field.name) == 0 for field in fields(self))


@dataclass(frozen=True, slots=True)
class AllocationKey:
    owner_control_boundary: str
    owner_attempt: str
    dispatch_kind: str
    dispatch_attempt_key: str

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if not value or value != value.strip():
                raise ValueError(f"{field.name} must be non-empty")


class UsageCompleteness(str, Enum):
    UNKNOWN = "UNKNOWN"
    PARTIAL = "PARTIAL"
    COMPLETE = "COMPLETE"


class AllocationState(str, Enum):
    RESERVED = "RESERVED"
    SETTLED = "SETTLED"
    RELEASED = "RELEASED"


class CancellationOutcome(str, Enum):
    CANCELED_BEFORE_DISPATCH = "CANCELED_BEFORE_DISPATCH"


@dataclass(frozen=True, slots=True)
class ResourceAllocation:
    allocation_id: StableId
    parent_allocation_id: StableId | None
    allocation_key: AllocationKey
    allocation_request_digest: Digest
    revision: Revision
    reserved_limits: ResourceLimits
    available_limits: ResourceLimits
    observed_usage: ResourceLimits
    charged_usage: ResourceLimits
    usage_completeness: UsageCompleteness
    policy_ref: str
    conversion_rule_ref: str
    dispatch_ref: str | None
    dispatch_digest: Digest | None
    state: AllocationState
    overrun: bool
    created_at: datetime
    revised_at: datetime
    actor: str
    reason: str
    digest: Digest


class ResourceAllocationRepository(Protocol):
    def reserve_root(
        self,
        *,
        allocation_key: AllocationKey,
        reserved_limits: ResourceLimits,
        policy_ref: str,
        conversion_rule_ref: str,
        operation_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> ResourceAllocation: ...

    def reserve_child(
        self,
        *,
        parent_allocation_id: StableId,
        expected_parent_revision: Revision,
        allocation_key: AllocationKey,
        reserved_limits: ResourceLimits,
        policy_ref: str,
        conversion_rule_ref: str,
        operation_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> ResourceAllocation: ...

    def bind_dispatch(
        self,
        *,
        allocation_id: StableId,
        expected_revision: Revision,
        dispatch_ref: str,
        dispatch_digest: Digest,
        operation_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> ResourceAllocation: ...

    def report_usage(
        self,
        *,
        allocation_id: StableId,
        expected_revision: Revision,
        usage_delta: ResourceLimits,
        completeness: UsageCompleteness,
        operation_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> ResourceAllocation: ...

    def settle(
        self,
        *,
        allocation_id: StableId,
        expected_revision: Revision,
        operation_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> ResourceAllocation: ...

    def release(
        self,
        *,
        allocation_id: StableId,
        expected_revision: Revision,
        cancellation_outcome: CancellationOutcome | None,
        operation_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> ResourceAllocation: ...

    def get(self, allocation_id: StableId, revision: Revision | None = None) -> ResourceAllocation: ...


class ResourceAllocationService:
    def __init__(
        self,
        repository: ResourceAllocationRepository,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def reserve_root(
        self,
        *,
        allocation_key: AllocationKey,
        reserved_limits: ResourceLimits,
        policy_ref: str,
        conversion_rule_ref: str,
        operation_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> ResourceAllocation:
        request_digest = self._request_digest(
            "ReserveRootAllocation@1",
            {
                "allocation_key": allocation_key,
                "reserved_limits": reserved_limits,
                "policy_ref": policy_ref,
                "conversion_rule_ref": conversion_rule_ref,
            },
            actor,
            reason,
            correlation_ref,
        )
        return self._repository.reserve_root(
            allocation_key=allocation_key,
            reserved_limits=reserved_limits,
            policy_ref=_text(policy_ref, "resource policy reference"),
            conversion_rule_ref=_text(conversion_rule_ref, "conversion rule reference"),
            operation_key=operation_key,
            request_digest=request_digest,
            actor=_text(actor, "actor"),
            reason=_text(reason, "reason"),
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def reserve_child(
        self,
        *,
        parent_allocation_id: StableId,
        expected_parent_revision: Revision,
        allocation_key: AllocationKey,
        reserved_limits: ResourceLimits,
        policy_ref: str,
        conversion_rule_ref: str,
        operation_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> ResourceAllocation:
        request_digest = self._request_digest(
            "ReserveChildAllocation@1",
            {
                "parent_allocation_id": parent_allocation_id.value,
                "expected_parent_revision": expected_parent_revision.value,
                "allocation_key": allocation_key,
                "reserved_limits": reserved_limits,
                "policy_ref": policy_ref,
                "conversion_rule_ref": conversion_rule_ref,
            },
            actor,
            reason,
            correlation_ref,
        )
        return self._repository.reserve_child(
            parent_allocation_id=parent_allocation_id,
            expected_parent_revision=expected_parent_revision,
            allocation_key=allocation_key,
            reserved_limits=reserved_limits,
            policy_ref=_text(policy_ref, "resource policy reference"),
            conversion_rule_ref=_text(conversion_rule_ref, "conversion rule reference"),
            operation_key=operation_key,
            request_digest=request_digest,
            actor=_text(actor, "actor"),
            reason=_text(reason, "reason"),
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def bind_dispatch(
        self,
        *,
        allocation_id: StableId,
        expected_revision: Revision,
        dispatch_ref: str,
        dispatch_digest: Digest,
        operation_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> ResourceAllocation:
        payload = {
            "allocation_id": allocation_id.value,
            "expected_revision": expected_revision.value,
            "dispatch_ref": dispatch_ref,
            "dispatch_digest": dispatch_digest.value,
        }
        request_digest = self._request_digest(
            "BindAllocationDispatch@1", payload, actor, reason, correlation_ref
        )
        return self._repository.bind_dispatch(
            allocation_id=allocation_id,
            expected_revision=expected_revision,
            dispatch_ref=_text(dispatch_ref, "dispatch reference"),
            dispatch_digest=dispatch_digest,
            operation_key=operation_key,
            request_digest=request_digest,
            actor=_text(actor, "actor"),
            reason=_text(reason, "reason"),
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def report_usage(
        self,
        *,
        allocation_id: StableId,
        expected_revision: Revision,
        usage_delta: ResourceLimits,
        completeness: UsageCompleteness,
        operation_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> ResourceAllocation:
        request_digest = self._request_digest(
            "ReportAllocationUsage@1",
            {
                "allocation_id": allocation_id.value,
                "expected_revision": expected_revision.value,
                "usage_delta": usage_delta,
                "completeness": completeness.value,
            },
            actor,
            reason,
            correlation_ref,
        )
        return self._repository.report_usage(
            allocation_id=allocation_id,
            expected_revision=expected_revision,
            usage_delta=usage_delta,
            completeness=completeness,
            operation_key=operation_key,
            request_digest=request_digest,
            actor=_text(actor, "actor"),
            reason=_text(reason, "reason"),
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def settle(
        self,
        *,
        allocation_id: StableId,
        expected_revision: Revision,
        operation_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> ResourceAllocation:
        request_digest = self._request_digest(
            "SettleAllocation@1",
            {"allocation_id": allocation_id.value, "expected_revision": expected_revision.value},
            actor,
            reason,
            correlation_ref,
        )
        return self._repository.settle(
            allocation_id=allocation_id,
            expected_revision=expected_revision,
            operation_key=operation_key,
            request_digest=request_digest,
            actor=_text(actor, "actor"),
            reason=_text(reason, "reason"),
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def release(
        self,
        *,
        allocation_id: StableId,
        expected_revision: Revision,
        cancellation_outcome: CancellationOutcome | None,
        operation_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> ResourceAllocation:
        request_digest = self._request_digest(
            "ReleaseAllocation@1",
            {
                "allocation_id": allocation_id.value,
                "expected_revision": expected_revision.value,
                "cancellation_outcome": (
                    cancellation_outcome.value if cancellation_outcome else None
                ),
            },
            actor,
            reason,
            correlation_ref,
        )
        return self._repository.release(
            allocation_id=allocation_id,
            expected_revision=expected_revision,
            cancellation_outcome=cancellation_outcome,
            operation_key=operation_key,
            request_digest=request_digest,
            actor=_text(actor, "actor"),
            reason=_text(reason, "reason"),
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def get(self, allocation_id: StableId, revision: Revision | None = None) -> ResourceAllocation:
        return self._repository.get(allocation_id, revision)

    @staticmethod
    def _request_digest(
        command: str,
        payload: dict[str, object],
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> Digest:
        return digest_of(
            {
                "command": command,
                **payload,
                "actor": _text(actor, "actor"),
                "reason": _text(reason, "reason"),
                "correlation_ref": correlation_ref.value,
            }
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return a timezone-aware datetime")
        return value.astimezone(timezone.utc)


def _text(value: str, label: str) -> str:
    if not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value
