"""Atomic publication contract for typed Structure knowledge.

Mechanical closure types live in :mod:`structure`; the independent persisted
Admission authority lives in :mod:`structure_authority`.  This module adds the
separate Application acceptance, exact Snapshot manifest, idempotent request,
and repository boundary needed to publish that closure.
"""

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

from .structure import (
    CoverageMember,
    PublicationMode,
    StructureEvidence,
    StructureKnowledgeBatch,
)
from .structure_authority import (
    StructureAdmissionDecision,
    StructureAdmissionOutcome,
    StructureArtifactUseProofVerifier,
    StructureSchemaAdoptionMode,
    StructureVerifierAuthority,
    structure_batch_digest,
    structure_closure_digest,
    structure_read_set_digest,
    structure_upstream_digest,
)
from .scope import AssertionOutcome, KnowledgeScopeService, ScopePurpose, ScopeType


class ApplicationAcceptanceDecision(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class StructureApplicationAcceptance:
    acceptance_ref: str
    decision: ApplicationAcceptanceDecision
    batch_digest: Digest
    report_digest: Digest
    digest: Digest

    @classmethod
    def decide(
        cls,
        *,
        acceptance_ref: str,
        decision: ApplicationAcceptanceDecision | str,
        batch_digest: Digest,
        report_digest: Digest,
    ) -> "StructureApplicationAcceptance":
        normalized_ref = _text(acceptance_ref, "Application acceptance ref")
        if not isinstance(batch_digest, Digest) or not isinstance(
            report_digest, Digest
        ):
            raise _invalid(
                "APPLICATION_ACCEPTANCE_DIGEST_INVALID",
                "Application acceptance requires typed batch and report digests",
            )
        try:
            normalized_decision = (
                decision
                if isinstance(decision, ApplicationAcceptanceDecision)
                else ApplicationAcceptanceDecision(decision)
            )
        except (TypeError, ValueError) as exc:
            raise _invalid(
                "APPLICATION_ACCEPTANCE_DECISION_INVALID",
                "Application acceptance decision is invalid",
            ) from exc
        core = {
            "acceptance_ref": normalized_ref,
            "decision": normalized_decision.value,
            "batch_digest": batch_digest.value,
            "report_digest": report_digest.value,
        }
        return cls(
            acceptance_ref=normalized_ref,
            decision=normalized_decision,
            batch_digest=batch_digest,
            report_digest=report_digest,
            digest=digest_of(["STRUCTURE_APPLICATION_ACCEPTANCE@1", core]),
        )

    @classmethod
    def pass_for(
        cls,
        batch: StructureKnowledgeBatch,
        *,
        acceptance_ref: str,
        report_digest: Digest,
    ) -> "StructureApplicationAcceptance":
        return cls.decide(
            acceptance_ref=acceptance_ref,
            decision=ApplicationAcceptanceDecision.PASS,
            batch_digest=structure_batch_digest(batch),
            report_digest=report_digest,
        )

    def require_valid(self) -> None:
        expected = self.decide(
            acceptance_ref=self.acceptance_ref,
            decision=self.decision,
            batch_digest=self.batch_digest,
            report_digest=self.report_digest,
        )
        if expected.digest != self.digest:
            raise _invalid(
                "APPLICATION_ACCEPTANCE_DIGEST_MISMATCH",
                "Application acceptance digest is not canonical",
            )


@dataclass(frozen=True, slots=True)
class SnapshotCoverage:
    coverage_root_id: StableId
    coverage_state_id: StableId
    coverage_state_digest: Digest

    def __post_init__(self) -> None:
        if self.coverage_root_id.kind != "coverage_root":
            raise _invalid(
                "SNAPSHOT_COVERAGE_ROOT_KIND_INVALID",
                "Snapshot Coverage Root ID has the wrong kind",
            )
        if self.coverage_state_id.kind != "coverage_state":
            raise _invalid(
                "SNAPSHOT_COVERAGE_STATE_KIND_INVALID",
                "Snapshot Coverage State ID has the wrong kind",
            )


@dataclass(frozen=True, slots=True)
class SnapshotUpstreamEntity:
    upstream_snapshot_id: StableId
    entity_root_id: StableId
    entity_state_id: StableId
    entity_state_digest: Digest

    def __post_init__(self) -> None:
        if self.upstream_snapshot_id.kind != "structure_snapshot":
            raise _invalid(
                "UPSTREAM_SNAPSHOT_KIND_INVALID",
                "exact upstream Snapshot ID has the wrong kind",
            )
        if (
            self.entity_root_id.kind != "entity_root"
            or self.entity_state_id.kind != "entity_state"
        ):
            raise _invalid(
                "UPSTREAM_ENTITY_KIND_INVALID",
                "exact upstream Entity Root/State ID has the wrong kind",
            )


@dataclass(frozen=True, slots=True)
class StructureEvidenceMetadata:
    """Evidence identity and locator projection with no observation payload."""

    evidence_id: StableId
    artifact_id: StableId
    source_context_id: StableId
    byte_start: int
    byte_end: int
    locator: str
    excerpt_digest: Digest
    artifact_content_digest: Digest
    digest: Digest

    @classmethod
    def from_evidence(cls, evidence: StructureEvidence) -> "StructureEvidenceMetadata":
        evidence.require_valid_identity()
        return cls(
            evidence_id=evidence.evidence_id,
            artifact_id=evidence.artifact_id,
            source_context_id=evidence.source_context_id,
            byte_start=evidence.byte_start,
            byte_end=evidence.byte_end,
            locator=evidence.locator,
            excerpt_digest=evidence.excerpt_digest,
            artifact_content_digest=evidence.artifact_content_digest,
            digest=evidence.digest,
        )


@dataclass(frozen=True, slots=True)
class StructureSnapshot:
    snapshot_id: StableId
    scope_id: StableId
    snapshot_revision: Revision
    previous_snapshot_id: StableId | None
    schema_ref: str
    schema_digest: Digest
    schema_adoption_mode: StructureSchemaAdoptionMode
    schema_registration_digest: Digest
    schema_availability_digest: Digest
    schema_adoption_digest: Digest
    publication_mode: PublicationMode
    members: tuple[CoverageMember, ...]
    coverages: tuple[SnapshotCoverage, ...]
    upstream_entities: tuple[SnapshotUpstreamEntity, ...]
    manifest_digest: Digest
    published_at: datetime

    @classmethod
    def create(
        cls,
        *,
        snapshot_id: StableId,
        scope_id: StableId,
        snapshot_revision: Revision,
        previous_snapshot_id: StableId | None,
        schema_ref: str,
        schema_digest: Digest,
        schema_adoption_mode: StructureSchemaAdoptionMode,
        schema_registration_digest: Digest,
        schema_availability_digest: Digest,
        schema_adoption_digest: Digest,
        publication_mode: PublicationMode,
        members: tuple[CoverageMember, ...],
        coverages: tuple[SnapshotCoverage, ...],
        upstream_entities: tuple[SnapshotUpstreamEntity, ...],
        published_at: datetime,
    ) -> "StructureSnapshot":
        normalized_members = tuple(
            sorted(members, key=lambda item: (item.kind.value, item.root_id.value))
        )
        normalized_coverages = tuple(
            sorted(coverages, key=lambda item: item.coverage_root_id.value)
        )
        normalized_upstream = tuple(
            sorted(
                upstream_entities,
                key=lambda item: (
                    item.entity_root_id.value,
                    item.upstream_snapshot_id.value,
                ),
            )
        )
        manifest_digest = _snapshot_manifest_digest_values(
            snapshot_id=snapshot_id,
            scope_id=scope_id,
            snapshot_revision=snapshot_revision,
            previous_snapshot_id=previous_snapshot_id,
            schema_ref=schema_ref,
            schema_digest=schema_digest,
            schema_adoption_mode=schema_adoption_mode,
            schema_registration_digest=schema_registration_digest,
            schema_availability_digest=schema_availability_digest,
            schema_adoption_digest=schema_adoption_digest,
            publication_mode=publication_mode,
            members=normalized_members,
            coverages=normalized_coverages,
            upstream_entities=normalized_upstream,
            published_at=published_at,
        )
        return cls(
            snapshot_id=snapshot_id,
            scope_id=scope_id,
            snapshot_revision=snapshot_revision,
            previous_snapshot_id=previous_snapshot_id,
            schema_ref=schema_ref,
            schema_digest=schema_digest,
            schema_adoption_mode=schema_adoption_mode,
            schema_registration_digest=schema_registration_digest,
            schema_availability_digest=schema_availability_digest,
            schema_adoption_digest=schema_adoption_digest,
            publication_mode=publication_mode,
            members=normalized_members,
            coverages=normalized_coverages,
            upstream_entities=normalized_upstream,
            manifest_digest=manifest_digest,
            published_at=published_at,
        )

    def __post_init__(self) -> None:
        if self.snapshot_id.kind != "structure_snapshot":
            raise _invalid(
                "STRUCTURE_SNAPSHOT_ID_KIND_INVALID",
                "Structure Snapshot ID has the wrong kind",
            )
        object.__setattr__(self, "schema_ref", _text(self.schema_ref, "Schema ref"))
        for value, label in (
            (self.schema_digest, "Schema digest"),
            (self.schema_registration_digest, "Schema Registration digest"),
            (self.schema_availability_digest, "Schema Availability digest"),
            (self.schema_adoption_digest, "Schema Adoption digest"),
        ):
            if not isinstance(value, Digest):
                raise _invalid("SNAPSHOT_SCHEMA_TRACE_INVALID", f"{label} must be typed")
        if self.published_at.tzinfo is None or self.published_at.utcoffset() is None:
            raise _invalid(
                "SNAPSHOT_TIMEZONE_REQUIRED",
                "Structure Snapshot publication time must include a timezone",
            )
        try:
            normalized_adoption_mode = (
                self.schema_adoption_mode
                if isinstance(self.schema_adoption_mode, StructureSchemaAdoptionMode)
                else StructureSchemaAdoptionMode(self.schema_adoption_mode)
            )
            normalized_mode = (
                self.publication_mode
                if isinstance(self.publication_mode, PublicationMode)
                else PublicationMode(self.publication_mode)
            )
        except (TypeError, ValueError) as exc:
            raise _invalid(
                "PUBLICATION_MODE_INVALID",
                "Structure Snapshot publication mode is invalid",
            ) from exc
        object.__setattr__(self, "publication_mode", normalized_mode)
        object.__setattr__(self, "schema_adoption_mode", normalized_adoption_mode)
        if (
            (self.previous_snapshot_id is None)
            != (normalized_adoption_mode is StructureSchemaAdoptionMode.INITIAL)
        ):
            raise _invalid(
                "SCHEMA_ADOPTION_MODE_INVALID",
                "INITIAL is allowed only for the first Snapshot; later publication is UNCHANGED",
            )
        expected_members = tuple(
            sorted(
                self.members,
                key=lambda item: (item.kind.value, item.root_id.value),
            )
        )
        expected_coverages = tuple(
            sorted(self.coverages, key=lambda item: item.coverage_root_id.value)
        )
        expected_upstream = tuple(
            sorted(
                self.upstream_entities,
                key=lambda item: (
                    item.entity_root_id.value,
                    item.upstream_snapshot_id.value,
                ),
            )
        )
        if self.members != expected_members or len(
            {item.root_id for item in self.members}
        ) != len(self.members):
            raise _invalid(
                "SNAPSHOT_MEMBER_MANIFEST_INVALID",
                "Structure Snapshot members must be sorted with one State per Root",
            )
        if self.coverages != expected_coverages or len(
            {item.coverage_root_id for item in self.coverages}
        ) != len(self.coverages):
            raise _invalid(
                "SNAPSHOT_COVERAGE_MANIFEST_INVALID",
                "Structure Snapshot Coverages must be sorted and unique",
            )
        if self.upstream_entities != expected_upstream or len(
            {item.entity_root_id for item in self.upstream_entities}
        ) != len(self.upstream_entities):
            raise _invalid(
                "SNAPSHOT_UPSTREAM_MANIFEST_INVALID",
                "Structure Snapshot upstream Entity refs must be sorted and unambiguous",
            )
        if self.manifest_digest != structure_snapshot_manifest_digest(self):
            raise _invalid(
                "SNAPSHOT_MANIFEST_DIGEST_MISMATCH",
                "Structure Snapshot manifest digest is not canonical",
            )


@dataclass(frozen=True, slots=True)
class StructurePublicationReceipt:
    publication_id: StableId
    request_digest: Digest
    batch_digest: Digest
    admission_id: StableId
    admission_digest: Digest
    application_acceptance_digest: Digest
    snapshot: StructureSnapshot
    published_at: datetime
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        publication_id: StableId,
        request_digest: Digest,
        batch_digest: Digest,
        admission_id: StableId,
        admission_digest: Digest,
        application_acceptance_digest: Digest,
        snapshot: StructureSnapshot,
        published_at: datetime,
    ) -> "StructurePublicationReceipt":
        digest = _publication_receipt_digest_values(
            publication_id=publication_id,
            request_digest=request_digest,
            batch_digest=batch_digest,
            admission_id=admission_id,
            admission_digest=admission_digest,
            application_acceptance_digest=application_acceptance_digest,
            snapshot=snapshot,
            published_at=published_at,
        )
        return cls(
            publication_id=publication_id,
            request_digest=request_digest,
            batch_digest=batch_digest,
            admission_id=admission_id,
            admission_digest=admission_digest,
            application_acceptance_digest=application_acceptance_digest,
            snapshot=snapshot,
            published_at=published_at,
            digest=digest,
        )

    def __post_init__(self) -> None:
        if self.publication_id.kind != "structure_publication":
            raise _invalid(
                "STRUCTURE_PUBLICATION_ID_KIND_INVALID",
                "Structure Publication ID has the wrong kind",
            )
        if self.admission_id.kind != "structure_admission":
            raise _invalid(
                "STRUCTURE_ADMISSION_ID_INVALID",
                "Publication Receipt Admission ID has the wrong kind",
            )
        if (
            self.published_at.tzinfo is None
            or self.published_at.utcoffset() is None
            or self.published_at != self.snapshot.published_at
        ):
            raise _invalid(
                "PUBLICATION_RECEIPT_TIME_INVALID",
                "Publication Receipt time must equal its exact Snapshot time",
            )
        expected = structure_publication_receipt_digest(self)
        if self.digest != expected:
            raise _invalid(
                "PUBLICATION_RECEIPT_DIGEST_MISMATCH",
                "Structure Publication Receipt digest is not canonical",
            )


