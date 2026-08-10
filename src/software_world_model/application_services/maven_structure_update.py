"""Independent, source-authorized Maven Structure update orchestration.

The service in this module has no Source adapter of its own.  It obtains an
exact Git tree and every POM solely through the public Source Configuration and
Source Operation contracts, evaluates the resulting immutable artifacts, makes
an explicit report-bound Application PASS, and only then invokes the Structure
publisher.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import PurePosixPath
import re
from typing import Callable, Iterator, Mapping, Protocol, Sequence

from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.knowledge_engine import (
    KnowledgeScopeService,
    ScopeLifecycle,
    ScopePurpose,
    ScopeStateAssertion,
    ScopeType,
)
from software_world_model.knowledge_engine.structure import (
    CoverageMember,
    CoverageMemberKind,
    StructureEvidence,
)
from software_world_model.knowledge_engine.structure_publication import (
    StructureApplicationAcceptance,
    StructurePublicationReceipt,
    StructurePublicationService,
    StructureSnapshot,
)
from software_world_model.knowledge_engine.structure_authority import (
    StructureAdmissionDecision,
    StructureAdmissionFinding,
    StructureAdmissionService,
    StructureVerificationCandidate,
    StructureVerificationResult,
    StructureVerifierAssessment,
    StructureVerifierAssessmentService,
    StructureVerifierAssessmentOutcome,
    structure_batch_digest,
)
from software_world_model.source_integration import (
    ArtifactReadOperationReference,
    ArtifactReadProtectionMode,
    ArtifactUseAuthorityService,
    ArtifactUseConfirmation,
    ArtifactUsePurpose,
    AuthorizedArtifactRead,
    LocalGitConnector,
    OperationBudget,
    SourceArtifact,
    SourceConfigurationService,
    SourceOperationIntent,
    SourceOperationResult,
    SourceOperationReplayPort,
    SourceOperationService,
    SourceOperationStatus,
    SourceTool,
    TargetKind,
    resolve_local_git_binding_target,
)
from software_world_model.source_integration.operations import content_digest

from .maven_structure import (
    CANONICALIZATION_DIGEST,
    CANONICALIZATION_REF,
    EVALUATION_CONTEXT_DIGEST,
    EVALUATION_CONTEXT_REF,
    SCHEMA_DIGEST,
    SCHEMA_REF,
    GitEntryMetadata,
    MavenEvaluationInput,
    MavenStructureError,
    MavenStructureEvaluation,
    MavenStructureEvaluator,
    PomEvidenceMetadata,
)
from .knowledge_update import (
    BuildObjective,
    CanonicalBuildTarget,
    CoverageObligation,
)


_FULL_GIT_COMMIT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_GIT_MODE = re.compile(r"^[0-7]{6}$")
_FULL_GIT_OBJECT = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_TREE_ARTIFACT_KIND = "LOCAL_GIT_TREE_ENTRY_LIST@1"
_FILE_ARTIFACT_KIND = "LOCAL_GIT_FILE@1"
_PAYLOAD_SCHEMA_VERSION = "1"
_LOCAL_GIT_TARGET_RESOLVER_CONTRACT = "local-git-target-resolver@1"
_CANONICAL_SYSTEM_KEY_METADATA = "canonical_system_key"
_MAVEN_CANDIDATE_GENERATOR_REF = "MAVEN_STRUCTURE_CANDIDATE_GENERATOR@1"
_MAVEN_INDEPENDENT_VERIFIER_REF = "MAVEN_STRUCTURE_INDEPENDENT_VERIFIER@1"


@dataclass(frozen=True, slots=True)
class MavenStructureUpdateRequest:
    """Exact authority and resource closure for one manual Structure update."""

    idempotency_key: IdempotencyKey
    objective: BuildObjective
    target: CanonicalBuildTarget
    requirement_binding: None
    scope_id: StableId
    scope_revision: Revision
    source_id: StableId
    source_revision: Revision
    binding_id: StableId
    binding_revision: Revision
    repository_revision: str
    logical_reactor_root: str
    canonical_system_key: str
    expected_current_snapshot_id: StableId | None
    max_poms: int
    max_calls: int
    tree_page_size: int
    max_bytes_per_call: int
    classification: str
    actor_ref: str
    correlation_ref: CorrelationRef

    def __post_init__(self) -> None:
        if not isinstance(self.idempotency_key, IdempotencyKey):
            _invalid("IDEMPOTENCY_KEY_REQUIRED", "update idempotency key must be typed")
        _require_objective(self.objective)
        if self.requirement_binding is not None:
            _invalid(
                "MANUAL_REQUIREMENT_BINDING_FORBIDDEN",
                "a manual Maven Structure update must explicitly bind no Requirement",
            )
        for value, label in (
            (self.scope_id, "Scope ID"),
            (self.source_id, "Source ID"),
            (self.binding_id, "Binding ID"),
        ):
            if not isinstance(value, StableId):
                _invalid("STABLE_ID_REQUIRED", f"{label} must be a typed StableId")
        if self.expected_current_snapshot_id is not None and not isinstance(
            self.expected_current_snapshot_id, StableId
        ):
            _invalid(
                "STABLE_ID_REQUIRED",
                "expected CURRENT Snapshot ID must be a typed StableId",
            )
        for value, label in (
            (self.scope_revision, "Scope revision"),
            (self.source_revision, "Source definition revision"),
            (self.binding_revision, "Binding revision"),
        ):
            if not isinstance(value, Revision):
                _invalid("REVISION_REQUIRED", f"{label} must be a typed Revision")
        if not isinstance(self.correlation_ref, CorrelationRef):
            _invalid("CORRELATION_REF_REQUIRED", "correlation ref must be typed")
        if not isinstance(self.repository_revision, str) or not _FULL_GIT_COMMIT.fullmatch(
            self.repository_revision
        ):
            _invalid(
                "EXACT_GIT_COMMIT_REQUIRED",
                "repository revision must be a full lowercase Git commit object ID",
            )
        _require_canonical_revision_target(self.target, self.repository_revision)
        object.__setattr__(
            self,
            "logical_reactor_root",
            _path(self.logical_reactor_root, "logical reactor root POM"),
        )
        if PurePosixPath(self.logical_reactor_root).name != "pom.xml":
            _invalid(
                "ROOT_POM_INVALID",
                "logical reactor root must identify a repository-relative pom.xml",
            )
        object.__setattr__(
            self,
            "canonical_system_key",
            _text(self.canonical_system_key, "canonical system key"),
        )
        object.__setattr__(
            self,
            "classification",
            _text(self.classification, "classification"),
        )
        object.__setattr__(self, "actor_ref", _text(self.actor_ref, "actor ref"))
        if any(
            type(value) is not int or value < 1
            for value in (
                self.max_poms,
                self.max_calls,
                self.tree_page_size,
                self.max_bytes_per_call,
            )
        ):
            _invalid("UPDATE_BUDGET_INVALID", "all Maven Structure update budgets must be positive integers")

    @property
    def digest(self) -> Digest:
        return digest_of(
            [
                "MAVEN_STRUCTURE_UPDATE_REQUEST@1",
                {
                    "idempotency_key": self.idempotency_key.value,
                    "objective_id": self.objective.objective_id,
                    "objective_digest": self.objective.digest.value,
                    "target_id": self.target.target_id.value,
                    "target_digest": self.target.digest.value,
                    "target_resolution_receipt_id": (
                        self.target.resolution_receipt_id.value
                    ),
                    "target_resolution_receipt_digest": (
                        self.target.resolution_receipt_digest.value
                    ),
                    "requirement_binding": None,
                    "scope_id": self.scope_id.value,
                    "scope_revision": self.scope_revision.value,
                    "source_id": self.source_id.value,
                    "source_revision": self.source_revision.value,
                    "binding_id": self.binding_id.value,
                    "binding_revision": self.binding_revision.value,
                    "repository_revision": self.repository_revision,
                    "logical_reactor_root": self.logical_reactor_root,
                    "canonical_system_key": self.canonical_system_key,
                    "expected_current_snapshot_id": (
                        self.expected_current_snapshot_id.value
                        if self.expected_current_snapshot_id is not None
                        else None
                    ),
                    "max_poms": self.max_poms,
                    "max_calls": self.max_calls,
                    "tree_page_size": self.tree_page_size,
                    "max_bytes_per_call": self.max_bytes_per_call,
                    "classification": self.classification,
                    "actor_ref": self.actor_ref,
                    "correlation_ref": self.correlation_ref.value,
                },
            ]
        )


class MavenStructureUpdateState(str, Enum):
    """Application-owned lifecycle for one exact manual Maven update."""

    PREPARING = "PREPARING"
    ADMITTING = "ADMITTING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    OUTCOME_PENDING = "OUTCOME_PENDING"


@dataclass(frozen=True, slots=True)
class MavenStructureTargetAuthority:
    """First-write identity authority for one Scope/Binding/reactor root."""

    authority_id: StableId
    scope_id: StableId
    binding_id: StableId
    logical_reactor_root: str
    canonical_system_key: str
    established_scope_revision: Revision
    established_binding_revision: Revision
    established_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class MavenStructureUpdateAttempt:
    attempt_id: StableId
    request_digest: Digest
    state: MavenStructureUpdateState
    objective_id: str
    objective_digest: Digest
    target_id: StableId
    target_digest: Digest
    target_resolution_receipt_id: StableId
    target_resolution_receipt_digest: Digest
    requirement_binding_digest: Digest | None
    scope_id: StableId
    scope_revision: Revision
    source_id: StableId
    source_revision: Revision
    binding_id: StableId
    binding_revision: Revision
    repository_revision: str
    logical_reactor_root: str
    canonical_system_key: str
    expected_current_snapshot_id: StableId | None
    target_authority_id: StableId | None
    created_at: datetime
    revised_at: datetime


@dataclass(frozen=True, slots=True)
class MavenStructureUpdateAuthorityResult:
    """Durable Application Result containing only immutable refs and digests.

    Rich evaluator values remain an execution projection.  This record is the
    recovery authority and therefore never embeds Source payload or a mutable
    Knowledge object.
    """

    result_id: StableId
    attempt_id: StableId
    request_digest: Digest
    state: MavenStructureUpdateState
    objective_id: str
    objective_digest: Digest
    target_id: StableId
    target_digest: Digest
    target_resolution_receipt_id: StableId
    target_resolution_receipt_digest: Digest
    requirement_binding_digest: Digest | None
    scope_id: StableId
    scope_revision: Revision
    source_id: StableId
    source_revision: Revision
    binding_id: StableId
    binding_revision: Revision
    repository_revision: str
    logical_reactor_root: str
    canonical_system_key: str
    expected_current_snapshot_id: StableId | None
    target_authority_id: StableId | None
    target_authority_digest: Digest | None
    source_collection_digest: Digest | None
    source_operation_ids: tuple[StableId, ...]
    build_report_digest: Digest | None
    admission_id: StableId | None
    admission_digest: Digest | None
    application_acceptance_ref: str | None
    application_acceptance_digest: Digest | None
    artifact_read_package_id: StableId | None
    artifact_read_package_digest: Digest | None
    artifact_use_confirmation_id: StableId | None
    artifact_use_confirmation_digest: Digest | None
    publication_id: StableId | None
    publication_digest: Digest | None
    published_snapshot_id: StableId | None
    previous_snapshot_id: StableId | None
    previous_snapshot_manifest_digest: Digest | None
    replacement_deletions_digest: Digest | None
    failure_code: str | None
    failure_message: str | None
    failure_details: tuple[tuple[str, str | int], ...]
    completed_at: datetime
    digest: Digest


class MavenStructureUpdateRepository(Protocol):
    """Application authority port; implementations must be durable."""

    def begin(
        self,
        *,
        request: MavenStructureUpdateRequest,
        occurred_at: datetime,
    ) -> tuple[MavenStructureUpdateAttempt, MavenStructureUpdateAuthorityResult | None]: ...

    def authorize_target(
        self,
        *,
        attempt_id: StableId,
        scope_id: StableId,
        scope_revision: Revision,
        binding_id: StableId,
        binding_revision: Revision,
        logical_reactor_root: str,
        canonical_system_key: str,
        occurred_at: datetime,
    ) -> MavenStructureTargetAuthority: ...

    def mark_admitting(
        self,
        *,
        attempt_id: StableId,
        source_collection_digest: Digest,
        source_operation_ids: tuple[StableId, ...],
        build_report_digest: Digest,
        application_acceptance_ref: str,
        application_acceptance_digest: Digest,
        occurred_at: datetime,
    ) -> MavenStructureUpdateAttempt: ...

    def mark_admitted(
        self,
        *,
        attempt_id: StableId,
        admission_id: StableId,
        admission_digest: Digest,
        occurred_at: datetime,
    ) -> MavenStructureUpdateAttempt: ...

    def mark_artifact_use_confirmed(
        self,
        *,
        attempt_id: StableId,
        confirmation: ArtifactUseConfirmation,
        occurred_at: datetime,
    ) -> MavenStructureUpdateAttempt: ...

    def finish_published(
        self,
        *,
        attempt_id: StableId,
        publication_receipt: StructurePublicationReceipt,
        occurred_at: datetime,
    ) -> MavenStructureUpdateAuthorityResult: ...

    def finish_failed(
        self,
        *,
        attempt_id: StableId,
        error_code: str,
        error_message: str,
        error_details: Mapping[str, str | int],
        outcome_pending: bool,
        occurred_at: datetime,
    ) -> MavenStructureUpdateAuthorityResult: ...

    def get_attempt(self, attempt_id: StableId) -> MavenStructureUpdateAttempt: ...

    def get_target_authority(
        self,
        *,
        scope_id: StableId,
        binding_id: StableId,
        logical_reactor_root: str,
    ) -> MavenStructureTargetAuthority | None: ...

    def get_result(
        self, *, idempotency_key: IdempotencyKey
    ) -> MavenStructureUpdateAuthorityResult | None: ...


@dataclass(frozen=True, slots=True)
class MavenStructureUpdatePreparation:
    attempt: MavenStructureUpdateAttempt
    target_authority: MavenStructureTargetAuthority | None
    terminal_result: MavenStructureUpdateAuthorityResult | None


class MavenStructureUpdateAuthorityService:
    """Seal manual objective/target/system identity before Source collection."""

    def __init__(
        self,
        repository: MavenStructureUpdateRepository,
        scopes: KnowledgeScopeService,
        configurations: SourceConfigurationService,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._scopes = scopes
        self._configurations = configurations
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def prepare(
        self,
        request: MavenStructureUpdateRequest,
    ) -> MavenStructureUpdatePreparation:
        now = self._now()
        attempt, terminal_result = self._repository.begin(
            request=request,
            occurred_at=now,
        )
        if terminal_result is not None:
            target_authority = None
            if attempt.target_authority_id is not None:
                target_authority = self._repository.get_target_authority(
                    scope_id=attempt.scope_id,
                    binding_id=attempt.binding_id,
                    logical_reactor_root=attempt.logical_reactor_root,
                )
                if (
                    target_authority is None
                    or target_authority.authority_id
                    != attempt.target_authority_id
                ):
                    raise DomainError(
                        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                        "Maven update target authority link cannot be recovered",
                        {"attempt_id": attempt.attempt_id.value},
                    )
            return MavenStructureUpdatePreparation(
                attempt=attempt,
                target_authority=target_authority,
                terminal_result=terminal_result,
            )
        try:
            scope = self._scopes.get_scope(request.scope_id)
            if scope.definition_revision != request.scope_revision:
                raise DomainError(
                    ErrorCode.REVISION_CONFLICT,
                    "Maven target authority Scope revision is stale",
                )
            if scope.lifecycle is not ScopeLifecycle.ACTIVE:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "Maven target authority Scope is not active",
                )
            metadata = dict(scope.metadata)
            authoritative_system_key = metadata.get(
                _CANONICAL_SYSTEM_KEY_METADATA
            )
            if scope.scope_type is not ScopeType.SYSTEM:
                _invalid(
                    "MAVEN_SCOPE_TYPE_INVALID",
                    "Maven Structure updates require a SYSTEM Knowledge Scope",
                )
            if authoritative_system_key is None:
                _invalid(
                    "CANONICAL_SYSTEM_KEY_METADATA_REQUIRED",
                    "SYSTEM Scope metadata must fix canonical_system_key",
                )
            if authoritative_system_key != request.canonical_system_key:
                _invalid(
                    "CANONICAL_SYSTEM_KEY_METADATA_MISMATCH",
                    "request canonical_system_key differs from SYSTEM Scope metadata",
                )

            source, binding = self._configurations.require_current_active_binding(
                source_id=request.source_id,
                expected_source_revision=request.source_revision,
                binding_id=request.binding_id,
                expected_binding_revision=request.binding_revision,
            )
            if (
                binding.scope_id != request.scope_id
                or binding.source_id != request.source_id
                or binding.observed_scope_revision != request.scope_revision
            ):
                _invalid(
                    "SOURCE_BINDING_MISMATCH",
                    "Maven target authority requires the exact Scope/Source Binding closure",
                )
            receipt = resolve_local_git_binding_target(
                connector=LocalGitConnector(source.canonical_source_target),
                selector=binding.selector,
                target_kind=TargetKind.REPOSITORY_REVISION,
                parameters={"revision": request.repository_revision},
            )
            try:
                authoritative_target = CanonicalBuildTarget.from_receipt(receipt)
            except DomainError as exc:
                raise DomainError(
                    ErrorCode.SOURCE_TARGET_NOT_FOUND,
                    "exact Maven repository revision is no longer resolvable",
                    {
                        "reason_code": "MAVEN_TARGET_RESOLUTION_NOT_EXACT",
                        "repository_revision": request.repository_revision,
                    },
                ) from exc
            if authoritative_target != request.target:
                _invalid(
                    "CANONICAL_BUILD_TARGET_RECEIPT_MISMATCH",
                    "request Canonical Build Target differs from the public Local Git resolver receipt",
                )

            target_authority = self._repository.authorize_target(
                attempt_id=attempt.attempt_id,
                scope_id=request.scope_id,
                scope_revision=request.scope_revision,
                binding_id=request.binding_id,
                binding_revision=request.binding_revision,
                logical_reactor_root=request.logical_reactor_root,
                canonical_system_key=request.canonical_system_key,
                occurred_at=self._now(),
            )
            return MavenStructureUpdatePreparation(
                attempt=self._repository.get_attempt(attempt.attempt_id),
                target_authority=target_authority,
                terminal_result=None,
            )
        except DomainError as exc:
            self._repository.finish_failed(
                attempt_id=attempt.attempt_id,
                error_code=exc.code.value,
                error_message=exc.message,
                error_details=exc.details,
                outcome_pending=False,
                occurred_at=self._now(),
            )
            raise
        except Exception as exc:
            self._repository.finish_failed(
                attempt_id=attempt.attempt_id,
                error_code="OUTCOME_PENDING",
                error_message=str(exc) or type(exc).__name__,
                error_details={"stage": "TARGET_AUTHORITY"},
                outcome_pending=True,
                occurred_at=self._now(),
            )
            raise

    def get_result(
        self,
        *,
        idempotency_key: IdempotencyKey,
    ) -> MavenStructureUpdateAuthorityResult | None:
        return self._repository.get_result(idempotency_key=idempotency_key)

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            _invalid(
                "UPDATE_TIMEZONE_REQUIRED",
                "Maven Structure update clock must return a timezone-aware time",
            )
        return value.astimezone(timezone.utc)


@dataclass(frozen=True, slots=True)
class MavenStructureSourceCollection:
    repository_revision: str
    tree_entries: tuple[tuple[str, GitEntryMetadata], ...]
    pom_artifacts: tuple[tuple[str, SourceArtifact], ...]
    tree_evidence: tuple[StructureEvidence, ...]
    operation_references: tuple[ArtifactReadOperationReference, ...]
    operation_ids: tuple[StableId, ...]
    operation_digests: tuple[Digest, ...]
    digest: Digest

    @property
    def git_entries(self) -> dict[str, GitEntryMetadata]:
        return dict(self.tree_entries)

    @property
    def pom_bytes(self) -> dict[str, bytes]:
        return {path: artifact.payload for path, artifact in self.pom_artifacts}

    @property
    def pom_evidence(self) -> dict[str, PomEvidenceMetadata]:
        return {
            path: PomEvidenceMetadata(
                artifact_id=artifact.artifact_id,
                source_context_id=artifact.source_context_id,
                artifact_content_digest=artifact.content_digest,
                locator=artifact.source_native_identity,
            )
            for path, artifact in self.pom_artifacts
        }

    @property
    def pom_paths(self) -> tuple[str, ...]:
        return tuple(path for path, _ in self.pom_artifacts)


@dataclass(frozen=True, slots=True)
class MavenStructureUpdateResult:
    authority_result: MavenStructureUpdateAuthorityResult
    request_digest: Digest
    source_collection_digest: Digest
    source_operation_ids: tuple[StableId, ...]
    build_report_digest: Digest
    verifier_assessment: StructureVerifierAssessment
    application_acceptance: StructureApplicationAcceptance
    artifact_use_confirmation: ArtifactUseConfirmation
    publication_receipt: StructurePublicationReceipt
    previous_snapshot: StructureSnapshot | None
    deletions: "StructureReplacementDeletions"
    evaluation: MavenStructureEvaluation
    digest: Digest


@dataclass(frozen=True, slots=True)
class StructureReplacementDeletions:
    """Previous States absent from the replacement Snapshot, by reason."""

    removed_members: tuple[CoverageMember, ...]
    replaced_members: tuple[CoverageMember, ...]
    digest: Digest

    @classmethod
    def between(
        cls,
        previous_members: Sequence[CoverageMember],
        current_members: Sequence[CoverageMember],
    ) -> "StructureReplacementDeletions":
        current_by_root = {item.root_id: item for item in current_members}
        removed: list[CoverageMember] = []
        replaced: list[CoverageMember] = []
        for item in previous_members:
            current = current_by_root.get(item.root_id)
            if current is None:
                removed.append(item)
            elif current.state_id != item.state_id:
                replaced.append(item)
        key = lambda item: (item.kind.value, item.root_id.value, item.state_id.value)
        normalized_removed = tuple(sorted(removed, key=key))
        normalized_replaced = tuple(sorted(replaced, key=key))
        core = {
            "removed_members": normalized_removed,
            "replaced_members": normalized_replaced,
        }
        return cls(
            removed_members=normalized_removed,
            replaced_members=normalized_replaced,
            digest=digest_of(["STRUCTURE_REPLACEMENT_DELETIONS@1", core]),
        )

    @property
    def deleted_entity_state_ids(self) -> tuple[StableId, ...]:
        return self._state_ids(CoverageMemberKind.ENTITY)

    @property
    def deleted_members(self) -> tuple[CoverageMember, ...]:
        """Every previous State absent from the replacement Snapshot."""

        return tuple(
            sorted(
                (*self.removed_members, *self.replaced_members),
                key=lambda item: (
                    item.kind.value,
                    item.root_id.value,
                    item.state_id.value,
                ),
            )
        )

    @property
    def deleted_relation_state_ids(self) -> tuple[StableId, ...]:
        return self._state_ids(CoverageMemberKind.RELATION_FACT)

    @property
    def deleted_literal_state_ids(self) -> tuple[StableId, ...]:
        return self._state_ids(CoverageMemberKind.LITERAL_FACT)

    def _state_ids(self, kind: CoverageMemberKind) -> tuple[StableId, ...]:
        return tuple(
            item.state_id
            for item in (*self.removed_members, *self.replaced_members)
            if item.kind is kind
        )


class MavenEvaluator(Protocol):
    def evaluate(self, evaluation_input: MavenEvaluationInput) -> MavenStructureEvaluation: ...


class MavenStructureSourceCollector:
    """Collect one exact-revision evaluator input through Source operations."""

    def __init__(
        self,
        scopes: KnowledgeScopeService,
        configurations: SourceConfigurationService,
        operations: SourceOperationService | None = None,
        replay: SourceOperationReplayPort | None = None,
    ) -> None:
        if (operations is None) == (replay is None):
            _invalid(
                "SOURCE_COLLECTION_CAPABILITY_INVALID",
                "collector requires exactly one execute or persisted replay capability",
            )
        self._scopes = scopes
        self._configurations = configurations
        self._operations = operations
        self._replay = replay

    def collect(
        self,
        request: MavenStructureUpdateRequest,
        *,
        expected_operation_ids: tuple[StableId, ...] = (),
    ) -> MavenStructureSourceCollection:
        if self._replay is None and expected_operation_ids:
            _invalid(
                "SOURCE_REPLAY_IDS_UNEXPECTED",
                "execute-capable collection cannot accept replay Operation IDs",
            )
        if self._replay is not None and not expected_operation_ids:
            _invalid(
                "SOURCE_REPLAY_IDS_REQUIRED",
                "persisted replay requires the exact expected Operation IDs",
            )
        replay_ids = iter(expected_operation_ids)
        calls = 0
        operation_ids: list[StableId] = []
        operation_digests: list[Digest] = []
        operation_references: list[ArtifactReadOperationReference] = []
        entries: dict[str, GitEntryMetadata] = {}
        tree_evidence: list[StructureEvidence] = []
        cursor = "0"
        matched_total: int | None = None

        while True:
            calls = self._require_call_budget(request, calls)
            parameters = {
                "revision": request.repository_revision,
                "cursor": cursor,
                "page_size": str(request.tree_page_size),
            }
            operation = self._execute_source_action(
                request=request,
                tool=SourceTool.TREE,
                parameters=parameters,
                budget=OperationBudget(
                    max_calls=1,
                    max_items=request.tree_page_size,
                    max_bytes=request.max_bytes_per_call,
                ),
                expected_operation_id=self._next_replay_id(replay_ids),
            )
            operation_ids.append(operation.operation_id)
            operation_digests.append(operation.digest)
            operation_references.append(
                ArtifactReadOperationReference.from_result(operation)
            )
            page_entries, page_evidence, next_cursor, page_total = self._tree_page(
                request=request,
                operation=operation,
                expected_cursor=cursor,
            )
            if matched_total is None:
                matched_total = page_total
            elif matched_total != page_total:
                _source_invalid(
                    "TREE_TOTAL_DRIFT",
                    "paginated Git tree observations disagree on matched_total",
                )
            for path, metadata in page_entries:
                if path in entries:
                    _source_invalid(
                        "TREE_ENTRY_DUPLICATE",
                        "paginated Git tree contains a duplicate canonical path",
                        path=path,
                    )
                entries[path] = metadata
            if page_evidence is not None:
                tree_evidence.append(page_evidence)
            if next_cursor is None:
                break
            cursor = next_cursor

        if matched_total is None or matched_total != len(entries):
            _source_invalid(
                "TREE_COVERAGE_INCOMPLETE",
                "Git tree pagination did not produce the declared complete entry count",
            )
        pom_paths = tuple(
            sorted(
                path
                for path in entries
                if path == "pom.xml" or path.endswith("/pom.xml")
            )
        )
        if request.logical_reactor_root not in pom_paths:
            _source_invalid(
                "ROOT_POM_MISSING",
                "exact Git tree does not contain the requested logical reactor root",
                path=request.logical_reactor_root,
            )
        if len(pom_paths) > request.max_poms:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "exact Git tree contains more POMs than the update budget permits",
                {
                    "reason_code": "MAX_POMS_EXCEEDED",
                    "max_poms": request.max_poms,
                    "observed_poms": len(pom_paths),
                },
            )

        pom_artifacts: list[tuple[str, SourceArtifact]] = []
        for path in pom_paths:
            calls = self._require_call_budget(request, calls)
            parameters = {
                "revision": request.repository_revision,
                "path": path,
                "offset": "0",
                "max_bytes": str(request.max_bytes_per_call),
            }
            operation = self._execute_source_action(
                request=request,
                tool=SourceTool.READ,
                parameters=parameters,
                budget=OperationBudget(
                    max_calls=1,
                    max_items=1,
                    max_bytes=request.max_bytes_per_call,
                ),
                expected_operation_id=self._next_replay_id(replay_ids),
            )
            operation_ids.append(operation.operation_id)
            operation_digests.append(operation.digest)
            operation_references.append(
                ArtifactReadOperationReference.from_result(operation)
            )
            pom_artifacts.append(
                (path, self._complete_pom_artifact(request, operation, path))
            )

        tree_entries = tuple(sorted(entries.items(), key=lambda item: item[0]))
        poms = tuple(pom_artifacts)
        evidence = tuple(tree_evidence)
        if self._replay is not None:
            try:
                next(replay_ids)
            except StopIteration:
                pass
            else:
                _source_invalid(
                    "SOURCE_REPLAY_OPERATION_COUNT_MISMATCH",
                    "persisted replay has unused expected Source Operation IDs",
                )
        collection_digest = digest_of(
            [
                "MAVEN_STRUCTURE_SOURCE_COLLECTION@1",
                {
                    "repository_revision": request.repository_revision,
                    "tree_entries": tree_entries,
                    "pom_artifacts": tuple(
                        (
                            path,
                            artifact.artifact_id.value,
                            artifact.content_digest.value,
                            artifact.source_context_id.value,
                        )
                        for path, artifact in poms
                    ),
                    "tree_evidence": tuple(
                        (item.evidence_id.value, item.digest.value) for item in evidence
                    ),
                    "operation_ids": tuple(item.value for item in operation_ids),
                    "operation_digests": tuple(
                        item.value for item in operation_digests
                    ),
                    "operation_references": tuple(operation_references),
                },
            ]
        )
        return MavenStructureSourceCollection(
            repository_revision=request.repository_revision,
            tree_entries=tree_entries,
            pom_artifacts=poms,
            tree_evidence=evidence,
            operation_references=tuple(operation_references),
            operation_ids=tuple(operation_ids),
            operation_digests=tuple(operation_digests),
            digest=collection_digest,
        )

    def _next_replay_id(
        self, replay_ids: Iterator[StableId]
    ) -> StableId | None:
        if self._replay is None:
            return None
        try:
            return next(replay_ids)
        except StopIteration:
            _source_invalid(
                "SOURCE_REPLAY_OPERATION_COUNT_MISMATCH",
                "persisted replay exhausted expected Source Operation IDs",
            )

    @staticmethod
    def _require_call_budget(request: MavenStructureUpdateRequest, calls: int) -> int:
        if calls >= request.max_calls:
            raise DomainError(
                ErrorCode.BUDGET_EXHAUSTED,
                "Maven Structure update exhausted its Source call budget",
                {"reason_code": "MAX_CALLS_EXCEEDED", "max_calls": request.max_calls},
            )
        return calls + 1

    def _execute_source_action(
        self,
        *,
        request: MavenStructureUpdateRequest,
        tool: SourceTool,
        parameters: Mapping[str, str],
        budget: OperationBudget,
        expected_operation_id: StableId | None,
    ) -> SourceOperationResult:
        action_digest = digest_of(
            [
                "MAVEN_STRUCTURE_SOURCE_ACTION@1",
                {
                    "scope_id": request.scope_id.value,
                    "scope_revision": request.scope_revision.value,
                    "source_id": request.source_id.value,
                    "source_revision": request.source_revision.value,
                    "binding_id": request.binding_id.value,
                    "binding_revision": request.binding_revision.value,
                    "repository_revision": request.repository_revision,
                    "tool": tool.value,
                    "parameters": tuple(sorted(parameters.items())),
                    "budget": budget,
                    "classification": request.classification,
                    "actor_ref": request.actor_ref,
                },
            ]
        )
        action_ref = f"maven-structure-source:{action_digest.value}"
        scope_assertion = self._scopes.read_scope_state_assertion(
            scope_id=request.scope_id,
            expected_revision=request.scope_revision,
            purpose=ScopePurpose.SOURCE_EXECUTION,
            caller_ref=request.actor_ref,
            request_ref=action_ref,
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
        if eligibility.source_id != request.source_id:
            _source_invalid(
                "SOURCE_BINDING_MISMATCH",
                "exact Binding resolves to a different Source than the update request",
            )
        intent = SourceOperationIntent.create(
            idempotency_key=IdempotencyKey(
                f"maven-structure-source-{action_digest.value.removeprefix('sha256:')}"
            ),
            causation_reference=action_ref,
            source_id=request.source_id,
            source_revision=request.source_revision,
            binding_id=request.binding_id,
            binding_revision=request.binding_revision,
            scope_assertion=scope_assertion,
            binding_eligibility=eligibility,
            tool=tool,
            parameters=parameters,
            budget=budget,
            classification=request.classification,
            correlation_ref=request.correlation_ref,
        )
        if self._operations is not None:
            if expected_operation_id is not None:
                _source_invalid(
                    "SOURCE_REPLAY_ID_ON_EXECUTE_PATH",
                    "execute-capable Source collection cannot consume replay IDs",
                )
            operation = self._operations.execute(intent)
        else:
            if self._replay is None or expected_operation_id is None:
                _source_invalid(
                    "SOURCE_REPLAY_CAPABILITY_MISSING",
                    "persisted Source replay capability or Operation ID is missing",
                )
            operation = self._replay.replay(
                operation_id=expected_operation_id,
                expected_intent_digest=intent.digest,
            )
        _require_persisted_source_operation(intent, operation)
        return operation

    @staticmethod
    def _tree_page(
        *,
        request: MavenStructureUpdateRequest,
        operation: SourceOperationResult,
        expected_cursor: str,
    ) -> tuple[
        tuple[tuple[str, GitEntryMetadata], ...],
        StructureEvidence | None,
        str | None,
        int,
    ]:
        observation = operation.observation
        if operation.status not in (
            SourceOperationStatus.PARTIAL,
            SourceOperationStatus.COMPLETED,
        ) or observation is None:
            _operation_failed(operation, "TREE_OPERATION_NOT_USABLE")
        if observation.tool is not SourceTool.TREE:
            _source_invalid("TREE_TOOL_MISMATCH", "Source result is not a TREE observation")
        if observation.source_context.repository_revision != request.repository_revision:
            _source_invalid("TREE_REVISION_MISMATCH", "TREE observation is not bound to the exact Git commit")
        if len(observation.artifacts) != 1:
            _source_invalid("TREE_ARTIFACT_COUNT_INVALID", "TREE observation must contain exactly one Artifact")
        artifact = observation.artifacts[0]
        _require_artifact_authority(request, artifact, _TREE_ARTIFACT_KIND)
        if artifact.content_digest != content_digest(artifact.payload):
            _source_invalid("ARTIFACT_DIGEST_MISMATCH", "TREE Artifact bytes do not match its content digest")
        parsed = parse_local_git_tree_jsonl(artifact.payload)
        if observation.item_count != len(parsed):
            _source_invalid("TREE_ITEM_COUNT_MISMATCH", "TREE item_count does not match canonical JSONL records")
        coverage = dict(observation.coverage)
        if coverage.get("revision") != request.repository_revision:
            _source_invalid("TREE_COVERAGE_REVISION_MISMATCH", "TREE Coverage is not bound to the exact Git commit")
        if coverage.get("cursor_start") != expected_cursor:
            _source_invalid("TREE_CURSOR_DISCONTINUITY", "TREE page does not start at the requested cursor")
        cursor_end = _nonnegative_int(coverage.get("cursor_end"), "TREE cursor_end")
        matched_total = _nonnegative_int(coverage.get("matched_total"), "TREE matched_total")
        if cursor_end != int(expected_cursor) + len(parsed):
            _source_invalid("TREE_CURSOR_COUNT_MISMATCH", "TREE cursor coverage does not match its records")
        if observation.has_more:
            if operation.status is not SourceOperationStatus.PARTIAL:
                _source_invalid("TREE_STATUS_INVALID", "non-terminal TREE page must be PARTIAL")
            if observation.next_cursor != str(cursor_end) or cursor_end <= int(expected_cursor):
                _source_invalid("TREE_CURSOR_NO_PROGRESS", "TREE pagination must advance exactly to next_cursor")
            next_cursor = observation.next_cursor
        else:
            if operation.status is not SourceOperationStatus.COMPLETED:
                _source_invalid("TREE_STATUS_INVALID", "terminal TREE page must be COMPLETED")
            if observation.next_cursor is not None or artifact.truncated:
                _source_invalid("TREE_TERMINAL_INCOMPLETE", "terminal TREE Artifact must be complete")
            if cursor_end != matched_total:
                _source_invalid("TREE_COVERAGE_INCOMPLETE", "terminal TREE cursor does not reach matched_total")
            next_cursor = None
        evidence = None
        if artifact.payload:
            try:
                excerpt = artifact.payload.decode("utf-8")
            except UnicodeDecodeError as exc:  # parse helper normally catches this first
                raise DomainError(
                    ErrorCode.SOURCE_OPERATION_FAILED,
                    "TREE Artifact is not UTF-8",
                    {"reason_code": "TREE_UTF8_INVALID"},
                ) from exc
            evidence = StructureEvidence.create(
                artifact_id=artifact.artifact_id,
                source_context_id=artifact.source_context_id,
                byte_start=0,
                byte_end=len(artifact.payload),
                locator=(
                    f"git-tree:{request.repository_revision}:"
                    f"cursor:{expected_cursor}-{cursor_end}"
                ),
                excerpt=excerpt,
                artifact_content_digest=artifact.content_digest,
            )
        return parsed, evidence, next_cursor, matched_total

    @staticmethod
    def _complete_pom_artifact(
        request: MavenStructureUpdateRequest,
        operation: SourceOperationResult,
        path: str,
    ) -> SourceArtifact:
        observation = operation.observation
        if observation is not None and any(
            artifact.truncated or artifact.truncation_offset is not None
            for artifact in observation.artifacts
        ):
            _source_invalid(
                "POM_READ_TRUNCATED",
                "POM READ Artifact must be complete and non-truncated",
                path=path,
            )
        if operation.status is not SourceOperationStatus.COMPLETED or observation is None:
            _operation_failed(operation, "POM_READ_NOT_COMPLETED")
        if observation.tool is not SourceTool.READ:
            _source_invalid("READ_TOOL_MISMATCH", "Source result is not a READ observation")
        if observation.source_context.repository_revision != request.repository_revision:
            _source_invalid("READ_REVISION_MISMATCH", "POM READ is not bound to the exact Git commit", path=path)
        if observation.has_more or observation.next_cursor is not None:
            _source_invalid("POM_READ_INCOMPLETE", "POM READ cannot require pagination", path=path)
        if len(observation.artifacts) != 1:
            _source_invalid("READ_ARTIFACT_COUNT_INVALID", "POM READ must contain exactly one Artifact", path=path)
        artifact = observation.artifacts[0]
        _require_artifact_authority(request, artifact, _FILE_ARTIFACT_KIND)
        if artifact.source_native_identity != path:
            _source_invalid("READ_PATH_MISMATCH", "POM Artifact path differs from the requested path", path=path)
        if artifact.truncated or artifact.truncation_offset is not None:
            _source_invalid("POM_READ_TRUNCATED", "POM READ Artifact must be complete and non-truncated", path=path)
        if artifact.content_digest != content_digest(artifact.payload):
            _source_invalid("ARTIFACT_DIGEST_MISMATCH", "POM Artifact bytes do not match its content digest", path=path)
        try:
            artifact.payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DomainError(
                ErrorCode.SOURCE_OPERATION_FAILED,
                "POM Artifact must be exact UTF-8",
                {"reason_code": "POM_UTF8_INVALID", "path": path},
            ) from exc
        return artifact


@dataclass(frozen=True, slots=True)
class MavenStructureVerificationContext:
    """Application-supplied coordinates; the verifier rebuilds all outcomes."""

    request: MavenStructureUpdateRequest
    expected_operation_ids: tuple[StableId, ...]
    package_id: StableId
    package_digest: Digest
    closure_id: StableId
    closure_digest: Digest
    protection_id: StableId
    protection_digest: Digest
    purpose: ArtifactUsePurpose
    downstream_request_ref: str
    downstream_request_digest: Digest

    @property
    def digest(self) -> Digest:
        return digest_of(
            [
                "MAVEN_STRUCTURE_VERIFICATION_COORDINATES@1",
                {
                    "request_digest": self.request.digest.value,
                    "expected_operation_ids": tuple(
                        item.value for item in self.expected_operation_ids
                    ),
                    "package_id": self.package_id.value,
                    "package_digest": self.package_digest.value,
                    "closure_id": self.closure_id.value,
                    "closure_digest": self.closure_digest.value,
                    "protection_id": self.protection_id.value,
                    "protection_digest": self.protection_digest.value,
                    "purpose": self.purpose.value,
                    "downstream_request_ref": self.downstream_request_ref,
                    "downstream_request_digest": (
                        self.downstream_request_digest.value
                    ),
                },
            ]
        )


class MavenStructureIndependentVerifier:
    """Fixed Maven verifier with replay-only Source access.

    The Application can bind request coordinates and completed Operation IDs,
    but it cannot submit any verified digest, report, or Structure batch.  This
    port independently replays and evaluates those coordinates when the
    verifier-owned assessment service invokes :meth:`verify`.
    """

    verifier_ref = _MAVEN_INDEPENDENT_VERIFIER_REF

    def __init__(
        self,
        scopes: KnowledgeScopeService,
        configurations: SourceConfigurationService,
        artifact_use: ArtifactUseAuthorityService,
    ) -> None:
        self._scopes = scopes
        self._configurations = configurations
        self._artifact_use = artifact_use
        self._contexts: dict[str, MavenStructureVerificationContext] = {}

    def bind_candidate(
        self,
        *,
        candidate_ref: str,
        request: MavenStructureUpdateRequest,
        expected_operation_ids: tuple[StableId, ...],
        authorized_read: AuthorizedArtifactRead,
    ) -> None:
        if not isinstance(candidate_ref, str) or not candidate_ref.strip():
            _invalid(
                "VERIFICATION_CANDIDATE_REF_REQUIRED",
                "Maven verifier candidate ref must be non-empty",
            )
        context = MavenStructureVerificationContext(
            request=request,
            expected_operation_ids=expected_operation_ids,
            package_id=authorized_read.package.package_id,
            package_digest=authorized_read.package.digest,
            closure_id=authorized_read.closure.closure_id,
            closure_digest=authorized_read.closure.digest,
            protection_id=authorized_read.protection.protection_id,
            protection_digest=authorized_read.protection.digest,
            purpose=authorized_read.package.purpose,
            downstream_request_ref=authorized_read.package.downstream_request_ref,
            downstream_request_digest=(
                authorized_read.package.downstream_request_digest
            ),
        )
        if not context.expected_operation_ids:
            _invalid(
                "SOURCE_REPLAY_IDS_REQUIRED",
                "Maven verifier requires exact persisted Source Operation IDs",
            )
        existing = self._contexts.get(candidate_ref)
        if existing is not None and existing != context:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Maven verifier candidate coordinates cannot drift",
                {"reason_code": "VERIFICATION_COORDINATES_DRIFT"},
            )
        self._contexts[candidate_ref] = context

    def verify(
        self,
        candidate: StructureVerificationCandidate,
    ) -> StructureVerificationResult:
        try:
            context = self._contexts[candidate.candidate_ref]
        except KeyError as exc:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Maven verifier has no bound replay coordinates for candidate",
                {"reason_code": "VERIFICATION_COORDINATES_MISSING"},
            ) from exc
        authorized_read = self._artifact_use.reopen_authorized_read(
            package_id=context.package_id,
            expected_package_digest=context.package_digest,
            closure_id=context.closure_id,
            expected_closure_digest=context.closure_digest,
            protection_id=context.protection_id,
            expected_protection_digest=context.protection_digest,
            purpose=context.purpose,
            downstream_request_ref=context.downstream_request_ref,
            downstream_request_digest=context.downstream_request_digest,
            scope_assertion=self._scopes.read_scope_state_assertion(
                scope_id=context.request.scope_id,
                expected_revision=context.request.scope_revision,
                purpose=ScopePurpose.SOURCE_EXECUTION,
                caller_ref=self.verifier_ref,
                request_ref=f"{candidate.candidate_ref}:artifact-replay",
                classification=context.request.classification,
            ),
        )
        collection = MavenStructureSourceCollector(
            self._scopes,
            self._configurations,
            replay=authorized_read,
        ).collect(
            context.request,
            expected_operation_ids=context.expected_operation_ids,
        )
        knowledge_context_digest = _maven_knowledge_context_digest(
            context.request
        )
        evaluation = MavenStructureEvaluator().evaluate(
            _maven_evaluation_input(
                context.request,
                collection,
                knowledge_context_digest,
            )
        )
        MavenStructureUpdateService._require_complete_evaluation(
            context.request,
            evaluation,
        )
        report_digest = digest_of(
            ["MAVEN_STRUCTURE_BUILD_REPORT@1", evaluation.report]
        )
        evaluation_digest = maven_structure_evaluation_digest(evaluation)
        candidate_digest = maven_structure_candidate_digest(
            request=context.request,
            collection=collection,
            evaluation=evaluation,
            evaluation_digest=evaluation_digest,
            report_digest=report_digest,
        )
        expected_context_digest = _maven_verification_context_digest(
            request=context.request,
            collection=collection,
            authorized_read=authorized_read,
        )
        findings: tuple[StructureAdmissionFinding, ...] = ()
        if candidate.verification_context_digest != expected_context_digest:
            findings = (
                StructureAdmissionFinding(
                    code="VERIFICATION_CONTEXT_MISMATCH",
                    message=(
                        "candidate verification context differs from the "
                        "independently replayed Source closure"
                    ),
                ),
            )
        return StructureVerificationResult(
            verified_candidate_digest=candidate_digest,
            verified_evaluation_digest=evaluation_digest,
            verified_report_digest=report_digest,
            verified_batch=evaluation.batch,
            findings=findings,
        )


class MavenStructureUpdateService:
    def __init__(
        self,
        repository: MavenStructureUpdateRepository,
        scopes: KnowledgeScopeService,
        configurations: SourceConfigurationService,
        operations: SourceOperationService,
        artifact_use: ArtifactUseAuthorityService,
        admission: StructureAdmissionService,
        verifier_assessments: StructureVerifierAssessmentService,
        verifier: MavenStructureIndependentVerifier,
        publication: StructurePublicationService,
        *,
        evaluator: MavenEvaluator | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._scopes = scopes
        self._configurations = configurations
        self._authority = MavenStructureUpdateAuthorityService(
            repository,
            scopes,
            configurations,
            clock=clock,
        )
        self._collector = MavenStructureSourceCollector(
            scopes, configurations, operations=operations
        )
        self._evaluator = evaluator or MavenStructureEvaluator()
        self._artifact_use = artifact_use
        self._admission = admission
        self._verifier_assessments = verifier_assessments
        self._verifier = verifier
        if (
            admission.verifier_ref != _MAVEN_INDEPENDENT_VERIFIER_REF
            or verifier_assessments.verifier_ref
            != _MAVEN_INDEPENDENT_VERIFIER_REF
            or verifier.verifier_ref != _MAVEN_INDEPENDENT_VERIFIER_REF
        ):
            _invalid(
                "MAVEN_VERIFIER_AUTHORITY_MISMATCH",
                "Maven Admission and Assessment require the fixed verifier authority",
            )
        self._publication = publication
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def execute(self, request: MavenStructureUpdateRequest) -> MavenStructureUpdateResult:
        preparation = self._authority.prepare(request)
        terminal = preparation.terminal_result
        if terminal is not None:
            if terminal.state is MavenStructureUpdateState.OUTCOME_PENDING:
                return self._recover_outcome_pending(request, preparation)
            if terminal.state is not MavenStructureUpdateState.PUBLISHED:
                self._raise_terminal(terminal)
        stage = "SOURCE_COLLECTION"
        publication_key: IdempotencyKey | None = None
        try:
            collected = self._collector.collect(request)
            stage = "ARTIFACT_READ_AUTHORITY"
            authorized_read = self._artifact_use.open_read_package(
                idempotency_key=_child_idempotency_key(
                    request,
                    "artifact-read-package",
                    collected.digest,
                ),
                operation_references=collected.operation_references,
                purpose=ArtifactUsePurpose.MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE,
                downstream_request_ref=preparation.attempt.attempt_id.value,
                downstream_request_digest=request.digest,
                protection_mode=ArtifactReadProtectionMode.NO_EVICTION,
                scope_assertion=self._artifact_scope_assertion(
                    request,
                    request_ref=(
                        f"{preparation.attempt.attempt_id.value}:artifact-open"
                    ),
                ),
            )
            collection = MavenStructureSourceCollector(
                self._scopes,
                self._configurations,
                replay=authorized_read,
            ).collect(
                request,
                expected_operation_ids=collected.operation_ids,
            )
            if collection != collected:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "authorized Artifact Read differs from collected Source closure",
                    {"reason_code": "ARTIFACT_READ_COLLECTION_DRIFT"},
                )
            knowledge_context_digest = _maven_knowledge_context_digest(request)
            evaluation = self._evaluator.evaluate(
                _maven_evaluation_input(
                    request, collection, knowledge_context_digest
                )
            )
            self._require_complete_evaluation(request, evaluation)
            report_digest = digest_of(
                ["MAVEN_STRUCTURE_BUILD_REPORT@1", evaluation.report]
            )
            evaluation_digest = maven_structure_evaluation_digest(evaluation)
            application_acceptance = _maven_application_acceptance(
                request=request,
                batch=evaluation.batch,
                report_digest=report_digest,
            )
            self._repository.mark_admitting(
                attempt_id=preparation.attempt.attempt_id,
                source_collection_digest=collection.digest,
                source_operation_ids=collection.operation_ids,
                build_report_digest=report_digest,
                application_acceptance_ref=application_acceptance.acceptance_ref,
                application_acceptance_digest=application_acceptance.digest,
                occurred_at=self._now(),
            )

            candidate_digest = maven_structure_candidate_digest(
                request=request,
                collection=collection,
                evaluation=evaluation,
                evaluation_digest=evaluation_digest,
                report_digest=report_digest,
            )
            candidate_ref = f"MAVEN_STRUCTURE_CANDIDATE@1:{candidate_digest.value}"
            target_authority_digest = (
                preparation.target_authority.digest
                if preparation.target_authority is not None
                else terminal.target_authority_digest
            )
            provenance_digest = _maven_provenance_digest(
                request=request,
                target_authority_digest=target_authority_digest,
                collection=collection,
                report_digest=report_digest,
                evaluation_digest=evaluation_digest,
            )

            stage = "ARTIFACT_USE_CONFIRMATION"
            artifact_use_confirmation = self._artifact_use.confirm_persistent_use(
                idempotency_key=_child_idempotency_key(
                    request,
                    "artifact-use-confirmation",
                    candidate_digest,
                ),
                package_id=authorized_read.package.package_id,
                expected_package_digest=authorized_read.package.digest,
                closure_id=authorized_read.closure.closure_id,
                expected_closure_digest=authorized_read.closure.digest,
                protection_id=authorized_read.protection.protection_id,
                expected_protection_digest=authorized_read.protection.digest,
                purpose=ArtifactUsePurpose.MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE,
                downstream_request_ref=preparation.attempt.attempt_id.value,
                downstream_request_digest=request.digest,
                downstream_candidate_ref=candidate_ref,
                downstream_candidate_digest=candidate_digest,
                scope_assertion=self._artifact_scope_assertion(
                    request,
                    request_ref=f"{candidate_ref}:artifact-confirm",
                ),
            )
            self._repository.mark_artifact_use_confirmed(
                attempt_id=preparation.attempt.attempt_id,
                confirmation=artifact_use_confirmation,
                occurred_at=self._now(),
            )

            stage = "INDEPENDENT_VERIFICATION"
            verification_context_digest = _maven_verification_context_digest(
                request=request,
                collection=collection,
                authorized_read=authorized_read,
            )
            self._verifier.bind_candidate(
                candidate_ref=candidate_ref,
                request=request,
                expected_operation_ids=collection.operation_ids,
                authorized_read=authorized_read,
            )
            assessment = self._verifier_assessments.assess(
                candidate_ref=candidate_ref,
                candidate_digest=candidate_digest,
                candidate_evaluation_digest=evaluation_digest,
                candidate_report_digest=report_digest,
                candidate_batch=evaluation.batch,
                provenance_digest=provenance_digest,
                verification_context_digest=verification_context_digest,
                artifact_use_confirmation_id=(
                    artifact_use_confirmation.confirmation_id
                ),
                artifact_use_confirmation_digest=artifact_use_confirmation.digest,
                idempotency_key=_child_idempotency_key(
                    request,
                    "verifier-assessment",
                    candidate_digest,
                ),
            )
            stage = "ADMISSION"
            if assessment.outcome is StructureVerifierAssessmentOutcome.FAIL:
                admission = self._admission.reject(
                    scope_id=request.scope_id,
                    expected_scope_revision=request.scope_revision,
                    expected_current_snapshot_id=request.expected_current_snapshot_id,
                    candidate_ref=candidate_ref,
                    candidate_digest=candidate_digest,
                    batch=evaluation.batch,
                    provenance_digest=provenance_digest,
                    assessment=assessment,
                    idempotency_key=_child_idempotency_key(
                        request,
                        "admission",
                        candidate_digest,
                    ),
                    caller_ref=request.actor_ref,
                    classification=request.classification,
                )
                self._repository.mark_admitted(
                    attempt_id=preparation.attempt.attempt_id,
                    admission_id=admission.admission_id,
                    admission_digest=admission.digest,
                    occurred_at=self._now(),
                )
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "independent Maven Structure verifier rejected the candidate",
                    {
                        "reason_code": "INDEPENDENT_VERIFIER_REJECTED",
                        "assessment_id": assessment.assessment_id.value,
                        "admission_id": admission.admission_id.value,
                        "finding_codes": ",".join(
                            item.code for item in assessment.findings
                        ),
                    },
                )
            admission = self._admission.accept(
                scope_id=request.scope_id,
                expected_scope_revision=request.scope_revision,
                expected_current_snapshot_id=request.expected_current_snapshot_id,
                candidate_ref=candidate_ref,
                candidate_digest=candidate_digest,
                batch=evaluation.batch,
                provenance_digest=provenance_digest,
                assessment=assessment,
                idempotency_key=_child_idempotency_key(
                    request,
                    "admission",
                    candidate_digest,
                ),
                caller_ref=request.actor_ref,
                classification=request.classification,
            )
            self._repository.mark_admitted(
                attempt_id=preparation.attempt.attempt_id,
                admission_id=admission.admission_id,
                admission_digest=admission.digest,
                occurred_at=self._now(),
            )
            publication_key = _child_idempotency_key(
                request,
                "publication",
                candidate_digest,
            )
            stage = "PUBLICATION_DISPATCHED"
            receipt = self._publication.publish(
                scope_id=request.scope_id,
                expected_scope_revision=request.scope_revision,
                expected_current_snapshot_id=request.expected_current_snapshot_id,
                idempotency_key=publication_key,
                batch=evaluation.batch,
                admission=admission,
                application_acceptance=application_acceptance,
                caller_ref=request.actor_ref,
                classification=request.classification,
            )
            stage = "PUBLICATION_COMMITTED"
            return self._finalize_publication(
                request=request,
                attempt_id=preparation.attempt.attempt_id,
                collection=collection,
                evaluation=evaluation,
                report_digest=report_digest,
                assessment=assessment,
                application_acceptance=application_acceptance,
                artifact_use_confirmation=artifact_use_confirmation,
                admission=admission,
                receipt=receipt,
            )
        except MavenStructureError as exc:
            details: dict[str, str | int] = {"reason_code": exc.code.value}
            if exc.locator is not None:
                details["locator"] = exc.locator
            converted = DomainError(
                ErrorCode.INVALID_ARGUMENT,
                str(exc),
                details,
            )
            if terminal is None:
                self._repository.finish_failed(
                    attempt_id=preparation.attempt.attempt_id,
                    error_code=converted.code.value,
                    error_message=converted.message,
                    error_details=converted.details,
                    outcome_pending=False,
                    occurred_at=self._now(),
                )
            raise converted from exc
        except DomainError as exc:
            if publication_key is not None:
                try:
                    recovered = self._publication.get_publication_by_idempotency_key(
                        publication_key
                    )
                    if recovered is not None:
                        return self._finalize_publication(
                            request=request,
                            attempt_id=preparation.attempt.attempt_id,
                            collection=collection,
                            evaluation=evaluation,
                            report_digest=report_digest,
                            assessment=assessment,
                            application_acceptance=application_acceptance,
                            artifact_use_confirmation=artifact_use_confirmation,
                            admission=admission,
                            receipt=recovered,
                        )
                except Exception as recovery_error:
                    if terminal is None:
                        self._repository.finish_failed(
                            attempt_id=preparation.attempt.attempt_id,
                            error_code="OUTCOME_PENDING",
                            error_message=str(recovery_error)
                            or type(recovery_error).__name__,
                            error_details={
                                "stage": stage,
                                "original_error": exc.code.value,
                            },
                            outcome_pending=True,
                            occurred_at=self._now(),
                        )
                    raise exc from recovery_error
            if terminal is None:
                self._repository.finish_failed(
                    attempt_id=preparation.attempt.attempt_id,
                    error_code=exc.code.value,
                    error_message=exc.message,
                    error_details=exc.details,
                    outcome_pending=False,
                    occurred_at=self._now(),
                )
            raise
        except Exception as exc:
            if publication_key is not None:
                try:
                    recovered = self._publication.get_publication_by_idempotency_key(
                        publication_key
                    )
                    if recovered is not None:
                        return self._finalize_publication(
                            request=request,
                            attempt_id=preparation.attempt.attempt_id,
                            collection=collection,
                            evaluation=evaluation,
                            report_digest=report_digest,
                            assessment=assessment,
                            application_acceptance=application_acceptance,
                            artifact_use_confirmation=artifact_use_confirmation,
                            admission=admission,
                            receipt=recovered,
                        )
                except Exception:
                    pass
            if terminal is None:
                self._repository.finish_failed(
                    attempt_id=preparation.attempt.attempt_id,
                    error_code="OUTCOME_PENDING",
                    error_message=str(exc) or type(exc).__name__,
                    error_details={"stage": stage},
                    outcome_pending=True,
                    occurred_at=self._now(),
                )
            raise

    def _finalize_publication(
        self,
        *,
        request: MavenStructureUpdateRequest,
        attempt_id: StableId,
        collection: MavenStructureSourceCollection,
        evaluation: MavenStructureEvaluation,
        report_digest: Digest,
        assessment: StructureVerifierAssessment,
        application_acceptance: StructureApplicationAcceptance,
        artifact_use_confirmation: ArtifactUseConfirmation,
        admission: StructureAdmissionDecision,
        receipt: StructurePublicationReceipt,
    ) -> MavenStructureUpdateResult:
        persisted_artifact_use = self._artifact_use.get_confirmation(
            artifact_use_confirmation.confirmation_id
        )
        if (
            persisted_artifact_use != artifact_use_confirmation
            or persisted_artifact_use.purpose
            is not ArtifactUsePurpose.MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE
            or persisted_artifact_use.downstream_request_ref != attempt_id.value
            or persisted_artifact_use.downstream_request_digest != request.digest
            or persisted_artifact_use.downstream_candidate_ref
            != admission.candidate_ref
            or persisted_artifact_use.downstream_candidate_digest
            != admission.candidate_digest
            or admission.artifact_use_confirmation_id
            != persisted_artifact_use.confirmation_id
            or admission.artifact_use_confirmation_digest
            != persisted_artifact_use.digest
            or assessment.artifact_use_confirmation_id
            != persisted_artifact_use.confirmation_id
            or assessment.artifact_use_confirmation_digest
            != persisted_artifact_use.digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Artifact use Confirmation differs from the Maven publication closure",
                {"reason_code": "ARTIFACT_USE_CONFIRMATION_DRIFT"},
            )
        persisted = self._publication.get_publication(receipt.publication_id)
        if persisted != receipt:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "returned Structure Publication Receipt differs from owner authority",
            )
        if (
            persisted.snapshot.scope_id != request.scope_id
            or persisted.snapshot.previous_snapshot_id
            != request.expected_current_snapshot_id
            or persisted.admission_id != admission.admission_id
            or persisted.admission_digest != admission.digest
            or persisted.application_acceptance_digest
            != application_acceptance.digest
            or persisted.batch_digest != structure_batch_digest(evaluation.batch)
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "persisted Structure Publication does not match the Maven authority closure",
            )
        previous_snapshot = (
            self._publication.get_snapshot(request.expected_current_snapshot_id)
            if request.expected_current_snapshot_id is not None
            else None
        )
        deletions = StructureReplacementDeletions.between(
            previous_snapshot.members if previous_snapshot is not None else (),
            persisted.snapshot.members,
        )
        existing = self._repository.get_result(
            idempotency_key=request.idempotency_key
        )
        if existing is None or (
            existing.state is MavenStructureUpdateState.OUTCOME_PENDING
        ):
            authority_result = self._repository.finish_published(
                attempt_id=attempt_id,
                publication_receipt=persisted,
                occurred_at=self._now(),
            )
        else:
            if (
                existing.state is not MavenStructureUpdateState.PUBLISHED
                or existing.admission_id != persisted.admission_id
                or existing.admission_digest != persisted.admission_digest
                or existing.application_acceptance_digest
                != persisted.application_acceptance_digest
                or existing.publication_id != persisted.publication_id
                or existing.publication_digest != persisted.digest
                or existing.published_snapshot_id
                != persisted.snapshot.snapshot_id
                or existing.previous_snapshot_id
                != persisted.snapshot.previous_snapshot_id
                or existing.replacement_deletions_digest != deletions.digest
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "durable Maven Result differs from committed Structure Publication",
                )
            authority_result = existing
        return MavenStructureUpdateResult(
            authority_result=authority_result,
            request_digest=request.digest,
            source_collection_digest=collection.digest,
            source_operation_ids=collection.operation_ids,
            build_report_digest=report_digest,
            verifier_assessment=assessment,
            application_acceptance=application_acceptance,
            artifact_use_confirmation=persisted_artifact_use,
            publication_receipt=persisted,
            previous_snapshot=previous_snapshot,
            deletions=deletions,
            evaluation=evaluation,
            digest=authority_result.digest,
        )

    def _recover_outcome_pending(
        self,
        request: MavenStructureUpdateRequest,
        preparation: MavenStructureUpdatePreparation,
    ) -> MavenStructureUpdateResult:
        """Reconcile one dispatched Publication without new Source effects.

        The durable Application Result deliberately carries refs/digests, not
        Source payload.  Recovery therefore rebuilds the execution projection
        exclusively through the replay-only verifier capability and then asks
        the Knowledge owner for the original Publication idempotency key.
        """

        terminal = preparation.terminal_result
        if terminal is None or terminal.state is not MavenStructureUpdateState.OUTCOME_PENDING:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Maven recovery requires an OUTCOME_PENDING authority Result",
            )
        if (
            preparation.target_authority is None
            or terminal.source_collection_digest is None
            or not terminal.source_operation_ids
            or terminal.build_report_digest is None
            or terminal.admission_id is None
            or terminal.admission_digest is None
            or terminal.application_acceptance_ref is None
            or terminal.application_acceptance_digest is None
            or terminal.artifact_read_package_id is None
            or terminal.artifact_read_package_digest is None
            or terminal.artifact_use_confirmation_id is None
            or terminal.artifact_use_confirmation_digest is None
        ):
            self._raise_terminal(terminal)

        # A persisted use confirmation identifies the exact Package and
        # Protection, but is not itself current permission to read payload.
        # Reopen through the Source owner before any replay/evaluation.
        recorded_artifact_use = self._artifact_use.get_confirmation(
            terminal.artifact_use_confirmation_id
        )
        if (
            recorded_artifact_use.digest
            != terminal.artifact_use_confirmation_digest
            or recorded_artifact_use.package_id
            != terminal.artifact_read_package_id
            or recorded_artifact_use.package_digest
            != terminal.artifact_read_package_digest
            or recorded_artifact_use.purpose
            is not ArtifactUsePurpose.MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE
            or recorded_artifact_use.downstream_request_ref
            != preparation.attempt.attempt_id.value
            or recorded_artifact_use.downstream_request_digest != request.digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "pending Maven Result differs from Artifact use authority",
                {"reason_code": "PENDING_ARTIFACT_USE_DRIFT"},
            )
        authorized_read = self._artifact_use.reopen_authorized_read(
            package_id=recorded_artifact_use.package_id,
            expected_package_digest=recorded_artifact_use.package_digest,
            closure_id=recorded_artifact_use.closure_id,
            expected_closure_digest=recorded_artifact_use.closure_digest,
            protection_id=recorded_artifact_use.protection_id,
            expected_protection_digest=recorded_artifact_use.protection_digest,
            purpose=recorded_artifact_use.purpose,
            downstream_request_ref=recorded_artifact_use.downstream_request_ref,
            downstream_request_digest=(
                recorded_artifact_use.downstream_request_digest
            ),
            scope_assertion=self._artifact_scope_assertion(
                request,
                request_ref=(
                    f"{preparation.attempt.attempt_id.value}:artifact-recovery"
                ),
            ),
        )
        collection = MavenStructureSourceCollector(
            self._scopes,
            self._configurations,
            replay=authorized_read,
        ).collect(
            request,
            expected_operation_ids=terminal.source_operation_ids,
        )
        if collection.digest != terminal.source_collection_digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "replayed Source collection differs from pending Maven Result",
                {"reason_code": "PENDING_SOURCE_COLLECTION_DRIFT"},
            )
        knowledge_context_digest = _maven_knowledge_context_digest(request)
        evaluation = MavenStructureEvaluator().evaluate(
            _maven_evaluation_input(
                request,
                collection,
                knowledge_context_digest,
            )
        )
        self._require_complete_evaluation(request, evaluation)
        report_digest = digest_of(
            ["MAVEN_STRUCTURE_BUILD_REPORT@1", evaluation.report]
        )
        if report_digest != terminal.build_report_digest:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "replayed Maven report differs from pending Result",
                {"reason_code": "PENDING_BUILD_REPORT_DRIFT"},
            )
        evaluation_digest = maven_structure_evaluation_digest(evaluation)
        candidate_digest = maven_structure_candidate_digest(
            request=request,
            collection=collection,
            evaluation=evaluation,
            evaluation_digest=evaluation_digest,
            report_digest=report_digest,
        )
        candidate_ref = f"MAVEN_STRUCTURE_CANDIDATE@1:{candidate_digest.value}"
        provenance_digest = _maven_provenance_digest(
            request=request,
            target_authority_digest=preparation.target_authority.digest,
            collection=collection,
            report_digest=report_digest,
            evaluation_digest=evaluation_digest,
        )
        application_acceptance = _maven_application_acceptance(
            request=request,
            batch=evaluation.batch,
            report_digest=report_digest,
        )
        if (
            application_acceptance.acceptance_ref
            != terminal.application_acceptance_ref
            or application_acceptance.digest
            != terminal.application_acceptance_digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "replayed Application PASS differs from pending Result",
                {"reason_code": "PENDING_APPLICATION_ACCEPTANCE_DRIFT"},
            )

        admission = self._admission.get_admission(terminal.admission_id)
        if (
            admission.digest != terminal.admission_digest
            or admission.candidate_ref != candidate_ref
            or admission.candidate_digest != candidate_digest
            or admission.batch_digest != structure_batch_digest(evaluation.batch)
            or admission.provenance_digest != provenance_digest
            or admission.artifact_use_confirmation_id
            != recorded_artifact_use.confirmation_id
            or admission.artifact_use_confirmation_digest
            != recorded_artifact_use.digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "persisted Admission differs from the pending Maven closure",
                {"reason_code": "PENDING_ADMISSION_DRIFT"},
            )
        assessment = self._admission.get_assessment(
            admission.verifier_assessment_id
        )
        verification_context_digest = _maven_verification_context_digest(
            request=request,
            collection=collection,
            authorized_read=authorized_read,
        )
        if (
            assessment.digest != admission.verifier_assessment_digest
            or assessment.verification_context_digest
            != verification_context_digest
            or assessment.artifact_use_confirmation_id
            != recorded_artifact_use.confirmation_id
            or assessment.artifact_use_confirmation_digest
            != recorded_artifact_use.digest
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "persisted verifier assessment differs from pending Admission",
                {"reason_code": "PENDING_ASSESSMENT_DRIFT"},
            )
        artifact_use_confirmation = self._artifact_use.confirm_persistent_use(
            idempotency_key=_child_idempotency_key(
                request,
                "artifact-use-confirmation",
                candidate_digest,
            ),
            package_id=recorded_artifact_use.package_id,
            expected_package_digest=recorded_artifact_use.package_digest,
            closure_id=recorded_artifact_use.closure_id,
            expected_closure_digest=recorded_artifact_use.closure_digest,
            protection_id=recorded_artifact_use.protection_id,
            expected_protection_digest=recorded_artifact_use.protection_digest,
            purpose=ArtifactUsePurpose.MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE,
            downstream_request_ref=preparation.attempt.attempt_id.value,
            downstream_request_digest=request.digest,
            downstream_candidate_ref=candidate_ref,
            downstream_candidate_digest=candidate_digest,
            scope_assertion=self._artifact_scope_assertion(
                request,
                request_ref=f"{candidate_ref}:artifact-reconfirm",
            ),
        )

        publication_key = _child_idempotency_key(
            request,
            "publication",
            candidate_digest,
        )
        try:
            receipt = self._publication.get_publication_by_idempotency_key(
                publication_key
            )
        except Exception as exc:
            raise DomainError(
                ErrorCode.EVALUATION_OUTCOME_PENDING,
                "Maven Structure publication outcome is still unavailable",
                {
                    "result_id": terminal.result_id.value,
                    "stage": "PUBLICATION_RECOVERY_QUERY",
                },
            ) from exc
        if receipt is None:
            receipt = self._publication.publish(
                scope_id=request.scope_id,
                expected_scope_revision=request.scope_revision,
                expected_current_snapshot_id=request.expected_current_snapshot_id,
                idempotency_key=publication_key,
                batch=evaluation.batch,
                admission=admission,
                application_acceptance=application_acceptance,
                caller_ref=request.actor_ref,
                classification=request.classification,
            )
        return self._finalize_publication(
            request=request,
            attempt_id=preparation.attempt.attempt_id,
            collection=collection,
            evaluation=evaluation,
            report_digest=report_digest,
            assessment=assessment,
            application_acceptance=application_acceptance,
            artifact_use_confirmation=artifact_use_confirmation,
            admission=admission,
            receipt=receipt,
        )

    def get_result(
        self,
        *,
        idempotency_key: IdempotencyKey,
    ) -> MavenStructureUpdateAuthorityResult | None:
        return self._repository.get_result(idempotency_key=idempotency_key)

    def _artifact_scope_assertion(
        self,
        request: MavenStructureUpdateRequest,
        *,
        request_ref: str,
    ) -> ScopeStateAssertion:
        return self._scopes.read_scope_state_assertion(
            scope_id=request.scope_id,
            expected_revision=request.scope_revision,
            purpose=ScopePurpose.SOURCE_EXECUTION,
            caller_ref=request.actor_ref,
            request_ref=request_ref,
            classification=request.classification,
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            _invalid(
                "UPDATE_TIMEZONE_REQUIRED",
                "Maven Structure update clock must return a timezone-aware time",
            )
        return value.astimezone(timezone.utc)

    @staticmethod
    def _raise_terminal(result: MavenStructureUpdateAuthorityResult) -> None:
        if result.state is MavenStructureUpdateState.OUTCOME_PENDING:
            raise DomainError(
                ErrorCode.EVALUATION_OUTCOME_PENDING,
                "Maven Structure update outcome is pending recovery",
                {"result_id": result.result_id.value},
            )
        error_code = _error_code(result.failure_code)
        raise DomainError(
            error_code,
            result.failure_message or "Maven Structure update failed",
            dict(result.failure_details),
        )

    @staticmethod
    def _require_complete_evaluation(
        request: MavenStructureUpdateRequest,
        evaluation: MavenStructureEvaluation,
    ) -> None:
        report = evaluation.report
        if (
            not report.complete
            or report.source_revision != request.repository_revision
            or report.schema_ref != SCHEMA_REF
            or report.evaluation_context_ref != EVALUATION_CONTEXT_REF
            or report.canonicalization_ref != CANONICALIZATION_REF
        ):
            _invalid(
                "APPLICATION_ACCEPTANCE_FAILED",
                "Maven evaluator report is incomplete or does not bind the exact frozen context",
            )
        expected_tree_evidence = {item.evidence_id for item in evaluation.batch.evidence}
        required_tree_evidence = {
            item.evidence_id for item in evaluation.batch.evidence
            if item.locator.startswith(f"git-tree:{request.repository_revision}:")
        }
        if not required_tree_evidence or not required_tree_evidence <= expected_tree_evidence:
            _invalid(
                "TREE_EVIDENCE_MISSING",
                "Maven Structure batch must retain exact TREE Evidence",
            )
        coverage_refs = set(evaluation.batch.coverage.state.evidence_references)
        if not required_tree_evidence <= coverage_refs:
            _invalid(
                "TREE_EVIDENCE_OUTSIDE_COVERAGE",
                "Coverage State must reference every exact TREE Evidence page",
            )


def _maven_evaluation_input(
    request: MavenStructureUpdateRequest,
    collection: MavenStructureSourceCollection,
    knowledge_context_digest: Digest,
) -> MavenEvaluationInput:
    return MavenEvaluationInput(
        owning_scope_id=request.scope_id,
        canonical_system_key=request.canonical_system_key,
        source_binding_id=request.binding_id,
        source_revision=request.repository_revision,
        knowledge_context_digest=knowledge_context_digest,
        pom_bytes=collection.pom_bytes,
        git_entries=collection.git_entries,
        pom_evidence=collection.pom_evidence,
        tree_evidence=collection.tree_evidence,
        logical_reactor_root=request.logical_reactor_root,
    )


def _maven_knowledge_context_digest(
    request: MavenStructureUpdateRequest,
) -> Digest:
    return digest_of(
        [
            "MAVEN_STRUCTURE_KNOWLEDGE_CONTEXT@1",
            {
                "scope_id": request.scope_id.value,
                "scope_revision": request.scope_revision.value,
                "source_id": request.source_id.value,
                "source_revision": request.source_revision.value,
                "binding_id": request.binding_id.value,
                "binding_revision": request.binding_revision.value,
                "repository_revision": request.repository_revision,
                "schema_ref": SCHEMA_REF,
                "schema_digest": SCHEMA_DIGEST,
                "evaluation_context_ref": EVALUATION_CONTEXT_REF,
                "evaluation_context_digest": EVALUATION_CONTEXT_DIGEST,
                "canonicalization_ref": CANONICALIZATION_REF,
                "canonicalization_digest": CANONICALIZATION_DIGEST,
            },
        ]
    )


def _maven_verification_context_digest(
    *,
    request: MavenStructureUpdateRequest,
    collection: MavenStructureSourceCollection,
    authorized_read: AuthorizedArtifactRead,
) -> Digest:
    return digest_of(
        [
            "MAVEN_STRUCTURE_INDEPENDENT_VERIFICATION_CONTEXT@1",
            {
                "verifier_ref": _MAVEN_INDEPENDENT_VERIFIER_REF,
                "candidate_generator_ref": _MAVEN_CANDIDATE_GENERATOR_REF,
                "request_digest": request.digest.value,
                "source_collection_digest": collection.digest.value,
                "source_operation_ids": tuple(
                    item.value for item in collection.operation_ids
                ),
                "source_operation_digests": tuple(
                    item.value for item in collection.operation_digests
                ),
                "artifact_read_package_id": (
                    authorized_read.package.package_id.value
                ),
                "artifact_read_package_digest": (
                    authorized_read.package.digest.value
                ),
                "artifact_read_closure_id": (
                    authorized_read.closure.closure_id.value
                ),
                "artifact_read_closure_digest": (
                    authorized_read.closure.digest.value
                ),
                "artifact_read_protection_id": (
                    authorized_read.protection.protection_id.value
                ),
                "artifact_read_protection_digest": (
                    authorized_read.protection.digest.value
                ),
                "artifact_read_purpose": authorized_read.package.purpose.value,
                "schema_ref": SCHEMA_REF,
                "schema_digest": SCHEMA_DIGEST,
                "evaluation_context_ref": EVALUATION_CONTEXT_REF,
                "evaluation_context_digest": EVALUATION_CONTEXT_DIGEST,
                "canonicalization_ref": CANONICALIZATION_REF,
                "canonicalization_digest": CANONICALIZATION_DIGEST,
            },
        ]
    )


def _maven_application_acceptance(
    *,
    request: MavenStructureUpdateRequest,
    batch: StructureKnowledgeBatch,
    report_digest: Digest,
) -> StructureApplicationAcceptance:
    acceptance_identity = digest_of(
        {
            "actor_ref": request.actor_ref,
            "report_digest": report_digest.value,
            "update_request_digest": request.digest.value,
        }
    )
    return StructureApplicationAcceptance.pass_for(
        batch,
        acceptance_ref=(
            "MAVEN_STRUCTURE_APPLICATION_PASS@1:"
            f"{acceptance_identity.value}"
        ),
        report_digest=report_digest,
    )


def _maven_provenance_digest(
    *,
    request: MavenStructureUpdateRequest,
    target_authority_digest: Digest,
    collection: MavenStructureSourceCollection,
    report_digest: Digest,
    evaluation_digest: Digest,
) -> Digest:
    return digest_of(
        [
            "MAVEN_STRUCTURE_PROVENANCE@1",
            {
                "objective_digest": request.objective.digest.value,
                "target_digest": request.target.digest.value,
                "target_authority_digest": target_authority_digest.value,
                "source_collection_digest": collection.digest.value,
                "source_operation_ids": tuple(
                    item.value for item in collection.operation_ids
                ),
                "source_operation_digests": tuple(
                    item.value for item in collection.operation_digests
                ),
                "build_report_digest": report_digest.value,
                "evaluation_digest": evaluation_digest.value,
                "generator_ref": _MAVEN_CANDIDATE_GENERATOR_REF,
            },
        ]
    )


def maven_structure_evaluation_digest(
    evaluation: MavenStructureEvaluation,
) -> Digest:
    """Digest every canonical evaluator output, including report-only facts."""

    return digest_of(
        [
            "MAVEN_STRUCTURE_CANONICAL_EVALUATION@1",
            {
                "root_project": evaluation.root_project,
                "modules": evaluation.modules,
                "relations": evaluation.relations,
                "coverage": evaluation.coverage,
                "complete_member_manifest": evaluation.complete_member_manifest,
                "evidence": evaluation.evidence,
                "exclusions": evaluation.exclusions,
                "report": evaluation.report,
                "batch": evaluation.batch,
            },
        ]
    )


def maven_structure_candidate_digest(
    *,
    request: MavenStructureUpdateRequest,
    collection: MavenStructureSourceCollection,
    evaluation: MavenStructureEvaluation,
    evaluation_digest: Digest,
    report_digest: Digest,
) -> Digest:
    return digest_of(
        [
            "MAVEN_STRUCTURE_CANDIDATE@1",
            {
                "generator_ref": _MAVEN_CANDIDATE_GENERATOR_REF,
                "batch_digest": structure_batch_digest(evaluation.batch).value,
                "evaluation_digest": evaluation_digest.value,
                "source_collection_digest": collection.digest.value,
                "source_operation_ids": tuple(
                    item.value for item in collection.operation_ids
                ),
                "source_operation_digests": tuple(
                    item.value for item in collection.operation_digests
                ),
                "build_report_digest": report_digest.value,
                "objective_digest": request.objective.digest.value,
                "target_digest": request.target.digest.value,
            },
        ]
    )


def parse_local_git_tree_jsonl(
    payload: bytes,
) -> tuple[tuple[str, GitEntryMetadata], ...]:
    """Parse and re-canonicalize ``LOCAL_GIT_TREE_ENTRY_LIST@1`` JSONL."""

    if not isinstance(payload, bytes):
        _source_invalid("TREE_PAYLOAD_NOT_BYTES", "Git tree payload must be immutable bytes")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DomainError(
            ErrorCode.SOURCE_OPERATION_FAILED,
            "Git tree JSONL must be UTF-8",
            {"reason_code": "TREE_UTF8_INVALID"},
        ) from exc
    if not text:
        return ()
    records: list[tuple[str, GitEntryMetadata]] = []
    seen_paths: set[str] = set()
    for ordinal, line in enumerate(text.splitlines(), 1):
        if not line:
            _source_invalid(
                "TREE_JSONL_EMPTY_RECORD",
                "Git tree JSONL contains an empty record",
                ordinal=ordinal,
            )
        try:
            value = json.loads(line, object_pairs_hook=_unique_json_object)
        except (json.JSONDecodeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.SOURCE_OPERATION_FAILED,
                "Git tree JSONL contains a malformed record",
                {"reason_code": "TREE_JSON_INVALID", "ordinal": ordinal},
            ) from exc
        if not isinstance(value, dict) or set(value) != {
            "is_symlink",
            "mode",
            "object_id",
            "path",
            "type",
        }:
            _source_invalid(
                "TREE_SCHEMA_INVALID",
                "Git tree JSONL record does not have the exact schema",
                ordinal=ordinal,
            )
        if canonical_json_bytes(value).decode("utf-8") != line:
            _source_invalid(
                "TREE_JSON_NOT_CANONICAL",
                "Git tree JSONL record is not canonical JSON",
                ordinal=ordinal,
            )
        path = _path(value["path"], "Git tree entry path")
        mode = value["mode"]
        object_type = value["type"]
        object_id = value["object_id"]
        is_symlink = value["is_symlink"]
        if not isinstance(mode, str) or not _GIT_MODE.fullmatch(mode):
            _source_invalid("TREE_MODE_INVALID", "Git tree mode must be six octal digits", path=path)
        if not isinstance(object_type, str) or not object_type or object_type != object_type.strip():
            _source_invalid("TREE_OBJECT_TYPE_INVALID", "Git tree object type must be non-empty", path=path)
        if not isinstance(object_id, str) or not _FULL_GIT_OBJECT.fullmatch(object_id):
            _source_invalid("TREE_OBJECT_ID_INVALID", "Git tree object ID must be full lowercase hex", path=path)
        if type(is_symlink) is not bool or is_symlink != (mode == "120000"):
            _source_invalid("TREE_SYMLINK_FLAG_INVALID", "Git tree symlink flag disagrees with mode", path=path)
        if path in seen_paths:
            _source_invalid("TREE_ENTRY_DUPLICATE", "Git tree JSONL repeats a canonical path", path=path)
        seen_paths.add(path)
        records.append(
            (
                path,
                GitEntryMetadata(
                    mode=mode,
                    object_type=object_type,
                    object_id=object_id,
                ),
            )
        )
    return tuple(records)


def _unique_json_object(pairs: Sequence[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _require_objective(objective: object) -> None:
    if not isinstance(objective, BuildObjective):
        _invalid(
            "BUILD_OBJECTIVE_REQUIRED",
            "manual Maven Structure update requires a typed Build Objective",
        )
    expected = BuildObjective.create(
        objective_id=objective.objective_id,
        description=objective.description,
        unacceptable_outcomes=objective.unacceptable_outcomes,
    )
    if expected != objective:
        _invalid(
            "BUILD_OBJECTIVE_INVALID",
            "manual Maven Structure update Build Objective is not canonical",
        )


def _require_canonical_revision_target(
    target: object,
    repository_revision: str,
) -> None:
    if not isinstance(target, CanonicalBuildTarget):
        _invalid(
            "CANONICAL_BUILD_TARGET_REQUIRED",
            "manual Maven Structure update requires a typed Canonical Build Target",
        )
    if (
        target.target_kind is not TargetKind.REPOSITORY_REVISION
        or target.canonical_identity != (("revision", repository_revision),)
        or target.obligation is not CoverageObligation.REQUIRED
        or target.boundary != "EXACT"
        or target.resolution_receipt_id.kind != "target_receipt"
    ):
        _invalid(
            "CANONICAL_BUILD_TARGET_MISMATCH",
            "Maven Structure target must be the exact required repository revision",
        )
    core = {
        "target_kind": target.target_kind.value,
        "canonical_identity": target.canonical_identity,
        "resolution_receipt_id": target.resolution_receipt_id.value,
        "resolution_receipt_digest": target.resolution_receipt_digest.value,
        "obligation": target.obligation.value,
        "boundary": target.boundary,
        "canonicalization_contract": _LOCAL_GIT_TARGET_RESOLVER_CONTRACT,
    }
    expected_digest = digest_of(core)
    expected_target_id = StableId(
        f"build_target_{expected_digest.value[-32:]}"
    )
    if target.digest != expected_digest or target.target_id != expected_target_id:
        _invalid(
            "CANONICAL_BUILD_TARGET_INVALID",
            "Canonical Build Target does not bind its exact resolver receipt",
        )


def _child_idempotency_key(
    request: MavenStructureUpdateRequest,
    stage: str,
    closure_digest: Digest,
) -> IdempotencyKey:
    digest = digest_of(
        [
            "MAVEN_STRUCTURE_UPDATE_CHILD_KEY@1",
            {
                "request_digest": request.digest.value,
                "stage": stage,
                "closure_digest": closure_digest.value,
            },
        ]
    )
    return IdempotencyKey(
        f"maven-structure-{stage}-{digest.value.removeprefix('sha256:')}"
    )


def _error_code(value: str | None) -> ErrorCode:
    if value is not None:
        try:
            return ErrorCode(value)
        except ValueError:
            pass
    return ErrorCode.AUTHORITY_RECORD_INCONSISTENT


def _require_artifact_authority(
    request: MavenStructureUpdateRequest,
    artifact: SourceArtifact,
    expected_kind: str,
) -> None:
    if (
        artifact.artifact_kind != expected_kind
        or artifact.payload_schema_version != _PAYLOAD_SCHEMA_VERSION
        or artifact.source_id != request.source_id
        or artifact.source_revision != request.source_revision
        or artifact.classification != request.classification
    ):
        _source_invalid(
            "ARTIFACT_AUTHORITY_MISMATCH",
            "Source Artifact does not match the exact update authority closure",
        )


def _require_persisted_source_operation(
    intent: SourceOperationIntent,
    operation: SourceOperationResult,
) -> None:
    """Recompute the complete persisted Source Operation authority closure."""

    if operation.intent_digest != intent.digest:
        _source_invalid(
            "SOURCE_OPERATION_INTENT_DIGEST_MISMATCH",
            "persisted Source Operation is bound to another intent",
        )
    observation = operation.observation
    expected_result_digest = digest_of(
        {
            "operation_id": operation.operation_id.value,
            "revision": operation.revision.value,
            "status": operation.status.value,
            "intent_digest": operation.intent_digest.value,
            "observation_id": (
                observation.observation_id.value if observation is not None else None
            ),
            "failure_code": operation.failure_code,
            "occurred_at": operation.revised_at,
        }
    )
    if operation.digest != expected_result_digest:
        _source_invalid(
            "SOURCE_OPERATION_RESULT_DIGEST_MISMATCH",
            "persisted Source Operation Result digest is inconsistent",
        )
    if observation is None:
        return
    if observation.operation_id != operation.operation_id or observation.tool is not intent.tool:
        _source_invalid(
            "SOURCE_OBSERVATION_AUTHORITY_MISMATCH",
            "persisted Source Observation belongs to another Operation",
        )
    context = observation.source_context
    context_digest = digest_of(
        {
            "source_id": context.source_id.value,
            "source_revision": context.source_revision.value,
            "repository_revision": context.repository_revision,
            "subject": context.subject,
            "observed_at": context.observed_at,
            "basis": "SINGLE_OBSERVATION",
            "context_contract": "local-git-context@1",
        }
    )
    if (
        context.digest != context_digest
        or context.context_id
        != StableId(f"source_context_{context_digest.value[-32:]}")
    ):
        _source_invalid(
            "SOURCE_CONTEXT_DIGEST_MISMATCH",
            "persisted Source Context is not canonical",
        )
    identity_coverage = _source_artifact_identity_coverage(
        observation.tool, dict(observation.coverage)
    )
    for artifact in observation.artifacts:
        payload_digest = content_digest(artifact.payload)
        identity_digest = digest_of(
            {
                "source_id": artifact.source_id.value,
                "source_revision": artifact.source_revision.value,
                "source_context_id": artifact.source_context_id.value,
                "source_native_identity": artifact.source_native_identity,
                "artifact_kind": artifact.artifact_kind,
                "payload_schema_version": artifact.payload_schema_version,
                "provider_contract": "LOCAL_GIT@0.1.0",
                "tool": observation.tool.value,
                "coverage": identity_coverage,
                "identity_strategy": "local-git-artifact@2",
            }
        )
        if (
            artifact.content_digest != payload_digest
            or artifact.identity_digest != identity_digest
            or artifact.artifact_id
            != StableId(f"source_artifact_{identity_digest.value[-32:]}")
            or artifact.source_context_id != context.context_id
        ):
            _source_invalid(
                "SOURCE_ARTIFACT_DIGEST_MISMATCH",
                "persisted Source Artifact identity or content is inconsistent",
            )
    expected_observation_digest = digest_of(
        {
            "observation_id": observation.observation_id.value,
            "operation_id": operation.operation_id.value,
            "tool": observation.tool.value,
            "context_digest": context.digest.value,
            "artifacts": tuple(
                (artifact.artifact_id.value, artifact.content_digest.value)
                for artifact in observation.artifacts
            ),
            "item_count": observation.item_count,
            "byte_count": observation.byte_count,
            "next_cursor": observation.next_cursor,
            "has_more": observation.has_more,
            "coverage": identity_coverage,
            "observed_at": observation.observed_at,
        }
    )
    if (
        observation.digest != expected_observation_digest
        or observation.observed_at != context.observed_at
        or observation.byte_count
        != sum(len(artifact.payload) for artifact in observation.artifacts)
    ):
        _source_invalid(
            "SOURCE_OBSERVATION_DIGEST_MISMATCH",
            "persisted Source Observation is not canonical",
        )


def _source_artifact_identity_coverage(
    tool: SourceTool,
    coverage: Mapping[str, str],
) -> tuple[tuple[str, str], ...]:
    if tool in (SourceTool.LIST, SourceTool.TREE, SourceTool.SEARCH):
        keys = ("cursor_start", "cursor_end", "matched_total", "revision")
    elif tool is SourceTool.READ:
        keys = ("path", "range", "revision")
    elif tool is SourceTool.COMPARE:
        keys = ("base", "target", "paths")
    else:  # pragma: no cover - SourceTool is a closed enum
        keys = tuple(sorted(coverage))
    if set(coverage) != set(keys):
        _source_invalid(
            "SOURCE_OBSERVATION_COVERAGE_INVALID",
            "persisted Source Observation Coverage is not canonical",
        )
    return tuple((key, coverage[key]) for key in keys)


def _operation_failed(operation: SourceOperationResult, reason_code: str) -> None:
    raise DomainError(
        ErrorCode.SOURCE_OPERATION_FAILED,
        "Source operation did not produce a usable terminal observation",
        {
            "reason_code": reason_code,
            "status": operation.status.value,
            "failure_code": operation.failure_code or "-",
        },
    )


def _nonnegative_int(value: object, label: str) -> int:
    if not isinstance(value, str) or not value.isdigit():
        _source_invalid("TREE_COVERAGE_INVALID", f"{label} must be a non-negative integer")
    return int(value)


def _path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value:
        _invalid("PATH_INVALID", f"{label} must be a canonical repository-relative path")
    parsed = PurePosixPath(value)
    if parsed.is_absolute() or any(part in ("", ".", "..") for part in parsed.parts):
        _invalid("PATH_INVALID", f"{label} must be a canonical repository-relative path")
    canonical = parsed.as_posix()
    if canonical != value:
        _invalid("PATH_INVALID", f"{label} must be a canonical repository-relative path")
    return canonical


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        _invalid("TEXT_INVALID", f"{label} must be non-empty and canonical")
    return value


def _source_invalid(reason_code: str, message: str, **details: str | int) -> None:
    raise DomainError(
        ErrorCode.SOURCE_OPERATION_FAILED,
        message,
        {"reason_code": reason_code, **details},
    )


def _invalid(reason_code: str, message: str) -> None:
    raise DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


__all__ = [
    "MavenEvaluator",
    "MavenStructureSourceCollection",
    "MavenStructureSourceCollector",
    "MavenStructureTargetAuthority",
    "MavenStructureUpdateAttempt",
    "MavenStructureUpdateAuthorityService",
    "MavenStructureUpdateAuthorityResult",
    "MavenStructureUpdatePreparation",
    "MavenStructureUpdateRepository",
    "MavenStructureUpdateRequest",
    "MavenStructureUpdateResult",
    "MavenStructureUpdateService",
    "MavenStructureUpdateState",
    "StructureReplacementDeletions",
    "parse_local_git_tree_jsonl",
]
