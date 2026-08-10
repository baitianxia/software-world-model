"""Task-driven, bounded Knowledge Update orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Mapping, Protocol

from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine import (
    AdmissionStatus,
    EntityProposal,
    EvidenceProposal,
    FactProposal,
    FormalKnowledgeRecord,
    FormalKnowledgeService,
    KnowledgeCandidateBundle,
    KnowledgeContext,
    KnowledgeObjectKind,
    KnowledgeScopeService,
    ScopePurpose,
)
from software_world_model.source_integration import (
    OperationBudget,
    ResolutionOutcome,
    SourceArtifact,
    SourceConfigurationService,
    SourceOperationIntent,
    SourceOperationResult,
    SourceOperationService,
    SourceOperationStatus,
    SourceTargetResolutionReceipt,
    SourceTool,
    TargetKind,
)

from .knowledge_use import KnowledgeRequirementPlan


class CoverageObligation(str, Enum):
    REQUIRED = "REQUIRED"
    SUPPORTING = "SUPPORTING"
    EXCLUDED = "EXCLUDED"


class UpdateAttemptState(str, Enum):
    PREPARING = "PREPARING"
    INVESTIGATING = "INVESTIGATING"
    ADMITTING = "ADMITTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class InvestigationStopReason(str, Enum):
    TARGET_COVERED = "TARGET_COVERED"
    SOURCE_FAILED = "SOURCE_FAILED"
    SOURCE_INCOMPLETE = "SOURCE_INCOMPLETE"
    NO_PROGRESS = "NO_PROGRESS"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    ADMISSION_REJECTED = "ADMISSION_REJECTED"
    PUBLICATION_CONFLICT = "PUBLICATION_CONFLICT"


@dataclass(frozen=True, slots=True)
class BuildObjective:
    objective_id: str
    description: str
    unacceptable_outcomes: tuple[str, ...]
    digest: Digest

    @classmethod
    def create(
        cls, *, objective_id: str, description: str, unacceptable_outcomes: tuple[str, ...]
    ) -> "BuildObjective":
        core = {
            "objective_id": _text(objective_id, "objective ID"),
            "description": _text(description, "objective description"),
            "unacceptable_outcomes": tuple(
                _text(item, "unacceptable outcome") for item in unacceptable_outcomes
            ),
        }
        return cls(**core, digest=digest_of(core))


@dataclass(frozen=True, slots=True)
class CanonicalBuildTarget:
    target_id: StableId
    target_kind: TargetKind
    canonical_identity: tuple[tuple[str, str], ...]
    resolution_receipt_id: StableId
    resolution_receipt_digest: Digest
    obligation: CoverageObligation
    boundary: str
    digest: Digest

    @classmethod
    def from_receipt(
        cls,
        receipt: SourceTargetResolutionReceipt,
        *,
        obligation: CoverageObligation = CoverageObligation.REQUIRED,
    ) -> "CanonicalBuildTarget":
        if receipt.outcome is not ResolutionOutcome.EXACT or not receipt.canonical_identity:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "only an EXACT target resolution receipt can become a build target",
            )
        core = {
            "target_kind": receipt.target_kind.value,
            "canonical_identity": receipt.canonical_identity,
            "resolution_receipt_id": receipt.receipt_id.value,
            "resolution_receipt_digest": receipt.digest.value,
            "obligation": obligation.value,
            "boundary": "EXACT",
            "canonicalization_contract": receipt.resolver_contract_version,
        }
        digest = digest_of(core)
        return cls(
            target_id=StableId(f"build_target_{digest.value[-32:]}"),
            target_kind=receipt.target_kind,
            canonical_identity=receipt.canonical_identity,
            resolution_receipt_id=receipt.receipt_id,
            resolution_receipt_digest=receipt.digest,
            obligation=obligation,
            boundary="EXACT",
            digest=digest,
        )


@dataclass(frozen=True, slots=True)
class KnowledgeUpdateRequest:
    idempotency_key: IdempotencyKey
    objective: BuildObjective
    target: CanonicalBuildTarget
    scope_id: StableId
    scope_revision: Revision
    source_id: StableId
    source_revision: Revision
    binding_id: StableId
    binding_revision: Revision
    expected_current_snapshot_id: StableId | None
    max_steps: int
    max_items_per_step: int
    max_bytes_per_step: int
    classification: str
    actor: str
    correlation_ref: CorrelationRef
    requirement_plan: KnowledgeRequirementPlan | None = None
    allowed_source_paths: tuple[str, ...] = ()
    required_source_paths: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.allowed_source_paths) != len(set(self.allowed_source_paths)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "allowed source paths must be unique",
            )
        if len(self.required_source_paths) != len(set(self.required_source_paths)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "required source paths must be unique",
            )
        if self.allowed_source_paths and not set(
            self.required_source_paths
        ).issubset(self.allowed_source_paths):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "required source paths must be inside the allowed source boundary",
            )

    @property
    def digest(self) -> Digest:
        return digest_of(
            {
                "command": "KnowledgeUpdate@1",
                "objective_digest": self.objective.digest.value,
                "target_digest": self.target.digest.value,
                "scope_id": self.scope_id.value,
                "scope_revision": self.scope_revision.value,
                "source_id": self.source_id.value,
                "source_revision": self.source_revision.value,
                "binding_id": self.binding_id.value,
                "binding_revision": self.binding_revision.value,
                "expected_current_snapshot_id": (
                    self.expected_current_snapshot_id.value
                    if self.expected_current_snapshot_id
                    else None
                ),
                "limits": (self.max_steps, self.max_items_per_step, self.max_bytes_per_step),
                "classification": self.classification,
                "actor": self.actor,
                "requirement_plan_digest": (
                    digest_of(self.requirement_plan).value
                    if self.requirement_plan is not None
                    else None
                ),
                "allowed_source_paths": self.allowed_source_paths,
                "required_source_paths": self.required_source_paths,
            }
        )


@dataclass(frozen=True, slots=True)
class KnowledgeUpdateAttempt:
    attempt_id: StableId
    request_digest: Digest
    state: UpdateAttemptState
    created_at: datetime
    revised_at: datetime


@dataclass(frozen=True, slots=True)
class KnowledgeUpdateResult:
    result_id: StableId
    attempt_id: StableId
    request_digest: Digest
    state: UpdateAttemptState
    stop_reason: InvestigationStopReason
    target_digest: Digest
    source_operation_references: tuple[StableId, ...]
    artifact_references: tuple[StableId, ...]
    target_coverage_complete: bool
    admission_id: StableId | None
    admission_status: AdmissionStatus | None
    published_snapshot_id: StableId | None
    limitations: tuple[str, ...]
    completed_at: datetime
    digest: Digest


class KnowledgeUpdateRepository(Protocol):
    def begin(
        self, *, request: KnowledgeUpdateRequest, occurred_at: datetime
    ) -> tuple[KnowledgeUpdateAttempt, KnowledgeUpdateResult | None]: ...

    def record_step(
        self,
        *,
        attempt_id: StableId,
        ordinal: int,
        action_digest: Digest,
        operation_id: StableId,
        artifact_ids: tuple[StableId, ...],
        progress_digest: Digest,
        occurred_at: datetime,
    ) -> None: ...

    def finish(
        self,
        *,
        attempt_id: StableId,
        state: UpdateAttemptState,
        stop_reason: InvestigationStopReason,
        target_digest: Digest,
        operation_ids: tuple[StableId, ...],
        artifact_ids: tuple[StableId, ...],
        coverage_complete: bool,
        admission_id: StableId | None,
        admission_status: AdmissionStatus | None,
        snapshot_id: StableId | None,
        limitations: tuple[str, ...],
        occurred_at: datetime,
    ) -> KnowledgeUpdateResult: ...


@dataclass(frozen=True, slots=True)
class SourceActionProposal:
    """Untrusted next-step proposal; Application Services re-authorizes it."""

    tool: SourceTool | None
    parameters: tuple[tuple[str, str], ...]
    stop: bool
    rationale: str

    @classmethod
    def execute(
        cls,
        tool: SourceTool,
        parameters: Mapping[str, str],
        *,
        rationale: str,
    ) -> "SourceActionProposal":
        return cls(
            tool=tool,
            parameters=tuple(sorted(parameters.items())),
            stop=False,
            rationale=_text(rationale, "source action rationale"),
        )

    @classmethod
    def finish(cls, *, rationale: str) -> "SourceActionProposal":
        return cls(
            tool=None,
            parameters=(),
            stop=True,
            rationale=_text(rationale, "source stop rationale"),
        )


class SourceInvestigationPlanner(Protocol):
    def propose(
        self,
        *,
        request: KnowledgeUpdateRequest,
        completed_operations: tuple[SourceOperationResult, ...],
        ordinal: int,
    ) -> SourceActionProposal: ...


class DeterministicSourceInvestigationPlanner:
    """Compatibility planner for exact targets; model planners are injected."""

    def propose(
        self,
        *,
        request: KnowledgeUpdateRequest,
        completed_operations: tuple[SourceOperationResult, ...],
        ordinal: int,
    ) -> SourceActionProposal:
        del ordinal
        if _operations_cover_target(request.target, completed_operations):
            return SourceActionProposal.finish(
                rationale="the exact deterministic target is fully observed"
            )
        cursor = None
        if completed_operations:
            observation = completed_operations[-1].observation
            if observation is not None and observation.has_more:
                cursor = observation.next_cursor
        tool, parameters = _next_action(request.target, cursor)
        return SourceActionProposal.execute(
            tool,
            parameters,
            rationale="execute the next deterministic exact-target source action",
        )


class KnowledgeCandidateBuilder(Protocol):
    def build(
        self,
        *,
        request: KnowledgeUpdateRequest,
        target: CanonicalBuildTarget,
        artifacts: tuple[SourceArtifact, ...],
        source_operations: tuple[SourceOperationResult, ...] = (),
    ) -> KnowledgeCandidateBundle: ...


class KnowledgeInferenceBuilder(Protocol):
    def build_inferences(
        self,
        *,
        request: KnowledgeUpdateRequest,
        target: CanonicalBuildTarget,
        premises: tuple[FormalKnowledgeRecord, ...],
    ) -> KnowledgeCandidateBundle: ...


class DirectTextKnowledgeBuilder:
    """A safe deterministic INITIAL builder; it makes only literal text facts."""

    def build(
        self,
        *,
        request: KnowledgeUpdateRequest,
        target: CanonicalBuildTarget,
        artifacts: tuple[SourceArtifact, ...],
        source_operations: tuple[SourceOperationResult, ...] = (),
    ) -> KnowledgeCandidateBundle:
        del request, source_operations
        evidence: list[EvidenceProposal] = []
        entities: list[EntityProposal] = []
        facts: list[FactProposal] = []
        identity = dict(target.canonical_identity)
        context = KnowledgeContext.create(
            {key: value for key, value in identity.items() if key in {"revision", "base", "target"}}
        )
        for index, artifact in enumerate(artifacts):
            if artifact.truncated or not artifact.payload:
                continue
            try:
                text = artifact.payload.decode("utf-8")
            except UnicodeDecodeError:
                continue
            evidence_key = f"evidence:{index}"
            entity_key = f"entity:{index}"
            evidence.append(
                EvidenceProposal(
                    evidence_key=evidence_key,
                    artifact=artifact,
                    byte_start=0,
                    byte_end=len(artifact.payload),
                    locator=artifact.source_native_identity,
                )
            )
            entities.append(
                EntityProposal(
                    candidate_key=entity_key,
                    entity_type="SOURCE_FILE",
                    natural_key=(
                        f"{target.digest.value}:{artifact.identity_digest.value}"
                    ),
                    label=artifact.source_native_identity,
                    context=context,
                    evidence_keys=(evidence_key,),
                )
            )
            facts.append(
                FactProposal(
                    candidate_key=f"fact:{index}",
                    subject_candidate_key=entity_key,
                    subject_entity_id=None,
                    predicate="DESCRIBED_AS",
                    object_value=text,
                    context=context,
                    evidence_keys=(evidence_key,),
                )
            )
        return KnowledgeCandidateBundle(
            schema_version="INITIAL@1",
            evidence=tuple(evidence),
            entities=tuple(entities),
            facts=tuple(facts),
            inferences=(),
        )


class KnowledgeUpdateService:
    def __init__(
        self,
        repository: KnowledgeUpdateRepository,
        scopes: KnowledgeScopeService,
        configurations: SourceConfigurationService,
        operations: SourceOperationService,
        knowledge: FormalKnowledgeService,
        *,
        builder: KnowledgeCandidateBuilder | None = None,
        planner: SourceInvestigationPlanner | None = None,
        strategy_implementation_digest: Digest | None = None,
        strategy_qualification_ref: str | None = None,
        strategy_classification: str | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._scopes = scopes
        self._configurations = configurations
        self._operations = operations
        self._knowledge = knowledge
        self._builder = builder or DirectTextKnowledgeBuilder()
        self._planner = planner or DeterministicSourceInvestigationPlanner()
        builder_digest = getattr(self._builder, "strategy_implementation_digest", None)
        planner_digest = getattr(self._planner, "strategy_implementation_digest", None)
        component_digests = (builder_digest, planner_digest)
        if strategy_implementation_digest is not None and any(
            digest != strategy_implementation_digest for digest in component_digests
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "knowledge update components do not match their strategy implementation",
            )
        if (
            strategy_implementation_digest is None
            and builder_digest is not None
            and planner_digest is not None
            and builder_digest != planner_digest
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "knowledge update planner and builder use different strategy implementations",
            )
        self._strategy_implementation_digest = (
            strategy_implementation_digest
            or (builder_digest if builder_digest == planner_digest else None)
        )
        builder_qualification_ref = getattr(self._builder, "qualification_ref", None)
        planner_qualification_ref = getattr(self._planner, "qualification_ref", None)
        if strategy_qualification_ref is not None and any(
            reference != strategy_qualification_ref
            for reference in (builder_qualification_ref, planner_qualification_ref)
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "knowledge update components do not bind the selected qualification",
            )
        if (
            strategy_qualification_ref is None
            and builder_qualification_ref is not None
            and planner_qualification_ref is not None
            and builder_qualification_ref != planner_qualification_ref
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "knowledge update planner and builder use different qualifications",
            )
        self._strategy_qualification_ref = (
            strategy_qualification_ref
            or (
                builder_qualification_ref
                if builder_qualification_ref == planner_qualification_ref
                else None
            )
        )
        builder_classification = getattr(self._builder, "classification", None)
        planner_classification = getattr(self._planner, "classification", None)
        if strategy_classification is not None and any(
            value != strategy_classification
            for value in (builder_classification, planner_classification)
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "knowledge update components do not match their classification",
            )
        if (
            strategy_classification is None
            and builder_classification is not None
            and planner_classification is not None
            and builder_classification != planner_classification
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "knowledge update planner and builder use different classifications",
            )
        self._strategy_classification = (
            strategy_classification
            or (
                builder_classification
                if builder_classification == planner_classification
                else None
            )
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

    def execute(self, request: KnowledgeUpdateRequest) -> KnowledgeUpdateResult:
        if min(request.max_steps, request.max_items_per_step, request.max_bytes_per_step) < 1:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "update resource limits must be positive")
        attempt, replay = self._repository.begin(request=request, occurred_at=self._now())
        if replay is not None:
            return replay
        operation_ids: list[StableId] = []
        operations: list[SourceOperationResult] = []
        artifacts: list[SourceArtifact] = []
        action_digests: set[Digest] = set()
        cursor: str | None = None
        stop = InvestigationStopReason.RESOURCE_EXHAUSTED
        limitations: list[str] = []
        coverage_complete = False
        for ordinal in range(1, request.max_steps + 1):
            try:
                proposal = self._planner.propose(
                    request=request,
                    completed_operations=tuple(operations),
                    ordinal=ordinal,
                )
                _validate_source_action(request.target, proposal)
            except DomainError as exc:
                return self._repository.finish(
                    attempt_id=attempt.attempt_id,
                    state=UpdateAttemptState.FAILED,
                    stop_reason=InvestigationStopReason.SOURCE_FAILED,
                    target_digest=request.target.digest,
                    operation_ids=tuple(operation_ids),
                    artifact_ids=tuple(item.artifact_id for item in artifacts),
                    coverage_complete=_operations_cover_target(
                        request.target, tuple(operations)
                    ),
                    admission_id=None,
                    admission_status=None,
                    snapshot_id=None,
                    limitations=(
                        f"source action proposal denied: {exc.code.value}",
                    ),
                    occurred_at=self._now(),
                )
            if proposal.stop:
                coverage_complete = _operations_cover_target(
                    request.target, tuple(operations)
                )
                if coverage_complete:
                    stop = InvestigationStopReason.TARGET_COVERED
                else:
                    stop = InvestigationStopReason.SOURCE_INCOMPLETE
                    limitations.append(
                        "the investigation stopped before the exact target was completely observed"
                    )
                break
            assert proposal.tool is not None
            tool = proposal.tool
            parameters = dict(proposal.parameters)
            action_digest = digest_of(
                {
                    "target_digest": request.target.digest.value,
                    "tool": tool.value,
                    "parameters": parameters,
                    "proposal_rationale": proposal.rationale,
                }
            )
            if action_digest in action_digests:
                stop = InvestigationStopReason.NO_PROGRESS
                limitations.append("the next canonical source action repeated without new state")
                break
            action_digests.add(action_digest)
            scope_assertion = self._scopes.read_scope_state_assertion(
                scope_id=request.scope_id,
                expected_revision=request.scope_revision,
                purpose=ScopePurpose.SOURCE_EXECUTION,
                caller_ref="application-services/knowledge-update",
                request_ref=f"{request.idempotency_key.value}:step:{ordinal}",
                classification=request.classification,
            )
            eligibility = self._configurations.resolve_binding_for_execution(
                binding_id=request.binding_id,
                expected_binding_revision=request.binding_revision,
                expected_source_revision=request.source_revision,
                assertion=scope_assertion,
                tool_id=tool.value,
                classification=request.classification,
            )
            intent = SourceOperationIntent.create(
                idempotency_key=IdempotencyKey(
                    f"{request.idempotency_key.value}:source-step:{ordinal}"
                ),
                causation_reference=attempt.attempt_id.value,
                source_id=request.source_id,
                source_revision=request.source_revision,
                binding_id=request.binding_id,
                binding_revision=request.binding_revision,
                scope_assertion=scope_assertion,
                binding_eligibility=eligibility,
                tool=tool,
                parameters=parameters,
                budget=OperationBudget(
                    max_calls=1,
                    max_items=request.max_items_per_step,
                    max_bytes=request.max_bytes_per_step,
                ),
                classification=request.classification,
                correlation_ref=request.correlation_ref,
            )
            operation = self._operations.execute(intent)
            operations.append(operation)
            operation_ids.append(operation.operation_id)
            new_artifacts = operation.observation.artifacts if operation.observation else ()
            artifacts.extend(new_artifacts)
            progress_digest = digest_of(
                {
                    "operation_id": operation.operation_id.value,
                    "status": operation.status.value,
                    "artifact_digests": tuple(item.content_digest.value for item in new_artifacts),
                    "cursor": operation.observation.next_cursor if operation.observation else None,
                }
            )
            self._repository.record_step(
                attempt_id=attempt.attempt_id,
                ordinal=ordinal,
                action_digest=action_digest,
                operation_id=operation.operation_id,
                artifact_ids=tuple(item.artifact_id for item in new_artifacts),
                progress_digest=progress_digest,
                occurred_at=self._now(),
            )
            if operation.status is SourceOperationStatus.FAILED:
                stop = InvestigationStopReason.SOURCE_FAILED
                limitations.append(operation.failure_code or "source operation failed")
                break
            coverage_complete = _operations_cover_target(
                request.target, tuple(operations)
            )
            if operation.observation and operation.observation.has_more:
                cursor = operation.observation.next_cursor
            else:
                cursor = None
        if not coverage_complete:
            return self._repository.finish(
                attempt_id=attempt.attempt_id,
                state=UpdateAttemptState.FAILED,
                stop_reason=stop,
                target_digest=request.target.digest,
                operation_ids=tuple(operation_ids),
                artifact_ids=tuple(item.artifact_id for item in artifacts),
                coverage_complete=False,
                admission_id=None,
                admission_status=None,
                snapshot_id=None,
                limitations=tuple(limitations),
                occurred_at=self._now(),
            )
        try:
            bundle = self._builder.build(
                request=request,
                target=request.target,
                artifacts=tuple(artifacts),
                source_operations=tuple(operations),
            )
        except DomainError as exc:
            return self._repository.finish(
                attempt_id=attempt.attempt_id,
                state=UpdateAttemptState.FAILED,
                stop_reason=InvestigationStopReason.ADMISSION_REJECTED,
                target_digest=request.target.digest,
                operation_ids=tuple(operation_ids),
                artifact_ids=tuple(item.artifact_id for item in artifacts),
                coverage_complete=True,
                admission_id=None,
                admission_status=AdmissionStatus.REJECTED,
                snapshot_id=None,
                limitations=(
                    "knowledge candidate construction denied: "
                    f"{exc.code.value}: {exc.message}",
                ),
                occurred_at=self._now(),
            )
        if not (bundle.entities or bundle.facts or bundle.inferences):
            return self._repository.finish(
                attempt_id=attempt.attempt_id,
                state=UpdateAttemptState.FAILED,
                stop_reason=InvestigationStopReason.ADMISSION_REJECTED,
                target_digest=request.target.digest,
                operation_ids=tuple(operation_ids),
                artifact_ids=tuple(item.artifact_id for item in artifacts),
                coverage_complete=True,
                admission_id=None,
                admission_status=AdmissionStatus.REJECTED,
                snapshot_id=None,
                limitations=("complete source coverage produced no admissible candidate",),
                occurred_at=self._now(),
            )
        try:
            admission = self._knowledge.admit_and_publish(
                scope_id=request.scope_id,
                expected_scope_revision=request.scope_revision,
                expected_current_snapshot_id=request.expected_current_snapshot_id,
                idempotency_key=IdempotencyKey(f"{request.idempotency_key.value}:publication"),
                bundle=bundle,
                caller_ref="application-services/knowledge-update",
                classification=request.classification,
            )
        except DomainError as exc:
            if exc.code is not ErrorCode.REVISION_CONFLICT:
                raise
            return self._repository.finish(
                attempt_id=attempt.attempt_id,
                state=UpdateAttemptState.FAILED,
                stop_reason=InvestigationStopReason.PUBLICATION_CONFLICT,
                target_digest=request.target.digest,
                operation_ids=tuple(operation_ids),
                artifact_ids=tuple(item.artifact_id for item in artifacts),
                coverage_complete=True,
                admission_id=None,
                admission_status=None,
                snapshot_id=None,
                limitations=("expected CURRENT snapshot is stale",),
                occurred_at=self._now(),
            )
        success = admission.status is AdmissionStatus.ADMITTED and admission.snapshot is not None
        final_admission = admission
        inference_builder = getattr(self._builder, "build_inferences", None)
        requires_inference = bool(
            request.requirement_plan is not None
            and any(
                KnowledgeObjectKind.INFERENCE in need.required_kinds
                for need in request.requirement_plan.needs
            )
        )
        if success and requires_inference and callable(inference_builder):
            assert admission.snapshot is not None
            premises = tuple(
                self._knowledge.get_record(admission.snapshot.snapshot_id, reference)
                for reference in admission.fact_references
            )
            try:
                inference_bundle = inference_builder(
                    request=request,
                    target=request.target,
                    premises=premises,
                )
            except DomainError as exc:
                success = False
                limitations.append(
                    "reviewed inference construction denied: "
                    f"{exc.code.value}: {exc.message}"
                )
            else:
                if not inference_bundle.inferences:
                    success = False
                    limitations.append(
                        "the reviewed requirement requested an inference but no "
                        "admissible relationship inference was produced"
                    )
                else:
                    final_admission = self._knowledge.admit_and_publish(
                        scope_id=request.scope_id,
                        expected_scope_revision=request.scope_revision,
                        expected_current_snapshot_id=admission.snapshot.snapshot_id,
                        idempotency_key=IdempotencyKey(
                            f"{request.idempotency_key.value}:inference-publication"
                        ),
                        bundle=inference_bundle,
                        caller_ref="application-services/knowledge-update",
                        classification=request.classification,
                    )
                    success = (
                        final_admission.status is AdmissionStatus.ADMITTED
                        and final_admission.snapshot is not None
                    )
                    if not success:
                        limitations.extend(
                            item.message for item in final_admission.findings
                        )
        return self._repository.finish(
            attempt_id=attempt.attempt_id,
            state=UpdateAttemptState.COMPLETED if success else UpdateAttemptState.FAILED,
            stop_reason=(
                InvestigationStopReason.TARGET_COVERED
                if success
                else InvestigationStopReason.ADMISSION_REJECTED
            ),
            target_digest=request.target.digest,
            operation_ids=tuple(operation_ids),
            artifact_ids=tuple(item.artifact_id for item in artifacts),
            coverage_complete=True,
            admission_id=final_admission.admission_id,
            admission_status=final_admission.status,
            snapshot_id=(
                final_admission.snapshot.snapshot_id
                if success and final_admission.snapshot
                else None
            ),
            limitations=tuple(limitations)
            + tuple(item.message for item in admission.findings),
            occurred_at=self._now(),
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return an aware datetime")
        return value.astimezone(timezone.utc)


def _next_action(
    target: CanonicalBuildTarget, cursor: str | None
) -> tuple[SourceTool, dict[str, str]]:
    identity = dict(target.canonical_identity)
    if target.target_kind in {
        TargetKind.SOURCE_PATH,
        TargetKind.SYMBOL,
        TargetKind.JAVA_SYMBOL,
    }:
        parameters = {"revision": identity["revision"], "path": identity["path"]}
        if cursor is not None:
            parameters["offset"] = cursor
        return SourceTool.READ, parameters
    if target.target_kind is TargetKind.REVISION_COMPARISON:
        return SourceTool.COMPARE, {"base": identity["base"], "revision": identity["target"]}
    if target.target_kind is TargetKind.REPOSITORY_REVISION:
        parameters = {"revision": identity["revision"]}
        if cursor is not None:
            parameters["cursor"] = cursor
        return SourceTool.LIST, parameters
    raise DomainError(ErrorCode.INVALID_ARGUMENT, "target kind has no deterministic update strategy")


_ACTION_PARAMETERS = {
    SourceTool.LIST: frozenset({"revision", "cursor", "page_size"}),
    SourceTool.SEARCH: frozenset(
        {"revision", "query", "cursor", "page_size"}
    ),
    SourceTool.READ: frozenset({"revision", "path", "offset", "max_bytes"}),
    SourceTool.COMPARE: frozenset({"base", "revision"}),
}


def _validate_source_action(
    target: CanonicalBuildTarget, proposal: SourceActionProposal
) -> None:
    if not isinstance(proposal, SourceActionProposal):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT, "source planner returned an invalid proposal"
        )
    if proposal.stop:
        if proposal.tool is not None or proposal.parameters:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "source stop proposal cannot carry an executable action",
            )
        return
    if proposal.tool is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT, "source action proposal has no tool"
        )
    parameters = dict(proposal.parameters)
    if len(parameters) != len(proposal.parameters) or any(
        not isinstance(key, str)
        or not key
        or not isinstance(value, str)
        or not value
        for key, value in proposal.parameters
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT, "source action parameters are invalid"
        )
    if set(parameters) - _ACTION_PARAMETERS[proposal.tool]:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "source action contains parameters outside the closed tool contract",
        )
    identity = dict(target.canonical_identity)
    revision = identity.get("revision", identity.get("target"))
    authorized_revisions = {revision}
    if target.target_kind is TargetKind.REVISION_COMPARISON:
        authorized_revisions.add(identity.get("base"))
    if parameters.get("revision") not in authorized_revisions:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "source action expanded beyond the exact target revision",
        )
    if proposal.tool is SourceTool.COMPARE:
        if (
            target.target_kind is not TargetKind.REVISION_COMPARISON
            or parameters.get("base") != identity.get("base")
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "source comparison expanded beyond the exact base and target",
            )
    elif "base" in parameters:
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "non-comparison source action cannot carry a base revision",
        )
    if target.target_kind in {
        TargetKind.SOURCE_PATH,
        TargetKind.SYMBOL,
        TargetKind.JAVA_SYMBOL,
    }:
        if (
            proposal.tool is not SourceTool.READ
            or parameters.get("path") != identity.get("path")
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "exact path or symbol targets permit only reads of the resolved path",
            )
    if proposal.tool is SourceTool.SEARCH and not parameters.get("query"):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT, "source search proposal has no query"
        )
    if proposal.tool is SourceTool.READ and not parameters.get("path"):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT, "source read proposal has no path"
        )


def authorize_source_action(
    target: CanonicalBuildTarget, proposal: SourceActionProposal
) -> None:
    """Apply the shared exact-target authorization fence to a proposed read.

    Evidence-first answering and formal-knowledge construction deliberately
    share this one source boundary.  Keeping the fence public prevents either
    application flow from growing a subtly different tool policy.
    """

    _validate_source_action(target, proposal)


def _operations_cover_target(
    target: CanonicalBuildTarget,
    operations: tuple[SourceOperationResult, ...],
) -> bool:
    return any(_target_covered(target, operation) for operation in operations)


def _target_covered(target: CanonicalBuildTarget, operation: object) -> bool:
    if operation.status is not SourceOperationStatus.COMPLETED or operation.observation is None:
        return False
    identity = dict(target.canonical_identity)
    observation = operation.observation
    coverage = dict(observation.coverage)
    if target.target_kind in {
        TargetKind.SOURCE_PATH,
        TargetKind.SYMBOL,
        TargetKind.JAVA_SYMBOL,
    }:
        return (
            observation.source_context.repository_revision == identity["revision"]
            and observation.source_context.subject == identity["path"]
            and not any(item.truncated for item in observation.artifacts)
        )
    if target.target_kind is TargetKind.REVISION_COMPARISON:
        return coverage.get("base") == identity["base"] and coverage.get("target") == identity["target"]
    if target.target_kind is TargetKind.REPOSITORY_REVISION:
        return (
            observation.tool is SourceTool.READ
            and observation.source_context.repository_revision
            == identity["revision"]
            and observation.item_count > 0
            and observation.byte_count > 0
            and not observation.has_more
            and not any(item.truncated for item in observation.artifacts)
        )
    return False


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value
