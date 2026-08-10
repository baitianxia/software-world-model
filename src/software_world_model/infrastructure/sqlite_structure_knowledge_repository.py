"""Additive SQLite authority for typed Structure Snapshot publication."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3
from threading import Lock

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    IdempotencyKey,
    Revision,
    StableId,
    Uuid4IdGenerator,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.knowledge_engine.structure import (
    CanonicalFields,
    CompleteMemberManifest,
    CoverageMember,
    CoverageMemberKind,
    CoverageRecord,
    CoverageRoot,
    CoverageState,
    EntityRecord,
    EntityRef,
    EntityRoot,
    EntityState,
    EntityType,
    LiteralFactRecord,
    LiteralFactRoot,
    LiteralFactState,
    LiteralObject,
    LiteralType,
    ObservationModality,
    PublicationMode,
    RelationFactRecord,
    RelationFactRoot,
    RelationFactState,
    RelationPredicate,
    StructureEvidence,
    StructureKnowledgeBatch,
)
from software_world_model.knowledge_engine.structure_publication import (
    ApplicationAcceptanceDecision,
    SnapshotCoverage,
    SnapshotUpstreamEntity,
    StructureApplicationAcceptance,
    StructureEvidenceMetadata,
    StructurePublicationReceipt,
    StructureSnapshot,
    structure_batch_digest,
)
from software_world_model.knowledge_engine.structure_authority import (
    StructureAdmissionDecision,
    StructureAdmissionFinding,
    StructureAdmissionOutcome,
    StructureVerifierAssessment,
    StructureVerifierAssessmentOutcome,
    StructureVerifierAuthority,
    StructureSchemaAdoption,
    StructureSchemaAdoptionMode,
    StructureSchemaAvailability,
    StructureSchemaAvailabilityStatus,
    StructureSchemaDefinition,
    StructureSchemaDependency,
    StructureSchemaRegistration,
    normalized_findings_value,
    structure_admission_decision_digest,
    structure_closure_digest,
    structure_read_set_digest,
    structure_schema_adoption_digest,
    structure_schema_availability_digest,
    structure_schema_registration_digest,
    structure_upstream_digest,
    structure_verifier_assessment_digest,
    structure_verifier_assessment_findings,
)
from software_world_model.knowledge_engine.scope import ScopeLifecycle, ScopeType

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS knw_structure_schema_registrations (
    registration_id TEXT PRIMARY KEY,
    schema_ref TEXT NOT NULL UNIQUE,
    schema_digest TEXT NOT NULL,
    eligible_scope_types_json TEXT NOT NULL,
    definition_digest TEXT NOT NULL,
    proposal_ref TEXT NOT NULL,
    review_ref TEXT NOT NULL,
    registered_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    registered_at TEXT NOT NULL,
    registration_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knw_structure_schema_dependencies (
    schema_ref TEXT NOT NULL,
    dependency_schema_ref TEXT NOT NULL,
    dependency_schema_digest TEXT NOT NULL,
    PRIMARY KEY (schema_ref, dependency_schema_ref),
    FOREIGN KEY (schema_ref) REFERENCES knw_structure_schema_registrations(schema_ref),
    FOREIGN KEY (dependency_schema_ref) REFERENCES knw_structure_schema_registrations(schema_ref)
);

CREATE TABLE IF NOT EXISTS knw_structure_schema_availability_roots (
    schema_ref TEXT PRIMARY KEY,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    current_availability_id TEXT NOT NULL UNIQUE,
    FOREIGN KEY (schema_ref) REFERENCES knw_structure_schema_registrations(schema_ref)
);

CREATE TABLE IF NOT EXISTS knw_structure_schema_availabilities (
    availability_id TEXT PRIMARY KEY,
    schema_ref TEXT NOT NULL,
    schema_digest TEXT NOT NULL,
    registration_id TEXT NOT NULL,
    availability_revision INTEGER NOT NULL CHECK (availability_revision >= 1),
    status TEXT NOT NULL CHECK (status IN ('AVAILABLE', 'DEPRECATED')),
    changed_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    changed_at TEXT NOT NULL,
    previous_availability_id TEXT,
    availability_digest TEXT NOT NULL,
    UNIQUE (schema_ref, availability_revision),
    FOREIGN KEY (schema_ref) REFERENCES knw_structure_schema_registrations(schema_ref),
    FOREIGN KEY (registration_id) REFERENCES knw_structure_schema_registrations(registration_id),
    FOREIGN KEY (previous_availability_id) REFERENCES knw_structure_schema_availabilities(availability_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_schema_commands (
    idempotency_key TEXT PRIMARY KEY,
    command_type TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    result_registration_id TEXT,
    result_availability_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knw_structure_verifier_authorities (
    authority_id TEXT PRIMARY KEY,
    verifier_ref TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knw_structure_verifier_authority_roots (
    verifier_ref TEXT PRIMARY KEY,
    authority_id TEXT NOT NULL UNIQUE,
    FOREIGN KEY (authority_id)
        REFERENCES knw_structure_verifier_authorities(authority_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_verifier_assessments (
    assessment_id TEXT PRIMARY KEY,
    outcome TEXT NOT NULL CHECK (outcome IN ('PASS', 'FAIL')),
    candidate_ref TEXT NOT NULL,
    candidate_digest TEXT NOT NULL,
    verified_candidate_digest TEXT NOT NULL,
    candidate_evaluation_digest TEXT NOT NULL,
    verified_evaluation_digest TEXT NOT NULL,
    candidate_report_digest TEXT NOT NULL,
    verified_report_digest TEXT NOT NULL,
    batch_digest TEXT NOT NULL,
    verified_batch_digest TEXT NOT NULL,
    closure_digest TEXT NOT NULL,
    verified_closure_digest TEXT NOT NULL,
    read_set_digest TEXT NOT NULL,
    verified_read_set_digest TEXT NOT NULL,
    provenance_digest TEXT NOT NULL,
    verification_context_digest TEXT NOT NULL,
    artifact_use_confirmation_id TEXT NOT NULL,
    artifact_use_confirmation_digest TEXT NOT NULL,
    verifier_authority_id TEXT NOT NULL,
    verifier_ref TEXT NOT NULL,
    findings_json TEXT NOT NULL,
    assessed_at TEXT NOT NULL,
    assessment_digest TEXT NOT NULL,
    FOREIGN KEY (verifier_authority_id)
        REFERENCES knw_structure_verifier_authorities(authority_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_verifier_assessment_commands (
    idempotency_key TEXT PRIMARY KEY,
    request_digest TEXT NOT NULL,
    result_assessment_id TEXT NOT NULL,
    FOREIGN KEY (result_assessment_id)
        REFERENCES knw_structure_verifier_assessments(assessment_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_admissions (
    admission_id TEXT PRIMARY KEY,
    outcome TEXT NOT NULL CHECK (outcome IN ('ACCEPT', 'REJECT')),
    candidate_ref TEXT NOT NULL,
    candidate_digest TEXT NOT NULL,
    batch_digest TEXT NOT NULL,
    closure_digest TEXT NOT NULL,
    read_set_digest TEXT NOT NULL,
    scope_id TEXT NOT NULL,
    expected_scope_revision INTEGER NOT NULL CHECK (expected_scope_revision >= 1),
    scope_assertion_digest TEXT NOT NULL,
    expected_current_snapshot_id TEXT,
    schema_ref TEXT NOT NULL,
    schema_digest TEXT NOT NULL,
    schema_registration_digest TEXT NOT NULL,
    schema_availability_digest TEXT NOT NULL,
    knowledge_context_digest TEXT NOT NULL,
    upstream_digest TEXT NOT NULL,
    provenance_digest TEXT NOT NULL,
    artifact_use_confirmation_id TEXT NOT NULL,
    artifact_use_confirmation_digest TEXT NOT NULL,
    verifier_assessment_id TEXT NOT NULL,
    verifier_assessment_digest TEXT NOT NULL,
    verifier_authority_id TEXT NOT NULL,
    verifier_ref TEXT NOT NULL,
    findings_json TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    admission_digest TEXT NOT NULL,
    FOREIGN KEY (schema_ref) REFERENCES knw_structure_schema_registrations(schema_ref),
    FOREIGN KEY (verifier_assessment_id)
        REFERENCES knw_structure_verifier_assessments(assessment_id),
    FOREIGN KEY (verifier_authority_id)
        REFERENCES knw_structure_verifier_authorities(authority_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_admission_commands (
    idempotency_key TEXT PRIMARY KEY,
    request_digest TEXT NOT NULL,
    result_admission_id TEXT NOT NULL,
    FOREIGN KEY (result_admission_id) REFERENCES knw_structure_admissions(admission_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_evidence (
    evidence_id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    source_context_id TEXT NOT NULL,
    byte_start INTEGER NOT NULL,
    byte_end INTEGER NOT NULL,
    locator TEXT NOT NULL,
    excerpt TEXT NOT NULL,
    excerpt_digest TEXT NOT NULL,
    artifact_content_digest TEXT NOT NULL,
    evidence_digest TEXT NOT NULL,
    record_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knw_structure_entity_roots (
    entity_root_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    identity_scheme TEXT NOT NULL,
    root_fields_json TEXT NOT NULL,
    allocation_key_digest TEXT NOT NULL,
    record_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knw_structure_entity_states (
    entity_state_id TEXT PRIMARY KEY,
    entity_root_id TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    state_payload_json TEXT NOT NULL,
    state_digest TEXT NOT NULL,
    allocation_key_digest TEXT NOT NULL,
    record_digest TEXT NOT NULL,
    FOREIGN KEY (entity_root_id) REFERENCES knw_structure_entity_roots(entity_root_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_relation_roots (
    relation_root_id TEXT PRIMARY KEY,
    owning_scope_id TEXT NOT NULL,
    schema_ref TEXT NOT NULL,
    subject_entity_root_id TEXT NOT NULL,
    subject_entity_type TEXT NOT NULL,
    subject_owning_scope_id TEXT NOT NULL,
    predicate TEXT NOT NULL,
    object_entity_root_id TEXT NOT NULL,
    object_entity_type TEXT NOT NULL,
    object_owning_scope_id TEXT NOT NULL,
    observation_modality TEXT NOT NULL,
    allocation_key_digest TEXT NOT NULL,
    record_digest TEXT NOT NULL,
    FOREIGN KEY (subject_entity_root_id) REFERENCES knw_structure_entity_roots(entity_root_id),
    FOREIGN KEY (object_entity_root_id) REFERENCES knw_structure_entity_roots(entity_root_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_relation_states (
    relation_state_id TEXT PRIMARY KEY,
    relation_root_id TEXT NOT NULL,
    subject_entity_state_id TEXT NOT NULL,
    object_entity_state_id TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    knowledge_context_digest TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL,
    predicate_state_payload_json TEXT NOT NULL,
    state_digest TEXT NOT NULL,
    allocation_key_digest TEXT NOT NULL,
    record_digest TEXT NOT NULL,
    FOREIGN KEY (relation_root_id) REFERENCES knw_structure_relation_roots(relation_root_id),
    FOREIGN KEY (subject_entity_state_id) REFERENCES knw_structure_entity_states(entity_state_id),
    FOREIGN KEY (object_entity_state_id) REFERENCES knw_structure_entity_states(entity_state_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_literal_roots (
    literal_root_id TEXT PRIMARY KEY,
    owning_scope_id TEXT NOT NULL,
    schema_ref TEXT NOT NULL,
    subject_entity_root_id TEXT NOT NULL,
    subject_entity_type TEXT NOT NULL,
    subject_owning_scope_id TEXT NOT NULL,
    predicate TEXT NOT NULL,
    literal_type TEXT NOT NULL,
    literal_value_json TEXT NOT NULL,
    observation_modality TEXT NOT NULL,
    allocation_key_digest TEXT NOT NULL,
    record_digest TEXT NOT NULL,
    FOREIGN KEY (subject_entity_root_id) REFERENCES knw_structure_entity_roots(entity_root_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_literal_states (
    literal_state_id TEXT PRIMARY KEY,
    literal_root_id TEXT NOT NULL,
    subject_entity_state_id TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    knowledge_context_digest TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL,
    state_digest TEXT NOT NULL,
    allocation_key_digest TEXT NOT NULL,
    record_digest TEXT NOT NULL,
    FOREIGN KEY (literal_root_id) REFERENCES knw_structure_literal_roots(literal_root_id),
    FOREIGN KEY (subject_entity_state_id) REFERENCES knw_structure_entity_states(entity_state_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_coverage_roots (
    coverage_root_id TEXT PRIMARY KEY,
    coverage_root_ref TEXT NOT NULL,
    owning_scope_id TEXT NOT NULL,
    profile_ref TEXT NOT NULL,
    schema_ref TEXT NOT NULL,
    schema_digest TEXT NOT NULL,
    source_binding_id TEXT NOT NULL,
    logical_reactor_root TEXT NOT NULL,
    evaluation_context_ref TEXT NOT NULL,
    evaluation_context_digest TEXT NOT NULL,
    covered_entity_types_json TEXT NOT NULL,
    covered_relation_predicates_json TEXT NOT NULL,
    canonicalization_ref TEXT NOT NULL,
    canonicalization_digest TEXT NOT NULL,
    allocation_key_digest TEXT NOT NULL,
    record_digest TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS knw_structure_coverage_states (
    coverage_state_id TEXT PRIMARY KEY,
    coverage_root_id TEXT NOT NULL,
    source_revision TEXT NOT NULL,
    knowledge_context_digest TEXT NOT NULL,
    schema_ref TEXT NOT NULL,
    schema_digest TEXT NOT NULL,
    evaluation_context_ref TEXT NOT NULL,
    evaluation_context_digest TEXT NOT NULL,
    canonicalization_ref TEXT NOT NULL,
    canonicalization_digest TEXT NOT NULL,
    member_manifest_json TEXT NOT NULL,
    member_manifest_digest TEXT NOT NULL,
    evidence_refs_json TEXT NOT NULL,
    state_digest TEXT NOT NULL,
    allocation_key_digest TEXT NOT NULL,
    record_digest TEXT NOT NULL,
    FOREIGN KEY (coverage_root_id) REFERENCES knw_structure_coverage_roots(coverage_root_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_snapshot_roots (
    scope_id TEXT PRIMARY KEY,
    current_snapshot_id TEXT NOT NULL UNIQUE,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1)
);

CREATE TABLE IF NOT EXISTS knw_structure_schema_adoptions (
    scope_id TEXT PRIMARY KEY,
    schema_ref TEXT NOT NULL,
    schema_digest TEXT NOT NULL,
    registration_id TEXT NOT NULL,
    initial_availability_id TEXT NOT NULL,
    initial_snapshot_id TEXT NOT NULL UNIQUE,
    adopted_at TEXT NOT NULL,
    adoption_digest TEXT NOT NULL,
    FOREIGN KEY (schema_ref) REFERENCES knw_structure_schema_registrations(schema_ref),
    FOREIGN KEY (registration_id) REFERENCES knw_structure_schema_registrations(registration_id),
    FOREIGN KEY (initial_availability_id) REFERENCES knw_structure_schema_availabilities(availability_id),
    FOREIGN KEY (initial_snapshot_id) REFERENCES knw_structure_snapshots(snapshot_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_snapshots (
    snapshot_id TEXT PRIMARY KEY,
    scope_id TEXT NOT NULL,
    snapshot_revision INTEGER NOT NULL CHECK (snapshot_revision >= 1),
    previous_snapshot_id TEXT,
    schema_ref TEXT NOT NULL,
    schema_digest TEXT NOT NULL,
    schema_adoption_mode TEXT NOT NULL CHECK (schema_adoption_mode IN ('INITIAL', 'UNCHANGED')),
    schema_registration_digest TEXT NOT NULL,
    schema_availability_digest TEXT NOT NULL,
    schema_adoption_digest TEXT NOT NULL,
    publication_mode TEXT NOT NULL,
    manifest_digest TEXT NOT NULL,
    published_at TEXT NOT NULL,
    UNIQUE (scope_id, snapshot_revision),
    FOREIGN KEY (previous_snapshot_id) REFERENCES knw_structure_snapshots(snapshot_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_snapshot_members (
    snapshot_id TEXT NOT NULL,
    member_kind TEXT NOT NULL,
    root_id TEXT NOT NULL,
    state_id TEXT NOT NULL,
    state_digest TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, root_id),
    FOREIGN KEY (snapshot_id) REFERENCES knw_structure_snapshots(snapshot_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_snapshot_coverages (
    snapshot_id TEXT NOT NULL,
    coverage_root_id TEXT NOT NULL,
    coverage_state_id TEXT NOT NULL,
    coverage_state_digest TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, coverage_root_id),
    FOREIGN KEY (snapshot_id) REFERENCES knw_structure_snapshots(snapshot_id),
    FOREIGN KEY (coverage_root_id) REFERENCES knw_structure_coverage_roots(coverage_root_id),
    FOREIGN KEY (coverage_state_id) REFERENCES knw_structure_coverage_states(coverage_state_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_snapshot_ownership (
    snapshot_id TEXT NOT NULL,
    root_id TEXT NOT NULL,
    member_kind TEXT NOT NULL,
    coverage_root_id TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, root_id),
    FOREIGN KEY (snapshot_id) REFERENCES knw_structure_snapshots(snapshot_id),
    FOREIGN KEY (coverage_root_id) REFERENCES knw_structure_coverage_roots(coverage_root_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_snapshot_upstream_entities (
    snapshot_id TEXT NOT NULL,
    upstream_snapshot_id TEXT NOT NULL,
    entity_root_id TEXT NOT NULL,
    entity_state_id TEXT NOT NULL,
    entity_state_digest TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, entity_root_id),
    FOREIGN KEY (snapshot_id) REFERENCES knw_structure_snapshots(snapshot_id),
    FOREIGN KEY (upstream_snapshot_id) REFERENCES knw_structure_snapshots(snapshot_id),
    FOREIGN KEY (entity_root_id) REFERENCES knw_structure_entity_roots(entity_root_id),
    FOREIGN KEY (entity_state_id) REFERENCES knw_structure_entity_states(entity_state_id)
);

CREATE TABLE IF NOT EXISTS knw_structure_publications (
    publication_id TEXT PRIMARY KEY,
    scope_id TEXT NOT NULL,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    batch_digest TEXT NOT NULL,
    admission_id TEXT NOT NULL,
    admission_digest TEXT NOT NULL,
    application_acceptance_digest TEXT NOT NULL,
    application_acceptance_ref TEXT NOT NULL,
    application_acceptance_decision TEXT NOT NULL,
    application_report_digest TEXT NOT NULL,
    snapshot_id TEXT NOT NULL UNIQUE,
    published_at TEXT NOT NULL,
    result_digest TEXT NOT NULL,
    FOREIGN KEY (snapshot_id) REFERENCES knw_structure_snapshots(snapshot_id),
    FOREIGN KEY (admission_id) REFERENCES knw_structure_admissions(admission_id)
);
"""


