"""SQLite authority store for conversational tasks, grants, and calls."""

from __future__ import annotations

from datetime import datetime
import json

from software_world_model.application_services.task_control import (
    AgentCapability,
    AgentCapabilityCatalog,
    AgentInvocation,
    ApplicationCallRecord,
    ApplicationCallState,
    ConversationalTask,
    DelegatedApplicationGrant,
    EffectClass,
    OrchestratorProposal,
    TaskRequestEnvelope,
    TaskState,
)
from software_world_model.cross_cutting import (
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
CREATE TABLE IF NOT EXISTS app_tasks (
    task_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    revision INTEGER NOT NULL,
    orchestration_revision INTEGER NOT NULL,
    conversation_ref TEXT NOT NULL,
    turn_ref TEXT NOT NULL,
    request_ref TEXT NOT NULL,
    original_request TEXT NOT NULL,
    caller_ref TEXT NOT NULL,
    classification TEXT NOT NULL,
    scope_id TEXT NOT NULL,
    catalog_id TEXT NOT NULL,
    catalog_revision INTEGER NOT NULL,
    catalog_digest TEXT NOT NULL,
    state TEXT NOT NULL,
    selected_capability_id TEXT,
    candidate_reference TEXT,
    created_at TEXT NOT NULL,
    revised_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_agent_invocations (
    invocation_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    task_revision INTEGER NOT NULL,
    capability_id TEXT NOT NULL,
    grant_id TEXT NOT NULL UNIQUE,
    grant_digest TEXT NOT NULL,
    allowed_use_cases_json TEXT NOT NULL,
    allowed_effects_json TEXT NOT NULL,
    scope_id TEXT NOT NULL,
    classification TEXT NOT NULL,
    input_digest TEXT NOT NULL,
    created_at TEXT NOT NULL,
    invocation_digest TEXT NOT NULL,
    UNIQUE (task_id, task_revision, capability_id, input_digest),
    FOREIGN KEY (task_id) REFERENCES app_tasks(task_id)
);

CREATE TABLE IF NOT EXISTS app_application_calls (
    call_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    logical_occurrence TEXT NOT NULL,
    invocation_id TEXT NOT NULL,
    use_case TEXT NOT NULL,
    effect_class TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    application_idempotency_key TEXT NOT NULL UNIQUE,
    revision INTEGER NOT NULL,
    state TEXT NOT NULL,
    result_reference TEXT,
    result_digest TEXT,
    UNIQUE (task_id, logical_occurrence),
    FOREIGN KEY (task_id) REFERENCES app_tasks(task_id),
    FOREIGN KEY (invocation_id) REFERENCES app_agent_invocations(invocation_id)
);
"""


class SqliteTaskControlRepository:
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def create_task(
        self,
        *,
        envelope: TaskRequestEnvelope,
        catalog: AgentCapabilityCatalog,
        occurred_at: datetime,
    ) -> ConversationalTask:
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM app_tasks WHERE idempotency_key = ?", (envelope.idempotency_key.value,)
            ).fetchone()
            if row is not None:
                if row["request_digest"] != envelope.digest.value:
                    raise DomainError(ErrorCode.IDEMPOTENCY_MISMATCH, "task key has another request")
                return _task(row)
            task_id = self._ids.new("task")
            timestamp = _time(occurred_at)
            connection.execute(
                """INSERT INTO app_tasks VALUES
                   (?, ?, ?, 1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)""",
                (
                    task_id.value,
                    envelope.idempotency_key.value,
                    envelope.digest.value,
                    envelope.conversation_ref,
                    envelope.turn_ref,
                    envelope.request_ref,
                    envelope.original_request,
                    envelope.caller_ref,
                    envelope.classification,
                    envelope.scope_id.value,
                    catalog.catalog_id.value,
                    catalog.revision.value,
                    catalog.digest.value,
                    TaskState.RECEIVED.value,
                    timestamp,
                    timestamp,
                ),
            )
            return _task(connection.execute("SELECT * FROM app_tasks WHERE task_id = ?", (task_id.value,)).fetchone())

    def apply_proposal(
        self,
        *,
        task_id: StableId,
        expected_revision: Revision,
        proposal: OrchestratorProposal,
        occurred_at: datetime,
    ) -> ConversationalTask:
        with self._database.transaction() as connection:
            row = connection.execute("SELECT * FROM app_tasks WHERE task_id = ?", (task_id.value,)).fetchone()
            if row is None or row["revision"] != expected_revision.value:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "task revision is stale")
            if TaskState(row["state"]) is not TaskState.RECEIVED:
                raise DomainError(ErrorCode.MANAGEMENT_STATE_CONFLICT, "task cannot accept routing proposal")
            connection.execute(
                """UPDATE app_tasks SET revision = revision + 1,
                   orchestration_revision = orchestration_revision + 1,
                   state = ?, selected_capability_id = ?, revised_at = ? WHERE task_id = ?""",
                (TaskState.READY.value, proposal.capability_id, _time(occurred_at), task_id.value),
            )
            return _task(connection.execute("SELECT * FROM app_tasks WHERE task_id = ?", (task_id.value,)).fetchone())

    def create_invocation(
        self,
        *,
        task: ConversationalTask,
        capability: AgentCapability,
        input_digest: Digest,
        occurred_at: datetime,
    ) -> AgentInvocation:
        with self._database.transaction() as connection:
            row = connection.execute(
                """SELECT * FROM app_agent_invocations WHERE task_id = ? AND task_revision = ?
                   AND capability_id = ? AND input_digest = ?""",
                (task.task_id.value, task.revision.value, capability.capability_id, input_digest.value),
            ).fetchone()
            if row is not None:
                return _invocation(row)
            grant_id = self._ids.new("delegated_grant")
            grant_core = {
                "grant_id": grant_id.value,
                "task_id": task.task_id.value,
                "task_revision": task.revision.value,
                "capability_id": capability.capability_id,
                "allowed_use_cases": capability.allowed_use_cases,
                "allowed_effect_classes": tuple(item.value for item in capability.allowed_effect_classes),
                "scope_id": task.scope_id.value,
                "classification": task.classification,
            }
            grant_digest = digest_of(grant_core)
            invocation_id = self._ids.new("agent_invocation")
            invocation_digest = digest_of(
                {
                    "invocation_id": invocation_id.value,
                    "grant_digest": grant_digest.value,
                    "input_digest": input_digest.value,
                }
            )
            connection.execute(
                "INSERT INTO app_agent_invocations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    invocation_id.value,
                    task.task_id.value,
                    task.revision.value,
                    capability.capability_id,
                    grant_id.value,
                    grant_digest.value,
                    _json(capability.allowed_use_cases),
                    _json(tuple(item.value for item in capability.allowed_effect_classes)),
                    task.scope_id.value,
                    task.classification,
                    input_digest.value,
                    _time(occurred_at),
                    invocation_digest.value,
                ),
            )
            connection.execute(
                "UPDATE app_tasks SET state = ? WHERE task_id = ?",
                (TaskState.RUNNING.value, task.task_id.value),
            )
            return _invocation(
                connection.execute(
                    "SELECT * FROM app_agent_invocations WHERE invocation_id = ?", (invocation_id.value,)
                ).fetchone()
            )

    def create_application_call(
        self,
        *,
        invocation: AgentInvocation,
        logical_occurrence: str,
        use_case: str,
        effect_class: EffectClass,
        request_digest: Digest,
    ) -> ApplicationCallRecord:
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM app_application_calls WHERE task_id = ? AND logical_occurrence = ?",
                (invocation.task_id.value, logical_occurrence),
            ).fetchone()
            if row is not None:
                if (
                    row["request_digest"] != request_digest.value
                    or row["use_case"] != use_case
                    or row["effect_class"] != effect_class.value
                ):
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "logical action occurrence has different call semantics",
                    )
                return _call(row)
            call_id = self._ids.new("application_call")
            key_digest = digest_of(
                {"task_id": invocation.task_id.value, "logical_occurrence": logical_occurrence}
            )
            app_key = IdempotencyKey(f"task-call:{key_digest.value[-32:]}")
            connection.execute(
                "INSERT INTO app_application_calls VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, NULL, NULL)",
                (
                    call_id.value,
                    invocation.task_id.value,
                    logical_occurrence,
                    invocation.invocation_id.value,
                    use_case,
                    effect_class.value,
                    request_digest.value,
                    app_key.value,
                    ApplicationCallState.PREPARED.value,
                ),
            )
            return _call(connection.execute("SELECT * FROM app_application_calls WHERE call_id = ?", (call_id.value,)).fetchone())

    def transition_application_call(
        self,
        *,
        call_id: StableId,
        expected_revision: Revision,
        target: ApplicationCallState,
        result_reference: str | None,
        result_digest: Digest | None,
    ) -> ApplicationCallRecord:
        with self._database.transaction() as connection:
            row = connection.execute("SELECT * FROM app_application_calls WHERE call_id = ?", (call_id.value,)).fetchone()
            if row is None or row["revision"] != expected_revision.value:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "application call revision is stale")
            current = ApplicationCallState(row["state"])
            if target not in _CALL_TRANSITIONS[current]:
                raise DomainError(ErrorCode.MANAGEMENT_STATE_CONFLICT, "invalid application call transition")
            if target is ApplicationCallState.SUCCEEDED and (not result_reference or result_digest is None):
                raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "success requires result proof")
            connection.execute(
                """UPDATE app_application_calls SET revision = revision + 1, state = ?,
                   result_reference = ?, result_digest = ? WHERE call_id = ?""",
                (target.value, result_reference, result_digest.value if result_digest else None, call_id.value),
            )
            return _call(connection.execute("SELECT * FROM app_application_calls WHERE call_id = ?", (call_id.value,)).fetchone())

    def get_application_call(
        self, *, task_id: StableId, logical_occurrence: str
    ) -> ApplicationCallRecord | None:
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT * FROM app_application_calls
                   WHERE task_id = ? AND logical_occurrence = ?""",
                (task_id.value, logical_occurrence),
            ).fetchone()
            return _call(row) if row is not None else None

    def bind_candidate(
        self,
        *,
        task_id: StableId,
        expected_revision: Revision,
        candidate_id: StableId,
        occurred_at: datetime,
    ) -> ConversationalTask:
        with self._database.transaction() as connection:
            row = connection.execute("SELECT * FROM app_tasks WHERE task_id = ?", (task_id.value,)).fetchone()
            if row is None or row["revision"] != expected_revision.value:
                raise DomainError(ErrorCode.REVISION_CONFLICT, "task revision is stale")
            connection.execute(
                """UPDATE app_tasks SET revision = revision + 1,
                   orchestration_revision = orchestration_revision + 1,
                   candidate_reference = ?, state = ?, revised_at = ? WHERE task_id = ?""",
                (candidate_id.value, TaskState.RESPONSE_PENDING.value, _time(occurred_at), task_id.value),
            )
            return _task(connection.execute("SELECT * FROM app_tasks WHERE task_id = ?", (task_id.value,)).fetchone())

    def get_task(self, task_id: StableId) -> ConversationalTask:
        with self._database.read() as connection:
            row = connection.execute("SELECT * FROM app_tasks WHERE task_id = ?", (task_id.value,)).fetchone()
            if row is None:
                raise DomainError(ErrorCode.INVALID_ARGUMENT, "task was not found")
            return _task(row)


_CALL_TRANSITIONS = {
    ApplicationCallState.PREPARED: {ApplicationCallState.DISPATCHED, ApplicationCallState.CANCELED_BEFORE_DISPATCH},
    ApplicationCallState.DISPATCHED: {ApplicationCallState.SUCCEEDED, ApplicationCallState.FAILED, ApplicationCallState.OUTCOME_PENDING},
    ApplicationCallState.OUTCOME_PENDING: {ApplicationCallState.SUCCEEDED, ApplicationCallState.FAILED},
    ApplicationCallState.SUCCEEDED: set(),
    ApplicationCallState.FAILED: set(),
    ApplicationCallState.CANCELED_BEFORE_DISPATCH: set(),
}


def _task(row: object) -> ConversationalTask:
    return ConversationalTask(
        task_id=StableId(row["task_id"]),
        revision=Revision(row["revision"]),
        orchestration_revision=Revision(row["orchestration_revision"]),
        request_digest=Digest(row["request_digest"]),
        conversation_ref=row["conversation_ref"],
        turn_ref=row["turn_ref"],
        request_ref=row["request_ref"],
        original_request=row["original_request"],
        caller_ref=row["caller_ref"],
        classification=row["classification"],
        scope_id=StableId(row["scope_id"]),
        catalog_id=StableId(row["catalog_id"]),
        catalog_revision=Revision(row["catalog_revision"]),
        catalog_digest=Digest(row["catalog_digest"]),
        state=TaskState(row["state"]),
        selected_capability_id=row["selected_capability_id"],
        candidate_reference=StableId(row["candidate_reference"]) if row["candidate_reference"] else None,
        created_at=_parse_time(row["created_at"]),
        revised_at=_parse_time(row["revised_at"]),
    )


def _invocation(row: object) -> AgentInvocation:
    grant = DelegatedApplicationGrant(
        grant_id=StableId(row["grant_id"]),
        task_id=StableId(row["task_id"]),
        task_revision=Revision(row["task_revision"]),
        capability_id=row["capability_id"],
        allowed_use_cases=tuple(json.loads(row["allowed_use_cases_json"])),
        allowed_effect_classes=tuple(EffectClass(item) for item in json.loads(row["allowed_effects_json"])),
        scope_id=StableId(row["scope_id"]),
        classification=row["classification"],
        digest=Digest(row["grant_digest"]),
    )
    return AgentInvocation(
        invocation_id=StableId(row["invocation_id"]),
        task_id=StableId(row["task_id"]),
        task_revision=Revision(row["task_revision"]),
        capability_id=row["capability_id"],
        grant=grant,
        input_digest=Digest(row["input_digest"]),
        created_at=_parse_time(row["created_at"]),
        digest=Digest(row["invocation_digest"]),
    )


def _call(row: object) -> ApplicationCallRecord:
    return ApplicationCallRecord(
        call_id=StableId(row["call_id"]),
        task_id=StableId(row["task_id"]),
        logical_occurrence=row["logical_occurrence"],
        invocation_id=StableId(row["invocation_id"]),
        use_case=row["use_case"],
        effect_class=EffectClass(row["effect_class"]),
        request_digest=Digest(row["request_digest"]),
        application_idempotency_key=IdempotencyKey(row["application_idempotency_key"]),
        revision=Revision(row["revision"]),
        state=ApplicationCallState(row["state"]),
        result_reference=row["result_reference"],
        result_digest=Digest(row["result_digest"]) if row["result_digest"] else None,
    )


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)
