"""Exact-snapshot knowledge use and per-Need sufficiency proofs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Protocol

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine import (
    FormalKnowledgeRecord,
    FormalKnowledgeService,
    KnowledgeObjectKind,
    KNOWLEDGE_TERM_MATCH_POLICY,
    KnowledgeSnapshot,
)


SEMANTIC_CANDIDATE_EXPANSION_POLICY = (
    "TERM_MATCH_THEN_COMPLETE_BOUNDED_KIND_TYPE_EXPANSION@2"
)
# Compatibility name retained for callers that recorded the first policy name.
SEMANTIC_ZERO_MATCH_FALLBACK_POLICY = SEMANTIC_CANDIDATE_EXPANSION_POLICY


class RequirementFidelity(str, Enum):
    ORIGINAL = "ORIGINAL"
    CLARIFIED = "CLARIFIED"


class NeedStatus(str, Enum):
    SATISFIED = "SATISFIED"
    GAP = "GAP"
    CONFLICT = "CONFLICT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class TaskBoundary:
    task_id: StableId
    task_revision: Revision
    scope_id: StableId
    purpose: str
    classification: str
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        task_id: StableId,
        task_revision: Revision,
        scope_id: StableId,
        purpose: str,
        classification: str,
    ) -> "TaskBoundary":
        core = {
            "task_id": task_id.value,
            "task_revision": task_revision.value,
            "scope_id": scope_id.value,
            "purpose": _text(purpose, "task purpose"),
            "classification": _text(classification, "classification"),
        }
        return cls(
            task_id=task_id,
            task_revision=task_revision,
            scope_id=scope_id,
            purpose=core["purpose"],
            classification=core["classification"],
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class KnowledgeNeed:
    need_id: str
    question: str
    required_kinds: tuple[KnowledgeObjectKind, ...]
    required_type_names: tuple[str, ...]
    required_terms: tuple[str, ...]
    minimum_support_count: int

    def __post_init__(self) -> None:
        _text(self.need_id, "need ID")
        _text(self.question, "need question")
        if self.minimum_support_count < 1:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "minimum support count must be positive")


@dataclass(frozen=True, slots=True)
class JointConstraint:
    constraint_id: str
    need_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True, slots=True)
class KnowledgeRequirement:
    requirement_id: StableId
    revision: Revision
    fidelity: RequirementFidelity
    original_request: str
    needs: tuple[KnowledgeNeed, ...]
    joint_constraints: tuple[JointConstraint, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        requirement_id: StableId,
        revision: Revision,
        fidelity: RequirementFidelity,
        original_request: str,
        needs: tuple[KnowledgeNeed, ...],
        joint_constraints: tuple[JointConstraint, ...] = (),
    ) -> "KnowledgeRequirement":
        if not needs:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "knowledge requirement has no needs")
        need_ids = {item.need_id for item in needs}
        if len(need_ids) != len(needs):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "need IDs must be unique")
        for constraint in joint_constraints:
            if not constraint.need_ids or any(item not in need_ids for item in constraint.need_ids):
                raise DomainError(ErrorCode.INVALID_ARGUMENT, "joint constraint has unknown needs")
        core = {
            "requirement_id": requirement_id.value,
            "revision": revision.value,
            "fidelity": fidelity.value,
            "original_request": _text(original_request, "original request"),
            "needs": needs,
            "joint_constraints": joint_constraints,
        }
        return cls(
            requirement_id=requirement_id,
            revision=revision,
            fidelity=fidelity,
            original_request=core["original_request"],
            needs=needs,
            joint_constraints=joint_constraints,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class KnowledgeRequirementPlan:
    """Untrusted task decomposition; the runtime seals the final requirement identity."""

    needs: tuple[KnowledgeNeed, ...]
    joint_constraints: tuple[JointConstraint, ...] = ()

    def __post_init__(self) -> None:
        if not self.needs:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "requirement plan has no Needs")
        need_ids = {item.need_id for item in self.needs}
        if len(need_ids) != len(self.needs):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "planned Need IDs must be unique")
        for constraint in self.joint_constraints:
            if (
                not constraint.need_ids
                or any(item not in need_ids for item in constraint.need_ids)
            ):
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "planned joint constraint references an unknown Need",
                )


class KnowledgeRequirementPlanner(Protocol):
    def plan(self, *, original_request: str) -> KnowledgeRequirementPlan: ...


@dataclass(frozen=True, slots=True)
class SnapshotReadSession:
    session_id: StableId
    task_boundary_digest: Digest
    requirement_id: StableId
    requirement_revision: Revision
    snapshot_id: StableId
    snapshot_revision: Revision
    snapshot_manifest_digest: Digest
    opened_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class KnowledgeReadSet:
    need_id: str
    records: tuple[FormalKnowledgeRecord, ...]
    query_digest: Digest
    complete: bool
    digest: Digest


@dataclass(frozen=True, slots=True)
class NeedSupportProof:
    proof_id: StableId
    need_id: str
    snapshot_id: StableId
    snapshot_manifest_digest: Digest
    read_session_id: StableId
    supporting_references: tuple[StableId, ...]
    supporting_digests: tuple[Digest, ...]
    criterion_digest: Digest
    digest: Digest


@dataclass(frozen=True, slots=True)
class SufficiencyItem:
    need_id: str
    status: NeedStatus
    proof: NeedSupportProof | None
    gap: str | None
    counterexamples: tuple[StableId, ...]
    conflicts: tuple[StableId, ...]
    unknowns: tuple[str, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SufficiencyAssessment:
    assessment_id: StableId
    requirement_id: StableId
    requirement_revision: Revision
    read_session_id: StableId
    snapshot_id: StableId
    items: tuple[SufficiencyItem, ...]
    joint_constraint_failures: tuple[str, ...]
    sufficient: bool
    assessed_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class NeedSufficiencyDecision:
    """Untrusted semantic decision that the service validates against one read set."""

    status: NeedStatus
    supporting_references: tuple[StableId, ...] = ()
    gap: str | None = None
    counterexamples: tuple[StableId, ...] = ()
    conflicts: tuple[StableId, ...] = ()
    unknowns: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class NeedSufficiencyEvaluator(Protocol):
    def evaluate(
        self,
        *,
        requirement: KnowledgeRequirement,
        need: KnowledgeNeed,
        read_set: KnowledgeReadSet,
    ) -> NeedSufficiencyDecision: ...


class DeterministicNeedSufficiencyEvaluator:
    """Compatibility evaluator preserving the original count-based behavior."""

    def evaluate(
        self,
        *,
        requirement: KnowledgeRequirement,
        need: KnowledgeNeed,
        read_set: KnowledgeReadSet,
    ) -> NeedSufficiencyDecision:
        del requirement
        if not read_set.complete:
            return NeedSufficiencyDecision(
                status=NeedStatus.UNKNOWN,
                unknowns=("knowledge query exceeded the bounded assessment page",),
                limitations=("assessment read set is incomplete",),
            )
        if len(read_set.records) < need.minimum_support_count:
            return NeedSufficiencyDecision(
                status=NeedStatus.GAP,
                gap=(
                    f"requires {need.minimum_support_count} formal support record(s); "
                    f"found {len(read_set.records)}"
                ),
            )
        return NeedSufficiencyDecision(
            status=NeedStatus.SATISFIED,
            supporting_references=tuple(item.object_id for item in read_set.records),
        )


class KnowledgeUseRepository(Protocol):
    def get_assessment(self, assessment_id: StableId) -> SufficiencyAssessment: ...

    def open_session(
        self,
        *,
        idempotency_key: IdempotencyKey,
        boundary: TaskBoundary,
        requirement: KnowledgeRequirement,
        snapshot: KnowledgeSnapshot,
        opened_at: datetime,
    ) -> SnapshotReadSession: ...

    def record_assessment(
        self,
        *,
        idempotency_key: IdempotencyKey,
        requirement: KnowledgeRequirement,
        session: SnapshotReadSession,
        items: tuple[SufficiencyItem, ...],
        joint_constraint_failures: tuple[str, ...],
        sufficient: bool,
        assessed_at: datetime,
    ) -> SufficiencyAssessment: ...


class KnowledgeUseService:
    def __init__(
        self,
        repository: KnowledgeUseRepository,
        knowledge: FormalKnowledgeService,
        *,
        evaluator: NeedSufficiencyEvaluator | None = None,
        strategy_implementation_digest: Digest | None = None,
        strategy_qualification_ref: str | None = None,
        strategy_classification: str | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._knowledge = knowledge
        self._evaluator = evaluator or DeterministicNeedSufficiencyEvaluator()
        evaluator_digest = getattr(
            self._evaluator, "strategy_implementation_digest", None
        )
        if (
            strategy_implementation_digest is not None
            and evaluator_digest is not None
            and strategy_implementation_digest != evaluator_digest
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "knowledge sufficiency evaluator does not match its strategy implementation",
            )
        self._strategy_implementation_digest = (
            strategy_implementation_digest or evaluator_digest
        )
        evaluator_qualification_ref = getattr(
            self._evaluator, "qualification_ref", None
        )
        if (
            strategy_qualification_ref is not None
            and evaluator_qualification_ref is not None
            and strategy_qualification_ref != evaluator_qualification_ref
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "knowledge sufficiency evaluator uses another qualification",
            )
        self._strategy_qualification_ref = (
            strategy_qualification_ref or evaluator_qualification_ref
        )
        evaluator_classification = getattr(self._evaluator, "classification", None)
        if (
            strategy_classification is not None
            and evaluator_classification is not None
            and strategy_classification != evaluator_classification
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "knowledge sufficiency evaluator uses another classification",
            )
        self._strategy_classification = (
            strategy_classification or evaluator_classification
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

    def open_session(
        self,
        *,
        idempotency_key: IdempotencyKey,
        boundary: TaskBoundary,
        requirement: KnowledgeRequirement,
        snapshot_id: StableId,
    ) -> SnapshotReadSession:
        snapshot = self._knowledge.get_snapshot(snapshot_id)
        if snapshot.scope_id != boundary.scope_id:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "snapshot is outside the task boundary")
        return self._repository.open_session(
            idempotency_key=idempotency_key,
            boundary=boundary,
            requirement=requirement,
            snapshot=snapshot,
            opened_at=self._now(),
        )

    def get_assessment(self, assessment_id: StableId) -> SufficiencyAssessment:
        return self._repository.get_assessment(assessment_id)

    def assess(
        self,
        *,
        idempotency_key: IdempotencyKey,
        requirement: KnowledgeRequirement,
        session: SnapshotReadSession,
    ) -> SufficiencyAssessment:
        if (
            session.requirement_id != requirement.requirement_id
            or session.requirement_revision != requirement.revision
        ):
            raise DomainError(ErrorCode.REVISION_CONFLICT, "read session binds another requirement revision")
        items: list[SufficiencyItem] = []
        for need in requirement.needs:
            records, next_cursor = self._knowledge.query_snapshot(
                snapshot_id=session.snapshot_id,
                kinds=need.required_kinds,
                type_names=need.required_type_names,
                terms=need.required_terms,
                cursor=0,
                limit=500,
            )
            semantic_expansion_applied = False
            if need.required_terms and getattr(
                self._evaluator,
                "semantic_candidate_expansion_enabled",
                getattr(
                    self._evaluator,
                    "semantic_zero_match_fallback_enabled",
                    False,
                ),
            ):
                expansion_limit = getattr(
                    self._evaluator, "semantic_candidate_expansion_limit", 100
                )
                expanded, expanded_cursor = self._knowledge.query_snapshot(
                    snapshot_id=session.snapshot_id,
                    kinds=need.required_kinds,
                    type_names=need.required_type_names,
                    terms=(),
                    cursor=0,
                    limit=expansion_limit + 1,
                )
                if expanded_cursor is None and len(expanded) <= expansion_limit:
                    records, next_cursor = expanded, None
                    semantic_expansion_applied = True
                elif not records:
                    # An empty lexical result over a larger semantic candidate
                    # space is not a verified gap. Preserve an incomplete or
                    # over-budget read set so the evaluator returns UNKNOWN.
                    records, next_cursor = expanded, expanded_cursor
            criterion_digest = digest_of(need)
            query_digest = digest_of(
                {
                    "snapshot_id": session.snapshot_id.value,
                    "need_id": need.need_id,
                    "kinds": tuple(item.value for item in need.required_kinds),
                    "type_names": need.required_type_names,
                    "terms": need.required_terms,
                    "term_match_policy": KNOWLEDGE_TERM_MATCH_POLICY,
                    "semantic_candidate_expansion_policy": (
                        SEMANTIC_CANDIDATE_EXPANSION_POLICY
                    ),
                    "semantic_expansion_applied": semantic_expansion_applied,
                    "limit": 500,
                }
            )
            read_set = KnowledgeReadSet(
                need_id=need.need_id,
                records=records,
                query_digest=query_digest,
                complete=next_cursor is None,
                digest=digest_of(
                    {
                        "need_id": need.need_id,
                        "records": tuple((item.object_id.value, item.object_digest.value) for item in records),
                        "query_digest": query_digest.value,
                        "complete": next_cursor is None,
                    }
                ),
            )
            decision = self._evaluator.evaluate(
                requirement=requirement,
                need=need,
                read_set=read_set,
            )
            selected_records = _validate_sufficiency_decision(
                need=need,
                read_set=read_set,
                decision=decision,
            )
            if decision.status is NeedStatus.SATISFIED:
                proof_core = {
                    "need_id": need.need_id,
                    "snapshot_id": session.snapshot_id.value,
                    "snapshot_manifest_digest": session.snapshot_manifest_digest.value,
                    "read_session_id": session.session_id.value,
                    "support": tuple(
                        (record.object_id.value, record.object_digest.value)
                        for record in selected_records
                    ),
                    "criterion_digest": criterion_digest.value,
                    "read_set_digest": read_set.digest.value,
                }
                proof_digest = digest_of(proof_core)
                proof = NeedSupportProof(
                    proof_id=StableId(f"need_proof_{proof_digest.value[-32:]}"),
                    need_id=need.need_id,
                    snapshot_id=session.snapshot_id,
                    snapshot_manifest_digest=session.snapshot_manifest_digest,
                    read_session_id=session.session_id,
                    supporting_references=tuple(
                        record.object_id for record in selected_records
                    ),
                    supporting_digests=tuple(
                        record.object_digest for record in selected_records
                    ),
                    criterion_digest=criterion_digest,
                    digest=proof_digest,
                )
                item = SufficiencyItem(
                    need_id=need.need_id,
                    status=NeedStatus.SATISFIED,
                    proof=proof,
                    gap=None,
                    counterexamples=(),
                    conflicts=(),
                    unknowns=(),
                    limitations=decision.limitations,
                )
            else:
                item = SufficiencyItem(
                    need_id=need.need_id,
                    status=decision.status,
                    proof=None,
                    gap=decision.gap,
                    counterexamples=decision.counterexamples,
                    conflicts=decision.conflicts,
                    unknowns=decision.unknowns,
                    limitations=decision.limitations,
                )
            items.append(item)
        statuses = {item.need_id: item.status for item in items}
        joint_failures = tuple(
            constraint.constraint_id
            for constraint in requirement.joint_constraints
            if any(statuses[need_id] is not NeedStatus.SATISFIED for need_id in constraint.need_ids)
        )
        sufficient = all(item.status is NeedStatus.SATISFIED for item in items) and not joint_failures
        return self._repository.record_assessment(
            idempotency_key=idempotency_key,
            requirement=requirement,
            session=session,
            items=tuple(items),
            joint_constraint_failures=joint_failures,
            sufficient=sufficient,
            assessed_at=self._now(),
        )

    def rebind_and_reassess(
        self,
        *,
        session_key: IdempotencyKey,
        assessment_key: IdempotencyKey,
        boundary: TaskBoundary,
        requirement: KnowledgeRequirement,
        new_snapshot_id: StableId,
    ) -> SufficiencyAssessment:
        session = self.open_session(
            idempotency_key=session_key,
            boundary=boundary,
            requirement=requirement,
            snapshot_id=new_snapshot_id,
        )
        return self.assess(
            idempotency_key=assessment_key, requirement=requirement, session=session
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return an aware datetime")
        return value.astimezone(timezone.utc)


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def _validate_sufficiency_decision(
    *,
    need: KnowledgeNeed,
    read_set: KnowledgeReadSet,
    decision: NeedSufficiencyDecision,
) -> tuple[FormalKnowledgeRecord, ...]:
    if not isinstance(decision, NeedSufficiencyDecision):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "Need sufficiency evaluator returned an invalid decision",
        )
    records = {item.object_id: item for item in read_set.records}
    reference_groups = (
        decision.supporting_references,
        decision.counterexamples,
        decision.conflicts,
    )
    if any(len(group) != len(set(group)) for group in reference_groups):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "Need sufficiency decision contains duplicate references",
        )
    if any(reference not in records for group in reference_groups for reference in group):
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Need sufficiency decision references knowledge outside its exact read set",
        )
    if any(not _decision_text(item) for item in (*decision.unknowns, *decision.limitations)):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "Need sufficiency decision contains an empty disclosure",
        )
    if decision.status is NeedStatus.SATISFIED:
        if (
            not read_set.complete
            or len(decision.supporting_references) < need.minimum_support_count
            or decision.gap is not None
            or decision.counterexamples
            or decision.conflicts
            or decision.unknowns
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "a satisfied Need decision is not closed over its exact read set",
            )
    elif decision.supporting_references:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "an unsatisfied Need cannot issue a support proof",
        )
    if decision.status is NeedStatus.GAP and not _decision_text(decision.gap):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "a GAP Need decision requires a gap disclosure",
        )
    if decision.status is not NeedStatus.GAP and decision.gap is not None:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "only a GAP Need decision may carry a gap disclosure",
        )
    if decision.status is NeedStatus.CONFLICT and not decision.conflicts:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "a CONFLICT Need decision requires conflict references",
        )
    if decision.status is NeedStatus.UNKNOWN and not decision.unknowns:
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "an UNKNOWN Need decision requires an unknown disclosure",
        )
    return tuple(records[reference] for reference in decision.supporting_references)


def _decision_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()
