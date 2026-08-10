"""Persistent exact-Snapshot selection for Structure knowledge use.

This module stops at the read authority boundary.  It fixes an exact single
Snapshot or an ordered comparable Snapshot set, but deliberately does not
project a Structure View, create a Read Bundle, or execute a query.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Protocol

from software_world_model.application_services.knowledge_use import TaskBoundary
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.knowledge_engine.context_comparison import (
    StructureContextComparisonAssessment,
    StructureContextComparisonCoverageInput,
    StructureContextComparisonInput,
    StructureContextComparisonOutcome,
    StructureContextComparisonService,
)
from software_world_model.knowledge_engine.scope import (
    AssertionOutcome,
    KnowledgeScopeService,
    ScopeLifecycle,
    ScopePurpose,
    ScopeStateAssertion,
)
from software_world_model.knowledge_engine.structure import CoverageRecord
from software_world_model.knowledge_engine.structure_publication import (
    StructureSnapshot,
    structure_snapshot_manifest_digest,
)


class StructureReadSelectionMode(str, Enum):
    CURRENT = "CURRENT"
    ORDERED_EXACT = "ORDERED_EXACT"


class StructureReadOrder(str, Enum):
    SINGLE = "SINGLE"
    CALLER_DECLARED = "CALLER_DECLARED"


class StructureReadPurpose(str, Enum):
    EXACT_SNAPSHOT = "STRUCTURE_EXACT_SNAPSHOT_READ@1"
    SNAPSHOT_COMPARISON = "STRUCTURE_SNAPSHOT_COMPARISON@1"


@dataclass(frozen=True, slots=True)
class StructureCoverageReadBinding:
    """No-payload binding needed to compare one exact Coverage State."""

    coverage_root_id: StableId
    coverage_root_digest: Digest
    coverage_root_ref: str
    coverage_state_id: StableId
    coverage_state_digest: Digest
    profile_ref: str
    schema_ref: str
    schema_digest: Digest
    source_binding_id: StableId
    logical_reactor_root: str
    evaluation_context_ref: str
    evaluation_context_digest: Digest
    canonicalization_ref: str
    canonicalization_digest: Digest
    knowledge_context_digest: Digest
    source_revision: str
    member_manifest_digest: Digest
    comparison_basis_digest: Digest
    digest: Digest

    @classmethod
    def from_record(cls, record: CoverageRecord) -> "StructureCoverageReadBinding":
        if not isinstance(record, CoverageRecord):
            raise _invalid(
                "READ_SET_COVERAGE_RECORD_REQUIRED",
                "Structure read selection requires a typed Coverage record",
            )
        record.root.require_valid_identity()
        record.state.require_valid_identity(record.root)
        root = record.root
        state = record.state
        comparison_basis_digest = _coverage_comparison_basis_digest(record)
        core = {
            "coverage_root_id": root.coverage_root_id.value,
            "coverage_root_digest": root.allocation_key_digest.value,
            "coverage_root_ref": root.coverage_root_ref,
            "coverage_state_id": state.coverage_state_id.value,
            "coverage_state_digest": state.coverage_state_digest.value,
            "profile_ref": root.profile_ref,
            "schema_ref": root.schema_ref,
            "schema_digest": root.schema_digest.value,
            "source_binding_id": root.source_binding_id.value,
            "logical_reactor_root": root.logical_reactor_root,
            "evaluation_context_ref": root.maven_evaluation_context_ref,
            "evaluation_context_digest": (
                root.maven_evaluation_context_digest.value
            ),
            "canonicalization_ref": root.canonicalization_ref,
            "canonicalization_digest": root.canonicalization_digest.value,
            "knowledge_context_digest": state.knowledge_context_digest.value,
            "source_revision": state.source_revision,
            "member_manifest_digest": state.complete_member_manifest.digest.value,
            "comparison_basis_digest": comparison_basis_digest.value,
        }
        return cls(
            coverage_root_id=root.coverage_root_id,
            coverage_root_digest=root.allocation_key_digest,
            coverage_root_ref=root.coverage_root_ref,
            coverage_state_id=state.coverage_state_id,
            coverage_state_digest=state.coverage_state_digest,
            profile_ref=root.profile_ref,
            schema_ref=root.schema_ref,
            schema_digest=root.schema_digest,
            source_binding_id=root.source_binding_id,
            logical_reactor_root=root.logical_reactor_root,
            evaluation_context_ref=root.maven_evaluation_context_ref,
            evaluation_context_digest=root.maven_evaluation_context_digest,
            canonicalization_ref=root.canonicalization_ref,
            canonicalization_digest=root.canonicalization_digest,
            knowledge_context_digest=state.knowledge_context_digest,
            source_revision=state.source_revision,
            member_manifest_digest=state.complete_member_manifest.digest,
            comparison_basis_digest=comparison_basis_digest,
            digest=digest_of(["STRUCTURE_COVERAGE_READ_BINDING@1", core]),
        )

    def require_valid(self) -> None:
        if self.coverage_root_id.kind != "coverage_root":
            raise _invalid(
                "READ_SET_COVERAGE_ROOT_KIND_INVALID",
                "Structure read Coverage Root ID has the wrong kind",
            )
        if self.coverage_state_id.kind != "coverage_state":
            raise _invalid(
                "READ_SET_COVERAGE_STATE_KIND_INVALID",
                "Structure read Coverage State ID has the wrong kind",
            )
        for value, label in (
            (self.coverage_root_ref, "Coverage Root ref"),
            (self.profile_ref, "Profile ref"),
            (self.schema_ref, "Schema ref"),
            (self.logical_reactor_root, "logical reactor root"),
            (self.evaluation_context_ref, "Evaluation Context ref"),
            (self.canonicalization_ref, "Canonicalization ref"),
            (self.source_revision, "source revision"),
        ):
            _text(value, label)
        comparison_core = {
            "coverage_root_id": self.coverage_root_id.value,
            "coverage_root_digest": self.coverage_root_digest.value,
            "coverage_root_ref": self.coverage_root_ref,
            "profile_ref": self.profile_ref,
            "schema_ref": self.schema_ref,
            "schema_digest": self.schema_digest.value,
            "source_binding_id": self.source_binding_id.value,
            "logical_reactor_root": self.logical_reactor_root,
            "evaluation_context_ref": self.evaluation_context_ref,
            "evaluation_context_digest": self.evaluation_context_digest.value,
            "canonicalization_ref": self.canonicalization_ref,
            "canonicalization_digest": self.canonicalization_digest.value,
        }
        expected_basis = digest_of(
            ["STRUCTURE_COVERAGE_COMPARISON_BASIS@1", comparison_core]
        )
        core = {
            **comparison_core,
            "coverage_state_id": self.coverage_state_id.value,
            "coverage_state_digest": self.coverage_state_digest.value,
            "knowledge_context_digest": self.knowledge_context_digest.value,
            "source_revision": self.source_revision,
            "member_manifest_digest": self.member_manifest_digest.value,
            "comparison_basis_digest": self.comparison_basis_digest.value,
        }
        expected_digest = digest_of(["STRUCTURE_COVERAGE_READ_BINDING@1", core])
        if (
            self.comparison_basis_digest != expected_basis
            or self.digest != expected_digest
        ):
            raise _invalid(
                "READ_SET_COVERAGE_DIGEST_MISMATCH",
                "Structure read Coverage binding is not canonical",
            )


@dataclass(frozen=True, slots=True)
class StructureSnapshotReadBinding:
    """Exact immutable Snapshot identity pinned into one ordered read set."""

    scope_id: StableId
    snapshot_id: StableId
    snapshot_revision: Revision
    snapshot_manifest_digest: Digest
    schema_ref: str
    schema_digest: Digest
    schema_registration_digest: Digest
    schema_availability_digest: Digest
    schema_adoption_digest: Digest
    coverages: tuple[StructureCoverageReadBinding, ...]
    coverage_set_digest: Digest
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        snapshot: StructureSnapshot,
        coverages: tuple[StructureCoverageReadBinding, ...],
    ) -> "StructureSnapshotReadBinding":
        normalized_coverages = tuple(
            sorted(coverages, key=lambda item: item.coverage_root_id.value)
        )
        coverage_set_digest = digest_of(
            [
                "STRUCTURE_SNAPSHOT_COVERAGE_SET@1",
                tuple(item.digest.value for item in normalized_coverages),
            ]
        )
        core = {
            "scope_id": snapshot.scope_id.value,
            "snapshot_id": snapshot.snapshot_id.value,
            "snapshot_revision": snapshot.snapshot_revision.value,
            "snapshot_manifest_digest": snapshot.manifest_digest.value,
            "schema_ref": snapshot.schema_ref,
            "schema_digest": snapshot.schema_digest.value,
            "schema_registration_digest": snapshot.schema_registration_digest.value,
            "schema_availability_digest": snapshot.schema_availability_digest.value,
            "schema_adoption_digest": snapshot.schema_adoption_digest.value,
            "coverage_set_digest": coverage_set_digest.value,
        }
        value = cls(
            scope_id=snapshot.scope_id,
            snapshot_id=snapshot.snapshot_id,
            snapshot_revision=snapshot.snapshot_revision,
            snapshot_manifest_digest=snapshot.manifest_digest,
            schema_ref=snapshot.schema_ref,
            schema_digest=snapshot.schema_digest,
            schema_registration_digest=snapshot.schema_registration_digest,
            schema_availability_digest=snapshot.schema_availability_digest,
            schema_adoption_digest=snapshot.schema_adoption_digest,
            coverages=normalized_coverages,
            coverage_set_digest=coverage_set_digest,
            digest=digest_of(["STRUCTURE_SNAPSHOT_READ_BINDING@1", core]),
        )
        value.require_valid()
        return value

    def require_valid(self) -> None:
        if self.snapshot_id.kind != "structure_snapshot":
            raise _invalid(
                "READ_SET_SNAPSHOT_KIND_INVALID",
                "Structure read Snapshot ID has the wrong kind",
            )
        _text(self.schema_ref, "Schema ref")
        expected_coverages = tuple(
            sorted(self.coverages, key=lambda item: item.coverage_root_id.value)
        )
        if (
            not self.coverages
            or self.coverages != expected_coverages
            or len({item.coverage_root_id for item in self.coverages})
            != len(self.coverages)
        ):
            raise _invalid(
                "READ_SET_COVERAGE_SET_INVALID",
                "Structure read Snapshot requires a sorted non-empty Coverage set",
            )
        for coverage in self.coverages:
            coverage.require_valid()
            if (
                coverage.schema_ref != self.schema_ref
                or coverage.schema_digest != self.schema_digest
            ):
                raise _invalid(
                    "READ_SET_SNAPSHOT_COVERAGE_SCHEMA_MISMATCH",
                    "Structure read Snapshot and Coverage use different Schema definitions",
                )
        expected_coverage_set = digest_of(
            [
                "STRUCTURE_SNAPSHOT_COVERAGE_SET@1",
                tuple(item.digest.value for item in self.coverages),
            ]
        )
        core = {
            "scope_id": self.scope_id.value,
            "snapshot_id": self.snapshot_id.value,
            "snapshot_revision": self.snapshot_revision.value,
            "snapshot_manifest_digest": self.snapshot_manifest_digest.value,
            "schema_ref": self.schema_ref,
            "schema_digest": self.schema_digest.value,
            "schema_registration_digest": self.schema_registration_digest.value,
            "schema_availability_digest": self.schema_availability_digest.value,
            "schema_adoption_digest": self.schema_adoption_digest.value,
            "coverage_set_digest": self.coverage_set_digest.value,
        }
        expected_digest = digest_of(["STRUCTURE_SNAPSHOT_READ_BINDING@1", core])
        if (
            self.coverage_set_digest != expected_coverage_set
            or self.digest != expected_digest
        ):
            raise _invalid(
                "READ_SET_SNAPSHOT_DIGEST_MISMATCH",
                "Structure Snapshot read binding is not canonical",
            )


@dataclass(frozen=True, slots=True)
class StructureReadSession:
    session_id: StableId
    request_digest: Digest
    scope_id: StableId
    scope_revision: Revision
    task_boundary: TaskBoundary
    scope_assertion: ScopeStateAssertion
    caller_ref: str
    purpose: StructureReadPurpose
    selection_mode: StructureReadSelectionMode
    order: StructureReadOrder
    snapshots: tuple[StructureSnapshotReadBinding, ...]
    context_comparisons: tuple[StructureContextComparisonAssessment, ...]
    read_set_digest: Digest
    opened_at: datetime
    digest: Digest

    def require_valid(self) -> None:
        if self.session_id.kind != "structure_read_session":
            raise _invalid(
                "READ_SESSION_ID_KIND_INVALID",
                "Structure read Session ID has the wrong kind",
            )
        try:
            mode = (
                self.selection_mode
                if isinstance(self.selection_mode, StructureReadSelectionMode)
                else StructureReadSelectionMode(self.selection_mode)
            )
            order = (
                self.order
                if isinstance(self.order, StructureReadOrder)
                else StructureReadOrder(self.order)
            )
            purpose = (
                self.purpose
                if isinstance(self.purpose, StructureReadPurpose)
                else StructureReadPurpose(self.purpose)
            )
        except (TypeError, ValueError) as exc:
            raise _invalid(
                "READ_SESSION_SELECTION_INVALID",
                "Structure read Session selection mode or order is invalid",
            ) from exc
        _text(self.caller_ref, "Structure read caller ref")
        _require_task_boundary(
            self.task_boundary,
            scope_id=self.scope_id,
            purpose=purpose,
        )
        _require_scope_assertion(
            self.scope_assertion,
            scope_id=self.scope_id,
            scope_revision=self.scope_revision,
            task_boundary=self.task_boundary,
            caller_ref=self.caller_ref,
        )
        if self.opened_at.tzinfo is None or self.opened_at.utcoffset() is None:
            raise _invalid(
                "READ_SESSION_TIMEZONE_REQUIRED",
                "Structure read Session time must include a timezone",
            )
        if not self.snapshots:
            raise _invalid(
                "READ_SET_EMPTY",
                "Structure read Session requires at least one exact Snapshot",
            )
        for snapshot in self.snapshots:
            snapshot.require_valid()
            if snapshot.scope_id != self.scope_id:
                raise _invalid(
                    "READ_SET_SCOPE_MISMATCH",
                    "Structure read Snapshot is outside the Session Scope",
                )
        if mode is StructureReadSelectionMode.CURRENT:
            if (
                len(self.snapshots) != 1
                or order is not StructureReadOrder.SINGLE
                or purpose is not StructureReadPurpose.EXACT_SNAPSHOT
            ):
                raise _invalid(
                    "READ_SESSION_CURRENT_SHAPE_INVALID",
                    "CURRENT selection must fix exactly one Snapshot",
                )
        else:
            expected_order = (
                StructureReadOrder.SINGLE
                if len(self.snapshots) == 1
                else StructureReadOrder.CALLER_DECLARED
            )
            expected_purpose = (
                StructureReadPurpose.EXACT_SNAPSHOT
                if len(self.snapshots) == 1
                else StructureReadPurpose.SNAPSHOT_COMPARISON
            )
            if order is not expected_order or purpose is not expected_purpose:
                raise _invalid(
                    "READ_SET_ORDER_POLICY_INVALID",
                    "exact Structure Snapshot set uses the wrong order policy",
                )
        if len({item.snapshot_id for item in self.snapshots}) != len(self.snapshots):
            raise _invalid(
                "READ_SET_DUPLICATE_SNAPSHOT",
                "ordered Structure read set cannot repeat a Snapshot ID",
            )
        expected_comparisons = _context_comparisons(
            self.snapshots,
            purpose=purpose,
        )
        if self.context_comparisons != expected_comparisons:
            raise _invalid(
                "READ_SET_CONTEXT_ASSESSMENTS_INVALID",
                "Structure read set does not contain the exact adjacent Context assessments",
            )
        expected_request = structure_read_session_request_digest(
            scope_id=self.scope_id,
            scope_revision=self.scope_revision,
            task_boundary=self.task_boundary,
            scope_assertion=self.scope_assertion,
            caller_ref=self.caller_ref,
            purpose=purpose,
            selection_mode=mode,
            snapshot_ids=(
                ()
                if mode is StructureReadSelectionMode.CURRENT
                else tuple(item.snapshot_id for item in self.snapshots)
            ),
        )
        expected_read_set = structure_ordered_read_set_digest(
            self.snapshots,
            self.context_comparisons,
        )
        expected_digest = structure_read_session_digest(
            session_id=self.session_id,
            request_digest=self.request_digest,
            scope_id=self.scope_id,
            scope_revision=self.scope_revision,
            task_boundary=self.task_boundary,
            scope_assertion=self.scope_assertion,
            caller_ref=self.caller_ref,
            purpose=purpose,
            selection_mode=mode,
            order=order,
            read_set_digest=self.read_set_digest,
            opened_at=self.opened_at,
        )
        if (
            self.request_digest != expected_request
            or self.read_set_digest != expected_read_set
            or self.digest != expected_digest
        ):
            raise _invalid(
                "READ_SESSION_DIGEST_MISMATCH",
                "Structure read Session is not canonical",
            )


class StructureSnapshotReadSource(Protocol):
    """Read-only subset of the Structure publication authority."""

    def current_snapshot(self, scope_id: StableId) -> StructureSnapshot | None: ...

    def get_snapshot(self, snapshot_id: StableId) -> StructureSnapshot: ...

    def get_coverage(
        self, snapshot_id: StableId, coverage_root_id: StableId
    ) -> CoverageRecord: ...


class StructureReadSessionRepository(Protocol):
    def replay_open(
        self, *, idempotency_key: IdempotencyKey, request_digest: Digest
    ) -> StructureReadSession | None: ...

    def save_session(
        self,
        *,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        scope_id: StableId,
        scope_revision: Revision,
        task_boundary: TaskBoundary,
        scope_assertion: ScopeStateAssertion,
        caller_ref: str,
        purpose: StructureReadPurpose,
        selection_mode: StructureReadSelectionMode,
        order: StructureReadOrder,
        snapshots: tuple[StructureSnapshotReadBinding, ...],
        context_comparisons: tuple[StructureContextComparisonAssessment, ...],
        opened_at: datetime,
    ) -> StructureReadSession: ...

    def get_session(self, session_id: StableId) -> StructureReadSession: ...


class StructureReadSessionService:
    def __init__(
        self,
        repository: StructureReadSessionRepository,
        snapshots: StructureSnapshotReadSource,
        scopes: KnowledgeScopeService,
        context_comparisons: StructureContextComparisonService | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._snapshots = snapshots
        self._scopes = scopes
        self._context_comparisons = (
            context_comparisons or StructureContextComparisonService()
        )
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def open_current(
        self,
        *,
        scope_id: StableId,
        scope_revision: Revision,
        task_boundary: TaskBoundary,
        caller_ref: str,
        idempotency_key: IdempotencyKey,
    ) -> StructureReadSession:
        purpose = StructureReadPurpose.EXACT_SNAPSHOT
        assertion = self._authorize(
            scope_id=scope_id,
            scope_revision=scope_revision,
            task_boundary=task_boundary,
            caller_ref=caller_ref,
            purpose=purpose,
            idempotency_key=idempotency_key,
        )
        request_digest = structure_read_session_request_digest(
            scope_id=scope_id,
            scope_revision=scope_revision,
            task_boundary=task_boundary,
            scope_assertion=assertion,
            caller_ref=caller_ref,
            purpose=purpose,
            selection_mode=StructureReadSelectionMode.CURRENT,
            snapshot_ids=(),
        )
        replay = self._repository.replay_open(
            idempotency_key=idempotency_key,
            request_digest=request_digest,
        )
        if replay is not None:
            return self._revalidate(
                replay,
                expected_task_boundary=task_boundary,
                expected_scope_assertion=assertion,
            )

        # Resolve the mutable pointer exactly once.  Everything after this line
        # is addressed by the immutable Snapshot ID returned here.
        current = self._snapshots.current_snapshot(scope_id)
        if current is None:
            raise _invalid(
                "READ_SESSION_CURRENT_NOT_FOUND",
                "Structure Scope has no CURRENT Snapshot",
            )
        if current.scope_id != scope_id:
            raise _invalid(
                "READ_SESSION_CURRENT_SCOPE_MISMATCH",
                "Structure CURRENT resolved outside the requested Scope",
            )
        binding = self._read_exact_binding(current.snapshot_id)
        if binding.scope_id != scope_id:
            raise _invalid(
                "READ_SET_SCOPE_MISMATCH",
                "resolved CURRENT Snapshot is outside the requested Scope",
            )
        session = self._repository.save_session(
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            scope_id=scope_id,
            scope_revision=scope_revision,
            task_boundary=task_boundary,
            scope_assertion=assertion,
            caller_ref=caller_ref,
            purpose=purpose,
            selection_mode=StructureReadSelectionMode.CURRENT,
            order=StructureReadOrder.SINGLE,
            snapshots=(binding,),
            context_comparisons=(),
            opened_at=self._now(),
        )
        return self._revalidate(
            session,
            expected_task_boundary=task_boundary,
            expected_scope_assertion=assertion,
        )

    def open_ordered(
        self,
        *,
        scope_id: StableId,
        scope_revision: Revision,
        task_boundary: TaskBoundary,
        caller_ref: str,
        snapshot_ids: tuple[StableId, ...],
        idempotency_key: IdempotencyKey,
    ) -> StructureReadSession:
        if not snapshot_ids:
            raise _invalid(
                "READ_SET_EMPTY",
                "ordered Structure read set requires exact Snapshot IDs",
            )
        if len(set(snapshot_ids)) != len(snapshot_ids):
            raise _invalid(
                "READ_SET_DUPLICATE_SNAPSHOT",
                "ordered Structure read set cannot repeat a Snapshot ID",
            )
        purpose = (
            StructureReadPurpose.EXACT_SNAPSHOT
            if len(snapshot_ids) == 1
            else StructureReadPurpose.SNAPSHOT_COMPARISON
        )
        assertion = self._authorize(
            scope_id=scope_id,
            scope_revision=scope_revision,
            task_boundary=task_boundary,
            caller_ref=caller_ref,
            purpose=purpose,
            idempotency_key=idempotency_key,
        )
        request_digest = structure_read_session_request_digest(
            scope_id=scope_id,
            scope_revision=scope_revision,
            task_boundary=task_boundary,
            scope_assertion=assertion,
            caller_ref=caller_ref,
            purpose=purpose,
            selection_mode=StructureReadSelectionMode.ORDERED_EXACT,
            snapshot_ids=snapshot_ids,
        )
        replay = self._repository.replay_open(
            idempotency_key=idempotency_key,
            request_digest=request_digest,
        )
        if replay is not None:
            return self._revalidate(
                replay,
                expected_task_boundary=task_boundary,
                expected_scope_assertion=assertion,
            )

        bindings = tuple(self._read_exact_binding(item) for item in snapshot_ids)
        if any(item.scope_id != scope_id for item in bindings):
            raise _invalid(
                "READ_SET_SCOPE_MISMATCH",
                "ordered Structure read set crosses the requested Scope",
            )
        comparisons = _context_comparisons(
            bindings,
            purpose=purpose,
            service=self._context_comparisons,
        )
        order = (
            StructureReadOrder.SINGLE
            if len(bindings) == 1
            else StructureReadOrder.CALLER_DECLARED
        )
        session = self._repository.save_session(
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            scope_id=scope_id,
            scope_revision=scope_revision,
            task_boundary=task_boundary,
            scope_assertion=assertion,
            caller_ref=caller_ref,
            purpose=purpose,
            selection_mode=StructureReadSelectionMode.ORDERED_EXACT,
            order=order,
            snapshots=bindings,
            context_comparisons=comparisons,
            opened_at=self._now(),
        )
        return self._revalidate(
            session,
            expected_task_boundary=task_boundary,
            expected_scope_assertion=assertion,
        )

    def get_session(self, session_id: StableId) -> StructureReadSession:
        return self._revalidate(self._repository.get_session(session_id))

    def _authorize(
        self,
        *,
        scope_id: StableId,
        scope_revision: Revision,
        task_boundary: TaskBoundary,
        caller_ref: str,
        purpose: StructureReadPurpose,
        idempotency_key: IdempotencyKey,
    ) -> ScopeStateAssertion:
        caller_ref = _text(caller_ref, "Structure read caller ref")
        _require_task_boundary(
            task_boundary,
            scope_id=scope_id,
            purpose=purpose,
        )
        assertion = self._scopes.read_scope_state_assertion(
            scope_id=scope_id,
            expected_revision=scope_revision,
            purpose=ScopePurpose.KNOWLEDGE_USE,
            caller_ref=caller_ref,
            request_ref=f"structure-read-session:{idempotency_key.value}",
            classification=task_boundary.classification,
        )
        _require_scope_assertion(
            assertion,
            scope_id=scope_id,
            scope_revision=scope_revision,
            task_boundary=task_boundary,
            caller_ref=caller_ref,
        )
        if not self._scopes.validate_scope_state_assertion(assertion):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "Structure read Scope authorization is no longer current",
                {"reason_code": "READ_SESSION_SCOPE_AUTHORIZATION_STALE"},
            )
        return assertion

    def _read_exact_binding(
        self, snapshot_id: StableId
    ) -> StructureSnapshotReadBinding:
        snapshot = self._snapshots.get_snapshot(snapshot_id)
        if not isinstance(snapshot, StructureSnapshot):
            raise _invalid(
                "READ_SET_SNAPSHOT_RECORD_REQUIRED",
                "exact Snapshot lookup did not return a Structure Snapshot",
            )
        if snapshot.snapshot_id != snapshot_id:
            raise _invalid(
                "READ_SET_SNAPSHOT_ID_MISMATCH",
                "exact Snapshot lookup returned another Snapshot",
            )
        if snapshot.manifest_digest != structure_snapshot_manifest_digest(snapshot):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "exact Structure Snapshot manifest does not verify",
            )
        coverages: list[StructureCoverageReadBinding] = []
        for reference in snapshot.coverages:
            record = self._snapshots.get_coverage(
                snapshot.snapshot_id, reference.coverage_root_id
            )
            if (
                record.root.coverage_root_id != reference.coverage_root_id
                or record.state.coverage_state_id != reference.coverage_state_id
                or record.state.coverage_state_digest
                != reference.coverage_state_digest
            ):
                raise _invalid(
                    "READ_SET_COVERAGE_REFERENCE_MISMATCH",
                    "exact Snapshot Coverage reference resolved to another State",
                )
            if record.root.owning_scope_id != snapshot.scope_id:
                raise _invalid(
                    "READ_SET_COVERAGE_SCOPE_MISMATCH",
                    "exact Snapshot Coverage belongs to another Scope",
                )
            coverages.append(StructureCoverageReadBinding.from_record(record))
        return StructureSnapshotReadBinding.create(
            snapshot=snapshot,
            coverages=tuple(coverages),
        )

    def _revalidate(
        self,
        session: StructureReadSession,
        *,
        expected_task_boundary: TaskBoundary | None = None,
        expected_scope_assertion: ScopeStateAssertion | None = None,
    ) -> StructureReadSession:
        session.require_valid()
        if (
            expected_task_boundary is not None
            and session.task_boundary != expected_task_boundary
        ):
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "Structure read Session belongs to another Task Boundary",
            )
        if (
            expected_scope_assertion is not None
            and session.scope_assertion != expected_scope_assertion
        ):
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "Structure read Session belongs to another Scope authorization",
            )
        if not self._scopes.validate_scope_state_assertion(session.scope_assertion):
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "persisted Structure read Session Scope authorization is no longer current",
                {"reason_code": "READ_SESSION_SCOPE_AUTHORIZATION_STALE"},
            )
        current_bindings = tuple(
            self._read_exact_binding(item.snapshot_id) for item in session.snapshots
        )
        if current_bindings != session.snapshots:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "persisted Structure read Session no longer matches exact Snapshot authority",
            )
        return session

    def _now(self) -> datetime:
        now = self._clock()
        if now.tzinfo is None or now.utcoffset() is None:
            raise _invalid(
                "READ_SESSION_TIMEZONE_REQUIRED",
                "Structure read Session clock must return a timezone-aware value",
            )
        return now.astimezone(timezone.utc)


def structure_read_session_request_digest(
    *,
    scope_id: StableId,
    scope_revision: Revision,
    task_boundary: TaskBoundary,
    scope_assertion: ScopeStateAssertion,
    caller_ref: str,
    purpose: StructureReadPurpose,
    selection_mode: StructureReadSelectionMode,
    snapshot_ids: tuple[StableId, ...],
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_READ_SESSION_REQUEST@1",
            {
                "scope_id": scope_id.value,
                "scope_revision": scope_revision.value,
                "task_boundary_digest": task_boundary.digest.value,
                "scope_assertion_id": scope_assertion.assertion_id.value,
                "scope_assertion_digest": scope_assertion.digest.value,
                "scope_assertion_purpose": scope_assertion.purpose.value,
                "caller_ref": caller_ref,
                "purpose": purpose.value,
                "selection_mode": selection_mode.value,
                "snapshot_ids": tuple(item.value for item in snapshot_ids),
            },
        ]
    )


def structure_ordered_read_set_digest(
    snapshots: tuple[StructureSnapshotReadBinding, ...],
    comparisons: tuple[StructureContextComparisonAssessment, ...],
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_ORDERED_READ_SET@1",
            {
                "snapshots": tuple(
                    {
                        "ordinal": ordinal,
                        "snapshot_id": item.snapshot_id.value,
                        "snapshot_manifest_digest": item.snapshot_manifest_digest.value,
                        "binding_digest": item.digest.value,
                    }
                    for ordinal, item in enumerate(snapshots)
                ),
                "context_comparisons": tuple(
                    {
                        "ordinal": item.ordinal,
                        "assessment_id": item.assessment_id.value,
                        "assessment_digest": item.digest.value,
                    }
                    for item in comparisons
                ),
            },
        ]
    )


def structure_read_session_digest(
    *,
    session_id: StableId,
    request_digest: Digest,
    scope_id: StableId,
    scope_revision: Revision,
    task_boundary: TaskBoundary,
    scope_assertion: ScopeStateAssertion,
    caller_ref: str,
    purpose: StructureReadPurpose,
    selection_mode: StructureReadSelectionMode,
    order: StructureReadOrder,
    read_set_digest: Digest,
    opened_at: datetime,
) -> Digest:
    return digest_of(
        [
            "STRUCTURE_READ_SESSION@1",
            {
                "session_id": session_id.value,
                "request_digest": request_digest.value,
                "scope_id": scope_id.value,
                "scope_revision": scope_revision.value,
                "task_boundary_digest": task_boundary.digest.value,
                "scope_assertion_id": scope_assertion.assertion_id.value,
                "scope_assertion_digest": scope_assertion.digest.value,
                "caller_ref": caller_ref,
                "purpose": purpose.value,
                "selection_mode": selection_mode.value,
                "order": order.value,
                "read_set_digest": read_set_digest.value,
                "opened_at": opened_at,
            },
        ]
    )


def _coverage_comparison_basis_digest(record: CoverageRecord) -> Digest:
    root = record.root
    return digest_of(
        [
            "STRUCTURE_COVERAGE_COMPARISON_BASIS@1",
            {
                "coverage_root_id": root.coverage_root_id.value,
                "coverage_root_digest": root.allocation_key_digest.value,
                "coverage_root_ref": root.coverage_root_ref,
                "profile_ref": root.profile_ref,
                "schema_ref": root.schema_ref,
                "schema_digest": root.schema_digest.value,
                "source_binding_id": root.source_binding_id.value,
                "logical_reactor_root": root.logical_reactor_root,
                "evaluation_context_ref": root.maven_evaluation_context_ref,
                "evaluation_context_digest": (
                    root.maven_evaluation_context_digest.value
                ),
                "canonicalization_ref": root.canonicalization_ref,
                "canonicalization_digest": root.canonicalization_digest.value,
            },
        ]
    )


def _context_comparisons(
    snapshots: tuple[StructureSnapshotReadBinding, ...],
    *,
    purpose: StructureReadPurpose,
    service: StructureContextComparisonService | None = None,
) -> tuple[StructureContextComparisonAssessment, ...]:
    if len(snapshots) < 2:
        return ()
    if purpose is not StructureReadPurpose.SNAPSHOT_COMPARISON:
        raise _invalid(
            "READ_SET_COMPARISON_PURPOSE_INVALID",
            "a multi-Snapshot read set requires the comparison purpose",
        )
    assessment_service = service or StructureContextComparisonService()
    inputs = tuple(_context_comparison_input(item) for item in snapshots)
    return tuple(
        assessment_service.assess(
            ordinal=ordinal,
            purpose=purpose.value,
            base=base,
            target=target,
        )
        for ordinal, (base, target) in enumerate(zip(inputs, inputs[1:]))
    )


def _context_comparison_input(
    snapshot: StructureSnapshotReadBinding,
) -> StructureContextComparisonInput:
    snapshot.require_valid()
    value = StructureContextComparisonInput(
        scope_id=snapshot.scope_id,
        snapshot_id=snapshot.snapshot_id,
        snapshot_binding_digest=snapshot.digest,
        schema_ref=snapshot.schema_ref,
        schema_digest=snapshot.schema_digest,
        coverages=tuple(
            StructureContextComparisonCoverageInput(
                coverage_root_id=item.coverage_root_id,
                knowledge_context_digest=item.knowledge_context_digest,
                comparison_basis_digest=item.comparison_basis_digest,
            )
            for item in snapshot.coverages
        ),
    )
    value.require_valid()
    return value


def _require_task_boundary(
    boundary: TaskBoundary,
    *,
    scope_id: StableId,
    purpose: StructureReadPurpose,
) -> None:
    if not isinstance(boundary, TaskBoundary):
        raise _invalid(
            "READ_SESSION_TASK_BOUNDARY_REQUIRED",
            "Structure read Session requires a typed Task Boundary",
        )
    expected = TaskBoundary.create(
        task_id=boundary.task_id,
        task_revision=boundary.task_revision,
        scope_id=boundary.scope_id,
        purpose=boundary.purpose,
        classification=boundary.classification,
    )
    if boundary != expected:
        raise _invalid(
            "READ_SESSION_TASK_BOUNDARY_INVALID",
            "Structure read Task Boundary is not canonical",
        )
    if boundary.scope_id != scope_id:
        raise _invalid(
            "READ_SESSION_TASK_SCOPE_MISMATCH",
            "Structure read Task Boundary belongs to another Scope",
        )
    if boundary.purpose != purpose.value:
        raise _invalid(
            "READ_SESSION_TASK_PURPOSE_MISMATCH",
            "Structure read Task Boundary has the wrong purpose",
        )


def _require_scope_assertion(
    assertion: ScopeStateAssertion,
    *,
    scope_id: StableId,
    scope_revision: Revision,
    task_boundary: TaskBoundary,
    caller_ref: str,
) -> None:
    if not isinstance(assertion, ScopeStateAssertion) or not assertion.verify_digest():
        raise _invalid(
            "READ_SESSION_SCOPE_ASSERTION_INVALID",
            "Structure read Scope assertion is not canonical",
        )
    if (
        assertion.scope_id != scope_id
        or assertion.definition_revision != scope_revision
        or assertion.purpose is not ScopePurpose.KNOWLEDGE_USE
        or assertion.lifecycle is not ScopeLifecycle.ACTIVE
        or assertion.outcome is not AssertionOutcome.ELIGIBLE
        or assertion.caller_ref != caller_ref
        or assertion.classification != task_boundary.classification
    ):
        raise _invalid(
            "READ_SESSION_SCOPE_ASSERTION_MISMATCH",
            "Structure read Scope assertion does not match the Task authorization closure",
        )


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise _invalid("READ_SET_TEXT_INVALID", f"{label} must be canonical text")
    return value


def _invalid(reason_code: str, message: str) -> DomainError:
    return DomainError(
        ErrorCode.INVALID_ARGUMENT,
        message,
        {"reason_code": reason_code},
    )


__all__ = [
    "StructureContextComparisonAssessment",
    "StructureContextComparisonOutcome",
    "StructureCoverageReadBinding",
    "StructureReadOrder",
    "StructureReadPurpose",
    "StructureReadSelectionMode",
    "StructureReadSession",
    "StructureReadSessionRepository",
    "StructureReadSessionService",
    "StructureSnapshotReadBinding",
    "StructureSnapshotReadSource",
    "structure_ordered_read_set_digest",
    "structure_read_session_digest",
    "structure_read_session_request_digest",
]
