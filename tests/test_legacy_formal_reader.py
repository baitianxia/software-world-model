from __future__ import annotations

from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.infrastructure.sqlite_legacy_formal_reader import (
    LegacyKnowledgeObjectKind,
    LegacySnapshotMember,
    SqliteLegacyFormalReader,
)
from software_world_model.knowledge_engine.formal import KnowledgeContext


ROOT = Path(__file__).resolve().parents[1]
LEGACY_ROOT = ROOT / "validation" / "structure_world_model_iteration_003" / "legacy"
DATABASE_PATH = LEGACY_ROOT / "iteration-002-legacy.sqlite3"
REPORT_PATH = LEGACY_ROOT / "iteration-002-legacy-report.json"
LEGACY_SCHEMA_DIGEST = (
    "sha256:75e96739d6b05aca368d5be4fcfb84eddf8fbbb996e65e9ba9f6738562a4e436"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class SqliteLegacyFormalReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        self.snapshot_id = StableId(self.report["snapshot_id"])
        self.scope_id = StableId(self.report["scope_id"])

    def _snapshot_members(
        self, connection: sqlite3.Connection, snapshot_id: StableId
    ) -> tuple[LegacySnapshotMember, ...]:
        rows = connection.execute(
            """SELECT kind, object_id, object_digest
               FROM knw_snapshot_members
               WHERE snapshot_id = ? ORDER BY kind, object_id""",
            (snapshot_id.value,),
        ).fetchall()
        return tuple(
            LegacySnapshotMember(
                kind=LegacyKnowledgeObjectKind(kind),
                object_id=StableId(object_id),
                object_digest=Digest(object_digest),
            )
            for kind, object_id, object_digest in rows
        )

    def _manifest_digest(
        self,
        *,
        snapshot_id: StableId,
        revision: int,
        previous_snapshot_id: StableId | None,
        members: tuple[LegacySnapshotMember, ...],
    ) -> Digest:
        return digest_of(
            {
                "snapshot_id": snapshot_id.value,
                "scope_id": self.scope_id.value,
                "snapshot_revision": revision,
                "previous_snapshot_id": (
                    previous_snapshot_id.value
                    if previous_snapshot_id is not None
                    else None
                ),
                "schema_version": "INITIAL@1",
                "schema_digest": LEGACY_SCHEMA_DIGEST,
                "members": members,
            }
        )

    def _insert_snapshot(
        self,
        connection: sqlite3.Connection,
        *,
        snapshot_id: StableId,
        revision: int,
        previous_snapshot_id: StableId | None,
        members: tuple[LegacySnapshotMember, ...],
    ) -> None:
        manifest_digest = self._manifest_digest(
            snapshot_id=snapshot_id,
            revision=revision,
            previous_snapshot_id=previous_snapshot_id,
            members=members,
        )
        connection.execute(
            "INSERT INTO knw_snapshots VALUES (?, ?, ?, ?, 'INITIAL@1', ?, ?)",
            (
                snapshot_id.value,
                self.scope_id.value,
                revision,
                (
                    previous_snapshot_id.value
                    if previous_snapshot_id is not None
                    else None
                ),
                manifest_digest.value,
                f"2026-08-10T00:00:00.{revision:06d}+00:00",
            ),
        )
        connection.executemany(
            "INSERT INTO knw_snapshot_members VALUES (?, ?, ?, ?)",
            (
                (
                    snapshot_id.value,
                    member.kind.value,
                    member.object_id.value,
                    member.object_digest.value,
                )
                for member in members
            ),
        )

    def _rewrite_fact_references(
        self,
        connection: sqlite3.Connection,
        references: tuple[StableId, ...],
    ) -> StableId:
        row = connection.execute(
            """SELECT fact_id, schema_version, subject_entity_id, predicate,
                      object_value, context_json, reviewed_grounding_json
               FROM knw_facts"""
        ).fetchone()
        (
            old_fact_id,
            schema_version,
            subject_entity_id,
            predicate,
            object_value,
            context_json,
            reviewed_grounding_json,
        ) = row
        self.assertIsNone(reviewed_grounding_json)
        context = KnowledgeContext.create(json.loads(context_json))
        reference_values = tuple(item.value for item in references)
        identity = digest_of(
            {
                "schema_version": schema_version,
                "subject_entity_id": subject_entity_id,
                "predicate": predicate,
                "object_value": object_value,
                "context_digest": context.digest.value,
                "evidence_references": reference_values,
                "reviewed_grounding_digest": None,
            }
        )
        fact_id = StableId("knowledge_fact_" + identity.value[-32:])
        object_digest = digest_of(
            {
                "fact_id": fact_id.value,
                "schema_version": schema_version,
                "subject_entity_id": subject_entity_id,
                "predicate": predicate,
                "object_value": object_value,
                "context": context,
                "evidence_references": reference_values,
                "reviewed_grounding_digest": None,
            }
        )
        connection.execute(
            """UPDATE knw_facts
               SET fact_id = ?, evidence_refs_json = ?, object_digest = ?
               WHERE fact_id = ?""",
            (
                fact_id.value,
                json.dumps(reference_values, separators=(",", ":")),
                object_digest.value,
                old_fact_id,
            ),
        )
        connection.execute(
            """UPDATE knw_snapshot_members
               SET object_id = ?, object_digest = ?
               WHERE snapshot_id = ? AND kind = 'FACT' AND object_id = ?""",
            (
                fact_id.value,
                object_digest.value,
                self.snapshot_id.value,
                old_fact_id,
            ),
        )
        members = self._snapshot_members(connection, self.snapshot_id)
        manifest_digest = self._manifest_digest(
            snapshot_id=self.snapshot_id,
            revision=1,
            previous_snapshot_id=None,
            members=members,
        )
        connection.execute(
            "UPDATE knw_snapshots SET manifest_digest = ? WHERE snapshot_id = ?",
            (manifest_digest.value, self.snapshot_id.value),
        )
        return fact_id

    def test_frozen_snapshot_and_records_match_report_without_mutating_artifact(self) -> None:
        digest_before = _sha256(DATABASE_PATH)
        stat_before = DATABASE_PATH.stat()
        directory_before = tuple(sorted(path.name for path in LEGACY_ROOT.iterdir()))

        reader = SqliteLegacyFormalReader(DATABASE_PATH)
        result = reader.read_snapshot(self.snapshot_id)
        current = reader.current_snapshot(self.scope_id)

        metadata = result.metadata
        self.assertEqual(metadata.snapshot_id.value, self.report["snapshot_id"])
        self.assertEqual(metadata.scope_id.value, self.report["scope_id"])
        self.assertEqual(
            metadata.snapshot_revision.value, self.report["snapshot_revision"]
        )
        self.assertIsNone(metadata.previous_snapshot_id)
        self.assertEqual(metadata.schema_version, self.report["schema_version"])
        self.assertEqual(metadata.manifest_digest.value, self.report["manifest_digest"])
        self.assertEqual(metadata.member_count, self.report["member_count"])
        self.assertEqual(current, metadata)

        actual_records = [
            {
                "kind": record.kind.value,
                "object_id": record.object_id.value,
                "object_digest": record.object_digest.value,
                "type_name": record.type_name,
                "text": record.text,
                "context_digest": record.context_digest.value,
                "support_references": [
                    reference.value for reference in record.support_references
                ],
                "source_locators": list(record.source_locators),
            }
            for record in result.records
        ]
        self.assertEqual(actual_records, self.report["records"])
        self.assertTrue(
            all(record.schema_version == "INITIAL@1" for record in result.records)
        )

        self.assertEqual(_sha256(DATABASE_PATH), digest_before)
        self.assertEqual(DATABASE_PATH.stat(), stat_before)
        self.assertEqual(
            tuple(sorted(path.name for path in LEGACY_ROOT.iterdir())),
            directory_before,
        )
        self.assertEqual(digest_before, self.report["database_sha256"])

    def test_query_is_manifest_bounded_and_resolves_all_legacy_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database_path = Path(temporary) / "legacy.sqlite3"
            shutil.copyfile(DATABASE_PATH, database_path)
            entity_id = self.report["records"][0]["object_id"]
            context = KnowledgeContext.create({})
            inference_identity = digest_of(
                {
                    "schema_version": "INITIAL@1",
                    "inference_type": "STRUCTURE",
                    "proposition": "Legacy service is declared",
                    "premises": (entity_id,),
                    "rule_ref": "legacy-rule",
                    "context_digest": context.digest.value,
                    "reviewed_need_ids": (),
                }
            )
            inference_id = "knowledge_inference_" + inference_identity.value[-32:]
            inference_digest = digest_of(
                {
                    "inference_id": inference_id,
                    "schema_version": "INITIAL@1",
                    "inference_type": "STRUCTURE",
                    "proposition": "Legacy service is declared",
                    "premises": (entity_id,),
                    "rule_ref": "legacy-rule",
                    "context": context,
                    "reviewed_need_ids": (),
                }
            )
            hidden_id = "knowledge_entity_00000000000000000000000000000003"
            hidden_digest = "sha256:" + "3" * 64
            with closing(sqlite3.connect(database_path)) as connection, connection:
                # The frozen artifact retains WAL as its historical journal
                # mode.  Switch only this disposable copy to DELETE so the
                # immutable reader sees the test mutation in the main file.
                connection.execute("PRAGMA journal_mode=DELETE")
                connection.execute(
                    """INSERT INTO knw_inferences (
                           inference_id, schema_version, inference_type,
                           proposition, premise_refs_json, rule_ref, context_json,
                           context_digest, reviewed_need_ids_json, object_digest
                       ) VALUES (?, 'INITIAL@1', 'STRUCTURE', ?, ?, 'legacy-rule',
                                 '{}', ?, '[]', ?)""",
                    (
                        inference_id,
                        "Legacy service is declared",
                        json.dumps([entity_id]),
                        context.digest.value,
                        inference_digest.value,
                    ),
                )
                connection.execute(
                    "INSERT INTO knw_snapshot_members VALUES (?, 'INFERENCE', ?, ?)",
                    (self.snapshot_id.value, inference_id, inference_digest.value),
                )
                members = tuple(
                    sorted(
                        (
                            *(
                                LegacySnapshotMember(
                                    kind=LegacyKnowledgeObjectKind(record["kind"]),
                                    object_id=StableId(record["object_id"]),
                                    object_digest=Digest(record["object_digest"]),
                                )
                                for record in self.report["records"]
                            ),
                            LegacySnapshotMember(
                                kind=LegacyKnowledgeObjectKind.INFERENCE,
                                object_id=StableId(inference_id),
                                object_digest=inference_digest,
                            ),
                        ),
                        key=lambda item: (item.kind.value, item.object_id.value),
                    )
                )
                manifest_digest = digest_of(
                    {
                        "snapshot_id": self.snapshot_id.value,
                        "scope_id": self.scope_id.value,
                        "snapshot_revision": self.report["snapshot_revision"],
                        "previous_snapshot_id": None,
                        "schema_version": "INITIAL@1",
                        "schema_digest": (
                            "sha256:75e96739d6b05aca368d5be4fcfb84eddf8fbbb996e65e9ba9f6738562a4e436"
                        ),
                        "members": members,
                    }
                )
                connection.execute(
                    "UPDATE knw_snapshots SET manifest_digest = ? WHERE snapshot_id = ?",
                    (manifest_digest.value, self.snapshot_id.value),
                )
                # This valid-looking object is deliberately not in the exact
                # manifest and therefore must never appear in the query.
                connection.execute(
                    """INSERT INTO knw_entities VALUES (
                           ?, 'INITIAL@1', 'CODE_SYMBOL', 'Hidden', 'Hidden',
                           '{}', ?, '[]', ?
                       )""",
                    (hidden_id, context.digest.value, hidden_digest),
                )

            reader = SqliteLegacyFormalReader(database_path)
            records = reader.query_snapshot(self.snapshot_id)

            self.assertEqual(
                tuple(record.kind for record in records),
                (
                    LegacyKnowledgeObjectKind.ENTITY,
                    LegacyKnowledgeObjectKind.FACT,
                    LegacyKnowledgeObjectKind.INFERENCE,
                ),
            )
            inference = records[-1]
            self.assertEqual(inference.object_id.value, inference_id)
            self.assertEqual(inference.type_name, "STRUCTURE")
            self.assertEqual(inference.text, "Legacy service is declared")
            self.assertEqual(
                tuple(item.value for item in inference.support_references),
                (entity_id,),
            )
            self.assertEqual(
                inference.source_locators,
                ("src/LegacyOrderService.java:1",),
            )
            self.assertNotIn(hidden_id, {record.object_id.value for record in records})
            self.assertEqual(
                reader.query_snapshot(
                    self.snapshot_id,
                    kinds=(LegacyKnowledgeObjectKind.INFERENCE,),
                ),
                (inference,),
            )

    def test_reader_uses_only_selects_over_read_only_immutable_uri(self) -> None:
        statements: list[str] = []
        calls: list[tuple[str, bool]] = []
        real_connect = sqlite3.connect

        def traced_connect(database: str, *args: object, **kwargs: object):
            calls.append((database, kwargs.get("uri") is True))
            connection = real_connect(database, *args, **kwargs)
            connection.set_trace_callback(statements.append)
            return connection

        with patch(
            "software_world_model.infrastructure.sqlite_legacy_formal_reader.sqlite3.connect",
            side_effect=traced_connect,
        ):
            SqliteLegacyFormalReader(DATABASE_PATH).read_snapshot(self.snapshot_id)

        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0][0].startswith("file:"))
        self.assertIn("mode=ro", calls[0][0])
        self.assertIn("immutable=1", calls[0][0])
        self.assertTrue(calls[0][1])
        self.assertTrue(statements)
        self.assertTrue(
            all(statement.lstrip().upper().startswith("SELECT") for statement in statements),
            statements,
        )

    def test_missing_snapshot_record_and_table_fail_closed(self) -> None:
        reader = SqliteLegacyFormalReader(DATABASE_PATH)
        with self.assertRaises(DomainError) as snapshot_error:
            reader.get_snapshot(
                StableId("knowledge_snapshot_000000000000000000000000000000ff")
            )
        self.assertEqual(snapshot_error.exception.code, ErrorCode.INVALID_ARGUMENT)

        for mutation in ("missing-record", "missing-manifest-member", "missing-table"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                database_path = Path(temporary) / "legacy.sqlite3"
                shutil.copyfile(DATABASE_PATH, database_path)
                with closing(sqlite3.connect(database_path)) as connection, connection:
                    connection.execute("PRAGMA journal_mode=DELETE")
                    if mutation == "missing-record":
                        connection.execute(
                            "DELETE FROM knw_entities WHERE entity_id = ?",
                            (self.report["records"][0]["object_id"],),
                        )
                    elif mutation == "missing-manifest-member":
                        connection.execute(
                            """DELETE FROM knw_snapshot_members
                               WHERE snapshot_id = ? AND object_id = ?""",
                            (
                                self.snapshot_id.value,
                                self.report["records"][0]["object_id"],
                            ),
                        )
                    else:
                        connection.execute("DROP TABLE knw_inferences")

                with self.assertRaises(DomainError) as failure:
                    SqliteLegacyFormalReader(database_path).read_snapshot(
                        self.snapshot_id
                    )
                self.assertEqual(
                    failure.exception.code,
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                )

    def test_tampered_record_or_evidence_content_fails_closed(self) -> None:
        mutations = (
            ("entity-label", "UPDATE knw_entities SET label = label || ' tampered'"),
            (
                "evidence-locator",
                "UPDATE knw_evidence SET locator = locator || ':tampered'",
            ),
            (
                "evidence-excerpt",
                "UPDATE knw_evidence SET excerpt = 'X' || substr(excerpt, 2)",
            ),
        )
        for name, statement in mutations:
            with self.subTest(mutation=name), tempfile.TemporaryDirectory() as temporary:
                database_path = Path(temporary) / "legacy.sqlite3"
                shutil.copyfile(DATABASE_PATH, database_path)
                with closing(sqlite3.connect(database_path)) as connection, connection:
                    connection.execute("PRAGMA journal_mode=DELETE")
                    connection.execute(statement)

                with self.assertRaises(DomainError) as failure:
                    SqliteLegacyFormalReader(database_path).read_snapshot(
                        self.snapshot_id
                    )
                self.assertEqual(
                    failure.exception.code,
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                )

    def test_entity_or_fact_support_cannot_masquerade_as_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database_path = Path(temporary) / "legacy.sqlite3"
            shutil.copyfile(DATABASE_PATH, database_path)
            entity_id = StableId(self.report["records"][0]["object_id"])
            with closing(sqlite3.connect(database_path)) as connection, connection:
                connection.execute("PRAGMA journal_mode=DELETE")
                self._rewrite_fact_references(connection, (entity_id,))

            with self.assertRaises(DomainError) as failure:
                SqliteLegacyFormalReader(database_path).read_snapshot(
                    self.snapshot_id
                )
            self.assertEqual(
                failure.exception.code,
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            )

    def test_duplicate_legacy_support_references_remain_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database_path = Path(temporary) / "legacy.sqlite3"
            shutil.copyfile(DATABASE_PATH, database_path)
            evidence_id = StableId(
                self.report["records"][0]["support_references"][0]
            )
            with closing(sqlite3.connect(database_path)) as connection, connection:
                connection.execute("PRAGMA journal_mode=DELETE")
                fact_id = self._rewrite_fact_references(
                    connection, (evidence_id, evidence_id)
                )

            fact = SqliteLegacyFormalReader(database_path).get_record(
                self.snapshot_id, fact_id
            )
            self.assertEqual(
                fact.support_references,
                (evidence_id, evidence_id),
            )
            self.assertEqual(
                fact.source_locators,
                ("src/LegacyOrderService.java:1",),
            )

    def test_snapshot_predecessor_chain_and_additive_membership_are_verified(self) -> None:
        successor_id = StableId(
            "knowledge_snapshot_00000000000000000000000000000002"
        )
        with tempfile.TemporaryDirectory() as temporary:
            database_path = Path(temporary) / "valid-successor.sqlite3"
            shutil.copyfile(DATABASE_PATH, database_path)
            with closing(sqlite3.connect(database_path)) as connection, connection:
                connection.execute("PRAGMA journal_mode=DELETE")
                members = self._snapshot_members(connection, self.snapshot_id)
                self._insert_snapshot(
                    connection,
                    snapshot_id=successor_id,
                    revision=2,
                    previous_snapshot_id=self.snapshot_id,
                    members=members,
                )
            successor = SqliteLegacyFormalReader(database_path).read_snapshot(
                successor_id
            )
            self.assertEqual(successor.metadata.previous_snapshot_id, self.snapshot_id)
            self.assertEqual(successor.metadata.snapshot_revision, Revision(2))

        for mutation in (
            "revision-one-self-cycle",
            "missing-predecessor",
            "non-consecutive-predecessor",
            "predecessor-member-loss",
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                database_path = Path(temporary) / "invalid-chain.sqlite3"
                shutil.copyfile(DATABASE_PATH, database_path)
                target_snapshot_id = successor_id
                with closing(sqlite3.connect(database_path)) as connection, connection:
                    connection.execute("PRAGMA journal_mode=DELETE")
                    members = self._snapshot_members(connection, self.snapshot_id)
                    if mutation == "revision-one-self-cycle":
                        target_snapshot_id = self.snapshot_id
                        manifest = self._manifest_digest(
                            snapshot_id=self.snapshot_id,
                            revision=1,
                            previous_snapshot_id=self.snapshot_id,
                            members=members,
                        )
                        connection.execute(
                            """UPDATE knw_snapshots
                               SET previous_snapshot_id = ?, manifest_digest = ?
                               WHERE snapshot_id = ?""",
                            (
                                self.snapshot_id.value,
                                manifest.value,
                                self.snapshot_id.value,
                            ),
                        )
                    elif mutation == "missing-predecessor":
                        self._insert_snapshot(
                            connection,
                            snapshot_id=successor_id,
                            revision=2,
                            previous_snapshot_id=StableId(
                                "knowledge_snapshot_ffffffffffffffffffffffffffffffff"
                            ),
                            members=members,
                        )
                    elif mutation == "non-consecutive-predecessor":
                        target_snapshot_id = StableId(
                            "knowledge_snapshot_00000000000000000000000000000003"
                        )
                        self._insert_snapshot(
                            connection,
                            snapshot_id=target_snapshot_id,
                            revision=3,
                            previous_snapshot_id=self.snapshot_id,
                            members=members,
                        )
                    else:
                        self._insert_snapshot(
                            connection,
                            snapshot_id=successor_id,
                            revision=2,
                            previous_snapshot_id=self.snapshot_id,
                            members=members[:1],
                        )

                with self.assertRaises(DomainError) as failure:
                    SqliteLegacyFormalReader(database_path).read_snapshot(
                        target_snapshot_id
                    )
                self.assertEqual(
                    failure.exception.code,
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                )


if __name__ == "__main__":
    unittest.main()
