from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from swm_demo.artifact_contract import SourceArtifact, SourceCollection
from swm_demo.ids import content_hash, stable_id
from swm_demo.knowledge_contract import (
    Evidence,
    FactCandidate,
    KnowledgeEntity,
)
from swm_demo.knowledge_engine import KnowledgeEngine
from swm_demo.knowledge_update import CandidateBundle
from swm_demo.storage import SQLiteKnowledgeStore


SCOPE_ID = "system:model-fact-admission"
SOURCE_ID = "source:model-fact-admission"
REVISION = "revision:1"
DIRECT_PROPOSITION = "service calls repository.save"


class ModelProposedFactAdmissionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.store = SQLiteKnowledgeStore(
            Path(self.temporary.name) / "model-fact-admission.sqlite3"
        )
        self.engine = KnowledgeEngine(repository=self.store)
        self.engine.configure_scope(SCOPE_ID, "model Fact admission")
        self.collection = self._collection()

        baseline_snapshot_id = self.engine.begin_update(SCOPE_ID, REVISION)
        self.store.save_source_artifacts(baseline_snapshot_id, self.collection)
        baseline = self.engine.admit_and_publish(
            baseline_snapshot_id, self.collection
        )
        self.assertEqual((), baseline.errors)
        self.baseline_snapshot_id = baseline_snapshot_id

    def tearDown(self) -> None:
        self.store.close()
        self.temporary.cleanup()

    def test_model_fact_beyond_evidence_is_rejected_without_replacing_snapshot(
        self,
    ) -> None:
        candidate_snapshot_id = self.engine.begin_update(SCOPE_ID, REVISION)
        self.store.save_source_artifacts(candidate_snapshot_id, self.collection)

        build = self.engine.admit_and_publish(
            candidate_snapshot_id,
            self.collection,
            candidate_bundle=self._bundle(
                "The service persists the value transactionally."
            ),
        )

        self.assertIsNone(build.package)
        self.assertTrue(
            any(
                "not directly present in its Evidence" in error
                for error in build.errors
            )
        )
        self.assertEqual(
            self.baseline_snapshot_id,
            self.engine.current_snapshot(SCOPE_ID)["snapshot_id"],
        )
        failed = self.store.connection.execute(
            "SELECT status FROM snapshots WHERE snapshot_id = ?",
            (candidate_snapshot_id,),
        ).fetchone()
        self.assertEqual("FAILED", failed["status"])
        self.assertEqual([], self.engine.read_facts(SCOPE_ID))

    def test_model_fact_literal_in_its_evidence_is_admitted(self) -> None:
        candidate_snapshot_id = self.engine.begin_update(SCOPE_ID, REVISION)
        self.store.save_source_artifacts(candidate_snapshot_id, self.collection)
        bundle = self._bundle(DIRECT_PROPOSITION)

        build = self.engine.admit_and_publish(
            candidate_snapshot_id,
            self.collection,
            candidate_bundle=bundle,
        )

        self.assertEqual((), build.errors)
        self.assertIsNotNone(build.package)
        self.assertEqual(
            candidate_snapshot_id,
            self.engine.current_snapshot(SCOPE_ID)["snapshot_id"],
        )
        admitted = self.engine.read_facts(SCOPE_ID)
        proposed = next(
            item for item in admitted if item["model_call_id"] == "model-call:proposal"
        )
        self.assertEqual(DIRECT_PROPOSITION, proposed["proposition"])

    @staticmethod
    def _collection() -> SourceCollection:
        root_pom = """<project>
  <modelVersion>4.0.0</modelVersion>
  <artifactId>model-fact-admission</artifactId>
</project>
"""
        observation = DIRECT_PROPOSITION + "\n"
        artifacts = (
            ModelProposedFactAdmissionTest._artifact(
                "pom.xml", "maven-pom", root_pom
            ),
            ModelProposedFactAdmissionTest._artifact(
                "observation.txt", "source-text", observation
            ),
        )
        return SourceCollection(
            source_id=SOURCE_ID,
            scope_id=SCOPE_ID,
            revision=REVISION,
            artifacts=artifacts,
            build_profile="structure-core",
        )

    @staticmethod
    def _artifact(
        relative_path: str, artifact_type: str, content: str
    ) -> SourceArtifact:
        digest = content_hash(content)
        return SourceArtifact(
            artifact_id=stable_id(
                "artifact", SCOPE_ID, relative_path, REVISION, digest
            ),
            artifact_type=artifact_type,
            source_id=SOURCE_ID,
            scope_id=SCOPE_ID,
            relative_path=relative_path,
            revision=REVISION,
            content_hash=digest,
            content=content,
        )

    def _bundle(self, proposition: str) -> CandidateBundle:
        artifact = next(
            item
            for item in self.collection.artifacts
            if item.relative_path == "observation.txt"
        )
        subject = KnowledgeEntity(
            entity_id=stable_id("entity", SCOPE_ID, "service", "ExampleService"),
            scope_id=SCOPE_ID,
            entity_type="service",
            name="ExampleService",
        )
        object_ = KnowledgeEntity(
            entity_id=stable_id("entity", SCOPE_ID, "operation", "repository.save"),
            scope_id=SCOPE_ID,
            entity_type="operation",
            name="repository.save",
        )
        quote_digest = content_hash(DIRECT_PROPOSITION)
        evidence = Evidence(
            evidence_id=stable_id(
                "evidence", artifact.artifact_id, 1, 1, quote_digest
            ),
            artifact_id=artifact.artifact_id,
            scope_id=SCOPE_ID,
            revision=REVISION,
            line_start=1,
            line_end=1,
            quote=DIRECT_PROPOSITION,
            quote_hash=quote_digest,
        )
        fact = FactCandidate(
            fact_id=stable_id(
                "fact",
                SCOPE_ID,
                subject.entity_id,
                "CALLS_OPERATION",
                object_.entity_id,
                proposition,
            ),
            scope_id=SCOPE_ID,
            revision=REVISION,
            subject_id=subject.entity_id,
            predicate="CALLS_OPERATION",
            object_id=object_.entity_id,
            evidence_ids=(evidence.evidence_id,),
            proposition=proposition,
            model_call_id="model-call:proposal",
        )
        return CandidateBundle(
            bundle_id=stable_id("bundle", proposition),
            intent_id="intent:model-fact-admission",
            scope_id=SCOPE_ID,
            source_artifact_ids=(artifact.artifact_id,),
            entities=(subject, object_),
            evidence=(evidence,),
            fact_candidates=(fact,),
            inference_candidates=(),
            covered_need_ids=("need:model-fact-admission",),
            unresolved_need_ids=(),
            proposal_model_call_id="model-call:proposal",
        )


if __name__ == "__main__":
    unittest.main()
