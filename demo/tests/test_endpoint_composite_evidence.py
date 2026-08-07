from __future__ import annotations

import unittest

from swm_demo.artifact_contract import SourceArtifact, SourceCollection
from swm_demo.extended_knowledge import ExtendedKnowledgeBuilder
from swm_demo.ids import content_hash, stable_id
from swm_demo.java_artifact_processor import JavaArtifactProcessor


SCOPE_ID = "system:endpoint-evidence-test"
SOURCE_ID = "source:endpoint-evidence-test"
REVISION = "revision-1"


def _build_endpoint_knowledge(source_text: str):
    digest = content_hash(source_text)
    source = SourceArtifact(
        artifact_id=stable_id("artifact", SCOPE_ID, "DemoController.java", digest),
        artifact_type="java-source",
        source_id=SOURCE_ID,
        scope_id=SCOPE_ID,
        relative_path="src/main/java/example/DemoController.java",
        revision=REVISION,
        content_hash=digest,
        content=source_text,
    )
    derived = JavaArtifactProcessor().derive(source)
    collection = SourceCollection(
        source_id=SOURCE_ID,
        scope_id=SCOPE_ID,
        revision=REVISION,
        artifacts=(source, derived),
    )
    entities, evidence, facts = ExtendedKnowledgeBuilder().build(collection, ())
    endpoint_fact = next(item for item in facts if item.predicate == "EXPOSES_ENDPOINT")
    endpoint = next(item for item in entities if item.entity_id == endpoint_fact.object_id)
    evidence_by_id = {item.evidence_id: item for item in evidence}
    observations = [evidence_by_id[item] for item in endpoint_fact.evidence_ids]
    return source, endpoint, endpoint_fact, observations


class EndpointCompositeEvidenceTest(unittest.TestCase):
    def test_composite_endpoint_has_separate_class_and_method_evidence(self) -> None:
        source, endpoint, fact, observations = _build_endpoint_knowledge(
            """package example;

import org.springframework.web.bind.annotation.*;

@RequestMapping("/api")
class DemoController {
    @PostMapping("/items")
    public void create() {}
}
"""
        )

        self.assertEqual("POST /api/items", endpoint.name)
        self.assertEqual(2, len(fact.evidence_ids))
        self.assertEqual(
            {'@RequestMapping("/api")', '@PostMapping("/items")'},
            {item.quote for item in observations},
        )
        self.assertEqual({(5, 5), (7, 7)}, {
            (item.line_start, item.line_end) for item in observations
        })
        self.assertTrue(
            all(item.artifact_id == source.artifact_id for item in observations)
        )

    def test_method_only_endpoint_has_one_evidence(self) -> None:
        source, endpoint, fact, observations = _build_endpoint_knowledge(
            """package example;

import org.springframework.web.bind.annotation.*;

class DemoController {
    @GetMapping("/health")
    public void health() {}
}
"""
        )

        self.assertEqual("GET /health", endpoint.name)
        self.assertEqual(1, len(fact.evidence_ids))
        self.assertEqual('@GetMapping("/health")', observations[0].quote)
        self.assertEqual((6, 6), (observations[0].line_start, observations[0].line_end))
        self.assertEqual(source.artifact_id, observations[0].artifact_id)


if __name__ == "__main__":
    unittest.main()
