from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from software_world_model.application_services.structure_view import (
    EntityResolutionStatus,
    StructureEntityArgument,
    StructureViewOperation,
    StructureViewService,
)
from software_world_model.application_services.world_model_answering import (
    EntitySelectorOrigin,
    InMemoryWorldModelAuthorityStore,
    InMemoryWorldModelEvaluationSink,
    OfflineWorldModelAnswerService,
    WorldModelAuthorityChain,
    WorldModelAnswerClaimProposal,
    WorldModelAnsweringService,
    WorldModelClaimKind,
    WorldModelDeliveryState,
    WorldModelDraftProposal,
    WorldModelEntitySelectorProposal,
    WorldModelJointConstraint,
    WorldModelJointConstraintKind,
    WorldModelNeed,
    WorldModelNeedOutcome,
    WorldModelQueryPlanProposal,
    WorldModelQueryStepProposal,
    WorldModelRequirementFidelityProposal,
    WorldModelRequirementProposal,
    WorldModelResponseControlService,
    WorldModelReviewDecision,
    WorldModelReviewDimension,
    WorldModelReviewDimensionAssessment,
    WorldModelReviewProposal,
)
from software_world_model.cross_cutting import DomainError, StableId, digest_of
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.knowledge_engine.structure import (
    EntityType,
    RelationPredicate,
)
from software_world_model.interface.world_model_evaluation import (
    world_model_evaluation_page_envelope,
)
from tests import test_iteration_003_g2_integration as _g2_integration


PROJECT_ROOT = Path(__file__).resolve().parents[1]
G3A_VALIDATION_ROOT = (
    PROJECT_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "g3a"
)


INVENTORY_NEED = WorldModelNeed(
    need_id="inventory-b",
    question="列出 B 的全部递归 Maven reactor child modules，不含 root。",
)
PATHS_NEED = WorldModelNeed(
    need_id="paths-b-admin-common",
    question=(
        "列出 B 中 mall-admin 到 mall-common 的全部简单内部依赖路径。"
    ),
)
DIFF_NEED = WorldModelNeed(
    need_id="diff-a1-b",
    question="说明有序 A1 到 B 的内部 reactor 模块图变化。",
)
ALL_NEEDS = (INVENTORY_NEED, PATHS_NEED, DIFF_NEED)
ORDER_CONSTRAINT_ID = "ordered-a1-b"
APPROVED_REVIEW_DIMENSIONS = tuple(
    WorldModelReviewDimensionAssessment(
        dimension=dimension,
        decision=WorldModelReviewDecision.APPROVE,
    )
    for dimension in WorldModelReviewDimension
)


