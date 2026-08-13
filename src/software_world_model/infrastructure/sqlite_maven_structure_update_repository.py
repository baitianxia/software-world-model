"""Durable Application authority for manual Maven Structure updates."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import json
import sqlite3
from typing import Mapping, Protocol

from software_world_model.application_services.maven_structure_update import (
    MavenStructureTargetAuthority,
    MavenStructureUpdateAttempt,
    MavenStructureUpdateAuthorityResult,
    MavenStructureUpdateRequest,
    MavenStructureUpdateState,
    StructureReplacementDeletions,
)
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
from software_world_model.knowledge_engine.structure_publication import (
    StructurePublicationReceipt,
    StructureSnapshot,
)
from software_world_model.source_integration import (
    ArtifactUseConfirmation,
    ArtifactUsePurpose,
)

from .sqlite_database import SqliteDatabase


class StructurePublicationAuthorityReader(Protocol):
    """Knowledge-owned immutable receipt/snapshot lookup used at Result sealing."""

    def get_publication(
        self, publication_id: StableId
    ) -> StructurePublicationReceipt: ...

    def get_snapshot(self, snapshot_id: StableId) -> StructureSnapshot: ...


class ArtifactUseAuthorityReader(Protocol):
    def get_confirmation(
        self, confirmation_id: StableId
    ) -> ArtifactUseConfirmation: ...


_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_maven_structure_targets (
    authority_id TEXT PRIMARY KEY,
    scope_id TEXT NOT NULL,
    binding_id TEXT NOT NULL,
    logical_reactor_root TEXT NOT NULL,
    canonical_system_key TEXT NOT NULL,
    established_scope_revision INTEGER NOT NULL CHECK (established_scope_revision >= 1),
    established_binding_revision INTEGER NOT NULL CHECK (established_binding_revision >= 1),
    established_at TEXT NOT NULL,
    authority_digest TEXT NOT NULL,
    UNIQUE (scope_id, binding_id, logical_reactor_root)
);

CREATE TABLE IF NOT EXISTS app_maven_structure_update_attempts (
    attempt_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    current_state TEXT NOT NULL,
    objective_id TEXT NOT NULL,
    objective_digest TEXT NOT NULL,
    target_id TEXT NOT NULL,
    target_digest TEXT NOT NULL,
    target_resolution_receipt_id TEXT NOT NULL,
    target_resolution_receipt_digest TEXT NOT NULL,
    requirement_binding_digest TEXT CHECK (requirement_binding_digest IS NULL),
    scope_id TEXT NOT NULL,
    scope_revision INTEGER NOT NULL CHECK (scope_revision >= 1),
    source_id TEXT NOT NULL,
    source_revision INTEGER NOT NULL CHECK (source_revision >= 1),
    binding_id TEXT NOT NULL,
    binding_revision INTEGER NOT NULL CHECK (binding_revision >= 1),
    repository_revision TEXT NOT NULL,
    logical_reactor_root TEXT NOT NULL,
    canonical_system_key TEXT NOT NULL,
    expected_current_snapshot_id TEXT,
    target_authority_id TEXT,
    created_at TEXT NOT NULL,
    revised_at TEXT NOT NULL,
    FOREIGN KEY (target_authority_id)
        REFERENCES app_maven_structure_targets(authority_id)
);

CREATE TABLE IF NOT EXISTS app_maven_structure_update_progress (
    attempt_id TEXT PRIMARY KEY,
    source_collection_digest TEXT NOT NULL,
    source_operation_ids_json TEXT NOT NULL,
    build_report_digest TEXT NOT NULL,
    application_acceptance_ref TEXT NOT NULL,
    application_acceptance_digest TEXT NOT NULL,
    admission_id TEXT,
    admission_digest TEXT,
    artifact_read_package_id TEXT,
    artifact_read_package_digest TEXT,
    artifact_use_confirmation_id TEXT,
    artifact_use_confirmation_digest TEXT,
    recorded_at TEXT NOT NULL,
    FOREIGN KEY (attempt_id)
        REFERENCES app_maven_structure_update_attempts(attempt_id)
);

CREATE TABLE IF NOT EXISTS app_maven_structure_update_results (
    result_id TEXT PRIMARY KEY,
    attempt_id TEXT NOT NULL UNIQUE,
    request_digest TEXT NOT NULL,
    state TEXT NOT NULL,
    objective_id TEXT NOT NULL,
    objective_digest TEXT NOT NULL,
    target_id TEXT NOT NULL,
    target_digest TEXT NOT NULL,
    target_resolution_receipt_id TEXT NOT NULL,
    target_resolution_receipt_digest TEXT NOT NULL,
    requirement_binding_digest TEXT CHECK (requirement_binding_digest IS NULL),
    scope_id TEXT NOT NULL,
    scope_revision INTEGER NOT NULL CHECK (scope_revision >= 1),
    source_id TEXT NOT NULL,
    source_revision INTEGER NOT NULL CHECK (source_revision >= 1),
    binding_id TEXT NOT NULL,
    binding_revision INTEGER NOT NULL CHECK (binding_revision >= 1),
    repository_revision TEXT NOT NULL,
    logical_reactor_root TEXT NOT NULL,
    canonical_system_key TEXT NOT NULL,
    expected_current_snapshot_id TEXT,
    target_authority_id TEXT,
    target_authority_digest TEXT,
    source_collection_digest TEXT,
    source_operation_ids_json TEXT NOT NULL,
    build_report_digest TEXT,
    admission_id TEXT,
    admission_digest TEXT,
    application_acceptance_ref TEXT,
    application_acceptance_digest TEXT,
    artifact_read_package_id TEXT,
    artifact_read_package_digest TEXT,
    artifact_use_confirmation_id TEXT,
    artifact_use_confirmation_digest TEXT,
    publication_id TEXT,
    publication_digest TEXT,
    published_snapshot_id TEXT,
    previous_snapshot_id TEXT,
    previous_snapshot_manifest_digest TEXT,
    replacement_deletions_digest TEXT,
    failure_code TEXT,
    failure_message TEXT,
    failure_details_json TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    result_digest TEXT NOT NULL,
    FOREIGN KEY (attempt_id)
        REFERENCES app_maven_structure_update_attempts(attempt_id),
    FOREIGN KEY (target_authority_id)
        REFERENCES app_maven_structure_targets(authority_id)
);
"""


