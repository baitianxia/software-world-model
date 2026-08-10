"""Answer candidate, independent review, authorization, and exactly-one delivery."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Protocol

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, StableId, digest_of
from software_world_model.knowledge_engine import FormalKnowledgeRecord, FormalKnowledgeService

from .knowledge_use import (
    KnowledgeRequirement,
    NeedStatus,
    SufficiencyAssessment,
    SufficiencyItem,
)
from .task_control import ConversationalTask, ConversationalTaskControl, TaskValidationAssertion


class ResponseKind(str, Enum):
    KNOWLEDGE_COMPLETE = "KNOWLEDGE_COMPLETE"
    KNOWLEDGE_PARTIAL = "KNOWLEDGE_PARTIAL"
    GAP = "GAP"
    FAILURE = "FAILURE"
    UNSUPPORTED = "UNSUPPORTED"


class AnswerClaimKind(str, Enum):
    FORMAL_KNOWLEDGE = "FORMAL_KNOWLEDGE"
    KNOWLEDGE_GAP = "KNOWLEDGE_GAP"
    APPLICATION_LIMITATION = "APPLICATION_LIMITATION"


class ReviewDimension(str, Enum):
    TASK_FIDELITY = "TASK_FIDELITY"
    CLAIM_SUPPORT = "CLAIM_SUPPORT"
    TEXT_FIDELITY = "TEXT_FIDELITY"
    CONTEXT_AND_CONFLICT = "CONTEXT_AND_CONFLICT"
    COMPLETENESS = "COMPLETENESS"
    SAFETY_AND_DISCLOSURE = "SAFETY_AND_DISCLOSURE"


class ReviewOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class ReviewDecision(str, Enum):
    APPROVED = "APPROVED"
    REVISION_REQUIRED = "REVISION_REQUIRED"
    REJECTED = "REJECTED"


@dataclass(frozen=True, slots=True)
class SemanticAnswerReviewDecision:
    approved: bool
    failed_dimensions: tuple[ReviewDimension, ...]
    findings: tuple[str, ...]


class SemanticAnswerReviewer(Protocol):
    def review(
        self,
        *,
        task: ConversationalTask,
        requirement: KnowledgeRequirement,
        candidate: AnswerCandidate,
        assessment: SufficiencyAssessment,
    ) -> SemanticAnswerReviewDecision: ...


class DeliveryState(str, Enum):
    PREPARED = "PREPARED"
    SENDING = "SENDING"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    OUTCOME_PENDING = "OUTCOME_PENDING"
    CANCELED_BEFORE_DISPATCH = "CANCELED_BEFORE_DISPATCH"


@dataclass(frozen=True, slots=True)
class AnswerClaim:
    claim_id: str
    need_id: str
    kind: AnswerClaimKind
    text: str
    formal_reference: StableId | None
    formal_digest: Digest | None
    support_proof_id: StableId | None
    gap: str | None


@dataclass(frozen=True, slots=True)
class AnswerNeedEvidence:
    need_id: str
    question: str
    status: NeedStatus
    formal_records: tuple[FormalKnowledgeRecord, ...]
    disclosure: str | None
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AnswerDraftSelection:
    need_id: str
    formal_references: tuple[StableId, ...]


@dataclass(frozen=True, slots=True)
class AnswerDraftPlan:
    selections: tuple[AnswerDraftSelection, ...]


class AnswerDraftPlanner(Protocol):
    def plan(
        self,
        *,
        original_request: str,
        needs: tuple[AnswerNeedEvidence, ...],
    ) -> AnswerDraftPlan: ...


class DeterministicAnswerDraftPlanner:
    """Compatibility planner selecting every record in each issued support proof."""

    def plan(
        self,
        *,
        original_request: str,
        needs: tuple[AnswerNeedEvidence, ...],
    ) -> AnswerDraftPlan:
        del original_request
        return AnswerDraftPlan(
            tuple(
                AnswerDraftSelection(
                    need_id=item.need_id,
                    formal_references=tuple(
                        record.object_id for record in item.formal_records
                    ),
                )
                for item in needs
            )
        )


@dataclass(frozen=True, slots=True)
class RequirementCoverage:
    need_id: str
    claim_ids: tuple[str, ...]
    decision: NeedStatus


@dataclass(frozen=True, slots=True)
class AnswerCandidate:
    candidate_id: StableId
    revision: int
    task_id: StableId
    source_task_revision: int
    source_orchestration_revision: int
    requirement_id: StableId
    requirement_revision: int
    assessment_id: StableId
    read_session_id: StableId
    snapshot_id: StableId
    response_kind: ResponseKind
    body: str
    claims: tuple[AnswerClaim, ...]
    coverage: tuple[RequirementCoverage, ...]
    digest: Digest
    sealed_at: datetime


@dataclass(frozen=True, slots=True)
class ReviewMatrixCell:
    claim_id: str | None
    dimension: ReviewDimension
    outcome: ReviewOutcome
    finding: str | None
    authority_references: tuple[StableId, ...]


@dataclass(frozen=True, slots=True)
class AnswerReviewResult:
    review_id: StableId
    candidate_id: StableId
    candidate_digest: Digest
    matrix: tuple[ReviewMatrixCell, ...]
    decision: ReviewDecision
    task_validation_digest: Digest
    digest: Digest
    reviewed_at: datetime


@dataclass(frozen=True, slots=True)
class FinalResponseAuthorization:
    authorization_id: StableId
    task_id: StableId
    task_revision: int
    orchestration_revision: int
    candidate_id: StableId
    candidate_digest: Digest
    review_id: StableId
    review_digest: Digest
    task_validation_digest: Digest
    classification: str
    digest: Digest
    authorized_at: datetime


@dataclass(frozen=True, slots=True)
class AdapterDeliveryReceipt:
    adapter_receipt_id: str
    adapter_idempotency_key: str
    body_digest: Digest
    accepted: bool
    provider_reference: str | None
    digest: Digest


@dataclass(frozen=True, slots=True)
class LogicalDelivery:
    delivery_id: StableId
    conversation_ref: str
    turn_ref: str
    request_ref: str
    adapter_idempotency_key: str
    candidate_id: StableId
    authorization_id: StableId
    body_digest: Digest
    revision: int
    state: DeliveryState
    receipt: AdapterDeliveryReceipt | None
    failure_code: str | None
    created_at: datetime
    revised_at: datetime


class DeliveryOutcomePending(RuntimeError):
    pass


class ResponseAdapter(Protocol):
    def send(
        self, *, adapter_idempotency_key: str, body: str, body_digest: Digest
    ) -> AdapterDeliveryReceipt: ...


class ResponseControlRepository(Protocol):
    def get_candidate(self, candidate_id: StableId) -> AnswerCandidate: ...

    def get_review_for_candidate(
        self, candidate_id: StableId
    ) -> AnswerReviewResult | None: ...

    def get_authorization_for_candidate(
        self, candidate_id: StableId
    ) -> FinalResponseAuthorization | None: ...

    def save_candidate(self, candidate: AnswerCandidate) -> AnswerCandidate: ...

    def save_review(self, review: AnswerReviewResult) -> AnswerReviewResult: ...

    def save_authorization(
        self, authorization: FinalResponseAuthorization
    ) -> FinalResponseAuthorization: ...

    def prepare_delivery(
        self,
        *,
        task: ConversationalTask,
        candidate: AnswerCandidate,
        authorization: FinalResponseAuthorization,
        occurred_at: datetime,
    ) -> LogicalDelivery: ...

    def transition_delivery(
        self,
        *,
        delivery_id: StableId,
        expected_revision: int,
        target: DeliveryState,
        receipt: AdapterDeliveryReceipt | None,
        failure_code: str | None,
        occurred_at: datetime,
    ) -> LogicalDelivery: ...


class ResponseControlService:
    _DIMENSIONS = tuple(ReviewDimension)

    def __init__(
        self,
        repository: ResponseControlRepository,
        task_control: ConversationalTaskControl,
        knowledge: FormalKnowledgeService,
        *,
        semantic_reviewer: SemanticAnswerReviewer | None = None,
        strategy_implementation_digest: Digest | None = None,
        strategy_qualification_ref: str | None = None,
        strategy_classification: str | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._tasks = task_control
        self._knowledge = knowledge
        self._semantic_reviewer = semantic_reviewer
        reviewer_digest = getattr(
            semantic_reviewer, "strategy_implementation_digest", None
        )
        if (
            strategy_implementation_digest is not None
            and reviewer_digest is not None
            and strategy_implementation_digest != reviewer_digest
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "semantic answer reviewer does not match its strategy implementation",
            )
        self._strategy_implementation_digest = (
            strategy_implementation_digest or reviewer_digest
        )
        reviewer_qualification_ref = getattr(
            semantic_reviewer, "qualification_ref", None
        )
        if (
            strategy_qualification_ref is not None
            and reviewer_qualification_ref is not None
            and strategy_qualification_ref != reviewer_qualification_ref
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "semantic answer reviewer uses another qualification",
            )
        self._strategy_qualification_ref = (
            strategy_qualification_ref or reviewer_qualification_ref
        )
        reviewer_classification = getattr(semantic_reviewer, "classification", None)
        if (
            strategy_classification is not None
            and reviewer_classification is not None
            and strategy_classification != reviewer_classification
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "semantic answer reviewer uses another classification",
            )
        self._strategy_classification = (
            strategy_classification or reviewer_classification
        )
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @property
    def strategy_implementation_digest(self) -> Digest | None:
        return self._strategy_implementation_digest

    @property
    def strategy_qualification_ref(self) -> str | None:
        return self._strategy_qualification_ref

    @property
    def strategy_classification(self) -> str | None:
        return self._strategy_classification

    def get_candidate(self, candidate_id: StableId) -> AnswerCandidate:
        return self._repository.get_candidate(candidate_id)

    def seal_candidate(
        self,
        *,
        task: ConversationalTask,
        requirement: KnowledgeRequirement,
        assessment: SufficiencyAssessment,
        claims: tuple[AnswerClaim, ...],
        body: str,
        partial_allowed: bool = False,
    ) -> tuple[AnswerCandidate, ConversationalTask]:
        if assessment.requirement_id != requirement.requirement_id or assessment.requirement_revision != requirement.revision:
            raise DomainError(ErrorCode.REVISION_CONFLICT, "assessment binds another requirement")
        if not claims or body != _canonical_answer_body(claims):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "candidate body must contain each distinct ordered claim text exactly once",
            )
        items = {item.need_id: item for item in assessment.items}
        needs_by_id = {item.need_id: item for item in requirement.needs}
        claims_by_need: dict[str, list[AnswerClaim]] = {item.need_id: [] for item in requirement.needs}
        for claim in claims:
            if claim.need_id not in claims_by_need:
                raise DomainError(ErrorCode.INVALID_ARGUMENT, "claim references an unknown Need")
            item = items[claim.need_id]
            if claim.kind is AnswerClaimKind.FORMAL_KNOWLEDGE:
                if item.status is not NeedStatus.SATISFIED or item.proof is None:
                    raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "formal claim is not backed by a satisfied Need")
                if (
                    claim.formal_reference not in item.proof.supporting_references
                    or claim.support_proof_id != item.proof.proof_id
                ):
                    raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "claim is outside the Need support proof")
            elif claim.kind is AnswerClaimKind.KNOWLEDGE_GAP:
                disclosure = _assessment_disclosure(item)
                if (
                    item.status is NeedStatus.SATISFIED
                    or claim.gap != disclosure
                    or claim.text
                    != _explicit_gap_text(
                        needs_by_id[claim.need_id].question,
                        disclosure,
                        joint_constraint_impact=_joint_constraint_impact(
                            claim.need_id, assessment, requirement
                        ),
                    )
                ):
                    raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "gap claim does not match assessment")
            elif claim.kind is AnswerClaimKind.APPLICATION_LIMITATION:
                if (
                    item.status is not NeedStatus.SATISFIED
                    or item.proof is None
                    or claim.text not in item.limitations
                    or claim.gap != claim.text
                    or claim.formal_reference is not None
                    or claim.formal_digest is not None
                    or claim.support_proof_id != item.proof.proof_id
                ):
                    raise DomainError(
                        ErrorCode.CONTROL_STATE_DENIED,
                        "application limitation does not match assessment",
                    )
            else:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "answer claim kind is unsupported",
                )
            claims_by_need[claim.need_id].append(claim)
        coverage: list[RequirementCoverage] = []
        for need in requirement.needs:
            need_claims = claims_by_need[need.need_id]
            item = items[need.need_id]
            if not need_claims:
                raise DomainError(ErrorCode.INVALID_ARGUMENT, "candidate omits a requirement Need")
            if item.status is NeedStatus.SATISFIED and not any(
                claim.kind is AnswerClaimKind.FORMAL_KNOWLEDGE for claim in need_claims
            ):
                raise DomainError(ErrorCode.INVALID_ARGUMENT, "satisfied Need lacks formal claim")
            if item.status is not NeedStatus.SATISFIED and not any(
                claim.kind is AnswerClaimKind.KNOWLEDGE_GAP for claim in need_claims
            ):
                raise DomainError(ErrorCode.INVALID_ARGUMENT, "unsatisfied Need lacks gap disclosure")
            coverage.append(
                RequirementCoverage(
                    need_id=need.need_id,
                    claim_ids=tuple(claim.claim_id for claim in need_claims),
                    decision=item.status,
                )
            )
        if assessment.sufficient:
            response_kind = ResponseKind.KNOWLEDGE_COMPLETE
        elif partial_allowed and any(item.status is NeedStatus.SATISFIED for item in assessment.items):
            response_kind = ResponseKind.KNOWLEDGE_PARTIAL
        else:
            if any(claim.kind is AnswerClaimKind.FORMAL_KNOWLEDGE for claim in claims):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "a GAP response cannot carry partial formal answer claims",
                )
            response_kind = ResponseKind.GAP
        sealed_at = self._now()
        core = {
            "task_id": task.task_id.value,
            "source_task_revision": task.revision.value,
            "source_orchestration_revision": task.orchestration_revision.value,
            "requirement_id": requirement.requirement_id.value,
            "requirement_revision": requirement.revision.value,
            "assessment_id": assessment.assessment_id.value,
            "read_session_id": assessment.read_session_id.value,
            "snapshot_id": assessment.snapshot_id.value,
            "response_kind": response_kind.value,
            "body": body,
            "claims": claims,
            "coverage": tuple(coverage),
        }
        digest = digest_of(core)
        candidate = AnswerCandidate(
            candidate_id=StableId(f"answer_candidate_{digest.value[-32:]}"),
            revision=1,
            task_id=task.task_id,
            source_task_revision=task.revision.value,
            source_orchestration_revision=task.orchestration_revision.value,
            requirement_id=requirement.requirement_id,
            requirement_revision=requirement.revision.value,
            assessment_id=assessment.assessment_id,
            read_session_id=assessment.read_session_id,
            snapshot_id=assessment.snapshot_id,
            response_kind=response_kind,
            body=body,
            claims=claims,
            coverage=tuple(coverage),
            digest=digest,
            sealed_at=sealed_at,
        )
        saved = self._repository.save_candidate(candidate)
        bound_task = self._tasks.bind_candidate(
            task_id=task.task_id,
            expected_revision=task.revision,
            candidate_id=saved.candidate_id,
        )
        return saved, bound_task

    def draft_and_seal_candidate(
        self,
        *,
        task: ConversationalTask,
        requirement: KnowledgeRequirement,
        assessment: SufficiencyAssessment,
        planner: AnswerDraftPlanner | None = None,
        partial_allowed: bool = False,
    ) -> tuple[AnswerCandidate, ConversationalTask]:
        """Build only source-closed claims from an assessment-bound draft plan."""

        if task.candidate_reference is not None:
            existing = self._repository.get_candidate(task.candidate_reference)
            if (
                existing.task_id != task.task_id
                or existing.requirement_id != requirement.requirement_id
                or existing.requirement_revision != requirement.revision.value
                or existing.assessment_id != assessment.assessment_id
                or existing.snapshot_id != assessment.snapshot_id
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "task candidate does not match the requested answer inputs",
                )
            return existing, task
        if (
            assessment.requirement_id != requirement.requirement_id
            or assessment.requirement_revision != requirement.revision
        ):
            raise DomainError(
                ErrorCode.REVISION_CONFLICT,
                "assessment binds another requirement",
            )
        assessment_by_need = {item.need_id: item for item in assessment.items}
        needs = []
        records_by_need = {}
        for need in requirement.needs:
            item = assessment_by_need.get(need.need_id)
            if item is None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "assessment omits a requirement Need",
                )
            records = ()
            if item.status is NeedStatus.SATISFIED:
                if item.proof is None:
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "satisfied Need is missing its support proof",
                    )
                records = tuple(
                    self._knowledge.get_record(assessment.snapshot_id, reference)
                    for reference in item.proof.supporting_references
                )
            records_by_need[need.need_id] = {
                record.object_id: record for record in records
            }
            needs.append(
                AnswerNeedEvidence(
                    need_id=need.need_id,
                    question=need.question,
                    status=item.status,
                    formal_records=records,
                    disclosure=(
                        None
                        if item.status is NeedStatus.SATISFIED
                        else _assessment_disclosure(item)
                    ),
                    limitations=item.limitations,
                )
            )
        plan = (planner or DeterministicAnswerDraftPlanner()).plan(
            original_request=requirement.original_request,
            needs=tuple(needs),
        )
        if not isinstance(plan, AnswerDraftPlan):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "answer draft planner returned an invalid plan",
            )
        selections = {item.need_id: item for item in plan.selections}
        if (
            len(selections) != len(plan.selections)
            or set(selections) != {item.need_id for item in requirement.needs}
        ):
            raise DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "answer draft plan must cover every Need exactly once",
            )
        claims = []
        for need in requirement.needs:
            item = assessment_by_need[need.need_id]
            selection = selections[need.need_id]
            known = records_by_need[need.need_id]
            if (
                len(selection.formal_references)
                != len(set(selection.formal_references))
                or any(reference not in known for reference in selection.formal_references)
            ):
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "answer draft references formal knowledge outside its Need proof",
                )
            if item.status is NeedStatus.SATISFIED:
                if not selection.formal_references or item.proof is None:
                    raise DomainError(
                        ErrorCode.CONTROL_STATE_DENIED,
                        "satisfied Need draft must select formal support",
                    )
                selected_record_texts: list[str] = []
                for ordinal, reference in enumerate(
                    selection.formal_references, 1
                ):
                    record = known[reference]
                    selected_record_texts.append(record.text.casefold())
                    claims.append(
                        AnswerClaim(
                            claim_id=f"claim:{need.need_id}:{ordinal}",
                            need_id=need.need_id,
                            kind=AnswerClaimKind.FORMAL_KNOWLEDGE,
                            text=record.text,
                            formal_reference=record.object_id,
                            formal_digest=record.object_digest,
                            support_proof_id=item.proof.proof_id,
                            gap=None,
                        )
                    )
                for ordinal, limitation in enumerate(
                    (
                        limitation
                        for limitation in dict.fromkeys(item.limitations)
                        if not any(
                            limitation.casefold() in record_text
                            for record_text in selected_record_texts
                        )
                    ),
                    1,
                ):
                    claims.append(
                        AnswerClaim(
                            claim_id=(
                                f"claim:{need.need_id}:limitation:{ordinal}"
                            ),
                            need_id=need.need_id,
                            kind=AnswerClaimKind.APPLICATION_LIMITATION,
                            text=limitation,
                            formal_reference=None,
                            formal_digest=None,
                            support_proof_id=item.proof.proof_id,
                            gap=limitation,
                        )
                    )
            else:
                if selection.formal_references:
                    raise DomainError(
                        ErrorCode.CONTROL_STATE_DENIED,
                        "unsatisfied Need draft cannot select formal answer records",
                    )
                disclosure = _assessment_disclosure(item)
                claims.append(
                    AnswerClaim(
                        claim_id=f"claim:{need.need_id}:gap",
                        need_id=need.need_id,
                        kind=AnswerClaimKind.KNOWLEDGE_GAP,
                        text=_explicit_gap_text(
                            need.question,
                            disclosure,
                            joint_constraint_impact=_joint_constraint_impact(
                                need.need_id, assessment, requirement
                            ),
                        ),
                        formal_reference=None,
                        formal_digest=None,
                        support_proof_id=None,
                        gap=disclosure,
                    )
                )
        frozen_claims = tuple(claims)
        return self.seal_candidate(
            task=task,
            requirement=requirement,
            assessment=assessment,
            claims=frozen_claims,
            body=_canonical_answer_body(frozen_claims),
            partial_allowed=partial_allowed,
        )

    def review(
        self,
        *,
        task: ConversationalTask,
        candidate: AnswerCandidate,
        assessment: SufficiencyAssessment,
        requirement: KnowledgeRequirement | None = None,
    ) -> AnswerReviewResult:
        existing = self._repository.get_review_for_candidate(candidate.candidate_id)
        if existing is not None:
            if existing.candidate_digest != candidate.digest:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "stored answer review binds another candidate digest",
                )
            return existing
        validation = self._tasks.validate_for_response(
            task_id=task.task_id,
            expected_revision=task.revision,
            expected_orchestration_revision=task.orchestration_revision,
            candidate_id=candidate.candidate_id,
            purpose="REVIEW_AUTHORIZATION",
        )
        semantic = None
        if self._semantic_reviewer is not None:
            if requirement is None:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "semantic answer review requires the exact Knowledge Requirement",
                )
            semantic = self._semantic_reviewer.review(
                task=task,
                requirement=requirement,
                candidate=candidate,
                assessment=assessment,
            )
            _validate_semantic_review(semantic)
        cells: list[ReviewMatrixCell] = []
        for claim in candidate.claims:
            support_pass, finding, refs = self._review_claim(
                claim, candidate, assessment, requirement
            )
            for dimension in self._DIMENSIONS:
                outcome = ReviewOutcome.PASS
                cell_finding = None
                if dimension in {ReviewDimension.CLAIM_SUPPORT, ReviewDimension.TEXT_FIDELITY} and not support_pass:
                    outcome = ReviewOutcome.FAIL
                    cell_finding = finding
                if dimension is ReviewDimension.TASK_FIDELITY and validation.outcome != "ALLOW":
                    outcome = ReviewOutcome.FAIL
                    cell_finding = "task binding is stale"
                if semantic is not None and dimension in semantic.failed_dimensions:
                    outcome = ReviewOutcome.FAIL
                    cell_finding = "; ".join(semantic.findings)
                cells.append(
                    ReviewMatrixCell(claim.claim_id, dimension, outcome, cell_finding, refs)
                )
        decision = (
            ReviewDecision.APPROVED
            if all(item.outcome is ReviewOutcome.PASS for item in cells)
            else ReviewDecision.REVISION_REQUIRED
        )
        reviewed_at = self._now()
        core = {
            "candidate_id": candidate.candidate_id.value,
            "candidate_digest": candidate.digest.value,
            "matrix": tuple(cells),
            "decision": decision.value,
            "task_validation_digest": validation.digest.value,
            "reviewed_at": reviewed_at,
        }
        digest = digest_of(core)
        review = AnswerReviewResult(
            review_id=StableId(f"answer_review_{digest.value[-32:]}"),
            candidate_id=candidate.candidate_id,
            candidate_digest=candidate.digest,
            matrix=tuple(cells),
            decision=decision,
            task_validation_digest=validation.digest,
            digest=digest,
            reviewed_at=reviewed_at,
        )
        return self._repository.save_review(review)

    def authorize(
        self,
        *,
        task: ConversationalTask,
        candidate: AnswerCandidate,
        review: AnswerReviewResult,
    ) -> FinalResponseAuthorization:
        existing = self._repository.get_authorization_for_candidate(
            candidate.candidate_id
        )
        if existing is not None:
            if (
                existing.candidate_digest != candidate.digest
                or existing.review_id != review.review_id
                or existing.review_digest != review.digest
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "stored response authorization binds different evidence",
                )
            return existing
        if review.decision is not ReviewDecision.APPROVED or review.candidate_digest != candidate.digest:
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "only an approved exact candidate can be authorized")
        validation = self._tasks.validate_for_response(
            task_id=task.task_id,
            expected_revision=task.revision,
            expected_orchestration_revision=task.orchestration_revision,
            candidate_id=candidate.candidate_id,
            purpose="DELIVERY_DISPATCH",
        )
        if validation.outcome != "ALLOW" or not self._claims_current(candidate):
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "candidate delivery authority is stale")
        authorized_at = self._now()
        core = {
            "task_id": task.task_id.value,
            "task_revision": task.revision.value,
            "orchestration_revision": task.orchestration_revision.value,
            "candidate_id": candidate.candidate_id.value,
            "candidate_digest": candidate.digest.value,
            "review_id": review.review_id.value,
            "review_digest": review.digest.value,
            "task_validation_digest": validation.digest.value,
            "classification": task.classification,
            "authorized_at": authorized_at,
        }
        digest = digest_of(core)
        authorization = FinalResponseAuthorization(
            authorization_id=StableId(f"response_authorization_{digest.value[-32:]}"),
            task_id=task.task_id,
            task_revision=task.revision.value,
            orchestration_revision=task.orchestration_revision.value,
            candidate_id=candidate.candidate_id,
            candidate_digest=candidate.digest,
            review_id=review.review_id,
            review_digest=review.digest,
            task_validation_digest=validation.digest,
            classification=task.classification,
            digest=digest,
            authorized_at=authorized_at,
        )
        return self._repository.save_authorization(authorization)

    def deliver(
        self,
        *,
        task: ConversationalTask,
        candidate: AnswerCandidate,
        authorization: FinalResponseAuthorization,
        adapter: ResponseAdapter,
    ) -> LogicalDelivery:
        if authorization.candidate_digest != candidate.digest:
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "authorization binds another candidate")
        validation = self._tasks.validate_for_response(
            task_id=task.task_id,
            expected_revision=task.revision,
            expected_orchestration_revision=task.orchestration_revision,
            candidate_id=candidate.candidate_id,
            purpose="DELIVERY_DISPATCH",
        )
        if validation.outcome != "ALLOW" or not self._claims_current(candidate):
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "delivery preconditions are stale")
        delivery = self._repository.prepare_delivery(
            task=task, candidate=candidate, authorization=authorization, occurred_at=self._now()
        )
        if delivery.state is DeliveryState.DELIVERED:
            return delivery
        if delivery.state is DeliveryState.PREPARED:
            delivery = self._repository.transition_delivery(
                delivery_id=delivery.delivery_id,
                expected_revision=delivery.revision,
                target=DeliveryState.SENDING,
                receipt=None,
                failure_code=None,
                occurred_at=self._now(),
            )
        if delivery.state not in {DeliveryState.SENDING, DeliveryState.OUTCOME_PENDING}:
            raise DomainError(
                ErrorCode.MANAGEMENT_STATE_CONFLICT,
                "logical delivery is not dispatchable",
            )
        try:
            receipt = adapter.send(
                adapter_idempotency_key=delivery.adapter_idempotency_key,
                body=candidate.body,
                body_digest=delivery.body_digest,
            )
        except DeliveryOutcomePending:
            return self._repository.transition_delivery(
                delivery_id=delivery.delivery_id,
                expected_revision=delivery.revision,
                target=DeliveryState.OUTCOME_PENDING,
                receipt=None,
                failure_code="DELIVERY_OUTCOME_PENDING",
                occurred_at=self._now(),
            )
        if (
            receipt.adapter_idempotency_key != delivery.adapter_idempotency_key
            or receipt.body_digest != delivery.body_digest
            or not receipt.accepted
        ):
            return self._repository.transition_delivery(
                delivery_id=delivery.delivery_id,
                expected_revision=delivery.revision,
                target=DeliveryState.FAILED,
                receipt=None,
                failure_code="ADAPTER_RECEIPT_INVALID",
                occurred_at=self._now(),
            )
        return self._repository.transition_delivery(
            delivery_id=delivery.delivery_id,
            expected_revision=delivery.revision,
            target=DeliveryState.DELIVERED,
            receipt=receipt,
            failure_code=None,
            occurred_at=self._now(),
        )

    def cancel_before_dispatch(
        self,
        *,
        task: ConversationalTask,
        candidate: AnswerCandidate,
        authorization: FinalResponseAuthorization,
        reason: str,
    ) -> LogicalDelivery:
        """Cancel the one logical delivery only while it is still undispatched."""

        if authorization.candidate_digest != candidate.digest:
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "authorization binds another candidate")
        delivery = self._repository.prepare_delivery(
            task=task,
            candidate=candidate,
            authorization=authorization,
            occurred_at=self._now(),
        )
        if delivery.state is DeliveryState.CANCELED_BEFORE_DISPATCH:
            return delivery
        if delivery.state is not DeliveryState.PREPARED:
            raise DomainError(
                ErrorCode.MANAGEMENT_STATE_CONFLICT,
                "delivery cannot be canceled after dispatch",
            )
        return self._repository.transition_delivery(
            delivery_id=delivery.delivery_id,
            expected_revision=delivery.revision,
            target=DeliveryState.CANCELED_BEFORE_DISPATCH,
            receipt=None,
            failure_code=_cancellation_reason(reason),
            occurred_at=self._now(),
        )

    def _review_claim(
        self,
        claim: AnswerClaim,
        candidate: AnswerCandidate,
        assessment: SufficiencyAssessment,
        requirement: KnowledgeRequirement | None,
    ) -> tuple[bool, str | None, tuple[StableId, ...]]:
        if claim.kind is AnswerClaimKind.FORMAL_KNOWLEDGE:
            try:
                record = self._knowledge.get_record(candidate.snapshot_id, claim.formal_reference)
            except DomainError:
                return False, "formal reference is absent from exact snapshot", ()
            passed = record.object_digest == claim.formal_digest and record.text == claim.text
            return passed, None if passed else "claim text exceeds its formal proposition", (record.object_id,)
        item = next(value for value in assessment.items if value.need_id == claim.need_id)
        if claim.kind is AnswerClaimKind.APPLICATION_LIMITATION:
            passed = (
                item.status is NeedStatus.SATISFIED
                and item.proof is not None
                and claim.text in item.limitations
                and claim.gap == claim.text
                and claim.formal_reference is None
                and claim.formal_digest is None
                and claim.support_proof_id == item.proof.proof_id
            )
            return (
                passed,
                None if passed else "application limitation differs from assessment",
                (),
            )
        disclosure = _assessment_disclosure(item)
        expected_text = None
        if requirement is not None:
            need = next(
                value for value in requirement.needs if value.need_id == claim.need_id
            )
            expected_text = _explicit_gap_text(
                need.question,
                disclosure,
                joint_constraint_impact=_joint_constraint_impact(
                    claim.need_id, assessment, requirement
                ),
            )
        passed = (
            claim.kind is AnswerClaimKind.KNOWLEDGE_GAP
            and claim.gap == disclosure
            and (expected_text is None or claim.text == expected_text)
        )
        return passed, None if passed else "gap disclosure differs from assessment", ()

    def _claims_current(self, candidate: AnswerCandidate) -> bool:
        for claim in candidate.claims:
            if claim.kind is not AnswerClaimKind.FORMAL_KNOWLEDGE:
                continue
            try:
                record = self._knowledge.get_record(candidate.snapshot_id, claim.formal_reference)
            except DomainError:
                return False
            if record.object_digest != claim.formal_digest:
                return False
        return True

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return an aware datetime")
        return value.astimezone(timezone.utc)


def _cancellation_reason(value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "cancellation reason is required")
    return normalized[:512]


def _canonical_answer_body(claims: tuple[AnswerClaim, ...]) -> str:
    return "\n".join(dict.fromkeys(item.text for item in claims))


def _assessment_disclosure(item: SufficiencyItem) -> str:
    if item.status is NeedStatus.GAP and item.gap:
        return item.gap
    if item.status is NeedStatus.CONFLICT:
        references = ", ".join(reference.value for reference in item.conflicts)
        return (
            f"knowledge conflict: supplied formal records disagree ({references})"
            if references
            else "knowledge conflict: the assessment found unresolved conflicting support"
        )
    if item.status is NeedStatus.UNKNOWN:
        detail = "; ".join(item.unknowns)
        return f"knowledge unknown: {detail or 'the assessment could not establish sufficiency'}"
    raise DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        "a satisfied Need has no gap disclosure",
    )


def _explicit_gap_text(
    question: str,
    disclosure: str,
    *,
    joint_constraint_impact: tuple[str, ...] = (),
) -> str:
    if any(
        "\u3400" <= character <= "\u9fff"
        or "\uf900" <= character <= "\ufaff"
        for character in question
    ):
        text = (
            f"问题：{question}\n"
            "基于当前授权证据，尚无法给出已验证的答案。\n"
            f"证据缺口：{disclosure}"
        )
        if joint_constraint_impact:
            text += "\n尚未确认的相关关系：" + "；".join(
                joint_constraint_impact
            )
        return text
    text = (
        f"Requested question: {question}\n"
        "Verified answer: unavailable from the authorized evidence.\n"
        f"Evidence gap: {disclosure}"
    )
    if joint_constraint_impact:
        text += "\nRelated answer relationships not established: " + "; ".join(
            joint_constraint_impact
        )
    return text


def _joint_constraint_impact(
    need_id: str,
    assessment: SufficiencyAssessment,
    requirement: KnowledgeRequirement,
) -> tuple[str, ...]:
    failed = frozenset(assessment.joint_constraint_failures)
    return tuple(
        constraint.description
        for constraint in requirement.joint_constraints
        if constraint.constraint_id in failed and need_id in constraint.need_ids
    )


def _validate_semantic_review(value: object) -> None:
    if (
        not isinstance(value, SemanticAnswerReviewDecision)
        or len(value.failed_dimensions) != len(set(value.failed_dimensions))
        or any(not isinstance(item, ReviewDimension) for item in value.failed_dimensions)
        or any(
            not isinstance(item, str) or not item.strip() or item != item.strip()
            for item in value.findings
        )
        or (value.approved and (value.failed_dimensions or value.findings))
        or (not value.approved and (not value.failed_dimensions or not value.findings))
    ):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "semantic answer reviewer returned an invalid decision",
        )
