from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from swm_demo.agent_contract import AgentTask
from swm_demo.answer_review_agent import AnswerReviewAgent
from swm_demo.application import ApplicationError, ApplicationServices
from swm_demo.knowledge_contract import KnowledgeEntity, KnowledgePackage
from swm_demo.model_gateway import DeterministicValidationProvider, ModelGateway
from swm_demo.storage import KnowledgeStoreError, SQLiteKnowledgeStore
from swm_demo.task_execution_agent import TaskExecutionAgent


WORKSPACE = Path(__file__).resolve().parents[2]
MALL_REPOSITORY = WORKSPACE / "validation-projects" / "mall"
MALL_REVISION = "0504e86b1f1b6f1b8aa6a734d37a90fb67346be7"
TARGET_COMMIT = "dacce5f28dfc1734f2db09668d928d7fac2a3a7a"
SCOPE_ID = "system:model-led-update"


class _RecordingProvider(DeterministicValidationProvider):
    def __init__(self, services: ApplicationServices):
        self.services = services
        self.calls: list[tuple[str, dict[str, object]]] = []

    def invoke(
        self, capability: str, payload: dict[str, object]
    ) -> dict[str, object]:
        self.calls.append((capability, payload))
        result = super().invoke(capability, payload)
        if capability == "derive-build-intent":
            # Deliberately collect only the root POM plus the requested Commit.
            # Preservation must come from Snapshot enrichment, not an accidental
            # full rebuild selected by this deterministic validation provider.
            result["artifact_request"]["include_globs"] = ["pom.xml"]
            result["artifact_request"]["derive_java_ast"] = False
        if capability == "propose-knowledge-candidates":
            # From this point onward the source boundary is physically closed.
            # Reassessment, drafting and review must survive on formal S1 only.
            def forbidden(*args: object, **kwargs: object):
                raise AssertionError("answer phase attempted to access Source Integration")

            self.services.source_integration.collect_sources = forbidden  # type: ignore[method-assign]
        return result