class MallRequirementPlanner:
    strategy_ref = "iter-003-g3a-mall-requirement-planner@1"

    def __init__(self, *, snapshot_a1: StableId, snapshot_b: StableId) -> None:
        self.snapshot_a1 = snapshot_a1
        self.snapshot_b = snapshot_b

    def plan(self, *, question, invocation):
        return WorldModelRequirementProposal(
            original_question=question.original_question,
            response_language=question.response_language,
            needs=ALL_NEEDS,
            joint_constraints=(
                WorldModelJointConstraint(
                    constraint_id=ORDER_CONSTRAINT_ID,
                    need_ids=tuple(item.need_id for item in ALL_NEEDS),
                    kind=WorldModelJointConstraintKind.ORDERED_READ_SET,
                    description="A1 必须是基础快照，B 必须是目标快照。",
                    base_snapshot_id=self.snapshot_a1,
                    target_snapshot_id=self.snapshot_b,
                ),
            ),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class MallRequirementReviewer:
    strategy_ref = "iter-003-g3a-mall-requirement-reviewer@1"

    def review(self, *, question, proposal, invocation):
        del question
        return WorldModelRequirementFidelityProposal(
            decision=WorldModelReviewDecision.APPROVE,
            accepted_need_ids=tuple(item.need_id for item in proposal.needs),
            accepted_constraint_ids=tuple(
                item.constraint_id for item in proposal.joint_constraints
            ),
            original_question_preserved=True,
            all_material_questions_covered=True,
            findings=(),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class MallQueryPlanner:
    strategy_ref = "iter-003-g3a-mall-query-planner@1"

    def __init__(self, *, snapshot_a1: StableId, snapshot_b: StableId) -> None:
        self.snapshot_a1 = snapshot_a1
        self.snapshot_b = snapshot_b

    def plan(self, *, question, requirement, invocation):
        del question
        system = WorldModelEntitySelectorProposal(
            selector_id="system-b",
            need_ids=(INVENTORY_NEED.need_id,),
            snapshot_id=self.snapshot_b,
            origin=EntitySelectorOrigin.MENTION,
            mention="mall",
            entity_type=EntityType.SOFTWARE_SYSTEM,
        )
        admin = WorldModelEntitySelectorProposal(
            selector_id="admin-b",
            need_ids=(PATHS_NEED.need_id,),
            snapshot_id=self.snapshot_b,
            origin=EntitySelectorOrigin.MENTION,
            mention="mall-admin",
            entity_type=EntityType.MAVEN_MODULE,
        )
        common = WorldModelEntitySelectorProposal(
            selector_id="common-b",
            need_ids=(PATHS_NEED.need_id,),
            snapshot_id=self.snapshot_b,
            origin=EntitySelectorOrigin.MENTION,
            mention="mall-common",
            entity_type=EntityType.MAVEN_MODULE,
        )
        steps = (
            WorldModelQueryStepProposal.create(
                step_id=INVENTORY_NEED.need_id,
                need_ids=(INVENTORY_NEED.need_id,),
                operation=StructureViewOperation.CHILD_MODULE_INVENTORY,
                arguments={"system": system.selector_id},
                constraint_ids=(ORDER_CONSTRAINT_ID,),
            ),
            WorldModelQueryStepProposal.create(
                step_id=PATHS_NEED.need_id,
                need_ids=(PATHS_NEED.need_id,),
                operation=StructureViewOperation.ALL_SIMPLE_PATHS,
                arguments={
                    "source": admin.selector_id,
                    "target": common.selector_id,
                },
                parameters={"predicate": RelationPredicate.DEPENDS_ON.value},
                constraint_ids=(ORDER_CONSTRAINT_ID,),
            ),
            WorldModelQueryStepProposal.create(
                step_id=DIFF_NEED.need_id,
                need_ids=(DIFF_NEED.need_id,),
                operation=StructureViewOperation.ORDERED_SNAPSHOT_DIFF,
                parameters={
                    "base_snapshot_id": self.snapshot_a1.value,
                    "target_snapshot_id": self.snapshot_b.value,
                },
                constraint_ids=(ORDER_CONSTRAINT_ID,),
            ),
        )
        return WorldModelQueryPlanProposal(
            requirement_id=requirement.requirement_id,
            requirement_digest=requirement.digest,
            read_set_digest=requirement.read_authority.read_set_digest,
            ordered_bundle_digest=requirement.read_authority.ordered_bundle_digest,
            selectors=(system, admin, common),
            steps=steps,
            explicit_gaps=(),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class MallDraftGenerator:
    strategy_ref = "iter-003-g3a-mall-draft-generator@1"

    def draft(
        self,
        *,
        question,
        requirement,
        plan,
        result_set,
        assessment,
        invocation,
    ):
        del question, requirement, plan
        by_step = {
            item.step_id: item for item in result_set.step_results
        }
        inventory = by_step[INVENTORY_NEED.need_id].view_result
        paths = by_step[PATHS_NEED.need_id].view_result
        diff = by_step[DIFF_NEED.need_id].view_result
        assessments = {item.need_id: item for item in assessment.needs}
        texts = {
            INVENTORY_NEED.need_id: (
                "B 包含 "
                f"{inventory.payload['module_count']} 个 reactor child modules。"
            ),
            PATHS_NEED.need_id: (
                "B 中 mall-admin 到 mall-common 共有 "
                f"{paths.payload['path_count']} 条简单内部依赖路径。"
            ),
            DIFF_NEED.need_id: (
                "A1 到 B 新增 "
                f"{diff.payload['entities']['counts']['added']} 个实体和 "
                f"{diff.payload['relations']['counts']['added']} 条关系。"
            ),
        }
        return WorldModelDraftProposal(
            assessment_id=assessment.assessment_id,
            assessment_digest=assessment.digest,
            claims=tuple(
                WorldModelAnswerClaimProposal(
                    claim_id=f"claim:{need.need_id}",
                    need_id=need.need_id,
                    kind=WorldModelClaimKind.QUERY_RESULT,
                    text=texts[need.need_id],
                    step_result_ids=assessments[need.need_id].step_result_ids,
                )
                for need in ALL_NEEDS
            ),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class MallAnswerReviewer:
    strategy_ref = "iter-003-g3a-mall-answer-reviewer@1"

    def review(
        self,
        *,
        question,
        requirement,
        plan,
        result_set,
        assessment,
        draft,
        invocation,
    ):
        del plan, assessment
        return WorldModelReviewProposal(
            decision=WorldModelReviewDecision.APPROVE,
            dimensions=APPROVED_REVIEW_DIMENSIONS,
            checked_need_ids=tuple(item.need_id for item in requirement.needs),
            checked_constraint_ids=tuple(
                item.constraint_id for item in requirement.joint_constraints
            ),
            checked_step_result_ids=tuple(
                item.step_result_id for item in result_set.step_results
            ),
            original_question_digest=digest_of(question.original_question),
            draft_digest=draft.digest,
            read_set_digest=question.read_authority.read_set_digest,
            finding_codes=(),
            findings=(),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class Iteration003G3aMallIntegrationTests(unittest.TestCase):
    """Run the G3a chain against G1/G2's real frozen mall bundles."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.g2_fixture = _g2_integration.Iteration003G2MallIntegrationTests(
            methodName="runTest"
        )
        cls.g2_fixture.setUp()
        cls.addClassCleanup(cls.g2_fixture.doCleanups)
        g1 = cls.g2_fixture.fixture

        revision_a = g1.oracle["repository"]["revision_a"]
        revision_b = g1.oracle["repository"]["revision_b"]
        cls.snapshot_a1_result = g1._successful_cli(
            *g1._build_arguments(
                revision_a,
                key="iter-003-g3a-mall-a1",
            )
        )
        cls.snapshot_b_result = g1._successful_cli(
            *g1._build_arguments(
                revision_b,
                key="iter-003-g3a-mall-b",
                expected_current=cls.snapshot_a1_result["snapshot"]["snapshot_id"],
            )
        )
        cls.snapshot_a1 = StableId(
            cls.snapshot_a1_result["snapshot"]["snapshot_id"]
        )
        cls.snapshot_b = StableId(
            cls.snapshot_b_result["snapshot"]["snapshot_id"]
        )
        primary_snapshot_ids = (cls.snapshot_a1.value, cls.snapshot_b.value)
        primary_session = cls.g2_fixture._open_ordered_session(
            name="g3a-a1-b-primary",
            task_marker="7",
            snapshot_ids=primary_snapshot_ids,
        )
        secondary_session = cls.g2_fixture._open_ordered_session(
            name="g3a-b-a1-secondary",
            task_marker="8",
            snapshot_ids=(cls.snapshot_b.value, cls.snapshot_a1.value),
        )

        snapshot_receipts = {
            "a1": cls.g2_fixture._export_snapshot_bundle(
                "g3a-a1", cls.snapshot_a1.value
            ),
            "b": cls.g2_fixture._export_snapshot_bundle(
                "g3a-b", cls.snapshot_b.value
            ),
        }
        ordered_receipts = {
            "primary": cls.g2_fixture._export_ordered_bundle(
                "g3a-a1-b-primary", primary_session["session_id"]
            ),
            "secondary": cls.g2_fixture._export_ordered_bundle(
                "g3a-b-a1-secondary", secondary_session["session_id"]
            ),
        }
        cls.snapshot_receipts = snapshot_receipts
        cls.ordered_receipts = ordered_receipts
        cls.g2_fixture._assert_no_payload(
            {
                "snapshots": {
                    name: json.loads(
                        Path(receipt["stored_bundle"]["locator"]).read_bytes()
                    )
                    for name, receipt in snapshot_receipts.items()
                },
                "ordered": {
                    name: json.loads(
                        Path(receipt["stored_bundle"]["locator"]).read_bytes()
                    )
                    for name, receipt in ordered_receipts.items()
                },
            }
        )

        bundle_store = FileStructureReadBundleStore()
        cls.loaded = {
            name: bundle_store.read_snapshot(
                receipt["stored_bundle"]["locator"]
            )
            for name, receipt in snapshot_receipts.items()
        }
        primary_envelope, _ = bundle_store.read_ordered(
            ordered_receipts["primary"]["stored_bundle"]["locator"]
        )
        secondary_envelope, _ = bundle_store.read_ordered(
            ordered_receipts["secondary"]["stored_bundle"]["locator"]
        )
        cls.primary_view = StructureViewService(
            primary_envelope,
            (cls.loaded["a1"], cls.loaded["b"]),
        )
        cls.secondary_view = StructureViewService(
            secondary_envelope,
            (cls.loaded["b"], cls.loaded["a1"]),
        )

    @staticmethod
    def _reason(error: DomainError) -> str | None:
        return error.details.get("reason_code")

    def _execute_chain(self):
        store = InMemoryWorldModelAuthorityStore()
        answering = WorldModelAnsweringService(store, self.primary_view)
        responses = WorldModelResponseControlService(store, answering)
        offline = OfflineWorldModelAnswerService(
            answering=answering,
            responses=responses,
        )
        sink = InMemoryWorldModelEvaluationSink()
        chain = offline.execute(
            request_ref="iter-003-g3a-real-mall",
            original_question=(
                "在调用方给定的有序 A1→B Read Set 上，"
                "列出 B 的全部递归 "
                "reactor child modules、mall-admin 到 mall-common 的全部"
                "简单内部"
                "依赖路径，并说明 A1→B 的内部模块图变化。"
            ),
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of("iter-003-g3a-mall-permission"),
            requirement_planner=MallRequirementPlanner(
                snapshot_a1=self.snapshot_a1,
                snapshot_b=self.snapshot_b,
            ),
            requirement_reviewer=MallRequirementReviewer(),
            query_planner=MallQueryPlanner(
                snapshot_a1=self.snapshot_a1,
                snapshot_b=self.snapshot_b,
            ),
            draft_generator=MallDraftGenerator(),
            answer_reviewer=MallAnswerReviewer(),
            sink=sink,
        )
        return store, answering, sink, chain

    def test_real_mall_bundles_drive_the_complete_offline_authority_chain(self):
        _, _, sink, chain = self._execute_chain()

        by_step = {
            item.step_id: item.view_result
            for item in chain.result_set.step_results
        }
        inventory = by_step[INVENTORY_NEED.need_id]
        paths = by_step[PATHS_NEED.need_id]
        diff = by_step[DIFF_NEED.need_id]
        self.assertEqual(inventory.payload["module_count"], 7)
        self.assertEqual(
            {item["canonical_gav"] for item in inventory.payload["modules"]},
            set(
                self.g2_fixture.fixture.oracle["revision_b_oracle"]
                ["reactor_child_module_gavs"]
            ),
        )
        self.assertEqual(paths.payload["path_count"], 2)
        self.assertEqual(
            self.g2_fixture._path_artifact_ids(self.loaded["b"][0], paths),
            self.g2_fixture.fixture.oracle["revision_b_oracle"]
            ["admin_to_common_all_simple_paths"],
        )
        self.assertEqual(
            diff.payload["entities"]["counts"],
            {"added": 1, "removed": 0, "state_changed": 7, "unchanged": 0},
        )
        self.assertEqual(
            diff.payload["relations"]["counts"],
            {"added": 3, "removed": 0, "state_changed": 11, "unchanged": 0},
        )

        self.assertTrue(chain.assessment.sufficient)
        self.assertEqual(
            {item.outcome for item in chain.assessment.needs},
            {WorldModelNeedOutcome.SATISFIED},
        )
        self.assertEqual(len(chain.assessment.joint_constraints), 1)
        self.assertTrue(chain.assessment.joint_constraints[0].satisfied)
        self.assertEqual(
            chain.requirement.joint_constraints[0].kind,
            WorldModelJointConstraintKind.ORDERED_READ_SET,
        )
        self.assertTrue(
            all(
                step.constraint_ids == (ORDER_CONSTRAINT_ID,)
                for step in chain.plan.steps
            )
        )
        self.assertEqual(
            chain.question.read_authority.session_id,
            self.primary_view.session_id,
        )
        self.assertEqual(
            chain.question.read_authority.snapshot_ids,
            (self.snapshot_a1, self.snapshot_b),
        )
        self.assertFalse(hasattr(self.primary_view, "source"))
        self.assertFalse(hasattr(self.primary_view, "repository"))
        self.assertEqual(chain.provider_call_count, 0)
        self.assertEqual(chain.network_operation_count, 0)
        self.assertEqual(chain.delivery.state, WorldModelDeliveryState.DELIVERED)
        self.assertEqual(sink.delivery_count, 1)
        chain.require_valid()
        summary = {
            "schema": "iteration-003-g3a-mall-authority-summary@1",
            "question_id": chain.question.question_id.value,
            "chain_digest": chain.digest.value,
            "session_id": chain.question.read_authority.session_id.value,
            "read_set_digest": (
                chain.question.read_authority.read_set_digest.value
            ),
            "ordered_bundle_digest": (
                chain.question.read_authority.ordered_bundle_digest.value
            ),
            "snapshot_ids": [
                item.value
                for item in chain.question.read_authority.snapshot_ids
            ],
            "need_outcomes": {
                item.need_id: item.outcome.value
                for item in chain.assessment.needs
            },
            "joint_assessments": [
                item.canonical_value()
                for item in chain.assessment.joint_constraints
            ],
            "result_counts": {
                "inventory_b": inventory.payload["module_count"],
                "paths_b": paths.payload["path_count"],
                "diff_entities_added": diff.payload["entities"]["counts"][
                    "added"
                ],
                "diff_relations_added": diff.payload["relations"]["counts"][
                    "added"
                ],
            },
            "delivery_state": chain.delivery.state.value,
            "provider_call_count": chain.provider_call_count,
            "network_operation_count": chain.network_operation_count,
        }
        self._write_report(summary)
        self._stage_isolation_if_requested(summary, chain)

    def test_foreign_session_candidate_argument_is_rejected(self):
        foreign_candidate = self.secondary_view.entity_candidates(
            snapshot_id=self.snapshot_b,
            mention="mall-admin",
            entity_type=EntityType.MAVEN_MODULE,
        )
        local_candidate = self.primary_view.entity_candidates(
            snapshot_id=self.snapshot_b,
            mention="mall-admin",
            entity_type=EntityType.MAVEN_MODULE,
        )
        self.assertEqual(
            foreign_candidate.payload["resolution_status"],
            EntityResolutionStatus.UNIQUE.value,
        )
        self.assertEqual(
            foreign_candidate.payload["candidates"],
            local_candidate.payload["candidates"],
        )
        self.assertNotEqual(foreign_candidate.session_id, local_candidate.session_id)
        foreign_argument = StructureEntityArgument.from_unique_candidate(
            foreign_candidate
        )

        with self.assertRaises(DomainError) as raised:
            self.primary_view.direct_neighborhood(entity=foreign_argument)

        self.assertEqual(
            self._reason(raised.exception),
            "VIEW_ENTITY_ARGUMENT_SESSION_MISMATCH",
        )

    def test_result_cannot_be_replayed_under_another_read_authority(self):
        store, _, _, chain = self._execute_chain()
        self.assertEqual(
            set(self.primary_view.snapshot_ids),
            set(self.secondary_view.snapshot_ids),
        )
        self.assertNotEqual(
            self.primary_view.snapshot_ids,
            self.secondary_view.snapshot_ids,
        )
        self.assertNotEqual(
            self.primary_view.read_set_digest,
            self.secondary_view.read_set_digest,
        )
        self.assertNotEqual(
            self.primary_view.ordered_bundle_digest,
            self.secondary_view.ordered_bundle_digest,
        )
        foreign_answering = WorldModelAnsweringService(store, self.secondary_view)

        with self.assertRaises(DomainError) as raised:
            foreign_answering.verify_query_result_set(
                chain.result_set.result_set_id
            )

        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_QUERY_RESULT_READ_SET_MISMATCH",
        )

    def test_isolation_staging_rejects_a_commit_label_other_than_head(self):
        _, _, _, chain = self._execute_chain()
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory).resolve() / "stage"
            with patch.dict(
                os.environ,
                {
                    "ITER003_G3A_STAGE_DIR": str(stage),
                    "ITER003_G3A_IMPLEMENTATION_COMMIT": "0" * 40,
                },
                clear=False,
            ):
                with self.assertRaisesRegex(
                    AssertionError,
                    "exact clean Git checkpoint",
                ):
                    self._stage_isolation_if_requested({}, chain)

    @staticmethod
    def _write_report(summary: dict[str, object]) -> None:
        configured = os.environ.get("ITER003_G3A_REPORT_DIR")
        if configured is None:
            return
        report_root = Path(configured)
        report_root.mkdir(parents=True, exist_ok=True)
        (report_root / "g3a-mall-authority-summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )

    def _stage_isolation_if_requested(
        self,
        summary: dict[str, object],
        chain: WorldModelAuthorityChain,
    ) -> None:
        configured = os.environ.get("ITER003_G3A_STAGE_DIR")
        if configured is None:
            return
        implementation_commit = os.environ.get(
            "ITER003_G3A_IMPLEMENTATION_COMMIT"
        )
        if (
            implementation_commit is None
            or len(implementation_commit) != 40
            or any(character not in "0123456789abcdef" for character in implementation_commit)
        ):
            raise AssertionError(
                "ITER003_G3A_IMPLEMENTATION_COMMIT must be exact lowercase 40-hex"
            )
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        implementation_tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        worktree_status = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all"],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        if head != implementation_commit or worktree_status:
            raise AssertionError(
                "G3a isolation staging requires the exact clean Git checkpoint"
            )
        chain.require_valid()
        expected_page_digest = world_model_evaluation_page_envelope(
            chain,
            implementation_commit,
        )["page_digest"]
        if not isinstance(expected_page_digest, str):
            raise AssertionError("connected PAGE digest must be canonical text")
        stage_root = Path(configured)
        if (
            not stage_root.is_absolute()
            or stage_root.resolve(strict=False) != stage_root
            or stage_root.exists()
        ):
            raise AssertionError(
                "ITER003_G3A_STAGE_DIR must be a new canonical absolute path"
            )
        answer_package = stage_root / "answer" / "package"
        answer_bundles = stage_root / "answer" / "bundles"
        answer_output = stage_root / "answer" / "output"
        projector_package = stage_root / "projector" / "package"
        projector_input = stage_root / "projector" / "input"
        projector_store = stage_root / "projector" / "store"
        projector_output = stage_root / "projector" / "output"
        for directory in (
            answer_package,
            answer_bundles,
            answer_output,
            projector_package,
            projector_input,
            projector_store,
            projector_output,
        ):
            directory.mkdir(parents=True)
        ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
        for package_root, workload_name in (
            (answer_package, "answer_workload.py"),
            (projector_package, "projection_workload.py"),
        ):
            shutil.copytree(
                PROJECT_ROOT / "src" / "software_world_model",
                package_root / "software_world_model",
                ignore=ignore,
            )
            shutil.copy2(
                G3A_VALIDATION_ROOT / workload_name,
                package_root / workload_name,
            )
        staged_bundles: dict[str, Path] = {}
        for name, receipt in sorted(self.snapshot_receipts.items()):
            target = answer_bundles / f"{name}.snapshot.json"
            shutil.copy2(Path(receipt["stored_bundle"]["locator"]), target)
            staged_bundles[name] = target
        primary = answer_bundles / "a1-b.ordered.json"
        shutil.copy2(
            Path(
                self.ordered_receipts["primary"]["stored_bundle"]["locator"]
            ),
            primary,
        )
        staged_bundles["a1-b"] = primary
        store_marker = projector_store / "manifest.json"
        store_marker.write_text(
            json.dumps(
                {
                    "schema": "iteration-003-g3a-empty-projection-store@1",
                    "evidence_payload_count": 0,
                },
                sort_keys=True,
                separators=(",", ":"),
            ),
            encoding="utf-8",
        )
        evidence_root = stage_root.parent
        forbidden_database = evidence_root / "g3a-authority-with-evidence.sqlite3"
        if forbidden_database.exists():
            raise AssertionError("G3a forbidden authority DB already exists")
        shutil.copy2(self.g2_fixture.fixture.database, forbidden_database)
        config_path = evidence_root / "isolation-config.json"
        if config_path.exists():
            raise AssertionError("G3a isolation config already exists")
        answer_page = answer_output / "authority-page.json"
        answer_summary = answer_output / "answer-summary.json"
        projector_page = projector_input / "authority-page.json"
        projection_summary = projector_output / "projection-summary.json"
        mall_repository = _g2_integration._g1_integration.MALL_REPOSITORY
        config = {
            "schema": "iteration-003-g2-isolation-config@1",
            "stage_root": str(stage_root),
            "python_executable": str(Path(sys.executable).resolve(strict=True)),
            "source_remote": {"host": "github.com", "port": 443},
            "public_endpoint": {"host": "1.1.1.1", "port": 443},
            "dns_host": "example.com",
            "forbidden": {
                "file": str(mall_repository / "pom.xml"),
                "sqlite": str(forbidden_database),
                "git_root": str(mall_repository),
                "git_marker": str(mall_repository / ".git" / "HEAD"),
            },
            "answer": {
                "package_root": str(answer_package),
                "bundle_root": str(answer_bundles),
                "output_root": str(answer_output),
                "package_canary": str(answer_package / "answer_workload.py"),
                "bundle_canary": str(staged_bundles["a1"]),
                "sealed_result": str(answer_page),
                "workload": {
                    "entrypoint": "answer_workload.py",
                    "argv": [
                        "--ordered-bundle",
                        str(staged_bundles["a1-b"]),
                        "--a1-bundle",
                        str(staged_bundles["a1"]),
                        "--b-bundle",
                        str(staged_bundles["b"]),
                        "--implementation-commit",
                        implementation_commit,
                        "--authority-page-output",
                        str(answer_page),
                        "--summary-output",
                        str(answer_summary),
                    ],
                    "stdout_output": "workload-stdout.json",
                    "expected_outputs": [
                        "answer-summary.json",
                        "authority-page.json",
                        "workload-stdout.json",
                    ],
                },
            },
            "projector": {
                "package_root": str(projector_package),
                "sealed_result": str(projector_page),
                "store_root": str(projector_store),
                "store_allowlist": ["manifest.json"],
                "output_root": str(projector_output),
                "package_canary": str(
                    projector_package / "projection_workload.py"
                ),
                "store_canary": str(store_marker),
                "workload": {
                    "entrypoint": "projection_workload.py",
                    "argv": [
                        "--authority-page",
                        str(projector_page),
                        "--expected-implementation-commit",
                        implementation_commit,
                        "--expected-page-digest",
                        expected_page_digest,
                        "--summary-output",
                        str(projection_summary),
                    ],
                    "stdout_output": "workload-stdout.json",
                    "expected_outputs": [
                        "projection-summary.json",
                        "workload-stdout.json",
                    ],
                },
            },
            "timeout_seconds": 120,
        }
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        (evidence_root / "staging-summary.json").write_text(
            json.dumps(
                {
                    "schema": "iteration-003-g3a-staging-summary@1",
                    "implementation_commit": implementation_commit,
                    "implementation_tree": implementation_tree,
                    "worktree_clean_before_staging": True,
                    "expected_page_digest": expected_page_digest,
                    "isolation_harness": (
                        "validation.structure_world_model_iteration_003.isolation.run_isolation"
                    ),
                    "isolation_config": str(config_path),
                    "stage_root": str(stage_root),
                    "connected_summary": summary,
                    "projection_store_payload_count": 0,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
