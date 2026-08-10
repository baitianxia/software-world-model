"""Read-only compatibility reader for the ITER-002 formal knowledge schema.

The normal formal repository owns schema creation and migration.  This adapter
deliberately does neither: it opens an existing database through SQLite's
read-only immutable URI and projects only records named by an exact legacy
Snapshot manifest.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import json
from pathlib import Path
import sqlite3
from typing import Iterator

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    Revision,
    StableId,
    digest_of,
)


class LegacyKnowledgeObjectKind(str, Enum):
    """Object kinds admitted by the pre-Structure formal knowledge schema."""

    ENTITY = "ENTITY"
    FACT = "FACT"
    INFERENCE = "INFERENCE"


@dataclass(frozen=True, slots=True)
class LegacySnapshotMember:
    kind: LegacyKnowledgeObjectKind
    object_id: StableId
    object_digest: Digest


@dataclass(frozen=True, slots=True)
class LegacySnapshotMetadata:
    snapshot_id: StableId
    scope_id: StableId
    snapshot_revision: Revision
    previous_snapshot_id: StableId | None
    schema_version: str
    members: tuple[LegacySnapshotMember, ...]
    manifest_digest: Digest
    published_at: datetime

    @property
    def member_count(self) -> int:
        return len(self.members)


@dataclass(frozen=True, slots=True)
class LegacyFormalRecord:
    kind: LegacyKnowledgeObjectKind
    object_id: StableId
    object_digest: Digest
    schema_version: str
    type_name: str
    text: str
    context_digest: Digest
    support_references: tuple[StableId, ...]
    source_locators: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LegacyFormalSnapshot:
    metadata: LegacySnapshotMetadata
    records: tuple[LegacyFormalRecord, ...]


@dataclass(frozen=True, slots=True)
class _LegacyContext:
    """Exact dataclass shape used by the frozen INITIAL@1 digest codec."""

    terms: tuple[tuple[str, str], ...]
    digest: Digest


_REQUIRED_COLUMNS = {
    "knw_snapshot_roots": (
        "scope_id",
        "current_snapshot_id",
        "current_revision",
    ),
    "knw_snapshots": (
        "snapshot_id",
        "scope_id",
        "snapshot_revision",
        "previous_snapshot_id",
        "schema_version",
        "manifest_digest",
        "published_at",
    ),
    "knw_snapshot_members": (
        "snapshot_id",
        "kind",
        "object_id",
        "object_digest",
    ),
    "knw_entities": (
        "entity_id",
        "schema_version",
        "entity_type",
        "natural_key",
        "label",
        "context_json",
        "context_digest",
        "evidence_refs_json",
        "object_digest",
    ),
    "knw_facts": (
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
    "knw_inferences": (
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
    "knw_evidence": (
        "evidence_id",
        "artifact_id",
        "source_context_id",
        "byte_start",
        "byte_end",
        "locator",
        "excerpt",
        "excerpt_digest",
        "artifact_content_digest",
        "evidence_digest",
    ),
}

# Exact digest emitted by the ITER-002 ``KnowledgeSchema.initial()`` contract.
# Keeping it here prevents later schema code from silently reinterpreting an
# old manifest while still allowing every stored manifest field to be checked.
_INITIAL_SCHEMA_DIGEST = Digest(
    "sha256:75e96739d6b05aca368d5be4fcfb84eddf8fbbb996e65e9ba9f6738562a4e436"
)

_INITIAL_ENTITY_TYPES = frozenset(
    {
        "SOFTWARE_SYSTEM",
        "MODULE",
        "SOURCE_FILE",
        "CODE_SYMBOL",
        "ENDPOINT",
        "CONFIGURATION",
    }
)
_INITIAL_FACT_PREDICATES = frozenset(
    {
        "DECLARES",
        "CALLS",
        "DEPENDS_ON",
        "EXPOSES",
        "HAS_VALUE",
        "CHANGED_IN",
        "DESCRIBED_AS",
    }
)
_INITIAL_INFERENCE_TYPES = frozenset(
    {
        "STRUCTURE",
        "BEHAVIOR",
        "HISTORY_IMPACT",
        "BUSINESS_CAPABILITY",
        "BUSINESS_CONSTRAINT",
    }
)


class SqliteLegacyFormalReader:
    """Fail-closed read port for an exact legacy formal Snapshot.

    A connection is opened and closed for each public read.  No connection is
    exposed to callers and this class contains no mutation or migration path.
    """

    def __init__(self, database_path: str | Path) -> None:
        try:
            resolved = Path(database_path).expanduser().resolve(strict=True)
        except OSError as exc:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "legacy formal database was not found",
            ) from exc
        if not resolved.is_file():
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "legacy formal database path is not a file",
            )
        self._database_uri = f"{resolved.as_uri()}?mode=ro&immutable=1"

    def current_snapshot(self, scope_id: StableId) -> LegacySnapshotMetadata:
        with self._read_connection() as connection:
            row = connection.execute(
                """SELECT current_snapshot_id, current_revision
                   FROM knw_snapshot_roots WHERE scope_id = ?""",
                (scope_id.value,),
            ).fetchone()
            if row is None:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "legacy formal scope has no CURRENT snapshot",
                )
            snapshot = self._load_formal_snapshot(
                connection, StableId(row["current_snapshot_id"])
            ).metadata
            if (
                snapshot.scope_id != scope_id
                or snapshot.snapshot_revision.value != row["current_revision"]
            ):
                raise _inconsistent("legacy CURRENT root does not match its snapshot")
            return snapshot

    def get_snapshot(self, snapshot_id: StableId) -> LegacySnapshotMetadata:
        with self._read_connection() as connection:
            return self._load_formal_snapshot(connection, snapshot_id).metadata

    def read_snapshot(self, snapshot_id: StableId) -> LegacyFormalSnapshot:
        with self._read_connection() as connection:
            return self._load_formal_snapshot(connection, snapshot_id)

    def query_snapshot(
        self,
        snapshot_id: StableId,
        *,
        kinds: tuple[LegacyKnowledgeObjectKind, ...] = (),
    ) -> tuple[LegacyFormalRecord, ...]:
        """Return selected records in exact manifest order.

        An empty ``kinds`` tuple means all three legacy object kinds.  Records
        present in an object table but absent from the manifest are never read.
        """

        if any(not isinstance(kind, LegacyKnowledgeObjectKind) for kind in kinds):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "legacy formal query kind is invalid",
            )
        selected = frozenset(kinds)
        with self._read_connection() as connection:
            snapshot = self._load_formal_snapshot(connection, snapshot_id)
            return tuple(
                record
                for record in snapshot.records
                if not selected or record.kind in selected
            )

    def get_record(
        self, snapshot_id: StableId, object_id: StableId
    ) -> LegacyFormalRecord:
        with self._read_connection() as connection:
            snapshot = self._load_formal_snapshot(connection, snapshot_id)
            records = tuple(
                record for record in snapshot.records if record.object_id == object_id
            )
            if len(records) != 1:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "legacy formal record is not a member of the exact snapshot",
                )
            return records[0]

    @contextmanager
    def _read_connection(self) -> Iterator[sqlite3.Connection]:
        connection: sqlite3.Connection | None = None
        try:
            connection = sqlite3.connect(self._database_uri, uri=True)
            connection.row_factory = sqlite3.Row
            self._verify_read_schema(connection)
            yield connection
        except DomainError:
            raise
        except (json.JSONDecodeError, sqlite3.Error, TypeError, ValueError) as exc:
            raise _inconsistent("legacy formal database could not be read exactly") from exc
        finally:
            if connection is not None:
                connection.close()

    @staticmethod
    def _verify_read_schema(connection: sqlite3.Connection) -> None:
        # Explicit zero-row SELECTs verify both table and column availability
        # without PRAGMA, DDL, migration, or any other write-capable statement.
        for table, columns in _REQUIRED_COLUMNS.items():
            column_sql = ", ".join(columns)
            connection.execute(f"SELECT {column_sql} FROM {table} LIMIT 0")

    @staticmethod
    def _load_snapshot(
        connection: sqlite3.Connection, snapshot_id: StableId
    ) -> LegacySnapshotMetadata:
        row = connection.execute(
            """SELECT snapshot_id, scope_id, snapshot_revision,
                      previous_snapshot_id, schema_version, manifest_digest,
                      published_at
               FROM knw_snapshots WHERE snapshot_id = ?""",
            (snapshot_id.value,),
        ).fetchone()
        if row is None:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "legacy formal snapshot was not found",
            )
        raw_members = connection.execute(
            """SELECT kind, object_id, object_digest
               FROM knw_snapshot_members
               WHERE snapshot_id = ? ORDER BY kind, object_id""",
            (snapshot_id.value,),
        ).fetchall()
        members = tuple(
            LegacySnapshotMember(
                kind=LegacyKnowledgeObjectKind(item["kind"]),
                object_id=StableId(item["object_id"]),
                object_digest=Digest(item["object_digest"]),
            )
            for item in raw_members
        )
        if len({member.object_id for member in members}) != len(members):
            raise _inconsistent("legacy snapshot manifest has ambiguous object IDs")
        revision = Revision(row["snapshot_revision"])
        published_at = datetime.fromisoformat(row["published_at"])
        if published_at.tzinfo is None or published_at.utcoffset() is None:
            raise _inconsistent("legacy snapshot publication time has no timezone")
        metadata = LegacySnapshotMetadata(
            snapshot_id=StableId(row["snapshot_id"]),
            scope_id=StableId(row["scope_id"]),
            snapshot_revision=revision,
            previous_snapshot_id=(
                StableId(row["previous_snapshot_id"])
                if row["previous_snapshot_id"] is not None
                else None
            ),
            schema_version=_required_text(row["schema_version"], "schema version"),
            members=members,
            manifest_digest=Digest(row["manifest_digest"]),
            published_at=published_at,
        )
        if metadata.schema_version != "INITIAL@1":
            raise _inconsistent("legacy snapshot schema is not INITIAL@1")
        expected_manifest_digest = digest_of(
            {
                "snapshot_id": metadata.snapshot_id.value,
                "scope_id": metadata.scope_id.value,
                "snapshot_revision": metadata.snapshot_revision.value,
                "previous_snapshot_id": (
                    metadata.previous_snapshot_id.value
                    if metadata.previous_snapshot_id is not None
                    else None
                ),
                "schema_version": metadata.schema_version,
                "schema_digest": _INITIAL_SCHEMA_DIGEST.value,
                "members": metadata.members,
            }
        )
        if expected_manifest_digest != metadata.manifest_digest:
            raise _inconsistent("legacy snapshot manifest digest does not verify")
        return metadata

    def _load_record_with_locators(
        self,
        connection: sqlite3.Connection,
        snapshot: LegacySnapshotMetadata,
        member: LegacySnapshotMember,
    ) -> LegacyFormalRecord:
        core = self._load_record(connection, snapshot, member)
        locators = self._resolve_source_locators(
            connection, snapshot, core.support_references
        )
        return LegacyFormalRecord(
            kind=member.kind,
            object_id=member.object_id,
            object_digest=member.object_digest,
            schema_version=core.schema_version,
            type_name=core.type_name,
            text=core.text,
            context_digest=core.context_digest,
            support_references=core.support_references,
            source_locators=locators,
        )

    def _load_formal_snapshot(
        self, connection: sqlite3.Connection, snapshot_id: StableId
    ) -> LegacyFormalSnapshot:
        metadata = self._load_snapshot(connection, snapshot_id)
        self._validate_snapshot_chain(connection, metadata)
        records = tuple(
            self._load_record_with_locators(connection, metadata, member)
            for member in metadata.members
        )
        return LegacyFormalSnapshot(metadata=metadata, records=records)

    def _validate_snapshot_chain(
        self,
        connection: sqlite3.Connection,
        snapshot: LegacySnapshotMetadata,
    ) -> None:
        current = snapshot
        seen: set[StableId] = set()
        while True:
            if current.snapshot_id in seen:
                raise _inconsistent("legacy Snapshot predecessor chain contains a cycle")
            seen.add(current.snapshot_id)
            revision = current.snapshot_revision.value
            predecessor_id = current.previous_snapshot_id
            if revision == 1:
                if predecessor_id is not None:
                    raise _inconsistent(
                        "legacy Snapshot revision 1 must not have a predecessor"
                    )
                return
            if predecessor_id is None:
                raise _inconsistent(
                    "legacy Snapshot revision greater than 1 has no predecessor"
                )
            try:
                predecessor = self._load_snapshot(connection, predecessor_id)
            except DomainError as exc:
                raise _inconsistent(
                    "legacy Snapshot predecessor cannot be resolved exactly"
                ) from exc
            if (
                predecessor.scope_id != current.scope_id
                or predecessor.snapshot_revision.value != revision - 1
            ):
                raise _inconsistent(
                    "legacy Snapshot predecessor Scope or revision is inconsistent"
                )
            current_members = {
                (item.kind, item.object_id): item.object_digest
                for item in current.members
            }
            if any(
                current_members.get((item.kind, item.object_id))
                != item.object_digest
                for item in predecessor.members
            ):
                raise _inconsistent(
                    "legacy additive Snapshot does not preserve predecessor members"
                )
            current = predecessor

    @staticmethod
    def _load_record(
        connection: sqlite3.Connection,
        snapshot: LegacySnapshotMetadata,
        member: LegacySnapshotMember,
    ) -> LegacyFormalRecord:
        if member.kind is LegacyKnowledgeObjectKind.ENTITY:
            row = connection.execute(
                """SELECT entity_id, schema_version, entity_type, natural_key,
                          label, context_json, context_digest,
                          evidence_refs_json, object_digest
                   FROM knw_entities WHERE entity_id = ?""",
                (member.object_id.value,),
            ).fetchone()
            if row is None:
                raise _inconsistent("legacy snapshot Entity record is missing")
            schema_version = _record_schema(row, snapshot)
            entity_type = _required_text(row["entity_type"], "Entity type")
            if entity_type not in _INITIAL_ENTITY_TYPES:
                raise _inconsistent("legacy Entity type is outside INITIAL@1")
            natural_key = _required_text(row["natural_key"], "Entity natural key")
            label = _required_text(row["label"], "Entity label")
            context = _legacy_context(row["context_json"], row["context_digest"])
            references = _stable_id_array(row["evidence_refs_json"])
            if not references:
                raise _inconsistent("legacy Entity has no Evidence support")
            if any(reference.kind != "evidence" for reference in references):
                raise _inconsistent("legacy Entity support is not Evidence")
            identity = digest_of(
                {
                    "schema_version": schema_version,
                    "entity_type": entity_type,
                    "natural_key": natural_key,
                    "label": label,
                    "context_digest": context.digest.value,
                    "evidence_references": tuple(item.value for item in references),
                }
            )
            expected_id = _stable("knowledge_entity", identity)
            record_digest = digest_of(
                {
                    "entity_id": expected_id.value,
                    "schema_version": schema_version,
                    "entity_type": entity_type,
                    "natural_key": natural_key,
                    "label": label,
                    "context": context,
                    "evidence_references": tuple(item.value for item in references),
                }
            )
            type_name = entity_type
            text = f"{natural_key} {label}"
        elif member.kind is LegacyKnowledgeObjectKind.FACT:
            row = connection.execute(
                """SELECT fact_id, schema_version, subject_entity_id,
                          predicate, object_value, context_json, context_digest,
                          evidence_refs_json, reviewed_grounding_json,
                          object_digest
                   FROM knw_facts WHERE fact_id = ?""",
                (member.object_id.value,),
            ).fetchone()
            if row is None:
                raise _inconsistent("legacy snapshot Fact record is missing")
            schema_version = _record_schema(row, snapshot)
            subject_id = StableId(row["subject_entity_id"])
            subject_members = {
                item.object_id
                for item in snapshot.members
                if item.kind is LegacyKnowledgeObjectKind.ENTITY
            }
            if subject_id not in subject_members:
                raise _inconsistent("legacy Fact subject is outside its exact Snapshot")
            predicate = _required_text(row["predicate"], "Fact predicate")
            if predicate not in _INITIAL_FACT_PREDICATES:
                raise _inconsistent("legacy Fact predicate is outside INITIAL@1")
            object_value = _required_text(row["object_value"], "Fact object value")
            context = _legacy_context(row["context_json"], row["context_digest"])
            references = _stable_id_array(row["evidence_refs_json"])
            if not references:
                raise _inconsistent("legacy Fact has no Evidence support")
            if any(reference.kind != "evidence" for reference in references):
                raise _inconsistent("legacy Fact support is not Evidence")
            grounding_digest = _reviewed_grounding_digest(
                row["reviewed_grounding_json"]
            )
            identity = digest_of(
                {
                    "schema_version": schema_version,
                    "subject_entity_id": subject_id.value,
                    "predicate": predicate,
                    "object_value": object_value,
                    "context_digest": context.digest.value,
                    "evidence_references": tuple(item.value for item in references),
                    "reviewed_grounding_digest": (
                        grounding_digest.value if grounding_digest is not None else None
                    ),
                }
            )
            expected_id = _stable("knowledge_fact", identity)
            record_digest = digest_of(
                {
                    "fact_id": expected_id.value,
                    "schema_version": schema_version,
                    "subject_entity_id": subject_id.value,
                    "predicate": predicate,
                    "object_value": object_value,
                    "context": context,
                    "evidence_references": tuple(item.value for item in references),
                    "reviewed_grounding_digest": (
                        grounding_digest.value if grounding_digest is not None else None
                    ),
                }
            )
            type_name = predicate
            text = object_value
        else:
            row = connection.execute(
                """SELECT inference_id, schema_version, inference_type,
                          proposition, premise_refs_json, rule_ref, context_json,
                          context_digest, reviewed_need_ids_json, object_digest
                   FROM knw_inferences WHERE inference_id = ?""",
                (member.object_id.value,),
            ).fetchone()
            if row is None:
                raise _inconsistent("legacy snapshot Inference record is missing")
            schema_version = _record_schema(row, snapshot)
            inference_type = _required_text(
                row["inference_type"], "Inference type"
            )
            if inference_type not in _INITIAL_INFERENCE_TYPES:
                raise _inconsistent("legacy Inference type is outside INITIAL@1")
            proposition = _required_text(
                row["proposition"], "Inference proposition"
            )
            references = _stable_id_array(row["premise_refs_json"])
            if not references:
                raise _inconsistent("legacy Inference has no formal premises")
            snapshot_ids = {item.object_id for item in snapshot.members}
            if not set(references) <= snapshot_ids:
                raise _inconsistent("legacy Inference premise is outside its exact Snapshot")
            rule_ref = _required_text(row["rule_ref"], "Inference rule")
            context = _legacy_context(row["context_json"], row["context_digest"])
            reviewed_need_ids = _text_array(
                row["reviewed_need_ids_json"],
                "reviewed Inference Need IDs",
                allow_empty=True,
            )
            identity = digest_of(
                {
                    "schema_version": schema_version,
                    "inference_type": inference_type,
                    "proposition": proposition,
                    "premises": tuple(item.value for item in references),
                    "rule_ref": rule_ref,
                    "context_digest": context.digest.value,
                    "reviewed_need_ids": reviewed_need_ids,
                }
            )
            expected_id = _stable("knowledge_inference", identity)
            record_digest = digest_of(
                {
                    "inference_id": expected_id.value,
                    "schema_version": schema_version,
                    "inference_type": inference_type,
                    "proposition": proposition,
                    "premises": tuple(item.value for item in references),
                    "rule_ref": rule_ref,
                    "context": context,
                    "reviewed_need_ids": reviewed_need_ids,
                }
            )
            type_name = inference_type
            text = proposition

        if StableId(row[0]) != expected_id or member.object_id != expected_id:
            raise _inconsistent("legacy record identity does not verify")
        row_digest = Digest(row["object_digest"])
        if row_digest != record_digest or row_digest != member.object_digest:
            raise _inconsistent("legacy record or manifest digest does not verify")
        return LegacyFormalRecord(
            kind=member.kind,
            object_id=member.object_id,
            object_digest=row_digest,
            schema_version=schema_version,
            type_name=_required_text(type_name, "record type"),
            text=_required_text(text, "record text"),
            context_digest=context.digest,
            support_references=references,
            source_locators=(),
        )

    def _resolve_source_locators(
        self,
        connection: sqlite3.Connection,
        snapshot: LegacySnapshotMetadata,
        references: tuple[StableId, ...],
    ) -> tuple[str, ...]:
        members = {member.object_id: member for member in snapshot.members}
        locators: list[str] = []
        resolved: set[StableId] = set()
        visiting: set[StableId] = set()

        def visit(reference: StableId) -> None:
            if reference in resolved:
                return
            if reference in visiting:
                raise _inconsistent("legacy support graph contains a cycle")
            visiting.add(reference)
            member = members.get(reference)
            if member is not None:
                record = self._load_record(connection, snapshot, member)
                for support in record.support_references:
                    visit(support)
            else:
                row = connection.execute(
                    """SELECT evidence_id, artifact_id, source_context_id,
                              byte_start, byte_end, locator, excerpt,
                              excerpt_digest, artifact_content_digest,
                              evidence_digest
                       FROM knw_evidence
                       WHERE evidence_id = ?""",
                    (reference.value,),
                ).fetchone()
                if row is None:
                    raise _inconsistent("legacy support reference cannot be resolved")
                locator = _verify_evidence(row, reference)
                if locator not in locators:
                    locators.append(locator)
            visiting.remove(reference)
            resolved.add(reference)

        for reference in references:
            visit(reference)
        return tuple(locators)


def _record_schema(
    row: sqlite3.Row, snapshot: LegacySnapshotMetadata
) -> str:
    schema_version = _required_text(row["schema_version"], "record schema version")
    if schema_version != snapshot.schema_version:
        raise _inconsistent("legacy record schema does not match its snapshot")
    return schema_version


def _legacy_context(raw_json: str, raw_digest: str) -> _LegacyContext:
    document = _json_value(raw_json)
    if not isinstance(document, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in document.items()
    ):
        raise _inconsistent("legacy Context is not a JSON string mapping")
    terms = tuple(
        sorted(
            (
                _required_text(key, "Context dimension"),
                _required_text(value, "Context value"),
            )
            for key, value in document.items()
        )
    )
    expected = digest_of({"context": terms, "canonicalization": "1"})
    if Digest(raw_digest) != expected:
        raise _inconsistent("legacy Context digest does not verify")
    return _LegacyContext(terms=terms, digest=expected)


def _reviewed_grounding_digest(raw_json: str | None) -> Digest | None:
    if raw_json is None:
        return None
    document = _json_value(raw_json)
    expected_keys = {
        "schema_version",
        "candidate_key",
        "proposer_model_call_id",
        "proposer_output_digest",
        "reviewer_model_call_id",
        "reviewer_output_digest",
        "actual_model_fingerprint",
        "need_ids",
        "digest",
    }
    if not isinstance(document, dict) or set(document) != expected_keys:
        raise _inconsistent("legacy reviewed Fact grounding has an invalid shape")
    schema_version = _required_text(
        document["schema_version"], "reviewed Fact grounding schema"
    )
    if schema_version != "REVIEWED_FACT_GROUNDING@2":
        raise _inconsistent("legacy reviewed Fact grounding schema is unsupported")
    proposer_id = StableId(document["proposer_model_call_id"])
    reviewer_id = StableId(document["reviewer_model_call_id"])
    if proposer_id == reviewer_id:
        raise _inconsistent("legacy reviewed Fact grounding reuses one model call")
    need_ids_value = document["need_ids"]
    if not isinstance(need_ids_value, list):
        raise _inconsistent("legacy reviewed Fact grounding Need IDs are invalid")
    need_ids = tuple(
        _required_text(item, "reviewed Fact grounding Need ID")
        for item in need_ids_value
    )
    if not need_ids or len(need_ids) != len(set(need_ids)):
        raise _inconsistent("legacy reviewed Fact grounding Need IDs are invalid")
    core = {
        "schema_version": schema_version,
        "candidate_key": _required_text(
            document["candidate_key"], "reviewed Fact candidate key"
        ),
        "proposer_model_call_id": proposer_id.value,
        "proposer_output_digest": Digest(
            document["proposer_output_digest"]
        ).value,
        "reviewer_model_call_id": reviewer_id.value,
        "reviewer_output_digest": Digest(
            document["reviewer_output_digest"]
        ).value,
        "actual_model_fingerprint": _required_text(
            document["actual_model_fingerprint"],
            "reviewed Fact model fingerprint",
        ),
        "need_ids": need_ids,
    }
    expected = digest_of(core)
    if Digest(document["digest"]) != expected:
        raise _inconsistent("legacy reviewed Fact grounding digest does not verify")
    return expected


def _verify_evidence(row: sqlite3.Row, reference: StableId) -> str:
    evidence_id = StableId(row["evidence_id"])
    if evidence_id != reference:
        raise _inconsistent("legacy Evidence identity does not match its reference")
    artifact_id = StableId(row["artifact_id"])
    source_context_id = StableId(row["source_context_id"])
    byte_start = row["byte_start"]
    byte_end = row["byte_end"]
    excerpt = row["excerpt"]
    if (
        type(byte_start) is not int
        or type(byte_end) is not int
        or byte_start < 0
        or byte_end <= byte_start
        or not isinstance(excerpt, str)
    ):
        raise _inconsistent("legacy Evidence byte range is invalid")
    try:
        encoded_excerpt = excerpt.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise _inconsistent("legacy Evidence excerpt is not UTF-8") from exc
    if len(encoded_excerpt) != byte_end - byte_start:
        raise _inconsistent("legacy Evidence range does not match its excerpt")
    locator = _required_text(row["locator"], "Evidence locator")
    excerpt_digest = digest_of(excerpt)
    if Digest(row["excerpt_digest"]) != excerpt_digest:
        raise _inconsistent("legacy Evidence excerpt digest does not verify")
    artifact_content_digest = Digest(row["artifact_content_digest"])
    core = {
        "artifact_id": artifact_id.value,
        "source_context_id": source_context_id.value,
        "byte_start": byte_start,
        "byte_end": byte_end,
        "locator": locator,
        "excerpt_digest": excerpt_digest.value,
        "artifact_content_digest": artifact_content_digest.value,
    }
    expected = digest_of(core)
    if Digest(row["evidence_digest"]) != expected or evidence_id != _stable(
        "evidence", expected
    ):
        raise _inconsistent("legacy Evidence identity or digest does not verify")
    return locator


def _stable_id_array(value: str) -> tuple[StableId, ...]:
    document = _json_value(value)
    if not isinstance(document, list) or any(not isinstance(item, str) for item in document):
        raise _inconsistent("legacy support references are not a JSON string array")
    references = tuple(StableId(item) for item in document)
    return references


def _text_array(value: str, label: str, *, allow_empty: bool) -> tuple[str, ...]:
    document = _json_value(value)
    if not isinstance(document, list):
        raise _inconsistent(f"legacy {label} are not a JSON string array")
    items = tuple(_required_text(item, label) for item in document)
    if (not allow_empty and not items) or len(items) != len(set(items)):
        raise _inconsistent(f"legacy {label} must be unique")
    return items


def _json_value(value: str) -> object:
    if not isinstance(value, str):
        raise _inconsistent("legacy JSON authority value is not text")
    try:
        return json.loads(value, object_pairs_hook=_unique_json_object)
    except (json.JSONDecodeError, ValueError) as exc:
        raise _inconsistent("legacy JSON authority value is not canonical JSON") from exc


def _unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _stable(kind: str, digest: Digest) -> StableId:
    return StableId(f"{kind}_{digest.value[-32:]}")


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _inconsistent(f"legacy {label} is invalid")
    return value


def _inconsistent(message: str) -> DomainError:
    return DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)
