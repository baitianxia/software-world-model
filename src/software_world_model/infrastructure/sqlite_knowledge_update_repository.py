"""SQLite application state for recoverable Knowledge Update requests."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

from software_world_model.application_services.knowledge_update import (
    InvestigationStopReason,
    KnowledgeUpdateAttempt,
    KnowledgeUpdateRequest,
    KnowledgeUpdateResult,
    UpdateAttemptState,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    StableId,
    Uuid4IdGenerator,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.knowledge_engine import AdmissionStatus

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_update_attempts (
    attempt_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    current_state TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revised_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_update_steps (
    attempt_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 1),
    action_digest TEXT NOT NULL,
    operation_id TEXT NOT NULL,
    artifact_ids_json TEXT NOT NULL,
    progress_digest TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    PRIMARY KEY (attempt_id, ordinal),
    FOREIGN KEY (attempt_id) REFERENCES app_update_attempts(attempt_id)
);

CREATE TABLE IF NOT EXISTS app_update_results (
    result_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    state TEXT NOT NULL,
    stop_reason TEXT NOT NULL,
    target_digest TEXT NOT NULL,
    operation_ids_json TEXT NOT NULL,
    artifact_ids_json TEXT NOT NULL,
    coverage_complete INTEGER NOT NULL CHECK (coverage_complete IN (0, 1)),
    admission_id TEXT,
    admission_status TEXT,
    snapshot_id TEXT,
    limitations_json TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    result_digest TEXT NOT NULL,
    FOREIGN KEY (attempt_id) REFERENCES app_update_attempts(attempt_id)
);
"""


class SqliteKnowledgeUpdateRepository:
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def begin(
        self, *, request: KnowledgeUpdateRequest, occurred_at: datetime
    ) -> tuple[KnowledgeUpdateAttempt, KnowledgeUpdateResult | None]:
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM app_update_attempts WHERE idempotency_key = ?",
                (request.idempotency_key.value,),
            ).fetchone()
            if row is not None:
                if row["request_digest"] != request.digest.value:
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "knowledge update idempotency key has a different request",
                    )
                attempt = _attempt(row)
                result_row = connection.execute(
                    "SELECT * FROM app_update_results WHERE attempt_id = ?", (row["attempt_id"],)
                ).fetchone()
                return attempt, _result(result_row) if result_row else None
            attempt_id = self._ids.new("knowledge_update")
            timestamp = _time(occurred_at)
            connection.execute(
                "INSERT INTO app_update_attempts VALUES (?, ?, ?, ?, ?, ?)",
                (
                    attempt_id.value,
                    request.idempotency_key.value,
                    request.digest.value,
                    UpdateAttemptState.PREPARING.value,
                    timestamp,
                    timestamp,
                ),
            )
            return (
                KnowledgeUpdateAttempt(
                    attempt_id=attempt_id,
                    request_digest=request.digest,
                    state=UpdateAttemptState.PREPARING,
                    created_at=occurred_at,
                    revised_at=occurred_at,
                ),
                None,
            )

    def record_step(
        self,
        *,
        attempt_id: StableId,
        ordinal: int,
        action_digest: Digest,
        operation_id: StableId,
        artifact_ids: tuple[StableId, ...],
        progress_digest: Digest,
        occurred_at: datetime,
    ) -> None:
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM app_update_steps WHERE attempt_id = ? AND ordinal = ?",
                (attempt_id.value, ordinal),
            ).fetchone()
            if existing is not None:
                if (
                    existing["action_digest"] != action_digest.value
                    or existing["operation_id"] != operation_id.value
                    or existing["progress_digest"] != progress_digest.value
                ):
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "recovered update step differs from its sealed result",
                    )
                return
            connection.execute(
                "INSERT INTO app_update_steps VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    attempt_id.value,
                    ordinal,
                    action_digest.value,
                    operation_id.value,
                    _json([item.value for item in artifact_ids]),
                    progress_digest.value,
                    _time(occurred_at),
                ),
            )
            connection.execute(
                """UPDATE app_update_attempts
                   SET current_state = ?, revised_at = ? WHERE attempt_id = ?""",
                (UpdateAttemptState.INVESTIGATING.value, _time(occurred_at), attempt_id.value),
            )

    def finish(
        self,
        *,
        attempt_id: StableId,
        state: UpdateAttemptState,
        stop_reason: InvestigationStopReason,
        target_digest: Digest,
        operation_ids: tuple[StableId, ...],
        artifact_ids: tuple[StableId, ...],
        coverage_complete: bool,
        admission_id: StableId | None,
        admission_status: AdmissionStatus | None,
        snapshot_id: StableId | None,
        limitations: tuple[str, ...],
        occurred_at: datetime,
    ) -> KnowledgeUpdateResult:
        with self._database.transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM app_update_results WHERE attempt_id = ?", (attempt_id.value,)
            ).fetchone()
            if existing is not None:
                return _result(existing)
            attempt = connection.execute(
                "SELECT * FROM app_update_attempts WHERE attempt_id = ?", (attempt_id.value,)
            ).fetchone()
            if attempt is None:
                raise DomainError(ErrorCode.INVALID_ARGUMENT, "knowledge update attempt was not found")
            result_id = self._ids.new("update_result")
            core = {
                "result_id": result_id.value,
                "attempt_id": attempt_id.value,
                "request_digest": attempt["request_digest"],
                "state": state.value,
                "stop_reason": stop_reason.value,
                "target_digest": target_digest.value,
                "operation_ids": tuple(item.value for item in operation_ids),
                "artifact_ids": tuple(item.value for item in artifact_ids),
                "coverage_complete": coverage_complete,
                "admission_id": admission_id.value if admission_id else None,
                "admission_status": admission_status.value if admission_status else None,
                "snapshot_id": snapshot_id.value if snapshot_id else None,
                "limitations": limitations,
                "completed_at": occurred_at,
            }
            result_digest = digest_of(core)
            connection.execute(
                "INSERT INTO app_update_results VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    result_id.value,
                    attempt_id.value,
                    attempt["request_digest"],
                    state.value,
                    stop_reason.value,
                    target_digest.value,
                    _json([item.value for item in operation_ids]),
                    _json([item.value for item in artifact_ids]),
                    int(coverage_complete),
                    admission_id.value if admission_id else None,
                    admission_status.value if admission_status else None,
                    snapshot_id.value if snapshot_id else None,
                    _json(limitations),
                    _time(occurred_at),
                    result_digest.value,
                ),
            )
            connection.execute(
                """UPDATE app_update_attempts
                   SET current_state = ?, revised_at = ? WHERE attempt_id = ?""",
                (state.value, _time(occurred_at), attempt_id.value),
            )
            row = connection.execute(
                "SELECT * FROM app_update_results WHERE result_id = ?", (result_id.value,)
            ).fetchone()
            return _result(row)


