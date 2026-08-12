from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from software_world_model.ai_infrastructure.world_model_answer_strategy import (
    COMPLETE_NEGATIVE_ANSWER,
    ENTITY_CANDIDATE_RESOLUTION,
    GENERIC_QUERY_PLANNING,
    ORDERED_DIFF_EXPRESSION,
    VIEW_LIMITATION_AND_KNOWLEDGE_GAP,
)
from software_world_model.application_services.structure_view import (
    StructureViewOperation,
    StructureViewService,
)
from software_world_model.application_services.world_model_answering import (
    WorldModelNeedOutcome,
)
from software_world_model.cross_cutting import DomainError, digest_of
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.interface.world_model_product import (
    WorldModelProductAnswerService,
)
from tests.test_iteration_003_g3a_integration import (
    Iteration003G3aMallIntegrationTests,
)
from validation.structure_world_model_iteration_003.g3b.prepare_inputs import (
    _prepare_metamorphic,
)
from validation.structure_world_model_iteration_003.metamorphic.generate_reactor import (
    generate,
)


class _QualifiedFixtureModel:
    def __init__(self) -> None:
        self.provider_call_count = 0
        self.network_operation_count = 0
        self.capabilities: list[str] = []
        self.sealed_inputs: list[object] = []

    def propose(
        self,
        *,
        case_id,
        capability,
        sealed_input,
        available_operations=(),
    ):
        del case_id
        self.provider_call_count += 1
        self.network_operation_count += 1
        self.capabilities.append(capability)
        self.sealed_inputs.append(sealed_input)
        if capability == GENERIC_QUERY_PLANNING:
            operations = []
            for need in sealed_input["needs"]:
                if need.startswith("inventory_"):
                    index = 0 if need.endswith("left") else 1
                    operations.append(
                        {
                            "operation": "inventory",
                            "snapshot": sealed_input["read_set"][index],
                        }
                    )
                elif need.startswith("paths_"):
                    index = 0 if need.endswith("left") else 1
                    operations.append(
                        {
                            "operation": "all_simple_paths",
                            "snapshot": sealed_input["read_set"][index],
                            "source_ref": sealed_input["source_entity_ref"],
                            "target_ref": sealed_input["target_entity_ref"],
                        }
                    )
                elif need == "new_paths":
                    operations.append(
                        {
                            "operation": "ordered_snapshot_diff",
                            "base": sealed_input["read_set"][0],
                            "target": sealed_input["read_set"][1],
                        }
                    )
            normalized = {"operations": operations}
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
                "claim_scope": "NO_PATH_IN_DEPENDS_ON_FOR_EXACT_READ_SET",
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
        else:  # pragma: no cover - closed by the assertions below
            raise AssertionError(f"unexpected capability: {capability}")
        return SimpleNamespace(normalized_result=normalized)


class WorldModelProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        Iteration003G3aMallIntegrationTests.setUpClass()
        cls.addClassCleanup(
            Iteration003G3aMallIntegrationTests.doClassCleanups
        )
        cls.mall_view = Iteration003G3aMallIntegrationTests.primary_view
        cls.mall_bundles = tuple(
            item[0]
            for item in (
                Iteration003G3aMallIntegrationTests.loaded["a1"],
                Iteration003G3aMallIntegrationTests.loaded["b"],
            )
        )
        identity = (
            Iteration003G3aMallIntegrationTests.g2_fixture
            ._export_identity_bundle_set()
        )
        files = FileStructureReadBundleStore()
        loaded = tuple(
            files.read_snapshot(path) for path in identity["snapshot_paths"]
        )
        ordered, _ = files.read_ordered(identity["ordered_path"])
        cls.identity_view = StructureViewService(ordered, loaded)
        cls.identity_bundles = tuple(item[0] for item in loaded)
        cls.meta_temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.meta_temporary.cleanup)
        meta_root = Path(cls.meta_temporary.name).resolve()
        cls.meta_generation = generate(
            meta_root / "product",
            meta_root / "evaluator",
            "iter-003-product-random-topology-test",
        )
        meta_binding = _prepare_metamorphic(
            database=meta_root / "authority.sqlite3",
            bundle_root=meta_root / "bundles",
            repository=meta_root / "product" / "repository",
            generation=cls.meta_generation,
        )
        meta_loaded = tuple(
            files.read_snapshot(path)
            for path in meta_binding["snapshot_bundles"]
        )
        meta_ordered, _ = files.read_ordered(meta_binding["ordered_bundle"])
        cls.meta_view = StructureViewService(meta_ordered, meta_loaded)
        cls.meta_bundles = tuple(item[0] for item in meta_loaded)

    def _execute(self, question: str, *, identity: bool = False):
        model = _QualifiedFixtureModel()
        execution = WorldModelProductAnswerService(
            view=self.identity_view if identity else self.mall_view,
            snapshot_bundles=(
                self.identity_bundles if identity else self.mall_bundles
            ),
            model_strategy=model,
            gateway_counters=model,
        ).execute(
            request_ref="fixture-request",
            original_question=question,
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of("fixture-permission"),
        )
        self.assertEqual(execution.chain.provider_call_count, 1)
        self.assertEqual(execution.chain.network_operation_count, 1)
        self.assertEqual(len(execution.model_proposals), 1)
        execution.chain.require_valid()
        return execution, model

    def _execute_meta(self, question: str):
        model = _QualifiedFixtureModel()
        execution = WorldModelProductAnswerService(
            view=self.meta_view,
            snapshot_bundles=self.meta_bundles,
            model_strategy=model,
            gateway_counters=model,
        ).execute(
            request_ref="runtime-random-topology",
            original_question=question,
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of("runtime-random-topology-permission"),
        )
        execution.chain.require_valid()
        self.assertEqual(execution.chain.provider_call_count, 1)
        return execution, model

    def test_inventory_paths_diff_and_gap_variants_use_closed_capabilities(self):
        cases = (
            (
                "分别列出 A 和 B 的全部递归 Maven reactor child modules（不含根项目 mall）。",
                GENERIC_QUERY_PLANNING,
            ),
            (
                "对比两个版本：各自有哪些由根 POM 的 modules 递归纳入的子项目？不要把 mall 根项目算进去。",
                GENERIC_QUERY_PLANNING,
            ),
            (
                "分别列出 A 和 B 中 mall-admin 到 mall-common 的全部简单内部依赖路径，并指出新增路径。",
                GENERIC_QUERY_PLANNING,
            ),
            (
                "从 admin 模块沿本地 POM 直接内部依赖走到 common，两个版本各有哪几条不重复节点的路线？哪条是 B 才有的？",
                GENERIC_QUERY_PLANNING,
            ),
            (
                "只说明 A 到 B 的内部 reactor child module 图变化。",
                ORDERED_DIFF_EXPRESSION,
            ),
            (
                "忽略外部依赖和代码行为，仅汇总这两个版本之间子模块成员及本地声明内部边的增删。",
                ORDERED_DIFF_EXPRESSION,
            ),
            (
                "为什么 B 新增了 mall-security？",
                VIEW_LIMITATION_AND_KNOWLEDGE_GAP,
            ),
            (
                "引入 security 模块的设计动机是什么？",
                VIEW_LIMITATION_AND_KNOWLEDGE_GAP,
            ),
        )
        for question, capability in cases:
            with self.subTest(question=question):
                execution, model = self._execute(question)
                self.assertEqual(model.capabilities, [capability])
                if capability == VIEW_LIMITATION_AND_KNOWLEDGE_GAP:
                    self.assertEqual(
                        execution.chain.assessment.needs[0].outcome,
                        WorldModelNeedOutcome.KNOWLEDGE_GAP,
                    )
                    self.assertIn(
                        "CHANGE_INTENT_OUTSIDE_STRUCTURE_COVERAGE",
                        execution.chain.draft.body,
                    )

    def test_frozen_supported_answers_expose_complete_formal_results(self):
        inventory, _ = self._execute(
            "分别列出 A 和 B 的全部递归 Maven reactor child modules（不含根项目 mall）。"
        )
        counts = [
            item.view_result.payload["module_count"]
            for item in inventory.chain.result_set.step_results
        ]
        self.assertEqual(counts, [6, 7])

        paths, _ = self._execute(
            "分别列出 A 和 B 中 mall-admin 到 mall-common 的全部简单内部依赖路径，并指出新增路径。"
        )
        path_counts = [
            item.view_result.payload["path_count"]
            for item in paths.chain.result_set.step_results
            if item.view_result.operation is StructureViewOperation.ALL_SIMPLE_PATHS
        ]
        self.assertEqual(path_counts, [1, 2])
        self.assertIn("mall-security", paths.chain.draft.body)

        diff, _ = self._execute(
            "只说明 A 到 B 的内部 reactor child module 图变化。"
        )
        payload = diff.chain.result_set.step_results[0].view_result.payload
        self.assertEqual(payload["entities"]["counts"]["added"], 1)
        self.assertEqual(payload["relations"]["counts"]["added"], 3)

    def test_direct_negative_and_same_name_identity_are_not_name_stitched(self):
        root, root_model = self._execute(
            "B 的根 POM dependencies 是否直接声明了 reactor child module mall-security？"
        )
        self.assertEqual(root_model.capabilities, [ENTITY_CANDIDATE_RESOLUTION])
        self.assertIn('"source":"com.macro.mall:mall"', root.chain.draft.body)
        self.assertIn('"com.macro.mall:mall-security":false', root.chain.draft.body)

        negative, negative_model = self._execute(
            "mall-admin 到 mall-search 是否存在本 Profile 内的内部依赖路径？"
        )
        self.assertEqual(negative_model.capabilities, [COMPLETE_NEGATIVE_ANSWER])
        self.assertTrue(
            all(
                item.outcome
                is WorldModelNeedOutcome.SATISFIED_SUPPORTED_NEGATIVE
                for item in negative.chain.assessment.needs
            )
        )
        self.assertIn("不存在从 com.macro.mall:mall-admin", negative.chain.draft.body)
        self.assertIn("不扩大为其他关系不存在", negative.chain.draft.body)

        billing, billing_model = self._execute(
            "maven-identity fixture 中 billing 实际直接依赖哪个 reactor 内的 common-lib？请给完整 GA；是否存在到另一个同名 common-lib GA 的边？",
            identity=True,
        )
        self.assertEqual(billing_model.capabilities, [ENTITY_CANDIDATE_RESOLUTION])
        self.assertIn('"org.example.shared:common-lib":true', billing.chain.draft.body)
        self.assertIn('"org.example.legacy:common-lib":false', billing.chain.draft.body)

        root_identity, _ = self._execute(
            "maven-identity fixture 的根 POM 是否本地直接依赖 shared common-lib？dependencyManagement 本身是否形成边？",
            identity=True,
        )
        self.assertIn(
            '"source":"org.example.root:structure-fixture"',
            root_identity.chain.draft.body,
        )
        self.assertIn(
            '"org.example.shared:common-lib":true',
            root_identity.chain.draft.body,
        )
        self.assertIn(
            '"dependency_management_forms_edge":false',
            root_identity.chain.draft.body,
        )

    def test_explicit_unknown_artifact_returns_zero_candidate_limitation(self):
        result, model = self._execute(
            "同名 artifact `definitely-missing-module` 有哪些候选？",
            identity=True,
        )

        self.assertEqual(model.capabilities, [ENTITY_CANDIDATE_RESOLUTION])
        self.assertEqual(model.provider_call_count, 1)
        self.assertEqual(
            result.chain.assessment.needs[0].outcome,
            WorldModelNeedOutcome.LIMITATION,
        )
        self.assertIn('"resolution_status":"ZERO"', result.chain.draft.body)
        self.assertIn('"candidate_count":0', result.chain.draft.body)

    def test_explicit_same_artifact_returns_ambiguous_candidate_limitation(self):
        result, model = self._execute(
            "同名 artifact `common-lib` 有哪些候选？",
            identity=True,
        )

        self.assertEqual(model.capabilities, [ENTITY_CANDIDATE_RESOLUTION])
        self.assertEqual(
            result.chain.assessment.needs[0].outcome,
            WorldModelNeedOutcome.LIMITATION,
        )
        self.assertIn('"resolution_status":"AMBIGUOUS"', result.chain.draft.body)
        self.assertIn('"candidate_count":2', result.chain.draft.body)
        self.assertIn("org.example.shared:common-lib", result.chain.draft.body)
        self.assertIn("org.example.legacy:common-lib", result.chain.draft.body)

    def test_ambiguous_group_excludes_unrelated_unique_mentions(self):
        result, model = self._execute(
            "同名 artifact `common-lib` 与 billing 有哪些候选？",
            identity=True,
        )

        self.assertEqual(
            result.chain.assessment.needs[0].outcome,
            WorldModelNeedOutcome.LIMITATION,
        )
        self.assertEqual(len(model.sealed_inputs[0]["candidate_refs"]), 2)
        self.assertIn('"candidate_count":2', result.chain.draft.body)

    def test_model_proposal_drift_fails_before_draft_delivery(self):
        model = _QualifiedFixtureModel()
        original = model.propose

        def drift(**kwargs):
            proposal = original(**kwargs)
            return SimpleNamespace(normalized_result={"operations": []})

        model.propose = drift
        service = WorldModelProductAnswerService(
            view=self.mall_view,
            snapshot_bundles=self.mall_bundles,
            model_strategy=model,
            gateway_counters=model,
        )
        with self.assertRaises(DomainError) as raised:
            service.execute(
                request_ref="drift",
                original_question=(
                    "分别列出 A 和 B 的全部递归 Maven reactor child modules（不含根项目 mall）。"
                ),
                response_language="zh-CN",
                classification="INTERNAL",
                permission_digest=digest_of("permission"),
            )
        self.assertEqual(
            raised.exception.details.get("reason_code"),
            "PRODUCT_MODEL_PROPOSAL_MISMATCH",
        )

    def test_runtime_random_identity_and_topology_are_not_name_bound(self):
        generated = self.meta_generation
        selectors = generated["question_selectors"]
        inventory, inventory_model = self._execute_meta(
            "列出 A/B 的全部 child module GA，并说明新增节点。"
        )
        self.assertEqual(inventory_model.capabilities, [ORDERED_DIFF_EXPRESSION])
        for node in (
            *generated["revision_a_oracle"]["nodes"],
            *generated["revision_b_oracle"]["nodes"],
        ):
            self.assertIn(node["ga"], inventory.chain.draft.body)
        self.assertIn(generated["a_to_b"]["added_nodes"][0], inventory.chain.draft.body)

        paths, paths_model = self._execute_meta(
            f"列出 {selectors['path_source_ga']} 到 "
            f"{selectors['path_target_ga']} 在 A/B 的全部简单路径。"
        )
        self.assertEqual(paths_model.capabilities, [GENERIC_QUERY_PLANNING])
        for path in (
            *generated["revision_a_oracle"]["all_simple_paths"],
            *generated["revision_b_oracle"]["all_simple_paths"],
        ):
            for ga in path:
                self.assertIn(ga, paths.chain.draft.body)

        changes, changes_model = self._execute_meta(
            "说明 A 到 B 的节点、边、path、label 和 version State 变化，"
            "且不把 State 变化误判为新 Root。"
        )
        self.assertEqual(changes_model.capabilities, [ORDERED_DIFF_EXPRESSION])
        for ga in generated["identity_state_counterexamples"].values():
            self.assertIn(ga, changes.chain.draft.body)
        self.assertIn(generated["a_to_b"]["added_nodes"][0], changes.chain.draft.body)

        left, right = selectors["same_artifact_distinct_ga"]
        identity, identity_model = self._execute_meta(
            f"区分 {left} 与 {right} 这两个同名 artifact。"
        )
        self.assertEqual(
            identity_model.capabilities,
            [ENTITY_CANDIDATE_RESOLUTION],
        )
        self.assertIn(left, identity.chain.draft.body)
        self.assertIn(right, identity.chain.draft.body)

    def test_product_implementation_contains_no_frozen_case_branch(self):
        source = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "software_world_model"
            / "interface"
            / "world_model_product.py"
        ).read_text(encoding="utf-8")
        for forbidden in (
            "WM-PRODUCT-",
            "MALL-MAVEN-STRUCTURE",
            "maven-identity-anti-name-stitch",
            "product-input-suite",
            "oracle_assertions",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
