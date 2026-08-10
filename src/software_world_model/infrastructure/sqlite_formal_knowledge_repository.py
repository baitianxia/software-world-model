"""Append-only SQLite formal knowledge and atomic snapshot publication."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

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
from software_world_model.knowledge_engine.formal import (
    AdmissionStatus,
    EvidenceSnapshot,
    KnowledgeAdmissionResult,
    KnowledgeEntity,
    KnowledgeFact,
    FormalKnowledgeRecord,
    KnowledgeInference,
    KnowledgeObjectKind,
    KnowledgeSchema,
    KnowledgeSnapshot,
    SnapshotMember,
    ValidatedKnowledgeBatch,
    VerificationFinding,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS knw_evidence (
    evidence_id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    source_context_id TEXT NOT NULL,
    byte_start INTEGER NOT NULL,
    byte_end INTEGER NOT NULL,
    locator TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    excerpt_digest TEXT NOT NULL,
    artifact_content_digest TEXT NOT NULL,
    evidence_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knw_entities (
    entity_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    natural_key TEXT NOT NULL,
    label TEXT NOT NULL,
    context_json TEXT NOT NULL,
    context_digest TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL,
    object_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knw_facts (
    fact_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    subject_entity_id TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_value TEXT NOT NULL,
    context_json TEXT NOT NULL,
    context_digest TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL,
    reviewed_grounding_json TEXT,
    object_digest TEXT NOT NULL,
    FOREIGN KEY (subject_entity_id) REFERENCES knw_entities(entity_id)
);

CREATE TABLE IF NOT EXISTS knw_inferences (
    inference_id TEXT PRIMARY KEY,
    schema_version TEXT NOT NULL,
    inference_type TEXT NOT NULL,
    proposition TEXT NOT NULL,
    premise_refs_json TEXT NOT NULL,
    rule_ref TEXT NOT NULL,
    context_json TEXT NOT NULL,
    context_digest TEXT NOT NULL,
    reviewed_need_ids_json TEXT NOT NULL DEFAULT '[]',
    object_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knw_snapshot_roots (
    scope_id TEXT PRIMARY KEY,
    current_snapshot_id TEXT NOT NULL UNIQUE,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1)
);

CREATE TABLE IF NOT EXISTS knw_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    scope_id TEXT NOT NULL,
    snapshot_revision INTEGER NOT NULL CHECK (snapshot_revision >= 1),
    previous_snapshot_id TEXT,
    schema_version TEXT NOT NULL,
    manifest_digest TEXT NOT NULL,
    published_at TEXT NOT NULL,
    UNIQUE (scope_id, snapshot_revision),
    FOREIGN KEY (previous_snapshot_id) REFERENCES knw_snapshots(snapshot_id)
);

CREATE TABLE IF NOT EXISTS knw_snapshot_members (
    snapshot_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    object_id TEXT NOT NULL,
    object_digest TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, kind, object_id),
    FOREIGN KEY (snapshot_id) REFERENCES knw_snapshots(snapshot_id)
);

CREATE TABLE IF NOT EXISTS knw_admissions (
    admission_id TEXT PRIMARY KEY,
    scope_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    status TEXT NOT NULL,
    findings_json TEXT NOT NULL,
    snapshot_id TEXT,
    entity_refs_json TEXT NOT NULL,
    fact_refs_json TEXT NOT NULL,
    inference_refs_json TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    result_digest TEXT NOT NULL,
    FOREIGN KEY (snapshot_id) REFERENCES knw_snapshots(snapshot_id)
);
"""


