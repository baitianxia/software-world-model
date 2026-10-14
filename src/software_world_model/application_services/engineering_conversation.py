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
from typing import Callable, Protocol, Sequence

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
ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN = (
    "EMPTY_CONTEXT_REFERENT_CLARIFICATION_ZH_CN@1"
)
ENGINEERING_CHAT_APPLICATION_CLARIFICATION_QUALITY = (
    "APPLICATION_INPUT_CLARIFICATION"
)

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
    ANSWER = "ANSWER"
    CLARIFICATION = "CLARIFICATION"
    LIMITATION = "LIMITATION"


class ConversationTurnState(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class EngineeringProviderFailureClassification(str, Enum):
    """Closed raw execution/application evidence; never fallback authority."""

    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_HTTP_ERROR = "PROVIDER_HTTP_ERROR"
    PROVIDER_OUTCOME_UNKNOWN = "PROVIDER_OUTCOME_UNKNOWN"
    PROVIDER_OUTPUT_INVALID = "PROVIDER_OUTPUT_INVALID"
    MODEL_REVIEW_REJECTED = "MODEL_REVIEW_REJECTED"


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
    execution_status: RuntimeCapabilityStatus
    execution_policy_ref: str | None
    conversation_input_policy_ref: str | None
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
        execution_status: RuntimeCapabilityStatus | None = None,
        execution_policy_ref: str | None = None,
        conversation_input_policy_ref: str | None = None,
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
        execution_status = (
            provider_status if execution_status is None else execution_status
        )
        execution_policy_ref = _optional_text(
            execution_policy_ref
            if execution_policy_ref is not None
            else provider_route_ref,
            "Model Execution policy",
        )
        conversation_input_policy_ref = _optional_text(
            conversation_input_policy_ref, "Conversation input policy"
        )
        if conversation_input_policy_ref is not None:
            _conversation_input_policy(conversation_input_policy_ref)
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
        if (
            execution_status is RuntimeCapabilityStatus.READY
            and execution_policy_ref is None
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "ready execution status requires an opaque execution policy reference",
            )
        core = {
            "schema": "ENGINEERING_CHAT_BINDING@2",
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
            "execution_status": execution_status.value,
            "execution_policy_ref": execution_policy_ref,
            "conversation_input_policy_ref": conversation_input_policy_ref,
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
            execution_status=execution_status,
            execution_policy_ref=execution_policy_ref,
            conversation_input_policy_ref=conversation_input_policy_ref,
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
    superseded_conclusion_refs: tuple[str, ...]
    work_state_ref: str | None
    work_state_digest: Digest | None
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
        return cls.seal(
            conversation_id=conversation_id,
            work_state_revision=work_state_revision,
            included_user_message_ids=included_user_message_ids,
            reducer_status="NOT_EXECUTED_ACCESS_ONLY",
        )

    @classmethod
    def seal(
        cls,
        *,
        conversation_id: StableId,
        work_state_revision: Revision,
        included_user_message_ids: Sequence[StableId],
        accepted_correction_message_ids: Sequence[StableId] = (),
        reviewed_conclusion_refs: Sequence[str] = (),
        superseded_conclusion_refs: Sequence[str] = (),
        work_state_ref: str | None = None,
        work_state_digest: Digest | None = None,
        reducer_status: str,
    ) -> "ConversationContext":
        included = tuple(included_user_message_ids)
        if len(included) != len(set(included)):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Conversation Context user message references must be unique",
            )
        corrections = tuple(accepted_correction_message_ids)
        if len(corrections) != len(set(corrections)) or not set(corrections).issubset(
            included
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "accepted corrections must be unique included user messages",
            )
        reviewed = _unique_texts(
            reviewed_conclusion_refs, "reviewed conclusion reference"
        )
        superseded = _unique_texts(
            superseded_conclusion_refs, "superseded conclusion reference"
        )
        if not set(superseded).issubset(reviewed):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "superseded conclusions must remain in reviewed conclusions",
            )
        work_state_ref = _optional_text(work_state_ref, "Agent Work State reference")
        if (work_state_ref is None) != (work_state_digest is None):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent Work State reference and digest must be present together",
            )
        reducer_status = _text(reducer_status, "Context reducer status")
        core = {
            "schema": "ENGINEERING_CONVERSATION_CONTEXT@1",
            "conversation_id": conversation_id.value,
            "work_state_revision": work_state_revision.value,
            "included_user_message_ids": tuple(item.value for item in included),
            "accepted_correction_message_ids": tuple(
                item.value for item in corrections
            ),
            "reviewed_conclusion_refs": reviewed,
            "superseded_conclusion_refs": superseded,
            "work_state_ref": work_state_ref,
            "work_state_digest": (
                work_state_digest.value if work_state_digest is not None else None
            ),
            "reducer_status": reducer_status,
        }
        return cls(
            conversation_id=conversation_id,
            work_state_revision=work_state_revision,
            included_user_message_ids=included,
            accepted_correction_message_ids=corrections,
            reviewed_conclusion_refs=reviewed,
            superseded_conclusion_refs=superseded,
            work_state_ref=work_state_ref,
            work_state_digest=work_state_digest,
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
class EngineeringTurnCitation:
    """Application projection of an exact Citation used by the delivered Draft."""

    citation_ref: str
    evidence_class: str
    source_revision: str
    locator: str
    modality: str
    content_digest: Digest
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        citation_ref: str,
        evidence_class: str,
        source_revision: str,
        locator: str,
        modality: str,
        content_digest: Digest,
    ) -> "EngineeringTurnCitation":
        if not isinstance(content_digest, Digest):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Citation content digest is invalid",
            )
        core = {
            # Preserve the authority-owned Citation identity while avoiding an
            # Application -> Agent module dependency cycle.
            "schema": "ENGINEERING_AGENT_CITATION@1",
            "citation_ref": _text(citation_ref, "Citation reference"),
            "evidence_class": _text(
                evidence_class, "Citation evidence class"
            ),
            "source_revision": _git_revision(
                source_revision, "Citation source revision"
            ),
            "locator": _bounded_text(
                locator, "Citation locator", maximum_bytes=4_096
            ),
            "modality": _text(modality, "Citation modality"),
            "content_digest": content_digest.value,
        }
        return cls(
            citation_ref=core["citation_ref"],
            evidence_class=core["evidence_class"],
            source_revision=core["source_revision"],
            locator=core["locator"],
            modality=core["modality"],
            content_digest=content_digest,
            digest=digest_of(core),
        )


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
    failure_code: str | None
    failure_message: str | None
    evidence_package_ref: str | None
    answer_ref: str | None
    review_ref: str | None
    delivery_authorization_ref: str | None
    citations: tuple[EngineeringTurnCitation, ...]
    work_state_ref: str | None
    work_state_revision: Revision | None
    work_state_digest: Digest | None
    delivery_state: str
    provider_dispatch_count: int
    model_dispatch_receipt_refs: tuple[str, ...]
    provider_failure_classification: EngineeringProviderFailureClassification | None
    provider_failure_code: str | None
    provider_http_status: int | None
    provider_http_failure_evidence_digest: Digest | None
    provider_route_receipt_ref: str | None
    provider_availability_verdict_ref: str | None
    provider_attempt_receipt_refs: tuple[str, ...]
    fallback_provider_attempt_count: int
    provider_duplicate_cost_risk: bool
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


