"""Application-owned control loop for a conversational engineering Agent.

The loop deliberately has no filesystem, Source, shell, network, credential, or
Provider adapter dependency.  A model driver can only propose a full Work State
revision and one closed-catalog action or response.  Trusted ports execute tool
requests, review the sealed evidence-bound draft, and authorize delivery.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Protocol, Sequence

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
    EngineeringTurnExecutionOutcome,
    EngineeringTurnExecutionRequest,
    RuntimeCapabilityStatus,
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

    @classmethod
    def create(
        cls,
        *,
        statement: str,
        support_observation_ids: Sequence[StableId],
    ) -> "EngineeringAgentClaimProposal":
        support = tuple(support_observation_ids)
        if not support or len(support) != len(set(support)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "an answer claim requires unique supporting observations",
            )
        return cls(
            statement=_bounded_text(statement, "answer claim"),
            support_observation_ids=support,
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
            "schema": "ENGINEERING_AGENT_DRAFT_PROPOSAL@1",
            "response_kind": response_kind.value,
            "content": content,
            "claims": tuple(
                {
                    "statement": claim.statement,
                    "support_observation_ids": tuple(
                        item.value for item in claim.support_observation_ids
                    ),
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
class EngineeringAgentInvocation:
    request: EngineeringTurnExecutionRequest
    previous_work_state: EngineeringAgentWorkState | None
    observations: tuple["EngineeringAgentToolObservation", ...]
    review_findings: tuple[EngineeringAgentReviewFinding, ...]
    review_digest: Digest | None
    available_operations: tuple[EngineeringAgentToolOperation, ...]


class EngineeringAgentDriver(Protocol):
    def propose(
        self, invocation: EngineeringAgentInvocation
    ) -> EngineeringAgentWorkStateProposal: ...


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
class EngineeringAgentReviewRequest:
    turn_request: EngineeringTurnExecutionRequest
    work_state: EngineeringAgentWorkState
    package: EngineeringAgentEvidencePackage
    draft: EngineeringAgentAnswerDraft


@dataclass(frozen=True, slots=True)
class EngineeringAgentReviewProposal:
    model_call_ref: str
    decision: EngineeringAgentReviewDecision
    findings: tuple[EngineeringAgentReviewFinding, ...]

    @classmethod
    def create(
        cls,
        *,
        model_call_ref: str,
        decision: EngineeringAgentReviewDecision,
        findings: Sequence[EngineeringAgentReviewFinding] = (),
    ) -> "EngineeringAgentReviewProposal":
        if not isinstance(decision, EngineeringAgentReviewDecision):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer decision is invalid",
            )
        normalized = tuple(findings)
        if any(not isinstance(item, EngineeringAgentReviewFinding) for item in normalized):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Reviewer Findings must use the typed contract",
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
        return cls(
            model_call_ref=_text(model_call_ref, "Reviewer model call reference"),
            decision=decision,
            findings=normalized,
        )


class EngineeringAgentReviewer(Protocol):
    def review(
        self, request: EngineeringAgentReviewRequest
    ) -> EngineeringAgentReviewProposal: ...


@dataclass(frozen=True, slots=True)
class EngineeringAgentReview:
    review_id: StableId
    turn_id: StableId
    work_state_digest: Digest
    package_digest: Digest
    answer_digest: Digest
    decision: EngineeringAgentReviewDecision
    findings: tuple[EngineeringAgentReviewFinding, ...]
    model_call_ref: str
    digest: Digest


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


@dataclass(frozen=True, slots=True)
class EngineeringAgentLoopLimits:
    maximum_agent_steps: int = 12
    maximum_tool_actions: int = 8
    maximum_reviews: int = 3
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
        self._driver = driver
        self._tool_port = tool_port
        self._reviewer = reviewer
        self._response_control = response_control
        self._available_operations = operations
        self._limits = limits
        self._require_tool_authority_receipts = require_tool_authority_receipts
        self._id_generator = id_generator or Uuid4IdGenerator()
        self._id_lock = Lock()
        self._model_call_lock = Lock()
        self._state_lock = Lock()
        self._issued_ids: set[StableId] = set()
        self._issued_model_call_refs: set[str] = set()
        self._current_work_states: dict[StableId, EngineeringAgentWorkState] = {}

    def execute(
        self, request: EngineeringTurnExecutionRequest
    ) -> EngineeringTurnExecutionOutcome:
        audit = _EngineeringAgentExecutionAudit(model_call_refs=[])
        try:
            initial_previous = self._load_previous_work_state(request)
            outcome = self._execute_bounded(request, audit, initial_previous)
        except DomainError:
            outcome = self._failed_outcome(
                request=request,
                work_state=audit.work_state,
                package=audit.package,
                draft=audit.draft,
                review=audit.review,
                provider_dispatch_count=audit.provider_dispatch_count,
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
        minimum_observations_for_draft = 0
        last_package: EngineeringAgentEvidencePackage | None = None
        last_draft: EngineeringAgentAnswerDraft | None = None
        last_review: EngineeringAgentReview | None = None
        available_operations = self._authorized_operations(request)

        for _ in range(self._limits.maximum_agent_steps):
            proposal = self._driver.propose(
                EngineeringAgentInvocation(
                    request=request,
                    previous_work_state=previous,
                    observations=observations,
                    review_findings=review_findings,
                    review_digest=(
                        pending_review.digest if pending_review is not None else None
                    ),
                    available_operations=available_operations,
                )
            )
            audit.provider_dispatch_count += 1
            if not isinstance(proposal, EngineeringAgentWorkStateProposal):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Agent driver returned an untyped Work State proposal",
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
            review_findings = ()
            pending_review = None

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
                        failure_code="AGENT_TOOL_LIMIT_REACHED",
                    )
                observation_batch = self._execute_tool(
                    request=request,
                    work_state=work_state,
                    action=proposal.action,
                    prior_observations=observations,
                )
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
                    return self._failed_outcome(
                        request=request,
                        work_state=work_state,
                        package=last_package,
                        draft=last_draft,
                        review=last_review,
                        provider_dispatch_count=audit.provider_dispatch_count,
                        failure_code="AGENT_NO_PROGRESS_LIMIT_REACHED",
                    )
                continue

            assert proposal.draft is not None
            if len(observations) < minimum_observations_for_draft:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "an evidence-required Review Finding must receive a new Observation before redrafting",
                )
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
            review_count += 1
            if review_count > self._limits.maximum_reviews:
                return self._failed_outcome(
                    request=request,
                    work_state=work_state,
                    package=package,
                    draft=draft,
                    review=last_review,
                    provider_dispatch_count=audit.provider_dispatch_count,
                    failure_code="AGENT_REVIEW_LIMIT_REACHED",
                )
            review_proposal = self._reviewer.review(
                EngineeringAgentReviewRequest(
                    turn_request=request,
                    work_state=work_state,
                    package=package,
                    draft=draft,
                )
            )
            audit.provider_dispatch_count += 1
            if not isinstance(review_proposal, EngineeringAgentReviewProposal):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Reviewer returned an untyped proposal",
                )
            self._record_model_call(
                model_call_refs, review_proposal.model_call_ref
            )
            review = self._seal_review(
                request=request,
                work_state=work_state,
                package=package,
                draft=draft,
                proposal=review_proposal,
            )
            last_package, last_draft, last_review = package, draft, review
            audit.review = review
            if review.decision is EngineeringAgentReviewDecision.FINDINGS:
                review_findings = review.findings
                pending_review = review
                if any(item.requires_evidence for item in review.findings):
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
            )

        return self._failed_outcome(
            request=request,
            work_state=previous,
            package=last_package,
            draft=last_draft,
            review=last_review,
            provider_dispatch_count=audit.provider_dispatch_count,
            failure_code="AGENT_STEP_LIMIT_REACHED",
        )

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
        if not _package_matches_observations(package, observations):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "answer Package does not match the current sealed observations",
            )
        by_id = {item.observation_id: item for item in packaged_observations}
        if proposal.response_kind is EngineeringAgentResponseKind.ANSWER:
            for claim in proposal.claims:
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
            "schema": "ENGINEERING_AGENT_ANSWER@1",
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
    ) -> EngineeringAgentReview:
        if not isinstance(proposal.decision, EngineeringAgentReviewDecision) or any(
            not isinstance(item, EngineeringAgentReviewFinding)
            for item in proposal.findings
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Reviewer proposal violates the typed decision contract",
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
            "schema": "ENGINEERING_AGENT_REVIEW@1",
            "review_id": review_id.value,
            "turn_id": request.turn_id.value,
            "work_state_digest": work_state.digest.value,
            "package_digest": package.digest.value,
            "answer_digest": draft.digest.value,
            "decision": proposal.decision.value,
            "findings": tuple(
                {
                    "code": item.code,
                    "message": item.message,
                    "requires_evidence": item.requires_evidence,
                    "claim_index": item.claim_index,
                }
                for item in proposal.findings
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
            quality_status=quality,
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
        failure_code: str,
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
        with self._state_lock:
            previous = self._current_work_states.get(conversation_id)
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
        with self._state_lock:
            current = self._current_work_states.get(work_state.conversation_id)
            if current is not None and (
                work_state.work_state_id != current.work_state_id
                or work_state.revision.value <= current.revision.value
            ):
                raise DomainError(
                    ErrorCode.REVISION_CONFLICT,
                    "Agent Work State successor does not extend the current revision",
                )
            self._current_work_states[work_state.conversation_id] = work_state


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
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Delivery authorization is bound to different Turn artifacts",
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
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} exceeds its boundary")
    return value


def _text(value: str, label: str) -> str:
    return _bounded_text(value, label, maximum_bytes=512)


__all__ = [
    "ApplicationOwnedEngineeringAgentTurnExecutor",
    "EngineeringAgentAnswerDraft",
    "EngineeringAgentClaimProposal",
    "EngineeringAgentCitation",
    "EngineeringAgentDeliveryAuthorization",
    "EngineeringAgentDeliveryRequest",
    "EngineeringAgentDraftProposal",
    "EngineeringAgentDriver",
    "EngineeringAgentEvidenceDisposition",
    "EngineeringAgentEvidencePackage",
    "EngineeringAgentInvocation",
    "EngineeringAgentLedgerEntryReceipt",
    "EngineeringAgentLoopLimits",
    "EngineeringAgentResponseControl",
    "EngineeringAgentResponseKind",
    "EngineeringAgentReview",
    "EngineeringAgentReviewDecision",
    "EngineeringAgentReviewFinding",
    "EngineeringAgentReviewProposal",
    "EngineeringAgentReviewRequest",
    "EngineeringAgentReviewer",
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
    "EngineeringAgentWorkState",
    "EngineeringAgentWorkStateProposal",
]