def _attempt(row: sqlite3.Row) -> KnowledgeUpdateAttempt:
    return KnowledgeUpdateAttempt(
        attempt_id=StableId(row["attempt_id"]),
        request_digest=Digest(row["request_digest"]),
        state=UpdateAttemptState(row["current_state"]),
        created_at=_parse_time(row["created_at"]),
        revised_at=_parse_time(row["revised_at"]),
    )


def _result(row: sqlite3.Row) -> KnowledgeUpdateResult:
    return KnowledgeUpdateResult(
        result_id=StableId(row["result_id"]),
        attempt_id=StableId(row["attempt_id"]),
        request_digest=Digest(row["request_digest"]),
        state=UpdateAttemptState(row["state"]),
        stop_reason=InvestigationStopReason(row["stop_reason"]),
        target_digest=Digest(row["target_digest"]),
        source_operation_references=tuple(
            StableId(item) for item in json.loads(row["operation_ids_json"])
        ),
        artifact_references=tuple(
            StableId(item) for item in json.loads(row["artifact_ids_json"])
        ),
        target_coverage_complete=bool(row["coverage_complete"]),
        admission_id=StableId(row["admission_id"]) if row["admission_id"] else None,
        admission_status=(
            AdmissionStatus(row["admission_status"]) if row["admission_status"] else None
        ),
        published_snapshot_id=StableId(row["snapshot_id"]) if row["snapshot_id"] else None,
        limitations=tuple(json.loads(row["limitations_json"])),
        completed_at=_parse_time(row["completed_at"]),
        digest=Digest(row["result_digest"]),
    )


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)
