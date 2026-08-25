from __future__ import annotations

import unittest

from software_world_model.application_services.conversational_engineering_agent import (
    ApplicationOwnedEngineeringAgentTurnExecutor,
    EngineeringAgentClaimProposal,
    EngineeringAgentDeliveryAuthorization,
    EngineeringAgentDraftProposal,
    EngineeringAgentEvidenceDisposition,
    EngineeringAgentLoopLimits,
    EngineeringAgentResponseKind,
    EngineeringAgentReviewDecision,
    EngineeringAgentReviewFinding,
    EngineeringAgentReviewProposal,
    EngineeringAgentToolActionProposal,
    EngineeringAgentToolOperation,
    EngineeringAgentToolResult,
    EngineeringAgentWorkPhase,
    EngineeringAgentWorkStateProposal,
)
from software_world_model.application_services.engineering_conversation import (
    ConversationMessageKind,
    ConversationTurnState,
    EngineeringChatBinding,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import Revision, StableId, digest_of


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


def _service(driver, *, tool=None, reviewer=None, response=None, limits=None):
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

    def test_reviewer_finding_returns_to_same_agent_and_reuses_package(self) -> None:
        class RewriteDriver:
            def __init__(self):
                self.calls = 0
                self.findings_seen = []
                self.review_digests_seen = []

            def propose(self, invocation):
                self.calls += 1
                self.findings_seen.append(invocation.review_findings)
                self.review_digests_seen.append(invocation.review_digest)
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
                )

        driver = RewriteDriver()
        reviewer = RewriteReviewer()
        service, _, _, response = _service(driver, reviewer=reviewer)
        conversation = service.create_conversation()
        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="说明当前行为",
        )

        self.assertEqual(submission.turn.provider_dispatch_count, 5)
        self.assertEqual(len(reviewer.requests), 2)
        self.assertEqual(
            reviewer.requests[0].package.digest,
            reviewer.requests[1].package.digest,
        )
        self.assertEqual(len(driver.findings_seen[2]), 1)
        self.assertIsNotNone(driver.review_digests_seen[2])
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

            def propose(self, invocation):
                self.calls += 1
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

    def test_no_progress_fuse_fails_only_the_turn(self) -> None:
        class NoProgressDriver:
            def __init__(self):
                self.calls = 0

            def propose(self, invocation):
                self.calls += 1
                return _proposal(
                    invocation,
                    call_ref=f"agent-no-progress-{self.calls}",
                    phase=EngineeringAgentWorkPhase.INVESTIGATING,
                    action=_action(
                        EngineeringAgentToolOperation.SOURCE_SEARCH,
                        query=f"unresolved evidence {self.calls}",
                    ),
                )

        service, tool, reviewer, response = _service(
            NoProgressDriver(),
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
        self.assertEqual(
            submission.turn.failure_code, "AGENT_NO_PROGRESS_LIMIT_REACHED"
        )
        self.assertEqual(submission.turn.delivery_state, "NOT_AUTHORIZED")
        self.assertEqual(submission.turn.provider_dispatch_count, 2)
        self.assertEqual(len(tool.requests), 2)
        self.assertEqual(len(reviewer.requests), 0)
        self.assertEqual(len(response.requests), 0)
        self.assertEqual(
            submission.snapshot.conversation.state.value,
            "ACTIVE",
        )
        self.assertIsNone(submission.snapshot.context.work_state_ref)

        next_submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(2),
            message="换一个方向继续",
        )
        self.assertEqual(next_submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            next_submission.turn.failure_code,
            "AGENT_NO_PROGRESS_LIMIT_REACHED",
        )
        self.assertIsNone(next_submission.snapshot.context.work_state_ref)
        self.assertEqual(next_submission.snapshot.conversation.revision, Revision(3))

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


if __name__ == "__main__":
    unittest.main()
