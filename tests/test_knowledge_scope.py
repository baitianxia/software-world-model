from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
)
from software_world_model.infrastructure import SqliteDatabase, SqliteKnowledgeScopeRepository
from software_world_model.knowledge_engine import (
    AssertionOutcome,
    KnowledgeScopeService,
    ScopeLifecycle,
    ScopePurpose,
    ScopeType,
)


class SequenceIds:
    def __init__(self, *, fixed_outbox: str | None = None) -> None:
        self._next = 1
        self._fixed_outbox = fixed_outbox

    def new(self, kind: str) -> StableId:
        if kind == "outbox_event" and self._fixed_outbox is not None:
            return StableId(self._fixed_outbox)
        value = self._next
        self._next += 1
        return StableId(f"{kind}_{value:032x}")


class StepClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 8, 6, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self._value
        self._value += timedelta(microseconds=1)
        return value


class OpenPublication:
    def has_open_publication(self, scope_id: StableId) -> bool:
        return True


class KnowledgeScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.repository = SqliteKnowledgeScopeRepository(
            self.database, id_generator=SequenceIds()
        )
        self.service = KnowledgeScopeService(self.repository, clock=StepClock())

    def tearDown(self) -> None:
        self.database.close()

    def create_scope(self, *, key: str = "scope-create-1", name: str = "Mall"):
        return self.service.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": name},
            idempotency_key=IdempotencyKey(key),
            actor="test-operator",
            reason="contract test",
            correlation_ref=CorrelationRef("test-run-1"),
        )

    def test_scope_lifecycle_is_append_only_and_assertions_bind_exact_revision(self) -> None:
        created = self.create_scope()
        self.assertEqual(created.definition_revision, Revision(1))
        self.assertEqual(created.lifecycle, ScopeLifecycle.ACTIVE)

        revised = self.service.update_scope_metadata(
            scope_id=created.scope_id,
            expected_revision=Revision(1),
            metadata={"display_name": "Mall Platform"},
            idempotency_key=IdempotencyKey("scope-update-1"),
            actor="test-operator",
            reason="rename",
            correlation_ref=CorrelationRef("test-run-1"),
        )
        assertion = self.service.read_scope_state_assertion(
            scope_id=created.scope_id,
            expected_revision=Revision(2),
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="source-integration",
            request_ref="binding-command-1",
            classification="INTERNAL",
        )
        self.assertEqual(assertion.outcome, AssertionOutcome.ELIGIBLE)
        self.assertEqual(assertion.definition_revision, Revision(2))
        self.assertTrue(assertion.verify_digest())

        retired = self.service.retire_scope(
            scope_id=created.scope_id,
            expected_revision=Revision(2),
            idempotency_key=IdempotencyKey("scope-retire-1"),
            actor="test-operator",
            reason="retire",
            correlation_ref=CorrelationRef("test-run-1"),
        )
        retired_assertion = self.service.read_scope_state_assertion(
            scope_id=created.scope_id,
            expected_revision=Revision(3),
            purpose=ScopePurpose.SNAPSHOT_PUBLICATION,
            caller_ref="publisher",
            request_ref="publication-1",
            classification="INTERNAL",
        )
        self.assertEqual(retired.lifecycle, ScopeLifecycle.RETIRED)
        self.assertEqual(retired_assertion.outcome, AssertionOutcome.INELIGIBLE)
        self.assertEqual(self.service.get_scope(created.scope_id, Revision(1)), created)
        self.assertEqual(len(self.service.list_outbox_events()), 3)

    def test_idempotent_replay_returns_original_revision_not_current_state(self) -> None:
        created = self.create_scope()
        self.service.update_scope_metadata(
            scope_id=created.scope_id,
            expected_revision=Revision(1),
            metadata={"display_name": "Changed"},
            idempotency_key=IdempotencyKey("scope-update-2"),
            actor="test-operator",
            reason="rename",
            correlation_ref=CorrelationRef("test-run-1"),
        )

        replay = self.create_scope()

        self.assertEqual(replay, created)
        self.assertEqual(replay.definition_revision, Revision(1))

    def test_assertion_read_replay_returns_the_original_exact_assertion(self) -> None:
        created = self.create_scope()
        arguments = {
            "scope_id": created.scope_id,
            "expected_revision": Revision(1),
            "purpose": ScopePurpose.BIND_CONFIGURATION,
            "caller_ref": "source-integration",
            "request_ref": "binding-command-retry",
            "classification": "INTERNAL",
        }

        first = self.service.read_scope_state_assertion(**arguments)
        replay = self.service.read_scope_state_assertion(**arguments)

        self.assertEqual(replay, first)
        with self.database.read() as connection:
            assertion_count = connection.execute(
                "SELECT COUNT(*) FROM knw_scope_assertions"
            ).fetchone()[0]
            read_count = connection.execute(
                "SELECT COUNT(*) FROM knw_scope_assertion_reads"
            ).fetchone()[0]
        self.assertEqual(assertion_count, 1)
        self.assertEqual(read_count, 1)

    def test_assertion_request_reference_cannot_move_to_a_new_revision(self) -> None:
        created = self.create_scope()
        arguments = {
            "scope_id": created.scope_id,
            "purpose": ScopePurpose.BIND_CONFIGURATION,
            "caller_ref": "source-integration",
            "request_ref": "binding-command-stable",
            "classification": "INTERNAL",
        }
        self.service.read_scope_state_assertion(
            expected_revision=Revision(1), **arguments
        )
        self.service.update_scope_metadata(
            scope_id=created.scope_id,
            expected_revision=Revision(1),
            metadata={"display_name": "Changed"},
            idempotency_key=IdempotencyKey("scope-update-after-assertion"),
            actor="test-operator",
            reason="change authority state",
            correlation_ref=CorrelationRef("test-run-1"),
        )

        with self.assertRaises(DomainError) as raised:
            self.service.read_scope_state_assertion(
                expected_revision=Revision(2), **arguments
            )

        self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

    def test_idempotency_key_cannot_change_meaning(self) -> None:
        self.create_scope()

        with self.assertRaises(DomainError) as raised:
            self.create_scope(name="Different")

        self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

    def test_stale_revision_fails_without_new_revision_or_outbox_event(self) -> None:
        created = self.create_scope()
        self.service.update_scope_metadata(
            scope_id=created.scope_id,
            expected_revision=Revision(1),
            metadata={"display_name": "Revision 2"},
            idempotency_key=IdempotencyKey("scope-update-3"),
            actor="test-operator",
            reason="rename",
            correlation_ref=CorrelationRef("test-run-1"),
        )

        with self.assertRaises(DomainError) as raised:
            self.service.update_scope_metadata(
                scope_id=created.scope_id,
                expected_revision=Revision(1),
                metadata={"display_name": "Stale"},
                idempotency_key=IdempotencyKey("scope-update-stale"),
                actor="test-operator",
                reason="stale",
                correlation_ref=CorrelationRef("test-run-1"),
            )

        self.assertEqual(raised.exception.code, ErrorCode.REVISION_CONFLICT)
        self.assertEqual(self.service.get_scope(created.scope_id).definition_revision, Revision(2))
        self.assertEqual(len(self.service.list_outbox_events()), 2)

    def test_concurrent_expected_revision_allows_exactly_one_writer(self) -> None:
        created = self.create_scope()

        def revise(index: int) -> str:
            try:
                self.service.update_scope_metadata(
                    scope_id=created.scope_id,
                    expected_revision=Revision(1),
                    metadata={"display_name": f"Writer {index}"},
                    idempotency_key=IdempotencyKey(f"concurrent-{index}"),
                    actor="test-operator",
                    reason="concurrency test",
                    correlation_ref=CorrelationRef("test-run-1"),
                )
                return "SUCCEEDED"
            except DomainError as error:
                return error.code.value

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(revise, (1, 2)))

        self.assertCountEqual(outcomes, ["SUCCEEDED", ErrorCode.REVISION_CONFLICT.value])
        self.assertEqual(self.service.get_scope(created.scope_id).definition_revision, Revision(2))

    def test_retirement_checks_open_publication_before_writing(self) -> None:
        created = self.create_scope()
        guarded = KnowledgeScopeService(
            self.repository, publication_activity=OpenPublication(), clock=StepClock()
        )

        with self.assertRaises(DomainError) as raised:
            guarded.retire_scope(
                scope_id=created.scope_id,
                expected_revision=Revision(1),
                idempotency_key=IdempotencyKey("retire-blocked"),
                actor="test-operator",
                reason="blocked",
                correlation_ref=CorrelationRef("test-run-1"),
            )

        self.assertEqual(raised.exception.code, ErrorCode.OPEN_PUBLICATION_ATTEMPT)
        self.assertEqual(self.service.get_scope(created.scope_id).lifecycle, ScopeLifecycle.ACTIVE)
        self.assertEqual(len(self.service.list_outbox_events()), 1)

    def test_outbox_failure_rolls_back_scope_and_idempotency(self) -> None:
        fixed_event = "outbox_event_00000000000000000000000000000001"
        database = SqliteDatabase()
        repository = SqliteKnowledgeScopeRepository(
            database, id_generator=SequenceIds(fixed_outbox=fixed_event)
        )
        service = KnowledgeScopeService(repository, clock=StepClock())
        first = service.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": "First"},
            idempotency_key=IdempotencyKey("first"),
            actor="test-operator",
            reason="seed event",
            correlation_ref=CorrelationRef("rollback-test"),
        )

        with self.assertRaises(DomainError) as raised:
            service.create_scope(
                scope_type=ScopeType.SYSTEM,
                metadata={"display_name": "Second"},
                idempotency_key=IdempotencyKey("second"),
                actor="test-operator",
                reason="force outbox collision",
                correlation_ref=CorrelationRef("rollback-test"),
            )

        self.assertEqual(raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT)
        self.assertEqual(len(service.list_outbox_events()), 1)
        self.assertEqual(service.get_scope(first.scope_id), first)
        database.close()

    def test_reopen_recovers_idempotent_result_and_outbox(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "swm.db"
            first_database = SqliteDatabase(path)
            first_repository = SqliteKnowledgeScopeRepository(
                first_database, id_generator=SequenceIds()
            )
            first_service = KnowledgeScopeService(first_repository, clock=StepClock())
            created = first_service.create_scope(
                scope_type=ScopeType.SYSTEM,
                metadata={"display_name": "Persistent"},
                idempotency_key=IdempotencyKey("persistent-create"),
                actor="test-operator",
                reason="recovery test",
                correlation_ref=CorrelationRef("recovery-test"),
            )
            first_database.close()

            second_database = SqliteDatabase(path)
            second_repository = SqliteKnowledgeScopeRepository(
                second_database, id_generator=SequenceIds()
            )
            second_service = KnowledgeScopeService(second_repository, clock=StepClock())
            replay = second_service.create_scope(
                scope_type=ScopeType.SYSTEM,
                metadata={"display_name": "Persistent"},
                idempotency_key=IdempotencyKey("persistent-create"),
                actor="test-operator",
                reason="recovery test",
                correlation_ref=CorrelationRef("recovery-test"),
            )

            self.assertEqual(replay, created)
            self.assertEqual(len(second_service.list_outbox_events()), 1)
            second_database.close()


if __name__ == "__main__":
    unittest.main()
