"""SQLite authority store for Source Operations, observations, and artifacts."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    Revision,
    StableId,
    Uuid4IdGenerator,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.source_integration.operations import (
    ConnectorOutcome,
    SourceArtifact,
    SourceContext,
    SourceObservation,
    SourceOperationIntent,
    SourceOperationResult,
    SourceOperationStatus,
    SourceTool,
    content_digest,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS src_operation_roots (
    operation_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    intent_digest TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_revision INTEGER NOT NULL,
    binding_id TEXT NOT NULL,
    binding_revision INTEGER NOT NULL,
    tool_id TEXT NOT NULL,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    current_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revised_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS src_operation_revisions (
    operation_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    status TEXT NOT NULL,
    observation_id TEXT,
    failure_code TEXT,
    failure_message TEXT,
    result_digest TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    PRIMARY KEY (operation_id, revision),
    FOREIGN KEY (operation_id) REFERENCES src_operation_roots(operation_id)
);

CREATE TABLE IF NOT EXISTS src_contexts (
    context_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    source_revision INTEGER NOT NULL,
    repository_revision TEXT NOT NULL,
    subject TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    context_digest TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS src_artifacts (
    artifact_id TEXT PRIMARY KEY,
    artifact_kind TEXT NOT NULL,
    payload_schema_version TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_revision INTEGER NOT NULL,
    source_context_id TEXT NOT NULL,
    source_native_identity TEXT NOT NULL,
    content_digest TEXT NOT NULL,
    payload BLOB NOT NULL,
    classification TEXT NOT NULL,
    truncated INTEGER NOT NULL CHECK (truncated IN (0, 1)),
    truncation_offset INTEGER,
    identity_digest TEXT NOT NULL UNIQUE,
    FOREIGN KEY (source_context_id) REFERENCES src_contexts(context_id)
);

CREATE TABLE IF NOT EXISTS src_observations (
    observation_id TEXT PRIMARY KEY,
    operation_id TEXT NOT NULL UNIQUE,
    tool_id TEXT NOT NULL,
    source_context_id TEXT NOT NULL,
    artifact_ids_json TEXT NOT NULL,
    item_count INTEGER NOT NULL,
    byte_count INTEGER NOT NULL,
    next_cursor TEXT,
    has_more INTEGER NOT NULL CHECK (has_more IN (0, 1)),
    coverage_json TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    observation_digest TEXT NOT NULL,
    FOREIGN KEY (operation_id) REFERENCES src_operation_roots(operation_id),
    FOREIGN KEY (source_context_id) REFERENCES src_contexts(context_id)
);
"""


