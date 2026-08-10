"""SQLite implementation of the KnowledgeScope owner repository port."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

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
from software_world_model.knowledge_engine.scope import (
    AssertionOutcome,
    KnowledgeScope,
    Metadata,
    OutboxEvent,
    ScopeLifecycle,
    ScopePurpose,
    ScopeStateAssertion,
    ScopeType,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS knw_scope_roots (
    scope_id TEXT PRIMARY KEY,
    scope_type TEXT NOT NULL,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    lifecycle TEXT NOT NULL CHECK (lifecycle IN ('ACTIVE', 'RETIRED')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knw_scope_revisions (
    scope_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    lifecycle TEXT NOT NULL CHECK (lifecycle IN ('ACTIVE', 'RETIRED')),
    metadata_json TEXT NOT NULL,
    actor TEXT NOT NULL,
    reason TEXT NOT NULL,
    correlation_ref TEXT NOT NULL,
    revised_at TEXT NOT NULL,
    definition_digest TEXT NOT NULL,
    PRIMARY KEY (scope_id, revision),
    FOREIGN KEY (scope_id) REFERENCES knw_scope_roots(scope_id)
);

CREATE TABLE IF NOT EXISTS knw_scope_idempotency (
    idempotency_key TEXT PRIMARY KEY,
    command_type TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    result_scope_id TEXT NOT NULL,
    result_revision INTEGER NOT NULL,
    FOREIGN KEY (result_scope_id, result_revision)
        REFERENCES knw_scope_revisions(scope_id, revision)
);

CREATE TABLE IF NOT EXISTS knw_scope_assertions (
    assertion_id TEXT PRIMARY KEY,
    assertion_digest TEXT NOT NULL UNIQUE,
    scope_id TEXT NOT NULL,
    scope_revision INTEGER NOT NULL,
    purpose TEXT NOT NULL,
    core_json TEXT NOT NULL,
    FOREIGN KEY (scope_id, scope_revision)
        REFERENCES knw_scope_revisions(scope_id, revision)
);

CREATE TABLE IF NOT EXISTS knw_scope_assertion_reads (
    read_key_digest TEXT PRIMARY KEY,
    request_digest TEXT NOT NULL,
    assertion_id TEXT NOT NULL UNIQUE,
    FOREIGN KEY (assertion_id) REFERENCES knw_scope_assertions(assertion_id)
);

CREATE TABLE IF NOT EXISTS knw_scope_outbox (
    event_id TEXT PRIMARY KEY,
    aggregate_id TEXT NOT NULL,
    authority_revision INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    payload_digest TEXT NOT NULL,
    correlation_ref TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    delivered_at TEXT,
    UNIQUE (aggregate_id, authority_revision, event_type),
    FOREIGN KEY (aggregate_id, authority_revision)
        REFERENCES knw_scope_revisions(scope_id, revision)
);
"""