class SqliteMavenStructureUpdateRepository:
    """SQLite implementation with idempotent terminal Result recovery."""

    def __init__(
        self,
        database: SqliteDatabase,
        publication_authority: StructurePublicationAuthorityReader,
        artifact_use_authority: ArtifactUseAuthorityReader,
        *,
        id_generator: IdGenerator | None = None,
    ) -> None:
        self._database = database
        self._publication_authority = publication_authority
        self._artifact_use_authority = artifact_use_authority
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def begin(
        self,
        *,
        request: MavenStructureUpdateRequest,
        occurred_at: datetime,
    ) -> tuple[MavenStructureUpdateAttempt, MavenStructureUpdateAuthorityResult | None]:
        _require_time(occurred_at)
        with self._database.transaction() as connection:
            row = connection.execute(
                """SELECT * FROM app_maven_structure_update_attempts
                   WHERE idempotency_key = ?""",
                (request.idempotency_key.value,),
            ).fetchone()
            if row is not None:
                if row["request_digest"] != request.digest.value:
                    raise DomainError(
                        ErrorCode.IDEMPOTENCY_MISMATCH,
                        "Maven Structure update idempotency key has a different request",
                    )
                result_row = connection.execute(
                    """SELECT * FROM app_maven_structure_update_results
                       WHERE attempt_id = ?""",
                    (row["attempt_id"],),
                ).fetchone()
                return _attempt(row), _result(result_row) if result_row else None

            attempt_id = self._ids.new("maven_update")
            timestamp = _time(occurred_at)
            connection.execute(
                """INSERT INTO app_maven_structure_update_attempts (
                       attempt_id, idempotency_key, request_digest, current_state,
                       objective_id, objective_digest, target_id, target_digest,
                       target_resolution_receipt_id,
                       target_resolution_receipt_digest,
                       requirement_binding_digest, scope_id, scope_revision,
                       source_id, source_revision, binding_id, binding_revision,
                       repository_revision, logical_reactor_root,
                       canonical_system_key, expected_current_snapshot_id,
                       target_authority_id, created_at, revised_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)""",
                (
                    attempt_id.value,
                    request.idempotency_key.value,
                    request.digest.value,
                    MavenStructureUpdateState.PREPARING.value,
                    request.objective.objective_id,
                    request.objective.digest.value,
                    request.target.target_id.value,
                    request.target.digest.value,
                    request.target.resolution_receipt_id.value,
                    request.target.resolution_receipt_digest.value,
                    request.scope_id.value,
                    request.scope_revision.value,
                    request.source_id.value,
                    request.source_revision.value,
                    request.binding_id.value,
                    request.binding_revision.value,
                    request.repository_revision,
                    request.logical_reactor_root,
                    request.canonical_system_key,
                    (
                        request.expected_current_snapshot_id.value
                        if request.expected_current_snapshot_id is not None
                        else None
                    ),
                    timestamp,
                    timestamp,
                ),
            )
            created = connection.execute(
                """SELECT * FROM app_maven_structure_update_attempts
                   WHERE attempt_id = ?""",
                (attempt_id.value,),
            ).fetchone()
            return _attempt(created), None

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
    ) -> MavenStructureTargetAuthority:
        _require_time(occurred_at)
        with self._database.transaction() as connection:
            attempt = _attempt_row(connection, attempt_id)
            expected = (
                attempt["scope_id"],
                int(attempt["scope_revision"]),
                attempt["binding_id"],
                int(attempt["binding_revision"]),
                attempt["logical_reactor_root"],
                attempt["canonical_system_key"],
            )
            actual = (
                scope_id.value,
                scope_revision.value,
                binding_id.value,
                binding_revision.value,
                logical_reactor_root,
                canonical_system_key,
            )
            if actual != expected:
                raise _inconsistent(
                    "target authority does not match the sealed Maven update request",
                    "TARGET_AUTHORITY_REQUEST_MISMATCH",
                )

            row = connection.execute(
                """SELECT * FROM app_maven_structure_targets
                   WHERE scope_id = ? AND binding_id = ?
                     AND logical_reactor_root = ?""",
                (scope_id.value, binding_id.value, logical_reactor_root),
            ).fetchone()
            if row is None:
                authority_id = self._ids.new("maven_target_authority")
                digest = _target_authority_digest(
                    authority_id=authority_id,
                    scope_id=scope_id,
                    binding_id=binding_id,
                    logical_reactor_root=logical_reactor_root,
                    canonical_system_key=canonical_system_key,
                    established_scope_revision=scope_revision,
                    established_binding_revision=binding_revision,
                    established_at=occurred_at,
                )
                connection.execute(
                    """INSERT INTO app_maven_structure_targets
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        authority_id.value,
                        scope_id.value,
                        binding_id.value,
                        logical_reactor_root,
                        canonical_system_key,
                        scope_revision.value,
                        binding_revision.value,
                        _time(occurred_at),
                        digest.value,
                    ),
                )
                row = connection.execute(
                    """SELECT * FROM app_maven_structure_targets
                       WHERE authority_id = ?""",
                    (authority_id.value,),
                ).fetchone()
            elif row["canonical_system_key"] != canonical_system_key:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "canonical Maven system identity cannot drift for a Scope/Binding/root",
                    {
                        "reason_code": "CANONICAL_SYSTEM_KEY_DRIFT",
                        "scope_id": scope_id.value,
                        "binding_id": binding_id.value,
                        "logical_reactor_root": logical_reactor_root,
                    },
                )

            authority = _target_authority(row)
            linked_id = attempt["target_authority_id"]
            if linked_id is not None and linked_id != authority.authority_id.value:
                raise _inconsistent(
                    "Maven update Attempt is linked to another target authority",
                    "TARGET_AUTHORITY_LINK_DRIFT",
                )
            connection.execute(
                """UPDATE app_maven_structure_update_attempts
                   SET target_authority_id = ?, revised_at = ?
                   WHERE attempt_id = ?""",
                (authority.authority_id.value, _time(occurred_at), attempt_id.value),
            )
            return authority

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
    ) -> MavenStructureUpdateAttempt:
        _require_time(occurred_at)
        _require_text(application_acceptance_ref, "Application acceptance ref")
        with self._database.transaction() as connection:
            attempt = _attempt_row(connection, attempt_id)
            if attempt["target_authority_id"] is None:
                raise _inconsistent(
                    "Maven update cannot enter Admission without target authority",
                    "TARGET_AUTHORITY_MISSING",
                )
            existing = connection.execute(
                """SELECT * FROM app_maven_structure_update_progress
                   WHERE attempt_id = ?""",
                (attempt_id.value,),
            ).fetchone()
            expected = (
                source_collection_digest.value,
                _json([item.value for item in source_operation_ids]),
                build_report_digest.value,
                application_acceptance_ref,
                application_acceptance_digest.value,
            )
            if existing is None:
                if attempt["current_state"] not in {
                    MavenStructureUpdateState.PREPARING.value,
                    MavenStructureUpdateState.ADMITTING.value,
                }:
                    raise _inconsistent(
                        "terminal Maven update cannot create new Admission progress",
                        "UPDATE_ALREADY_TERMINAL",
                    )
                connection.execute(
                    """INSERT INTO app_maven_structure_update_progress (
                           attempt_id, source_collection_digest,
                           source_operation_ids_json, build_report_digest,
                           application_acceptance_ref,
                           application_acceptance_digest, admission_id,
                           admission_digest, artifact_read_package_id,
                           artifact_read_package_digest,
                           artifact_use_confirmation_id,
                           artifact_use_confirmation_digest, recorded_at
                       ) VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL,
                                 NULL, NULL, ?)""",
                    (attempt_id.value, *expected, _time(occurred_at)),
                )
            else:
                actual = (
                    existing["source_collection_digest"],
                    existing["source_operation_ids_json"],
                    existing["build_report_digest"],
                    existing["application_acceptance_ref"],
                    existing["application_acceptance_digest"],
                )
                if actual != expected:
                    raise _inconsistent(
                        "recovered Maven update progress differs from its sealed closure",
                        "UPDATE_PROGRESS_DRIFT",
                    )
            if attempt["current_state"] in {
                MavenStructureUpdateState.PREPARING.value,
                MavenStructureUpdateState.ADMITTING.value,
            }:
                connection.execute(
                    """UPDATE app_maven_structure_update_attempts
                       SET current_state = ?, revised_at = ? WHERE attempt_id = ?""",
                    (
                        MavenStructureUpdateState.ADMITTING.value,
                        _time(occurred_at),
                        attempt_id.value,
                    ),
                )
            return _attempt(_attempt_row(connection, attempt_id))

    def mark_admitted(
        self,
        *,
        attempt_id: StableId,
        admission_id: StableId,
        admission_digest: Digest,
        occurred_at: datetime,
    ) -> MavenStructureUpdateAttempt:
        _require_time(occurred_at)
        with self._database.transaction() as connection:
            attempt = _attempt_row(connection, attempt_id)
            progress = connection.execute(
                """SELECT * FROM app_maven_structure_update_progress
                   WHERE attempt_id = ?""",
                (attempt_id.value,),
            ).fetchone()
            if progress is None:
                raise _inconsistent(
                    "Maven update cannot record Admission before its candidate closure",
                    "UPDATE_PROGRESS_MISSING",
                )
            if progress["admission_id"] is not None:
                if (
                    progress["admission_id"] != admission_id.value
                    or progress["admission_digest"] != admission_digest.value
                ):
                    raise _inconsistent(
                        "recovered Maven Admission differs from its sealed Result",
                        "UPDATE_ADMISSION_DRIFT",
                    )
                return _attempt(attempt)
            if attempt["current_state"] is not None and attempt[
                "current_state"
            ] != MavenStructureUpdateState.ADMITTING.value:
                raise _inconsistent(
                    "terminal Maven update cannot acquire a new Admission",
                    "UPDATE_ALREADY_TERMINAL",
                )
            connection.execute(
                """UPDATE app_maven_structure_update_progress
                   SET admission_id = ?, admission_digest = ?, recorded_at = ?
                   WHERE attempt_id = ?""",
                (
                    admission_id.value,
                    admission_digest.value,
                    _time(occurred_at),
                    attempt_id.value,
                ),
            )
            connection.execute(
                """UPDATE app_maven_structure_update_attempts
                   SET revised_at = ? WHERE attempt_id = ?""",
                (_time(occurred_at), attempt_id.value),
            )
            return _attempt(_attempt_row(connection, attempt_id))

    def mark_artifact_use_confirmed(
        self,
        *,
        attempt_id: StableId,
        confirmation: ArtifactUseConfirmation,
        occurred_at: datetime,
    ) -> MavenStructureUpdateAttempt:
        _require_time(occurred_at)
        if not isinstance(confirmation, ArtifactUseConfirmation):
            raise _inconsistent(
                "Maven Artifact use requires a typed Confirmation",
                "ARTIFACT_USE_CONFIRMATION_REQUIRED",
            )
        persisted = self._artifact_use_authority.get_confirmation(
            confirmation.confirmation_id
        )
        if persisted != confirmation:
            raise _inconsistent(
                "Artifact use Confirmation differs from Source owner authority",
                "ARTIFACT_USE_CONFIRMATION_NOT_PERSISTED",
            )
        with self._database.transaction() as connection:
            attempt = _attempt_row(connection, attempt_id)
            progress = connection.execute(
                """SELECT * FROM app_maven_structure_update_progress
                   WHERE attempt_id = ?""",
                (attempt_id.value,),
            ).fetchone()
            if progress is None:
                raise _inconsistent(
                    "Artifact use cannot be recorded before its candidate closure",
                    "UPDATE_PROGRESS_MISSING",
                )
            if (
                confirmation.purpose
                not in {
                    ArtifactUsePurpose.MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE,
                    ArtifactUsePurpose.JAVA_STATIC_CALL_EVIDENCE_PERSISTENCE,
                }
                or confirmation.downstream_request_ref != attempt_id.value
                or confirmation.downstream_request_digest
                != Digest(attempt["request_digest"])
            ):
                raise _inconsistent(
                    "Artifact use Confirmation belongs to another Maven request",
                    "ARTIFACT_USE_REQUEST_DRIFT",
                )
            expected = (
                confirmation.package_id.value,
                confirmation.package_digest.value,
                confirmation.confirmation_id.value,
                confirmation.digest.value,
            )
            actual = (
                progress["artifact_read_package_id"],
                progress["artifact_read_package_digest"],
                progress["artifact_use_confirmation_id"],
                progress["artifact_use_confirmation_digest"],
            )
            if any(item is not None for item in actual):
                if actual != expected:
                    raise _inconsistent(
                        "Maven Artifact use Confirmation cannot drift",
                        "ARTIFACT_USE_CONFIRMATION_DRIFT",
                    )
                return _attempt(attempt)
            if attempt["current_state"] != MavenStructureUpdateState.ADMITTING.value:
                raise _inconsistent(
                    "terminal Maven update cannot acquire Artifact use authority",
                    "UPDATE_ALREADY_TERMINAL",
                )
            connection.execute(
                """UPDATE app_maven_structure_update_progress
                   SET artifact_read_package_id = ?,
                       artifact_read_package_digest = ?,
                       artifact_use_confirmation_id = ?,
                       artifact_use_confirmation_digest = ?, recorded_at = ?
                   WHERE attempt_id = ?""",
                (*expected, _time(occurred_at), attempt_id.value),
            )
            connection.execute(
                """UPDATE app_maven_structure_update_attempts
                   SET revised_at = ? WHERE attempt_id = ?""",
                (_time(occurred_at), attempt_id.value),
            )
            return _attempt(_attempt_row(connection, attempt_id))

    def finish_published(
        self,
        *,
        attempt_id: StableId,
        publication_receipt: StructurePublicationReceipt,
        occurred_at: datetime,
    ) -> MavenStructureUpdateAuthorityResult:
        _require_time(occurred_at)
        if not isinstance(publication_receipt, StructurePublicationReceipt):
            raise _inconsistent(
                "published Maven update requires a typed Structure Publication Receipt",
                "PUBLICATION_RECEIPT_REQUIRED",
            )
        persisted_receipt = self._publication_authority.get_publication(
            publication_receipt.publication_id
        )
        if persisted_receipt != publication_receipt:
            raise _inconsistent(
                "returned Structure Publication Receipt differs from owner authority",
                "PUBLICATION_RECEIPT_NOT_PERSISTED",
            )
        snapshot = persisted_receipt.snapshot
        previous_snapshot = (
            self._publication_authority.get_snapshot(snapshot.previous_snapshot_id)
            if snapshot.previous_snapshot_id is not None
            else None
        )
        if previous_snapshot is not None and (
            previous_snapshot.scope_id != snapshot.scope_id
            or previous_snapshot.snapshot_id != snapshot.previous_snapshot_id
        ):
            raise _inconsistent(
                "published Structure Snapshot predecessor is not exact",
                "PUBLICATION_PREDECESSOR_MISMATCH",
            )
        deletions = StructureReplacementDeletions.between(
            previous_snapshot.members if previous_snapshot is not None else (),
            snapshot.members,
        )
        admission_id = persisted_receipt.admission_id
        admission_digest = persisted_receipt.admission_digest
        publication_id = persisted_receipt.publication_id
        publication_digest = persisted_receipt.digest
        published_snapshot_id = snapshot.snapshot_id
        previous_snapshot_id = snapshot.previous_snapshot_id
        previous_snapshot_manifest_digest = (
            previous_snapshot.manifest_digest
            if previous_snapshot is not None
            else None
        )
        replacement_deletions_digest = deletions.digest
        with self._database.read() as connection:
            authority_attempt = _attempt_row(connection, attempt_id)
            authority_progress = connection.execute(
                """SELECT * FROM app_maven_structure_update_progress
                   WHERE attempt_id = ?""",
                (attempt_id.value,),
            ).fetchone()
        if (
            authority_progress is None
            or authority_progress["artifact_use_confirmation_id"] is None
            or authority_progress["artifact_use_confirmation_digest"] is None
            or authority_progress["artifact_read_package_id"] is None
            or authority_progress["artifact_read_package_digest"] is None
        ):
            raise _inconsistent(
                "published Maven update has no Artifact use Confirmation",
                "ARTIFACT_USE_CONFIRMATION_MISSING",
            )
        persisted_artifact_use = self._artifact_use_authority.get_confirmation(
            StableId(authority_progress["artifact_use_confirmation_id"])
        )
        if (
            persisted_artifact_use.digest.value
            != authority_progress["artifact_use_confirmation_digest"]
            or persisted_artifact_use.package_id.value
            != authority_progress["artifact_read_package_id"]
            or persisted_artifact_use.package_digest.value
            != authority_progress["artifact_read_package_digest"]
            or persisted_artifact_use.purpose
            not in {
                ArtifactUsePurpose.MAVEN_STRUCTURE_EVIDENCE_PERSISTENCE,
                ArtifactUsePurpose.JAVA_STATIC_CALL_EVIDENCE_PERSISTENCE,
            }
            or persisted_artifact_use.downstream_request_ref != attempt_id.value
            or persisted_artifact_use.downstream_request_digest
            != Digest(authority_attempt["request_digest"])
        ):
            raise _inconsistent(
                "Artifact use Confirmation differs from sealed Maven progress",
                "ARTIFACT_USE_CONFIRMATION_DRIFT",
            )
        with self._database.transaction() as connection:
            attempt = _attempt_row(connection, attempt_id)
            progress = connection.execute(
                """SELECT * FROM app_maven_structure_update_progress
                   WHERE attempt_id = ?""",
                (attempt_id.value,),
            ).fetchone()
            if progress is None:
                raise _inconsistent(
                    "published Maven update has no sealed Admission progress",
                    "UPDATE_PROGRESS_MISSING",
                )
            if (
                progress["artifact_use_confirmation_id"]
                != persisted_artifact_use.confirmation_id.value
                or progress["artifact_use_confirmation_digest"]
                != persisted_artifact_use.digest.value
                or progress["artifact_read_package_id"]
                != persisted_artifact_use.package_id.value
                or progress["artifact_read_package_digest"]
                != persisted_artifact_use.package_digest.value
            ):
                raise _inconsistent(
                    "Artifact use progress changed during Publication finalization",
                    "ARTIFACT_USE_CONFIRMATION_DRIFT",
                )
            if progress["admission_id"] is None or progress["admission_digest"] is None:
                raise _inconsistent(
                    "published Maven update has no persisted Admission",
                    "UPDATE_ADMISSION_MISSING",
                )
            if (
                progress["admission_id"] != admission_id.value
                or progress["admission_digest"] != admission_digest.value
            ):
                raise _inconsistent(
                    "publication Admission differs from the sealed Maven update Admission",
                    "UPDATE_ADMISSION_DRIFT",
                )
            if (
                progress["application_acceptance_digest"]
                != persisted_receipt.application_acceptance_digest.value
            ):
                raise _inconsistent(
                    "publication Application PASS differs from sealed Maven progress",
                    "UPDATE_APPLICATION_ACCEPTANCE_DRIFT",
                )
            expected_previous = attempt["expected_current_snapshot_id"]
            if expected_previous != (
                previous_snapshot_id.value
                if previous_snapshot_id is not None
                else None
            ):
                raise _inconsistent(
                    "published predecessor differs from sealed expected CURRENT",
                    "UPDATE_PREVIOUS_SNAPSHOT_DRIFT",
                )
            if attempt["scope_id"] != snapshot.scope_id.value:
                raise _inconsistent(
                    "published Snapshot belongs to another Scope",
                    "UPDATE_PUBLICATION_SCOPE_DRIFT",
                )
            authority = _linked_target_authority(connection, attempt)
            existing = _result_row(connection, attempt_id)
            if existing is not None:
                result = _result(existing)
                if result.state is MavenStructureUpdateState.PUBLISHED:
                    _require_same_published_result(
                        result,
                        admission_id=admission_id,
                        admission_digest=admission_digest,
                        publication_id=publication_id,
                        publication_digest=publication_digest,
                        published_snapshot_id=published_snapshot_id,
                        previous_snapshot_id=previous_snapshot_id,
                        previous_snapshot_manifest_digest=(
                            previous_snapshot_manifest_digest
                        ),
                        replacement_deletions_digest=(
                            replacement_deletions_digest
                        ),
                    )
                    return result
                if result.state is not MavenStructureUpdateState.OUTCOME_PENDING:
                    raise _inconsistent(
                        "only an OUTCOME_PENDING Maven Result can be reconciled",
                        "UPDATE_RESULT_NOT_RECOVERABLE",
                    )
                recovered = replace(
                    result,
                    state=MavenStructureUpdateState.PUBLISHED,
                    admission_id=admission_id,
                    admission_digest=admission_digest,
                    publication_id=publication_id,
                    publication_digest=publication_digest,
                    published_snapshot_id=published_snapshot_id,
                    previous_snapshot_id=previous_snapshot_id,
                    previous_snapshot_manifest_digest=(
                        previous_snapshot_manifest_digest
                    ),
                    replacement_deletions_digest=replacement_deletions_digest,
                    failure_code=None,
                    failure_message=None,
                    failure_details=(),
                    completed_at=occurred_at,
                )
                recovered = replace(
                    recovered,
                    digest=_authority_result_digest(recovered),
                )
                connection.execute(
                    """UPDATE app_maven_structure_update_results
                       SET state = ?, admission_id = ?, admission_digest = ?,
                           publication_id = ?, publication_digest = ?,
                           published_snapshot_id = ?, previous_snapshot_id = ?,
                           previous_snapshot_manifest_digest = ?,
                           replacement_deletions_digest = ?, failure_code = NULL,
                           failure_message = NULL, failure_details_json = ?,
                           completed_at = ?, result_digest = ?
                       WHERE attempt_id = ? AND state = ?""",
                    (
                        recovered.state.value,
                        recovered.admission_id.value,
                        recovered.admission_digest.value,
                        recovered.publication_id.value,
                        recovered.publication_digest.value,
                        recovered.published_snapshot_id.value,
                        (
                            recovered.previous_snapshot_id.value
                            if recovered.previous_snapshot_id is not None
                            else None
                        ),
                        (
                            recovered.previous_snapshot_manifest_digest.value
                            if recovered.previous_snapshot_manifest_digest
                            is not None
                            else None
                        ),
                        recovered.replacement_deletions_digest.value,
                        _json({}),
                        _time(recovered.completed_at),
                        recovered.digest.value,
                        attempt_id.value,
                        MavenStructureUpdateState.OUTCOME_PENDING.value,
                    ),
                )
                _set_attempt_state(
                    connection,
                    attempt_id,
                    MavenStructureUpdateState.PUBLISHED,
                    occurred_at,
                )
                recovered_row = _result_row(connection, attempt_id)
                if recovered_row is None:  # pragma: no cover - transaction guard
                    raise _inconsistent(
                        "recovered Maven Result disappeared",
                        "UPDATE_RESULT_MISSING",
                    )
                persisted_recovered = _result(recovered_row)
                if persisted_recovered != recovered:
                    raise _inconsistent(
                        "recovered Maven Result differs from its durable record",
                        "UPDATE_RECOVERY_RESULT_DRIFT",
                    )
                return persisted_recovered
            if attempt["current_state"] != MavenStructureUpdateState.ADMITTING.value:
                raise _inconsistent(
                    "Maven update cannot publish from its current state",
                    "UPDATE_STATE_INVALID",
                )
            result = _create_result(
                connection=connection,
                ids=self._ids,
                attempt=attempt,
                authority=authority,
                progress=progress,
                state=MavenStructureUpdateState.PUBLISHED,
                admission_id=admission_id,
                admission_digest=admission_digest,
                publication_id=publication_id,
                publication_digest=publication_digest,
                published_snapshot_id=published_snapshot_id,
                previous_snapshot_id=previous_snapshot_id,
                previous_snapshot_manifest_digest=previous_snapshot_manifest_digest,
                replacement_deletions_digest=replacement_deletions_digest,
                failure_code=None,
                failure_message=None,
                failure_details=(),
                completed_at=occurred_at,
            )
            _set_attempt_state(
                connection,
                attempt_id,
                MavenStructureUpdateState.PUBLISHED,
                occurred_at,
            )
            return result

    def finish_failed(
        self,
        *,
        attempt_id: StableId,
        error_code: str,
        error_message: str,
        error_details: Mapping[str, str | int],
        outcome_pending: bool,
        occurred_at: datetime,
    ) -> MavenStructureUpdateAuthorityResult:
        _require_time(occurred_at)
        clean_code = _require_text(error_code, "failure code")
        clean_message = _require_text(error_message, "failure message")
        clean_details = _failure_details(error_details)
        state = (
            MavenStructureUpdateState.OUTCOME_PENDING
            if outcome_pending
            else MavenStructureUpdateState.FAILED
        )
        with self._database.transaction() as connection:
            attempt = _attempt_row(connection, attempt_id)
            existing = _result_row(connection, attempt_id)
            if existing is not None:
                result = _result(existing)
                if (
                    result.state != state
                    or result.failure_code != clean_code
                    or result.failure_message != clean_message
                    or result.failure_details != clean_details
                ):
                    raise _inconsistent(
                        "terminal Maven update Result cannot be overwritten",
                        "UPDATE_TERMINAL_RESULT_DRIFT",
                    )
                return result
            authority = (
                _linked_target_authority(connection, attempt)
                if attempt["target_authority_id"] is not None
                else None
            )
            progress = connection.execute(
                """SELECT * FROM app_maven_structure_update_progress
                   WHERE attempt_id = ?""",
                (attempt_id.value,),
            ).fetchone()
            result = _create_result(
                connection=connection,
                ids=self._ids,
                attempt=attempt,
                authority=authority,
                progress=progress,
                state=state,
                admission_id=None,
                admission_digest=None,
                publication_id=None,
                publication_digest=None,
                published_snapshot_id=None,
                previous_snapshot_id=None,
                previous_snapshot_manifest_digest=None,
                replacement_deletions_digest=None,
                failure_code=clean_code,
                failure_message=clean_message,
                failure_details=clean_details,
                completed_at=occurred_at,
            )
            _set_attempt_state(connection, attempt_id, state, occurred_at)
            return result

    def get_attempt(self, attempt_id: StableId) -> MavenStructureUpdateAttempt:
        with self._database.read() as connection:
            return _attempt(_attempt_row(connection, attempt_id))

    def get_target_authority(
        self,
        *,
        scope_id: StableId,
        binding_id: StableId,
        logical_reactor_root: str,
    ) -> MavenStructureTargetAuthority | None:
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT * FROM app_maven_structure_targets
                   WHERE scope_id = ? AND binding_id = ?
                     AND logical_reactor_root = ?""",
                (scope_id.value, binding_id.value, logical_reactor_root),
            ).fetchone()
            return _target_authority(row) if row is not None else None

    def get_result(
        self,
        *,
        idempotency_key: IdempotencyKey,
    ) -> MavenStructureUpdateAuthorityResult | None:
        with self._database.read() as connection:
            row = connection.execute(
                """SELECT result.*
                   FROM app_maven_structure_update_results AS result
                   JOIN app_maven_structure_update_attempts AS attempt
                     ON attempt.attempt_id = result.attempt_id
                   WHERE attempt.idempotency_key = ?""",
                (idempotency_key.value,),
            ).fetchone()
            return _result(row) if row is not None else None


