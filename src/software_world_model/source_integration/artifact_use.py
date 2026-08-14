"""Source-owned authority for persistent cross-module Artifact use.

This module has no Connector capability.  It can only replay already-persisted
Source Operations, validate their exact authority closure, authorize a bounded
read under explicit retention protection, and confirm one exact downstream
persistent use.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Protocol, Sequence

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine import ScopeStateAssertion

from .operations import (
    SourceArtifact,
    SourceContext,
    SourceObservation,
    SourceOperationCurrentAuthorizedReplayPort,
    SourceOperationResult,
    SourceOperationStatus,
    SourceTool,
    content_digest,
)


class ArtifactReadProtectionMode(str, Enum):
    NO_EVICTION = "NO_EVICTION"


class ArtifactUsePurpose(str, Enum):
    MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE = (
        "MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE@1"
    )
    JAVA_STATIC_CALL_EVIDENCE_PERSISTENCE = (
        "JAVA_STATIC_CALL_EVIDENCE_PERSISTENCE@1"
    )
    JAVA_SOURCE_SEMANTICS_EVIDENCE_PERSISTENCE = (
        "JAVA_SOURCE_SEMANTICS_EVIDENCE_PERSISTENCE@1"
    )


@dataclass(frozen=True, slots=True)
class ArtifactReadOperationReference:
    operation_id: StableId
    intent_digest: Digest
    result_digest: Digest

    def __post_init__(self) -> None:
        _typed(self.operation_id, StableId, "Source Operation ID")
        _typed(self.intent_digest, Digest, "Source Operation intent digest")
        _typed(self.result_digest, Digest, "Source Operation Result digest")

    @classmethod
    def from_result(
        cls, result: SourceOperationResult
    ) -> "ArtifactReadOperationReference":
        _typed(result, SourceOperationResult, "Source Operation Result")
        return cls(result.operation_id, result.intent_digest, result.digest)


@dataclass(frozen=True, slots=True)
class ArtifactReadArtifactReference:
    artifact_id: StableId
    identity_digest: Digest
    content_digest: Digest


@dataclass(frozen=True, slots=True)
class ArtifactReadOperationClosure:
    operation_id: StableId
    revision: Revision
    status: SourceOperationStatus
    intent_digest: Digest
    result_digest: Digest
    observation_id: StableId
    observation_digest: Digest
    source_context_id: StableId
    source_context_digest: Digest
    artifacts: tuple[ArtifactReadArtifactReference, ...]


@dataclass(frozen=True, slots=True)
class ArtifactReadClosure:
    """Ordered exact Operation -> Observation -> Artifact closure."""

    closure_id: StableId
    operations: tuple[ArtifactReadOperationClosure, ...]
    digest: Digest


@dataclass(frozen=True, slots=True)
class ArtifactReadPackage:
    package_id: StableId
    request_digest: Digest
    operation_references: tuple[ArtifactReadOperationReference, ...]
    closure_id: StableId
    closure_digest: Digest
    purpose: ArtifactUsePurpose
    downstream_request_ref: str
    downstream_request_digest: Digest
    created_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class ArtifactReadProtection:
    protection_id: StableId
    package_id: StableId
    package_digest: Digest
    closure_id: StableId
    closure_digest: Digest
    mode: ArtifactReadProtectionMode
    guard_required: bool
    issued_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class AuthorizedArtifactRead:
    package: ArtifactReadPackage
    closure: ArtifactReadClosure
    protection: ArtifactReadProtection
    operation_results: tuple[SourceOperationResult, ...]

    @property
    def artifacts(self) -> tuple[SourceArtifact, ...]:
        values: list[SourceArtifact] = []
        for result in self.operation_results:
            observation = result.observation
            assert observation is not None
            values.extend(observation.artifacts)
        return tuple(values)

    def replay(
        self,
        *,
        operation_id: StableId,
        expected_intent_digest: Digest,
    ) -> SourceOperationResult:
        """Replay only an Operation carried by this exact authorized Package."""

        _typed(operation_id, StableId, "Source Operation ID")
        _typed(expected_intent_digest, Digest, "Source Operation intent digest")
        for result in self.operation_results:
            if result.operation_id != operation_id:
                continue
            if result.intent_digest != expected_intent_digest:
                _inconsistent(
                    "ARTIFACT_READ_INTENT_MISMATCH",
                    "authorized Artifact Read intent differs from replay request",
                    operation_id=operation_id.value,
                )
            return result
        raise DomainError(
            ErrorCode.CONTROL_STATE_DENIED,
            "Source Operation is outside the authorized Artifact Read Package",
            {"reason_code": "ARTIFACT_READ_OPERATION_OUTSIDE_PACKAGE"},
        )


@dataclass(frozen=True, slots=True)
class ArtifactUseConfirmation:
    confirmation_id: StableId
    downstream_use_digest: Digest
    use_identity_digest: Digest
    request_digest: Digest
    package_id: StableId
    package_digest: Digest
    closure_id: StableId
    closure_digest: Digest
    protection_id: StableId
    protection_digest: Digest
    purpose: ArtifactUsePurpose
    downstream_request_ref: str
    downstream_request_digest: Digest
    downstream_candidate_ref: str
    downstream_candidate_digest: Digest
    confirmed_at: datetime
    digest: Digest


class ArtifactUseAuthorityRepository(Protocol):
    def save_read_authority(
        self,
        *,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        operation_references: tuple[ArtifactReadOperationReference, ...],
        closure_id: StableId,
        closure_digest: Digest,
        purpose: ArtifactUsePurpose,
        downstream_request_ref: str,
        downstream_request_digest: Digest,
        protection_mode: ArtifactReadProtectionMode,
        occurred_at: datetime,
    ) -> tuple[ArtifactReadPackage, ArtifactReadProtection]: ...

    def get_read_authority(
        self, package_id: StableId
    ) -> tuple[ArtifactReadPackage, ArtifactReadProtection]: ...

    def save_confirmation(
        self,
        *,
        idempotency_key: IdempotencyKey,
        downstream_use_digest: Digest,
        use_identity_digest: Digest,
        request_digest: Digest,
        package: ArtifactReadPackage,
        closure: ArtifactReadClosure,
        protection: ArtifactReadProtection,
        downstream_candidate_ref: str,
        downstream_candidate_digest: Digest,
        occurred_at: datetime,
    ) -> ArtifactUseConfirmation: ...

    def get_confirmation(
        self, confirmation_id: StableId
    ) -> ArtifactUseConfirmation: ...


class ArtifactUseAuthorityService:
    """Replay-only Source authority for cross-module persistent Artifact use."""

    def __init__(
        self,
        repository: ArtifactUseAuthorityRepository,
        replay: SourceOperationCurrentAuthorizedReplayPort,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._replay = replay
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def open_read_package(
        self,
        *,
        idempotency_key: IdempotencyKey,
        operation_references: Sequence[ArtifactReadOperationReference],
        purpose: ArtifactUsePurpose,
        downstream_request_ref: str,
        downstream_request_digest: Digest,
        protection_mode: ArtifactReadProtectionMode,
        scope_assertion: ScopeStateAssertion,
    ) -> AuthorizedArtifactRead:
        _typed(idempotency_key, IdempotencyKey, "read Package idempotency key")
        _typed(purpose, ArtifactUsePurpose, "Artifact use purpose")
        _typed(downstream_request_digest, Digest, "downstream request digest")
        _typed(scope_assertion, ScopeStateAssertion, "Scope state assertion")
        _typed(
            protection_mode,
            ArtifactReadProtectionMode,
            "Artifact Read Protection mode",
        )
        request_ref = _text(downstream_request_ref, "downstream request reference")
        references = _references(operation_references)
        results, closure = self._replay_closure(references, scope_assertion)
        request_digest = artifact_read_request_digest(
            idempotency_key=idempotency_key,
            operation_references=references,
            closure_id=closure.closure_id,
            closure_digest=closure.digest,
            purpose=purpose,
            downstream_request_ref=request_ref,
            downstream_request_digest=downstream_request_digest,
            protection_mode=protection_mode,
        )
        package, protection = self._repository.save_read_authority(
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            operation_references=references,
            closure_id=closure.closure_id,
            closure_digest=closure.digest,
            purpose=purpose,
            downstream_request_ref=request_ref,
            downstream_request_digest=downstream_request_digest,
            protection_mode=protection_mode,
            occurred_at=self._now(),
        )
        _match_read_authority(
            package,
            closure,
            protection,
            request_digest=request_digest,
            references=references,
            purpose=purpose,
            request_ref=request_ref,
            downstream_request_digest=downstream_request_digest,
            protection_mode=protection_mode,
        )
        return AuthorizedArtifactRead(package, closure, protection, results)

    def reopen_authorized_read(
        self,
        *,
        package_id: StableId,
        expected_package_digest: Digest,
        closure_id: StableId,
        expected_closure_digest: Digest,
        protection_id: StableId,
        expected_protection_digest: Digest,
        purpose: ArtifactUsePurpose,
        downstream_request_ref: str,
        downstream_request_digest: Digest,
        scope_assertion: ScopeStateAssertion,
    ) -> AuthorizedArtifactRead:
        """Issue a fresh package-bounded replay capability.

        Persisted Package and Protection identity is authenticated before any
        Artifact payload is replayed.  A historical confirmation is therefore
        never treated as current read permission.
        """

        for value, expected, label in (
            (package_id, StableId, "Artifact Read Package ID"),
            (expected_package_digest, Digest, "Artifact Read Package digest"),
            (closure_id, StableId, "Artifact Read Closure ID"),
            (expected_closure_digest, Digest, "Artifact Read Closure digest"),
            (protection_id, StableId, "Artifact Read Protection ID"),
            (expected_protection_digest, Digest, "Artifact Read Protection digest"),
            (purpose, ArtifactUsePurpose, "Artifact use purpose"),
            (downstream_request_digest, Digest, "downstream request digest"),
            (scope_assertion, ScopeStateAssertion, "Scope state assertion"),
        ):
            _typed(value, expected, label)
        request_ref = _text(downstream_request_ref, "downstream request reference")

        package, protection = self._repository.get_read_authority(package_id)
        if (
            package.package_id != package_id
            or package.digest != expected_package_digest
            or artifact_read_package_digest(package) != package.digest
            or package.closure_id != closure_id
            or package.closure_digest != expected_closure_digest
            or package.purpose is not purpose
            or package.downstream_request_ref != request_ref
            or package.downstream_request_digest != downstream_request_digest
            or protection.protection_id != protection_id
            or protection.digest != expected_protection_digest
            or artifact_read_protection_digest(protection) != protection.digest
            or protection.package_id != package.package_id
            or protection.package_digest != package.digest
            or protection.closure_id != closure_id
            or protection.closure_digest != expected_closure_digest
            or protection.mode is not ArtifactReadProtectionMode.NO_EVICTION
            or protection.guard_required
        ):
            _inconsistent(
                "ARTIFACT_READ_REOPEN_AUTHORITY_MISMATCH",
                "Artifact Read Package cannot be reopened under the requested authority",
                package_id=package_id.value,
            )

        results, current_closure = self._replay_closure(
            package.operation_references,
            scope_assertion,
        )
        if (
            current_closure.closure_id != closure_id
            or current_closure.digest != expected_closure_digest
        ):
            _inconsistent(
                "ARTIFACT_READ_REOPEN_CLOSURE_MISMATCH",
                "current Artifact closure differs from the protected Read Package",
                package_id=package_id.value,
            )
        return AuthorizedArtifactRead(
            package,
            current_closure,
            protection,
            results,
        )

    def confirm_persistent_use(
        self,
        *,
        idempotency_key: IdempotencyKey,
        package_id: StableId,
        expected_package_digest: Digest,
        closure_id: StableId,
        expected_closure_digest: Digest,
        protection_id: StableId,
        expected_protection_digest: Digest,
        purpose: ArtifactUsePurpose,
        downstream_request_ref: str,
        downstream_request_digest: Digest,
        downstream_candidate_ref: str,
        downstream_candidate_digest: Digest,
        scope_assertion: ScopeStateAssertion,
    ) -> ArtifactUseConfirmation:
        """Revalidate current read authority and confirm one exact Candidate use."""

        _typed(idempotency_key, IdempotencyKey, "use idempotency key")
        for value, expected, label in (
            (package_id, StableId, "Artifact Read Package ID"),
            (expected_package_digest, Digest, "Artifact Read Package digest"),
            (closure_id, StableId, "Artifact Read Closure ID"),
            (expected_closure_digest, Digest, "Artifact Read Closure digest"),
            (protection_id, StableId, "Artifact Read Protection ID"),
            (expected_protection_digest, Digest, "Artifact Read Protection digest"),
            (purpose, ArtifactUsePurpose, "Artifact use purpose"),
            (downstream_request_digest, Digest, "downstream request digest"),
            (downstream_candidate_digest, Digest, "downstream Candidate digest"),
            (scope_assertion, ScopeStateAssertion, "Scope state assertion"),
        ):
            _typed(value, expected, label)
        request_ref = _text(downstream_request_ref, "downstream request reference")
        candidate_ref = _text(
            downstream_candidate_ref, "downstream Candidate reference"
        )
        package, protection = self._repository.get_read_authority(package_id)
        _, current_closure = self._replay_closure(
            package.operation_references,
            scope_assertion,
        )
        if (
            package.digest != expected_package_digest
            or current_closure.closure_id != closure_id
            or current_closure.digest != expected_closure_digest
            or package.closure_id != current_closure.closure_id
            or package.closure_digest != current_closure.digest
            or protection.protection_id != protection_id
            or protection.digest != expected_protection_digest
            or protection.package_id != package.package_id
            or protection.package_digest != package.digest
            or protection.closure_id != current_closure.closure_id
            or protection.closure_digest != current_closure.digest
            or protection.mode is not ArtifactReadProtectionMode.NO_EVICTION
            or protection.guard_required
            or package.purpose is not purpose
            or package.downstream_request_ref != request_ref
            or package.downstream_request_digest != downstream_request_digest
        ):
            _inconsistent(
                "ARTIFACT_USE_BINDING_MISMATCH",
                "Artifact use confirmation does not match current exact read authority",
                package_id=package.package_id.value,
            )

        downstream_use_digest = artifact_downstream_use_digest(
            purpose=purpose,
            downstream_request_ref=request_ref,
            downstream_request_digest=downstream_request_digest,
            downstream_candidate_ref=candidate_ref,
            downstream_candidate_digest=downstream_candidate_digest,
        )
        use_identity_digest = artifact_use_identity_digest(
            package=package,
            closure=current_closure,
            protection=protection,
            downstream_use_digest=downstream_use_digest,
        )
        request_digest = artifact_use_request_digest(
            idempotency_key=idempotency_key,
            use_identity_digest=use_identity_digest,
        )
        confirmation = self._repository.save_confirmation(
            idempotency_key=idempotency_key,
            downstream_use_digest=downstream_use_digest,
            use_identity_digest=use_identity_digest,
            request_digest=request_digest,
            package=package,
            closure=current_closure,
            protection=protection,
            downstream_candidate_ref=candidate_ref,
            downstream_candidate_digest=downstream_candidate_digest,
            occurred_at=self._now(),
        )
        if (
            confirmation.downstream_use_digest != downstream_use_digest
            or confirmation.use_identity_digest != use_identity_digest
            or confirmation.request_digest != request_digest
            or confirmation.package_id != package.package_id
            or confirmation.package_digest != package.digest
            or confirmation.closure_id != current_closure.closure_id
            or confirmation.closure_digest != current_closure.digest
            or confirmation.protection_id != protection.protection_id
            or confirmation.protection_digest != protection.digest
            or confirmation.purpose is not purpose
            or confirmation.downstream_request_ref != request_ref
            or confirmation.downstream_request_digest != downstream_request_digest
            or confirmation.downstream_candidate_ref != candidate_ref
            or confirmation.downstream_candidate_digest
            != downstream_candidate_digest
        ):
            _inconsistent(
                "ARTIFACT_USE_CONFIRMATION_MISMATCH",
                "persisted Artifact use Confirmation differs from its request",
            )
        return confirmation

    def get_confirmation(
        self, confirmation_id: StableId
    ) -> ArtifactUseConfirmation:
        _typed(confirmation_id, StableId, "Artifact use Confirmation ID")
        return self._repository.get_confirmation(confirmation_id)

    def verify_structure_candidate_use(
        self,
        *,
        confirmation_id: StableId,
        expected_confirmation_digest: Digest,
        candidate_ref: str,
        candidate_digest: Digest,
    ) -> None:
        """Verify a Structure proof by owner-read, without replaying payload.

        This is the structural implementation of the Knowledge-side proof port.
        Artifact payload access remains confined to ``open``/``reopen``; an
        Admission or Publisher can only authenticate the persisted proof and
        its exact downstream candidate binding.
        """

        _typed(confirmation_id, StableId, "Artifact use Confirmation ID")
        _typed(
            expected_confirmation_digest,
            Digest,
            "Artifact use Confirmation digest",
        )
        normalized_candidate_ref = _text(
            candidate_ref, "downstream Candidate reference"
        )
        _typed(candidate_digest, Digest, "downstream Candidate digest")
        confirmation = self.get_confirmation(confirmation_id)
        if (
            confirmation.confirmation_id != confirmation_id
            or confirmation.digest != expected_confirmation_digest
            or confirmation.downstream_candidate_ref != normalized_candidate_ref
            or confirmation.downstream_candidate_digest != candidate_digest
        ):
            _inconsistent(
                "ARTIFACT_USE_STRUCTURE_PROOF_MISMATCH",
                "persisted Artifact use Confirmation does not authorize the exact Structure candidate",
                confirmation_id=confirmation_id.value,
            )

    def _replay_closure(
        self,
        references: tuple[ArtifactReadOperationReference, ...],
        scope_assertion: ScopeStateAssertion,
    ) -> tuple[tuple[SourceOperationResult, ...], ArtifactReadClosure]:
        results: list[SourceOperationResult] = []
        operations: list[ArtifactReadOperationClosure] = []
        seen_artifacts: set[StableId] = set()
        for reference in references:
            result = self._replay.replay(
                operation_id=reference.operation_id,
                expected_intent_digest=reference.intent_digest,
                scope_assertion=scope_assertion,
            )
            _validate_result(reference, result)
            observation = result.observation
            assert observation is not None
            artifact_refs = tuple(
                ArtifactReadArtifactReference(
                    artifact.artifact_id,
                    artifact.identity_digest,
                    artifact.content_digest,
                )
                for artifact in observation.artifacts
            )
            for artifact in artifact_refs:
                if artifact.artifact_id in seen_artifacts:
                    _inconsistent(
                        "ARTIFACT_READ_CLOSURE_DUPLICATE_ARTIFACT",
                        "Artifact Read Closure repeats an Artifact identity",
                        artifact_id=artifact.artifact_id.value,
                    )
                seen_artifacts.add(artifact.artifact_id)
            operations.append(
                ArtifactReadOperationClosure(
                    operation_id=result.operation_id,
                    revision=result.revision,
                    status=result.status,
                    intent_digest=result.intent_digest,
                    result_digest=result.digest,
                    observation_id=observation.observation_id,
                    observation_digest=observation.digest,
                    source_context_id=observation.source_context.context_id,
                    source_context_digest=observation.source_context.digest,
                    artifacts=artifact_refs,
                )
            )
            results.append(result)
        closure_operations = tuple(operations)
        closure_digest = artifact_read_closure_digest(closure_operations)
        closure = ArtifactReadClosure(
            StableId(
                "artifact_read_closure_"
                + closure_digest.value.removeprefix("sha256:")[-32:]
            ),
            closure_operations,
            closure_digest,
        )
        return tuple(results), closure

    def _now(self) -> datetime:
        value = self._clock()
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            _invalid(
                "ARTIFACT_AUTHORITY_TIME_INVALID",
                "Artifact authority clock must return a timezone-aware datetime",
            )
        return value.astimezone(timezone.utc)


def _validate_result(
    reference: ArtifactReadOperationReference,
    result: SourceOperationResult,
) -> None:
    if not isinstance(result, SourceOperationResult):
        _inconsistent(
            "SOURCE_OPERATION_REPLAY_TYPE_INVALID",
            "Source replay returned an invalid Result type",
        )
    if (
        result.operation_id != reference.operation_id
        or result.intent_digest != reference.intent_digest
        or result.digest != reference.result_digest
    ):
        _inconsistent(
            "SOURCE_OPERATION_REPLAY_RESULT_MISMATCH",
            "Source replay Result differs from the exact requested identity/digests",
            operation_id=reference.operation_id.value,
        )
    if result.status not in {
        SourceOperationStatus.COMPLETED,
        SourceOperationStatus.PARTIAL,
    } or result.observation is None:
        _inconsistent(
            "SOURCE_OPERATION_REPLAY_NOT_USABLE",
            "Artifact use requires a persisted usable Source Result",
            operation_id=reference.operation_id.value,
        )
    if result.failure_code is not None or result.failure_message is not None:
        _inconsistent(
            "SOURCE_OPERATION_REPLAY_FAILURE_PRESENT",
            "usable Source Result cannot carry a failure",
            operation_id=reference.operation_id.value,
        )
    _aware(result.created_at, "Source Operation created_at")
    _aware(result.revised_at, "Source Operation revised_at")
    observation = result.observation
    expected_result_digest = digest_of(
        {
            "operation_id": result.operation_id.value,
            "revision": result.revision.value,
            "status": result.status.value,
            "intent_digest": result.intent_digest.value,
            "observation_id": observation.observation_id.value,
            "failure_code": None,
            "occurred_at": result.revised_at,
        }
    )
    if result.created_at > result.revised_at or result.digest != expected_result_digest:
        _inconsistent(
            "SOURCE_OPERATION_RESULT_DIGEST_INVALID",
            "Source Operation Result is not self-consistent",
            operation_id=result.operation_id.value,
        )
    _validate_observation(result.operation_id, observation)
    partial = observation.has_more or any(
        artifact.truncated for artifact in observation.artifacts
    )
    if (result.status is SourceOperationStatus.PARTIAL) != partial:
        _inconsistent(
            "SOURCE_OPERATION_COMPLETENESS_MISMATCH",
            "Source Result status disagrees with Observation completeness",
            operation_id=result.operation_id.value,
        )


def _validate_observation(
    operation_id: StableId,
    observation: SourceObservation,
) -> None:
    context = observation.source_context
    if observation.operation_id != operation_id or not observation.artifacts:
        _inconsistent(
            "SOURCE_OBSERVATION_BINDING_INVALID",
            "Source Observation is missing or bound to another Operation",
            operation_id=operation_id.value,
        )
    _aware(observation.observed_at, "Source Observation observed_at")
    _validate_context(context)
    if context.observed_at != observation.observed_at:
        _inconsistent(
            "SOURCE_OBSERVATION_CONTEXT_MISMATCH",
            "Source Observation and Context timestamps differ",
            observation_id=observation.observation_id.value,
        )
    artifact_ids = tuple(item.artifact_id for item in observation.artifacts)
    if len(set(artifact_ids)) != len(artifact_ids):
        _inconsistent(
            "SOURCE_OBSERVATION_ARTIFACT_DUPLICATE",
            "Source Observation repeats an Artifact identity",
            observation_id=observation.observation_id.value,
        )
    digest_coverage = _source_digest_coverage(
        observation.tool, observation.coverage
    )
    for artifact in observation.artifacts:
        _validate_artifact(artifact, context, observation.tool, digest_coverage)
    if (
        observation.byte_count
        != sum(len(item.payload) for item in observation.artifacts)
        or type(observation.item_count) is not int
        or observation.item_count < 0
        or observation.has_more != (observation.next_cursor is not None)
    ):
        _inconsistent(
            "SOURCE_OBSERVATION_COMPLETENESS_INVALID",
            "Source Observation counts or cursor are inconsistent",
            observation_id=observation.observation_id.value,
        )
    expected = digest_of(
        {
            "observation_id": observation.observation_id.value,
            "operation_id": operation_id.value,
            "tool": observation.tool.value,
            "context_digest": context.digest.value,
            "artifacts": tuple(
                (item.artifact_id.value, item.content_digest.value)
                for item in observation.artifacts
            ),
            "item_count": observation.item_count,
            "byte_count": observation.byte_count,
            "next_cursor": observation.next_cursor,
            "has_more": observation.has_more,
            "coverage": digest_coverage,
            "observed_at": observation.observed_at,
        }
    )
    if observation.digest != expected:
        _inconsistent(
            "SOURCE_OBSERVATION_DIGEST_INVALID",
            "Source Observation digest is not self-consistent",
            observation_id=observation.observation_id.value,
        )


def _validate_context(context: SourceContext) -> None:
    _aware(context.observed_at, "Source Context observed_at")
    expected = digest_of(
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
    if context.digest != expected:
        _inconsistent(
            "SOURCE_CONTEXT_DIGEST_INVALID",
            "Source Context digest is not self-consistent",
            context_id=context.context_id.value,
        )


def _validate_artifact(
    artifact: SourceArtifact,
    context: SourceContext,
    tool: SourceTool,
    coverage: tuple[tuple[str, str], ...],
) -> None:
    if (
        artifact.source_context_id != context.context_id
        or artifact.source_id != context.source_id
        or artifact.source_revision != context.source_revision
        or artifact.content_digest != content_digest(artifact.payload)
        or artifact.truncated != (artifact.truncation_offset is not None)
    ):
        _inconsistent(
            "SOURCE_ARTIFACT_CONTENT_OR_CONTEXT_INVALID",
            "Source Artifact content or Context binding is invalid",
            artifact_id=artifact.artifact_id.value,
        )
    identity = digest_of(
        {
            "source_id": artifact.source_id.value,
            "source_revision": artifact.source_revision.value,
            "source_context_id": artifact.source_context_id.value,
            "source_native_identity": artifact.source_native_identity,
            "artifact_kind": artifact.artifact_kind,
            "payload_schema_version": artifact.payload_schema_version,
            "provider_contract": "LOCAL_GIT@0.1.0",
            "tool": tool.value,
            "coverage": coverage,
            "identity_strategy": "local-git-artifact@2",
        }
    )
    artifact_id = StableId(
        "source_artifact_" + identity.value.removeprefix("sha256:")[-32:]
    )
    if artifact.identity_digest != identity or artifact.artifact_id != artifact_id:
        _inconsistent(
            "SOURCE_ARTIFACT_IDENTITY_INVALID",
            "Source Artifact identity is not self-consistent",
            artifact_id=artifact.artifact_id.value,
        )


def _source_digest_coverage(
    tool: SourceTool,
    coverage: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    try:
        mapping = dict(coverage)
    except (TypeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Source Observation Coverage cannot be decoded",
            {"reason_code": "SOURCE_OBSERVATION_COVERAGE_INVALID"},
        ) from exc
    if len(mapping) != len(coverage) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in coverage
    ):
        _inconsistent(
            "SOURCE_OBSERVATION_COVERAGE_INVALID",
            "Source Observation Coverage must contain unique text fields",
        )
    if tool in {SourceTool.LIST, SourceTool.TREE, SourceTool.SEARCH}:
        keys = ("cursor_start", "cursor_end", "matched_total", "revision")
    elif tool is SourceTool.READ:
        keys = ("path", "range", "revision")
    elif tool is SourceTool.COMPARE:
        keys = ("base", "target", "paths")
    else:
        _inconsistent(
            "SOURCE_OBSERVATION_TOOL_UNSUPPORTED",
            "Artifact authority does not implement this Source Tool contract",
            tool=tool.value,
        )
    if set(mapping) != set(keys):
        _inconsistent(
            "SOURCE_OBSERVATION_COVERAGE_SHAPE_INVALID",
            "Source Observation Coverage does not match its Tool contract",
            tool=tool.value,
        )
    return tuple((key, mapping[key]) for key in keys)


def _references(
    values: Sequence[ArtifactReadOperationReference],
) -> tuple[ArtifactReadOperationReference, ...]:
    if isinstance(values, (str, bytes)):
        _invalid(
            "ARTIFACT_READ_OPERATION_REFERENCES_INVALID",
            "Artifact Read Package requires typed Operation references",
        )
    references = tuple(values)
    if not references or any(
        not isinstance(item, ArtifactReadOperationReference) for item in references
    ):
        _invalid(
            "ARTIFACT_READ_OPERATION_REFERENCES_INVALID",
            "Artifact Read Package requires typed Operation references",
        )
    if len({item.operation_id for item in references}) != len(references):
        _invalid(
            "ARTIFACT_READ_OPERATION_REFERENCE_DUPLICATE",
            "Artifact Read Package cannot repeat a Source Operation",
        )
    return references


def _match_read_authority(
    package: ArtifactReadPackage,
    closure: ArtifactReadClosure,
    protection: ArtifactReadProtection,
    *,
    request_digest: Digest,
    references: tuple[ArtifactReadOperationReference, ...],
    purpose: ArtifactUsePurpose,
    request_ref: str,
    downstream_request_digest: Digest,
    protection_mode: ArtifactReadProtectionMode,
) -> None:
    if (
        package.request_digest != request_digest
        or package.operation_references != references
        or package.closure_id != closure.closure_id
        or package.closure_digest != closure.digest
        or package.purpose is not purpose
        or package.downstream_request_ref != request_ref
        or package.downstream_request_digest != downstream_request_digest
        or protection.package_id != package.package_id
        or protection.package_digest != package.digest
        or protection.closure_id != closure.closure_id
        or protection.closure_digest != closure.digest
        or protection.mode is not protection_mode
        or protection.guard_required
    ):
        _inconsistent(
            "ARTIFACT_READ_AUTHORITY_MISMATCH",
            "persisted Artifact Read authority differs from its request",
        )


def artifact_read_closure_digest(
    operations: tuple[ArtifactReadOperationClosure, ...],
) -> Digest:
    return digest_of(["ARTIFACT_READ_CLOSURE@1", {"operations": operations}])


def artifact_read_request_digest(
    *,
    idempotency_key: IdempotencyKey,
    operation_references: tuple[ArtifactReadOperationReference, ...],
    closure_id: StableId,
    closure_digest: Digest,
    purpose: ArtifactUsePurpose,
    downstream_request_ref: str,
    downstream_request_digest: Digest,
    protection_mode: ArtifactReadProtectionMode,
) -> Digest:
    return digest_of(
        [
            "OPEN_ARTIFACT_READ_PACKAGE@1",
            {
                "idempotency_key": idempotency_key.value,
                "operation_references": operation_references,
                "closure_id": closure_id.value,
                "closure_digest": closure_digest.value,
                "purpose": purpose.value,
                "downstream_request_ref": downstream_request_ref,
                "downstream_request_digest": downstream_request_digest.value,
                "protection_mode": protection_mode.value,
            },
        ]
    )


def artifact_read_package_digest(
    package: ArtifactReadPackage,
) -> Digest:
    return digest_of(
        [
            "ARTIFACT_READ_PACKAGE@1",
            {
                "package_id": package.package_id.value,
                "request_digest": package.request_digest.value,
                "operation_references": package.operation_references,
                "closure_id": package.closure_id.value,
                "closure_digest": package.closure_digest.value,
                "purpose": package.purpose.value,
                "downstream_request_ref": package.downstream_request_ref,
                "downstream_request_digest": package.downstream_request_digest.value,
                "created_at": package.created_at,
            },
        ]
    )


def artifact_read_protection_digest(
    protection: ArtifactReadProtection,
) -> Digest:
    return digest_of(
        [
            "ARTIFACT_READ_PROTECTION@1",
            {
                "protection_id": protection.protection_id.value,
                "package_id": protection.package_id.value,
                "package_digest": protection.package_digest.value,
                "closure_id": protection.closure_id.value,
                "closure_digest": protection.closure_digest.value,
                "mode": protection.mode.value,
                "guard_required": protection.guard_required,
                "issued_at": protection.issued_at,
            },
        ]
    )


def artifact_downstream_use_digest(
    *,
    purpose: ArtifactUsePurpose,
    downstream_request_ref: str,
    downstream_request_digest: Digest,
    downstream_candidate_ref: str,
    downstream_candidate_digest: Digest,
) -> Digest:
    return digest_of(
        [
            "ARTIFACT_DOWNSTREAM_PERSISTENT_USE@1",
            {
                "purpose": purpose.value,
                "downstream_request_ref": downstream_request_ref,
                "downstream_request_digest": downstream_request_digest.value,
                "downstream_candidate_ref": downstream_candidate_ref,
                "downstream_candidate_digest": downstream_candidate_digest.value,
            },
        ]
    )


def artifact_use_identity_digest(
    *,
    package: ArtifactReadPackage,
    closure: ArtifactReadClosure,
    protection: ArtifactReadProtection,
    downstream_use_digest: Digest,
) -> Digest:
    return digest_of(
        [
            "ARTIFACT_PERSISTENT_USE_IDENTITY@1",
            {
                "package_id": package.package_id.value,
                "package_digest": package.digest.value,
                "closure_id": closure.closure_id.value,
                "closure_digest": closure.digest.value,
                "protection_id": protection.protection_id.value,
                "protection_digest": protection.digest.value,
                "downstream_use_digest": downstream_use_digest.value,
            },
        ]
    )


def artifact_use_request_digest(
    *, idempotency_key: IdempotencyKey, use_identity_digest: Digest
) -> Digest:
    return digest_of(
        [
            "CONFIRM_ARTIFACT_PERSISTENT_USE@1",
            {
                "idempotency_key": idempotency_key.value,
                "use_identity_digest": use_identity_digest.value,
            },
        ]
    )


def artifact_use_confirmation_digest(
    confirmation: ArtifactUseConfirmation,
) -> Digest:
    return digest_of(
        [
            "ARTIFACT_USE_CONFIRMATION@1",
            {
                field: value
                for field, value in (
                    ("confirmation_id", confirmation.confirmation_id.value),
                    ("downstream_use_digest", confirmation.downstream_use_digest.value),
                    ("use_identity_digest", confirmation.use_identity_digest.value),
                    ("request_digest", confirmation.request_digest.value),
                    ("package_id", confirmation.package_id.value),
                    ("package_digest", confirmation.package_digest.value),
                    ("closure_id", confirmation.closure_id.value),
                    ("closure_digest", confirmation.closure_digest.value),
                    ("protection_id", confirmation.protection_id.value),
                    ("protection_digest", confirmation.protection_digest.value),
                    ("purpose", confirmation.purpose.value),
                    ("downstream_request_ref", confirmation.downstream_request_ref),
                    (
                        "downstream_request_digest",
                        confirmation.downstream_request_digest.value,
                    ),
                    ("downstream_candidate_ref", confirmation.downstream_candidate_ref),
                    (
                        "downstream_candidate_digest",
                        confirmation.downstream_candidate_digest.value,
                    ),
                    ("confirmed_at", confirmation.confirmed_at),
                )
            },
        ]
    )


def _typed(value: object, expected: type, label: str) -> None:
    if not isinstance(value, expected):
        _invalid(
            "ARTIFACT_AUTHORITY_TYPE_INVALID",
            f"{label} must be a typed {expected.__name__}",
        )


def _text(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value.encode("utf-8")) > 512
    ):
        _invalid(
            "ARTIFACT_AUTHORITY_TEXT_INVALID",
            f"{label} must be bounded non-empty canonical text",
        )
    return value


def _aware(value: datetime, label: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _inconsistent(
            "ARTIFACT_AUTHORITY_TIME_INVALID",
            f"{label} must be timezone-aware",
        )


def _invalid(reason_code: str, message: str) -> None:
    raise DomainError(ErrorCode.INVALID_ARGUMENT, message, {"reason_code": reason_code})


def _inconsistent(
    reason_code: str,
    message: str,
    **details: str | int,
) -> None:
    raise DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        message,
        {"reason_code": reason_code, **details},
    )
