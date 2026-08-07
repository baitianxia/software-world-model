from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from swm_demo.application import ApplicationError, ApplicationServices
from swm_demo.knowledge_engine import KnowledgeEngine


WORKSPACE = Path(__file__).resolve().parents[2]
MALL_REPOSITORY = WORKSPACE / "validation-projects" / "mall"
MALL_REVISION = "0504e86b1f1b6f1b8aa6a734d37a90fb67346be7"
SCOPE_ID = "system:mall"


class _RejectingVerifier:
    def verify(self, collection, entities, evidence, candidates):
        return ("forced admission rejection",)


class StructureSliceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary.name) / "validation.sqlite3"
        self.services: ApplicationServices | None = ApplicationServices(self.database)
        self.services.configure_scope(
            scope_id=SCOPE_ID,
            name="mall",
            source_path=MALL_REPOSITORY,
            expected_revision=MALL_REVISION,
        )

    def tearDown(self) -> None:
        if self.services is not None:
            self.services.close()
        self.temporary.cleanup()

    def test_real_project_matches_slice_one_baseline(self) -> None:
        result = self.services.update_knowledge(SCOPE_ID)
        self.assertEqual(9, result["artifact_count"])
        self.assertEqual(8, result["entity_count"])
        self.assertEqual(22, result["evidence_count"])
        self.assertEqual(15, result["fact_count"])

        view = self.services.query_structure(SCOPE_ID)
        self.assertEqual(MALL_REVISION, view["revision"])
        self.assertEqual(1, len(view["roots"]))
        self.assertEqual("mall", view["roots"][0]["name"])
        self.assertEqual(7, len(view["modules"]))
        self.assertEqual(8, len(view["dependencies"]))
        self.assertTrue(
            all(module["evidence_count"] == 2 for module in view["modules"])
        )

    def test_fact_can_be_explained_to_exact_source_lines(self) -> None:
        self.services.update_knowledge(SCOPE_ID)
        view = self.services.query_structure(SCOPE_ID)
        dependency = next(
            edge
            for edge in view["dependencies"]
            if edge["source"] == "mall-admin" and edge["target"] == "mall-security"
        )

        explanation = self.services.explain_fact(
            SCOPE_ID, str(dependency["fact_id"])
        )
        self.assertEqual("DEPENDS_ON", explanation["predicate"])
        self.assertEqual("mall-admin", explanation["subject_name"])
        self.assertEqual("mall-security", explanation["object_name"])
        self.assertEqual(1, len(explanation["evidence"]))
        observation = explanation["evidence"][0]
        self.assertEqual("mall-admin/pom.xml", observation["relative_path"])
        self.assertEqual(MALL_REVISION, observation["revision"])
        self.assertEqual(
            "<artifactId>mall-security</artifactId>", observation["quote"]
        )
        self.assertTrue(observation["quote_hash"])
        self.assertTrue(observation["artifact_content_hash"])

    def test_repeated_build_keeps_entity_and_fact_identity_stable(self) -> None:
        first = self.services.update_knowledge(SCOPE_ID)
        first_view = self.services.query_structure(SCOPE_ID)
        first_entities = {
            item["entity_id"]
            for item in [*first_view["roots"], *first_view["modules"]]
        }
        first_facts = {
            item["fact_id"]
            for item in [*first_view["modules"], *first_view["dependencies"]]
        }

        second = self.services.update_knowledge(SCOPE_ID)
        second_view = self.services.query_structure(SCOPE_ID)
        second_entities = {
            item["entity_id"]
            for item in [*second_view["roots"], *second_view["modules"]]
        }
        second_facts = {
            item["fact_id"]
            for item in [*second_view["modules"], *second_view["dependencies"]]
        }

        self.assertNotEqual(first["snapshot_id"], second["snapshot_id"])
        self.assertEqual(first_entities, second_entities)
        self.assertEqual(first_facts, second_facts)

    def test_admission_failure_keeps_previous_snapshot_current(self) -> None:
        first = self.services.update_knowledge(SCOPE_ID)
        self.services.close()
        self.services = None

        rejecting_engine = KnowledgeEngine(verifier=_RejectingVerifier())
        failing_services = ApplicationServices(
            self.database, knowledge_engine=rejecting_engine
        )
        try:
            with self.assertRaisesRegex(ApplicationError, "forced admission rejection"):
                failing_services.update_knowledge(SCOPE_ID)
            current = failing_services.current_snapshot(SCOPE_ID)
            self.assertEqual(first["snapshot_id"], current["snapshot_id"])
            view = failing_services.query_structure(SCOPE_ID)
            self.assertEqual(7, len(view["modules"]))
        finally:
            failing_services.close()

    def test_static_module_dependencies_follow_architecture(self) -> None:
        package = WORKSPACE / "demo" / "swm_demo"
        semantic_view = (package / "semantic_view.py").read_text(encoding="utf-8")
        knowledge_engine = (package / "knowledge_engine.py").read_text(
            encoding="utf-8"
        )
        source_integration = (package / "source_integration.py").read_text(
            encoding="utf-8"
        )
        application = (package / "application.py").read_text(encoding="utf-8")

        self.assertNotIn("swm_demo.storage", semantic_view)
        self.assertNotIn("swm_demo.source_integration", knowledge_engine)
        self.assertNotIn("swm_demo.storage", knowledge_engine)
        self.assertNotIn("swm_demo.knowledge_engine", source_integration)
        self.assertNotIn("LocalGitConnector", application)


if __name__ == "__main__":
    unittest.main()