def _create_result(
    *,
    connection: sqlite3.Connection,
    ids: IdGenerator,
    attempt: sqlite3.Row,
    authority: MavenStructureTargetAuthority | None,
    progress: sqlite3.Row | None,
    state: MavenStructureUpdateState,
    admission_id: StableId | None,
    admission_digest: Digest | None,
    publication_id: StableId | None,
    publication_digest: Digest | None,
    published_snapshot_id: StableId | None,
    previous_snapshot_id: StableId | None,
    previous_snapshot_manifest_digest: Digest | None,
    replacement_deletions_digest: Digest | None,
    failure_code: str | None,
    failure_message: str | None,
    failure_details: tuple[tuple[str, str | int], ...],
    completed_at: datetime,
) -> MavenStructureUpdateAuthorityResult:
    result_id = ids.new("maven_update_result")
    if admission_id is None and progress is not None and progress["admission_id"]:
        admission_id = StableId(progress["admission_id"])
        admission_digest = Digest(progress["admission_digest"])
    source_operation_ids = (
        tuple(json.loads(progress["source_operation_ids_json"]))
        if progress is not None
        else ()
    )
    core = {
        "result_id": result_id.value,
        "attempt_id": attempt["attempt_id"],
        "request_digest": attempt["request_digest"],
        "state": state.value,
        "objective_id": attempt["objective_id"],
        "objective_digest": attempt["objective_digest"],
        "target_id": attempt["target_id"],
        "target_digest": attempt["target_digest"],
        "target_resolution_receipt_id": attempt["target_resolution_receipt_id"],
        "target_resolution_receipt_digest": attempt[
            "target_resolution_receipt_digest"
        ],
        "requirement_binding_digest": attempt["requirement_binding_digest"],
        "scope_id": attempt["scope_id"],
        "scope_revision": int(attempt["scope_revision"]),
        "source_id": attempt["source_id"],
        "source_revision": int(attempt["source_revision"]),
        "binding_id": attempt["binding_id"],
        "binding_revision": int(attempt["binding_revision"]),
        "repository_revision": attempt["repository_revision"],
        "logical_reactor_root": attempt["logical_reactor_root"],
        "canonical_system_key": attempt["canonical_system_key"],
        "expected_current_snapshot_id": attempt["expected_current_snapshot_id"],
        "target_authority_id": authority.authority_id.value if authority else None,
        "target_authority_digest": authority.digest.value if authority else None,
        "source_collection_digest": (
            progress["source_collection_digest"] if progress is not None else None
        ),
        "source_operation_ids": source_operation_ids,
        "build_report_digest": (
            progress["build_report_digest"] if progress is not None else None
        ),
        "admission_id": admission_id.value if admission_id else None,
        "admission_digest": admission_digest.value if admission_digest else None,
        "application_acceptance_ref": (
            progress["application_acceptance_ref"] if progress is not None else None
        ),
        "application_acceptance_digest": (
            progress["application_acceptance_digest"]
            if progress is not None
            else None
        ),
        "artifact_read_package_id": (
            progress["artifact_read_package_id"] if progress is not None else None
        ),
        "artifact_read_package_digest": (
            progress["artifact_read_package_digest"]
            if progress is not None
            else None
        ),
        "artifact_use_confirmation_id": (
            progress["artifact_use_confirmation_id"]
            if progress is not None
            else None
        ),
        "artifact_use_confirmation_digest": (
            progress["artifact_use_confirmation_digest"]
            if progress is not None
            else None
        ),
        "publication_id": publication_id.value if publication_id else None,
        "publication_digest": publication_digest.value if publication_digest else None,
        "published_snapshot_id": (
            published_snapshot_id.value if published_snapshot_id else None
        ),
        "previous_snapshot_id": (
            previous_snapshot_id.value if previous_snapshot_id else None
        ),
        "previous_snapshot_manifest_digest": (
            previous_snapshot_manifest_digest.value
            if previous_snapshot_manifest_digest
            else None
        ),
        "replacement_deletions_digest": (
            replacement_deletions_digest.value
            if replacement_deletions_digest
            else None
        ),
        "failure_code": failure_code,
        "failure_message": failure_message,
        "failure_details": failure_details,
        "completed_at": completed_at,
    }
    result_digest = digest_of(["MAVEN_STRUCTURE_UPDATE_AUTHORITY_RESULT@1", core])
    connection.execute(
        """INSERT INTO app_maven_structure_update_results (
               result_id, attempt_id, request_digest, state, objective_id,
               objective_digest, target_id, target_digest,
               target_resolution_receipt_id, target_resolution_receipt_digest,
               requirement_binding_digest, scope_id, scope_revision, source_id,
               source_revision, binding_id, binding_revision, repository_revision,
               logical_reactor_root, canonical_system_key,
               expected_current_snapshot_id, target_authority_id,
               target_authority_digest, source_collection_digest,
               source_operation_ids_json, build_report_digest, admission_id,
               admission_digest, application_acceptance_ref,
               application_acceptance_digest, artifact_read_package_id,
               artifact_read_package_digest, artifact_use_confirmation_id,
               artifact_use_confirmation_digest, publication_id, publication_digest,
               published_snapshot_id, previous_snapshot_id,
               previous_snapshot_manifest_digest, replacement_deletions_digest,
               failure_code, failure_message, failure_details_json, completed_at,
               result_digest
           ) VALUES (
               ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
               ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
               ?, ?, ?, ?
           )""",
        (
            result_id.value,
            attempt["attempt_id"],
            attempt["request_digest"],
            state.value,
            attempt["objective_id"],
            attempt["objective_digest"],
            attempt["target_id"],
            attempt["target_digest"],
            attempt["target_resolution_receipt_id"],
            attempt["target_resolution_receipt_digest"],
            attempt["requirement_binding_digest"],
            attempt["scope_id"],
            int(attempt["scope_revision"]),
            attempt["source_id"],
            int(attempt["source_revision"]),
            attempt["binding_id"],
            int(attempt["binding_revision"]),
            attempt["repository_revision"],
            attempt["logical_reactor_root"],
            attempt["canonical_system_key"],
            attempt["expected_current_snapshot_id"],
            authority.authority_id.value if authority else None,
            authority.digest.value if authority else None,
            progress["source_collection_digest"] if progress is not None else None,
            _json(source_operation_ids),
            progress["build_report_digest"] if progress is not None else None,
            admission_id.value if admission_id else None,
            admission_digest.value if admission_digest else None,
            progress["application_acceptance_ref"] if progress is not None else None,
            (
                progress["application_acceptance_digest"]
                if progress is not None
                else None
            ),
            progress["artifact_read_package_id"] if progress is not None else None,
            (
                progress["artifact_read_package_digest"]
                if progress is not None
                else None
            ),
            (
                progress["artifact_use_confirmation_id"]
                if progress is not None
                else None
            ),
            (
                progress["artifact_use_confirmation_digest"]
                if progress is not None
                else None
            ),
            publication_id.value if publication_id else None,
            publication_digest.value if publication_digest else None,
            published_snapshot_id.value if published_snapshot_id else None,
            previous_snapshot_id.value if previous_snapshot_id else None,
            (
                previous_snapshot_manifest_digest.value
                if previous_snapshot_manifest_digest
                else None
            ),
            replacement_deletions_digest.value if replacement_deletions_digest else None,
            failure_code,
            failure_message,
            _json(dict(failure_details)),
            _time(completed_at),
            result_digest.value,
        ),
    )
    row = _result_row(connection, StableId(attempt["attempt_id"]))
    if row is None:  # pragma: no cover - protected by the transaction
        raise _inconsistent(
            "Maven update Result disappeared after insertion",
            "UPDATE_RESULT_MISSING",
        )
    return _result(row)


