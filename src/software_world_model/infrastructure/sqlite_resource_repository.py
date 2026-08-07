"""SQLite hierarchical Resource Allocation ledger."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

from software_world_model.application_services.resources import (
    AllocationKey,
    AllocationState,
    CancellationOutcome,
    ResourceAllocation,
    ResourceLimits,
    UsageCompleteness,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    IdempotencyKey,
    Revision,
    StableId,
    Uuid4IdGenerator,
    canonical_json_bytes,
    digest_of,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_allocation_roots (
    allocation_id TEXT PRIMARY KEY,
    parent_allocation_id TEXT,
    parent_identity TEXT NOT NULL,
    allocation_key_json TEXT NOT NULL,
    allocation_key_digest TEXT NOT NULL,
    allocation_request_digest TEXT NOT NULL,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    state TEXT NOT NULL CHECK (state IN ('RESERVED', 'SETTLED', 'RELEASED')),
    created_at TEXT NOT NULL,
    UNIQUE (parent_identity, allocation_key_digest),
    FOREIGN KEY (parent_allocation_id) REFERENCES app_allocation_roots(allocation_id)
);

CREATE TABLE IF NOT EXISTS app_allocation_revisions (
    allocation_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    reserved_limits_json TEXT NOT NULL,
    available_limits_json TEXT NOT NULL,
    observed_usage_json TEXT NOT NULL,
    charged_usage_json TEXT NOT NULL,
    usage_completeness TEXT NOT NULL CHECK (usage_completeness IN ('UNKNOWN', 'PARTIAL', 'COMPLETE')),
    policy_ref TEXT NOT NULL,
    conversion_rule_ref TEXT NOT NULL,
    dispatch_ref TEXT,
    dispatch_digest TEXT,
    state TEXT NOT NULL CHECK (state IN ('RESERVED', 'SETTLED', 'RELEASED')),
    overrun INTEGER NOT NULL CHECK (overrun IN (0, 1)),
    actor TEXT NOT NULL,
    reason TEXT NOT NULL,
    correlation_ref TEXT NOT NULL,
    revised_at TEXT NOT NULL,
    allocation_digest TEXT NOT NULL,
    PRIMARY KEY (allocation_id, revision),
    FOREIGN KEY (allocation_id) REFERENCES app_allocation_roots(allocation_id)
);

CREATE TABLE IF NOT EXISTS app_allocation_idempotency (
    operation_key TEXT PRIMARY KEY,
    command_type TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    result_allocation_id TEXT NOT NULL,
    result_revision INTEGER NOT NULL,
    FOREIGN KEY (result_allocation_id, result_revision)
        REFERENCES app_allocation_revisions(allocation_id, revision)
);

CREATE TABLE IF NOT EXISTS app_allocation_outbox (
    event_id TEXT PRIMARY KEY,
    allocation_id TEXT NOT NULL,
    allocation_revision INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload_digest TEXT NOT NULL,
    correlation_ref TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    delivered_at TEXT,
    UNIQUE (allocation_id, allocation_revision, event_type),
    FOREIGN KEY (allocation_id, allocation_revision)
        REFERENCES app_allocation_revisions(allocation_id, revision)
);
"""


