"""Application-owned state for the ITER-010 Engineering Chat access slice.

This module deliberately stops at the access boundary.  It owns immutable
Conversation, Context, Message, and Turn records, but it has no Provider,
Source, World Model, filesystem, or network dependency.  Until a qualified
turn executor is authorized, every submitted Turn is sealed as an honest
failure while its Conversation remains active.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
from threading import Lock
from typing import Callable, Sequence

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    Revision,
    StableId,
    Uuid4IdGenerator,
    digest_of,
)


ENGINEERING_CHAT_PROTOCOL = "CONVERSATIONAL_ENGINEERING_AGENT@1"
ENGINEERING_CHAT_EXPERIENCE = "ENGINEERING_CHAT_EXPERIENCE@1"
ENGINEERING_CHAT_ACCESS_VERSION = "ITER-010-CHAT-ACCESS@1"
ENGINEERING_CHAT_MAXIMUM_MESSAGE_CHARACTERS = 16_000
ENGINEERING_CHAT_MAXIMUM_MESSAGE_BYTES = 48_000

_GIT_REVISION = re.compile(r"^[0-9a-f]{40}$")


class RuntimeCapabilityStatus(str, Enum):
    NOT_CONFIGURED = "NOT_CONFIGURED"
    NOT_QUALIFIED = "NOT_QUALIFIED"
    READY = "READY"


class ConversationLifecycleState(str, Enum):
    ACTIVE = "ACTIVE"


class ConversationMessageRole(str, Enum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"


class ConversationMessageKind(str, Enum):
    USER_INPUT = "USER_INPUT"
    LIMITATION = "LIMITATION"


class ConversationTurnState(str, Enum):
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class EngineeringChatBinding:
    product_version: str
    product_revision: str
    project_name: str
    repository_revision: str
    world_model_status: RuntimeCapabilityStatus
    world_model_authority_digest: Digest | None
    source_profile_ref: str | None
    source_access_status: RuntimeCapabilityStatus
    provider_status: RuntimeCapabilityStatus
    provider_route_ref: str | None
    excluded_source_paths: tuple[str, ...]
    known_limitations: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        product_revision: str,
        project_name: str,
        repository_revision: str,
        world_model_status: RuntimeCapabilityStatus = RuntimeCapabilityStatus.NOT_CONFIGURED,
        world_model_authority_digest: Digest | None = None,
        source_profile_ref: str | None = None,
        source_access_status: RuntimeCapabilityStatus = RuntimeCapabilityStatus.NOT_CONFIGURED,
        provider_status: RuntimeCapabilityStatus = RuntimeCapabilityStatus.NOT_CONFIGURED,
        provider_route_ref: str | None = None,
        excluded_source_paths: Sequence[str] = ("src/main/resources",),
        known_limitations: Sequence[str],
        product_version: str = ENGINEERING_CHAT_ACCESS_VERSION,
    ) -> "EngineeringChatBinding":
        product_version = _text(product_version, "product version")
        project_name = _text(project_name, "project name")
        product_revision = _git_revision(product_revision, "product revision")
        repository_revision = _git_revision(
            repository_revision, "repository revision"
        )
        source_profile_ref = _optional_text(source_profile_ref, "Source Profile")
        provider_route_ref = _optional_text(provider_route_ref, "Provider route")
        exclusions = _unique_texts(excluded_source_paths, "excluded source path")
        limitations = _unique_texts(known_limitations, "known limitation")
        if "src/main/resources" not in exclusions:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Engineering Chat access must keep src/main/resources excluded",
            )
        if not limitations:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Engineering Chat access requires explicit known limitations",
            )
        if (
            world_model_status is RuntimeCapabilityStatus.READY
            and world_model_authority_digest is None
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "ready World Model status requires an exact authority digest",
            )
        if (
            source_access_status is RuntimeCapabilityStatus.READY
            and source_profile_ref is None
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "ready Source access requires an exact Source Profile",
            )
        if (
            provider_status is RuntimeCapabilityStatus.READY
            and provider_route_ref is None
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "ready Provider status requires an exact Provider route",
            )
        core = {
            "schema": "ENGINEERING_CHAT_BINDING@1",
            "product_version": product_version,
            "product_revision": product_revision,
            "project_name": project_name,
            "repository_revision": repository_revision,
            "world_model_status": world_model_status.value,
            "world_model_authority_digest": (
                world_model_authority_digest.value
                if world_model_authority_digest is not None
                else None
            ),
            "source_profile_ref": source_profile_ref,
            "source_access_status": source_access_status.value,
            "provider_status": provider_status.value,
            "provider_route_ref": provider_route_ref,
            "excluded_source_paths": exclusions,
            "known_limitations": limitations,
        }
        return cls(
            product_version=product_version,
            product_revision=product_revision,
            project_name=project_name,
            repository_revision=repository_revision,
            world_model_status=world_model_status,
            world_model_authority_digest=world_model_authority_digest,
            source_profile_ref=source_profile_ref,
            source_access_status=source_access_status,
            provider_status=provider_status,
            provider_route_ref=provider_route_ref,
            excluded_source_paths=exclusions,
            known_limitations=limitations,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class ConversationContext:
    conversation_id: StableId
    work_state_revision: Revision
    included_user_message_ids: tuple[StableId, ...]
    accepted_correction_message_ids: tuple[StableId, ...]
    reviewed_conclusion_refs: tuple[str, ...]
    reducer_status: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        conversation_id: StableId,
        work_state_revision: Revision,
        included_user_message_ids: Sequence[StableId],
    ) -> "ConversationContext":
        included = tuple(included_user_message_ids)
        if len(included) != len(set(included)):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Conversation Context user message references must be unique",
            )
        core = {
            "schema": "ENGINEERING_CONVERSATION_CONTEXT@1",
            "conversation_id": conversation_id.value,
            "work_state_revision": work_state_revision.value,
            "included_user_message_ids": tuple(item.value for item in included),
            "accepted_correction_message_ids": (),
            "reviewed_conclusion_refs": (),
            "reducer_status": "NOT_EXECUTED_ACCESS_ONLY",
        }
        return cls(
            conversation_id=conversation_id,
            work_state_revision=work_state_revision,
            included_user_message_ids=included,
            accepted_correction_message_ids=(),
            reviewed_conclusion_refs=(),
            reducer_status=core["reducer_status"],
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringConversationMessage:
    message_id: StableId
    conversation_id: StableId
    turn_id: StableId
    sequence: int
    role: ConversationMessageRole
    kind: ConversationMessageKind
    content: str
    created_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class EngineeringConversationTurn:
    turn_id: StableId
    result_id: StableId
    conversation_id: StableId
    sequence: int
    conversation_revision_before: Revision
    conversation_revision_after: Revision
    context_digest_before: Digest
    context_digest_after: Digest
    request_digest: Digest
    user_message_id: StableId
    assistant_message_id: StableId
    state: ConversationTurnState
    failure_code: str
    failure_message: str
    evidence_package_ref: str | None
    answer_ref: str | None
    review_ref: str | None
    delivery_state: str
    provider_dispatch_count: int
    retry_count: int
    quality_status: str
    production_activation: str
    created_at: datetime
    completed_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class EngineeringConversation:
    conversation_id: StableId
    revision: Revision
    binding_digest: Digest
    state: ConversationLifecycleState
    context_digest: Digest
    turn_ids: tuple[StableId, ...]
    message_ids: tuple[StableId, ...]
    created_at: datetime
    revised_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class EngineeringConversationSnapshot:
    conversation: EngineeringConversation
    context: ConversationContext
    messages: tuple[EngineeringConversationMessage, ...]
    turns: tuple[EngineeringConversationTurn, ...]


@dataclass(frozen=True, slots=True)
class EngineeringTurnSubmission:
    snapshot: EngineeringConversationSnapshot
    turn: EngineeringConversationTurn


class ConversationNotFoundError(LookupError):
    def __init__(self, conversation_id: StableId) -> None:
        super().__init__(f"Conversation {conversation_id.value} was not found")
        self.conversation_id = conversation_id


class InMemoryEngineeringConversationService:
    """Ephemeral Application authority for the pre-Provider access checkpoint."""

    def __init__(
        self,
        binding: EngineeringChatBinding,
        *,
        id_generator: IdGenerator | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if binding.provider_status is RuntimeCapabilityStatus.READY:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "the access-only Conversation service cannot dispatch a Provider",
            )
        self.binding = binding
        self._id_generator = id_generator or Uuid4IdGenerator()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._lock = Lock()
        self._history: dict[
            StableId, tuple[EngineeringConversationSnapshot, ...]
        ] = {}
        self._issued_ids: set[StableId] = set()
        self._turn_count = 0

    def create_conversation(self) -> EngineeringConversationSnapshot:
        with self._lock:
            conversation_id = self._new_id("conversation")
            now = self._now()
            context = ConversationContext.create(
                conversation_id=conversation_id,
                work_state_revision=Revision(1),
                included_user_message_ids=(),
            )
            conversation = _conversation(
                conversation_id=conversation_id,
                revision=Revision(1),
                binding_digest=self.binding.digest,
                context_digest=context.digest,
                turn_ids=(),
                message_ids=(),
                created_at=now,
                revised_at=now,
            )
            snapshot = EngineeringConversationSnapshot(
                conversation=conversation,
                context=context,
                messages=(),
                turns=(),
            )
            self._history[conversation_id] = (snapshot,)
            return snapshot

    def get_conversation(
        self, conversation_id: StableId
    ) -> EngineeringConversationSnapshot:
        with self._lock:
            return self._current(conversation_id)

    def submit_turn(
        self,
        *,
        conversation_id: StableId,
        expected_revision: Revision,
        message: str,
    ) -> EngineeringTurnSubmission:
        message = _chat_message(message)
        with self._lock:
            current = self._current(conversation_id)
            if current.conversation.revision != expected_revision:
                raise DomainError(
                    ErrorCode.REVISION_CONFLICT,
                    "Conversation revision is stale",
                    {
                        "expected_revision": expected_revision.value,
                        "actual_revision": current.conversation.revision.value,
                    },
                )
            now = self._now()
            turn_id = self._new_id("turn")
            result_id = self._new_id("turn_result")
            user_message_id = self._new_id("message")
            assistant_message_id = self._new_id("message")
            turn_sequence = len(current.turns) + 1
            user_message = _message(
                message_id=user_message_id,
                conversation_id=conversation_id,
                turn_id=turn_id,
                sequence=len(current.messages) + 1,
                role=ConversationMessageRole.USER,
                kind=ConversationMessageKind.USER_INPUT,
                content=message,
                created_at=now,
            )
            failure_code = (
                "PROVIDER_NOT_QUALIFIED"
                if self.binding.provider_status
                is RuntimeCapabilityStatus.NOT_QUALIFIED
                else "PROVIDER_NOT_CONFIGURED"
            )
            failure_message = (
                "当前 Chat Access 尚未配置或取得 Provider 资格；本 Turn 已失败关闭，"
                "没有生成或授权工程答案。Conversation 仍可继续使用。"
            )
            assistant_message = _message(
                message_id=assistant_message_id,
                conversation_id=conversation_id,
                turn_id=turn_id,
                sequence=len(current.messages) + 2,
                role=ConversationMessageRole.ASSISTANT,
                kind=ConversationMessageKind.LIMITATION,
                content=failure_message,
                created_at=now,
            )
            context = ConversationContext.create(
                conversation_id=conversation_id,
                work_state_revision=current.context.work_state_revision.next(),
                included_user_message_ids=(
                    *current.context.included_user_message_ids,
                    user_message_id,
                ),
            )
            next_revision = current.conversation.revision.next()
            request_digest = digest_of(
                {
                    "schema": "ENGINEERING_CONVERSATION_TURN_REQUEST@1",
                    "conversation_id": conversation_id.value,
                    "conversation_revision": expected_revision.value,
                    "turn_id": turn_id.value,
                    "user_message_digest": user_message.digest.value,
                    "context_digest": current.context.digest.value,
                    "binding_digest": self.binding.digest.value,
                }
            )
            turn = _failed_turn(
                turn_id=turn_id,
                result_id=result_id,
                conversation_id=conversation_id,
                sequence=turn_sequence,
                conversation_revision_before=expected_revision,
                conversation_revision_after=next_revision,
                context_digest_before=current.context.digest,
                context_digest_after=context.digest,
                request_digest=request_digest,
                user_message_id=user_message_id,
                assistant_message_id=assistant_message_id,
                failure_code=failure_code,
                failure_message=failure_message,
                at=now,
            )
            messages = (*current.messages, user_message, assistant_message)
            turns = (*current.turns, turn)
            conversation = _conversation(
                conversation_id=conversation_id,
                revision=next_revision,
                binding_digest=self.binding.digest,
                context_digest=context.digest,
                turn_ids=tuple(item.turn_id for item in turns),
                message_ids=tuple(item.message_id for item in messages),
                created_at=current.conversation.created_at,
                revised_at=now,
            )
            snapshot = EngineeringConversationSnapshot(
                conversation=conversation,
                context=context,
                messages=messages,
                turns=turns,
            )
            self._history[conversation_id] = (
                *self._history[conversation_id],
                snapshot,
            )
            self._turn_count += 1
            return EngineeringTurnSubmission(snapshot=snapshot, turn=turn)

    def statistics(self) -> tuple[int, int]:
        with self._lock:
            return len(self._history), self._turn_count

    def revision_history(
        self, conversation_id: StableId
    ) -> tuple[EngineeringConversationSnapshot, ...]:
        with self._lock:
            history = self._history.get(conversation_id)
            if history is None:
                raise ConversationNotFoundError(conversation_id)
            return history

    def _current(self, conversation_id: StableId) -> EngineeringConversationSnapshot:
        history = self._history.get(conversation_id)
        if history is None:
            raise ConversationNotFoundError(conversation_id)
        return history[-1]

    def _new_id(self, kind: str) -> StableId:
        value = self._id_generator.new(kind)
        if value in self._issued_ids:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "ID generator returned a duplicate stable ID",
            )
        self._issued_ids.add(value)
        return value

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Conversation clock must return an aware datetime",
            )
        return value.astimezone(timezone.utc)


def _message(
    *,
    message_id: StableId,
    conversation_id: StableId,
    turn_id: StableId,
    sequence: int,
    role: ConversationMessageRole,
    kind: ConversationMessageKind,
    content: str,
    created_at: datetime,
) -> EngineeringConversationMessage:
    core = {
        "schema": "ENGINEERING_CONVERSATION_MESSAGE@1",
        "message_id": message_id.value,
        "conversation_id": conversation_id.value,
        "turn_id": turn_id.value,
        "sequence": sequence,
        "role": role.value,
        "kind": kind.value,
        "content": content,
        "created_at": created_at,
    }
    return EngineeringConversationMessage(
        message_id=message_id,
        conversation_id=conversation_id,
        turn_id=turn_id,
        sequence=sequence,
        role=role,
        kind=kind,
        content=content,
        created_at=created_at,
        digest=digest_of(core),
    )


def _failed_turn(
    *,
    turn_id: StableId,
    result_id: StableId,
    conversation_id: StableId,
    sequence: int,
    conversation_revision_before: Revision,
    conversation_revision_after: Revision,
    context_digest_before: Digest,
    context_digest_after: Digest,
    request_digest: Digest,
    user_message_id: StableId,
    assistant_message_id: StableId,
    failure_code: str,
    failure_message: str,
    at: datetime,
) -> EngineeringConversationTurn:
    core = {
        "schema": "ENGINEERING_CONVERSATION_TURN_RESULT@1",
        "turn_id": turn_id.value,
        "result_id": result_id.value,
        "conversation_id": conversation_id.value,
        "sequence": sequence,
        "conversation_revision_before": conversation_revision_before.value,
        "conversation_revision_after": conversation_revision_after.value,
        "context_digest_before": context_digest_before.value,
        "context_digest_after": context_digest_after.value,
        "request_digest": request_digest.value,
        "user_message_id": user_message_id.value,
        "assistant_message_id": assistant_message_id.value,
        "state": ConversationTurnState.FAILED.value,
        "failure_code": failure_code,
        "failure_message": failure_message,
        "evidence_package_ref": None,
        "answer_ref": None,
        "review_ref": None,
        "delivery_state": "NOT_AUTHORIZED",
        "provider_dispatch_count": 0,
        "retry_count": 0,
        "quality_status": "NOT_ACCEPTED",
        "production_activation": "NOT_EXECUTED",
        "created_at": at,
        "completed_at": at,
    }
    return EngineeringConversationTurn(
        turn_id=turn_id,
        result_id=result_id,
        conversation_id=conversation_id,
        sequence=sequence,
        conversation_revision_before=conversation_revision_before,
        conversation_revision_after=conversation_revision_after,
        context_digest_before=context_digest_before,
        context_digest_after=context_digest_after,
        request_digest=request_digest,
        user_message_id=user_message_id,
        assistant_message_id=assistant_message_id,
        state=ConversationTurnState.FAILED,
        failure_code=failure_code,
        failure_message=failure_message,
        evidence_package_ref=None,
        answer_ref=None,
        review_ref=None,
        delivery_state="NOT_AUTHORIZED",
        provider_dispatch_count=0,
        retry_count=0,
        quality_status="NOT_ACCEPTED",
        production_activation="NOT_EXECUTED",
        created_at=at,
        completed_at=at,
        digest=digest_of(core),
    )


def _conversation(
    *,
    conversation_id: StableId,
    revision: Revision,
    binding_digest: Digest,
    context_digest: Digest,
    turn_ids: tuple[StableId, ...],
    message_ids: tuple[StableId, ...],
    created_at: datetime,
    revised_at: datetime,
) -> EngineeringConversation:
    core = {
        "schema": "ENGINEERING_CONVERSATION@1",
        "conversation_id": conversation_id.value,
        "revision": revision.value,
        "binding_digest": binding_digest.value,
        "state": ConversationLifecycleState.ACTIVE.value,
        "context_digest": context_digest.value,
        "turn_ids": tuple(item.value for item in turn_ids),
        "message_ids": tuple(item.value for item in message_ids),
        "created_at": created_at,
        "revised_at": revised_at,
    }
    return EngineeringConversation(
        conversation_id=conversation_id,
        revision=revision,
        binding_digest=binding_digest,
        state=ConversationLifecycleState.ACTIVE,
        context_digest=context_digest,
        turn_ids=turn_ids,
        message_ids=message_ids,
        created_at=created_at,
        revised_at=revised_at,
        digest=digest_of(core),
    )


def _chat_message(value: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "chat message must be non-empty without surrounding whitespace",
        )
    if (
        len(value) > ENGINEERING_CHAT_MAXIMUM_MESSAGE_CHARACTERS
        or len(value.encode("utf-8")) > ENGINEERING_CHAT_MAXIMUM_MESSAGE_BYTES
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "chat message exceeds the local Access input limit",
        )
    return value


def _git_revision(value: str, label: str) -> str:
    value = _text(value, label)
    if not _GIT_REVISION.fullmatch(value):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be an exact 40-character lowercase Git commit",
        )
    return value


def _optional_text(value: str | None, label: str) -> str | None:
    return None if value is None else _text(value, label)


def _unique_texts(values: Sequence[str], label: str) -> tuple[str, ...]:
    normalized = tuple(_text(item, label) for item in values)
    if len(normalized) != len(set(normalized)):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label}s must be unique",
        )
    return normalized


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be non-empty without surrounding whitespace",
        )
    if len(value.encode("utf-8")) > 512:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} exceeds its UTF-8 boundary",
        )
    return value


__all__ = [
    "ConversationContext",
    "ConversationLifecycleState",
    "ConversationMessageKind",
    "ConversationMessageRole",
    "ConversationNotFoundError",
    "ConversationTurnState",
    "ENGINEERING_CHAT_ACCESS_VERSION",
    "ENGINEERING_CHAT_EXPERIENCE",
    "ENGINEERING_CHAT_MAXIMUM_MESSAGE_BYTES",
    "ENGINEERING_CHAT_MAXIMUM_MESSAGE_CHARACTERS",
    "ENGINEERING_CHAT_PROTOCOL",
    "EngineeringChatBinding",
    "EngineeringConversation",
    "EngineeringConversationMessage",
    "EngineeringConversationSnapshot",
    "EngineeringConversationTurn",
    "EngineeringTurnSubmission",
    "InMemoryEngineeringConversationService",
    "RuntimeCapabilityStatus",
]
