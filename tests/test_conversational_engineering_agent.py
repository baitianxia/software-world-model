from __future__ import annotations

import json
import unittest
from dataclasses import replace
from types import SimpleNamespace

from software_world_model.application_services.conversational_engineering_agent import (
    ApplicationOwnedEngineeringAgentTurnExecutor,
    EngineeringAgentAnswerDraft,
    EngineeringAgentBoundaryRelevanceAssessment,
    EngineeringAgentBoundaryRelevanceAssessmentDisposition,
    EngineeringAgentBoundaryRelevanceChallenge,
    EngineeringAgentBoundaryRelevanceChallengeKind,
    EngineeringAgentClaimProposal,
    EngineeringAgentClaimSemanticScope,
    EngineeringAgentContentCoverageAssessment,
    EngineeringAgentContentCoverageDisposition,
    EngineeringAgentDeliveryAuthorization,
    EngineeringAgentDraftProposal,
    EngineeringAgentDriverModelResult,
    EngineeringAgentEvidenceBoundaryAssessment,
    EngineeringAgentEvidenceBoundaryAssessmentDisposition,
    EngineeringAgentEvidenceDisposition,
    EngineeringAgentInvocationMode,
    EngineeringAgentLoopLimits,
    EngineeringAgentModelCallFailure,
    EngineeringAgentModelCallReceipt,
    EngineeringAgentModelDispatchState,
    EngineeringAgentModelFailureKind,
    EngineeringAgentModelRole,
    EngineeringAgentResponseKind,
    EngineeringAgentRequirementCoverageAssessment,
    EngineeringAgentRequirementCoverageDisposition,
    EngineeringAgentReviewDecision,
    EngineeringAgentReviewFinding,
    EngineeringAgentReviewFocus,
    EngineeringAgentReviewProposal,
    EngineeringAgentReviewerModelResult,
    EngineeringAgentToolActionProposal,
    EngineeringAgentToolOperation,
    EngineeringAgentToolResult,
    EngineeringAgentWorkPhase,
    EngineeringAgentWorkStateProposal,
    InMemoryEngineeringAgentWorkStateRepository,
    SealedEngineeringAgentResponseControl,
    engineering_agent_boundary_relevance_assessment_matches_challenge,
    engineering_agent_content_coverage_nonassertive_body_fragments,
    engineering_agent_content_coverage_nonassertive_inline_code_anchors,
    engineering_agent_content_coverage_unmatched_claim_assertion_replicas,
    engineering_agent_content_coverage_unmatched_inline_code_anchors,
    project_engineering_agent_boundary_relevance_challenges,
    project_engineering_agent_draft_content_units,
    project_engineering_agent_evidence_boundary_challenges,
)
from software_world_model.application_services.engineering_conversation import (
    ConversationMessageKind,
    ConversationTurnState,
    EngineeringChatBinding,
    EngineeringProviderFailureClassification,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import (
    DomainError,
    ErrorCode,
    Revision,
    StableId,
    digest_of,
)


class SequentialIdGenerator:
    def __init__(self) -> None:
        self.value = 0

    def new(self, kind: str) -> StableId:
        self.value += 1
        return StableId(f"{kind}_{self.value:032x}")


def _ready_binding() -> EngineeringChatBinding:
    return EngineeringChatBinding.create(
        product_revision="a" * 40,
        project_name="mall",
        repository_revision="b" * 40,
        world_model_status=RuntimeCapabilityStatus.READY,
        world_model_authority_digest=digest_of({"world_model": "exact"}),
        source_profile_ref="source-profile@1",
        source_access_status=RuntimeCapabilityStatus.READY,
        provider_status=RuntimeCapabilityStatus.READY,
        provider_route_ref="qualified-route@1",
        known_limitations=("Alpha only", "Production is disabled"),
    )


def _action(
    operation: EngineeringAgentToolOperation,
    *,
    query: str,
) -> EngineeringAgentToolActionProposal:
    return EngineeringAgentToolActionProposal.create(
        operation=operation,
        arguments=(("query", query),),
        evidence_need=f"evidence for {query}",
    )


def _full_requirement_coverage(request):
    return EngineeringAgentRequirementCoverageAssessment.create(
        current_user_requirement=request.turn_request.user_message.content,
        coverage_summary="The Draft addresses the complete fixture requirement.",
        disposition=(
            EngineeringAgentRequirementCoverageDisposition.FULLY_ADDRESSED
        ),
        finding_code=None,
    )


def _fixture_content_coverage(request):
    claim_indices = tuple(range(len(request.draft.claims)))
    if (
        request.focus is EngineeringAgentReviewFocus.COMPREHENSIVE
        and request.draft.boundary_observation_ids
    ):
        disposition = (
            EngineeringAgentContentCoverageDisposition.BOUNDARY_REVIEW_DEFERRED
        )
        boundary_ids = ()
    elif request.draft.boundary_observation_ids:
        disposition = EngineeringAgentContentCoverageDisposition.COVERED
        boundary_ids = request.draft.boundary_observation_ids
    elif claim_indices:
        disposition = EngineeringAgentContentCoverageDisposition.COVERED
        boundary_ids = ()
    else:
        disposition = EngineeringAgentContentCoverageDisposition.NON_ASSERTIVE
        boundary_ids = ()
    return tuple(
        EngineeringAgentContentCoverageAssessment.create(
            content_unit_index=item.content_unit_index,
            disposition=disposition,
            claim_indices=claim_indices,
            boundary_observation_ids=boundary_ids,
            finding_code=None,
        )
        for item in project_engineering_agent_draft_content_units(
            request.draft.content
        )
    )


def _proposal(
    invocation,
    *,
    call_ref: str,
    phase: EngineeringAgentWorkPhase,
    action=None,
    draft=None,
    accepted_corrections=None,
    superseded=None,
    plan=("inspect current evidence",),
    open_items=("complete independent review",),
):
    previous = invocation.previous_work_state
    context = invocation.request.snapshot_before.context
    if draft is not None and draft.claims:
        observations = {
            item.observation_id: item for item in invocation.observations
        }
        replicated_claims = []
        for index, claim in enumerate(draft.claims):
            statement = claim.statement
            if index == 0 and draft.content not in statement:
                statement = f"{statement}\n{draft.content}"
            replicated_claims.append(
                EngineeringAgentClaimProposal.create(
                    statement=statement,
                    support_observation_ids=claim.support_observation_ids,
                    support_citation_refs=tuple(
                        observation.citation_refs[0]
                        for observation_id in claim.support_observation_ids
                        for observation in (observations[observation_id],)
                        if observation.citation_refs
                    ),
                )
            )
        draft = EngineeringAgentDraftProposal.create(
            response_kind=draft.response_kind,
            content=draft.content,
            claims=tuple(replicated_claims),
            boundary_observation_ids=draft.boundary_observation_ids,
        )
    return EngineeringAgentWorkStateProposal.create(
        model_call_ref=call_ref,
        expected_context_digest=context.digest,
        expected_previous_work_state_digest=(
            previous.digest if previous is not None else None
        ),
        goal=invocation.request.user_message.content,
        response_language="zh-CN",
        audience="software engineer",
        constraints=("use only sealed evidence",),
        resolved_referents=(),
        accepted_correction_message_ids=(
            tuple(accepted_corrections)
            if accepted_corrections is not None
            else (
                previous.accepted_correction_message_ids
                if previous is not None
                else context.accepted_correction_message_ids
            )
        ),
        superseded_conclusion_refs=(
            tuple(superseded)
            if superseded is not None
            else (
                previous.superseded_conclusion_refs
                if previous is not None
                else context.superseded_conclusion_refs
            )
        ),
        hypotheses=("the current evidence can falsify the working explanation",),
        plan=plan,
        observation_ids=tuple(
            item.observation_id for item in invocation.observations
        ),
        open_items=open_items,
        phase=phase,
        action=action,
        draft=draft,
    )


class RecordingToolPort:
    def __init__(self, *, progress: bool = True) -> None:
        self.requests = []
        self.progress = progress

    def execute(self, request):
        self.requests.append(request)
        operation = request.action.operation
        return EngineeringAgentToolResult.create(
            tool_request_digest=request.digest,
            result_ref=f"result-{len(self.requests)}",
            content=f"sealed observation for {operation.value}",
            disposition=(
                EngineeringAgentEvidenceDisposition.SUPPORT
                if self.progress
                else EngineeringAgentEvidenceDisposition.BOUNDARY
            ),
            progress=self.progress,
        )


class ApprovingReviewer:
    def __init__(self) -> None:
        self.requests = []

    def review(self, request):
        self.requests.append(request)
        return EngineeringAgentReviewProposal.create(
            model_call_ref=f"review-call-{len(self.requests)}",
            decision=EngineeringAgentReviewDecision.APPROVED,
            content_coverage_assessments=_fixture_content_coverage(request),
            requirement_coverage_assessment=(
                _full_requirement_coverage(request)
            ),
        )


class JavaCallerToolPort:
    def __init__(self) -> None:
        self.requests = []

    def execute(self, request):
        self.requests.append(request)
        return EngineeringAgentToolResult.create(
            tool_request_digest=request.digest,
            result_ref="java-source-read",
            content=json.dumps(
                {
                    "schema": "ENGINEERING_AGENT_SOURCE_SUPPORT@1",
                    "retrieval_result": {
                        "items": [
                            {
                                "locator": "module/src/main/java/example/ProductService.java",
                                "modality": "EXACT_STATIC_SOURCE_TEXT",
                                "coverage_complete": True,
                                "content": (
                                    "package example;\n"
                                    "class ProductService {\n"
                                    "  private ProductRepository productRepository;\n"
                                    "  void save() { productRepository.save(item); }\n"
                                    "}\n"
                                ),
                            }
                        ]
                    },
                }
            ),
            disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
            progress=True,
        )


class JavaCallerAnswerDriver:
    def __init__(self) -> None:
        self.invocations = []

    def propose(self, invocation):
        self.invocations.append(invocation)
        if not invocation.observations:
            return _proposal(
                invocation,
                call_ref="caller-agent-1",
                phase=EngineeringAgentWorkPhase.INVESTIGATING,
                action=_action(
                    EngineeringAgentToolOperation.SOURCE_READ,
                    query="read caller",
                ),
            )
        observation_id = invocation.observations[0].observation_id
        return _proposal(
            invocation,
            call_ref="caller-agent-2",
            phase=EngineeringAgentWorkPhase.RESPONSE_READY,
            draft=EngineeringAgentDraftProposal.create(
                response_kind=EngineeringAgentResponseKind.ANSWER,
                content="源码显示 productRepository.save(item) 调用。",
                claims=(
                    EngineeringAgentClaimProposal.create(
                        statement="源码显示 productRepository.save(item) 调用。",
                        support_observation_ids=(observation_id,),
                    ),
                ),
            ),
            open_items=(),
        )


class FocusAwareApprovingReviewer:
    def __init__(self) -> None:
        self.requests = []

    def review(self, request):
        self.requests.append(request)
        assessments = ()
        relevance_assessments = ()
        if (
            request.focus
            is EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE
        ):
            assessments = tuple(
                EngineeringAgentEvidenceBoundaryAssessment.create(
                    challenge_id=item.challenge_id,
                    evidence_boundary=(
                        "The cited source establishes the caller invocation only."
                    ),
                    draft_scope="The Claim states only that invocation.",
                    draft_semantic_scopes=(
                        EngineeringAgentClaimSemanticScope.CALLER_INVOCATION,
                    ),
                    disposition=(
                        EngineeringAgentEvidenceBoundaryAssessmentDisposition.WITHIN_CALLER_EVIDENCE
                    ),
                    finding_code=None,
                )
                for item in project_engineering_agent_evidence_boundary_challenges(
                    request.package,
                    request.draft,
                )
            )
            relevance_assessments = tuple(
                EngineeringAgentBoundaryRelevanceAssessment.create(
                    challenge_id=item.challenge_id,
                    user_requirement="State the material evidence limitation.",
                    boundary_scope="The Draft binds this retained Boundary.",
                    disposition=(
                        EngineeringAgentBoundaryRelevanceAssessmentDisposition.MATERIAL_TO_USER_REQUEST
                        if item.draft_declared_boundary_reference
                        else EngineeringAgentBoundaryRelevanceAssessmentDisposition.NOT_DISCLOSED_IN_DRAFT
                    ),
                    finding_code=None,
                    draft_disclosed_fragments=(
                        (request.draft.content,)
                        if item.draft_declared_boundary_reference
                        else ()
                    ),
                )
                for item in project_engineering_agent_boundary_relevance_challenges(
                    request.package,
                    request.draft,
                )
            )
        return EngineeringAgentReviewProposal.create(
            model_call_ref=f"focused-review-call-{len(self.requests)}",
            decision=EngineeringAgentReviewDecision.APPROVED,
            focus=request.focus,
            content_coverage_assessments=_fixture_content_coverage(request),
            requirement_coverage_assessment=(
                _full_requirement_coverage(request)
            ),
            evidence_boundary_assessments=assessments,
            boundary_relevance_assessments=relevance_assessments,
        )


class RecordingResponseControl:
    def __init__(self) -> None:
        self.requests = []

    def authorize(self, request):
        self.requests.append(request)
        return EngineeringAgentDeliveryAuthorization.create(
            authorization_ref=f"delivery-{len(self.requests)}",
            turn_request_digest=request.turn_request_digest,
            work_state_digest=request.work_state.digest,
            package_digest=request.package.digest,
            answer_digest=request.draft.digest,
            review_digest=request.review.digest,
        )


def _service(
    driver,
    *,
    tool=None,
    reviewer=None,
    response=None,
    limits=None,
    require_receipts=False,
    require_model_receipts=False,
):
    tool = tool or RecordingToolPort()
    reviewer = reviewer or ApprovingReviewer()
    response = response or RecordingResponseControl()
    executor = ApplicationOwnedEngineeringAgentTurnExecutor(
        driver=driver,
        tool_port=tool,
        reviewer=reviewer,
        response_control=response,
        available_operations=(
            EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
            EngineeringAgentToolOperation.SOURCE_SEARCH,
            EngineeringAgentToolOperation.SOURCE_READ,
        ),
        limits=limits or EngineeringAgentLoopLimits(),
        require_tool_authority_receipts=require_receipts,
        require_model_call_receipts=require_model_receipts,
        id_generator=SequentialIdGenerator(),
    )
    service = InMemoryEngineeringConversationService(
        _ready_binding(),
        turn_executor=executor,
        id_generator=SequentialIdGenerator(),
    )
    return service, tool, reviewer, response


class ReplanningAnswerDriver:
    def __init__(self) -> None:
        self.invocations = []

    def propose(self, invocation):
        self.invocations.append(invocation)
        count = len(invocation.observations)
        if count == 0:
            return _proposal(
                invocation,
                call_ref="agent-call-1",
                phase=EngineeringAgentWorkPhase.PLANNING,
                action=_action(
                    EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                    query="login behavior and boundaries",
                ),
            )
        if count == 1:
            self.asserted_first_observation = invocation.observations[0].content
            return _proposal(
                invocation,
                call_ref="agent-call-2",
                phase=EngineeringAgentWorkPhase.INVESTIGATING,
                action=_action(
                    EngineeringAgentToolOperation.SOURCE_READ,
                    query="verify the material runtime path",
                ),
                plan=("verify World Model observation against exact Source",),
            )
        support = tuple(item.observation_id for item in invocation.observations)
        draft = EngineeringAgentDraftProposal.create(
            response_kind=EngineeringAgentResponseKind.ANSWER,
            content="登录行为由已密封的世界模型认知和精确来源观察共同支持。",
            claims=(
                EngineeringAgentClaimProposal.create(
                    statement="登录行为已经过两类当前证据核对。",
                    support_observation_ids=support,
                ),
            ),
        )
        return _proposal(
            invocation,
            call_ref="agent-call-3",
            phase=EngineeringAgentWorkPhase.RESPONSE_READY,
            draft=draft,
            plan=("answer with current evidence",),
        )


class ConversationalEngineeringAgentTests(unittest.TestCase):
    def test_boundary_disclosure_fragments_ignore_only_backtick_presentation(
        self,
    ) -> None:
        challenge = EngineeringAgentBoundaryRelevanceChallenge.create(
            kind=(
                EngineeringAgentBoundaryRelevanceChallengeKind
                .BOUNDARY_MATERIALITY
            ),
            boundary_observation_id=StableId("observation_" + "8" * 32),
            resolving_support_observation_ids=(),
            draft_declared_boundary_reference=True,
        )
        assessment = EngineeringAgentBoundaryRelevanceAssessment.create(
            challenge_id=challenge.challenge_id,
            user_requirement="Explain the service boundary.",
            boundary_scope="Runtime effects are outside the current evidence.",
            draft_disclosed_fragments=(
                "getResourceList cannot establish consumer refresh.",
            ),
            disposition=(
                EngineeringAgentBoundaryRelevanceAssessmentDisposition
                .MATERIAL_TO_USER_REQUEST
            ),
            finding_code=None,
        )

        self.assertTrue(
            engineering_agent_boundary_relevance_assessment_matches_challenge(
                challenge,
                assessment,
                draft_content=(
                    "`getResourceList` cannot establish consumer refresh."
                ),
            )
        )
        self.assertFalse(
            engineering_agent_boundary_relevance_assessment_matches_challenge(
                challenge,
                assessment,
                draft_content=(
                    "`getResourceList` does establish consumer refresh."
                ),
            )
        )
        with self.assertRaises(DomainError):
            EngineeringAgentBoundaryRelevanceAssessment.create(
                challenge_id=challenge.challenge_id,
                user_requirement="Explain the service boundary.",
                boundary_scope="Runtime effects are outside the current evidence.",
                draft_disclosed_fragments=(
                    "`getResourceList` cannot establish consumer refresh.",
                    "getResourceList cannot establish consumer refresh.",
                ),
                disposition=(
                    EngineeringAgentBoundaryRelevanceAssessmentDisposition
                    .MATERIAL_TO_USER_REQUEST
                ),
                finding_code=None,
            )

    def test_audit_only_relevance_assessment_requires_global_no_evidence_finding(
        self,
    ) -> None:
        assessment = EngineeringAgentBoundaryRelevanceAssessment.create(
            challenge_id=StableId("boundary_challenge_" + "a" * 32),
            user_requirement="Explain the business flow.",
            boundary_scope="An earlier search stopped after an exact filename match.",
            disposition=(
                EngineeringAgentBoundaryRelevanceAssessmentDisposition.RESOLVED_AUDIT_ONLY
            ),
            finding_code="RESOLVED_DIAGNOSTIC",
        )
        finding = EngineeringAgentReviewFinding.create(
            code="RESOLVED_DIAGNOSTIC",
            message="Remove the resolved acquisition diagnostic.",
            requires_evidence=True,
            claim_index=None,
        )

        with self.assertRaises(DomainError) as caught:
            EngineeringAgentReviewProposal.create(
                model_call_ref="focused-review-invalid-audit-finding",
                decision=EngineeringAgentReviewDecision.FINDINGS,
                requirement_coverage_assessment=(
                    EngineeringAgentRequirementCoverageAssessment.create(
                        current_user_requirement="Explain the business flow.",
                        coverage_summary="Fixture coverage is otherwise complete.",
                        disposition=(
                            EngineeringAgentRequirementCoverageDisposition.FULLY_ADDRESSED
                        ),
                        finding_code=None,
                    )
                ),
                findings=(finding,),
                focus=EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
                boundary_relevance_assessments=(assessment,),
            )

        self.assertEqual(caught.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_review_proposal_enforces_content_coverage_focus_boundary(self) -> None:
        requirement = EngineeringAgentRequirementCoverageAssessment.create(
            current_user_requirement="Explain the exact source boundary.",
            coverage_summary="The fixture requirement is fully addressed.",
            disposition=(
                EngineeringAgentRequirementCoverageDisposition.FULLY_ADDRESSED
            ),
            finding_code=None,
        )
        deferred = EngineeringAgentContentCoverageAssessment.create(
            content_unit_index=0,
            disposition=(
                EngineeringAgentContentCoverageDisposition
                .BOUNDARY_REVIEW_DEFERRED
            ),
            finding_code=None,
        )
        with self.assertRaises(DomainError) as focused:
            EngineeringAgentReviewProposal.create(
                model_call_ref="focused-review-deferred-content",
                decision=EngineeringAgentReviewDecision.APPROVED,
                focus=(
                    EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE
                ),
                requirement_coverage_assessment=requirement,
                content_coverage_assessments=(deferred,),
            )
        self.assertIn(
            "focused content coverage cannot defer",
            str(focused.exception),
        )

        exposed_boundary = EngineeringAgentContentCoverageAssessment.create(
            content_unit_index=0,
            disposition=EngineeringAgentContentCoverageDisposition.COVERED,
            boundary_observation_ids=(StableId("observation_" + "9" * 32),),
            finding_code=None,
        )
        with self.assertRaises(DomainError) as comprehensive:
            EngineeringAgentReviewProposal.create(
                model_call_ref="comprehensive-review-exposed-boundary",
                decision=EngineeringAgentReviewDecision.APPROVED,
                focus=EngineeringAgentReviewFocus.COMPREHENSIVE,
                requirement_coverage_assessment=requirement,
                content_coverage_assessments=(exposed_boundary,),
            )
        self.assertIn(
            "cannot expose redacted Boundary IDs",
            str(comprehensive.exception),
        )

    def test_content_coverage_requires_exact_inline_code_anchor_in_reference(self) -> None:
        unit = project_engineering_agent_draft_content_units(
            "- `Dao.load` is not proven to live in `config/sql`."
        )[0]
        assessment = EngineeringAgentContentCoverageAssessment.create(
            content_unit_index=0,
            disposition=EngineeringAgentContentCoverageDisposition.COVERED,
            claim_indices=(0,),
            finding_code=None,
        )
        package = SimpleNamespace(boundary_observations=())
        missing = engineering_agent_content_coverage_unmatched_inline_code_anchors(
            package,
            SimpleNamespace(
                claims=(
                    SimpleNamespace(
                        statement="Dao.load does not establish implementation location."
                    ),
                )
            ),
            unit,
            assessment,
        )
        self.assertEqual(missing, ("config/sql",))

        covered = engineering_agent_content_coverage_unmatched_inline_code_anchors(
            package,
            SimpleNamespace(
                claims=(
                    SimpleNamespace(
                        statement=(
                            "Dao.load does not establish that config/sql is its "
                            "implementation location."
                        )
                    ),
                )
            ),
            unit,
            assessment,
        )
        self.assertEqual(covered, ())

        nonassertive = EngineeringAgentContentCoverageAssessment.create(
            content_unit_index=0,
            disposition=EngineeringAgentContentCoverageDisposition.NON_ASSERTIVE,
            finding_code=None,
        )
        self.assertEqual(
            engineering_agent_content_coverage_nonassertive_inline_code_anchors(
                unit,
                nonassertive,
            ),
            ("Dao.load", "config/sql"),
        )
        structural_heading = project_engineering_agent_draft_content_units(
            "## exact revision `0123456789abcdef`"
        )[0]
        self.assertEqual(
            engineering_agent_content_coverage_nonassertive_inline_code_anchors(
                structural_heading,
                nonassertive,
            ),
            (),
        )

    def test_content_coverage_requires_whole_assertion_replica_in_mapped_claim(
        self,
    ) -> None:
        unit = project_engineering_agent_draft_content_units(
            "1. **分类说明**：步骤 1–5 是数据库写入调用，含 "
            "`orderMapper.insert`。"
        )[0]
        assessment = EngineeringAgentContentCoverageAssessment.create(
            content_unit_index=0,
            disposition=EngineeringAgentContentCoverageDisposition.COVERED,
            claim_indices=(0,),
            finding_code=None,
        )
        narrower = EngineeringAgentAnswerDraft(
            answer_id=StableId("agent_answer_" + "1" * 32),
            turn_id=StableId("turn_" + "2" * 32),
            work_state_digest=digest_of("replica-work"),
            package_digest=digest_of("replica-package"),
            response_kind=EngineeringAgentResponseKind.ANSWER,
            content=unit.fragment,
            claims=(
                SimpleNamespace(
                    statement="步骤 1–5 是调用方源码可见的本地调用。"
                ),
            ),
            boundary_observation_ids=(),
            digest=digest_of("narrower-replica-draft"),
        )
        self.assertEqual(
            engineering_agent_content_coverage_unmatched_claim_assertion_replicas(
                narrower,
                unit,
                assessment,
            ),
            (
                "分类说明：步骤 1–5 是数据库写入调用，含 "
                "orderMapper.insert。",
            ),
        )

        exact = EngineeringAgentAnswerDraft(
            answer_id=StableId("agent_answer_" + "3" * 32),
            turn_id=StableId("turn_" + "2" * 32),
            work_state_digest=digest_of("replica-work"),
            package_digest=digest_of("replica-package"),
            response_kind=EngineeringAgentResponseKind.ANSWER,
            content=unit.fragment,
            claims=(
                SimpleNamespace(
                    statement=(
                        "分类说明：步骤 1–5 是数据库写入调用，含 "
                        "orderMapper.insert。"
                        "该分类必须由所选证据直接支持。"
                    )
                ),
            ),
            boundary_observation_ids=(),
            digest=digest_of("exact-replica-draft"),
        )
        self.assertEqual(
            engineering_agent_content_coverage_unmatched_claim_assertion_replicas(
                exact,
                unit,
                assessment,
            ),
            (),
        )

    def test_nonassertive_body_is_limited_to_structure_or_clarification(self) -> None:
        nonassertive = EngineeringAgentContentCoverageAssessment.create(
            content_unit_index=0,
            disposition=EngineeringAgentContentCoverageDisposition.NON_ASSERTIVE,
            finding_code=None,
        )
        body = project_engineering_agent_draft_content_units(
            "步骤 1–5 是数据库写入调用。"
        )[0]
        answer_draft = EngineeringAgentAnswerDraft(
            answer_id=StableId("agent_answer_" + "4" * 32),
            turn_id=StableId("turn_" + "5" * 32),
            work_state_digest=digest_of("nonassertive-work"),
            package_digest=digest_of("nonassertive-package"),
            response_kind=EngineeringAgentResponseKind.ANSWER,
            content=body.fragment,
            claims=(),
            boundary_observation_ids=(),
            digest=digest_of("nonassertive-answer-draft"),
        )
        self.assertEqual(
            engineering_agent_content_coverage_nonassertive_body_fragments(
                answer_draft,
                body,
                nonassertive,
            ),
            ("步骤 1–5 是数据库写入调用。",),
        )
        heading = project_engineering_agent_draft_content_units(
            "## 数据库写入"
        )[0]
        self.assertEqual(
            engineering_agent_content_coverage_nonassertive_body_fragments(
                answer_draft,
                heading,
                nonassertive,
            ),
            (),
        )
        clarification_draft = EngineeringAgentAnswerDraft(
            answer_id=StableId("agent_answer_" + "6" * 32),
            turn_id=StableId("turn_" + "5" * 32),
            work_state_digest=digest_of("nonassertive-work"),
            package_digest=digest_of("nonassertive-package"),
            response_kind=EngineeringAgentResponseKind.CLARIFICATION,
            content=body.fragment,
            claims=(),
            boundary_observation_ids=(),
            digest=digest_of("nonassertive-clarification-draft"),
        )
        self.assertEqual(
            engineering_agent_content_coverage_nonassertive_body_fragments(
                clarification_draft,
                body,
                nonassertive,
            ),
            (),
        )

    def test_observation_driven_replan_closes_a_reviewed_turn(self) -> None:
        driver = ReplanningAnswerDriver()
        service, tool, reviewer, response = _service(driver)
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 4)
        self.assertEqual(submission.turn.retry_count, 0)
        self.assertEqual(submission.turn.delivery_state, "AUTHORIZED")
        self.assertEqual(submission.turn.quality_status, "ACCEPTED")
        self.assertIsNotNone(submission.turn.work_state_ref)
        self.assertIsNotNone(submission.turn.evidence_package_ref)
        self.assertIsNotNone(submission.turn.review_ref)
        self.assertEqual(
            submission.snapshot.messages[-1].kind,
            ConversationMessageKind.ANSWER,
        )
        self.assertEqual(
            [request.action.operation for request in tool.requests],
            [
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                EngineeringAgentToolOperation.SOURCE_READ,
            ],
        )
        self.assertEqual(
            tuple(len(item.action_history) for item in driver.invocations),
            (0, 1, 2),
        )
        self.assertEqual(
            driver.invocations[-1].action_history,
            tuple(request.action for request in tool.requests),
        )
        self.assertIn("WORLD_MODEL_QUERY", driver.asserted_first_observation)
        self.assertEqual(len(reviewer.requests), 1)
        self.assertEqual(
            [
                item.operation
                for item in reviewer.requests[0].package.support_observations
            ],
            [
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                EngineeringAgentToolOperation.SOURCE_READ,
            ],
        )
        self.assertTrue(
            all(
                item.content.startswith("sealed observation")
                for item in reviewer.requests[0].package.support_observations
            )
        )
        self.assertEqual(len(response.requests), 1)
        self.assertEqual(service.provider_dispatch_count(), 4)
        self.assertEqual(
            submission.snapshot.context.reducer_status,
            "EXECUTED_APPLICATION_SEALED",
        )
        self.assertEqual(len(submission.snapshot.context.reviewed_conclusion_refs), 1)

    def test_structural_caller_risk_requires_fresh_focused_review(self) -> None:
        driver = JavaCallerAnswerDriver()
        tool = JavaCallerToolPort()
        reviewer = FocusAwareApprovingReviewer()
        service, _, _, response = _service(
            driver,
            tool=tool,
            reviewer=reviewer,
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="这个保存调用在哪里？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(
            tuple(item.focus for item in reviewer.requests),
            (
                EngineeringAgentReviewFocus.COMPREHENSIVE,
                EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
            ),
        )
        challenges = project_engineering_agent_evidence_boundary_challenges(
            reviewer.requests[1].package,
            reviewer.requests[1].draft,
        )
        self.assertEqual(len(challenges), 1)
        self.assertEqual(challenges[0].call_expression, "productRepository.save")
        self.assertEqual(len(response.requests), 1)
        self.assertEqual(
            response.requests[0].review.focus,
            EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
        )
        self.assertEqual(
            response.requests[0].review.evidence_boundary_assessments[0].challenge_id,
            challenges[0].challenge_id,
        )

    def test_focused_review_cannot_add_a_finding_unbound_to_a_challenge(
        self,
    ) -> None:
        class ExtraFindingReviewer:
            def __init__(self) -> None:
                self.requests = []

            def review(self, request):
                self.requests.append(request)
                if request.focus is EngineeringAgentReviewFocus.COMPREHENSIVE:
                    return EngineeringAgentReviewProposal.create(
                        model_call_ref="extra-finding-comprehensive",
                        decision=EngineeringAgentReviewDecision.APPROVED,
                        content_coverage_assessments=_fixture_content_coverage(request),
                        requirement_coverage_assessment=(
                            _full_requirement_coverage(request)
                        ),
                        focus=request.focus,
                    )
                challenge = project_engineering_agent_evidence_boundary_challenges(
                    request.package,
                    request.draft,
                )[0]
                return EngineeringAgentReviewProposal.create(
                    model_call_ref="extra-finding-focused",
                    decision=EngineeringAgentReviewDecision.FINDINGS,
                    content_coverage_assessments=_fixture_content_coverage(request),
                    requirement_coverage_assessment=(
                        _full_requirement_coverage(request)
                    ),
                    findings=(
                        EngineeringAgentReviewFinding.create(
                            code="UNBOUND_FOCUSED_FINDING",
                            message="A comprehensive defect invented in focused Review.",
                            requires_evidence=False,
                            claim_index=None,
                        ),
                    ),
                    focus=request.focus,
                    evidence_boundary_assessments=(
                        EngineeringAgentEvidenceBoundaryAssessment.create(
                            challenge_id=challenge.challenge_id,
                            evidence_boundary="Caller invocation only.",
                            draft_scope="Caller invocation only.",
                            draft_semantic_scopes=(
                                EngineeringAgentClaimSemanticScope.CALLER_INVOCATION,
                            ),
                            disposition=(
                                EngineeringAgentEvidenceBoundaryAssessmentDisposition.WITHIN_CALLER_EVIDENCE
                            ),
                            finding_code=None,
                        ),
                    ),
                )

        reviewer = ExtraFindingReviewer()
        response = RecordingResponseControl()
        service, _, _, _ = _service(
            JavaCallerAnswerDriver(),
            tool=JavaCallerToolPort(),
            reviewer=reviewer,
            response=response,
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="这个保存调用在哪里？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.failure_code, "AGENT_PROTOCOL_VIOLATION")
        self.assertEqual(len(reviewer.requests), 2)
        self.assertEqual(len(response.requests), 0)

    def test_fourth_review_closes_comprehensive_and_focused_rewrites(self) -> None:
        class RewriteDriver:
            def __init__(self) -> None:
                self.calls = 0

            def propose(self, invocation):
                self.calls += 1
                if not invocation.observations:
                    return _proposal(
                        invocation,
                        call_ref="four-review-agent-1",
                        phase=EngineeringAgentWorkPhase.INVESTIGATING,
                        action=_action(
                            EngineeringAgentToolOperation.SOURCE_READ,
                            query="read caller",
                        ),
                    )
                observation_id = invocation.observations[0].observation_id
                caller_only = self.calls >= 4
                statement = (
                    "源码显示 productRepository.save(item) 调用。"
                    if caller_only
                    else (
                        "productRepository.save(item) 已把商品写入外部数据库。"
                    )
                )
                return _proposal(
                    invocation,
                    call_ref=f"four-review-agent-{self.calls}",
                    phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                    draft=EngineeringAgentDraftProposal.create(
                        response_kind=EngineeringAgentResponseKind.ANSWER,
                        content=statement,
                        claims=(
                            EngineeringAgentClaimProposal.create(
                                statement=statement,
                                support_observation_ids=(observation_id,),
                            ),
                        ),
                    ),
                    open_items=(),
                )

        class FourStageReviewer:
            def __init__(self) -> None:
                self.requests = []

            def review(self, request):
                self.requests.append(request)
                ordinal = len(self.requests)
                if ordinal == 1:
                    return EngineeringAgentReviewProposal.create(
                        model_call_ref="four-review-comprehensive-finding",
                        decision=EngineeringAgentReviewDecision.FINDINGS,
                        content_coverage_assessments=_fixture_content_coverage(request),
                        requirement_coverage_assessment=(
                            _full_requirement_coverage(request)
                        ),
                        findings=(
                            EngineeringAgentReviewFinding.create(
                                code="COMPREHENSIVE_REWRITE",
                                message="Rewrite one unsupported qualifier.",
                                requires_evidence=False,
                                claim_index=0,
                            ),
                        ),
                        focus=request.focus,
                    )
                if ordinal == 2:
                    return EngineeringAgentReviewProposal.create(
                        model_call_ref="four-review-comprehensive-approved",
                        decision=EngineeringAgentReviewDecision.APPROVED,
                        content_coverage_assessments=_fixture_content_coverage(request),
                        requirement_coverage_assessment=(
                            _full_requirement_coverage(request)
                        ),
                        focus=request.focus,
                    )
                challenges = (
                    project_engineering_agent_evidence_boundary_challenges(
                        request.package,
                        request.draft,
                    )
                )
                challenge = challenges[0]
                if ordinal == 3:
                    return EngineeringAgentReviewProposal.create(
                        model_call_ref="four-review-focused-finding",
                        decision=EngineeringAgentReviewDecision.FINDINGS,
                        content_coverage_assessments=_fixture_content_coverage(request),
                        requirement_coverage_assessment=(
                            _full_requirement_coverage(request)
                        ),
                        findings=(
                            EngineeringAgentReviewFinding.create(
                                code="CALLEE_EFFECT_REWRITE",
                                message="Narrow the effect to the caller invocation.",
                                requires_evidence=False,
                                claim_index=0,
                            ),
                        ),
                        focus=request.focus,
                        evidence_boundary_assessments=(
                            EngineeringAgentEvidenceBoundaryAssessment.create(
                                challenge_id=challenge.challenge_id,
                                evidence_boundary="Caller invocation only.",
                                draft_scope="External database effect.",
                                draft_semantic_scopes=(
                                    EngineeringAgentClaimSemanticScope.DATABASE_OR_EXTERNAL_STATE_EFFECT,
                                ),
                                disposition=(
                                    EngineeringAgentEvidenceBoundaryAssessmentDisposition.CLAIM_EXCEEDS_CALLER_EVIDENCE
                                ),
                                finding_code="CALLEE_EFFECT_REWRITE",
                            ),
                        ),
                    )
                return EngineeringAgentReviewProposal.create(
                    model_call_ref="four-review-focused-approved",
                    decision=EngineeringAgentReviewDecision.APPROVED,
                    content_coverage_assessments=_fixture_content_coverage(request),
                    requirement_coverage_assessment=(
                        _full_requirement_coverage(request)
                    ),
                    focus=request.focus,
                    evidence_boundary_assessments=(
                        EngineeringAgentEvidenceBoundaryAssessment.create(
                            challenge_id=challenge.challenge_id,
                            evidence_boundary="Caller invocation only.",
                            draft_scope="Caller invocation only.",
                            draft_semantic_scopes=(
                                EngineeringAgentClaimSemanticScope.CALLER_INVOCATION,
                            ),
                            disposition=(
                                EngineeringAgentEvidenceBoundaryAssessmentDisposition.WITHIN_CALLER_EVIDENCE
                            ),
                            finding_code=None,
                        ),
                    ),
                )

        driver = RewriteDriver()
        reviewer = FourStageReviewer()
        service, _, _, response = _service(
            driver,
            tool=JavaCallerToolPort(),
            reviewer=reviewer,
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="这个保存调用会产生什么效果？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 8)
        self.assertEqual(
            tuple(item.focus for item in reviewer.requests),
            (
                EngineeringAgentReviewFocus.COMPREHENSIVE,
                EngineeringAgentReviewFocus.COMPREHENSIVE,
                EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
                EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
            ),
        )
        self.assertEqual(len(response.requests), 1)

    def test_reviewer_finding_returns_to_same_agent_and_reuses_package(self) -> None:
        class RewriteDriver:
            def __init__(self):
                self.calls = 0
                self.findings_seen = []
                self.review_digests_seen = []
                self.reviewed_drafts_seen = []

            def propose(self, invocation):
                self.calls += 1
                self.findings_seen.append(invocation.review_findings)
                self.review_digests_seen.append(invocation.review_digest)
                self.reviewed_drafts_seen.append(invocation.reviewed_draft)
                if self.calls == 1:
                    return _proposal(
                        invocation,
                        call_ref="agent-rewrite-1",
                        phase=EngineeringAgentWorkPhase.INVESTIGATING,
                        action=_action(
                            EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                            query="current behavior",
                        ),
                    )
                observation_id = invocation.observations[0].observation_id
                content = "第一版。" if self.calls == 2 else "按审核意见直接回答的第二版。"
                return _proposal(
                    invocation,
                    call_ref=f"agent-rewrite-{self.calls}",
                    phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                    draft=EngineeringAgentDraftProposal.create(
                        response_kind=EngineeringAgentResponseKind.ANSWER,
                        content=content,
                        claims=(
                            EngineeringAgentClaimProposal.create(
                                statement="当前行为有密封证据支持。",
                                support_observation_ids=(observation_id,),
                            ),
                        ),
                    ),
                )

        class RewriteReviewer:
            def __init__(self):
                self.requests = []

            def review(self, request):
                self.requests.append(request)
                if len(self.requests) == 1:
                    return EngineeringAgentReviewProposal.create(
                        model_call_ref="review-rewrite-1",
                        decision=EngineeringAgentReviewDecision.FINDINGS,
                        content_coverage_assessments=_fixture_content_coverage(request),
                        requirement_coverage_assessment=(
                            _full_requirement_coverage(request)
                        ),
                        findings=(
                            EngineeringAgentReviewFinding.create(
                                code="DIRECTNESS",
                                message="直接回答后再解释。",
                                requires_evidence=False,
                                claim_index=0,
                            ),
                        ),
                    )
                return EngineeringAgentReviewProposal.create(
                    model_call_ref="review-rewrite-2",
                    decision=EngineeringAgentReviewDecision.APPROVED,
                    content_coverage_assessments=_fixture_content_coverage(request),
                    requirement_coverage_assessment=(
                        _full_requirement_coverage(request)
                    ),
                )

        class RecordingSealedResponseControl:
            def __init__(self):
                self.requests = []
                self.delegate = SealedEngineeringAgentResponseControl()

            def authorize(self, request):
                self.requests.append(request)
                return self.delegate.authorize(request)

        driver = RewriteDriver()
        reviewer = RewriteReviewer()
        response = RecordingSealedResponseControl()
        service, _, _, _ = _service(
            driver,
            reviewer=reviewer,
            response=response,
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="说明当前行为",
        )

        self.assertEqual(submission.turn.provider_dispatch_count, 5)
        self.assertEqual(submission.turn.fallback_provider_attempt_count, 0)
        self.assertEqual(submission.turn.retry_count, 0)
        self.assertEqual(driver.calls, 3)
        self.assertEqual(len(reviewer.requests), 2)
        self.assertEqual(
            reviewer.requests[0].package.digest,
            reviewer.requests[1].package.digest,
        )
        self.assertEqual(len(driver.findings_seen[2]), 1)
        self.assertIsNotNone(driver.review_digests_seen[2])
        self.assertEqual(
            driver.reviewed_drafts_seen,
            [None, None, reviewer.requests[0].draft],
        )
        self.assertEqual(
            driver.reviewed_drafts_seen[2].digest,
            reviewer.requests[0].draft.digest,
        )
        self.assertEqual(
            reviewer.requests[1].work_state.review_input_digest,
            driver.review_digests_seen[2],
        )
        self.assertEqual(len(response.requests), 1)
        self.assertIn("第二版", submission.snapshot.messages[-1].content)

    def test_evidence_gap_creates_a_successor_package_and_fresh_review(self) -> None:
        class GapDriver:
            def __init__(self):
                self.calls = 0
                self.findings_seen = []
                self.evidence_action_completed_seen = []

            def propose(self, invocation):
                self.calls += 1
                self.findings_seen.append(invocation.review_findings)
                self.evidence_action_completed_seen.append(
                    invocation.review_feedback_evidence_action_completed
                )
                if self.calls == 1:
                    return _proposal(
                        invocation,
                        call_ref="agent-gap-1",
                        phase=EngineeringAgentWorkPhase.INVESTIGATING,
                        action=_action(
                            EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                            query="candidate behavior",
                        ),
                    )
                if self.calls == 3:
                    if not invocation.review_findings[0].requires_evidence:
                        raise AssertionError("evidence-gap Finding was not returned")
                    return _proposal(
                        invocation,
                        call_ref="agent-gap-3",
                        phase=EngineeringAgentWorkPhase.REVISING,
                        action=_action(
                            EngineeringAgentToolOperation.SOURCE_READ,
                            query="missing side effect",
                        ),
                    )
                support = tuple(
                    item.observation_id for item in invocation.observations
                )
                return _proposal(
                    invocation,
                    call_ref=f"agent-gap-{self.calls}",
                    phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                    draft=EngineeringAgentDraftProposal.create(
                        response_kind=EngineeringAgentResponseKind.ANSWER,
                        content="补证前答案。" if self.calls == 2 else "补证后的答案。",
                        claims=(
                            EngineeringAgentClaimProposal.create(
                                statement="当前结论由全部当前观察支持。",
                                support_observation_ids=support,
                            ),
                        ),
                    ),
                )

        class GapReviewer:
            def __init__(self):
                self.requests = []

            def review(self, request):
                self.requests.append(request)
                if len(self.requests) == 1:
                    return EngineeringAgentReviewProposal.create(
                        model_call_ref="review-gap-1",
                        decision=EngineeringAgentReviewDecision.FINDINGS,
                        content_coverage_assessments=_fixture_content_coverage(request),
                        requirement_coverage_assessment=(
                            _full_requirement_coverage(request)
                        ),
                        findings=(
                            EngineeringAgentReviewFinding.create(
                                code="MISSING_EFFECT",
                                message="缺少副作用证据。",
                                requires_evidence=True,
                                claim_index=0,
                            ),
                        ),
                    )
                return EngineeringAgentReviewProposal.create(
                    model_call_ref="review-gap-2",
                    decision=EngineeringAgentReviewDecision.APPROVED,
                    content_coverage_assessments=_fixture_content_coverage(request),
                    requirement_coverage_assessment=(
                        _full_requirement_coverage(request)
                    ),
                )

        driver = GapDriver()
        reviewer = GapReviewer()
        service, tool, _, response = _service(driver, reviewer=reviewer)
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="说明行为及副作用",
        )

        self.assertEqual(submission.turn.provider_dispatch_count, 6)
        self.assertEqual(len(tool.requests), 2)
        self.assertNotEqual(
            reviewer.requests[0].package.digest,
            reviewer.requests[1].package.digest,
        )
        self.assertEqual(len(driver.findings_seen[2]), 1)
        self.assertFalse(driver.evidence_action_completed_seen[2])
        self.assertEqual(len(driver.findings_seen[3]), 1)
        self.assertTrue(driver.evidence_action_completed_seen[3])
        self.assertEqual(len(response.requests), 1)
        self.assertIn("补证后的", submission.snapshot.messages[-1].content)

    def test_evidence_required_finding_cannot_be_rewritten_without_new_observation(self) -> None:
        class IgnoringGapDriver:
            def __init__(self):
                self.calls = 0

            def propose(self, invocation):
                self.calls += 1
                if self.calls == 1:
                    return _proposal(
                        invocation,
                        call_ref="agent-ignore-gap-1",
                        phase=EngineeringAgentWorkPhase.INVESTIGATING,
                        action=_action(
                            EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                            query="incomplete behavior",
                        ),
                    )
                observation_id = invocation.observations[0].observation_id
                return _proposal(
                    invocation,
                    call_ref=f"agent-ignore-gap-{self.calls}",
                    phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                    draft=EngineeringAgentDraftProposal.create(
                        response_kind=EngineeringAgentResponseKind.ANSWER,
                        content="没有补证的重复答案。",
                        claims=(
                            EngineeringAgentClaimProposal.create(
                                statement="现有证据仍不完整。",
                                support_observation_ids=(observation_id,),
                            ),
                        ),
                    ),
                )

        class EvidenceGapReviewer:
            def __init__(self):
                self.requests = []

            def review(self, request):
                self.requests.append(request)
                return EngineeringAgentReviewProposal.create(
                    model_call_ref=f"review-ignore-gap-{len(self.requests)}",
                    decision=EngineeringAgentReviewDecision.FINDINGS,
                    content_coverage_assessments=_fixture_content_coverage(request),
                    requirement_coverage_assessment=(
                        _full_requirement_coverage(request)
                    ),
                    findings=(
                        EngineeringAgentReviewFinding.create(
                            code="MISSING_EVIDENCE",
                            message="必须补充当前缺失证据。",
                            requires_evidence=True,
                            claim_index=0,
                        ),
                    ),
                )

        reviewer = EvidenceGapReviewer()
        service, _, _, response = _service(
            IgnoringGapDriver(), reviewer=reviewer
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="说明完整行为",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.failure_code, "AGENT_PROTOCOL_VIOLATION")
        self.assertEqual(submission.turn.provider_dispatch_count, 4)
        self.assertEqual(len(reviewer.requests), 1)
        self.assertEqual(len(response.requests), 0)

    def test_ambiguous_referent_can_deliver_reviewed_clarification_without_tools(self) -> None:
        class ClarificationDriver:
            def propose(self, invocation):
                return _proposal(
                    invocation,
                    call_ref="agent-clarify-1",
                    phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                    draft=EngineeringAgentDraftProposal.create(
                        response_kind=EngineeringAgentResponseKind.CLARIFICATION,
                        content="你说的“它”是指登录请求还是认证过滤器？",
                    ),
                    open_items=("resolve ambiguous referent",),
                )

        service, tool, reviewer, response = _service(ClarificationDriver())
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="它失败时会记录什么？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.quality_status, "REVIEWED_CLARIFICATION")
        self.assertEqual(
            submission.snapshot.messages[-1].kind,
            ConversationMessageKind.CLARIFICATION,
        )
        self.assertEqual(len(tool.requests), 0)
        self.assertEqual(len(reviewer.requests), 1)
        self.assertEqual(len(response.requests), 1)
        self.assertEqual(submission.turn.provider_dispatch_count, 2)

    def test_no_progress_switches_to_reviewed_evidence_only_limitation(self) -> None:
        class NoProgressDriver:
            def __init__(self):
                self.calls = 0
                self.modes = []
                self.maximum_tool_actions = []

            def propose(self, invocation):
                self.calls += 1
                self.modes.append(invocation.mode)
                self.maximum_tool_actions.append(
                    invocation.maximum_tool_actions
                )
                if (
                    invocation.mode
                    is EngineeringAgentInvocationMode.EVIDENCE_ONLY_SYNTHESIS
                ):
                    return _proposal(
                        invocation,
                        call_ref=f"agent-no-progress-{self.calls}",
                        phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                        draft=EngineeringAgentDraftProposal.create(
                            response_kind=EngineeringAgentResponseKind.LIMITATION,
                            content=(
                                "现有证据边界不足以确认该行为，不能继续补证。"
                            ),
                            boundary_observation_ids=tuple(
                                item.observation_id
                                for item in invocation.observations
                                if item.disposition
                                is EngineeringAgentEvidenceDisposition.BOUNDARY
                            ),
                        ),
                        plan=("synthesize only the sealed evidence boundary",),
                        open_items=(),
                    )
                return _proposal(
                    invocation,
                    call_ref=f"agent-no-progress-{self.calls}",
                    phase=EngineeringAgentWorkPhase.INVESTIGATING,
                    action=_action(
                        EngineeringAgentToolOperation.SOURCE_SEARCH,
                        query=f"unresolved evidence {self.calls}",
                    ),
                )

        driver = NoProgressDriver()
        service, tool, reviewer, response = _service(
            driver,
            tool=RecordingToolPort(progress=False),
            reviewer=FocusAwareApprovingReviewer(),
            limits=EngineeringAgentLoopLimits(
                maximum_agent_steps=4,
                maximum_tool_actions=4,
                maximum_reviews=2,
                maximum_consecutive_no_progress=2,
            ),
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="查找不存在的证据",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertIsNone(submission.turn.failure_code)
        self.assertEqual(submission.turn.delivery_state, "AUTHORIZED")
        self.assertEqual(submission.turn.quality_status, "REVIEWED_LIMITATION")
        self.assertEqual(submission.turn.provider_dispatch_count, 5)
        self.assertEqual(len(tool.requests), 2)
        self.assertEqual(len(reviewer.requests), 2)
        self.assertEqual(len(response.requests), 1)
        self.assertEqual(
            driver.modes,
            [
                EngineeringAgentInvocationMode.STANDARD,
                EngineeringAgentInvocationMode.STANDARD,
                EngineeringAgentInvocationMode.EVIDENCE_ONLY_SYNTHESIS,
            ],
        )
        self.assertEqual(driver.maximum_tool_actions, [4, 4, 4])
        self.assertEqual(
            submission.snapshot.conversation.state.value,
            "ACTIVE",
        )
        self.assertIsNotNone(submission.snapshot.context.work_state_ref)

    def test_evidence_only_synthesis_rejects_more_tool_actions(self) -> None:
        class NoncompliantDriver:
            def __init__(self):
                self.calls = 0

            def propose(self, invocation):
                self.calls += 1
                return _proposal(
                    invocation,
                    call_ref=f"agent-terminal-action-{self.calls}",
                    phase=EngineeringAgentWorkPhase.INVESTIGATING,
                    action=_action(
                        EngineeringAgentToolOperation.SOURCE_SEARCH,
                        query=f"still searching {self.calls}",
                    ),
                )

        service, tool, reviewer, response = _service(
            NoncompliantDriver(),
            tool=RecordingToolPort(progress=False),
            limits=EngineeringAgentLoopLimits(
                maximum_agent_steps=4,
                maximum_tool_actions=4,
                maximum_reviews=1,
                maximum_consecutive_no_progress=2,
            ),
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="查找不存在的证据",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.failure_code, "AGENT_PROTOCOL_VIOLATION")
        self.assertEqual(submission.turn.delivery_state, "NOT_AUTHORIZED")
        self.assertEqual(submission.turn.provider_dispatch_count, 3)
        self.assertEqual(len(tool.requests), 2)
        self.assertEqual(len(reviewer.requests), 0)
        self.assertEqual(len(response.requests), 0)
        self.assertEqual(submission.snapshot.conversation.state.value, "ACTIVE")
        self.assertIsNone(submission.snapshot.context.work_state_ref)

    def test_evidence_only_synthesis_does_not_reopen_tools_for_review(self) -> None:
        class BoundaryDriver:
            def __init__(self):
                self.calls = 0

            def propose(self, invocation):
                self.calls += 1
                if (
                    invocation.mode
                    is EngineeringAgentInvocationMode.EVIDENCE_ONLY_SYNTHESIS
                ):
                    return _proposal(
                        invocation,
                        call_ref=f"agent-terminal-review-{self.calls}",
                        phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                        draft=EngineeringAgentDraftProposal.create(
                            response_kind=EngineeringAgentResponseKind.LIMITATION,
                            content="现有证据边界不足以确认该行为。",
                            boundary_observation_ids=tuple(
                                item.observation_id
                                for item in invocation.observations
                            ),
                        ),
                        open_items=(),
                    )
                return _proposal(
                    invocation,
                    call_ref=f"agent-terminal-review-{self.calls}",
                    phase=EngineeringAgentWorkPhase.INVESTIGATING,
                    action=_action(
                        EngineeringAgentToolOperation.SOURCE_SEARCH,
                        query=f"missing evidence {self.calls}",
                    ),
                )

        class EvidenceRequiredReviewer:
            def __init__(self):
                self.requests = []

            def review(self, request):
                self.requests.append(request)
                return EngineeringAgentReviewProposal.create(
                    model_call_ref="review-terminal-evidence-required",
                    decision=EngineeringAgentReviewDecision.FINDINGS,
                    content_coverage_assessments=_fixture_content_coverage(request),
                    requirement_coverage_assessment=(
                        _full_requirement_coverage(request)
                    ),
                    findings=(
                        EngineeringAgentReviewFinding.create(
                            code="MORE_EVIDENCE_REQUIRED",
                            message="当前 Package 不能支持该结论。",
                            requires_evidence=True,
                        ),
                    ),
                )

        reviewer = EvidenceRequiredReviewer()
        service, tool, _, response = _service(
            BoundaryDriver(),
            tool=RecordingToolPort(progress=False),
            reviewer=reviewer,
            limits=EngineeringAgentLoopLimits(
                maximum_agent_steps=4,
                maximum_tool_actions=4,
                maximum_reviews=1,
                maximum_consecutive_no_progress=2,
            ),
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="查找不存在的证据",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code,
            "AGENT_NO_PROGRESS_LIMIT_REACHED",
        )
        self.assertEqual(
            submission.turn.provider_failure_classification,
            EngineeringProviderFailureClassification.MODEL_REVIEW_REJECTED,
        )
        self.assertEqual(submission.turn.provider_dispatch_count, 4)
        self.assertEqual(len(tool.requests), 2)
        self.assertEqual(len(reviewer.requests), 1)
        self.assertEqual(len(response.requests), 0)
        self.assertEqual(submission.snapshot.conversation.state.value, "ACTIVE")
        self.assertIsNone(submission.snapshot.context.work_state_ref)

    def test_forged_tool_result_binding_fails_closed_with_dispatch_audit(self) -> None:
        class OneActionDriver:
            def propose(self, invocation):
                return _proposal(
                    invocation,
                    call_ref="agent-forged-tool-1",
                    phase=EngineeringAgentWorkPhase.INVESTIGATING,
                    action=_action(
                        EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                        query="trusted current state",
                    ),
                )

        class ForgedToolPort:
            def execute(self, request):
                return EngineeringAgentToolResult.create(
                    tool_request_digest=digest_of({"forged": request.digest.value}),
                    result_ref="forged-result",
                    content="this result is bound to the wrong request",
                    disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
                    progress=True,
                )

        service, _, _, response = _service(
            OneActionDriver(), tool=ForgedToolPort()
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="读取当前状态",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.failure_code, "AGENT_PROTOCOL_VIOLATION")
        self.assertEqual(submission.turn.provider_dispatch_count, 1)
        self.assertEqual(submission.turn.delivery_state, "NOT_AUTHORIZED")
        self.assertEqual(len(response.requests), 0)

    def test_qualified_tool_mode_rejects_unreceipted_evidence(self) -> None:
        class OneActionDriver:
            def propose(self, invocation):
                return _proposal(
                    invocation,
                    call_ref="agent-unreceipted-tool-1",
                    phase=EngineeringAgentWorkPhase.INVESTIGATING,
                    action=_action(
                        EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                        query="trusted current state",
                    ),
                )

        service, tool, _, response = _service(
            OneActionDriver(), require_receipts=True
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="读取当前状态",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.failure_code, "AGENT_PROTOCOL_VIOLATION")
        self.assertEqual(len(tool.requests), 1)
        self.assertEqual(len(response.requests), 0)

    def test_typed_model_receipts_drive_actual_dispatch_count(self) -> None:
        class ReceiptedClarificationDriver:
            def propose(self, invocation):
                work_state = _proposal(
                    invocation,
                    call_ref="receipted-agent-call",
                    phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                    draft=EngineeringAgentDraftProposal.create(
                        response_kind=EngineeringAgentResponseKind.CLARIFICATION,
                        content="请明确你指的是哪个登录入口。",
                    ),
                )
                return EngineeringAgentDriverModelResult.create(
                    proposal=work_state,
                    receipt=EngineeringAgentModelCallReceipt.create(
                        model_call_ref=work_state.model_call_ref,
                        gateway_call_ref="gateway-agent-call",
                        role=EngineeringAgentModelRole.PRIMARY_AGENT,
                        state=(
                            EngineeringAgentModelDispatchState.REPLAYED_COMPLETED
                        ),
                    ),
                )

        class ReceiptedReviewer:
            def review(self, request):
                review = EngineeringAgentReviewProposal.create(
                    model_call_ref="receipted-review-call",
                    decision=EngineeringAgentReviewDecision.APPROVED,
                    content_coverage_assessments=_fixture_content_coverage(request),
                    requirement_coverage_assessment=(
                        _full_requirement_coverage(request)
                    ),
                )
                return EngineeringAgentReviewerModelResult.create(
                    proposal=review,
                    receipt=EngineeringAgentModelCallReceipt.create(
                        model_call_ref=review.model_call_ref,
                        gateway_call_ref="gateway-review-call",
                        role=EngineeringAgentModelRole.INDEPENDENT_REVIEWER,
                        state=(
                            EngineeringAgentModelDispatchState.DISPATCHED_COMPLETED
                        ),
                    ),
                )

        service, _, _, _ = _service(
            ReceiptedClarificationDriver(), reviewer=ReceiptedReviewer()
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="它是怎样登录的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.turn.provider_dispatch_count, 1)
        self.assertEqual(len(submission.turn.model_dispatch_receipt_refs), 2)
        self.assertEqual(service.provider_dispatch_count(), 1)

    def test_post_dispatch_model_failure_retains_exact_receipt(self) -> None:
        receipt = EngineeringAgentModelCallReceipt.create(
            model_call_ref="failed-agent-call",
            gateway_call_ref="gateway-failed-call",
            role=EngineeringAgentModelRole.PRIMARY_AGENT,
            state=EngineeringAgentModelDispatchState.DISPATCHED_OUTCOME_UNKNOWN,
            failure_kind=(
                EngineeringAgentModelFailureKind.PROVIDER_OUTCOME_UNKNOWN
            ),
            failure_code="NETWORK_OUTCOME_UNKNOWN",
        )

        class FailingDriver:
            def propose(self, invocation):
                del invocation
                raise EngineeringAgentModelCallFailure(
                    receipt=receipt,
                    code=ErrorCode.LIVE_INTEGRATION_HELD,
                    message="Gateway outcome is unknown and cannot be retried",
                )

        service, _, reviewer, response = _service(FailingDriver())
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code, "AGENT_MODEL_OUTCOME_UNKNOWN"
        )
        self.assertEqual(submission.turn.provider_dispatch_count, 1)
        self.assertEqual(
            submission.turn.model_dispatch_receipt_refs,
            (receipt.digest.value,),
        )
        self.assertEqual(len(reviewer.requests), 0)
        self.assertEqual(len(response.requests), 0)

    def test_qualified_executor_rejects_unreceipted_model_proposal(self) -> None:
        class BareDriver:
            def propose(self, invocation):
                return _proposal(
                    invocation,
                    call_ref="unreceipted-agent-call",
                    phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                    draft=EngineeringAgentDraftProposal.create(
                        response_kind=EngineeringAgentResponseKind.CLARIFICATION,
                        content="请明确登录入口。",
                    ),
                )

        service, _, reviewer, response = _service(
            BareDriver(), require_model_receipts=True
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="它怎样登录？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.failure_code, "AGENT_PROTOCOL_VIOLATION")
        self.assertEqual(submission.turn.provider_dispatch_count, 0)
        self.assertEqual(submission.turn.model_dispatch_receipt_refs, ())
        self.assertEqual(len(reviewer.requests), 0)
        self.assertEqual(len(response.requests), 0)

    def test_wrong_role_failure_is_protocol_violation_but_keeps_dispatch_audit(self) -> None:
        receipt = EngineeringAgentModelCallReceipt.create(
            model_call_ref="wrong-role-call",
            gateway_call_ref="gateway-wrong-role-call",
            role=EngineeringAgentModelRole.INDEPENDENT_REVIEWER,
            state=EngineeringAgentModelDispatchState.DISPATCHED_REJECTED,
            failure_kind=(
                EngineeringAgentModelFailureKind.PROVIDER_OUTPUT_INVALID
            ),
            failure_code="STRUCTURED_OUTPUT_INVALID",
        )

        class WrongRoleDriver:
            def propose(self, invocation):
                del invocation
                raise EngineeringAgentModelCallFailure(
                    receipt=receipt,
                    code=ErrorCode.STRUCTURED_OUTPUT_INVALID,
                    message="wrong role receipt",
                )

        service, _, reviewer, response = _service(WrongRoleDriver())
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.failure_code, "AGENT_PROTOCOL_VIOLATION")
        self.assertEqual(submission.turn.provider_dispatch_count, 1)
        self.assertEqual(
            submission.turn.model_dispatch_receipt_refs,
            (receipt.digest.value,),
        )
        self.assertEqual(len(reviewer.requests), 0)
        self.assertEqual(len(response.requests), 0)

    def test_replayed_unknown_model_outcome_does_not_increment_dispatch_count(self) -> None:
        receipt = EngineeringAgentModelCallReceipt.create(
            model_call_ref="replayed-unknown-agent-call",
            gateway_call_ref="gateway-replayed-unknown-call",
            role=EngineeringAgentModelRole.PRIMARY_AGENT,
            state=EngineeringAgentModelDispatchState.REPLAYED_OUTCOME_UNKNOWN,
            failure_kind=(
                EngineeringAgentModelFailureKind.PROVIDER_OUTCOME_UNKNOWN
            ),
            failure_code="PROVIDER_OUTCOME_UNKNOWN",
        )

        class ReplayedUnknownDriver:
            def propose(self, invocation):
                del invocation
                raise EngineeringAgentModelCallFailure(
                    receipt=receipt,
                    code=ErrorCode.LIVE_INTEGRATION_HELD,
                    message="recovered terminal outcome-unknown call",
                )

        service, _, _, _ = _service(ReplayedUnknownDriver())
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code, "AGENT_MODEL_OUTCOME_UNKNOWN"
        )
        self.assertEqual(submission.turn.provider_dispatch_count, 0)
        self.assertEqual(
            submission.turn.model_dispatch_receipt_refs,
            (receipt.digest.value,),
        )

    def test_source_operation_is_denied_when_binding_has_no_source_authority(self) -> None:
        class UnauthorizedSourceDriver:
            def propose(self, invocation):
                self.available_operations = invocation.available_operations
                return _proposal(
                    invocation,
                    call_ref="agent-unauthorized-source-1",
                    phase=EngineeringAgentWorkPhase.INVESTIGATING,
                    action=_action(
                        EngineeringAgentToolOperation.SOURCE_READ,
                        query="unavailable source",
                    ),
                )

        binding = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="mall",
            repository_revision="b" * 40,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=digest_of({"world_model": "exact"}),
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref="qualified-route@1",
            known_limitations=("Alpha only", "Production is disabled"),
        )
        driver = UnauthorizedSourceDriver()
        tool = RecordingToolPort()
        executor = ApplicationOwnedEngineeringAgentTurnExecutor(
            driver=driver,
            tool_port=tool,
            reviewer=ApprovingReviewer(),
            response_control=RecordingResponseControl(),
            available_operations=(
                EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                EngineeringAgentToolOperation.SOURCE_READ,
            ),
            id_generator=SequentialIdGenerator(),
        )
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=executor,
            id_generator=SequentialIdGenerator(),
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="读取未授权来源",
        )

        self.assertEqual(
            driver.available_operations,
            (EngineeringAgentToolOperation.WORLD_MODEL_QUERY,),
        )
        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.failure_code, "AGENT_PROTOCOL_VIOLATION")
        self.assertEqual(len(tool.requests), 0)

    def test_forged_delivery_authorization_cannot_release_reviewed_text(self) -> None:
        class ClarificationDriver:
            def propose(self, invocation):
                return _proposal(
                    invocation,
                    call_ref="agent-forged-delivery-1",
                    phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                    draft=EngineeringAgentDraftProposal.create(
                        response_kind=EngineeringAgentResponseKind.CLARIFICATION,
                        content="请明确你指的是哪个组件。",
                    ),
                )

        class ForgedResponseControl(RecordingResponseControl):
            def authorize(self, request):
                self.requests.append(request)
                return EngineeringAgentDeliveryAuthorization.create(
                    authorization_ref="forged-delivery",
                    turn_request_digest=request.turn_request_digest,
                    work_state_digest=request.work_state.digest,
                    package_digest=request.package.digest,
                    answer_digest=request.draft.digest,
                    review_digest=digest_of({"forged": request.review.digest.value}),
                )

        response = ForgedResponseControl()
        service, _, _, _ = _service(
            ClarificationDriver(), response=response
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="它是什么？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(submission.turn.failure_code, "AGENT_PROTOCOL_VIOLATION")
        self.assertEqual(submission.turn.provider_dispatch_count, 2)
        self.assertIsNone(submission.turn.delivery_authorization_ref)
        self.assertEqual(submission.snapshot.messages[-1].kind, ConversationMessageKind.LIMITATION)
        self.assertEqual(len(response.requests), 1)

    def test_user_correction_supersedes_reviewed_conclusion_without_rewriting_history(self) -> None:
        class CorrectionDriver:
            def __init__(self):
                self.calls_by_turn = {}

            def propose(self, invocation):
                sequence = invocation.request.sequence
                call = self.calls_by_turn.get(sequence, 0) + 1
                self.calls_by_turn[sequence] = call
                context = invocation.request.snapshot_before.context
                corrections = context.accepted_correction_message_ids
                superseded = context.superseded_conclusion_refs
                if sequence == 2:
                    corrections = (*corrections, invocation.request.user_message.message_id)
                    superseded = context.reviewed_conclusion_refs
                if call == 1:
                    return _proposal(
                        invocation,
                        call_ref=f"agent-correction-{sequence}-1",
                        phase=EngineeringAgentWorkPhase.INVESTIGATING,
                        action=_action(
                            EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                            query=f"turn {sequence} current truth",
                        ),
                        accepted_corrections=corrections,
                        superseded=superseded,
                    )
                observation_id = invocation.observations[0].observation_id
                return _proposal(
                    invocation,
                    call_ref=f"agent-correction-{sequence}-2",
                    phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                    draft=EngineeringAgentDraftProposal.create(
                        response_kind=EngineeringAgentResponseKind.ANSWER,
                        content=f"第 {sequence} 轮当前结论。",
                        claims=(
                            EngineeringAgentClaimProposal.create(
                                statement=f"第 {sequence} 轮结论有当前证据。",
                                support_observation_ids=(observation_id,),
                            ),
                        ),
                    ),
                    accepted_corrections=corrections,
                    superseded=superseded,
                )

        driver = CorrectionDriver()
        service, _, _, _ = _service(driver)
        conversation = service.create_conversation()
        first = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="先说明默认登录行为",
        )
        prior_conclusion = first.snapshot.context.reviewed_conclusion_refs[0]
        second = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(2),
            message="纠正：只讨论禁用账户",
        )

        self.assertEqual(
            second.snapshot.context.accepted_correction_message_ids,
            (second.turn.user_message_id,),
        )
        self.assertEqual(
            first.snapshot.context.work_state_ref,
            second.snapshot.context.work_state_ref,
        )
        self.assertGreater(
            second.snapshot.context.work_state_revision.value,
            first.snapshot.context.work_state_revision.value,
        )
        self.assertIn(
            prior_conclusion,
            second.snapshot.context.superseded_conclusion_refs,
        )
        self.assertEqual(len(second.snapshot.messages), 4)
        self.assertEqual(second.snapshot.messages[0].content, "先说明默认登录行为")
        self.assertEqual(second.snapshot.conversation.revision, Revision(3))

    def test_fresh_attempt_executors_share_only_committed_conversation_state(self) -> None:
        repository = InMemoryEngineeringAgentWorkStateRepository()
        initial_previous_revisions = {}

        class PerTurnDriver:
            def __init__(self, sequence):
                self.sequence = sequence
                self.calls = 0

            def propose(self, invocation):
                self.calls += 1
                if self.calls == 1:
                    initial_previous_revisions[self.sequence] = (
                        invocation.previous_work_state.revision
                        if invocation.previous_work_state is not None
                        else None
                    )
                    return _proposal(
                        invocation,
                        call_ref=f"fresh-{self.sequence}-1",
                        phase=EngineeringAgentWorkPhase.INVESTIGATING,
                        action=_action(
                            EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                            query=f"turn {self.sequence}",
                        ),
                    )
                if self.sequence == 2:
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "failed attempt must not commit its intermediate Work State",
                    )
                observation_id = invocation.observations[0].observation_id
                return _proposal(
                    invocation,
                    call_ref=f"fresh-{self.sequence}-2",
                    phase=EngineeringAgentWorkPhase.RESPONSE_READY,
                    draft=EngineeringAgentDraftProposal.create(
                        response_kind=EngineeringAgentResponseKind.ANSWER,
                        content=f"第 {self.sequence} 轮答案。",
                        claims=(
                            EngineeringAgentClaimProposal.create(
                                statement=f"第 {self.sequence} 轮有密封证据。",
                                support_observation_ids=(observation_id,),
                            ),
                        ),
                    ),
                )

        class FreshExecutorPerTurn:
            def execute(self, request):
                executor = ApplicationOwnedEngineeringAgentTurnExecutor(
                    driver=PerTurnDriver(request.sequence),
                    tool_port=RecordingToolPort(),
                    reviewer=ApprovingReviewer(),
                    response_control=RecordingResponseControl(),
                    available_operations=(
                        EngineeringAgentToolOperation.WORLD_MODEL_QUERY,
                    ),
                    work_state_repository=repository,
                    id_generator=SequentialIdGenerator(),
                )
                return executor.execute(request)

        service = InMemoryEngineeringConversationService(
            _ready_binding(),
            turn_executor=FreshExecutorPerTurn(),
            id_generator=SequentialIdGenerator(),
        )
        conversation = service.create_conversation()
        first = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="先说明登录流程",
        )
        failed = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(2),
            message="这轮模拟失败",
        )
        third = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(3),
            message="继续上一条已提交结论",
        )

        self.assertEqual(first.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(failed.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(third.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertIsNone(initial_previous_revisions[1])
        self.assertEqual(
            initial_previous_revisions[2],
            first.snapshot.context.work_state_revision,
        )
        self.assertEqual(
            initial_previous_revisions[3],
            first.snapshot.context.work_state_revision,
        )
        self.assertEqual(
            failed.snapshot.context.work_state_digest,
            first.snapshot.context.work_state_digest,
        )
        self.assertGreater(
            third.snapshot.context.work_state_revision.value,
            first.snapshot.context.work_state_revision.value,
        )

    def test_sealed_response_control_authorizes_exact_approved_chain_once(self) -> None:
        response = RecordingResponseControl()
        service, _, _, _ = _service(
            ReplanningAnswerDriver(),
            response=response,
        )
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )
        request = response.requests[0]
        control = SealedEngineeringAgentResponseControl()

        forged_package = replace(
            request.package,
            origin_work_state_digest=digest_of({"forged": "origin"}),
        )
        with self.assertRaises(DomainError) as raised:
            control.authorize(replace(request, package=forged_package))
        self.assertEqual(
            raised.exception.code,
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        )

        authorization = control.authorize(request)

        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(
            authorization.turn_request_digest,
            request.turn_request_digest,
        )
        self.assertEqual(authorization.review_digest, request.review.digest)
        with self.assertRaises(DomainError):
            control.authorize(request)


if __name__ == "__main__":
    unittest.main()