class SqliteResourceAllocationRepository:
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

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
    ) -> ResourceAllocation:
        return self._reserve(
            parent_allocation_id=None,
            expected_parent_revision=None,
            allocation_key=allocation_key,
            reserved_limits=reserved_limits,
            policy_ref=policy_ref,
            conversion_rule_ref=conversion_rule_ref,
            operation_key=operation_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            occurred_at=occurred_at,
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
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> ResourceAllocation:
        return self._reserve(
            parent_allocation_id=parent_allocation_id,
            expected_parent_revision=expected_parent_revision,
            allocation_key=allocation_key,
            reserved_limits=reserved_limits,
            policy_ref=policy_ref,
            conversion_rule_ref=conversion_rule_ref,
            operation_key=operation_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            occurred_at=occurred_at,
        )

    def _reserve(
        self,
        *,
        parent_allocation_id: StableId | None,
        expected_parent_revision: Revision | None,
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
    ) -> ResourceAllocation:
        command_type = "ReserveRootAllocation@1" if parent_allocation_id is None else "ReserveChildAllocation@1"
        parent_identity = parent_allocation_id.value if parent_allocation_id else "ROOT"
        key_digest = digest_of(allocation_key)
        allocation_request_digest = digest_of(
            {
                "parent_allocation_id": (
                    parent_allocation_id.value if parent_allocation_id else None
                ),
                "allocation_key": allocation_key,
                "reserved_limits": reserved_limits,
                "policy_ref": policy_ref,
                "conversion_rule_ref": conversion_rule_ref,
            }
        )
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, operation_key, command_type, request_digest
                )
                if replay is not None:
                    return replay
                existing = connection.execute(
                    """SELECT allocation_id, allocation_request_digest
                       FROM app_allocation_roots
                       WHERE parent_identity = ? AND allocation_key_digest = ?""",
                    (parent_identity, key_digest.value),
                ).fetchone()
                if existing is not None:
                    if existing["allocation_request_digest"] != allocation_request_digest.value:
                        raise DomainError(
                            ErrorCode.ALLOCATION_KEY_CONFLICT,
                            "allocation key was reused for different reserved limits or policy",
                        )
                    current = self._load(
                        connection, StableId(existing["allocation_id"]), None
                    )
                    self._insert_idempotency(
                        connection, operation_key, command_type, request_digest, current
                    )
                    return current
                parent = None
                if parent_allocation_id is not None:
                    parent = self._load(connection, parent_allocation_id, None)
                    _require_revision(parent, expected_parent_revision)
                    if parent.state is not AllocationState.RESERVED or parent.overrun:
                        raise DomainError(
                            ErrorCode.ALLOCATION_STATE_CONFLICT,
                            "parent allocation cannot reserve another child",
                        )
                    if (
                        parent.dispatch_ref is not None
                        or not parent.observed_usage.is_zero()
                        or parent.usage_completeness is UsageCompleteness.COMPLETE
                    ):
                        raise DomainError(
                            ErrorCode.ALLOCATION_STATE_CONFLICT,
                            "a direct-dispatch allocation cannot also become a parent budget",
                        )
                    if not reserved_limits.fits_within(parent.available_limits):
                        raise DomainError(
                            ErrorCode.BUDGET_EXHAUSTED,
                            "requested child limits exceed the parent's available balance",
                        )
                allocation = self._build(
                    allocation_id=self._ids.new("allocation"),
                    parent_allocation_id=parent_allocation_id,
                    allocation_key=allocation_key,
                    allocation_request_digest=allocation_request_digest,
                    revision=Revision(1),
                    reserved_limits=reserved_limits,
                    available_limits=reserved_limits,
                    observed_usage=ResourceLimits(),
                    charged_usage=ResourceLimits(),
                    usage_completeness=UsageCompleteness.UNKNOWN,
                    policy_ref=policy_ref,
                    conversion_rule_ref=conversion_rule_ref,
                    dispatch_ref=None,
                    dispatch_digest=None,
                    state=AllocationState.RESERVED,
                    overrun=False,
                    created_at=occurred_at,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                connection.execute(
                    """INSERT INTO app_allocation_roots
                       (allocation_id, parent_allocation_id, parent_identity,
                        allocation_key_json, allocation_key_digest, allocation_request_digest,
                        current_revision, state, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        allocation.allocation_id.value,
                        parent_allocation_id.value if parent_allocation_id else None,
                        parent_identity,
                        canonical_json_bytes(allocation_key).decode("utf-8"),
                        key_digest.value,
                        allocation_request_digest.value,
                        1,
                        AllocationState.RESERVED.value,
                        _time(occurred_at),
                    ),
                )
                self._insert_revision(connection, allocation, correlation_ref)
                self._insert_idempotency(
                    connection, operation_key, command_type, request_digest, allocation
                )
                self._insert_outbox(
                    connection, allocation, "RESOURCE_ALLOCATION_RESERVED@1", correlation_ref
                )
                if parent is not None:
                    revised_parent = self._revise(
                        parent,
                        revision=parent.revision.next(),
                        available_limits=parent.available_limits.subtract(reserved_limits),
                        revised_at=occurred_at,
                        actor=actor,
                        reason=f"reserve child {allocation.allocation_id.value}",
                    )
                    self._advance(connection, parent, revised_parent, correlation_ref)
                    self._insert_outbox(
                        connection,
                        revised_parent,
                        "RESOURCE_ALLOCATION_CHILD_RESERVED@1",
                        correlation_ref,
                    )
                return allocation
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise self._integrity_error(exc) from exc

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
    ) -> ResourceAllocation:
        command_type = "BindAllocationDispatch@1"
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, operation_key, command_type, request_digest
                )
                if replay is not None:
                    return replay
                current = self._load(connection, allocation_id, None)
                _require_revision(current, expected_revision)
                self._require_reserved(current)
                self._require_no_children(connection, allocation_id)
                if current.dispatch_ref is not None:
                    if (
                        current.dispatch_ref == dispatch_ref
                        and current.dispatch_digest == dispatch_digest
                    ):
                        self._insert_idempotency(
                            connection, operation_key, command_type, request_digest, current
                        )
                        return current
                    raise DomainError(
                        ErrorCode.ALLOCATION_STATE_CONFLICT,
                        "allocation is already bound to another dispatch",
                    )
                revised = self._revise(
                    current,
                    revision=current.revision.next(),
                    dispatch_ref=dispatch_ref,
                    dispatch_digest=dispatch_digest,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                self._advance(connection, current, revised, correlation_ref)
                self._insert_idempotency(
                    connection, operation_key, command_type, request_digest, revised
                )
                self._insert_outbox(
                    connection, revised, "RESOURCE_ALLOCATION_DISPATCH_BOUND@1", correlation_ref
                )
                return revised
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise self._integrity_error(exc) from exc

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
    ) -> ResourceAllocation:
        command_type = "ReportAllocationUsage@1"
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, operation_key, command_type, request_digest
                )
                if replay is not None:
                    return replay
                current = self._load(connection, allocation_id, None)
                _require_revision(current, expected_revision)
                self._require_reserved(current)
                self._require_no_children(connection, allocation_id)
                rank = {
                    UsageCompleteness.UNKNOWN: 0,
                    UsageCompleteness.PARTIAL: 1,
                    UsageCompleteness.COMPLETE: 2,
                }
                if current.usage_completeness is UsageCompleteness.COMPLETE:
                    raise DomainError(
                        ErrorCode.ALLOCATION_STATE_CONFLICT,
                        "complete usage cannot accept another report",
                    )
                if rank[completeness] < rank[current.usage_completeness]:
                    raise DomainError(
                        ErrorCode.ALLOCATION_STATE_CONFLICT,
                        "usage completeness cannot regress",
                    )
                observed = current.observed_usage.add(usage_delta)
                revised = self._revise(
                    current,
                    revision=current.revision.next(),
                    observed_usage=observed,
                    usage_completeness=completeness,
                    overrun=current.overrun or not observed.fits_within(current.reserved_limits),
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                self._advance(connection, current, revised, correlation_ref)
                self._insert_idempotency(
                    connection, operation_key, command_type, request_digest, revised
                )
                self._insert_outbox(
                    connection, revised, "RESOURCE_ALLOCATION_USAGE_REPORTED@1", correlation_ref
                )
                return revised
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise self._integrity_error(exc) from exc

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
    ) -> ResourceAllocation:
        command_type = "SettleAllocation@1"
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, operation_key, command_type, request_digest
                )
                if replay is not None:
                    return replay
                current = self._load(connection, allocation_id, None)
                _require_revision(current, expected_revision)
                self._require_reserved(current)
                self._require_no_reserved_children(connection, allocation_id)
                has_children = self._has_children(connection, allocation_id)
                if has_children:
                    charged = current.charged_usage
                    settled_completeness = UsageCompleteness.COMPLETE
                else:
                    charged = (
                        current.observed_usage
                        if current.usage_completeness is UsageCompleteness.COMPLETE
                        else current.reserved_limits.max_with(current.observed_usage)
                    )
                    settled_completeness = current.usage_completeness
                settled = self._revise(
                    current,
                    revision=current.revision.next(),
                    available_limits=ResourceLimits(),
                    charged_usage=charged,
                    usage_completeness=settled_completeness,
                    state=AllocationState.SETTLED,
                    overrun=current.overrun or not charged.fits_within(current.reserved_limits),
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                self._advance(connection, current, settled, correlation_ref)
                self._settle_parent(
                    connection,
                    child=current,
                    charged=charged,
                    actor=actor,
                    correlation_ref=correlation_ref,
                    occurred_at=occurred_at,
                )
                self._insert_idempotency(
                    connection, operation_key, command_type, request_digest, settled
                )
                self._insert_outbox(
                    connection, settled, "RESOURCE_ALLOCATION_SETTLED@1", correlation_ref
                )
                return settled
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise self._integrity_error(exc) from exc

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
    ) -> ResourceAllocation:
        command_type = "ReleaseAllocation@1"
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, operation_key, command_type, request_digest
                )
                if replay is not None:
                    return replay
                current = self._load(connection, allocation_id, None)
                _require_revision(current, expected_revision)
                self._require_reserved(current)
                self._require_no_reserved_children(connection, allocation_id)
                if not current.observed_usage.is_zero():
                    raise DomainError(
                        ErrorCode.ALLOCATION_STATE_CONFLICT,
                        "allocation with observed usage must be settled, not released",
                    )
                if (
                    current.dispatch_ref is not None
                    and cancellation_outcome is not CancellationOutcome.CANCELED_BEFORE_DISPATCH
                ):
                    raise DomainError(
                        ErrorCode.ALLOCATION_STATE_CONFLICT,
                        "bound allocation requires an exact canceled-before-dispatch outcome",
                    )
                released = self._revise(
                    current,
                    revision=current.revision.next(),
                    available_limits=ResourceLimits(),
                    state=AllocationState.RELEASED,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                self._advance(connection, current, released, correlation_ref)
                self._release_to_parent(
                    connection,
                    child=current,
                    actor=actor,
                    correlation_ref=correlation_ref,
                    occurred_at=occurred_at,
                )
                self._insert_idempotency(
                    connection, operation_key, command_type, request_digest, released
                )
                self._insert_outbox(
                    connection, released, "RESOURCE_ALLOCATION_RELEASED@1", correlation_ref
                )
                return released
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise self._integrity_error(exc) from exc

    def get(
        self, allocation_id: StableId, revision: Revision | None = None
    ) -> ResourceAllocation:
        with self._database.read() as connection:
            return self._load(connection, allocation_id, revision)

    def _settle_parent(
        self,
        connection: sqlite3.Connection,
        *,
        child: ResourceAllocation,
        charged: ResourceLimits,
        actor: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> None:
        if child.parent_allocation_id is None:
            return
        parent = self._load(connection, child.parent_allocation_id, None)
        self._require_reserved(parent)
        unused = child.reserved_limits.unused_after(charged)
        excess = charged.excess_over(child.reserved_limits)
        revised_parent = self._revise(
            parent,
            revision=parent.revision.next(),
            available_limits=parent.available_limits.add(unused).subtract_floor(excess),
            charged_usage=parent.charged_usage.add(charged),
            overrun=parent.overrun or not excess.is_zero(),
            revised_at=occurred_at,
            actor=actor,
            reason=f"settle child {child.allocation_id.value}",
        )
        self._advance(connection, parent, revised_parent, correlation_ref)
        self._insert_outbox(
            connection,
            revised_parent,
            "RESOURCE_ALLOCATION_CHILD_SETTLED@1",
            correlation_ref,
        )

    def _release_to_parent(
        self,
        connection: sqlite3.Connection,
        *,
        child: ResourceAllocation,
        actor: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> None:
        if child.parent_allocation_id is None:
            return
        parent = self._load(connection, child.parent_allocation_id, None)
        self._require_reserved(parent)
        revised_parent = self._revise(
            parent,
            revision=parent.revision.next(),
            available_limits=parent.available_limits.add(child.reserved_limits),
            revised_at=occurred_at,
            actor=actor,
            reason=f"release child {child.allocation_id.value}",
        )
        self._advance(connection, parent, revised_parent, correlation_ref)
        self._insert_outbox(
            connection,
            revised_parent,
            "RESOURCE_ALLOCATION_CHILD_RELEASED@1",
            correlation_ref,
        )

    @staticmethod
    def _require_no_reserved_children(
        connection: sqlite3.Connection, allocation_id: StableId
    ) -> None:
        row = connection.execute(
            """SELECT 1 FROM app_allocation_roots
               WHERE parent_allocation_id = ? AND state = 'RESERVED' LIMIT 1""",
            (allocation_id.value,),
        ).fetchone()
        if row is not None:
            raise DomainError(
                ErrorCode.ALLOCATION_STATE_CONFLICT,
                "allocation cannot become terminal while a child remains reserved",
            )

    @staticmethod
    def _has_children(connection: sqlite3.Connection, allocation_id: StableId) -> bool:
        row = connection.execute(
            """SELECT 1 FROM app_allocation_roots
               WHERE parent_allocation_id = ? LIMIT 1""",
            (allocation_id.value,),
        ).fetchone()
        return row is not None

    @classmethod
    def _require_no_children(
        cls, connection: sqlite3.Connection, allocation_id: StableId
    ) -> None:
        if cls._has_children(connection, allocation_id):
            raise DomainError(
                ErrorCode.ALLOCATION_STATE_CONFLICT,
                "a parent budget allocation cannot bind or report direct dispatch usage",
            )

    @staticmethod
    def _require_reserved(allocation: ResourceAllocation) -> None:
        if allocation.state is not AllocationState.RESERVED:
            raise DomainError(
                ErrorCode.ALLOCATION_STATE_CONFLICT,
                "resource allocation is already terminal",
            )

    def _idempotent_result(
        self,
        connection: sqlite3.Connection,
        operation_key: IdempotencyKey,
        command_type: str,
        request_digest: Digest,
    ) -> ResourceAllocation | None:
        row = connection.execute(
            """SELECT command_type, request_digest, result_allocation_id, result_revision
               FROM app_allocation_idempotency WHERE operation_key = ?""",
            (operation_key.value,),
        ).fetchone()
        if row is None:
            return None
        if row["command_type"] != command_type or row["request_digest"] != request_digest.value:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "resource operation key was used for a different request",
            )
        return self._load(
            connection,
            StableId(row["result_allocation_id"]),
            Revision(row["result_revision"]),
        )

    @staticmethod
    def _insert_idempotency(
        connection: sqlite3.Connection,
        operation_key: IdempotencyKey,
        command_type: str,
        request_digest: Digest,
        result: ResourceAllocation,
    ) -> None:
        connection.execute(
            "INSERT INTO app_allocation_idempotency VALUES (?, ?, ?, ?, ?)",
            (
                operation_key.value,
                command_type,
                request_digest.value,
                result.allocation_id.value,
                result.revision.value,
            ),
        )

    def _load(
        self,
        connection: sqlite3.Connection,
        allocation_id: StableId,
        revision: Revision | None,
    ) -> ResourceAllocation:
        if revision is None:
            row = connection.execute(
                """SELECT root.*, r.revision, r.reserved_limits_json,
                          r.available_limits_json, r.observed_usage_json,
                          r.charged_usage_json, r.usage_completeness, r.policy_ref,
                          r.conversion_rule_ref, r.dispatch_ref, r.dispatch_digest,
                          r.state AS revision_state, r.overrun, r.actor, r.reason,
                          r.revised_at, r.allocation_digest
                   FROM app_allocation_roots root
                   JOIN app_allocation_revisions r
                     ON r.allocation_id = root.allocation_id
                    AND r.revision = root.current_revision
                   WHERE root.allocation_id = ?""",
                (allocation_id.value,),
            ).fetchone()
        else:
            row = connection.execute(
                """SELECT root.*, r.revision, r.reserved_limits_json,
                          r.available_limits_json, r.observed_usage_json,
                          r.charged_usage_json, r.usage_completeness, r.policy_ref,
                          r.conversion_rule_ref, r.dispatch_ref, r.dispatch_digest,
                          r.state AS revision_state, r.overrun, r.actor, r.reason,
                          r.revised_at, r.allocation_digest
                   FROM app_allocation_roots root
                   JOIN app_allocation_revisions r ON r.allocation_id = root.allocation_id
                   WHERE root.allocation_id = ? AND r.revision = ?""",
                (allocation_id.value, revision.value),
            ).fetchone()
        if row is None:
            raise DomainError(
                ErrorCode.RESOURCE_RESERVATION_FAILED,
                "resource allocation or requested revision does not exist",
                {"allocation_id": allocation_id.value},
            )
        key_data = json.loads(row["allocation_key_json"])
        allocation_key = AllocationKey(**key_data)
        return ResourceAllocation(
            allocation_id=StableId(row["allocation_id"]),
            parent_allocation_id=(
                StableId(row["parent_allocation_id"])
                if row["parent_allocation_id"] is not None
                else None
            ),
            allocation_key=allocation_key,
            allocation_request_digest=Digest(row["allocation_request_digest"]),
            revision=Revision(row["revision"]),
            reserved_limits=_limits(row["reserved_limits_json"]),
            available_limits=_limits(row["available_limits_json"]),
            observed_usage=_limits(row["observed_usage_json"]),
            charged_usage=_limits(row["charged_usage_json"]),
            usage_completeness=UsageCompleteness(row["usage_completeness"]),
            policy_ref=row["policy_ref"],
            conversion_rule_ref=row["conversion_rule_ref"],
            dispatch_ref=row["dispatch_ref"],
            dispatch_digest=(
                Digest(row["dispatch_digest"])
                if row["dispatch_digest"] is not None
                else None
            ),
            state=AllocationState(row["revision_state"]),
            overrun=bool(row["overrun"]),
            created_at=_parse_time(row["created_at"]),
            revised_at=_parse_time(row["revised_at"]),
            actor=row["actor"],
            reason=row["reason"],
            digest=Digest(row["allocation_digest"]),
        )

    @staticmethod
    def _build(
        *,
        allocation_id: StableId,
        parent_allocation_id: StableId | None,
        allocation_key: AllocationKey,
        allocation_request_digest: Digest,
        revision: Revision,
        reserved_limits: ResourceLimits,
        available_limits: ResourceLimits,
        observed_usage: ResourceLimits,
        charged_usage: ResourceLimits,
        usage_completeness: UsageCompleteness,
        policy_ref: str,
        conversion_rule_ref: str,
        dispatch_ref: str | None,
        dispatch_digest: Digest | None,
        state: AllocationState,
        overrun: bool,
        created_at: datetime,
        revised_at: datetime,
        actor: str,
        reason: str,
    ) -> ResourceAllocation:
        core = {
            "allocation_id": allocation_id.value,
            "parent_allocation_id": (
                parent_allocation_id.value if parent_allocation_id else None
            ),
            "allocation_key": allocation_key,
            "allocation_request_digest": allocation_request_digest.value,
            "revision": revision.value,
            "reserved_limits": reserved_limits,
            "available_limits": available_limits,
            "observed_usage": observed_usage,
            "charged_usage": charged_usage,
            "usage_completeness": usage_completeness.value,
            "policy_ref": policy_ref,
            "conversion_rule_ref": conversion_rule_ref,
            "dispatch_ref": dispatch_ref,
            "dispatch_digest": dispatch_digest.value if dispatch_digest else None,
            "state": state.value,
            "overrun": overrun,
            "created_at": created_at,
            "revised_at": revised_at,
        }
        return ResourceAllocation(
            allocation_id=allocation_id,
            parent_allocation_id=parent_allocation_id,
            allocation_key=allocation_key,
            allocation_request_digest=allocation_request_digest,
            revision=revision,
            reserved_limits=reserved_limits,
            available_limits=available_limits,
            observed_usage=observed_usage,
            charged_usage=charged_usage,
            usage_completeness=usage_completeness,
            policy_ref=policy_ref,
            conversion_rule_ref=conversion_rule_ref,
            dispatch_ref=dispatch_ref,
            dispatch_digest=dispatch_digest,
            state=state,
            overrun=overrun,
            created_at=created_at,
            revised_at=revised_at,
            actor=actor,
            reason=reason,
            digest=digest_of(core),
        )

    def _revise(self, current: ResourceAllocation, **changes: object) -> ResourceAllocation:
        values: dict[str, object] = {
            "allocation_id": current.allocation_id,
            "parent_allocation_id": current.parent_allocation_id,
            "allocation_key": current.allocation_key,
            "allocation_request_digest": current.allocation_request_digest,
            "revision": current.revision,
            "reserved_limits": current.reserved_limits,
            "available_limits": current.available_limits,
            "observed_usage": current.observed_usage,
            "charged_usage": current.charged_usage,
            "usage_completeness": current.usage_completeness,
            "policy_ref": current.policy_ref,
            "conversion_rule_ref": current.conversion_rule_ref,
            "dispatch_ref": current.dispatch_ref,
            "dispatch_digest": current.dispatch_digest,
            "state": current.state,
            "overrun": current.overrun,
            "created_at": current.created_at,
            "revised_at": current.revised_at,
            "actor": current.actor,
            "reason": current.reason,
        }
        values.update(changes)
        return self._build(**values)  # type: ignore[arg-type]

    @staticmethod
    def _insert_revision(
        connection: sqlite3.Connection,
        allocation: ResourceAllocation,
        correlation_ref: CorrelationRef,
    ) -> None:
        connection.execute(
            """INSERT INTO app_allocation_revisions
               (allocation_id, revision, reserved_limits_json, available_limits_json,
                observed_usage_json, charged_usage_json, usage_completeness,
                policy_ref, conversion_rule_ref, dispatch_ref, dispatch_digest,
                state, overrun, actor, reason, correlation_ref, revised_at,
                allocation_digest)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                allocation.allocation_id.value,
                allocation.revision.value,
                canonical_json_bytes(allocation.reserved_limits).decode("utf-8"),
                canonical_json_bytes(allocation.available_limits).decode("utf-8"),
                canonical_json_bytes(allocation.observed_usage).decode("utf-8"),
                canonical_json_bytes(allocation.charged_usage).decode("utf-8"),
                allocation.usage_completeness.value,
                allocation.policy_ref,
                allocation.conversion_rule_ref,
                allocation.dispatch_ref,
                allocation.dispatch_digest.value if allocation.dispatch_digest else None,
                allocation.state.value,
                int(allocation.overrun),
                allocation.actor,
                allocation.reason,
                correlation_ref.value,
                _time(allocation.revised_at),
                allocation.digest.value,
            ),
        )

    def _advance(
        self,
        connection: sqlite3.Connection,
        current: ResourceAllocation,
        revised: ResourceAllocation,
        correlation_ref: CorrelationRef,
    ) -> None:
        self._insert_revision(connection, revised, correlation_ref)
        cursor = connection.execute(
            """UPDATE app_allocation_roots SET current_revision = ?, state = ?
               WHERE allocation_id = ? AND current_revision = ?""",
            (
                revised.revision.value,
                revised.state.value,
                current.allocation_id.value,
                current.revision.value,
            ),
        )
        if cursor.rowcount != 1:
            raise DomainError(
                ErrorCode.ALLOCATION_STATE_CONFLICT,
                "allocation revision changed before commit",
            )

    def _insert_outbox(
        self,
        connection: sqlite3.Connection,
        allocation: ResourceAllocation,
        event_type: str,
        correlation_ref: CorrelationRef,
    ) -> None:
        payload_digest = digest_of(
            {
                "owner": "APPLICATION_SERVICES",
                "allocation_id": allocation.allocation_id.value,
                "allocation_revision": allocation.revision.value,
                "allocation_digest": allocation.digest.value,
                "event_type": event_type,
            }
        )
        connection.execute(
            """INSERT INTO app_allocation_outbox
               (event_id, allocation_id, allocation_revision, event_type,
                payload_digest, correlation_ref, occurred_at, delivered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, NULL)""",
            (
                self._ids.new("outbox_event").value,
                allocation.allocation_id.value,
                allocation.revision.value,
                event_type,
                payload_digest.value,
                correlation_ref.value,
                _time(allocation.revised_at),
            ),
        )

    @staticmethod
    def _integrity_error(exc: sqlite3.IntegrityError) -> DomainError:
        message = str(exc)
        if "app_allocation_roots.parent_identity" in message:
            return DomainError(
                ErrorCode.ALLOCATION_KEY_CONFLICT,
                "allocation key already identifies another reservation",
            )
        return DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "resource allocation transaction violated a store invariant",
            {"sqlite_error": message},
        )


def _require_revision(
    allocation: ResourceAllocation, expected_revision: Revision | None
) -> None:
    if expected_revision is None or allocation.revision != expected_revision:
        raise DomainError(
            ErrorCode.ALLOCATION_STATE_CONFLICT,
            "expected allocation revision is stale",
            {
                "actual_revision": allocation.revision.value,
                "expected_revision": expected_revision.value if expected_revision else 0,
            },
        )


def _limits(value: str) -> ResourceLimits:
    return ResourceLimits(**json.loads(value))


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))
