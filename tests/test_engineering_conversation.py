from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from threading import Event, Thread
import unittest

from software_world_model.application_services.engineering_conversation import (
    ENGINEERING_CHAT_APPLICATION_CLARIFICATION_QUALITY,
    ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN,
    ConversationLifecycleState,
    ConversationMessageKind,
    ConversationNotFoundError,
    ConversationTurnState,
    EngineeringChatBinding,
    EngineeringTurnCitation,
    EngineeringTurnExecutionOutcome,
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


def _binding(
    provider_status: RuntimeCapabilityStatus = RuntimeCapabilityStatus.NOT_CONFIGURED,
) -> EngineeringChatBinding:
    return EngineeringChatBinding.create(
        product_revision="a" * 40,
        project_name="mall",
        repository_revision="b" * 40,
        provider_status=provider_status,
        known_limitations=(
            "Chat Access only",
            "src/main/resources and credentials are excluded",
        ),
    )


class EngineeringConversationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = InMemoryEngineeringConversationService(
            _binding(),
            id_generator=SequentialIdGenerator(),
            clock=lambda: datetime(2026, 8, 25, 7, 0, tzinfo=timezone.utc),
        )

    def test_new_conversation_has_server_identity_and_empty_work_state(self) -> None:
        snapshot = self.service.create_conversation()

        self.assertEqual(snapshot.conversation.conversation_id.kind, "conversation")
        self.assertEqual(snapshot.conversation.revision, Revision(1))
        self.assertEqual(snapshot.conversation.state, ConversationLifecycleState.ACTIVE)
        self.assertEqual(snapshot.context.included_user_message_ids, ())
        self.assertEqual(snapshot.context.reducer_status, "NOT_EXECUTED_ACCESS_ONLY")
        self.assertEqual(snapshot.messages, ())
        self.assertEqual(snapshot.turns, ())

    def test_turn_is_recorded_as_honest_failure_without_provider_dispatch(self) -> None:
        created = self.service.create_conversation()
        submission = self.service.submit_turn(
            conversation_id=created.conversation.conversation_id,
            expected_revision=created.conversation.revision,
            message="登录流程是怎样的？",
        )

        turn = submission.turn
        self.assertEqual(turn.state, ConversationTurnState.FAILED)
        self.assertEqual(turn.failure_code, "MODEL_EXECUTION_NOT_CONFIGURED")
        self.assertEqual(turn.provider_dispatch_count, 0)
        self.assertEqual(turn.retry_count, 0)
        self.assertEqual(turn.delivery_state, "NOT_AUTHORIZED")
        self.assertEqual(turn.quality_status, "NOT_ACCEPTED")
        self.assertEqual(turn.production_activation, "NOT_EXECUTED")
        self.assertIsNone(turn.evidence_package_ref)
        self.assertIsNone(turn.answer_ref)
        self.assertIsNone(turn.review_ref)
        self.assertEqual(submission.snapshot.conversation.revision, Revision(2))
        self.assertEqual(
            submission.snapshot.conversation.state,
            ConversationLifecycleState.ACTIVE,
        )
        self.assertEqual(
            tuple(item.kind for item in submission.snapshot.messages),
            (ConversationMessageKind.USER_INPUT, ConversationMessageKind.LIMITATION),
        )
        self.assertEqual(
            submission.snapshot.context.included_user_message_ids,
            (turn.user_message_id,),
        )

    def test_failed_turn_does_not_close_conversation(self) -> None:
        created = self.service.create_conversation()
        first = self.service.submit_turn(
            conversation_id=created.conversation.conversation_id,
            expected_revision=Revision(1),
            message="先解释登录流程",
        )
        second = self.service.submit_turn(
            conversation_id=created.conversation.conversation_id,
            expected_revision=first.snapshot.conversation.revision,
            message="再说明失败分支",
        )

        self.assertEqual(second.turn.sequence, 2)
        self.assertEqual(second.snapshot.conversation.revision, Revision(3))
        self.assertEqual(second.snapshot.conversation.state, ConversationLifecycleState.ACTIVE)
        self.assertEqual(len(second.snapshot.turns), 2)
        self.assertEqual(len(second.snapshot.messages), 4)
        self.assertNotEqual(
            first.snapshot.context.digest,
            second.snapshot.context.digest,
        )
        history = self.service.revision_history(created.conversation.conversation_id)
        self.assertEqual(tuple(item.conversation.revision.value for item in history), (1, 2, 3))

    def test_new_conversation_does_not_inherit_old_context(self) -> None:
        first = self.service.create_conversation()
        first_result = self.service.submit_turn(
            conversation_id=first.conversation.conversation_id,
            expected_revision=Revision(1),
            message="记住这个登录问题",
        )
        second = self.service.create_conversation()

        self.assertNotEqual(
            first_result.snapshot.conversation.conversation_id,
            second.conversation.conversation_id,
        )
        self.assertEqual(second.context.included_user_message_ids, ())
        self.assertEqual(second.messages, ())
        self.assertEqual(second.turns, ())

    def test_empty_new_conversation_requests_referent_before_executor_dispatch(self) -> None:
        class RecordingExecutor:
            def __init__(self):
                self.requests = []

            def execute(self, request):
                self.requests.append(request)
                return EngineeringTurnExecutionOutcome.failed(
                    request_digest=request.request_digest,
                    assistant_content="fixture executor reached",
                    included_user_message_ids=(request.user_message.message_id,),
                    failure_code="FIXTURE_EXECUTOR_REACHED",
                    failure_message="fixture executor reached",
                )

        executor = RecordingExecutor()
        binding = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="mall",
            repository_revision="b" * 40,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=digest_of({"world_model": "exact"}),
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref="qualified-route",
            conversation_input_policy_ref=(
                ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN
            ),
            known_limitations=("Alpha only",),
        )
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=executor,
            id_generator=SequentialIdGenerator(),
        )
        for message in (
            "它失败时会记录什么？",
            "这些失败也会回滚吗？",
            "那些写入都会回滚吗？",
            "此类副作用能确认吗？",
        ):
            with self.subTest(message=message):
                conversation = service.create_conversation()
                submission = service.submit_turn(
                    conversation_id=conversation.conversation.conversation_id,
                    expected_revision=Revision(1),
                    message=message,
                )

                self.assertEqual(executor.requests, [])
                self.assertEqual(
                    submission.turn.state, ConversationTurnState.SUCCEEDED
                )
                self.assertEqual(
                    submission.snapshot.messages[-1].kind,
                    ConversationMessageKind.CLARIFICATION,
                )
                self.assertIn("请明确", submission.snapshot.messages[-1].content)
                self.assertEqual(submission.turn.provider_dispatch_count, 0)
                self.assertEqual(submission.turn.retry_count, 0)
                self.assertEqual(submission.turn.delivery_state, "NOT_AUTHORIZED")
                self.assertEqual(
                    submission.turn.quality_status,
                    ENGINEERING_CHAT_APPLICATION_CLARIFICATION_QUALITY,
                )
                self.assertIsNone(submission.turn.work_state_ref)
                self.assertEqual(
                    submission.snapshot.context.included_user_message_ids,
                    (submission.turn.user_message_id,),
                )

        explicit = service.create_conversation()
        explicit_submission = service.submit_turn(
            conversation_id=explicit.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )
        self.assertEqual(len(executor.requests), 1)
        self.assertEqual(
            explicit_submission.turn.failure_code,
            "FIXTURE_EXECUTOR_REACHED",
        )

    def test_binding_rejects_unregistered_conversation_input_policy(self) -> None:
        with self.assertRaises(DomainError) as failure:
            EngineeringChatBinding.create(
                product_revision="a" * 40,
                project_name="mall",
                repository_revision="b" * 40,
                conversation_input_policy_ref="UNREGISTERED_INPUT_POLICY@1",
                known_limitations=("Alpha only",),
            )
        self.assertEqual(failure.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_executor_cannot_claim_application_clarification_for_explicit_input(self) -> None:
        class ForgedClarificationExecutor:
            def execute(self, request):
                return EngineeringTurnExecutionOutcome.application_clarification(
                    request_digest=request.request_digest,
                    assistant_content="请明确对象。",
                    included_user_message_ids=(request.user_message.message_id,),
                    accepted_correction_message_ids=(),
                    reviewed_conclusion_refs=(),
                    superseded_conclusion_refs=(),
                )

        binding = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="mall",
            repository_revision="b" * 40,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=digest_of({"world_model": "exact"}),
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref="qualified-route",
            conversation_input_policy_ref=(
                ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN
            ),
            known_limitations=("Alpha only",),
        )
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=ForgedClarificationExecutor(),
            id_generator=SequentialIdGenerator(),
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="登录流程是怎样的？",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code,
            "TURN_EXECUTOR_PROTOCOL_VIOLATION",
        )
        self.assertEqual(submission.turn.provider_dispatch_count, 0)

    def test_stale_revision_and_invalid_messages_do_not_mutate_state(self) -> None:
        created = self.service.create_conversation()
        with self.assertRaises(DomainError) as stale:
            self.service.submit_turn(
                conversation_id=created.conversation.conversation_id,
                expected_revision=Revision(2),
                message="并发提交",
            )
        self.assertEqual(stale.exception.code, ErrorCode.REVISION_CONFLICT)

        for invalid in ("", " leading", "trailing ", "x" * 16_001):
            with self.subTest(invalid_length=len(invalid)):
                with self.assertRaises(DomainError) as failure:
                    self.service.submit_turn(
                        conversation_id=created.conversation.conversation_id,
                        expected_revision=Revision(1),
                        message=invalid,
                    )
                self.assertEqual(failure.exception.code, ErrorCode.INVALID_ARGUMENT)

        current = self.service.get_conversation(created.conversation.conversation_id)
        self.assertEqual(current.conversation.revision, Revision(1))
        self.assertEqual(current.turns, ())

    def test_unknown_conversation_is_typed_and_provider_ready_is_rejected(self) -> None:
        with self.assertRaises(ConversationNotFoundError):
            self.service.get_conversation(StableId("conversation_" + "f" * 32))

        ready = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="mall",
            repository_revision="b" * 40,
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref="qualified-route",
            known_limitations=("Access only",),
        )
        with self.assertRaises(DomainError) as failure:
            InMemoryEngineeringConversationService(ready)
        self.assertEqual(failure.exception.code, ErrorCode.CONTROL_STATE_DENIED)

    def test_same_conversation_rejects_parallel_turn_while_executor_is_running(self) -> None:
        started = Event()
        release = Event()

        class BlockingExecutor:
            def execute(self, request):
                started.set()
                if not release.wait(1):
                    raise RuntimeError("test executor was not released")
                work_state_digest = digest_of(
                    {"request": request.request_digest.value}
                )
                return EngineeringTurnExecutionOutcome.succeeded(
                    request_digest=request.request_digest,
                    assistant_kind=ConversationMessageKind.ANSWER,
                    assistant_content="已完成当前 Turn。",
                    included_user_message_ids=(request.user_message.message_id,),
                    accepted_correction_message_ids=(),
                    reviewed_conclusion_refs=("answer-ref",),
                    superseded_conclusion_refs=(),
                    reducer_status="EXECUTED_APPLICATION_SEALED",
                    work_state_ref="work-state-ref",
                    work_state_revision=Revision(1),
                    work_state_digest=work_state_digest,
                    evidence_package_ref="package-ref",
                    answer_ref="answer-ref",
                    review_ref="review-ref",
                    delivery_authorization_ref="delivery-ref",
                    provider_dispatch_count=2,
                    quality_status="ACCEPTED",
                )

        binding = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="mall",
            repository_revision="b" * 40,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=digest_of({"world_model": "exact"}),
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref="qualified-route",
            known_limitations=("Alpha only",),
        )
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=BlockingExecutor(),
            id_generator=SequentialIdGenerator(),
        )
        conversation = service.create_conversation()
        result: dict[str, object] = {}

        def submit() -> None:
            try:
                result["submission"] = service.submit_turn(
                    conversation_id=conversation.conversation.conversation_id,
                    expected_revision=Revision(1),
                    message="第一个 Turn",
                )
            except Exception as exc:  # pragma: no cover - assertion reports it
                result["error"] = exc

        thread = Thread(target=submit)
        thread.start()
        self.assertTrue(started.wait(1))
        with self.assertRaises(DomainError) as parallel:
            service.submit_turn(
                conversation_id=conversation.conversation.conversation_id,
                expected_revision=Revision(1),
                message="并行 Turn",
            )
        self.assertEqual(parallel.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        release.set()
        thread.join(1)

        self.assertFalse(thread.is_alive())
        self.assertNotIn("error", result)
        submission = result["submission"]
        self.assertEqual(submission.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(submission.snapshot.conversation.revision, Revision(2))

    def test_invalid_executor_outcome_fails_turn_and_preserves_reviewed_context(self) -> None:
        class DroppingExecutor:
            def __init__(self):
                self.calls = 0

            def execute(self, request):
                self.calls += 1
                before = request.snapshot_before.context
                work_state_digest = digest_of(
                    {
                        "request": request.request_digest.value,
                        "call": self.calls,
                    }
                )
                return EngineeringTurnExecutionOutcome.succeeded(
                    request_digest=request.request_digest,
                    assistant_kind=ConversationMessageKind.ANSWER,
                    assistant_content=f"候选答案 {self.calls}",
                    included_user_message_ids=(
                        *before.included_user_message_ids,
                        request.user_message.message_id,
                    ),
                    accepted_correction_message_ids=(
                        before.accepted_correction_message_ids
                    ),
                    reviewed_conclusion_refs=(f"answer-{self.calls}",),
                    superseded_conclusion_refs=before.superseded_conclusion_refs,
                    reducer_status="EXECUTED_APPLICATION_SEALED",
                    work_state_ref=before.work_state_ref or "work-state-ref",
                    work_state_revision=(
                        Revision(1)
                        if before.work_state_ref is None
                        else before.work_state_revision.next()
                    ),
                    work_state_digest=work_state_digest,
                    evidence_package_ref=f"package-{self.calls}",
                    answer_ref=f"answer-{self.calls}",
                    review_ref=f"review-{self.calls}",
                    delivery_authorization_ref=f"delivery-{self.calls}",
                    provider_dispatch_count=2,
                    quality_status="ACCEPTED",
                )

        binding = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="mall",
            repository_revision="b" * 40,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=digest_of({"world_model": "exact"}),
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref="qualified-route",
            known_limitations=("Alpha only",),
        )
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=DroppingExecutor(),
            id_generator=SequentialIdGenerator(),
        )
        conversation = service.create_conversation()
        first = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="第一个问题",
        )
        second = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(2),
            message="第二个问题",
        )

        self.assertEqual(first.turn.state, ConversationTurnState.SUCCEEDED)
        self.assertEqual(second.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            second.turn.failure_code,
            "TURN_EXECUTOR_PROTOCOL_VIOLATION",
        )
        self.assertEqual(second.turn.provider_dispatch_count, 2)
        self.assertEqual(
            second.snapshot.context.reviewed_conclusion_refs,
            first.snapshot.context.reviewed_conclusion_refs,
        )
        self.assertEqual(
            second.snapshot.context.work_state_digest,
            first.snapshot.context.work_state_digest,
        )
        self.assertEqual(second.snapshot.conversation.revision, Revision(3))

    def test_tampered_turn_citation_fails_closed_before_projection(self) -> None:
        class TamperedCitationExecutor:
            def execute(self, request):
                citation = EngineeringTurnCitation.create(
                    citation_ref="citation-ref",
                    evidence_class="SOURCE",
                    source_revision=request.binding.repository_revision,
                    locator="README.md:L1-L2",
                    modality="REPOSITORY_DOCUMENT",
                    content_digest=digest_of("source-content"),
                )
                citation = replace(citation, locator="README.md:L9")
                return EngineeringTurnExecutionOutcome.succeeded(
                    request_digest=request.request_digest,
                    assistant_kind=ConversationMessageKind.ANSWER,
                    assistant_content="候选答案。",
                    included_user_message_ids=(request.user_message.message_id,),
                    accepted_correction_message_ids=(),
                    reviewed_conclusion_refs=("answer-ref",),
                    superseded_conclusion_refs=(),
                    reducer_status="EXECUTED_APPLICATION_SEALED",
                    work_state_ref="work-state-ref",
                    work_state_revision=Revision(1),
                    work_state_digest=digest_of("work-state"),
                    evidence_package_ref="package-ref",
                    answer_ref="answer-ref",
                    review_ref="review-ref",
                    delivery_authorization_ref="delivery-ref",
                    provider_dispatch_count=2,
                    quality_status="ACCEPTED",
                    citations=(citation,),
                )

        binding = EngineeringChatBinding.create(
            product_revision="a" * 40,
            project_name="mall",
            repository_revision="b" * 40,
            world_model_status=RuntimeCapabilityStatus.READY,
            world_model_authority_digest=digest_of("world-model"),
            source_profile_ref="source-profile@1",
            source_access_status=RuntimeCapabilityStatus.READY,
            provider_status=RuntimeCapabilityStatus.READY,
            provider_route_ref="qualified-route@1",
            known_limitations=("Alpha only",),
        )
        service = InMemoryEngineeringConversationService(
            binding,
            turn_executor=TamperedCitationExecutor(),
            id_generator=SequentialIdGenerator(),
        )
        conversation = service.create_conversation()

        submission = service.submit_turn(
            conversation_id=conversation.conversation.conversation_id,
            expected_revision=Revision(1),
            message="解释当前行为",
        )

        self.assertEqual(submission.turn.state, ConversationTurnState.FAILED)
        self.assertEqual(
            submission.turn.failure_code,
            "TURN_EXECUTOR_PROTOCOL_VIOLATION",
        )
        self.assertEqual(submission.turn.citations, ())


if __name__ == "__main__":
    unittest.main()