class EngineeringConversationInputPolicy(Protocol):
    """Versioned, binding-owned guard for non-semantic input clarification."""

    policy_ref: str

    def clarification_for(
        self,
        *,
        snapshot: EngineeringConversationSnapshot,
        message: str,
    ) -> str | None: ...


@dataclass(frozen=True, slots=True)
class _EmptyContextZhCnReferentPolicy:
    policy_ref: str = ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN

    _ANAPHORIC_MARKERS = (
        "它",
        "它们",
        "这些",
        "那些",
        "这类",
        "那类",
        "此类",
        "前者",
        "后者",
        "上述",
        "前述",
        "前面那个",
        "上面那个",
    )

    def clarification_for(
        self,
        *,
        snapshot: EngineeringConversationSnapshot,
        message: str,
    ) -> str | None:
        context = snapshot.context
        if (
            snapshot.messages
            or snapshot.turns
            or context.included_user_message_ids
            or context.work_state_ref is not None
            or context.reviewed_conclusion_refs
        ):
            return None
        compact = re.sub(r"\s+", "", message)
        if not any(marker in compact for marker in self._ANAPHORIC_MARKERS):
            return None
        return (
            "当前新对话没有可解析的先行对象。请明确你指的是哪个组件、"
            "流程或请求，我再继续调查。"
        )


def _conversation_input_policy(
    policy_ref: str | None,
) -> EngineeringConversationInputPolicy | None:
    if policy_ref is None:
        return None
    if policy_ref == ENGINEERING_CHAT_EMPTY_CONTEXT_REFERENT_POLICY_ZH_CN:
        return _EmptyContextZhCnReferentPolicy()
    raise DomainError(
        ErrorCode.INVALID_ARGUMENT,
        "Engineering Chat Conversation input policy is not registered",
    )


@dataclass(frozen=True, slots=True)
class EngineeringTurnSubmission:
    snapshot: EngineeringConversationSnapshot
    turn: EngineeringConversationTurn


@dataclass(frozen=True, slots=True)
class EngineeringTurnExecutionRequest:
    binding: EngineeringChatBinding
    snapshot_before: EngineeringConversationSnapshot
    turn_id: StableId
    result_id: StableId
    sequence: int
    user_message: EngineeringConversationMessage
    request_digest: Digest
    requested_at: datetime


