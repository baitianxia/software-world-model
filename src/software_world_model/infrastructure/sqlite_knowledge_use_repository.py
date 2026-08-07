"""SQLite read-session and sufficiency assessment authority records."""

from __future__ import annotations

from datetime import datetime
import json

from software_world_model.application_services.knowledge_use import (
    KnowledgeRequirement,
    KnowledgeUseRepository,
    NeedStatus,
    NeedSupportProof,
    SnapshotReadSession,
    SufficiencyAssessment,
    SufficiencyItem,
    TaskBoundary,
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
from software_world_model.knowledge_engine import KnowledgeSnapshot

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_snapshot_read_sessions (
    session_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    task_boundary_digest TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    requirement_revision INTEGER NOT NULL,
    snapshot_id TEXT NOT NULL,
    snapshot_revision INTEGER NOT NULL,
    snapshot_manifest_digest TEXT NOT NULL,
    opened_at TEXT NOT NULL,
    session_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_sufficiency_assessments (
    assessment_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    requirement_id TEXT NOT NULL,
    requirement_revision INTEGER NOT NULL,
    read_session_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    items_json TEXT NOT NULL,
    joint_failures_json TEXT NOT NULL,
    sufficient INTEGER NOT NULL CHECK (sufficient IN (0, 1)),
    assessed_at TEXT NOT NULL,
    assessment_digest TEXT NOT NULL,
    FOREIGN KEY (read_session_id) REFERENCES app_snapshot_read_sessions(session_id)
);
"""


class SqliteKnowledgeUseRepository(KnowledgeUseRepository):
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def get_assessment(self, assessment_id: StableId) -> SufficiencyAssessment:
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT * FROM app_sufficiency_assessments
                   WHERE assessment_id = ?""",
                (assessment_id.value,),
            ).fetchone()
            if row is None:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "sufficiency assessment was not found",
                )
            return _assessment(row)

    def open_session(
        self,
        *,
        idempotency_key: IdempotencyKey,
        boundary: TaskBoundary,
        requirement: KnowledgeRequirement,
        snapshot: KnowledgeSnapshot,
        opened_at: datetime,
    ) -> SnapshotReadSession:
        request_digest = digest_of(
            {
                "boundary_digest": boundary.digest.value,
                "requirement_digest": requirement.digest.value,
                "snapshot_id": snapshot.snapshot_id.value,
                "snapshot_manifest_digest": snapshot.manifest_digest.value,
            }
        )
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM app_snapshot_read_sessions WHERE idempotency_key = ?",
                (idempotency_key.value,),
            ).fetchone()
            if row is not None:
                if row["request_digest"] != request_digest.value:
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "snapshot session idempotency key has a different request",
                    )
                return _session(row)
            session_id = self._ids.new("snapshot_session")
            core = {
                "session_id": session_id.value,
                "task_boundary_digest": boundary.digest.value,
                "requirement_id": requirement.requirement_id.value,
                "requirement_revision": requirement.revision.value,
                "snapshot_id": snapshot.snapshot_id.value,
                "snapshot_revision": snapshot.snapshot_revision.value,
                "snapshot_manifest_digest": snapshot.manifest_digest.value,
                "opened_at": opened_at,
            }
            session_digest = digest_of(core)
            connection.execute(
                "INSERT INTO app_snapshot_read_sessions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    session_id.value,
                    idempotency_key.value,
                    request_digest.value,
                    boundary.digest.value,
                    requirement.requirement_id.value,
                    requirement.revision.value,
                    snapshot.snapshot_id.value,
                    snapshot.snapshot_revision.value,
                    snapshot.manifest_digest.value,
                    _time(opened_at),
                    session_digest.value,
                ),
            )
            row = connection.execute(
                "SELECT * FROM app_snapshot_read_sessions WHERE session_id = ?", (session_id.value,)
            ).fetchone()
            return _session(row)

    def record_assessment(
        self,
        *,
        idempotency_key: IdempotencyKey,
        requirement: KnowledgeRequirement,
        session: SnapshotReadSession,
        items: tuple[SufficiencyItem, ...],
        joint_constraint_failures: tuple[str, ...],
        sufficient: bool,
        assessed_at: datetime,
    ) -> SufficiencyAssessment:
        request_digest = digest_of(
            {
                "requirement_digest": requirement.digest.value,
                "session_digest": session.digest.value,
                "items": tuple(_item_payload(item) for item in items),
                "joint_failures": joint_constraint_failures,
                "sufficient": sufficient,
            }
        )
        with self._database.transaction() as connection:
            row = connection.execute(
                "SELECT * FROM app_sufficiency_assessments WHERE idempotency_key = ?",
                (idempotency_key.value,),
            ).fetchone()
            if row is not None:
                if row["request_digest"] != request_digest.value:
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "sufficiency idempotency key has a different assessment",
                    )
                return _assessment(row)
            assessment_id = self._ids.new("sufficiency_assessment")
            core = {
                "assessment_id": assessment_id.value,
                "requirement_id": requirement.requirement_id.value,
                "requirement_revision": requirement.revision.value,
                "read_session_id": session.session_id.value,
                "snapshot_id": session.snapshot_id.value,
                "items": tuple(_item_payload(item) for item in items),
                "joint_failures": joint_constraint_failures,
                "sufficient": sufficient,
                "assessed_at": assessed_at,
            }
            assessment_digest = digest_of(core)
            connection.execute(
                "INSERT INTO app_sufficiency_assessments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    assessment_id.value,
                    idempotency_key.value,
                    request_digest.value,
                    requirement.requirement_id.value,
                    requirement.revision.value,
                    session.session_id.value,
                    session.snapshot_id.value,
                    _json([_item_payload(item) for item in items]),
                    _json(joint_constraint_failures),
                    int(sufficient),
                    _time(assessed_at),
                    assessment_digest.value,
                ),
            )
            row = connection.execute(
                "SELECT * FROM app_sufficiency_assessments WHERE assessment_id = ?",
                (assessment_id.value,),
            ).fetchone()
            return _assessment(row)