class ModelLedUpdateContextIsolationTest(unittest.TestCase):
    def test_gap_drives_arbitrary_commit_update_then_answer_uses_only_new_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            services = ApplicationServices(Path(directory) / "model-led.sqlite3")
            try:
                services.configure_scope(
                    SCOPE_ID,
                    "model-led update",
                    MALL_REPOSITORY,
                    MALL_REVISION,
                )
                services.update_knowledge(SCOPE_ID, "full-validation")
                old_context = services.open_knowledge_context(SCOPE_ID)
                old_history = services.query_semantic_view(SCOPE_ID, "history")
                old_entities = {
                    str(item["entity_id"])
                    for item in services.knowledge_engine.read_entities(SCOPE_ID)
                }
                old_facts = {
                    str(item["fact_id"])
                    for item in services.knowledge_engine.read_facts(SCOPE_ID)
                }
                old_inferences = {
                    str(item["inference_id"])
                    for item in services.knowledge_engine.read_inferences(SCOPE_ID)
                }
                old_artifacts = {
                    str(row["artifact_id"])
                    for row in services.store.connection.execute(
                        """
                        SELECT artifact_id FROM snapshot_artifacts
                        WHERE snapshot_id = ?
                        """,
                        (old_context["snapshot_id"],),
                    ).fetchall()
                }
                old_behavior = services.query_semantic_view(SCOPE_ID, "behavior")
                old_business = services.query_semantic_view(SCOPE_ID, "business")
                self.assertTrue(old_behavior["items"])
                self.assertTrue(old_business["items"])
                old_behavior_ids = {
                    str(item["inference_id"]) for item in old_behavior["items"]
                }
                old_business_ids = {
                    str(item["inference_id"]) for item in old_business["items"]
                }
                old_explained_fact_id = next(iter(old_facts))
                old_fact_explanation = services.explain_fact(
                    SCOPE_ID, old_explained_fact_id
                )
                old_evidence_ids = {
                    str(item["evidence_id"])
                    for item in old_fact_explanation["evidence"]
                }
                self.assertTrue(old_evidence_ids)
                self.assertNotIn(
                    TARGET_COMMIT[:7],
                    "\n".join(item["statement"] for item in old_history["items"]),
                )

                provider = _RecordingProvider(services)
                gateway = ModelGateway(provider, services.store)
                task_agent = TaskExecutionAgent(services, gateway)
                review_agent = AnswerReviewAgent(services, gateway)
                task = AgentTask(
                    task_id="agent-task:arbitrary-commit",
                    original_request=f"提交 {TARGET_COMMIT} 做了什么？",
                    scope_id=SCOPE_ID,
                    use_case="history-view",
                    parameters={},
                    routing_model_call_id="model-call:test-routing",
                )

                original_query_semantic_view = services.query_semantic_view

                def forbidden_view(*args: object, **kwargs: object):
                    raise AssertionError(
                        "TaskExecutionAgent attempted to use a fixed Semantic View"
                    )

                services.query_semantic_view = forbidden_view  # type: ignore[method-assign]
                try:
                    candidate = task_agent.execute(task)
                finally:
                    services.query_semantic_view = original_query_semantic_view  # type: ignore[method-assign]
                review = review_agent.review(task.original_request, task, candidate)

                self.assertEqual("PASS", review.decision)
                self.assertIn(TARGET_COMMIT[:7], candidate.answer)
                self.assertIsNotNone(candidate.requirement)
                self.assertIsNotNone(candidate.assessment)
                self.assertTrue(candidate.assessment.complete)  # type: ignore[union-attr]
                self.assertEqual(
                    candidate.assessment.assessment_id,  # type: ignore[union-attr]
                    candidate.assessment_reference,
                )
                self.assertNotEqual(old_context["snapshot_id"], candidate.snapshot_id)

                new_entities = {
                    str(item["entity_id"])
                    for item in services.knowledge_engine.read_entities(SCOPE_ID)
                }
                new_facts = {
                    str(item["fact_id"])
                    for item in services.knowledge_engine.read_facts(SCOPE_ID)
                }
                new_inferences = {
                    str(item["inference_id"])
                    for item in services.knowledge_engine.read_inferences(SCOPE_ID)
                }
                new_artifacts = {
                    str(row["artifact_id"])
                    for row in services.store.connection.execute(
                        """
                        SELECT artifact_id FROM snapshot_artifacts
                        WHERE snapshot_id = ?
                        """,
                        (candidate.snapshot_id,),
                    ).fetchall()
                }
                self.assertTrue(old_entities <= new_entities)
                self.assertTrue(old_facts <= new_facts)
                self.assertTrue(old_inferences <= new_inferences)
                self.assertTrue(old_artifacts <= new_artifacts)

                current_behavior_ids = {
                    str(item["inference_id"])
                    for item in services.query_semantic_view(
                        SCOPE_ID, "behavior"
                    )["items"]
                }
                current_business_ids = {
                    str(item["inference_id"])
                    for item in services.query_semantic_view(
                        SCOPE_ID, "business"
                    )["items"]
                }
                self.assertTrue(old_behavior_ids <= current_behavior_ids)
                self.assertTrue(old_business_ids <= current_business_ids)

                inherited_explanation = services.explain_fact(
                    SCOPE_ID, old_explained_fact_id
                )
                self.assertEqual(
                    old_evidence_ids,
                    {
                        str(item["evidence_id"])
                        for item in inherited_explanation["evidence"]
                    },
                )

                with self.assertRaisesRegex(ApplicationError, "STALE_CONTEXT"):
                    services.search_knowledge(
                        SCOPE_ID,
                        str(old_context["snapshot_token"]),
                        "ENTITY",
                        "JwtTokenUtil",
                    )

                assessment_payloads = [
                    payload
                    for capability, payload in provider.calls
                    if capability == "assess-knowledge-sufficiency"
                ]
                self.assertEqual(2, len(assessment_payloads))
                self.assertEqual(
                    assessment_payloads[0]["requirement"],
                    assessment_payloads[1]["requirement"],
                )
                knowledge_use_payloads = [
                    payload
                    for capability, payload in provider.calls
                    if capability == "plan-formal-knowledge-step"
                ]
                self.assertEqual(
                    [0, 1, 0, 1],
                    [len(payload["tool_trace"]) for payload in knowledge_use_payloads],
                )

                draft_payload = next(
                    payload
                    for capability, payload in provider.calls
                    if capability == "draft-answer"
                )
                serialized_draft = json.dumps(
                    draft_payload, ensure_ascii=False, sort_keys=True
                ).lower()
                for forbidden in (
                    "source_artifacts",
                    "artifact_content",
                    "candidate_bundle",
                    "evidence_quote",
                    "jwttokenutil.java",
                    "jwtutil.createtoken",
                ):
                    self.assertNotIn(forbidden, serialized_draft)

                phase_rows = services.store.connection.execute(
                    """
                    SELECT capability, context_id, phase
                    FROM model_calls
                    WHERE capability IN (
                        'plan-formal-knowledge-step',
                        'derive-build-intent',
                        'propose-knowledge-candidates',
                        'draft-answer',
                        'review-answer'
                    )
                    ORDER BY rowid
                    """
                ).fetchall()
                investigation_context_ids = {
                    row["context_id"]
                    for row in phase_rows
                    if row["phase"] == "INVESTIGATION"
                }
                answer_context_ids = {
                    row["context_id"]
                    for row in phase_rows
                    if row["phase"] == "ANSWER"
                }
                self.assertEqual(1, len(investigation_context_ids))
                self.assertEqual(1, len(answer_context_ids))
                knowledge_use_context_ids = {
                    row["context_id"]
                    for row in phase_rows
                    if row["phase"] == "KNOWLEDGE_USE"
                }
                self.assertEqual(2, len(knowledge_use_context_ids))
                self.assertTrue(
                    investigation_context_ids.isdisjoint(answer_context_ids)
                )
                self.assertTrue(
                    knowledge_use_context_ids.isdisjoint(
                        investigation_context_ids | answer_context_ids
                    )
                )
            finally:
                services.close()

    def test_stale_base_cannot_overwrite_a_concurrent_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteKnowledgeStore(Path(directory) / "stale-base.sqlite3")
            scope_id = "system:stale-base"
            revision = "revision:same"
            store.upsert_scope(scope_id, "stale base")
            try:
                base_snapshot_id = store.start_snapshot(scope_id, revision)
                store.publish_knowledge(
                    base_snapshot_id,
                    KnowledgePackage(
                        scope_id=scope_id,
                        revision=revision,
                        entities=(
                            KnowledgeEntity(
                                "entity:base", scope_id, "test", "base"
                            ),
                        ),
                        evidence=(),
                        facts=(),
                    ),
                )

                stale_building_id = store.start_snapshot(scope_id, revision)

                concurrent_snapshot_id = store.start_snapshot(scope_id, revision)
                store.publish_knowledge(
                    concurrent_snapshot_id,
                    KnowledgePackage(
                        scope_id=scope_id,
                        revision=revision,
                        entities=(
                            KnowledgeEntity(
                                "entity:concurrent",
                                scope_id,
                                "test",
                                "concurrent",
                            ),
                        ),
                        evidence=(),
                        facts=(),
                    ),
                )
                # base_snapshot_id=None remains a replacement, not enrichment.
                self.assertEqual(
                    ["entity:concurrent"],
                    [item["entity_id"] for item in store.current_entities(scope_id)],
                )

                with self.assertRaisesRegex(
                    KnowledgeStoreError, "STALE_BASE_SNAPSHOT"
                ):
                    store.publish_knowledge(
                        stale_building_id,
                        KnowledgePackage(
                            scope_id=scope_id,
                            revision=revision,
                            entities=(
                                KnowledgeEntity(
                                    "entity:stale", scope_id, "test", "stale"
                                ),
                            ),
                            evidence=(),
                            facts=(),
                        ),
                        base_snapshot_id=base_snapshot_id,
                    )

                self.assertEqual(
                    concurrent_snapshot_id,
                    store.current_snapshot(scope_id)["snapshot_id"],
                )
                self.assertEqual(
                    ["entity:concurrent"],
                    [item["entity_id"] for item in store.current_entities(scope_id)],
                )
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
