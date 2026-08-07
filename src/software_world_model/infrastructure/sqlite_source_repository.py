"""SQLite Source Integration configuration repository."""

from __future__ import annotations

from datetime import datetime
import json
import sqlite3

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
    canonical_json_bytes,
    digest_of,
)
from software_world_model.knowledge_engine import ScopeStateAssertion
from software_world_model.source_integration.configuration import (
    BindingLifecycle,
    CanonicalFields,
    DataSource,
    DataSourceBinding,
    DataSourceLifecycle,
    NormalizedDataSource,
    NormalizedSelection,
    SourceOutboxEvent,
)

from .sqlite_database import SqliteDatabase


_SCHEMA = """
CREATE TABLE IF NOT EXISTS src_datasource_roots (
    source_id TEXT PRIMARY KEY,
    provider_type TEXT NOT NULL,
    provider_contract_version TEXT NOT NULL,
    identity_strategy_version TEXT NOT NULL,
    identity_domain TEXT NOT NULL,
    canonical_source_target TEXT NOT NULL,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    lifecycle TEXT NOT NULL CHECK (lifecycle IN ('ACTIVE', 'DISABLED', 'RETIRED')),
    control_fence_revision INTEGER NOT NULL CHECK (control_fence_revision >= 1),
    created_at TEXT NOT NULL,
    UNIQUE (provider_type, identity_strategy_version, identity_domain, canonical_source_target)
);

CREATE TABLE IF NOT EXISTS src_datasource_revisions (
    source_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    provider_configuration_json TEXT NOT NULL,
    secret_reference TEXT,
    lifecycle TEXT NOT NULL CHECK (lifecycle IN ('ACTIVE', 'DISABLED', 'RETIRED')),
    control_fence_revision INTEGER NOT NULL CHECK (control_fence_revision >= 1),
    actor TEXT NOT NULL,
    reason TEXT NOT NULL,
    correlation_ref TEXT NOT NULL,
    revised_at TEXT NOT NULL,
    definition_digest TEXT NOT NULL,
    PRIMARY KEY (source_id, revision),
    FOREIGN KEY (source_id) REFERENCES src_datasource_roots(source_id)
);

CREATE TABLE IF NOT EXISTS src_binding_roots (
    binding_id TEXT PRIMARY KEY,
    scope_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    provider_contract_version TEXT NOT NULL,
    current_revision INTEGER NOT NULL CHECK (current_revision >= 1),
    lifecycle TEXT NOT NULL CHECK (lifecycle IN ('ACTIVE', 'SUSPENDED', 'RETIRED')),
    effective_range_digest TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES src_datasource_roots(source_id)
);

CREATE UNIQUE INDEX IF NOT EXISTS src_binding_one_active_range
    ON src_binding_roots(scope_id, source_id, provider_contract_version, effective_range_digest)
    WHERE lifecycle = 'ACTIVE';

CREATE TABLE IF NOT EXISTS src_binding_revisions (
    binding_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    observed_scope_revision INTEGER NOT NULL CHECK (observed_scope_revision >= 1),
    scope_assertion_id TEXT NOT NULL,
    scope_assertion_digest TEXT NOT NULL,
    selector_json TEXT NOT NULL,
    selector_digest TEXT NOT NULL,
    context_constraint_json TEXT NOT NULL,
    context_hint TEXT,
    effective_range_digest TEXT NOT NULL,
    lifecycle TEXT NOT NULL CHECK (lifecycle IN ('ACTIVE', 'SUSPENDED', 'RETIRED')),
    actor TEXT NOT NULL,
    reason TEXT NOT NULL,
    correlation_ref TEXT NOT NULL,
    revised_at TEXT NOT NULL,
    definition_digest TEXT NOT NULL,
    PRIMARY KEY (binding_id, revision),
    FOREIGN KEY (binding_id) REFERENCES src_binding_roots(binding_id)
);

CREATE TABLE IF NOT EXISTS src_configuration_idempotency (
    idempotency_key TEXT PRIMARY KEY,
    command_type TEXT NOT NULL,
    request_digest TEXT NOT NULL,
    result_kind TEXT NOT NULL CHECK (result_kind IN ('DATASOURCE', 'BINDING')),
    result_id TEXT NOT NULL,
    result_revision INTEGER NOT NULL CHECK (result_revision >= 1)
);

CREATE TABLE IF NOT EXISTS src_configuration_outbox (
    event_id TEXT PRIMARY KEY,
    aggregate_kind TEXT NOT NULL CHECK (aggregate_kind IN ('DATASOURCE', 'BINDING')),
    aggregate_id TEXT NOT NULL,
    authority_revision INTEGER NOT NULL CHECK (authority_revision >= 1),
    event_type TEXT NOT NULL,
    payload_digest TEXT NOT NULL,
    correlation_ref TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    delivered_at TEXT,
    UNIQUE (aggregate_kind, aggregate_id, authority_revision, event_type)
);
"""