class SqliteKnowledgeScopeRepository:
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)
        self._migrate_scope_assertion_reads()

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
    ) -> KnowledgeScope:
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, idempotency_key, "CreateScope@1", request_digest
                )
                if replay is not None:
                    return replay
                scope_id = self._ids.new("scope")
                revision = Revision(1)
                scope = self._build_scope(
                    scope_id=scope_id,
                    scope_type=scope_type,
                    lifecycle=ScopeLifecycle.ACTIVE,
                    revision=revision,
                    metadata=metadata,
                    created_at=occurred_at,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                connection.execute(
                    "INSERT INTO knw_scope_roots VALUES (?, ?, ?, ?, ?)",
                    (scope_id.value, scope_type.value, 1, ScopeLifecycle.ACTIVE.value, _time(occurred_at)),
                )
                self._insert_revision(connection, scope, correlation_ref)
                self._insert_idempotency(
                    connection, idempotency_key, "CreateScope@1", request_digest, scope
                )
                self._insert_outbox(connection, scope, "KNOWLEDGE_SCOPE_CREATED@1", correlation_ref)
                return scope
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

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
    ) -> KnowledgeScope:
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, idempotency_key, "UpdateScopeMetadata@1", request_digest
                )
                if replay is not None:
                    return replay
                current = self._load_scope(connection, scope_id, None)
                self._require_expected(current, expected_revision)
                if current.lifecycle is ScopeLifecycle.RETIRED:
                    raise DomainError(ErrorCode.SCOPE_RETIRED, "retired scopes cannot be revised")
                if current.metadata == metadata:
                    self._insert_idempotency(
                        connection,
                        idempotency_key,
                        "UpdateScopeMetadata@1",
                        request_digest,
                        current,
                    )
                    return current
                revised = self._build_scope(
                    scope_id=scope_id,
                    scope_type=current.scope_type,
                    lifecycle=current.lifecycle,
                    revision=current.definition_revision.next(),
                    metadata=metadata,
                    created_at=current.created_at,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                self._advance_root(connection, current, revised)
                self._insert_revision(connection, revised, correlation_ref)
                self._insert_idempotency(
                    connection, idempotency_key, "UpdateScopeMetadata@1", request_digest, revised
                )
                self._insert_outbox(connection, revised, "KNOWLEDGE_SCOPE_METADATA_UPDATED@1", correlation_ref)
                return revised
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

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
    ) -> KnowledgeScope:
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, idempotency_key, "RetireScope@1", request_digest
                )
                if replay is not None:
                    return replay
                current = self._load_scope(connection, scope_id, None)
                self._require_expected(current, expected_revision)
                if current.lifecycle is ScopeLifecycle.RETIRED:
                    raise DomainError(ErrorCode.SCOPE_RETIRED, "scope is already retired")
                retired = self._build_scope(
                    scope_id=scope_id,
                    scope_type=current.scope_type,
                    lifecycle=ScopeLifecycle.RETIRED,
                    revision=current.definition_revision.next(),
                    metadata=current.metadata,
                    created_at=current.created_at,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                self._advance_root(connection, current, retired)
                self._insert_revision(connection, retired, correlation_ref)
                self._insert_idempotency(
                    connection, idempotency_key, "RetireScope@1", request_digest, retired
                )
                self._insert_outbox(connection, retired, "KNOWLEDGE_SCOPE_RETIRED@1", correlation_ref)
                return retired
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

    def get(self, scope_id: StableId, revision: Revision | None = None) -> KnowledgeScope:
        with self._database.read() as connection:
            return self._load_scope(connection, scope_id, revision)

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
    ) -> ScopeStateAssertion:
        try:
            with self._database.transaction() as connection:
                scope = self._load_scope(connection, scope_id, None)
                if expected_revision is not None:
                    self._require_expected(scope, expected_revision)
                outcome = (
                    AssertionOutcome.ELIGIBLE
                    if scope.lifecycle is ScopeLifecycle.ACTIVE
                    else AssertionOutcome.INELIGIBLE
                )
                read_key_digest = _scope_assertion_read_key(
                    scope_id=scope.scope_id,
                    purpose=purpose,
                    caller_ref=caller_ref,
                    request_ref=request_ref,
                    classification=classification,
                )
                request_digest = _scope_assertion_request_digest(
                    scope=scope,
                    purpose=purpose,
                    outcome=outcome,
                    caller_ref=caller_ref,
                    request_ref=request_ref,
                    classification=classification,
                )
                replay = connection.execute(
                    """SELECT request_digest, assertion_id
                       FROM knw_scope_assertion_reads
                       WHERE read_key_digest = ?""",
                    (read_key_digest.value,),
                ).fetchone()
                if replay is not None:
                    if replay["request_digest"] != request_digest.value:
                        raise DomainError(
                            ErrorCode.IDEMPOTENCY_MISMATCH,
                            "scope assertion request reference was reused for different authority state",
                            {"request_ref": request_ref},
                        )
                    return self._load_assertion(
                        connection, StableId(replay["assertion_id"])
                    )
                core = {
                    "scope_id": scope.scope_id.value,
                    "scope_type": scope.scope_type.value,
                    "definition_revision": scope.definition_revision.value,
                    "lifecycle": scope.lifecycle.value,
                    "purpose": purpose.value,
                    "outcome": outcome.value,
                    "caller_ref": caller_ref,
                    "request_ref": request_ref,
                    "classification": classification,
                    "read_at": read_at,
                }
                assertion_digest = digest_of(core)
                assertion = ScopeStateAssertion(
                    assertion_id=self._ids.new("scope_assertion"),
                    scope_id=scope.scope_id,
                    scope_type=scope.scope_type,
                    definition_revision=scope.definition_revision,
                    lifecycle=scope.lifecycle,
                    purpose=purpose,
                    outcome=outcome,
                    caller_ref=caller_ref,
                    request_ref=request_ref,
                    classification=classification,
                    read_at=read_at,
                    digest=assertion_digest,
                )
                connection.execute(
                    """INSERT INTO knw_scope_assertions
                       (assertion_id, assertion_digest, scope_id, scope_revision, purpose, core_json)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        assertion.assertion_id.value,
                        assertion.digest.value,
                        scope.scope_id.value,
                        scope.definition_revision.value,
                        purpose.value,
                        canonical_json_bytes(core).decode("utf-8"),
                    ),
                )
                connection.execute(
                    "INSERT INTO knw_scope_assertion_reads VALUES (?, ?, ?)",
                    (
                        read_key_digest.value,
                        request_digest.value,
                        assertion.assertion_id.value,
                    ),
                )
                return assertion
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

    def list_outbox(self) -> tuple[OutboxEvent, ...]:
        with self._database.read() as connection:
            rows = connection.execute(
                """SELECT event_id, aggregate_id, authority_revision, event_type,
                          payload_digest, occurred_at
                   FROM knw_scope_outbox ORDER BY rowid"""
            ).fetchall()
        return tuple(
            OutboxEvent(
                event_id=StableId(row["event_id"]),
                owner="KNOWLEDGE_ENGINE",
                aggregate_id=StableId(row["aggregate_id"]),
                authority_revision=Revision(row["authority_revision"]),
                event_type=row["event_type"],
                payload_digest=Digest(row["payload_digest"]),
                occurred_at=_parse_time(row["occurred_at"]),
            )
            for row in rows
        )

    def validate_state_assertion(self, assertion: ScopeStateAssertion) -> bool:
        if not assertion.verify_digest():
            return False
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT a.assertion_digest, a.scope_id, a.scope_revision, a.purpose,
                          a.core_json, root.current_revision, root.lifecycle
                   FROM knw_scope_assertions a
                   JOIN knw_scope_roots root ON root.scope_id = a.scope_id
                   WHERE a.assertion_id = ?""",
                (assertion.assertion_id.value,),
            ).fetchone()
        if row is None:
            return False
        return (
            row["assertion_digest"] == assertion.digest.value
            and row["scope_id"] == assertion.scope_id.value
            and row["scope_revision"] == assertion.definition_revision.value
            and row["current_revision"] == assertion.definition_revision.value
            and row["lifecycle"] == assertion.lifecycle.value
            and row["purpose"] == assertion.purpose.value
            and row["core_json"] == canonical_json_bytes(assertion.core()).decode("utf-8")
        )

    def _migrate_scope_assertion_reads(self) -> None:
        """Backfill stable read identities for assertions written before this table existed."""

        with self._database.transaction() as connection:
            rows = connection.execute(
                """SELECT assertion_id, core_json
                   FROM knw_scope_assertions
                   ORDER BY rowid"""
            ).fetchall()
            for row in rows:
                core = json.loads(row["core_json"])
                scope = self._load_scope(
                    connection,
                    StableId(core["scope_id"]),
                    Revision(core["definition_revision"]),
                )
                purpose = ScopePurpose(core["purpose"])
                outcome = AssertionOutcome(core["outcome"])
                read_key_digest = _scope_assertion_read_key(
                    scope_id=scope.scope_id,
                    purpose=purpose,
                    caller_ref=core["caller_ref"],
                    request_ref=core["request_ref"],
                    classification=core["classification"],
                )
                request_digest = _scope_assertion_request_digest(
                    scope=scope,
                    purpose=purpose,
                    outcome=outcome,
                    caller_ref=core["caller_ref"],
                    request_ref=core["request_ref"],
                    classification=core["classification"],
                )
                connection.execute(
                    """INSERT OR IGNORE INTO knw_scope_assertion_reads
                       (read_key_digest, request_digest, assertion_id)
                       VALUES (?, ?, ?)""",
                    (
                        read_key_digest.value,
                        request_digest.value,
                        row["assertion_id"],
                    ),
                )

    @staticmethod
    def _load_assertion(
        connection: sqlite3.Connection, assertion_id: StableId
    ) -> ScopeStateAssertion:
        row = connection.execute(
            """SELECT assertion_id, assertion_digest, core_json
               FROM knw_scope_assertions WHERE assertion_id = ?""",
            (assertion_id.value,),
        ).fetchone()
        if row is None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "scope assertion read identity has no assertion result",
            )
        core = json.loads(row["core_json"])
        assertion = ScopeStateAssertion(
            assertion_id=StableId(row["assertion_id"]),
            scope_id=StableId(core["scope_id"]),
            scope_type=ScopeType(core["scope_type"]),
            definition_revision=Revision(core["definition_revision"]),
            lifecycle=ScopeLifecycle(core["lifecycle"]),
            purpose=ScopePurpose(core["purpose"]),
            outcome=AssertionOutcome(core["outcome"]),
            caller_ref=core["caller_ref"],
            request_ref=core["request_ref"],
            classification=core["classification"],
            read_at=_parse_time(core["read_at"]),
            digest=Digest(row["assertion_digest"]),
        )
        if not assertion.verify_digest():
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "stored scope assertion does not match its authority digest",
            )
        return assertion

    def _idempotent_result(
        self,
        connection: sqlite3.Connection,
        key: IdempotencyKey,
        command_type: str,
        request_digest: Digest,
    ) -> KnowledgeScope | None:
        row = connection.execute(
            """SELECT command_type, request_digest, result_scope_id, result_revision
               FROM knw_scope_idempotency WHERE idempotency_key = ?""",
            (key.value,),
        ).fetchone()
        if row is None:
            return None
        if row["command_type"] != command_type or row["request_digest"] != request_digest.value:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "idempotency key was already used for a different scope command",
                {"idempotency_key": key.value},
            )
        return self._load_scope(
            connection, StableId(row["result_scope_id"]), Revision(row["result_revision"])
        )

    def _load_scope(
        self,
        connection: sqlite3.Connection,
        scope_id: StableId,
        revision: Revision | None,
    ) -> KnowledgeScope:
        if revision is None:
            row = connection.execute(
                """SELECT r.scope_id, root.scope_type, root.created_at, r.revision,
                          r.lifecycle, r.metadata_json, r.actor, r.reason,
                          r.revised_at, r.definition_digest
                   FROM knw_scope_roots root
                   JOIN knw_scope_revisions r
                     ON r.scope_id = root.scope_id AND r.revision = root.current_revision
                   WHERE root.scope_id = ?""",
                (scope_id.value,),
            ).fetchone()
        else:
            row = connection.execute(
                """SELECT r.scope_id, root.scope_type, root.created_at, r.revision,
                          r.lifecycle, r.metadata_json, r.actor, r.reason,
                          r.revised_at, r.definition_digest
                   FROM knw_scope_roots root
                   JOIN knw_scope_revisions r ON r.scope_id = root.scope_id
                   WHERE root.scope_id = ? AND r.revision = ?""",
                (scope_id.value, revision.value),
            ).fetchone()
        if row is None:
            raise DomainError(
                ErrorCode.SCOPE_NOT_FOUND,
                "scope or requested scope revision does not exist",
                {"scope_id": scope_id.value},
            )
        raw_metadata = json.loads(row["metadata_json"])
        metadata = tuple((item[0], item[1]) for item in raw_metadata)
        return KnowledgeScope(
            scope_id=StableId(row["scope_id"]),
            scope_type=ScopeType(row["scope_type"]),
            lifecycle=ScopeLifecycle(row["lifecycle"]),
            definition_revision=Revision(row["revision"]),
            metadata=metadata,
            created_at=_parse_time(row["created_at"]),
            revised_at=_parse_time(row["revised_at"]),
            actor=row["actor"],
            reason=row["reason"],
            definition_digest=Digest(row["definition_digest"]),
        )

    @staticmethod
    def _build_scope(
        *,
        scope_id: StableId,
        scope_type: ScopeType,
        lifecycle: ScopeLifecycle,
        revision: Revision,
        metadata: Metadata,
        created_at: datetime,
        revised_at: datetime,
        actor: str,
        reason: str,
    ) -> KnowledgeScope:
        definition_core = {
            "scope_id": scope_id.value,
            "scope_type": scope_type.value,
            "lifecycle": lifecycle.value,
            "definition_revision": revision.value,
            "metadata": metadata,
            "created_at": created_at,
            "revised_at": revised_at,
            "actor": actor,
            "reason": reason,
        }
        return KnowledgeScope(
            scope_id=scope_id,
            scope_type=scope_type,
            lifecycle=lifecycle,
            definition_revision=revision,
            metadata=metadata,
            created_at=created_at,
            revised_at=revised_at,
            actor=actor,
            reason=reason,
            definition_digest=digest_of(definition_core),
        )

    @staticmethod
    def _insert_revision(
        connection: sqlite3.Connection,
        scope: KnowledgeScope,
        correlation_ref: CorrelationRef,
    ) -> None:
        connection.execute(
            """INSERT INTO knw_scope_revisions
               (scope_id, revision, lifecycle, metadata_json, actor, reason,
                correlation_ref, revised_at, definition_digest)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                scope.scope_id.value,
                scope.definition_revision.value,
                scope.lifecycle.value,
                canonical_json_bytes(scope.metadata).decode("utf-8"),
                scope.actor,
                scope.reason,
                correlation_ref.value,
                _time(scope.revised_at),
                scope.definition_digest.value,
            ),
        )

    @staticmethod
    def _insert_idempotency(
        connection: sqlite3.Connection,
        key: IdempotencyKey,
        command_type: str,
        request_digest: Digest,
        result: KnowledgeScope,
    ) -> None:
        connection.execute(
            "INSERT INTO knw_scope_idempotency VALUES (?, ?, ?, ?, ?)",
            (
                key.value,
                command_type,
                request_digest.value,
                result.scope_id.value,
                result.definition_revision.value,
            ),
        )

    def _insert_outbox(
        self,
        connection: sqlite3.Connection,
        scope: KnowledgeScope,
        event_type: str,
        correlation_ref: CorrelationRef,
    ) -> None:
        payload_digest = digest_of(
            {
                "owner": "KNOWLEDGE_ENGINE",
                "aggregate_id": scope.scope_id.value,
                "authority_revision": scope.definition_revision.value,
                "event_type": event_type,
                "definition_digest": scope.definition_digest.value,
            }
        )
        connection.execute(
            """INSERT INTO knw_scope_outbox
               (event_id, aggregate_id, authority_revision, event_type, payload_digest,
                correlation_ref, occurred_at, delivered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, NULL)""",
            (
                self._ids.new("outbox_event").value,
                scope.scope_id.value,
                scope.definition_revision.value,
                event_type,
                payload_digest.value,
                correlation_ref.value,
                _time(scope.revised_at),
            ),
        )

    @staticmethod
    def _advance_root(
        connection: sqlite3.Connection,
        current: KnowledgeScope,
        revised: KnowledgeScope,
    ) -> None:
        cursor = connection.execute(
            """UPDATE knw_scope_roots
               SET current_revision = ?, lifecycle = ?
               WHERE scope_id = ? AND current_revision = ?""",
            (
                revised.definition_revision.value,
                revised.lifecycle.value,
                current.scope_id.value,
                current.definition_revision.value,
            ),
        )
        if cursor.rowcount != 1:
            raise DomainError(
                ErrorCode.REVISION_CONFLICT,
                "scope revision changed before the command could commit",
                {"scope_id": current.scope_id.value},
            )

    @staticmethod
    def _require_expected(scope: KnowledgeScope, expected_revision: Revision) -> None:
        if scope.definition_revision != expected_revision:
            raise DomainError(
                ErrorCode.REVISION_CONFLICT,
                "expected scope revision is stale",
                {
                    "scope_id": scope.scope_id.value,
                    "expected_revision": expected_revision.value,
                    "actual_revision": scope.definition_revision.value,
                },
            )


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _scope_assertion_read_key(
    *,
    scope_id: StableId,
    purpose: ScopePurpose,
    caller_ref: str,
    request_ref: str,
    classification: str,
) -> Digest:
    return digest_of(
        {
            "command": "ReadScopeStateAssertion@1",
            "scope_id": scope_id.value,
            "purpose": purpose.value,
            "caller_ref": caller_ref,
            "request_ref": request_ref,
            "classification": classification,
        }
    )


def _scope_assertion_request_digest(
    *,
    scope: KnowledgeScope,
    purpose: ScopePurpose,
    outcome: AssertionOutcome,
    caller_ref: str,
    request_ref: str,
    classification: str,
) -> Digest:
    return digest_of(
        {
            "command": "ReadScopeStateAssertion@1",
            "scope_id": scope.scope_id.value,
            "scope_type": scope.scope_type.value,
            "definition_revision": scope.definition_revision.value,
            "lifecycle": scope.lifecycle.value,
            "purpose": purpose.value,
            "outcome": outcome.value,
            "caller_ref": caller_ref,
            "request_ref": request_ref,
            "classification": classification,
        }
    )


def _integrity_error(exc: sqlite3.IntegrityError) -> DomainError:
    return DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        "scope authority transaction violated a store invariant",
        {"sqlite_error": str(exc)},
    )