class SqliteSourceOperationRepository:
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def prepare(
        self, *, intent: SourceOperationIntent, occurred_at: datetime
    ) -> SourceOperationResult:
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT operation_id, intent_digest FROM src_operation_roots WHERE idempotency_key = ?",
                (intent.idempotency_key.value,),
            ).fetchone()
            if existing is not None:
                if existing["intent_digest"] != intent.digest.value:
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "source operation idempotency key has a different intent",
                    )
                return self._load(connection, StableId(existing["operation_id"]))
            operation_id = self._ids.new("source_operation")
            timestamp = _time(occurred_at)
            initial_digest = _result_digest(
                operation_id,
                Revision(1),
                SourceOperationStatus.PREPARED,
                intent.digest,
                None,
                None,
                occurred_at,
            )
            connection.execute(
                """INSERT INTO src_operation_roots
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)""",
                (
                    operation_id.value,
                    intent.idempotency_key.value,
                    intent.digest.value,
                    intent.source_id.value,
                    intent.source_revision.value,
                    intent.binding_id.value,
                    intent.binding_revision.value,
                    intent.tool.value,
                    SourceOperationStatus.PREPARED.value,
                    timestamp,
                    timestamp,
                ),
            )
            connection.execute(
                """INSERT INTO src_operation_revisions
                   VALUES (?, 1, ?, NULL, NULL, NULL, ?, ?)""",
                (
                    operation_id.value,
                    SourceOperationStatus.PREPARED.value,
                    initial_digest.value,
                    timestamp,
                ),
            )
            return self._load(connection, operation_id)

    def mark_dispatched(
        self, *, operation_id: StableId, expected_revision: Revision, occurred_at: datetime
    ) -> SourceOperationResult:
        return self._transition(
            operation_id=operation_id,
            expected_revision=expected_revision,
            status=SourceOperationStatus.DISPATCHED,
            outcome=None,
            classification="INTERNAL",
            failure_code=None,
            failure_message=None,
            occurred_at=occurred_at,
        )

    def complete(
        self,
        *,
        operation_id: StableId,
        expected_revision: Revision,
        status: SourceOperationStatus,
        outcome: ConnectorOutcome | None,
        classification: str,
        failure_code: str | None,
        failure_message: str | None,
        occurred_at: datetime,
    ) -> SourceOperationResult:
        return self._transition(
            operation_id=operation_id,
            expected_revision=expected_revision,
            status=status,
            outcome=outcome,
            classification=classification,
            failure_code=failure_code,
            failure_message=failure_message,
            occurred_at=occurred_at,
        )

    def get(self, operation_id: StableId) -> SourceOperationResult:
        with self._database.read() as connection:
            return self._load(connection, operation_id)

    def _transition(
        self,
        *,
        operation_id: StableId,
        expected_revision: Revision,
        status: SourceOperationStatus,
        outcome: ConnectorOutcome | None,
        classification: str,
        failure_code: str | None,
        failure_message: str | None,
        occurred_at: datetime,
    ) -> SourceOperationResult:
        try:
            with self._database.transaction() as connection:
                root = connection.execute(
                    "SELECT * FROM src_operation_roots WHERE operation_id = ?",
                    (operation_id.value,),
                ).fetchone()
                if root is None:
                    raise DomainError(ErrorCode.INVALID_ARGUMENT, "source operation was not found")
                if root["current_revision"] != expected_revision.value:
                    raise DomainError(ErrorCode.REVISION_CONFLICT, "source operation revision is stale")
                current = SourceOperationStatus(root["current_status"])
                if status not in _ALLOWED[current]:
                    raise DomainError(
                        ErrorCode.MANAGEMENT_STATE_CONFLICT,
                        f"source operation cannot transition from {current.value} to {status.value}",
                    )
                observation_id = None
                if outcome is not None:
                    observation_id = self._materialize_observation(
                        connection,
                        operation_id=operation_id,
                        root=root,
                        outcome=outcome,
                        classification=classification,
                        tool=SourceTool(root["tool_id"]),
                        occurred_at=occurred_at,
                    ).observation_id
                elif status in {SourceOperationStatus.COMPLETED, SourceOperationStatus.PARTIAL}:
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "successful source operation requires an observation",
                    )
                revision = expected_revision.next()
                result_digest = _result_digest(
                    operation_id,
                    revision,
                    status,
                    Digest(root["intent_digest"]),
                    observation_id,
                    failure_code,
                    occurred_at,
                )
                connection.execute(
                    """INSERT INTO src_operation_revisions
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        operation_id.value,
                        revision.value,
                        status.value,
                        observation_id.value if observation_id else None,
                        failure_code,
                        failure_message,
                        result_digest.value,
                        _time(occurred_at),
                    ),
                )
                cursor = connection.execute(
                    """UPDATE src_operation_roots
                       SET current_revision = ?, current_status = ?, revised_at = ?
                       WHERE operation_id = ? AND current_revision = ?""",
                    (
                        revision.value,
                        status.value,
                        _time(occurred_at),
                        operation_id.value,
                        expected_revision.value,
                    ),
                )
                if cursor.rowcount != 1:
                    raise DomainError(ErrorCode.REVISION_CONFLICT, "source operation changed")
                return self._load(connection, operation_id)
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "source operation transaction violated a store invariant",
                {"sqlite_error": str(exc)},
            ) from exc

    def _materialize_observation(
        self,
        connection: sqlite3.Connection,
        *,
        operation_id: StableId,
        root: sqlite3.Row,
        outcome: ConnectorOutcome,
        classification: str,
        tool: SourceTool,
        occurred_at: datetime,
    ) -> SourceObservation:
        context_core = {
            "source_id": root["source_id"],
            "source_revision": root["source_revision"],
            "repository_revision": outcome.repository_revision,
            "subject": outcome.subject,
            "observed_at": occurred_at,
            "basis": "SINGLE_OBSERVATION",
            "context_contract": "local-git-context@1",
        }
        context_digest = digest_of(context_core)
        context_id = StableId(f"source_context_{context_digest.value[-32:]}")
        connection.execute(
            """INSERT OR IGNORE INTO src_contexts VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                context_id.value,
                root["source_id"],
                root["source_revision"],
                outcome.repository_revision,
                outcome.subject,
                _time(occurred_at),
                context_digest.value,
            ),
        )
        context = SourceContext(
            context_id=context_id,
            source_id=StableId(root["source_id"]),
            source_revision=Revision(root["source_revision"]),
            repository_revision=outcome.repository_revision,
            subject=outcome.subject,
            observed_at=occurred_at,
            digest=context_digest,
        )
        payload_digest = content_digest(outcome.payload)
        identity_core = {
            "source_id": root["source_id"],
            "source_revision": root["source_revision"],
            "source_context_id": context_id.value,
            "source_native_identity": outcome.subject,
            "artifact_kind": outcome.artifact_kind,
            "payload_schema_version": "1",
            "provider_contract": "LOCAL_GIT@0.1.0",
            "tool": tool.value,
            "coverage": outcome.coverage,
            "identity_strategy": "local-git-artifact@2",
        }
        identity_digest = digest_of(identity_core)
        artifact_id = StableId(f"source_artifact_{identity_digest.value[-32:]}")
        existing = connection.execute(
            "SELECT content_digest FROM src_artifacts WHERE identity_digest = ?",
            (identity_digest.value,),
        ).fetchone()
        if existing is not None and existing["content_digest"] != payload_digest.value:
            raise DomainError(
                ErrorCode.SOURCE_REVISION_INCONSISTENT,
                "the same immutable source artifact identity produced different content",
            )
        connection.execute(
            """INSERT OR IGNORE INTO src_artifacts
               VALUES (?, ?, '1', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                artifact_id.value,
                outcome.artifact_kind,
                root["source_id"],
                root["source_revision"],
                context_id.value,
                outcome.subject,
                payload_digest.value,
                outcome.payload,
                classification,
                int(outcome.truncated),
                outcome.truncation_offset,
                identity_digest.value,
            ),
        )
        artifact = SourceArtifact(
            artifact_id=artifact_id,
            artifact_kind=outcome.artifact_kind,
            payload_schema_version="1",
            source_id=StableId(root["source_id"]),
            source_revision=Revision(root["source_revision"]),
            source_context_id=context_id,
            source_native_identity=outcome.subject,
            content_digest=payload_digest,
            payload=outcome.payload,
            classification=classification,
            truncated=outcome.truncated,
            truncation_offset=outcome.truncation_offset,
            identity_digest=identity_digest,
        )
        observation_id = self._ids.new("source_observation")
        observation_core = {
            "observation_id": observation_id.value,
            "operation_id": operation_id.value,
            "tool": tool.value,
            "context_digest": context_digest.value,
            "artifacts": ((artifact_id.value, payload_digest.value),),
            "item_count": outcome.item_count,
            "byte_count": len(outcome.payload),
            "next_cursor": outcome.next_cursor,
            "has_more": outcome.has_more,
            "coverage": outcome.coverage,
            "observed_at": occurred_at,
        }
        observation_digest = digest_of(observation_core)
        connection.execute(
            """INSERT INTO src_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                observation_id.value,
                operation_id.value,
                tool.value,
                context_id.value,
                canonical_json_bytes((artifact_id.value,)).decode("utf-8"),
                outcome.item_count,
                len(outcome.payload),
                outcome.next_cursor,
                int(outcome.has_more),
                canonical_json_bytes(dict(outcome.coverage)).decode("utf-8"),
                _time(occurred_at),
                observation_digest.value,
            ),
        )
        return SourceObservation(
            observation_id=observation_id,
            operation_id=operation_id,
            tool=tool,
            source_context=context,
            artifacts=(artifact,),
            item_count=outcome.item_count,
            byte_count=len(outcome.payload),
            next_cursor=outcome.next_cursor,
            has_more=outcome.has_more,
            coverage=outcome.coverage,
            observed_at=occurred_at,
            digest=observation_digest,
        )

    def _load(
        self, connection: sqlite3.Connection, operation_id: StableId
    ) -> SourceOperationResult:
        row = connection.execute(
            """SELECT root.*, revision.observation_id, revision.failure_code,
                      revision.failure_message, revision.result_digest
               FROM src_operation_roots AS root
               JOIN src_operation_revisions AS revision
                 ON revision.operation_id = root.operation_id
                AND revision.revision = root.current_revision
               WHERE root.operation_id = ?""",
            (operation_id.value,),
        ).fetchone()
        if row is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "source operation was not found")
        observation = (
            self._load_observation(connection, StableId(row["observation_id"]))
            if row["observation_id"]
            else None
        )
        return SourceOperationResult(
            operation_id=operation_id,
            revision=Revision(row["current_revision"]),
            status=SourceOperationStatus(row["current_status"]),
            intent_digest=Digest(row["intent_digest"]),
            observation=observation,
            failure_code=row["failure_code"],
            failure_message=row["failure_message"],
            created_at=_parse_time(row["created_at"]),
            revised_at=_parse_time(row["revised_at"]),
            digest=Digest(row["result_digest"]),
        )

    def _load_observation(
        self, connection: sqlite3.Connection, observation_id: StableId
    ) -> SourceObservation:
        row = connection.execute(
            "SELECT * FROM src_observations WHERE observation_id = ?",
            (observation_id.value,),
        ).fetchone()
        context_row = connection.execute(
            "SELECT * FROM src_contexts WHERE context_id = ?", (row["source_context_id"],)
        ).fetchone()
        context = SourceContext(
            context_id=StableId(context_row["context_id"]),
            source_id=StableId(context_row["source_id"]),
            source_revision=Revision(context_row["source_revision"]),
            repository_revision=context_row["repository_revision"],
            subject=context_row["subject"],
            observed_at=_parse_time(context_row["observed_at"]),
            digest=Digest(context_row["context_digest"]),
        )
        artifacts = tuple(
            self._load_artifact(connection, StableId(item))
            for item in json.loads(row["artifact_ids_json"])
        )
        return SourceObservation(
            observation_id=observation_id,
            operation_id=StableId(row["operation_id"]),
            tool=SourceTool(row["tool_id"]),
            source_context=context,
            artifacts=artifacts,
            item_count=row["item_count"],
            byte_count=row["byte_count"],
            next_cursor=row["next_cursor"],
            has_more=bool(row["has_more"]),
            coverage=tuple(sorted(json.loads(row["coverage_json"]).items())),
            observed_at=_parse_time(row["observed_at"]),
            digest=Digest(row["observation_digest"]),
        )

    @staticmethod
    def _load_artifact(connection: sqlite3.Connection, artifact_id: StableId) -> SourceArtifact:
        row = connection.execute(
            "SELECT * FROM src_artifacts WHERE artifact_id = ?", (artifact_id.value,)
        ).fetchone()
        return SourceArtifact(
            artifact_id=artifact_id,
            artifact_kind=row["artifact_kind"],
            payload_schema_version=row["payload_schema_version"],
            source_id=StableId(row["source_id"]),
            source_revision=Revision(row["source_revision"]),
            source_context_id=StableId(row["source_context_id"]),
            source_native_identity=row["source_native_identity"],
            content_digest=Digest(row["content_digest"]),
            payload=bytes(row["payload"]),
            classification=row["classification"],
            truncated=bool(row["truncated"]),
            truncation_offset=row["truncation_offset"],
            identity_digest=Digest(row["identity_digest"]),
        )