def _attempt(row: sqlite3.Row) -> MavenStructureUpdateAttempt:
    return MavenStructureUpdateAttempt(
        attempt_id=StableId(row["attempt_id"]),
        request_digest=Digest(row["request_digest"]),
        state=MavenStructureUpdateState(row["current_state"]),
        objective_id=row["objective_id"],
        objective_digest=Digest(row["objective_digest"]),
        target_id=StableId(row["target_id"]),
        target_digest=Digest(row["target_digest"]),
        target_resolution_receipt_id=StableId(
            row["target_resolution_receipt_id"]
        ),
        target_resolution_receipt_digest=Digest(
            row["target_resolution_receipt_digest"]
        ),
        requirement_binding_digest=(
            Digest(row["requirement_binding_digest"])
            if row["requirement_binding_digest"]
            else None
        ),
        scope_id=StableId(row["scope_id"]),
        scope_revision=Revision(int(row["scope_revision"])),
        source_id=StableId(row["source_id"]),
        source_revision=Revision(int(row["source_revision"])),
        binding_id=StableId(row["binding_id"]),
        binding_revision=Revision(int(row["binding_revision"])),
        repository_revision=row["repository_revision"],
        logical_reactor_root=row["logical_reactor_root"],
        canonical_system_key=row["canonical_system_key"],
        expected_current_snapshot_id=(
            StableId(row["expected_current_snapshot_id"])
            if row["expected_current_snapshot_id"]
            else None
        ),
        target_authority_id=(
            StableId(row["target_authority_id"])
            if row["target_authority_id"]
            else None
        ),
        created_at=_parse_time(row["created_at"]),
        revised_at=_parse_time(row["revised_at"]),
    )


