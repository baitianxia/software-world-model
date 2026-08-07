"""SQLite authority store for recoverable management orchestration."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

from software_world_model.application_services.management import (
    ConfigureSystemSourceCommand,
    ManagementAttempt,
    ManagementAttemptState,
    ManagementExecution,
    ManagementResult,
    ManagementStep,
    ManagementStepState,
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
from software_world_model.knowledge_engine import ScopeType

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_management_commands (
    command_id TEXT PRIMARY KEY,
    command_type TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    command_json TEXT NOT NULL,
    attempt_id TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_management_attempt_roots (
    attempt_id TEXT PRIMARY KEY,
    command_id TEXT NOT NULL UNIQUE,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    current_state TEXT NOT NULL,
    cancel_requested INTEGER NOT NULL CHECK (cancel_requested IN (0, 1)),
    cancellation_reason TEXT,
    created_at TEXT NOT NULL,
    revised_at TEXT NOT NULL,
    FOREIGN KEY (command_id) REFERENCES app_management_commands(command_id)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS app_management_attempt_revisions (
    attempt_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    state TEXT NOT NULL,
    cancel_requested INTEGER NOT NULL CHECK (cancel_requested IN (0, 1)),
    cancellation_reason TEXT,
    occurred_at TEXT NOT NULL,
    PRIMARY KEY (attempt_id, revision),
    FOREIGN KEY (attempt_id) REFERENCES app_management_attempt_roots(attempt_id)
);

CREATE TABLE IF NOT EXISTS app_management_step_roots (
    step_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 1),
    name TEXT NOT NULL,
    owner_contract TEXT NOT NULL,
    owner_idempotency_key TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    current_state TEXT NOT NULL,
    UNIQUE (attempt_id, ordinal),
    UNIQUE (attempt_id, name),
    UNIQUE (owner_contract, owner_idempotency_key),
    FOREIGN KEY (attempt_id) REFERENCES app_management_attempt_roots(attempt_id)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS app_management_step_revisions (
    step_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    state TEXT NOT NULL,
    dispatch_attempt INTEGER NOT NULL CHECK (dispatch_attempt >= 0),
    result_reference TEXT,
    result_digest TEXT,
    output_json TEXT NOT NULL,
    failure_code TEXT,
    failure_message TEXT,
    retryable INTEGER NOT NULL CHECK (retryable IN (0, 1)),
    occurred_at TEXT NOT NULL,
    PRIMARY KEY (step_id, revision),
    FOREIGN KEY (step_id) REFERENCES app_management_step_roots(step_id)
);

CREATE TABLE IF NOT EXISTS app_management_result_roots (
    result_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL UNIQUE,
    effective_revision INTEGER NOT NULL CHECK (effective_revision >= 1),
    FOREIGN KEY (attempt_id) REFERENCES app_management_attempt_roots(attempt_id)
        DEFERRABLE INITIALLY DEFERRED
);

CREATE TABLE IF NOT EXISTS app_management_result_revisions (
    result_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    supersedes_revision INTEGER,
    command_id TEXT NOT NULL,
    attempt_id TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    caller TEXT NOT NULL,
    overall_state TEXT NOT NULL,
    steps_json TEXT NOT NULL,
    result_digest TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    PRIMARY KEY (result_id, revision),
    FOREIGN KEY (result_id) REFERENCES app_management_result_roots(result_id)
        DEFERRABLE INITIALLY DEFERRED
);
"""


