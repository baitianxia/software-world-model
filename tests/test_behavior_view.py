from __future__ import annotations

from types import SimpleNamespace
import unittest

from software_world_model.ai_infrastructure.world_model_answer_strategy import (
    COMPLETE_NEGATIVE_ANSWER,
    ENTITY_CANDIDATE_RESOLUTION,
    GENERIC_QUERY_PLANNING,
    ORDERED_DIFF_EXPRESSION,
    VIEW_LIMITATION_AND_KNOWLEDGE_GAP,
)
from software_world_model.ai_infrastructure.model_egress_gateway import (
    JAVA_MODEL_EGRESS_GATEWAY_ROUTE,
)
from software_world_model.application_services.structure_view import (
    StructureViewOperation,
)
from software_world_model.application_services.world_model_answering import (
    WorldModelNeedOutcome,
)
from software_world_model.cross_cutting import digest_of
from software_world_model.interface.world_model_product import (
    JAVA_PRODUCT_STRATEGY_REF,
    WorldModelProductAnswerService,
)
from tests import test_java_static_call as java_fixture


class _JavaQualifiedFixtureModel:
    """Return the exact bounded capability proposal requested by the product."""

    strategy_ref = JAVA_PRODUCT_STRATEGY_REF

    def __init__(self) -> None:
        self.provider_call_count = 0
        self.network_operation_count = 0
        self.capabilities: list[str] = []
        self.sealed_inputs: list[object] = []

    def propose(
        self,
        *,
        case_id: str,
        capability: str,
        sealed_input: object,
        available_operations: tuple[str, ...] = (),
    ) -> object:
        del case_id, available_operations
        self.provider_call_count += 1
        self.network_operation_count += 1
        self.capabilities.append(capability)
        self.sealed_inputs.append(sealed_input)
        if capability == GENERIC_QUERY_PLANNING:
            operations: list[dict[str, object]] = []
            for need in sealed_input["needs"]:
                index = 0 if need.endswith("left") else 1
                if need.startswith("method_inventory_"):
                    operations.append(
                        {
                            "operation": "declared_method_inventory",
                            "snapshot": sealed_input["read_set"][index],
                        }
                    )
                elif need.startswith("paths_"):
                    operations.append(
                        {
                            "operation": "all_simple_paths",
                            "snapshot": sealed_input["read_set"][index],
                            "source_ref": sealed_input["source_entity_ref"],
                            "target_ref": sealed_input["target_entity_ref"],
                        }
                    )
                else:  # pragma: no cover - the closed fixture has no other Need
                    raise AssertionError(f"unexpected Java plan Need: {need}")
            normalized = {"operations": operations}
        elif capability == ENTITY_CANDIDATE_RESOLUTION:
            candidates = sealed_input["candidate_refs"]
            normalized = {
                "resolution_status": (
                    "NOT_FOUND"
                    if not candidates
                    else "RESOLVED"
                    if len(candidates) == 1
                    else "AMBIGUOUS"
                ),
                "candidate_refs": candidates,
                "next_operation_allowed": len(candidates) == 1,
            }
        elif capability == ORDERED_DIFF_EXPRESSION:
            normalized = {
                "direction": {
                    "base": sealed_input["base"],
                    "target": sealed_input["target"],
                },
                "added_entities": sealed_input["target_added"],
            }
        elif capability == COMPLETE_NEGATIVE_ANSWER:
            normalized = {
                "need_status": "SATISFIED_SUPPORTED_NEGATIVE",
                "claim_scope": "NO_PATH_IN_CALLS_FOR_EXACT_READ_SET",
            }
        elif capability == VIEW_LIMITATION_AND_KNOWLEDGE_GAP:
            normalized = {
                "view_result": {
                    "status": "LIMITED",
                    "code": "COVERAGE_PARTIAL",
                    "owner": "STRUCTURE_VIEW",
                },
                "need_assessment": {
                    "status": "KNOWLEDGE_GAP",
                    "code": "INSUFFICIENT_COMPLETE_COVERAGE",
                    "owner": "KNOWLEDGE_USE",
                },
            }
        else:  # pragma: no cover - closed by the assertions below
            raise AssertionError(f"unexpected capability: {capability}")
        return SimpleNamespace(normalized_result=normalized)