@dataclass(frozen=True, slots=True)
class EngineeringTurnExecutionOutcome:
    request_digest: Digest
    state: ConversationTurnState
    assistant_kind: ConversationMessageKind
    assistant_content: str
    included_user_message_ids: tuple[StableId, ...]
    accepted_correction_message_ids: tuple[StableId, ...]
    reviewed_conclusion_refs: tuple[str, ...]
    superseded_conclusion_refs: tuple[str, ...]
    reducer_status: str
    work_state_ref: str | None
    work_state_revision: Revision | None
    work_state_digest: Digest | None
    failure_code: str | None
    failure_message: str | None
    evidence_package_ref: str | None
    answer_ref: str | None
    review_ref: str | None
    delivery_authorization_ref: str | None
    citations: tuple[EngineeringTurnCitation, ...]
    provider_dispatch_count: int
    model_dispatch_receipt_refs: tuple[str, ...]
    provider_failure_classification: EngineeringProviderFailureClassification | None
    provider_failure_code: str | None
    provider_http_status: int | None
    provider_http_failure_evidence_digest: Digest | None
    provider_route_receipt_ref: str | None
    provider_availability_verdict_ref: str | None
    provider_attempt_receipt_refs: tuple[str, ...]
    fallback_provider_attempt_count: int
    provider_duplicate_cost_risk: bool
    retry_count: int
    quality_status: str

    @classmethod
    def succeeded(
        cls,
        *,
        request_digest: Digest,
        assistant_kind: ConversationMessageKind,
        assistant_content: str,
        included_user_message_ids: Sequence[StableId],
        accepted_correction_message_ids: Sequence[StableId],
        reviewed_conclusion_refs: Sequence[str],
        superseded_conclusion_refs: Sequence[str],
        reducer_status: str,
        work_state_ref: str,
        work_state_revision: Revision,
        work_state_digest: Digest,
        evidence_package_ref: str,
        answer_ref: str,
        review_ref: str,
        delivery_authorization_ref: str,
        provider_dispatch_count: int,
        quality_status: str,
        model_dispatch_receipt_refs: Sequence[str] = (),
        provider_route_receipt_ref: str | None = None,
        provider_availability_verdict_ref: str | None = None,
        provider_attempt_receipt_refs: Sequence[str] = (),
        fallback_provider_attempt_count: int = 0,
        provider_duplicate_cost_risk: bool = False,
        citations: Sequence[EngineeringTurnCitation] = (),
    ) -> "EngineeringTurnExecutionOutcome":
        return cls(
            request_digest=request_digest,
            state=ConversationTurnState.SUCCEEDED,
            assistant_kind=assistant_kind,
            assistant_content=assistant_content,
            included_user_message_ids=tuple(included_user_message_ids),
            accepted_correction_message_ids=tuple(
                accepted_correction_message_ids
            ),
            reviewed_conclusion_refs=tuple(reviewed_conclusion_refs),
            superseded_conclusion_refs=tuple(superseded_conclusion_refs),
            reducer_status=reducer_status,
            work_state_ref=work_state_ref,
            work_state_revision=work_state_revision,
            work_state_digest=work_state_digest,
            failure_code=None,
            failure_message=None,
            evidence_package_ref=evidence_package_ref,
            answer_ref=answer_ref,
            review_ref=review_ref,
            delivery_authorization_ref=delivery_authorization_ref,
            citations=tuple(citations),
            provider_dispatch_count=provider_dispatch_count,
            model_dispatch_receipt_refs=tuple(model_dispatch_receipt_refs),
            provider_failure_classification=None,
            provider_failure_code=None,
            provider_http_status=None,
            provider_http_failure_evidence_digest=None,
            provider_route_receipt_ref=provider_route_receipt_ref,
            provider_availability_verdict_ref=(
                provider_availability_verdict_ref
            ),
            provider_attempt_receipt_refs=tuple(provider_attempt_receipt_refs),
            fallback_provider_attempt_count=fallback_provider_attempt_count,
            provider_duplicate_cost_risk=provider_duplicate_cost_risk,
            retry_count=0,
            quality_status=quality_status,
        )

    @classmethod
    def failed(
        cls,
        *,
        request_digest: Digest,
        assistant_content: str,
        included_user_message_ids: Sequence[StableId],
        accepted_correction_message_ids: Sequence[StableId] = (),
        reviewed_conclusion_refs: Sequence[str] = (),
        superseded_conclusion_refs: Sequence[str] = (),
        reducer_status: str = "EXECUTION_FAILED",
        work_state_ref: str | None = None,
        work_state_revision: Revision | None = None,
        work_state_digest: Digest | None = None,
        failure_code: str,
        failure_message: str,
        evidence_package_ref: str | None = None,
        answer_ref: str | None = None,
        review_ref: str | None = None,
        provider_dispatch_count: int = 0,
        model_dispatch_receipt_refs: Sequence[str] = (),
        provider_failure_classification: EngineeringProviderFailureClassification | None = None,
        provider_failure_code: str | None = None,
        provider_http_status: int | None = None,
        provider_http_failure_evidence_digest: Digest | None = None,
        provider_route_receipt_ref: str | None = None,
        provider_availability_verdict_ref: str | None = None,
        provider_attempt_receipt_refs: Sequence[str] = (),
        fallback_provider_attempt_count: int = 0,
        provider_duplicate_cost_risk: bool = False,
    ) -> "EngineeringTurnExecutionOutcome":
        return cls(
            request_digest=request_digest,
            state=ConversationTurnState.FAILED,
            assistant_kind=ConversationMessageKind.LIMITATION,
            assistant_content=assistant_content,
            included_user_message_ids=tuple(included_user_message_ids),
            accepted_correction_message_ids=tuple(
                accepted_correction_message_ids
            ),
            reviewed_conclusion_refs=tuple(reviewed_conclusion_refs),
            superseded_conclusion_refs=tuple(superseded_conclusion_refs),
            reducer_status=reducer_status,
            work_state_ref=work_state_ref,
            work_state_revision=work_state_revision,
            work_state_digest=work_state_digest,
            failure_code=failure_code,
            failure_message=failure_message,
            evidence_package_ref=evidence_package_ref,
            answer_ref=answer_ref,
            review_ref=review_ref,
            delivery_authorization_ref=None,
            citations=(),
            provider_dispatch_count=provider_dispatch_count,
            model_dispatch_receipt_refs=tuple(model_dispatch_receipt_refs),
            provider_failure_classification=provider_failure_classification,
            provider_failure_code=provider_failure_code,
            provider_http_status=provider_http_status,
            provider_http_failure_evidence_digest=(
                provider_http_failure_evidence_digest
            ),
            provider_route_receipt_ref=provider_route_receipt_ref,
            provider_availability_verdict_ref=(
                provider_availability_verdict_ref
            ),
            provider_attempt_receipt_refs=tuple(provider_attempt_receipt_refs),
            fallback_provider_attempt_count=fallback_provider_attempt_count,
            provider_duplicate_cost_risk=provider_duplicate_cost_risk,
            retry_count=0,
            quality_status="NOT_ACCEPTED",
        )

    @classmethod
    def application_clarification(
        cls,
        *,
        request_digest: Digest,
        assistant_content: str,
        included_user_message_ids: Sequence[StableId],
        accepted_correction_message_ids: Sequence[StableId],
        reviewed_conclusion_refs: Sequence[str],
        superseded_conclusion_refs: Sequence[str],
    ) -> "EngineeringTurnExecutionOutcome":
        """Seal a deterministic input clarification before evidence/model dispatch."""

        return cls(
            request_digest=request_digest,
            state=ConversationTurnState.SUCCEEDED,
            assistant_kind=ConversationMessageKind.CLARIFICATION,
            assistant_content=assistant_content,
            included_user_message_ids=tuple(included_user_message_ids),
            accepted_correction_message_ids=tuple(
                accepted_correction_message_ids
            ),
            reviewed_conclusion_refs=tuple(reviewed_conclusion_refs),
            superseded_conclusion_refs=tuple(superseded_conclusion_refs),
            reducer_status="PRE_DISPATCH_CLARIFICATION_REQUIRED",
            work_state_ref=None,
            work_state_revision=None,
            work_state_digest=None,
            failure_code=None,
            failure_message=None,
            evidence_package_ref=None,
            answer_ref=None,
            review_ref=None,
            delivery_authorization_ref=None,
            citations=(),
            provider_dispatch_count=0,
            model_dispatch_receipt_refs=(),
            provider_failure_classification=None,
            provider_failure_code=None,
            provider_http_status=None,
            provider_http_failure_evidence_digest=None,
            provider_route_receipt_ref=None,
            provider_availability_verdict_ref=None,
            provider_attempt_receipt_refs=(),
            fallback_provider_attempt_count=0,
            provider_duplicate_cost_risk=False,
            retry_count=0,
            quality_status=ENGINEERING_CHAT_APPLICATION_CLARIFICATION_QUALITY,
        )