def _target_authority(row: sqlite3.Row) -> MavenStructureTargetAuthority:
    value = MavenStructureTargetAuthority(
        authority_id=StableId(row["authority_id"]),
        scope_id=StableId(row["scope_id"]),
        binding_id=StableId(row["binding_id"]),
        logical_reactor_root=row["logical_reactor_root"],
        canonical_system_key=row["canonical_system_key"],
        established_scope_revision=Revision(int(row["established_scope_revision"])),
        established_binding_revision=Revision(
            int(row["established_binding_revision"])
        ),
        established_at=_parse_time(row["established_at"]),
        digest=Digest(row["authority_digest"]),
    )
    expected = _target_authority_digest(
        authority_id=value.authority_id,
        scope_id=value.scope_id,
        binding_id=value.binding_id,
        logical_reactor_root=value.logical_reactor_root,
        canonical_system_key=value.canonical_system_key,
        established_scope_revision=value.established_scope_revision,
        established_binding_revision=value.established_binding_revision,
        established_at=value.established_at,
    )
    if expected != value.digest:
        raise _inconsistent(
            "persisted Maven target authority digest is invalid",
            "TARGET_AUTHORITY_DIGEST_MISMATCH",
        )
    return value


def _result(row: sqlite3.Row) -> MavenStructureUpdateAuthorityResult:
    value = MavenStructureUpdateAuthorityResult(
        result_id=StableId(row["result_id"]),
        attempt_id=StableId(row["attempt_id"]),
        request_digest=Digest(row["request_digest"]),
        state=MavenStructureUpdateState(row["state"]),
        objective_id=row["objective_id"],
        objective_digest=Digest(row["objective_digest"]),
        target_id=StableId(row["target_id"]),
        target_digest=Digest(row["target_digest"]),
        target_resolution_receipt_id=StableId(
            row["target_resolution_receipt_id"]
        ),
        target_resolution_receipt_digest=Digest(
            row["target_resolution_receipt_digest"]
        ),
        requirement_binding_digest=(
            Digest(row["requirement_binding_digest"])
            if row["requirement_binding_digest"]
            else None
        ),
        scope_id=StableId(row["scope_id"]),
        scope_revision=Revision(int(row["scope_revision"])),
        source_id=StableId(row["source_id"]),
        source_revision=Revision(int(row["source_revision"])),
        binding_id=StableId(row["binding_id"]),
        binding_revision=Revision(int(row["binding_revision"])),
        repository_revision=row["repository_revision"],
        logical_reactor_root=row["logical_reactor_root"],
        canonical_system_key=row["canonical_system_key"],
        expected_current_snapshot_id=(
            StableId(row["expected_current_snapshot_id"])
            if row["expected_current_snapshot_id"]
            else None
        ),
        target_authority_id=(
            StableId(row["target_authority_id"])
            if row["target_authority_id"]
            else None
        ),
        target_authority_digest=(
            Digest(row["target_authority_digest"])
            if row["target_authority_digest"]
            else None
        ),
        source_collection_digest=(
            Digest(row["source_collection_digest"])
            if row["source_collection_digest"]
            else None
        ),
        source_operation_ids=tuple(
            StableId(item) for item in json.loads(row["source_operation_ids_json"])
        ),
        build_report_digest=(
            Digest(row["build_report_digest"])
            if row["build_report_digest"]
            else None
        ),
        admission_id=StableId(row["admission_id"]) if row["admission_id"] else None,
        admission_digest=(
            Digest(row["admission_digest"]) if row["admission_digest"] else None
        ),
        application_acceptance_ref=row["application_acceptance_ref"],
        application_acceptance_digest=(
            Digest(row["application_acceptance_digest"])
            if row["application_acceptance_digest"]
            else None
        ),
        artifact_read_package_id=(
            StableId(row["artifact_read_package_id"])
            if row["artifact_read_package_id"]
            else None
        ),
        artifact_read_package_digest=(
            Digest(row["artifact_read_package_digest"])
            if row["artifact_read_package_digest"]
            else None
        ),
        artifact_use_confirmation_id=(
            StableId(row["artifact_use_confirmation_id"])
            if row["artifact_use_confirmation_id"]
            else None
        ),
        artifact_use_confirmation_digest=(
            Digest(row["artifact_use_confirmation_digest"])
            if row["artifact_use_confirmation_digest"]
            else None
        ),
        publication_id=(
            StableId(row["publication_id"]) if row["publication_id"] else None
        ),
        publication_digest=(
            Digest(row["publication_digest"])
            if row["publication_digest"]
            else None
        ),
        published_snapshot_id=(
            StableId(row["published_snapshot_id"])
            if row["published_snapshot_id"]
            else None
        ),
        previous_snapshot_id=(
            StableId(row["previous_snapshot_id"])
            if row["previous_snapshot_id"]
            else None
        ),
        previous_snapshot_manifest_digest=(
            Digest(row["previous_snapshot_manifest_digest"])
            if row["previous_snapshot_manifest_digest"]
            else None
        ),
        replacement_deletions_digest=(
            Digest(row["replacement_deletions_digest"])
            if row["replacement_deletions_digest"]
            else None
        ),
        failure_code=row["failure_code"],
        failure_message=row["failure_message"],
        failure_details=tuple(sorted(json.loads(row["failure_details_json"]).items())),
        completed_at=_parse_time(row["completed_at"]),
        digest=Digest(row["result_digest"]),
    )
    if _authority_result_digest(value) != value.digest:
        raise _inconsistent(
            "persisted Maven update Result digest is invalid",
            "UPDATE_RESULT_DIGEST_MISMATCH",
        )
    return value