class StructureKnowledgeRepository(Protocol):
    def current_snapshot(self, scope_id: StableId) -> StructureSnapshot | None: ...

    def get_snapshot(self, snapshot_id: StableId) -> StructureSnapshot: ...

    def get_evidence(self, evidence_id: StableId) -> StructureEvidence: ...

    def get_evidence_metadata(
        self, evidence_id: StableId
    ) -> StructureEvidenceMetadata: ...

    def get_publication(
        self, publication_id: StableId
    ) -> StructurePublicationReceipt: ...

    def get_publication_by_idempotency_key(
        self, idempotency_key: IdempotencyKey
    ) -> StructurePublicationReceipt | None: ...

    def publish(
        self,
        *,
        scope_id: StableId,
        expected_scope_revision: Revision,
        expected_current_snapshot_id: StableId | None,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        batch_digest: Digest,
        admission: StructureAdmissionDecision,
        verifier_authority: StructureVerifierAuthority,
        application_acceptance: StructureApplicationAcceptance,
        batch: StructureKnowledgeBatch,
        published_at: datetime,
    ) -> StructurePublicationReceipt: ...


class StructurePublicationService:
    def __init__(
        self,
        repository: StructureKnowledgeRepository,
        scopes: KnowledgeScopeService,
        artifact_use_proofs: StructureArtifactUseProofVerifier,
        *,
        verifier_authority: StructureVerifierAuthority,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._scopes = scopes
        if not callable(
            getattr(artifact_use_proofs, "verify_structure_candidate_use", None)
        ):
            raise _invalid(
                "ARTIFACT_USE_PROOF_VERIFIER_REQUIRED",
                "Structure publication requires an Artifact-use proof verifier",
            )
        self._artifact_use_proofs = artifact_use_proofs
        if not isinstance(verifier_authority, StructureVerifierAuthority):
            raise _invalid(
                "VERIFIER_AUTHORITY_REQUIRED",
                "Structure publication requires a repository-issued verifier authority",
            )
        verifier_authority.require_valid()
        self._verifier_authority = verifier_authority
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def current_snapshot(self, scope_id: StableId) -> StructureSnapshot | None:
        return self._repository.current_snapshot(scope_id)

    def get_snapshot(self, snapshot_id: StableId) -> StructureSnapshot:
        return self._repository.get_snapshot(snapshot_id)

    def get_evidence(self, evidence_id: StableId) -> StructureEvidence:
        return self._repository.get_evidence(evidence_id)

    def get_evidence_metadata(
        self, evidence_id: StableId
    ) -> StructureEvidenceMetadata:
        return self._repository.get_evidence_metadata(evidence_id)

    def get_publication(
        self, publication_id: StableId
    ) -> StructurePublicationReceipt:
        """Re-read one committed Publication Receipt from its owner authority."""

        return self._repository.get_publication(publication_id)

    def get_publication_by_idempotency_key(
        self, idempotency_key: IdempotencyKey
    ) -> StructurePublicationReceipt | None:
        """Recover a committed receipt after an uncertain publication return."""

        return self._repository.get_publication_by_idempotency_key(
            idempotency_key
        )

    def publish(
        self,
        *,
        scope_id: StableId,
        expected_scope_revision: Revision,
        expected_current_snapshot_id: StableId | None,
        idempotency_key: IdempotencyKey,
        batch: StructureKnowledgeBatch,
        admission: StructureAdmissionDecision,
        application_acceptance: StructureApplicationAcceptance,
        caller_ref: str,
        classification: str,
    ) -> StructurePublicationReceipt:
        normalized_caller = _text(caller_ref, "caller reference")
        normalized_classification = _text(classification, "classification")
        assertion = self._scopes.read_scope_state_assertion(
            scope_id=scope_id,
            expected_revision=expected_scope_revision,
            purpose=ScopePurpose.SNAPSHOT_PUBLICATION,
            caller_ref=normalized_caller,
            request_ref=idempotency_key.value,
            classification=normalized_classification,
        )
        if (
            assertion.outcome is not AssertionOutcome.ELIGIBLE
            or assertion.scope_type is not ScopeType.SYSTEM
            or not self._scopes.validate_scope_state_assertion(assertion)
        ):
            raise DomainError(
                ErrorCode.SCOPE_ASSERTION_INVALID,
                "Structure publication requires a valid eligible Scope assertion",
                {"scope_id": scope_id.value},
            )
        # Candidate validation, persisted Admission, and Application acceptance
        # are intentionally three different gates.
        batch.require_admissible()
        if batch.coverage.root.owning_scope_id != scope_id:
            raise _invalid(
                "PUBLICATION_SCOPE_MISMATCH",
                "Structure batch Coverage does not belong to the publication Scope",
            )
        batch_digest = structure_batch_digest(batch)
        admission.require_valid()
        if admission.outcome is not StructureAdmissionOutcome.ACCEPT:
            raise _invalid(
                "ADMISSION_NOT_ACCEPT",
                "Structure publication requires an exact Admission ACCEPT",
            )
        if (
            admission.verifier_authority_id
            != self._verifier_authority.authority_id
            or admission.verifier_ref != self._verifier_authority.verifier_ref
        ):
            raise _invalid(
                "VERIFIER_AUTHORITY_MISMATCH",
                "Admission was not issued under the configured verifier authority",
            )
        admission_pairs = (
            (admission.batch_digest, batch_digest),
            (admission.closure_digest, structure_closure_digest(batch)),
            (admission.read_set_digest, structure_read_set_digest(batch)),
            (admission.scope_id, scope_id),
            (admission.expected_scope_revision, expected_scope_revision),
            (admission.expected_current_snapshot_id, expected_current_snapshot_id),
            (admission.schema_ref, batch.coverage.root.schema_ref),
            (admission.schema_digest, batch.coverage.root.schema_digest),
            (
                admission.knowledge_context_digest,
                batch.coverage.state.knowledge_context_digest,
            ),
            (admission.upstream_digest, structure_upstream_digest(batch)),
        )
        if any(actual != expected for actual, expected in admission_pairs):
            raise _invalid(
                "ADMISSION_CLOSURE_MISMATCH",
                "Admission ACCEPT is bound to another candidate closure or target",
            )
        self._artifact_use_proofs.verify_structure_candidate_use(
            confirmation_id=admission.artifact_use_confirmation_id,
            expected_confirmation_digest=admission.artifact_use_confirmation_digest,
            candidate_ref=admission.candidate_ref,
            candidate_digest=admission.candidate_digest,
        )
        application_acceptance.require_valid()
        if application_acceptance.decision is not ApplicationAcceptanceDecision.PASS:
            raise _invalid(
                "APPLICATION_ACCEPTANCE_NOT_PASS",
                "Structure publication requires an explicit Application PASS",
            )
        if application_acceptance.batch_digest != batch_digest:
            raise _invalid(
                "APPLICATION_ACCEPTANCE_BATCH_MISMATCH",
                "Application PASS is bound to a different Structure batch",
            )
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise _invalid(
                "PUBLICATION_TIMEZONE_REQUIRED",
                "Structure publication clock must return a timezone-aware value",
            )
        published_at = now.astimezone(timezone.utc)
        request_digest = structure_publication_request_digest(
            scope_id=scope_id,
            expected_scope_revision=expected_scope_revision,
            expected_current_snapshot_id=expected_current_snapshot_id,
            idempotency_key=idempotency_key,
            batch_digest=batch_digest,
            admission_digest=admission.digest,
            application_acceptance_digest=application_acceptance.digest,
            caller_ref=normalized_caller,
            classification=normalized_classification,
        )
        return self._repository.publish(
            scope_id=scope_id,
            expected_scope_revision=expected_scope_revision,
            expected_current_snapshot_id=expected_current_snapshot_id,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            batch_digest=batch_digest,
            admission=admission,
            verifier_authority=self._verifier_authority,
            application_acceptance=application_acceptance,
            batch=batch,
            published_at=published_at,
        )


def structure_publication_request_digest(
    *,
    scope_id: StableId,
    expected_scope_revision: Revision,
    expected_current_snapshot_id: StableId | None,
    idempotency_key: IdempotencyKey,
    batch_digest: Digest,
    admission_digest: Digest,
    application_acceptance_digest: Digest,
    caller_ref: str,
    classification: str,
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_PUBLICATION_REQUEST@1",
            {
                "scope_id": scope_id.value,
                "expected_scope_revision": expected_scope_revision.value,
                "expected_current_snapshot_id": (
                    expected_current_snapshot_id.value
                    if expected_current_snapshot_id is not None
                    else None
                ),
                "idempotency_key": idempotency_key.value,
                "batch_digest": batch_digest.value,
                "admission_digest": admission_digest.value,
                "application_acceptance_digest": (
                    application_acceptance_digest.value
                ),
                "caller_ref": caller_ref,
                "classification": classification,
            },
        ]
    )


