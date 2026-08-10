from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from software_world_model.application_services.knowledge_use import TaskBoundary
from software_world_model.application_services.structure_read_session import (
    StructureReadOrder,
    StructureReadPurpose,
    StructureReadSelectionMode,
    StructureReadSessionService,
    structure_read_session_digest,
)
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
from software_world_model.infrastructure.sqlite_database import SqliteDatabase
from software_world_model.infrastructure.sqlite_scope_repository import (
    SqliteKnowledgeScopeRepository,
)
from software_world_model.infrastructure.sqlite_structure_read_session_repository import (
    SqliteStructureReadSessionRepository,
)
from software_world_model.knowledge_engine.structure import (
    CompleteMemberManifest,
    CoverageRecord,
    CoverageRoot,
    CoverageState,
    PublicationMode,
)
from software_world_model.knowledge_engine.context_comparison import (
    StructureContextComparisonOutcome,
    StructureContextComparisonService,
)
from software_world_model.knowledge_engine.structure_authority import (
    StructureSchemaAdoptionMode,
)
from software_world_model.knowledge_engine.structure_publication import (
    SnapshotCoverage,
    StructureSnapshot,
)
from software_world_model.knowledge_engine.scope import (
    KnowledgeScopeService,
    ScopeType,
)


class SequenceIds:
    def __init__(self) -> None:
        self.value = 0

    def new(self, kind: str) -> StableId:
        self.value += 1
        return StableId(f"{kind}_{self.value:032x}")


class FrozenClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 10, 12, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value


class FakeStructureSnapshotSource:
    def __init__(self) -> None:
        self.snapshots: dict[StableId, StructureSnapshot] = {}
        self.coverages: dict[tuple[StableId, StableId], CoverageRecord] = {}
        self.current_by_scope: dict[StableId, StableId] = {}
        self.current_calls = 0
        self.exact_snapshot_calls = 0

    def add(
        self,
        snapshot: StructureSnapshot,
        coverages: tuple[CoverageRecord, ...],
        *,
        current: bool = False,
    ) -> None:
        self.snapshots[snapshot.snapshot_id] = snapshot
        for coverage in coverages:
            self.coverages[(snapshot.snapshot_id, coverage.root.coverage_root_id)] = (
                coverage
            )
        if current:
            self.current_by_scope[snapshot.scope_id] = snapshot.snapshot_id

    def move_current(self, snapshot: StructureSnapshot) -> None:
        self.current_by_scope[snapshot.scope_id] = snapshot.snapshot_id

    def current_snapshot(self, scope_id: StableId) -> StructureSnapshot | None:
        self.current_calls += 1
        snapshot_id = self.current_by_scope.get(scope_id)
        return self.snapshots.get(snapshot_id) if snapshot_id is not None else None

    def get_snapshot(self, snapshot_id: StableId) -> StructureSnapshot:
        self.exact_snapshot_calls += 1
        return self.snapshots[snapshot_id]

    def get_coverage(
        self, snapshot_id: StableId, coverage_root_id: StableId
    ) -> CoverageRecord:
        return self.coverages[(snapshot_id, coverage_root_id)]


class StructureReadSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.ids = SequenceIds()
        self.clock = FrozenClock()
        self.scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(self.database, id_generator=self.ids),
            clock=self.clock,
        )
        scope = self.scopes.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": "Structure read fixture"},
            idempotency_key=IdempotencyKey("structure-read-scope"),
            actor="test",
            reason="Structure read Session tests",
            correlation_ref=CorrelationRef("structure-read-session"),
        )
        self.repository = SqliteStructureReadSessionRepository(
            self.database, id_generator=self.ids
        )
        self.source = FakeStructureSnapshotSource()
        self.service = StructureReadSessionService(
            self.repository,
            self.source,
            self.scopes,
            StructureContextComparisonService(),
            clock=self.clock,
        )
        self.scope = scope.scope_id
        self.scope_revision = scope.definition_revision
        self.binding = StableId("binding_" + "2" * 32)
        self.schema_ref = "TEST-STRUCTURE@1"
        self.schema_digest = digest_of({"schema": self.schema_ref})
        self.a1, self.b, self.a2 = self._chain(self.scope)
        self.source.add(*self.a1)
        self.source.add(*self.b, current=True)
        self.source.add(*self.a2)

    def tearDown(self) -> None:
        self.database.close()

    def _boundary(
        self,
        purpose: StructureReadPurpose,
        *,
        classification: str = "INTERNAL",
        marker: str = "1",
        scope_id: StableId | None = None,
    ) -> TaskBoundary:
        return TaskBoundary.create(
            task_id=StableId("task_" + marker * 32),
            task_revision=Revision(1),
            scope_id=scope_id or self.scope,
            purpose=purpose.value,
            classification=classification,
        )

    def _open_current(
        self,
        key: str,
        *,
        boundary: TaskBoundary | None = None,
        caller_ref: str = "structure-read-test",
        scope_revision: Revision | None = None,
    ):
        return self.service.open_current(
            scope_id=self.scope,
            scope_revision=scope_revision or self.scope_revision,
            task_boundary=boundary
            or self._boundary(StructureReadPurpose.EXACT_SNAPSHOT),
            caller_ref=caller_ref,
            idempotency_key=IdempotencyKey(key),
        )

    def _open_ordered(
        self,
        snapshot_ids: tuple[StableId, ...],
        key: str,
        *,
        boundary: TaskBoundary | None = None,
        caller_ref: str = "structure-read-test",
        scope_revision: Revision | None = None,
    ):
        purpose = (
            StructureReadPurpose.EXACT_SNAPSHOT
            if len(snapshot_ids) == 1
            else StructureReadPurpose.SNAPSHOT_COMPARISON
        )
        return self.service.open_ordered(
            scope_id=self.scope,
            scope_revision=scope_revision or self.scope_revision,
            task_boundary=boundary or self._boundary(purpose),
            caller_ref=caller_ref,
            snapshot_ids=snapshot_ids,
            idempotency_key=IdempotencyKey(key),
        )

    def test_current_and_ordered_set_do_not_drift_after_a2(self) -> None:
        current_boundary = self._boundary(StructureReadPurpose.EXACT_SNAPSHOT)
        comparison_boundary = self._boundary(
            StructureReadPurpose.SNAPSHOT_COMPARISON
        )
        current_b = self._open_current(
            "read-current-after-b",
            boundary=current_boundary,
        )
        ordered_a1_b = self._open_ordered(
            (self.a1[0].snapshot_id, self.b[0].snapshot_id),
            "read-ordered-a1-b",
            boundary=comparison_boundary,
        )
        self.assertEqual(
            tuple(item.snapshot_id for item in current_b.snapshots),
            (self.b[0].snapshot_id,),
        )
        self.assertEqual(current_b.selection_mode, StructureReadSelectionMode.CURRENT)
        self.assertEqual(ordered_a1_b.order, StructureReadOrder.CALLER_DECLARED)
        self.assertEqual(self.source.current_calls, 1)

        self.source.move_current(self.a2[0])
        restarted_repository = SqliteStructureReadSessionRepository(self.database)
        restarted = StructureReadSessionService(
            restarted_repository,
            self.source,
            self.scopes,
            StructureContextComparisonService(),
            clock=self.clock,
        )

        self.assertEqual(restarted.get_session(current_b.session_id), current_b)
        self.assertEqual(restarted.get_session(ordered_a1_b.session_id), ordered_a1_b)
        self.assertEqual(
            restarted.open_current(
                scope_id=self.scope,
                scope_revision=self.scope_revision,
                task_boundary=current_boundary,
                caller_ref="structure-read-test",
                idempotency_key=IdempotencyKey("read-current-after-b"),
            ),
            current_b,
        )
        self.assertEqual(
            restarted.open_ordered(
                scope_id=self.scope,
                scope_revision=self.scope_revision,
                task_boundary=comparison_boundary,
                caller_ref="structure-read-test",
                snapshot_ids=(self.a1[0].snapshot_id, self.b[0].snapshot_id),
                idempotency_key=IdempotencyKey("read-ordered-a1-b"),
            ),
            ordered_a1_b,
        )
        self.assertEqual(self.source.current_calls, 1)

        current_a2 = restarted.open_current(
            scope_id=self.scope,
            scope_revision=self.scope_revision,
            task_boundary=current_boundary,
            caller_ref="structure-read-test",
            idempotency_key=IdempotencyKey("read-current-after-a2"),
        )
        self.assertEqual(current_a2.snapshots[0].snapshot_id, self.a2[0].snapshot_id)
        self.assertEqual(self.source.current_calls, 2)

    def test_ordered_set_rejects_wrong_scope(self) -> None:
        other_scope = StableId("scope_" + "9" * 32)
        other = self._snapshot(
            scope_id=other_scope,
            marker="f",
            revision=Revision(1),
        )
        self.source.add(*other)

        with self.assertRaises(DomainError) as raised:
            self._open_ordered(
                (self.a1[0].snapshot_id, other[0].snapshot_id),
                "read-cross-scope",
            )
        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)
        self.assertEqual(
            raised.exception.details["reason_code"], "READ_SET_SCOPE_MISMATCH"
        )

    def test_ordered_set_preserves_caller_declared_reverse_order(self) -> None:
        session = self._open_ordered(
            (self.b[0].snapshot_id, self.a1[0].snapshot_id),
            "read-reversed",
        )

        self.assertEqual(
            tuple(item.snapshot_id for item in session.snapshots),
            (self.b[0].snapshot_id, self.a1[0].snapshot_id),
        )
        self.assertEqual(session.order, StructureReadOrder.CALLER_DECLARED)
        self.assertEqual(len(session.context_comparisons), 1)
        self.assertEqual(
            session.context_comparisons[0].base_snapshot_id,
            self.b[0].snapshot_id,
        )
        self.assertEqual(
            session.context_comparisons[0].target_snapshot_id,
            self.a1[0].snapshot_id,
        )

    def test_ordered_set_rejects_schema_mismatch(self) -> None:
        alternate = self._snapshot(
            scope_id=self.scope,
            marker="d",
            revision=Revision(2),
            previous_snapshot_id=self.a1[0].snapshot_id,
            schema_ref="OTHER-STRUCTURE@1",
            schema_digest=digest_of({"schema": "other"}),
        )
        self.source.add(*alternate)

        with self.assertRaises(DomainError) as raised:
            self._open_ordered(
                (self.a1[0].snapshot_id, alternate[0].snapshot_id),
                "read-schema-drift",
            )
        self.assertEqual(
            raised.exception.details["reason_code"], "READ_SET_SCHEMA_INCOMPARABLE"
        )

    def test_ordered_set_rejects_definition_basis_drift(self) -> None:
        alternate = self._snapshot(
            scope_id=self.scope,
            marker="e",
            revision=Revision(2),
            previous_snapshot_id=self.a1[0].snapshot_id,
            evaluation_context_digest=digest_of({"evaluation": "changed"}),
        )
        self.source.add(*alternate)

        with self.assertRaises(DomainError) as raised:
            self._open_ordered(
                (self.a1[0].snapshot_id, alternate[0].snapshot_id),
                "read-definition-drift",
            )
        self.assertEqual(
            raised.exception.details["reason_code"], "READ_SET_COVERAGE_INCOMPARABLE"
        )

    def test_different_knowledge_contexts_compare_under_same_frozen_basis(self) -> None:
        session = self._open_ordered(
            (self.a1[0].snapshot_id, self.b[0].snapshot_id),
            "read-context-assessment",
        )

        self.assertEqual(len(session.context_comparisons), 1)
        assessment = session.context_comparisons[0]
        self.assertEqual(
            assessment.outcome,
            StructureContextComparisonOutcome.COMPATIBLE,
        )
        self.assertNotEqual(
            assessment.base_knowledge_context_digests,
            assessment.target_knowledge_context_digests,
        )
        self.assertEqual(
            assessment.base_knowledge_context_digests,
            tuple(
                item.knowledge_context_digest for item in session.snapshots[0].coverages
            ),
        )
        self.assertEqual(
            assessment.target_knowledge_context_digests,
            tuple(
                item.knowledge_context_digest for item in session.snapshots[1].coverages
            ),
        )
        self.assertEqual(
            assessment.comparison_basis_digests,
            tuple(
                item.comparison_basis_digest for item in session.snapshots[0].coverages
            ),
        )
        self.assertEqual(self.repository.get_session(session.session_id), session)

    def test_idempotency_key_is_bound_to_selection_and_exact_order(self) -> None:
        self._open_ordered(
            (self.a1[0].snapshot_id, self.b[0].snapshot_id),
            "read-idempotency-bound",
        )

        with self.assertRaises(DomainError) as raised:
            self._open_ordered(
                (self.b[0].snapshot_id, self.a2[0].snapshot_id),
                "read-idempotency-bound",
            )
        self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

    def test_persisted_manifest_tamper_is_detected(self) -> None:
        session = self._open_current("read-db-tamper")
        with self.database.transaction() as connection:
            connection.execute(
                """UPDATE app_structure_read_session_snapshots
                   SET snapshot_manifest_digest = ?
                   WHERE session_id = ? AND ordinal = 0""",
                (digest_of({"tampered": True}).value, session.session_id.value),
            )

        with self.assertRaises(DomainError) as raised:
            self.repository.get_session(session.session_id)
        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )

    def test_persisted_context_assessment_is_rebuilt_by_knowledge_owner(self) -> None:
        session = self._open_ordered(
            (self.a1[0].snapshot_id, self.b[0].snapshot_id),
            "read-context-assessment-tamper",
        )
        with self.database.transaction() as connection:
            connection.execute(
                """UPDATE app_structure_read_session_context_comparisons
                   SET assessment_digest = ?
                   WHERE session_id = ? AND ordinal = 0""",
                (digest_of({"tampered": "assessment"}).value, session.session_id.value),
            )

        with self.assertRaises(DomainError) as raised:
            self.repository.get_session(session.session_id)
        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )

    def test_coordinated_request_and_session_rehash_is_detected(self) -> None:
        session = self._open_ordered(
            (self.a1[0].snapshot_id, self.b[0].snapshot_id),
            "read-coordinated-rehash",
        )
        forged_request_digest = digest_of({"forged": "request"})
        forged_session_digest = structure_read_session_digest(
            session_id=session.session_id,
            request_digest=forged_request_digest,
            scope_id=session.scope_id,
            scope_revision=session.scope_revision,
            task_boundary=session.task_boundary,
            scope_assertion=session.scope_assertion,
            caller_ref=session.caller_ref,
            purpose=session.purpose,
            selection_mode=session.selection_mode,
            order=session.order,
            read_set_digest=session.read_set_digest,
            opened_at=session.opened_at,
        )
        with self.database.transaction() as connection:
            connection.execute(
                """UPDATE app_structure_read_sessions
                   SET request_digest = ?, session_digest = ?
                   WHERE session_id = ?""",
                (
                    forged_request_digest.value,
                    forged_session_digest.value,
                    session.session_id.value,
                ),
            )

        with self.assertRaises(DomainError) as raised:
            self.repository.get_session(session.session_id)
        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )

    def test_scope_metadata_revision_invalidates_persisted_session(self) -> None:
        session = self._open_current("read-stale-scope-assertion")
        self.scopes.update_scope_metadata(
            scope_id=self.scope,
            expected_revision=self.scope_revision,
            metadata={"display_name": "Revised Structure read fixture"},
            idempotency_key=IdempotencyKey("structure-read-scope-revise"),
            actor="test",
            reason="Invalidate the persisted read authorization",
            correlation_ref=CorrelationRef("structure-read-session"),
        )

        with self.assertRaises(DomainError) as raised:
            self.service.get_session(session.session_id)
        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(
            raised.exception.details["reason_code"],
            "READ_SESSION_SCOPE_AUTHORIZATION_STALE",
        )

    def test_retired_scope_invalidates_persisted_session_and_replay(self) -> None:
        session = self._open_current("read-retired-scope")
        self.scopes.retire_scope(
            scope_id=self.scope,
            expected_revision=self.scope_revision,
            idempotency_key=IdempotencyKey("structure-read-scope-retire"),
            actor="test",
            reason="Retire the read Scope",
            correlation_ref=CorrelationRef("structure-read-session"),
        )

        with self.assertRaises(DomainError) as raised:
            self.service.get_session(session.session_id)
        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)

        with self.assertRaises(DomainError) as replay_raised:
            self._open_current("read-retired-scope")
        self.assertEqual(replay_raised.exception.code, ErrorCode.REVISION_CONFLICT)

    def test_task_scope_purpose_and_assertion_classification_must_match(self) -> None:
        with self.assertRaises(DomainError) as wrong_scope:
            self._open_current(
                "read-wrong-task-scope",
                boundary=self._boundary(
                    StructureReadPurpose.EXACT_SNAPSHOT,
                    scope_id=StableId("scope_" + "8" * 32),
                ),
            )
        self.assertEqual(
            wrong_scope.exception.details["reason_code"],
            "READ_SESSION_TASK_SCOPE_MISMATCH",
        )

        with self.assertRaises(DomainError) as wrong_purpose:
            self._open_current(
                "read-wrong-task-purpose",
                boundary=self._boundary(
                    StructureReadPurpose.SNAPSHOT_COMPARISON,
                ),
            )
        self.assertEqual(
            wrong_purpose.exception.details["reason_code"],
            "READ_SESSION_TASK_PURPOSE_MISMATCH",
        )

        session = self._open_current("read-wrong-task-classification")
        other_classification = self._boundary(
            StructureReadPurpose.EXACT_SNAPSHOT,
            classification="SECRET",
        )
        with self.assertRaises(DomainError) as wrong_classification:
            replace(session, task_boundary=other_classification).require_valid()
        self.assertEqual(
            wrong_classification.exception.details["reason_code"],
            "READ_SESSION_SCOPE_ASSERTION_MISMATCH",
        )

    def test_exact_snapshot_authority_drift_is_detected(self) -> None:
        session = self._open_ordered(
            (self.a1[0].snapshot_id, self.b[0].snapshot_id),
            "read-source-tamper",
        )
        original = self.source.snapshots[self.b[0].snapshot_id]
        tampered = StructureSnapshot.create(
            snapshot_id=original.snapshot_id,
            scope_id=original.scope_id,
            snapshot_revision=original.snapshot_revision,
            previous_snapshot_id=original.previous_snapshot_id,
            schema_ref=original.schema_ref,
            schema_digest=original.schema_digest,
            schema_adoption_mode=original.schema_adoption_mode,
            schema_registration_digest=original.schema_registration_digest,
            schema_availability_digest=original.schema_availability_digest,
            schema_adoption_digest=original.schema_adoption_digest,
            publication_mode=original.publication_mode,
            members=original.members,
            coverages=original.coverages,
            upstream_entities=original.upstream_entities,
            published_at=original.published_at + timedelta(seconds=1),
        )
        # A second, internally canonical record under the same exact ID must
        # still fail against the Session's pinned manifest.
        self.source.snapshots[original.snapshot_id] = tampered

        with self.assertRaises(DomainError) as raised:
            self.service.get_session(session.session_id)
        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )

    def test_persistence_contains_no_evidence_or_source_payload_columns(self) -> None:
        self._open_current("read-no-payload")
        with self.database.read() as connection:
            tables = (
                "app_structure_read_sessions",
                "app_structure_read_session_snapshots",
                "app_structure_read_session_coverages",
                "app_structure_read_session_context_comparisons",
            )
            columns = {
                row["name"]
                for table in tables
                for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
            }
        self.assertTrue(
            {
                "snapshot_manifest_digest",
                "member_manifest_digest",
                "knowledge_context_digest",
            }
            <= columns
        )
        self.assertFalse(
            {"evidence", "excerpt", "observation", "artifact_bytes", "source_bytes"}
            & columns
        )

    def _chain(
        self, scope_id: StableId
    ) -> tuple[
        tuple[StructureSnapshot, tuple[CoverageRecord, ...]],
        tuple[StructureSnapshot, tuple[CoverageRecord, ...]],
        tuple[StructureSnapshot, tuple[CoverageRecord, ...]],
    ]:
        a1 = self._snapshot(scope_id=scope_id, marker="a", revision=Revision(1))
        b = self._snapshot(
            scope_id=scope_id,
            marker="b",
            revision=Revision(2),
            previous_snapshot_id=a1[0].snapshot_id,
        )
        a2 = self._snapshot(
            scope_id=scope_id,
            marker="c",
            revision=Revision(3),
            previous_snapshot_id=b[0].snapshot_id,
        )
        return a1, b, a2

    def _snapshot(
        self,
        *,
        scope_id: StableId,
        marker: str,
        revision: Revision,
        previous_snapshot_id: StableId | None = None,
        schema_ref: str | None = None,
        schema_digest: Digest | None = None,
        evaluation_context_digest: Digest | None = None,
    ) -> tuple[StructureSnapshot, tuple[CoverageRecord, ...]]:
        actual_schema_ref = schema_ref or self.schema_ref
        actual_schema_digest = schema_digest or self.schema_digest
        root = CoverageRoot.create(
            owning_scope_id=scope_id,
            source_binding_id=self.binding,
            logical_reactor_root="pom.xml",
            profile_ref="TEST_STRUCTURE@1",
            schema_ref=actual_schema_ref,
            schema_digest=actual_schema_digest,
            maven_evaluation_context_ref="TEST-EVALUATION@1",
            maven_evaluation_context_digest=(
                evaluation_context_digest or digest_of({"evaluation": 1})
            ),
            canonicalization_ref="TEST-CANONICALIZATION@1",
            canonicalization_digest=digest_of({"canonicalization": 1}),
            coverage_root_ref="TEST_STRUCTURE_COVERAGE@1",
        )
        state = CoverageState.create(
            root=root,
            source_revision=f"revision-{marker}",
            knowledge_context_digest=digest_of({"revision": marker}),
            complete_member_manifest=CompleteMemberManifest.create(()),
            evidence_references=(),
        )
        coverage = CoverageRecord(root, state)
        snapshot = StructureSnapshot.create(
            snapshot_id=StableId("structure_snapshot_" + marker * 32),
            scope_id=scope_id,
            snapshot_revision=revision,
            previous_snapshot_id=previous_snapshot_id,
            schema_ref=actual_schema_ref,
            schema_digest=actual_schema_digest,
            schema_adoption_mode=(
                StructureSchemaAdoptionMode.INITIAL
                if previous_snapshot_id is None
                else StructureSchemaAdoptionMode.UNCHANGED
            ),
            schema_registration_digest=digest_of(
                {"registration": actual_schema_ref}
            ),
            schema_availability_digest=digest_of(
                {"availability": actual_schema_ref}
            ),
            schema_adoption_digest=digest_of(
                {"adoption": scope_id.value, "schema": actual_schema_ref}
            ),
            publication_mode=PublicationMode.REPLACE_COVERAGE,
            members=(),
            coverages=(
                SnapshotCoverage(
                    coverage_root_id=root.coverage_root_id,
                    coverage_state_id=state.coverage_state_id,
                    coverage_state_digest=state.coverage_state_digest,
                ),
            ),
            upstream_entities=(),
            published_at=datetime(2026, 8, 10, 10, revision.value, tzinfo=timezone.utc),
        )
        return snapshot, (coverage,)


if __name__ == "__main__":
    unittest.main()
