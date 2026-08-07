"""SQLite repository for derived artifacts and immutable lineage edges."""

from __future__ import annotations

import json
import sqlite3

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, StableId, canonical_json_bytes
from software_world_model.source_integration.artifact_processing import (
    ArtifactLineage,
    DerivedArtifact,
    TransformationClass,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS src_derived_artifacts (
    artifact_id TEXT PRIMARY KEY,
    artifact_kind TEXT NOT NULL,
    payload_schema_version TEXT NOT NULL,
    parent_artifact_ids_json TEXT NOT NULL,
    content_digest TEXT NOT NULL,
    payload BLOB NOT NULL,
    classification TEXT NOT NULL,
    derivation_key_digest TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS src_artifact_lineage (
    lineage_id TEXT PRIMARY KEY,
    child_artifact_id TEXT NOT NULL UNIQUE,
    parent_artifact_ids_json TEXT NOT NULL,
    transformation_class TEXT NOT NULL,
    transformation_contract TEXT NOT NULL,
    input_ranges_json TEXT NOT NULL,
    output_start INTEGER NOT NULL,
    output_end INTEGER NOT NULL,
    locator_reversible INTEGER NOT NULL,
    replayable INTEGER NOT NULL,
    source_root_cardinality INTEGER NOT NULL,
    lineage_digest TEXT NOT NULL,
    FOREIGN KEY (child_artifact_id) REFERENCES src_derived_artifacts(artifact_id)
);
"""


class SqliteArtifactProcessingRepository:
    def __init__(self, database: SqliteDatabase) -> None:
        self._database = database
        self._database.executescript(_SCHEMA)

    def save(
        self,
        *,
        artifacts: tuple[DerivedArtifact, ...],
        lineages: tuple[ArtifactLineage, ...],
    ) -> tuple[DerivedArtifact, ...]:
        if {item.artifact_id for item in artifacts} != {item.child_artifact_id for item in lineages}:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "each derived artifact requires exactly one lineage edge in this slice",
            )
        try:
            with self._database.transaction() as connection:
                for artifact in artifacts:
                    existing = connection.execute(
                        "SELECT content_digest FROM src_derived_artifacts WHERE derivation_key_digest = ?",
                        (artifact.derivation_key_digest.value,),
                    ).fetchone()
                    if existing is not None:
                        if existing["content_digest"] != artifact.content_digest.value:
                            raise DomainError(
                                ErrorCode.SOURCE_REVISION_INCONSISTENT,
                                "deterministic derivation key produced different content",
                            )
                        continue
                    connection.execute(
                        "INSERT INTO src_derived_artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            artifact.artifact_id.value,
                            artifact.artifact_kind,
                            artifact.payload_schema_version,
                            _json([item.value for item in artifact.parent_artifact_ids]),
                            artifact.content_digest.value,
                            artifact.payload,
                            artifact.classification,
                            artifact.derivation_key_digest.value,
                        ),
                    )
                for lineage in lineages:
                    existing = connection.execute(
                        "SELECT lineage_digest FROM src_artifact_lineage WHERE child_artifact_id = ?",
                        (lineage.child_artifact_id.value,),
                    ).fetchone()
                    if existing is not None:
                        if existing["lineage_digest"] != lineage.digest.value:
                            raise DomainError(
                                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                                "derived artifact lineage cannot change",
                            )
                        continue
                    if lineage.child_artifact_id in lineage.parent_artifact_ids:
                        raise DomainError(ErrorCode.INVALID_ARGUMENT, "artifact lineage cannot self-cycle")
                    connection.execute(
                        "INSERT INTO src_artifact_lineage VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            lineage.lineage_id.value,
                            lineage.child_artifact_id.value,
                            _json([item.value for item in lineage.parent_artifact_ids]),
                            lineage.transformation_class.value,
                            lineage.transformation_contract,
                            _json(lineage.input_ranges),
                            lineage.output_range[0],
                            lineage.output_range[1],
                            int(lineage.locator_reversible),
                            int(lineage.replayable),
                            lineage.source_root_cardinality,
                            lineage.digest.value,
                        ),
                    )
                return tuple(self._load(connection, item.artifact_id) for item in artifacts)
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "derived artifact transaction violated a store invariant",
                {"sqlite_error": str(exc)},
            ) from exc

    @staticmethod
    def _load(connection: sqlite3.Connection, artifact_id: StableId) -> DerivedArtifact:
        row = connection.execute(
            "SELECT * FROM src_derived_artifacts WHERE artifact_id = ?", (artifact_id.value,)
        ).fetchone()
        return DerivedArtifact(
            artifact_id=artifact_id,
            artifact_kind=row["artifact_kind"],
            payload_schema_version=row["payload_schema_version"],
            parent_artifact_ids=tuple(StableId(item) for item in json.loads(row["parent_artifact_ids_json"])),
            content_digest=Digest(row["content_digest"]),
            payload=bytes(row["payload"]),
            classification=row["classification"],
            derivation_key_digest=Digest(row["derivation_key_digest"]),
        )


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")