class SqliteStructureKnowledgeRepository:
    def __init__(
        self,
        database: SqliteDatabase,
        *,
        id_generator: IdGenerator | None = None,
    ) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._verifier_authority_lock = Lock()
        self._verifier_authorities: dict[str, StructureVerifierAuthority] = {}
        self._admission_authorities: dict[str, StructureVerifierAuthority] = {}
        self._database.executescript(_SCHEMA)

    def register_structure_verifier_authority(
        self, *, verifier_ref: str
    ) -> StructureVerifierAuthority:
        if (
            not isinstance(verifier_ref, str)
            or not verifier_ref
            or verifier_ref != verifier_ref.strip()
        ):
            raise _invalid(
                "VERIFIER_AUTHORITY_REF_INVALID",
                "Structure verifier authority ref must be non-empty and canonical",
            )
        with self._verifier_authority_lock:
            try:
                with self._database.transaction() as connection:
                    primary = self._admission_authorities.get(verifier_ref)
                    if primary is None:
                        row = connection.execute(
                            """SELECT authority_id
                               FROM knw_structure_verifier_authority_roots
                               WHERE verifier_ref = ?""",
                            (verifier_ref,),
                        ).fetchone()
                        if row is None:
                            authority = StructureVerifierAuthority(
                                authority_id=self._ids.new("verifier_authority"),
                                verifier_ref=verifier_ref,
                            )
                            authority.require_valid()
                            connection.execute(
                                "INSERT INTO knw_structure_verifier_authorities VALUES (?, ?)",
                                (authority.authority_id.value, authority.verifier_ref),
                            )
                            connection.execute(
                                "INSERT INTO knw_structure_verifier_authority_roots VALUES (?, ?)",
                                (authority.verifier_ref, authority.authority_id.value),
                            )
                        else:
                            authority = StructureVerifierAuthority(
                                authority_id=StableId(row["authority_id"]),
                                verifier_ref=verifier_ref,
                            )
                            authority.require_valid()
                            authority_row = connection.execute(
                                """SELECT verifier_ref
                                   FROM knw_structure_verifier_authorities
                                   WHERE authority_id = ?""",
                                (authority.authority_id.value,),
                            ).fetchone()
                            if (
                                authority_row is None
                                or authority_row["verifier_ref"] != verifier_ref
                            ):
                                raise _inconsistent(
                                    "Structure verifier authority root is inconsistent"
                                )
                        self._admission_authorities[verifier_ref] = authority
                    else:
                        authority = StructureVerifierAuthority(
                            authority_id=self._ids.new("verifier_authority"),
                            verifier_ref=verifier_ref,
                        )
                        authority.require_valid()
                        connection.execute(
                            "INSERT INTO knw_structure_verifier_authorities VALUES (?, ?)",
                            (authority.authority_id.value, authority.verifier_ref),
                        )
            except sqlite3.IntegrityError as exc:
                raise _inconsistent(
                    "Structure verifier authority registration ID collided"
                ) from exc
            self._verifier_authorities[authority.authority_id.value] = authority
            return authority

    def _require_registered_verifier_authority(
        self,
        connection: sqlite3.Connection,
        authority: StructureVerifierAuthority,
        *,
        require_admission_authority: bool = False,
    ) -> None:
        if not isinstance(authority, StructureVerifierAuthority):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Structure verifier capability is not registered",
                {"reason_code": "VERIFIER_AUTHORITY_CAPABILITY_INVALID"},
            )
        authority.require_valid()
        registered = self._verifier_authorities.get(authority.authority_id.value)
        row = connection.execute(
            "SELECT verifier_ref FROM knw_structure_verifier_authorities WHERE authority_id = ?",
            (authority.authority_id.value,),
        ).fetchone()
        if (
            registered is not authority
            or row is None
            or row["verifier_ref"] != authority.verifier_ref
            or (
                require_admission_authority
                and self._admission_authorities.get(authority.verifier_ref)
                is not authority
            )
        ):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Structure verifier capability is not registered",
                {
                    "reason_code": (
                        "VERIFIER_ADMISSION_AUTHORITY_DENIED"
                        if require_admission_authority
                        else "VERIFIER_AUTHORITY_CAPABILITY_INVALID"
                    )
                },
            )

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
    ) -> tuple[StructureSchemaRegistration, StructureSchemaAvailability]:
        definition.require_valid()
        try:
            with self._database.transaction() as connection:
                replay = self._schema_command_result(
                    connection, idempotency_key, request_digest
                )
                if replay is not None:
                    return replay
                existing = connection.execute(
                    "SELECT registration_id FROM knw_structure_schema_registrations WHERE schema_ref = ?",
                    (definition.schema_ref,),
                ).fetchone()
                if existing is not None:
                    registered = self._load_schema_registration(
                        connection, definition.schema_ref
                    )
                    if (
                        registered.definition != definition
                        or registered.proposal_ref != proposal_ref
                        or registered.review_ref != review_ref
                        or registered.registered_by != registered_by
                        or registered.reason != reason
                    ):
                        raise _invalid(
                            "SCHEMA_REGISTRATION_IMMUTABILITY_VIOLATION",
                            "an exact Schema ref cannot be registered with new content",
                        )
                    availability = self._load_schema_availability(
                        connection, definition.schema_ref, None
                    )
                    self._insert_schema_command(
                        connection,
                        idempotency_key=idempotency_key,
                        command_type="REGISTER@1",
                        request_digest=request_digest,
                        registration_id=registered.registration_id,
                        availability_id=availability.availability_id,
                    )
                    return registered, availability
                for dependency in definition.dependencies:
                    registered_dependency = self._load_schema_registration(
                        connection, dependency.schema_ref
                    )
                    if (
                        registered_dependency.definition.schema_digest
                        != dependency.schema_digest
                    ):
                        raise _invalid(
                            "SCHEMA_DEPENDENCY_DIGEST_MISMATCH",
                            "Schema dependency does not match its registered digest",
                        )
                registration_id = self._ids.new("schema_registration")
                registration_digest = structure_schema_registration_digest(
                    registration_id=registration_id,
                    definition=definition,
                    proposal_ref=proposal_ref,
                    review_ref=review_ref,
                    registered_by=registered_by,
                    reason=reason,
                    registered_at=registered_at,
                )
                registration = StructureSchemaRegistration(
                    registration_id=registration_id,
                    definition=definition,
                    proposal_ref=proposal_ref,
                    review_ref=review_ref,
                    registered_by=registered_by,
                    reason=reason,
                    registered_at=registered_at,
                    digest=registration_digest,
                )
                registration.require_valid()
                connection.execute(
                    """INSERT INTO knw_structure_schema_registrations VALUES
                       (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        registration_id.value,
                        definition.schema_ref,
                        definition.schema_digest.value,
                        _json(tuple(item.value for item in definition.eligible_scope_types)),
                        definition.digest.value,
                        proposal_ref,
                        review_ref,
                        registered_by,
                        reason,
                        _time(registered_at),
                        registration_digest.value,
                    ),
                )
                for dependency in definition.dependencies:
                    connection.execute(
                        "INSERT INTO knw_structure_schema_dependencies VALUES (?, ?, ?)",
                        (
                            definition.schema_ref,
                            dependency.schema_ref,
                            dependency.schema_digest.value,
                        ),
                    )
                availability_id = self._ids.new("schema_availability")
                availability_digest = structure_schema_availability_digest(
                    availability_id=availability_id,
                    schema_ref=definition.schema_ref,
                    schema_digest=definition.schema_digest,
                    registration_id=registration_id,
                    availability_revision=Revision(1),
                    status=StructureSchemaAvailabilityStatus.AVAILABLE,
                    changed_by=registered_by,
                    reason=reason,
                    changed_at=registered_at,
                    previous_availability_id=None,
                )
                availability = StructureSchemaAvailability(
                    availability_id=availability_id,
                    schema_ref=definition.schema_ref,
                    schema_digest=definition.schema_digest,
                    registration_id=registration_id,
                    availability_revision=Revision(1),
                    status=StructureSchemaAvailabilityStatus.AVAILABLE,
                    changed_by=registered_by,
                    reason=reason,
                    changed_at=registered_at,
                    previous_availability_id=None,
                    digest=availability_digest,
                )
                availability.require_valid()
                self._insert_schema_availability(connection, availability)
                connection.execute(
                    "INSERT INTO knw_structure_schema_availability_roots VALUES (?, ?, ?)",
                    (definition.schema_ref, 1, availability_id.value),
                )
                self._insert_schema_command(
                    connection,
                    idempotency_key=idempotency_key,
                    command_type="REGISTER@1",
                    request_digest=request_digest,
                    registration_id=registration_id,
                    availability_id=availability_id,
                )
                return registration, availability
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _inconsistent(
                f"Schema registration violated an authority invariant: {exc}"
            ) from exc

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
    ) -> StructureSchemaAvailability:
        try:
            with self._database.transaction() as connection:
                replay = self._schema_command_result(
                    connection, idempotency_key, request_digest
                )
                if replay is not None:
                    return replay[1]
                registration = self._load_schema_registration(connection, schema_ref)
                current = self._load_schema_availability(connection, schema_ref, None)
                if registration.definition.schema_digest != schema_digest:
                    raise _invalid(
                        "SCHEMA_DIGEST_MISMATCH",
                        "Schema deprecation requires the exact registered digest",
                    )
                if current.availability_revision != expected_availability_revision:
                    raise DomainError(
                        ErrorCode.REVISION_CONFLICT,
                        "Schema Availability changed before deprecation",
                    )
                if current.status is StructureSchemaAvailabilityStatus.DEPRECATED:
                    raise _invalid(
                        "SCHEMA_ALREADY_DEPRECATED",
                        "deprecated exact Schema refs cannot be enabled or deprecated again",
                    )
                availability_id = self._ids.new("schema_availability")
                revision = current.availability_revision.next()
                availability = StructureSchemaAvailability(
                    availability_id=availability_id,
                    schema_ref=schema_ref,
                    schema_digest=schema_digest,
                    registration_id=registration.registration_id,
                    availability_revision=revision,
                    status=StructureSchemaAvailabilityStatus.DEPRECATED,
                    changed_by=changed_by,
                    reason=reason,
                    changed_at=changed_at,
                    previous_availability_id=current.availability_id,
                    digest=structure_schema_availability_digest(
                        availability_id=availability_id,
                        schema_ref=schema_ref,
                        schema_digest=schema_digest,
                        registration_id=registration.registration_id,
                        availability_revision=revision,
                        status=StructureSchemaAvailabilityStatus.DEPRECATED,
                        changed_by=changed_by,
                        reason=reason,
                        changed_at=changed_at,
                        previous_availability_id=current.availability_id,
                    ),
                )
                availability.require_valid()
                self._insert_schema_availability(connection, availability)
                cursor = connection.execute(
                    """UPDATE knw_structure_schema_availability_roots
                       SET current_revision = ?, current_availability_id = ?
                       WHERE schema_ref = ? AND current_revision = ?
                         AND current_availability_id = ?""",
                    (
                        revision.value,
                        availability_id.value,
                        schema_ref,
                        current.availability_revision.value,
                        current.availability_id.value,
                    ),
                )
                if cursor.rowcount != 1:
                    raise DomainError(
                        ErrorCode.REVISION_CONFLICT,
                        "Schema Availability changed during deprecation",
                    )
                self._insert_schema_command(
                    connection,
                    idempotency_key=idempotency_key,
                    command_type="DEPRECATE@1",
                    request_digest=request_digest,
                    registration_id=registration.registration_id,
                    availability_id=availability_id,
                )
                return availability
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _inconsistent(
                f"Schema deprecation violated an authority invariant: {exc}"
            ) from exc

    def get_schema_registration(
        self, schema_ref: str
    ) -> StructureSchemaRegistration:
        with self._database.read() as connection:
            return self._load_schema_registration(connection, schema_ref)

    def get_schema_availability(
        self, schema_ref: str, revision: Revision | None = None
    ) -> StructureSchemaAvailability:
        with self._database.read() as connection:
            return self._load_schema_availability(connection, schema_ref, revision)

    def get_schema_adoption(
        self, scope_id: StableId
    ) -> StructureSchemaAdoption | None:
        with self._database.read() as connection:
            return self._load_schema_adoption(connection, scope_id)

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
    ) -> StructureVerifierAssessment:
        if not isinstance(verifier_authority, StructureVerifierAuthority):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Structure verifier capability is not registered",
                {"reason_code": "VERIFIER_AUTHORITY_CAPABILITY_INVALID"},
            )
        verifier_authority.require_valid()
        candidate_batch.require_admissible()
        verified_batch.require_admissible()
        batch_digest = structure_batch_digest(candidate_batch)
        verified_batch_digest = structure_batch_digest(verified_batch)
        closure_digest = structure_closure_digest(candidate_batch)
        verified_closure_digest = structure_closure_digest(verified_batch)
        read_set_digest = structure_read_set_digest(candidate_batch)
        verified_read_set_digest = structure_read_set_digest(verified_batch)
        canonical_findings = structure_verifier_assessment_findings(
            candidate_digest=candidate_digest,
            verified_candidate_digest=verified_candidate_digest,
            candidate_evaluation_digest=candidate_evaluation_digest,
            verified_evaluation_digest=verified_evaluation_digest,
            candidate_report_digest=candidate_report_digest,
            verified_report_digest=verified_report_digest,
            batch_digest=batch_digest,
            verified_batch_digest=verified_batch_digest,
            closure_digest=closure_digest,
            verified_closure_digest=verified_closure_digest,
            read_set_digest=read_set_digest,
            verified_read_set_digest=verified_read_set_digest,
            findings=findings,
        )
        if canonical_findings != findings:
            raise _invalid(
                "VERIFIER_ASSESSMENT_FINDINGS_INCOMPLETE",
                "Verifier Assessment findings do not cover every canonical mismatch",
            )
        outcome = (
            StructureVerifierAssessmentOutcome.FAIL
            if findings
            else StructureVerifierAssessmentOutcome.PASS
        )
        try:
            with self._database.transaction() as connection:
                self._require_registered_verifier_authority(
                    connection, verifier_authority
                )
                replay = self._verifier_assessment_command_result(
                    connection, idempotency_key, request_digest
                )
                if replay is not None:
                    return replay
                assessment_id = self._ids.new("structure_assessment")
                assessment_digest = structure_verifier_assessment_digest(
                    assessment_id=assessment_id,
                    outcome=outcome,
                    candidate_ref=candidate_ref,
                    candidate_digest=candidate_digest,
                    verified_candidate_digest=verified_candidate_digest,
                    candidate_evaluation_digest=candidate_evaluation_digest,
                    verified_evaluation_digest=verified_evaluation_digest,
                    candidate_report_digest=candidate_report_digest,
                    verified_report_digest=verified_report_digest,
                    batch_digest=batch_digest,
                    verified_batch_digest=verified_batch_digest,
                    closure_digest=closure_digest,
                    verified_closure_digest=verified_closure_digest,
                    read_set_digest=read_set_digest,
                    verified_read_set_digest=verified_read_set_digest,
                    provenance_digest=provenance_digest,
                    verification_context_digest=verification_context_digest,
                    artifact_use_confirmation_id=artifact_use_confirmation_id,
                    artifact_use_confirmation_digest=(
                        artifact_use_confirmation_digest
                    ),
                    verifier_authority_id=verifier_authority.authority_id,
                    verifier_ref=verifier_authority.verifier_ref,
                    findings=findings,
                    assessed_at=assessed_at,
                )
                assessment = StructureVerifierAssessment(
                    assessment_id=assessment_id,
                    outcome=outcome,
                    candidate_ref=candidate_ref,
                    candidate_digest=candidate_digest,
                    verified_candidate_digest=verified_candidate_digest,
                    candidate_evaluation_digest=candidate_evaluation_digest,
                    verified_evaluation_digest=verified_evaluation_digest,
                    candidate_report_digest=candidate_report_digest,
                    verified_report_digest=verified_report_digest,
                    batch_digest=batch_digest,
                    verified_batch_digest=verified_batch_digest,
                    closure_digest=closure_digest,
                    verified_closure_digest=verified_closure_digest,
                    read_set_digest=read_set_digest,
                    verified_read_set_digest=verified_read_set_digest,
                    provenance_digest=provenance_digest,
                    verification_context_digest=verification_context_digest,
                    artifact_use_confirmation_id=artifact_use_confirmation_id,
                    artifact_use_confirmation_digest=(
                        artifact_use_confirmation_digest
                    ),
                    verifier_authority_id=verifier_authority.authority_id,
                    verifier_ref=verifier_authority.verifier_ref,
                    findings=findings,
                    assessed_at=assessed_at,
                    digest=assessment_digest,
                )
                assessment.require_valid()
                connection.execute(
                    """INSERT INTO knw_structure_verifier_assessments
                       (assessment_id, outcome, candidate_ref, candidate_digest,
                        verified_candidate_digest, candidate_evaluation_digest,
                        verified_evaluation_digest, candidate_report_digest,
                        verified_report_digest, batch_digest,
                        verified_batch_digest, closure_digest,
                        verified_closure_digest, read_set_digest,
                        verified_read_set_digest, provenance_digest,
                        verification_context_digest,
                        artifact_use_confirmation_id,
                        artifact_use_confirmation_digest,
                        verifier_authority_id,
                        verifier_ref, findings_json,
                        assessed_at, assessment_digest)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        assessment_id.value,
                        outcome.value,
                        candidate_ref,
                        candidate_digest.value,
                        verified_candidate_digest.value,
                        candidate_evaluation_digest.value,
                        verified_evaluation_digest.value,
                        candidate_report_digest.value,
                        verified_report_digest.value,
                        batch_digest.value,
                        verified_batch_digest.value,
                        closure_digest.value,
                        verified_closure_digest.value,
                        read_set_digest.value,
                        verified_read_set_digest.value,
                        provenance_digest.value,
                        verification_context_digest.value,
                        artifact_use_confirmation_id.value,
                        artifact_use_confirmation_digest.value,
                        verifier_authority.authority_id.value,
                        verifier_authority.verifier_ref,
                        _json(normalized_findings_value(findings)),
                        _time(assessed_at),
                        assessment_digest.value,
                    ),
                )
                connection.execute(
                    """INSERT INTO knw_structure_verifier_assessment_commands
                       VALUES (?, ?, ?)""",
                    (
                        idempotency_key.value,
                        request_digest.value,
                        assessment_id.value,
                    ),
                )
                return assessment
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _inconsistent(
                f"Structure Verifier Assessment violated an authority invariant: {exc}"
            ) from exc

    def get_structure_verifier_assessment(
        self, assessment_id: StableId
    ) -> StructureVerifierAssessment:
        with self._database.read() as connection:
            return self._load_structure_verifier_assessment(
                connection, assessment_id
            )

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
    ) -> StructureAdmissionDecision:
        if not isinstance(verifier_authority, StructureVerifierAuthority):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Structure verifier capability is not registered",
                {"reason_code": "VERIFIER_AUTHORITY_CAPABILITY_INVALID"},
            )
        verifier_authority.require_valid()
        batch_digest = structure_batch_digest(batch)
        closure_digest = structure_closure_digest(batch)
        read_set_digest = structure_read_set_digest(batch)
        upstream_digest = structure_upstream_digest(batch)
        normalized_findings_value(findings)
        assessment.require_valid()
        if outcome is StructureAdmissionOutcome.ACCEPT:
            batch.require_admissible()
            if (
                findings
                or assessment.outcome
                is not StructureVerifierAssessmentOutcome.PASS
            ):
                raise _invalid(
                    "ADMISSION_ACCEPT_WITHOUT_VERIFIER_PASS",
                    "Admission ACCEPT requires a finding-free Verifier Assessment PASS",
                )
        elif (
            not findings
            or assessment.outcome is not StructureVerifierAssessmentOutcome.FAIL
            or findings != assessment.findings
        ):
            raise _invalid(
                "ADMISSION_REJECT_ASSESSMENT_MISMATCH",
                "Admission REJECT must preserve the Verifier Assessment FAIL findings",
            )
        try:
            with self._database.transaction() as connection:
                self._require_registered_verifier_authority(
                    connection,
                    verifier_authority,
                    require_admission_authority=True,
                )
                replay = self._admission_command_result(
                    connection, idempotency_key, request_digest
                )
                if replay is not None:
                    return replay
                stored_assessment = self._load_structure_verifier_assessment(
                    connection, assessment.assessment_id
                )
                if stored_assessment != assessment:
                    raise _invalid(
                        "VERIFIER_ASSESSMENT_PERSISTED_RECORD_MISMATCH",
                        "Admission assessment differs from persisted authority",
                    )
                assessment_bindings = (
                    (
                        stored_assessment.verifier_authority_id,
                        verifier_authority.authority_id,
                    ),
                    (stored_assessment.verifier_ref, verifier_authority.verifier_ref),
                    (stored_assessment.candidate_ref, candidate_ref),
                    (stored_assessment.candidate_digest, candidate_digest),
                    (stored_assessment.batch_digest, batch_digest),
                    (stored_assessment.closure_digest, closure_digest),
                    (stored_assessment.read_set_digest, read_set_digest),
                    (stored_assessment.provenance_digest, provenance_digest),
                    (stored_assessment.findings, findings),
                )
                if any(
                    actual != expected
                    for actual, expected in assessment_bindings
                ):
                    raise _invalid(
                        "VERIFIER_ASSESSMENT_CANDIDATE_MISMATCH",
                        "persisted Verifier Assessment binds another candidate closure",
                    )
                self._require_system_scope(
                    connection, scope_id, expected_scope_revision
                )
                actual_current = self._current_snapshot_id(connection, scope_id)
                if actual_current != expected_current_snapshot_id:
                    raise DomainError(
                        ErrorCode.REVISION_CONFLICT,
                        "Structure CURRENT changed before Admission decision",
                    )
                if batch.coverage.root.owning_scope_id != scope_id:
                    raise _invalid(
                        "ADMISSION_SCOPE_MISMATCH",
                        "Admission candidate belongs to another Scope",
                    )
                registration = self._load_schema_registration(
                    connection, batch.coverage.root.schema_ref
                )
                if (
                    registration.definition.schema_digest
                    != batch.coverage.root.schema_digest
                ):
                    raise _invalid(
                        "ADMISSION_SCHEMA_DIGEST_MISMATCH",
                        "Admission candidate does not bind the registered Schema digest",
                    )
                if ScopeType.SYSTEM not in registration.definition.eligible_scope_types:
                    raise _invalid(
                        "SCHEMA_SCOPE_INELIGIBLE",
                        "registered Schema is not eligible for SYSTEM Scope",
                    )
                availability = self._load_schema_availability(
                    connection, batch.coverage.root.schema_ref, None
                )
                if outcome is StructureAdmissionOutcome.ACCEPT:
                    if (
                        availability.status
                        is not StructureSchemaAvailabilityStatus.AVAILABLE
                    ):
                        raise _invalid(
                            "SCHEMA_NOT_AVAILABLE",
                            "Admission ACCEPT requires current Schema Availability",
                        )
                admission_id = self._ids.new("structure_admission")
                decision_digest = structure_admission_decision_digest(
                    admission_id=admission_id,
                    outcome=outcome,
                    candidate_ref=candidate_ref,
                    candidate_digest=candidate_digest,
                    batch_digest=batch_digest,
                    closure_digest=closure_digest,
                    read_set_digest=read_set_digest,
                    scope_id=scope_id,
                    expected_scope_revision=expected_scope_revision,
                    scope_assertion_digest=scope_assertion_digest,
                    expected_current_snapshot_id=expected_current_snapshot_id,
                    schema_ref=batch.coverage.root.schema_ref,
                    schema_digest=batch.coverage.root.schema_digest,
                    schema_registration_digest=registration.digest,
                    schema_availability_digest=availability.digest,
                    knowledge_context_digest=batch.coverage.state.knowledge_context_digest,
                    upstream_digest=upstream_digest,
                    provenance_digest=provenance_digest,
                    artifact_use_confirmation_id=(
                        assessment.artifact_use_confirmation_id
                    ),
                    artifact_use_confirmation_digest=(
                        assessment.artifact_use_confirmation_digest
                    ),
                    verifier_assessment_id=assessment.assessment_id,
                    verifier_assessment_digest=assessment.digest,
                    verifier_authority_id=assessment.verifier_authority_id,
                    verifier_ref=assessment.verifier_ref,
                    findings=findings,
                    decided_at=decided_at,
                )
                decision = StructureAdmissionDecision(
                    admission_id=admission_id,
                    outcome=outcome,
                    candidate_ref=candidate_ref,
                    candidate_digest=candidate_digest,
                    batch_digest=batch_digest,
                    closure_digest=closure_digest,
                    read_set_digest=read_set_digest,
                    scope_id=scope_id,
                    expected_scope_revision=expected_scope_revision,
                    scope_assertion_digest=scope_assertion_digest,
                    expected_current_snapshot_id=expected_current_snapshot_id,
                    schema_ref=batch.coverage.root.schema_ref,
                    schema_digest=batch.coverage.root.schema_digest,
                    schema_registration_digest=registration.digest,
                    schema_availability_digest=availability.digest,
                    knowledge_context_digest=batch.coverage.state.knowledge_context_digest,
                    upstream_digest=upstream_digest,
                    provenance_digest=provenance_digest,
                    artifact_use_confirmation_id=(
                        assessment.artifact_use_confirmation_id
                    ),
                    artifact_use_confirmation_digest=(
                        assessment.artifact_use_confirmation_digest
                    ),
                    verifier_assessment_id=assessment.assessment_id,
                    verifier_assessment_digest=assessment.digest,
                    verifier_authority_id=assessment.verifier_authority_id,
                    verifier_ref=assessment.verifier_ref,
                    findings=findings,
                    decided_at=decided_at,
                    digest=decision_digest,
                )
                decision.require_valid()
                connection.execute(
                    """INSERT INTO knw_structure_admissions
                       (admission_id, outcome, candidate_ref, candidate_digest,
                        batch_digest, closure_digest, read_set_digest, scope_id,
                        expected_scope_revision, scope_assertion_digest,
                        expected_current_snapshot_id, schema_ref, schema_digest,
                        schema_registration_digest, schema_availability_digest,
                        knowledge_context_digest, upstream_digest,
                        provenance_digest, artifact_use_confirmation_id,
                        artifact_use_confirmation_digest,
                        verifier_assessment_id,
                        verifier_assessment_digest, verifier_authority_id,
                        verifier_ref, findings_json,
                        decided_at, admission_digest)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        admission_id.value,
                        outcome.value,
                        candidate_ref,
                        candidate_digest.value,
                        batch_digest.value,
                        closure_digest.value,
                        read_set_digest.value,
                        scope_id.value,
                        expected_scope_revision.value,
                        scope_assertion_digest.value,
                        (
                            expected_current_snapshot_id.value
                            if expected_current_snapshot_id is not None
                            else None
                        ),
                        batch.coverage.root.schema_ref,
                        batch.coverage.root.schema_digest.value,
                        registration.digest.value,
                        availability.digest.value,
                        batch.coverage.state.knowledge_context_digest.value,
                        upstream_digest.value,
                        provenance_digest.value,
                        assessment.artifact_use_confirmation_id.value,
                        assessment.artifact_use_confirmation_digest.value,
                        assessment.assessment_id.value,
                        assessment.digest.value,
                        assessment.verifier_authority_id.value,
                        assessment.verifier_ref,
                        _json(normalized_findings_value(findings)),
                        _time(decided_at),
                        decision_digest.value,
                    ),
                )
                connection.execute(
                    "INSERT INTO knw_structure_admission_commands VALUES (?, ?, ?)",
                    (idempotency_key.value, request_digest.value, admission_id.value),
                )
                return decision
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _inconsistent(
                f"Structure Admission violated an authority invariant: {exc}"
            ) from exc

    def get_structure_admission(
        self, admission_id: StableId
    ) -> StructureAdmissionDecision:
        with self._database.read() as connection:
            return self._load_structure_admission(connection, admission_id)

    def _schema_command_result(
        self,
        connection: sqlite3.Connection,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
    ) -> tuple[StructureSchemaRegistration, StructureSchemaAvailability] | None:
        row = connection.execute(
            "SELECT * FROM knw_structure_schema_commands WHERE idempotency_key = ?",
            (idempotency_key.value,),
        ).fetchone()
        if row is None:
            return None
        if row["request_digest"] != request_digest.value:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "Schema authority idempotency key has a different request",
            )
        availability = self._load_schema_availability_by_id(
            connection, StableId(row["result_availability_id"])
        )
        registration = self._load_schema_registration(
            connection, availability.schema_ref
        )
        if (
            row["result_registration_id"] is not None
            and registration.registration_id.value != row["result_registration_id"]
        ):
            raise _inconsistent(
                "Schema command result does not match its Registration"
            )
        return registration, availability

    @staticmethod
    def _insert_schema_command(
        connection: sqlite3.Connection,
        *,
        idempotency_key: IdempotencyKey,
        command_type: str,
        request_digest: Digest,
        registration_id: StableId,
        availability_id: StableId,
    ) -> None:
        connection.execute(
            "INSERT INTO knw_structure_schema_commands VALUES (?, ?, ?, ?, ?)",
            (
                idempotency_key.value,
                command_type,
                request_digest.value,
                registration_id.value,
                availability_id.value,
            ),
        )

    def _load_schema_registration(
        self, connection: sqlite3.Connection, schema_ref: str
    ) -> StructureSchemaRegistration:
        row = connection.execute(
            "SELECT * FROM knw_structure_schema_registrations WHERE schema_ref = ?",
            (schema_ref,),
        ).fetchone()
        if row is None:
            raise _invalid(
                "SCHEMA_NOT_REGISTERED",
                "exact Structure Schema ref is not registered",
            )
        dependencies = tuple(
            StructureSchemaDependency(
                schema_ref=item["dependency_schema_ref"],
                schema_digest=Digest(item["dependency_schema_digest"]),
            )
            for item in connection.execute(
                """SELECT dependency_schema_ref, dependency_schema_digest
                   FROM knw_structure_schema_dependencies
                   WHERE schema_ref = ? ORDER BY dependency_schema_ref""",
                (schema_ref,),
            ).fetchall()
        )
        definition = StructureSchemaDefinition(
            schema_ref=row["schema_ref"],
            schema_digest=Digest(row["schema_digest"]),
            eligible_scope_types=tuple(
                ScopeType(item)
                for item in _json_array(row["eligible_scope_types_json"])
            ),
            dependencies=dependencies,
            digest=Digest(row["definition_digest"]),
        )
        definition.require_valid()
        registration = StructureSchemaRegistration(
            registration_id=StableId(row["registration_id"]),
            definition=definition,
            proposal_ref=row["proposal_ref"],
            review_ref=row["review_ref"],
            registered_by=row["registered_by"],
            reason=row["reason"],
            registered_at=_parse_time(row["registered_at"]),
            digest=Digest(row["registration_digest"]),
        )
        registration.require_valid()
        return registration

    def _load_schema_availability(
        self,
        connection: sqlite3.Connection,
        schema_ref: str,
        revision: Revision | None,
    ) -> StructureSchemaAvailability:
        if revision is None:
            root = connection.execute(
                """SELECT current_revision, current_availability_id
                   FROM knw_structure_schema_availability_roots
                   WHERE schema_ref = ?""",
                (schema_ref,),
            ).fetchone()
            if root is None:
                raise _invalid(
                    "SCHEMA_AVAILABILITY_NOT_FOUND",
                    "Schema has no Availability authority record",
                )
            availability = self._load_schema_availability_by_id(
                connection, StableId(root["current_availability_id"])
            )
            if (
                availability.schema_ref != schema_ref
                or availability.availability_revision.value != root["current_revision"]
            ):
                raise _inconsistent(
                    "Schema Availability CURRENT does not match its exact revision"
                )
            return availability
        row = connection.execute(
            """SELECT availability_id FROM knw_structure_schema_availabilities
               WHERE schema_ref = ? AND availability_revision = ?""",
            (schema_ref, revision.value),
        ).fetchone()
        if row is None:
            raise _invalid(
                "SCHEMA_AVAILABILITY_NOT_FOUND",
                "exact Schema Availability revision was not found",
            )
        return self._load_schema_availability_by_id(
            connection, StableId(row["availability_id"])
        )

    @staticmethod
    def _load_schema_availability_by_id(
        connection: sqlite3.Connection, availability_id: StableId
    ) -> StructureSchemaAvailability:
        row = connection.execute(
            """SELECT * FROM knw_structure_schema_availabilities
               WHERE availability_id = ?""",
            (availability_id.value,),
        ).fetchone()
        if row is None:
            raise _invalid(
                "SCHEMA_AVAILABILITY_NOT_FOUND",
                "exact Schema Availability record was not found",
            )
        availability = StructureSchemaAvailability(
            availability_id=StableId(row["availability_id"]),
            schema_ref=row["schema_ref"],
            schema_digest=Digest(row["schema_digest"]),
            registration_id=StableId(row["registration_id"]),
            availability_revision=Revision(row["availability_revision"]),
            status=StructureSchemaAvailabilityStatus(row["status"]),
            changed_by=row["changed_by"],
            reason=row["reason"],
            changed_at=_parse_time(row["changed_at"]),
            previous_availability_id=(
                StableId(row["previous_availability_id"])
                if row["previous_availability_id"] is not None
                else None
            ),
            digest=Digest(row["availability_digest"]),
        )
        availability.require_valid()
        return availability

    @staticmethod
    def _insert_schema_availability(
        connection: sqlite3.Connection,
        availability: StructureSchemaAvailability,
    ) -> None:
        connection.execute(
            """INSERT INTO knw_structure_schema_availabilities VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                availability.availability_id.value,
                availability.schema_ref,
                availability.schema_digest.value,
                availability.registration_id.value,
                availability.availability_revision.value,
                availability.status.value,
                availability.changed_by,
                availability.reason,
                _time(availability.changed_at),
                (
                    availability.previous_availability_id.value
                    if availability.previous_availability_id is not None
                    else None
                ),
                availability.digest.value,
            ),
        )

    @staticmethod
    def _load_schema_adoption(
        connection: sqlite3.Connection, scope_id: StableId
    ) -> StructureSchemaAdoption | None:
        row = connection.execute(
            "SELECT * FROM knw_structure_schema_adoptions WHERE scope_id = ?",
            (scope_id.value,),
        ).fetchone()
        if row is None:
            return None
        adoption = StructureSchemaAdoption(
            scope_id=StableId(row["scope_id"]),
            schema_ref=row["schema_ref"],
            schema_digest=Digest(row["schema_digest"]),
            registration_id=StableId(row["registration_id"]),
            initial_availability_id=StableId(row["initial_availability_id"]),
            initial_snapshot_id=StableId(row["initial_snapshot_id"]),
            adopted_at=_parse_time(row["adopted_at"]),
            digest=Digest(row["adoption_digest"]),
        )
        adoption.require_valid()
        return adoption

    @staticmethod
    def _insert_schema_adoption(
        connection: sqlite3.Connection, adoption: StructureSchemaAdoption
    ) -> None:
        adoption.require_valid()
        connection.execute(
            "INSERT INTO knw_structure_schema_adoptions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                adoption.scope_id.value,
                adoption.schema_ref,
                adoption.schema_digest.value,
                adoption.registration_id.value,
                adoption.initial_availability_id.value,
                adoption.initial_snapshot_id.value,
                _time(adoption.adopted_at),
                adoption.digest.value,
            ),
        )

    def _verifier_assessment_command_result(
        self,
        connection: sqlite3.Connection,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
    ) -> StructureVerifierAssessment | None:
        row = connection.execute(
            """SELECT request_digest, result_assessment_id
               FROM knw_structure_verifier_assessment_commands
               WHERE idempotency_key = ?""",
            (idempotency_key.value,),
        ).fetchone()
        if row is None:
            return None
        if row["request_digest"] != request_digest.value:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "Structure Verifier Assessment idempotency key has a different request",
            )
        return self._load_structure_verifier_assessment(
            connection, StableId(row["result_assessment_id"])
        )

    @staticmethod
    def _load_structure_verifier_assessment(
        connection: sqlite3.Connection,
        assessment_id: StableId,
    ) -> StructureVerifierAssessment:
        row = connection.execute(
            """SELECT * FROM knw_structure_verifier_assessments
               WHERE assessment_id = ?""",
            (assessment_id.value,),
        ).fetchone()
        if row is None:
            raise _invalid(
                "VERIFIER_ASSESSMENT_NOT_PERSISTED",
                "exact Structure Verifier Assessment was not found",
            )
        findings_value = json.loads(row["findings_json"])
        if not isinstance(findings_value, list) or any(
            not isinstance(item, list)
            or len(item) != 2
            or not all(isinstance(value, str) for value in item)
            for item in findings_value
        ):
            raise _inconsistent("Structure Verifier Assessment findings are malformed")
        assessment = StructureVerifierAssessment(
            assessment_id=StableId(row["assessment_id"]),
            outcome=StructureVerifierAssessmentOutcome(row["outcome"]),
            candidate_ref=row["candidate_ref"],
            candidate_digest=Digest(row["candidate_digest"]),
            verified_candidate_digest=Digest(row["verified_candidate_digest"]),
            candidate_evaluation_digest=Digest(
                row["candidate_evaluation_digest"]
            ),
            verified_evaluation_digest=Digest(
                row["verified_evaluation_digest"]
            ),
            candidate_report_digest=Digest(row["candidate_report_digest"]),
            verified_report_digest=Digest(row["verified_report_digest"]),
            batch_digest=Digest(row["batch_digest"]),
            verified_batch_digest=Digest(row["verified_batch_digest"]),
            closure_digest=Digest(row["closure_digest"]),
            verified_closure_digest=Digest(row["verified_closure_digest"]),
            read_set_digest=Digest(row["read_set_digest"]),
            verified_read_set_digest=Digest(row["verified_read_set_digest"]),
            provenance_digest=Digest(row["provenance_digest"]),
            verification_context_digest=Digest(
                row["verification_context_digest"]
            ),
            artifact_use_confirmation_id=StableId(
                row["artifact_use_confirmation_id"]
            ),
            artifact_use_confirmation_digest=Digest(
                row["artifact_use_confirmation_digest"]
            ),
            verifier_authority_id=StableId(row["verifier_authority_id"]),
            verifier_ref=row["verifier_ref"],
            findings=tuple(
                StructureAdmissionFinding(code=item[0], message=item[1])
                for item in findings_value
            ),
            assessed_at=_parse_time(row["assessed_at"]),
            digest=Digest(row["assessment_digest"]),
        )
        assessment.require_valid()
        return assessment

    def _admission_command_result(
        self,
        connection: sqlite3.Connection,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
    ) -> StructureAdmissionDecision | None:
        row = connection.execute(
            """SELECT request_digest, result_admission_id
               FROM knw_structure_admission_commands WHERE idempotency_key = ?""",
            (idempotency_key.value,),
        ).fetchone()
        if row is None:
            return None
        if row["request_digest"] != request_digest.value:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "Structure Admission idempotency key has a different request",
            )
        return self._load_structure_admission(
            connection, StableId(row["result_admission_id"])
        )

    @staticmethod
    def _load_structure_admission(
        connection: sqlite3.Connection, admission_id: StableId
    ) -> StructureAdmissionDecision:
        row = connection.execute(
            "SELECT * FROM knw_structure_admissions WHERE admission_id = ?",
            (admission_id.value,),
        ).fetchone()
        if row is None:
            raise _invalid(
                "ADMISSION_NOT_PERSISTED",
                "exact Structure Admission Decision was not found",
            )
        findings_value = json.loads(row["findings_json"])
        if not isinstance(findings_value, list) or any(
            not isinstance(item, list)
            or len(item) != 2
            or not all(isinstance(value, str) for value in item)
            for item in findings_value
        ):
            raise _inconsistent("Structure Admission findings are malformed")
        decision = StructureAdmissionDecision(
            admission_id=StableId(row["admission_id"]),
            outcome=StructureAdmissionOutcome(row["outcome"]),
            candidate_ref=row["candidate_ref"],
            candidate_digest=Digest(row["candidate_digest"]),
            batch_digest=Digest(row["batch_digest"]),
            closure_digest=Digest(row["closure_digest"]),
            read_set_digest=Digest(row["read_set_digest"]),
            scope_id=StableId(row["scope_id"]),
            expected_scope_revision=Revision(row["expected_scope_revision"]),
            scope_assertion_digest=Digest(row["scope_assertion_digest"]),
            expected_current_snapshot_id=(
                StableId(row["expected_current_snapshot_id"])
                if row["expected_current_snapshot_id"] is not None
                else None
            ),
            schema_ref=row["schema_ref"],
            schema_digest=Digest(row["schema_digest"]),
            schema_registration_digest=Digest(
                row["schema_registration_digest"]
            ),
            schema_availability_digest=Digest(
                row["schema_availability_digest"]
            ),
            knowledge_context_digest=Digest(row["knowledge_context_digest"]),
            upstream_digest=Digest(row["upstream_digest"]),
            provenance_digest=Digest(row["provenance_digest"]),
            artifact_use_confirmation_id=StableId(
                row["artifact_use_confirmation_id"]
            ),
            artifact_use_confirmation_digest=Digest(
                row["artifact_use_confirmation_digest"]
            ),
            verifier_assessment_id=StableId(row["verifier_assessment_id"]),
            verifier_assessment_digest=Digest(
                row["verifier_assessment_digest"]
            ),
            verifier_authority_id=StableId(row["verifier_authority_id"]),
            verifier_ref=row["verifier_ref"],
            findings=tuple(
                StructureAdmissionFinding(code=item[0], message=item[1])
                for item in findings_value
            ),
            decided_at=_parse_time(row["decided_at"]),
            digest=Digest(row["admission_digest"]),
        )
        decision.require_valid()
        return decision

    @staticmethod
    def _require_system_scope(
        connection: sqlite3.Connection,
        scope_id: StableId,
        expected_scope_revision: Revision,
    ) -> None:
        row = connection.execute(
            """SELECT scope_type, current_revision, lifecycle
               FROM knw_scope_roots WHERE scope_id = ?""",
            (scope_id.value,),
        ).fetchone()
        if row is None:
            raise DomainError(ErrorCode.SCOPE_NOT_FOUND, "Knowledge Scope was not found")
        if row["current_revision"] != expected_scope_revision.value:
            raise DomainError(
                ErrorCode.REVISION_CONFLICT,
                "Knowledge Scope changed before Structure authority commit",
            )
        if (
            row["scope_type"] != ScopeType.SYSTEM.value
            or row["lifecycle"] != ScopeLifecycle.ACTIVE.value
        ):
            raise DomainError(
                ErrorCode.SCOPE_ASSERTION_INVALID,
                "Structure authority requires an active SYSTEM Scope",
            )

    @staticmethod
    def _current_snapshot_id(
        connection: sqlite3.Connection, scope_id: StableId
    ) -> StableId | None:
        row = connection.execute(
            """SELECT current_snapshot_id FROM knw_structure_snapshot_roots
               WHERE scope_id = ?""",
            (scope_id.value,),
        ).fetchone()
        return StableId(row["current_snapshot_id"]) if row is not None else None

    def current_snapshot(self, scope_id: StableId) -> StructureSnapshot | None:
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT current_snapshot_id, current_revision
                   FROM knw_structure_snapshot_roots
                   WHERE scope_id = ?""",
                (scope_id.value,),
            ).fetchone()
            if row is None:
                return None
            snapshot = self._load_snapshot(
                connection, StableId(row["current_snapshot_id"])
            )
            if (
                snapshot.scope_id != scope_id
                or snapshot.snapshot_revision.value != row["current_revision"]
            ):
                raise _inconsistent(
                    "Structure CURRENT root does not match its exact Snapshot"
                )
            return snapshot

    def get_snapshot(self, snapshot_id: StableId) -> StructureSnapshot:
        with self._database.read() as connection:
            return self._load_snapshot(connection, snapshot_id)

    def get_publication(
        self, publication_id: StableId
    ) -> StructurePublicationReceipt:
        with self._database.read() as connection:
            return self._load_receipt(connection, publication_id)

    def get_publication_by_idempotency_key(
        self, idempotency_key: IdempotencyKey
    ) -> StructurePublicationReceipt | None:
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT publication_id FROM knw_structure_publications
                   WHERE idempotency_key = ?""",
                (idempotency_key.value,),
            ).fetchone()
            if row is None:
                return None
            return self._load_receipt(
                connection,
                StableId(row["publication_id"]),
            )

    def get_evidence(self, evidence_id: StableId) -> StructureEvidence:
        with self._database.read() as connection:
            return self._load_evidence(connection, evidence_id)

    def get_evidence_metadata(
        self, evidence_id: StableId
    ) -> StructureEvidenceMetadata:
        return StructureEvidenceMetadata.from_evidence(self.get_evidence(evidence_id))

    def get_entity(
        self, snapshot_id: StableId, entity_root_id: StableId
    ) -> EntityRecord:
        with self._database.read() as connection:
            snapshot = self._load_snapshot(connection, snapshot_id)
            member = _snapshot_member(
                snapshot, CoverageMemberKind.ENTITY, entity_root_id
            )
            return self._load_entity_record(connection, member.root_id, member.state_id)

    def get_relation_fact(
        self, snapshot_id: StableId, relation_root_id: StableId
    ) -> RelationFactRecord:
        with self._database.read() as connection:
            snapshot = self._load_snapshot(connection, snapshot_id)
            member = _snapshot_member(
                snapshot, CoverageMemberKind.RELATION_FACT, relation_root_id
            )
            return self._load_relation_record(connection, member.root_id, member.state_id)

    def get_literal_fact(
        self, snapshot_id: StableId, literal_root_id: StableId
    ) -> LiteralFactRecord:
        with self._database.read() as connection:
            snapshot = self._load_snapshot(connection, snapshot_id)
            member = _snapshot_member(
                snapshot, CoverageMemberKind.LITERAL_FACT, literal_root_id
            )
            return self._load_literal_record(connection, member.root_id, member.state_id)

    def get_coverage(
        self, snapshot_id: StableId, coverage_root_id: StableId
    ) -> CoverageRecord:
        with self._database.read() as connection:
            snapshot = self._load_snapshot(connection, snapshot_id)
            matches = tuple(
                item
                for item in snapshot.coverages
                if item.coverage_root_id == coverage_root_id
            )
            if len(matches) != 1:
                raise _invalid(
                    "COVERAGE_NOT_IN_SNAPSHOT",
                    "Coverage is not present in the exact Structure Snapshot",
                )
            return self._load_coverage_record(
                connection,
                matches[0].coverage_root_id,
                matches[0].coverage_state_id,
            )

    def owner_of(
        self, snapshot_id: StableId, root_id: StableId
    ) -> StableId:
        with self._database.read() as connection:
            self._load_snapshot(connection, snapshot_id)
            row = connection.execute(
                """SELECT coverage_root_id FROM knw_structure_snapshot_ownership
                   WHERE snapshot_id = ? AND root_id = ?""",
                (snapshot_id.value, root_id.value),
            ).fetchone()
            if row is None:
                raise _invalid(
                    "MEMBER_OWNERSHIP_NOT_FOUND",
                    "Structure Snapshot member has no Coverage owner",
                )
            return StableId(row["coverage_root_id"])

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
    ) -> StructurePublicationReceipt:
        if not isinstance(verifier_authority, StructureVerifierAuthority):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Structure verifier capability is not registered",
                {"reason_code": "VERIFIER_AUTHORITY_CAPABILITY_INVALID"},
            )
        verifier_authority.require_valid()
        batch.require_admissible()
        admission.require_valid()
        if admission.outcome is not StructureAdmissionOutcome.ACCEPT:
            raise _invalid(
                "ADMISSION_NOT_ACCEPT",
                "Structure publication requires Admission ACCEPT",
            )
        application_acceptance.require_valid()
        if application_acceptance.decision is not ApplicationAcceptanceDecision.PASS:
            raise _invalid(
                "APPLICATION_ACCEPTANCE_NOT_PASS",
                "Structure publication requires Application PASS",
            )
        if structure_batch_digest(batch) != batch_digest:
            raise _invalid(
                "BATCH_DIGEST_MISMATCH",
                "Structure batch digest changed before publication",
            )
        if application_acceptance.batch_digest != batch_digest:
            raise _invalid(
                "APPLICATION_ACCEPTANCE_BATCH_MISMATCH",
                "Application acceptance is bound to another Structure batch",
            )
        admission_bindings = (
            (admission.verifier_authority_id, verifier_authority.authority_id),
            (admission.verifier_ref, verifier_authority.verifier_ref),
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
        if any(actual != expected for actual, expected in admission_bindings):
            raise _invalid(
                "ADMISSION_CLOSURE_MISMATCH",
                "Admission ACCEPT is bound to another candidate closure or target",
            )
        if batch.coverage.root.owning_scope_id != scope_id:
            raise _invalid(
                "PUBLICATION_SCOPE_MISMATCH",
                "Structure batch does not belong to the publication Scope",
            )
        if published_at.tzinfo is None or published_at.utcoffset() is None:
            raise _invalid(
                "PUBLICATION_TIMEZONE_REQUIRED",
                "Structure publication time must include a timezone",
            )
        try:
            with self._database.transaction() as connection:
                self._require_registered_verifier_authority(
                    connection,
                    verifier_authority,
                    require_admission_authority=True,
                )
                replay = self._idempotent(
                    connection, idempotency_key, request_digest
                )
                if replay is not None:
                    return replay

                # Scope, Admission, Registry Availability and adoption are all
                # re-read under the same write transaction as CURRENT.
                self._require_system_scope(
                    connection, scope_id, expected_scope_revision
                )
                stored_admission = self._load_structure_admission(
                    connection, admission.admission_id
                )
                if stored_admission != admission:
                    raise _invalid(
                        "ADMISSION_PERSISTED_RECORD_MISMATCH",
                        "provided Admission does not equal its persisted authority record",
                    )
                stored_assessment = self._load_structure_verifier_assessment(
                    connection, stored_admission.verifier_assessment_id
                )
                assessment_bindings = (
                    (
                        stored_assessment.outcome,
                        StructureVerifierAssessmentOutcome.PASS,
                    ),
                    (stored_assessment.digest, stored_admission.verifier_assessment_digest),
                    (
                        stored_assessment.verifier_authority_id,
                        verifier_authority.authority_id,
                    ),
                    (
                        stored_admission.verifier_authority_id,
                        verifier_authority.authority_id,
                    ),
                    (stored_assessment.verifier_ref, stored_admission.verifier_ref),
                    (stored_assessment.candidate_ref, stored_admission.candidate_ref),
                    (
                        stored_assessment.candidate_digest,
                        stored_admission.candidate_digest,
                    ),
                    (stored_assessment.batch_digest, structure_batch_digest(batch)),
                    (
                        stored_assessment.closure_digest,
                        structure_closure_digest(batch),
                    ),
                    (
                        stored_assessment.read_set_digest,
                        structure_read_set_digest(batch),
                    ),
                    (
                        stored_assessment.provenance_digest,
                        stored_admission.provenance_digest,
                    ),
                    (
                        stored_assessment.artifact_use_confirmation_id,
                        stored_admission.artifact_use_confirmation_id,
                    ),
                    (
                        stored_assessment.artifact_use_confirmation_digest,
                        stored_admission.artifact_use_confirmation_digest,
                    ),
                )
                if any(
                    actual != expected
                    for actual, expected in assessment_bindings
                ):
                    raise _invalid(
                        "VERIFIER_ASSESSMENT_PUBLICATION_MISMATCH",
                        "persisted Verifier Assessment does not authorize this publication",
                    )
                transactional_admission_bindings = (
                    (stored_admission.batch_digest, structure_batch_digest(batch)),
                    (stored_admission.closure_digest, structure_closure_digest(batch)),
                    (stored_admission.read_set_digest, structure_read_set_digest(batch)),
                    (stored_admission.scope_id, scope_id),
                    (
                        stored_admission.expected_scope_revision,
                        expected_scope_revision,
                    ),
                    (
                        stored_admission.expected_current_snapshot_id,
                        expected_current_snapshot_id,
                    ),
                    (stored_admission.schema_ref, batch.coverage.root.schema_ref),
                    (stored_admission.schema_digest, batch.coverage.root.schema_digest),
                    (
                        stored_admission.knowledge_context_digest,
                        batch.coverage.state.knowledge_context_digest,
                    ),
                    (stored_admission.upstream_digest, structure_upstream_digest(batch)),
                )
                if any(
                    actual != expected
                    for actual, expected in transactional_admission_bindings
                ):
                    raise _invalid(
                        "ADMISSION_CLOSURE_MISMATCH",
                        "persisted Admission does not bind the transactional candidate closure",
                    )
                registration = self._load_schema_registration(
                    connection, batch.coverage.root.schema_ref
                )
                availability = self._load_schema_availability(
                    connection, batch.coverage.root.schema_ref, None
                )
                if (
                    availability.status
                    is not StructureSchemaAvailabilityStatus.AVAILABLE
                ):
                    raise _invalid(
                        "SCHEMA_NOT_AVAILABLE",
                        "Structure publication requires current Schema Availability",
                    )
                if (
                    registration.definition.schema_digest
                    != batch.coverage.root.schema_digest
                    or availability.schema_digest
                    != batch.coverage.root.schema_digest
                    or availability.registration_id != registration.registration_id
                    or admission.schema_registration_digest != registration.digest
                    or admission.schema_availability_digest != availability.digest
                ):
                    raise _invalid(
                        "PUBLICATION_SCHEMA_REGISTRY_MISMATCH",
                        "publication target does not match exact Schema Registry facts",
                    )
                if ScopeType.SYSTEM not in registration.definition.eligible_scope_types:
                    raise _invalid(
                        "SCHEMA_SCOPE_INELIGIBLE",
                        "registered Schema is not eligible for SYSTEM Scope",
                    )

                root_row = connection.execute(
                    """SELECT current_snapshot_id, current_revision
                       FROM knw_structure_snapshot_roots WHERE scope_id = ?""",
                    (scope_id.value,),
                ).fetchone()
                actual_current = (
                    StableId(root_row["current_snapshot_id"])
                    if root_row is not None
                    else None
                )
                if actual_current != expected_current_snapshot_id:
                    raise DomainError(
                        ErrorCode.REVISION_CONFLICT,
                        "Structure CURRENT changed before publication",
                    )
                previous = (
                    self._load_snapshot(connection, actual_current)
                    if actual_current is not None
                    else None
                )
                adoption = self._load_schema_adoption(connection, scope_id)
                if previous is None:
                    if adoption is not None:
                        raise _inconsistent(
                            "Schema Adoption exists without a Structure CURRENT"
                        )
                    schema_adoption_mode = StructureSchemaAdoptionMode.INITIAL
                else:
                    if adoption is None:
                        raise _inconsistent(
                            "Structure CURRENT has no immutable Schema Adoption"
                        )
                    adoption.require_valid()
                    if (
                        previous.schema_ref != batch.coverage.root.schema_ref
                        or previous.schema_digest != batch.coverage.root.schema_digest
                        or adoption.schema_ref != batch.coverage.root.schema_ref
                        or adoption.schema_digest != batch.coverage.root.schema_digest
                        or adoption.registration_id != registration.registration_id
                    ):
                        raise _invalid(
                            "SCHEMA_EVOLUTION_UNSUPPORTED",
                            "Structure publication cannot change an adopted Schema",
                        )
                    schema_adoption_mode = StructureSchemaAdoptionMode.UNCHANGED

                previous_members = {
                    member.root_id: member
                    for member in (previous.members if previous is not None else ())
                }
                previous_coverages = {
                    coverage.coverage_root_id: coverage
                    for coverage in (previous.coverages if previous is not None else ())
                }
                previous_ownership = (
                    self._load_ownership(connection, previous.snapshot_id)
                    if previous is not None
                    else {}
                )
                target_coverage_root_id = batch.coverage.root_id
                local_members = {
                    record.root_id: record.coverage_member
                    for record in (
                        *batch.entities,
                        *batch.relation_facts,
                        *batch.literal_facts,
                    )
                }
                declared_members = {
                    member.root_id: member
                    for member in batch.coverage.state.complete_member_manifest.members
                }

                if batch.publication_mode is PublicationMode.ENRICH:
                    (
                        final_members,
                        final_ownership,
                    ) = self._apply_enrich(
                        previous_members=previous_members,
                        previous_ownership=previous_ownership,
                        target_coverage_root_id=target_coverage_root_id,
                        local_members=local_members,
                        declared_members=declared_members,
                    )
                else:
                    (
                        final_members,
                        final_ownership,
                    ) = self._apply_replace_coverage(
                        previous_members=previous_members,
                        previous_ownership=previous_ownership,
                        target_coverage_root_id=target_coverage_root_id,
                        local_members=local_members,
                        declared_members=declared_members,
                    )

                self._insert_batch(connection, batch)
                final_coverages = dict(previous_coverages)
                final_coverages[target_coverage_root_id] = SnapshotCoverage(
                    coverage_root_id=target_coverage_root_id,
                    coverage_state_id=batch.coverage.state_id,
                    coverage_state_digest=batch.coverage.state.state_digest,
                )

                upstream_by_root = {
                    item.entity_root_id: item
                    for item in (
                        previous.upstream_entities if previous is not None else ()
                    )
                }
                for upstream in batch.exact_upstream_entities:
                    exact = self._verify_exact_upstream_entity(
                        connection, upstream.snapshot_id, upstream.entity
                    )
                    prior = upstream_by_root.get(exact.entity_root_id)
                    if prior is not None and prior != exact:
                        raise _invalid(
                            "AMBIGUOUS_UPSTREAM_ENTITY",
                            "one Entity Root resolves to multiple exact upstream States",
                        )
                    upstream_by_root[exact.entity_root_id] = exact

                final_upstream = self._validate_final_closure(
                    connection,
                    members=tuple(final_members.values()),
                    coverages=tuple(final_coverages.values()),
                    ownership=final_ownership,
                    upstream_by_root=upstream_by_root,
                    expected_scope_id=scope_id,
                    expected_schema_ref=batch.coverage.root.schema_ref,
                )

                snapshot_id = self._ids.new("structure_snapshot")
                snapshot_revision = Revision(
                    root_row["current_revision"] + 1
                    if root_row is not None
                    else 1
                )
                if adoption is None:
                    adoption = StructureSchemaAdoption(
                        scope_id=scope_id,
                        schema_ref=registration.definition.schema_ref,
                        schema_digest=registration.definition.schema_digest,
                        registration_id=registration.registration_id,
                        initial_availability_id=availability.availability_id,
                        initial_snapshot_id=snapshot_id,
                        adopted_at=published_at,
                        digest=structure_schema_adoption_digest(
                            scope_id=scope_id,
                            schema_ref=registration.definition.schema_ref,
                            schema_digest=registration.definition.schema_digest,
                            registration_id=registration.registration_id,
                            initial_availability_id=availability.availability_id,
                            initial_snapshot_id=snapshot_id,
                            adopted_at=published_at,
                        ),
                    )
                    adoption.require_valid()
                snapshot = StructureSnapshot.create(
                    snapshot_id=snapshot_id,
                    scope_id=scope_id,
                    snapshot_revision=snapshot_revision,
                    previous_snapshot_id=actual_current,
                    schema_ref=batch.coverage.root.schema_ref,
                    schema_digest=batch.coverage.root.schema_digest,
                    schema_adoption_mode=schema_adoption_mode,
                    schema_registration_digest=registration.digest,
                    schema_availability_digest=availability.digest,
                    schema_adoption_digest=adoption.digest,
                    publication_mode=batch.publication_mode,
                    members=tuple(final_members.values()),
                    coverages=tuple(final_coverages.values()),
                    upstream_entities=final_upstream,
                    published_at=published_at,
                )
                self._insert_snapshot(
                    connection,
                    snapshot=snapshot,
                    ownership=final_ownership,
                )
                if schema_adoption_mode is StructureSchemaAdoptionMode.INITIAL:
                    self._insert_schema_adoption(connection, adoption)
                if root_row is None:
                    connection.execute(
                        "INSERT INTO knw_structure_snapshot_roots VALUES (?, ?, ?)",
                        (
                            scope_id.value,
                            snapshot.snapshot_id.value,
                            snapshot.snapshot_revision.value,
                        ),
                    )
                else:
                    cursor = connection.execute(
                        """UPDATE knw_structure_snapshot_roots
                           SET current_snapshot_id = ?, current_revision = ?
                           WHERE scope_id = ? AND current_snapshot_id = ?""",
                        (
                            snapshot.snapshot_id.value,
                            snapshot.snapshot_revision.value,
                            scope_id.value,
                            actual_current.value,
                        ),
                    )
                    if cursor.rowcount != 1:
                        raise DomainError(
                            ErrorCode.REVISION_CONFLICT,
                            "Structure CURRENT changed during publication",
                        )

                publication_id = self._ids.new("structure_publication")
                receipt = StructurePublicationReceipt.create(
                    publication_id=publication_id,
                    request_digest=request_digest,
                    batch_digest=batch_digest,
                    admission_id=admission.admission_id,
                    admission_digest=admission.digest,
                    application_acceptance_digest=application_acceptance.digest,
                    snapshot=snapshot,
                    published_at=published_at,
                )
                connection.execute(
                    """INSERT INTO knw_structure_publications VALUES
                       (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        publication_id.value,
                        scope_id.value,
                        idempotency_key.value,
                        request_digest.value,
                        batch_digest.value,
                        admission.admission_id.value,
                        admission.digest.value,
                        application_acceptance.digest.value,
                        application_acceptance.acceptance_ref,
                        application_acceptance.decision.value,
                        application_acceptance.report_digest.value,
                        snapshot.snapshot_id.value,
                        _time(published_at),
                        receipt.digest.value,
                    ),
                )
                return receipt
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Structure publication violated a persistence invariant",
                {"sqlite_error": str(exc)},
            ) from exc

    @staticmethod
    def _apply_enrich(
        *,
        previous_members: dict[StableId, CoverageMember],
        previous_ownership: dict[StableId, StableId],
        target_coverage_root_id: StableId,
        local_members: dict[StableId, CoverageMember],
        declared_members: dict[StableId, CoverageMember],
    ) -> tuple[dict[StableId, CoverageMember], dict[StableId, StableId]]:
        previous_owned = {
            root_id: previous_members[root_id]
            for root_id, owner in previous_ownership.items()
            if owner == target_coverage_root_id
        }
        expected_declared = dict(previous_owned)
        final_members = dict(previous_members)
        final_ownership = dict(previous_ownership)
        for root_id, member in local_members.items():
            existing = previous_members.get(root_id)
            if existing is not None:
                if existing != member:
                    raise _invalid(
                        "ENRICH_STATE_CONFLICT",
                        "ENRICH cannot add a different State for an existing Root",
                    )
                if previous_ownership[root_id] != target_coverage_root_id:
                    raise _invalid(
                        "COVERAGE_OWNERSHIP_OVERLAP",
                        "ENRICH cannot claim a Root owned by another Coverage",
                    )
            expected_declared[root_id] = member
            final_members[root_id] = member
            final_ownership[root_id] = target_coverage_root_id
        if declared_members != expected_declared:
            raise _invalid(
                "ENRICH_COVERAGE_MANIFEST_INVALID",
                "ENRICH Coverage Manifest must be exact base ownership union local members",
            )
        return final_members, final_ownership

    @staticmethod
    def _apply_replace_coverage(
        *,
        previous_members: dict[StableId, CoverageMember],
        previous_ownership: dict[StableId, StableId],
        target_coverage_root_id: StableId,
        local_members: dict[StableId, CoverageMember],
        declared_members: dict[StableId, CoverageMember],
    ) -> tuple[dict[StableId, CoverageMember], dict[StableId, StableId]]:
        if declared_members != local_members:
            raise _invalid(
                "REPLACEMENT_COVERAGE_MANIFEST_INVALID",
                "REPLACE_COVERAGE Manifest must equal the admitted local closure",
            )
        removed = {
            root_id
            for root_id, owner in previous_ownership.items()
            if owner == target_coverage_root_id
        }
        final_members = {
            root_id: member
            for root_id, member in previous_members.items()
            if root_id not in removed
        }
        final_ownership = {
            root_id: owner
            for root_id, owner in previous_ownership.items()
            if root_id not in removed
        }
        for root_id, member in local_members.items():
            if root_id in final_members:
                raise _invalid(
                    "COVERAGE_OWNERSHIP_OVERLAP",
                    "replacement cannot claim a Root owned by another Coverage",
                )
            final_members[root_id] = member
            final_ownership[root_id] = target_coverage_root_id
        return final_members, final_ownership

    def _insert_batch(
        self, connection: sqlite3.Connection, batch: StructureKnowledgeBatch
    ) -> None:
        for evidence in batch.evidence:
            self._insert_immutable(
                connection,
                table="knw_structure_evidence",
                id_column="evidence_id",
                object_id=evidence.evidence_id,
                record_digest=digest_of(evidence),
                columns=(
                    "evidence_id",
                    "artifact_id",
                    "source_context_id",
                    "byte_start",
                    "byte_end",
                    "locator",
                    "excerpt",
                    "excerpt_digest",
                    "artifact_content_digest",
                    "evidence_digest",
                    "record_digest",
                ),
                values=(
                    evidence.evidence_id.value,
                    evidence.artifact_id.value,
                    evidence.source_context_id.value,
                    evidence.byte_start,
                    evidence.byte_end,
                    evidence.locator,
                    evidence.excerpt,
                    evidence.excerpt_digest.value,
                    evidence.artifact_content_digest.value,
                    evidence.digest.value,
                    digest_of(evidence).value,
                ),
            )
        for entity in batch.entities:
            self._insert_entity_record(connection, entity)
        # Exact upstream Entity roots/states must pre-exist in an authoritative
        # Snapshot.  They are verified later and are never inserted from input.
        for relation in batch.relation_facts:
            self._insert_relation_record(connection, relation)
        for literal in batch.literal_facts:
            self._insert_literal_record(connection, literal)
        self._insert_coverage_record(connection, batch.coverage)

    def _insert_entity_record(
        self, connection: sqlite3.Connection, record: EntityRecord
    ) -> None:
        root = record.root
        root_digest = digest_of(root)
        self._insert_immutable(
            connection,
            table="knw_structure_entity_roots",
            id_column="entity_root_id",
            object_id=root.entity_root_id,
            record_digest=root_digest,
            columns=(
                "entity_root_id",
                "entity_type",
                "identity_scheme",
                "root_fields_json",
                "allocation_key_digest",
                "record_digest",
            ),
            values=(
                root.entity_root_id.value,
                root.entity_type.value,
                root.identity_scheme,
                _json(root.root_fields.as_dict()),
                root.allocation_key_digest.value,
                root_digest.value,
            ),
        )
        state = record.state
        state_record_digest = digest_of(state)
        self._insert_immutable(
            connection,
            table="knw_structure_entity_states",
            id_column="entity_state_id",
            object_id=state.entity_state_id,
            record_digest=state_record_digest,
            columns=(
                "entity_state_id",
                "entity_root_id",
                "entity_type",
                "state_payload_json",
                "state_digest",
                "allocation_key_digest",
                "record_digest",
            ),
            values=(
                state.entity_state_id.value,
                state.entity_root_id.value,
                state.entity_type.value,
                _json(state.state_payload_fields.as_dict()),
                state.entity_state_digest.value,
                state.allocation_key_digest.value,
                state_record_digest.value,
            ),
        )

    def _insert_relation_record(
        self, connection: sqlite3.Connection, record: RelationFactRecord
    ) -> None:
        root = record.root
        root_digest = digest_of(root)
        self._insert_immutable(
            connection,
            table="knw_structure_relation_roots",
            id_column="relation_root_id",
            object_id=root.relation_root_id,
            record_digest=root_digest,
            columns=(
                "relation_root_id",
                "owning_scope_id",
                "schema_ref",
                "subject_entity_root_id",
                "subject_entity_type",
                "subject_owning_scope_id",
                "predicate",
                "object_entity_root_id",
                "object_entity_type",
                "object_owning_scope_id",
                "observation_modality",
                "allocation_key_digest",
                "record_digest",
            ),
            values=(
                root.relation_root_id.value,
                root.owning_scope_id.value,
                root.schema_ref,
                root.subject.entity_root_id.value,
                root.subject.entity_type.value,
                root.subject.owning_scope_id.value,
                root.predicate.value,
                root.object.entity_root_id.value,
                root.object.entity_type.value,
                root.object.owning_scope_id.value,
                root.observation_modality.value,
                root.allocation_key_digest.value,
                root_digest.value,
            ),
        )
        state = record.state
        state_record_digest = digest_of(state)
        self._insert_immutable(
            connection,
            table="knw_structure_relation_states",
            id_column="relation_state_id",
            object_id=state.relation_state_id,
            record_digest=state_record_digest,
            columns=(
                "relation_state_id",
                "relation_root_id",
                "subject_entity_state_id",
                "object_entity_state_id",
                "source_revision",
                "knowledge_context_digest",
                "evidence_refs_json",
                "predicate_state_payload_json",
                "state_digest",
                "allocation_key_digest",
                "record_digest",
            ),
            values=(
                state.relation_state_id.value,
                state.relation_root_id.value,
                state.subject_entity_state_id.value,
                state.object_entity_state_id.value,
                state.source_revision,
                state.knowledge_context_digest.value,
                _refs(state.evidence_references),
                _json(state.predicate_state_payload_fields.as_dict()),
                state.relation_state_digest.value,
                state.allocation_key_digest.value,
                state_record_digest.value,
            ),
        )

    def _insert_literal_record(
        self, connection: sqlite3.Connection, record: LiteralFactRecord
    ) -> None:
        root = record.root
        root_digest = digest_of(root)
        self._insert_immutable(
            connection,
            table="knw_structure_literal_roots",
            id_column="literal_root_id",
            object_id=root.literal_root_id,
            record_digest=root_digest,
            columns=(
                "literal_root_id",
                "owning_scope_id",
                "schema_ref",
                "subject_entity_root_id",
                "subject_entity_type",
                "subject_owning_scope_id",
                "predicate",
                "literal_type",
                "literal_value_json",
                "observation_modality",
                "allocation_key_digest",
                "record_digest",
            ),
            values=(
                root.literal_root_id.value,
                root.owning_scope_id.value,
                root.schema_ref,
                root.subject.entity_root_id.value,
                root.subject.entity_type.value,
                root.subject.owning_scope_id.value,
                root.predicate,
                root.object.literal_type.value,
                _json(root.object.value),
                root.observation_modality,
                root.allocation_key_digest.value,
                root_digest.value,
            ),
        )
        state = record.state
        state_record_digest = digest_of(state)
        self._insert_immutable(
            connection,
            table="knw_structure_literal_states",
            id_column="literal_state_id",
            object_id=state.literal_state_id,
            record_digest=state_record_digest,
            columns=(
                "literal_state_id",
                "literal_root_id",
                "subject_entity_state_id",
                "source_revision",
                "knowledge_context_digest",
                "evidence_refs_json",
                "state_digest",
                "allocation_key_digest",
                "record_digest",
            ),
            values=(
                state.literal_state_id.value,
                state.literal_root_id.value,
                state.subject_entity_state_id.value,
                state.source_revision,
                state.knowledge_context_digest.value,
                _refs(state.evidence_references),
                state.literal_state_digest.value,
                state.allocation_key_digest.value,
                state_record_digest.value,
            ),
        )

    def _insert_coverage_record(
        self, connection: sqlite3.Connection, record: CoverageRecord
    ) -> None:
        root = record.root
        root_digest = digest_of(root)
        self._insert_immutable(
            connection,
            table="knw_structure_coverage_roots",
            id_column="coverage_root_id",
            object_id=root.coverage_root_id,
            record_digest=root_digest,
            columns=(
                "coverage_root_id",
                "coverage_root_ref",
                "owning_scope_id",
                "profile_ref",
                "schema_ref",
                "schema_digest",
                "source_binding_id",
                "logical_reactor_root",
                "evaluation_context_ref",
                "evaluation_context_digest",
                "covered_entity_types_json",
                "covered_relation_predicates_json",
                "canonicalization_ref",
                "canonicalization_digest",
                "allocation_key_digest",
                "record_digest",
            ),
            values=(
                root.coverage_root_id.value,
                root.coverage_root_ref,
                root.owning_scope_id.value,
                root.profile_ref,
                root.schema_ref,
                root.schema_digest.value,
                root.source_binding_id.value,
                root.logical_reactor_root,
                root.maven_evaluation_context_ref,
                root.maven_evaluation_context_digest.value,
                _json(tuple(item.value for item in root.covered_entity_types)),
                _json(
                    tuple(item.value for item in root.covered_relation_predicates)
                ),
                root.canonicalization_ref,
                root.canonicalization_digest.value,
                root.allocation_key_digest.value,
                root_digest.value,
            ),
        )
        state = record.state
        state_record_digest = digest_of(state)
        manifest = state.complete_member_manifest
        self._insert_immutable(
            connection,
            table="knw_structure_coverage_states",
            id_column="coverage_state_id",
            object_id=state.coverage_state_id,
            record_digest=state_record_digest,
            columns=(
                "coverage_state_id",
                "coverage_root_id",
                "source_revision",
                "knowledge_context_digest",
                "schema_ref",
                "schema_digest",
                "evaluation_context_ref",
                "evaluation_context_digest",
                "canonicalization_ref",
                "canonicalization_digest",
                "member_manifest_json",
                "member_manifest_digest",
                "evidence_refs_json",
                "state_digest",
                "allocation_key_digest",
                "record_digest",
            ),
            values=(
                state.coverage_state_id.value,
                state.coverage_root_id.value,
                state.source_revision,
                state.knowledge_context_digest.value,
                state.schema_ref,
                state.schema_digest.value,
                state.maven_evaluation_context_ref,
                state.maven_evaluation_context_digest.value,
                state.canonicalization_ref,
                state.canonicalization_digest.value,
                _json(
                    tuple(
                        member.canonical_value() for member in manifest.members
                    )
                ),
                manifest.digest.value,
                _refs(state.evidence_references),
                state.coverage_state_digest.value,
                state.allocation_key_digest.value,
                state_record_digest.value,
            ),
        )

    @staticmethod
    def _insert_immutable(
        connection: sqlite3.Connection,
        *,
        table: str,
        id_column: str,
        object_id: StableId,
        record_digest: Digest,
        columns: tuple[str, ...],
        values: tuple[object, ...],
    ) -> None:
        row = connection.execute(
            f"SELECT record_digest FROM {table} WHERE {id_column} = ?",
            (object_id.value,),
        ).fetchone()
        if row is not None:
            if row["record_digest"] != record_digest.value:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "immutable Structure identity has conflicting content",
                )
            return
        placeholders = ",".join("?" for _ in values)
        connection.execute(
            f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
            values,
        )

    @staticmethod
    def _load_evidence(
        connection: sqlite3.Connection, evidence_id: StableId
    ) -> StructureEvidence:
        row = connection.execute(
            "SELECT * FROM knw_structure_evidence WHERE evidence_id = ?",
            (evidence_id.value,),
        ).fetchone()
        if row is None:
            raise _invalid(
                "STRUCTURE_EVIDENCE_NOT_FOUND",
                "Structure Evidence was not found",
            )
        evidence = StructureEvidence(
            evidence_id=StableId(row["evidence_id"]),
            artifact_id=StableId(row["artifact_id"]),
            source_context_id=StableId(row["source_context_id"]),
            byte_start=row["byte_start"],
            byte_end=row["byte_end"],
            locator=row["locator"],
            excerpt=row["excerpt"],
            excerpt_digest=Digest(row["excerpt_digest"]),
            artifact_content_digest=Digest(row["artifact_content_digest"]),
            digest=Digest(row["evidence_digest"]),
        )
        _verify_record_digest(row, evidence, "Structure Evidence")
        return evidence

    @staticmethod
    def _load_entity_record(
        connection: sqlite3.Connection,
        root_id: StableId,
        state_id: StableId,
    ) -> EntityRecord:
        root_row = connection.execute(
            """SELECT * FROM knw_structure_entity_roots
               WHERE entity_root_id = ?""",
            (root_id.value,),
        ).fetchone()
        state_row = connection.execute(
            """SELECT * FROM knw_structure_entity_states
               WHERE entity_state_id = ?""",
            (state_id.value,),
        ).fetchone()
        if root_row is None or state_row is None:
            raise _inconsistent("Structure Entity Root/State record is missing")
        root = EntityRoot(
            entity_root_id=StableId(root_row["entity_root_id"]),
            entity_type=EntityType(root_row["entity_type"]),
            identity_scheme=root_row["identity_scheme"],
            root_fields=_fields(root_row["root_fields_json"]),
            allocation_key_digest=Digest(root_row["allocation_key_digest"]),
        )
        state = EntityState(
            entity_state_id=StableId(state_row["entity_state_id"]),
            entity_state_digest=Digest(state_row["state_digest"]),
            entity_root_id=StableId(state_row["entity_root_id"]),
            entity_type=EntityType(state_row["entity_type"]),
            state_payload_fields=_fields(state_row["state_payload_json"]),
            allocation_key_digest=Digest(state_row["allocation_key_digest"]),
        )
        _verify_record_digest(root_row, root, "Structure Entity Root")
        _verify_record_digest(state_row, state, "Structure Entity State")
        return EntityRecord(root=root, state=state)

    @staticmethod
    def _load_relation_record(
        connection: sqlite3.Connection,
        root_id: StableId,
        state_id: StableId,
    ) -> RelationFactRecord:
        root_row = connection.execute(
            """SELECT * FROM knw_structure_relation_roots
               WHERE relation_root_id = ?""",
            (root_id.value,),
        ).fetchone()
        state_row = connection.execute(
            """SELECT * FROM knw_structure_relation_states
               WHERE relation_state_id = ?""",
            (state_id.value,),
        ).fetchone()
        if root_row is None or state_row is None:
            raise _inconsistent("Structure Relation Fact Root/State record is missing")
        root = RelationFactRoot(
            relation_root_id=StableId(root_row["relation_root_id"]),
            owning_scope_id=StableId(root_row["owning_scope_id"]),
            schema_ref=root_row["schema_ref"],
            subject=EntityRef(
                entity_root_id=StableId(root_row["subject_entity_root_id"]),
                entity_type=EntityType(root_row["subject_entity_type"]),
                owning_scope_id=StableId(root_row["subject_owning_scope_id"]),
            ),
            predicate=RelationPredicate(root_row["predicate"]),
            object=EntityRef(
                entity_root_id=StableId(root_row["object_entity_root_id"]),
                entity_type=EntityType(root_row["object_entity_type"]),
                owning_scope_id=StableId(root_row["object_owning_scope_id"]),
            ),
            observation_modality=ObservationModality(
                root_row["observation_modality"]
            ),
            allocation_key_digest=Digest(root_row["allocation_key_digest"]),
        )
        state = RelationFactState(
            relation_state_id=StableId(state_row["relation_state_id"]),
            relation_state_digest=Digest(state_row["state_digest"]),
            relation_root_id=StableId(state_row["relation_root_id"]),
            subject_entity_state_id=StableId(
                state_row["subject_entity_state_id"]
            ),
            object_entity_state_id=StableId(
                state_row["object_entity_state_id"]
            ),
            source_revision=state_row["source_revision"],
            knowledge_context_digest=Digest(
                state_row["knowledge_context_digest"]
            ),
            evidence_references=_parse_refs(state_row["evidence_refs_json"]),
            predicate_state_payload_fields=_fields(
                state_row["predicate_state_payload_json"]
            ),
            allocation_key_digest=Digest(state_row["allocation_key_digest"]),
        )
        _verify_record_digest(root_row, root, "Structure Relation Fact Root")
        _verify_record_digest(state_row, state, "Structure Relation Fact State")
        return RelationFactRecord(root=root, state=state)

    @staticmethod
    def _load_literal_record(
        connection: sqlite3.Connection,
        root_id: StableId,
        state_id: StableId,
    ) -> LiteralFactRecord:
        root_row = connection.execute(
            """SELECT * FROM knw_structure_literal_roots
               WHERE literal_root_id = ?""",
            (root_id.value,),
        ).fetchone()
        state_row = connection.execute(
            """SELECT * FROM knw_structure_literal_states
               WHERE literal_state_id = ?""",
            (state_id.value,),
        ).fetchone()
        if root_row is None or state_row is None:
            raise _inconsistent("Structure Literal Fact Root/State record is missing")
        root = LiteralFactRoot(
            literal_root_id=StableId(root_row["literal_root_id"]),
            owning_scope_id=StableId(root_row["owning_scope_id"]),
            schema_ref=root_row["schema_ref"],
            subject=EntityRef(
                entity_root_id=StableId(root_row["subject_entity_root_id"]),
                entity_type=EntityType(root_row["subject_entity_type"]),
                owning_scope_id=StableId(root_row["subject_owning_scope_id"]),
            ),
            predicate=root_row["predicate"],
            object=LiteralObject(
                literal_type=LiteralType(root_row["literal_type"]),
                value=_json_value(root_row["literal_value_json"]),
            ),
            observation_modality=root_row["observation_modality"],
            allocation_key_digest=Digest(root_row["allocation_key_digest"]),
        )
        state = LiteralFactState(
            literal_state_id=StableId(state_row["literal_state_id"]),
            literal_state_digest=Digest(state_row["state_digest"]),
            literal_root_id=StableId(state_row["literal_root_id"]),
            subject_entity_state_id=StableId(
                state_row["subject_entity_state_id"]
            ),
            source_revision=state_row["source_revision"],
            knowledge_context_digest=Digest(
                state_row["knowledge_context_digest"]
            ),
            evidence_references=_parse_refs(state_row["evidence_refs_json"]),
            allocation_key_digest=Digest(state_row["allocation_key_digest"]),
        )
        _verify_record_digest(root_row, root, "Structure Literal Fact Root")
        _verify_record_digest(state_row, state, "Structure Literal Fact State")
        return LiteralFactRecord(root=root, state=state)

    @staticmethod
    def _load_coverage_record(
        connection: sqlite3.Connection,
        root_id: StableId,
        state_id: StableId,
    ) -> CoverageRecord:
        root_row = connection.execute(
            """SELECT * FROM knw_structure_coverage_roots
               WHERE coverage_root_id = ?""",
            (root_id.value,),
        ).fetchone()
        state_row = connection.execute(
            """SELECT * FROM knw_structure_coverage_states
               WHERE coverage_state_id = ?""",
            (state_id.value,),
        ).fetchone()
        if root_row is None or state_row is None:
            raise _inconsistent("Structure Coverage Root/State record is missing")
        root = CoverageRoot(
            coverage_root_id=StableId(root_row["coverage_root_id"]),
            coverage_root_ref=root_row["coverage_root_ref"],
            owning_scope_id=StableId(root_row["owning_scope_id"]),
            profile_ref=root_row["profile_ref"],
            schema_ref=root_row["schema_ref"],
            schema_digest=Digest(root_row["schema_digest"]),
            source_binding_id=StableId(root_row["source_binding_id"]),
            logical_reactor_root=root_row["logical_reactor_root"],
            maven_evaluation_context_ref=root_row["evaluation_context_ref"],
            maven_evaluation_context_digest=Digest(
                root_row["evaluation_context_digest"]
            ),
            covered_entity_types=tuple(
                EntityType(item)
                for item in _json_array(root_row["covered_entity_types_json"])
            ),
            covered_relation_predicates=tuple(
                RelationPredicate(item)
                for item in _json_array(
                    root_row["covered_relation_predicates_json"]
                )
            ),
            canonicalization_ref=root_row["canonicalization_ref"],
            canonicalization_digest=Digest(
                root_row["canonicalization_digest"]
            ),
            allocation_key_digest=Digest(root_row["allocation_key_digest"]),
        )
        manifest_members = tuple(
            CoverageMember(
                kind=CoverageMemberKind(item["kind"]),
                root_id=StableId(item["root_id"]),
                state_id=StableId(item["state_id"]),
                state_digest=Digest(item["state_digest"]),
            )
            for item in _json_object_array(state_row["member_manifest_json"])
        )
        manifest = CompleteMemberManifest(
            members=manifest_members,
            digest=Digest(state_row["member_manifest_digest"]),
        )
        state = CoverageState(
            coverage_state_id=StableId(state_row["coverage_state_id"]),
            coverage_state_digest=Digest(state_row["state_digest"]),
            coverage_root_id=StableId(state_row["coverage_root_id"]),
            source_revision=state_row["source_revision"],
            knowledge_context_digest=Digest(
                state_row["knowledge_context_digest"]
            ),
            schema_ref=state_row["schema_ref"],
            schema_digest=Digest(state_row["schema_digest"]),
            maven_evaluation_context_ref=state_row["evaluation_context_ref"],
            maven_evaluation_context_digest=Digest(
                state_row["evaluation_context_digest"]
            ),
            canonicalization_ref=state_row["canonicalization_ref"],
            canonicalization_digest=Digest(
                state_row["canonicalization_digest"]
            ),
            complete_member_manifest=manifest,
            evidence_references=_parse_refs(state_row["evidence_refs_json"]),
            allocation_key_digest=Digest(state_row["allocation_key_digest"]),
        )
        _verify_record_digest(root_row, root, "Structure Coverage Root")
        _verify_record_digest(state_row, state, "Structure Coverage State")
        return CoverageRecord(root=root, state=state)

    def _load_snapshot(
        self, connection: sqlite3.Connection, snapshot_id: StableId
    ) -> StructureSnapshot:
        row = connection.execute(
            """SELECT * FROM knw_structure_snapshots WHERE snapshot_id = ?""",
            (snapshot_id.value,),
        ).fetchone()
        if row is None:
            raise _invalid(
                "STRUCTURE_SNAPSHOT_NOT_FOUND",
                "Structure Snapshot was not found",
            )
        members = tuple(
            CoverageMember(
                kind=CoverageMemberKind(item["member_kind"]),
                root_id=StableId(item["root_id"]),
                state_id=StableId(item["state_id"]),
                state_digest=Digest(item["state_digest"]),
            )
            for item in connection.execute(
                """SELECT member_kind, root_id, state_id, state_digest
                   FROM knw_structure_snapshot_members
                   WHERE snapshot_id = ? ORDER BY member_kind, root_id""",
                (snapshot_id.value,),
            ).fetchall()
        )
        coverages = tuple(
            SnapshotCoverage(
                coverage_root_id=StableId(item["coverage_root_id"]),
                coverage_state_id=StableId(item["coverage_state_id"]),
                coverage_state_digest=Digest(item["coverage_state_digest"]),
            )
            for item in connection.execute(
                """SELECT coverage_root_id, coverage_state_id,
                          coverage_state_digest
                   FROM knw_structure_snapshot_coverages
                   WHERE snapshot_id = ? ORDER BY coverage_root_id""",
                (snapshot_id.value,),
            ).fetchall()
        )
        upstream = tuple(
            SnapshotUpstreamEntity(
                upstream_snapshot_id=StableId(item["upstream_snapshot_id"]),
                entity_root_id=StableId(item["entity_root_id"]),
                entity_state_id=StableId(item["entity_state_id"]),
                entity_state_digest=Digest(item["entity_state_digest"]),
            )
            for item in connection.execute(
                """SELECT upstream_snapshot_id, entity_root_id,
                          entity_state_id, entity_state_digest
                   FROM knw_structure_snapshot_upstream_entities
                   WHERE snapshot_id = ?
                   ORDER BY entity_root_id, upstream_snapshot_id""",
                (snapshot_id.value,),
            ).fetchall()
        )
        snapshot = StructureSnapshot(
            snapshot_id=StableId(row["snapshot_id"]),
            scope_id=StableId(row["scope_id"]),
            snapshot_revision=Revision(row["snapshot_revision"]),
            previous_snapshot_id=(
                StableId(row["previous_snapshot_id"])
                if row["previous_snapshot_id"] is not None
                else None
            ),
            schema_ref=row["schema_ref"],
            schema_digest=Digest(row["schema_digest"]),
            schema_adoption_mode=StructureSchemaAdoptionMode(
                row["schema_adoption_mode"]
            ),
            schema_registration_digest=Digest(
                row["schema_registration_digest"]
            ),
            schema_availability_digest=Digest(
                row["schema_availability_digest"]
            ),
            schema_adoption_digest=Digest(row["schema_adoption_digest"]),
            publication_mode=PublicationMode(row["publication_mode"]),
            members=members,
            coverages=coverages,
            upstream_entities=upstream,
            manifest_digest=Digest(row["manifest_digest"]),
            published_at=_parse_time(row["published_at"]),
        )
        ownership = self._load_ownership(connection, snapshot_id)
        validated_upstream = self._validate_final_closure(
            connection,
            members=snapshot.members,
            coverages=snapshot.coverages,
            ownership=ownership,
            upstream_by_root={
                item.entity_root_id: item for item in snapshot.upstream_entities
            },
            expected_scope_id=snapshot.scope_id,
            expected_schema_ref=snapshot.schema_ref,
        )
        if validated_upstream != snapshot.upstream_entities:
            raise _inconsistent(
                "Structure Snapshot upstream Entity Manifest is not exact"
            )
        return snapshot

    @staticmethod
    def _load_ownership(
        connection: sqlite3.Connection, snapshot_id: StableId
    ) -> dict[StableId, StableId]:
        rows = connection.execute(
            """SELECT ownership.root_id, ownership.coverage_root_id,
                      ownership.member_kind AS ownership_kind,
                      member.member_kind AS manifest_kind
               FROM knw_structure_snapshot_ownership AS ownership
               JOIN knw_structure_snapshot_members AS member
                 ON member.snapshot_id = ownership.snapshot_id
                AND member.root_id = ownership.root_id
               WHERE ownership.snapshot_id = ? ORDER BY ownership.root_id""",
            (snapshot_id.value,),
        ).fetchall()
        if any(item["ownership_kind"] != item["manifest_kind"] for item in rows):
            raise _inconsistent(
                "Structure Snapshot ownership member kind is inconsistent"
            )
        ownership = {
            StableId(item["root_id"]): StableId(item["coverage_root_id"])
            for item in rows
        }
        if len(ownership) != len(rows):
            raise _inconsistent("Structure Snapshot ownership is ambiguous")
        return ownership

    def _validate_final_closure(
        self,
        connection: sqlite3.Connection,
        *,
        members: tuple[CoverageMember, ...],
        coverages: tuple[SnapshotCoverage, ...],
        ownership: dict[StableId, StableId],
        upstream_by_root: dict[StableId, SnapshotUpstreamEntity],
        expected_scope_id: StableId,
        expected_schema_ref: str,
    ) -> tuple[SnapshotUpstreamEntity, ...]:
        members_by_root = {member.root_id: member for member in members}
        if len(members_by_root) != len(members) or set(ownership) != set(
            members_by_root
        ):
            raise _inconsistent(
                "Structure Snapshot members and Coverage ownership do not match"
            )

        records: dict[
            StableId, EntityRecord | RelationFactRecord | LiteralFactRecord
        ] = {}
        for member in members:
            record = self._load_member_record(connection, member)
            if record.state_digest != member.state_digest:
                raise _inconsistent(
                    "Structure Snapshot member State digest does not match storage"
                )
            records[member.root_id] = record
            if isinstance(record, EntityRecord):
                record_scope_id = record.root.owning_scope_id
                record_schema_ref = expected_schema_ref
            else:
                record_scope_id = record.root.owning_scope_id
                record_schema_ref = record.root.schema_ref
            if (
                record_scope_id != expected_scope_id
                or record_schema_ref != expected_schema_ref
            ):
                raise _inconsistent(
                    "Structure Snapshot member Scope/Schema does not match its Snapshot"
                )
            for evidence_id in _record_evidence_references(record):
                self._load_evidence(connection, evidence_id)

        expected_ownership: dict[StableId, StableId] = {}
        coverage_ids = {coverage.coverage_root_id for coverage in coverages}
        if len(coverage_ids) != len(coverages):
            raise _inconsistent("Structure Snapshot has duplicate Coverage Roots")
        for binding in coverages:
            coverage = self._load_coverage_record(
                connection,
                binding.coverage_root_id,
                binding.coverage_state_id,
            )
            if (
                coverage.root.owning_scope_id != expected_scope_id
                or coverage.root.schema_ref != expected_schema_ref
            ):
                raise _inconsistent(
                    "Structure Snapshot Coverage Scope/Schema is inconsistent"
                )
            if coverage.state.state_digest != binding.coverage_state_digest:
                raise _inconsistent(
                    "Structure Snapshot Coverage State digest does not match storage"
                )
            for evidence_id in coverage.state.evidence_references:
                self._load_evidence(connection, evidence_id)
            for member in coverage.state.complete_member_manifest.members:
                existing = expected_ownership.get(member.root_id)
                if existing is not None and existing != binding.coverage_root_id:
                    raise _inconsistent(
                        "Structure Snapshot Coverage ownership overlaps"
                    )
                if members_by_root.get(member.root_id) != member:
                    raise _inconsistent(
                        "Coverage Manifest is not an exact subset of the Snapshot"
                    )
                expected_ownership[member.root_id] = binding.coverage_root_id
        if expected_ownership != ownership or any(
            owner not in coverage_ids for owner in ownership.values()
        ):
            raise _inconsistent(
                "Structure Snapshot ownership differs from Coverage Manifests"
            )

        local_entities = {
            root_id: record
            for root_id, record in records.items()
            if isinstance(record, EntityRecord)
        }
        verified_upstream: dict[StableId, tuple[SnapshotUpstreamEntity, EntityRecord]] = {}
        for root_id, upstream in upstream_by_root.items():
            exact = self._verify_exact_upstream_binding(connection, upstream)
            if root_id != exact[0].entity_root_id:
                raise _inconsistent("upstream Entity Root key is inconsistent")
            local = local_entities.get(root_id)
            if local is not None:
                if (
                    local.state_id != exact[0].entity_state_id
                    or local.state_digest != exact[0].entity_state_digest
                ):
                    raise _invalid(
                        "AMBIGUOUS_RELATION_ENDPOINT",
                        "Relation endpoint has local and upstream States for one Root",
                    )
                continue
            verified_upstream[root_id] = exact

        required_upstream: set[StableId] = set()
        for record in records.values():
            if isinstance(record, RelationFactRecord):
                self._require_endpoint(
                    ref=record.root.subject,
                    state_id=record.state.subject_entity_state_id,
                    local_entities=local_entities,
                    upstream_entities=verified_upstream,
                    required_upstream=required_upstream,
                )
                self._require_endpoint(
                    ref=record.root.object,
                    state_id=record.state.object_entity_state_id,
                    local_entities=local_entities,
                    upstream_entities=verified_upstream,
                    required_upstream=required_upstream,
                )
            elif isinstance(record, LiteralFactRecord):
                self._require_endpoint(
                    ref=record.root.subject,
                    state_id=record.state.subject_entity_state_id,
                    local_entities=local_entities,
                    upstream_entities=verified_upstream,
                    required_upstream=required_upstream,
                )
        return tuple(
            sorted(
                (verified_upstream[root_id][0] for root_id in required_upstream),
                key=lambda item: (
                    item.entity_root_id.value,
                    item.upstream_snapshot_id.value,
                ),
            )
        )

    def _load_member_record(
        self, connection: sqlite3.Connection, member: CoverageMember
    ) -> EntityRecord | RelationFactRecord | LiteralFactRecord:
        if member.kind is CoverageMemberKind.ENTITY:
            return self._load_entity_record(
                connection, member.root_id, member.state_id
            )
        if member.kind is CoverageMemberKind.RELATION_FACT:
            return self._load_relation_record(
                connection, member.root_id, member.state_id
            )
        return self._load_literal_record(
            connection, member.root_id, member.state_id
        )

    @staticmethod
    def _require_endpoint(
        *,
        ref: EntityRef,
        state_id: StableId,
        local_entities: dict[StableId, EntityRecord],
        upstream_entities: dict[
            StableId, tuple[SnapshotUpstreamEntity, EntityRecord]
        ],
        required_upstream: set[StableId],
    ) -> None:
        local = local_entities.get(ref.entity_root_id)
        if local is not None:
            record = local
        else:
            upstream = upstream_entities.get(ref.entity_root_id)
            if upstream is None:
                raise _invalid(
                    "DANGLING_RELATION_ENDPOINT",
                    "final Structure Snapshot has a dangling typed endpoint",
                )
            required_upstream.add(ref.entity_root_id)
            record = upstream[1]
        if (
            record.state_id != state_id
            or record.root.entity_type != ref.entity_type
            or record.root.owning_scope_id != ref.owning_scope_id
        ):
            raise _invalid(
                "RELATION_ENDPOINT_STATE_MISMATCH",
                "final typed endpoint does not resolve to its exact Entity State",
            )

    def _verify_exact_upstream_entity(
        self,
        connection: sqlite3.Connection,
        snapshot_id: StableId,
        supplied: EntityRecord,
    ) -> SnapshotUpstreamEntity:
        binding = SnapshotUpstreamEntity(
            upstream_snapshot_id=snapshot_id,
            entity_root_id=supplied.root_id,
            entity_state_id=supplied.state_id,
            entity_state_digest=supplied.state_digest,
        )
        exact_binding, exact_record = self._verify_exact_upstream_binding(
            connection, binding
        )
        if exact_record != supplied:
            raise _invalid(
                "UPSTREAM_ENTITY_RECORD_MISMATCH",
                "supplied exact upstream Entity differs from its Snapshot member",
            )
        return exact_binding

    def _verify_exact_upstream_binding(
        self,
        connection: sqlite3.Connection,
        binding: SnapshotUpstreamEntity,
    ) -> tuple[SnapshotUpstreamEntity, EntityRecord]:
        row = connection.execute(
            """SELECT member_kind, state_id, state_digest
               FROM knw_structure_snapshot_members
               WHERE snapshot_id = ? AND root_id = ?""",
            (
                binding.upstream_snapshot_id.value,
                binding.entity_root_id.value,
            ),
        ).fetchone()
        if (
            row is None
            or row["member_kind"] != CoverageMemberKind.ENTITY.value
            or row["state_id"] != binding.entity_state_id.value
            or row["state_digest"] != binding.entity_state_digest.value
        ):
            raise _invalid(
                "UPSTREAM_ENTITY_NOT_EXACT",
                "upstream Entity is not an exact member of its fixed Snapshot",
            )
        record = self._load_entity_record(
            connection, binding.entity_root_id, binding.entity_state_id
        )
        return binding, record

    @staticmethod
    def _insert_snapshot(
        connection: sqlite3.Connection,
        *,
        snapshot: StructureSnapshot,
        ownership: dict[StableId, StableId],
    ) -> None:
        connection.execute(
            """INSERT INTO knw_structure_snapshots VALUES
               (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot.snapshot_id.value,
                snapshot.scope_id.value,
                snapshot.snapshot_revision.value,
                (
                    snapshot.previous_snapshot_id.value
                    if snapshot.previous_snapshot_id is not None
                    else None
                ),
                snapshot.schema_ref,
                snapshot.schema_digest.value,
                snapshot.schema_adoption_mode.value,
                snapshot.schema_registration_digest.value,
                snapshot.schema_availability_digest.value,
                snapshot.schema_adoption_digest.value,
                snapshot.publication_mode.value,
                snapshot.manifest_digest.value,
                _time(snapshot.published_at),
            ),
        )
        connection.executemany(
            """INSERT INTO knw_structure_snapshot_members
               VALUES (?, ?, ?, ?, ?)""",
            (
                (
                    snapshot.snapshot_id.value,
                    member.kind.value,
                    member.root_id.value,
                    member.state_id.value,
                    member.state_digest.value,
                )
                for member in snapshot.members
            ),
        )
        connection.executemany(
            """INSERT INTO knw_structure_snapshot_coverages
               VALUES (?, ?, ?, ?)""",
            (
                (
                    snapshot.snapshot_id.value,
                    coverage.coverage_root_id.value,
                    coverage.coverage_state_id.value,
                    coverage.coverage_state_digest.value,
                )
                for coverage in snapshot.coverages
            ),
        )
        member_by_root = {member.root_id: member for member in snapshot.members}
        connection.executemany(
            """INSERT INTO knw_structure_snapshot_ownership
               VALUES (?, ?, ?, ?)""",
            (
                (
                    snapshot.snapshot_id.value,
                    root_id.value,
                    member_by_root[root_id].kind.value,
                    coverage_root_id.value,
                )
                for root_id, coverage_root_id in sorted(
                    ownership.items(), key=lambda item: item[0].value
                )
            ),
        )
        connection.executemany(
            """INSERT INTO knw_structure_snapshot_upstream_entities
               VALUES (?, ?, ?, ?, ?)""",
            (
                (
                    snapshot.snapshot_id.value,
                    upstream.upstream_snapshot_id.value,
                    upstream.entity_root_id.value,
                    upstream.entity_state_id.value,
                    upstream.entity_state_digest.value,
                )
                for upstream in snapshot.upstream_entities
            ),
        )

    def _idempotent(
        self,
        connection: sqlite3.Connection,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
    ) -> StructurePublicationReceipt | None:
        row = connection.execute(
            """SELECT publication_id, request_digest
               FROM knw_structure_publications WHERE idempotency_key = ?""",
            (idempotency_key.value,),
        ).fetchone()
        if row is None:
            return None
        if row["request_digest"] != request_digest.value:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "Structure publication idempotency key has a different request",
            )
        return self._load_receipt(
            connection, StableId(row["publication_id"])
        )

    def _load_receipt(
        self, connection: sqlite3.Connection, publication_id: StableId
    ) -> StructurePublicationReceipt:
        row = connection.execute(
            """SELECT * FROM knw_structure_publications
               WHERE publication_id = ?""",
            (publication_id.value,),
        ).fetchone()
        if row is None:
            raise _inconsistent("Structure Publication Receipt is missing")
        snapshot = self._load_snapshot(
            connection, StableId(row["snapshot_id"])
        )
        acceptance = StructureApplicationAcceptance(
            acceptance_ref=row["application_acceptance_ref"],
            decision=ApplicationAcceptanceDecision(
                row["application_acceptance_decision"]
            ),
            batch_digest=Digest(row["batch_digest"]),
            report_digest=Digest(row["application_report_digest"]),
            digest=Digest(row["application_acceptance_digest"]),
        )
        acceptance.require_valid()
        if acceptance.decision is not ApplicationAcceptanceDecision.PASS:
            raise _inconsistent(
                "persisted Structure Publication has no Application PASS"
            )
        admission = self._load_structure_admission(
            connection, StableId(row["admission_id"])
        )
        if (
            admission.outcome is not StructureAdmissionOutcome.ACCEPT
            or admission.digest.value != row["admission_digest"]
            or admission.batch_digest.value != row["batch_digest"]
        ):
            raise _inconsistent(
                "persisted Structure Publication has no exact Admission ACCEPT"
            )
        return StructurePublicationReceipt(
            publication_id=StableId(row["publication_id"]),
            request_digest=Digest(row["request_digest"]),
            batch_digest=Digest(row["batch_digest"]),
            admission_id=StableId(row["admission_id"]),
            admission_digest=Digest(row["admission_digest"]),
            application_acceptance_digest=Digest(
                row["application_acceptance_digest"]
            ),
            snapshot=snapshot,
            published_at=_parse_time(row["published_at"]),
            digest=Digest(row["result_digest"]),
        )


