from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
)
from software_world_model.infrastructure import (
    SqliteDatabase,
    SqliteKnowledgeScopeRepository,
    SqliteSourceConfigurationRepository,
)
from software_world_model.knowledge_engine import (
    KnowledgeScopeService,
    ScopePurpose,
    ScopeType,
)
from software_world_model.source_integration import (
    BindingLifecycle,
    DataSourceLifecycle,
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
                provider_configuration,
                label="test provider configuration",
                reject_credentials=True,
            ),
            secret_reference=secret_reference,
        )

    def normalize_selection(
        self,
        *,
        selector: dict[str, str],
        context_constraint: dict[str, str],
    ) -> NormalizedSelection:
        normalized_selector = dict(selector)
        if "paths" in normalized_selector:
            paths = sorted(
                part.strip().rstrip("/")
                for part in normalized_selector["paths"].split(",")
                if part.strip()
            )
            normalized_selector["paths"] = ",".join(paths)
        return NormalizedSelection(
            selector=canonical_fields(normalized_selector, label="test selector"),
            context_constraint=canonical_fields(
                context_constraint, label="test context constraint"
            ),
        )


class SourceConfigurationTests(unittest.TestCase):
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
        self.scope = self.scope_service.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": "Mall"},
            idempotency_key=IdempotencyKey("scope-create"),
            actor="test-operator",
            reason="source configuration test",
            correlation_ref=CorrelationRef("source-test"),
        )

    def tearDown(self) -> None:
        self.database.close()

    def register_source(
        self,
        *,
        key: str = "source-register",
        target: str = "/projects/mall/",
        configuration: dict[str, str] | None = None,
    ):
        return self.source_service.register_data_source(
            provider_type="LOCAL_GIT",
            provider_contract_version="0.1.0",
            identity_domain="LOCAL",
            source_target=target,
            provider_configuration=configuration or {"read_mode": "read_only"},
            secret_reference=None,
            idempotency_key=IdempotencyKey(key),
            actor="test-operator",
            reason="register source",
            correlation_ref=CorrelationRef("source-test"),
        )

    def binding_assertion(self):
        current = self.scope_service.get_scope(self.scope.scope_id)
        return self.scope_service.read_scope_state_assertion(
            scope_id=self.scope.scope_id,
            expected_revision=current.definition_revision,
            purpose=ScopePurpose.BIND_CONFIGURATION,
            caller_ref="source-integration",
            request_ref="binding-command",
            classification="INTERNAL",
        )

    def bind_source(
        self,
        source_id: StableId,
        *,
        key: str = "binding-create",
        paths: str = "src,lib",
        assertion=None,
    ):
        return self.source_service.bind_source_to_scope(
            source_id=source_id,
            assertion=assertion or self.binding_assertion(),
            selector={"paths": paths},
            context_constraint={"revision_policy": "exact"},
            context_hint="mall source",
            idempotency_key=IdempotencyKey(key),
            actor="test-operator",
            reason="bind source",
            correlation_ref=CorrelationRef("source-test"),
        )

    def test_equivalent_registration_returns_same_source_and_tombstone_blocks_reuse(self) -> None:
        source = self.register_source()
        equivalent = self.register_source(key="source-equivalent", target="/projects/mall")
        self.assertEqual(equivalent, source)

        retired = self.source_service.retire_data_source(
            source_id=source.source_id,
            expected_revision=Revision(1),
            idempotency_key=IdempotencyKey("source-retire"),
            actor="test-operator",
            reason="retire source",
            correlation_ref=CorrelationRef("source-test"),
        )
        self.assertEqual(retired.lifecycle, DataSourceLifecycle.RETIRED)

        with self.assertRaises(DomainError) as raised:
            self.register_source(key="source-reuse", target="/projects/mall")
        self.assertEqual(raised.exception.code, ErrorCode.DATASOURCE_IDENTITY_CONFLICT)

    def test_provider_configuration_revision_advances_control_fence(self) -> None:
        source = self.register_source()
        revised = self.source_service.revise_data_source(
            source_id=source.source_id,
            expected_revision=Revision(1),
            provider_configuration={"read_mode": "read_only", "max_bytes": "4096"},
            secret_reference=None,
            idempotency_key=IdempotencyKey("source-revise"),
            actor="test-operator",
            reason="set bound",
            correlation_ref=CorrelationRef("source-test"),
        )
        disabled = self.source_service.disable_data_source(
            source_id=source.source_id,
            expected_revision=Revision(2),
            idempotency_key=IdempotencyKey("source-disable"),
            actor="test-operator",
            reason="maintenance",
            correlation_ref=CorrelationRef("source-test"),
        )
        enabled = self.source_service.enable_data_source(
            source_id=source.source_id,
            expected_revision=Revision(3),
            idempotency_key=IdempotencyKey("source-enable"),
            actor="test-operator",
            reason="maintenance complete",
            correlation_ref=CorrelationRef("source-test"),
        )

        self.assertEqual(revised.control_fence_revision, Revision(2))
        self.assertEqual(disabled.lifecycle, DataSourceLifecycle.DISABLED)
        self.assertEqual(enabled.lifecycle, DataSourceLifecycle.ACTIVE)
        self.assertEqual(enabled.control_fence_revision, Revision(4))

    def test_binding_rejects_forged_or_stale_scope_assertion(self) -> None:
        source = self.register_source()
        assertion = self.binding_assertion()
        forged = replace(
            assertion,
            assertion_id=StableId("scope_assertion_ffffffffffffffffffffffffffffffff"),
        )

        with self.assertRaises(DomainError) as forged_error:
            self.bind_source(source.source_id, key="forged", assertion=forged)
        self.assertEqual(forged_error.exception.code, ErrorCode.SCOPE_ASSERTION_INVALID)

        self.scope_service.retire_scope(
            scope_id=self.scope.scope_id,
            expected_revision=Revision(1),
            idempotency_key=IdempotencyKey("scope-retire"),
            actor="test-operator",
            reason="retire scope",
            correlation_ref=CorrelationRef("source-test"),
        )
        with self.assertRaises(DomainError) as stale_error:
            self.bind_source(source.source_id, key="stale", assertion=assertion)
        self.assertEqual(stale_error.exception.code, ErrorCode.SCOPE_ASSERTION_INVALID)

    def test_active_effective_range_is_unique_and_resume_rechecks_it(self) -> None:
        source = self.register_source()
        first = self.bind_source(source.source_id, paths="src/, lib/")

        with self.assertRaises(DomainError) as duplicate:
            self.bind_source(source.source_id, key="binding-duplicate", paths="lib,src")
        self.assertEqual(duplicate.exception.code, ErrorCode.BINDING_RANGE_CONFLICT)

        suspended = self.source_service.suspend_binding(
            binding_id=first.binding_id,
            expected_revision=Revision(1),
            idempotency_key=IdempotencyKey("binding-suspend"),
            actor="test-operator",
            reason="replace binding",
            correlation_ref=CorrelationRef("source-test"),
        )
        replacement = self.bind_source(
            source.source_id, key="binding-replacement", paths="lib,src"
        )
        self.assertEqual(suspended.lifecycle, BindingLifecycle.SUSPENDED)
        self.assertNotEqual(replacement.binding_id, first.binding_id)

        with self.assertRaises(DomainError) as resume_error:
            self.source_service.resume_binding(
                binding_id=first.binding_id,
                expected_revision=Revision(2),
                idempotency_key=IdempotencyKey("binding-resume"),
                actor="test-operator",
                reason="resume old binding",
                correlation_ref=CorrelationRef("source-test"),
            )
        self.assertEqual(resume_error.exception.code, ErrorCode.BINDING_RANGE_CONFLICT)

    def test_source_retirement_atomically_retires_its_bindings_not_scope(self) -> None:
        source = self.register_source()
        binding = self.bind_source(source.source_id)

        retired_source = self.source_service.retire_data_source(
            source_id=source.source_id,
            expected_revision=Revision(1),
            idempotency_key=IdempotencyKey("source-retire-with-binding"),
            actor="test-operator",
            reason="retire source and bindings",
            correlation_ref=CorrelationRef("source-test"),
        )

        current_binding = self.source_service.get_binding(binding.binding_id)
        self.assertEqual(retired_source.lifecycle, DataSourceLifecycle.RETIRED)
        self.assertEqual(current_binding.lifecycle, BindingLifecycle.RETIRED)
        self.assertEqual(current_binding.definition_revision, Revision(2))
        self.assertEqual(
            self.scope_service.get_scope(self.scope.scope_id).lifecycle.value, "ACTIVE"
        )
        self.assertEqual(len(self.source_service.list_outbox_events()), 4)

    def test_scope_retirement_does_not_cascade_to_existing_binding(self) -> None:
        source = self.register_source()
        binding = self.bind_source(source.source_id)

        self.scope_service.retire_scope(
            scope_id=self.scope.scope_id,
            expected_revision=Revision(1),
            idempotency_key=IdempotencyKey("scope-retire-no-cascade"),
            actor="test-operator",
            reason="retire scope",
            correlation_ref=CorrelationRef("source-test"),
        )

        self.assertEqual(
            self.source_service.get_binding(binding.binding_id).lifecycle,
            BindingLifecycle.ACTIVE,
        )

    def test_secret_values_are_rejected_from_provider_configuration(self) -> None:
        with self.assertRaises(DomainError) as raised:
            self.register_source(configuration={"api_key": "must-not-be-stored"})
        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)


if __name__ == "__main__":
    unittest.main()
