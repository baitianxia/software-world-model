from __future__ import annotations

from datetime import datetime, timezone
import unittest

from software_world_model.application_services.engineering_conversation import (
    ConversationLifecycleState,
    ConversationMessageKind,
    ConversationNotFoundError,
    ConversationTurnState,
    EngineeringChatBinding,
    InMemoryEngineeringConversationService,
    RuntimeCapabilityStatus,
)
from software_world_model.cross_cutting import DomainError, ErrorCode, Revision, StableId


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
        self.assertEqual(turn.failure_code, "PROVIDER_NOT_CONFIGURED")
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


if __name__ == "__main__":
    unittest.main()