def _item_payload(item: SufficiencyItem) -> dict[str, object]:
    proof = item.proof
    return {
        "need_id": item.need_id,
        "status": item.status.value,
        "proof": (
            {
                "proof_id": proof.proof_id.value,
                "need_id": proof.need_id,
                "snapshot_id": proof.snapshot_id.value,
                "snapshot_manifest_digest": proof.snapshot_manifest_digest.value,
                "read_session_id": proof.read_session_id.value,
                "supporting_references": [item.value for item in proof.supporting_references],
                "supporting_digests": [item.value for item in proof.supporting_digests],
                "criterion_digest": proof.criterion_digest.value,
                "digest": proof.digest.value,
            }
            if proof
            else None
        ),
        "gap": item.gap,
        "counterexamples": [value.value for value in item.counterexamples],
        "conflicts": [value.value for value in item.conflicts],
        "unknowns": item.unknowns,
        "limitations": item.limitations,
    }


def _parse_item(value: dict[str, object]) -> SufficiencyItem:
    proof_value = value["proof"]
    proof = None
    if proof_value:
        proof = NeedSupportProof(
            proof_id=StableId(proof_value["proof_id"]),
            need_id=proof_value["need_id"],
            snapshot_id=StableId(proof_value["snapshot_id"]),
            snapshot_manifest_digest=Digest(proof_value["snapshot_manifest_digest"]),
            read_session_id=StableId(proof_value["read_session_id"]),
            supporting_references=tuple(
                StableId(item) for item in proof_value["supporting_references"]
            ),
            supporting_digests=tuple(Digest(item) for item in proof_value["supporting_digests"]),
            criterion_digest=Digest(proof_value["criterion_digest"]),
            digest=Digest(proof_value["digest"]),
        )
    return SufficiencyItem(
        need_id=value["need_id"],
        status=NeedStatus(value["status"]),
        proof=proof,
        gap=value["gap"],
        counterexamples=tuple(StableId(item) for item in value["counterexamples"]),
        conflicts=tuple(StableId(item) for item in value["conflicts"]),
        unknowns=tuple(value["unknowns"]),
        limitations=tuple(value["limitations"]),
    )


def _session(row: object) -> SnapshotReadSession:
    return SnapshotReadSession(
        session_id=StableId(row["session_id"]),
        task_boundary_digest=Digest(row["task_boundary_digest"]),
        requirement_id=StableId(row["requirement_id"]),
        requirement_revision=Revision(row["requirement_revision"]),
        snapshot_id=StableId(row["snapshot_id"]),
        snapshot_revision=Revision(row["snapshot_revision"]),
        snapshot_manifest_digest=Digest(row["snapshot_manifest_digest"]),
        opened_at=_parse_time(row["opened_at"]),
        digest=Digest(row["session_digest"]),
    )


def _assessment(row: object) -> SufficiencyAssessment:
    return SufficiencyAssessment(
        assessment_id=StableId(row["assessment_id"]),
        requirement_id=StableId(row["requirement_id"]),
        requirement_revision=Revision(row["requirement_revision"]),
        read_session_id=StableId(row["read_session_id"]),
        snapshot_id=StableId(row["snapshot_id"]),
        items=tuple(_parse_item(item) for item in json.loads(row["items_json"])),
        joint_constraint_failures=tuple(json.loads(row["joint_failures_json"])),
        sufficient=bool(row["sufficient"]),
        assessed_at=_parse_time(row["assessed_at"]),
        digest=Digest(row["assessment_digest"]),
    )


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)
