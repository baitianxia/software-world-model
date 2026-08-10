"""SQLite authority records for exact Structure Snapshot read sessions."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

from software_world_model.application_services.knowledge_use import TaskBoundary
from software_world_model.application_services.structure_read_session import (
    StructureCoverageReadBinding,
    StructureReadOrder,
    StructureReadPurpose,
    StructureReadSelectionMode,
    StructureReadSession,
    StructureReadSessionRepository,
    StructureSnapshotReadBinding,
    structure_ordered_read_set_digest,
    structure_read_session_digest,
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
)
from software_world_model.knowledge_engine.scope import (
    AssertionOutcome,
    ScopeLifecycle,
    ScopePurpose,
    ScopeStateAssertion,
    ScopeType,
)
from software_world_model.knowledge_engine.context_comparison import (
    StructureContextComparisonAssessment,
    StructureContextComparisonOutcome,
    StructureContextComparisonPurpose,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_structure_read_sessions (
    session_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    scope_id TEXT NOT NULL,
    scope_revision INTEGER NOT NULL CHECK (scope_revision >= 1),
    task_boundary_json TEXT NOT NULL,
    task_boundary_digest TEXT NOT NULL,
    scope_assertion_json TEXT NOT NULL,
    scope_assertion_digest TEXT NOT NULL,
    caller_ref TEXT NOT NULL,
    read_purpose TEXT NOT NULL CHECK (
        read_purpose IN (
            'STRUCTURE_EXACT_SNAPSHOT_READ@1',
            'STRUCTURE_SNAPSHOT_COMPARISON@1'
        )
    ),
    selection_mode TEXT NOT NULL CHECK (
        selection_mode IN ('CURRENT', 'ORDERED_EXACT')
    ),
    read_order TEXT NOT NULL CHECK (
        read_order IN ('SINGLE', 'CALLER_DECLARED')
    ),
    read_set_digest TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    session_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_structure_read_session_snapshots (
    session_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    scope_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    snapshot_revision INTEGER NOT NULL CHECK (snapshot_revision >= 1),
    snapshot_manifest_digest TEXT NOT NULL,
    schema_ref TEXT NOT NULL,
    schema_digest TEXT NOT NULL,
    schema_registration_digest TEXT NOT NULL,
    schema_availability_digest TEXT NOT NULL,
    schema_adoption_digest TEXT NOT NULL,
    coverage_set_digest TEXT NOT NULL,
    binding_digest TEXT NOT NULL,
    PRIMARY KEY (session_id, ordinal),
    UNIQUE (session_id, snapshot_id),
    FOREIGN KEY (session_id) REFERENCES app_structure_read_sessions(session_id)
);

CREATE TABLE IF NOT EXISTS app_structure_read_session_coverages (
    session_id TEXT NOT NULL,
    snapshot_ordinal INTEGER NOT NULL CHECK (snapshot_ordinal >= 0),
    coverage_ordinal INTEGER NOT NULL CHECK (coverage_ordinal >= 0),
    coverage_root_id TEXT NOT NULL,
    coverage_root_digest TEXT NOT NULL,
    coverage_root_ref TEXT NOT NULL,
    coverage_state_id TEXT NOT NULL,
    coverage_state_digest TEXT NOT NULL,
    profile_ref TEXT NOT NULL,
    schema_ref TEXT NOT NULL,
    schema_digest TEXT NOT NULL,
    source_binding_id TEXT NOT NULL,
    logical_reactor_root TEXT NOT NULL,
    evaluation_context_ref TEXT NOT NULL,
    evaluation_context_digest TEXT NOT NULL,
    canonicalization_ref TEXT NOT NULL,
    canonicalization_digest TEXT NOT NULL,
    knowledge_context_digest TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    member_manifest_digest TEXT NOT NULL,
    comparison_basis_digest TEXT NOT NULL,
    binding_digest TEXT NOT NULL,
    PRIMARY KEY (session_id, snapshot_ordinal, coverage_ordinal),
    UNIQUE (session_id, snapshot_ordinal, coverage_root_id),
    FOREIGN KEY (session_id, snapshot_ordinal)
        REFERENCES app_structure_read_session_snapshots(session_id, ordinal)
);

CREATE TABLE IF NOT EXISTS app_structure_read_session_context_comparisons (
    session_id TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    assessment_id TEXT NOT NULL,
    purpose TEXT NOT NULL CHECK (
        purpose = 'STRUCTURE_SNAPSHOT_COMPARISON@1'
    ),
    base_snapshot_id TEXT NOT NULL,
    base_snapshot_binding_digest TEXT NOT NULL,
    target_snapshot_id TEXT NOT NULL,
    target_snapshot_binding_digest TEXT NOT NULL,
    base_knowledge_context_digests_json TEXT NOT NULL,
    target_knowledge_context_digests_json TEXT NOT NULL,
    comparison_basis_digests_json TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome = 'COMPATIBLE'),
    assessment_digest TEXT NOT NULL,
    PRIMARY KEY (session_id, ordinal),
    UNIQUE (session_id, assessment_id),
    FOREIGN KEY (session_id) REFERENCES app_structure_read_sessions(session_id)
);
"""