_ALLOWED = {
    SourceOperationStatus.PREPARED: {
        SourceOperationStatus.DISPATCHED,
        SourceOperationStatus.FAILED,
        SourceOperationStatus.CANCELED,
    },
    SourceOperationStatus.DISPATCHED: {
        SourceOperationStatus.COMPLETED,
        SourceOperationStatus.PARTIAL,
        SourceOperationStatus.FAILED,
        SourceOperationStatus.BUDGET_EXHAUSTED,
        SourceOperationStatus.OUTCOME_UNKNOWN,
    },
    SourceOperationStatus.COMPLETED: set(),
    SourceOperationStatus.PARTIAL: set(),
    SourceOperationStatus.FAILED: set(),
    SourceOperationStatus.BUDGET_EXHAUSTED: set(),
    SourceOperationStatus.OUTCOME_UNKNOWN: set(),
    SourceOperationStatus.CANCELED: set(),
}


def _result_digest(
    operation_id: StableId,
    revision: Revision,
    status: SourceOperationStatus,
    intent_digest: Digest,
    observation_id: StableId | None,
    failure_code: str | None,
    occurred_at: datetime,
) -> Digest:
    return digest_of(
        {
            "operation_id": operation_id.value,
            "revision": revision.value,
            "status": status.value,
            "intent_digest": intent_digest.value,
            "observation_id": observation_id.value if observation_id else None,
            "failure_code": failure_code,
            "occurred_at": occurred_at,
        }
    )


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)