def structure_snapshot_manifest_digest(snapshot: StructureSnapshot) -> Digest:
    return _snapshot_manifest_digest_values(
        snapshot_id=snapshot.snapshot_id,
        scope_id=snapshot.scope_id,
        snapshot_revision=snapshot.snapshot_revision,
        previous_snapshot_id=snapshot.previous_snapshot_id,
        schema_ref=snapshot.schema_ref,
        schema_digest=snapshot.schema_digest,
        schema_adoption_mode=snapshot.schema_adoption_mode,
        schema_registration_digest=snapshot.schema_registration_digest,
        schema_availability_digest=snapshot.schema_availability_digest,
        schema_adoption_digest=snapshot.schema_adoption_digest,
        publication_mode=snapshot.publication_mode,
        members=snapshot.members,
        coverages=snapshot.coverages,
        upstream_entities=snapshot.upstream_entities,
        published_at=snapshot.published_at,
    )


def _snapshot_manifest_digest_values(
    *,
    snapshot_id: StableId,
    scope_id: StableId,
    snapshot_revision: Revision,
    previous_snapshot_id: StableId | None,
    schema_ref: str,
    schema_digest: Digest,
    schema_adoption_mode: StructureSchemaAdoptionMode,
    schema_registration_digest: Digest,
    schema_availability_digest: Digest,
    schema_adoption_digest: Digest,
    publication_mode: PublicationMode,
    members: tuple[CoverageMember, ...],
    coverages: tuple[SnapshotCoverage, ...],
    upstream_entities: tuple[SnapshotUpstreamEntity, ...],
    published_at: datetime,
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_SNAPSHOT_MANIFEST@1",
            {
                "snapshot_id": snapshot_id.value,
                "scope_id": scope_id.value,
                "snapshot_revision": snapshot_revision.value,
                "previous_snapshot_id": (
                    previous_snapshot_id.value
                    if previous_snapshot_id is not None
                    else None
                ),
                "schema_ref": schema_ref,
                "schema_digest": schema_digest.value,
                "schema_adoption_mode": schema_adoption_mode.value,
                "schema_registration_digest": schema_registration_digest.value,
                "schema_availability_digest": schema_availability_digest.value,
                "schema_adoption_digest": schema_adoption_digest.value,
                "publication_mode": publication_mode.value,
                "members": members,
                "coverages": coverages,
                "upstream_entities": upstream_entities,
                "published_at": published_at,
            },
        ]
    )


