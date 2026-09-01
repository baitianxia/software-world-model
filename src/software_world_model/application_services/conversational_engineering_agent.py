"""Application-owned control loop for a conversational engineering Agent.

The loop deliberately has no filesystem, Source, shell, network, credential, or
Provider adapter dependency.  A model driver can only propose a full Work State
revision and one closed-catalog action or response.  Trusted ports execute tool
requests, review the sealed evidence-bound draft, and authorize delivery.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import re
from threading import Lock
from typing import TYPE_CHECKING, Protocol, Sequence

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    Revision,
    StableId,
    Uuid4IdGenerator,
    canonical_json_bytes,
    digest_of,
)

from .engineering_conversation import (
    ConversationMessageKind,
    ConversationTurnState,
    EngineeringConversationTurnExecutor,
    EngineeringTurnCitation,
    EngineeringTurnExecutionOutcome,
    EngineeringTurnExecutionRequest,
    EngineeringProviderFailureClassification,
    RuntimeCapabilityStatus,
)

if TYPE_CHECKING:
    from software_world_model.knowledge_engine.capability_cognition import (
        CognitionProvenance,
    )


_DEFAULT_MAXIMUM_TOOL_ACTIONS = 8
_MAXIMUM_DRAFT_CONTENT_UNITS = 128
_MARKDOWN_HEADING_RE = re.compile(r"^(?P<marks>#{1,6})\s+(?P<title>.+)$")
_MARKDOWN_STANDALONE_LABEL_RE = re.compile(r"^\*\*[^\n]+\*\*$")
_MARKDOWN_INLINE_CODE_SPAN_RE = re.compile(r"(?<!`)`([^`\n]+)`(?!`)")
_MARKDOWN_LIST_ITEM_PREFIX_RE = re.compile(
    r"^(?:(?:[-+*])|(?:[0-9]+[.)]))[ \t]+"
)
_MARKDOWN_PAIRED_BOLD_SPAN_RE = re.compile(
    r"(?P<delimiter>\*\*|__)(?P<content>\S(?:.*?\S)?)"
    r"(?P=delimiter)"
)


class EngineeringAgentToolOperation(str, Enum):
    WORLD_MODEL_QUERY = "WORLD_MODEL_QUERY"
    SOURCE_SEARCH = "SOURCE_SEARCH"
    SOURCE_READ = "SOURCE_READ"


class EngineeringAgentEvidenceDisposition(str, Enum):
    SUPPORT = "SUPPORT"
    BOUNDARY = "BOUNDARY"


class EngineeringAgentToolAuthorityKind(str, Enum):
    WORLD_MODEL = "WORLD_MODEL"
    SOURCE = "SOURCE"


class EngineeringAgentResponseKind(str, Enum):
    ANSWER = "ANSWER"
    CLARIFICATION = "CLARIFICATION"
    LIMITATION = "LIMITATION"


class EngineeringAgentWorkPhase(str, Enum):
    PLANNING = "PLANNING"
    INVESTIGATING = "INVESTIGATING"
    REVISING = "REVISING"
    RESPONSE_READY = "RESPONSE_READY"


class EngineeringAgentReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    FINDINGS = "FINDINGS"


class EngineeringAgentReviewFocus(str, Enum):
    COMPREHENSIVE = "COMPREHENSIVE"
    EVIDENCE_BOUNDARY_CHALLENGE = "EVIDENCE_BOUNDARY_CHALLENGE"


class EngineeringAgentRequirementCoverageDisposition(str, Enum):
    FULLY_ADDRESSED = "FULLY_ADDRESSED"
    MATERIAL_REQUIREMENT_MISSING_OR_MISALIGNED = (
        "MATERIAL_REQUIREMENT_MISSING_OR_MISALIGNED"
    )


class EngineeringAgentContentCoverageDisposition(str, Enum):
    COVERED = "COVERED"
    BOUNDARY_REVIEW_DEFERRED = "BOUNDARY_REVIEW_DEFERRED"
    NON_ASSERTIVE = "NON_ASSERTIVE"
    DEFECT = "DEFECT"


class EngineeringAgentEvidenceBoundaryAssessmentDisposition(str, Enum):
    WITHIN_CALLER_EVIDENCE = "WITHIN_CALLER_EVIDENCE"
    CLAIM_EXCEEDS_CALLER_EVIDENCE = "CLAIM_EXCEEDS_CALLER_EVIDENCE"


class EngineeringAgentClaimSemanticScope(str, Enum):
    CALLER_INVOCATION = "CALLER_INVOCATION"
    SOURCE_VISIBLE_LOCAL_ORDER = "SOURCE_VISIBLE_LOCAL_ORDER"
    CALLEE_IMPLEMENTATION_OR_RETURN = "CALLEE_IMPLEMENTATION_OR_RETURN"
    DATABASE_OR_EXTERNAL_STATE_EFFECT = "DATABASE_OR_EXTERNAL_STATE_EFFECT"
    CONSUMER_VISIBLE_RUNTIME_EFFECT = "CONSUMER_VISIBLE_RUNTIME_EFFECT"


class EngineeringAgentBoundaryRelevanceAssessmentDisposition(str, Enum):
    MATERIAL_TO_USER_REQUEST = "MATERIAL_TO_USER_REQUEST"
    RESOLVED_AUDIT_ONLY = "RESOLVED_AUDIT_ONLY"
    NON_MATERIAL_AUDIT_ONLY = "NON_MATERIAL_AUDIT_ONLY"
    NOT_DISCLOSED_IN_DRAFT = "NOT_DISCLOSED_IN_DRAFT"


class EngineeringAgentBoundaryRelevanceChallengeKind(str, Enum):
    RESOLVED_ACQUISITION = "RESOLVED_ACQUISITION"
    BOUNDARY_MATERIALITY = "BOUNDARY_MATERIALITY"


_BOUNDARY_RELEVANCE_AUDIT_ONLY_DISPOSITIONS = frozenset(
    {
        EngineeringAgentBoundaryRelevanceAssessmentDisposition.RESOLVED_AUDIT_ONLY,
        EngineeringAgentBoundaryRelevanceAssessmentDisposition.NON_MATERIAL_AUDIT_ONLY,
    }
)


class EngineeringAgentModelRole(str, Enum):
    PRIMARY_AGENT = "PRIMARY_AGENT"
    INDEPENDENT_REVIEWER = "INDEPENDENT_REVIEWER"


class EngineeringAgentInvocationMode(str, Enum):
    STANDARD = "STANDARD"
    EVIDENCE_ONLY_SYNTHESIS = "EVIDENCE_ONLY_SYNTHESIS"


class EngineeringAgentModelDispatchState(str, Enum):
    PRE_DISPATCH_REJECTED = "PRE_DISPATCH_REJECTED"
    DISPATCHED_COMPLETED = "DISPATCHED_COMPLETED"
    DISPATCHED_REJECTED = "DISPATCHED_REJECTED"
    DISPATCHED_OUTCOME_UNKNOWN = "DISPATCHED_OUTCOME_UNKNOWN"
    REPLAYED_COMPLETED = "REPLAYED_COMPLETED"
    REPLAYED_REJECTED = "REPLAYED_REJECTED"
    REPLAYED_OUTCOME_UNKNOWN = "REPLAYED_OUTCOME_UNKNOWN"


class EngineeringAgentModelFailureKind(str, Enum):
    """Trusted ownership classification for one failed model boundary call.

    ``failure_code`` preserves the raw owner outcome.  This enum records which
    boundary established that outcome so routing never infers fallback
    eligibility from an ambiguous string alone.
    """

    PRE_DISPATCH_REJECTED = "PRE_DISPATCH_REJECTED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    PROVIDER_HTTP_ERROR = "PROVIDER_HTTP_ERROR"
    PROVIDER_OUTCOME_UNKNOWN = "PROVIDER_OUTCOME_UNKNOWN"
    PROVIDER_OUTPUT_INVALID = "PROVIDER_OUTPUT_INVALID"
    QUALIFICATION_REJECTED = "QUALIFICATION_REJECTED"
    GATEWAY_RESULT_INVALID = "GATEWAY_RESULT_INVALID"
    GATEWAY_FAILURE = "GATEWAY_FAILURE"


@dataclass(frozen=True, slots=True)
class EngineeringAgentModelCallReceipt:
    model_call_ref: str
    gateway_call_ref: str | None
    role: EngineeringAgentModelRole
    state: EngineeringAgentModelDispatchState
    provider_dispatch_count: int
    failure_kind: EngineeringAgentModelFailureKind | None
    failure_code: str | None
    provider_http_status: int | None
    provider_http_failure_evidence_digest: Digest | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        model_call_ref: str,
        role: EngineeringAgentModelRole,
        state: EngineeringAgentModelDispatchState,
        gateway_call_ref: str | None = None,
        failure_kind: EngineeringAgentModelFailureKind | None = None,
        failure_code: str | None = None,
        provider_http_status: int | None = None,
        provider_http_failure_evidence_digest: Digest | None = None,
    ) -> "EngineeringAgentModelCallReceipt":
        if not isinstance(role, EngineeringAgentModelRole) or not isinstance(
            state, EngineeringAgentModelDispatchState
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Agent model call role or dispatch state is invalid",
            )
        dispatched = state in {
            EngineeringAgentModelDispatchState.DISPATCHED_COMPLETED,
            EngineeringAgentModelDispatchState.DISPATCHED_REJECTED,
            EngineeringAgentModelDispatchState.DISPATCHED_OUTCOME_UNKNOWN,
        }
        successful = state in {
            EngineeringAgentModelDispatchState.DISPATCHED_COMPLETED,
            EngineeringAgentModelDispatchState.REPLAYED_COMPLETED,
        }
        gateway_call_ref = _optional_text(
            gateway_call_ref, "Gateway model call reference"
        )
        failure_code = _optional_text(failure_code, "model call failure code")
        if failure_kind is not None and not isinstance(
            failure_kind, EngineeringAgentModelFailureKind
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Agent model failure kind is invalid",
            )
        has_http_evidence = provider_http_status is not None
        if has_http_evidence != (
            provider_http_failure_evidence_digest is not None
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Provider HTTP status and failure-evidence digest must be present together",
            )
        if has_http_evidence and (
            type(provider_http_status) is not int
            or not 100 <= provider_http_status <= 599
            or not isinstance(provider_http_failure_evidence_digest, Digest)
            or failure_kind
            is not EngineeringAgentModelFailureKind.PROVIDER_HTTP_ERROR
            or failure_code != ErrorCode.PROVIDER_HTTP_ERROR.value
            or state
            not in {
                EngineeringAgentModelDispatchState.DISPATCHED_REJECTED,
                EngineeringAgentModelDispatchState.REPLAYED_REJECTED,
            }
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Provider HTTP failure evidence does not bind an exact failed Gateway call",
            )
        if (
            (gateway_call_ref is not None)
            != (state is not EngineeringAgentModelDispatchState.PRE_DISPATCH_REJECTED)
            or (failure_code is None) != successful
            or (failure_kind is None) != successful
            or (
                state is EngineeringAgentModelDispatchState.PRE_DISPATCH_REJECTED
                and failure_kind
                is not EngineeringAgentModelFailureKind.PRE_DISPATCH_REJECTED
            )
            or (
                state
                in {
                    EngineeringAgentModelDispatchState.DISPATCHED_OUTCOME_UNKNOWN,
                    EngineeringAgentModelDispatchState.REPLAYED_OUTCOME_UNKNOWN,
                }
                and failure_kind
                not in {
                    EngineeringAgentModelFailureKind.PROVIDER_OUTCOME_UNKNOWN,
                    EngineeringAgentModelFailureKind.GATEWAY_FAILURE,
                }
            )
            or (
                state
                in {
                    EngineeringAgentModelDispatchState.DISPATCHED_REJECTED,
                    EngineeringAgentModelDispatchState.REPLAYED_REJECTED,
                }
                and failure_kind
                not in {
                    EngineeringAgentModelFailureKind.PROVIDER_UNAVAILABLE,
                    EngineeringAgentModelFailureKind.PROVIDER_HTTP_ERROR,
                    EngineeringAgentModelFailureKind.PROVIDER_OUTPUT_INVALID,
                    EngineeringAgentModelFailureKind.QUALIFICATION_REJECTED,
                    EngineeringAgentModelFailureKind.GATEWAY_RESULT_INVALID,
                    EngineeringAgentModelFailureKind.GATEWAY_FAILURE,
                }
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent model dispatch state, Gateway reference, and failure disagree",
            )
        core = {
            "schema": "ENGINEERING_AGENT_MODEL_CALL_RECEIPT@3",
            "model_call_ref": _text(
                model_call_ref, "Agent model call reference"
            ),
            "gateway_call_ref": gateway_call_ref,
            "role": role.value,
            "state": state.value,
            "provider_dispatch_count": 1 if dispatched else 0,
            "failure_kind": (
                failure_kind.value if failure_kind is not None else None
            ),
            "failure_code": failure_code,
            "provider_http_status": provider_http_status,
            "provider_http_failure_evidence_digest": (
                provider_http_failure_evidence_digest.value
                if provider_http_failure_evidence_digest is not None
                else None
            ),
        }
        return cls(
            model_call_ref=core["model_call_ref"],
            gateway_call_ref=gateway_call_ref,
            role=role,
            state=state,
            provider_dispatch_count=core["provider_dispatch_count"],
            failure_kind=failure_kind,
            failure_code=failure_code,
            provider_http_status=provider_http_status,
            provider_http_failure_evidence_digest=(
                provider_http_failure_evidence_digest
            ),
            digest=digest_of(core),
        )

    @property
    def successful(self) -> bool:
        return self.state in {
            EngineeringAgentModelDispatchState.DISPATCHED_COMPLETED,
            EngineeringAgentModelDispatchState.REPLAYED_COMPLETED,
        }


class EngineeringAgentModelCallFailure(DomainError):
    """A sealed pre- or post-dispatch model failure with exact call accounting."""

    def __init__(
        self,
        *,
        receipt: EngineeringAgentModelCallReceipt,
        code: ErrorCode,
        message: str,
        prior_receipts: Sequence[EngineeringAgentModelCallReceipt] = (),
        invalid_output_text: str | None = None,
    ) -> None:
        receipts = (*tuple(prior_receipts), receipt)
        if (
            not _exact_model_receipt_sequence(
                receipts,
                role=receipt.role,
                terminal_must_succeed=False,
            )
            or invalid_output_text is not None
            and not isinstance(invalid_output_text, str)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "model call failure requires exact unique non-success receipts",
            )
        super().__init__(code, message)
        self.receipt = receipt
        self.prior_receipts = tuple(prior_receipts)
        self.invalid_output_text = invalid_output_text

    @property
    def receipts(self) -> tuple[EngineeringAgentModelCallReceipt, ...]:
        return (*self.prior_receipts, self.receipt)


@dataclass(frozen=True, slots=True)
class EngineeringAgentToolActionProposal:
    operation: EngineeringAgentToolOperation
    arguments: tuple[tuple[str, str], ...]
    evidence_need: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        operation: EngineeringAgentToolOperation,
        arguments: Sequence[tuple[str, str]],
        evidence_need: str,
    ) -> "EngineeringAgentToolActionProposal":
        if not isinstance(operation, EngineeringAgentToolOperation):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Agent tool operation must come from the closed catalog",
            )
        normalized = tuple(
            (_text(key, "tool argument name"), _bounded_text(value, "tool argument"))
            for key, value in arguments
        )
        keys = tuple(key for key, _ in normalized)
        if len(keys) != len(set(keys)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Agent tool argument names must be unique",
            )
        evidence_need = _bounded_text(evidence_need, "evidence need")
        core = {
            "schema": "ENGINEERING_AGENT_TOOL_ACTION_PROPOSAL@1",
            "operation": operation.value,
            "arguments": normalized,
            "evidence_need": evidence_need,
        }
        return cls(
            operation=operation,
            arguments=normalized,
            evidence_need=evidence_need,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentClaimProposal:
    statement: str
    support_observation_ids: tuple[StableId, ...]
    support_citation_refs: tuple[str, ...]

    @classmethod
    def create(
        cls,
        *,
        statement: str,
        support_observation_ids: Sequence[StableId],
        support_citation_refs: Sequence[str] = (),
    ) -> "EngineeringAgentClaimProposal":
        support = tuple(support_observation_ids)
        if not support or len(support) != len(set(support)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "an answer claim requires unique supporting observations",
            )
        citations = tuple(
            _text(item, "answer claim Citation reference")
            for item in support_citation_refs
        )
        if len(citations) != len(set(citations)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "answer claim Citation references must be unique",
            )
        return cls(
            statement=_bounded_text(statement, "answer claim"),
            support_observation_ids=support,
            support_citation_refs=citations,
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentDraftProposal:
    response_kind: EngineeringAgentResponseKind
    content: str
    claims: tuple[EngineeringAgentClaimProposal, ...]
    boundary_observation_ids: tuple[StableId, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        response_kind: EngineeringAgentResponseKind,
        content: str,
        claims: Sequence[EngineeringAgentClaimProposal] = (),
        boundary_observation_ids: Sequence[StableId] = (),
    ) -> "EngineeringAgentDraftProposal":
        if not isinstance(response_kind, EngineeringAgentResponseKind):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Agent response kind is invalid",
            )
        content = _response_text(content)
        normalized_claims = tuple(claims)
        boundary = tuple(boundary_observation_ids)
        if len(boundary) != len(set(boundary)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "boundary observation references must be unique",
            )
        if response_kind is EngineeringAgentResponseKind.ANSWER:
            if not normalized_claims:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "an answer requires at least one evidence-bound claim",
                )
        elif normalized_claims:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "clarification and limitation responses cannot carry affirmative claims",
            )
        if (
            response_kind is EngineeringAgentResponseKind.LIMITATION
            and not boundary
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "a limitation requires boundary evidence",
            )
        if (
            response_kind is EngineeringAgentResponseKind.CLARIFICATION
            and boundary
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "a clarification cannot claim an evidence boundary",
            )
        core = {
            "schema": "ENGINEERING_AGENT_DRAFT_PROPOSAL@2",
            "response_kind": response_kind.value,
            "content": content,
            "claims": tuple(
                {
                    "statement": claim.statement,
                    "support_observation_ids": tuple(
                        item.value for item in claim.support_observation_ids
                    ),
                    "support_citation_refs": claim.support_citation_refs,
                }
                for claim in normalized_claims
            ),
            "boundary_observation_ids": tuple(item.value for item in boundary),
        }
        return cls(
            response_kind=response_kind,
            content=content,
            claims=normalized_claims,
            boundary_observation_ids=boundary,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentWorkStateProposal:
    model_call_ref: str
    expected_context_digest: Digest
    expected_previous_work_state_digest: Digest | None
    goal: str
    response_language: str
    audience: str
    constraints: tuple[str, ...]
    resolved_referents: tuple[str, ...]
    accepted_correction_message_ids: tuple[StableId, ...]
    superseded_conclusion_refs: tuple[str, ...]
    hypotheses: tuple[str, ...]
    plan: tuple[str, ...]
    observation_ids: tuple[StableId, ...]
    open_items: tuple[str, ...]
    phase: EngineeringAgentWorkPhase
    action: EngineeringAgentToolActionProposal | None
    draft: EngineeringAgentDraftProposal | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        model_call_ref: str,
        expected_context_digest: Digest,
        expected_previous_work_state_digest: Digest | None,
        goal: str,
        response_language: str,
        audience: str,
        constraints: Sequence[str] = (),
        resolved_referents: Sequence[str] = (),
        accepted_correction_message_ids: Sequence[StableId] = (),
        superseded_conclusion_refs: Sequence[str] = (),
        hypotheses: Sequence[str] = (),
        plan: Sequence[str] = (),
        observation_ids: Sequence[StableId] = (),
        open_items: Sequence[str] = (),
        phase: EngineeringAgentWorkPhase,
        action: EngineeringAgentToolActionProposal | None = None,
        draft: EngineeringAgentDraftProposal | None = None,
    ) -> "EngineeringAgentWorkStateProposal":
        if (action is None) == (draft is None):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "an Agent step must propose exactly one tool action or response draft",
            )
        if action is not None and phase not in {
            EngineeringAgentWorkPhase.PLANNING,
            EngineeringAgentWorkPhase.INVESTIGATING,
            EngineeringAgentWorkPhase.REVISING,
        }:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "a tool action requires a non-terminal Work State phase",
            )
        if draft is not None and phase is not EngineeringAgentWorkPhase.RESPONSE_READY:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "a response draft requires RESPONSE_READY phase",
            )
        normalized_constraints = _unique_bounded_texts(constraints, "constraint")
        normalized_referents = _unique_bounded_texts(
            resolved_referents, "resolved referent"
        )
        normalized_superseded = _unique_texts(
            superseded_conclusion_refs, "superseded conclusion reference"
        )
        normalized_hypotheses = _unique_bounded_texts(hypotheses, "hypothesis")
        normalized_plan = _unique_bounded_texts(plan, "plan item")
        normalized_open = _unique_bounded_texts(open_items, "open item")
        corrections = tuple(accepted_correction_message_ids)
        observations = tuple(observation_ids)
        if len(corrections) != len(set(corrections)) or len(observations) != len(
            set(observations)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "correction and observation references must be unique",
            )
        model_call_ref = _text(model_call_ref, "Agent model call reference")
        goal = _bounded_text(goal, "current user goal")
        response_language = _text(response_language, "response language")
        audience = _bounded_text(audience, "audience")
        core = {
            "schema": "ENGINEERING_AGENT_WORK_STATE_PROPOSAL@1",
            "model_call_ref": model_call_ref,
            "expected_context_digest": expected_context_digest.value,
            "expected_previous_work_state_digest": (
                expected_previous_work_state_digest.value
                if expected_previous_work_state_digest is not None
                else None
            ),
            "goal": goal,
            "response_language": response_language,
            "audience": audience,
            "constraints": normalized_constraints,
            "resolved_referents": normalized_referents,
            "accepted_correction_message_ids": tuple(
                item.value for item in corrections
            ),
            "superseded_conclusion_refs": normalized_superseded,
            "hypotheses": normalized_hypotheses,
            "plan": normalized_plan,
            "observation_ids": tuple(item.value for item in observations),
            "open_items": normalized_open,
            "phase": phase.value,
            "action_digest": action.digest.value if action is not None else None,
            "draft_digest": draft.digest.value if draft is not None else None,
        }
        return cls(
            model_call_ref=model_call_ref,
            expected_context_digest=expected_context_digest,
            expected_previous_work_state_digest=expected_previous_work_state_digest,
            goal=goal,
            response_language=response_language,
            audience=audience,
            constraints=normalized_constraints,
            resolved_referents=normalized_referents,
            accepted_correction_message_ids=corrections,
            superseded_conclusion_refs=normalized_superseded,
            hypotheses=normalized_hypotheses,
            plan=normalized_plan,
            observation_ids=observations,
            open_items=normalized_open,
            phase=phase,
            action=action,
            draft=draft,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentWorkState:
    work_state_id: StableId
    conversation_id: StableId
    turn_id: StableId
    revision: Revision
    previous_digest: Digest | None
    context_digest: Digest
    goal: str
    response_language: str
    audience: str
    constraints: tuple[str, ...]
    resolved_referents: tuple[str, ...]
    accepted_correction_message_ids: tuple[StableId, ...]
    superseded_conclusion_refs: tuple[str, ...]
    hypotheses: tuple[str, ...]
    plan: tuple[str, ...]
    observation_ids: tuple[StableId, ...]
    open_items: tuple[str, ...]
    phase: EngineeringAgentWorkPhase
    review_input_digest: Digest | None
    proposal_digest: Digest
    digest: Digest


class EngineeringAgentWorkStateRepository(Protocol):
    """Application-owned store for only the last successfully committed state."""

    def load(self, conversation_id: StableId) -> EngineeringAgentWorkState | None: ...

    def commit(self, work_state: EngineeringAgentWorkState) -> None: ...


class InMemoryEngineeringAgentWorkStateRepository:
    """Share sealed Conversation state without sharing failed-attempt intermediates."""

    def __init__(self) -> None:
        self._states: dict[StableId, EngineeringAgentWorkState] = {}
        self._lock = Lock()

    def load(self, conversation_id: StableId) -> EngineeringAgentWorkState | None:
        if not isinstance(conversation_id, StableId):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Agent Work State lookup requires a Conversation ID",
            )
        with self._lock:
            return self._states.get(conversation_id)

    def commit(self, work_state: EngineeringAgentWorkState) -> None:
        if not isinstance(work_state, EngineeringAgentWorkState):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent Work State repository accepts only sealed Work State",
            )
        with self._lock:
            current = self._states.get(work_state.conversation_id)
            if current is not None and (
                work_state.work_state_id != current.work_state_id
                or work_state.revision.value <= current.revision.value
            ):
                raise DomainError(
                    ErrorCode.REVISION_CONFLICT,
                    "Agent Work State successor does not extend committed Conversation state",
                )
            self._states[work_state.conversation_id] = work_state


@dataclass(frozen=True, slots=True)
class EngineeringAgentReviewFinding:
    code: str
    message: str
    requires_evidence: bool
    claim_index: int | None = None

    @classmethod
    def create(
        cls,
        *,
        code: str,
        message: str,
        requires_evidence: bool,
        claim_index: int | None = None,
    ) -> "EngineeringAgentReviewFinding":
        if type(requires_evidence) is not bool:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "review Finding evidence requirement must be a boolean",
            )
        if claim_index is not None and (type(claim_index) is not int or claim_index < 0):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "review Finding claim index must be a non-negative integer",
            )
        return cls(
            code=_text(code, "review Finding code"),
            message=_bounded_text(message, "review Finding"),
            requires_evidence=requires_evidence,
            claim_index=claim_index,
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentRequirementCoverageAssessment:
    current_user_requirement: str
    coverage_summary: str
    disposition: EngineeringAgentRequirementCoverageDisposition
    finding_code: str | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        current_user_requirement: str,
        coverage_summary: str,
        disposition: EngineeringAgentRequirementCoverageDisposition,
        finding_code: str | None,
    ) -> "EngineeringAgentRequirementCoverageAssessment":
        if not isinstance(
            disposition,
            EngineeringAgentRequirementCoverageDisposition,
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "requirement coverage disposition is invalid",
            )
        finding_code = _optional_text(
            finding_code,
            "requirement coverage Finding code",
        )
        fully_addressed = (
            disposition
            is EngineeringAgentRequirementCoverageDisposition.FULLY_ADDRESSED
        )
        if fully_addressed != (finding_code is None):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "only missing or misaligned requirement coverage may bind a Finding code",
            )
        core = {
            "schema": "ENGINEERING_AGENT_REQUIREMENT_COVERAGE_ASSESSMENT@1",
            "current_user_requirement": _bounded_text(
                current_user_requirement,
                "current User requirement",
                maximum_bytes=48_000,
            ),
            "coverage_summary": _bounded_text(
                coverage_summary,
                "requirement coverage summary",
            ),
            "disposition": disposition.value,
            "finding_code": finding_code,
        }
        return cls(
            current_user_requirement=core["current_user_requirement"],
            coverage_summary=core["coverage_summary"],
            disposition=disposition,
            finding_code=finding_code,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentInvocation:
    request: EngineeringTurnExecutionRequest
    previous_work_state: EngineeringAgentWorkState | None
    observations: tuple["EngineeringAgentToolObservation", ...]
    review_findings: tuple[EngineeringAgentReviewFinding, ...]
    review_digest: Digest | None
    available_operations: tuple[EngineeringAgentToolOperation, ...]
    action_history: tuple[EngineeringAgentToolActionProposal, ...] = ()
    mode: EngineeringAgentInvocationMode = EngineeringAgentInvocationMode.STANDARD
    preissued_source_read_options: tuple[
        "EngineeringAgentSourceReadOption", ...
    ] = ()
    maximum_tool_actions: int = _DEFAULT_MAXIMUM_TOOL_ACTIONS
    reviewed_draft: "EngineeringAgentAnswerDraft | None" = None
    review_feedback_evidence_action_completed: bool = False


class EngineeringAgentDriver(Protocol):
    def propose(
        self, invocation: EngineeringAgentInvocation
    ) -> "EngineeringAgentWorkStateProposal | EngineeringAgentDriverModelResult": ...


@dataclass(frozen=True, slots=True)
class EngineeringAgentDriverModelResult:
    proposal: EngineeringAgentWorkStateProposal
    receipt: EngineeringAgentModelCallReceipt
    prior_receipts: tuple[EngineeringAgentModelCallReceipt, ...] = ()

    @classmethod
    def create(
        cls,
        *,
        proposal: EngineeringAgentWorkStateProposal,
        receipt: EngineeringAgentModelCallReceipt,
        prior_receipts: Sequence[EngineeringAgentModelCallReceipt] = (),
    ) -> "EngineeringAgentDriverModelResult":
        if (
            receipt.role is not EngineeringAgentModelRole.PRIMARY_AGENT
            or receipt.model_call_ref != proposal.model_call_ref
            or not _exact_model_receipt_sequence(
                (*tuple(prior_receipts), receipt),
                role=EngineeringAgentModelRole.PRIMARY_AGENT,
                terminal_must_succeed=True,
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent proposal does not bind its successful model call receipt",
            )
        return cls(
            proposal=proposal,
            receipt=receipt,
            prior_receipts=tuple(prior_receipts),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentToolRequest:
    tool_request_id: StableId
    turn_request_digest: Digest
    binding_digest: Digest
    work_state_digest: Digest
    turn_request: EngineeringTurnExecutionRequest
    action: EngineeringAgentToolActionProposal
    digest: Digest


@dataclass(frozen=True, slots=True)
class EngineeringAgentCitation:
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
    ) -> "EngineeringAgentCitation":
        core = {
            "schema": "ENGINEERING_AGENT_CITATION@1",
            "citation_ref": _text(citation_ref, "Citation reference"),
            "evidence_class": _text(evidence_class, "Citation evidence class"),
            "source_revision": _repository_revision(source_revision),
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
class EngineeringAgentSourceReadOption:
    """Current-Turn opaque read capability derived from prior exact evidence.

    The option carries no source content and is not evidence.  It only lets the
    current Turn ask the Source Broker to re-read a previously delivered full
    resource under the current Request, attempt, Profile, allowlist, revision,
    and resource fuses.
    """

    locator_reference: StableId
    locator: str
    resource_locator: str
    evidence_class: str
    source_revision: str
    modality: str
    content_digest: Digest
    origin_turn_id: StableId
    origin_citation_digest: Digest
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        locator_reference: StableId,
        locator: str,
        evidence_class: str,
        source_revision: str,
        modality: str,
        content_digest: Digest,
        origin_turn_id: StableId,
        origin_citation_digest: Digest,
    ) -> "EngineeringAgentSourceReadOption":
        if not isinstance(locator_reference, StableId) or not isinstance(
            origin_turn_id, StableId
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Source revalidation option identifiers are invalid",
            )
        if not isinstance(content_digest, Digest) or not isinstance(
            origin_citation_digest, Digest
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Source revalidation option digests are invalid",
            )
        locator = _bounded_text(
            locator, "Source revalidation locator", maximum_bytes=4_096
        )
        evidence_class = _text(
            evidence_class, "Source revalidation evidence class"
        )
        if evidence_class not in {
            "SOURCE",
            "REPOSITORY_DOCUMENT",
            "BUILD_CONFIGURATION",
            "TEST",
        }:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Source revalidation option needs a retrievable evidence class",
            )
        core = {
            "schema": "ENGINEERING_AGENT_SOURCE_READ_OPTION@1",
            "locator_reference": locator_reference.value,
            "locator": locator,
            "resource_locator": locator,
            "evidence_class": evidence_class,
            "source_revision": _repository_revision(source_revision),
            "modality": _text(modality, "Source revalidation modality"),
            "content_digest": content_digest.value,
            "origin_turn_id": origin_turn_id.value,
            "origin_citation_digest": origin_citation_digest.value,
        }
        return cls(
            locator_reference=locator_reference,
            locator=locator,
            resource_locator=locator,
            evidence_class=evidence_class,
            source_revision=core["source_revision"],
            modality=core["modality"],
            content_digest=content_digest,
            origin_turn_id=origin_turn_id,
            origin_citation_digest=origin_citation_digest,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentLedgerEntryReceipt:
    sequence: int
    kind: str
    subject_ref: str
    subject_digest: Digest
    references: tuple[str, ...]
    details: tuple[tuple[str, str], ...]
    previous_entry_digest: Digest | None
    source_entry_digest: Digest
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        sequence: int,
        kind: str,
        subject_ref: str,
        subject_digest: Digest,
        references: Sequence[str],
        details: Sequence[tuple[str, str]],
        previous_entry_digest: Digest | None,
        source_entry_digest: Digest,
    ) -> "EngineeringAgentLedgerEntryReceipt":
        if type(sequence) is not int or sequence < 1:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Ledger receipt sequence must be a positive integer",
            )
        normalized_references = tuple(
            _text(item, "Ledger receipt reference") for item in references
        )
        if len(normalized_references) != len(set(normalized_references)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Ledger receipt references must be unique",
            )
        normalized_details = tuple(
            sorted(
                (
                    _text(key, "Ledger receipt detail key"),
                    _bounded_text(
                        value,
                        "Ledger receipt detail value",
                        maximum_bytes=8_192,
                    ),
                )
                for key, value in details
            )
        )
        if len({key for key, _ in normalized_details}) != len(normalized_details):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Ledger receipt detail keys must be unique",
            )
        core = {
            "schema": "ENGINEERING_AGENT_LEDGER_ENTRY_RECEIPT@1",
            "sequence": sequence,
            "kind": _text(kind, "Ledger receipt kind"),
            "subject_ref": _text(subject_ref, "Ledger receipt subject"),
            "subject_digest": subject_digest.value,
            "references": normalized_references,
            "details": normalized_details,
            "previous_entry_digest": (
                previous_entry_digest.value
                if previous_entry_digest is not None
                else None
            ),
            "source_entry_digest": source_entry_digest.value,
        }
        return cls(
            sequence=sequence,
            kind=core["kind"],
            subject_ref=core["subject_ref"],
            subject_digest=subject_digest,
            references=normalized_references,
            details=normalized_details,
            previous_entry_digest=previous_entry_digest,
            source_entry_digest=source_entry_digest,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentToolAuthorityReceipt:
    authority_kind: EngineeringAgentToolAuthorityKind
    turn_request_digest: Digest
    tool_request_digest: Digest
    evidence_request_digest: Digest
    repository_revision: str
    evidence_digest: Digest
    ledger_ref: str
    ledger_generation: int
    ledger_parent_seal_digest: Digest | None
    ledger_prefix_digest: Digest
    ledger_entries: tuple[EngineeringAgentLedgerEntryReceipt, ...]
    citations: tuple[EngineeringAgentCitation, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        authority_kind: EngineeringAgentToolAuthorityKind,
        turn_request_digest: Digest,
        tool_request_digest: Digest,
        evidence_request_digest: Digest,
        repository_revision: str,
        evidence_digest: Digest,
        ledger_ref: str,
        ledger_generation: int,
        ledger_parent_seal_digest: Digest | None,
        ledger_prefix_digest: Digest,
        ledger_entries: Sequence[EngineeringAgentLedgerEntryReceipt],
        citations: Sequence[EngineeringAgentCitation] = (),
    ) -> "EngineeringAgentToolAuthorityReceipt":
        if not isinstance(authority_kind, EngineeringAgentToolAuthorityKind):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "tool authority receipt kind is invalid",
            )
        if (
            type(ledger_generation) is not int
            or ledger_generation < 1
            or (ledger_generation == 1) != (ledger_parent_seal_digest is None)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "tool authority Ledger generation and parent seal are invalid",
            )
        ledger_ref = _text(ledger_ref, "tool authority Ledger reference")
        try:
            StableId(ledger_ref)
        except ValueError as exc:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "tool authority Ledger reference must be a stable ID",
            ) from exc
        entries = tuple(ledger_entries)
        previous: Digest | None = None
        for sequence, entry in enumerate(entries, 1):
            expected = EngineeringAgentLedgerEntryReceipt.create(
                sequence=entry.sequence,
                kind=entry.kind,
                subject_ref=entry.subject_ref,
                subject_digest=entry.subject_digest,
                references=entry.references,
                details=entry.details,
                previous_entry_digest=entry.previous_entry_digest,
                source_entry_digest=entry.source_entry_digest,
            )
            source_entry_core = {
                "ledger_id": ledger_ref,
                "sequence": entry.sequence,
                "kind": entry.kind,
                "subject_id": entry.subject_ref,
                "subject_digest": entry.subject_digest.value,
                "references": entry.references,
                "details": entry.details,
                "previous_entry_digest": (
                    entry.previous_entry_digest.value
                    if entry.previous_entry_digest is not None
                    else None
                ),
            }
            if (
                entry != expected
                or entry.sequence != sequence
                or entry.previous_entry_digest != previous
                or entry.source_entry_digest
                != digest_of(["EVIDENCE_LEDGER_ENTRY@1", source_entry_core])
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "tool authority Ledger receipt chain is invalid",
                )
            previous = entry.source_entry_digest
        normalized_citations = tuple(citations)
        for citation in normalized_citations:
            expected_citation = EngineeringAgentCitation.create(
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
                    "tool authority Citation identity is invalid",
                )
        citation_refs = tuple(item.citation_ref for item in normalized_citations)
        if len(citation_refs) != len(set(citation_refs)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "tool authority Citation references must be unique",
            )
        expected_prefix_digest = digest_of(
            [
                "EVIDENCE_LEDGER_PREFIX@1",
                ledger_ref,
                evidence_request_digest.value,
                ledger_generation,
                (
                    ledger_parent_seal_digest.value
                    if ledger_parent_seal_digest is not None
                    else None
                ),
                tuple(item.source_entry_digest.value for item in entries),
            ]
        )
        if ledger_prefix_digest != expected_prefix_digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "tool authority Ledger prefix digest is invalid",
            )
        core = {
            "schema": "ENGINEERING_AGENT_TOOL_AUTHORITY_RECEIPT@1",
            "authority_kind": authority_kind.value,
            "turn_request_digest": turn_request_digest.value,
            "tool_request_digest": tool_request_digest.value,
            "evidence_request_digest": evidence_request_digest.value,
            "repository_revision": _repository_revision(repository_revision),
            "evidence_digest": evidence_digest.value,
            "ledger_ref": ledger_ref,
            "ledger_generation": ledger_generation,
            "ledger_parent_seal_digest": (
                ledger_parent_seal_digest.value
                if ledger_parent_seal_digest is not None
                else None
            ),
            "ledger_prefix_digest": ledger_prefix_digest.value,
            "ledger_entries": tuple(item.digest.value for item in entries),
            "citations": tuple(item.digest.value for item in normalized_citations),
        }
        return cls(
            authority_kind=authority_kind,
            turn_request_digest=turn_request_digest,
            tool_request_digest=tool_request_digest,
            evidence_request_digest=evidence_request_digest,
            repository_revision=core["repository_revision"],
            evidence_digest=evidence_digest,
            ledger_ref=core["ledger_ref"],
            ledger_generation=ledger_generation,
            ledger_parent_seal_digest=ledger_parent_seal_digest,
            ledger_prefix_digest=ledger_prefix_digest,
            ledger_entries=entries,
            citations=normalized_citations,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentToolEvidence:
    result_ref: str
    content: str
    disposition: EngineeringAgentEvidenceDisposition
    progress: bool
    citation_refs: tuple[str, ...]
    authority_receipt: EngineeringAgentToolAuthorityReceipt | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        tool_request_digest: Digest,
        result_ref: str,
        content: str,
        disposition: EngineeringAgentEvidenceDisposition,
        progress: bool,
        citation_refs: Sequence[str] = (),
        authority_receipt: EngineeringAgentToolAuthorityReceipt | None = None,
    ) -> "EngineeringAgentToolEvidence":
        if not isinstance(disposition, EngineeringAgentEvidenceDisposition):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "tool evidence disposition is invalid",
            )
        if type(progress) is not bool:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "tool progress must be a boolean",
            )
        citations = tuple(
            _text(item, "tool evidence Citation reference")
            for item in citation_refs
        )
        if len(citations) != len(set(citations)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "tool evidence Citation references must be unique",
            )
        if authority_receipt is not None:
            expected_receipt = EngineeringAgentToolAuthorityReceipt.create(
                authority_kind=authority_receipt.authority_kind,
                turn_request_digest=authority_receipt.turn_request_digest,
                tool_request_digest=authority_receipt.tool_request_digest,
                evidence_request_digest=authority_receipt.evidence_request_digest,
                repository_revision=authority_receipt.repository_revision,
                evidence_digest=authority_receipt.evidence_digest,
                ledger_ref=authority_receipt.ledger_ref,
                ledger_generation=authority_receipt.ledger_generation,
                ledger_parent_seal_digest=(
                    authority_receipt.ledger_parent_seal_digest
                ),
                ledger_prefix_digest=authority_receipt.ledger_prefix_digest,
                ledger_entries=authority_receipt.ledger_entries,
                citations=authority_receipt.citations,
            )
            available = {item.citation_ref for item in authority_receipt.citations}
            if (
                authority_receipt != expected_receipt
                or authority_receipt.tool_request_digest != tool_request_digest
                or not set(citations).issubset(available)
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "tool evidence authority receipt or Citation binding is invalid",
                )
        elif citations:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "tool evidence Citations require an authority receipt",
            )
        result_ref = _text(result_ref, "tool result reference")
        content = _observation_text(content)
        core = {
            "schema": "ENGINEERING_AGENT_TOOL_EVIDENCE@1",
            "tool_request_digest": tool_request_digest.value,
            "result_ref": result_ref,
            "content": content,
            "disposition": disposition.value,
            "progress": progress,
            "citation_refs": citations,
            "authority_receipt_digest": (
                authority_receipt.digest.value
                if authority_receipt is not None
                else None
            ),
        }
        return cls(
            result_ref=result_ref,
            content=content,
            disposition=disposition,
            progress=progress,
            citation_refs=citations,
            authority_receipt=authority_receipt,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentToolResult:
    tool_request_digest: Digest
    evidence: tuple[EngineeringAgentToolEvidence, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        tool_request_digest: Digest,
        result_ref: str,
        content: str,
        disposition: EngineeringAgentEvidenceDisposition,
        progress: bool,
        citation_refs: Sequence[str] = (),
        authority_receipt: EngineeringAgentToolAuthorityReceipt | None = None,
    ) -> "EngineeringAgentToolResult":
        return cls.create_many(
            tool_request_digest=tool_request_digest,
            evidence=(
                EngineeringAgentToolEvidence.create(
                    tool_request_digest=tool_request_digest,
                    result_ref=result_ref,
                    content=content,
                    disposition=disposition,
                    progress=progress,
                    citation_refs=citation_refs,
                    authority_receipt=authority_receipt,
                ),
            ),
        )

    @classmethod
    def create_many(
        cls,
        *,
        tool_request_digest: Digest,
        evidence: Sequence[EngineeringAgentToolEvidence],
    ) -> "EngineeringAgentToolResult":
        normalized = tuple(evidence)
        if not normalized:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "a tool result requires at least one evidence observation",
            )
        for item in normalized:
            expected = EngineeringAgentToolEvidence.create(
                tool_request_digest=tool_request_digest,
                result_ref=item.result_ref,
                content=item.content,
                disposition=item.disposition,
                progress=item.progress,
                citation_refs=item.citation_refs,
                authority_receipt=item.authority_receipt,
            )
            if item != expected:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "tool evidence identity is invalid",
                )
        references = tuple(item.result_ref for item in normalized)
        if len(references) != len(set(references)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "tool evidence result references must be unique",
            )
        core = {
            "schema": "ENGINEERING_AGENT_TOOL_RESULT@2",
            "tool_request_digest": tool_request_digest.value,
            "evidence": tuple(item.digest.value for item in normalized),
        }
        return cls(
            tool_request_digest=tool_request_digest,
            evidence=normalized,
            digest=digest_of(core),
        )


class EngineeringAgentToolPort(Protocol):
    def source_read_options(
        self, request: EngineeringTurnExecutionRequest
    ) -> tuple[EngineeringAgentSourceReadOption, ...]: ...

    def cognition_source_read_options(
        self,
        request: EngineeringTurnExecutionRequest,
        provenances: Sequence["CognitionProvenance"],
    ) -> tuple[EngineeringAgentCitation, ...]: ...

    def execute(
        self, request: EngineeringAgentToolRequest
    ) -> EngineeringAgentToolResult: ...


@dataclass(frozen=True, slots=True)
class EngineeringAgentToolObservation:
    observation_id: StableId
    tool_request_id: StableId
    operation: EngineeringAgentToolOperation
    result_ref: str
    content: str
    disposition: EngineeringAgentEvidenceDisposition
    progress: bool
    citation_refs: tuple[str, ...]
    authority_receipt: EngineeringAgentToolAuthorityReceipt | None
    tool_evidence_digest: Digest
    digest: Digest


@dataclass(frozen=True, slots=True)
class EngineeringAgentEvidencePackage:
    package_id: StableId
    turn_id: StableId
    origin_work_state_digest: Digest
    support_observations: tuple[EngineeringAgentToolObservation, ...]
    boundary_observations: tuple[EngineeringAgentToolObservation, ...]
    digest: Digest

    @property
    def support_observation_ids(self) -> tuple[StableId, ...]:
        return tuple(item.observation_id for item in self.support_observations)

    @property
    def boundary_observation_ids(self) -> tuple[StableId, ...]:
        return tuple(item.observation_id for item in self.boundary_observations)


@dataclass(frozen=True, slots=True)
class EngineeringAgentAnswerDraft:
    answer_id: StableId
    turn_id: StableId
    work_state_digest: Digest
    package_digest: Digest
    response_kind: EngineeringAgentResponseKind
    content: str
    claims: tuple[EngineeringAgentClaimProposal, ...]
    boundary_observation_ids: tuple[StableId, ...]
    digest: Digest


@dataclass(frozen=True, slots=True)
class EngineeringAgentDraftContentUnit:
    content_unit_index: int
    fragment: str
    inherited_context_fragments: tuple[str, ...]
    digest: Digest


@dataclass(frozen=True, slots=True)
class EngineeringAgentContentCoverageAssessment:
    content_unit_index: int
    disposition: EngineeringAgentContentCoverageDisposition
    claim_indices: tuple[int, ...]
    boundary_observation_ids: tuple[StableId, ...]
    finding_code: str | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        content_unit_index: int,
        disposition: EngineeringAgentContentCoverageDisposition,
        claim_indices: Sequence[int] = (),
        boundary_observation_ids: Sequence[StableId] = (),
        finding_code: str | None,
    ) -> "EngineeringAgentContentCoverageAssessment":
        if type(content_unit_index) is not int or content_unit_index < 0:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "content coverage unit index must be a non-negative integer",
            )
        if not isinstance(
            disposition,
            EngineeringAgentContentCoverageDisposition,
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "content coverage disposition is invalid",
            )
        claims = tuple(claim_indices)
        boundaries = tuple(boundary_observation_ids)
        if (
            any(type(item) is not int or item < 0 for item in claims)
            or claims != tuple(sorted(set(claims)))
            or any(not isinstance(item, StableId) for item in boundaries)
            or len(boundaries) != len(set(boundaries))
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "content coverage references must be unique and ordered",
            )
        finding_code = _optional_text(
            finding_code,
            "content coverage Finding code",
        )
        if disposition is EngineeringAgentContentCoverageDisposition.COVERED:
            valid_shape = bool(claims or boundaries) and finding_code is None
        elif (
            disposition
            is EngineeringAgentContentCoverageDisposition.BOUNDARY_REVIEW_DEFERRED
        ):
            valid_shape = not boundaries and finding_code is None
        elif (
            disposition
            is EngineeringAgentContentCoverageDisposition.NON_ASSERTIVE
        ):
            valid_shape = not claims and not boundaries and finding_code is None
        else:
            valid_shape = not claims and not boundaries and finding_code is not None
        if not valid_shape:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "content coverage disposition and reference shape are inconsistent",
            )
        core = {
            "schema": "ENGINEERING_AGENT_CONTENT_COVERAGE_ASSESSMENT@1",
            "content_unit_index": content_unit_index,
            "disposition": disposition.value,
            "claim_indices": claims,
            "boundary_observation_ids": tuple(item.value for item in boundaries),
            "finding_code": finding_code,
        }
        return cls(
            content_unit_index=content_unit_index,
            disposition=disposition,
            claim_indices=claims,
            boundary_observation_ids=boundaries,
            finding_code=finding_code,
            digest=digest_of(core),
        )


def project_engineering_agent_draft_content_units(
    content: str,
) -> tuple[EngineeringAgentDraftContentUnit, ...]:
    """Project every non-blank visible line with its Markdown container context."""

    content = _response_text(content)
    headings: dict[int, str] = {}
    standalone_label: str | None = None
    raw_units: list[tuple[str, tuple[str, ...]]] = []
    for raw_line in content.splitlines():
        normalized_fragment = raw_line.strip()
        if not normalized_fragment:
            continue
        fragment = _draft_content_unit_text(
            raw_line,
            "Draft content unit fragment",
            maximum_bytes=48_000,
        )
        heading_match = _MARKDOWN_HEADING_RE.fullmatch(normalized_fragment)
        if heading_match is not None:
            level = len(heading_match.group("marks"))
            inherited = tuple(
                headings[item]
                for item in sorted(headings)
                if item < level
            )
            raw_units.append((fragment, inherited))
            headings = {
                item: value for item, value in headings.items() if item < level
            }
            headings[level] = fragment
            standalone_label = None
            continue
        inherited = tuple(headings[item] for item in sorted(headings))
        if (
            _MARKDOWN_STANDALONE_LABEL_RE.fullmatch(normalized_fragment)
            is not None
        ):
            raw_units.append((fragment, inherited))
            standalone_label = fragment
            continue
        if standalone_label is not None:
            inherited = (*inherited, standalone_label)
        raw_units.append((fragment, inherited))

    if len(raw_units) > _MAXIMUM_DRAFT_CONTENT_UNITS:
        group_size = (
            len(raw_units) + _MAXIMUM_DRAFT_CONTENT_UNITS - 1
        ) // _MAXIMUM_DRAFT_CONTENT_UNITS
        grouped: list[tuple[str, tuple[str, ...]]] = []
        for start in range(0, len(raw_units), group_size):
            group = raw_units[start : start + group_size]
            inherited: list[str] = []
            for _, contexts in group:
                for context in contexts:
                    if context not in inherited:
                        inherited.append(context)
            grouped.append(
                ("\n".join(fragment for fragment, _ in group), tuple(inherited))
            )
        raw_units = grouped

    units: list[EngineeringAgentDraftContentUnit] = []
    for index, (fragment, inherited) in enumerate(raw_units):
        core = {
            "schema": "ENGINEERING_AGENT_DRAFT_CONTENT_UNIT@1",
            "content_unit_index": index,
            "fragment": _draft_content_unit_text(
                fragment,
                "Draft content unit fragment",
                maximum_bytes=48_000,
            ),
            "inherited_context_fragments": tuple(
                _draft_content_unit_text(
                    item,
                    "Draft content inherited context",
                )
                for item in inherited
            ),
        }
        units.append(
            EngineeringAgentDraftContentUnit(
                content_unit_index=index,
                fragment=core["fragment"],
                inherited_context_fragments=core[
                    "inherited_context_fragments"
                ],
                digest=digest_of(core),
            )
        )
    return tuple(units)


def _draft_content_unit_inline_code_anchors(
    content_unit: EngineeringAgentDraftContentUnit,
) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(
            match.group(1)
            for match in _MARKDOWN_INLINE_CODE_SPAN_RE.finditer(
                content_unit.fragment
            )
            if match.group(1).strip()
        )
    )


def _draft_assertion_replica_text(value: str) -> str:
    """Remove only Markdown presentation bytes before exact assertion matching."""

    normalized_lines: list[str] = []
    for line in value.splitlines():
        normalized = _MARKDOWN_LIST_ITEM_PREFIX_RE.sub(
            "",
            line.strip(),
            count=1,
        )
        normalized = _MARKDOWN_INLINE_CODE_SPAN_RE.sub(
            lambda match: match.group(1),
            normalized,
        )
        normalized = _MARKDOWN_PAIRED_BOLD_SPAN_RE.sub(
            lambda match: match.group("content"),
            normalized,
        )
        if normalized:
            normalized_lines.append(normalized)
    return re.sub(r"\s+", " ", " ".join(normalized_lines)).strip()


def engineering_agent_content_coverage_unmatched_claim_assertion_replicas(
    draft: EngineeringAgentAnswerDraft,
    content_unit: EngineeringAgentDraftContentUnit,
    assessment: EngineeringAgentContentCoverageAssessment,
) -> tuple[str, ...]:
    """Return a visible assertion absent in full from every mapped Claim.

    This is a conservative lexical floor, not a factual or semantic proof. It
    applies only when a Reviewer maps the unit to one or more affirmative
    Claims; pure Boundary coverage remains a semantic Review responsibility.
    """

    if (
        not isinstance(draft, EngineeringAgentAnswerDraft)
        or assessment.disposition
        is not EngineeringAgentContentCoverageDisposition.COVERED
        or not assessment.claim_indices
    ):
        return ()
    assertion = _draft_assertion_replica_text(content_unit.fragment)
    if not assertion:
        return ()
    claim_texts = tuple(
        _draft_assertion_replica_text(draft.claims[index].statement)
        for index in assessment.claim_indices
        if 0 <= index < len(draft.claims)
    )
    if any(assertion in statement for statement in claim_texts):
        return ()
    return (assertion,)


def engineering_agent_content_coverage_unmatched_inline_code_anchors(
    package: EngineeringAgentEvidencePackage,
    draft: EngineeringAgentAnswerDraft,
    content_unit: EngineeringAgentDraftContentUnit,
    assessment: EngineeringAgentContentCoverageAssessment,
) -> tuple[str, ...]:
    """Return exact visible technical anchors absent from the mapped references."""

    if (
        assessment.disposition
        is not EngineeringAgentContentCoverageDisposition.COVERED
    ):
        return ()
    anchors = _draft_content_unit_inline_code_anchors(content_unit)
    if not anchors:
        return ()
    reference_texts = [
        draft.claims[index].statement
        for index in assessment.claim_indices
        if 0 <= index < len(draft.claims)
    ]
    boundary_by_id = {
        item.observation_id: item for item in package.boundary_observations
    }
    reference_texts.extend(
        boundary_by_id[observation_id].content
        for observation_id in assessment.boundary_observation_ids
        if observation_id in boundary_by_id
    )
    return tuple(
        anchor
        for anchor in anchors
        if not any(anchor in reference for reference in reference_texts)
    )


def engineering_agent_content_coverage_nonassertive_inline_code_anchors(
    content_unit: EngineeringAgentDraftContentUnit,
    assessment: EngineeringAgentContentCoverageAssessment,
) -> tuple[str, ...]:
    """Return anchors that make a non-structural unit ineligible as non-assertive."""

    if (
        assessment.disposition
        is not EngineeringAgentContentCoverageDisposition.NON_ASSERTIVE
    ):
        return ()
    fragment = content_unit.fragment.strip()
    if (
        _MARKDOWN_HEADING_RE.fullmatch(fragment) is not None
        or _MARKDOWN_STANDALONE_LABEL_RE.fullmatch(fragment) is not None
    ):
        return ()
    return _draft_content_unit_inline_code_anchors(content_unit)


def engineering_agent_content_coverage_nonassertive_body_fragments(
    draft: EngineeringAgentAnswerDraft,
    content_unit: EngineeringAgentDraftContentUnit,
    assessment: EngineeringAgentContentCoverageAssessment,
) -> tuple[str, ...]:
    """Return ordinary Answer/Limitation body mislabeled as non-assertive."""

    if (
        not isinstance(draft, EngineeringAgentAnswerDraft)
        or assessment.disposition
        is not EngineeringAgentContentCoverageDisposition.NON_ASSERTIVE
        or draft.response_kind
        is EngineeringAgentResponseKind.CLARIFICATION
    ):
        return ()
    fragment = content_unit.fragment.strip()
    if (
        _MARKDOWN_HEADING_RE.fullmatch(fragment) is not None
        or _MARKDOWN_STANDALONE_LABEL_RE.fullmatch(fragment) is not None
    ):
        return ()
    normalized = _draft_assertion_replica_text(fragment)
    return (normalized,) if normalized else ()


@dataclass(frozen=True, slots=True)
class EngineeringAgentEvidenceBoundaryChallenge:
    challenge_id: StableId
    claim_index: int
    support_observation_id: StableId
    source_locator: str
    call_expression: str
    receiver_declared_type: str | None
    cited_implementation_observation_ids: tuple[StableId, ...]
    package_implementation_observation_ids: tuple[StableId, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        claim_index: int,
        support_observation_id: StableId,
        source_locator: str,
        call_expression: str,
        receiver_declared_type: str | None,
        cited_implementation_observation_ids: Sequence[StableId] = (),
        package_implementation_observation_ids: Sequence[StableId] = (),
    ) -> "EngineeringAgentEvidenceBoundaryChallenge":
        if type(claim_index) is not int or claim_index < 0:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "evidence-boundary challenge Claim index is invalid",
            )
        cited = tuple(cited_implementation_observation_ids)
        package = tuple(package_implementation_observation_ids)
        if (
            len(cited) != len(set(cited))
            or len(package) != len(set(package))
            or not set(cited).issubset(package)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "evidence-boundary challenge implementation references are invalid",
            )
        core = {
            "schema": "ENGINEERING_AGENT_EVIDENCE_BOUNDARY_CHALLENGE@1",
            "claim_index": claim_index,
            "support_observation_id": support_observation_id.value,
            "source_locator": _text(source_locator, "challenge Source locator"),
            "call_expression": _text(call_expression, "challenge call expression"),
            "receiver_declared_type": (
                _text(receiver_declared_type, "challenge receiver type")
                if receiver_declared_type is not None
                else None
            ),
            "cited_implementation_observation_ids": tuple(
                item.value for item in cited
            ),
            "package_implementation_observation_ids": tuple(
                item.value for item in package
            ),
        }
        challenge_digest = digest_of(core)
        return cls(
            challenge_id=StableId(
                f"evidence_challenge_{challenge_digest.value[-32:]}"
            ),
            claim_index=claim_index,
            support_observation_id=support_observation_id,
            source_locator=core["source_locator"],
            call_expression=core["call_expression"],
            receiver_declared_type=core["receiver_declared_type"],
            cited_implementation_observation_ids=cited,
            package_implementation_observation_ids=package,
            digest=challenge_digest,
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentEvidenceBoundaryAssessment:
    challenge_id: StableId
    evidence_boundary: str
    draft_scope: str
    draft_semantic_scopes: tuple[EngineeringAgentClaimSemanticScope, ...]
    disposition: EngineeringAgentEvidenceBoundaryAssessmentDisposition
    finding_code: str | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        challenge_id: StableId,
        evidence_boundary: str,
        draft_scope: str,
        draft_semantic_scopes: Sequence[EngineeringAgentClaimSemanticScope],
        disposition: EngineeringAgentEvidenceBoundaryAssessmentDisposition,
        finding_code: str | None,
    ) -> "EngineeringAgentEvidenceBoundaryAssessment":
        if not isinstance(
            disposition,
            EngineeringAgentEvidenceBoundaryAssessmentDisposition,
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "evidence-boundary assessment disposition is invalid",
            )
        semantic_scopes = tuple(draft_semantic_scopes)
        if (
            not semantic_scopes
            or len(semantic_scopes) != len(set(semantic_scopes))
            or any(
                not isinstance(item, EngineeringAgentClaimSemanticScope)
                for item in semantic_scopes
            )
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "evidence-boundary assessment requires unique typed Draft semantic scopes",
            )
        finding_code = _optional_text(
            finding_code,
            "evidence-boundary assessment Finding code",
        )
        within_boundary = (
            disposition
            is EngineeringAgentEvidenceBoundaryAssessmentDisposition.WITHIN_CALLER_EVIDENCE
        )
        if (within_boundary and finding_code is not None) or (
            not within_boundary and finding_code is None
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "only an exceeded evidence boundary may bind a Finding code",
            )
        core = {
            "schema": "ENGINEERING_AGENT_EVIDENCE_BOUNDARY_ASSESSMENT@2",
            "challenge_id": challenge_id.value,
            "evidence_boundary": _bounded_text(
                evidence_boundary,
                "assessment evidence boundary",
            ),
            "draft_scope": _bounded_text(draft_scope, "assessment Draft scope"),
            "draft_semantic_scopes": tuple(
                item.value for item in semantic_scopes
            ),
            "disposition": disposition.value,
            "finding_code": finding_code,
        }
        return cls(
            challenge_id=challenge_id,
            evidence_boundary=core["evidence_boundary"],
            draft_scope=core["draft_scope"],
            draft_semantic_scopes=semantic_scopes,
            disposition=disposition,
            finding_code=finding_code,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentBoundaryRelevanceChallenge:
    challenge_id: StableId
    kind: EngineeringAgentBoundaryRelevanceChallengeKind
    boundary_observation_id: StableId
    resolving_support_observation_ids: tuple[StableId, ...]
    draft_declared_boundary_reference: bool
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        kind: EngineeringAgentBoundaryRelevanceChallengeKind,
        boundary_observation_id: StableId,
        resolving_support_observation_ids: Sequence[StableId],
        draft_declared_boundary_reference: bool,
    ) -> "EngineeringAgentBoundaryRelevanceChallenge":
        resolving = tuple(resolving_support_observation_ids)
        if not isinstance(kind, EngineeringAgentBoundaryRelevanceChallengeKind):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "boundary relevance challenge kind is invalid",
            )
        if len(resolving) != len(set(resolving)) or (
            kind
            is EngineeringAgentBoundaryRelevanceChallengeKind.RESOLVED_ACQUISITION
        ) != bool(resolving):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "only a resolved-acquisition challenge requires unique resolving support",
            )
        if type(draft_declared_boundary_reference) is not bool:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "boundary relevance challenge Draft reference flag is invalid",
            )
        core = {
            "schema": "ENGINEERING_AGENT_BOUNDARY_RELEVANCE_CHALLENGE@3",
            "kind": kind.value,
            "boundary_observation_id": boundary_observation_id.value,
            "resolving_support_observation_ids": tuple(
                item.value for item in resolving
            ),
            "draft_declared_boundary_reference": (
                draft_declared_boundary_reference
            ),
        }
        challenge_digest = digest_of(core)
        return cls(
            challenge_id=StableId(
                f"boundary_challenge_{challenge_digest.value[-32:]}"
            ),
            kind=kind,
            boundary_observation_id=boundary_observation_id,
            resolving_support_observation_ids=resolving,
            draft_declared_boundary_reference=(
                draft_declared_boundary_reference
            ),
            digest=challenge_digest,
        )


def _draft_disclosure_presentation_text(value: str) -> str:
    """Ignore only Markdown inline-code delimiter bytes for fragment matching."""

    return value.replace("`", "")


@dataclass(frozen=True, slots=True)
class EngineeringAgentBoundaryRelevanceAssessment:
    challenge_id: StableId
    user_requirement: str
    boundary_scope: str
    draft_disclosed_fragments: tuple[str, ...]
    disposition: EngineeringAgentBoundaryRelevanceAssessmentDisposition
    finding_code: str | None
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        challenge_id: StableId,
        user_requirement: str,
        boundary_scope: str,
        disposition: EngineeringAgentBoundaryRelevanceAssessmentDisposition,
        finding_code: str | None,
        draft_disclosed_fragments: Sequence[str] = (),
    ) -> "EngineeringAgentBoundaryRelevanceAssessment":
        if not isinstance(
            disposition,
            EngineeringAgentBoundaryRelevanceAssessmentDisposition,
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "boundary relevance assessment disposition is invalid",
            )
        finding_code = _optional_text(
            finding_code,
            "boundary relevance assessment Finding code",
        )
        requires_finding = (
            disposition in _BOUNDARY_RELEVANCE_AUDIT_ONLY_DISPOSITIONS
        )
        if requires_finding and finding_code is None:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "an audit-only boundary relevance assessment requires a "
                "Finding code",
            )
        if not requires_finding and finding_code is not None:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "a non-audit-only boundary relevance assessment must not "
                "bind a Finding code",
            )
        if isinstance(draft_disclosed_fragments, (str, bytes)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "boundary relevance Draft disclosed fragments must be a sequence",
            )
        disclosed_fragments = tuple(
            _bounded_text(
                item,
                "boundary relevance Draft disclosed fragment",
            )
            for item in draft_disclosed_fragments
        )
        if len(disclosed_fragments) > 16:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "boundary relevance Draft disclosed fragments exceed the maximum",
            )
        presentation_normalized_fragments = tuple(
            _draft_disclosure_presentation_text(item)
            for item in disclosed_fragments
        )
        if any(not item.strip() for item in presentation_normalized_fragments):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "boundary relevance Draft disclosed fragments cannot contain only inline-code delimiters",
            )
        if (
            len(set(presentation_normalized_fragments))
            != len(presentation_normalized_fragments)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "boundary relevance Draft disclosed fragments must be presentation-unique",
            )
        core = {
            "schema": "ENGINEERING_AGENT_BOUNDARY_RELEVANCE_ASSESSMENT@4",
            "challenge_id": challenge_id.value,
            "user_requirement": _bounded_text(
                user_requirement,
                "boundary relevance user requirement",
            ),
            "boundary_scope": _bounded_text(
                boundary_scope,
                "boundary relevance scope",
            ),
            "draft_disclosed_fragments": disclosed_fragments,
            "disposition": disposition.value,
            "finding_code": finding_code,
        }
        return cls(
            challenge_id=challenge_id,
            user_requirement=core["user_requirement"],
            boundary_scope=core["boundary_scope"],
            draft_disclosed_fragments=disclosed_fragments,
            disposition=disposition,
            finding_code=finding_code,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentReviewRequest:
    turn_request: EngineeringTurnExecutionRequest
    work_state: EngineeringAgentWorkState
    package: EngineeringAgentEvidencePackage
    draft: EngineeringAgentAnswerDraft
    focus: EngineeringAgentReviewFocus = EngineeringAgentReviewFocus.COMPREHENSIVE


@dataclass(frozen=True, slots=True)
class EngineeringAgentReviewProposal:
    model_call_ref: str
    decision: EngineeringAgentReviewDecision
    findings: tuple[EngineeringAgentReviewFinding, ...]
    focus: EngineeringAgentReviewFocus
    requirement_coverage_assessment: (
        EngineeringAgentRequirementCoverageAssessment
    )
    content_coverage_assessments: tuple[
        EngineeringAgentContentCoverageAssessment, ...
    ]
    evidence_boundary_assessments: tuple[
        EngineeringAgentEvidenceBoundaryAssessment, ...
    ]
    boundary_relevance_assessments: tuple[
        EngineeringAgentBoundaryRelevanceAssessment, ...
    ]

    @classmethod
    def create(
        cls,
        *,
        model_call_ref: str,
        decision: EngineeringAgentReviewDecision,
        findings: Sequence[EngineeringAgentReviewFinding] = (),
        focus: EngineeringAgentReviewFocus = EngineeringAgentReviewFocus.COMPREHENSIVE,
        requirement_coverage_assessment: EngineeringAgentRequirementCoverageAssessment,
        content_coverage_assessments: Sequence[
            EngineeringAgentContentCoverageAssessment
        ] = (),
        evidence_boundary_assessments: Sequence[
            EngineeringAgentEvidenceBoundaryAssessment
        ] = (),
        boundary_relevance_assessments: Sequence[
            EngineeringAgentBoundaryRelevanceAssessment
        ] = (),
    ) -> "EngineeringAgentReviewProposal":
        if not isinstance(decision, EngineeringAgentReviewDecision):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer decision is invalid",
            )
        normalized = tuple(findings)
        content_assessments = tuple(content_coverage_assessments)
        assessments = tuple(evidence_boundary_assessments)
        relevance_assessments = tuple(boundary_relevance_assessments)
        if any(not isinstance(item, EngineeringAgentReviewFinding) for item in normalized):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer Findings must use the typed contract",
            )
        if (
            not isinstance(focus, EngineeringAgentReviewFocus)
            or not isinstance(
                requirement_coverage_assessment,
                EngineeringAgentRequirementCoverageAssessment,
            )
            or any(
                not isinstance(
                    item,
                    EngineeringAgentContentCoverageAssessment,
                )
                for item in content_assessments
            )
            or any(
                not isinstance(
                    item,
                    EngineeringAgentEvidenceBoundaryAssessment,
                )
                for item in assessments
            )
            or any(
                not isinstance(
                    item,
                    EngineeringAgentBoundaryRelevanceAssessment,
                )
                for item in relevance_assessments
            )
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer focus or evidence-boundary assessments are invalid",
            )
        if (
            focus is EngineeringAgentReviewFocus.COMPREHENSIVE
            and (assessments or relevance_assessments)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "comprehensive Review cannot pre-disposition evidence-boundary challenges",
            )
        if (
            focus is EngineeringAgentReviewFocus.COMPREHENSIVE
            and any(item.boundary_observation_ids for item in content_assessments)
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "comprehensive content coverage cannot expose redacted Boundary IDs",
            )
        if (
            focus is EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE
            and any(
                item.disposition
                is EngineeringAgentContentCoverageDisposition.BOUNDARY_REVIEW_DEFERRED
                for item in content_assessments
            )
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "focused content coverage cannot defer exact Boundary coverage",
            )
        if decision is EngineeringAgentReviewDecision.APPROVED and (
            requirement_coverage_assessment.disposition
            is not EngineeringAgentRequirementCoverageDisposition.FULLY_ADDRESSED
            or any(
                item.disposition
                is EngineeringAgentContentCoverageDisposition.DEFECT
                for item in content_assessments
            )
            or any(
                item.disposition
                is not EngineeringAgentEvidenceBoundaryAssessmentDisposition.WITHIN_CALLER_EVIDENCE
                for item in assessments
            )
            or any(
                not engineering_agent_boundary_relevance_assessment_is_closed(item)
                for item in relevance_assessments
            )
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "an approved Review cannot leave an evidence-boundary challenge open",
            )
        if decision is EngineeringAgentReviewDecision.APPROVED and normalized:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "an approved Review cannot carry Findings",
            )
        if decision is EngineeringAgentReviewDecision.FINDINGS and not normalized:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "a non-approved Review requires Findings",
            )
        finding_by_code = {item.code: item for item in normalized}
        if len(finding_by_code) != len(normalized):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer Finding codes must be unique",
            )
        for assessment in relevance_assessments:
            if (
                assessment.disposition
                not in _BOUNDARY_RELEVANCE_AUDIT_ONLY_DISPOSITIONS
            ):
                continue
            finding = finding_by_code.get(assessment.finding_code or "")
            if (
                finding is None
                or finding.claim_index is not None
                or finding.requires_evidence
            ):
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "an audit-only boundary assessment requires a global no-evidence Finding",
                )
        if (
            requirement_coverage_assessment.disposition
            is EngineeringAgentRequirementCoverageDisposition.MATERIAL_REQUIREMENT_MISSING_OR_MISALIGNED
        ):
            finding = finding_by_code.get(
                requirement_coverage_assessment.finding_code or ""
            )
            if finding is None or finding.claim_index is not None:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "missing or misaligned requirement coverage requires a global Finding",
                )
        for assessment in content_assessments:
            if (
                assessment.disposition
                is EngineeringAgentContentCoverageDisposition.DEFECT
                and assessment.finding_code not in finding_by_code
            ):
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "a defective content unit requires a bound Finding",
                )
        return cls(
            model_call_ref=_text(model_call_ref, "Reviewer model call reference"),
            decision=decision,
            findings=normalized,
            focus=focus,
            requirement_coverage_assessment=(
                requirement_coverage_assessment
            ),
            content_coverage_assessments=content_assessments,
            evidence_boundary_assessments=assessments,
            boundary_relevance_assessments=relevance_assessments,
        )


class EngineeringAgentReviewer(Protocol):
    def review(
        self, request: EngineeringAgentReviewRequest
    ) -> "EngineeringAgentReviewProposal | EngineeringAgentReviewerModelResult": ...


@dataclass(frozen=True, slots=True)
class EngineeringAgentReviewerModelResult:
    proposal: EngineeringAgentReviewProposal
    receipt: EngineeringAgentModelCallReceipt
    prior_receipts: tuple[EngineeringAgentModelCallReceipt, ...] = ()

    @classmethod
    def create(
        cls,
        *,
        proposal: EngineeringAgentReviewProposal,
        receipt: EngineeringAgentModelCallReceipt,
        prior_receipts: Sequence[EngineeringAgentModelCallReceipt] = (),
    ) -> "EngineeringAgentReviewerModelResult":
        if (
            receipt.role is not EngineeringAgentModelRole.INDEPENDENT_REVIEWER
            or receipt.model_call_ref != proposal.model_call_ref
            or not _exact_model_receipt_sequence(
                (*tuple(prior_receipts), receipt),
                role=EngineeringAgentModelRole.INDEPENDENT_REVIEWER,
                terminal_must_succeed=True,
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Reviewer proposal does not bind its successful model call receipt",
            )
        return cls(
            proposal=proposal,
            receipt=receipt,
            prior_receipts=tuple(prior_receipts),
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentReview:
    review_id: StableId
    turn_id: StableId
    work_state_digest: Digest
    package_digest: Digest
    answer_digest: Digest
    decision: EngineeringAgentReviewDecision
    findings: tuple[EngineeringAgentReviewFinding, ...]
    focus: EngineeringAgentReviewFocus
    requirement_coverage_assessment: (
        EngineeringAgentRequirementCoverageAssessment
    )
    content_coverage_assessments: tuple[
        EngineeringAgentContentCoverageAssessment, ...
    ]
    evidence_boundary_assessments: tuple[
        EngineeringAgentEvidenceBoundaryAssessment, ...
    ]
    boundary_relevance_assessments: tuple[
        EngineeringAgentBoundaryRelevanceAssessment, ...
    ]
    model_call_ref: str
    digest: Digest


@dataclass(frozen=True, slots=True)
class EngineeringAgentDraftBoundaryProjection:
    reportable_boundary_observation_ids: tuple[StableId, ...]
    resolved_acquisition_candidate_observation_ids: tuple[StableId, ...]
    digest: Digest


@dataclass(frozen=True, slots=True)
class _EngineeringAgentJavaSourceItem:
    observation_id: StableId
    locator: str
    content: str


_JAVA_NON_CODE_RE = re.compile(
    r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*.*?\*/',
    re.DOTALL,
)
_JAVA_FIELD_RE = re.compile(
    r"(?m)^[ \t]*(?:public|protected|private)[ \t]+"
    r"(?:(?:static|final|volatile|transient)[ \t]+)*"
    r"(?P<type>[A-Za-z_$][A-Za-z0-9_$.]*(?:\s*<[^;=\n]+>)?(?:\[\])?)"
    r"[ \t]+(?P<name>[A-Za-z_$][A-Za-z0-9_$]*)[ \t]*(?:[;=])"
)
_JAVA_RECEIVER_CALL_RE = re.compile(
    r"(?P<receiver>[A-Za-z_$][A-Za-z0-9_$]*"
    r"(?:\s*\([^()\n;{}]*\))?)\s*\.\s*"
    r"(?P<method>[A-Za-z_$][A-Za-z0-9_$]*)\s*\("
)
_SOURCE_LINE_LOCATOR_RE = re.compile(
    r"^(?P<resource>.+):L[1-9][0-9]*(?:-[1-9][0-9]*)?$"
)


def project_engineering_agent_draft_boundaries(
    observations: Sequence[EngineeringAgentToolObservation],
) -> EngineeringAgentDraftBoundaryProjection:
    """Separate retained audit diagnostics from Draft-reportable boundaries.

    A Source Search boundary becomes a relevance-challenge candidate once a
    later full Source Read consumes a locator issued by that exact search.  The
    immutable Package and copy domain retain it because the User may have asked
    for the acquisition diagnostic itself; a focused Review decides materiality.
    """

    normalized = tuple(observations)
    support_sequence = tuple(
        item
        for item in normalized
        if item.disposition is EngineeringAgentEvidenceDisposition.SUPPORT
    )
    support_position = {
        item.observation_id: index
        for index, item in enumerate(support_sequence)
    }
    search_support_by_request: dict[
        StableId, EngineeringAgentToolObservation
    ] = {
        item.tool_request_id: item
        for item in support_sequence
        if item.operation is EngineeringAgentToolOperation.SOURCE_SEARCH
        and item.citation_refs
    }
    resolved_candidates: set[StableId] = set()
    full_reads = tuple(
        (support_position[observation.observation_id], observation)
        for observation in support_sequence
        if observation.operation is EngineeringAgentToolOperation.SOURCE_READ
    )
    for item in normalized:
        if (
            item.operation is not EngineeringAgentToolOperation.SOURCE_SEARCH
            or item.disposition
            is not EngineeringAgentEvidenceDisposition.BOUNDARY
        ):
            continue
        paired_support = search_support_by_request.get(item.tool_request_id)
        if paired_support is None:
            continue
        search_position = support_position[paired_support.observation_id]
        if any(
            read_position > search_position
            and _engineering_agent_search_is_resolved_by_full_read(
                search_support=paired_support,
                read_support=read_support,
            )
            for read_position, read_support in full_reads
        ):
            resolved_candidates.add(item.observation_id)
    boundary_ids = tuple(
        item.observation_id
        for item in normalized
        if item.disposition is EngineeringAgentEvidenceDisposition.BOUNDARY
    )
    reportable = boundary_ids
    candidates = tuple(
        item for item in boundary_ids if item in resolved_candidates
    )
    core = {
        "schema": "ENGINEERING_AGENT_DRAFT_BOUNDARY_PROJECTION@1",
        "reportable_boundary_observation_ids": tuple(
            item.value for item in reportable
        ),
        "resolved_acquisition_candidate_observation_ids": tuple(
            item.value for item in candidates
        ),
    }
    return EngineeringAgentDraftBoundaryProjection(
        reportable_boundary_observation_ids=reportable,
        resolved_acquisition_candidate_observation_ids=candidates,
        digest=digest_of(core),
    )


def _engineering_agent_full_source_read_citation_refs(
    observation: EngineeringAgentToolObservation,
) -> tuple[str, ...]:
    try:
        payload = json.loads(observation.content)
    except (TypeError, json.JSONDecodeError):
        return ()
    retrieval = payload.get("retrieval_result")
    if not isinstance(retrieval, dict):
        return ()
    raw_items = retrieval.get("items")
    if not isinstance(raw_items, list):
        return ()
    authorized = set(observation.citation_refs)
    references: list[str] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        reference = item.get("locator_reference")
        if (
            item.get("coverage_complete") is True
            and item.get("modality") == "EXACT_STATIC_SOURCE_TEXT"
            and isinstance(reference, str)
            and reference in authorized
            and reference not in references
        ):
            references.append(reference)
    return tuple(references)


def _engineering_agent_retrieval_resource_locators(
    observation: EngineeringAgentToolObservation,
    *,
    full_resource_required: bool,
) -> tuple[str, ...]:
    """Return trusted resource identities independent of one-use locator IDs."""

    expected_operation = (
        EngineeringAgentToolOperation.SOURCE_READ
        if full_resource_required
        else EngineeringAgentToolOperation.SOURCE_SEARCH
    )
    expected_modality = (
        "EXACT_STATIC_SOURCE_TEXT"
        if full_resource_required
        else "LITERAL_TEXT_SEARCH_HIT"
    )
    if observation.operation is not expected_operation:
        return ()

    try:
        payload = json.loads(observation.content)
    except (TypeError, json.JSONDecodeError):
        return ()
    retrieval = payload.get("retrieval_result")
    if not isinstance(retrieval, dict):
        return ()
    raw_items = retrieval.get("items")
    if not isinstance(raw_items, list):
        return ()
    authorized = set(observation.citation_refs)
    resources: list[str] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        reference = item.get("locator_reference")
        locator = item.get("locator")
        if (
            item.get("modality") != expected_modality
            or (
                full_resource_required
                and item.get("coverage_complete") is not True
            )
            or not isinstance(reference, str)
            or reference not in authorized
            or not isinstance(locator, str)
        ):
            continue
        line_match = _SOURCE_LINE_LOCATOR_RE.fullmatch(locator)
        resource = (
            line_match.group("resource") if line_match is not None else locator
        )
        if resource not in resources:
            resources.append(resource)
    return tuple(resources)


def _engineering_agent_search_is_resolved_by_full_read(
    *,
    search_support: EngineeringAgentToolObservation,
    read_support: EngineeringAgentToolObservation,
) -> bool:
    issued_references = set(
        _engineering_agent_search_citation_refs(search_support)
    )
    read_references = set(
        _engineering_agent_full_source_read_citation_refs(read_support)
    )
    if issued_references.intersection(read_references):
        return True
    issued_resources = set(
        _engineering_agent_retrieval_resource_locators(
            search_support,
            full_resource_required=False,
        )
    )
    read_resources = set(
        _engineering_agent_retrieval_resource_locators(
            read_support,
            full_resource_required=True,
        )
    )
    return bool(issued_resources.intersection(read_resources))


def _engineering_agent_search_citation_refs(
    observation: EngineeringAgentToolObservation,
) -> tuple[str, ...]:
    if observation.operation is not EngineeringAgentToolOperation.SOURCE_SEARCH:
        return ()
    try:
        payload = json.loads(observation.content)
    except (TypeError, json.JSONDecodeError):
        return ()
    retrieval = payload.get("retrieval_result")
    raw_items = retrieval.get("items") if isinstance(retrieval, dict) else None
    if not isinstance(raw_items, list):
        return ()
    authorized = set(observation.citation_refs)
    references: list[str] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        reference = item.get("locator_reference")
        if (
            item.get("modality") == "LITERAL_TEXT_SEARCH_HIT"
            and isinstance(reference, str)
            and reference in authorized
            and reference not in references
        ):
            references.append(reference)
    return tuple(references)


def project_engineering_agent_boundary_relevance_challenges(
    package: EngineeringAgentEvidencePackage,
    draft: EngineeringAgentAnswerDraft,
) -> tuple[EngineeringAgentBoundaryRelevanceChallenge, ...]:
    observations = (
        *package.support_observations,
        *package.boundary_observations,
    )
    projection = project_engineering_agent_draft_boundaries(observations)
    search_support_by_request = {
        item.tool_request_id: item
        for item in package.support_observations
        if item.operation is EngineeringAgentToolOperation.SOURCE_SEARCH
        and item.citation_refs
    }
    support_position = {
        item.observation_id: index
        for index, item in enumerate(package.support_observations)
    }
    resolved_candidates = set(
        projection.resolved_acquisition_candidate_observation_ids
    )
    challenges: list[EngineeringAgentBoundaryRelevanceChallenge] = []
    for boundary in package.boundary_observations:
        boundary_id = boundary.observation_id
        search_support = search_support_by_request.get(boundary.tool_request_id)
        resolving: tuple[StableId, ...] = ()
        if boundary_id in resolved_candidates:
            if search_support is None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "resolved Source boundary lacks its paired Search support",
                )
            search_position = support_position[search_support.observation_id]
            resolving = tuple(
                item.observation_id
                for index, item in enumerate(package.support_observations)
                if item.operation is EngineeringAgentToolOperation.SOURCE_READ
                and index > search_position
                and _engineering_agent_search_is_resolved_by_full_read(
                    search_support=search_support,
                    read_support=item,
                )
            )
            if not resolving:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "resolved Source boundary lacks exact full-read support",
                )
        challenges.append(
            EngineeringAgentBoundaryRelevanceChallenge.create(
                kind=(
                    EngineeringAgentBoundaryRelevanceChallengeKind.RESOLVED_ACQUISITION
                    if resolving
                    else EngineeringAgentBoundaryRelevanceChallengeKind.BOUNDARY_MATERIALITY
                ),
                boundary_observation_id=boundary_id,
                resolving_support_observation_ids=resolving,
                draft_declared_boundary_reference=(
                    boundary_id in draft.boundary_observation_ids
                ),
            )
        )
    return tuple(challenges)


_CALLER_ONLY_SEMANTIC_SCOPES = frozenset(
    {
        EngineeringAgentClaimSemanticScope.CALLER_INVOCATION,
        EngineeringAgentClaimSemanticScope.SOURCE_VISIBLE_LOCAL_ORDER,
    }
)


def engineering_agent_evidence_boundary_assessment_matches_challenge(
    challenge: EngineeringAgentEvidenceBoundaryChallenge,
    assessment: EngineeringAgentEvidenceBoundaryAssessment,
) -> bool:
    semantic_scopes = set(assessment.draft_semantic_scopes)
    exceeds_caller_scope = not semantic_scopes.issubset(
        _CALLER_ONLY_SEMANTIC_SCOPES
    )
    if not exceeds_caller_scope:
        return (
            assessment.disposition
            is EngineeringAgentEvidenceBoundaryAssessmentDisposition.WITHIN_CALLER_EVIDENCE
        )
    if not challenge.cited_implementation_observation_ids:
        return (
            assessment.disposition
            is EngineeringAgentEvidenceBoundaryAssessmentDisposition.CLAIM_EXCEEDS_CALLER_EVIDENCE
        )
    return True


def engineering_agent_boundary_relevance_assessment_matches_challenge(
    challenge: EngineeringAgentBoundaryRelevanceChallenge,
    assessment: EngineeringAgentBoundaryRelevanceAssessment,
    *,
    draft_content: str,
) -> bool:
    disclosed = bool(assessment.draft_disclosed_fragments)
    normalized_draft_content = _draft_disclosure_presentation_text(
        draft_content
    )
    if any(
        _draft_disclosure_presentation_text(fragment)
        not in normalized_draft_content
        for fragment in assessment.draft_disclosed_fragments
    ):
        return False
    if (
        assessment.disposition
        is EngineeringAgentBoundaryRelevanceAssessmentDisposition.NOT_DISCLOSED_IN_DRAFT
    ):
        return not challenge.draft_declared_boundary_reference and not disclosed
    if (
        assessment.disposition
        is EngineeringAgentBoundaryRelevanceAssessmentDisposition.MATERIAL_TO_USER_REQUEST
    ):
        return challenge.draft_declared_boundary_reference and disclosed
    if (
        assessment.disposition
        is EngineeringAgentBoundaryRelevanceAssessmentDisposition.RESOLVED_AUDIT_ONLY
    ):
        return (
            challenge.kind
            is EngineeringAgentBoundaryRelevanceChallengeKind.RESOLVED_ACQUISITION
            and (challenge.draft_declared_boundary_reference or disclosed)
        )
    if (
        assessment.disposition
        is EngineeringAgentBoundaryRelevanceAssessmentDisposition.NON_MATERIAL_AUDIT_ONLY
    ):
        return (
            challenge.kind
            is EngineeringAgentBoundaryRelevanceChallengeKind.BOUNDARY_MATERIALITY
            and (challenge.draft_declared_boundary_reference or disclosed)
        )
    return True


def engineering_agent_boundary_relevance_assessment_is_closed(
    assessment: EngineeringAgentBoundaryRelevanceAssessment,
) -> bool:
    return assessment.disposition in {
        EngineeringAgentBoundaryRelevanceAssessmentDisposition.MATERIAL_TO_USER_REQUEST,
        EngineeringAgentBoundaryRelevanceAssessmentDisposition.NOT_DISCLOSED_IN_DRAFT,
    }


def project_engineering_agent_evidence_boundary_challenges(
    package: EngineeringAgentEvidencePackage,
    draft: EngineeringAgentAnswerDraft,
) -> tuple[EngineeringAgentEvidenceBoundaryChallenge, ...]:
    """Project caller/callee review leads without interpreting answer prose.

    The projector uses source structure only: a Claim that cites a full Java
    read and repeats one of that file's receiver call expressions receives an
    exact challenge.  The Reviewer, not a language keyword filter, decides
    whether the Claim stays at invocation/order scope or exceeds it.
    """

    source_items = _engineering_agent_java_source_items(
        package.support_observations
    )
    items_by_observation: dict[StableId, list[_EngineeringAgentJavaSourceItem]] = {}
    for item in source_items:
        items_by_observation.setdefault(item.observation_id, []).append(item)
    challenges: list[EngineeringAgentEvidenceBoundaryChallenge] = []
    seen: set[tuple[object, ...]] = set()
    for claim_index, claim in enumerate(draft.claims):
        compact_statement = re.sub(r"\s+", "", claim.statement)
        for support_observation_id in claim.support_observation_ids:
            for source_item in items_by_observation.get(
                support_observation_id, ()
            ):
                code = _JAVA_NON_CODE_RE.sub(" ", source_item.content)
                fields = {
                    match.group("name"): _java_simple_type(match.group("type"))
                    for match in _JAVA_FIELD_RE.finditer(code)
                }
                for match in _JAVA_RECEIVER_CALL_RE.finditer(code):
                    receiver = re.sub(r"\s+", "", match.group("receiver"))
                    method = match.group("method")
                    call_expression = f"{receiver}.{method}"
                    if re.search(
                        rf"(?<![A-Za-z0-9_$]){re.escape(call_expression)}"
                        rf"(?![A-Za-z0-9_$])",
                        compact_statement,
                    ) is None:
                        continue
                    receiver_type = _java_receiver_type(
                        code=code,
                        receiver=receiver,
                        fields=fields,
                    )
                    package_implementations = (
                        _java_method_implementation_observation_ids(
                            source_items,
                            receiver_type=receiver_type,
                            method=method,
                        )
                        if receiver_type is not None
                        else ()
                    )
                    cited_implementations = tuple(
                        item
                        for item in package_implementations
                        if item in claim.support_observation_ids
                    )
                    identity = (
                        claim_index,
                        support_observation_id,
                        source_item.locator,
                        call_expression,
                        receiver_type,
                    )
                    if identity in seen:
                        continue
                    seen.add(identity)
                    challenges.append(
                        EngineeringAgentEvidenceBoundaryChallenge.create(
                            claim_index=claim_index,
                            support_observation_id=support_observation_id,
                            source_locator=source_item.locator,
                            call_expression=call_expression,
                            receiver_declared_type=receiver_type,
                            cited_implementation_observation_ids=(
                                cited_implementations
                            ),
                            package_implementation_observation_ids=(
                                package_implementations
                            ),
                        )
                    )
    return tuple(challenges)


def _engineering_agent_java_source_items(
    observations: Sequence[EngineeringAgentToolObservation],
) -> tuple[_EngineeringAgentJavaSourceItem, ...]:
    items: list[_EngineeringAgentJavaSourceItem] = []
    for observation in observations:
        if (
            observation.operation is not EngineeringAgentToolOperation.SOURCE_READ
            or observation.disposition
            is not EngineeringAgentEvidenceDisposition.SUPPORT
        ):
            continue
        try:
            payload = json.loads(observation.content)
        except (TypeError, json.JSONDecodeError):
            continue
        retrieval = payload.get("retrieval_result")
        if not isinstance(retrieval, dict):
            continue
        raw_items = retrieval.get("items")
        if not isinstance(raw_items, list):
            continue
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue
            locator = raw_item.get("locator")
            content = raw_item.get("content")
            if (
                raw_item.get("modality") != "EXACT_STATIC_SOURCE_TEXT"
                or raw_item.get("coverage_complete") is not True
                or not isinstance(locator, str)
                or not locator.endswith(".java")
                or not isinstance(content, str)
            ):
                continue
            items.append(
                _EngineeringAgentJavaSourceItem(
                    observation_id=observation.observation_id,
                    locator=locator,
                    content=content,
                )
            )
    return tuple(items)


def _java_simple_type(value: str) -> str:
    without_generic = value.split("<", 1)[0].strip().removesuffix("[]")
    return without_generic.rsplit(".", 1)[-1]


def _java_receiver_type(
    *,
    code: str,
    receiver: str,
    fields: dict[str, str],
) -> str | None:
    if receiver in fields:
        return fields[receiver]
    if not receiver.endswith("()"):
        return None
    accessor = re.escape(receiver[:-2])
    declaration = re.search(
        rf"\b(?P<type>[A-Za-z_$][A-Za-z0-9_$.<>\[\]]*)\s+"
        rf"{accessor}\s*\([^)]*\)\s*(?:throws\s+[^{{]+)?\{{",
        code,
    )
    return (
        _java_simple_type(declaration.group("type"))
        if declaration is not None
        else None
    )


def _java_method_implementation_observation_ids(
    source_items: Sequence[_EngineeringAgentJavaSourceItem],
    *,
    receiver_type: str,
    method: str,
) -> tuple[StableId, ...]:
    matched: list[StableId] = []
    for item in source_items:
        code = _JAVA_NON_CODE_RE.sub(" ", item.content)
        declares_receiver = re.search(
            rf"\b(?:class|record|enum)\s+{re.escape(receiver_type)}\b",
            code,
        ) or re.search(
            rf"\b(?:implements|extends)\s+[^{{;]*\b{re.escape(receiver_type)}\b",
            code,
        )
        declares_body = re.search(
            rf"\b{re.escape(method)}\s*\([^;{{}}]*\)\s*"
            rf"(?:throws\s+[^{{]+)?\{{",
            code,
        )
        if declares_receiver and declares_body and item.observation_id not in matched:
            matched.append(item.observation_id)
    return tuple(matched)


@dataclass(frozen=True, slots=True)
class EngineeringAgentDeliveryRequest:
    turn_request_digest: Digest
    work_state: EngineeringAgentWorkState
    package: EngineeringAgentEvidencePackage
    draft: EngineeringAgentAnswerDraft
    review: EngineeringAgentReview


@dataclass(frozen=True, slots=True)
class EngineeringAgentDeliveryAuthorization:
    authorization_ref: str
    turn_request_digest: Digest
    work_state_digest: Digest
    package_digest: Digest
    answer_digest: Digest
    review_digest: Digest

    @classmethod
    def create(
        cls,
        *,
        authorization_ref: str,
        turn_request_digest: Digest,
        work_state_digest: Digest,
        package_digest: Digest,
        answer_digest: Digest,
        review_digest: Digest,
    ) -> "EngineeringAgentDeliveryAuthorization":
        return cls(
            authorization_ref=_text(
                authorization_ref, "Delivery authorization reference"
            ),
            turn_request_digest=turn_request_digest,
            work_state_digest=work_state_digest,
            package_digest=package_digest,
            answer_digest=answer_digest,
            review_digest=review_digest,
        )


class EngineeringAgentResponseControl(Protocol):
    def authorize(
        self, request: EngineeringAgentDeliveryRequest
    ) -> EngineeringAgentDeliveryAuthorization: ...


class SealedEngineeringAgentResponseControl:
    """Authorize only one exact independently approved attempt result."""

    def __init__(self) -> None:
        self._issued: set[Digest] = set()
        self._lock = Lock()

    def authorize(
        self, request: EngineeringAgentDeliveryRequest
    ) -> EngineeringAgentDeliveryAuthorization:
        if not isinstance(request, EngineeringAgentDeliveryRequest):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Response Control requires a typed Delivery request",
            )
        _validate_evidence_package_identity(request.package)
        if (
            request.review.decision
            is not EngineeringAgentReviewDecision.APPROVED
            or request.review.findings
            or request.work_state.digest != request.draft.work_state_digest
            or request.package.digest != request.draft.package_digest
            or request.work_state.digest != request.review.work_state_digest
            or request.package.digest != request.review.package_digest
            or request.draft.digest != request.review.answer_digest
            or request.work_state.turn_id != request.package.turn_id
            or request.work_state.turn_id != request.draft.turn_id
            or request.work_state.turn_id != request.review.turn_id
            or not _engineering_agent_review_closes_boundary_challenges(
                package=request.package,
                draft=request.draft,
                review=request.review,
            )
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Response Control requires one exact independently approved result chain",
            )
        request_digest = digest_of(
            {
                "schema": "ENGINEERING_AGENT_DELIVERY_REQUEST@1",
                "turn_request_digest": request.turn_request_digest.value,
                "work_state_digest": request.work_state.digest.value,
                "package_digest": request.package.digest.value,
                "answer_digest": request.draft.digest.value,
                "review_digest": request.review.digest.value,
            }
        )
        with self._lock:
            if request_digest in self._issued:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "Response Control cannot authorize the same result twice",
                )
            self._issued.add(request_digest)
        return EngineeringAgentDeliveryAuthorization.create(
            authorization_ref=(
                f"engineering-agent-delivery:{request_digest.value}"
            ),
            turn_request_digest=request.turn_request_digest,
            work_state_digest=request.work_state.digest,
            package_digest=request.package.digest,
            answer_digest=request.draft.digest,
            review_digest=request.review.digest,
        )


@dataclass(frozen=True, slots=True)
class EngineeringAgentLoopLimits:
    maximum_agent_steps: int = 11
    maximum_tool_actions: int = _DEFAULT_MAXIMUM_TOOL_ACTIONS
    maximum_reviews: int = 4
    maximum_consecutive_no_progress: int = 2
    maximum_evidence_package_bytes: int = 4_194_304

    def __post_init__(self) -> None:
        for label, value in (
            ("maximum Agent steps", self.maximum_agent_steps),
            ("maximum tool actions", self.maximum_tool_actions),
            ("maximum Reviews", self.maximum_reviews),
            ("maximum consecutive no-progress observations", self.maximum_consecutive_no_progress),
            ("maximum evidence Package bytes", self.maximum_evidence_package_bytes),
        ):
            if type(value) is not int or value < 1:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    f"{label} must be a positive integer",
                )


@dataclass(slots=True)
class _EngineeringAgentExecutionAudit:
    model_call_refs: list[str]
    model_call_receipts: list[EngineeringAgentModelCallReceipt]
    expected_model_role: EngineeringAgentModelRole | None = None
    provider_dispatch_count: int = 0
    work_state: EngineeringAgentWorkState | None = None
    package: EngineeringAgentEvidencePackage | None = None
    draft: EngineeringAgentAnswerDraft | None = None
    review: EngineeringAgentReview | None = None


class ApplicationOwnedEngineeringAgentTurnExecutor(
    EngineeringConversationTurnExecutor
):
    """Runs one bounded Turn through Agent, tools, Review, and Response Control."""

    def __init__(
        self,
        *,
        driver: EngineeringAgentDriver,
        tool_port: EngineeringAgentToolPort,
        reviewer: EngineeringAgentReviewer,
        response_control: EngineeringAgentResponseControl,
        available_operations: Sequence[EngineeringAgentToolOperation],
        limits: EngineeringAgentLoopLimits = EngineeringAgentLoopLimits(),
        require_tool_authority_receipts: bool = False,
        require_model_call_receipts: bool = False,
        work_state_repository: EngineeringAgentWorkStateRepository | None = None,
        id_generator: IdGenerator | None = None,
    ) -> None:
        operations = tuple(available_operations)
        if not operations or len(operations) != len(set(operations)) or any(
            not isinstance(item, EngineeringAgentToolOperation)
            for item in operations
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Agent executor requires a unique non-empty closed tool catalog",
            )
        if type(require_tool_authority_receipts) is not bool:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "tool authority receipt requirement must be a boolean",
            )
        if type(require_model_call_receipts) is not bool:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "model call receipt requirement must be a boolean",
            )
        self._driver = driver
        self._tool_port = tool_port
        self._reviewer = reviewer
        self._response_control = response_control
        self._available_operations = operations
        self._limits = limits
        self._require_tool_authority_receipts = require_tool_authority_receipts
        self._require_model_call_receipts = require_model_call_receipts
        self._work_state_repository = (
            work_state_repository
            or InMemoryEngineeringAgentWorkStateRepository()
        )
        self._id_generator = id_generator or Uuid4IdGenerator()
        self._id_lock = Lock()
        self._model_call_lock = Lock()
        self._issued_ids: set[StableId] = set()
        self._issued_model_call_refs: set[str] = set()

    def execute(
        self, request: EngineeringTurnExecutionRequest
    ) -> EngineeringTurnExecutionOutcome:
        audit = _EngineeringAgentExecutionAudit(
            model_call_refs=[], model_call_receipts=[]
        )
        try:
            initial_previous = self._load_previous_work_state(request)
            outcome = self._execute_bounded(request, audit, initial_previous)
        except EngineeringAgentModelCallFailure as exc:
            failure_code = _model_failure_code(exc.receipt)
            provider_failure_classification = None
            provider_failure_code = None
            provider_http_status = None
            provider_http_failure_evidence_digest = None
            role_matches = audit.expected_model_role is exc.receipt.role
            if not role_matches:
                failure_code = "AGENT_PROTOCOL_VIOLATION"
            try:
                for receipt in exc.receipts:
                    _record_model_receipt(audit, receipt)
                    self._record_model_call(
                        audit.model_call_refs, receipt.model_call_ref
                    )
            except DomainError:
                failure_code = "AGENT_PROTOCOL_VIOLATION"
            else:
                if role_matches:
                    provider_failure_classification = (
                        _provider_failure_classification(
                            exc.receipt.failure_kind
                        )
                    )
                    if provider_failure_classification is not None:
                        provider_failure_code = exc.receipt.failure_code
                        provider_http_status = exc.receipt.provider_http_status
                        provider_http_failure_evidence_digest = (
                            exc.receipt.provider_http_failure_evidence_digest
                        )
            outcome = self._failed_outcome(
                request=request,
                work_state=audit.work_state,
                package=audit.package,
                draft=audit.draft,
                review=audit.review,
                provider_dispatch_count=audit.provider_dispatch_count,
                model_dispatch_receipt_refs=_model_receipt_refs(audit),
                failure_code=failure_code,
                provider_failure_classification=(
                    provider_failure_classification
                ),
                provider_failure_code=provider_failure_code,
                provider_http_status=provider_http_status,
                provider_http_failure_evidence_digest=(
                    provider_http_failure_evidence_digest
                ),
            )
        except DomainError:
            outcome = self._failed_outcome(
                request=request,
                work_state=audit.work_state,
                package=audit.package,
                draft=audit.draft,
                review=audit.review,
                provider_dispatch_count=audit.provider_dispatch_count,
                model_dispatch_receipt_refs=_model_receipt_refs(audit),
                failure_code="AGENT_PROTOCOL_VIOLATION",
            )
        if (
            outcome.state is ConversationTurnState.SUCCEEDED
            and audit.work_state is not None
        ):
            self._remember_work_state(audit.work_state)
        return outcome

    def _execute_bounded(
        self,
        request: EngineeringTurnExecutionRequest,
        audit: _EngineeringAgentExecutionAudit,
        initial_previous: EngineeringAgentWorkState | None,
    ) -> EngineeringTurnExecutionOutcome:
        previous = initial_previous
        observations: tuple[EngineeringAgentToolObservation, ...] = ()
        review_findings: tuple[EngineeringAgentReviewFinding, ...] = ()
        pending_review: EngineeringAgentReview | None = None
        model_call_refs = audit.model_call_refs
        tool_actions = 0
        review_count = 0
        consecutive_no_progress = 0
        action_history: tuple[EngineeringAgentToolActionProposal, ...] = ()
        invocation_mode = EngineeringAgentInvocationMode.STANDARD
        minimum_observations_for_draft = 0
        last_package: EngineeringAgentEvidencePackage | None = None
        last_draft: EngineeringAgentAnswerDraft | None = None
        last_review: EngineeringAgentReview | None = None
        next_review_focus = EngineeringAgentReviewFocus.COMPREHENSIVE
        review_feedback_evidence_action_completed = False
        available_operations = self._authorized_operations(request)
        preissued_source_read_options = (
            self._prepare_source_read_options(request)
            if EngineeringAgentToolOperation.SOURCE_READ in available_operations
            else ()
        )

        for _ in range(self._limits.maximum_agent_steps):
            audit.expected_model_role = EngineeringAgentModelRole.PRIMARY_AGENT
            reviewed_draft = last_draft if pending_review is not None else None
            if pending_review is not None and (
                reviewed_draft is None
                or pending_review.answer_digest != reviewed_draft.digest
                or pending_review.findings != review_findings
                or pending_review.turn_id != request.turn_id
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "pending Review does not bind the exact rejected Draft",
                )
            try:
                driver_output = self._driver.propose(
                    EngineeringAgentInvocation(
                        request=request,
                        previous_work_state=previous,
                        observations=observations,
                        review_findings=review_findings,
                        review_digest=(
                            pending_review.digest if pending_review is not None else None
                        ),
                        available_operations=available_operations,
                        action_history=action_history,
                        mode=invocation_mode,
                        preissued_source_read_options=(
                            preissued_source_read_options
                        ),
                        maximum_tool_actions=(
                            self._limits.maximum_tool_actions
                        ),
                        reviewed_draft=reviewed_draft,
                        review_feedback_evidence_action_completed=(
                            review_feedback_evidence_action_completed
                        ),
                    )
                )
            except BaseException:
                raise
            else:
                audit.expected_model_role = None
            if isinstance(driver_output, EngineeringAgentDriverModelResult):
                expected_driver_output = EngineeringAgentDriverModelResult.create(
                    proposal=driver_output.proposal,
                    receipt=driver_output.receipt,
                    prior_receipts=driver_output.prior_receipts,
                )
                if driver_output != expected_driver_output:
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "Agent driver model result identity is invalid",
                    )
                proposal = driver_output.proposal
                for receipt in driver_output.prior_receipts:
                    _record_model_receipt(audit, receipt)
                    self._record_model_call(
                        model_call_refs, receipt.model_call_ref
                    )
                _record_model_receipt(audit, driver_output.receipt)
            else:
                if self._require_model_call_receipts:
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "qualified Agent driver requires an exact model call receipt",
                    )
                proposal = driver_output
                audit.provider_dispatch_count += 1
            if not isinstance(proposal, EngineeringAgentWorkStateProposal):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Agent driver returned an untyped Work State proposal",
                )
            if invocation_mode is EngineeringAgentInvocationMode.EVIDENCE_ONLY_SYNTHESIS:
                if proposal.action is not None or (
                    proposal.draft is not None
                    and proposal.draft.response_kind
                    not in {
                        EngineeringAgentResponseKind.ANSWER,
                        EngineeringAgentResponseKind.LIMITATION,
                    }
                ):
                    raise DomainError(
                        ErrorCode.CONTROL_STATE_DENIED,
                        "evidence-only synthesis requires an Answer or Limitation draft",
                    )
            self._record_model_call(model_call_refs, proposal.model_call_ref)
            work_state = self._seal_work_state(
                request=request,
                proposal=proposal,
                previous=previous,
                observations=observations,
                review_input=pending_review,
            )
            previous = work_state
            audit.work_state = work_state

            if proposal.action is not None:
                tool_actions += 1
                if tool_actions > self._limits.maximum_tool_actions:
                    return self._failed_outcome(
                        request=request,
                        work_state=work_state,
                        package=last_package,
                        draft=last_draft,
                        review=last_review,
                        provider_dispatch_count=audit.provider_dispatch_count,
                        model_dispatch_receipt_refs=_model_receipt_refs(audit),
                        failure_code="AGENT_TOOL_LIMIT_REACHED",
                    )
                observation_batch = self._execute_tool(
                    request=request,
                    work_state=work_state,
                    action=proposal.action,
                    prior_observations=observations,
                )
                action_history = (*action_history, proposal.action)
                observations = (*observations, *observation_batch)
                consecutive_no_progress = (
                    0
                    if any(item.progress for item in observation_batch)
                    else consecutive_no_progress + 1
                )
                if (
                    consecutive_no_progress
                    >= self._limits.maximum_consecutive_no_progress
                ):
                    invocation_mode = (
                        EngineeringAgentInvocationMode.EVIDENCE_ONLY_SYNTHESIS
                    )
                    available_operations = ()
                if pending_review is not None and any(
                    item.requires_evidence for item in review_findings
                ):
                    # The new Observation satisfies the one-action admission
                    # condition for a redraft, but it does not erase the
                    # rejected Draft or any mixed no-evidence correction. Keep
                    # the sealed Review attached until a replacement Draft is
                    # actually produced and reviewed.
                    review_feedback_evidence_action_completed = True
                continue

            assert proposal.draft is not None
            if len(observations) < minimum_observations_for_draft:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "an evidence-required Review Finding must receive a new Observation before redrafting",
                )
            review_findings = ()
            pending_review = None
            review_feedback_evidence_action_completed = False
            package = (
                last_package
                if last_package is not None
                and _package_matches_observations(last_package, observations)
                else self._seal_package(
                    request=request,
                    work_state=work_state,
                    observations=observations,
                )
            )
            audit.package = package
            draft = self._seal_draft(
                request=request,
                work_state=work_state,
                package=package,
                proposal=proposal.draft,
                observations=observations,
            )
            audit.draft = draft
            challenges = project_engineering_agent_evidence_boundary_challenges(
                package,
                draft,
            )
            relevance_challenges = (
                project_engineering_agent_boundary_relevance_challenges(
                    package,
                    draft,
                )
            )
            focused_review_required = bool(
                challenges or relevance_challenges
            )
            review_focus = (
                next_review_focus
                if focused_review_required
                else EngineeringAgentReviewFocus.COMPREHENSIVE
            )
            review_request = EngineeringAgentReviewRequest(
                turn_request=request,
                work_state=work_state,
                package=package,
                draft=draft,
                focus=review_focus,
            )
            review_count += 1
            if review_count > self._limits.maximum_reviews:
                return self._review_limit_outcome(
                    request=request,
                    work_state=work_state,
                    package=package,
                    draft=draft,
                    review=last_review,
                    audit=audit,
                )
            review_proposal = self._request_review_proposal(
                review_request=review_request,
                audit=audit,
                model_call_refs=model_call_refs,
            )
            review = self._seal_review(
                request=request,
                work_state=work_state,
                package=package,
                draft=draft,
                proposal=review_proposal,
                focus=review_request.focus,
            )
            if (
                review.decision is EngineeringAgentReviewDecision.APPROVED
                and focused_review_required
                and review.focus is EngineeringAgentReviewFocus.COMPREHENSIVE
            ):
                review_request = EngineeringAgentReviewRequest(
                    turn_request=request,
                    work_state=work_state,
                    package=package,
                    draft=draft,
                    focus=EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE,
                )
                review_count += 1
                if review_count > self._limits.maximum_reviews:
                    return self._review_limit_outcome(
                        request=request,
                        work_state=work_state,
                        package=package,
                        draft=draft,
                        review=review,
                        audit=audit,
                    )
                review_proposal = self._request_review_proposal(
                    review_request=review_request,
                    audit=audit,
                    model_call_refs=model_call_refs,
                )
                review = self._seal_review(
                    request=request,
                    work_state=work_state,
                    package=package,
                    draft=draft,
                    proposal=review_proposal,
                    focus=review_request.focus,
                )
            last_package, last_draft, last_review = package, draft, review
            audit.review = review
            if review.decision is EngineeringAgentReviewDecision.FINDINGS:
                next_review_focus = review.focus
                review_findings = review.findings
                pending_review = review
                review_feedback_evidence_action_completed = False
                if any(item.requires_evidence for item in review.findings):
                    if invocation_mode is (
                        EngineeringAgentInvocationMode.EVIDENCE_ONLY_SYNTHESIS
                    ):
                        return self._failed_outcome(
                            request=request,
                            work_state=work_state,
                            package=package,
                            draft=draft,
                            review=review,
                            provider_dispatch_count=audit.provider_dispatch_count,
                            model_dispatch_receipt_refs=_model_receipt_refs(audit),
                            failure_code="AGENT_NO_PROGRESS_LIMIT_REACHED",
                            provider_failure_classification=(
                                EngineeringProviderFailureClassification.MODEL_REVIEW_REJECTED
                            ),
                            provider_failure_code="AGENT_NO_PROGRESS_LIMIT_REACHED",
                        )
                    minimum_observations_for_draft = len(observations) + 1
                continue

            authorization = self._response_control.authorize(
                EngineeringAgentDeliveryRequest(
                    turn_request_digest=request.request_digest,
                    work_state=work_state,
                    package=package,
                    draft=draft,
                    review=review,
                )
            )
            if not isinstance(
                authorization, EngineeringAgentDeliveryAuthorization
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Response Control returned an untyped authorization",
                )
            _validate_delivery_authorization(
                request=request,
                work_state=work_state,
                package=package,
                draft=draft,
                review=review,
                authorization=authorization,
            )
            return self._successful_outcome(
                request=request,
                work_state=work_state,
                package=package,
                draft=draft,
                review=review,
                authorization=authorization,
                provider_dispatch_count=audit.provider_dispatch_count,
                model_dispatch_receipt_refs=_model_receipt_refs(audit),
            )

        return self._failed_outcome(
            request=request,
            work_state=previous,
            package=last_package,
            draft=last_draft,
            review=last_review,
            provider_dispatch_count=audit.provider_dispatch_count,
            model_dispatch_receipt_refs=_model_receipt_refs(audit),
            failure_code="AGENT_STEP_LIMIT_REACHED",
        )

    def _review_limit_outcome(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        work_state: EngineeringAgentWorkState,
        package: EngineeringAgentEvidencePackage,
        draft: EngineeringAgentAnswerDraft,
        review: EngineeringAgentReview | None,
        audit: _EngineeringAgentExecutionAudit,
    ) -> EngineeringTurnExecutionOutcome:
        return self._failed_outcome(
            request=request,
            work_state=work_state,
            package=package,
            draft=draft,
            review=review,
            provider_dispatch_count=audit.provider_dispatch_count,
            model_dispatch_receipt_refs=_model_receipt_refs(audit),
            failure_code="AGENT_REVIEW_LIMIT_REACHED",
            provider_failure_classification=(
                EngineeringProviderFailureClassification.MODEL_REVIEW_REJECTED
            ),
            provider_failure_code="AGENT_REVIEW_LIMIT_REACHED",
        )

    def _request_review_proposal(
        self,
        *,
        review_request: EngineeringAgentReviewRequest,
        audit: _EngineeringAgentExecutionAudit,
        model_call_refs: list[str],
    ) -> EngineeringAgentReviewProposal:
        audit.expected_model_role = EngineeringAgentModelRole.INDEPENDENT_REVIEWER
        try:
            reviewer_output = self._reviewer.review(review_request)
        except BaseException:
            raise
        else:
            audit.expected_model_role = None
        if isinstance(reviewer_output, EngineeringAgentReviewerModelResult):
            expected_reviewer_output = EngineeringAgentReviewerModelResult.create(
                proposal=reviewer_output.proposal,
                receipt=reviewer_output.receipt,
                prior_receipts=reviewer_output.prior_receipts,
            )
            if reviewer_output != expected_reviewer_output:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Reviewer model result identity is invalid",
                )
            review_proposal = reviewer_output.proposal
            for receipt in reviewer_output.prior_receipts:
                _record_model_receipt(audit, receipt)
                self._record_model_call(model_call_refs, receipt.model_call_ref)
            _record_model_receipt(audit, reviewer_output.receipt)
        else:
            if self._require_model_call_receipts:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "qualified Agent Reviewer requires an exact model call receipt",
                )
            review_proposal = reviewer_output
            audit.provider_dispatch_count += 1
        if not isinstance(review_proposal, EngineeringAgentReviewProposal):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Reviewer returned an untyped proposal",
            )
        self._record_model_call(model_call_refs, review_proposal.model_call_ref)
        return review_proposal

    def _prepare_source_read_options(
        self, request: EngineeringTurnExecutionRequest
    ) -> tuple[EngineeringAgentSourceReadOption, ...]:
        provider = getattr(self._tool_port, "source_read_options", None)
        if not callable(provider):
            return ()
        options = tuple(provider(request))
        if len(options) > 16:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "prior-Turn Source revalidation option fuse is exhausted",
            )
        normalized: list[EngineeringAgentSourceReadOption] = []
        for option in options:
            if not isinstance(option, EngineeringAgentSourceReadOption):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Source tool port returned an untyped read option",
                )
            expected = EngineeringAgentSourceReadOption.create(
                locator_reference=option.locator_reference,
                locator=option.locator,
                evidence_class=option.evidence_class,
                source_revision=option.source_revision,
                modality=option.modality,
                content_digest=option.content_digest,
                origin_turn_id=option.origin_turn_id,
                origin_citation_digest=option.origin_citation_digest,
            )
            if (
                option != expected
                or option.source_revision != request.binding.repository_revision
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Source read option does not bind the current repository revision",
                )
            normalized.append(option)
        if (
            len({item.locator_reference for item in normalized})
            != len(normalized)
            or len({item.resource_locator for item in normalized})
            != len(normalized)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Source revalidation options must have unique references and resources",
            )
        return tuple(normalized)

    def _seal_work_state(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        proposal: EngineeringAgentWorkStateProposal,
        previous: EngineeringAgentWorkState | None,
        observations: tuple[EngineeringAgentToolObservation, ...],
        review_input: EngineeringAgentReview | None,
    ) -> EngineeringAgentWorkState:
        if (
            not isinstance(proposal.phase, EngineeringAgentWorkPhase)
            or (proposal.action is None) == (proposal.draft is None)
            or (
                proposal.action is not None
                and not isinstance(proposal.action, EngineeringAgentToolActionProposal)
            )
            or (
                proposal.draft is not None
                and not isinstance(proposal.draft, EngineeringAgentDraftProposal)
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent Work State proposal violates the typed action contract",
            )
        if (
            proposal.action is not None
            and proposal.phase is EngineeringAgentWorkPhase.RESPONSE_READY
        ) or (
            proposal.draft is not None
            and proposal.phase is not EngineeringAgentWorkPhase.RESPONSE_READY
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent Work State phase does not match its proposed action",
            )
        expected_previous = previous.digest if previous is not None else None
        if (
            proposal.expected_context_digest
            != request.snapshot_before.context.digest
            or proposal.expected_previous_work_state_digest != expected_previous
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent Work State proposal is bound to stale context or state",
            )
        expected_observations = tuple(item.observation_id for item in observations)
        if proposal.observation_ids != expected_observations:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent Work State must preserve the complete ordered observation prefix",
            )
        known_user_messages = {
            item.message_id
            for item in request.snapshot_before.messages
            if item.role.value == "USER"
        }
        known_user_messages.add(request.user_message.message_id)
        previous_corrections = (
            request.snapshot_before.context.accepted_correction_message_ids
            if previous is None
            else previous.accepted_correction_message_ids
        )
        if (
            proposal.accepted_correction_message_ids[: len(previous_corrections)]
            != previous_corrections
            or not set(proposal.accepted_correction_message_ids).issubset(
                known_user_messages
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "accepted corrections must be monotonic known User Messages",
            )
        reviewed = set(request.snapshot_before.context.reviewed_conclusion_refs)
        previous_superseded = (
            request.snapshot_before.context.superseded_conclusion_refs
            if previous is None
            else previous.superseded_conclusion_refs
        )
        if (
            proposal.superseded_conclusion_refs[: len(previous_superseded)]
            != previous_superseded
            or not set(proposal.superseded_conclusion_refs).issubset(reviewed)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "superseded conclusions must be monotonic and previously reviewed",
            )
        work_state_id = (
            self._new_id("agent_work_state")
            if previous is None
            else previous.work_state_id
        )
        revision = Revision(1) if previous is None else previous.revision.next()
        core = {
            "schema": "ENGINEERING_AGENT_WORK_STATE@1",
            "work_state_id": work_state_id.value,
            "conversation_id": request.snapshot_before.conversation.conversation_id.value,
            "turn_id": request.turn_id.value,
            "revision": revision.value,
            "previous_digest": expected_previous.value if expected_previous else None,
            "context_digest": proposal.expected_context_digest.value,
            "goal": proposal.goal,
            "response_language": proposal.response_language,
            "audience": proposal.audience,
            "constraints": proposal.constraints,
            "resolved_referents": proposal.resolved_referents,
            "accepted_correction_message_ids": tuple(
                item.value for item in proposal.accepted_correction_message_ids
            ),
            "superseded_conclusion_refs": proposal.superseded_conclusion_refs,
            "hypotheses": proposal.hypotheses,
            "plan": proposal.plan,
            "observation_ids": tuple(
                item.value for item in proposal.observation_ids
            ),
            "open_items": proposal.open_items,
            "phase": proposal.phase.value,
            "review_input_digest": (
                review_input.digest.value if review_input is not None else None
            ),
            "proposal_digest": proposal.digest.value,
        }
        return EngineeringAgentWorkState(
            work_state_id=work_state_id,
            conversation_id=request.snapshot_before.conversation.conversation_id,
            turn_id=request.turn_id,
            revision=revision,
            previous_digest=expected_previous,
            context_digest=proposal.expected_context_digest,
            goal=proposal.goal,
            response_language=proposal.response_language,
            audience=proposal.audience,
            constraints=proposal.constraints,
            resolved_referents=proposal.resolved_referents,
            accepted_correction_message_ids=proposal.accepted_correction_message_ids,
            superseded_conclusion_refs=proposal.superseded_conclusion_refs,
            hypotheses=proposal.hypotheses,
            plan=proposal.plan,
            observation_ids=proposal.observation_ids,
            open_items=proposal.open_items,
            phase=proposal.phase,
            review_input_digest=(
                review_input.digest if review_input is not None else None
            ),
            proposal_digest=proposal.digest,
            digest=digest_of(core),
        )

    def _execute_tool(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        work_state: EngineeringAgentWorkState,
        action: EngineeringAgentToolActionProposal,
        prior_observations: tuple[EngineeringAgentToolObservation, ...],
    ) -> tuple[EngineeringAgentToolObservation, ...]:
        if action.operation not in self._available_operations:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Agent proposed an operation outside the frozen tool catalog",
            )
        if (
            action.operation
            in {
                EngineeringAgentToolOperation.SOURCE_SEARCH,
                EngineeringAgentToolOperation.SOURCE_READ,
            }
            and request.binding.source_access_status
            is not RuntimeCapabilityStatus.READY
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Agent proposed a Source operation without ready Source authority",
            )
        tool_request_id = self._new_id("agent_tool_request")
        core = {
            "schema": "ENGINEERING_AGENT_TOOL_REQUEST@1",
            "tool_request_id": tool_request_id.value,
            "turn_request_digest": request.request_digest.value,
            "binding_digest": request.binding.digest.value,
            "work_state_digest": work_state.digest.value,
            "action_digest": action.digest.value,
        }
        tool_request = EngineeringAgentToolRequest(
            tool_request_id=tool_request_id,
            turn_request_digest=request.request_digest,
            binding_digest=request.binding.digest,
            work_state_digest=work_state.digest,
            turn_request=request,
            action=action,
            digest=digest_of(core),
        )
        result = self._tool_port.execute(tool_request)
        if not isinstance(result, EngineeringAgentToolResult):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent tool port returned an untyped result",
            )
        if result.tool_request_digest != tool_request.digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "tool result is bound to a different request",
            )
        expected_result = EngineeringAgentToolResult.create_many(
            tool_request_digest=result.tool_request_digest,
            evidence=result.evidence,
        )
        if result != expected_result:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent tool result identity is invalid",
            )
        receipts = tuple(
            item.authority_receipt
            for item in result.evidence
            if item.authority_receipt is not None
        )
        if self._require_tool_authority_receipts and len(receipts) != len(
            result.evidence
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "qualified Agent tools require an authority receipt for every evidence observation",
            )
        if receipts:
            first_receipt = receipts[0]
            if len(receipts) != len(result.evidence) or any(
                receipt != first_receipt for receipt in receipts[1:]
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "one tool result cannot mix authority receipts or unreceipted evidence",
                )
            self._validate_tool_authority_receipt(
                request=request,
                tool_request=tool_request,
                receipt=first_receipt,
                prior_observations=prior_observations,
            )
        observations: list[EngineeringAgentToolObservation] = []
        for evidence in result.evidence:
            observation_id = self._new_id("agent_observation")
            observation_core = {
                "schema": "ENGINEERING_AGENT_TOOL_OBSERVATION@2",
                "observation_id": observation_id.value,
                "tool_request_id": tool_request_id.value,
                "operation": action.operation.value,
                "result_ref": evidence.result_ref,
                "content": evidence.content,
                "disposition": evidence.disposition.value,
                "progress": evidence.progress,
                "citation_refs": evidence.citation_refs,
                "authority_receipt_digest": (
                    evidence.authority_receipt.digest.value
                    if evidence.authority_receipt is not None
                    else None
                ),
                "tool_evidence_digest": evidence.digest.value,
            }
            observations.append(
                EngineeringAgentToolObservation(
                    observation_id=observation_id,
                    tool_request_id=tool_request_id,
                    operation=action.operation,
                    result_ref=evidence.result_ref,
                    content=evidence.content,
                    disposition=evidence.disposition,
                    progress=evidence.progress,
                    citation_refs=evidence.citation_refs,
                    authority_receipt=evidence.authority_receipt,
                    tool_evidence_digest=evidence.digest,
                    digest=digest_of(observation_core),
                )
            )
        return tuple(observations)

    @staticmethod
    def _validate_tool_authority_receipt(
        *,
        request: EngineeringTurnExecutionRequest,
        tool_request: EngineeringAgentToolRequest,
        receipt: EngineeringAgentToolAuthorityReceipt,
        prior_observations: tuple[EngineeringAgentToolObservation, ...],
    ) -> None:
        expected_authority_kind = (
            EngineeringAgentToolAuthorityKind.WORLD_MODEL
            if tool_request.action.operation
            is EngineeringAgentToolOperation.WORLD_MODEL_QUERY
            else EngineeringAgentToolAuthorityKind.SOURCE
        )
        if (
            receipt.turn_request_digest != request.request_digest
            or receipt.tool_request_digest != tool_request.digest
            or receipt.repository_revision
            != request.binding.repository_revision
            or receipt.authority_kind is not expected_authority_kind
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "tool authority receipt is bound to another Turn or revision",
            )
        prior_receipts = tuple(
            item.authority_receipt
            for item in prior_observations
            if item.authority_receipt is not None
        )
        if not prior_receipts:
            return
        previous = prior_receipts[-1]
        if (
            receipt.ledger_ref != previous.ledger_ref
            or receipt.ledger_generation != previous.ledger_generation
            or receipt.ledger_parent_seal_digest
            != previous.ledger_parent_seal_digest
            or receipt.evidence_request_digest
            != previous.evidence_request_digest
            or len(receipt.ledger_entries) < len(previous.ledger_entries)
            or receipt.ledger_entries[: len(previous.ledger_entries)]
            != previous.ledger_entries
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "tool authority Ledger snapshot does not extend the current Turn prefix",
            )

    def _seal_package(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        work_state: EngineeringAgentWorkState,
        observations: tuple[EngineeringAgentToolObservation, ...],
    ) -> EngineeringAgentEvidencePackage:
        package_id = self._new_id("agent_evidence_package")
        support = tuple(
            item
            for item in observations
            if item.disposition is EngineeringAgentEvidenceDisposition.SUPPORT
        )
        boundary = tuple(
            item
            for item in observations
            if item.disposition is EngineeringAgentEvidenceDisposition.BOUNDARY
        )
        core = {
            "schema": "ENGINEERING_AGENT_EVIDENCE_PACKAGE@1",
            "package_id": package_id.value,
            "turn_id": request.turn_id.value,
            "origin_work_state_digest": work_state.digest.value,
            "support_observations": tuple(
                (item.observation_id.value, item.digest.value) for item in support
            ),
            "boundary_observations": tuple(
                (item.observation_id.value, item.digest.value) for item in boundary
            ),
        }
        if (
            len(
                canonical_json_bytes(
                    {
                        "identity": core,
                        "support_observations": support,
                        "boundary_observations": boundary,
                    }
                )
            )
            > self._limits.maximum_evidence_package_bytes
        ):
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "Agent evidence Package byte fuse is exhausted",
            )
        return EngineeringAgentEvidencePackage(
            package_id=package_id,
            turn_id=request.turn_id,
            origin_work_state_digest=work_state.digest,
            support_observations=support,
            boundary_observations=boundary,
            digest=digest_of(core),
        )

    def _seal_draft(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        work_state: EngineeringAgentWorkState,
        package: EngineeringAgentEvidencePackage,
        proposal: EngineeringAgentDraftProposal,
        observations: tuple[EngineeringAgentToolObservation, ...],
    ) -> EngineeringAgentAnswerDraft:
        if not isinstance(proposal.response_kind, EngineeringAgentResponseKind):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent draft uses an invalid response kind",
            )
        _response_text(proposal.content)
        if any(
            not isinstance(item, EngineeringAgentClaimProposal)
            for item in proposal.claims
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent draft Claims must use the typed contract",
            )
        for claim in proposal.claims:
            if claim != EngineeringAgentClaimProposal.create(
                statement=claim.statement,
                support_observation_ids=claim.support_observation_ids,
                support_citation_refs=claim.support_citation_refs,
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Agent draft Claim identity is invalid",
                )
        if (
            proposal.response_kind is EngineeringAgentResponseKind.ANSWER
            and not proposal.claims
        ) or (
            proposal.response_kind is not EngineeringAgentResponseKind.ANSWER
            and proposal.claims
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent draft Claim shape does not match its response kind",
            )
        if (
            proposal.response_kind is EngineeringAgentResponseKind.LIMITATION
            and not proposal.boundary_observation_ids
        ) or (
            proposal.response_kind is EngineeringAgentResponseKind.CLARIFICATION
            and proposal.boundary_observation_ids
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent draft boundary evidence does not match its response kind",
            )
        packaged_observations = (
            *package.support_observations,
            *package.boundary_observations,
        )
        _validate_evidence_package_identity(package)
        if (
            package.turn_id != request.turn_id
            or work_state.turn_id != request.turn_id
            or not _package_matches_observations(package, observations)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "answer Package does not match the current Turn and sealed observations",
            )
        by_id = {item.observation_id: item for item in packaged_observations}
        if proposal.response_kind is EngineeringAgentResponseKind.ANSWER:
            for claim in proposal.claims:
                claim_citation_refs = set(claim.support_citation_refs)
                for observation_id in claim.support_observation_ids:
                    observation = by_id.get(observation_id)
                    if (
                        observation is None
                        or observation.disposition
                        is not EngineeringAgentEvidenceDisposition.SUPPORT
                    ):
                        raise DomainError(
                            ErrorCode.CONTROL_STATE_DENIED,
                            "answer Claim references unavailable or non-support evidence",
                        )
                    if observation.citation_refs and not claim_citation_refs.intersection(
                        observation.citation_refs
                    ):
                        raise DomainError(
                            ErrorCode.CONTROL_STATE_DENIED,
                            "answer Claim must select a Citation from every cited Source observation",
                        )
                available_citation_refs = {
                    citation_ref
                    for observation_id in claim.support_observation_ids
                    for citation_ref in by_id[observation_id].citation_refs
                }
                if not claim_citation_refs.issubset(available_citation_refs):
                    raise DomainError(
                        ErrorCode.CONTROL_STATE_DENIED,
                        "answer Claim selects a Citation outside its supporting observations",
                    )
        for observation_id in proposal.boundary_observation_ids:
            observation = by_id.get(observation_id)
            if (
                observation is None
                or observation.disposition
                is not EngineeringAgentEvidenceDisposition.BOUNDARY
            ):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "limitation references unavailable or non-boundary evidence",
                )
        answer_id = self._new_id("agent_answer")
        core = {
            "schema": "ENGINEERING_AGENT_ANSWER@2",
            "answer_id": answer_id.value,
            "turn_id": request.turn_id.value,
            "work_state_digest": work_state.digest.value,
            "package_digest": package.digest.value,
            "response_kind": proposal.response_kind.value,
            "content": proposal.content,
            "claims": tuple(
                {
                    "statement": claim.statement,
                    "support_observation_ids": tuple(
                        item.value for item in claim.support_observation_ids
                    ),
                    "support_citation_refs": claim.support_citation_refs,
                }
                for claim in proposal.claims
            ),
            "boundary_observation_ids": tuple(
                item.value for item in proposal.boundary_observation_ids
            ),
        }
        return EngineeringAgentAnswerDraft(
            answer_id=answer_id,
            turn_id=request.turn_id,
            work_state_digest=work_state.digest,
            package_digest=package.digest,
            response_kind=proposal.response_kind,
            content=proposal.content,
            claims=proposal.claims,
            boundary_observation_ids=proposal.boundary_observation_ids,
            digest=digest_of(core),
        )

    def _seal_review(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        work_state: EngineeringAgentWorkState,
        package: EngineeringAgentEvidencePackage,
        draft: EngineeringAgentAnswerDraft,
        proposal: EngineeringAgentReviewProposal,
        focus: EngineeringAgentReviewFocus,
    ) -> EngineeringAgentReview:
        if (
            not isinstance(proposal.decision, EngineeringAgentReviewDecision)
            or proposal.focus is not focus
            or any(
                not isinstance(item, EngineeringAgentReviewFinding)
                for item in proposal.findings
            )
            or any(
                not isinstance(
                    item,
                    EngineeringAgentContentCoverageAssessment,
                )
                for item in proposal.content_coverage_assessments
            )
            or any(
                not isinstance(
                    item,
                    EngineeringAgentEvidenceBoundaryAssessment,
                )
                for item in proposal.evidence_boundary_assessments
            )
            or any(
                not isinstance(
                    item,
                    EngineeringAgentBoundaryRelevanceAssessment,
                )
                for item in proposal.boundary_relevance_assessments
            )
            or not isinstance(
                proposal.requirement_coverage_assessment,
                EngineeringAgentRequirementCoverageAssessment,
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Reviewer proposal violates the typed focus or decision contract",
            )
        if (
            proposal.decision is EngineeringAgentReviewDecision.APPROVED
            and proposal.findings
        ) or (
            proposal.decision is EngineeringAgentReviewDecision.FINDINGS
            and not proposal.findings
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Reviewer decision and Finding shape are inconsistent",
            )
        expected_challenges = (
            project_engineering_agent_evidence_boundary_challenges(
                package,
                draft,
            )
            if focus
            is EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE
            else ()
        )
        expected_relevance_challenges = (
            project_engineering_agent_boundary_relevance_challenges(
                package,
                draft,
            )
            if focus
            is EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE
            else ()
        )
        expected_content_units = project_engineering_agent_draft_content_units(
            draft.content
        )
        if tuple(
            item.content_unit_index
            for item in proposal.content_coverage_assessments
        ) != tuple(item.content_unit_index for item in expected_content_units):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Reviewer did not disposition the exact ordered Draft content units",
            )
        expected_challenge_ids = tuple(
            item.challenge_id for item in expected_challenges
        )
        assessment_ids = tuple(
            item.challenge_id
            for item in proposal.evidence_boundary_assessments
        )
        if assessment_ids != expected_challenge_ids:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Reviewer did not disposition the exact ordered caller evidence challenges",
            )
        if tuple(
            item.challenge_id
            for item in proposal.boundary_relevance_assessments
        ) != tuple(
            item.challenge_id for item in expected_relevance_challenges
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Reviewer did not disposition the exact ordered boundary relevance challenges",
            )
        challenge_by_id = {
            item.challenge_id: item for item in expected_challenges
        }
        relevance_challenge_by_id = {
            item.challenge_id: item for item in expected_relevance_challenges
        }
        finding_by_code = {item.code: item for item in proposal.findings}
        if len(finding_by_code) != len(proposal.findings):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Reviewer Finding codes must be unique within one Review",
            )
        selected_boundary_ids = set(draft.boundary_observation_ids)
        content_unit_by_index = {
            item.content_unit_index: item for item in expected_content_units
        }
        for assessment in proposal.content_coverage_assessments:
            expected_assessment = EngineeringAgentContentCoverageAssessment.create(
                content_unit_index=assessment.content_unit_index,
                disposition=assessment.disposition,
                claim_indices=assessment.claim_indices,
                boundary_observation_ids=assessment.boundary_observation_ids,
                finding_code=assessment.finding_code,
            )
            if assessment != expected_assessment:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Reviewer content coverage assessment identity is invalid",
                )
            if any(
                index >= len(draft.claims)
                for index in assessment.claim_indices
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Reviewer content coverage references an unknown Claim",
                )
            if not set(assessment.boundary_observation_ids).issubset(
                selected_boundary_ids
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Reviewer content coverage references an unselected Boundary",
                )
            if focus is EngineeringAgentReviewFocus.COMPREHENSIVE:
                if assessment.boundary_observation_ids or (
                    assessment.disposition
                    is EngineeringAgentContentCoverageDisposition.BOUNDARY_REVIEW_DEFERRED
                    and not package.boundary_observations
                ):
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "comprehensive content coverage must defer only a present redacted Boundary",
                    )
            elif (
                assessment.disposition
                is EngineeringAgentContentCoverageDisposition.BOUNDARY_REVIEW_DEFERRED
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "focused content coverage cannot defer an exact Boundary decision",
                )
            if (
                assessment.disposition
                is EngineeringAgentContentCoverageDisposition.DEFECT
                and assessment.finding_code not in finding_by_code
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "a defective Draft content unit must bind an existing Finding",
                )
            content_unit = content_unit_by_index[
                assessment.content_unit_index
            ]
            if (
                engineering_agent_content_coverage_unmatched_claim_assertion_replicas(
                    draft,
                    content_unit,
                    assessment,
                )
                or engineering_agent_content_coverage_unmatched_inline_code_anchors(
                    package,
                    draft,
                    content_unit,
                    assessment,
                )
                or engineering_agent_content_coverage_nonassertive_inline_code_anchors(
                    content_unit,
                    assessment,
                )
                or engineering_agent_content_coverage_nonassertive_body_fragments(
                    draft,
                    content_unit,
                    assessment,
                )
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Reviewer content coverage has invalid assertion closure",
                )
        requirement_coverage = proposal.requirement_coverage_assessment
        expected_requirement_coverage = (
            EngineeringAgentRequirementCoverageAssessment.create(
                current_user_requirement=(
                    requirement_coverage.current_user_requirement
                ),
                coverage_summary=requirement_coverage.coverage_summary,
                disposition=requirement_coverage.disposition,
                finding_code=requirement_coverage.finding_code,
            )
        )
        if requirement_coverage != expected_requirement_coverage:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Reviewer requirement coverage identity is invalid",
            )
        if (
            requirement_coverage.current_user_requirement
            != request.user_message.content
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Reviewer requirement coverage did not bind the exact current User Message",
            )
        if (
            requirement_coverage.disposition
            is EngineeringAgentRequirementCoverageDisposition.MATERIAL_REQUIREMENT_MISSING_OR_MISALIGNED
        ):
            finding = finding_by_code.get(
                requirement_coverage.finding_code or ""
            )
            if finding is None or finding.claim_index is not None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "missing or misaligned requirement coverage must bind a global Finding",
                )
        for assessment in proposal.evidence_boundary_assessments:
            if not engineering_agent_evidence_boundary_assessment_matches_challenge(
                challenge_by_id[assessment.challenge_id],
                assessment,
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Reviewer caller-scope classification contradicts the trusted challenge",
                )
            if (
                assessment.disposition
                is (
                    EngineeringAgentEvidenceBoundaryAssessmentDisposition.CLAIM_EXCEEDS_CALLER_EVIDENCE
                )
            ):
                finding = finding_by_code.get(assessment.finding_code or "")
                if (
                    finding is None
                    or finding.claim_index
                    != challenge_by_id[assessment.challenge_id].claim_index
                ):
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "an exceeded caller evidence boundary must bind a Finding on its Claim",
                    )
        for assessment in proposal.boundary_relevance_assessments:
            if not engineering_agent_boundary_relevance_assessment_matches_challenge(
                relevance_challenge_by_id[assessment.challenge_id],
                assessment,
                draft_content=draft.content,
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Reviewer disclosure classification contradicts the Draft reference set",
                )
            if (
                assessment.disposition
                in _BOUNDARY_RELEVANCE_AUDIT_ONLY_DISPOSITIONS
            ):
                finding = finding_by_code.get(assessment.finding_code or "")
                if (
                    finding is None
                    or finding.claim_index is not None
                    or finding.requires_evidence
                ):
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "an audit-only boundary must bind one global no-evidence relevance Finding",
                    )
        if focus is EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE:
            expected_finding_codes = {
                assessment.finding_code
                for assessment in proposal.evidence_boundary_assessments
                if assessment.disposition
                is EngineeringAgentEvidenceBoundaryAssessmentDisposition.CLAIM_EXCEEDS_CALLER_EVIDENCE
                and assessment.finding_code is not None
            } | {
                assessment.finding_code
                for assessment in proposal.boundary_relevance_assessments
                if assessment.disposition
                in _BOUNDARY_RELEVANCE_AUDIT_ONLY_DISPOSITIONS
                and assessment.finding_code is not None
            }
            expected_finding_codes.update(
                assessment.finding_code
                for assessment in proposal.content_coverage_assessments
                if assessment.disposition
                is EngineeringAgentContentCoverageDisposition.DEFECT
                and assessment.finding_code is not None
            )
            if (
                requirement_coverage.disposition
                is EngineeringAgentRequirementCoverageDisposition.MATERIAL_REQUIREMENT_MISSING_OR_MISALIGNED
                and requirement_coverage.finding_code is not None
            ):
                expected_finding_codes.add(requirement_coverage.finding_code)
            if set(finding_by_code) != expected_finding_codes:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "focused Reviewer Findings must equal the exact challenge-bound Finding set",
                )
        if proposal.decision is EngineeringAgentReviewDecision.APPROVED and (
            requirement_coverage.disposition
            is not EngineeringAgentRequirementCoverageDisposition.FULLY_ADDRESSED
            or any(
                item.disposition
                is EngineeringAgentContentCoverageDisposition.DEFECT
                for item in proposal.content_coverage_assessments
            )
            or any(
                item.disposition
                is not EngineeringAgentEvidenceBoundaryAssessmentDisposition.WITHIN_CALLER_EVIDENCE
                for item in proposal.evidence_boundary_assessments
            )
            or any(
                not engineering_agent_boundary_relevance_assessment_is_closed(item)
                for item in proposal.boundary_relevance_assessments
            )
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "an approved Review cannot leave an evidence-boundary challenge open",
            )
        _text(proposal.model_call_ref, "Reviewer model call reference")
        for finding in proposal.findings:
            if finding.claim_index is not None and finding.claim_index >= len(
                draft.claims
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Reviewer Finding references an unknown Claim",
                )
        review_id = self._new_id("agent_review")
        core = {
            "schema": "ENGINEERING_AGENT_REVIEW@5",
            "review_id": review_id.value,
            "turn_id": request.turn_id.value,
            "work_state_digest": work_state.digest.value,
            "package_digest": package.digest.value,
            "answer_digest": draft.digest.value,
            "decision": proposal.decision.value,
            "focus": focus.value,
            "requirement_coverage_assessment": {
                "current_user_requirement": (
                    requirement_coverage.current_user_requirement
                ),
                "coverage_summary": requirement_coverage.coverage_summary,
                "disposition": requirement_coverage.disposition.value,
                "finding_code": requirement_coverage.finding_code,
                "digest": requirement_coverage.digest.value,
            },
            "findings": tuple(
                {
                    "code": item.code,
                    "message": item.message,
                    "requires_evidence": item.requires_evidence,
                    "claim_index": item.claim_index,
                }
                for item in proposal.findings
            ),
            "content_coverage_assessments": tuple(
                {
                    "content_unit_index": item.content_unit_index,
                    "disposition": item.disposition.value,
                    "claim_indices": item.claim_indices,
                    "boundary_observation_ids": tuple(
                        boundary_id.value
                        for boundary_id in item.boundary_observation_ids
                    ),
                    "finding_code": item.finding_code,
                    "digest": item.digest.value,
                }
                for item in proposal.content_coverage_assessments
            ),
            "evidence_boundary_assessments": tuple(
                {
                    "challenge_id": item.challenge_id.value,
                    "evidence_boundary": item.evidence_boundary,
                    "draft_scope": item.draft_scope,
                    "draft_semantic_scopes": tuple(
                        scope.value for scope in item.draft_semantic_scopes
                    ),
                    "disposition": item.disposition.value,
                    "finding_code": item.finding_code,
                    "digest": item.digest.value,
                }
                for item in proposal.evidence_boundary_assessments
            ),
            "boundary_relevance_assessments": tuple(
                {
                    "challenge_id": item.challenge_id.value,
                    "user_requirement": item.user_requirement,
                    "boundary_scope": item.boundary_scope,
                    "draft_disclosed_fragments": (
                        item.draft_disclosed_fragments
                    ),
                    "disposition": item.disposition.value,
                    "finding_code": item.finding_code,
                    "digest": item.digest.value,
                }
                for item in proposal.boundary_relevance_assessments
            ),
            "model_call_ref": proposal.model_call_ref,
        }
        return EngineeringAgentReview(
            review_id=review_id,
            turn_id=request.turn_id,
            work_state_digest=work_state.digest,
            package_digest=package.digest,
            answer_digest=draft.digest,
            decision=proposal.decision,
            findings=proposal.findings,
            focus=focus,
            requirement_coverage_assessment=requirement_coverage,
            content_coverage_assessments=(
                proposal.content_coverage_assessments
            ),
            evidence_boundary_assessments=(
                proposal.evidence_boundary_assessments
            ),
            boundary_relevance_assessments=(
                proposal.boundary_relevance_assessments
            ),
            model_call_ref=proposal.model_call_ref,
            digest=digest_of(core),
        )

    def _successful_outcome(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        work_state: EngineeringAgentWorkState,
        package: EngineeringAgentEvidencePackage,
        draft: EngineeringAgentAnswerDraft,
        review: EngineeringAgentReview,
        authorization: EngineeringAgentDeliveryAuthorization,
        provider_dispatch_count: int,
        model_dispatch_receipt_refs: tuple[str, ...],
    ) -> EngineeringTurnExecutionOutcome:
        kind = {
            EngineeringAgentResponseKind.ANSWER: ConversationMessageKind.ANSWER,
            EngineeringAgentResponseKind.CLARIFICATION: ConversationMessageKind.CLARIFICATION,
            EngineeringAgentResponseKind.LIMITATION: ConversationMessageKind.LIMITATION,
        }[draft.response_kind]
        quality = {
            EngineeringAgentResponseKind.ANSWER: "ACCEPTED",
            EngineeringAgentResponseKind.CLARIFICATION: "REVIEWED_CLARIFICATION",
            EngineeringAgentResponseKind.LIMITATION: "REVIEWED_LIMITATION",
        }[draft.response_kind]
        reviewed = request.snapshot_before.context.reviewed_conclusion_refs
        if draft.response_kind is EngineeringAgentResponseKind.ANSWER:
            reviewed = (*reviewed, draft.answer_id.value)
        included = _append_unique(
            request.snapshot_before.context.included_user_message_ids,
            request.user_message.message_id,
        )
        citations = _draft_citations(package=package, draft=draft)
        return EngineeringTurnExecutionOutcome.succeeded(
            request_digest=request.request_digest,
            assistant_kind=kind,
            assistant_content=draft.content,
            included_user_message_ids=included,
            accepted_correction_message_ids=work_state.accepted_correction_message_ids,
            reviewed_conclusion_refs=reviewed,
            superseded_conclusion_refs=work_state.superseded_conclusion_refs,
            reducer_status="EXECUTED_APPLICATION_SEALED",
            work_state_ref=work_state.work_state_id.value,
            work_state_revision=work_state.revision,
            work_state_digest=work_state.digest,
            evidence_package_ref=package.package_id.value,
            answer_ref=draft.answer_id.value,
            review_ref=review.review_id.value,
            delivery_authorization_ref=authorization.authorization_ref,
            provider_dispatch_count=provider_dispatch_count,
            model_dispatch_receipt_refs=model_dispatch_receipt_refs,
            quality_status=quality,
            citations=citations,
        )

    def _failed_outcome(
        self,
        *,
        request: EngineeringTurnExecutionRequest,
        work_state: EngineeringAgentWorkState | None,
        package: EngineeringAgentEvidencePackage | None,
        draft: EngineeringAgentAnswerDraft | None,
        review: EngineeringAgentReview | None,
        provider_dispatch_count: int,
        model_dispatch_receipt_refs: tuple[str, ...],
        failure_code: str,
        provider_failure_classification: EngineeringProviderFailureClassification | None = None,
        provider_failure_code: str | None = None,
        provider_http_status: int | None = None,
        provider_http_failure_evidence_digest: Digest | None = None,
    ) -> EngineeringTurnExecutionOutcome:
        message = (
            "主工程 Agent 在本 Turn 的高安全熔断内未形成可授权结果；"
            "本 Turn 已失败关闭，Conversation 仍可继续使用。"
        )
        included = _append_unique(
            request.snapshot_before.context.included_user_message_ids,
            request.user_message.message_id,
        )
        return EngineeringTurnExecutionOutcome.failed(
            request_digest=request.request_digest,
            assistant_content=message,
            included_user_message_ids=included,
            accepted_correction_message_ids=(
                work_state.accepted_correction_message_ids
                if work_state is not None
                else request.snapshot_before.context.accepted_correction_message_ids
            ),
            reviewed_conclusion_refs=request.snapshot_before.context.reviewed_conclusion_refs,
            superseded_conclusion_refs=(
                work_state.superseded_conclusion_refs
                if work_state is not None
                else request.snapshot_before.context.superseded_conclusion_refs
            ),
            reducer_status="AGENT_EXECUTION_FAILED_CLOSED",
            work_state_ref=(
                work_state.work_state_id.value
                if work_state is not None
                else request.snapshot_before.context.work_state_ref
            ),
            work_state_revision=(
                work_state.revision
                if work_state is not None
                else (
                    request.snapshot_before.context.work_state_revision
                    if request.snapshot_before.context.work_state_ref is not None
                    else None
                )
            ),
            work_state_digest=(
                work_state.digest
                if work_state is not None
                else request.snapshot_before.context.work_state_digest
            ),
            failure_code=failure_code,
            failure_message=message,
            evidence_package_ref=(package.package_id.value if package else None),
            answer_ref=(draft.answer_id.value if draft else None),
            review_ref=(review.review_id.value if review else None),
            provider_dispatch_count=provider_dispatch_count,
            model_dispatch_receipt_refs=model_dispatch_receipt_refs,
            provider_failure_classification=(
                provider_failure_classification
            ),
            provider_failure_code=provider_failure_code,
            provider_http_status=provider_http_status,
            provider_http_failure_evidence_digest=(
                provider_http_failure_evidence_digest
            ),
        )

    def _new_id(self, kind: str) -> StableId:
        with self._id_lock:
            value = self._id_generator.new(kind)
            if value in self._issued_ids:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Agent ID generator returned a duplicate stable ID",
                )
            self._issued_ids.add(value)
            return value

    def _record_model_call(self, turn_refs: list[str], value: str) -> None:
        value = _text(value, "model call reference")
        with self._model_call_lock:
            if value in self._issued_model_call_refs:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "model call references cannot be replayed across Turns",
                )
            self._issued_model_call_refs.add(value)
        turn_refs.append(value)

    def _authorized_operations(
        self,
        request: EngineeringTurnExecutionRequest,
    ) -> tuple[EngineeringAgentToolOperation, ...]:
        operations = tuple(
            item
            for item in self._available_operations
            if item is EngineeringAgentToolOperation.WORLD_MODEL_QUERY
            or request.binding.source_access_status is RuntimeCapabilityStatus.READY
        )
        if not operations:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "the Turn has no authorized Agent tool operation",
            )
        return operations

    def _load_previous_work_state(
        self,
        request: EngineeringTurnExecutionRequest,
    ) -> EngineeringAgentWorkState | None:
        conversation_id = request.snapshot_before.conversation.conversation_id
        context = request.snapshot_before.context
        previous = self._work_state_repository.load(conversation_id)
        if context.work_state_ref is None:
            if previous is not None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Agent state exists outside the sealed Conversation Context",
                )
            return None
        if (
            previous is None
            or previous.work_state_id.value != context.work_state_ref
            or previous.revision != context.work_state_revision
            or previous.digest != context.work_state_digest
            or previous.accepted_correction_message_ids
            != context.accepted_correction_message_ids
            or previous.superseded_conclusion_refs
            != context.superseded_conclusion_refs
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Agent state does not match the sealed Conversation Context",
            )
        return previous

    def _remember_work_state(self, work_state: EngineeringAgentWorkState) -> None:
        self._work_state_repository.commit(work_state)


def _validate_delivery_authorization(
    *,
    request: EngineeringTurnExecutionRequest,
    work_state: EngineeringAgentWorkState,
    package: EngineeringAgentEvidencePackage,
    draft: EngineeringAgentAnswerDraft,
    review: EngineeringAgentReview,
    authorization: EngineeringAgentDeliveryAuthorization,
) -> None:
    _text(authorization.authorization_ref, "Delivery authorization reference")
    if review.decision is not EngineeringAgentReviewDecision.APPROVED:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Response Control cannot authorize a non-approved Review",
        )
    if (
        authorization.turn_request_digest != request.request_digest
        or authorization.work_state_digest != work_state.digest
        or authorization.package_digest != package.digest
        or authorization.answer_digest != draft.digest
        or authorization.review_digest != review.digest
        or review.requirement_coverage_assessment.current_user_requirement
        != request.user_message.content
        or review.requirement_coverage_assessment.disposition
        is not EngineeringAgentRequirementCoverageDisposition.FULLY_ADDRESSED
        or not _engineering_agent_review_closes_boundary_challenges(
            package=package,
            draft=draft,
            review=review,
        )
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Delivery authorization is bound to different Turn artifacts",
        )


def _engineering_agent_review_closes_boundary_challenges(
    *,
    package: EngineeringAgentEvidencePackage,
    draft: EngineeringAgentAnswerDraft,
    review: EngineeringAgentReview,
) -> bool:
    content_units = project_engineering_agent_draft_content_units(draft.content)
    content_assessments = review.content_coverage_assessments
    if (
        tuple(item.content_unit_index for item in content_assessments)
        != tuple(item.content_unit_index for item in content_units)
        or any(
            item.disposition
            in {
                EngineeringAgentContentCoverageDisposition.BOUNDARY_REVIEW_DEFERRED,
                EngineeringAgentContentCoverageDisposition.DEFECT,
            }
            for item in content_assessments
        )
        or any(
            index >= len(draft.claims)
            for item in content_assessments
            for index in item.claim_indices
        )
        or any(
            boundary_id not in draft.boundary_observation_ids
            for item in content_assessments
            for boundary_id in item.boundary_observation_ids
        )
        or any(
            (
                engineering_agent_content_coverage_unmatched_claim_assertion_replicas(
                    draft,
                    content_unit,
                    assessment,
                )
                or engineering_agent_content_coverage_unmatched_inline_code_anchors(
                    package,
                    draft,
                    content_unit,
                    assessment,
                )
                or engineering_agent_content_coverage_nonassertive_inline_code_anchors(
                    content_unit,
                    assessment,
                )
                or engineering_agent_content_coverage_nonassertive_body_fragments(
                    draft,
                    content_unit,
                    assessment,
                )
            )
            for content_unit, assessment in zip(
                content_units,
                content_assessments,
            )
        )
    ):
        return False
    expected = project_engineering_agent_evidence_boundary_challenges(
        package,
        draft,
    )
    expected_relevance = project_engineering_agent_boundary_relevance_challenges(
        package,
        draft,
    )
    assessments = review.evidence_boundary_assessments
    relevance_assessments = review.boundary_relevance_assessments
    if (
        review.requirement_coverage_assessment.disposition
        is not EngineeringAgentRequirementCoverageDisposition.FULLY_ADDRESSED
    ):
        return False
    challenge_by_id = {item.challenge_id: item for item in expected}
    relevance_challenge_by_id = {
        item.challenge_id: item for item in expected_relevance
    }
    if not expected and not expected_relevance:
        return (
            review.focus is EngineeringAgentReviewFocus.COMPREHENSIVE
            and not assessments
            and not relevance_assessments
        )
    return (
        review.focus
        is EngineeringAgentReviewFocus.EVIDENCE_BOUNDARY_CHALLENGE
        and tuple(item.challenge_id for item in assessments)
        == tuple(item.challenge_id for item in expected)
        and tuple(item.challenge_id for item in relevance_assessments)
        == tuple(item.challenge_id for item in expected_relevance)
        and all(
            item.disposition
            is EngineeringAgentEvidenceBoundaryAssessmentDisposition.WITHIN_CALLER_EVIDENCE
            for item in assessments
        )
        and all(
            engineering_agent_evidence_boundary_assessment_matches_challenge(
                challenge_by_id[item.challenge_id], item
            )
            for item in assessments
        )
        and all(
            engineering_agent_boundary_relevance_assessment_is_closed(item)
            for item in relevance_assessments
        )
        and all(
            engineering_agent_boundary_relevance_assessment_matches_challenge(
                relevance_challenge_by_id[item.challenge_id],
                item,
                draft_content=draft.content,
            )
            for item in relevance_assessments
        )
    )


def _package_matches_observations(
    package: EngineeringAgentEvidencePackage,
    observations: Sequence[EngineeringAgentToolObservation],
) -> bool:
    support = tuple(
        item
        for item in observations
        if item.disposition is EngineeringAgentEvidenceDisposition.SUPPORT
    )
    boundary = tuple(
        item
        for item in observations
        if item.disposition is EngineeringAgentEvidenceDisposition.BOUNDARY
    )
    return (
        package.support_observations == support
        and package.boundary_observations == boundary
    )


def _validate_evidence_package_identity(
    package: EngineeringAgentEvidencePackage,
) -> None:
    """Validate one immutable current-Turn evidence set.

    ``origin_work_state_digest`` records the Work State that first sealed the
    evidence set.  A Reviewer-directed rewrite can intentionally reuse that
    exact Package while producing a successor Work State, Draft, and Review;
    the Package origin therefore is not the Delivery Work State identity.
    """

    if not isinstance(package, EngineeringAgentEvidencePackage):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Agent evidence Package is untyped",
        )
    observations = (
        *package.support_observations,
        *package.boundary_observations,
    )
    if (
        any(
            not isinstance(item, EngineeringAgentToolObservation)
            for item in observations
        )
        or any(
            item.disposition
            is not EngineeringAgentEvidenceDisposition.SUPPORT
            for item in package.support_observations
        )
        or any(
            item.disposition
            is not EngineeringAgentEvidenceDisposition.BOUNDARY
            for item in package.boundary_observations
        )
        or len({item.observation_id for item in observations})
        != len(observations)
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Agent evidence Package partitions are invalid",
        )
    core = {
        "schema": "ENGINEERING_AGENT_EVIDENCE_PACKAGE@1",
        "package_id": package.package_id.value,
        "turn_id": package.turn_id.value,
        "origin_work_state_digest": package.origin_work_state_digest.value,
        "support_observations": tuple(
            (item.observation_id.value, item.digest.value)
            for item in package.support_observations
        ),
        "boundary_observations": tuple(
            (item.observation_id.value, item.digest.value)
            for item in package.boundary_observations
        ),
    }
    if package.digest != digest_of(core):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Engineering Agent evidence Package identity is invalid",
        )


def _draft_citations(
    *,
    package: EngineeringAgentEvidencePackage,
    draft: EngineeringAgentAnswerDraft,
) -> tuple[EngineeringTurnCitation, ...]:
    """Project only authority Citations reached by the delivered Draft."""

    observations = {
        item.observation_id: item
        for item in (
            *package.support_observations,
            *package.boundary_observations,
        )
    }
    projected_by_ref: dict[str, EngineeringTurnCitation] = {}
    projected: list[EngineeringTurnCitation] = []

    def project_reference(
        observation: EngineeringAgentToolObservation,
        citation_ref: str,
    ) -> None:
        receipt = observation.authority_receipt
        if receipt is None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Draft Citation projection lacks an authority receipt",
            )
        authority_citations = {
            item.citation_ref: item for item in receipt.citations
        }
        if len(authority_citations) != len(receipt.citations):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Citation authority receipt contains duplicate references",
            )
        citation = authority_citations.get(citation_ref)
        if citation is None or citation_ref not in observation.citation_refs:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "selected Draft Citation is absent from its supporting Observation",
            )
        turn_citation = EngineeringTurnCitation.create(
            citation_ref=citation.citation_ref,
            evidence_class=citation.evidence_class,
            source_revision=citation.source_revision,
            locator=citation.locator,
            modality=citation.modality,
            content_digest=citation.content_digest,
        )
        if turn_citation.digest != citation.digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Turn Citation projection changed the authority identity",
            )
        previous = projected_by_ref.get(citation_ref)
        if previous is not None:
            if previous != turn_citation:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Turn Citation reference resolves to inconsistent identities",
                )
            return
        projected_by_ref[citation_ref] = turn_citation
        projected.append(turn_citation)

    for claim in draft.claims:
        claim_observations: list[EngineeringAgentToolObservation] = []
        for observation_id in claim.support_observation_ids:
            observation = observations.get(observation_id)
            if observation is None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Draft Citation projection references an unknown Observation",
                )
            claim_observations.append(observation)
        for citation_ref in claim.support_citation_refs:
            matching = tuple(
                observation
                for observation in claim_observations
                if citation_ref in observation.citation_refs
            )
            if not matching:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Draft Citation selection is outside its Claim evidence",
                )
            for observation in matching:
                project_reference(observation, citation_ref)

    for observation_id in draft.boundary_observation_ids:
        observation = observations.get(observation_id)
        if observation is None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Draft Citation projection references an unknown Observation",
            )
        for citation_ref in observation.citation_refs:
            project_reference(observation, citation_ref)
    return tuple(projected)


def _append_unique(values: Sequence[StableId], value: StableId) -> tuple[StableId, ...]:
    normalized = tuple(values)
    return normalized if value in normalized else (*normalized, value)


def _response_text(value: str) -> str:
    value = _bounded_text(value, "Agent response", maximum_bytes=48_000)
    if len(value) > 16_000:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Agent response exceeds the Chat character boundary",
        )
    return value


def _observation_text(value: str) -> str:
    return _bounded_text(value, "tool observation", maximum_bytes=256_000)


def _repository_revision(value: str) -> str:
    normalized = _text(value, "repository revision").casefold()
    if len(normalized) != 40 or any(
        character not in "0123456789abcdef" for character in normalized
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "repository revision must be a full Git object ID",
        )
    return normalized


def _optional_text(value: str | None, label: str) -> str | None:
    return None if value is None else _text(value, label)


def _model_receipt_refs(
    audit: _EngineeringAgentExecutionAudit,
) -> tuple[str, ...]:
    references = tuple(item.digest.value for item in audit.model_call_receipts)
    if len(references) != len(set(references)):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Agent model call receipts cannot be replayed",
        )
    return references


def _record_model_receipt(
    audit: _EngineeringAgentExecutionAudit,
    receipt: EngineeringAgentModelCallReceipt,
) -> None:
    expected = EngineeringAgentModelCallReceipt.create(
        model_call_ref=receipt.model_call_ref,
        gateway_call_ref=receipt.gateway_call_ref,
        role=receipt.role,
        state=receipt.state,
        failure_kind=receipt.failure_kind,
        failure_code=receipt.failure_code,
        provider_http_status=receipt.provider_http_status,
        provider_http_failure_evidence_digest=(
            receipt.provider_http_failure_evidence_digest
        ),
    )
    if receipt != expected or any(
        item.digest == receipt.digest for item in audit.model_call_receipts
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Agent model call receipt identity is invalid or replayed",
        )
    audit.model_call_receipts.append(receipt)
    audit.provider_dispatch_count += receipt.provider_dispatch_count


def _exact_model_receipt_sequence(
    receipts: Sequence[EngineeringAgentModelCallReceipt],
    *,
    role: EngineeringAgentModelRole,
    terminal_must_succeed: bool,
) -> bool:
    normalized = tuple(receipts)
    if not normalized:
        return False
    for receipt in normalized:
        expected = EngineeringAgentModelCallReceipt.create(
            model_call_ref=receipt.model_call_ref,
            gateway_call_ref=receipt.gateway_call_ref,
            role=receipt.role,
            state=receipt.state,
            failure_kind=receipt.failure_kind,
            failure_code=receipt.failure_code,
            provider_http_status=receipt.provider_http_status,
            provider_http_failure_evidence_digest=(
                receipt.provider_http_failure_evidence_digest
            ),
        )
        if receipt != expected or receipt.role is not role:
            return False
    terminal = normalized[-1]
    if terminal.successful is not terminal_must_succeed:
        return False
    if terminal_must_succeed and any(
        receipt.successful for receipt in normalized[:-1]
    ):
        return False
    if not terminal_must_succeed and any(
        receipt.successful for receipt in normalized
    ):
        return False
    return (
        len({receipt.digest for receipt in normalized}) == len(normalized)
        and len({receipt.model_call_ref for receipt in normalized})
        == len(normalized)
    )


def _model_failure_code(receipt: EngineeringAgentModelCallReceipt) -> str:
    role = (
        "AGENT"
        if receipt.role is EngineeringAgentModelRole.PRIMARY_AGENT
        else "REVIEWER"
    )
    outcome = {
        EngineeringAgentModelDispatchState.PRE_DISPATCH_REJECTED: "PRE_DISPATCH_REJECTED",
        EngineeringAgentModelDispatchState.DISPATCHED_REJECTED: "MODEL_CALL_REJECTED",
        EngineeringAgentModelDispatchState.DISPATCHED_OUTCOME_UNKNOWN: "MODEL_OUTCOME_UNKNOWN",
        EngineeringAgentModelDispatchState.REPLAYED_REJECTED: "MODEL_CALL_REJECTED",
        EngineeringAgentModelDispatchState.REPLAYED_OUTCOME_UNKNOWN: "MODEL_OUTCOME_UNKNOWN",
    }.get(receipt.state)
    if outcome is None:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "a successful model receipt cannot produce a failure code",
        )
    return f"{role}_{outcome}"


def _provider_failure_classification(
    failure_kind: EngineeringAgentModelFailureKind | None,
) -> EngineeringProviderFailureClassification | None:
    return {
        EngineeringAgentModelFailureKind.PROVIDER_UNAVAILABLE: (
            EngineeringProviderFailureClassification.PROVIDER_UNAVAILABLE
        ),
        EngineeringAgentModelFailureKind.PROVIDER_HTTP_ERROR: (
            EngineeringProviderFailureClassification.PROVIDER_HTTP_ERROR
        ),
        EngineeringAgentModelFailureKind.PROVIDER_OUTCOME_UNKNOWN: (
            EngineeringProviderFailureClassification.PROVIDER_OUTCOME_UNKNOWN
        ),
        EngineeringAgentModelFailureKind.PROVIDER_OUTPUT_INVALID: (
            EngineeringProviderFailureClassification.PROVIDER_OUTPUT_INVALID
        ),
    }.get(failure_kind)


def _unique_bounded_texts(values: Sequence[str], label: str) -> tuple[str, ...]:
    normalized = tuple(_bounded_text(item, label) for item in values)
    if len(normalized) != len(set(normalized)):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label}s must be unique")
    return normalized


def _unique_texts(values: Sequence[str], label: str) -> tuple[str, ...]:
    normalized = tuple(_text(item, label) for item in values)
    if len(normalized) != len(set(normalized)):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label}s must be unique")
    return normalized


def _bounded_text(value: str, label: str, *, maximum_bytes: int = 8_192) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must be non-empty without surrounding whitespace",
        )
    if len(value.encode("utf-8")) > maximum_bytes:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} exceeds its boundary",
        )
    return value


def _draft_content_unit_text(
    value: str,
    label: str,
    *,
    maximum_bytes: int = 8_192,
) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            f"{label} must contain visible non-whitespace text",
        )
    if len(value.encode("utf-8")) > maximum_bytes:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} exceeds its boundary")
    return value


def _text(value: str, label: str) -> str:
    return _bounded_text(value, label, maximum_bytes=512)


__all__ = [
    "ApplicationOwnedEngineeringAgentTurnExecutor",
    "EngineeringAgentAnswerDraft",
    "EngineeringAgentClaimProposal",
    "EngineeringAgentClaimSemanticScope",
    "EngineeringAgentCitation",
    "EngineeringAgentContentCoverageAssessment",
    "EngineeringAgentContentCoverageDisposition",
    "EngineeringAgentDeliveryAuthorization",
    "EngineeringAgentDeliveryRequest",
    "EngineeringAgentDraftProposal",
    "EngineeringAgentDraftContentUnit",
    "EngineeringAgentDriver",
    "EngineeringAgentDriverModelResult",
    "EngineeringAgentDraftBoundaryProjection",
    "EngineeringAgentBoundaryRelevanceAssessment",
    "EngineeringAgentBoundaryRelevanceAssessmentDisposition",
    "EngineeringAgentBoundaryRelevanceChallenge",
    "EngineeringAgentBoundaryRelevanceChallengeKind",
    "EngineeringAgentEvidenceBoundaryAssessment",
    "EngineeringAgentEvidenceBoundaryAssessmentDisposition",
    "EngineeringAgentEvidenceBoundaryChallenge",
    "EngineeringAgentEvidenceDisposition",
    "EngineeringAgentEvidencePackage",
    "EngineeringAgentInvocation",
    "EngineeringAgentInvocationMode",
    "EngineeringAgentLedgerEntryReceipt",
    "EngineeringAgentLoopLimits",
    "EngineeringAgentModelCallFailure",
    "EngineeringAgentModelCallReceipt",
    "EngineeringAgentModelDispatchState",
    "EngineeringAgentModelFailureKind",
    "EngineeringAgentModelRole",
    "EngineeringAgentResponseControl",
    "EngineeringAgentResponseKind",
    "EngineeringAgentRequirementCoverageAssessment",
    "EngineeringAgentRequirementCoverageDisposition",
    "EngineeringAgentReview",
    "EngineeringAgentReviewDecision",
    "EngineeringAgentReviewFinding",
    "EngineeringAgentReviewFocus",
    "EngineeringAgentReviewProposal",
    "EngineeringAgentReviewRequest",
    "EngineeringAgentReviewer",
    "EngineeringAgentReviewerModelResult",
    "EngineeringAgentToolActionProposal",
    "EngineeringAgentToolAuthorityKind",
    "EngineeringAgentToolAuthorityReceipt",
    "EngineeringAgentToolEvidence",
    "EngineeringAgentToolObservation",
    "EngineeringAgentToolOperation",
    "EngineeringAgentToolPort",
    "EngineeringAgentToolRequest",
    "EngineeringAgentToolResult",
    "EngineeringAgentWorkPhase",
    "EngineeringAgentWorkStateRepository",
    "EngineeringAgentWorkState",
    "EngineeringAgentWorkStateProposal",
    "InMemoryEngineeringAgentWorkStateRepository",
    "SealedEngineeringAgentResponseControl",
    "engineering_agent_boundary_relevance_assessment_is_closed",
    "engineering_agent_boundary_relevance_assessment_matches_challenge",
    "engineering_agent_content_coverage_nonassertive_body_fragments",
    "engineering_agent_content_coverage_nonassertive_inline_code_anchors",
    "engineering_agent_content_coverage_unmatched_claim_assertion_replicas",
    "engineering_agent_content_coverage_unmatched_inline_code_anchors",
    "engineering_agent_evidence_boundary_assessment_matches_challenge",
    "project_engineering_agent_draft_boundaries",
    "project_engineering_agent_draft_content_units",
    "project_engineering_agent_boundary_relevance_challenges",
    "project_engineering_agent_evidence_boundary_challenges",
]
