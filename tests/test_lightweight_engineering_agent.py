from __future__ import annotations

import json
import unittest

from software_world_model.application_services.conversational_engineering_agent import (
    EngineeringAgentCitation,
    EngineeringAgentEvidenceDisposition,
    EngineeringAgentLoopLimits,
    EngineeringAgentModelCallReceipt,
    EngineeringAgentModelDispatchState,
    EngineeringAgentModelRole,
    EngineeringAgentToolAuthorityKind,
    EngineeringAgentToolAuthorityReceipt,
    EngineeringAgentToolOperation,
    EngineeringAgentToolResult,
)
from software_world_model.application_services.engineering_conversation import (
    EngineeringChatBinding,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.application_services.lightweight_engineering_agent import (
    ApplicationOwnedLightweightAgentTurnExecutor,
    LightweightAgentAction,
    LightweightAgentDecision,
    LightweightAgentResponseKind,
    LightweightAgentTraceStore,
    LightweightCitationSelection,
    LightweightDecisionResult,
    LightweightReview,
    LightweightReviewResult,
    LightweightReviewVerdict,
    SealedLightweightDeliveryControl,
)
from software_world_model.cross_cutting import Revision, StableId, digest_of


REVISION = "a" * 40


def _binding() -> EngineeringChatBinding:
    return EngineeringChatBinding.create(
        product_revision="b" * 40,
        project_name="example",
        repository_revision=REVISION,
        world_model_status=RuntimeCapabilityStatus.READY,
        world_model_authority_digest=digest_of("world-model"),
        source_profile_ref="source-profile",
        source_access_status=RuntimeCapabilityStatus.READY,
        provider_status=RuntimeCapabilityStatus.READY,
        provider_route_ref="preferred-then-fallback",
        known_limitations=("diagnostic baseline",),
    )


def _id(kind: str, ordinal: int) -> StableId:
    return StableId(f"{kind}_{ordinal:032x}")


class _SourceTool:
    def __init__(self) -> None:
        self.calls = []
        self._ordinal = 0

    def source_read_options(self, request):
        return ()

    def execute(self, request):
        self.calls.append(request)
        self._ordinal += 1
        operation = request.action.operation
        if operation is EngineeringAgentToolOperation.SOURCE_SEARCH:
            locator = f"src/example/Entry{self._ordinal}.java:L1-L8"
            content = json.dumps(
                {
                    "result": "search match",
                    "locator": locator,
                    "next": "read the matching source",
                },
                sort_keys=True,
            )
        else:
            locator = f"src/example/Entry{self._ordinal}.java:L1-L80"
            content = json.dumps(
                {
                    "result": "full source",
                    "locator": locator,
                    "behavior": "the entry delegates after checking its input",
                },
                sort_keys=True,
            )
        citation = EngineeringAgentCitation.create(
            citation_ref=_id("locator", self._ordinal).value,
            evidence_class="SOURCE",
            source_revision=REVISION,
            locator=locator,
            modality="SOURCE_TEXT",
            content_digest=digest_of(content),
        )
        evidence_request_digest = digest_of(
            ["test-evidence-request", request.turn_request_digest.value]
        )
        ledger_ref = _id("ledger", self._ordinal)
        prefix = digest_of(
            [
                "EVIDENCE_LEDGER_PREFIX@1",
                ledger_ref.value,
                evidence_request_digest.value,
                1,
                None,
                (),
            ]
        )
        authority = EngineeringAgentToolAuthorityReceipt.create(
            authority_kind=EngineeringAgentToolAuthorityKind.SOURCE,
            turn_request_digest=request.turn_request_digest,
            tool_request_digest=request.digest,
            evidence_request_digest=evidence_request_digest,
            repository_revision=REVISION,
            evidence_digest=digest_of(content),
            ledger_ref=ledger_ref.value,
            ledger_generation=1,
            ledger_parent_seal_digest=None,
            ledger_prefix_digest=prefix,
            ledger_entries=(),
            citations=(citation,),
        )
        return EngineeringAgentToolResult.create(
            tool_request_digest=request.digest,
            result_ref=f"result-{self._ordinal}",
            content=content,
            disposition=EngineeringAgentEvidenceDisposition.SUPPORT,
            progress=True,
            citation_refs=(citation.citation_ref,),
            authority_receipt=authority,
        )


class _Model:
    instance_ref = "test-lightweight-model"

    def __init__(self) -> None:
        self.steps = []
        self.reviews = []
        self._calls = 0

    def _receipt(self, role):
        self._calls += 1
        ref = _id("modelcall", self._calls).value
        return EngineeringAgentModelCallReceipt.create(
            model_call_ref=ref,
            gateway_call_ref=ref,
            role=role,
            state=EngineeringAgentModelDispatchState.DISPATCHED_COMPLETED,
        )

    def decide(self, request):
        self.steps.append(request)
        question = request.turn_request.user_message.content
        if not request.observations:
            decision = LightweightAgentDecision(
                goal=question,
                plan="Find the relevant entry before making a conclusion.",
                action=LightweightAgentAction.SEARCH_SOURCE,
                query="Entry",
                read_index=None,
                response_kind=None,
                answer=None,
                citations=(),
            )
        elif request.observations[-1].operation is (
            EngineeringAgentToolOperation.SOURCE_SEARCH
        ):
            decision = LightweightAgentDecision(
                goal=question,
                plan="The search found a candidate; read it to establish behavior.",
                action=LightweightAgentAction.READ_SOURCE,
                query=None,
                read_index=request.read_candidates[-1].read_index,
                response_kind=None,
                answer=None,
                citations=(),
            )
        else:
            decision = LightweightAgentDecision(
                goal=question,
                plan="The full source answers the current request; stop.",
                action=LightweightAgentAction.FINISH,
                query=None,
                read_index=None,
                response_kind=LightweightAgentResponseKind.ANSWER,
                answer=f"针对“{question}”：入口先检查输入，再调用协作者。",
                citations=(
                    LightweightCitationSelection(
                        request.observations[-1].observation_index,
                        1,
                    ),
                ),
            )
        return LightweightDecisionResult(
            decision=decision,
            receipt=self._receipt(EngineeringAgentModelRole.PRIMARY_AGENT),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )

    def review(self, request):
        self.reviews.append(request)
        return LightweightReviewResult(
            review=LightweightReview(
                verdict=LightweightReviewVerdict.APPROVED,
                findings=(),
            ),
            receipt=self._receipt(
                EngineeringAgentModelRole.INDEPENDENT_REVIEWER
            ),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )


class _NeedsMoreEvidenceModel(_Model):
    def decide(self, request):
        self.steps.append(request)
        if not request.observations:
            decision = LightweightAgentDecision(
                goal=request.goal,
                plan="Search once before deciding.",
                action=LightweightAgentAction.SEARCH_SOURCE,
                query="Entry",
                read_index=None,
                response_kind=None,
                answer=None,
                citations=(),
            )
        else:
            decision = LightweightAgentDecision(
                goal=request.goal,
                plan="The tool budget is closed; report the evidence gap.",
                action=LightweightAgentAction.FINISH,
                query=None,
                read_index=None,
                response_kind=LightweightAgentResponseKind.LIMITATION,
                answer="现有证据不足以确认请求中的实现行为。",
                citations=(),
            )
        return LightweightDecisionResult(
            decision=decision,
            receipt=self._receipt(EngineeringAgentModelRole.PRIMARY_AGENT),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )

    def review(self, request):
        self.reviews.append(request)
        return LightweightReviewResult(
            review=LightweightReview(
                verdict=LightweightReviewVerdict.MORE_EVIDENCE,
                findings=("需要读取实现源码才能回答。",),
            ),
            receipt=self._receipt(
                EngineeringAgentModelRole.INDEPENDENT_REVIEWER
            ),
            disclosure_record_ref=f"disclosure-{self._calls}",
        )


class LightweightEngineeringAgentTest(unittest.TestCase):
    def test_two_questions_and_followup_replan_from_source_observations(self) -> None:
        binding = _binding()
        model = _Model()
        tool = _SourceTool()
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=tool,
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-test",
        )
        service = InMemoryEngineeringConversationService(
            binding, turn_executor=executor
        )
        snapshot = service.create_conversation()
        questions = (
            "入口如何处理输入？",
            "失败路径会继续调用协作者吗？",
            "结合前两轮，调用发生在检查之前还是之后？",
        )
        submissions = []
        for question in questions:
            submission = service.submit_turn(
                conversation_id=snapshot.conversation.conversation_id,
                expected_revision=snapshot.conversation.revision,
                message=question,
            )
            submissions.append(submission)
            snapshot = submission.snapshot

        self.assertEqual(len(tool.calls), 6)
        self.assertEqual(len(model.reviews), 3)
        self.assertTrue(all(item.turn.citations for item in submissions))
        self.assertEqual(snapshot.conversation.revision, Revision(4))
        self.assertEqual(snapshot.context.work_state_revision, Revision(3))
        for submission in submissions:
            trajectories = traces.for_turn(submission.turn.request_digest)
            self.assertEqual(len(trajectories), 1)
            trace = trajectories[0]
            self.assertEqual(trace.terminal_status, "SUCCEEDED")
            actions = [
                item["action"]
                for item in trace.events
                if item["kind"] == "MODEL_DECISION"
            ]
            self.assertEqual(
                actions, ["SEARCH_SOURCE", "READ_SOURCE", "FINISH"]
            )
            decisions = [
                item
                for item in trace.events
                if item["kind"] == "MODEL_DECISION"
            ]
            self.assertEqual(decisions[0]["query"], "Entry")
            self.assertIsNone(decisions[0]["read_index"])
            self.assertIsNone(decisions[1]["query"])
            self.assertIsInstance(decisions[1]["read_index"], int)
            self.assertIsNone(decisions[2]["query"])
            self.assertIsNone(decisions[2]["read_index"])
            plans = [
                item["plan"]
                for item in trace.events
                if item["kind"] == "MODEL_DECISION"
            ]
            self.assertEqual(len(set(plans)), 3)

    def test_more_evidence_after_tool_fuse_fails_without_repeated_reviews(self) -> None:
        model = _NeedsMoreEvidenceModel()
        traces = LightweightAgentTraceStore()
        executor = ApplicationOwnedLightweightAgentTurnExecutor(
            model=model,
            tool_port=_SourceTool(),
            delivery_control=SealedLightweightDeliveryControl(),
            trace_store=traces,
            attempt_ref="attempt-tool-fuse",
            limits=EngineeringAgentLoopLimits(
                maximum_agent_steps=11,
                maximum_tool_actions=1,
                maximum_reviews=4,
            ),
        )
        service = InMemoryEngineeringConversationService(
            _binding(), turn_executor=executor
        )
        snapshot = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=snapshot.conversation.conversation_id,
            expected_revision=snapshot.conversation.revision,
            message="实现失败时会发生什么？",
        )

        self.assertEqual(submission.turn.failure_code, "BUDGET_EXHAUSTED")
        self.assertEqual(submission.turn.provider_dispatch_count, 3)
        self.assertEqual(len(model.steps), 2)
        self.assertEqual(len(model.reviews), 1)
        trace = traces.for_turn(submission.turn.request_digest)[0]
        self.assertEqual(trace.terminal_status, "FAILED")
        self.assertEqual(
            [item["kind"] for item in trace.events].count(
                "INDEPENDENT_REVIEW"
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