class SqliteSourceConfigurationRepository:
    def __init__(self, database: SqliteDatabase, *, id_generator: IdGenerator | None = None) -> None:
        self._database = database
        self._ids = id_generator or Uuid4IdGenerator()
        self._database.executescript(_SCHEMA)

    def register_data_source(
        self,
        *,
        provider_type: str,
        provider_contract_version: str,
        normalized: NormalizedDataSource,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> DataSource:
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, idempotency_key, "RegisterDataSource@1", request_digest
                )
                if replay is not None:
                    return _expect_source(replay)
                identity_row = connection.execute(
                    """SELECT source_id FROM src_datasource_roots
                       WHERE provider_type = ? AND identity_strategy_version = ?
                         AND identity_domain = ? AND canonical_source_target = ?""",
                    (
                        provider_type,
                        normalized.identity_strategy_version,
                        normalized.identity_domain,
                        normalized.canonical_source_target,
                    ),
                ).fetchone()
                if identity_row is not None:
                    existing = self._load_data_source(
                        connection, StableId(identity_row["source_id"]), None
                    )
                    if (
                        existing.lifecycle is not DataSourceLifecycle.RETIRED
                        and existing.provider_contract_version == provider_contract_version
                        and existing.provider_configuration == normalized.provider_configuration
                        and existing.secret_reference == normalized.secret_reference
                    ):
                        self._insert_idempotency(
                            connection,
                            idempotency_key,
                            "RegisterDataSource@1",
                            request_digest,
                            existing,
                        )
                        return existing
                    raise DomainError(
                        ErrorCode.DATASOURCE_IDENTITY_CONFLICT,
                        "the permanent data source identity is already occupied",
                    )
                source = self._build_data_source(
                    source_id=self._ids.new("datasource"),
                    provider_type=provider_type,
                    provider_contract_version=provider_contract_version,
                    identity_strategy_version=normalized.identity_strategy_version,
                    identity_domain=normalized.identity_domain,
                    canonical_source_target=normalized.canonical_source_target,
                    provider_configuration=normalized.provider_configuration,
                    secret_reference=normalized.secret_reference,
                    lifecycle=DataSourceLifecycle.ACTIVE,
                    revision=Revision(1),
                    control_fence_revision=Revision(1),
                    created_at=occurred_at,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                connection.execute(
                    """INSERT INTO src_datasource_roots
                       (source_id, provider_type, provider_contract_version,
                        identity_strategy_version, identity_domain, canonical_source_target,
                        current_revision, lifecycle, control_fence_revision, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        source.source_id.value,
                        source.provider_type,
                        source.provider_contract_version,
                        source.identity_strategy_version,
                        source.identity_domain,
                        source.canonical_source_target,
                        1,
                        source.lifecycle.value,
                        1,
                        _time(source.created_at),
                    ),
                )
                self._insert_data_source_revision(connection, source, correlation_ref)
                self._insert_idempotency(
                    connection,
                    idempotency_key,
                    "RegisterDataSource@1",
                    request_digest,
                    source,
                )
                self._insert_outbox(
                    connection, source, "DATASOURCE", "DATA_SOURCE_REGISTERED@1", correlation_ref
                )
                return source
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

    def revise_data_source(
        self,
        *,
        source_id: StableId,
        expected_revision: Revision,
        normalized: NormalizedDataSource,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> DataSource:
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, idempotency_key, "ReviseDataSource@1", request_digest
                )
                if replay is not None:
                    return _expect_source(replay)
                current = self._load_data_source(connection, source_id, None)
                _require_revision(current.definition_revision, expected_revision, source_id)
                if current.lifecycle is DataSourceLifecycle.RETIRED:
                    raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "retired data source cannot be revised")
                if (
                    current.identity_strategy_version != normalized.identity_strategy_version
                    or current.identity_domain != normalized.identity_domain
                    or current.canonical_source_target != normalized.canonical_source_target
                ):
                    raise DomainError(
                        ErrorCode.DATASOURCE_IDENTITY_CONFLICT,
                        "data source revision changed the permanent identity",
                    )
                if (
                    current.provider_configuration == normalized.provider_configuration
                    and current.secret_reference == normalized.secret_reference
                ):
                    self._insert_idempotency(
                        connection,
                        idempotency_key,
                        "ReviseDataSource@1",
                        request_digest,
                        current,
                    )
                    return current
                revised = self._build_data_source(
                    source_id=current.source_id,
                    provider_type=current.provider_type,
                    provider_contract_version=current.provider_contract_version,
                    identity_strategy_version=current.identity_strategy_version,
                    identity_domain=current.identity_domain,
                    canonical_source_target=current.canonical_source_target,
                    provider_configuration=normalized.provider_configuration,
                    secret_reference=normalized.secret_reference,
                    lifecycle=current.lifecycle,
                    revision=current.definition_revision.next(),
                    control_fence_revision=current.control_fence_revision.next(),
                    created_at=current.created_at,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                self._advance_data_source_root(connection, current, revised)
                self._insert_data_source_revision(connection, revised, correlation_ref)
                self._insert_idempotency(
                    connection,
                    idempotency_key,
                    "ReviseDataSource@1",
                    request_digest,
                    revised,
                )
                self._insert_outbox(
                    connection, revised, "DATASOURCE", "DATA_SOURCE_REVISED@1", correlation_ref
                )
                return revised
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

    def change_data_source_lifecycle(
        self,
        *,
        source_id: StableId,
        expected_revision: Revision,
        target: DataSourceLifecycle,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> DataSource:
        command_type = f"ChangeDataSourceLifecycle:{target.value}@1"
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, idempotency_key, command_type, request_digest
                )
                if replay is not None:
                    return _expect_source(replay)
                current = self._load_data_source(connection, source_id, None)
                _require_revision(current.definition_revision, expected_revision, source_id)
                allowed = {
                    DataSourceLifecycle.ACTIVE: {
                        DataSourceLifecycle.DISABLED,
                        DataSourceLifecycle.RETIRED,
                    },
                    DataSourceLifecycle.DISABLED: {
                        DataSourceLifecycle.ACTIVE,
                        DataSourceLifecycle.RETIRED,
                    },
                    DataSourceLifecycle.RETIRED: set(),
                }
                if target not in allowed[current.lifecycle]:
                    raise DomainError(
                        ErrorCode.CONTROL_STATE_DENIED,
                        f"cannot change data source from {current.lifecycle.value} to {target.value}",
                    )
                if target is DataSourceLifecycle.RETIRED:
                    self._retire_current_bindings(
                        connection,
                        source_id=source_id,
                        actor=actor,
                        reason=reason,
                        correlation_ref=correlation_ref,
                        occurred_at=occurred_at,
                    )
                revised = self._build_data_source(
                    source_id=current.source_id,
                    provider_type=current.provider_type,
                    provider_contract_version=current.provider_contract_version,
                    identity_strategy_version=current.identity_strategy_version,
                    identity_domain=current.identity_domain,
                    canonical_source_target=current.canonical_source_target,
                    provider_configuration=current.provider_configuration,
                    secret_reference=current.secret_reference,
                    lifecycle=target,
                    revision=current.definition_revision.next(),
                    control_fence_revision=current.control_fence_revision.next(),
                    created_at=current.created_at,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                self._advance_data_source_root(connection, current, revised)
                self._insert_data_source_revision(connection, revised, correlation_ref)
                self._insert_idempotency(
                    connection, idempotency_key, command_type, request_digest, revised
                )
                self._insert_outbox(
                    connection,
                    revised,
                    "DATASOURCE",
                    f"DATA_SOURCE_{target.value}@1",
                    correlation_ref,
                )
                return revised
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

    def get_data_source(
        self, source_id: StableId, revision: Revision | None = None
    ) -> DataSource:
        with self._database.read() as connection:
            return self._load_data_source(connection, source_id, revision)

    def bind_source(
        self,
        *,
        source: DataSource,
        assertion: ScopeStateAssertion,
        selection: NormalizedSelection,
        context_hint: str | None,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> DataSourceBinding:
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, idempotency_key, "BindSourceToScope@1", request_digest
                )
                if replay is not None:
                    return _expect_binding(replay)
                current_source = self._load_data_source(connection, source.source_id, None)
                _require_revision(
                    current_source.definition_revision,
                    source.definition_revision,
                    source.source_id,
                )
                if current_source.lifecycle is DataSourceLifecycle.RETIRED:
                    raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "retired data source cannot be bound")
                conflict = connection.execute(
                    """SELECT binding_id FROM src_binding_roots
                       WHERE scope_id = ? AND source_id = ? AND provider_contract_version = ?
                         AND effective_range_digest = ? AND lifecycle = 'ACTIVE'""",
                    (
                        assertion.scope_id.value,
                        source.source_id.value,
                        source.provider_contract_version,
                        selection.effective_range_digest.value,
                    ),
                ).fetchone()
                if conflict is not None:
                    raise DomainError(
                        ErrorCode.BINDING_RANGE_CONFLICT,
                        "an active binding already owns the equivalent effective range",
                    )
                binding = self._build_binding(
                    binding_id=self._ids.new("binding"),
                    scope_id=assertion.scope_id,
                    observed_scope_revision=assertion.definition_revision,
                    scope_assertion_id=assertion.assertion_id,
                    scope_assertion_digest=assertion.digest,
                    source_id=source.source_id,
                    provider_contract_version=source.provider_contract_version,
                    selection=selection,
                    context_hint=context_hint,
                    lifecycle=BindingLifecycle.ACTIVE,
                    revision=Revision(1),
                    created_at=occurred_at,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                connection.execute(
                    """INSERT INTO src_binding_roots
                       (binding_id, scope_id, source_id, provider_contract_version,
                        current_revision, lifecycle, effective_range_digest, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        binding.binding_id.value,
                        binding.scope_id.value,
                        binding.source_id.value,
                        binding.provider_contract_version,
                        1,
                        binding.lifecycle.value,
                        binding.effective_range_digest.value,
                        _time(binding.created_at),
                    ),
                )
                self._insert_binding_revision(connection, binding, correlation_ref)
                self._insert_idempotency(
                    connection,
                    idempotency_key,
                    "BindSourceToScope@1",
                    request_digest,
                    binding,
                )
                self._insert_outbox(
                    connection, binding, "BINDING", "DATA_SOURCE_BOUND_TO_SCOPE@1", correlation_ref
                )
                return binding
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

    def revise_binding(
        self,
        *,
        binding_id: StableId,
        expected_revision: Revision,
        selection: NormalizedSelection,
        context_hint: str | None,
        assertion: ScopeStateAssertion,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> DataSourceBinding:
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, idempotency_key, "ReviseBinding@1", request_digest
                )
                if replay is not None:
                    return _expect_binding(replay)
                current = self._load_binding(connection, binding_id, None)
                _require_revision(current.definition_revision, expected_revision, binding_id)
                if current.lifecycle is BindingLifecycle.RETIRED:
                    raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "retired binding cannot be revised")
                if current.scope_id != assertion.scope_id:
                    raise DomainError(
                        ErrorCode.SCOPE_ASSERTION_INVALID,
                        "assertion scope does not match binding",
                    )
                revised = self._build_binding(
                    binding_id=current.binding_id,
                    scope_id=current.scope_id,
                    observed_scope_revision=assertion.definition_revision,
                    scope_assertion_id=assertion.assertion_id,
                    scope_assertion_digest=assertion.digest,
                    source_id=current.source_id,
                    provider_contract_version=current.provider_contract_version,
                    selection=selection,
                    context_hint=context_hint,
                    lifecycle=current.lifecycle,
                    revision=current.definition_revision.next(),
                    created_at=current.created_at,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                self._advance_binding_root(connection, current, revised)
                self._insert_binding_revision(connection, revised, correlation_ref)
                self._insert_idempotency(
                    connection, idempotency_key, "ReviseBinding@1", request_digest, revised
                )
                self._insert_outbox(
                    connection, revised, "BINDING", "DATA_SOURCE_BINDING_REVISED@1", correlation_ref
                )
                return revised
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

    def change_binding_lifecycle(
        self,
        *,
        binding_id: StableId,
        expected_revision: Revision,
        target: BindingLifecycle,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> DataSourceBinding:
        command_type = f"ChangeBindingLifecycle:{target.value}@1"
        try:
            with self._database.transaction() as connection:
                replay = self._idempotent_result(
                    connection, idempotency_key, command_type, request_digest
                )
                if replay is not None:
                    return _expect_binding(replay)
                current = self._load_binding(connection, binding_id, None)
                _require_revision(current.definition_revision, expected_revision, binding_id)
                allowed = {
                    BindingLifecycle.ACTIVE: {
                        BindingLifecycle.SUSPENDED,
                        BindingLifecycle.RETIRED,
                    },
                    BindingLifecycle.SUSPENDED: {
                        BindingLifecycle.ACTIVE,
                        BindingLifecycle.RETIRED,
                    },
                    BindingLifecycle.RETIRED: set(),
                }
                if target not in allowed[current.lifecycle]:
                    raise DomainError(
                        ErrorCode.CONTROL_STATE_DENIED,
                        f"cannot change binding from {current.lifecycle.value} to {target.value}",
                    )
                if target is BindingLifecycle.ACTIVE:
                    conflict = connection.execute(
                        """SELECT binding_id FROM src_binding_roots
                           WHERE scope_id = ? AND source_id = ?
                             AND provider_contract_version = ? AND effective_range_digest = ?
                             AND lifecycle = 'ACTIVE' AND binding_id <> ?""",
                        (
                            current.scope_id.value,
                            current.source_id.value,
                            current.provider_contract_version,
                            current.effective_range_digest.value,
                            current.binding_id.value,
                        ),
                    ).fetchone()
                    if conflict is not None:
                        raise DomainError(
                            ErrorCode.BINDING_RANGE_CONFLICT,
                            "an active binding already owns the equivalent effective range",
                        )
                revised = self._build_binding(
                    binding_id=current.binding_id,
                    scope_id=current.scope_id,
                    observed_scope_revision=current.observed_scope_revision,
                    scope_assertion_id=current.scope_assertion_id,
                    scope_assertion_digest=current.scope_assertion_digest,
                    source_id=current.source_id,
                    provider_contract_version=current.provider_contract_version,
                    selection=NormalizedSelection(
                        selector=current.selector,
                        context_constraint=current.context_constraint,
                    ),
                    context_hint=current.context_hint,
                    lifecycle=target,
                    revision=current.definition_revision.next(),
                    created_at=current.created_at,
                    revised_at=occurred_at,
                    actor=actor,
                    reason=reason,
                )
                self._advance_binding_root(connection, current, revised)
                self._insert_binding_revision(connection, revised, correlation_ref)
                self._insert_idempotency(
                    connection, idempotency_key, command_type, request_digest, revised
                )
                self._insert_outbox(
                    connection,
                    revised,
                    "BINDING",
                    f"DATA_SOURCE_BINDING_{target.value}@1",
                    correlation_ref,
                )
                return revised
        except DomainError:
            raise
        except sqlite3.IntegrityError as exc:
            raise _integrity_error(exc) from exc

    def get_binding(
        self, binding_id: StableId, revision: Revision | None = None
    ) -> DataSourceBinding:
        with self._database.read() as connection:
            return self._load_binding(connection, binding_id, revision)

    def list_bindings(self, *, source_id: StableId | None = None) -> tuple[DataSourceBinding, ...]:
        with self._database.read() as connection:
            if source_id is None:
                rows = connection.execute(
                    "SELECT binding_id FROM src_binding_roots ORDER BY binding_id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """SELECT binding_id FROM src_binding_roots
                       WHERE source_id = ? ORDER BY binding_id""",
                    (source_id.value,),
                ).fetchall()
            return tuple(
                self._load_binding(connection, StableId(row["binding_id"]), None)
                for row in rows
            )

    def list_outbox(self) -> tuple[SourceOutboxEvent, ...]:
        with self._database.read() as connection:
            rows = connection.execute(
                """SELECT event_id, aggregate_kind, aggregate_id, authority_revision,
                          event_type, payload_digest, occurred_at
                   FROM src_configuration_outbox ORDER BY rowid"""
            ).fetchall()
        return tuple(
            SourceOutboxEvent(
                event_id=StableId(row["event_id"]),
                aggregate_kind=row["aggregate_kind"],
                aggregate_id=StableId(row["aggregate_id"]),
                authority_revision=Revision(row["authority_revision"]),
                event_type=row["event_type"],
                payload_digest=Digest(row["payload_digest"]),
                occurred_at=_parse_time(row["occurred_at"]),
            )
            for row in rows
        )

    def _retire_current_bindings(
        self,
        connection: sqlite3.Connection,
        *,
        source_id: StableId,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> None:
        rows = connection.execute(
            """SELECT binding_id FROM src_binding_roots
               WHERE source_id = ? AND lifecycle <> 'RETIRED' ORDER BY binding_id""",
            (source_id.value,),
        ).fetchall()
        for row in rows:
            current = self._load_binding(connection, StableId(row["binding_id"]), None)
            retired = self._build_binding(
                binding_id=current.binding_id,
                scope_id=current.scope_id,
                observed_scope_revision=current.observed_scope_revision,
                scope_assertion_id=current.scope_assertion_id,
                scope_assertion_digest=current.scope_assertion_digest,
                source_id=current.source_id,
                provider_contract_version=current.provider_contract_version,
                selection=NormalizedSelection(
                    selector=current.selector,
                    context_constraint=current.context_constraint,
                ),
                context_hint=current.context_hint,
                lifecycle=BindingLifecycle.RETIRED,
                revision=current.definition_revision.next(),
                created_at=current.created_at,
                revised_at=occurred_at,
                actor=actor,
                reason=reason,
            )
            self._advance_binding_root(connection, current, retired)
            self._insert_binding_revision(connection, retired, correlation_ref)
            self._insert_outbox(
                connection,
                retired,
                "BINDING",
                "DATA_SOURCE_BINDING_RETIRED_WITH_SOURCE@1",
                correlation_ref,
            )

    def _idempotent_result(
        self,
        connection: sqlite3.Connection,
        key: IdempotencyKey,
        command_type: str,
        request_digest: Digest,
    ) -> DataSource | DataSourceBinding | None:
        row = connection.execute(
            """SELECT command_type, request_digest, result_kind, result_id, result_revision
               FROM src_configuration_idempotency WHERE idempotency_key = ?""",
            (key.value,),
        ).fetchone()
        if row is None:
            return None
        if row["command_type"] != command_type or row["request_digest"] != request_digest.value:
            raise DomainError(
                ErrorCode.IDEMPOTENCY_MISMATCH,
                "idempotency key was already used for another source configuration command",
                {"idempotency_key": key.value},
            )
        stable_id = StableId(row["result_id"])
        revision = Revision(row["result_revision"])
        if row["result_kind"] == "DATASOURCE":
            return self._load_data_source(connection, stable_id, revision)
        return self._load_binding(connection, stable_id, revision)

    def _load_data_source(
        self,
        connection: sqlite3.Connection,
        source_id: StableId,
        revision: Revision | None,
    ) -> DataSource:
        revision_clause = "root.current_revision" if revision is None else "?"
        parameters: tuple[object, ...] = (
            (source_id.value,) if revision is None else (source_id.value, revision.value)
        )
        row = connection.execute(
            f"""SELECT root.*, r.revision, r.provider_configuration_json,
                       r.secret_reference, r.actor, r.reason, r.revised_at,
                       r.definition_digest, r.lifecycle AS revision_lifecycle,
                       r.control_fence_revision AS revision_control_fence
                FROM src_datasource_roots root
                JOIN src_datasource_revisions r
                  ON r.source_id = root.source_id AND r.revision = {revision_clause}
                WHERE root.source_id = ?"""
            if revision is None
            else """SELECT root.*, r.revision, r.provider_configuration_json,
                            r.secret_reference, r.actor, r.reason, r.revised_at,
                            r.definition_digest, r.lifecycle AS revision_lifecycle,
                            r.control_fence_revision AS revision_control_fence
                     FROM src_datasource_roots root
                     JOIN src_datasource_revisions r ON r.source_id = root.source_id
                     WHERE root.source_id = ? AND r.revision = ?""",
            parameters,
        ).fetchone()
        if row is None:
            raise DomainError(
                ErrorCode.DATASOURCE_NOT_FOUND,
                "data source or requested revision does not exist",
                {"source_id": source_id.value},
            )
        return DataSource(
            source_id=StableId(row["source_id"]),
            provider_type=row["provider_type"],
            provider_contract_version=row["provider_contract_version"],
            identity_strategy_version=row["identity_strategy_version"],
            identity_domain=row["identity_domain"],
            canonical_source_target=row["canonical_source_target"],
            provider_configuration=_fields(row["provider_configuration_json"]),
            secret_reference=row["secret_reference"],
            lifecycle=DataSourceLifecycle(row["revision_lifecycle"]),
            definition_revision=Revision(row["revision"]),
            control_fence_revision=Revision(row["revision_control_fence"]),
            created_at=_parse_time(row["created_at"]),
            revised_at=_parse_time(row["revised_at"]),
            actor=row["actor"],
            reason=row["reason"],
            definition_digest=Digest(row["definition_digest"]),
        )

    def _load_binding(
        self,
        connection: sqlite3.Connection,
        binding_id: StableId,
        revision: Revision | None,
    ) -> DataSourceBinding:
        if revision is None:
            row = connection.execute(
                """SELECT root.*, r.revision, r.observed_scope_revision,
                          r.scope_assertion_id, r.scope_assertion_digest,
                          r.selector_json, r.selector_digest, r.context_constraint_json,
                          r.context_hint, r.effective_range_digest AS revision_range_digest,
                          r.lifecycle AS revision_lifecycle, r.actor, r.reason,
                          r.revised_at, r.definition_digest
                   FROM src_binding_roots root
                   JOIN src_binding_revisions r
                     ON r.binding_id = root.binding_id AND r.revision = root.current_revision
                   WHERE root.binding_id = ?""",
                (binding_id.value,),
            ).fetchone()
        else:
            row = connection.execute(
                """SELECT root.*, r.revision, r.observed_scope_revision,
                          r.scope_assertion_id, r.scope_assertion_digest,
                          r.selector_json, r.selector_digest, r.context_constraint_json,
                          r.context_hint, r.effective_range_digest AS revision_range_digest,
                          r.lifecycle AS revision_lifecycle, r.actor, r.reason,
                          r.revised_at, r.definition_digest
                   FROM src_binding_roots root
                   JOIN src_binding_revisions r ON r.binding_id = root.binding_id
                   WHERE root.binding_id = ? AND r.revision = ?""",
                (binding_id.value, revision.value),
            ).fetchone()
        if row is None:
            raise DomainError(
                ErrorCode.BINDING_NOT_FOUND,
                "binding or requested revision does not exist",
                {"binding_id": binding_id.value},
            )
        return DataSourceBinding(
            binding_id=StableId(row["binding_id"]),
            scope_id=StableId(row["scope_id"]),
            observed_scope_revision=Revision(row["observed_scope_revision"]),
            scope_assertion_id=StableId(row["scope_assertion_id"]),
            scope_assertion_digest=Digest(row["scope_assertion_digest"]),
            source_id=StableId(row["source_id"]),
            provider_contract_version=row["provider_contract_version"],
            selector=_fields(row["selector_json"]),
            selector_digest=Digest(row["selector_digest"]),
            context_constraint=_fields(row["context_constraint_json"]),
            context_hint=row["context_hint"],
            effective_range_digest=Digest(row["revision_range_digest"]),
            lifecycle=BindingLifecycle(row["revision_lifecycle"]),
            definition_revision=Revision(row["revision"]),
            created_at=_parse_time(row["created_at"]),
            revised_at=_parse_time(row["revised_at"]),
            actor=row["actor"],
            reason=row["reason"],
            definition_digest=Digest(row["definition_digest"]),
        )

    @staticmethod
    def _build_data_source(
        *,
        source_id: StableId,
        provider_type: str,
        provider_contract_version: str,
        identity_strategy_version: str,
        identity_domain: str,
        canonical_source_target: str,
        provider_configuration: CanonicalFields,
        secret_reference: str | None,
        lifecycle: DataSourceLifecycle,
        revision: Revision,
        control_fence_revision: Revision,
        created_at: datetime,
        revised_at: datetime,
        actor: str,
        reason: str,
    ) -> DataSource:
        core = {
            "source_id": source_id.value,
            "provider_type": provider_type,
            "provider_contract_version": provider_contract_version,
            "identity_strategy_version": identity_strategy_version,
            "identity_domain": identity_domain,
            "canonical_source_target": canonical_source_target,
            "provider_configuration": provider_configuration,
            "secret_reference": secret_reference,
            "lifecycle": lifecycle.value,
            "definition_revision": revision.value,
            "control_fence_revision": control_fence_revision.value,
            "created_at": created_at,
            "revised_at": revised_at,
        }
        return DataSource(
            source_id=source_id,
            provider_type=provider_type,
            provider_contract_version=provider_contract_version,
            identity_strategy_version=identity_strategy_version,
            identity_domain=identity_domain,
            canonical_source_target=canonical_source_target,
            provider_configuration=provider_configuration,
            secret_reference=secret_reference,
            lifecycle=lifecycle,
            definition_revision=revision,
            control_fence_revision=control_fence_revision,
            created_at=created_at,
            revised_at=revised_at,
            actor=actor,
            reason=reason,
            definition_digest=digest_of(core),
        )

    @staticmethod
    def _build_binding(
        *,
        binding_id: StableId,
        scope_id: StableId,
        observed_scope_revision: Revision,
        scope_assertion_id: StableId,
        scope_assertion_digest: Digest,
        source_id: StableId,
        provider_contract_version: str,
        selection: NormalizedSelection,
        context_hint: str | None,
        lifecycle: BindingLifecycle,
        revision: Revision,
        created_at: datetime,
        revised_at: datetime,
        actor: str,
        reason: str,
    ) -> DataSourceBinding:
        core = {
            "binding_id": binding_id.value,
            "scope_id": scope_id.value,
            "observed_scope_revision": observed_scope_revision.value,
            "scope_assertion_id": scope_assertion_id.value,
            "scope_assertion_digest": scope_assertion_digest.value,
            "source_id": source_id.value,
            "provider_contract_version": provider_contract_version,
            "selector": selection.selector,
            "selector_digest": selection.selector_digest.value,
            "context_constraint": selection.context_constraint,
            "context_hint": context_hint,
            "effective_range_digest": selection.effective_range_digest.value,
            "lifecycle": lifecycle.value,
            "definition_revision": revision.value,
            "created_at": created_at,
            "revised_at": revised_at,
        }
        return DataSourceBinding(
            binding_id=binding_id,
            scope_id=scope_id,
            observed_scope_revision=observed_scope_revision,
            scope_assertion_id=scope_assertion_id,
            scope_assertion_digest=scope_assertion_digest,
            source_id=source_id,
            provider_contract_version=provider_contract_version,
            selector=selection.selector,
            selector_digest=selection.selector_digest,
            context_constraint=selection.context_constraint,
            context_hint=context_hint,
            effective_range_digest=selection.effective_range_digest,
            lifecycle=lifecycle,
            definition_revision=revision,
            created_at=created_at,
            revised_at=revised_at,
            actor=actor,
            reason=reason,
            definition_digest=digest_of(core),
        )

    @staticmethod
    def _insert_data_source_revision(
        connection: sqlite3.Connection,
        source: DataSource,
        correlation_ref: CorrelationRef,
    ) -> None:
        connection.execute(
            """INSERT INTO src_datasource_revisions
               (source_id, revision, provider_configuration_json, secret_reference,
                lifecycle, control_fence_revision, actor, reason, correlation_ref,
                revised_at, definition_digest)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source.source_id.value,
                source.definition_revision.value,
                canonical_json_bytes(source.provider_configuration).decode("utf-8"),
                source.secret_reference,
                source.lifecycle.value,
                source.control_fence_revision.value,
                source.actor,
                source.reason,
                correlation_ref.value,
                _time(source.revised_at),
                source.definition_digest.value,
            ),
        )

    @staticmethod
    def _insert_binding_revision(
        connection: sqlite3.Connection,
        binding: DataSourceBinding,
        correlation_ref: CorrelationRef,
    ) -> None:
        connection.execute(
            """INSERT INTO src_binding_revisions
               (binding_id, revision, observed_scope_revision, scope_assertion_id,
                scope_assertion_digest, selector_json, selector_digest,
                context_constraint_json, context_hint, effective_range_digest,
                lifecycle, actor, reason, correlation_ref, revised_at, definition_digest)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                binding.binding_id.value,
                binding.definition_revision.value,
                binding.observed_scope_revision.value,
                binding.scope_assertion_id.value,
                binding.scope_assertion_digest.value,
                canonical_json_bytes(binding.selector).decode("utf-8"),
                binding.selector_digest.value,
                canonical_json_bytes(binding.context_constraint).decode("utf-8"),
                binding.context_hint,
                binding.effective_range_digest.value,
                binding.lifecycle.value,
                binding.actor,
                binding.reason,
                correlation_ref.value,
                _time(binding.revised_at),
                binding.definition_digest.value,
            ),
        )

    @staticmethod
    def _insert_idempotency(
        connection: sqlite3.Connection,
        key: IdempotencyKey,
        command_type: str,
        request_digest: Digest,
        result: DataSource | DataSourceBinding,
    ) -> None:
        if isinstance(result, DataSource):
            result_kind = "DATASOURCE"
            result_id = result.source_id
        else:
            result_kind = "BINDING"
            result_id = result.binding_id
        connection.execute(
            "INSERT INTO src_configuration_idempotency VALUES (?, ?, ?, ?, ?, ?)",
            (
                key.value,
                command_type,
                request_digest.value,
                result_kind,
                result_id.value,
                result.definition_revision.value,
            ),
        )

    def _insert_outbox(
        self,
        connection: sqlite3.Connection,
        aggregate: DataSource | DataSourceBinding,
        aggregate_kind: str,
        event_type: str,
        correlation_ref: CorrelationRef,
    ) -> None:
        aggregate_id = (
            aggregate.source_id if isinstance(aggregate, DataSource) else aggregate.binding_id
        )
        payload_digest = digest_of(
            {
                "owner": "SOURCE_INTEGRATION",
                "aggregate_kind": aggregate_kind,
                "aggregate_id": aggregate_id.value,
                "authority_revision": aggregate.definition_revision.value,
                "event_type": event_type,
                "definition_digest": aggregate.definition_digest.value,
            }
        )
        connection.execute(
            """INSERT INTO src_configuration_outbox
               (event_id, aggregate_kind, aggregate_id, authority_revision,
                event_type, payload_digest, correlation_ref, occurred_at, delivered_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)""",
            (
                self._ids.new("outbox_event").value,
                aggregate_kind,
                aggregate_id.value,
                aggregate.definition_revision.value,
                event_type,
                payload_digest.value,
                correlation_ref.value,
                _time(aggregate.revised_at),
            ),
        )

    @staticmethod
    def _advance_data_source_root(
        connection: sqlite3.Connection, current: DataSource, revised: DataSource
    ) -> None:
        cursor = connection.execute(
            """UPDATE src_datasource_roots
               SET current_revision = ?, lifecycle = ?, control_fence_revision = ?
               WHERE source_id = ? AND current_revision = ?""",
            (
                revised.definition_revision.value,
                revised.lifecycle.value,
                revised.control_fence_revision.value,
                current.source_id.value,
                current.definition_revision.value,
            ),
        )
        if cursor.rowcount != 1:
            raise DomainError(ErrorCode.REVISION_CONFLICT, "data source revision changed")

    @staticmethod
    def _advance_binding_root(
        connection: sqlite3.Connection,
        current: DataSourceBinding,
        revised: DataSourceBinding,
    ) -> None:
        cursor = connection.execute(
            """UPDATE src_binding_roots
               SET current_revision = ?, lifecycle = ?, effective_range_digest = ?
               WHERE binding_id = ? AND current_revision = ?""",
            (
                revised.definition_revision.value,
                revised.lifecycle.value,
                revised.effective_range_digest.value,
                current.binding_id.value,
                current.definition_revision.value,
            ),
        )
        if cursor.rowcount != 1:
            raise DomainError(ErrorCode.REVISION_CONFLICT, "binding revision changed")


def _require_revision(actual: Revision, expected: Revision, aggregate_id: StableId) -> None:
    if actual != expected:
        raise DomainError(
            ErrorCode.REVISION_CONFLICT,
            "expected definition revision is stale",
            {
                "aggregate_id": aggregate_id.value,
                "expected_revision": expected.value,
                "actual_revision": actual.value,
            },
        )


def _expect_source(value: DataSource | DataSourceBinding) -> DataSource:
    if not isinstance(value, DataSource):
        raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "idempotent result kind changed")
    return value


def _expect_binding(value: DataSource | DataSourceBinding) -> DataSourceBinding:
    if not isinstance(value, DataSourceBinding):
        raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, "idempotent result kind changed")
    return value


def _fields(value: str) -> CanonicalFields:
    raw = json.loads(value)
    return tuple((item[0], item[1]) for item in raw)


def _time(value: datetime) -> str:
    return value.isoformat(timespec="microseconds").replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _integrity_error(exc: sqlite3.IntegrityError) -> DomainError:
    message = str(exc)
    if "src_datasource_roots.provider_type" in message:
        return DomainError(
            ErrorCode.DATASOURCE_IDENTITY_CONFLICT,
            "the permanent data source identity is already occupied",
        )
    if "src_binding_roots.scope_id" in message:
        return DomainError(
            ErrorCode.BINDING_RANGE_CONFLICT,
            "an active binding already owns the equivalent effective range",
        )
    return DomainError(
        ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
        "source configuration transaction violated a store invariant",
        {"sqlite_error": message},
    )