def _snapshot_member(
    snapshot: StructureSnapshot,
    kind: CoverageMemberKind,
    root_id: StableId,
) -> CoverageMember:
    matches = tuple(
        member
        for member in snapshot.members
        if member.kind is kind and member.root_id == root_id
    )
    if len(matches) != 1:
        raise _invalid(
            "STRUCTURE_MEMBER_NOT_FOUND",
            "typed Root is not a member of the exact Structure Snapshot",
        )
    return matches[0]


def _record_evidence_references(
    record: EntityRecord | RelationFactRecord | LiteralFactRecord,
) -> tuple[StableId, ...]:
    return record.state.evidence_references


def _verify_record_digest(row: sqlite3.Row, value: object, label: str) -> None:
    if row["record_digest"] != digest_of(value).value:
        raise _inconsistent(f"{label} persistence digest does not verify")


def _fields(value: str) -> CanonicalFields:
    try:
        document = json.loads(value)
    except (json.JSONDecodeError, TypeError) as exc:
        raise _inconsistent("canonical Structure fields contain invalid JSON") from exc
    if not isinstance(document, dict):
        raise _inconsistent("canonical Structure fields are not a JSON object")
    return CanonicalFields(document)


def _parse_refs(value: str) -> tuple[StableId, ...]:
    return tuple(StableId(item) for item in _json_array(value))