class ModelExecutionPort(Protocol):
    """Provider-neutral execution port owned by the Model Execution Runtime."""

    def execute(
        self, request: EngineeringTurnExecutionRequest
    ) -> EngineeringTurnExecutionOutcome: ...


# Compatibility alias: existing infrastructure adapters can migrate without
# making Provider routing a new application contract.
EngineeringConversationTurnExecutor = ModelExecutionPort


class ConversationNotFoundError(LookupError):
    def __init__(self, conversation_id: StableId) -> None:
        super().__init__(f"Conversation {conversation_id.value} was not found")
        self.conversation_id = conversation_id


class InMemoryEngineeringConversationService:
    """Ephemeral Application authority for Access and qualified Turn execution."""

    def __init__(
        self,
        binding: EngineeringChatBinding,
        *,
        turn_executor: EngineeringConversationTurnExecutor | None = None,
        id_generator: IdGenerator | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if binding.execution_status is RuntimeCapabilityStatus.READY and turn_executor is None:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "a ready Provider binding requires a qualified Turn executor",
            )
        if turn_executor is not None and (
            binding.execution_status is not RuntimeCapabilityStatus.READY
            or binding.world_model_status is not RuntimeCapabilityStatus.READY
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Turn execution requires ready Provider and World Model bindings",
            )
        self.binding = binding
        self._turn_executor = turn_executor
        self._input_policy = _conversation_input_policy(
            binding.conversation_input_policy_ref
        )
        self._id_generator = id_generator or Uuid4IdGenerator()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._lock = Lock()
        self._history: dict[
            StableId, tuple[EngineeringConversationSnapshot, ...]
        ] = {}
        self._issued_ids: set[StableId] = set()
        self._inflight: set[StableId] = set()
        self._turn_count = 0
        self._provider_dispatch_count = 0

    @property
    def semantic_agent_execution(self) -> bool:
        return self._turn_executor is not None

    @property
    def implementation_scope(self) -> str:
        return (
            "CONVERSATIONAL_AGENT_EXECUTOR"
            if self.semantic_agent_execution
            else "CHAT_ACCESS_ONLY"
        )

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
            if conversation_id in self._inflight:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "Conversation already has an executing Turn",
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
            execution_request = EngineeringTurnExecutionRequest(
                binding=self.binding,
                snapshot_before=current,
                turn_id=turn_id,
                result_id=result_id,
                sequence=turn_sequence,
                user_message=user_message,
                request_digest=request_digest,
                requested_at=now,
            )
            if self._input_policy is not None:
                clarification = self._input_policy.clarification_for(
                    snapshot=current,
                    message=message,
                )
                if clarification is not None:
                    return self._commit_outcome(
                        request=execution_request,
                        assistant_message_id=assistant_message_id,
                        outcome=EngineeringTurnExecutionOutcome.application_clarification(
                            request_digest=request_digest,
                            assistant_content=clarification,
                            included_user_message_ids=(user_message_id,),
                            accepted_correction_message_ids=(
                                current.context.accepted_correction_message_ids
                            ),
                            reviewed_conclusion_refs=(
                                current.context.reviewed_conclusion_refs
                            ),
                            superseded_conclusion_refs=(
                                current.context.superseded_conclusion_refs
                            ),
                        ),
                    )
            if self._turn_executor is None:
                return self._commit_outcome(
                    request=execution_request,
                    assistant_message_id=assistant_message_id,
                    outcome=_access_failure_outcome(execution_request),
                )
            self._inflight.add(conversation_id)

        try:
            outcome = self._turn_executor.execute(execution_request)
        except Exception:
            outcome = _execution_error_outcome(execution_request)

        with self._lock:
            try:
                current = self._current(conversation_id)
                if current.conversation.revision != expected_revision:
                    raise DomainError(
                        ErrorCode.REVISION_CONFLICT,
                        "Conversation changed while its Turn was executing",
                    )
                outcome = _fail_closed_invalid_outcome(execution_request, outcome)
                return self._commit_outcome(
                    request=execution_request,
                    assistant_message_id=assistant_message_id,
                    outcome=outcome,
                )
            finally:
                self._inflight.discard(conversation_id)

    def _commit_outcome(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        assistant_message_id: StableId,
        outcome: EngineeringTurnExecutionOutcome,
    ) -> EngineeringTurnSubmission:
        current = request.snapshot_before
        _validate_execution_outcome(request, outcome)
        completed_at = self._now()
        commits_agent_state = outcome.state is ConversationTurnState.SUCCEEDED
        context = ConversationContext.seal(
            conversation_id=current.conversation.conversation_id,
            work_state_revision=(
                outcome.work_state_revision
                if commits_agent_state and outcome.work_state_revision is not None
                else current.context.work_state_revision
            ),
            included_user_message_ids=outcome.included_user_message_ids,
            accepted_correction_message_ids=(
                outcome.accepted_correction_message_ids
                if commits_agent_state
                else current.context.accepted_correction_message_ids
            ),
            reviewed_conclusion_refs=outcome.reviewed_conclusion_refs,
            superseded_conclusion_refs=(
                outcome.superseded_conclusion_refs
                if commits_agent_state
                else current.context.superseded_conclusion_refs
            ),
            work_state_ref=(
                outcome.work_state_ref
                if commits_agent_state
                else current.context.work_state_ref
            ),
            work_state_digest=(
                outcome.work_state_digest
                if commits_agent_state
                else current.context.work_state_digest
            ),
            reducer_status=outcome.reducer_status,
        )
        assistant_message = _message(
            message_id=assistant_message_id,
            conversation_id=current.conversation.conversation_id,
            turn_id=request.turn_id,
            sequence=len(current.messages) + 2,
            role=ConversationMessageRole.ASSISTANT,
            kind=outcome.assistant_kind,
            content=outcome.assistant_content,
            created_at=completed_at,
        )
        next_revision = current.conversation.revision.next()
        turn = _turn(
            request=request,
            outcome=outcome,
            assistant_message_id=assistant_message_id,
            context_after=context,
            conversation_revision_after=next_revision,
            completed_at=completed_at,
        )
        messages = (*current.messages, request.user_message, assistant_message)
        turns = (*current.turns, turn)
        conversation = _conversation(
            conversation_id=current.conversation.conversation_id,
            revision=next_revision,
            binding_digest=self.binding.digest,
            context_digest=context.digest,
            turn_ids=tuple(item.turn_id for item in turns),
            message_ids=tuple(item.message_id for item in messages),
            created_at=current.conversation.created_at,
            revised_at=completed_at,
        )
        snapshot = EngineeringConversationSnapshot(
            conversation=conversation,
            context=context,
            messages=messages,
            turns=turns,
        )
        self._history[current.conversation.conversation_id] = (
            *self._history[current.conversation.conversation_id],
            snapshot,
        )
        self._turn_count += 1
        self._provider_dispatch_count += outcome.provider_dispatch_count
        return EngineeringTurnSubmission(snapshot=snapshot, turn=turn)

    def statistics(self) -> tuple[int, int]:
        with self._lock:
            return len(self._history), self._turn_count

    def provider_dispatch_count(self) -> int:
        with self._lock:
            return self._provider_dispatch_count

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


