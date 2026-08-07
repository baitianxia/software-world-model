from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import TYPE_CHECKING
import uuid

from swm_demo.artifact_contract import SourceCollection
from swm_demo.knowledge_contract import KNOWLEDGE_SCHEMA_VERSION

if TYPE_CHECKING:
    from swm_demo.knowledge_engine import KnowledgePackage


class KnowledgeStoreError(RuntimeError):
    pass


class SQLiteKnowledgeStore:
    """One physical store with module-specific ownership methods.

    Sharing SQLite does not merge logical ownership: Source Integration writes
    Artifacts, while Knowledge Engine publishes Evidence and formal knowledge.
    """

    def __init__(self, database: Path):
        self.database = database.resolve()
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._initialize()

    def close(self) -> None:
        self.connection.close()

    def upsert_scope(self, scope_id: str, name: str) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO knowledge_scopes(scope_id, name)
                VALUES (?, ?)
                ON CONFLICT(scope_id) DO UPDATE SET name = excluded.name
                """,
                (scope_id, name),
            )

    def bind_source(
        self,
        scope_id: str,
        source_type: str,
        source_path: Path,
        expected_revision: str | None,
    ) -> None:
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO source_bindings(
                    scope_id, source_type, source_path, expected_revision
                )
                VALUES (?, ?, ?, ?)
                ON CONFLICT(scope_id) DO UPDATE SET
                    source_type = excluded.source_type,
                    source_path = excluded.source_path,
                    expected_revision = excluded.expected_revision
                """,
                (
                    scope_id,
                    source_type,
                    str(source_path.resolve()),
                    expected_revision,
                ),
            )

    def get_binding(self, scope_id: str) -> dict[str, str | None]:
        row = self.connection.execute(
            """
            SELECT s.scope_id, s.name, b.source_type,
                   b.source_path, b.expected_revision
            FROM knowledge_scopes s
            JOIN source_bindings b ON b.scope_id = s.scope_id
            WHERE s.scope_id = ?
            """,
            (scope_id,),
        ).fetchone()
        if row is None:
            raise KnowledgeStoreError(f"KnowledgeScope is not configured: {scope_id}")
        return dict(row)

    def start_snapshot(
        self,
        scope_id: str,
        revision: str,
        knowledge_schema_version: str = KNOWLEDGE_SCHEMA_VERSION,
    ) -> str:
        snapshot_id = f"snapshot:{uuid.uuid4()}"
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO snapshots(
                    snapshot_id, scope_id, revision, knowledge_schema_version,
                    status, created_at
                )
                VALUES (?, ?, ?, ?, 'BUILDING', ?)
                """,
                (
                    snapshot_id,
                    scope_id,
                    revision,
                    knowledge_schema_version,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
        return snapshot_id

    def save_source_artifacts(
        self, snapshot_id: str, collection: SourceCollection
    ) -> None:
        """Source Integration's persistence boundary."""

        with self.connection:
            for artifact in collection.artifacts:
                self.connection.execute(
                    """
                    INSERT INTO artifacts(
                        artifact_id, artifact_type, source_id, scope_id,
                        relative_path, revision, content_hash, content
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(artifact_id) DO NOTHING
                    """,
                    (
                        artifact.artifact_id,
                        artifact.artifact_type,
                        artifact.source_id,
                        artifact.scope_id,
                        artifact.relative_path,
                        artifact.revision,
                        artifact.content_hash,
                        artifact.content,
                    ),
                )
                self.connection.execute(
                    """
                    INSERT INTO snapshot_artifacts(snapshot_id, artifact_id)
                    VALUES (?, ?)
                    """,
                    (snapshot_id, artifact.artifact_id),
                )
            for artifact in collection.artifacts:
                for parent_artifact_id in artifact.lineage_ids:
                    self.connection.execute(
                        """
                        INSERT INTO artifact_lineage(artifact_id, parent_artifact_id)
                        VALUES (?, ?)
                        ON CONFLICT(artifact_id, parent_artifact_id) DO NOTHING
                        """,
                        (artifact.artifact_id, parent_artifact_id),
                    )

    def publish_knowledge(
        self,
        snapshot_id: str,
        package: "KnowledgePackage",
        base_snapshot_id: str | None = None,
    ) -> None:
        """Atomically publish a replacement or same-Revision enrichment.

        ``base_snapshot_id`` is used only by targeted Knowledge Update.  Its
        complete formal state is inherited before the admitted delta is merged.
        Omitting it preserves the existing full-replacement behavior.
        """

        snapshot = self.connection.execute(
            """
            SELECT scope_id, revision, knowledge_schema_version, status
            FROM snapshots WHERE snapshot_id = ?
            """,
            (snapshot_id,),
        ).fetchone()
        if snapshot is None:
            raise KnowledgeStoreError(f"Snapshot does not exist: {snapshot_id}")
        if snapshot["status"] != "BUILDING":
            raise KnowledgeStoreError(
                f"Snapshot is not publishable: {snapshot_id} ({snapshot['status']})"
            )
        if (
            snapshot["scope_id"] != package.scope_id
            or snapshot["revision"] != package.revision
        ):
            raise KnowledgeStoreError("Snapshot and KnowledgePackage context differ")

        with self.connection:
            current = self.connection.execute(
                "SELECT current_snapshot_id FROM knowledge_scopes WHERE scope_id = ?",
                (package.scope_id,),
            ).fetchone()
            current_snapshot_id = (
                str(current["current_snapshot_id"])
                if current is not None and current["current_snapshot_id"]
                else None
            )

            if base_snapshot_id is not None:
                base = self.connection.execute(
                    """
                    SELECT scope_id, revision, knowledge_schema_version, status
                    FROM snapshots WHERE snapshot_id = ?
                    """,
                    (base_snapshot_id,),
                ).fetchone()
                if (
                    base is None
                    or base["scope_id"] != package.scope_id
                    or base["revision"] != package.revision
                    or base["knowledge_schema_version"]
                    != snapshot["knowledge_schema_version"]
                ):
                    raise KnowledgeStoreError(
                        "Snapshot enrichment Base and target context differ"
                    )
                if (
                    current_snapshot_id != base_snapshot_id
                    or base["status"] != "CURRENT"
                ):
                    raise KnowledgeStoreError(
                        "STALE_BASE_SNAPSHOT: targeted update Base is no longer CURRENT"
                    )

                # Acquire SQLite's write lock while re-checking the compare-and-set
                # precondition.  A concurrent publisher cannot pass this point and
                # silently overwrite the investigation's Base.
                locked = self.connection.execute(
                    """
                    UPDATE knowledge_scopes
                    SET current_snapshot_id = current_snapshot_id
                    WHERE scope_id = ? AND current_snapshot_id = ?
                    """,
                    (package.scope_id, base_snapshot_id),
                )
                if locked.rowcount != 1:
                    raise KnowledgeStoreError(
                        "STALE_BASE_SNAPSHOT: targeted update Base changed"
                    )
                self._inherit_snapshot(snapshot_id, base_snapshot_id)

            self._merge_knowledge_package(snapshot_id, package)

            if current_snapshot_id is not None:
                self.connection.execute(
                    "UPDATE snapshots SET status = 'SUPERSEDED' WHERE snapshot_id = ?",
                    (current_snapshot_id,),
                )
            activated = self.connection.execute(
                """
                UPDATE snapshots SET status = 'CURRENT'
                WHERE snapshot_id = ? AND status = 'BUILDING'
                """,
                (snapshot_id,),
            )
            if activated.rowcount != 1:
                raise KnowledgeStoreError("Snapshot activation state changed")

            if base_snapshot_id is None:
                switched = self.connection.execute(
                    """
                    UPDATE knowledge_scopes
                    SET current_snapshot_id = ?
                    WHERE scope_id = ?
                    """,
                    (snapshot_id, package.scope_id),
                )
            else:
                switched = self.connection.execute(
                    """
                    UPDATE knowledge_scopes
                    SET current_snapshot_id = ?
                    WHERE scope_id = ? AND current_snapshot_id = ?
                    """,
                    (snapshot_id, package.scope_id, base_snapshot_id),
                )
            if switched.rowcount != 1:
                raise KnowledgeStoreError(
                    "STALE_BASE_SNAPSHOT: current Snapshot changed during publication"
                )

    def _inherit_snapshot(self, snapshot_id: str, base_snapshot_id: str) -> None:
        """Copy the complete authoritative Base into a BUILDING Snapshot."""

        self.connection.execute(
            """
            INSERT OR IGNORE INTO snapshot_artifacts(snapshot_id, artifact_id)
            SELECT ?, artifact_id
            FROM snapshot_artifacts WHERE snapshot_id = ?
            """,
            (snapshot_id, base_snapshot_id),
        )
        copy_statements = (
            """
            INSERT INTO entities(snapshot_id, entity_id, scope_id, entity_type, name)
            SELECT ?, entity_id, scope_id, entity_type, name
            FROM entities WHERE snapshot_id = ?
            """,
            """
            INSERT INTO evidence(
                snapshot_id, evidence_id, artifact_id, scope_id, revision,
                line_start, line_end, quote, quote_hash
            )
            SELECT ?, evidence_id, artifact_id, scope_id, revision,
                   line_start, line_end, quote, quote_hash
            FROM evidence WHERE snapshot_id = ?
            """,
            """
            INSERT INTO facts(
                snapshot_id, fact_id, scope_id, revision, subject_id,
                predicate, object_id, proposition, model_call_id
            )
            SELECT ?, fact_id, scope_id, revision, subject_id,
                   predicate, object_id, proposition, model_call_id
            FROM facts WHERE snapshot_id = ?
            """,
            """
            INSERT INTO fact_evidence(snapshot_id, fact_id, evidence_id)
            SELECT ?, fact_id, evidence_id
            FROM fact_evidence WHERE snapshot_id = ?
            """,
            """
            INSERT INTO inferences(
                snapshot_id, inference_id, scope_id, revision,
                inference_type, statement, model_call_id
            )
            SELECT ?, inference_id, scope_id, revision,
                   inference_type, statement, model_call_id
            FROM inferences WHERE snapshot_id = ?
            """,
            """
            INSERT INTO inference_facts(snapshot_id, inference_id, fact_id)
            SELECT ?, inference_id, fact_id
            FROM inference_facts WHERE snapshot_id = ?
            """,
            """
            INSERT INTO inference_dependencies(
                snapshot_id, inference_id, dependency_inference_id
            )
            SELECT ?, inference_id, dependency_inference_id
            FROM inference_dependencies WHERE snapshot_id = ?
            """,
        )
        for statement in copy_statements:
            self.connection.execute(statement, (snapshot_id, base_snapshot_id))

    def _merge_knowledge_package(
        self, snapshot_id: str, package: "KnowledgePackage"
    ) -> None:
        """Merge an admitted delta, rejecting stable-ID semantic conflicts."""

        for entity in package.entities:
            merged = self.connection.execute(
                """
                INSERT INTO entities(
                    snapshot_id, entity_id, scope_id, entity_type, name
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_id, entity_id) DO UPDATE SET
                    entity_id = excluded.entity_id
                WHERE entities.scope_id IS excluded.scope_id
                  AND entities.entity_type IS excluded.entity_type
                  AND entities.name IS excluded.name
                """,
                (
                    snapshot_id,
                    entity.entity_id,
                    entity.scope_id,
                    entity.entity_type,
                    entity.name,
                ),
            )
            self._require_compatible_merge(merged.rowcount, "Entity", entity.entity_id)

        for item in package.evidence:
            merged = self.connection.execute(
                """
                INSERT INTO evidence(
                    snapshot_id, evidence_id, artifact_id, scope_id, revision,
                    line_start, line_end, quote, quote_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_id, evidence_id) DO UPDATE SET
                    evidence_id = excluded.evidence_id
                WHERE evidence.artifact_id IS excluded.artifact_id
                  AND evidence.scope_id IS excluded.scope_id
                  AND evidence.revision IS excluded.revision
                  AND evidence.line_start IS excluded.line_start
                  AND evidence.line_end IS excluded.line_end
                  AND evidence.quote IS excluded.quote
                  AND evidence.quote_hash IS excluded.quote_hash
                """,
                (
                    snapshot_id,
                    item.evidence_id,
                    item.artifact_id,
                    item.scope_id,
                    item.revision,
                    item.line_start,
                    item.line_end,
                    item.quote,
                    item.quote_hash,
                ),
            )
            self._require_compatible_merge(merged.rowcount, "Evidence", item.evidence_id)

        for fact in package.facts:
            merged = self.connection.execute(
                """
                INSERT INTO facts(
                    snapshot_id, fact_id, scope_id, revision,
                    subject_id, predicate, object_id, proposition,
                    model_call_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_id, fact_id) DO UPDATE SET
                    model_call_id = COALESCE(facts.model_call_id, excluded.model_call_id)
                WHERE facts.scope_id IS excluded.scope_id
                  AND facts.revision IS excluded.revision
                  AND facts.subject_id IS excluded.subject_id
                  AND facts.predicate IS excluded.predicate
                  AND facts.object_id IS excluded.object_id
                  AND facts.proposition IS excluded.proposition
                """,
                (
                    snapshot_id,
                    fact.fact_id,
                    fact.scope_id,
                    fact.revision,
                    fact.subject_id,
                    fact.predicate,
                    fact.object_id,
                    fact.proposition,
                    fact.model_call_id,
                ),
            )
            self._require_compatible_merge(merged.rowcount, "Fact", fact.fact_id)
            for evidence_id in fact.evidence_ids:
                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO fact_evidence(
                        snapshot_id, fact_id, evidence_id
                    ) VALUES (?, ?, ?)
                    """,
                    (snapshot_id, fact.fact_id, evidence_id),
                )

        for inference in package.inferences:
            merged = self.connection.execute(
                """
                INSERT INTO inferences(
                    snapshot_id, inference_id, scope_id, revision,
                    inference_type, statement, model_call_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(snapshot_id, inference_id) DO UPDATE SET
                    model_call_id = COALESCE(
                        inferences.model_call_id, excluded.model_call_id
                    )
                WHERE inferences.scope_id IS excluded.scope_id
                  AND inferences.revision IS excluded.revision
                  AND inferences.inference_type IS excluded.inference_type
                  AND inferences.statement IS excluded.statement
                """,
                (
                    snapshot_id,
                    inference.inference_id,
                    inference.scope_id,
                    inference.revision,
                    inference.inference_type,
                    inference.statement,
                    inference.model_call_id,
                ),
            )
            self._require_compatible_merge(
                merged.rowcount, "Inference", inference.inference_id
            )
            for fact_id in inference.support_fact_ids:
                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO inference_facts(
                        snapshot_id, inference_id, fact_id
                    ) VALUES (?, ?, ?)
                    """,
                    (snapshot_id, inference.inference_id, fact_id),
                )
            for dependency_id in inference.dependency_inference_ids:
                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO inference_dependencies(
                        snapshot_id, inference_id, dependency_inference_id
                    ) VALUES (?, ?, ?)
                    """,
                    (snapshot_id, inference.inference_id, dependency_id),
                )

    @staticmethod
    def _require_compatible_merge(rowcount: int, kind: str, identifier: str) -> None:
        if rowcount != 1:
            raise KnowledgeStoreError(
                f"conflicting {kind} identity during Snapshot enrichment: {identifier}"
            )

    def fail_snapshot(self, snapshot_id: str, errors: tuple[str, ...]) -> None:
        with self.connection:
            self.connection.execute(
                """
                UPDATE snapshots SET status = 'FAILED', failure_reason = ?
                WHERE snapshot_id = ? AND status = 'BUILDING'
                """,
                ("\n".join(errors), snapshot_id),
            )

    def current_snapshot(self, scope_id: str) -> dict[str, object]:
        row = self.connection.execute(
            """
            SELECT sn.snapshot_id, sn.scope_id, sn.revision,
                   sn.knowledge_schema_version, sn.status, sn.created_at
            FROM knowledge_scopes s
            JOIN snapshots sn ON sn.snapshot_id = s.current_snapshot_id
            WHERE s.scope_id = ?
            """,
            (scope_id,),
        ).fetchone()
        if row is None:
            raise KnowledgeStoreError(
                f"KnowledgeScope has no current Snapshot: {scope_id}"
            )
        return dict(row)

    def current_entities(self, scope_id: str) -> list[dict[str, object]]:
        snapshot_id = self.current_snapshot(scope_id)["snapshot_id"]
        rows = self.connection.execute(
            """
            SELECT entity_id, scope_id, entity_type, name
            FROM entities WHERE snapshot_id = ? ORDER BY entity_type, name
            """,
            (snapshot_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def current_facts(self, scope_id: str) -> list[dict[str, object]]:
        snapshot_id = self.current_snapshot(scope_id)["snapshot_id"]
        rows = self.connection.execute(
            """
            SELECT f.fact_id, f.scope_id, f.revision, f.subject_id,
                   f.predicate, f.object_id, f.proposition, f.model_call_id,
                   COUNT(fe.evidence_id) AS evidence_count
            FROM facts f
            LEFT JOIN fact_evidence fe
              ON fe.snapshot_id = f.snapshot_id AND fe.fact_id = f.fact_id
            WHERE f.snapshot_id = ?
            GROUP BY f.fact_id, f.scope_id, f.revision, f.subject_id,
                     f.predicate, f.object_id, f.proposition, f.model_call_id
            ORDER BY f.predicate, f.fact_id
            """,
            (snapshot_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def current_inferences(self, scope_id: str) -> list[dict[str, object]]:
        snapshot_id = self.current_snapshot(scope_id)["snapshot_id"]
        rows = self.connection.execute(
            """
            SELECT i.inference_id, i.scope_id, i.revision, i.inference_type,
                   i.statement, i.model_call_id,
                   COUNT(DISTINCT inf.fact_id) AS support_fact_count,
                   COUNT(DISTINCT dep.dependency_inference_id) AS dependency_count
            FROM inferences i
            LEFT JOIN inference_facts inf
              ON inf.snapshot_id = i.snapshot_id
             AND inf.inference_id = i.inference_id
            LEFT JOIN inference_dependencies dep
              ON dep.snapshot_id = i.snapshot_id
             AND dep.inference_id = i.inference_id
            WHERE i.snapshot_id = ?
            GROUP BY i.inference_id, i.scope_id, i.revision, i.inference_type,
                     i.statement, i.model_call_id
            ORDER BY i.inference_type, i.inference_id
            """,
            (snapshot_id,),
        ).fetchall()
        return [dict(row) for row in rows]

    def assert_current_context(
        self, scope_id: str, snapshot_token: str
    ) -> dict[str, object]:
        """Resolve a read context and reject a token superseded by publication.

        The token is deliberately just a Snapshot identity in this validation
        demo.  It is an optimistic-consistency token, not an authentication or
        authorization credential.
        """

        current = self.current_snapshot(scope_id)
        if (
            current["snapshot_id"] != snapshot_token
            or current["status"] != "CURRENT"
        ):
            raise KnowledgeStoreError(
                "STALE_CONTEXT: requested Snapshot "
                f"{snapshot_token} is not CURRENT for {scope_id}; "
                f"resolved Snapshot is {current['snapshot_id']} "
                f"with status {current['status']}"
            )
        return current

    def formal_knowledge_catalog(
        self, scope_id: str, snapshot_token: str
    ) -> dict[str, list[dict[str, object]]]:
        self.assert_current_context(scope_id, snapshot_token)
        entity_types = self.connection.execute(
            """
            SELECT entity_type, COUNT(*) AS item_count
            FROM entities
            WHERE snapshot_id = ?
            GROUP BY entity_type
            ORDER BY entity_type
            """,
            (snapshot_token,),
        ).fetchall()
        predicates = self.connection.execute(
            """
            SELECT predicate, COUNT(*) AS fact_count
            FROM facts
            WHERE snapshot_id = ?
            GROUP BY predicate
            ORDER BY predicate
            """,
            (snapshot_token,),
        ).fetchall()
        inference_types = self.connection.execute(
            """
            SELECT inference_type, COUNT(*) AS item_count
            FROM inferences
            WHERE snapshot_id = ?
            GROUP BY inference_type
            ORDER BY inference_type
            """,
            (snapshot_token,),
        ).fetchall()
        return {
            "entity_types": [dict(row) for row in entity_types],
            "predicates": [dict(row) for row in predicates],
            "inference_types": [dict(row) for row in inference_types],
        }

    def search_formal_entities(
        self,
        scope_id: str,
        snapshot_token: str,
        query: str,
        match_mode: str,
        entity_type: str | None,
        limit: int,
        cursor: int = 0,
    ) -> list[dict[str, object]]:
        self.assert_current_context(scope_id, snapshot_token)
        clauses = ["snapshot_id = ?"]
        parameters: list[object] = [snapshot_token]
        if match_mode == "EXACT":
            clauses.append("name = ?")
        else:
            clauses.append("instr(name, ?) > 0")
        parameters.append(query)
        if entity_type is not None:
            clauses.append("entity_type = ?")
            parameters.append(entity_type)
        parameters.extend((limit + 1, cursor))
        rows = self.connection.execute(
            f"""
            SELECT entity_id, scope_id, entity_type, name
            FROM entities
            WHERE {' AND '.join(clauses)}
            ORDER BY entity_type, name, entity_id
            LIMIT ? OFFSET ?
            """,
            parameters,
        ).fetchall()
        return [dict(row) for row in rows]

    def search_formal_inferences(
        self,
        scope_id: str,
        snapshot_token: str,
        query: str,
        match_mode: str,
        inference_type: str | None,
        limit: int,
        cursor: int = 0,
    ) -> list[dict[str, object]]:
        self.assert_current_context(scope_id, snapshot_token)
        clauses = ["i.snapshot_id = ?"]
        parameters: list[object] = [snapshot_token]
        if match_mode == "EXACT":
            clauses.append("i.statement = ?")
        else:
            clauses.append("instr(i.statement, ?) > 0")
        parameters.append(query)
        if inference_type is not None:
            clauses.append("i.inference_type = ?")
            parameters.append(inference_type)
        parameters.extend((limit + 1, cursor))
        rows = self.connection.execute(
            f"""
            SELECT i.inference_id, i.scope_id, i.revision,
                   i.inference_type, i.statement, i.model_call_id,
                   COUNT(DISTINCT inf.fact_id) AS support_fact_count,
                   COUNT(DISTINCT dep.dependency_inference_id) AS dependency_count
            FROM inferences i
            LEFT JOIN inference_facts inf
              ON inf.snapshot_id = i.snapshot_id
             AND inf.inference_id = i.inference_id
            LEFT JOIN inference_dependencies dep
              ON dep.snapshot_id = i.snapshot_id
             AND dep.inference_id = i.inference_id
            WHERE {' AND '.join(clauses)}
            GROUP BY i.inference_id, i.scope_id, i.revision,
                     i.inference_type, i.statement, i.model_call_id
            ORDER BY i.inference_type, i.statement, i.inference_id
            LIMIT ? OFFSET ?
            """,
            parameters,
        ).fetchall()
        return [dict(row) for row in rows]

    def formal_fact_neighborhood(
        self,
        scope_id: str,
        snapshot_token: str,
        entity_ids: tuple[str, ...],
        direction: str,
        predicates: tuple[str, ...],
        limit: int,
        cursor: int = 0,
    ) -> list[dict[str, object]]:
        self.assert_current_context(scope_id, snapshot_token)
        entity_placeholders = ", ".join("?" for _ in entity_ids)
        parameters: list[object] = [snapshot_token]
        if direction == "OUTGOING":
            relation_clause = f"f.subject_id IN ({entity_placeholders})"
            parameters.extend(entity_ids)
        elif direction == "INCOMING":
            relation_clause = f"f.object_id IN ({entity_placeholders})"
            parameters.extend(entity_ids)
        else:
            relation_clause = (
                f"(f.subject_id IN ({entity_placeholders}) "
                f"OR f.object_id IN ({entity_placeholders}))"
            )
            parameters.extend(entity_ids)
            parameters.extend(entity_ids)

        predicate_clause = ""
        if predicates:
            predicate_placeholders = ", ".join("?" for _ in predicates)
            predicate_clause = f"AND f.predicate IN ({predicate_placeholders})"
            parameters.extend(predicates)
        parameters.extend((limit + 1, cursor))
        rows = self.connection.execute(
            f"""
            SELECT f.fact_id, f.scope_id, f.revision, f.proposition,
                   f.model_call_id,
                   f.subject_id, subject.entity_type AS subject_type,
                   subject.name AS subject_name, f.predicate,
                   f.object_id, object.entity_type AS object_type,
                   object.name AS object_name,
                   COUNT(fe.evidence_id) AS evidence_count
            FROM facts f
            JOIN entities subject
              ON subject.snapshot_id = f.snapshot_id
             AND subject.entity_id = f.subject_id
            JOIN entities object
              ON object.snapshot_id = f.snapshot_id
             AND object.entity_id = f.object_id
            LEFT JOIN fact_evidence fe
              ON fe.snapshot_id = f.snapshot_id AND fe.fact_id = f.fact_id
            WHERE f.snapshot_id = ? AND {relation_clause}
                  {predicate_clause}
            GROUP BY f.fact_id, f.scope_id, f.revision, f.proposition,
                     f.model_call_id,
                     f.subject_id, subject.entity_type, subject.name,
                     f.predicate, f.object_id, object.entity_type, object.name
            ORDER BY f.predicate, subject.name, object.name, f.fact_id
            LIMIT ? OFFSET ?
            """,
            parameters,
        ).fetchall()
        return [dict(row) for row in rows]

    def explain_formal_facts(
        self,
        scope_id: str,
        snapshot_token: str,
        fact_ids: tuple[str, ...],
    ) -> tuple[list[dict[str, object]], list[str]]:
        self.assert_current_context(scope_id, snapshot_token)
        placeholders = ", ".join("?" for _ in fact_ids)
        facts = self.connection.execute(
            f"""
            SELECT f.fact_id, f.scope_id, f.predicate, f.revision,
                   f.proposition, f.model_call_id,
                   f.subject_id, subject.entity_type AS subject_type,
                   subject.name AS subject_name,
                   f.object_id, object.entity_type AS object_type,
                   object.name AS object_name
            FROM facts f
            JOIN entities subject
              ON subject.snapshot_id = f.snapshot_id
             AND subject.entity_id = f.subject_id
            JOIN entities object
              ON object.snapshot_id = f.snapshot_id
             AND object.entity_id = f.object_id
            WHERE f.snapshot_id = ? AND f.fact_id IN ({placeholders})
            ORDER BY f.fact_id
            """,
            (snapshot_token, *fact_ids),
        ).fetchall()
        by_id = {row["fact_id"]: dict(row) for row in facts}
        observations = self.connection.execute(
            f"""
            SELECT fe.fact_id, e.evidence_id, a.relative_path, e.revision,
                   e.line_start, e.line_end, e.quote_hash,
                   a.artifact_id, a.content_hash AS artifact_content_hash
            FROM fact_evidence fe
            JOIN evidence e
              ON e.snapshot_id = fe.snapshot_id
             AND e.evidence_id = fe.evidence_id
            JOIN artifacts a ON a.artifact_id = e.artifact_id
            WHERE fe.snapshot_id = ? AND fe.fact_id IN ({placeholders})
            ORDER BY fe.fact_id, a.relative_path, e.line_start,
                     e.line_end, e.evidence_id
            """,
            (snapshot_token, *fact_ids),
        ).fetchall()
        for item in by_id.values():
            item["evidence"] = []
        for row in observations:
            fact_id = row["fact_id"]
            observation = dict(row)
            del observation["fact_id"]
            by_id[fact_id]["evidence"].append(observation)
        missing = sorted(set(fact_ids) - set(by_id))
        return [by_id[fact_id] for fact_id in sorted(by_id)], missing

    def explain_formal_inferences(
        self,
        scope_id: str,
        snapshot_token: str,
        inference_ids: tuple[str, ...],
    ) -> tuple[list[dict[str, object]], list[str]]:
        self.assert_current_context(scope_id, snapshot_token)
        placeholders = ", ".join("?" for _ in inference_ids)
        inferences = self.connection.execute(
            f"""
            SELECT inference_id, scope_id, inference_type, statement,
                   revision, model_call_id
            FROM inferences
            WHERE snapshot_id = ? AND inference_id IN ({placeholders})
            ORDER BY inference_id
            """,
            (snapshot_token, *inference_ids),
        ).fetchall()
        by_id = {row["inference_id"]: dict(row) for row in inferences}
        supports = self.connection.execute(
            f"""
            SELECT inf.inference_id, f.fact_id, f.predicate, f.proposition,
                   subject.name AS subject_name, object.name AS object_name
            FROM inference_facts inf
            JOIN facts f
              ON f.snapshot_id = inf.snapshot_id AND f.fact_id = inf.fact_id
            JOIN entities subject
              ON subject.snapshot_id = f.snapshot_id
             AND subject.entity_id = f.subject_id
            JOIN entities object
              ON object.snapshot_id = f.snapshot_id
             AND object.entity_id = f.object_id
            WHERE inf.snapshot_id = ?
              AND inf.inference_id IN ({placeholders})
            ORDER BY inf.inference_id, f.fact_id
            """,
            (snapshot_token, *inference_ids),
        ).fetchall()
        dependencies = self.connection.execute(
            f"""
            SELECT inference_id, dependency_inference_id
            FROM inference_dependencies
            WHERE snapshot_id = ? AND inference_id IN ({placeholders})
            ORDER BY inference_id, dependency_inference_id
            """,
            (snapshot_token, *inference_ids),
        ).fetchall()
        for item in by_id.values():
            item["supporting_facts"] = []
            item["dependency_inference_ids"] = []
        for row in supports:
            inference_id = row["inference_id"]
            support = dict(row)
            del support["inference_id"]
            by_id[inference_id]["supporting_facts"].append(support)
        for row in dependencies:
            by_id[row["inference_id"]]["dependency_inference_ids"].append(
                row["dependency_inference_id"]
            )
        missing = sorted(set(inference_ids) - set(by_id))
        return [by_id[item_id] for item_id in sorted(by_id)], missing

    def explain_fact(self, scope_id: str, fact_id: str) -> dict[str, object]:
        snapshot_id = self.current_snapshot(scope_id)["snapshot_id"]
        fact = self.connection.execute(
            """
            SELECT f.fact_id, f.predicate, f.revision, f.proposition,
                   f.model_call_id,
                   subject.name AS subject_name, object.name AS object_name
            FROM facts f
            JOIN entities subject
              ON subject.snapshot_id = f.snapshot_id
             AND subject.entity_id = f.subject_id
            JOIN entities object
              ON object.snapshot_id = f.snapshot_id
             AND object.entity_id = f.object_id
            WHERE f.snapshot_id = ? AND f.fact_id = ?
            """,
            (snapshot_id, fact_id),
        ).fetchone()
        if fact is None:
            raise KnowledgeStoreError(
                f"Fact is not in the current Snapshot: {fact_id}"
            )
        observations = self.connection.execute(
            """
            SELECT e.evidence_id, a.relative_path, e.revision,
                   e.line_start, e.line_end, e.quote, e.quote_hash,
                   a.artifact_id, a.content_hash AS artifact_content_hash
            FROM fact_evidence fe
            JOIN evidence e
              ON e.snapshot_id = fe.snapshot_id
             AND e.evidence_id = fe.evidence_id
            JOIN artifacts a ON a.artifact_id = e.artifact_id
            WHERE fe.snapshot_id = ? AND fe.fact_id = ?
            ORDER BY a.relative_path, e.line_start
            """,
            (snapshot_id, fact_id),
        ).fetchall()
        result = dict(fact)
        result["snapshot_id"] = snapshot_id
        result["evidence"] = [dict(row) for row in observations]
        return result

    def explain_inference(
        self, scope_id: str, inference_id: str
    ) -> dict[str, object]:
        snapshot_id = self.current_snapshot(scope_id)["snapshot_id"]
        inference = self.connection.execute(
            """
            SELECT inference_id, inference_type, statement, revision, model_call_id
            FROM inferences
            WHERE snapshot_id = ? AND inference_id = ?
            """,
            (snapshot_id, inference_id),
        ).fetchone()
        if inference is None:
            raise KnowledgeStoreError(
                f"Inference is not in the current Snapshot: {inference_id}"
            )
        support_rows = self.connection.execute(
            """
            SELECT f.fact_id, f.predicate, f.proposition,
                   subject.name AS subject_name, object.name AS object_name
            FROM inference_facts inf
            JOIN facts f
              ON f.snapshot_id = inf.snapshot_id AND f.fact_id = inf.fact_id
            JOIN entities subject
              ON subject.snapshot_id = f.snapshot_id
             AND subject.entity_id = f.subject_id
            JOIN entities object
              ON object.snapshot_id = f.snapshot_id
             AND object.entity_id = f.object_id
            WHERE inf.snapshot_id = ? AND inf.inference_id = ?
            ORDER BY f.fact_id
            """,
            (snapshot_id, inference_id),
        ).fetchall()
        dependency_rows = self.connection.execute(
            """
            SELECT dependency_inference_id
            FROM inference_dependencies
            WHERE snapshot_id = ? AND inference_id = ?
            ORDER BY dependency_inference_id
            """,
            (snapshot_id, inference_id),
        ).fetchall()
        result = dict(inference)
        result["snapshot_id"] = snapshot_id
        result["supporting_facts"] = [dict(row) for row in support_rows]
        result["dependency_inference_ids"] = [
            row["dependency_inference_id"] for row in dependency_rows
        ]
        return result

    def missing_formal_references(
        self,
        scope_id: str,
        snapshot_token: str,
        references: tuple[tuple[str, str], ...],
    ) -> tuple[tuple[str, str], ...]:
        self.assert_current_context(scope_id, snapshot_token)
        missing: list[tuple[str, str]] = []
        for kind, reference_id in sorted(set(references)):
            table, column = (
                ("facts", "fact_id")
                if kind == "FACT"
                else ("inferences", "inference_id")
            )
            row = self.connection.execute(
                f"SELECT 1 FROM {table} WHERE snapshot_id = ? AND {column} = ?",
                (snapshot_token, reference_id),
            ).fetchone()
            if row is None:
                missing.append((kind, reference_id))
        return tuple(missing)

    def snapshot_counts(self, snapshot_id: str) -> dict[str, int]:
        queries = {
            "artifact_count": "SELECT COUNT(*) FROM snapshot_artifacts WHERE snapshot_id = ?",
            "entity_count": "SELECT COUNT(*) FROM entities WHERE snapshot_id = ?",
            "evidence_count": "SELECT COUNT(*) FROM evidence WHERE snapshot_id = ?",
            "fact_count": "SELECT COUNT(*) FROM facts WHERE snapshot_id = ?",
            "inference_count": "SELECT COUNT(*) FROM inferences WHERE snapshot_id = ?",
        }
        return {
            name: int(self.connection.execute(sql, (snapshot_id,)).fetchone()[0])
            for name, sql in queries.items()
        }

    def record_model_call(self, record: dict[str, object]) -> None:
        """Model Gateway's append-only provenance boundary."""

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO model_calls(
                    model_call_id, provider, model, model_version, capability,
                    request_hash, response, created_at, context_id, phase
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["model_call_id"],
                    record["provider"],
                    record["model"],
                    record["model_version"],
                    record["capability"],
                    record["request_hash"],
                    record["response"],
                    record["created_at"],
                    record.get("context_id"),
                    record.get("phase"),
                ),
            )

    def model_call_count(self) -> int:
        return int(self.connection.execute("SELECT COUNT(*) FROM model_calls").fetchone()[0])

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS knowledge_scopes (
                scope_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                current_snapshot_id TEXT
            );

            CREATE TABLE IF NOT EXISTS source_bindings (
                scope_id TEXT PRIMARY KEY REFERENCES knowledge_scopes(scope_id),
                source_type TEXT NOT NULL DEFAULT 'local-git',
                source_path TEXT NOT NULL,
                expected_revision TEXT
            );

            CREATE TABLE IF NOT EXISTS snapshots (
                snapshot_id TEXT PRIMARY KEY,
                scope_id TEXT NOT NULL REFERENCES knowledge_scopes(scope_id),
                revision TEXT NOT NULL,
                knowledge_schema_version TEXT NOT NULL DEFAULT '1.1',
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                failure_reason TEXT
            );

            CREATE TABLE IF NOT EXISTS artifacts (
                artifact_id TEXT PRIMARY KEY,
                artifact_type TEXT NOT NULL,
                source_id TEXT NOT NULL,
                scope_id TEXT NOT NULL,
                relative_path TEXT NOT NULL,
                revision TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                content TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS snapshot_artifacts (
                snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id),
                artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
                PRIMARY KEY(snapshot_id, artifact_id)
            );

            CREATE TABLE IF NOT EXISTS artifact_lineage (
                artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
                parent_artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
                PRIMARY KEY(artifact_id, parent_artifact_id)
            );

            CREATE TABLE IF NOT EXISTS entities (
                snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id),
                entity_id TEXT NOT NULL,
                scope_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                name TEXT NOT NULL,
                PRIMARY KEY(snapshot_id, entity_id)
            );

            CREATE TABLE IF NOT EXISTS evidence (
                snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id),
                evidence_id TEXT NOT NULL,
                artifact_id TEXT NOT NULL REFERENCES artifacts(artifact_id),
                scope_id TEXT NOT NULL,
                revision TEXT NOT NULL,
                line_start INTEGER NOT NULL,
                line_end INTEGER NOT NULL,
                quote TEXT NOT NULL,
                quote_hash TEXT NOT NULL,
                PRIMARY KEY(snapshot_id, evidence_id)
            );

            CREATE TABLE IF NOT EXISTS facts (
                snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id),
                fact_id TEXT NOT NULL,
                scope_id TEXT NOT NULL,
                revision TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                predicate TEXT NOT NULL,
                object_id TEXT NOT NULL,
                proposition TEXT NOT NULL DEFAULT '',
                model_call_id TEXT,
                PRIMARY KEY(snapshot_id, fact_id)
            );

            CREATE TABLE IF NOT EXISTS fact_evidence (
                snapshot_id TEXT NOT NULL,
                fact_id TEXT NOT NULL,
                evidence_id TEXT NOT NULL,
                PRIMARY KEY(snapshot_id, fact_id, evidence_id),
                FOREIGN KEY(snapshot_id, fact_id)
                    REFERENCES facts(snapshot_id, fact_id),
                FOREIGN KEY(snapshot_id, evidence_id)
                    REFERENCES evidence(snapshot_id, evidence_id)
            );

            CREATE TABLE IF NOT EXISTS inferences (
                snapshot_id TEXT NOT NULL REFERENCES snapshots(snapshot_id),
                inference_id TEXT NOT NULL,
                scope_id TEXT NOT NULL,
                revision TEXT NOT NULL,
                inference_type TEXT NOT NULL,
                statement TEXT NOT NULL,
                model_call_id TEXT,
                PRIMARY KEY(snapshot_id, inference_id)
            );

            CREATE TABLE IF NOT EXISTS inference_facts (
                snapshot_id TEXT NOT NULL,
                inference_id TEXT NOT NULL,
                fact_id TEXT NOT NULL,
                PRIMARY KEY(snapshot_id, inference_id, fact_id),
                FOREIGN KEY(snapshot_id, inference_id)
                    REFERENCES inferences(snapshot_id, inference_id),
                FOREIGN KEY(snapshot_id, fact_id)
                    REFERENCES facts(snapshot_id, fact_id)
            );

            CREATE TABLE IF NOT EXISTS inference_dependencies (
                snapshot_id TEXT NOT NULL,
                inference_id TEXT NOT NULL,
                dependency_inference_id TEXT NOT NULL,
                PRIMARY KEY(snapshot_id, inference_id, dependency_inference_id),
                FOREIGN KEY(snapshot_id, inference_id)
                    REFERENCES inferences(snapshot_id, inference_id),
                FOREIGN KEY(snapshot_id, dependency_inference_id)
                    REFERENCES inferences(snapshot_id, inference_id)
            );

            CREATE TABLE IF NOT EXISTS model_calls (
                model_call_id TEXT PRIMARY KEY,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                model_version TEXT NOT NULL,
                capability TEXT NOT NULL,
                request_hash TEXT NOT NULL,
                response TEXT NOT NULL,
                created_at TEXT NOT NULL,
                context_id TEXT,
                phase TEXT
            );
            """
        )
        source_binding_columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(source_bindings)")
        }
        if "source_type" not in source_binding_columns:
            with self.connection:
                self.connection.execute(
                    """
                    ALTER TABLE source_bindings
                    ADD COLUMN source_type TEXT NOT NULL DEFAULT 'local-git'
                    """
                )
        snapshot_columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(snapshots)")
        }
        if "knowledge_schema_version" not in snapshot_columns:
            with self.connection:
                self.connection.execute(
                    """
                    ALTER TABLE snapshots
                    ADD COLUMN knowledge_schema_version TEXT NOT NULL DEFAULT '1.0'
                    """
                )
        fact_columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(facts)")
        }
        if "proposition" not in fact_columns:
            with self.connection:
                self.connection.execute(
                    """
                    ALTER TABLE facts
                    ADD COLUMN proposition TEXT NOT NULL DEFAULT ''
                    """
                )
        if "model_call_id" not in fact_columns:
            with self.connection:
                self.connection.execute(
                    """
                    ALTER TABLE facts ADD COLUMN model_call_id TEXT
                    """
                )
        model_call_columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(model_calls)")
        }
        if "context_id" not in model_call_columns:
            with self.connection:
                self.connection.execute(
                    "ALTER TABLE model_calls ADD COLUMN context_id TEXT"
                )
        if "phase" not in model_call_columns:
            with self.connection:
                self.connection.execute(
                    "ALTER TABLE model_calls ADD COLUMN phase TEXT"
                )
