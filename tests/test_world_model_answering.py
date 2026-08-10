from __future__ import annotations

from dataclasses import replace
import unittest

from software_world_model.application_services.structure_view import (
    EntityResolutionStatus,
    StructureViewOperation,
)
from software_world_model.application_services.world_model_answering import (
    EntitySelectorOrigin,
    InMemoryWorldModelAuthorityStore,
    InMemoryWorldModelEvaluationSink,
    OfflineWorldModelAnswerService,
    QueryStepState,
    WorldModelAnswerClaimProposal,
    WorldModelAnswerReviewer,
    WorldModelAnsweringService,
    WorldModelAuthorityChain,
    WorldModelClaimKind,
    WorldModelDelivery,
    WorldModelDeliveryReceipt,
    WorldModelDeliveryState,
    WorldModelDraftGenerator,
    WorldModelDraftProposal,
    WorldModelEntitySelectorProposal,
    WorldModelExplicitEntityRef,
    WorldModelJointConstraint,
    WorldModelJointConstraintKind,
    WorldModelNeed,
    WorldModelNeedOutcome,
    WorldModelQueryPlan,
    WorldModelQueryPlanProposal,
    WorldModelQueryPlanner,
    WorldModelQueryResultSet,
    WorldModelQueryStepProposal,
    WorldModelRequirementFidelityProposal,
    WorldModelRequirementFidelityReviewer,
    WorldModelRequirementPlanner,
    WorldModelRequirementProposal,
    WorldModelResourceLimits,
    WorldModelResponseControlService,
    WorldModelReviewDecision,
    WorldModelReviewDimension,
    WorldModelReviewDimensionAssessment,
    WorldModelReviewProposal,
)
from software_world_model.cross_cutting import (
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine.structure import (
    EntityType,
    RelationPredicate,
)
from tests import test_structure_view as _structure_view_tests


INVENTORY_NEED = WorldModelNeed(
    need_id="inventory-b",
    question="列出 B 的全部 reactor child modules。",
)
DIFF_NEED = WorldModelNeed(
    need_id="diff-a-b",
    question="比较 A 到 B 的结构变化。",
)
ORDERED_CONSTRAINT_ID = "ordered-a-b"
APPROVED_REVIEW_DIMENSIONS = tuple(
    WorldModelReviewDimensionAssessment(
        dimension=dimension,
        decision=WorldModelReviewDecision.APPROVE,
    )
    for dimension in WorldModelReviewDimension
)


def _redigest_record(record, domain: str):
    core = {
        key: value
        for key, value in record.canonical_value().items()
        if key != "digest"
    }
    return replace(record, digest=digest_of([domain, core]))


def _resign_stable_record(
    record,
    *,
    id_field: str,
    stable_kind: str,
    id_domain: str,
    digest_domain: str,
):
    core = {
        key: value
        for key, value in record.canonical_value().items()
        if key not in {id_field, "digest"}
    }
    identity = digest_of([id_domain, core])
    record_id = StableId(f"{stable_kind}_{identity.value[-32:]}")
    return replace(
        record,
        **{
            id_field: record_id,
            "digest": digest_of(
                [digest_domain, {id_field: record_id.value, **core}]
            ),
        },
    )


def _redigest_delivery(delivery: WorldModelDelivery) -> WorldModelDelivery:
    core = {
        key: value
        for key, value in delivery.canonical_value().items()
        if key not in {"delivery_id", "digest"}
    }
    return replace(
        delivery,
        digest=digest_of(["WORLD_MODEL_DELIVERY@1", core]),
    )


def _redigest_chain(chain: WorldModelAuthorityChain) -> WorldModelAuthorityChain:
    core = {
        key: value
        for key, value in chain.canonical_value().items()
        if key != "digest"
    }
    return replace(
        chain,
        digest=digest_of(["WORLD_MODEL_AUTHORITY_CHAIN@1", core]),
    )


class StaticRequirementPlanner(WorldModelRequirementPlanner):
    strategy_ref = "test-world-model-requirement-planner@1"

    def __init__(
        self,
        *needs: WorldModelNeed,
        joint_constraints: tuple[WorldModelJointConstraint, ...] = (),
    ) -> None:
        self.needs = tuple(needs)
        self.joint_constraints = joint_constraints

    def plan(self, *, question, invocation) -> WorldModelRequirementProposal:
        return WorldModelRequirementProposal(
            original_question=question.original_question,
            response_language=question.response_language,
            needs=self.needs,
            joint_constraints=self.joint_constraints,
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class ApprovingRequirementReviewer(WorldModelRequirementFidelityReviewer):
    strategy_ref = "test-world-model-requirement-reviewer@1"

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


class OmittedNeedRequirementReviewer(WorldModelRequirementFidelityReviewer):
    strategy_ref = "test-world-model-omitted-need-reviewer@1"

    def review(self, *, question, proposal, invocation):
        del question
        return WorldModelRequirementFidelityProposal(
            decision=WorldModelReviewDecision.REJECT,
            accepted_need_ids=tuple(item.need_id for item in proposal.needs),
            accepted_constraint_ids=(),
            original_question_preserved=True,
            all_material_questions_covered=False,
            findings=("NEED_OMITTED",),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class NonBooleanRequirementReviewer(ApprovingRequirementReviewer):
    strategy_ref = "test-world-model-non-boolean-requirement-reviewer@1"

    def review(self, **arguments):
        return replace(
            super().review(**arguments),
            original_question_preserved=1,
        )


class InventoryQueryPlanner(WorldModelQueryPlanner):
    strategy_ref = "test-world-model-inventory-query-planner@1"

    def __init__(self, snapshot_id: StableId, *, mention: str = "mall") -> None:
        self.snapshot_id = snapshot_id
        self.mention = mention

    def plan(self, *, question, requirement, invocation):
        del question
        selector = WorldModelEntitySelectorProposal(
            selector_id="system-b",
            need_ids=(INVENTORY_NEED.need_id,),
            snapshot_id=self.snapshot_id,
            origin=EntitySelectorOrigin.MENTION,
            mention=self.mention,
            entity_type=EntityType.SOFTWARE_SYSTEM,
        )
        step = WorldModelQueryStepProposal.create(
            step_id="inventory-b",
            need_ids=(INVENTORY_NEED.need_id,),
            operation=StructureViewOperation.CHILD_MODULE_INVENTORY,
            arguments={"system": selector.selector_id},
        )
        return WorldModelQueryPlanProposal(
            requirement_id=requirement.requirement_id,
            requirement_digest=requirement.digest,
            read_set_digest=requirement.read_authority.read_set_digest,
            ordered_bundle_digest=requirement.read_authority.ordered_bundle_digest,
            selectors=(selector,),
            steps=(step,),
            explicit_gaps=(),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class InventoryDiffQueryPlanner(WorldModelQueryPlanner):
    strategy_ref = "test-world-model-inventory-diff-planner@1"

    def __init__(
        self,
        *,
        snapshot_a: StableId,
        snapshot_b: StableId,
        inventory_need: WorldModelNeed = INVENTORY_NEED,
        diff_need: WorldModelNeed = INVENTORY_NEED,
        inventory_constraint_ids: tuple[str, ...] = (),
        diff_constraint_ids: tuple[str, ...] = (),
    ) -> None:
        self.snapshot_a = snapshot_a
        self.snapshot_b = snapshot_b
        self.inventory_need = inventory_need
        self.diff_need = diff_need
        self.inventory_constraint_ids = inventory_constraint_ids
        self.diff_constraint_ids = diff_constraint_ids

    def plan(self, *, question, requirement, invocation):
        del question
        selector = WorldModelEntitySelectorProposal(
            selector_id="system-b",
            need_ids=(self.inventory_need.need_id,),
            snapshot_id=self.snapshot_b,
            origin=EntitySelectorOrigin.MENTION,
            mention="mall",
            entity_type=EntityType.SOFTWARE_SYSTEM,
        )
        steps = (
            WorldModelQueryStepProposal.create(
                step_id="inventory-b",
                need_ids=(self.inventory_need.need_id,),
                operation=StructureViewOperation.CHILD_MODULE_INVENTORY,
                arguments={"system": selector.selector_id},
                constraint_ids=self.inventory_constraint_ids,
            ),
            WorldModelQueryStepProposal.create(
                step_id="diff-a-b",
                need_ids=(self.diff_need.need_id,),
                operation=StructureViewOperation.ORDERED_SNAPSHOT_DIFF,
                parameters={
                    "base_snapshot_id": self.snapshot_a.value,
                    "target_snapshot_id": self.snapshot_b.value,
                },
                constraint_ids=self.diff_constraint_ids,
            ),
        )
        return WorldModelQueryPlanProposal(
            requirement_id=requirement.requirement_id,
            requirement_digest=requirement.digest,
            read_set_digest=requirement.read_authority.read_set_digest,
            ordered_bundle_digest=requirement.read_authority.ordered_bundle_digest,
            selectors=(selector,),
            steps=steps,
            explicit_gaps=(),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class UnauthorizedQualifierQueryPlanner(WorldModelQueryPlanner):
    strategy_ref = "test-world-model-unauthorized-qualifier-planner@1"

    def __init__(
        self,
        *,
        snapshot_id: StableId,
        canonical_ga: str | None = None,
        canonical_gav: str | None = None,
    ) -> None:
        self.snapshot_id = snapshot_id
        self.canonical_ga = canonical_ga
        self.canonical_gav = canonical_gav

    def plan(self, *, question, requirement, invocation):
        del question
        selector = WorldModelEntitySelectorProposal(
            selector_id="qualified-common-lib",
            need_ids=(INVENTORY_NEED.need_id,),
            snapshot_id=self.snapshot_id,
            origin=EntitySelectorOrigin.MENTION,
            mention="common-lib",
            entity_type=EntityType.MAVEN_MODULE,
            canonical_ga=self.canonical_ga,
            canonical_gav=self.canonical_gav,
        )
        step = WorldModelQueryStepProposal.create(
            step_id="qualified-neighborhood",
            need_ids=(INVENTORY_NEED.need_id,),
            operation=StructureViewOperation.DIRECT_NEIGHBORHOOD,
            arguments={"entity": selector.selector_id},
        )
        return WorldModelQueryPlanProposal(
            requirement_id=requirement.requirement_id,
            requirement_digest=requirement.digest,
            read_set_digest=requirement.read_authority.read_set_digest,
            ordered_bundle_digest=requirement.read_authority.ordered_bundle_digest,
            selectors=(selector,),
            steps=(step,),
            explicit_gaps=(),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class AmbiguousPathQueryPlanner(WorldModelQueryPlanner):
    strategy_ref = "test-world-model-ambiguous-path-planner@1"

    def __init__(self, snapshot_id: StableId) -> None:
        self.snapshot_id = snapshot_id

    def plan(self, *, question, requirement, invocation):
        del question
        source = WorldModelEntitySelectorProposal(
            selector_id="ambiguous-common-lib",
            need_ids=(INVENTORY_NEED.need_id,),
            snapshot_id=self.snapshot_id,
            origin=EntitySelectorOrigin.MENTION,
            mention="common-lib",
            entity_type=EntityType.MAVEN_MODULE,
        )
        target = WorldModelEntitySelectorProposal(
            selector_id="common-target",
            need_ids=(INVENTORY_NEED.need_id,),
            snapshot_id=self.snapshot_id,
            origin=EntitySelectorOrigin.MENTION,
            mention="common",
            entity_type=EntityType.MAVEN_MODULE,
        )
        step = WorldModelQueryStepProposal.create(
            step_id="ambiguous-path",
            need_ids=(INVENTORY_NEED.need_id,),
            operation=StructureViewOperation.PATH_EXISTS,
            arguments={
                "source": source.selector_id,
                "target": target.selector_id,
            },
            parameters={"predicate": RelationPredicate.DEPENDS_ON.value},
        )
        return WorldModelQueryPlanProposal(
            requirement_id=requirement.requirement_id,
            requirement_digest=requirement.digest,
            read_set_digest=requirement.read_authority.read_set_digest,
            ordered_bundle_digest=requirement.read_authority.ordered_bundle_digest,
            selectors=(source, target),
            steps=(step,),
            explicit_gaps=(),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class ForgedCallerRefQueryPlanner(WorldModelQueryPlanner):
    strategy_ref = "test-world-model-forged-caller-ref-planner@1"

    def __init__(
        self,
        *,
        snapshot_id: StableId,
        entity_root_id: StableId,
        entity_state_id: StableId,
    ) -> None:
        self.snapshot_id = snapshot_id
        self.entity_root_id = entity_root_id
        self.entity_state_id = entity_state_id

    def plan(self, *, question, requirement, invocation):
        del question
        selector = WorldModelEntitySelectorProposal(
            selector_id="forged-system-ref",
            need_ids=(INVENTORY_NEED.need_id,),
            snapshot_id=self.snapshot_id,
            origin=EntitySelectorOrigin.CALLER_EXACT_REF,
            entity_root_id=self.entity_root_id,
            entity_state_id=self.entity_state_id,
        )
        step = WorldModelQueryStepProposal.create(
            step_id="inventory-forged-ref",
            need_ids=(INVENTORY_NEED.need_id,),
            operation=StructureViewOperation.CHILD_MODULE_INVENTORY,
            arguments={"system": selector.selector_id},
        )
        return WorldModelQueryPlanProposal(
            requirement_id=requirement.requirement_id,
            requirement_digest=requirement.digest,
            read_set_digest=requirement.read_authority.read_set_digest,
            ordered_bundle_digest=requirement.read_authority.ordered_bundle_digest,
            selectors=(selector,),
            steps=(step,),
            explicit_gaps=(),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class ResultBoundDraftGenerator(WorldModelDraftGenerator):
    strategy_ref = "test-world-model-draft-generator@1"

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
        del question, plan, result_set
        by_need = {item.need_id: item for item in assessment.needs}
        claims = []
        for need in requirement.needs:
            item = by_need[need.need_id]
            if item.outcome is WorldModelNeedOutcome.LIMITATION:
                kind = WorldModelClaimKind.APPLICATION_LIMITATION
                text = f"应用限制：{', '.join(item.limitations)}。"
                result_ids = ()
            elif item.outcome is WorldModelNeedOutcome.KNOWLEDGE_GAP:
                kind = WorldModelClaimKind.KNOWLEDGE_GAP
                text = f"知识缺口：{item.gap_code}。"
                result_ids = ()
            else:
                kind = WorldModelClaimKind.QUERY_RESULT
                text = f"需求 {need.need_id} 已由精确查询结果支持。"
                result_ids = item.step_result_ids
            claims.append(
                WorldModelAnswerClaimProposal(
                    claim_id=f"claim:{need.need_id}",
                    need_id=need.need_id,
                    kind=kind,
                    text=text,
                    step_result_ids=result_ids,
                )
            )
        return WorldModelDraftProposal(
            assessment_id=assessment.assessment_id,
            assessment_digest=assessment.digest,
            claims=tuple(claims),
            invocation_id=invocation.invocation_id,
            invocation_digest=invocation.digest,
        )


class ApprovingAnswerReviewer(WorldModelAnswerReviewer):
    strategy_ref = "test-world-model-answer-reviewer@1"

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


class GenerationInvocationAnswerReviewer(ApprovingAnswerReviewer):
    strategy_ref = "test-world-model-self-reviewer@1"

    def review(self, **arguments):
        proposal = super().review(**arguments)
        draft = arguments["draft"]
        return replace(
            proposal,
            invocation_id=draft.generation_invocation.invocation_id,
            invocation_digest=draft.generation_invocation.digest,
        )


class DimensionAnswerReviewer(ApprovingAnswerReviewer):
    strategy_ref = "test-world-model-dimension-reviewer@1"

    def __init__(
        self,
        dimensions: tuple[WorldModelReviewDimensionAssessment, ...],
    ) -> None:
        self.dimensions = dimensions

    def review(self, **arguments):
        return replace(
            super().review(**arguments),
            dimensions=self.dimensions,
        )


class WorldModelAnsweringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.view_fixture = _structure_view_tests.StructureViewTests(
            methodName="runTest"
        )
        self.view_fixture.setUp()
        self.addCleanup(self.view_fixture.doCleanups)
        self.view = self.view_fixture.service
        self.snapshot_a = self.view_fixture.a[0].snapshot_id
        self.snapshot_b = self.view_fixture.b[0].snapshot_id
        self.store = InMemoryWorldModelAuthorityStore()
        self.answering = WorldModelAnsweringService(self.store, self.view)
        self.responses = WorldModelResponseControlService(
            self.store, self.answering
        )
        self.offline = OfflineWorldModelAnswerService(
            answering=self.answering,
            responses=self.responses,
        )

    def _execute(self, *, query_planner=None, sink=None) -> WorldModelAuthorityChain:
        return self.offline.execute(
            request_ref="world-model-test-request",
            original_question="列出 B 的全部 reactor child modules。",
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of({"permission": "world-model-test"}),
            requirement_planner=StaticRequirementPlanner(INVENTORY_NEED),
            requirement_reviewer=ApprovingRequirementReviewer(),
            query_planner=query_planner or InventoryQueryPlanner(self.snapshot_b),
            draft_generator=ResultBoundDraftGenerator(),
            answer_reviewer=ApprovingAnswerReviewer(),
            sink=sink or InMemoryWorldModelEvaluationSink(),
        )

    def _open_requirement(
        self,
        *,
        answering=None,
        request_ref="world-model-test-request",
        original_question="列出 B 的全部 reactor child modules。",
        planner=None,
    ):
        service = answering or self.answering
        question = service.open_question(
            request_ref=request_ref,
            original_question=original_question,
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of({"permission": "world-model-test"}),
        )
        requirement = service.seal_requirement(
            question_id=question.question_id,
            planner=planner or StaticRequirementPlanner(INVENTORY_NEED),
            fidelity_reviewer=ApprovingRequirementReviewer(),
        )
        return question, requirement

    def _seal_inventory_draft(self):
        _, requirement = self._open_requirement()
        plan = self.answering.seal_query_plan(
            requirement_id=requirement.requirement_id,
            planner=InventoryQueryPlanner(self.snapshot_b),
        )
        result_set = self.answering.execute_query_plan(plan_id=plan.plan_id)
        assessment = self.answering.assess(
            result_set_id=result_set.result_set_id
        )
        return self.responses.seal_draft(
            assessment_id=assessment.assessment_id,
            generator=ResultBoundDraftGenerator(),
        )

    @staticmethod
    def _reason(error: DomainError) -> str | None:
        return error.details.get("reason_code")

    def test_full_inventory_chain_is_source_closed_and_human_reconstructable(self):
        sink = InMemoryWorldModelEvaluationSink()

        chain = self._execute(sink=sink)

        self.assertEqual(chain.provider_call_count, 0)
        self.assertEqual(chain.network_operation_count, 0)
        self.assertEqual(chain.delivery.state, WorldModelDeliveryState.DELIVERED)
        self.assertEqual(sink.delivery_count, 1)
        self.assertEqual(
            chain.result_set.step_results[0].view_result.payload["module_count"],
            7,
        )
        self.assertEqual(
            chain.assessment.needs[0].outcome,
            WorldModelNeedOutcome.SATISFIED,
        )
        result = chain.result_set.step_results[0]
        claim = chain.draft.claims[0]
        self.assertEqual(claim.kind, WorldModelClaimKind.QUERY_RESULT)
        self.assertEqual(claim.step_result_ids, (result.step_result_id,))
        self.assertEqual(
            claim.view_result_ids,
            (result.view_result.result_id,),
        )
        self.assertIsNone(claim.gap_code)
        self.assertEqual(claim.limitation_codes, ())
        self.assertNotEqual(
            chain.draft.generation_invocation.invocation_id,
            chain.review.review_invocation.invocation_id,
        )
        self.assertEqual(chain.authorization.sink_id, sink.sink_id)
        chain.require_valid()

    def test_outer_chain_redigest_cannot_hide_child_record_tamper(self):
        chain = self._execute()
        tampered = replace(
            chain,
            draft=replace(chain.draft, body="篡改后的未授权正文。"),
        )
        outer_core = {
            key: value
            for key, value in tampered.canonical_value().items()
            if key != "digest"
        }
        tampered = replace(
            tampered,
            digest=digest_of(["WORLD_MODEL_AUTHORITY_CHAIN@1", outer_core]),
        )
        self.assertNotEqual(tampered.digest, chain.digest)

        with self.assertRaises(DomainError) as raised:
            tampered.require_valid()

        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_EXPORTED_RECORD_DIGEST_MISMATCH",
        )

    def test_boolean_execution_counters_are_not_offline_zero_counts(self):
        chain = self._execute()
        tampered = _redigest_chain(
            replace(
                chain,
                provider_call_count=False,
                network_operation_count=False,
            )
        )

        with self.assertRaises(DomainError) as raised:
            tampered.require_valid()

        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_CHAIN_EXECUTION_BOUNDARY_INVALID",
        )

    def test_offline_invocation_requires_an_exact_false_dispatch_marker(self):
        chain = self._execute()
        invocation = chain.draft.generation_invocation
        tampered = _resign_stable_record(
            replace(invocation, external_dispatch_allowed=0),
            id_field="invocation_id",
            stable_kind="offline_invocation",
            id_domain="OFFLINE_STRATEGY_INVOCATION_ID@1",
            digest_domain="OFFLINE_STRATEGY_INVOCATION@1",
        )

        with self.assertRaises(DomainError) as raised:
            tampered.require_valid()

        self.assertEqual(
            self._reason(raised.exception),
            "OFFLINE_INVOCATION_BOUNDARY_INVALID",
        )

    def test_fidelity_review_requires_exact_boolean_acceptance_markers(self):
        question = self.answering.open_question(
            request_ref="world-model-non-boolean-fidelity",
            original_question="列出 B 的全部 reactor child modules。",
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of(
                {"permission": "world-model-non-boolean-fidelity"}
            ),
        )

        with self.assertRaises(DomainError) as raised:
            self.answering.seal_requirement(
                question_id=question.question_id,
                planner=StaticRequirementPlanner(INVENTORY_NEED),
                fidelity_reviewer=NonBooleanRequirementReviewer(),
            )

        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_REQUIREMENT_FIDELITY_REJECTED",
        )

    def test_resigned_question_cannot_hide_explicit_entity_ref_tamper(self):
        system = next(
            item
            for item in self.view_fixture.b[1].entities
            if item.root.entity_type is EntityType.SOFTWARE_SYSTEM
        )
        exact_ref = WorldModelExplicitEntityRef.create(
            snapshot_id=self.snapshot_b,
            entity_root_id=system.root_id,
            entity_state_id=system.state_id,
        )
        question = self.answering.open_question(
            request_ref="world-model-explicit-ref-integrity",
            original_question="列出 B 的全部 reactor child modules。",
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of(
                {"permission": "world-model-explicit-ref-integrity"}
            ),
            explicit_entity_refs=(exact_ref,),
        )
        tampered_ref = replace(
            exact_ref,
            digest=digest_of("unrelated-explicit-entity-ref"),
        )
        tampered = _resign_stable_record(
            replace(question, explicit_entity_refs=(tampered_ref,)),
            id_field="question_id",
            stable_kind="world_model_question",
            id_domain="WORLD_MODEL_QUESTION_ID@1",
            digest_domain="WORLD_MODEL_QUESTION@1",
        )

        with self.assertRaises(DomainError) as raised:
            tampered.require_valid()

        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_EXPLICIT_ENTITY_REF_INVALID",
        )

    def test_exported_chain_rejects_hidden_argument_candidate_tamper(self):
        chain = self._execute()
        resolution = chain.resolutions.resolutions[0]
        self.assertIsNotNone(resolution.argument)
        assert resolution.argument is not None
        self.assertIsNotNone(resolution.argument.candidate_result)
        hidden_argument = replace(
            resolution.argument,
            candidate_result=None,
        )
        tampered = replace(
            chain,
            resolutions=replace(
                chain.resolutions,
                resolutions=(
                    replace(resolution, argument=hidden_argument),
                ),
            ),
        )
        self.assertEqual(tampered.digest, chain.digest)
        self.assertEqual(tampered.canonical_value(), chain.canonical_value())

        with self.assertRaises(DomainError) as raised:
            tampered.require_valid()

        self.assertEqual(
            self._reason(raised.exception),
            "VIEW_CANDIDATE_PROOF_REQUIRED",
        )

    def test_exported_chain_rejects_duplicate_or_substituted_ready_result(self):
        chain = self._execute()
        issued = chain.result_set.step_results[0]
        resolution = chain.resolutions.resolutions[0]
        self.assertIsNotNone(resolution.argument)
        assert resolution.argument is not None
        substitute_view = self.view.direct_neighborhood(
            entity=resolution.argument,
        )
        substituted = _resign_stable_record(
            replace(issued, view_result=substitute_view),
            id_field="step_result_id",
            stable_kind="world_model_step_result",
            id_domain="WORLD_MODEL_QUERY_STEP_RESULT_ID@1",
            digest_domain="WORLD_MODEL_QUERY_STEP_RESULT@1",
        )
        cases = (
            (
                "duplicate",
                (issued, issued),
                "WORLD_MODEL_EXPORTED_RESULT_SET_MISMATCH",
            ),
            (
                "substituted",
                (substituted,),
                "WORLD_MODEL_EXPORTED_STEP_RESULT_MISMATCH",
            ),
        )

        for name, step_results, expected_reason in cases:
            with self.subTest(name):
                result_set = _resign_stable_record(
                    replace(chain.result_set, step_results=step_results),
                    id_field="result_set_id",
                    stable_kind="world_model_result_set",
                    id_domain="WORLD_MODEL_QUERY_RESULT_SET_ID@1",
                    digest_domain="WORLD_MODEL_QUERY_RESULT_SET@1",
                )
                tampered = _redigest_chain(
                    replace(chain, result_set=result_set)
                )

                with self.assertRaises(DomainError) as raised:
                    tampered.require_valid()

                self.assertEqual(
                    self._reason(raised.exception),
                    expected_reason,
                )

    def test_exported_chain_replays_resigned_assessment_semantics(self):
        chain = self._execute()
        need = _redigest_record(
            replace(
                chain.assessment.needs[0],
                outcome=WorldModelNeedOutcome.LIMITATION,
                step_result_ids=(),
                view_result_ids=(),
                support_digests=(),
                gap_code=None,
                gap_detail=None,
                limitations=("FORGED_LIMITATION",),
            ),
            "WORLD_MODEL_NEED_ASSESSMENT@1",
        )
        assessment = _resign_stable_record(
            replace(
                chain.assessment,
                needs=(need,),
                sufficient=False,
            ),
            id_field="assessment_id",
            stable_kind="world_model_assessment",
            id_domain="WORLD_MODEL_ASSESSMENT_ID@1",
            digest_domain="WORLD_MODEL_ASSESSMENT@1",
        )
        tampered = _redigest_chain(replace(chain, assessment=assessment))

        with self.assertRaises(DomainError) as raised:
            tampered.require_valid()

        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_EXPORTED_ASSESSMENT_REPLAY_MISMATCH",
        )

    def test_exported_chain_replays_claim_grounding_and_need_coverage(self):
        chain = self._execute()
        issued_claim = chain.draft.claims[0]
        ungrounded = _redigest_record(
            replace(
                issued_claim,
                step_result_ids=(),
                view_result_ids=(),
                support_digests=(),
                evidence_references=(),
            ),
            "WORLD_MODEL_ANSWER_CLAIM@1",
        )
        cases = (
            ("ungrounded", (ungrounded,), ungrounded.text),
            ("need-omitted", (), ""),
        )

        for name, claims, body in cases:
            with self.subTest(name):
                draft = _resign_stable_record(
                    replace(
                        chain.draft,
                        claims=claims,
                        body=body,
                        body_digest=digest_of(body),
                    ),
                    id_field="draft_id",
                    stable_kind="world_model_draft",
                    id_domain="WORLD_MODEL_ANSWER_DRAFT_ID@1",
                    digest_domain="WORLD_MODEL_ANSWER_DRAFT@1",
                )
                tampered = _redigest_chain(replace(chain, draft=draft))

                with self.assertRaises(DomainError) as raised:
                    tampered.require_valid()

                self.assertEqual(
                    self._reason(raised.exception),
                    "WORLD_MODEL_EXPORTED_CLAIM_REPLAY_MISMATCH",
                )

    def test_exported_chain_rejects_fake_receipt_id_and_delivery_revision(self):
        chain = self._execute()
        receipt = chain.delivery.receipt
        self.assertIsNotNone(receipt)
        assert receipt is not None
        fake_receipt = WorldModelDeliveryReceipt.create(
            receipt_id="evaluation-receipt:forged-canonical-id",
            sink_id=receipt.sink_id,
            delivery_key=receipt.delivery_key,
            body_digest=receipt.body_digest,
            projection_digest=receipt.projection_digest,
            accepted=True,
        )
        cases = (
            (
                "receipt-id",
                replace(chain.delivery, receipt=fake_receipt),
                "WORLD_MODEL_DELIVERY_RECEIPT_DIGEST_MISMATCH",
            ),
            (
                "revision",
                replace(chain.delivery, revision=chain.delivery.revision + 1),
                "WORLD_MODEL_DELIVERY_DIGEST_MISMATCH",
            ),
        )

        for name, delivery, expected_reason in cases:
            with self.subTest(name):
                tampered = _redigest_chain(
                    replace(chain, delivery=_redigest_delivery(delivery))
                )

                with self.assertRaises(DomainError) as raised:
                    tampered.require_valid()

                self.assertEqual(
                    self._reason(raised.exception),
                    expected_reason,
                )

    def test_requirement_need_omission_is_rejected_by_fidelity_review(self):
        question = self.answering.open_question(
            request_ref="omitted-need-request",
            original_question=(
                "列出 B 的模块，并说明 admin 到 common 的路径。"
            ),
            response_language="zh-CN",
            classification="INTERNAL",
            permission_digest=digest_of("omitted-need-permission"),
        )

        with self.assertRaises(DomainError) as raised:
            self.answering.seal_requirement(
                question_id=question.question_id,
                planner=StaticRequirementPlanner(INVENTORY_NEED),
                fidelity_reviewer=OmittedNeedRequirementReviewer(),
            )

        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_REQUIREMENT_FIDELITY_REJECTED",
        )

    def test_request_ref_cannot_be_reused_with_changed_input(self):
        arguments = {
            "request_ref": "stable-request-ref",
            "original_question": "列出 B 的模块。",
            "response_language": "zh-CN",
            "classification": "INTERNAL",
            "permission_digest": digest_of("stable-request-permission"),
        }
        self.answering.open_question(**arguments)

        with self.assertRaises(DomainError) as raised:
            self.answering.open_question(
                **{**arguments, "original_question": "列出 A 的模块。"}
            )

        self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

    def test_fixed_resource_caps_cannot_be_changed_or_exceeded(self):
        limits = WorldModelResourceLimits()

        with self.subTest("override"):
            with self.assertRaises(DomainError) as raised:
                self.answering.open_question(
                    request_ref="changed-resource-cap",
                    original_question="列出 B 的模块。",
                    response_language="zh-CN",
                    classification="INTERNAL",
                    permission_digest=digest_of("changed-resource-cap"),
                    resource_limits=replace(
                        limits,
                        max_question_chars=limits.max_question_chars - 1,
                    ),
                )
            self.assertEqual(
                self._reason(raised.exception),
                "WORLD_MODEL_RESOURCE_LIMIT_INVALID",
            )

        with self.subTest("question-size"):
            with self.assertRaises(DomainError) as raised:
                self.answering.open_question(
                    request_ref="exceeded-question-cap",
                    original_question="问" * (limits.max_question_chars + 1),
                    response_language="zh-CN",
                    classification="INTERNAL",
                    permission_digest=digest_of("exceeded-question-cap"),
                )
            self.assertEqual(
                self._reason(raised.exception),
                "WORLD_MODEL_QUESTION_SIZE_LIMIT",
            )

    def test_unknown_joint_constraint_kind_is_rejected(self):
        unknown = WorldModelJointConstraint(
            constraint_id="unknown-constraint",
            need_ids=(INVENTORY_NEED.need_id,),
            kind="UNKNOWN",  # type: ignore[arg-type]
            description="未知约束不得进入 Requirement。",
        )

        with self.assertRaises(DomainError) as raised:
            self._open_requirement(
                request_ref="unknown-constraint",
                planner=StaticRequirementPlanner(
                    INVENTORY_NEED,
                    joint_constraints=(unknown,),
                ),
            )

        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_REQUIREMENT_CONSTRAINT_INVALID",
        )

    def test_joint_constraint_proof_cannot_be_omitted_or_misbound(self):
        cases = (
            (
                "omitted",
                (INVENTORY_NEED,),
                INVENTORY_NEED,
                (),
                "WORLD_MODEL_QUERY_CONSTRAINT_OMITTED",
            ),
            (
                "misbound",
                (INVENTORY_NEED, DIFF_NEED),
                DIFF_NEED,
                (ORDERED_CONSTRAINT_ID,),
                "WORLD_MODEL_QUERY_CONSTRAINT_NEED_MISMATCH",
            ),
        )
        for name, needs, diff_need, diff_bindings, expected_reason in cases:
            with self.subTest(name):
                store = InMemoryWorldModelAuthorityStore()
                answering = WorldModelAnsweringService(store, self.view)
                constraint = WorldModelJointConstraint(
                    constraint_id=ORDERED_CONSTRAINT_ID,
                    need_ids=(INVENTORY_NEED.need_id,),
                    kind=WorldModelJointConstraintKind.ORDERED_READ_SET,
                    description="A 必须先于 B。",
                    base_snapshot_id=self.snapshot_a,
                    target_snapshot_id=self.snapshot_b,
                )
                _, requirement = self._open_requirement(
                    answering=answering,
                    request_ref=f"constraint-{name}",
                    original_question="列出 B 模块并比较 A 到 B。",
                    planner=StaticRequirementPlanner(
                        *needs,
                        joint_constraints=(constraint,),
                    ),
                )

                with self.assertRaises(DomainError) as raised:
                    answering.seal_query_plan(
                        requirement_id=requirement.requirement_id,
                        planner=InventoryDiffQueryPlanner(
                            snapshot_a=self.snapshot_a,
                            snapshot_b=self.snapshot_b,
                            diff_need=diff_need,
                            diff_constraint_ids=diff_bindings,
                        ),
                    )

                self.assertEqual(
                    self._reason(raised.exception),
                    expected_reason,
                )

    def test_ordered_constraint_assessment_binds_exact_query_results(self):
        constraint = WorldModelJointConstraint(
            constraint_id=ORDERED_CONSTRAINT_ID,
            need_ids=(INVENTORY_NEED.need_id,),
            kind=WorldModelJointConstraintKind.ORDERED_READ_SET,
            description="A 必须先于 B。",
            base_snapshot_id=self.snapshot_a,
            target_snapshot_id=self.snapshot_b,
        )
        _, requirement = self._open_requirement(
            request_ref="ordered-constraint-assessment",
            original_question="列出 B 模块并比较 A 到 B。",
            planner=StaticRequirementPlanner(
                INVENTORY_NEED,
                joint_constraints=(constraint,),
            ),
        )
        plan = self.answering.seal_query_plan(
            requirement_id=requirement.requirement_id,
            planner=InventoryDiffQueryPlanner(
                snapshot_a=self.snapshot_a,
                snapshot_b=self.snapshot_b,
                inventory_constraint_ids=(ORDERED_CONSTRAINT_ID,),
                diff_constraint_ids=(ORDERED_CONSTRAINT_ID,),
            ),
        )
        result_set = self.answering.execute_query_plan(plan_id=plan.plan_id)
        assessment = self.answering.assess(
            result_set_id=result_set.result_set_id
        )
        joint = assessment.joint_constraints[0]

        self.assertTrue(joint.satisfied)
        self.assertEqual(
            joint.step_result_ids,
            tuple(item.step_result_id for item in result_set.step_results),
        )
        self.assertEqual(
            joint.view_result_ids,
            tuple(
                item.view_result.result_id
                for item in result_set.step_results
            ),
        )

    def test_planner_cannot_forge_a_caller_exact_entity_ref(self):
        _, requirement = self._open_requirement()
        system = next(
            item
            for item in self.view_fixture.b[1].entities
            if item.root.entity_type is EntityType.SOFTWARE_SYSTEM
        )

        with self.assertRaises(DomainError) as raised:
            self.answering.seal_query_plan(
                requirement_id=requirement.requirement_id,
                planner=ForgedCallerRefQueryPlanner(
                    snapshot_id=self.snapshot_b,
                    entity_root_id=system.root_id,
                    entity_state_id=system.state_id,
                ),
            )

        self.assertEqual(
            self._reason(raised.exception), "WORLD_MODEL_FORGED_ENTITY_REF"
        )

    def test_mention_selector_cannot_forge_an_exact_entity_qualifier(self):
        _, requirement = self._open_requirement()
        qualifiers = (
            {"canonical_ga": "org.example.shared:common-lib"},
            {"canonical_gav": "org.example.shared:common-lib:1.0.0"},
        )

        for qualifier in qualifiers:
            with self.subTest(**qualifier):
                with self.assertRaises(DomainError) as raised:
                    self.answering.seal_query_plan(
                        requirement_id=requirement.requirement_id,
                        planner=UnauthorizedQualifierQueryPlanner(
                            snapshot_id=self.snapshot_b,
                            **qualifier,
                        ),
                    )

                self.assertEqual(
                    self._reason(raised.exception),
                    "WORLD_MODEL_UNAUTHORIZED_ENTITY_QUALIFIER",
                )

    def test_ambiguous_candidate_blocks_typed_step_and_becomes_a_limitation(self):
        chain = self._execute(
            query_planner=AmbiguousPathQueryPlanner(self.snapshot_b)
        )

        self.assertEqual(chain.plan.steps[0].state, QueryStepState.BLOCKED)
        self.assertEqual(chain.result_set.step_results, ())
        self.assertEqual(
            chain.assessment.needs[0].outcome,
            WorldModelNeedOutcome.LIMITATION,
        )
        self.assertIsNone(chain.assessment.needs[0].gap_code)
        self.assertEqual(
            chain.assessment.needs[0].limitations,
            ("ENTITY_RESOLUTION_NOT_UNIQUE",),
        )
        self.assertEqual(
            chain.draft.claims[0].kind,
            WorldModelClaimKind.APPLICATION_LIMITATION,
        )
        self.assertEqual(
            chain.draft.claims[0].limitation_codes,
            ("ENTITY_RESOLUTION_NOT_UNIQUE",),
        )
        self.assertEqual(chain.draft.claims[0].step_result_ids, ())
        self.assertEqual(chain.draft.claims[0].view_result_ids, ())
        self.assertIsNone(chain.draft.claims[0].gap_code)

    def test_zero_candidate_cannot_become_typed_query_authority(self):
        chain = self._execute(
            query_planner=InventoryQueryPlanner(
                self.snapshot_b,
                mention="missing-software-system",
            )
        )
        resolution = chain.resolutions.resolutions[0]

        self.assertEqual(resolution.status, EntityResolutionStatus.ZERO)
        self.assertIsNone(resolution.argument)
        self.assertIsNotNone(resolution.candidate_result)
        assert resolution.candidate_result is not None
        self.assertEqual(
            resolution.candidate_result.payload["candidate_count"],
            0,
        )
        self.assertEqual(chain.plan.steps[0].state, QueryStepState.BLOCKED)
        self.assertEqual(chain.result_set.step_results, ())
        self.assertEqual(
            chain.assessment.needs[0].outcome,
            WorldModelNeedOutcome.LIMITATION,
        )
        self.assertEqual(
            chain.draft.claims[0].kind,
            WorldModelClaimKind.APPLICATION_LIMITATION,
        )
        chain.require_valid()

    def test_tampered_and_unissued_query_results_are_rejected(self):
        _, requirement = self._open_requirement()
        plan = self.answering.seal_query_plan(
            requirement_id=requirement.requirement_id,
            planner=InventoryQueryPlanner(self.snapshot_b),
        )
        result_set = self.answering.execute_query_plan(plan_id=plan.plan_id)
        unissued = StableId("world_model_result_set_" + "f" * 32)

        with self.assertRaises(DomainError) as unissued_error:
            self.answering.verify_query_result_set(unissued)
        self.assertEqual(unissued_error.exception.code, ErrorCode.INVALID_ARGUMENT)

        self.store._records[WorldModelQueryResultSet][result_set.result_set_id] = (
            replace(result_set, digest=digest_of({"tampered": True}))
        )
        with self.assertRaises(DomainError) as tampered_error:
            self.answering.verify_query_result_set(result_set.result_set_id)
        self.assertEqual(
            self._reason(tampered_error.exception),
            "WORLD_MODEL_QUERY_RESULT_DIGEST_MISMATCH",
        )

    def test_noncanonical_or_external_plan_invocation_cannot_be_replayed(self):
        cases = (
            ("external", "OFFLINE_INVOCATION_BOUNDARY_INVALID"),
            ("noncanonical", "OFFLINE_INVOCATION_DIGEST_MISMATCH"),
        )
        for name, expected_reason in cases:
            with self.subTest(name):
                store = InMemoryWorldModelAuthorityStore()
                answering = WorldModelAnsweringService(store, self.view)
                _, requirement = self._open_requirement(
                    answering=answering,
                    request_ref=f"plan-invocation-{name}",
                )
                plan = answering.seal_query_plan(
                    requirement_id=requirement.requirement_id,
                    planner=InventoryQueryPlanner(self.snapshot_b),
                )
                if name == "external":
                    invocation = replace(
                        plan.planning_invocation,
                        external_dispatch_allowed=True,
                    )
                else:
                    invocation = replace(
                        plan.planning_invocation,
                        digest=digest_of("noncanonical-plan-invocation"),
                    )
                store._records[WorldModelQueryPlan][plan.plan_id] = replace(
                    plan,
                    planning_invocation=invocation,
                )

                with self.assertRaises(DomainError) as raised:
                    answering.execute_query_plan(plan_id=plan.plan_id)

                self.assertEqual(
                    self._reason(raised.exception),
                    expected_reason,
                )

    def test_review_cannot_reuse_the_generation_invocation(self):
        _, requirement = self._open_requirement()
        plan = self.answering.seal_query_plan(
            requirement_id=requirement.requirement_id,
            planner=InventoryQueryPlanner(self.snapshot_b),
        )
        result_set = self.answering.execute_query_plan(plan_id=plan.plan_id)
        assessment = self.answering.assess(result_set_id=result_set.result_set_id)
        draft = self.responses.seal_draft(
            assessment_id=assessment.assessment_id,
            generator=ResultBoundDraftGenerator(),
        )

        with self.assertRaises(DomainError) as raised:
            self.responses.review(
                draft_id=draft.draft_id,
                reviewer=GenerationInvocationAnswerReviewer(),
            )

        self.assertEqual(
            self._reason(raised.exception),
            "WORLD_MODEL_SELF_REVIEW",
        )

    def test_review_requires_every_dimension_to_pass(self):
        draft = self._seal_inventory_draft()
        rejected_dimensions = (
            replace(
                APPROVED_REVIEW_DIMENSIONS[0],
                decision=WorldModelReviewDecision.REJECT,
            ),
            *APPROVED_REVIEW_DIMENSIONS[1:],
        )
        cases = (
            (
                "missing",
                APPROVED_REVIEW_DIMENSIONS[:-1],
                "WORLD_MODEL_REVIEW_DIMENSIONS_INCOMPLETE",
            ),
            (
                "non-pass",
                rejected_dimensions,
                "WORLD_MODEL_REVIEW_DIMENSION_REJECTED",
            ),
        )

        for name, dimensions, expected_reason in cases:
            with self.subTest(name):
                with self.assertRaises(DomainError) as raised:
                    self.responses.review(
                        draft_id=draft.draft_id,
                        reviewer=DimensionAnswerReviewer(dimensions),
                    )

                self.assertEqual(
                    self._reason(raised.exception),
                    expected_reason,
                )

    def test_invalid_delivery_receipt_cannot_transition_or_form_a_chain(self):
        chain = self._execute()
        valid_receipt = chain.delivery.receipt
        self.assertIsNotNone(valid_receipt)
        assert valid_receipt is not None
        receipts = (
            (
                "forged",
                replace(
                    valid_receipt,
                    digest=digest_of("forged-delivery-receipt"),
                ),
            ),
            (
                "mismatched",
                WorldModelDeliveryReceipt.create(
                    receipt_id="mismatched-receipt",
                    sink_id=valid_receipt.sink_id,
                    delivery_key=valid_receipt.delivery_key,
                    body_digest=digest_of("another-body"),
                    projection_digest=valid_receipt.projection_digest,
                    accepted=True,
                ),
            ),
            (
                "rejected",
                WorldModelDeliveryReceipt.create(
                    receipt_id="rejected-receipt",
                    sink_id=valid_receipt.sink_id,
                    delivery_key=valid_receipt.delivery_key,
                    body_digest=valid_receipt.body_digest,
                    projection_digest=valid_receipt.projection_digest,
                    accepted=False,
                ),
            ),
        )

        for name, receipt in receipts:
            with self.subTest(name):
                store = InMemoryWorldModelAuthorityStore()
                answering = WorldModelAnsweringService(store, self.view)
                responses = WorldModelResponseControlService(store, answering)
                prepared = store.prepare_delivery(
                    question=chain.question,
                    authorization=chain.authorization,
                    draft=chain.draft,
                    projection_digest=chain.delivery.projection_digest,
                )
                sending = store.transition_delivery(
                    delivery_id=prepared.delivery_id,
                    expected_revision=prepared.revision,
                    state=WorldModelDeliveryState.SENDING,
                    receipt=None,
                    failure_code=None,
                )

                with self.assertRaises(DomainError) as transition_error:
                    store.transition_delivery(
                        delivery_id=sending.delivery_id,
                        expected_revision=sending.revision,
                        state=WorldModelDeliveryState.DELIVERED,
                        receipt=receipt,
                        failure_code=None,
                    )
                self.assertEqual(
                    transition_error.exception.code,
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                )
                current = store.get(WorldModelDelivery, sending.delivery_id)
                self.assertEqual(current.state, WorldModelDeliveryState.SENDING)
                self.assertIsNone(current.receipt)

                with self.assertRaises(DomainError) as chain_error:
                    responses.authority_chain(delivery_id=sending.delivery_id)
                self.assertEqual(
                    self._reason(chain_error.exception),
                    "WORLD_MODEL_DELIVERY_NOT_COMPLETE",
                )

    def test_unauthorized_delivery_id_never_reaches_the_sink(self):
        sink = InMemoryWorldModelEvaluationSink()

        with self.assertRaises(DomainError) as raised:
            self.responses.deliver(
                authorization_id=StableId(
                    "world_model_authorization_" + "f" * 32
                ),
                sink=sink,
            )

        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)
        self.assertEqual(sink.delivery_count, 0)

    def test_delivery_is_exactly_once_across_full_chain_replay(self):
        sink = InMemoryWorldModelEvaluationSink()

        first = self._execute(sink=sink)
        replay = self._execute(sink=sink)

        self.assertEqual(replay, first)
        self.assertEqual(sink.delivery_count, 1)
        self.assertEqual(
            replay.delivery.delivery_key, first.delivery.delivery_key
        )
        self.assertEqual(replay.delivery.receipt, first.delivery.receipt)


if __name__ == "__main__":
    unittest.main()