def _access_failure_outcome(
    request: EngineeringTurnExecutionRequest,
) -> EngineeringTurnExecutionOutcome:
    failure_code = (
        "MODEL_EXECUTION_NOT_QUALIFIED"
        if request.binding.execution_status is RuntimeCapabilityStatus.NOT_QUALIFIED
        else "MODEL_EXECUTION_NOT_CONFIGURED"
    )
    failure_message = (
        "当前 Chat Access 尚未配置或取得模型执行资格；本 Turn 已失败关闭，"
        "没有生成或授权工程答案。Conversation 仍可继续使用。"
    )
    return EngineeringTurnExecutionOutcome.failed(
        request_digest=request.request_digest,
        assistant_content=failure_message,
        included_user_message_ids=(
            *request.snapshot_before.context.included_user_message_ids,
            request.user_message.message_id,
        ),
        accepted_correction_message_ids=(
            request.snapshot_before.context.accepted_correction_message_ids
        ),
        reviewed_conclusion_refs=(
            request.snapshot_before.context.reviewed_conclusion_refs
        ),
        superseded_conclusion_refs=(
            request.snapshot_before.context.superseded_conclusion_refs
        ),
        reducer_status="NOT_EXECUTED_ACCESS_ONLY",
        failure_code=failure_code,
        failure_message=failure_message,
    )


def _execution_error_outcome(
    request: EngineeringTurnExecutionRequest,
    *,
    failure_code: str = "AGENT_EXECUTION_FAILED",
    provider_dispatch_count: int = 0,
) -> EngineeringTurnExecutionOutcome:
    failure_message = (
        "主工程 Agent 执行未能形成可审核、可授权的本 Turn 结果；"
        "本 Turn 已失败关闭，Conversation 仍可继续使用。"
    )
    return EngineeringTurnExecutionOutcome.failed(
        request_digest=request.request_digest,
        assistant_content=failure_message,
        included_user_message_ids=(
            *request.snapshot_before.context.included_user_message_ids,
            request.user_message.message_id,
        ),
        accepted_correction_message_ids=(
            request.snapshot_before.context.accepted_correction_message_ids
        ),
        reviewed_conclusion_refs=(
            request.snapshot_before.context.reviewed_conclusion_refs
        ),
        superseded_conclusion_refs=(
            request.snapshot_before.context.superseded_conclusion_refs
        ),
        reducer_status="AGENT_EXECUTION_FAILED_CLOSED",
        work_state_ref=request.snapshot_before.context.work_state_ref,
        work_state_revision=(
            request.snapshot_before.context.work_state_revision
            if request.snapshot_before.context.work_state_ref is not None
            else None
        ),
        work_state_digest=request.snapshot_before.context.work_state_digest,
        failure_code=failure_code,
        failure_message=failure_message,
        provider_dispatch_count=provider_dispatch_count,
    )


def _fail_closed_invalid_outcome(
    request: EngineeringTurnExecutionRequest,
    outcome: object,
) -> EngineeringTurnExecutionOutcome:
    if isinstance(outcome, EngineeringTurnExecutionOutcome):
        try:
            _validate_execution_outcome(request, outcome)
        except DomainError:
            pass
        else:
            return outcome
        dispatch_count = (
            outcome.provider_dispatch_count
            if type(outcome.provider_dispatch_count) is int
            and outcome.provider_dispatch_count >= 0
            else 0
        )
    else:
        dispatch_count = 0
    return _execution_error_outcome(
        request,
        failure_code="TURN_EXECUTOR_PROTOCOL_VIOLATION",
        provider_dispatch_count=dispatch_count,
    )