class SqliteManagementRepository:
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def prepare(
        self,
        *,
        command: ConfigureSystemSourceCommand,
        steps: tuple[tuple[str, str, IdempotencyKey, Digest], ...],
        occurred_at: datetime,
    ) -> ManagementExecution:
        try:
            with self._database.transaction() as connection:
                existing = connection.execute(
                    "SELECT command_id, request_digest FROM app_management_commands WHERE idempotency_key = ?",
                    (command.idempotency_key.value,),
                ).fetchone()
                if existing is not None:
                    if existing["request_digest"] != command.request_digest.value:
                        raise DomainError(
                            ErrorCode.IDEMPOTENCY_MISMATCH,
                            "management idempotency key was reused with a different request",
                        )
                    return self._load_execution(connection, StableId(existing["command_id"]))

                command_id = self._ids.new("management_command")
                attempt_id = self._ids.new("management_attempt")
                result_id = self._ids.new("management_result")
                timestamp = _time(occurred_at)
                connection.execute(
                    "INSERT INTO app_management_commands VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        command_id.value,
                        "ConfigureSystemSource@1",
                        command.idempotency_key.value,
                        command.request_digest.value,
                        _command_json(command),
                        attempt_id.value,
                        timestamp,
                    ),
                )
                connection.execute(
                    "INSERT INTO app_management_attempt_roots VALUES (?, ?, 1, ?, 0, NULL, ?, ?)",
                    (
                        attempt_id.value,
                        command_id.value,
                        ManagementAttemptState.PREPARED.value,
                        timestamp,
                        timestamp,
                    ),
                )
                connection.execute(
                    "INSERT INTO app_management_attempt_revisions VALUES (?, 1, ?, 0, NULL, ?)",
                    (attempt_id.value, ManagementAttemptState.PREPARED.value, timestamp),
                )
                initial_steps: list[ManagementStep] = []
                for ordinal, (name, contract, owner_key, request_digest) in enumerate(steps, 1):
                    step_id = self._ids.new("management_step")
                    connection.execute(
                        """INSERT INTO app_management_step_roots
                           VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)""",
                        (
                            step_id.value,
                            attempt_id.value,
                            ordinal,
                            name,
                            contract,
                            owner_key.value,
                            request_digest.value,
                            ManagementStepState.NOT_STARTED.value,
                        ),
                    )
                    connection.execute(
                        """INSERT INTO app_management_step_revisions
                           VALUES (?, 1, ?, 0, NULL, NULL, '{}', NULL, NULL, 0, ?)""",
                        (step_id.value, ManagementStepState.NOT_STARTED.value, timestamp),
                    )
                    initial_steps.append(
                        ManagementStep(
                            step_id=step_id,
                            attempt_id=attempt_id,
                            ordinal=ordinal,
                            name=name,
                            owner_contract=contract,
                            owner_idempotency_key=owner_key,
                            request_digest=request_digest,
                            revision=Revision(1),
                            state=ManagementStepState.NOT_STARTED,
                            dispatch_attempt=0,
                            result_reference=None,
                            result_digest=None,
                            output=(),
                            failure_code=None,
                            failure_message=None,
                            retryable=False,
                            occurred_at=occurred_at,
                        )
                    )
                connection.execute(
                    "INSERT INTO app_management_result_roots VALUES (?, ?, 1)",
                    (result_id.value, attempt_id.value),
                )
                self._insert_result(
                    connection,
                    result_id=result_id,
                    revision=Revision(1),
                    supersedes=None,
                    command_id=command_id,
                    attempt_id=attempt_id,
                    request_digest=command.request_digest,
                    caller=command.caller,
                    state=ManagementAttemptState.PREPARED,
                    steps=tuple(initial_steps),
                    occurred_at=occurred_at,
                )
                return self._load_execution(connection, command_id)
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

    def get_by_attempt(self, attempt_id: StableId) -> ManagementExecution:
        with self._database.read() as connection:
            row = connection.execute(
                "SELECT command_id FROM app_management_attempt_roots WHERE attempt_id = ?",
                (attempt_id.value,),
            ).fetchone()
            if row is None:
                raise DomainError(
                    ErrorCode.MANAGEMENT_ATTEMPT_NOT_FOUND, "management attempt was not found"
                )
            return self._load_execution(connection, StableId(row["command_id"]))

    def transition_step(
        self,
        *,
        step_id: StableId,
        expected_revision: Revision,
        target: ManagementStepState,
        result_reference: str | None,
        result_digest: Digest | None,
        output: dict[str, str] | None,
        failure_code: str | None,
        failure_message: str | None,
        retryable: bool,
        occurred_at: datetime,
    ) -> ManagementExecution:
        try:
            with self._database.transaction() as connection:
                root = connection.execute(
                    """SELECT attempt_id, current_revision, current_state
                       FROM app_management_step_roots WHERE step_id = ?""",
                    (step_id.value,),
                ).fetchone()
                if root is None:
                    raise DomainError(
                        ErrorCode.MANAGEMENT_ATTEMPT_NOT_FOUND, "management step was not found"
                    )
                if root["current_revision"] != expected_revision.value:
                    raise DomainError(
                        ErrorCode.REVISION_CONFLICT,
                        "management step revision is stale",
                        {
                            "expected_revision": expected_revision.value,
                            "actual_revision": root["current_revision"],
                        },
                    )
                current = ManagementStepState(root["current_state"])
                if target not in _ALLOWED_STEP_TRANSITIONS[current]:
                    raise DomainError(
                        ErrorCode.MANAGEMENT_STATE_CONFLICT,
                        f"step cannot transition from {current.value} to {target.value}",
                    )
                if target is ManagementStepState.SUCCEEDED:
                    if not result_reference or result_digest is None:
                        raise DomainError(
                            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                            "successful management step requires an owner result",
                        )
                elif result_reference is not None or result_digest is not None:
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "non-successful management step cannot claim an owner result",
                    )
                new_revision = expected_revision.next()
                prior = connection.execute(
                    """SELECT dispatch_attempt FROM app_management_step_revisions
                       WHERE step_id = ? AND revision = ?""",
                    (step_id.value, expected_revision.value),
                ).fetchone()
                dispatch_attempt = prior["dispatch_attempt"] + (
                    1 if target is ManagementStepState.DISPATCHED else 0
                )
                connection.execute(
                    """INSERT INTO app_management_step_revisions
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        step_id.value,
                        new_revision.value,
                        target.value,
                        dispatch_attempt,
                        result_reference,
                        result_digest.value if result_digest else None,
                        _fields_json(output),
                        failure_code,
                        failure_message,
                        int(retryable),
                        _time(occurred_at),
                    ),
                )
                cursor = connection.execute(
                    """UPDATE app_management_step_roots
                       SET current_revision = ?, current_state = ?
                       WHERE step_id = ? AND current_revision = ?""",
                    (new_revision.value, target.value, step_id.value, expected_revision.value),
                )
                if cursor.rowcount != 1:
                    raise DomainError(ErrorCode.REVISION_CONFLICT, "management step changed")
                command_id = self._advance_attempt_and_result(
                    connection, StableId(root["attempt_id"]), occurred_at
                )
                return self._load_execution(connection, command_id)
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

    def request_cancel(
        self, *, attempt_id: StableId, reason: str, occurred_at: datetime
    ) -> ManagementExecution:
        with self._database.transaction() as connection:
            root = connection.execute(
                """SELECT command_id, cancel_requested, cancellation_reason
                   FROM app_management_attempt_roots WHERE attempt_id = ?""",
                (attempt_id.value,),
            ).fetchone()
            if root is None:
                raise DomainError(
                    ErrorCode.MANAGEMENT_ATTEMPT_NOT_FOUND, "management attempt was not found"
                )
            if root["cancel_requested"]:
                return self._load_execution(connection, StableId(root["command_id"]))
            connection.execute(
                """UPDATE app_management_attempt_roots
                   SET cancel_requested = 1, cancellation_reason = ?, revised_at = ?
                   WHERE attempt_id = ?""",
                (reason, _time(occurred_at), attempt_id.value),
            )
            command_id = self._advance_attempt_and_result(connection, attempt_id, occurred_at)
            return self._load_execution(connection, command_id)

    def _advance_attempt_and_result(
        self, connection: sqlite3.Connection, attempt_id: StableId, occurred_at: datetime
    ) -> StableId:
        attempt_root = connection.execute(
            "SELECT * FROM app_management_attempt_roots WHERE attempt_id = ?",
            (attempt_id.value,),
        ).fetchone()
        steps = self._load_steps(connection, attempt_id)
        state = _aggregate(steps, bool(attempt_root["cancel_requested"]))
        attempt_revision = Revision(attempt_root["current_revision"] + 1)
        connection.execute(
            """INSERT INTO app_management_attempt_revisions
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                attempt_id.value,
                attempt_revision.value,
                state.value,
                attempt_root["cancel_requested"],
                attempt_root["cancellation_reason"],
                _time(occurred_at),
            ),
        )
        connection.execute(
            """UPDATE app_management_attempt_roots
               SET current_revision = ?, current_state = ?, revised_at = ?
               WHERE attempt_id = ?""",
            (attempt_revision.value, state.value, _time(occurred_at), attempt_id.value),
        )
        result_root = connection.execute(
            "SELECT result_id, effective_revision FROM app_management_result_roots WHERE attempt_id = ?",
            (attempt_id.value,),
        ).fetchone()
        command = connection.execute(
            "SELECT * FROM app_management_commands WHERE command_id = ?",
            (attempt_root["command_id"],),
        ).fetchone()
        result_revision = Revision(result_root["effective_revision"] + 1)
        self._insert_result(
            connection,
            result_id=StableId(result_root["result_id"]),
            revision=result_revision,
            supersedes=Revision(result_root["effective_revision"]),
            command_id=StableId(command["command_id"]),
            attempt_id=attempt_id,
            request_digest=Digest(command["request_digest"]),
            caller=_parse_command(command["command_json"]).caller,
            state=state,
            steps=steps,
            occurred_at=occurred_at,
        )
        connection.execute(
            "UPDATE app_management_result_roots SET effective_revision = ? WHERE result_id = ?",
            (result_revision.value, result_root["result_id"]),
        )
        return StableId(command["command_id"])

    def _insert_result(
        self,
        connection: sqlite3.Connection,
        *,
        result_id: StableId,
        revision: Revision,
        supersedes: Revision | None,
        command_id: StableId,
        attempt_id: StableId,
        request_digest: Digest,
        caller: str,
        state: ManagementAttemptState,
        steps: tuple[ManagementStep, ...],
        occurred_at: datetime,
    ) -> None:
        summaries = _step_summaries(steps)
        result_digest = digest_of(
            {
                "result_id": result_id.value,
                "revision": revision.value,
                "supersedes_revision": supersedes.value if supersedes else None,
                "command_id": command_id.value,
                "attempt_id": attempt_id.value,
                "request_digest": request_digest.value,
                "caller": caller,
                "overall_state": state.value,
                "steps": summaries,
                "occurred_at": occurred_at,
            }
        )
        connection.execute(
            """INSERT INTO app_management_result_revisions
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                result_id.value,
                revision.value,
                supersedes.value if supersedes else None,
                command_id.value,
                attempt_id.value,
                request_digest.value,
                caller,
                state.value,
                canonical_json_bytes(summaries).decode("utf-8"),
                result_digest.value,
                _time(occurred_at),
            ),
        )

    def _load_execution(
        self, connection: sqlite3.Connection, command_id: StableId
    ) -> ManagementExecution:
        command_row = connection.execute(
            "SELECT * FROM app_management_commands WHERE command_id = ?", (command_id.value,)
        ).fetchone()
        if command_row is None:
            raise DomainError(
                ErrorCode.MANAGEMENT_ATTEMPT_NOT_FOUND, "management command was not found"
            )
        attempt_row = connection.execute(
            "SELECT * FROM app_management_attempt_roots WHERE command_id = ?", (command_id.value,)
        ).fetchone()
        attempt_id = StableId(attempt_row["attempt_id"])
        steps = self._load_steps(connection, attempt_id)
        result_root = connection.execute(
            "SELECT * FROM app_management_result_roots WHERE attempt_id = ?", (attempt_id.value,)
        ).fetchone()
        result_row = connection.execute(
            """SELECT * FROM app_management_result_revisions
               WHERE result_id = ? AND revision = ?""",
            (result_root["result_id"], result_root["effective_revision"]),
        ).fetchone()
        return ManagementExecution(
            command=_parse_command(command_row["command_json"]),
            attempt=ManagementAttempt(
                attempt_id=attempt_id,
                command_id=command_id,
                revision=Revision(attempt_row["current_revision"]),
                state=ManagementAttemptState(attempt_row["current_state"]),
                cancel_requested=bool(attempt_row["cancel_requested"]),
                cancellation_reason=attempt_row["cancellation_reason"],
                created_at=_parse_time(attempt_row["created_at"]),
                revised_at=_parse_time(attempt_row["revised_at"]),
            ),
            result=ManagementResult(
                result_id=StableId(result_row["result_id"]),
                revision=Revision(result_row["revision"]),
                supersedes_revision=(
                    Revision(result_row["supersedes_revision"])
                    if result_row["supersedes_revision"] is not None
                    else None
                ),
                command_id=command_id,
                attempt_id=attempt_id,
                request_digest=Digest(result_row["request_digest"]),
                caller=result_row["caller"],
                overall_state=ManagementAttemptState(result_row["overall_state"]),
                steps=steps,
                result_digest=Digest(result_row["result_digest"]),
                occurred_at=_parse_time(result_row["occurred_at"]),
            ),
        )

    def _load_steps(
        self, connection: sqlite3.Connection, attempt_id: StableId
    ) -> tuple[ManagementStep, ...]:
        rows = connection.execute(
            """SELECT root.*, revision.state, revision.dispatch_attempt,
                      revision.result_reference, revision.result_digest,
                      revision.output_json, revision.failure_code,
                      revision.failure_message, revision.retryable, revision.occurred_at
               FROM app_management_step_roots AS root
               JOIN app_management_step_revisions AS revision
                 ON revision.step_id = root.step_id
                AND revision.revision = root.current_revision
               WHERE root.attempt_id = ? ORDER BY root.ordinal""",
            (attempt_id.value,),
        ).fetchall()
        return tuple(
            ManagementStep(
                step_id=StableId(row["step_id"]),
                attempt_id=attempt_id,
                ordinal=row["ordinal"],
                name=row["name"],
                owner_contract=row["owner_contract"],
                owner_idempotency_key=IdempotencyKey(row["owner_idempotency_key"]),
                request_digest=Digest(row["request_digest"]),
                revision=Revision(row["current_revision"]),
                state=ManagementStepState(row["state"]),
                dispatch_attempt=row["dispatch_attempt"],
                result_reference=row["result_reference"],
                result_digest=Digest(row["result_digest"]) if row["result_digest"] else None,
                output=tuple(sorted(json.loads(row["output_json"]).items())),
                failure_code=row["failure_code"],
                failure_message=row["failure_message"],
                retryable=bool(row["retryable"]),
                occurred_at=_parse_time(row["occurred_at"]),
            )
            for row in rows
        )


_ALLOWED_STEP_TRANSITIONS = {
    ManagementStepState.NOT_STARTED: {
        ManagementStepState.DISPATCHED,
        ManagementStepState.CANCELED_BEFORE_DISPATCH,
    },
    ManagementStepState.DISPATCHED: {
        ManagementStepState.SUCCEEDED,
        ManagementStepState.FAILED,
        ManagementStepState.OUTCOME_PENDING,
    },
    ManagementStepState.OUTCOME_PENDING: {
        ManagementStepState.SUCCEEDED,
        ManagementStepState.FAILED,
    },
    ManagementStepState.FAILED: {ManagementStepState.DISPATCHED},
    ManagementStepState.SUCCEEDED: set(),
    ManagementStepState.CANCELED_BEFORE_DISPATCH: set(),
}


def _aggregate(
    steps: tuple[ManagementStep, ...], cancel_requested: bool
) -> ManagementAttemptState:
    states = {step.state for step in steps}
    if ManagementStepState.DISPATCHED in states or ManagementStepState.OUTCOME_PENDING in states:
        return ManagementAttemptState.OUTCOME_PENDING
    if states == {ManagementStepState.SUCCEEDED}:
        return ManagementAttemptState.SUCCEEDED
    successes = sum(step.state is ManagementStepState.SUCCEEDED for step in steps)
    failures = ManagementStepState.FAILED in states
    canceled = ManagementStepState.CANCELED_BEFORE_DISPATCH in states
    if failures or canceled:
        if successes:
            return ManagementAttemptState.PARTIALLY_SUCCEEDED
        return ManagementAttemptState.CANCELED if canceled and not failures else ManagementAttemptState.FAILED
    if successes or cancel_requested:
        return ManagementAttemptState.RUNNING
    return ManagementAttemptState.PREPARED


def _step_summaries(steps: tuple[ManagementStep, ...]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "step_id": step.step_id.value,
            "ordinal": step.ordinal,
            "name": step.name,
            "owner_contract": step.owner_contract,
            "owner_idempotency_key": step.owner_idempotency_key.value,
            "request_digest": step.request_digest.value,
            "revision": step.revision.value,
            "state": step.state.value,
            "dispatch_attempt": step.dispatch_attempt,
            "result_reference": step.result_reference,
            "result_digest": step.result_digest.value if step.result_digest else None,
            "failure_code": step.failure_code,
            "retryable": step.retryable,
        }
        for step in steps
    )


def _command_json(command: ConfigureSystemSourceCommand) -> str:
    payload = {
        "idempotency_key": command.idempotency_key.value,
        "caller": command.caller,
        "purpose": command.purpose,
        "classification": command.classification,
        "request_context": dict(command.request_context),
        "scope_type": command.scope_type.value,
        "scope_metadata": dict(command.scope_metadata),
        "provider_type": command.provider_type,
        "provider_contract_version": command.provider_contract_version,
        "identity_domain": command.identity_domain,
        "source_target": command.source_target,
        "provider_configuration": dict(command.provider_configuration),
        "secret_reference": command.secret_reference,
        "selector": dict(command.selector),
        "context_constraint": dict(command.context_constraint),
        "context_hint": command.context_hint,
        "actor": command.actor,
        "reason": command.reason,
        "correlation_ref": command.correlation_ref.value,
    }
    return canonical_json_bytes(payload).decode("utf-8")


def _parse_command(value: str) -> ConfigureSystemSourceCommand:
    payload = json.loads(value)
    return ConfigureSystemSourceCommand.create(
        idempotency_key=IdempotencyKey(payload["idempotency_key"]),
        caller=payload["caller"],
        purpose=payload["purpose"],
        classification=payload["classification"],
        request_context=payload["request_context"],
        scope_type=ScopeType(payload["scope_type"]),
        scope_metadata=payload["scope_metadata"],
        provider_type=payload["provider_type"],
        provider_contract_version=payload["provider_contract_version"],
        identity_domain=payload["identity_domain"],
        source_target=payload["source_target"],
        provider_configuration=payload["provider_configuration"],
        secret_reference=payload["secret_reference"],
        selector=payload["selector"],
        context_constraint=payload["context_constraint"],
        context_hint=payload["context_hint"],
        actor=payload["actor"],
        reason=payload["reason"],
        correlation_ref=CorrelationRef(payload["correlation_ref"]),
    )


def _fields_json(values: dict[str, str] | None) -> str:
    return canonical_json_bytes(values or {}).decode("utf-8")


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _integrity_error(exc: sqlite3.IntegrityError) -> DomainError:
    return DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        "management transaction violated a store invariant",
        {"sqlite_error": str(exc)},
    )
