#!/usr/bin/env python3
"""Run the full deterministic G3a authority chain from exact Read Bundles."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import stat

from software_world_model.application_services.structure_view import (
    StructureViewOperation,
    StructureViewService,
)
from software_world_model.application_services.world_model_answering import (
    EntitySelectorOrigin,
    InMemoryWorldModelAuthorityStore,
    InMemoryWorldModelEvaluationSink,
    OfflineWorldModelAnswerService,
    WorldModelAnswerClaimProposal,
    WorldModelAnsweringService,
    WorldModelClaimKind,
    WorldModelDraftProposal,
    WorldModelEntitySelectorProposal,
    WorldModelJointConstraint,
    WorldModelJointConstraintKind,
    WorldModelNeed,
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
from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.interface.world_model_evaluation import (
    write_world_model_evaluation_page,
)
from software_world_model.knowledge_engine.structure import (
    EntityType,
    RelationPredicate,
)


INVENTORY_NEED = WorldModelNeed(
    need_id="inventory-b",
    question="列出 B 的全部递归 Maven reactor child modules，不含 root。",
)
PATHS_NEED = WorldModelNeed(
    need_id="paths-b-admin-common",
    question="列出 B 中 mall-admin 到 mall-common 的全部简单内部依赖路径。",
)
DIFF_NEED = WorldModelNeed(
    need_id="diff-a1-b",
    question="说明有序 A1 到 B 的内部 reactor 模块图变化。",
)
NEEDS = (INVENTORY_NEED, PATHS_NEED, DIFF_NEED)
ORDER_CONSTRAINT_ID = "ordered-a1-b"


class RequirementPlanner:
    strategy_ref = "iter-003-g3a-mall-requirement-planner@1"

    def __init__(self, snapshot_a1, snapshot_b) -> None:
        self.snapshot_a1 = snapshot_a1
        self.snapshot_b = snapshot_b

    def plan(self, *, question, invocation):
        return WorldModelRequirementProposal(
            original_question=question.original_question,
            response_language=question.response_language,
            needs=NEEDS,
            joint_constraints=(
                WorldModelJointConstraint(
                    constraint_id=ORDER_CONSTRAINT_ID,
                    need_ids=tuple(item.need_id for item in NEEDS),
                    kind=WorldModelJointConstraintKind.ORDERED_READ_SET,
                    description="A1 必须是基础快照，B 必须是目标快照。",
                    base_snapshot_id=self.snapshot_a1,
                    target_snapshot_id=self.snapshot_b,
                ),
            ),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class RequirementReviewer:
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


class QueryPlanner:
    strategy_ref = "iter-003-g3a-mall-query-planner@1"

    def __init__(self, snapshot_a1, snapshot_b) -> None:
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
        constraint = (ORDER_CONSTRAINT_ID,)
        steps = (
            WorldModelQueryStepProposal.create(
                step_id=INVENTORY_NEED.need_id,
                need_ids=(INVENTORY_NEED.need_id,),
                operation=StructureViewOperation.CHILD_MODULE_INVENTORY,
                arguments={"system": system.selector_id},
                constraint_ids=constraint,
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
                constraint_ids=constraint,
            ),
            WorldModelQueryStepProposal.create(
                step_id=DIFF_NEED.need_id,
                need_ids=(DIFF_NEED.need_id,),
                operation=StructureViewOperation.ORDERED_SNAPSHOT_DIFF,
                parameters={
                    "base_snapshot_id": self.snapshot_a1.value,
                    "target_snapshot_id": self.snapshot_b.value,
                },
                constraint_ids=constraint,
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


class DraftGenerator:
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
        by_step = {item.step_id: item for item in result_set.step_results}
        by_need = {item.need_id: item for item in assessment.needs}
        inventory = by_step[INVENTORY_NEED.need_id].view_result
        paths = by_step[PATHS_NEED.need_id].view_result
        diff = by_step[DIFF_NEED.need_id].view_result
        text = {
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
                    text=text[need.need_id],
                    step_result_ids=by_need[need.need_id].step_result_ids,
                )
                for need in NEEDS
            ),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class AnswerReviewer:
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
            dimensions=tuple(
                WorldModelReviewDimensionAssessment(
                    dimension=dimension,
                    decision=WorldModelReviewDecision.APPROVE,
                )
                for dimension in WorldModelReviewDimension
            ),
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ordered-bundle", required=True)
    parser.add_argument("--a1-bundle", required=True)
    parser.add_argument("--b-bundle", required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--authority-page-output", required=True)
    parser.add_argument("--summary-output", required=True)
    return parser


def _write_new(path_text: str, payload: bytes) -> None:
    path = Path(path_text)
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise ValueError("output path must be canonical and absolute")
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("output parent must be canonical")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        remaining = memoryview(payload)
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError("output is not a regular file")
    finally:
        os.close(descriptor)


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    bundle_store = FileStructureReadBundleStore()
    ordered, _ = bundle_store.read_ordered(arguments.ordered_bundle)
    a1 = bundle_store.read_snapshot(arguments.a1_bundle)
    b = bundle_store.read_snapshot(arguments.b_bundle)
    view = StructureViewService(ordered, (a1, b))
    snapshot_a1, snapshot_b = view.snapshot_ids
    store = InMemoryWorldModelAuthorityStore()
    answering = WorldModelAnsweringService(store, view)
    responses = WorldModelResponseControlService(store, answering)
    sink = InMemoryWorldModelEvaluationSink()
    chain = OfflineWorldModelAnswerService(
        answering=answering,
        responses=responses,
    ).execute(
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
        requirement_planner=RequirementPlanner(snapshot_a1, snapshot_b),
        requirement_reviewer=RequirementReviewer(),
        query_planner=QueryPlanner(snapshot_a1, snapshot_b),
        draft_generator=DraftGenerator(),
        answer_reviewer=AnswerReviewer(),
        sink=sink,
    )
    by_step = {
        item.step_id: item.view_result for item in chain.result_set.step_results
    }
    inventory_count = by_step[INVENTORY_NEED.need_id].payload["module_count"]
    path_count = by_step[PATHS_NEED.need_id].payload["path_count"]
    diff = by_step[DIFF_NEED.need_id].payload
    if (
        inventory_count != 7
        or path_count != 2
        or diff["entities"]["counts"]["added"] != 1
        or diff["relations"]["counts"]["added"] != 3
        or not chain.assessment.sufficient
        or not all(item.satisfied for item in chain.assessment.joint_constraints)
        or chain.provider_call_count != 0
        or chain.network_operation_count != 0
        or sink.delivery_count != 1
    ):
        raise RuntimeError("isolated G3a authority chain differs from frozen oracle")
    page_digest = write_world_model_evaluation_page(
        arguments.authority_page_output,
        chain,
        arguments.implementation_commit,
    )
    summary = {
        "schema": "iteration-003-g3a-answer-workload@1",
        "status": "PASS",
        "question_id": chain.question.question_id.value,
        "chain_digest": chain.digest.value,
        "page_digest": page_digest.value,
        "read_set_digest": chain.question.read_authority.read_set_digest.value,
        "inventory_count": inventory_count,
        "path_count": path_count,
        "diff_entities_added": 1,
        "diff_relations_added": 3,
        "provider_call_count": chain.provider_call_count,
        "network_operation_count": chain.network_operation_count,
    }
    _write_new(arguments.summary_output, canonical_json_bytes(summary))
    print(canonical_json_bytes(summary).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