def _refs(values: tuple[StableId, ...]) -> str:
    return _json(tuple(item.value for item in values))


def _json_array(value: str) -> list[str]:
    try:
        document = json.loads(value)
    except (json.JSONDecodeError, TypeError) as exc:
        raise _inconsistent("Structure string array contains invalid JSON") from exc
    if not isinstance(document, list) or any(
        not isinstance(item, str) for item in document
    ):
        raise _inconsistent("Structure persistence value is not a JSON string array")
    return document


def _json_object_array(value: str) -> list[dict[str, str]]:
    try:
        document = json.loads(value)
    except (json.JSONDecodeError, TypeError) as exc:
        raise _inconsistent("Structure object array contains invalid JSON") from exc
    if not isinstance(document, list) or any(
        not isinstance(item, dict)
        or set(item) != {"kind", "root_id", "state_id", "state_digest"}
        or any(not isinstance(field, str) for field in item.values())
        for item in document
    ):
        raise _inconsistent(
            "Structure Coverage Manifest is not a canonical JSON object array"
        )
    return document


def _json_value(value: str) -> bool | int | str:
    try:
        document = json.loads(value)
    except (json.JSONDecodeError, TypeError) as exc:
        raise _inconsistent("typed literal contains invalid JSON") from exc
    if type(document) not in (bool, int, str):
        raise _inconsistent("typed literal persistence value is invalid")
    return document


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise _inconsistent("Structure persistence time has no timezone")
    return parsed


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


def _inconsistent(message: str) -> DomainError:
    return DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, message)


__all__ = ["SqliteStructureKnowledgeRepository"]