def _authority_result_digest(value: MavenStructureUpdateAuthorityResult) -> Digest:
    core = {
        "result_id": value.result_id.value,
        "attempt_id": value.attempt_id.value,
        "request_digest": value.request_digest.value,
        "state": value.state.value,
        "objective_id": value.objective_id,
        "objective_digest": value.objective_digest.value,
        "target_id": value.target_id.value,
        "target_digest": value.target_digest.value,
        "target_resolution_receipt_id": value.target_resolution_receipt_id.value,
        "target_resolution_receipt_digest": value.target_resolution_receipt_digest.value,
        "requirement_binding_digest": (
            value.requirement_binding_digest.value
            if value.requirement_binding_digest
            else None
        ),
        "scope_id": value.scope_id.value,
        "scope_revision": value.scope_revision.value,
        "source_id": value.source_id.value,
        "source_revision": value.source_revision.value,
        "binding_id": value.binding_id.value,
        "binding_revision": value.binding_revision.value,
        "repository_revision": value.repository_revision,
        "logical_reactor_root": value.logical_reactor_root,
        "canonical_system_key": value.canonical_system_key,
        "expected_current_snapshot_id": (
            value.expected_current_snapshot_id.value
            if value.expected_current_snapshot_id
            else None
        ),
        "target_authority_id": (
            value.target_authority_id.value if value.target_authority_id else None
        ),
        "target_authority_digest": (
            value.target_authority_digest.value
            if value.target_authority_digest
            else None
        ),
        "source_collection_digest": (
            value.source_collection_digest.value
            if value.source_collection_digest
            else None
        ),
        "source_operation_ids": tuple(
            item.value for item in value.source_operation_ids
        ),
        "build_report_digest": (
            value.build_report_digest.value if value.build_report_digest else None
        ),
        "admission_id": value.admission_id.value if value.admission_id else None,
        "admission_digest": (
            value.admission_digest.value if value.admission_digest else None
        ),
        "application_acceptance_ref": value.application_acceptance_ref,
        "application_acceptance_digest": (
            value.application_acceptance_digest.value
            if value.application_acceptance_digest
            else None
        ),
        "artifact_read_package_id": (
            value.artifact_read_package_id.value
            if value.artifact_read_package_id
            else None
        ),
        "artifact_read_package_digest": (
            value.artifact_read_package_digest.value
            if value.artifact_read_package_digest
            else None
        ),
        "artifact_use_confirmation_id": (
            value.artifact_use_confirmation_id.value
            if value.artifact_use_confirmation_id
            else None
        ),
        "artifact_use_confirmation_digest": (
            value.artifact_use_confirmation_digest.value
            if value.artifact_use_confirmation_digest
            else None
        ),
        "publication_id": (
            value.publication_id.value if value.publication_id else None
        ),
        "publication_digest": (
            value.publication_digest.value if value.publication_digest else None
        ),
        "published_snapshot_id": (
            value.published_snapshot_id.value
            if value.published_snapshot_id
            else None
        ),
        "previous_snapshot_id": (
            value.previous_snapshot_id.value if value.previous_snapshot_id else None
        ),
        "previous_snapshot_manifest_digest": (
            value.previous_snapshot_manifest_digest.value
            if value.previous_snapshot_manifest_digest
            else None
        ),
        "replacement_deletions_digest": (
            value.replacement_deletions_digest.value
            if value.replacement_deletions_digest
            else None
        ),
        "failure_code": value.failure_code,
        "failure_message": value.failure_message,
        "failure_details": value.failure_details,
        "completed_at": value.completed_at,
    }
    return digest_of(["MAVEN_STRUCTURE_UPDATE_AUTHORITY_RESULT@1", core])