class JavaBehaviorProductTests(unittest.TestCase):
    def setUp(self) -> None:
        fixture = java_fixture.JavaBehaviorViewTests(methodName="runTest")
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        self.view = fixture.service
        self.bundle = fixture.bundle
        self.ordered_view = fixture.ordered_service
        self.r2_bundle = fixture.r2_bundle

    def _execute(self, question: str, *, ordered: bool = False):
        model = _JavaQualifiedFixtureModel()
        execution = WorldModelProductAnswerService(
            view=self.ordered_view if ordered else self.view,
            snapshot_bundles=(
                (self.bundle, self.r2_bundle)
                if ordered
                else (self.bundle,)
            ),
            model_strategy=model,
            gateway_counters=model,
        ).execute(
            request_ref="java-behavior-product",
            original_question=question,
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of("java-behavior-product-permission"),
        )
        execution.chain.require_valid()
        self.assertEqual(execution.chain.provider_call_count, 1)
        self.assertEqual(execution.chain.network_operation_count, 1)
        self.assertEqual(len(execution.model_proposals), 1)
        self.assertEqual(
            execution.chain.draft.generation_invocation.strategy_ref,
            "model-snapshot-first-world-model-answer@1.1.0",
        )
        self.assertEqual(
            execution.chain.draft.generation_invocation.provider_route,
            JAVA_MODEL_EGRESS_GATEWAY_ROUTE,
        )
        self.assertEqual(
            execution.chain.question.model_route,
            JAVA_MODEL_EGRESS_GATEWAY_ROUTE,
        )
        self.assertNotIn("Audit.record(input)", repr(model.sealed_inputs))
        return execution, model

    def test_declared_methods_direct_calls_and_paths_use_formal_java_view(self) -> None:
        inventory, inventory_model = self._execute("FlowService 有哪些方法？")
        self.assertEqual(inventory_model.capabilities, [GENERIC_QUERY_PLANNING])
        inventory_result = inventory.chain.result_set.step_results[0].view_result
        self.assertEqual(
            inventory_result.operation,
            StructureViewOperation.DECLARED_METHOD_INVENTORY,
        )
        self.assertEqual(inventory_result.payload["method_count"], 3)
        self.assertTrue(inventory_result.support_map)
        self.assertTrue(inventory_result.evidence_allowlist)
        self.assertIn("JAVA_SOURCE_DECLARATION@1", inventory.chain.draft.body)

        direct, direct_model = self._execute(
            "FlowService.start(String) 直接调用哪些方法？"
        )
        self.assertEqual(
            direct_model.capabilities, [ENTITY_CANDIDATE_RESOLUTION]
        )
        direct_result = direct.chain.result_set.step_results[0].view_result
        self.assertEqual(
            direct_result.operation, StructureViewOperation.DIRECT_NEIGHBORHOOD
        )
        self.assertEqual(len(direct_result.payload["relations"]), 2)
        self.assertIn("JAVA_SOURCE_STATIC_CALL@1", direct.chain.draft.body)
        self.assertIn('"runtime_dispatch_claimed":false', direct.chain.draft.body)

        paths, path_model = self._execute(
            "FlowService.start(String) 到 FlowService.finish(String) 的调用路径？"
        )
        self.assertEqual(path_model.capabilities, [GENERIC_QUERY_PLANNING])
        path_result = paths.chain.result_set.step_results[0].view_result
        self.assertEqual(
            path_result.operation, StructureViewOperation.ALL_SIMPLE_PATHS
        )
        self.assertEqual(path_result.payload["path_count"], 1)
        self.assertEqual(
            len(path_result.payload["paths"][0]["relation_root_ids"]), 2
        )
        self.assertTrue(path_result.support_map)
        self.assertIn("全部简单静态调用路径", paths.chain.draft.body)

    def test_runtime_semantics_question_is_an_explicit_knowledge_gap(self) -> None:
        result, model = self._execute(
            "FlowService.start(String) 实际运行时会调用哪个实现？"
        )

        self.assertEqual(
            model.capabilities, [VIEW_LIMITATION_AND_KNOWLEDGE_GAP]
        )
        self.assertEqual(
            result.chain.assessment.needs[0].outcome,
            WorldModelNeedOutcome.KNOWLEDGE_GAP,
        )
        self.assertEqual(result.chain.result_set.step_results, ())
        self.assertIn("KNOWLEDGE_NOT_MODELED", result.chain.draft.body)
        self.assertIn("不证明运行时分派", result.chain.draft.body)

    def test_complete_coverage_supports_only_a_static_no_path_conclusion(self) -> None:
        result, model = self._execute(
            "Audit#record(String) 到 FlowService#finish(String) 是否有调用路径？"
        )

        self.assertEqual(model.capabilities, [COMPLETE_NEGATIVE_ANSWER])
        path = result.chain.result_set.step_results[0].view_result
        self.assertEqual(path.operation, StructureViewOperation.ALL_SIMPLE_PATHS)
        self.assertEqual(path.payload["path_count"], 0)
        self.assertTrue(path.payload["negative_conclusion_supported"])
        self.assertIn("不存在", result.chain.draft.body)
        self.assertIn("不扩大为运行时不调用", result.chain.draft.body)

    def test_ordered_java_call_graph_diff_uses_formal_view(self) -> None:
        result, model = self._execute(
            "说明 R1 到 R2 的调用图变化。",
            ordered=True,
        )

        self.assertEqual(model.capabilities, [ORDERED_DIFF_EXPRESSION])
        diff = result.chain.result_set.step_results[0].view_result
        self.assertEqual(
            diff.operation,
            StructureViewOperation.ORDERED_SNAPSHOT_DIFF,
        )
        self.assertEqual(diff.payload["entities"]["counts"]["added"], 1)
        self.assertEqual(diff.payload["relations"]["counts"]["added"], 3)
        self.assertEqual(diff.payload["relations"]["counts"]["removed"], 1)
        self.assertIn("FlowService#normalize(String)", result.chain.draft.body)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