class SqliteStructureReadSessionRepository(StructureReadSessionRepository):
    def __init__(
        self,
        database: SqliteDatabase,
        *,
        id_generator: IdGenerator | None = None,
    ) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def replay_open(
        self, *, idempotency_key: IdempotencyKey, request_digest: Digest
    ) -> StructureReadSession | None:
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT session_id, request_digest
                   FROM app_structure_read_sessions WHERE idempotency_key = ?""",
                (idempotency_key.value,),
            ).fetchone()
            if row is None:
                return None
            if row["request_digest"] != request_digest.value:
                raise DomainError(
                    ErrorCode.IDEMPOTENCY_MISMATCH,
                    "Structure read Session idempotency key has a different request",
                )
            return self._load_session(connection, StableId(row["session_id"]))

    def save_session(
        self,
        *,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        scope_id: StableId,
        scope_revision: Revision,
        task_boundary: TaskBoundary,
        scope_assertion: ScopeStateAssertion,
        caller_ref: str,
        purpose: StructureReadPurpose,
        selection_mode: StructureReadSelectionMode,
        order: StructureReadOrder,
        snapshots: tuple[StructureSnapshotReadBinding, ...],
        context_comparisons: tuple[StructureContextComparisonAssessment, ...],
        opened_at: datetime,
    ) -> StructureReadSession:
        session = _create_session(
            session_id=self._ids.new("structure_read_session"),
            request_digest=request_digest,
            scope_id=scope_id,
            scope_revision=scope_revision,
            task_boundary=task_boundary,
            scope_assertion=scope_assertion,
            caller_ref=caller_ref,
            purpose=purpose,
            selection_mode=selection_mode,
            order=order,
            snapshots=snapshots,
            context_comparisons=context_comparisons,
            opened_at=opened_at,
        )
        try:
            with self._database.transaction() as connection:
                existing = connection.execute(
                    """SELECT session_id, request_digest
                       FROM app_structure_read_sessions
                       WHERE idempotency_key = ?""",
                    (idempotency_key.value,),
                ).fetchone()
                if existing is not None:
                    if existing["request_digest"] != request_digest.value:
                        raise DomainError(
                            ErrorCode.IDEMPOTENCY_MISMATCH,
                            "Structure read Session idempotency key has a different request",
                        )
                    return self._load_session(
                        connection, StableId(existing["session_id"])
                    )
                self._insert_session(connection, idempotency_key, session)
                return self._load_session(connection, session.session_id)
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            # A concurrent writer may have won the same idempotent command.
            replay = self.replay_open(
                idempotency_key=idempotency_key,
                request_digest=request_digest,
            )
            if replay is not None:
                return replay
            raise _inconsistent(
                "Structure read Session violated a persistence invariant"
            ) from exc

    def get_session(self, session_id: StableId) -> StructureReadSession:
        with self._database.read() as connection:
            return self._load_session(connection, session_id)

    @staticmethod
    def _insert_session(
        connection: sqlite3.Connection,
        idempotency_key: IdempotencyKey,
        session: StructureReadSession,
    ) -> None:
        session.require_valid()
        connection.execute(
            """INSERT INTO app_structure_read_sessions (
                   session_id, idempotency_key, request_digest, scope_id,
                   scope_revision, task_boundary_json, task_boundary_digest,
                   scope_assertion_json, scope_assertion_digest, caller_ref,
                   read_purpose, selection_mode, read_order, read_set_digest,
                   opened_at, session_digest
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                session.session_id.value,
                idempotency_key.value,
                session.request_digest.value,
                session.scope_id.value,
                session.scope_revision.value,
                _json(_task_boundary_core(session.task_boundary)),
                session.task_boundary.digest.value,
                _json(_scope_assertion_core(session.scope_assertion)),
                session.scope_assertion.digest.value,
                session.caller_ref,
                session.purpose.value,
                session.selection_mode.value,
                session.order.value,
                session.read_set_digest.value,
                _time(session.opened_at),
                session.digest.value,
            ),
        )
        for snapshot_ordinal, snapshot in enumerate(session.snapshots):
            connection.execute(
                """INSERT INTO app_structure_read_session_snapshots (
                       session_id, ordinal, scope_id, snapshot_id,
                       snapshot_revision, snapshot_manifest_digest, schema_ref,
                       schema_digest, schema_registration_digest,
                       schema_availability_digest, schema_adoption_digest,
                       coverage_set_digest, binding_digest
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session.session_id.value,
                    snapshot_ordinal,
                    snapshot.scope_id.value,
                    snapshot.snapshot_id.value,
                    snapshot.snapshot_revision.value,
                    snapshot.snapshot_manifest_digest.value,
                    snapshot.schema_ref,
                    snapshot.schema_digest.value,
                    snapshot.schema_registration_digest.value,
                    snapshot.schema_availability_digest.value,
                    snapshot.schema_adoption_digest.value,
                    snapshot.coverage_set_digest.value,
                    snapshot.digest.value,
                ),
            )
            for coverage_ordinal, coverage in enumerate(snapshot.coverages):
                connection.execute(
                    """INSERT INTO app_structure_read_session_coverages (
                           session_id, snapshot_ordinal, coverage_ordinal,
                           coverage_root_id, coverage_root_digest,
                           coverage_root_ref, coverage_state_id,
                           coverage_state_digest, profile_ref, schema_ref,
                           schema_digest, source_binding_id,
                           logical_reactor_root, evaluation_context_ref,
                           evaluation_context_digest, canonicalization_ref,
                           canonicalization_digest, knowledge_context_digest,
                           source_revision, member_manifest_digest,
                           comparison_basis_digest, binding_digest
                       ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        session.session_id.value,
                        snapshot_ordinal,
                        coverage_ordinal,
                        coverage.coverage_root_id.value,
                        coverage.coverage_root_digest.value,
                        coverage.coverage_root_ref,
                        coverage.coverage_state_id.value,
                        coverage.coverage_state_digest.value,
                        coverage.profile_ref,
                        coverage.schema_ref,
                        coverage.schema_digest.value,
                        coverage.source_binding_id.value,
                        coverage.logical_reactor_root,
                        coverage.evaluation_context_ref,
                        coverage.evaluation_context_digest.value,
                        coverage.canonicalization_ref,
                        coverage.canonicalization_digest.value,
                        coverage.knowledge_context_digest.value,
                        coverage.source_revision,
                        coverage.member_manifest_digest.value,
                        coverage.comparison_basis_digest.value,
                        coverage.digest.value,
                    ),
                )
        for comparison in session.context_comparisons:
            connection.execute(
                """INSERT INTO app_structure_read_session_context_comparisons (
                       session_id, ordinal, assessment_id, purpose,
                       base_snapshot_id, base_snapshot_binding_digest,
                       target_snapshot_id, target_snapshot_binding_digest,
                       base_knowledge_context_digests_json,
                       target_knowledge_context_digests_json,
                       comparison_basis_digests_json, outcome,
                       assessment_digest
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    session.session_id.value,
                    comparison.ordinal,
                    comparison.assessment_id.value,
                    comparison.purpose.value,
                    comparison.base_snapshot_id.value,
                    comparison.base_snapshot_binding_digest.value,
                    comparison.target_snapshot_id.value,
                    comparison.target_snapshot_binding_digest.value,
                    _json(
                        tuple(
                            item.value
                            for item in comparison.base_knowledge_context_digests
                        )
                    ),
                    _json(
                        tuple(
                            item.value
                            for item in comparison.target_knowledge_context_digests
                        )
                    ),
                    _json(
                        tuple(
                            item.value for item in comparison.comparison_basis_digests
                        )
                    ),
                    comparison.outcome.value,
                    comparison.digest.value,
                ),
            )

    @staticmethod
    def _load_session(
        connection: sqlite3.Connection, session_id: StableId
    ) -> StructureReadSession:
        row = connection.execute(
            "SELECT * FROM app_structure_read_sessions WHERE session_id = ?",
            (session_id.value,),
        ).fetchone()
        if row is None:
            raise _invalid(
                "READ_SESSION_NOT_FOUND",
                "Structure read Session was not found",
            )
        try:
            snapshot_rows = connection.execute(
                """SELECT * FROM app_structure_read_session_snapshots
                   WHERE session_id = ? ORDER BY ordinal""",
                (session_id.value,),
            ).fetchall()
            if [item["ordinal"] for item in snapshot_rows] != list(
                range(len(snapshot_rows))
            ):
                raise ValueError("Snapshot ordinals are not contiguous")
            snapshots: list[StructureSnapshotReadBinding] = []
            for snapshot_row in snapshot_rows:
                coverage_rows = connection.execute(
                    """SELECT * FROM app_structure_read_session_coverages
                       WHERE session_id = ? AND snapshot_ordinal = ?
                       ORDER BY coverage_ordinal""",
                    (session_id.value, snapshot_row["ordinal"]),
                ).fetchall()
                if [item["coverage_ordinal"] for item in coverage_rows] != list(
                    range(len(coverage_rows))
                ):
                    raise ValueError("Coverage ordinals are not contiguous")
                coverages = tuple(
                    StructureCoverageReadBinding(
                        coverage_root_id=StableId(item["coverage_root_id"]),
                        coverage_root_digest=Digest(item["coverage_root_digest"]),
                        coverage_root_ref=item["coverage_root_ref"],
                        coverage_state_id=StableId(item["coverage_state_id"]),
                        coverage_state_digest=Digest(item["coverage_state_digest"]),
                        profile_ref=item["profile_ref"],
                        schema_ref=item["schema_ref"],
                        schema_digest=Digest(item["schema_digest"]),
                        source_binding_id=StableId(item["source_binding_id"]),
                        logical_reactor_root=item["logical_reactor_root"],
                        evaluation_context_ref=item["evaluation_context_ref"],
                        evaluation_context_digest=Digest(
                            item["evaluation_context_digest"]
                        ),
                        canonicalization_ref=item["canonicalization_ref"],
                        canonicalization_digest=Digest(
                            item["canonicalization_digest"]
                        ),
                        knowledge_context_digest=Digest(
                            item["knowledge_context_digest"]
                        ),
                        source_revision=item["source_revision"],
                        member_manifest_digest=Digest(
                            item["member_manifest_digest"]
                        ),
                        comparison_basis_digest=Digest(
                            item["comparison_basis_digest"]
                        ),
                        digest=Digest(item["binding_digest"]),
                    )
                    for item in coverage_rows
                )
                snapshots.append(
                    StructureSnapshotReadBinding(
                        scope_id=StableId(snapshot_row["scope_id"]),
                        snapshot_id=StableId(snapshot_row["snapshot_id"]),
                        snapshot_revision=Revision(
                            snapshot_row["snapshot_revision"]
                        ),
                        snapshot_manifest_digest=Digest(
                            snapshot_row["snapshot_manifest_digest"]
                        ),
                        schema_ref=snapshot_row["schema_ref"],
                        schema_digest=Digest(snapshot_row["schema_digest"]),
                        schema_registration_digest=Digest(
                            snapshot_row["schema_registration_digest"]
                        ),
                        schema_availability_digest=Digest(
                            snapshot_row["schema_availability_digest"]
                        ),
                        schema_adoption_digest=Digest(
                            snapshot_row["schema_adoption_digest"]
                        ),
                        coverages=coverages,
                        coverage_set_digest=Digest(
                            snapshot_row["coverage_set_digest"]
                        ),
                        digest=Digest(snapshot_row["binding_digest"]),
                    )
                )
            comparison_rows = connection.execute(
                """SELECT *
                   FROM app_structure_read_session_context_comparisons
                   WHERE session_id = ? ORDER BY ordinal""",
                (session_id.value,),
            ).fetchall()
            if [item["ordinal"] for item in comparison_rows] != list(
                range(len(comparison_rows))
            ):
                raise ValueError("Context Comparison ordinals are not contiguous")
            comparisons = tuple(
                StructureContextComparisonAssessment(
                    assessment_id=StableId(item["assessment_id"]),
                    ordinal=item["ordinal"],
                    purpose=StructureContextComparisonPurpose(item["purpose"]),
                    base_snapshot_id=StableId(item["base_snapshot_id"]),
                    base_snapshot_binding_digest=Digest(
                        item["base_snapshot_binding_digest"]
                    ),
                    target_snapshot_id=StableId(item["target_snapshot_id"]),
                    target_snapshot_binding_digest=Digest(
                        item["target_snapshot_binding_digest"]
                    ),
                    base_knowledge_context_digests=_digest_tuple(
                        item["base_knowledge_context_digests_json"]
                    ),
                    target_knowledge_context_digests=_digest_tuple(
                        item["target_knowledge_context_digests_json"]
                    ),
                    comparison_basis_digests=_digest_tuple(
                        item["comparison_basis_digests_json"]
                    ),
                    outcome=StructureContextComparisonOutcome(item["outcome"]),
                    digest=Digest(item["assessment_digest"]),
                )
                for item in comparison_rows
            )
            task_boundary = _task_boundary(
                row["task_boundary_json"],
                Digest(row["task_boundary_digest"]),
            )
            scope_assertion = _scope_assertion(
                row["scope_assertion_json"],
                Digest(row["scope_assertion_digest"]),
            )
            session = StructureReadSession(
                session_id=StableId(row["session_id"]),
                request_digest=Digest(row["request_digest"]),
                scope_id=StableId(row["scope_id"]),
                scope_revision=Revision(row["scope_revision"]),
                task_boundary=task_boundary,
                scope_assertion=scope_assertion,
                caller_ref=row["caller_ref"],
                purpose=StructureReadPurpose(row["read_purpose"]),
                selection_mode=StructureReadSelectionMode(row["selection_mode"]),
                order=StructureReadOrder(row["read_order"]),
                snapshots=tuple(snapshots),
                context_comparisons=comparisons,
                read_set_digest=Digest(row["read_set_digest"]),
                opened_at=_parse_time(row["opened_at"]),
                digest=Digest(row["session_digest"]),
            )
            session.require_valid()
            return session
        except DomainError as exc:
            raise _inconsistent(
                "persisted Structure read Session failed canonical verification"
            ) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise _inconsistent(
                "persisted Structure read Session contains malformed authority fields"
            ) from exc


def _create_session(
    *,
    session_id: StableId,
    request_digest: Digest,
    scope_id: StableId,
    scope_revision: Revision,
    task_boundary: TaskBoundary,
    scope_assertion: ScopeStateAssertion,
    caller_ref: str,
    purpose: StructureReadPurpose,
    selection_mode: StructureReadSelectionMode,
    order: StructureReadOrder,
    snapshots: tuple[StructureSnapshotReadBinding, ...],
    context_comparisons: tuple[StructureContextComparisonAssessment, ...],
    opened_at: datetime,
) -> StructureReadSession:
    read_set_digest = structure_ordered_read_set_digest(
        snapshots,
        context_comparisons,
    )
    session = StructureReadSession(
        session_id=session_id,
        request_digest=request_digest,
        scope_id=scope_id,
        scope_revision=scope_revision,
        task_boundary=task_boundary,
        scope_assertion=scope_assertion,
        caller_ref=caller_ref,
        purpose=purpose,
        selection_mode=selection_mode,
        order=order,
        snapshots=snapshots,
        context_comparisons=context_comparisons,
        read_set_digest=read_set_digest,
        opened_at=opened_at,
        digest=structure_read_session_digest(
            session_id=session_id,
            request_digest=request_digest,
            scope_id=scope_id,
            scope_revision=scope_revision,
            task_boundary=task_boundary,
            scope_assertion=scope_assertion,
            caller_ref=caller_ref,
            purpose=purpose,
            selection_mode=selection_mode,
            order=order,
            read_set_digest=read_set_digest,
            opened_at=opened_at,
        ),
    )
    session.require_valid()
    return session


def _task_boundary_core(boundary: TaskBoundary) -> dict[str, object]:
    return {
        "task_id": boundary.task_id.value,
        "task_revision": boundary.task_revision.value,
        "scope_id": boundary.scope_id.value,
        "purpose": boundary.purpose,
        "classification": boundary.classification,
    }


def _task_boundary(value: str, digest: Digest) -> TaskBoundary:
    core = _json_object(value)
    boundary = TaskBoundary.create(
        task_id=StableId(core["task_id"]),
        task_revision=Revision(core["task_revision"]),
        scope_id=StableId(core["scope_id"]),
        purpose=core["purpose"],
        classification=core["classification"],
    )
    if boundary.digest != digest or value != _json(_task_boundary_core(boundary)):
        raise ValueError("Task Boundary does not match its persisted digest")
    return boundary


def _scope_assertion_core(assertion: ScopeStateAssertion) -> dict[str, object]:
    return {
        "assertion_id": assertion.assertion_id.value,
        **assertion.core(),
    }


def _scope_assertion(value: str, digest: Digest) -> ScopeStateAssertion:
    core = _json_object(value)
    assertion = ScopeStateAssertion(
        assertion_id=StableId(core["assertion_id"]),
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
        digest=digest,
    )
    if not assertion.verify_digest() or value != _json(_scope_assertion_core(assertion)):
        raise ValueError("Scope assertion does not match its persisted digest")
    return assertion


def _digest_tuple(value: str) -> tuple[Digest, ...]:
    raw = json.loads(value)
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise ValueError("digest tuple must be a JSON string array")
    result = tuple(Digest(item) for item in raw)
    if value != _json(tuple(item.value for item in result)):
        raise ValueError("digest tuple is not canonical JSON")
    return result


def _json_object(value: str) -> dict[str, object]:
    raw = json.loads(value)
    if not isinstance(raw, dict) or not all(isinstance(key, str) for key in raw):
        raise ValueError("authority core must be a JSON object")
    return raw


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("Structure read Session time has no timezone")
    return parsed


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


def _inconsistent(message: str) -> DomainError:
    return DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)


__all__ = ["SqliteStructureReadSessionRepository"]
