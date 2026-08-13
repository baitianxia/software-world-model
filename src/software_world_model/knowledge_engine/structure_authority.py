"""Independent Admission and Schema authority for typed Structure knowledge.

The value objects in this module are deliberately separate from both the
mechanical candidate closure in :mod:`structure` and Application acceptance.
An ACCEPT is useful to a Publisher only after the repository has persisted it
and can re-read the exact canonical record during the publication transaction.
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

from .scope import (
    AssertionOutcome,
    KnowledgeScopeService,
    ScopePurpose,
    ScopeType,
)
from .structure import (
    JAVA_STATIC_CALL_SCHEMA_DIGEST,
    JAVA_STATIC_CALL_SCHEMA_REF,
    MAVEN_STRUCTURE_SCHEMA_DIGEST,
    MAVEN_STRUCTURE_SCHEMA_REF,
    StructureKnowledgeBatch,
)


class StructureSchemaAvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEPRECATED = "DEPRECATED"


class StructureSchemaAdoptionMode(str, Enum):
    INITIAL = "INITIAL"
    UNCHANGED = "UNCHANGED"


class StructureAdmissionOutcome(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


class StructureVerifierAssessmentOutcome(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True, slots=True)
class StructureSchemaDependency:
    schema_ref: str
    schema_digest: Digest

    def __post_init__(self) -> None:
        object.__setattr__(self, "schema_ref", _text(self.schema_ref, "Schema dependency ref"))
        _require_digest(self.schema_digest, "Schema dependency digest")


@dataclass(frozen=True, slots=True)
class StructureSchemaDefinition:
    """Exact immutable Definition proposed for registry registration."""

    schema_ref: str
    schema_digest: Digest
    eligible_scope_types: tuple[ScopeType, ...]
    dependencies: tuple[StructureSchemaDependency, ...]
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        schema_ref: str,
        schema_digest: Digest,
        eligible_scope_types: Sequence[ScopeType] = (ScopeType.SYSTEM,),
        dependencies: Sequence[StructureSchemaDependency] = (),
    ) -> "StructureSchemaDefinition":
        normalized_ref = _text(schema_ref, "Schema ref")
        _require_digest(schema_digest, "Schema digest")
        supplied_scope_types = tuple(eligible_scope_types)
        if not supplied_scope_types or any(
            not isinstance(item, ScopeType) for item in supplied_scope_types
        ):
            raise _invalid(
                "SCHEMA_SCOPE_ELIGIBILITY_INVALID",
                "Schema Definition requires typed eligible Scope kinds",
            )
        normalized_scope_types = tuple(
            sorted(set(supplied_scope_types), key=lambda item: item.value)
        )
        supplied_dependencies = tuple(dependencies)
        if any(
            not isinstance(item, StructureSchemaDependency)
            for item in supplied_dependencies
        ):
            raise _invalid(
                "SCHEMA_DEPENDENCIES_INVALID",
                "Schema dependencies must be typed, sorted, and unique",
            )
        normalized_dependencies = tuple(
            sorted(supplied_dependencies, key=lambda item: item.schema_ref)
        )
        if len({item.schema_ref for item in normalized_dependencies}) != len(
            normalized_dependencies
        ):
            raise _invalid(
                "SCHEMA_DEPENDENCIES_INVALID",
                "Schema dependencies must be typed, sorted, and unique",
            )
        if any(item.schema_ref == normalized_ref for item in normalized_dependencies):
            raise _invalid(
                "SCHEMA_DEPENDENCY_CYCLE",
                "Schema Definition cannot depend on itself",
            )
        core = {
            "schema_ref": normalized_ref,
            "schema_digest": schema_digest.value,
            "eligible_scope_types": tuple(
                item.value for item in normalized_scope_types
            ),
            "dependencies": tuple(
                (item.schema_ref, item.schema_digest.value)
                for item in normalized_dependencies
            ),
        }
        return cls(
            schema_ref=normalized_ref,
            schema_digest=schema_digest,
            eligible_scope_types=normalized_scope_types,
            dependencies=normalized_dependencies,
            digest=digest_of(["STRUCTURE_SCHEMA_DEFINITION@1", core]),
        )

    @classmethod
    def maven_reactor_structure(cls) -> "StructureSchemaDefinition":
        """Frozen ITER-003 schema; it is not authoritative until registered."""

        return cls.create(
            schema_ref=MAVEN_STRUCTURE_SCHEMA_REF,
            schema_digest=MAVEN_STRUCTURE_SCHEMA_DIGEST,
            eligible_scope_types=(ScopeType.SYSTEM,),
        )

    @classmethod
    def java_static_call_graph(cls) -> "StructureSchemaDefinition":
        """Frozen ITER-006 schema; it is not authoritative until registered."""

        return cls.create(
            schema_ref=JAVA_STATIC_CALL_SCHEMA_REF,
            schema_digest=JAVA_STATIC_CALL_SCHEMA_DIGEST,
            eligible_scope_types=(ScopeType.SYSTEM,),
        )

    def require_valid(self) -> None:
        expected = self.create(
            schema_ref=self.schema_ref,
            schema_digest=self.schema_digest,
            eligible_scope_types=self.eligible_scope_types,
            dependencies=self.dependencies,
        )
        if expected != self:
            raise _invalid(
                "SCHEMA_DEFINITION_DIGEST_MISMATCH",
                "Schema Definition is not canonical",
            )


@dataclass(frozen=True, slots=True)
class StructureSchemaRegistration:
    registration_id: StableId
    definition: StructureSchemaDefinition
    proposal_ref: str
    review_ref: str
    registered_by: str
    reason: str
    registered_at: datetime
    digest: Digest

    def require_valid(self) -> None:
        if self.registration_id.kind != "schema_registration":
            raise _invalid(
                "SCHEMA_REGISTRATION_ID_INVALID",
                "Schema Registration ID has the wrong kind",
            )
        self.definition.require_valid()
        proposal_ref = _text(self.proposal_ref, "Schema Proposal ref")
        review_ref = _text(self.review_ref, "Schema Review ref")
        if proposal_ref == review_ref:
            raise _invalid(
                "SCHEMA_AUTHORITY_IDENTITIES_NOT_SEPARATE",
                "Schema Proposal and Review require separate identities",
            )
        _require_digest(self.digest, "Schema Registration digest")
        _require_time(self.registered_at, "Schema Registration time")
        expected = structure_schema_registration_digest(
            registration_id=self.registration_id,
            definition=self.definition,
            proposal_ref=proposal_ref,
            review_ref=review_ref,
            registered_by=self.registered_by,
            reason=self.reason,
            registered_at=self.registered_at,
        )
        if expected != self.digest:
            raise _invalid(
                "SCHEMA_REGISTRATION_DIGEST_MISMATCH",
                "Schema Registration is not canonical",
            )


@dataclass(frozen=True, slots=True)
class StructureSchemaAvailability:
    availability_id: StableId
    schema_ref: str
    schema_digest: Digest
    registration_id: StableId
    availability_revision: Revision
    status: StructureSchemaAvailabilityStatus
    changed_by: str
    reason: str
    changed_at: datetime
    previous_availability_id: StableId | None
    digest: Digest

    def require_valid(self) -> None:
        if self.availability_id.kind != "schema_availability":
            raise _invalid(
                "SCHEMA_AVAILABILITY_ID_INVALID",
                "Schema Availability ID has the wrong kind",
            )
        if self.registration_id.kind != "schema_registration":
            raise _invalid(
                "SCHEMA_REGISTRATION_ID_INVALID",
                "Schema Availability Registration ID has the wrong kind",
            )
        if self.previous_availability_id is not None and (
            self.previous_availability_id.kind != "schema_availability"
        ):
            raise _invalid(
                "SCHEMA_AVAILABILITY_PREDECESSOR_INVALID",
                "Schema Availability predecessor has the wrong kind",
            )
        if not isinstance(self.status, StructureSchemaAvailabilityStatus):
            raise _invalid(
                "SCHEMA_AVAILABILITY_STATUS_INVALID",
                "Schema Availability status is not typed",
            )
        _require_digest(self.digest, "Schema Availability digest")
        _require_time(self.changed_at, "Schema Availability time")
        if self.availability_revision == Revision(1):
            valid_transition = (
                self.status is StructureSchemaAvailabilityStatus.AVAILABLE
                and self.previous_availability_id is None
            )
        else:
            valid_transition = (
                self.status is StructureSchemaAvailabilityStatus.DEPRECATED
                and self.previous_availability_id is not None
            )
        if not valid_transition:
            raise _invalid(
                "SCHEMA_AVAILABILITY_TRANSITION_INVALID",
                "Schema Availability starts AVAILABLE and can only transition to DEPRECATED",
            )
        expected = structure_schema_availability_digest(
            availability_id=self.availability_id,
            schema_ref=self.schema_ref,
            schema_digest=self.schema_digest,
            registration_id=self.registration_id,
            availability_revision=self.availability_revision,
            status=self.status,
            changed_by=self.changed_by,
            reason=self.reason,
            changed_at=self.changed_at,
            previous_availability_id=self.previous_availability_id,
        )
        if expected != self.digest:
            raise _invalid(
                "SCHEMA_AVAILABILITY_DIGEST_MISMATCH",
                "Schema Availability is not canonical",
            )


@dataclass(frozen=True, slots=True)
class StructureSchemaAdoption:
    scope_id: StableId
    schema_ref: str
    schema_digest: Digest
    registration_id: StableId
    initial_availability_id: StableId
    initial_snapshot_id: StableId
    adopted_at: datetime
    digest: Digest

    def require_valid(self) -> None:
        if self.scope_id.kind != "scope":
            raise _invalid(
                "SCHEMA_ADOPTION_SCOPE_INVALID",
                "Schema Adoption Scope ID has the wrong kind",
            )
        if self.registration_id.kind != "schema_registration":
            raise _invalid(
                "SCHEMA_REGISTRATION_ID_INVALID",
                "Schema Adoption Registration ID has the wrong kind",
            )
        if self.initial_availability_id.kind != "schema_availability":
            raise _invalid(
                "SCHEMA_AVAILABILITY_ID_INVALID",
                "Schema Adoption Availability ID has the wrong kind",
            )
        if self.initial_snapshot_id.kind != "structure_snapshot":
            raise _invalid(
                "SCHEMA_ADOPTION_SNAPSHOT_INVALID",
                "Schema Adoption must bind the first Structure Snapshot",
            )
        _require_digest(self.digest, "Schema Adoption digest")
        _require_time(self.adopted_at, "Schema Adoption time")
        expected = structure_schema_adoption_digest(
            scope_id=self.scope_id,
            schema_ref=self.schema_ref,
            schema_digest=self.schema_digest,
            registration_id=self.registration_id,
            initial_availability_id=self.initial_availability_id,
            initial_snapshot_id=self.initial_snapshot_id,
            adopted_at=self.adopted_at,
        )
        if expected != self.digest:
            raise _invalid(
                "SCHEMA_ADOPTION_DIGEST_MISMATCH",
                "Schema Adoption is not canonical",
            )


@dataclass(frozen=True, slots=True)
class StructureAdmissionFinding:
    code: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _text(self.code, "Admission finding code"))
        object.__setattr__(self, "message", _text(self.message, "Admission finding message"))


@dataclass(frozen=True, slots=True, eq=False)
class StructureVerifierAuthority:
    """Opaque repository-issued capability for one verifier authority.

    Equality intentionally remains object identity.  Recreating these public
    fields does not recreate the repository registration that authorizes
    assessment, Admission, or publication writes.
    """

    authority_id: StableId
    verifier_ref: str

    def require_valid(self) -> None:
        if self.authority_id.kind != "verifier_authority":
            raise _invalid(
                "VERIFIER_AUTHORITY_ID_INVALID",
                "Structure verifier authority ID has the wrong kind",
            )
        _text(self.verifier_ref, "Admission verifier ref")


@dataclass(frozen=True, slots=True)
class StructureVerificationCandidate:
    """Candidate-side material supplied to an independently owned verifier."""

    candidate_ref: str
    candidate_digest: Digest
    candidate_evaluation_digest: Digest
    candidate_report_digest: Digest
    candidate_batch: StructureKnowledgeBatch
    provenance_digest: Digest
    verification_context_digest: Digest
    artifact_use_confirmation_id: StableId
    artifact_use_confirmation_digest: Digest

    def require_valid(self) -> None:
        _text(self.candidate_ref, "Structure candidate ref")
        for value, label in (
            (self.candidate_digest, "Structure candidate digest"),
            (self.candidate_evaluation_digest, "candidate evaluation digest"),
            (self.candidate_report_digest, "candidate report digest"),
            (self.provenance_digest, "Structure provenance digest"),
            (self.verification_context_digest, "verification context digest"),
            (
                self.artifact_use_confirmation_digest,
                "Artifact use Confirmation digest",
            ),
        ):
            _require_digest(value, label)
        if self.artifact_use_confirmation_id.kind != "artifact_use":
            raise _invalid(
                "ARTIFACT_USE_CONFIRMATION_ID_INVALID",
                "Structure candidate Artifact use Confirmation ID has the wrong kind",
            )
        if not isinstance(self.candidate_batch, StructureKnowledgeBatch):
            raise _invalid(
                "STRUCTURE_CANDIDATE_BATCH_REQUIRED",
                "Structure verifier requires a typed candidate batch",
            )
        self.candidate_batch.require_admissible()


@dataclass(frozen=True, slots=True)
class StructureVerificationResult:
    """Verifier-owned rebuild material; callers cannot supply it to assessment."""

    verified_candidate_digest: Digest
    verified_evaluation_digest: Digest
    verified_report_digest: Digest
    verified_batch: StructureKnowledgeBatch
    findings: tuple[StructureAdmissionFinding, ...] = ()

    def require_valid(self) -> None:
        for value, label in (
            (self.verified_candidate_digest, "verified Structure candidate digest"),
            (self.verified_evaluation_digest, "verified evaluation digest"),
            (self.verified_report_digest, "verified report digest"),
        ):
            _require_digest(value, label)
        if not isinstance(self.verified_batch, StructureKnowledgeBatch):
            raise _invalid(
                "VERIFIED_STRUCTURE_BATCH_REQUIRED",
                "Structure verifier result requires a typed verified batch",
            )
        self.verified_batch.require_admissible()
        if not isinstance(self.findings, tuple) or any(
            not isinstance(item, StructureAdmissionFinding) for item in self.findings
        ):
            raise _invalid(
                "ADMISSION_FINDINGS_INVALID",
                "Verifier Assessment findings must be a tuple of typed findings",
            )
        if tuple((item.code, item.message) for item in self.findings) != (
            normalized_findings_value(self.findings)
        ):
            raise _invalid(
                "ASSESSMENT_FINDINGS_NOT_CANONICAL",
                "Verifier result findings must be sorted and unique",
            )


class StructureCandidateVerifier(Protocol):
    """Private authority port used by the verifier-owned assessment service."""

    def verify(
        self, candidate: StructureVerificationCandidate
    ) -> StructureVerificationResult: ...


class StructureArtifactUseProofVerifier(Protocol):
    """Knowledge-side port for Source-owned Artifact-use proof verification.

    The port deliberately exposes no Artifact payload or replay capability.
    Its implementation must owner-read the exact persisted confirmation and
    fail closed unless it binds the supplied Structure candidate identity.
    """

    def verify_structure_candidate_use(
        self,
        *,
        confirmation_id: StableId,
        expected_confirmation_digest: Digest,
        candidate_ref: str,
        candidate_digest: Digest,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class StructureVerifierAssessment:
    """Persisted independent comparison of a Candidate and verifier rebuild.

    The assessment keeps both sides of every material canonical comparison.
    Admission therefore cannot turn caller-supplied comparison material into
    an ACCEPT. The configured verifier identity and exact persisted record are
    rechecked at Admission, then again by the Publisher transaction.
    """

    assessment_id: StableId
    outcome: StructureVerifierAssessmentOutcome
    candidate_ref: str
    candidate_digest: Digest
    verified_candidate_digest: Digest
    candidate_evaluation_digest: Digest
    verified_evaluation_digest: Digest
    candidate_report_digest: Digest
    verified_report_digest: Digest
    batch_digest: Digest
    verified_batch_digest: Digest
    closure_digest: Digest
    verified_closure_digest: Digest
    read_set_digest: Digest
    verified_read_set_digest: Digest
    provenance_digest: Digest
    verification_context_digest: Digest
    artifact_use_confirmation_id: StableId
    artifact_use_confirmation_digest: Digest
    verifier_authority_id: StableId
    verifier_ref: str
    findings: tuple[StructureAdmissionFinding, ...]
    assessed_at: datetime
    digest: Digest

    def require_valid(self) -> None:
        if self.assessment_id.kind != "structure_assessment":
            raise _invalid(
                "VERIFIER_ASSESSMENT_ID_INVALID",
                "Structure Verifier Assessment ID has the wrong kind",
            )
        if not isinstance(self.outcome, StructureVerifierAssessmentOutcome):
            raise _invalid(
                "VERIFIER_ASSESSMENT_OUTCOME_INVALID",
                "Structure Verifier Assessment outcome is not typed",
            )
        _text(self.candidate_ref, "Structure candidate ref")
        _text(self.verifier_ref, "Structure verifier ref")
        if self.verifier_authority_id.kind != "verifier_authority":
            raise _invalid(
                "VERIFIER_AUTHORITY_ID_INVALID",
                "Verifier Assessment authority ID has the wrong kind",
            )
        if self.artifact_use_confirmation_id.kind != "artifact_use":
            raise _invalid(
                "ARTIFACT_USE_CONFIRMATION_ID_INVALID",
                "Verifier Assessment Artifact use Confirmation ID has the wrong kind",
            )
        for value, label in (
            (self.candidate_digest, "candidate digest"),
            (self.verified_candidate_digest, "verified candidate digest"),
            (self.candidate_evaluation_digest, "candidate evaluation digest"),
            (self.verified_evaluation_digest, "verified evaluation digest"),
            (self.candidate_report_digest, "candidate report digest"),
            (self.verified_report_digest, "verified report digest"),
            (self.batch_digest, "candidate batch digest"),
            (self.verified_batch_digest, "verified batch digest"),
            (self.closure_digest, "candidate closure digest"),
            (self.verified_closure_digest, "verified closure digest"),
            (self.read_set_digest, "candidate Read Set digest"),
            (self.verified_read_set_digest, "verified Read Set digest"),
            (self.provenance_digest, "candidate provenance digest"),
            (self.verification_context_digest, "verification context digest"),
            (
                self.artifact_use_confirmation_digest,
                "Artifact use Confirmation digest",
            ),
            (self.digest, "Verifier Assessment digest"),
        ):
            _require_digest(value, label)
        _require_time(self.assessed_at, "Verifier Assessment time")
        if tuple((item.code, item.message) for item in self.findings) != (
            normalized_findings_value(self.findings)
        ):
            raise _invalid(
                "ASSESSMENT_FINDINGS_NOT_CANONICAL",
                "Verifier Assessment findings must be sorted and unique",
            )
        expected_findings = structure_verifier_assessment_findings(
            candidate_digest=self.candidate_digest,
            verified_candidate_digest=self.verified_candidate_digest,
            candidate_evaluation_digest=self.candidate_evaluation_digest,
            verified_evaluation_digest=self.verified_evaluation_digest,
            candidate_report_digest=self.candidate_report_digest,
            verified_report_digest=self.verified_report_digest,
            batch_digest=self.batch_digest,
            verified_batch_digest=self.verified_batch_digest,
            closure_digest=self.closure_digest,
            verified_closure_digest=self.verified_closure_digest,
            read_set_digest=self.read_set_digest,
            verified_read_set_digest=self.verified_read_set_digest,
            findings=self.findings,
        )
        if expected_findings != self.findings:
            raise _invalid(
                "VERIFIER_ASSESSMENT_FINDINGS_INCOMPLETE",
                "Verifier Assessment omits a canonical candidate mismatch",
            )
        if self.outcome is StructureVerifierAssessmentOutcome.PASS:
            if self.findings:
                raise _invalid(
                    "VERIFIER_ASSESSMENT_PASS_HAS_FINDINGS",
                    "Verifier Assessment PASS cannot carry findings",
                )
        elif not self.findings:
            raise _invalid(
                "VERIFIER_ASSESSMENT_FAIL_FINDINGS_MISSING",
                "Verifier Assessment FAIL requires at least one finding",
            )
        expected = structure_verifier_assessment_digest(
            assessment_id=self.assessment_id,
            outcome=self.outcome,
            candidate_ref=self.candidate_ref,
            candidate_digest=self.candidate_digest,
            verified_candidate_digest=self.verified_candidate_digest,
            candidate_evaluation_digest=self.candidate_evaluation_digest,
            verified_evaluation_digest=self.verified_evaluation_digest,
            candidate_report_digest=self.candidate_report_digest,
            verified_report_digest=self.verified_report_digest,
            batch_digest=self.batch_digest,
            verified_batch_digest=self.verified_batch_digest,
            closure_digest=self.closure_digest,
            verified_closure_digest=self.verified_closure_digest,
            read_set_digest=self.read_set_digest,
            verified_read_set_digest=self.verified_read_set_digest,
            provenance_digest=self.provenance_digest,
            verification_context_digest=self.verification_context_digest,
            artifact_use_confirmation_id=self.artifact_use_confirmation_id,
            artifact_use_confirmation_digest=self.artifact_use_confirmation_digest,
            verifier_authority_id=self.verifier_authority_id,
            verifier_ref=self.verifier_ref,
            findings=self.findings,
            assessed_at=self.assessed_at,
        )
        if expected != self.digest:
            raise _invalid(
                "VERIFIER_ASSESSMENT_DIGEST_MISMATCH",
                "Structure Verifier Assessment is not canonical",
            )


@dataclass(frozen=True, slots=True)
class StructureAdmissionDecision:
    """Persisted, exact decision over one candidate closure revision."""

    admission_id: StableId
    outcome: StructureAdmissionOutcome
    candidate_ref: str
    candidate_digest: Digest
    batch_digest: Digest
    closure_digest: Digest
    read_set_digest: Digest
    scope_id: StableId
    expected_scope_revision: Revision
    scope_assertion_digest: Digest
    expected_current_snapshot_id: StableId | None
    schema_ref: str
    schema_digest: Digest
    schema_registration_digest: Digest
    schema_availability_digest: Digest
    knowledge_context_digest: Digest
    upstream_digest: Digest
    provenance_digest: Digest
    artifact_use_confirmation_id: StableId
    artifact_use_confirmation_digest: Digest
    verifier_assessment_id: StableId
    verifier_assessment_digest: Digest
    verifier_authority_id: StableId
    verifier_ref: str
    findings: tuple[StructureAdmissionFinding, ...]
    decided_at: datetime
    digest: Digest

    def require_valid(self) -> None:
        if self.admission_id.kind != "structure_admission":
            raise _invalid(
                "STRUCTURE_ADMISSION_ID_INVALID",
                "Structure Admission ID has the wrong kind",
            )
        if self.scope_id.kind != "scope":
            raise _invalid(
                "ADMISSION_SCOPE_ID_INVALID",
                "Structure Admission Scope ID has the wrong kind",
            )
        if self.expected_current_snapshot_id is not None and (
            self.expected_current_snapshot_id.kind != "structure_snapshot"
        ):
            raise _invalid(
                "ADMISSION_EXPECTED_CURRENT_INVALID",
                "Admission expected CURRENT has the wrong kind",
            )
        if self.verifier_assessment_id.kind != "structure_assessment":
            raise _invalid(
                "VERIFIER_ASSESSMENT_ID_INVALID",
                "Admission Verifier Assessment ID has the wrong kind",
            )
        if self.verifier_authority_id.kind != "verifier_authority":
            raise _invalid(
                "VERIFIER_AUTHORITY_ID_INVALID",
                "Admission verifier authority ID has the wrong kind",
            )
        if self.artifact_use_confirmation_id.kind != "artifact_use":
            raise _invalid(
                "ARTIFACT_USE_CONFIRMATION_ID_INVALID",
                "Admission Artifact use Confirmation ID has the wrong kind",
            )
        if not isinstance(self.outcome, StructureAdmissionOutcome):
            raise _invalid(
                "ADMISSION_OUTCOME_INVALID",
                "Structure Admission outcome is not typed",
            )
        for value, label in (
            (self.candidate_digest, "Admission candidate digest"),
            (self.batch_digest, "Admission batch digest"),
            (self.closure_digest, "Admission closure digest"),
            (self.read_set_digest, "Admission Read Set digest"),
            (self.scope_assertion_digest, "Admission Scope assertion digest"),
            (self.schema_digest, "Admission Schema digest"),
            (
                self.schema_registration_digest,
                "Admission Schema Registration digest",
            ),
            (
                self.schema_availability_digest,
                "Admission Schema Availability digest",
            ),
            (self.knowledge_context_digest, "Admission Context digest"),
            (self.upstream_digest, "Admission upstream digest"),
            (self.provenance_digest, "Admission provenance digest"),
            (
                self.artifact_use_confirmation_digest,
                "Admission Artifact use Confirmation digest",
            ),
            (
                self.verifier_assessment_digest,
                "Admission Verifier Assessment digest",
            ),
            (self.digest, "Admission Decision digest"),
        ):
            _require_digest(value, label)
        _require_time(self.decided_at, "Admission Decision time")
        if tuple((item.code, item.message) for item in self.findings) != (
            normalized_findings_value(self.findings)
        ):
            raise _invalid(
                "ADMISSION_FINDINGS_NOT_CANONICAL",
                "Admission findings must be sorted and unique",
            )
        if self.outcome is StructureAdmissionOutcome.ACCEPT and self.findings:
            raise _invalid(
                "ADMISSION_ACCEPT_HAS_FINDINGS",
                "Admission ACCEPT cannot carry rejection findings",
            )
        if self.outcome is StructureAdmissionOutcome.REJECT and not self.findings:
            raise _invalid(
                "ADMISSION_REJECT_FINDINGS_MISSING",
                "Admission REJECT requires at least one finding",
            )
        expected = structure_admission_decision_digest(
            admission_id=self.admission_id,
            outcome=self.outcome,
            candidate_ref=self.candidate_ref,
            candidate_digest=self.candidate_digest,
            batch_digest=self.batch_digest,
            closure_digest=self.closure_digest,
            read_set_digest=self.read_set_digest,
            scope_id=self.scope_id,
            expected_scope_revision=self.expected_scope_revision,
            scope_assertion_digest=self.scope_assertion_digest,
            expected_current_snapshot_id=self.expected_current_snapshot_id,
            schema_ref=self.schema_ref,
            schema_digest=self.schema_digest,
            schema_registration_digest=self.schema_registration_digest,
            schema_availability_digest=self.schema_availability_digest,
            knowledge_context_digest=self.knowledge_context_digest,
            upstream_digest=self.upstream_digest,
            provenance_digest=self.provenance_digest,
            artifact_use_confirmation_id=self.artifact_use_confirmation_id,
            artifact_use_confirmation_digest=self.artifact_use_confirmation_digest,
            verifier_assessment_id=self.verifier_assessment_id,
            verifier_assessment_digest=self.verifier_assessment_digest,
            verifier_authority_id=self.verifier_authority_id,
            verifier_ref=self.verifier_ref,
            findings=self.findings,
            decided_at=self.decided_at,
        )
        if expected != self.digest:
            raise _invalid(
                "ADMISSION_DECISION_DIGEST_MISMATCH",
                "Structure Admission Decision is not canonical",
            )


class StructureAuthorityRepository(Protocol):
    def register_structure_verifier_authority(
        self, *, verifier_ref: str
    ) -> StructureVerifierAuthority: ...

    def register_schema(
        self,
        *,
        definition: StructureSchemaDefinition,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        proposal_ref: str,
        review_ref: str,
        registered_by: str,
        reason: str,
        registered_at: datetime,
    ) -> tuple[StructureSchemaRegistration, StructureSchemaAvailability]: ...

    def deprecate_schema(
        self,
        *,
        schema_ref: str,
        schema_digest: Digest,
        expected_availability_revision: Revision,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        changed_by: str,
        reason: str,
        changed_at: datetime,
    ) -> StructureSchemaAvailability: ...

    def get_schema_registration(
        self, schema_ref: str
    ) -> StructureSchemaRegistration: ...

    def get_schema_availability(
        self, schema_ref: str, revision: Revision | None = None
    ) -> StructureSchemaAvailability: ...

    def get_schema_adoption(self, scope_id: StableId) -> StructureSchemaAdoption | None: ...

    def record_structure_verifier_assessment(
        self,
        *,
        candidate_ref: str,
        candidate_digest: Digest,
        verified_candidate_digest: Digest,
        candidate_evaluation_digest: Digest,
        verified_evaluation_digest: Digest,
        candidate_report_digest: Digest,
        verified_report_digest: Digest,
        candidate_batch: StructureKnowledgeBatch,
        verified_batch: StructureKnowledgeBatch,
        provenance_digest: Digest,
        verification_context_digest: Digest,
        artifact_use_confirmation_id: StableId,
        artifact_use_confirmation_digest: Digest,
        verifier_authority: StructureVerifierAuthority,
        findings: tuple[StructureAdmissionFinding, ...],
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        assessed_at: datetime,
    ) -> StructureVerifierAssessment: ...

    def get_structure_verifier_assessment(
        self, assessment_id: StableId
    ) -> StructureVerifierAssessment: ...

    def record_structure_admission(
        self,
        *,
        outcome: StructureAdmissionOutcome,
        candidate_ref: str,
        candidate_digest: Digest,
        batch: StructureKnowledgeBatch,
        scope_id: StableId,
        expected_scope_revision: Revision,
        scope_assertion_digest: Digest,
        expected_current_snapshot_id: StableId | None,
        provenance_digest: Digest,
        assessment: StructureVerifierAssessment,
        verifier_authority: StructureVerifierAuthority,
        findings: tuple[StructureAdmissionFinding, ...],
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        decided_at: datetime,
    ) -> StructureAdmissionDecision: ...

    def get_structure_admission(
        self, admission_id: StableId
    ) -> StructureAdmissionDecision: ...


class StructureSchemaRegistryService:
    def __init__(
        self,
        repository: StructureAuthorityRepository,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def register(
        self,
        *,
        definition: StructureSchemaDefinition,
        idempotency_key: IdempotencyKey,
        proposal_ref: str,
        review_ref: str,
        registered_by: str,
        reason: str,
    ) -> tuple[StructureSchemaRegistration, StructureSchemaAvailability]:
        definition.require_valid()
        normalized_proposal_ref = _text(proposal_ref, "Schema Proposal ref")
        normalized_review_ref = _text(review_ref, "Schema Review ref")
        if normalized_proposal_ref == normalized_review_ref:
            raise _invalid(
                "SCHEMA_AUTHORITY_IDENTITIES_NOT_SEPARATE",
                "Schema Proposal and Review require separate identities",
            )
        normalized_by = _text(registered_by, "Schema registrar")
        normalized_reason = _text(reason, "Schema registration reason")
        request_digest = digest_of(
            [
                "STRUCTURE_SCHEMA_REGISTRATION_REQUEST@1",
                {
                    "definition_digest": definition.digest.value,
                    "proposal_ref": normalized_proposal_ref,
                    "review_ref": normalized_review_ref,
                    "registered_by": normalized_by,
                    "reason": normalized_reason,
                },
            ]
        )
        return self._repository.register_schema(
            definition=definition,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            proposal_ref=normalized_proposal_ref,
            review_ref=normalized_review_ref,
            registered_by=normalized_by,
            reason=normalized_reason,
            registered_at=_now(self._clock),
        )

    def deprecate(
        self,
        *,
        schema_ref: str,
        schema_digest: Digest,
        expected_availability_revision: Revision,
        idempotency_key: IdempotencyKey,
        changed_by: str,
        reason: str,
    ) -> StructureSchemaAvailability:
        normalized_ref = _text(schema_ref, "Schema ref")
        normalized_by = _text(changed_by, "Schema authority actor")
        normalized_reason = _text(reason, "Schema deprecation reason")
        request_digest = digest_of(
            [
                "STRUCTURE_SCHEMA_DEPRECATION_REQUEST@1",
                {
                    "schema_ref": normalized_ref,
                    "schema_digest": schema_digest.value,
                    "expected_availability_revision": expected_availability_revision.value,
                    "changed_by": normalized_by,
                    "reason": normalized_reason,
                },
            ]
        )
        return self._repository.deprecate_schema(
            schema_ref=normalized_ref,
            schema_digest=schema_digest,
            expected_availability_revision=expected_availability_revision,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            changed_by=normalized_by,
            reason=normalized_reason,
            changed_at=_now(self._clock),
        )

    def get_registration(self, schema_ref: str) -> StructureSchemaRegistration:
        return self._repository.get_schema_registration(schema_ref)

    def get_availability(
        self, schema_ref: str, revision: Revision | None = None
    ) -> StructureSchemaAvailability:
        return self._repository.get_schema_availability(schema_ref, revision)

    def get_adoption(self, scope_id: StableId) -> StructureSchemaAdoption | None:
        return self._repository.get_schema_adoption(scope_id)


class StructureVerifierAssessmentService:
    def __init__(
        self,
        repository: StructureAuthorityRepository,
        verifier: StructureCandidateVerifier,
        *,
        verifier_authority: StructureVerifierAuthority,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        if not callable(getattr(verifier, "verify", None)):
            raise _invalid(
                "STRUCTURE_VERIFIER_REQUIRED",
                "Structure assessment requires an independent verifier port",
            )
        self._verifier = verifier
        if not isinstance(verifier_authority, StructureVerifierAuthority):
            raise _invalid(
                "VERIFIER_AUTHORITY_REQUIRED",
                "Structure assessment requires a repository-issued verifier authority",
            )
        verifier_authority.require_valid()
        self._verifier_authority = verifier_authority
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @property
    def verifier_ref(self) -> str:
        return self._verifier_authority.verifier_ref

    def assess(
        self,
        *,
        candidate_ref: str,
        candidate_digest: Digest,
        candidate_evaluation_digest: Digest,
        candidate_report_digest: Digest,
        candidate_batch: StructureKnowledgeBatch,
        provenance_digest: Digest,
        verification_context_digest: Digest,
        artifact_use_confirmation_id: StableId,
        artifact_use_confirmation_digest: Digest,
        idempotency_key: IdempotencyKey,
    ) -> StructureVerifierAssessment:
        candidate = StructureVerificationCandidate(
            candidate_ref=candidate_ref,
            candidate_digest=candidate_digest,
            candidate_evaluation_digest=candidate_evaluation_digest,
            candidate_report_digest=candidate_report_digest,
            candidate_batch=candidate_batch,
            provenance_digest=provenance_digest,
            verification_context_digest=verification_context_digest,
            artifact_use_confirmation_id=artifact_use_confirmation_id,
            artifact_use_confirmation_digest=artifact_use_confirmation_digest,
        )
        candidate.require_valid()
        verified = self._verifier.verify(candidate)
        if not isinstance(verified, StructureVerificationResult):
            raise _invalid(
                "STRUCTURE_VERIFIER_RESULT_INVALID",
                "independent verifier returned an untyped result",
            )
        verified.require_valid()
        canonical_findings = structure_verifier_assessment_findings(
            candidate_digest=candidate.candidate_digest,
            verified_candidate_digest=verified.verified_candidate_digest,
            candidate_evaluation_digest=candidate.candidate_evaluation_digest,
            verified_evaluation_digest=verified.verified_evaluation_digest,
            candidate_report_digest=candidate.candidate_report_digest,
            verified_report_digest=verified.verified_report_digest,
            batch_digest=structure_batch_digest(candidate.candidate_batch),
            verified_batch_digest=structure_batch_digest(verified.verified_batch),
            closure_digest=structure_closure_digest(candidate.candidate_batch),
            verified_closure_digest=structure_closure_digest(verified.verified_batch),
            read_set_digest=structure_read_set_digest(candidate.candidate_batch),
            verified_read_set_digest=structure_read_set_digest(verified.verified_batch),
            findings=verified.findings,
        )
        request_digest = digest_of(
            [
                "STRUCTURE_VERIFIER_ASSESSMENT_REQUEST@3",
                {
                    "candidate_ref": candidate.candidate_ref,
                    "candidate_digest": candidate.candidate_digest.value,
                    "verified_candidate_digest": verified.verified_candidate_digest.value,
                    "candidate_evaluation_digest": candidate.candidate_evaluation_digest.value,
                    "verified_evaluation_digest": verified.verified_evaluation_digest.value,
                    "candidate_report_digest": candidate.candidate_report_digest.value,
                    "verified_report_digest": verified.verified_report_digest.value,
                    "candidate_batch_digest": structure_batch_digest(candidate.candidate_batch).value,
                    "verified_batch_digest": structure_batch_digest(verified.verified_batch).value,
                    "candidate_closure_digest": structure_closure_digest(candidate.candidate_batch).value,
                    "verified_closure_digest": structure_closure_digest(verified.verified_batch).value,
                    "candidate_read_set_digest": structure_read_set_digest(candidate.candidate_batch).value,
                    "verified_read_set_digest": structure_read_set_digest(verified.verified_batch).value,
                    "provenance_digest": candidate.provenance_digest.value,
                    "verification_context_digest": candidate.verification_context_digest.value,
                    "artifact_use_confirmation_id": (
                        candidate.artifact_use_confirmation_id.value
                    ),
                    "artifact_use_confirmation_digest": (
                        candidate.artifact_use_confirmation_digest.value
                    ),
                    "verifier_authority_id": self._verifier_authority.authority_id.value,
                    "verifier_ref": self._verifier_authority.verifier_ref,
                    "findings": normalized_findings_value(canonical_findings),
                },
            ]
        )
        return self._repository.record_structure_verifier_assessment(
            candidate_ref=candidate.candidate_ref,
            candidate_digest=candidate.candidate_digest,
            verified_candidate_digest=verified.verified_candidate_digest,
            candidate_evaluation_digest=candidate.candidate_evaluation_digest,
            verified_evaluation_digest=verified.verified_evaluation_digest,
            candidate_report_digest=candidate.candidate_report_digest,
            verified_report_digest=verified.verified_report_digest,
            candidate_batch=candidate.candidate_batch,
            verified_batch=verified.verified_batch,
            provenance_digest=candidate.provenance_digest,
            verification_context_digest=candidate.verification_context_digest,
            artifact_use_confirmation_id=candidate.artifact_use_confirmation_id,
            artifact_use_confirmation_digest=(
                candidate.artifact_use_confirmation_digest
            ),
            verifier_authority=self._verifier_authority,
            findings=canonical_findings,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            assessed_at=_now(self._clock),
        )


class StructureAdmissionService:
    def __init__(
        self,
        repository: StructureAuthorityRepository,
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
                "Structure Admission requires an Artifact-use proof verifier",
            )
        self._artifact_use_proofs = artifact_use_proofs
        if not isinstance(verifier_authority, StructureVerifierAuthority):
            raise _invalid(
                "VERIFIER_AUTHORITY_REQUIRED",
                "Structure Admission requires a repository-issued verifier authority",
            )
        verifier_authority.require_valid()
        self._verifier_authority = verifier_authority
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    @property
    def verifier_ref(self) -> str:
        return self._verifier_authority.verifier_ref

    def get_assessment(
        self, assessment_id: StableId
    ) -> StructureVerifierAssessment:
        return self._repository.get_structure_verifier_assessment(assessment_id)

    def accept(
        self,
        *,
        scope_id: StableId,
        expected_scope_revision: Revision,
        expected_current_snapshot_id: StableId | None,
        candidate_ref: str,
        candidate_digest: Digest,
        batch: StructureKnowledgeBatch,
        provenance_digest: Digest,
        assessment: StructureVerifierAssessment,
        idempotency_key: IdempotencyKey,
        caller_ref: str,
        classification: str,
    ) -> StructureAdmissionDecision:
        batch.require_admissible()
        self._require_assessment(
            assessment=assessment,
            expected_outcome=StructureVerifierAssessmentOutcome.PASS,
            candidate_ref=candidate_ref,
            candidate_digest=candidate_digest,
            batch=batch,
            provenance_digest=provenance_digest,
        )
        return self._decide(
            outcome=StructureAdmissionOutcome.ACCEPT,
            findings=(),
            scope_id=scope_id,
            expected_scope_revision=expected_scope_revision,
            expected_current_snapshot_id=expected_current_snapshot_id,
            candidate_ref=candidate_ref,
            candidate_digest=candidate_digest,
            batch=batch,
            provenance_digest=provenance_digest,
            assessment=assessment,
            idempotency_key=idempotency_key,
            caller_ref=caller_ref,
            classification=classification,
        )

    def reject(
        self,
        *,
        scope_id: StableId,
        expected_scope_revision: Revision,
        expected_current_snapshot_id: StableId | None,
        candidate_ref: str,
        candidate_digest: Digest,
        batch: StructureKnowledgeBatch,
        provenance_digest: Digest,
        assessment: StructureVerifierAssessment,
        idempotency_key: IdempotencyKey,
        caller_ref: str,
        classification: str,
    ) -> StructureAdmissionDecision:
        self._require_assessment(
            assessment=assessment,
            expected_outcome=StructureVerifierAssessmentOutcome.FAIL,
            candidate_ref=candidate_ref,
            candidate_digest=candidate_digest,
            batch=batch,
            provenance_digest=provenance_digest,
        )
        return self._decide(
            outcome=StructureAdmissionOutcome.REJECT,
            findings=assessment.findings,
            scope_id=scope_id,
            expected_scope_revision=expected_scope_revision,
            expected_current_snapshot_id=expected_current_snapshot_id,
            candidate_ref=candidate_ref,
            candidate_digest=candidate_digest,
            batch=batch,
            provenance_digest=provenance_digest,
            assessment=assessment,
            idempotency_key=idempotency_key,
            caller_ref=caller_ref,
            classification=classification,
        )

    def get_admission(self, admission_id: StableId) -> StructureAdmissionDecision:
        return self._repository.get_structure_admission(admission_id)

    def get(self, admission_id: StableId) -> StructureAdmissionDecision:
        """Compatibility alias for callers migrating to ``get_admission``."""

        return self.get_admission(admission_id)

    def _decide(
        self,
        *,
        outcome: StructureAdmissionOutcome,
        findings: tuple[StructureAdmissionFinding, ...],
        scope_id: StableId,
        expected_scope_revision: Revision,
        expected_current_snapshot_id: StableId | None,
        candidate_ref: str,
        candidate_digest: Digest,
        batch: StructureKnowledgeBatch,
        provenance_digest: Digest,
        assessment: StructureVerifierAssessment,
        idempotency_key: IdempotencyKey,
        caller_ref: str,
        classification: str,
    ) -> StructureAdmissionDecision:
        normalized_candidate_ref = _text(candidate_ref, "Structure candidate ref")
        normalized_verifier_ref = assessment.verifier_ref
        normalized_caller = _text(caller_ref, "Admission caller ref")
        normalized_classification = _text(classification, "Admission classification")
        _require_digest(candidate_digest, "Structure candidate digest")
        _require_digest(provenance_digest, "Structure provenance digest")
        assertion = self._scopes.read_scope_state_assertion(
            scope_id=scope_id,
            expected_revision=expected_scope_revision,
            purpose=ScopePurpose.KNOWLEDGE_ADMISSION,
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
                "Structure Admission requires an eligible SYSTEM Scope assertion",
                {"scope_id": scope_id.value},
            )
        batch_digest = structure_batch_digest(batch)
        request_digest = digest_of(
            [
                "STRUCTURE_ADMISSION_REQUEST@3",
                {
                    "outcome": outcome.value,
                    "candidate_ref": normalized_candidate_ref,
                    "candidate_digest": candidate_digest.value,
                    "batch_digest": batch_digest.value,
                    "closure_digest": structure_closure_digest(batch).value,
                    "read_set_digest": structure_read_set_digest(batch).value,
                    "scope_id": scope_id.value,
                    "expected_scope_revision": expected_scope_revision.value,
                    "expected_current_snapshot_id": (
                        expected_current_snapshot_id.value
                        if expected_current_snapshot_id is not None
                        else None
                    ),
                    "schema_ref": batch.coverage.root.schema_ref,
                    "schema_digest": batch.coverage.root.schema_digest.value,
                    "knowledge_context_digest": (
                        batch.coverage.state.knowledge_context_digest.value
                    ),
                    "upstream_digest": structure_upstream_digest(batch).value,
                    "provenance_digest": provenance_digest.value,
                    "artifact_use_confirmation_id": (
                        assessment.artifact_use_confirmation_id.value
                    ),
                    "artifact_use_confirmation_digest": (
                        assessment.artifact_use_confirmation_digest.value
                    ),
                    "verifier_assessment_id": assessment.assessment_id.value,
                    "verifier_assessment_digest": assessment.digest.value,
                    "verifier_authority_id": self._verifier_authority.authority_id.value,
                    "verifier_ref": normalized_verifier_ref,
                    "findings": normalized_findings_value(findings),
                    "scope_assertion_digest": assertion.digest.value,
                },
            ]
        )
        return self._repository.record_structure_admission(
            outcome=outcome,
            candidate_ref=normalized_candidate_ref,
            candidate_digest=candidate_digest,
            batch=batch,
            scope_id=scope_id,
            expected_scope_revision=expected_scope_revision,
            scope_assertion_digest=assertion.digest,
            expected_current_snapshot_id=expected_current_snapshot_id,
            provenance_digest=provenance_digest,
            assessment=assessment,
            verifier_authority=self._verifier_authority,
            findings=findings,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            decided_at=_now(self._clock),
        )

    def _require_assessment(
        self,
        *,
        assessment: StructureVerifierAssessment,
        expected_outcome: StructureVerifierAssessmentOutcome,
        candidate_ref: str,
        candidate_digest: Digest,
        batch: StructureKnowledgeBatch,
        provenance_digest: Digest,
    ) -> None:
        if not isinstance(assessment, StructureVerifierAssessment):
            raise _invalid(
                "VERIFIER_ASSESSMENT_REQUIRED",
                "Structure Admission requires a typed Verifier Assessment",
            )
        assessment.require_valid()
        if (
            assessment.verifier_authority_id
            != self._verifier_authority.authority_id
            or assessment.verifier_ref != self._verifier_authority.verifier_ref
        ):
            raise _invalid(
                "VERIFIER_AUTHORITY_MISMATCH",
                "Verifier Assessment was not issued by the configured authority",
            )
        stored = self._repository.get_structure_verifier_assessment(
            assessment.assessment_id
        )
        if stored != assessment:
            raise _invalid(
                "VERIFIER_ASSESSMENT_PERSISTED_RECORD_MISMATCH",
                "provided Verifier Assessment differs from persisted authority",
            )
        self._artifact_use_proofs.verify_structure_candidate_use(
            confirmation_id=assessment.artifact_use_confirmation_id,
            expected_confirmation_digest=(
                assessment.artifact_use_confirmation_digest
            ),
            candidate_ref=_text(candidate_ref, "Structure candidate ref"),
            candidate_digest=candidate_digest,
        )
        bindings = (
            (assessment.outcome, expected_outcome),
            (assessment.candidate_ref, _text(candidate_ref, "Structure candidate ref")),
            (assessment.candidate_digest, candidate_digest),
            (assessment.batch_digest, structure_batch_digest(batch)),
            (assessment.closure_digest, structure_closure_digest(batch)),
            (assessment.read_set_digest, structure_read_set_digest(batch)),
            (assessment.provenance_digest, provenance_digest),
        )
        if any(actual != expected for actual, expected in bindings):
            raise _invalid(
                "VERIFIER_ASSESSMENT_CANDIDATE_MISMATCH",
                "Verifier Assessment is bound to another candidate closure",
            )


def structure_batch_digest(batch: StructureKnowledgeBatch) -> Digest:
    return digest_of(["STRUCTURE_KNOWLEDGE_BATCH@1", batch])


def structure_closure_digest(batch: StructureKnowledgeBatch) -> Digest:
    return digest_of(
        [
            "STRUCTURE_CANDIDATE_CLOSURE@1",
            {
                "batch_digest": structure_batch_digest(batch).value,
                "coverage_root_id": batch.coverage.root_id.value,
                "coverage_state_id": batch.coverage.state_id.value,
                "evidence": tuple(
                    (item.evidence_id.value, item.digest.value) for item in batch.evidence
                ),
                "members": tuple(
                    (
                        record.coverage_member.kind.value,
                        record.root_id.value,
                        record.state_id.value,
                        record.state_digest.value,
                    )
                    for record in (
                        *batch.entities,
                        *batch.relation_facts,
                        *batch.literal_facts,
                    )
                ),
                "upstream": tuple(
                    (
                        item.snapshot_id.value,
                        item.entity.root_id.value,
                        item.entity.state_id.value,
                        item.entity.state_digest.value,
                    )
                    for item in batch.exact_upstream_entities
                ),
            },
        ]
    )


def structure_read_set_digest(batch: StructureKnowledgeBatch) -> Digest:
    return digest_of(
        [
            "STRUCTURE_ADMISSION_READ_SET@1",
            {
                "evidence": tuple(
                    sorted(
                        (
                            item.evidence_id.value,
                            item.artifact_id.value,
                            item.source_context_id.value,
                            item.artifact_content_digest.value,
                            item.excerpt_digest.value,
                        )
                        for item in batch.evidence
                    )
                ),
                "upstream": tuple(
                    sorted(
                        (
                            item.snapshot_id.value,
                            item.entity.root_id.value,
                            item.entity.state_id.value,
                            item.entity.state_digest.value,
                        )
                        for item in batch.exact_upstream_entities
                    )
                ),
            },
        ]
    )


def structure_upstream_digest(batch: StructureKnowledgeBatch) -> Digest:
    return digest_of(
        [
            "STRUCTURE_EXACT_UPSTREAM@1",
            tuple(
                sorted(
                    (
                        item.snapshot_id.value,
                        item.entity.root_id.value,
                        item.entity.state_id.value,
                        item.entity.state_digest.value,
                    )
                    for item in batch.exact_upstream_entities
                )
            ),
        ]
    )


def structure_verifier_assessment_findings(
    *,
    candidate_digest: Digest,
    verified_candidate_digest: Digest,
    candidate_evaluation_digest: Digest,
    verified_evaluation_digest: Digest,
    candidate_report_digest: Digest,
    verified_report_digest: Digest,
    batch_digest: Digest,
    verified_batch_digest: Digest,
    closure_digest: Digest,
    verified_closure_digest: Digest,
    read_set_digest: Digest,
    verified_read_set_digest: Digest,
    findings: Sequence[StructureAdmissionFinding] = (),
) -> tuple[StructureAdmissionFinding, ...]:
    supplied = tuple(findings)
    if any(not isinstance(item, StructureAdmissionFinding) for item in supplied):
        raise _invalid(
            "ADMISSION_FINDINGS_INVALID",
            "Verifier Assessment findings must be typed",
        )
    values = set(normalized_findings_value(supplied))
    comparisons = (
        (
            candidate_digest,
            verified_candidate_digest,
            "CANDIDATE_DIGEST_MISMATCH",
            "independent verifier rebuilt a different candidate digest",
        ),
        (
            candidate_evaluation_digest,
            verified_evaluation_digest,
            "EVALUATION_DIGEST_MISMATCH",
            "independent verifier rebuilt a different canonical evaluation",
        ),
        (
            candidate_report_digest,
            verified_report_digest,
            "BUILD_REPORT_DIGEST_MISMATCH",
            "independent verifier rebuilt a different complete build report",
        ),
        (
            batch_digest,
            verified_batch_digest,
            "BATCH_DIGEST_MISMATCH",
            "independent verifier rebuilt a different Structure batch",
        ),
        (
            closure_digest,
            verified_closure_digest,
            "CLOSURE_DIGEST_MISMATCH",
            "independent verifier rebuilt a different candidate closure",
        ),
        (
            read_set_digest,
            verified_read_set_digest,
            "READ_SET_DIGEST_MISMATCH",
            "independent verifier rebuilt a different candidate Read Set",
        ),
    )
    for candidate_value, verified_value, code, message in comparisons:
        if candidate_value != verified_value:
            values.add((code, message))
    return tuple(
        StructureAdmissionFinding(code=code, message=message)
        for code, message in sorted(values)
    )


def structure_verifier_assessment_digest(
    *,
    assessment_id: StableId,
    outcome: StructureVerifierAssessmentOutcome,
    candidate_ref: str,
    candidate_digest: Digest,
    verified_candidate_digest: Digest,
    candidate_evaluation_digest: Digest,
    verified_evaluation_digest: Digest,
    candidate_report_digest: Digest,
    verified_report_digest: Digest,
    batch_digest: Digest,
    verified_batch_digest: Digest,
    closure_digest: Digest,
    verified_closure_digest: Digest,
    read_set_digest: Digest,
    verified_read_set_digest: Digest,
    provenance_digest: Digest,
    verification_context_digest: Digest,
    artifact_use_confirmation_id: StableId,
    artifact_use_confirmation_digest: Digest,
    verifier_authority_id: StableId,
    verifier_ref: str,
    findings: tuple[StructureAdmissionFinding, ...],
    assessed_at: datetime,
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_VERIFIER_ASSESSMENT@3",
            {
                "assessment_id": assessment_id.value,
                "outcome": outcome.value,
                "candidate_ref": _text(candidate_ref, "Structure candidate ref"),
                "candidate_digest": candidate_digest.value,
                "verified_candidate_digest": verified_candidate_digest.value,
                "candidate_evaluation_digest": candidate_evaluation_digest.value,
                "verified_evaluation_digest": verified_evaluation_digest.value,
                "candidate_report_digest": candidate_report_digest.value,
                "verified_report_digest": verified_report_digest.value,
                "batch_digest": batch_digest.value,
                "verified_batch_digest": verified_batch_digest.value,
                "closure_digest": closure_digest.value,
                "verified_closure_digest": verified_closure_digest.value,
                "read_set_digest": read_set_digest.value,
                "verified_read_set_digest": verified_read_set_digest.value,
                "provenance_digest": provenance_digest.value,
                "verification_context_digest": verification_context_digest.value,
                "artifact_use_confirmation_id": artifact_use_confirmation_id.value,
                "artifact_use_confirmation_digest": (
                    artifact_use_confirmation_digest.value
                ),
                "verifier_authority_id": verifier_authority_id.value,
                "verifier_ref": _text(verifier_ref, "Admission verifier ref"),
                "findings": normalized_findings_value(findings),
                "assessed_at": assessed_at,
            },
        ]
    )


def structure_admission_decision_digest(
    *,
    admission_id: StableId,
    outcome: StructureAdmissionOutcome,
    candidate_ref: str,
    candidate_digest: Digest,
    batch_digest: Digest,
    closure_digest: Digest,
    read_set_digest: Digest,
    scope_id: StableId,
    expected_scope_revision: Revision,
    scope_assertion_digest: Digest,
    expected_current_snapshot_id: StableId | None,
    schema_ref: str,
    schema_digest: Digest,
    schema_registration_digest: Digest,
    schema_availability_digest: Digest,
    knowledge_context_digest: Digest,
    upstream_digest: Digest,
    provenance_digest: Digest,
    artifact_use_confirmation_id: StableId,
    artifact_use_confirmation_digest: Digest,
    verifier_assessment_id: StableId,
    verifier_assessment_digest: Digest,
    verifier_authority_id: StableId,
    verifier_ref: str,
    findings: tuple[StructureAdmissionFinding, ...],
    decided_at: datetime,
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_ADMISSION_DECISION@3",
            {
                "admission_id": admission_id.value,
                "outcome": outcome.value,
                "candidate_ref": _text(candidate_ref, "Structure candidate ref"),
                "candidate_digest": candidate_digest.value,
                "batch_digest": batch_digest.value,
                "closure_digest": closure_digest.value,
                "read_set_digest": read_set_digest.value,
                "scope_id": scope_id.value,
                "expected_scope_revision": expected_scope_revision.value,
                "scope_assertion_digest": scope_assertion_digest.value,
                "expected_current_snapshot_id": (
                    expected_current_snapshot_id.value
                    if expected_current_snapshot_id is not None
                    else None
                ),
                "schema_ref": _text(schema_ref, "Schema ref"),
                "schema_digest": schema_digest.value,
                "schema_registration_digest": schema_registration_digest.value,
                "schema_availability_digest": schema_availability_digest.value,
                "knowledge_context_digest": knowledge_context_digest.value,
                "upstream_digest": upstream_digest.value,
                "provenance_digest": provenance_digest.value,
                "artifact_use_confirmation_id": artifact_use_confirmation_id.value,
                "artifact_use_confirmation_digest": (
                    artifact_use_confirmation_digest.value
                ),
                "verifier_assessment_id": verifier_assessment_id.value,
                "verifier_assessment_digest": verifier_assessment_digest.value,
                "verifier_authority_id": verifier_authority_id.value,
                "verifier_ref": _text(verifier_ref, "Admission verifier ref"),
                "findings": normalized_findings_value(findings),
                "decided_at": decided_at,
            },
        ]
    )


def structure_schema_registration_digest(
    *,
    registration_id: StableId,
    definition: StructureSchemaDefinition,
    proposal_ref: str,
    review_ref: str,
    registered_by: str,
    reason: str,
    registered_at: datetime,
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_SCHEMA_REGISTRATION@1",
            {
                "registration_id": registration_id.value,
                "definition_digest": definition.digest.value,
                "proposal_ref": _text(proposal_ref, "Schema Proposal ref"),
                "review_ref": _text(review_ref, "Schema Review ref"),
                "registered_by": _text(registered_by, "Schema registrar"),
                "reason": _text(reason, "Schema registration reason"),
                "registered_at": registered_at,
            },
        ]
    )


def structure_schema_availability_digest(
    *,
    availability_id: StableId,
    schema_ref: str,
    schema_digest: Digest,
    registration_id: StableId,
    availability_revision: Revision,
    status: StructureSchemaAvailabilityStatus,
    changed_by: str,
    reason: str,
    changed_at: datetime,
    previous_availability_id: StableId | None,
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_SCHEMA_AVAILABILITY@1",
            {
                "availability_id": availability_id.value,
                "schema_ref": _text(schema_ref, "Schema ref"),
                "schema_digest": schema_digest.value,
                "registration_id": registration_id.value,
                "availability_revision": availability_revision.value,
                "status": status.value,
                "changed_by": _text(changed_by, "Schema authority actor"),
                "reason": _text(reason, "Schema availability reason"),
                "changed_at": changed_at,
                "previous_availability_id": (
                    previous_availability_id.value
                    if previous_availability_id is not None
                    else None
                ),
            },
        ]
    )


def structure_schema_adoption_digest(
    *,
    scope_id: StableId,
    schema_ref: str,
    schema_digest: Digest,
    registration_id: StableId,
    initial_availability_id: StableId,
    initial_snapshot_id: StableId,
    adopted_at: datetime,
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_SCHEMA_ADOPTION@1",
            {
                "scope_id": scope_id.value,
                "schema_ref": _text(schema_ref, "Schema ref"),
                "schema_digest": schema_digest.value,
                "registration_id": registration_id.value,
                "initial_availability_id": initial_availability_id.value,
                "initial_snapshot_id": initial_snapshot_id.value,
                "adopted_at": adopted_at,
            },
        ]
    )


def normalized_findings_value(
    findings: Sequence[StructureAdmissionFinding],
) -> tuple[tuple[str, str], ...]:
    normalized = tuple(sorted((item.code, item.message) for item in findings))
    if len(set(normalized)) != len(normalized):
        raise _invalid(
            "ADMISSION_FINDINGS_DUPLICATE",
            "Admission findings must be unique",
        )
    return normalized


def _now(clock: Callable[[], datetime]) -> datetime:
    value = clock()
    if value.tzinfo is None or value.utcoffset() is None:
        raise _invalid(
            "AUTHORITY_TIMEZONE_REQUIRED",
            "Structure authority clock must return a timezone-aware value",
        )
    return value.astimezone(timezone.utc)


def _require_digest(value: object, label: str) -> None:
    if not isinstance(value, Digest):
        raise _invalid("DIGEST_REQUIRED", f"{label} must be typed")


def _require_time(value: object, label: str) -> None:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise _invalid("AUTHORITY_TIMEZONE_REQUIRED", f"{label} must include timezone")


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
    "StructureArtifactUseProofVerifier",
    "StructureCandidateVerifier",
    "StructureAdmissionDecision",
    "StructureAdmissionFinding",
    "StructureAdmissionOutcome",
    "StructureAdmissionService",
    "StructureAuthorityRepository",
    "StructureVerifierAssessment",
    "StructureVerifierAssessmentOutcome",
    "StructureVerifierAuthority",
    "StructureVerificationCandidate",
    "StructureVerificationResult",
    "StructureVerifierAssessmentService",
    "StructureSchemaAdoption",
    "StructureSchemaAdoptionMode",
    "StructureSchemaAvailability",
    "StructureSchemaAvailabilityStatus",
    "StructureSchemaDefinition",
    "StructureSchemaDependency",
    "StructureSchemaRegistration",
    "StructureSchemaRegistryService",
    "structure_admission_decision_digest",
    "structure_batch_digest",
    "structure_closure_digest",
    "structure_read_set_digest",
    "structure_schema_adoption_digest",
    "structure_schema_availability_digest",
    "structure_schema_registration_digest",
    "structure_upstream_digest",
    "structure_verifier_assessment_digest",
    "structure_verifier_assessment_findings",
]