def _validate_execution_outcome(
    request: EngineeringTurnExecutionRequest,
    outcome: EngineeringTurnExecutionOutcome,
) -> None:
    if not isinstance(outcome.state, ConversationTurnState) or not isinstance(
        outcome.assistant_kind, ConversationMessageKind
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Turn executor outcome uses an invalid state or message kind",
        )
    if outcome.request_digest != request.request_digest:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Turn executor outcome is bound to a different request",
        )
    _chat_message(outcome.assistant_content)
    if outcome.retry_count != 0:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Engineering Conversation does not permit same-Provider retries",
        )
    if (
        type(outcome.provider_dispatch_count) is not int
        or outcome.provider_dispatch_count < 0
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Provider dispatch count must be a non-negative integer",
        )
    model_receipts = tuple(
        _text(item, "model dispatch receipt reference")
        for item in outcome.model_dispatch_receipt_refs
    )
    if len(model_receipts) != len(set(model_receipts)):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "model dispatch receipt references must be unique",
        )
    classification = outcome.provider_failure_classification
    provider_failure_code = _optional_text(
        outcome.provider_failure_code, "Provider failure code"
    )
    if classification is not None and not isinstance(
        classification, EngineeringProviderFailureClassification
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Provider failure classification is invalid",
        )
    if (classification is None) != (provider_failure_code is None):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Provider failure classification and raw code must be present together",
        )
    has_http_evidence = outcome.provider_http_status is not None
    if has_http_evidence != (
        outcome.provider_http_failure_evidence_digest is not None
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Provider HTTP status and failure-evidence digest must be present together",
        )
    if has_http_evidence and (
        type(outcome.provider_http_status) is not int
        or not 100 <= outcome.provider_http_status <= 599
        or not isinstance(
            outcome.provider_http_failure_evidence_digest, Digest
        )
        or classification
        is not EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR
        or provider_failure_code != ErrorCode.PROVIDER_HTTP_ERROR.value
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Provider HTTP failure evidence is inconsistent with the raw failure",
        )
    route_receipt_ref = _optional_text(
        outcome.provider_route_receipt_ref, "Provider route receipt reference"
    )
    availability_verdict_ref = _optional_text(
        outcome.provider_availability_verdict_ref,
        "execution-profile availability verdict reference",
    )
    attempt_receipts = tuple(
        _text(item, "Provider attempt receipt reference")
        for item in outcome.provider_attempt_receipt_refs
    )
    if len(attempt_receipts) != len(set(attempt_receipts)):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Provider attempt receipt references must be unique",
        )
    if (
        type(outcome.fallback_provider_attempt_count) is not int
        or outcome.fallback_provider_attempt_count not in {0, 1}
        or type(outcome.provider_duplicate_cost_risk) is not bool
        or (
            route_receipt_ref is None
            and (
                attempt_receipts
                or outcome.fallback_provider_attempt_count != 0
                or outcome.provider_duplicate_cost_risk
                or availability_verdict_ref is not None
            )
        )
        or (
            route_receipt_ref is not None
            and len(attempt_receipts)
            != 1 + outcome.fallback_provider_attempt_count
        )
        or (
            outcome.provider_duplicate_cost_risk
            and outcome.fallback_provider_attempt_count != 1
        )
        or (
            outcome.fallback_provider_attempt_count == 0
            and availability_verdict_ref is not None
        )
        or (
            outcome.fallback_provider_attempt_count == 1
            and availability_verdict_ref is None
        )
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Provider route, attempt count, and duplicate-cost audit disagree",
        )
    available_user_messages = {
        item.message_id
        for item in request.snapshot_before.messages
        if item.role is ConversationMessageRole.USER
    }
    available_user_messages.add(request.user_message.message_id)
    included = tuple(outcome.included_user_message_ids)
    if (
        not included
        or request.user_message.message_id not in included
        or len(included) != len(set(included))
        or not set(included).issubset(available_user_messages)
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "executed Context must uniquely include the current User Message and only known history",
        )
    work_state_parts = (
        outcome.work_state_ref,
        outcome.work_state_revision,
        outcome.work_state_digest,
    )
    if any(item is None for item in work_state_parts) and any(
        item is not None for item in work_state_parts
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "executed Agent Work State reference, revision, and digest must be present together",
        )
    if outcome.work_state_revision is not None and not isinstance(
        outcome.work_state_revision, Revision
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "executed Agent Work State revision is invalid",
        )
    if outcome.work_state_digest is not None and not isinstance(
        outcome.work_state_digest, Digest
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "executed Agent Work State digest is invalid",
        )
    for value, label in (
        (outcome.work_state_ref, "Agent Work State reference"),
        (outcome.evidence_package_ref, "Evidence Package reference"),
        (outcome.answer_ref, "Answer reference"),
        (outcome.review_ref, "Review reference"),
        (outcome.delivery_authorization_ref, "Delivery authorization reference"),
        (outcome.failure_code, "failure code"),
        (outcome.failure_message, "failure message"),
    ):
        _optional_text(value, label)
    citations = tuple(outcome.citations)
    citation_refs: list[str] = []
    for citation in citations:
        if not isinstance(citation, EngineeringTurnCitation):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Turn Citation projection is untyped",
            )
        expected_citation = EngineeringTurnCitation.create(
            citation_ref=citation.citation_ref,
            evidence_class=citation.evidence_class,
            source_revision=citation.source_revision,
            locator=citation.locator,
            modality=citation.modality,
            content_digest=citation.content_digest,
        )
        if citation != expected_citation:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Turn Citation projection identity is inconsistent",
            )
        citation_refs.append(citation.citation_ref)
    if len(citation_refs) != len(set(citation_refs)):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Turn Citation references must be unique",
        )
    _text(outcome.reducer_status, "Context reducer status")
    _text(outcome.quality_status, "quality status")
    application_clarification = (
        outcome.quality_status
        == ENGINEERING_CHAT_APPLICATION_CLARIFICATION_QUALITY
    )
    input_policy = _conversation_input_policy(
        request.binding.conversation_input_policy_ref
    )
    expected_application_clarification = (
        input_policy.clarification_for(
            snapshot=request.snapshot_before,
            message=request.user_message.content,
        )
        if input_policy is not None
        else None
    )
    if application_clarification != (
        expected_application_clarification is not None
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Application input clarification must be authorized by the exact Binding policy",
        )
    if (
        application_clarification
        and outcome.assistant_content != expected_application_clarification
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Application input clarification must use the Binding policy result",
        )

    before = request.snapshot_before.context
    if outcome.work_state_revision is not None:
        if before.work_state_ref is not None and (
            outcome.work_state_ref != before.work_state_ref
            or outcome.work_state_revision.value < before.work_state_revision.value
            or (
                (outcome.work_state_digest == before.work_state_digest)
                != (outcome.work_state_revision == before.work_state_revision)
            )
        ):
            raise DomainError(
                ErrorCode.REVISION_CONFLICT,
                "Agent Work State identity or revision does not continue the sealed Conversation state",
            )
    elif before.work_state_ref is not None:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "an existing Agent Work State cannot be dropped",
        )
    corrections = tuple(outcome.accepted_correction_message_ids)
    if corrections[: len(before.accepted_correction_message_ids)] != (
        before.accepted_correction_message_ids
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "accepted Conversation corrections cannot be dropped",
        )
    reviewed = tuple(outcome.reviewed_conclusion_refs)
    superseded = tuple(outcome.superseded_conclusion_refs)
    if not set(before.reviewed_conclusion_refs).issubset(reviewed):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "reviewed Conversation conclusions cannot be dropped",
        )
    if superseded[: len(before.superseded_conclusion_refs)] != (
        before.superseded_conclusion_refs
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "superseded Conversation conclusions cannot be restored silently",
        )
    newly_superseded = set(superseded) - set(before.superseded_conclusion_refs)
    if not newly_superseded.issubset(before.reviewed_conclusion_refs):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "only conclusions reviewed before this Turn can be newly superseded",
        )
    if outcome.state is ConversationTurnState.SUCCEEDED:
        if classification is not None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "successful Turn cannot carry a Provider failure classification",
            )
        if outcome.assistant_kind not in {
            ConversationMessageKind.ANSWER,
            ConversationMessageKind.CLARIFICATION,
            ConversationMessageKind.LIMITATION,
        }:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "successful Turn requires an answer, clarification, or reviewed limitation",
            )
        if application_clarification:
            empty_context = (
                request.sequence == 1
                and not request.snapshot_before.messages
                and not request.snapshot_before.turns
                and not before.included_user_message_ids
                and before.work_state_ref is None
                and not before.reviewed_conclusion_refs
            )
            forbidden = (
                outcome.work_state_ref,
                outcome.work_state_revision,
                outcome.work_state_digest,
                outcome.evidence_package_ref,
                outcome.answer_ref,
                outcome.review_ref,
                outcome.delivery_authorization_ref,
                outcome.failure_code,
                outcome.failure_message,
                route_receipt_ref,
                availability_verdict_ref,
            )
            if (
                outcome.assistant_kind
                is not ConversationMessageKind.CLARIFICATION
                or not empty_context
                or any(item is not None for item in forbidden)
                or included != (request.user_message.message_id,)
                or corrections != before.accepted_correction_message_ids
                or reviewed != before.reviewed_conclusion_refs
                or superseded != before.superseded_conclusion_refs
                or outcome.reducer_status
                != "PRE_DISPATCH_CLARIFICATION_REQUIRED"
                or outcome.provider_dispatch_count != 0
                or model_receipts
                or attempt_receipts
                or outcome.fallback_provider_attempt_count != 0
                or outcome.provider_duplicate_cost_risk
                or citations
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Application input clarification must remain empty-context and pre-dispatch",
                )
            return
        required = (
            outcome.work_state_ref,
            outcome.work_state_revision,
            outcome.work_state_digest,
            outcome.evidence_package_ref,
            outcome.answer_ref,
            outcome.review_ref,
            outcome.delivery_authorization_ref,
        )
        if any(item is None for item in required):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "successful Turn requires Work State, Package, Answer, Review, and Delivery authorization",
            )
        if outcome.failure_code is not None or outcome.failure_message is not None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "successful Turn cannot carry a failure",
            )
        expected_quality = {
            ConversationMessageKind.ANSWER: "ACCEPTED",
            ConversationMessageKind.CLARIFICATION: "REVIEWED_CLARIFICATION",
            ConversationMessageKind.LIMITATION: "REVIEWED_LIMITATION",
        }[outcome.assistant_kind]
        if outcome.quality_status != expected_quality:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "successful Turn quality status does not match its reviewed response kind",
            )
        expected_reviewed = before.reviewed_conclusion_refs
        if outcome.assistant_kind is ConversationMessageKind.ANSWER:
            if outcome.answer_ref in before.reviewed_conclusion_refs:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "a successful answer requires a fresh Answer reference",
                )
            expected_reviewed = (*expected_reviewed, outcome.answer_ref)
        if reviewed != expected_reviewed:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "reviewed conclusions must preserve history and append only the current reviewed Answer",
            )
    else:
        if (
            outcome.assistant_kind is not ConversationMessageKind.LIMITATION
            or not outcome.failure_code
            or not outcome.failure_message
            or outcome.delivery_authorization_ref is not None
            or outcome.quality_status != "NOT_ACCEPTED"
            or citations
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "failed Turn must be an un-authorized explicit limitation",
            )
        if reviewed != before.reviewed_conclusion_refs:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "a failed Turn cannot add a reviewed conclusion",
            )


