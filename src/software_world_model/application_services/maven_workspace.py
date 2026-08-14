"""Recoverable Maven Workspace management over existing owner services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import os
from pathlib import Path
import re
from typing import Callable, Protocol

from software_world_model.application_services.knowledge_use import TaskBoundary
from software_world_model.application_services.read_set_catalog import (
    ReadSetCatalog,
    ReadSetCatalogPointer,
    ReadSetCatalogService,
    ReadSetRegistration,
)
from software_world_model.application_services.structure_read_bundle import (
    StructureReadBundleReceipt,
)
from software_world_model.application_services.structure_read_session import (
    StructureReadSession,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdGenerator,
    IdempotencyKey,
    Revision,
    StableId,
    Uuid4IdGenerator,
    digest_of,
)
from software_world_model.knowledge_engine.structure import (
    JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    JAVA_STATIC_CALL_PROFILE_REF,
    MAVEN_STRUCTURE_PROFILE_REF,
)


_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class WorkspaceVersionAvailability(str, Enum):
    READ_BUNDLE_UNAVAILABLE = "READ_BUNDLE_UNAVAILABLE"
    CATALOG_UNAVAILABLE = "CATALOG_UNAVAILABLE"
    QUERYABLE = "QUERYABLE"


class WorkspaceAttemptState(str, Enum):
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    OUTCOME_PENDING = "OUTCOME_PENDING"
    READ_BUNDLE_UNAVAILABLE = "READ_BUNDLE_UNAVAILABLE"
    CATALOG_UNAVAILABLE = "CATALOG_UNAVAILABLE"
    SUCCEEDED = "SUCCEEDED"


class WorkspaceStepName(str, Enum):
    SNAPSHOT_PUBLICATION = "SNAPSHOT_PUBLICATION"
    SINGLE_READ_SET = "SINGLE_READ_SET"
    COMPARISON_READ_SET = "COMPARISON_READ_SET"
    CATALOG_PUBLICATION = "CATALOG_PUBLICATION"


class WorkspaceStepOutcome(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    OUTCOME_PENDING = "OUTCOME_PENDING"
    SKIPPED = "SKIPPED"


@dataclass(frozen=True, slots=True)
class WorkspaceConfigurationAuthority:
    scope_id: StableId
    scope_revision: Revision
    source_id: StableId
    source_revision: Revision
    binding_id: StableId
    binding_revision: Revision
    management_attempt_id: StableId
    management_result_digest: Digest

    def require_valid(self) -> None:
        if (
            self.scope_id.kind != "scope"
            or self.source_id.kind != "datasource"
            or self.binding_id.kind != "binding"
            or self.management_attempt_id.kind != "management_attempt"
        ):
            raise _invalid(
                "MAVEN_WORKSPACE_CONFIGURATION_AUTHORITY_INVALID",
                "Workspace configuration authority has an invalid owner reference",
            )


@dataclass(frozen=True, slots=True)
class MavenWorkspace:
    workspace_id: StableId
    idempotency_key: IdempotencyKey
    request_digest: Digest
    canonical_system_key: str
    display_name: str
    repository_locator: str
    root_pom: str
    scope_id: StableId
    scope_revision: Revision
    source_id: StableId
    source_revision: Revision
    binding_id: StableId
    binding_revision: Revision
    management_attempt_id: StableId
    management_result_digest: Digest
    knowledge_profile_ref: str
    created_at: datetime
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        workspace_id: StableId,
        idempotency_key: IdempotencyKey,
        canonical_system_key: str,
        display_name: str,
        repository_locator: str,
        root_pom: str,
        authority: WorkspaceConfigurationAuthority,
        created_at: datetime,
        knowledge_profile_ref: str = MAVEN_STRUCTURE_PROFILE_REF,
    ) -> "MavenWorkspace":
        authority.require_valid()
        profile_ref = _knowledge_profile(knowledge_profile_ref)
        request_core = {
            "canonical_system_key": _text(canonical_system_key, "canonical system key"),
            "display_name": _text(display_name, "display name"),
            "repository_locator": _absolute_repository(repository_locator),
            "root_pom": _relative_path(root_pom, "root POM"),
        }
        request_format = "REGISTER_MAVEN_WORKSPACE@1"
        workspace_format = "MAVEN_WORKSPACE@1"
        if profile_ref != MAVEN_STRUCTURE_PROFILE_REF:
            request_core["knowledge_profile_ref"] = profile_ref
            request_format = "REGISTER_STRUCTURE_WORKSPACE@1"
            workspace_format = "STRUCTURE_WORKSPACE@1"
        request_digest = digest_of([request_format, request_core])
        core = {
            "workspace_id": workspace_id.value,
            "idempotency_key": idempotency_key.value,
            "request_digest": request_digest.value,
            **request_core,
            "scope_id": authority.scope_id.value,
            "scope_revision": authority.scope_revision.value,
            "source_id": authority.source_id.value,
            "source_revision": authority.source_revision.value,
            "binding_id": authority.binding_id.value,
            "binding_revision": authority.binding_revision.value,
            "management_attempt_id": authority.management_attempt_id.value,
            "management_result_digest": authority.management_result_digest.value,
            "created_at": created_at,
        }
        value = cls(
            workspace_id=workspace_id,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            canonical_system_key=request_core["canonical_system_key"],
            display_name=request_core["display_name"],
            repository_locator=request_core["repository_locator"],
            root_pom=request_core["root_pom"],
            scope_id=authority.scope_id,
            scope_revision=authority.scope_revision,
            source_id=authority.source_id,
            source_revision=authority.source_revision,
            binding_id=authority.binding_id,
            binding_revision=authority.binding_revision,
            management_attempt_id=authority.management_attempt_id,
            management_result_digest=authority.management_result_digest,
            knowledge_profile_ref=profile_ref,
            created_at=created_at,
            digest=digest_of([workspace_format, core]),
        )
        value.require_valid()
        return value

    def require_valid(self) -> None:
        if self.workspace_id.kind != "maven_workspace":
            raise _invalid("MAVEN_WORKSPACE_ID_INVALID", "Workspace ID is invalid")
        authority = WorkspaceConfigurationAuthority(
            self.scope_id,
            self.scope_revision,
            self.source_id,
            self.source_revision,
            self.binding_id,
            self.binding_revision,
            self.management_attempt_id,
            self.management_result_digest,
        )
        authority.require_valid()
        profile_ref = _knowledge_profile(self.knowledge_profile_ref)
        request_core = {
            "canonical_system_key": _text(self.canonical_system_key, "canonical system key"),
            "display_name": _text(self.display_name, "display name"),
            "repository_locator": _absolute_repository(self.repository_locator),
            "root_pom": _relative_path(self.root_pom, "root POM"),
        }
        request_format = "REGISTER_MAVEN_WORKSPACE@1"
        workspace_format = "MAVEN_WORKSPACE@1"
        if profile_ref != MAVEN_STRUCTURE_PROFILE_REF:
            request_core["knowledge_profile_ref"] = profile_ref
            request_format = "REGISTER_STRUCTURE_WORKSPACE@1"
            workspace_format = "STRUCTURE_WORKSPACE@1"
        if self.request_digest != digest_of([request_format, request_core]):
            raise _invalid("MAVEN_WORKSPACE_REQUEST_DIGEST_MISMATCH", "Workspace request digest is not canonical")
        core = {
            "workspace_id": self.workspace_id.value,
            "idempotency_key": self.idempotency_key.value,
            "request_digest": self.request_digest.value,
            **request_core,
            "scope_id": self.scope_id.value,
            "scope_revision": self.scope_revision.value,
            "source_id": self.source_id.value,
            "source_revision": self.source_revision.value,
            "binding_id": self.binding_id.value,
            "binding_revision": self.binding_revision.value,
            "management_attempt_id": self.management_attempt_id.value,
            "management_result_digest": self.management_result_digest.value,
            "created_at": self.created_at,
        }
        _aware_time(self.created_at, "Workspace creation time")
        if self.digest != digest_of([workspace_format, core]):
            raise _invalid("MAVEN_WORKSPACE_DIGEST_MISMATCH", "Workspace digest is not canonical")

    @property
    def source_root(self) -> str:
        return self.root_pom


@dataclass(frozen=True, slots=True)
class MavenWorkspaceVersion:
    version_id: StableId
    workspace_id: StableId
    ordinal: int
    repository_revision: str
    snapshot_id: StableId
    snapshot_manifest_digest: Digest
    availability: WorkspaceVersionAvailability
    single_read_set_id: StableId | None
    comparison_read_set_id: StableId | None
    created_at: datetime
    revision: Revision
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        version_id: StableId,
        workspace_id: StableId,
        ordinal: int,
        repository_revision: str,
        snapshot_id: StableId,
        snapshot_manifest_digest: Digest,
        created_at: datetime,
    ) -> "MavenWorkspaceVersion":
        value = cls(
            version_id=version_id,
            workspace_id=workspace_id,
            ordinal=ordinal,
            repository_revision=repository_revision,
            snapshot_id=snapshot_id,
            snapshot_manifest_digest=snapshot_manifest_digest,
            availability=WorkspaceVersionAvailability.READ_BUNDLE_UNAVAILABLE,
            single_read_set_id=None,
            comparison_read_set_id=None,
            created_at=created_at,
            revision=Revision(1),
            digest=Digest("sha256:" + "0" * 64),
        )
        return value._with_digest()

    def transition(
        self,
        *,
        availability: WorkspaceVersionAvailability,
        single_read_set_id: StableId | None,
        comparison_read_set_id: StableId | None,
    ) -> "MavenWorkspaceVersion":
        if self.availability is WorkspaceVersionAvailability.QUERYABLE and availability is not self.availability:
            raise _invalid("MAVEN_WORKSPACE_VERSION_REGRESSION", "queryable Workspace Version cannot regress")
        if (
            self.availability is WorkspaceVersionAvailability.CATALOG_UNAVAILABLE
            and availability is WorkspaceVersionAvailability.READ_BUNDLE_UNAVAILABLE
        ):
            raise _invalid(
                "MAVEN_WORKSPACE_VERSION_REGRESSION",
                "Catalog-unavailable Workspace Version cannot regress to Bundle-unavailable",
            )
        if (
            self.single_read_set_id is not None
            and single_read_set_id != self.single_read_set_id
        ) or (
            self.comparison_read_set_id is not None
            and comparison_read_set_id != self.comparison_read_set_id
        ):
            raise _invalid(
                "MAVEN_WORKSPACE_VERSION_READ_SET_REGRESSION",
                "Workspace Version cannot remove or replace an exact Read Set",
            )
        return MavenWorkspaceVersion(
            version_id=self.version_id,
            workspace_id=self.workspace_id,
            ordinal=self.ordinal,
            repository_revision=self.repository_revision,
            snapshot_id=self.snapshot_id,
            snapshot_manifest_digest=self.snapshot_manifest_digest,
            availability=availability,
            single_read_set_id=single_read_set_id,
            comparison_read_set_id=comparison_read_set_id,
            created_at=self.created_at,
            revision=self.revision.next(),
            digest=Digest("sha256:" + "0" * 64),
        )._with_digest()

    def _with_digest(self) -> "MavenWorkspaceVersion":
        core = self._core()
        value = MavenWorkspaceVersion(
            version_id=self.version_id,
            workspace_id=self.workspace_id,
            ordinal=self.ordinal,
            repository_revision=self.repository_revision,
            snapshot_id=self.snapshot_id,
            snapshot_manifest_digest=self.snapshot_manifest_digest,
            availability=self.availability,
            single_read_set_id=self.single_read_set_id,
            comparison_read_set_id=self.comparison_read_set_id,
            created_at=self.created_at,
            revision=self.revision,
            digest=digest_of(["MAVEN_WORKSPACE_VERSION@1", core]),
        )
        value.require_valid()
        return value

    def _core(self) -> dict[str, object]:
        return {
            "version_id": self.version_id.value,
            "workspace_id": self.workspace_id.value,
            "ordinal": self.ordinal,
            "repository_revision": self.repository_revision,
            "snapshot_id": self.snapshot_id.value,
            "snapshot_manifest_digest": self.snapshot_manifest_digest.value,
            "availability": self.availability.value,
            "single_read_set_id": self.single_read_set_id.value if self.single_read_set_id else None,
            "comparison_read_set_id": self.comparison_read_set_id.value if self.comparison_read_set_id else None,
            "created_at": self.created_at,
            "revision": self.revision.value,
        }

    def require_valid(self) -> None:
        if self.version_id.kind != "workspace_version" or self.workspace_id.kind != "maven_workspace":
            raise _invalid("MAVEN_WORKSPACE_VERSION_ID_INVALID", "Workspace Version identity is invalid")
        if type(self.ordinal) is not int or self.ordinal < 1 or not _COMMIT_RE.fullmatch(self.repository_revision):
            raise _invalid("MAVEN_WORKSPACE_VERSION_REVISION_INVALID", "Workspace Version requires an ordinal and exact commit")
        if self.snapshot_id.kind != "structure_snapshot":
            raise _invalid("MAVEN_WORKSPACE_VERSION_SNAPSHOT_INVALID", "Workspace Version Snapshot ID is invalid")
        for read_set_id in (self.single_read_set_id, self.comparison_read_set_id):
            if read_set_id is not None and read_set_id.kind != "read_set":
                raise _invalid("MAVEN_WORKSPACE_VERSION_READ_SET_INVALID", "Workspace Version Read Set ID is invalid")
        if self.availability is WorkspaceVersionAvailability.CATALOG_UNAVAILABLE and (
            self.single_read_set_id is None
            or (self.ordinal > 1 and self.comparison_read_set_id is None)
        ):
            raise _invalid(
                "MAVEN_WORKSPACE_VERSION_CATALOG_INVALID",
                "Catalog-unavailable Workspace Version requires its single Read Set",
            )
        if self.availability is WorkspaceVersionAvailability.QUERYABLE and (
            self.single_read_set_id is None
            or (self.ordinal > 1 and self.comparison_read_set_id is None)
        ):
            raise _invalid(
                "MAVEN_WORKSPACE_VERSION_QUERYABLE_INVALID",
                "queryable Workspace Version requires all of its Read Sets",
            )
        _aware_time(self.created_at, "Workspace Version time")
        if self.digest != digest_of(["MAVEN_WORKSPACE_VERSION@1", self._core()]):
            raise _invalid("MAVEN_WORKSPACE_VERSION_DIGEST_MISMATCH", "Workspace Version digest is not canonical")


@dataclass(frozen=True, slots=True)
class WorkspaceStepEvent:
    event_id: StableId
    attempt_id: StableId
    sequence: int
    name: WorkspaceStepName
    outcome: WorkspaceStepOutcome
    reference_id: str | None
    reference_digest: Digest | None
    error_code: str | None
    error_message: str | None
    occurred_at: datetime
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        event_id: StableId,
        attempt_id: StableId,
        sequence: int,
        name: WorkspaceStepName,
        outcome: WorkspaceStepOutcome,
        reference_id: str | None,
        reference_digest: Digest | None,
        error_code: str | None,
        error_message: str | None,
        occurred_at: datetime,
    ) -> "WorkspaceStepEvent":
        core = {
            "event_id": event_id.value,
            "attempt_id": attempt_id.value,
            "sequence": sequence,
            "name": name.value,
            "outcome": outcome.value,
            "reference_id": reference_id,
            "reference_digest": reference_digest.value if reference_digest else None,
            "error_code": error_code,
            "error_message": error_message,
            "occurred_at": occurred_at,
        }
        value = cls(
            event_id=event_id,
            attempt_id=attempt_id,
            sequence=sequence,
            name=name,
            outcome=outcome,
            reference_id=reference_id,
            reference_digest=reference_digest,
            error_code=error_code,
            error_message=error_message,
            occurred_at=occurred_at,
            digest=digest_of(["MAVEN_WORKSPACE_STEP_EVENT@1", core]),
        )
        value.require_valid()
        return value

    def require_valid(self) -> None:
        if self.event_id.kind != "workspace_step" or self.attempt_id.kind != "workspace_attempt" or self.sequence < 1:
            raise _invalid("MAVEN_WORKSPACE_STEP_ID_INVALID", "Workspace Step Event identity is invalid")
        succeeded = self.outcome in {WorkspaceStepOutcome.SUCCEEDED, WorkspaceStepOutcome.SKIPPED}
        if succeeded and (self.error_code is not None or self.error_message is not None):
            raise _invalid("MAVEN_WORKSPACE_STEP_SHAPE_INVALID", "successful Workspace Step cannot contain an error")
        if not succeeded and (not self.error_code or not self.error_message):
            raise _invalid("MAVEN_WORKSPACE_STEP_SHAPE_INVALID", "failed/pending Workspace Step requires error details")
        if (self.reference_id is None) != (self.reference_digest is None):
            raise _invalid("MAVEN_WORKSPACE_STEP_REFERENCE_INVALID", "Workspace Step reference ID/digest must be paired")
        if self.outcome is WorkspaceStepOutcome.SUCCEEDED and self.reference_id is None:
            raise _invalid(
                "MAVEN_WORKSPACE_STEP_REFERENCE_REQUIRED",
                "successful Workspace Step requires an owner reference",
            )
        if self.outcome is WorkspaceStepOutcome.SKIPPED and self.reference_id is not None:
            raise _invalid(
                "MAVEN_WORKSPACE_STEP_SKIPPED_REFERENCE_INVALID",
                "skipped Workspace Step cannot claim an owner reference",
            )
        if not succeeded and self.reference_id is not None:
            raise _invalid(
                "MAVEN_WORKSPACE_STEP_FAILURE_REFERENCE_INVALID",
                "failed or pending Workspace Step cannot claim a success reference",
            )
        _aware_time(self.occurred_at, "Workspace Step time")
        core = {
            "event_id": self.event_id.value,
            "attempt_id": self.attempt_id.value,
            "sequence": self.sequence,
            "name": self.name.value,
            "outcome": self.outcome.value,
            "reference_id": self.reference_id,
            "reference_digest": self.reference_digest.value if self.reference_digest else None,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "occurred_at": self.occurred_at,
        }
        if self.digest != digest_of(["MAVEN_WORKSPACE_STEP_EVENT@1", core]):
            raise _invalid("MAVEN_WORKSPACE_STEP_DIGEST_MISMATCH", "Workspace Step digest is not canonical")


@dataclass(frozen=True, slots=True)
class MavenWorkspaceAttempt:
    attempt_id: StableId
    idempotency_key: IdempotencyKey
    request_digest: Digest
    workspace_id: StableId
    repository_revision: str
    expected_current_snapshot_id: StableId | None
    state: WorkspaceAttemptState
    revision: Revision
    created_at: datetime
    revised_at: datetime
    steps: tuple[WorkspaceStepEvent, ...]
    digest: Digest

    def latest_step(self, name: WorkspaceStepName) -> WorkspaceStepEvent | None:
        matches = [item for item in self.steps if item.name is name]
        return matches[-1] if matches else None

    def require_valid(self) -> None:
        if self.attempt_id.kind != "workspace_attempt" or self.workspace_id.kind != "maven_workspace":
            raise _invalid("MAVEN_WORKSPACE_ATTEMPT_ID_INVALID", "Workspace Attempt identity is invalid")
        if not _COMMIT_RE.fullmatch(self.repository_revision):
            raise _invalid("MAVEN_WORKSPACE_ATTEMPT_REVISION_INVALID", "Workspace Attempt requires an exact commit")
        if self.expected_current_snapshot_id is not None and self.expected_current_snapshot_id.kind != "structure_snapshot":
            raise _invalid("MAVEN_WORKSPACE_ATTEMPT_CURRENT_INVALID", "Workspace Attempt expected CURRENT is invalid")
        if tuple(item.sequence for item in self.steps) != tuple(range(1, len(self.steps) + 1)):
            raise _invalid("MAVEN_WORKSPACE_STEP_SEQUENCE_INVALID", "Workspace Step history is not contiguous")
        for item in self.steps:
            item.require_valid()
            if item.attempt_id != self.attempt_id:
                raise _invalid("MAVEN_WORKSPACE_STEP_ATTEMPT_MISMATCH", "Workspace Step belongs to another Attempt")
        _aware_time(self.created_at, "Workspace Attempt creation time")
        _aware_time(self.revised_at, "Workspace Attempt revision time")
        if self.revised_at < self.created_at or any(
            item.occurred_at < self.created_at
            or item.occurred_at > self.revised_at
            or (
                index > 0
                and item.occurred_at < self.steps[index - 1].occurred_at
            )
            for index, item in enumerate(self.steps)
        ):
            raise _invalid(
                "MAVEN_WORKSPACE_ATTEMPT_TIME_ORDER_INVALID",
                "Workspace Attempt and Step times are not monotonic",
            )
        core = workspace_attempt_core(self)
        if self.digest != digest_of(["MAVEN_WORKSPACE_ATTEMPT@1", core]):
            raise _invalid("MAVEN_WORKSPACE_ATTEMPT_DIGEST_MISMATCH", "Workspace Attempt digest is not canonical")


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshotMetrics:
    source_call_count: int
    source_byte_count: int
    elapsed_milliseconds: int

    def require_valid(self) -> None:
        if any(
            type(value) is not int or value < 0
            for value in (
                self.source_call_count,
                self.source_byte_count,
                self.elapsed_milliseconds,
            )
        ):
            raise _invalid(
                "MAVEN_WORKSPACE_METRICS_INVALID",
                "Workspace Snapshot metrics must be non-negative integers",
            )


@dataclass(frozen=True, slots=True)
class WorkspaceSnapshotPublication:
    snapshot_id: StableId
    snapshot_manifest_digest: Digest
    owner_result: object | None = None
    metrics: WorkspaceSnapshotMetrics | None = None


class MavenWorkspaceOperations(Protocol):
    def publish_snapshot(
        self,
        *,
        workspace: MavenWorkspace,
        repository_revision: str,
        expected_current_snapshot_id: StableId | None,
        idempotency_key: IdempotencyKey,
        correlation_ref: CorrelationRef,
    ) -> WorkspaceSnapshotPublication: ...

    def open_read_session(
        self,
        *,
        workspace: MavenWorkspace,
        snapshot_ids: tuple[StableId, ...],
        task_boundary: TaskBoundary,
        idempotency_key: IdempotencyKey,
    ) -> StructureReadSession: ...

    def build_snapshot_bundle(
        self,
        *,
        snapshot_id: StableId,
        idempotency_key: IdempotencyKey,
        destination: str,
    ) -> StructureReadBundleReceipt: ...

    def build_ordered_bundle(
        self,
        *,
        session_id: StableId,
        idempotency_key: IdempotencyKey,
        destination: str,
    ) -> StructureReadBundleReceipt: ...


class MavenWorkspaceRepository(Protocol):
    def save_workspace(self, workspace: MavenWorkspace) -> MavenWorkspace: ...
    def get_workspace(self, workspace_id: StableId) -> MavenWorkspace: ...
    def list_workspaces(self) -> tuple[MavenWorkspace, ...]: ...
    def prepare_attempt(
        self,
        *,
        attempt_id: StableId,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        workspace_id: StableId,
        repository_revision: str,
        expected_current_snapshot_id: StableId | None,
        occurred_at: datetime,
    ) -> MavenWorkspaceAttempt: ...
    def get_attempt(self, attempt_id: StableId) -> MavenWorkspaceAttempt: ...
    def find_attempt_by_idempotency_key(
        self, idempotency_key: IdempotencyKey
    ) -> MavenWorkspaceAttempt | None: ...
    def transition_attempt(
        self,
        *,
        attempt_id: StableId,
        expected_revision: Revision,
        state: WorkspaceAttemptState,
        occurred_at: datetime,
    ) -> MavenWorkspaceAttempt: ...
    def append_step(
        self,
        *,
        attempt_id: StableId,
        name: WorkspaceStepName,
        outcome: WorkspaceStepOutcome,
        reference_id: str | None,
        reference_digest: Digest | None,
        error_code: str | None,
        error_message: str | None,
        occurred_at: datetime,
    ) -> MavenWorkspaceAttempt: ...
    def save_version(self, version: MavenWorkspaceVersion, *, attempt_id: StableId) -> MavenWorkspaceVersion: ...
    def update_version(self, version: MavenWorkspaceVersion, *, expected_revision: Revision) -> MavenWorkspaceVersion: ...
    def find_version_for_attempt(self, attempt_id: StableId) -> MavenWorkspaceVersion | None: ...
    def list_versions(self, workspace_id: StableId) -> tuple[MavenWorkspaceVersion, ...]: ...


@dataclass(frozen=True, slots=True)
class MavenWorkspaceUpdateResult:
    workspace: MavenWorkspace
    attempt: MavenWorkspaceAttempt
    version: MavenWorkspaceVersion | None
    single_read_set: ReadSetRegistration | None
    comparison_read_set: ReadSetRegistration | None
    catalog: ReadSetCatalog | None
    catalog_pointer: ReadSetCatalogPointer | None
    snapshot_owner_result: object | None
    snapshot_metrics: WorkspaceSnapshotMetrics | None


class MavenWorkspaceService:
    """Compose owner calls without pretending they share one transaction."""

    def __init__(
        self,
        repository: MavenWorkspaceRepository,
        operations: MavenWorkspaceOperations,
        catalog: ReadSetCatalogService,
        *,
        id_generator: IdGenerator | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._operations = operations
        self._catalog = catalog
        self._ids = id_generator or Uuid4IdGenerator()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def register(
        self,
        *,
        idempotency_key: IdempotencyKey,
        canonical_system_key: str,
        display_name: str,
        repository_locator: str,
        root_pom: str,
        authority: WorkspaceConfigurationAuthority,
        knowledge_profile_ref: str = MAVEN_STRUCTURE_PROFILE_REF,
    ) -> MavenWorkspace:
        workspace = MavenWorkspace.create(
            workspace_id=self._ids.new("maven_workspace"),
            idempotency_key=idempotency_key,
            canonical_system_key=canonical_system_key,
            display_name=display_name,
            repository_locator=repository_locator,
            root_pom=root_pom,
            authority=authority,
            created_at=self._now(),
            knowledge_profile_ref=knowledge_profile_ref,
        )
        return self._repository.save_workspace(workspace)

    def update(
        self,
        *,
        workspace_id: StableId,
        repository_revision: str,
        idempotency_key: IdempotencyKey,
        correlation_ref: CorrelationRef,
    ) -> MavenWorkspaceUpdateResult:
        workspace = self._repository.get_workspace(workspace_id)
        replay = self._repository.find_attempt_by_idempotency_key(idempotency_key)
        if replay is None:
            versions = self._repository.list_versions(workspace_id)
            expected_current = versions[-1].snapshot_id if versions else None
        else:
            expected_current = replay.expected_current_snapshot_id
        request_core = {
            "workspace_id": workspace_id.value,
            "workspace_digest": workspace.digest.value,
            "repository_revision": _exact_commit(repository_revision),
            "expected_current_snapshot_id": (
                expected_current.value if expected_current else None
            ),
        }
        request_format = "UPDATE_MAVEN_WORKSPACE@1"
        if workspace.knowledge_profile_ref != MAVEN_STRUCTURE_PROFILE_REF:
            request_core["knowledge_profile_ref"] = workspace.knowledge_profile_ref
            request_format = "UPDATE_STRUCTURE_WORKSPACE@1"
        request_digest = digest_of([request_format, request_core])
        attempt = self._repository.prepare_attempt(
            attempt_id=self._ids.new("workspace_attempt"),
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            workspace_id=workspace_id,
            repository_revision=repository_revision,
            expected_current_snapshot_id=expected_current,
            occurred_at=self._now(),
        )
        return self._execute_reported(
            workspace, attempt, correlation_ref=correlation_ref
        )

    def resume(
        self,
        *,
        attempt_id: StableId,
        correlation_ref: CorrelationRef,
    ) -> MavenWorkspaceUpdateResult:
        attempt = self._repository.get_attempt(attempt_id)
        workspace = self._repository.get_workspace(attempt.workspace_id)
        return self._execute_reported(
            workspace, attempt, correlation_ref=correlation_ref
        )

    def get_attempt(self, attempt_id: StableId) -> MavenWorkspaceAttempt:
        return self._repository.get_attempt(attempt_id)

    def list_workspaces(self) -> tuple[MavenWorkspace, ...]:
        return self._repository.list_workspaces()

    def list_versions(self, workspace_id: StableId) -> tuple[MavenWorkspaceVersion, ...]:
        return self._repository.list_versions(workspace_id)

    def _execute_reported(
        self,
        workspace: MavenWorkspace,
        attempt: MavenWorkspaceAttempt,
        *,
        correlation_ref: CorrelationRef,
    ) -> MavenWorkspaceUpdateResult:
        try:
            return self._execute(
                workspace, attempt, correlation_ref=correlation_ref
            )
        except DomainError as error:
            current = self._repository.get_attempt(attempt.attempt_id)
            raise DomainError(
                error.code,
                error.message,
                {
                    **dict(error.details),
                    "workspace_attempt_id": current.attempt_id.value,
                    "workspace_attempt_state": current.state.value,
                    "workspace_attempt_digest": current.digest.value,
                },
            ) from error
        except Exception as error:
            current = self._repository.get_attempt(attempt.attempt_id)
            raise DomainError(
                ErrorCode.OUTCOME_PENDING,
                "Workspace Update outcome requires explicit resume and reconciliation",
                {
                    "workspace_attempt_id": current.attempt_id.value,
                    "workspace_attempt_state": current.state.value,
                    "workspace_attempt_digest": current.digest.value,
                    "cause_type": type(error).__name__,
                },
            ) from error

    def _execute(
        self,
        workspace: MavenWorkspace,
        attempt: MavenWorkspaceAttempt,
        *,
        correlation_ref: CorrelationRef,
    ) -> MavenWorkspaceUpdateResult:
        if attempt.state is WorkspaceAttemptState.SUCCEEDED:
            return self._assemble(workspace, attempt, None)
        if attempt.state is not WorkspaceAttemptState.RUNNING:
            attempt = self._repository.transition_attempt(
                attempt_id=attempt.attempt_id,
                expected_revision=attempt.revision,
                state=WorkspaceAttemptState.RUNNING,
                occurred_at=self._now(),
            )

        owner_result: object | None = None
        snapshot_metrics: WorkspaceSnapshotMetrics | None = None
        version = self._repository.find_version_for_attempt(attempt.attempt_id)
        if version is None:
            try:
                publication = self._operations.publish_snapshot(
                    workspace=workspace,
                    repository_revision=attempt.repository_revision,
                    expected_current_snapshot_id=attempt.expected_current_snapshot_id,
                    idempotency_key=self._owner_key(attempt, "snapshot"),
                    correlation_ref=correlation_ref,
                )
                owner_result = publication.owner_result
                snapshot_metrics = publication.metrics
                if snapshot_metrics is not None:
                    snapshot_metrics.require_valid()
                ordinal = len(self._repository.list_versions(workspace.workspace_id)) + 1
                version = MavenWorkspaceVersion.create(
                    version_id=self._ids.new("workspace_version"),
                    workspace_id=workspace.workspace_id,
                    ordinal=ordinal,
                    repository_revision=attempt.repository_revision,
                    snapshot_id=publication.snapshot_id,
                    snapshot_manifest_digest=publication.snapshot_manifest_digest,
                    created_at=self._now(),
                )
                version = self._repository.save_version(version, attempt_id=attempt.attempt_id)
                attempt = self._success_step(
                    attempt,
                    WorkspaceStepName.SNAPSHOT_PUBLICATION,
                    publication.snapshot_id.value,
                    publication.snapshot_manifest_digest,
                )
            except Exception as error:
                self._record_failure(attempt, WorkspaceStepName.SNAPSHOT_PUBLICATION, error, WorkspaceAttemptState.FAILED)
                raise
        else:
            if (
                version.workspace_id != workspace.workspace_id
                or version.repository_revision != attempt.repository_revision
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "Workspace Attempt is bound to an inconsistent Version",
                )
            current_attempt = self._repository.get_attempt(attempt.attempt_id)
            snapshot_step = current_attempt.latest_step(
                WorkspaceStepName.SNAPSHOT_PUBLICATION
            )
            if (
                snapshot_step is None
                or snapshot_step.outcome is not WorkspaceStepOutcome.SUCCEEDED
            ):
                attempt = self._success_step(
                    current_attempt,
                    WorkspaceStepName.SNAPSHOT_PUBLICATION,
                    version.snapshot_id.value,
                    version.snapshot_manifest_digest,
                )

        try:
            single = self._ensure_read_set(workspace, (version,), attempt, WorkspaceStepName.SINGLE_READ_SET)
            if version.single_read_set_id != single.read_set_id:
                version = self._repository.update_version(
                    version.transition(
                        availability=WorkspaceVersionAvailability.READ_BUNDLE_UNAVAILABLE,
                        single_read_set_id=single.read_set_id,
                        comparison_read_set_id=version.comparison_read_set_id,
                    ),
                    expected_revision=version.revision,
                )
            previous = self._previous_version(workspace.workspace_id, version)
            comparison: ReadSetRegistration | None = None
            if previous is None:
                latest = self._repository.get_attempt(attempt.attempt_id).latest_step(WorkspaceStepName.COMPARISON_READ_SET)
                if latest is None or latest.outcome is not WorkspaceStepOutcome.SKIPPED:
                    attempt = self._repository.append_step(
                        attempt_id=attempt.attempt_id,
                        name=WorkspaceStepName.COMPARISON_READ_SET,
                        outcome=WorkspaceStepOutcome.SKIPPED,
                        reference_id=None,
                        reference_digest=None,
                        error_code=None,
                        error_message=None,
                        occurred_at=self._now(),
                    )
            else:
                comparison = self._ensure_read_set(
                    workspace,
                    (previous, version),
                    attempt,
                    WorkspaceStepName.COMPARISON_READ_SET,
                )
                if version.comparison_read_set_id != comparison.read_set_id:
                    version = self._repository.update_version(
                        version.transition(
                            availability=WorkspaceVersionAvailability.READ_BUNDLE_UNAVAILABLE,
                            single_read_set_id=version.single_read_set_id,
                            comparison_read_set_id=comparison.read_set_id,
                        ),
                        expected_revision=version.revision,
                    )
        except Exception as error:
            current_attempt = self._repository.get_attempt(attempt.attempt_id)
            name = (
                WorkspaceStepName.COMPARISON_READ_SET
                if current_attempt.latest_step(WorkspaceStepName.SINGLE_READ_SET)
                and current_attempt.latest_step(WorkspaceStepName.SINGLE_READ_SET).outcome is WorkspaceStepOutcome.SUCCEEDED
                else WorkspaceStepName.SINGLE_READ_SET
            )
            self._record_failure(current_attempt, name, error, WorkspaceAttemptState.READ_BUNDLE_UNAVAILABLE)
            raise

        try:
            catalog, pointer = self._catalog.publish()
        except Exception as error:
            current = self._repository.get_attempt(attempt.attempt_id)
            if version.availability not in {
                WorkspaceVersionAvailability.CATALOG_UNAVAILABLE,
                WorkspaceVersionAvailability.QUERYABLE,
            }:
                version = self._repository.update_version(
                    version.transition(
                        availability=WorkspaceVersionAvailability.CATALOG_UNAVAILABLE,
                        single_read_set_id=version.single_read_set_id,
                        comparison_read_set_id=version.comparison_read_set_id,
                    ),
                    expected_revision=version.revision,
                )
            self._record_failure(current, WorkspaceStepName.CATALOG_PUBLICATION, error, WorkspaceAttemptState.CATALOG_UNAVAILABLE)
            raise

        try:
            current_attempt = self._repository.get_attempt(attempt.attempt_id)
            latest = current_attempt.latest_step(WorkspaceStepName.CATALOG_PUBLICATION)
            if latest is None or latest.outcome is not WorkspaceStepOutcome.SUCCEEDED:
                current_attempt = self._success_step(
                    current_attempt,
                    WorkspaceStepName.CATALOG_PUBLICATION,
                    catalog.catalog_id.value,
                    catalog.document_digest,
                )
            if version.availability is not WorkspaceVersionAvailability.QUERYABLE:
                version = self._repository.update_version(
                    version.transition(
                        availability=WorkspaceVersionAvailability.QUERYABLE,
                        single_read_set_id=version.single_read_set_id,
                        comparison_read_set_id=version.comparison_read_set_id,
                    ),
                    expected_revision=version.revision,
                )
            final_attempt = self._repository.transition_attempt(
                attempt_id=current_attempt.attempt_id,
                expected_revision=current_attempt.revision,
                state=WorkspaceAttemptState.SUCCEEDED,
                occurred_at=self._now(),
            )
        except Exception:
            # The Catalog publication is already authoritative.  Never relabel it
            # as failed or regress a queryable Version when local finalization is
            # interrupted; a resume can deterministically reconcile this state.
            current = self._repository.get_attempt(attempt.attempt_id)
            if current.state is not WorkspaceAttemptState.OUTCOME_PENDING:
                self._repository.transition_attempt(
                    attempt_id=current.attempt_id,
                    expected_revision=current.revision,
                    state=WorkspaceAttemptState.OUTCOME_PENDING,
                    occurred_at=self._now(),
                )
            raise
        return MavenWorkspaceUpdateResult(
            workspace=workspace,
            attempt=final_attempt,
            version=version,
            single_read_set=single,
            comparison_read_set=comparison,
            catalog=catalog,
            catalog_pointer=pointer,
            snapshot_owner_result=owner_result,
            snapshot_metrics=snapshot_metrics,
        )


    def _ensure_read_set(
        self,
        workspace: MavenWorkspace,
        versions: tuple[MavenWorkspaceVersion, ...],
        attempt: MavenWorkspaceAttempt,
        step_name: WorkspaceStepName,
    ) -> ReadSetRegistration:
        read_set_id = _derived_id(
            "read_set",
            workspace.workspace_id.value,
            *(item.snapshot_id.value for item in versions),
        )
        try:
            existing = self._catalog.get(read_set_id)
        except DomainError as error:
            if (
                error.code is not ErrorCode.INVALID_ARGUMENT
                or error.details.get("reason_code")
                != "READ_SET_REGISTRATION_NOT_FOUND"
            ):
                raise
            existing = None
        if existing is not None:
            if (
                existing.workspace_id != workspace.workspace_id
                or existing.workspace_version_ids
                != tuple(item.version_id for item in versions)
                or tuple(item.snapshot_id for item in existing.snapshot_bindings)
                != tuple(item.snapshot_id for item in versions)
            ):
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "derived Read Set identity is bound to another exact selection",
                )
            current = self._repository.get_attempt(attempt.attempt_id)
            latest = current.latest_step(step_name)
            if latest is None or latest.outcome is not WorkspaceStepOutcome.SUCCEEDED:
                self._success_step(current, step_name, read_set_id.value, existing.digest)
            return existing

        snapshot_ids = tuple(item.snapshot_id for item in versions)
        task_boundary = TaskBoundary.create(
            task_id=_derived_id("task", "workspace-read-set", read_set_id.value),
            task_revision=Revision(1),
            scope_id=workspace.scope_id,
            purpose=(
                "STRUCTURE_EXACT_SNAPSHOT_READ@1"
                if len(snapshot_ids) == 1
                else "STRUCTURE_SNAPSHOT_COMPARISON@1"
            ),
            classification="INTERNAL",
        )
        session = self._operations.open_read_session(
            workspace=workspace,
            snapshot_ids=snapshot_ids,
            task_boundary=task_boundary,
            idempotency_key=IdempotencyKey(f"workspace:{read_set_id.value}:session"),
        )
        directory = read_set_id.value
        snapshot_receipts = tuple(
            self._operations.build_snapshot_bundle(
                snapshot_id=snapshot_id,
                idempotency_key=IdempotencyKey(f"workspace:{read_set_id.value}:snapshot:{ordinal}"),
                destination=f"{directory}/snapshot-{ordinal:03d}.json",
            )
            for ordinal, snapshot_id in enumerate(snapshot_ids)
        )
        ordered_receipt = self._operations.build_ordered_bundle(
            session_id=session.session_id,
            idempotency_key=IdempotencyKey(f"workspace:{read_set_id.value}:ordered"),
            destination=f"{directory}/ordered.json",
        )
        registration = self._catalog.register(
            read_set_id=read_set_id,
            workspace_id=workspace.workspace_id,
            workspace_version_ids=tuple(item.version_id for item in versions),
            session=session,
            ordered_receipt=ordered_receipt,
            snapshot_receipts=snapshot_receipts,
            bundle_locator=directory,
        )
        current = self._repository.get_attempt(attempt.attempt_id)
        self._success_step(current, step_name, registration.read_set_id.value, registration.digest)
        return registration

    def _previous_version(
        self, workspace_id: StableId, version: MavenWorkspaceVersion
    ) -> MavenWorkspaceVersion | None:
        versions = self._repository.list_versions(workspace_id)
        previous = [item for item in versions if item.ordinal < version.ordinal]
        return previous[-1] if previous else None

    def _success_step(
        self,
        attempt: MavenWorkspaceAttempt,
        name: WorkspaceStepName,
        reference_id: str,
        reference_digest: Digest,
    ) -> MavenWorkspaceAttempt:
        return self._repository.append_step(
            attempt_id=attempt.attempt_id,
            name=name,
            outcome=WorkspaceStepOutcome.SUCCEEDED,
            reference_id=reference_id,
            reference_digest=reference_digest,
            error_code=None,
            error_message=None,
            occurred_at=self._now(),
        )

    def _record_failure(
        self,
        attempt: MavenWorkspaceAttempt,
        name: WorkspaceStepName,
        error: Exception,
        known_state: WorkspaceAttemptState,
    ) -> None:
        if isinstance(error, DomainError):
            outcome = WorkspaceStepOutcome.FAILED
            error_code = error.code.value
            message = error.message
            state = known_state
        else:
            outcome = WorkspaceStepOutcome.OUTCOME_PENDING
            error_code = "OUTCOME_PENDING"
            message = str(error) or type(error).__name__
            state = WorkspaceAttemptState.OUTCOME_PENDING
        updated = self._repository.append_step(
            attempt_id=attempt.attempt_id,
            name=name,
            outcome=outcome,
            reference_id=None,
            reference_digest=None,
            error_code=error_code,
            error_message=message,
            occurred_at=self._now(),
        )
        self._repository.transition_attempt(
            attempt_id=updated.attempt_id,
            expected_revision=updated.revision,
            state=state,
            occurred_at=self._now(),
        )

    def _assemble(
        self,
        workspace: MavenWorkspace,
        attempt: MavenWorkspaceAttempt,
        owner_result: object | None,
    ) -> MavenWorkspaceUpdateResult:
        version = self._repository.find_version_for_attempt(attempt.attempt_id)
        single = (
            self._catalog.get(version.single_read_set_id)
            if version is not None and version.single_read_set_id is not None
            else None
        )
        comparison = (
            self._catalog.get(version.comparison_read_set_id)
            if version is not None and version.comparison_read_set_id is not None
            else None
        )
        catalog = self._catalog.read_current_source_off() if version and version.availability is WorkspaceVersionAvailability.QUERYABLE else None
        pointer = ReadSetCatalogPointer.from_catalog(catalog) if catalog else None
        return MavenWorkspaceUpdateResult(
            workspace,
            attempt,
            version,
            single,
            comparison,
            catalog,
            pointer,
            owner_result,
            None,
        )

    @staticmethod
    def _owner_key(attempt: MavenWorkspaceAttempt, suffix: str) -> IdempotencyKey:
        return IdempotencyKey(f"workspace:{attempt.attempt_id.value}:{suffix}")

    def _now(self) -> datetime:
        return _aware_time(self._clock(), "Workspace clock").astimezone(timezone.utc)


def workspace_attempt_core(value: MavenWorkspaceAttempt) -> dict[str, object]:
    return {
        "attempt_id": value.attempt_id.value,
        "idempotency_key": value.idempotency_key.value,
        "request_digest": value.request_digest.value,
        "workspace_id": value.workspace_id.value,
        "repository_revision": value.repository_revision,
        "expected_current_snapshot_id": value.expected_current_snapshot_id.value if value.expected_current_snapshot_id else None,
        "state": value.state.value,
        "revision": value.revision.value,
        "created_at": value.created_at,
        "revised_at": value.revised_at,
        "steps": tuple(item.digest.value for item in value.steps),
    }


def _derived_id(kind: str, *parts: str) -> StableId:
    payload = "\0".join(parts).encode("utf-8")
    return StableId(f"{kind}_{hashlib.sha256(payload).hexdigest()[:32]}")


def _exact_commit(value: str) -> str:
    if not isinstance(value, str) or not _COMMIT_RE.fullmatch(value):
        raise _invalid("MAVEN_WORKSPACE_COMMIT_INVALID", "Workspace update requires an exact full Git commit")
    return value


def _absolute_repository(value: str) -> str:
    text = _text(value, "repository locator")
    path = Path(text)
    if (
        not path.is_absolute()
        or str(path) != text
        or os.path.normpath(text) != text
        or path == Path(path.anchor)
    ):
        raise _invalid("MAVEN_WORKSPACE_REPOSITORY_INVALID", "Workspace repository locator must be an absolute normalized path")
    return text


def _relative_path(value: str, label: str) -> str:
    text = _text(value, label)
    if "\\" in text or text.startswith("/") or text.endswith("/") or any(part in {"", ".", ".."} for part in text.split("/")):
        raise _invalid("MAVEN_WORKSPACE_PATH_INVALID", f"{label} must be a normalized relative POSIX path")
    return text


def _knowledge_profile(value: str) -> str:
    profile_ref = _text(value, "knowledge profile ref")
    if profile_ref not in {
        MAVEN_STRUCTURE_PROFILE_REF,
        JAVA_STATIC_CALL_PROFILE_REF,
        JAVA_SOURCE_SEMANTICS_PROFILE_REF,
    }:
        raise _invalid(
            "MAVEN_WORKSPACE_PROFILE_UNSUPPORTED",
            "Workspace knowledge profile is not supported",
        )
    return profile_ref


def _aware_time(value: datetime, label: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise _invalid("MAVEN_WORKSPACE_TIME_INVALID", f"{label} must include a timezone")
    return value


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value.encode("utf-8")) > 512:
        raise _invalid("MAVEN_WORKSPACE_TEXT_INVALID", f"{label} is invalid")
    return value


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(ErrorCode.INVALID_ARGUMENT, message, {"reason_code": reason_code})


__all__ = [
    "MavenWorkspace",
    "MavenWorkspaceAttempt",
    "MavenWorkspaceOperations",
    "MavenWorkspaceRepository",
    "MavenWorkspaceService",
    "MavenWorkspaceUpdateResult",
    "MavenWorkspaceVersion",
    "WorkspaceAttemptState",
    "WorkspaceConfigurationAuthority",
    "WorkspaceSnapshotPublication",
    "WorkspaceSnapshotMetrics",
    "WorkspaceStepEvent",
    "WorkspaceStepName",
    "WorkspaceStepOutcome",
    "WorkspaceVersionAvailability",
    "workspace_attempt_core",
]