def structure_publication_receipt_digest(
    receipt: StructurePublicationReceipt,
) -> Digest:
    return _publication_receipt_digest_values(
        publication_id=receipt.publication_id,
        request_digest=receipt.request_digest,
        batch_digest=receipt.batch_digest,
        admission_id=receipt.admission_id,
        admission_digest=receipt.admission_digest,
        application_acceptance_digest=receipt.application_acceptance_digest,
        snapshot=receipt.snapshot,
        published_at=receipt.published_at,
    )


def _publication_receipt_digest_values(
    *,
    publication_id: StableId,
    request_digest: Digest,
    batch_digest: Digest,
    admission_id: StableId,
    admission_digest: Digest,
    application_acceptance_digest: Digest,
    snapshot: StructureSnapshot,
    published_at: datetime,
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_PUBLICATION_RECEIPT@1",
            {
                "publication_id": publication_id.value,
                "request_digest": request_digest.value,
                "batch_digest": batch_digest.value,
                "admission_id": admission_id.value,
                "admission_digest": admission_digest.value,
                "application_acceptance_digest": (
                    application_acceptance_digest.value
                ),
                "snapshot_id": snapshot.snapshot_id.value,
                "snapshot_manifest_digest": snapshot.manifest_digest.value,
                "published_at": published_at,
            },
        ]
    )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _invalid("TEXT_INVALID", f"{label} must be non-empty and canonical")
    return value


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


__all__ = [
    "ApplicationAcceptanceDecision",
    "SnapshotCoverage",
    "SnapshotUpstreamEntity",
    "StructureEvidenceMetadata",
    "StructureApplicationAcceptance",
    "StructureKnowledgeRepository",
    "StructurePublicationReceipt",
    "StructurePublicationService",
    "StructureSnapshot",
    "structure_batch_digest",
    "structure_publication_receipt_digest",
    "structure_publication_request_digest",
    "structure_snapshot_manifest_digest",
]
