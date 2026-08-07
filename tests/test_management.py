from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from software_world_model.application_services import (
    ConfigureSystemSourceCommand,
    ManagementApplicationService,
    ManagementAttemptState,
    ManagementStepState,
    OwnerOutcomePending,
)
from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    StableId,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteKnowledgeScopeRepository,
    SqliteManagementRepository,
    SqliteSourceConfigurationRepository,
)
from software_world_model.knowledge_engine import KnowledgeScopeService, ScopeType
from software_world_model.source_integration import (
    NormalizedDataSource,
    NormalizedSelection,
    ProviderRegistry,
    SourceConfigurationService,
    canonical_fields,
)


class SequenceIds:
    def __init__(self) -> None:
        self._next = 1

    def new(self, kind: str) -> StableId:
        current = self._next
        self._next += 1
        return StableId(f"{kind}_{current:032x}")


class StepClock:
    def __init__(self) -> None:
        self._value = datetime(2026, 8, 6, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        value = self._value
        self._value += timedelta(microseconds=1)
        return value


class LocalGitConfigurationProvider:
    provider_type = "LOCAL_GIT"
    contract_version = "0.1.0"

    def normalize_data_source(
        self,
        *,
        identity_domain: str,
        source_target: str,
        provider_configuration: dict[str, str],
        secret_reference: str | None,
    ) -> NormalizedDataSource:
        return NormalizedDataSource(
            identity_strategy_version="local-git-path@1",
            identity_domain=identity_domain.strip().casefold(),
            canonical_source_target=source_target.rstrip("/") or "/",
            provider_configuration=canonical_fields(
                provider_configuration, label="local git configuration", reject_credentials=True
            ),
            secret_reference=secret_reference,
        )

    def normalize_selection(
        self, *, selector: dict[str, str], context_constraint: dict[str, str]
    ) -> NormalizedSelection:
        return NormalizedSelection(
            selector=canonical_fields(selector, label="local git selector"),
            context_constraint=canonical_fields(
                context_constraint, label="local git context constraint"
            ),
        )


class FailFirstSourceService:
    def __init__(self, delegate: SourceConfigurationService) -> None:
        self._delegate = delegate
        self.failed = False

    def register_data_source(self, **arguments: object):
        if not self.failed:
            self.failed = True
            raise DomainError(ErrorCode.PROVIDER_CONTRACT_UNAVAILABLE, "temporary provider failure")
        return self._delegate.register_data_source(**arguments)

    def __getattr__(self, name: str):
        return getattr(self._delegate, name)


class PendingOnceScopeService:
    def __init__(self, delegate: KnowledgeScopeService) -> None:
        self._delegate = delegate
        self.pending = False

    def create_scope(self, **arguments: object):
        result = self._delegate.create_scope(**arguments)
        if not self.pending:
            self.pending = True
            raise OwnerOutcomePending("scope response was lost after dispatch")
        return result

    def __getattr__(self, name: str):
        return getattr(self._delegate, name)


class PendingOnceBindingService:
    def __init__(self, delegate: SourceConfigurationService) -> None:
        self._delegate = delegate
        self.pending = False

    def bind_source_to_scope(self, **arguments: object):
        result = self._delegate.bind_source_to_scope(**arguments)
        if not self.pending:
            self.pending = True
            raise OwnerOutcomePending("binding response was lost after dispatch")
        return result

    def __getattr__(self, name: str):
        return getattr(self._delegate, name)


class ManagementTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.clock = StepClock()
        self.scope_repository = SqliteKnowledgeScopeRepository(
            self.database, id_generator=SequenceIds()
        )
        self.scope_service = KnowledgeScopeService(self.scope_repository, clock=self.clock)
        self.source_repository = SqliteSourceConfigurationRepository(
            self.database, id_generator=SequenceIds()
        )
        self.source_service = SourceConfigurationService(
            self.source_repository,
            ProviderRegistry((LocalGitConfigurationProvider(),)),
            self.scope_service,
            clock=self.clock,
        )
        self.management_repository = SqliteManagementRepository(
            self.database, id_generator=SequenceIds()
        )
        self.management = ManagementApplicationService(
            self.management_repository,
            self.scope_service,
            self.source_service,
            clock=self.clock,
        )

    def tearDown(self) -> None:
        self.database.close()

    def command(self, *, key: str = "configure-mall", target: str = "/projects/mall"):
        return ConfigureSystemSourceCommand.create(
            idempotency_key=IdempotencyKey(key),
            caller="cli:test",
            purpose="configure source",
            classification="INTERNAL",
            request_context={"request": "test"},
            scope_type=ScopeType.SYSTEM,
            scope_metadata={"display_name": "Mall"},
            provider_type="LOCAL_GIT",
            provider_contract_version="0.1.0",
            identity_domain="LOCAL",
            source_target=target,
            provider_configuration={"read_mode": "read_only"},
            secret_reference=None,
            selector={"paths": "src"},
            context_constraint={"revision_policy": "exact"},
            context_hint="mall source",
            actor="test-operator",
            reason="management test",
            correlation_ref=CorrelationRef("management-test"),
        )

    def test_composite_command_succeeds_and_replay_returns_same_attempt(self) -> None:
        first = self.management.configure(self.command())
        replay = self.management.configure(self.command())

        self.assertEqual(first.attempt.state, ManagementAttemptState.SUCCEEDED)
        self.assertTrue(
            all(step.state is ManagementStepState.SUCCEEDED for step in first.result.steps)
        )
        self.assertEqual(replay.attempt.attempt_id, first.attempt.attempt_id)
        self.assertEqual(replay.result.result_id, first.result.result_id)
        self.assertEqual(replay.result.revision, first.result.revision)

    def test_partial_success_is_preserved_then_same_steps_resume(self) -> None:
        flaky = FailFirstSourceService(self.source_service)
        service = ManagementApplicationService(
            self.management_repository, self.scope_service, flaky, clock=self.clock
        )
        partial = service.configure(self.command())

        self.assertEqual(partial.attempt.state, ManagementAttemptState.PARTIALLY_SUCCEEDED)
        self.assertEqual(partial.result.steps[0].state, ManagementStepState.SUCCEEDED)
        self.assertEqual(partial.result.steps[1].state, ManagementStepState.FAILED)
        scope_id = StableId(dict(partial.result.steps[0].output)["scope_id"])
        self.assertEqual(self.scope_service.get_scope(scope_id).scope_id, scope_id)

        recovered = service.execute(partial.attempt.attempt_id)
        self.assertEqual(recovered.attempt.state, ManagementAttemptState.SUCCEEDED)
        self.assertEqual(recovered.result.steps[0].dispatch_attempt, 1)
        self.assertEqual(recovered.result.steps[1].dispatch_attempt, 2)

    def test_cancel_before_dispatch_cancels_every_step(self) -> None:
        prepared = self.management.prepare(self.command())
        canceled = self.management.cancel(prepared.attempt.attempt_id, reason="operator request")

        self.assertEqual(canceled.attempt.state, ManagementAttemptState.CANCELED)
        self.assertTrue(canceled.attempt.cancel_requested)
        self.assertTrue(
            all(
                step.state is ManagementStepState.CANCELED_BEFORE_DISPATCH
                for step in canceled.result.steps
            )
        )

    def test_unknown_scope_outcome_recovers_same_owner_operation(self) -> None:
        pending_scopes = PendingOnceScopeService(self.scope_service)
        service = ManagementApplicationService(
            self.management_repository, pending_scopes, self.source_service, clock=self.clock
        )
        pending = service.configure(self.command())

        self.assertEqual(pending.attempt.state, ManagementAttemptState.OUTCOME_PENDING)
        self.assertEqual(pending.result.steps[0].state, ManagementStepState.OUTCOME_PENDING)
        result_id = pending.result.result_id

        recovered = service.execute(pending.attempt.attempt_id)
        self.assertEqual(recovered.attempt.state, ManagementAttemptState.SUCCEEDED)
        self.assertEqual(recovered.result.result_id, result_id)
        self.assertGreater(recovered.result.revision.value, pending.result.revision.value)
        self.assertEqual(recovered.result.steps[0].dispatch_attempt, 1)

    def test_binding_response_loss_reuses_saved_assertion_and_does_not_duplicate(self) -> None:
        pending_sources = PendingOnceBindingService(self.source_service)
        service = ManagementApplicationService(
            self.management_repository, self.scope_service, pending_sources, clock=self.clock
        )
        pending = service.configure(self.command())
        assertion_output = pending.result.steps[2].output

        recovered = service.execute(pending.attempt.attempt_id)

        self.assertEqual(recovered.attempt.state, ManagementAttemptState.SUCCEEDED)
        self.assertEqual(recovered.result.steps[2].output, assertion_output)
        self.assertEqual(len(self.source_service.list_bindings()), 1)
        self.assertEqual(recovered.result.steps[3].dispatch_attempt, 1)

    def test_idempotency_key_rejects_different_request(self) -> None:
        self.management.prepare(self.command())
        with self.assertRaises(DomainError) as raised:
            self.management.prepare(self.command(target="/projects/other"))
        self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

    def test_effective_result_and_owner_objects_survive_database_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "management.sqlite3"
            first_database = SqliteDatabase(path)
            first_service = self._service_for(first_database)
            completed = first_service.configure(self.command(key="persistent"))
            first_database.close()

            second_database = SqliteDatabase(path)
            second_service = self._service_for(second_database)
            loaded = second_service.get(completed.attempt.attempt_id)
            replay = second_service.configure(self.command(key="persistent"))
            second_database.close()

        self.assertEqual(loaded.result.result_digest, completed.result.result_digest)
        self.assertEqual(replay.result.revision, completed.result.revision)
        self.assertEqual(replay.attempt.state, ManagementAttemptState.SUCCEEDED)

    def _service_for(self, database: SqliteDatabase) -> ManagementApplicationService:
        scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(database, id_generator=SequenceIds()), clock=self.clock
        )
        sources = SourceConfigurationService(
            SqliteSourceConfigurationRepository(database, id_generator=SequenceIds()),
            ProviderRegistry((LocalGitConfigurationProvider(),)),
            scopes,
            clock=self.clock,
        )
        management = SqliteManagementRepository(database, id_generator=SequenceIds())
        return ManagementApplicationService(management, scopes, sources, clock=self.clock)


if __name__ == "__main__":
    unittest.main()