def _target_authority_digest(
    *,
    authority_id: StableId,
    scope_id: StableId,
    binding_id: StableId,
    logical_reactor_root: str,
    canonical_system_key: str,
    established_scope_revision: Revision,
    established_binding_revision: Revision,
    established_at: datetime,
) -> Digest:
    return digest_of(
        [
            "MAVEN_STRUCTURE_TARGET_AUTHORITY@1",
            {
                "authority_id": authority_id.value,
                "scope_id": scope_id.value,
                "binding_id": binding_id.value,
                "logical_reactor_root": logical_reactor_root,
                "canonical_system_key": canonical_system_key,
                "established_scope_revision": established_scope_revision.value,
                "established_binding_revision": established_binding_revision.value,
                "established_at": established_at,
            },
        ]
    )


def _require_same_published_result(
    result: MavenStructureUpdateAuthorityResult,
    *,
    admission_id: StableId | None,
    admission_digest: Digest | None,
    publication_id: StableId,
    publication_digest: Digest,
    published_snapshot_id: StableId,
    previous_snapshot_id: StableId | None,
    previous_snapshot_manifest_digest: Digest | None,
    replacement_deletions_digest: Digest,
) -> None:
    expected = (
        MavenStructureUpdateState.PUBLISHED,
        admission_id,
        admission_digest,
        publication_id,
        publication_digest,
        published_snapshot_id,
        previous_snapshot_id,
        previous_snapshot_manifest_digest,
        replacement_deletions_digest,
    )
    actual = (
        result.state,
        result.admission_id,
        result.admission_digest,
        result.publication_id,
        result.publication_digest,
        result.published_snapshot_id,
        result.previous_snapshot_id,
        result.previous_snapshot_manifest_digest,
        result.replacement_deletions_digest,
    )
    if actual != expected:
        raise _inconsistent(
            "replayed publication differs from the durable Maven update Result",
            "UPDATE_PUBLICATION_RESULT_DRIFT",
        )


