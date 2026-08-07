from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from swm_demo.application import ApplicationError, ApplicationServices
from swm_demo.artifact_contract import SourceArtifact, SourceCollection
from swm_demo.cli import parser
from swm_demo.ids import content_hash, stable_id
from swm_demo.knowledge_contract import (
    Evidence,
    FormalFact,
    FormalInference,
    KnowledgeEntity,
    KnowledgePackage,
)
from swm_demo.storage import KnowledgeStoreError


SCOPE_ID = "system:generic-tools"


class GenericFormalKnowledgeToolsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        database = Path(self.temporary.name) / "generic-tools.sqlite3"
        self.services = ApplicationServices(database)
        self._publish("revision:one")

    def tearDown(self) -> None:
        self.services.close()
        self.temporary.cleanup()

    def _publish(self, revision: str) -> None:
        self.services.store.upsert_scope(SCOPE_ID, "generic tools")
        artifact_content = "Alpha#run invokes Beta#save"
        artifact = SourceArtifact(
            artifact_id=stable_id("artifact", SCOPE_ID, revision),
            artifact_type="source-text",
            source_id="source:fixture",
            scope_id=SCOPE_ID,
            relative_path="src/Alpha.java",
            revision=revision,
            content_hash=content_hash(artifact_content),
            content=artifact_content,
        )
        collection = SourceCollection(
            source_id=artifact.source_id,
            scope_id=SCOPE_ID,
            revision=revision,
            artifacts=(artifact,),
        )
        alpha = KnowledgeEntity(
            entity_id="entity:alpha",
            scope_id=SCOPE_ID,
            entity_type="java-method",
            name="Alpha#run",
        )
        alpha_helper = KnowledgeEntity(
            entity_id="entity:alpha-helper",
            scope_id=SCOPE_ID,
            entity_type="java-method",
            name="AlphaHelper#run",
        )
        beta = KnowledgeEntity(
            entity_id="entity:beta",
            scope_id=SCOPE_ID,
            entity_type="java-method",
            name="Beta#save",
        )
        observation = Evidence(
            evidence_id=stable_id("evidence", artifact.artifact_id, 1),
            artifact_id=artifact.artifact_id,
            scope_id=SCOPE_ID,
            revision=revision,
            line_start=1,
            line_end=1,
            quote=artifact_content,
            quote_hash=content_hash(artifact_content),
        )
        fact = FormalFact(
            fact_id="fact:alpha-calls-beta",
            scope_id=SCOPE_ID,
            revision=revision,
            subject_id=alpha.entity_id,
            predicate="CALLS",
            object_id=beta.entity_id,
            evidence_ids=(observation.evidence_id,),
            proposition="Alpha#run calls Beta#save.",
        )
        reverse_fact = FormalFact(
            fact_id="fact:beta-calls-alpha",
            scope_id=SCOPE_ID,
            revision=revision,
            subject_id=beta.entity_id,
            predicate="CALLS",
            object_id=alpha.entity_id,
            evidence_ids=(observation.evidence_id,),
            proposition="Beta#save calls Alpha#run.",
        )
        primary = FormalInference(
            inference_id="inference:primary",
            scope_id=SCOPE_ID,
            revision=revision,
            inference_type="BEHAVIOR_FLOW",
            statement="Alpha#run invokes Beta#save.",
            support_fact_ids=(fact.fact_id,),
        )
        secondary = FormalInference(
            inference_id="inference:secondary",
            scope_id=SCOPE_ID,
            revision=revision,
            inference_type="BEHAVIOR_FLOW",
            statement="The flow invokes one persistence method.",
            support_fact_ids=(fact.fact_id,),
            dependency_inference_ids=(primary.inference_id,),
        )
        snapshot_id = self.services.store.start_snapshot(SCOPE_ID, revision)
        self.services.store.save_source_artifacts(snapshot_id, collection)
        self.services.store.publish_knowledge(
            snapshot_id,
            KnowledgePackage(
                scope_id=SCOPE_ID,
                revision=revision,
                entities=(alpha, alpha_helper, beta),
                evidence=(observation,),
                facts=(fact, reverse_fact),
                inferences=(primary, secondary),
            ),
        )

    def test_context_declares_schema_semantics_limits_and_unknown_coverage(self) -> None:
        context = self.services.open_knowledge_context(SCOPE_ID)

        self.assertEqual(context["snapshot_id"], context["snapshot_token"])
        self.assertEqual("1.1", context["knowledge_schema_version"])
        self.assertEqual("UNDECLARED", context["coverage"]["status"])
        self.assertEqual(1, context["query_contract"]["neighborhood_depth"])
        self.assertIn("Evidence", context["schema"])
        calls = next(
            item
            for item in context["catalog"]["predicates"]
            if item["predicate"] == "CALLS"
        )
        self.assertEqual("DECLARED", calls["semantic_status"])
        self.assertIn("resolved", calls["meaning"])

    def test_open_context_rejects_a_snapshot_from_an_older_knowledge_schema(
        self,
    ) -> None:
        snapshot = self.services.current_snapshot(SCOPE_ID)
        with self.services.store.connection:
            self.services.store.connection.execute(
                """
                UPDATE snapshots SET knowledge_schema_version = '1.0'
                WHERE snapshot_id = ?
                """,
                (snapshot["snapshot_id"],),
            )

        with self.assertRaisesRegex(
            Exception, "INCOMPATIBLE_KNOWLEDGE_SCHEMA"
        ):
            self.services.open_knowledge_context(SCOPE_ID)

    def test_enrichment_cannot_inherit_an_older_knowledge_schema(self) -> None:
        base = self.services.current_snapshot(SCOPE_ID)
        with self.services.store.connection:
            self.services.store.connection.execute(
                """
                UPDATE snapshots SET knowledge_schema_version = '1.0'
                WHERE snapshot_id = ?
                """,
                (base["snapshot_id"],),
            )
        candidate = self.services.store.start_snapshot(
            SCOPE_ID, str(base["revision"])
        )

        with self.assertRaisesRegex(
            KnowledgeStoreError, "Base and target context differ"
        ):
            self.services.store.publish_knowledge(
                candidate,
                KnowledgePackage(
                    scope_id=SCOPE_ID,
                    revision=str(base["revision"]),
                    entities=(),
                    evidence=(),
                    facts=(),
                    inferences=(),
                ),
                base_snapshot_id=str(base["snapshot_id"]),
            )

    def test_entity_and_inference_search_are_bounded_and_stably_sorted(self) -> None:
        token = self.services.open_knowledge_context(SCOPE_ID)["snapshot_token"]
        exact = self.services.search_knowledge(
            SCOPE_ID,
            str(token),
            "ENTITY",
            "Alpha#run",
            "EXACT",
            "java-method",
        )
        self.assertEqual(["entity:alpha"], [item["entity_id"] for item in exact["items"]])

        contains = self.services.search_knowledge(
            SCOPE_ID, str(token), "ENTITY", "Alpha", "CONTAINS"
        )
        self.assertEqual(
            ["Alpha#run", "AlphaHelper#run"],
            [item["name"] for item in contains["items"]],
        )
        inferred = self.services.search_knowledge(
            SCOPE_ID, str(token), "INFERENCE", "invokes", "CONTAINS"
        )
        self.assertEqual(
            ["inference:primary", "inference:secondary"],
            sorted(item["inference_id"] for item in inferred["items"]),
        )
        with self.assertRaisesRegex(ApplicationError, "between 1 and 100"):
            self.services.search_knowledge(
                SCOPE_ID, str(token), "ENTITY", "Alpha", limit=101
            )

    def test_search_cursor_continues_after_a_bounded_page(self) -> None:
        token = str(self.services.open_knowledge_context(SCOPE_ID)["snapshot_token"])
        first = self.services.search_knowledge(
            SCOPE_ID, token, "ENTITY", "Alpha", limit=1
        )

        self.assertEqual(["entity:alpha"], [item["entity_id"] for item in first["items"]])
        self.assertTrue(first["has_more"])
        self.assertEqual(1, first["next_cursor"])
        self.assertTrue(first["limit_reached"])

        second = self.services.search_knowledge(
            SCOPE_ID,
            token,
            "ENTITY",
            "Alpha",
            limit=1,
            cursor=int(first["next_cursor"]),
        )
        self.assertEqual(
            ["entity:alpha-helper"],
            [item["entity_id"] for item in second["items"]],
        )
        self.assertFalse(second["has_more"])
        self.assertIsNone(second["next_cursor"])
        self.assertTrue(second["limit_reached"])

        inference_first = self.services.search_knowledge(
            SCOPE_ID, token, "INFERENCE", "invokes", limit=1
        )
        inference_second = self.services.search_knowledge(
            SCOPE_ID,
            token,
            "INFERENCE",
            "invokes",
            limit=1,
            cursor=int(inference_first["next_cursor"]),
        )
        self.assertEqual(
            ["inference:primary", "inference:secondary"],
            [
                inference_first["items"][0]["inference_id"],
                inference_second["items"][0]["inference_id"],
            ],
        )
        self.assertFalse(inference_second["has_more"])

        with self.assertRaisesRegex(ApplicationError, "non-negative integer"):
            self.services.search_knowledge(
                SCOPE_ID, token, "ENTITY", "Alpha", cursor=-1
            )
        with self.assertRaisesRegex(ApplicationError, "non-negative integer"):
            self.services.search_knowledge(
                SCOPE_ID, token, "ENTITY", "Alpha", cursor=1.5  # type: ignore[arg-type]
            )

    def test_one_hop_neighborhood_and_batch_explain_read_only_formal_knowledge(self) -> None:
        token = str(
            self.services.open_knowledge_context(SCOPE_ID)["snapshot_token"]
        )
        neighborhood = self.services.query_knowledge_neighborhood(
            SCOPE_ID,
            token,
            ("entity:alpha",),
            direction="OUTGOING",
            predicates=("CALLS",),
        )
        self.assertEqual(1, neighborhood["depth"])
        self.assertEqual(
            ["fact:alpha-calls-beta"],
            [item["fact_id"] for item in neighborhood["facts"]],
        )
        self.assertEqual(
            "DECLARED", neighborhood["predicate_semantics"][0]["semantic_status"]
        )

        explained = self.services.explain_knowledge_batch(
            SCOPE_ID,
            token,
            "FACT",
            ("fact:missing", "fact:alpha-calls-beta"),
        )
        self.assertEqual(["fact:missing"], explained["missing_ids"])
        self.assertEqual("Alpha#run calls Beta#save.", explained["items"][0]["proposition"])
        self.assertEqual("src/Alpha.java", explained["items"][0]["evidence"][0]["relative_path"])
        self.assertNotIn("content", explained["items"][0]["evidence"][0])
        self.assertNotIn("quote", explained["items"][0]["evidence"][0])

        inference = self.services.explain_knowledge_batch(
            SCOPE_ID,
            token,
            "INFERENCE",
            ("inference:secondary", "inference:primary"),
        )
        self.assertEqual(
            ["inference:primary", "inference:secondary"],
            [item["inference_id"] for item in inference["items"]],
        )
        self.assertEqual(
            ["inference:primary"],
            inference["items"][1]["dependency_inference_ids"],
        )

    def test_neighborhood_cursor_continues_in_stable_fact_order(self) -> None:
        token = str(self.services.open_knowledge_context(SCOPE_ID)["snapshot_token"])
        first = self.services.query_knowledge_neighborhood(
            SCOPE_ID,
            token,
            ("entity:alpha",),
            predicates=("CALLS",),
            limit=1,
        )

        self.assertEqual(
            ["fact:alpha-calls-beta"],
            [item["fact_id"] for item in first["facts"]],
        )
        self.assertTrue(first["has_more"])
        self.assertEqual(1, first["next_cursor"])

        second = self.services.query_knowledge_neighborhood(
            SCOPE_ID,
            token,
            ("entity:alpha",),
            predicates=("CALLS",),
            limit=1,
            cursor=int(first["next_cursor"]),
        )
        self.assertEqual(
            ["fact:beta-calls-alpha"],
            [item["fact_id"] for item in second["facts"]],
        )
        self.assertFalse(second["has_more"])
        self.assertIsNone(second["next_cursor"])

        with self.assertRaisesRegex(ApplicationError, "non-negative integer"):
            self.services.query_knowledge_neighborhood(
                SCOPE_ID,
                token,
                ("entity:alpha",),
                cursor=True,  # type: ignore[arg-type]
            )

    def test_open_context_rechecks_current_snapshot_after_catalog_read(self) -> None:
        original_catalog = self.services.store.formal_knowledge_catalog

        def catalog_then_publish(
            scope_id: str, snapshot_token: str
        ) -> dict[str, list[dict[str, object]]]:
            catalog = original_catalog(scope_id, snapshot_token)
            self._publish("revision:two")
            return catalog

        with patch.object(
            self.services.store,
            "formal_knowledge_catalog",
            side_effect=catalog_then_publish,
        ):
            with self.assertRaisesRegex(ApplicationError, "STALE_CONTEXT"):
                self.services.open_knowledge_context(SCOPE_ID)

    def test_superseded_token_is_rejected_as_stale_context(self) -> None:
        old_token = str(
            self.services.open_knowledge_context(SCOPE_ID)["snapshot_token"]
        )
        self._publish("revision:two")

        with self.assertRaisesRegex(ApplicationError, "STALE_CONTEXT"):
            self.services.search_knowledge(
                SCOPE_ID, old_token, "ENTITY", "Alpha", "CONTAINS"
            )

    def test_cli_exposes_four_composable_tool_classes(self) -> None:
        arguments = parser().parse_args(
            [
                "knowledge-search",
                "--scope",
                SCOPE_ID,
                "--context",
                "snapshot:test",
                "--kind",
                "entity",
                "--query",
                "Alpha",
            ]
        )
        self.assertEqual("knowledge-search", arguments.command)
        self.assertEqual("ENTITY", arguments.kind)
        self.assertEqual(0, arguments.cursor)

        neighborhood = parser().parse_args(
            [
                "knowledge-neighborhood",
                "--scope",
                SCOPE_ID,
                "--context",
                "snapshot:test",
                "--entity",
                "entity:alpha",
                "--cursor",
                "7",
            ]
        )
        self.assertEqual(7, neighborhood.cursor)


if __name__ == "__main__":
    unittest.main()
