from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from swm_demo.agent_contract import AgentTask, AnswerClaim
from swm_demo.agent_orchestrator import AgentOrchestrator
from swm_demo.answer_review_agent import AnswerReviewAgent
from swm_demo.application import ApplicationServices
from swm_demo.artifact_contract import ArtifactRequest, SourceArtifact, SourceCollection
from swm_demo.ids import content_hash, stable_id
from swm_demo.knowledge_contract import (
    Evidence,
    FactCandidate,
    InferenceCandidate,
    KnowledgeEntity,
)
from swm_demo.knowledge_engine import InferenceVerifier, KnowledgeEngine
from swm_demo.model_gateway import (
    DeterministicValidationProvider,
    ModelGateway,
    ModelPhase,
)
from swm_demo.scheduler import SchedulerAdapter
from swm_demo.source_integration import (
    LocalGitConnectorProvider,
    SourceIntegration,
)
from swm_demo.task_execution_agent import TaskExecutionAgent
from swm_demo.web_chat import WebChatAdapter


WORKSPACE = Path(__file__).resolve().parents[2]
MALL_REPOSITORY = WORKSPACE / "validation-projects" / "mall"
MALL_REVISION = "0504e86b1f1b6f1b8aa6a734d37a90fb67346be7"
SCOPE_ID = "system:mall"


class FullArchitectureValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.database = Path(cls.temporary.name) / "full-validation.sqlite3"
        cls.services = ApplicationServices(cls.database)
        cls.services.configure_scope(
            scope_id=SCOPE_ID,
            name="mall",
            source_path=MALL_REPOSITORY,
            expected_revision=MALL_REVISION,
        )
        cls.update_result = cls.services.update_knowledge(
            SCOPE_ID, "full-validation"
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.services.close()
        cls.temporary.cleanup()

    def test_full_profile_processes_real_input_and_preserves_artifact_lineage(self) -> None:
        self.assertEqual(1186, self.update_result["artifact_count"])
        self.assertEqual(16, self.update_result["inference_count"])
        lineage_count = self.services.store.connection.execute(
            "SELECT COUNT(*) FROM artifact_lineage"
        ).fetchone()[0]
        derived_count = self.services.store.connection.execute(
            "SELECT COUNT(*) FROM artifacts WHERE artifact_type = 'java-ast-summary'"
        ).fetchone()[0]
        self.assertEqual(524, derived_count)
        self.assertEqual(derived_count, lineage_count)

    def test_s02_endpoint_chain_is_composed_only_from_structure_facts(self) -> None:
        view = self.services.query_endpoint_structure(
            SCOPE_ID, "POST /order/generateOrder"
        )
        self.assertEqual("READY", view["status"])
        self.assertEqual(["mall-portal"], [item["name"] for item in view["module"]])
        self.assertEqual(
            [
                "com.macro.mall.portal.controller."
                "OmsPortalOrderController#generateOrder(OrderParam)"
            ],
            [item["name"] for item in view["controller_methods"]],
        )
        self.assertEqual(
            [
                "com.macro.mall.portal.service."
                "OmsPortalOrderService#generateOrder(OrderParam)"
            ],
            [item["name"] for item in view["service_methods"]],
        )
        self.assertEqual(
            [
                "com.macro.mall.portal.service.impl."
                "OmsPortalOrderServiceImpl#generateOrder(OrderParam)"
            ],
            [item["name"] for item in view["implementation_methods"]],
        )
        self.assertTrue(view["knowledge_references"])
        explanations = [
            self.services.explain_fact(SCOPE_ID, fact_id)
            for fact_id in view["knowledge_references"]
        ]
        self.assertTrue(all(item["evidence"] for item in explanations))
        paths = {
            observation["relative_path"]
            for item in explanations
            for observation in item["evidence"]
        }
        self.assertIn(
            "mall-portal/src/main/java/com/macro/mall/portal/controller/"
            "OmsPortalOrderController.java",
            paths,
        )
        self.assertIn(
            "mall-portal/src/main/java/com/macro/mall/portal/service/impl/"
            "OmsPortalOrderServiceImpl.java",
            paths,
        )

    def test_behavior_view_reuses_structure_and_code_facts(self) -> None:
        view = self.services.query_semantic_view(SCOPE_ID, "behavior")
        self.assertEqual(3, len(view["items"]))
        create_order = next(
            item for item in view["items"] if "B-01 创建订单" in item["statement"]
        )
        statement = create_order["statement"]
        expected_order = [
            "校验收货地址",
            "判断购物车中商品是否都有库存",
            "进行库存锁定",
            "插入order表和order_item表",
            "删除购物车中的下单商品",
            "发送延迟消息取消订单",
        ]
        positions = [statement.index(item) for item in expected_order]
        self.assertEqual(sorted(positions), positions)

        explanation = self.services.explain_inference(
            SCOPE_ID, create_order["inference_id"]
        )
        predicates = {
            item["predicate"] for item in explanation["supporting_facts"]
        }
        self.assertIn("DECLARES_STEP", predicates)
        self.assertTrue(
            predicates.intersection({"CALLS", "CALLS_OPERATION"})
        )
        self.assertIn("HAS_FAILURE_GUARD", predicates)

    def test_business_view_keeps_source_declarations_and_business_meaning_separate(self) -> None:
        view = self.services.query_semantic_view(SCOPE_ID, "business")
        capability_items = [
            item
            for item in view["items"]
            if item["inference_type"] == "BUSINESS_CAPABILITY"
        ]
        constraint_items = [
            item
            for item in view["items"]
            if item["inference_type"] == "BUSINESS_CONSTRAINT"
        ]
        self.assertEqual(7, len(capability_items))
        self.assertEqual(4, len(constraint_items))
        combined = "\n".join(item["statement"] for item in view["items"])
        self.assertIn("mall-admin 承载的业务能力", combined)
        self.assertIn("mall-portal 承载的业务能力", combined)
        self.assertIn("mall-search 承载的业务能力", combined)
        self.assertIn("请选择收货地址", combined)
        self.assertIn("库存不足", combined)

        constraint = next(
            item for item in constraint_items if "库存不足" in item["statement"]
        )
        explanation = self.services.explain_inference(
            SCOPE_ID, constraint["inference_id"]
        )
        self.assertEqual(
            {"HAS_FAILURE_GUARD"},
            {item["predicate"] for item in explanation["supporting_facts"]},
        )

    def test_history_view_uses_commit_context_without_inventing_motivation(self) -> None:
        view = self.services.query_semantic_view(SCOPE_ID, "history")
        self.assertEqual(2, len(view["items"]))
        upgrade = next(
            item for item in view["items"] if "0504e86" in item["statement"]
        )
        ordering = next(
            item for item in view["items"] if "dd6569c" in item["statement"]
        )
        self.assertIn("Thu May 14 16:30:28 2026 +0800", upgrade["statement"])
        self.assertIn("升级支持Spring Boot 3.5", upgrade["statement"])
        self.assertIn("构建与依赖", upgrade["statement"])
        self.assertIn(
            "getCacheService().delAdmin(id); now precedes "
            "int count = adminMapper.deleteByPrimaryKey(id);",
            ordering["statement"],
        )
        self.assertIn("不补写提交信息之外的作者动机", ordering["statement"])

        explanation = self.services.explain_inference(
            SCOPE_ID, ordering["inference_id"]
        )
        predicates = {
            item["predicate"] for item in explanation["supporting_facts"]
        }
        self.assertIn("AUTHORED_AT", predicates)
        self.assertIn("DECLARES_CHANGE", predicates)
        self.assertIn("CHANGED_ORDER", predicates)
        declaration_fact = next(
            item
            for item in explanation["supporting_facts"]
            if item["predicate"] == "DECLARES_CHANGE"
        )
        fact_explanation = self.services.explain_fact(
            SCOPE_ID, declaration_fact["fact_id"]
        )
        self.assertEqual(
            "dd6569c3558f79af5b21aad601349e0f029b9a6d",
            fact_explanation["revision"],
        )
        self.assertEqual(
            "dd6569c3558f79af5b21aad601349e0f029b9a6d",
            fact_explanation["evidence"][0]["revision"],
        )

    def test_web_chat_passes_through_dynamic_agent_and_independent_review(self) -> None:
        before_calls = self.services.store.model_call_count()
        gateway = ModelGateway(
            DeterministicValidationProvider(), self.services.store
        )
        task_agent = TaskExecutionAgent(self.services, gateway)
        review_agent = AnswerReviewAgent(self.services, gateway)
        orchestrator = AgentOrchestrator(task_agent, review_agent, gateway)
        web = WebChatAdapter(orchestrator)

        response = web.send("创建订单的流程是什么？", SCOPE_ID)
        self.assertEqual("ANSWERED", response["status"])
        self.assertEqual("PASS", response["review"]["decision"])
        self.assertIn("B-01 创建订单", response["answer"])
        self.assertTrue(response["knowledge_reference_ids"])
        # Routing, Requirement, SEARCH, STOP, Assessment, Answer and Review.
        self.assertEqual(before_calls + 7, self.services.store.model_call_count())

    def test_answer_review_rejects_tampered_claim_and_stale_snapshot(self) -> None:
        gateway = ModelGateway(
            DeterministicValidationProvider(), self.services.store
        )
        task_agent = TaskExecutionAgent(self.services, gateway)
        review_agent = AnswerReviewAgent(self.services, gateway)
        task = AgentTask(
            task_id="agent-task:review-test",
            original_request="订单有哪些业务约束？",
            scope_id=SCOPE_ID,
            use_case="business-view",
            parameters={},
            routing_model_call_id="model-call:test-routing",
        )
        candidate = task_agent.execute(task)
        false_claim = AnswerClaim(
            text="系统保证所有订单永远库存充足。",
            knowledge_reference_ids=candidate.claims[0].knowledge_reference_ids,
        )
        tampered_claims = (*candidate.claims, false_claim)
        tampered = replace(
            candidate,
            claims=tampered_claims,
            answer="\n".join(item.text for item in tampered_claims),
        )
        rejected = review_agent.review(task.original_request, task, tampered)
        self.assertEqual("REJECT", rejected.decision)
        self.assertTrue(rejected.issues)

        stale = replace(candidate, snapshot_id="snapshot:stale")
        stale_result = review_agent.review(task.original_request, task, stale)
        self.assertEqual("REJECT", stale_result.decision)
        self.assertIn("stale Snapshot", stale_result.issues[0])

    def test_answer_review_does_not_treat_candidate_text_as_authoritative(self) -> None:
        gateway = ModelGateway(
            DeterministicValidationProvider(), self.services.store
        )
        task_agent = TaskExecutionAgent(self.services, gateway)
        review_agent = AnswerReviewAgent(self.services, gateway)
        task = AgentTask(
            task_id="agent-task:self-authority-test",
            original_request="订单有哪些业务约束？",
            scope_id=SCOPE_ID,
            use_case="business-view",
            parameters={},
            routing_model_call_id="model-call:test-routing",
        )
        candidate = task_agent.execute(task)
        original = candidate.claims[0]
        tampered_claim = replace(
            original,
            text=original.text + "；系统保证所有订单永远库存充足。",
        )
        tampered = replace(
            candidate,
            claims=(tampered_claim, *candidate.claims[1:]),
            answer="\n".join(
                item.text for item in (tampered_claim, *candidate.claims[1:])
            ),
        )

        result = review_agent.review(task.original_request, task, tampered)

        self.assertEqual("REJECT", result.decision)
        self.assertTrue(result.issues)

    def test_answer_review_rejects_pass_with_unsupported_claims(self) -> None:
        class _ContradictoryReviewProvider(DeterministicValidationProvider):
            def invoke(
                self, capability: str, payload: dict[str, object]
            ) -> dict[str, object]:
                if capability == "review-answer":
                    return {
                        "decision": "PASS",
                        "unsupported_claims": [payload["candidate_claims"][0]],  # type: ignore[index]
                    }
                return super().invoke(capability, payload)

        gateway = ModelGateway(_ContradictoryReviewProvider(), self.services.store)
        task_agent = TaskExecutionAgent(self.services, gateway)
        review_agent = AnswerReviewAgent(self.services, gateway)
        task = AgentTask(
            task_id="agent-task:contradictory-review-test",
            original_request="订单有哪些业务约束？",
            scope_id=SCOPE_ID,
            use_case="business-view",
            parameters={},
            routing_model_call_id="model-call:test-routing",
        )
        candidate = task_agent.execute(task)

        result = review_agent.review(task.original_request, task, candidate)

        self.assertEqual("REJECT", result.decision)
        self.assertTrue(result.issues)

    def test_inference_admission_rejects_missing_support_and_cycles(self) -> None:
        missing = InferenceCandidate(
            inference_id="invalid",
            scope_id=SCOPE_ID,
            revision=MALL_REVISION,
            inference_type="TEST",
            statement="unsupported",
            support_fact_ids=(),
        )
        errors = InferenceVerifier().verify((), (missing,))
        self.assertTrue(any("no direct Fact support" in item for item in errors))

        first = replace(
            missing,
            inference_id="first",
            support_fact_ids=("fact:missing",),
            dependency_inference_ids=("second",),
        )
        second = replace(
            missing,
            inference_id="second",
            support_fact_ids=("fact:missing",),
            dependency_inference_ids=("first",),
        )
        cycle_errors = InferenceVerifier().verify((), (first, second))
        self.assertTrue(any("cycle" in item for item in cycle_errors))

    def test_optional_rejected_inference_is_excluded_without_blocking_snapshot(self) -> None:
        source = SourceArtifact(
            artifact_id="artifact:admission",
            artifact_type="text-document",
            source_id="source:admission",
            scope_id="system:admission",
            relative_path="admission.txt",
            revision="revision:admission",
            content_hash=content_hash("support"),
            content="support",
        )
        collection = SourceCollection(
            source_id=source.source_id,
            scope_id=source.scope_id,
            revision=source.revision,
            artifacts=(source,),
            build_profile="admission-test",
        )
        subject = KnowledgeEntity(
            stable_id("entity", source.scope_id, "test", "subject"),
            source.scope_id,
            "test",
            "subject",
        )
        object_ = KnowledgeEntity(
            stable_id("entity", source.scope_id, "test", "object"),
            source.scope_id,
            "test",
            "object",
        )
        observation = Evidence(
            evidence_id=stable_id(
                "evidence", source.artifact_id, 1, 1, content_hash("support")
            ),
            artifact_id=source.artifact_id,
            scope_id=source.scope_id,
            revision=source.revision,
            line_start=1,
            line_end=1,
            quote="support",
            quote_hash=content_hash("support"),
        )
        fact = FactCandidate(
            fact_id=stable_id(
                "fact",
                source.scope_id,
                subject.entity_id,
                "SUPPORTS",
                object_.entity_id,
            ),
            scope_id=source.scope_id,
            revision=source.revision,
            subject_id=subject.entity_id,
            predicate="SUPPORTS",
            object_id=object_.entity_id,
            evidence_ids=(observation.evidence_id,),
        )

        def inference(inference_type: str, statement: str) -> InferenceCandidate:
            return InferenceCandidate(
                inference_id=stable_id(
                    "inference",
                    source.scope_id,
                    inference_type,
                    statement,
                    fact.fact_id,
                ),
                scope_id=source.scope_id,
                revision=source.revision,
                inference_type=inference_type,
                statement=statement,
                support_fact_ids=(fact.fact_id,),
            )

        required = tuple(
            inference(item, f"accepted {item}")
            for item in (
                "BEHAVIOR_FLOW",
                "BUSINESS_CAPABILITY",
                "BUSINESS_CONSTRAINT",
                "HISTORY_IMPACT",
            )
        )
        optional = inference("BUSINESS_CONSTRAINT", "rejected optional")

        class _BaseBuilder:
            def build(self, ignored):
                return (subject, object_), (observation,), (fact,)

        class _ExtendedBuilder:
            def build(self, ignored, existing):
                return (), (), ()

            def build_inferences(self, ignored, entities, facts, target):
                return (*required, optional)

        class _SemanticReviewer:
            def review(self, entities, facts, candidates):
                return {
                    item.inference_id: (
                        ("forced optional rejection",)
                        if item.inference_id == optional.inference_id
                        else ()
                    )
                    for item in candidates
                }

        build = KnowledgeEngine(
            builder=_BaseBuilder(),
            extended_builder=_ExtendedBuilder(),
            inference_semantic_reviewer=_SemanticReviewer(),
        ).construct(collection)
        self.assertEqual((), build.errors)
        self.assertIsNotNone(build.package)
        self.assertEqual(4, len(build.package.inferences))
        self.assertNotIn(
            optional.inference_id,
            {item.inference_id for item in build.package.inferences},
        )
        self.assertEqual(1, len(build.diagnostics))

    def test_scheduler_reuses_the_fixed_application_use_case(self) -> None:
        class _UpdateSpy:
            def __init__(self) -> None:
                self.calls: list[tuple[str, str]] = []

            def update_knowledge(
                self, scope_id: str, build_profile: str = "structure-core"
            ) -> dict[str, object]:
                self.calls.append((scope_id, build_profile))
                return {"scope_id": scope_id, "build_profile": build_profile}

        spy = _UpdateSpy()
        result = SchedulerAdapter(spy).trigger_update(
            SCOPE_ID, "full-validation"
        )
        self.assertEqual([(SCOPE_ID, "full-validation")], spy.calls)
        self.assertEqual("full-validation", result["build_profile"])

    def test_connector_provider_and_tool_are_separate_extension_contracts(self) -> None:
        local_provider = LocalGitConnectorProvider()
        self.assertEqual("local-git", local_provider.source_type)
        self.assertIn("read-commit", local_provider.capabilities())
        self.assertNotEqual(
            local_provider.__class__.__name__,
            local_provider.create_tool(MALL_REPOSITORY).__class__.__name__,
        )

        class _Tool:
            def collect_sources(
                self,
                scope_id: str,
                request: ArtifactRequest,
                expected_revision: str | None = None,
            ) -> SourceCollection:
                return SourceCollection(
                    source_id="source:fake",
                    scope_id=scope_id,
                    revision=expected_revision or "fake-revision",
                    artifacts=(),
                    build_profile=request.build_profile,
                )

        class _Provider:
            source_type = "fake-source"

            def validate_configuration(self, source_path: Path) -> None:
                self.validated = source_path

            def capabilities(self) -> tuple[str, ...]:
                return ("collect-text",)

            def create_tool(self, source_path: Path) -> _Tool:
                self.created = source_path
                return _Tool()

        provider = _Provider()
        integration = SourceIntegration(
            self.services.store,
            providers=(LocalGitConnectorProvider(), provider),
        )
        self.services.knowledge_engine.configure_scope("system:fake", "fake")
        integration.bind_source(
            "system:fake", "fake-source", MALL_REPOSITORY, "fake-revision"
        )
        collection = integration.collect_sources(
            "system:fake", ArtifactRequest("extension-test", ("README.md",))
        )
        self.assertEqual("extension-test", collection.build_profile)
        self.assertEqual(MALL_REPOSITORY, provider.validated)
        self.assertEqual(MALL_REPOSITORY, provider.created)

    def test_semantic_view_registry_extends_without_new_knowledge_store(self) -> None:
        class _QualityView:
            def render(self, scope_id: str) -> dict[str, object]:
                snapshot = self_outer.services.current_snapshot(scope_id)
                return {
                    "view": "Quality",
                    "scope_id": scope_id,
                    "snapshot_id": snapshot["snapshot_id"],
                    "revision": snapshot["revision"],
                    "items": [],
                    "knowledge_references": [],
                }

        self_outer = self
        before = self.services.store.connection.execute(
            "SELECT COUNT(*) FROM facts"
        ).fetchone()[0]
        self.services.semantic_views.register("quality", _QualityView())
        rendered = self.services.semantic_views.render("quality", SCOPE_ID)
        after = self.services.store.connection.execute(
            "SELECT COUNT(*) FROM facts"
        ).fetchone()[0]
        self.assertEqual("Quality", rendered["view"])
        self.assertEqual(before, after)

    def test_model_gateway_records_provider_version_for_replay(self) -> None:
        class _VersionTwoProvider(DeterministicValidationProvider):
            model_version = "2"

        before = self.services.store.model_call_count()
        gateway = ModelGateway(_VersionTwoProvider(), self.services.store)
        context = gateway.open_context("task:model-version", ModelPhase.ROUTING)
        try:
            result = gateway.invoke(
                "route-task",
                {"request": "查看结构", "scope_id": SCOPE_ID},
                context=context,
            )
        finally:
            gateway.close_context(context)
        record = self.services.store.connection.execute(
            """
            SELECT provider, model, model_version, capability, request_hash
            FROM model_calls WHERE model_call_id = ?
            """,
            (result.model_call_id,),
        ).fetchone()
        self.assertEqual(before + 1, self.services.store.model_call_count())
        self.assertEqual("validation", record["provider"])
        self.assertEqual("deterministic-semantic-double", record["model"])
        self.assertEqual("2", record["model_version"])
        self.assertEqual("route-task", record["capability"])
        self.assertTrue(record["request_hash"])

    def test_static_agent_dependencies_follow_architecture(self) -> None:
        package = WORKSPACE / "demo" / "swm_demo"
        orchestrator = (package / "agent_orchestrator.py").read_text()
        web = (package / "web_chat.py").read_text()
        task = (package / "task_execution_agent.py").read_text()
        review = (package / "answer_review_agent.py").read_text()

        for forbidden in (
            "ApplicationServices",
            "source_integration",
            "knowledge_engine",
            "semantic_view",
        ):
            self.assertNotIn(forbidden, orchestrator)
        self.assertNotIn("TaskExecutionAgent", web)
        self.assertNotIn("AnswerReviewAgent", web)
        for source in (task, review):
            self.assertNotIn("from swm_demo.source_integration", source)
            self.assertNotIn("from swm_demo.knowledge_engine", source)
            self.assertNotIn("from swm_demo.semantic_view", source)


if __name__ == "__main__":
    unittest.main()