class SqliteFormalKnowledgeRepository:
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)
        with self._database.transaction() as connection:
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(knw_facts)")
            }
            if "reviewed_grounding_json" not in columns:
                connection.execute(
                    "ALTER TABLE knw_facts ADD COLUMN reviewed_grounding_json TEXT"
                )
            inference_columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(knw_inferences)")
            }
            if "reviewed_need_ids_json" not in inference_columns:
                connection.execute(
                    "ALTER TABLE knw_inferences ADD COLUMN "
                    "reviewed_need_ids_json TEXT NOT NULL DEFAULT '[]'"
                )

    def current_snapshot(self, scope_id: StableId) -> KnowledgeSnapshot | None:
        with self._database.read() as connection:
            row = connection.execute(
                "SELECT current_snapshot_id FROM knw_snapshot_roots WHERE scope_id = ?",
                (scope_id.value,),
            ).fetchone()
            return self._load_snapshot(connection, StableId(row["current_snapshot_id"])) if row else None

    def get_snapshot(self, snapshot_id: StableId) -> KnowledgeSnapshot:
        with self._database.read() as connection:
            return self._load_snapshot(connection, snapshot_id)

    def member_exists(self, snapshot_id: StableId, object_id: StableId) -> bool:
        with self._database.read() as connection:
            row = connection.execute(
                "SELECT 1 FROM knw_snapshot_members WHERE snapshot_id = ? AND object_id = ?",
                (snapshot_id.value, object_id.value),
            ).fetchone()
            return row is not None

    def query_snapshot(
        self,
        *,
        snapshot_id: StableId,
        kinds: tuple[KnowledgeObjectKind, ...],
        type_names: tuple[str, ...],
        terms: tuple[str, ...],
        cursor: int,
        limit: int,
    ) -> tuple[tuple[FormalKnowledgeRecord, ...], int | None]:
        with self._database.read() as connection:
            # Loading through the immutable manifest prevents CURRENT changes
            # from altering an open read session's result set.
            snapshot = self._load_snapshot(connection, snapshot_id)
            allowed_kinds = set(kinds)
            allowed_types = set(type_names)
            normalized_terms = tuple(item.casefold() for item in terms)
            records: list[FormalKnowledgeRecord] = []
            for member in snapshot.members:
                if allowed_kinds and member.kind not in allowed_kinds:
                    continue
                record = self._load_record(connection, member)
                if allowed_types and record.type_name not in allowed_types:
                    continue
                searchable = record.text.casefold()
                if normalized_terms and not any(
                    term in searchable for term in normalized_terms
                ):
                    continue
                records.append(record)
            page = tuple(records[cursor : cursor + limit])
            next_cursor = cursor + len(page) if cursor + len(page) < len(records) else None
            return page, next_cursor

    def get_record(self, snapshot_id: StableId, object_id: StableId) -> FormalKnowledgeRecord:
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT kind, object_id, object_digest FROM knw_snapshot_members
                   WHERE snapshot_id = ? AND object_id = ?""",
                (snapshot_id.value, object_id.value),
            ).fetchone()
            if row is None:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "formal knowledge reference is not a member of the exact snapshot",
                )
            return self._load_record(
                connection,
                SnapshotMember(
                    kind=KnowledgeObjectKind(row["kind"]),
                    object_id=StableId(row["object_id"]),
                    object_digest=Digest(row["object_digest"]),
                ),
            )

    def get_evidence(self, evidence_id: StableId) -> EvidenceSnapshot:
        with self._database.read() as connection:
            row = connection.execute(
                "SELECT * FROM knw_evidence WHERE evidence_id = ?",
                (evidence_id.value,),
            ).fetchone()
            if row is None:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "formal evidence reference does not exist",
                )
            return EvidenceSnapshot(
                evidence_id=StableId(row["evidence_id"]),
                artifact_id=StableId(row["artifact_id"]),
                source_context_id=StableId(row["source_context_id"]),
                byte_start=row["byte_start"],
                byte_end=row["byte_end"],
                locator=row["locator"],
                excerpt=row["excerpt"],
                excerpt_digest=Digest(row["excerpt_digest"]),
                artifact_content_digest=Digest(row["artifact_content_digest"]),
                digest=Digest(row["evidence_digest"]),
            )

    @staticmethod
    def _load_record(
        connection: sqlite3.Connection, member: SnapshotMember
    ) -> FormalKnowledgeRecord:
        if member.kind is KnowledgeObjectKind.ENTITY:
            row = connection.execute(
                "SELECT * FROM knw_entities WHERE entity_id = ?", (member.object_id.value,)
            ).fetchone()
            return FormalKnowledgeRecord(
                kind=member.kind,
                object_id=member.object_id,
                object_digest=member.object_digest,
                type_name=row["entity_type"],
                text=f"{row['natural_key']} {row['label']}",
                context_digest=Digest(row["context_digest"]),
                support_references=_parse_refs(row["evidence_refs_json"]),
            )
        if member.kind is KnowledgeObjectKind.FACT:
            row = connection.execute(
                "SELECT * FROM knw_facts WHERE fact_id = ?", (member.object_id.value,)
            ).fetchone()
            return FormalKnowledgeRecord(
                kind=member.kind,
                object_id=member.object_id,
                object_digest=member.object_digest,
                type_name=row["predicate"],
                text=row["object_value"],
                context_digest=Digest(row["context_digest"]),
                support_references=_parse_refs(row["evidence_refs_json"]),
                reviewed_need_ids=_reviewed_need_ids(
                    row["reviewed_grounding_json"]
                ),
            )
        row = connection.execute(
            "SELECT * FROM knw_inferences WHERE inference_id = ?", (member.object_id.value,)
        ).fetchone()
        return FormalKnowledgeRecord(
            kind=member.kind,
            object_id=member.object_id,
            object_digest=member.object_digest,
            type_name=row["inference_type"],
            text=row["proposition"],
            context_digest=Digest(row["context_digest"]),
            support_references=_parse_refs(row["premise_refs_json"]),
            reviewed_need_ids=tuple(
                item for item in json.loads(row["reviewed_need_ids_json"])
            ),
        )

    def record_rejection(
        self,
        *,
        scope_id: StableId,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        findings: tuple[VerificationFinding, ...],
        decided_at: datetime,
    ) -> KnowledgeAdmissionResult:
        with self._database.transaction() as connection:
            replay = self._idempotent(connection, idempotency_key, request_digest)
            if replay is not None:
                return replay
            return self._insert_admission(
                connection,
                scope_id=scope_id,
                idempotency_key=idempotency_key,
                request_digest=request_digest,
                status=AdmissionStatus.REJECTED,
                findings=findings,
                snapshot=None,
                entity_refs=(),
                fact_refs=(),
                inference_refs=(),
                decided_at=decided_at,
            )

    def admit_and_publish(
        self,
        *,
        scope_id: StableId,
        expected_current_snapshot_id: StableId | None,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        schema: KnowledgeSchema,
        batch: ValidatedKnowledgeBatch,
        decided_at: datetime,
    ) -> KnowledgeAdmissionResult:
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent(connection, idempotency_key, request_digest)
                if replay is not None:
                    return replay
                root = connection.execute(
                    "SELECT * FROM knw_snapshot_roots WHERE scope_id = ?", (scope_id.value,)
                ).fetchone()
                actual_id = StableId(root["current_snapshot_id"]) if root else None
                if actual_id != expected_current_snapshot_id:
                    raise DomainError(
                        ErrorCode.REVISION_CONFLICT,
                        "CURRENT snapshot changed before publication",
                    )
                for evidence in batch.evidence:
                    self._insert_immutable(connection, "knw_evidence", "evidence_id", evidence.evidence_id, evidence.digest, (
                        evidence.evidence_id.value,
                        evidence.artifact_id.value,
                        evidence.source_context_id.value,
                        evidence.byte_start,
                        evidence.byte_end,
                        evidence.locator,
                        evidence.excerpt,
                        evidence.excerpt_digest.value,
                        evidence.artifact_content_digest.value,
                        evidence.digest.value,
                    ))
                for entity in batch.entities:
                    self._insert_immutable(connection, "knw_entities", "entity_id", entity.entity_id, entity.digest, (
                        entity.entity_id.value,
                        entity.schema_version,
                        entity.entity_type,
                        entity.natural_key,
                        entity.label,
                        _json(dict(entity.context.terms)),
                        entity.context.digest.value,
                        _refs(entity.evidence_references),
                        entity.digest.value,
                    ))
                for fact in batch.facts:
                    self._insert_immutable(
                        connection,
                        "knw_facts",
                        "fact_id",
                        fact.fact_id,
                        fact.digest,
                        (
                            fact.fact_id.value,
                            fact.schema_version,
                            fact.subject_entity_id.value,
                            fact.predicate,
                            fact.object_value,
                            _json(dict(fact.context.terms)),
                            fact.context.digest.value,
                            _refs(fact.evidence_references),
                            _reviewed_grounding_json(fact),
                            fact.digest.value,
                        ),
                        columns=(
                            "fact_id",
                            "schema_version",
                            "subject_entity_id",
                            "predicate",
                            "object_value",
                            "context_json",
                            "context_digest",
                            "evidence_refs_json",
                            "reviewed_grounding_json",
                            "object_digest",
                        ),
                    )
                for inference in batch.inferences:
                    self._insert_immutable(
                        connection,
                        "knw_inferences",
                        "inference_id",
                        inference.inference_id,
                        inference.digest,
                        (
                            inference.inference_id.value,
                            inference.schema_version,
                            inference.inference_type,
                            inference.proposition,
                            _refs(inference.premise_references),
                            inference.rule_ref,
                            _json(dict(inference.context.terms)),
                            inference.context.digest.value,
                            _json(inference.reviewed_need_ids),
                            inference.digest.value,
                        ),
                        columns=(
                            "inference_id",
                            "schema_version",
                            "inference_type",
                            "proposition",
                            "premise_refs_json",
                            "rule_ref",
                            "context_json",
                            "context_digest",
                            "reviewed_need_ids_json",
                            "object_digest",
                        ),
                    )
                previous_members: tuple[SnapshotMember, ...] = ()
                if actual_id is not None:
                    previous_members = self._load_snapshot(connection, actual_id).members
                members_by_key = {
                    (member.kind, member.object_id): member for member in previous_members
                }
                for kind, objects in (
                    (KnowledgeObjectKind.ENTITY, batch.entities),
                    (KnowledgeObjectKind.FACT, batch.facts),
                    (KnowledgeObjectKind.INFERENCE, batch.inferences),
                ):
                    for item in objects:
                        object_id = getattr(item, f"{kind.value.casefold()}_id")
                        candidate = SnapshotMember(kind, object_id, item.digest)
                        existing = members_by_key.get((kind, object_id))
                        if existing is not None and existing.object_digest != item.digest:
                            raise DomainError(
                                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                                "formal object identity cannot change its digest",
                            )
                        members_by_key[(kind, object_id)] = candidate
                members = tuple(
                    sorted(members_by_key.values(), key=lambda item: (item.kind.value, item.object_id.value))
                )
                snapshot_id = self._ids.new("knowledge_snapshot")
                snapshot_revision = Revision(root["current_revision"] + 1 if root else 1)
                manifest_digest = digest_of(
                    {
                        "snapshot_id": snapshot_id.value,
                        "scope_id": scope_id.value,
                        "snapshot_revision": snapshot_revision.value,
                        "previous_snapshot_id": actual_id.value if actual_id else None,
                        "schema_version": schema.version,
                        "schema_digest": schema.digest.value,
                        "members": members,
                    }
                )
                connection.execute(
                    "INSERT INTO knw_snapshots VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        snapshot_id.value,
                        scope_id.value,
                        snapshot_revision.value,
                        actual_id.value if actual_id else None,
                        schema.version,
                        manifest_digest.value,
                        _time(decided_at),
                    ),
                )
                connection.executemany(
                    "INSERT INTO knw_snapshot_members VALUES (?, ?, ?, ?)",
                    (
                        (snapshot_id.value, member.kind.value, member.object_id.value, member.object_digest.value)
                        for member in members
                    ),
                )
                if root is None:
                    connection.execute(
                        "INSERT INTO knw_snapshot_roots VALUES (?, ?, ?)",
                        (scope_id.value, snapshot_id.value, snapshot_revision.value),
                    )
                else:
                    cursor = connection.execute(
                        """UPDATE knw_snapshot_roots
                           SET current_snapshot_id = ?, current_revision = ?
                           WHERE scope_id = ? AND current_snapshot_id = ?""",
                        (
                            snapshot_id.value,
                            snapshot_revision.value,
                            scope_id.value,
                            actual_id.value,
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise DomainError(ErrorCode.REVISION_CONFLICT, "CURRENT changed")
                snapshot = KnowledgeSnapshot(
                    snapshot_id=snapshot_id,
                    scope_id=scope_id,
                    snapshot_revision=snapshot_revision,
                    previous_snapshot_id=actual_id,
                    schema_version=schema.version,
                    members=members,
                    manifest_digest=manifest_digest,
                    published_at=decided_at,
                )
                return self._insert_admission(
                    connection,
                    scope_id=scope_id,
                    idempotency_key=idempotency_key,
                    request_digest=request_digest,
                    status=AdmissionStatus.ADMITTED,
                    findings=(),
                    snapshot=snapshot,
                    entity_refs=tuple(item.entity_id for item in batch.entities),
                    fact_refs=tuple(item.fact_id for item in batch.facts),
                    inference_refs=tuple(item.inference_id for item in batch.inferences),
                    decided_at=decided_at,
                )
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "knowledge publication violated a store invariant",
                {"sqlite_error": str(exc)},
            ) from exc

    def _insert_immutable(
        self,
        connection: sqlite3.Connection,
        table: str,
        id_column: str,
        object_id: StableId,
        digest: Digest,
        values: tuple[object, ...],
        columns: tuple[str, ...] | None = None,
    ) -> None:
        # Table and column are internal constants chosen by the caller above.
        row = connection.execute(
            f"SELECT * FROM {table} WHERE {id_column} = ?", (object_id.value,)
        ).fetchone()
        if row is not None:
            if row["object_digest" if table != "knw_evidence" else "evidence_digest"] != digest.value:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "immutable knowledge identity has a conflicting digest",
                )
            return
        placeholders = ",".join("?" for _ in values)
        column_clause = f" ({','.join(columns)})" if columns is not None else ""
        connection.execute(
            f"INSERT INTO {table}{column_clause} VALUES ({placeholders})", values
        )

    def _insert_admission(
        self,
        connection: sqlite3.Connection,
        *,
        scope_id: StableId,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        status: AdmissionStatus,
        findings: tuple[VerificationFinding, ...],
        snapshot: KnowledgeSnapshot | None,
        entity_refs: tuple[StableId, ...],
        fact_refs: tuple[StableId, ...],
        inference_refs: tuple[StableId, ...],
        decided_at: datetime,
    ) -> KnowledgeAdmissionResult:
        admission_id = self._ids.new("knowledge_admission")
        core = {
            "admission_id": admission_id.value,
            "scope_id": scope_id.value,
            "request_digest": request_digest.value,
            "status": status.value,
            "findings": findings,
            "snapshot_id": snapshot.snapshot_id.value if snapshot else None,
            "entity_refs": tuple(item.value for item in entity_refs),
            "fact_refs": tuple(item.value for item in fact_refs),
            "inference_refs": tuple(item.value for item in inference_refs),
            "decided_at": decided_at,
        }
        result_digest = digest_of(core)
        connection.execute(
            "INSERT INTO knw_admissions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                admission_id.value,
                scope_id.value,
                idempotency_key.value,
                request_digest.value,
                status.value,
                _json([finding.__dict__ if hasattr(finding, "__dict__") else {
                    "code": finding.code,
                    "candidate_key": finding.candidate_key,
                    "message": finding.message,
                } for finding in findings]),
                snapshot.snapshot_id.value if snapshot else None,
                _refs(entity_refs),
                _refs(fact_refs),
                _refs(inference_refs),
                _time(decided_at),
                result_digest.value,
            ),
        )
        return KnowledgeAdmissionResult(
            admission_id=admission_id,
            status=status,
            request_digest=request_digest,
            findings=findings,
            snapshot=snapshot,
            entity_references=entity_refs,
            fact_references=fact_refs,
            inference_references=inference_refs,
            decided_at=decided_at,
            digest=result_digest,
        )

    def _idempotent(
        self,
        connection: sqlite3.Connection,
        key: IdempotencyKey,
        request_digest: Digest,
    ) -> KnowledgeAdmissionResult | None:
        row = connection.execute(
            "SELECT admission_id, request_digest FROM knw_admissions WHERE idempotency_key = ?",
            (key.value,),
        ).fetchone()
        if row is None:
            return None
        if row["request_digest"] != request_digest.value:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "knowledge admission idempotency key has a different request",
            )
        return self._load_admission(connection, StableId(row["admission_id"]))

    def _load_admission(
        self, connection: sqlite3.Connection, admission_id: StableId
    ) -> KnowledgeAdmissionResult:
        row = connection.execute(
            "SELECT * FROM knw_admissions WHERE admission_id = ?", (admission_id.value,)
        ).fetchone()
        findings = tuple(VerificationFinding(**item) for item in json.loads(row["findings_json"]))
        snapshot = (
            self._load_snapshot(connection, StableId(row["snapshot_id"]))
            if row["snapshot_id"]
            else None
        )
        return KnowledgeAdmissionResult(
            admission_id=admission_id,
            status=AdmissionStatus(row["status"]),
            request_digest=Digest(row["request_digest"]),
            findings=findings,
            snapshot=snapshot,
            entity_references=_parse_refs(row["entity_refs_json"]),
            fact_references=_parse_refs(row["fact_refs_json"]),
            inference_references=_parse_refs(row["inference_refs_json"]),
            decided_at=_parse_time(row["decided_at"]),
            digest=Digest(row["result_digest"]),
        )

    def _load_snapshot(
        self, connection: sqlite3.Connection, snapshot_id: StableId
    ) -> KnowledgeSnapshot:
        row = connection.execute(
            "SELECT * FROM knw_snapshots WHERE snapshot_id = ?", (snapshot_id.value,)
        ).fetchone()
        if row is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "knowledge snapshot was not found")
        members = tuple(
            SnapshotMember(
                kind=KnowledgeObjectKind(item["kind"]),
                object_id=StableId(item["object_id"]),
                object_digest=Digest(item["object_digest"]),
            )
            for item in connection.execute(
                """SELECT kind, object_id, object_digest FROM knw_snapshot_members
                   WHERE snapshot_id = ? ORDER BY kind, object_id""",
                (snapshot_id.value,),
            ).fetchall()
        )
        return KnowledgeSnapshot(
            snapshot_id=snapshot_id,
            scope_id=StableId(row["scope_id"]),
            snapshot_revision=Revision(row["snapshot_revision"]),
            previous_snapshot_id=(
                StableId(row["previous_snapshot_id"]) if row["previous_snapshot_id"] else None
            ),
            schema_version=row["schema_version"],
            members=members,
            manifest_digest=Digest(row["manifest_digest"]),
            published_at=_parse_time(row["published_at"]),
        )


def _refs(values: tuple[StableId, ...]) -> str:
    return _json([item.value for item in values])


def _reviewed_grounding_json(fact: KnowledgeFact) -> str | None:
    grounding = fact.reviewed_grounding
    if grounding is None:
        return None
    return _json(
        {
            "schema_version": grounding.schema_version,
            "candidate_key": grounding.candidate_key,
            "proposer_model_call_id": grounding.proposer_model_call_id.value,
            "proposer_output_digest": grounding.proposer_output_digest.value,
            "reviewer_model_call_id": grounding.reviewer_model_call_id.value,
            "reviewer_output_digest": grounding.reviewer_output_digest.value,
            "actual_model_fingerprint": grounding.actual_model_fingerprint,
            "need_ids": grounding.need_ids,
            "digest": grounding.digest.value,
        }
    )


def _reviewed_need_ids(value: str | None) -> tuple[str, ...]:
    if not value:
        return ()
    try:
        document = json.loads(value)
    except json.JSONDecodeError:
        return ()
    items = document.get("need_ids") if isinstance(document, dict) else None
    if (
        not isinstance(items, list)
        or not items
        or not all(isinstance(item, str) and item.strip() for item in items)
        or len(items) != len(set(items))
    ):
        return ()
    return tuple(items)


def _parse_refs(value: str) -> tuple[StableId, ...]:
    return tuple(StableId(item) for item in json.loads(value))


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)