def validate_engineering_turn_execution_outcome(
    request: EngineeringTurnExecutionRequest,
    outcome: EngineeringTurnExecutionOutcome,
) -> None:
    """Validate a Turn executor result before another Application owner trusts it."""

    _validate_execution_outcome(request, outcome)


def _turn(
    *,
    request: EngineeringTurnExecutionRequest,
    outcome: EngineeringTurnExecutionOutcome,
    assistant_message_id: StableId,
    context_after: ConversationContext,
    conversation_revision_after: Revision,
    completed_at: datetime,
) -> EngineeringConversationTurn:
    core = {
        "schema": "ENGINEERING_CONVERSATION_TURN_RESULT@6",
        "turn_id": request.turn_id.value,
        "result_id": request.result_id.value,
        "conversation_id": request.snapshot_before.conversation.conversation_id.value,
        "sequence": request.sequence,
        "conversation_revision_before": request.snapshot_before.conversation.revision.value,
        "conversation_revision_after": conversation_revision_after.value,
        "context_digest_before": request.snapshot_before.context.digest.value,
        "context_digest_after": context_after.digest.value,
        "request_digest": request.request_digest.value,
        "user_message_id": request.user_message.message_id.value,
        "assistant_message_id": assistant_message_id.value,
        "state": outcome.state.value,
        "failure_code": outcome.failure_code,
        "failure_message": outcome.failure_message,
        "evidence_package_ref": outcome.evidence_package_ref,
        "answer_ref": outcome.answer_ref,
        "review_ref": outcome.review_ref,
        "delivery_authorization_ref": outcome.delivery_authorization_ref,
        "citations": tuple(
            (item.citation_ref, item.digest.value) for item in outcome.citations
        ),
        "work_state_ref": outcome.work_state_ref,
        "work_state_revision": (
            outcome.work_state_revision.value
            if outcome.work_state_revision is not None
            else None
        ),
        "work_state_digest": (
            outcome.work_state_digest.value
            if outcome.work_state_digest is not None
            else None
        ),
        "delivery_state": (
            "AUTHORIZED"
            if outcome.delivery_authorization_ref is not None
            else "NOT_AUTHORIZED"
        ),
        "provider_dispatch_count": outcome.provider_dispatch_count,
        "model_dispatch_receipt_refs": outcome.model_dispatch_receipt_refs,
        "provider_failure_classification": (
            outcome.provider_failure_classification.value
            if outcome.provider_failure_classification is not None
            else None
        ),
        "provider_failure_code": outcome.provider_failure_code,
        "provider_http_status": outcome.provider_http_status,
        "provider_http_failure_evidence_digest": (
            outcome.provider_http_failure_evidence_digest.value
            if outcome.provider_http_failure_evidence_digest is not None
            else None
        ),
        "provider_route_receipt_ref": outcome.provider_route_receipt_ref,
        "provider_availability_verdict_ref": (
            outcome.provider_availability_verdict_ref
        ),
        "provider_attempt_receipt_refs": outcome.provider_attempt_receipt_refs,
        "fallback_provider_attempt_count": (
            outcome.fallback_provider_attempt_count
        ),
        "provider_duplicate_cost_risk": outcome.provider_duplicate_cost_risk,
        "retry_count": outcome.retry_count,
        "quality_status": outcome.quality_status,
        "production_activation": "NOT_EXECUTED",
        "created_at": request.requested_at,
        "completed_at": completed_at,
    }
    return EngineeringConversationTurn(
        turn_id=request.turn_id,
        result_id=request.result_id,
        conversation_id=request.snapshot_before.conversation.conversation_id,
        sequence=request.sequence,
        conversation_revision_before=request.snapshot_before.conversation.revision,
        conversation_revision_after=conversation_revision_after,
        context_digest_before=request.snapshot_before.context.digest,
        context_digest_after=context_after.digest,
        request_digest=request.request_digest,
        user_message_id=request.user_message.message_id,
        assistant_message_id=assistant_message_id,
        state=outcome.state,
        failure_code=outcome.failure_code,
        failure_message=outcome.failure_message,
        evidence_package_ref=outcome.evidence_package_ref,
        answer_ref=outcome.answer_ref,
        review_ref=outcome.review_ref,
        delivery_authorization_ref=outcome.delivery_authorization_ref,
        citations=outcome.citations,
        work_state_ref=outcome.work_state_ref,
        work_state_revision=outcome.work_state_revision,
        work_state_digest=outcome.work_state_digest,
        delivery_state=core["delivery_state"],
        provider_dispatch_count=outcome.provider_dispatch_count,
        model_dispatch_receipt_refs=outcome.model_dispatch_receipt_refs,
        provider_failure_classification=(
            outcome.provider_failure_classification
        ),
        provider_failure_code=outcome.provider_failure_code,
        provider_http_status=outcome.provider_http_status,
        provider_http_failure_evidence_digest=(
            outcome.provider_http_failure_evidence_digest
        ),
        provider_route_receipt_ref=outcome.provider_route_receipt_ref,
        provider_availability_verdict_ref=(
            outcome.provider_availability_verdict_ref
        ),
        provider_attempt_receipt_refs=outcome.provider_attempt_receipt_refs,
        fallback_provider_attempt_count=outcome.fallback_provider_attempt_count,
        provider_duplicate_cost_risk=outcome.provider_duplicate_cost_risk,
        retry_count=outcome.retry_count,
        quality_status=outcome.quality_status,
        production_activation="NOT_EXECUTED",
        created_at=request.requested_at,
        completed_at=completed_at,
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


def _bounded_text(value: str, label: str, *, maximum_bytes: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be non-empty without surrounding whitespace",
        )
    if len(value.encode("utf-8")) > maximum_bytes:
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
    "EngineeringConversationTurnExecutor",
    "EngineeringConversationTurn",
    "EngineeringTurnCitation",
    "EngineeringTurnExecutionOutcome",
    "EngineeringTurnExecutionRequest",
    "EngineeringTurnSubmission",
    "InMemoryEngineeringConversationService",
    "RuntimeCapabilityStatus",
]
