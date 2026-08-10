"""Evidence-first orchestration for synchronous software questions.

The synchronous path owns only four durable semantic objects: the question
checklist, a sealed source-evidence packet, an answer draft, and an independent
review.  Formal knowledge publication is intentionally outside this path.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Protocol

from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine import KnowledgeScopeService, ScopePurpose
from software_world_model.source_integration import (
    OperationBudget,
    SourceArtifact,
    SourceConfigurationService,
    SourceOperationIntent,
    SourceOperationResult,
    SourceOperationService,
    SourceOperationStatus,
)

from .knowledge_update import (
    BuildObjective,
    KnowledgeUpdateRequest,
    SourceInvestigationPlanner,
    authorize_source_action,
)


MAX_CHECKLIST_ITEMS = 12
MAX_EVIDENCE_ITEMS = 96
EVIDENCE_ANSWER_CAPABILITY_ID = "software-evidence-answer-task"
EVIDENCE_ANSWER_CAPABILITY_CONTRACT_VERSION = "1.0.0"


@dataclass(frozen=True, slots=True)
class QuestionChecklistItem:
    item_id: str
    question: str
    digest: Digest

    @classmethod
    def create(cls, *, item_id: str, question: str) -> "QuestionChecklistItem":
        core = {
            "item_id": _text(item_id, "checklist item ID"),
            "question": _text(question, "checklist question"),
        }
        return cls(**core, digest=digest_of(core))


@dataclass(frozen=True, slots=True)
class QuestionChecklist:
    original_request: str
    items: tuple[QuestionChecklistItem, ...]
    digest: Digest

    @classmethod
    def create(
        cls, *, original_request: str, questions: tuple[str, ...]
    ) -> "QuestionChecklist":
        original_request = _text(original_request, "original request")
        if not questions or len(questions) > MAX_CHECKLIST_ITEMS:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "question checklist must contain one to twelve items",
            )
        normalized = tuple(_text(item, "checklist question") for item in questions)
        if len(set(normalized)) != len(normalized):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "question checklist contains duplicate items",
            )
        items = tuple(
            QuestionChecklistItem.create(item_id=f"check-{index}", question=question)
            for index, question in enumerate(normalized, 1)
        )
        core = {
            "original_request": original_request,
            "items": tuple(item.digest.value for item in items),
        }
        return cls(original_request, items, digest_of(core))

    def model_view(self) -> dict[str, object]:
        return {
            "original_request": self.original_request,
            "checklist_digest": self.digest.value,
            "items": [
                {"item_id": item.item_id, "question": item.question}
                for item in self.items
            ],
        }


class QuestionChecklistPlanner(Protocol):
    def plan(
        self, *, original_request: str, execution_ref: str
    ) -> QuestionChecklist: ...


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    evidence_id: str
    operation_id: StableId
    artifact_id: StableId
    tool: str
    repository_revision: str
    locator: str
    coverage: tuple[tuple[str, str], ...]
    content: str
    content_digest: Digest
    digest: Digest

    @classmethod
    def from_artifact(
        cls,
        *,
        operation: SourceOperationResult,
        artifact: SourceArtifact,
        ordinal: int,
    ) -> "EvidenceItem":
        observation = operation.observation
        if observation is None:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "evidence artifact has no source observation",
            )
        try:
            content = artifact.payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DomainError(
                ErrorCode.SOURCE_OPERATION_FAILED,
                "authorized source evidence is not UTF-8 text",
            ) from exc
        evidence_id = f"evidence-{ordinal}"
        coverage = tuple(sorted(observation.coverage))
        core = {
            "evidence_id": evidence_id,
            "operation_id": operation.operation_id.value,
            "artifact_id": artifact.artifact_id.value,
            "tool": observation.tool.value,
            "repository_revision": observation.source_context.repository_revision,
            "locator": artifact.source_native_identity,
            "coverage": coverage,
            "content_digest": artifact.content_digest.value,
        }
        return cls(
            evidence_id=evidence_id,
            operation_id=operation.operation_id,
            artifact_id=artifact.artifact_id,
            tool=observation.tool.value,
            repository_revision=observation.source_context.repository_revision,
            locator=artifact.source_native_identity,
            coverage=coverage,
            content=content,
            content_digest=artifact.content_digest,
            digest=digest_of(core),
        )

    def model_view(self) -> dict[str, object]:
        return {
            "evidence_id": self.evidence_id,
            "tool": self.tool,
            "repository_revision": self.repository_revision,
            "locator": self.locator,
            "coverage": dict(self.coverage),
            "content": self.content,
            "content_digest": self.content_digest.value,
        }

    @property
    def source_label(self) -> str:
        coverage = dict(self.coverage)
        range_value = coverage.get("range")
        suffix = f" ({range_value})" if range_value else ""
        return f"{self.locator}@{self.repository_revision}{suffix}"


@dataclass(frozen=True, slots=True)
class EvidencePacket:
    packet_id: StableId
    checklist_digest: Digest
    target_digest: Digest
    items: tuple[EvidenceItem, ...]
    operation_references: tuple[StableId, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        checklist: QuestionChecklist,
        source_request: KnowledgeUpdateRequest,
        operations: tuple[SourceOperationResult, ...],
    ) -> "EvidencePacket":
        evidence: list[EvidenceItem] = []
        operation_references: list[StableId] = []
        for operation in operations:
            observation = operation.observation
            if operation.status not in {
                SourceOperationStatus.COMPLETED,
                SourceOperationStatus.PARTIAL,
            } or observation is None:
                continue
            operation_references.append(operation.operation_id)
            for artifact in observation.artifacts:
                evidence.append(
                    EvidenceItem.from_artifact(
                        operation=operation,
                        artifact=artifact,
                        ordinal=len(evidence) + 1,
                    )
                )
        if not evidence:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "source investigation produced no usable evidence",
            )
        if len(evidence) > MAX_EVIDENCE_ITEMS:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "source investigation produced an unreviewable evidence packet",
            )
        core = {
            "checklist_digest": checklist.digest.value,
            "target_digest": source_request.target.digest.value,
            "items": tuple(item.digest.value for item in evidence),
            "operation_references": tuple(
                item.value for item in operation_references
            ),
        }
        digest = digest_of(core)
        return cls(
            packet_id=StableId(f"evidence_packet_{digest.value[-32:]}"),
            checklist_digest=checklist.digest,
            target_digest=source_request.target.digest,
            items=tuple(evidence),
            operation_references=tuple(operation_references),
            digest=digest,
        )

    def model_view(self) -> dict[str, object]:
        return {
            "packet_id": self.packet_id.value,
            "packet_digest": self.digest.value,
            "target_digest": self.target_digest.value,
            "items": [item.model_view() for item in self.items],
        }


class AnswerSectionKind(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class EvidenceAnswerSection:
    section_id: str
    kind: AnswerSectionKind
    text: str
    checklist_item_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        section_id: str,
        kind: AnswerSectionKind,
        text: str,
        checklist_item_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
    ) -> "EvidenceAnswerSection":
        checklist_item_ids = _unique_texts(
            checklist_item_ids, "answer checklist item ID", allow_empty=False
        )
        evidence_ids = _unique_texts(
            evidence_ids, "answer evidence ID", allow_empty=True
        )
        if kind is AnswerSectionKind.SUPPORTED and not evidence_ids:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "supported answer section has no evidence",
            )
        if kind is AnswerSectionKind.UNKNOWN and evidence_ids:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "unknown answer section cannot claim evidence",
            )
        core = {
            "section_id": _text(section_id, "answer section ID"),
            "kind": kind.value,
            "text": _text(text, "answer section text"),
            "checklist_item_ids": checklist_item_ids,
            "evidence_ids": evidence_ids,
        }
        return cls(
            section_id=core["section_id"],
            kind=kind,
            text=core["text"],
            checklist_item_ids=checklist_item_ids,
            evidence_ids=evidence_ids,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EvidenceAnswerDraft:
    draft_id: StableId
    revision: int
    checklist_digest: Digest
    evidence_packet_digest: Digest
    sections: tuple[EvidenceAnswerSection, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        revision: int,
        checklist: QuestionChecklist,
        packet: EvidencePacket,
        sections: tuple[EvidenceAnswerSection, ...],
    ) -> "EvidenceAnswerDraft":
        if revision < 1 or not sections:
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "answer draft revision or sections are invalid",
            )
        if len({item.section_id for item in sections}) != len(sections):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "answer section IDs must be unique",
            )
        checklist_ids = {item.item_id for item in checklist.items}
        evidence_ids = {item.evidence_id for item in packet.items}
        if any(
            not set(section.checklist_item_ids).issubset(checklist_ids)
            or not set(section.evidence_ids).issubset(evidence_ids)
            for section in sections
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "answer draft cites an unauthorized checklist item or evidence item",
            )
        core = {
            "revision": revision,
            "checklist_digest": checklist.digest.value,
            "evidence_packet_digest": packet.digest.value,
            "sections": tuple(item.digest.value for item in sections),
        }
        digest = digest_of(core)
        return cls(
            draft_id=StableId(f"evidence_answer_{digest.value[-32:]}"),
            revision=revision,
            checklist_digest=checklist.digest,
            evidence_packet_digest=packet.digest,
            sections=sections,
            digest=digest,
        )

    @property
    def body(self) -> str:
        return "\n\n".join(item.text for item in self.sections)

    def model_view(self) -> dict[str, object]:
        return {
            "draft_id": self.draft_id.value,
            "revision": self.revision,
            "draft_digest": self.digest.value,
            "sections": [
                {
                    "section_id": item.section_id,
                    "kind": item.kind.value,
                    "text": item.text,
                    "checklist_item_ids": list(item.checklist_item_ids),
                    "evidence_ids": list(item.evidence_ids),
                }
                for item in self.sections
            ],
        }


class EvidenceAnswerGenerator(Protocol):
    def generate(
        self,
        *,
        checklist: QuestionChecklist,
        packet: EvidencePacket,
        revision: int,
        prior_draft: EvidenceAnswerDraft | None,
        review_findings: tuple["EvidenceReviewFinding", ...],
        execution_ref: str,
    ) -> EvidenceAnswerDraft: ...


class EvidenceReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    REWRITE_REQUIRED = "REWRITE_REQUIRED"
    MORE_EVIDENCE_REQUIRED = "MORE_EVIDENCE_REQUIRED"


EVIDENCE_REVIEW_DIMENSIONS = (
    "QUESTION_FIDELITY",
    "EVIDENCE_GROUNDING",
    "REQUEST_COMPLETENESS",
    "RESPONSE_LANGUAGE",
    "RELEVANCE_READABILITY",
)


@dataclass(frozen=True, slots=True)
class EvidenceReviewFinding:
    checklist_item_id: str
    category: str
    description: str
    evidence_ids: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        checklist_item_id: str,
        category: str,
        description: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> "EvidenceReviewFinding":
        evidence_ids = _unique_texts(
            evidence_ids, "review evidence ID", allow_empty=True
        )
        core = {
            "checklist_item_id": _text(
                checklist_item_id, "review checklist item ID"
            ),
            "category": _text(category, "review finding category"),
            "description": _text(description, "review finding description"),
            "evidence_ids": evidence_ids,
        }
        return cls(**core, digest=digest_of(core))

    def model_view(self) -> dict[str, object]:
        return {
            "checklist_item_id": self.checklist_item_id,
            "category": self.category,
            "description": self.description,
            "evidence_ids": list(self.evidence_ids),
        }


@dataclass(frozen=True, slots=True)
class EvidenceAnswerReview:
    decision: EvidenceReviewDecision
    checks: tuple[tuple[str, bool], ...]
    checklist_digest: Digest
    evidence_packet_digest: Digest
    draft_digest: Digest
    findings: tuple[EvidenceReviewFinding, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        decision: EvidenceReviewDecision,
        checks: tuple[tuple[str, bool], ...],
        checklist: QuestionChecklist,
        packet: EvidencePacket,
        draft: EvidenceAnswerDraft,
        findings: tuple[EvidenceReviewFinding, ...],
    ) -> "EvidenceAnswerReview":
        if (
            not isinstance(checks, tuple)
            or tuple(name for name, _ in checks) != EVIDENCE_REVIEW_DIMENSIONS
            or any(not isinstance(value, bool) for _, value in checks)
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "evidence answer review checks are incomplete or unordered",
            )
        all_checks_passed = all(value for _, value in checks)
        if decision is EvidenceReviewDecision.APPROVED and (
            findings or not all_checks_passed
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "approved evidence answer requires every review check to pass",
            )
        if decision is not EvidenceReviewDecision.APPROVED and (
            not findings or all_checks_passed
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "rejected evidence answer requires a failed check and actionable finding",
            )
        checklist_ids = {item.item_id for item in checklist.items}
        evidence_ids = {item.evidence_id for item in packet.items}
        if any(
            finding.checklist_item_id not in checklist_ids
            or not set(finding.evidence_ids).issubset(evidence_ids)
            for finding in findings
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "review cites an unauthorized checklist item or evidence item",
            )
        if (
            decision is EvidenceReviewDecision.REWRITE_REQUIRED
            and any(not finding.evidence_ids for finding in findings)
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "rewrite findings must identify existing evidence",
            )
        core = {
            "decision": decision.value,
            "checks": checks,
            "checklist_digest": checklist.digest.value,
            "evidence_packet_digest": packet.digest.value,
            "draft_digest": draft.digest.value,
            "findings": tuple(item.digest.value for item in findings),
        }
        return cls(
            decision=decision,
            checks=checks,
            checklist_digest=checklist.digest,
            evidence_packet_digest=packet.digest,
            draft_digest=draft.digest,
            findings=findings,
            digest=digest_of(core),
        )


class EvidenceAnswerReviewer(Protocol):
    def review(
        self,
        *,
        checklist: QuestionChecklist,
        packet: EvidencePacket,
        draft: EvidenceAnswerDraft,
        execution_ref: str,
    ) -> EvidenceAnswerReview: ...


class EvidenceResponseControlService:
    """Own answer drafting, independent review, and fixed-packet rewrites."""

    def __init__(
        self,
        *,
        answer_generator: EvidenceAnswerGenerator,
        answer_reviewer: EvidenceAnswerReviewer,
        max_rewrite_attempts: int = 4,
    ) -> None:
        if max_rewrite_attempts < 1:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "evidence answer rewrite safety fuse must be positive",
            )
        self._answer_generator = answer_generator
        self._answer_reviewer = answer_reviewer
        self._max_rewrite_attempts = max_rewrite_attempts

    def prepare(
        self,
        *,
        checklist: QuestionChecklist,
        packet: EvidencePacket,
        execution_ref: str,
    ) -> tuple[EvidenceAnswerDraft, EvidenceAnswerReview]:
        prior: EvidenceAnswerDraft | None = None
        findings: tuple[EvidenceReviewFinding, ...] = ()
        for revision in range(1, self._max_rewrite_attempts + 1):
            draft = self._answer_generator.generate(
                checklist=checklist,
                packet=packet,
                revision=revision,
                prior_draft=prior,
                review_findings=findings,
                execution_ref=(
                    f"{execution_ref}:draft:{revision}"
                ),
            )
            if (
                draft.checklist_digest != checklist.digest
                or draft.evidence_packet_digest != packet.digest
            ):
                raise DomainError(
                    ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                    "answer generator changed the sealed question or evidence packet",
                )
            review = self._answer_reviewer.review(
                checklist=checklist,
                packet=packet,
                draft=draft,
                execution_ref=f"{execution_ref}:review:{revision}",
            )
            if review.decision in {
                EvidenceReviewDecision.APPROVED,
                EvidenceReviewDecision.MORE_EVIDENCE_REQUIRED,
            }:
                return draft, review
            prior = draft
            findings = review.findings
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "evidence answer did not pass independent review",
        )


@dataclass(frozen=True, slots=True)
class EvidenceAnswerRequest:
    idempotency_key: IdempotencyKey
    original_request: str
    source_request: KnowledgeUpdateRequest
    classification: str
    caller_ref: str
    correlation_ref: CorrelationRef

    @property
    def digest(self) -> Digest:
        return digest_of(
            {
                "command": "EvidenceAnswer@1",
                "idempotency_key": self.idempotency_key.value,
                "original_request": self.original_request,
                "source_request_digest": self.source_request.digest.value,
                "classification": self.classification,
                "caller_ref": self.caller_ref,
            }
        )


@dataclass(frozen=True, slots=True)
class AuthorizedEvidenceAnswer:
    checklist: QuestionChecklist
    evidence_packet: EvidencePacket
    draft: EvidenceAnswerDraft
    review: EvidenceAnswerReview
    source_operation_count: int
    digest: Digest

    @property
    def sources(self) -> tuple[str, ...]:
        labels: list[str] = []
        cited = {
            evidence_id
            for section in self.draft.sections
            for evidence_id in section.evidence_ids
        }
        for item in self.evidence_packet.items:
            if item.evidence_id in cited and item.source_label not in labels:
                labels.append(item.source_label)
        return tuple(labels)

    @property
    def unresolved_count(self) -> int:
        return sum(
            item.kind is AnswerSectionKind.UNKNOWN for item in self.draft.sections
        )


class EvidenceAnswerService:
    """Run source investigation, answer generation, and independent review."""

    def __init__(
        self,
        *,
        scopes: KnowledgeScopeService,
        configurations: SourceConfigurationService,
        operations: SourceOperationService,
        source_planner: SourceInvestigationPlanner,
        checklist_planner: QuestionChecklistPlanner,
        responses: EvidenceResponseControlService,
        max_retrieval_rounds: int = 3,
        activation_guard: Callable[[], bool] | None = None,
    ) -> None:
        if max_retrieval_rounds < 1:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "evidence answer safety fuses must be positive",
            )
        self._scopes = scopes
        self._configurations = configurations
        self._operations = operations
        self._source_planner = source_planner
        self._checklist_planner = checklist_planner
        self._responses = responses
        self._max_retrieval_rounds = max_retrieval_rounds
        self._activation_guard = activation_guard

    def is_currently_active(self) -> bool:
        return self._activation_guard is None or self._activation_guard()

    def execute(self, request: EvidenceAnswerRequest) -> AuthorizedEvidenceAnswer:
        if not self.is_currently_active():
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "evidence-first answer strategy is not currently activated",
            )
        checklist = self._checklist_planner.plan(
            original_request=request.original_request,
            execution_ref=f"evidence-answer:{request.idempotency_key.value}:checklist",
        )
        if checklist.original_request != request.original_request:
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "question planner changed the original request",
            )
        operations: list[SourceOperationResult] = []
        action_signatures: set[Digest] = set()
        retrieval_findings: tuple[EvidenceReviewFinding, ...] = ()
        for retrieval_round in range(1, self._max_retrieval_rounds + 1):
            before = len(operations)
            source_request = self._focused_source_request(
                request,
                checklist=checklist,
                retrieval_round=retrieval_round,
                findings=retrieval_findings,
            )
            self._investigate(source_request, operations, action_signatures)
            if len(operations) == before:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "independent review requested evidence but investigation made no progress",
                )
            packet = EvidencePacket.create(
                checklist=checklist,
                source_request=source_request,
                operations=tuple(operations),
            )
            draft, review = self._responses.prepare(
                checklist=checklist,
                packet=packet,
                execution_ref=(
                    f"evidence-answer:{request.idempotency_key.value}:"
                    f"packet:{packet.digest.value}"
                ),
            )
            if review.decision is EvidenceReviewDecision.APPROVED:
                core = {
                    "request_digest": request.digest.value,
                    "checklist_digest": checklist.digest.value,
                    "evidence_packet_digest": packet.digest.value,
                    "draft_digest": draft.digest.value,
                    "review_digest": review.digest.value,
                }
                return AuthorizedEvidenceAnswer(
                    checklist=checklist,
                    evidence_packet=packet,
                    draft=draft,
                    review=review,
                    source_operation_count=len(operations),
                    digest=digest_of(core),
                )
            retrieval_findings = review.findings
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "authorized source evidence remained insufficient after targeted retrieval",
        )

    def _focused_source_request(
        self,
        request: EvidenceAnswerRequest,
        *,
        checklist: QuestionChecklist,
        retrieval_round: int,
        findings: tuple[EvidenceReviewFinding, ...],
    ) -> KnowledgeUpdateRequest:
        focus = "\n".join(
            f"- {item.item_id}: {item.question}" for item in checklist.items
        )
        if findings:
            focus += "\nIndependent review requested more evidence:\n" + "\n".join(
                f"- {item.checklist_item_id}: {item.description}"
                for item in findings
            )
        objective = BuildObjective.create(
            objective_id=(
                f"evidence-question:{request.idempotency_key.value}:"
                f"round:{retrieval_round}"
            ),
            description=(
                "Collect source evidence needed to answer the exact user request.\n"
                f"Original request:\n{request.original_request}\n"
                f"Question checklist:\n{focus}"
            ),
            unacceptable_outcomes=(
                "source boundary expansion",
                "unsupported answer",
                "missing a material checklist item",
            ),
        )
        return replace(
            request.source_request,
            idempotency_key=IdempotencyKey(
                f"{request.idempotency_key.value}:source-round:{retrieval_round}"
            ),
            objective=objective,
            requirement_plan=None,
        )

    def _investigate(
        self,
        source_request: KnowledgeUpdateRequest,
        completed_operations: list[SourceOperationResult],
        action_signatures: set[Digest],
    ) -> None:
        initial_count = len(completed_operations)
        remaining_actions = source_request.max_steps - initial_count
        if remaining_actions < 1:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "source investigation exhausted its overall safety fuse",
            )
        for local_ordinal in range(1, remaining_actions + 1):
            proposal = self._source_planner.propose(
                request=source_request,
                completed_operations=tuple(completed_operations),
                ordinal=len(completed_operations) + 1,
            )
            authorize_source_action(source_request.target, proposal)
            if proposal.stop:
                return
            assert proposal.tool is not None
            signature = digest_of(
                {"tool": proposal.tool.value, "parameters": proposal.parameters}
            )
            if signature in action_signatures:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "source investigation repeated an already completed action",
                )
            action_signatures.add(signature)
            ordinal = initial_count + local_ordinal
            scope_assertion = self._scopes.read_scope_state_assertion(
                scope_id=source_request.scope_id,
                expected_revision=source_request.scope_revision,
                purpose=ScopePurpose.SOURCE_EXECUTION,
                caller_ref="application-services/evidence-answer",
                request_ref=(
                    f"{source_request.idempotency_key.value}:step:{ordinal}"
                ),
                classification=source_request.classification,
            )
            eligibility = self._configurations.resolve_binding_for_execution(
                binding_id=source_request.binding_id,
                expected_binding_revision=source_request.binding_revision,
                expected_source_revision=source_request.source_revision,
                assertion=scope_assertion,
                tool_id=proposal.tool.value,
                classification=source_request.classification,
            )
            intent = SourceOperationIntent.create(
                idempotency_key=IdempotencyKey(
                    f"{source_request.idempotency_key.value}:source-step:{ordinal}"
                ),
                causation_reference=f"evidence-answer:{source_request.idempotency_key.value}",
                source_id=source_request.source_id,
                source_revision=source_request.source_revision,
                binding_id=source_request.binding_id,
                binding_revision=source_request.binding_revision,
                scope_assertion=scope_assertion,
                binding_eligibility=eligibility,
                tool=proposal.tool,
                parameters=dict(proposal.parameters),
                budget=OperationBudget(
                    max_calls=1,
                    max_items=source_request.max_items_per_step,
                    max_bytes=source_request.max_bytes_per_step,
                ),
                classification=source_request.classification,
                correlation_ref=source_request.correlation_ref,
            )
            operation = self._operations.execute(intent)
            if operation.status not in {
                SourceOperationStatus.COMPLETED,
                SourceOperationStatus.PARTIAL,
            }:
                raise DomainError(
                    ErrorCode.SOURCE_OPERATION_FAILED,
                    operation.failure_message or "authorized source read failed",
                )
            completed_operations.append(operation)
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "source investigation reached its overall safety fuse before declaring completion",
        )


def _unique_texts(
    values: tuple[str, ...], label: str, *, allow_empty: bool
) -> tuple[str, ...]:
    if not allow_empty and not values:
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, f"{label} is empty")
    normalized = tuple(_text(item, label) for item in values)
    if len(set(normalized)) != len(normalized):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID, f"{label} contains duplicates"
        )
    return normalized


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty text"
        )
    return value