def _linked_target_authority(
    connection: sqlite3.Connection,
    attempt: sqlite3.Row,
) -> MavenStructureTargetAuthority:
    authority_id = attempt["target_authority_id"]
    if authority_id is None:
        raise _inconsistent(
            "Maven update has no target authority",
            "TARGET_AUTHORITY_MISSING",
        )
    row = connection.execute(
        """SELECT * FROM app_maven_structure_targets WHERE authority_id = ?""",
        (authority_id,),
    ).fetchone()
    if row is None:
        raise _inconsistent(
            "Maven update target authority is missing",
            "TARGET_AUTHORITY_MISSING",
        )
    return _target_authority(row)


def _attempt_row(
    connection: sqlite3.Connection,
    attempt_id: StableId,
) -> sqlite3.Row:
    row = connection.execute(
        """SELECT * FROM app_maven_structure_update_attempts
           WHERE attempt_id = ?""",
        (attempt_id.value,),
    ).fetchone()
    if row is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Maven Structure update Attempt was not found",
            {"attempt_id": attempt_id.value},
        )
    return row


def _result_row(
    connection: sqlite3.Connection,
    attempt_id: StableId,
) -> sqlite3.Row | None:
    return connection.execute(
        """SELECT * FROM app_maven_structure_update_results
           WHERE attempt_id = ?""",
        (attempt_id.value,),
    ).fetchone()


def _set_attempt_state(
    connection: sqlite3.Connection,
    attempt_id: StableId,
    state: MavenStructureUpdateState,
    occurred_at: datetime,
) -> None:
    connection.execute(
        """UPDATE app_maven_structure_update_attempts
           SET current_state = ?, revised_at = ? WHERE attempt_id = ?""",
        (state.value, _time(occurred_at), attempt_id.value),
    )


def _failure_details(
    details: Mapping[str, str | int],
) -> tuple[tuple[str, str | int], ...]:
    normalized: list[tuple[str, str | int]] = []
    for key, value in details.items():
        clean_key = _require_text(key, "failure detail key")
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Maven update failure detail values must be strings or integers",
            )
        normalized.append((clean_key, value))
    return tuple(sorted(normalized))


def _require_text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def _require_time(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Maven update authority time must include a timezone",
        )


def _inconsistent(message: str, reason_code: str) -> DomainError:
    return DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        message,
        {"reason_code": reason_code},
    )


def _json(value: object) -> str:
    return canonical_json_bytes(value).decode("utf-8")


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value)


__all__ = ["SqliteMavenStructureUpdateRepository"]
