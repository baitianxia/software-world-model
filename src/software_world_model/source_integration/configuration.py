"""DataSource and DataSourceBinding owner contracts without source I/O."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Mapping, Protocol

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
from software_world_model.knowledge_engine import (
    AssertionOutcome,
    ScopeLifecycle,
    ScopePurpose,
    ScopeStateAssertion,
)


CanonicalFields = tuple[tuple[str, str], ...]
_PROHIBITED_CONFIGURATION_KEYS = {"api_key", "credential", "password", "secret", "token"}


def _nonempty(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def canonical_fields(
    values: Mapping[str, str] | CanonicalFields | None,
    *,
    label: str,
    reject_credentials: bool = False,
) -> CanonicalFields:
    if values is None:
        return ()
    items = values.items() if isinstance(values, Mapping) else values
    normalized: list[tuple[str, str]] = []
    for key, value in items:
        clean_key = _nonempty(key, f"{label} key")
        if not isinstance(value, str):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} values must be strings")
        if reject_credentials and clean_key.casefold() in _PROHIBITED_CONFIGURATION_KEYS:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                f"{label} cannot contain credential values; use a secret reference",
            )
        if len(clean_key.encode("utf-8")) > 128 or len(value.encode("utf-8")) > 4096:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} exceeds the supported size")
        normalized.append((clean_key, value))
    normalized.sort(key=lambda item: item[0])
    if len({key for key, _ in normalized}) != len(normalized):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} keys must be unique")
    return tuple(normalized)


class DataSourceLifecycle(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    RETIRED = "RETIRED"


class BindingLifecycle(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


@dataclass(frozen=True, slots=True)
class NormalizedDataSource:
    identity_strategy_version: str
    identity_domain: str
    canonical_source_target: str
    provider_configuration: CanonicalFields
    secret_reference: str | None


@dataclass(frozen=True, slots=True)
class NormalizedSelection:
    selector: CanonicalFields
    context_constraint: CanonicalFields

    @property
    def selector_digest(self) -> Digest:
        return digest_of({"selector": self.selector})

    @property
    def effective_range_digest(self) -> Digest:
        return digest_of(
            {"selector": self.selector, "context_constraint": self.context_constraint}
        )


class DataSourceProvider(Protocol):
    provider_type: str
    contract_version: str

    def normalize_data_source(
        self,
        *,
        identity_domain: str,
        source_target: str,
        provider_configuration: Mapping[str, str],
        secret_reference: str | None,
    ) -> NormalizedDataSource: ...

    def normalize_selection(
        self,
        *,
        selector: Mapping[str, str],
        context_constraint: Mapping[str, str],
    ) -> NormalizedSelection: ...


class ProviderRegistry:
    def __init__(self, providers: tuple[DataSourceProvider, ...] = ()) -> None:
        self._providers: dict[tuple[str, str], DataSourceProvider] = {}
        for provider in providers:
            self.register(provider)

    def register(self, provider: DataSourceProvider) -> None:
        provider_type = _nonempty(provider.provider_type, "provider type")
        contract_version = _nonempty(provider.contract_version, "provider contract version")
        key = (provider_type, contract_version)
        if key in self._providers:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "provider contract is already registered",
                {"provider_type": provider_type, "contract_version": contract_version},
            )
        self._providers[key] = provider

    def resolve(self, provider_type: str, contract_version: str) -> DataSourceProvider:
        key = (provider_type, contract_version)
        provider = self._providers.get(key)
        if provider is None:
            raise DomainError(
                ErrorCode.PROVIDER_CONTRACT_UNAVAILABLE,
                "exact provider contract is not registered",
                {"provider_type": provider_type, "contract_version": contract_version},
            )
        return provider


@dataclass(frozen=True, slots=True)
class DataSource:
    source_id: StableId
    provider_type: str
    provider_contract_version: str
    identity_strategy_version: str
    identity_domain: str
    canonical_source_target: str
    provider_configuration: CanonicalFields
    secret_reference: str | None
    lifecycle: DataSourceLifecycle
    definition_revision: Revision
    control_fence_revision: Revision
    created_at: datetime
    revised_at: datetime
    actor: str
    reason: str
    definition_digest: Digest


@dataclass(frozen=True, slots=True)
class DataSourceBinding:
    binding_id: StableId
    scope_id: StableId
    observed_scope_revision: Revision
    scope_assertion_id: StableId
    scope_assertion_digest: Digest
    source_id: StableId
    provider_contract_version: str
    selector: CanonicalFields
    selector_digest: Digest
    context_constraint: CanonicalFields
    context_hint: str | None
    effective_range_digest: Digest
    lifecycle: BindingLifecycle
    definition_revision: Revision
    created_at: datetime
    revised_at: datetime
    actor: str
    reason: str
    definition_digest: Digest


@dataclass(frozen=True, slots=True)
class BindingEligibilityAssertion:
    assertion_id: StableId
    binding_id: StableId
    binding_revision: Revision
    source_id: StableId
    source_revision: Revision
    scope_id: StableId
    scope_revision: Revision
    scope_assertion_id: StableId
    scope_assertion_digest: Digest
    provider_type: str
    provider_contract_version: str
    provider_configuration_fingerprint: Digest
    control_fence_revision: Revision
    selector: CanonicalFields
    context_constraint: CanonicalFields
    tool_id: str
    classification: str
    resolved_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class SourceOutboxEvent:
    event_id: StableId
    aggregate_kind: str
    aggregate_id: StableId
    authority_revision: Revision
    event_type: str
    payload_digest: Digest
    occurred_at: datetime


class KnowledgeScopeAssertionVerifier(Protocol):
    def validate_scope_state_assertion(self, assertion: ScopeStateAssertion) -> bool: ...


class SourceConfigurationRepository(Protocol):
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
    ) -> DataSource: ...

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
    ) -> DataSource: ...

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
    ) -> DataSource: ...

    def get_data_source(self, source_id: StableId, revision: Revision | None = None) -> DataSource: ...

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
    ) -> DataSourceBinding: ...

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
    ) -> DataSourceBinding: ...

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
    ) -> DataSourceBinding: ...

    def get_binding(
        self, binding_id: StableId, revision: Revision | None = None
    ) -> DataSourceBinding: ...

    def list_bindings(self, *, source_id: StableId | None = None) -> tuple[DataSourceBinding, ...]: ...

    def list_outbox(self) -> tuple[SourceOutboxEvent, ...]: ...


class SourceConfigurationService:
    def __init__(
        self,
        repository: SourceConfigurationRepository,
        providers: ProviderRegistry,
        scope_assertions: KnowledgeScopeAssertionVerifier,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._providers = providers
        self._scope_assertions = scope_assertions
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def register_data_source(
        self,
        *,
        provider_type: str,
        provider_contract_version: str,
        identity_domain: str,
        source_target: str,
        provider_configuration: Mapping[str, str],
        secret_reference: str | None,
        idempotency_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> DataSource:
        provider = self._providers.resolve(provider_type, provider_contract_version)
        normalized = self._validate_normalized_source(
            provider.normalize_data_source(
                identity_domain=identity_domain,
                source_target=source_target,
                provider_configuration=provider_configuration,
                secret_reference=secret_reference,
            )
        )
        actor = _nonempty(actor, "actor")
        reason = _nonempty(reason, "reason")
        request_digest = digest_of(
            {
                "command": "RegisterDataSource@1",
                "provider_type": provider_type,
                "provider_contract_version": provider_contract_version,
                "normalized": normalized,
                "actor": actor,
                "reason": reason,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.register_data_source(
            provider_type=provider_type,
            provider_contract_version=provider_contract_version,
            normalized=normalized,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def revise_data_source(
        self,
        *,
        source_id: StableId,
        expected_revision: Revision,
        provider_configuration: Mapping[str, str],
        secret_reference: str | None,
        idempotency_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> DataSource:
        current = self._repository.get_data_source(source_id)
        provider = self._providers.resolve(
            current.provider_type, current.provider_contract_version
        )
        normalized = self._validate_normalized_source(
            provider.normalize_data_source(
                identity_domain=current.identity_domain,
                source_target=current.canonical_source_target,
                provider_configuration=provider_configuration,
                secret_reference=secret_reference,
            )
        )
        if (
            normalized.identity_strategy_version != current.identity_strategy_version
            or normalized.identity_domain != current.identity_domain
            or normalized.canonical_source_target != current.canonical_source_target
        ):
            raise DomainError(
                ErrorCode.DATASOURCE_IDENTITY_CONFLICT,
                "a data source revision cannot change its permanent identity",
            )
        actor = _nonempty(actor, "actor")
        reason = _nonempty(reason, "reason")
        request_digest = digest_of(
            {
                "command": "ReviseDataSource@1",
                "source_id": source_id.value,
                "expected_revision": expected_revision.value,
                "normalized": normalized,
                "actor": actor,
                "reason": reason,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.revise_data_source(
            source_id=source_id,
            expected_revision=expected_revision,
            normalized=normalized,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def disable_data_source(self, **arguments: object) -> DataSource:
        return self._change_data_source_lifecycle(DataSourceLifecycle.DISABLED, **arguments)

    def enable_data_source(self, **arguments: object) -> DataSource:
        return self._change_data_source_lifecycle(DataSourceLifecycle.ACTIVE, **arguments)

    def retire_data_source(self, **arguments: object) -> DataSource:
        return self._change_data_source_lifecycle(DataSourceLifecycle.RETIRED, **arguments)

    def bind_source_to_scope(
        self,
        *,
        source_id: StableId,
        assertion: ScopeStateAssertion,
        selector: Mapping[str, str],
        context_constraint: Mapping[str, str] | None,
        context_hint: str | None,
        idempotency_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> DataSourceBinding:
        self._validate_scope_assertion(assertion, ScopePurpose.BIND_CONFIGURATION)
        source = self._repository.get_data_source(source_id)
        if source.lifecycle is DataSourceLifecycle.RETIRED:
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "retired data source cannot be bound")
        provider = self._providers.resolve(source.provider_type, source.provider_contract_version)
        selection = self._validate_selection(
            provider.normalize_selection(
                selector=selector, context_constraint=context_constraint or {}
            )
        )
        context_hint = self._optional_text(context_hint, "context hint")
        actor = _nonempty(actor, "actor")
        reason = _nonempty(reason, "reason")
        request_digest = digest_of(
            {
                "command": "BindSourceToScope@1",
                "source_id": source_id.value,
                "source_revision": source.definition_revision.value,
                "scope_assertion_id": assertion.assertion_id.value,
                "scope_assertion_digest": assertion.digest.value,
                "selection": selection,
                "context_hint": context_hint,
                "actor": actor,
                "reason": reason,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.bind_source(
            source=source,
            assertion=assertion,
            selection=selection,
            context_hint=context_hint,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def revise_binding(
        self,
        *,
        binding_id: StableId,
        expected_revision: Revision,
        assertion: ScopeStateAssertion,
        selector: Mapping[str, str],
        context_constraint: Mapping[str, str] | None,
        context_hint: str | None,
        idempotency_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> DataSourceBinding:
        self._validate_scope_assertion(assertion, ScopePurpose.BIND_CONFIGURATION)
        current = self._repository.get_binding(binding_id)
        if current.scope_id != assertion.scope_id:
            raise DomainError(ErrorCode.SCOPE_ASSERTION_INVALID, "assertion scope does not match binding")
        source = self._repository.get_data_source(current.source_id)
        provider = self._providers.resolve(source.provider_type, source.provider_contract_version)
        selection = self._validate_selection(
            provider.normalize_selection(
                selector=selector, context_constraint=context_constraint or {}
            )
        )
        context_hint = self._optional_text(context_hint, "context hint")
        actor = _nonempty(actor, "actor")
        reason = _nonempty(reason, "reason")
        request_digest = digest_of(
            {
                "command": "ReviseBinding@1",
                "binding_id": binding_id.value,
                "expected_revision": expected_revision.value,
                "scope_assertion_id": assertion.assertion_id.value,
                "scope_assertion_digest": assertion.digest.value,
                "selection": selection,
                "context_hint": context_hint,
                "actor": actor,
                "reason": reason,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.revise_binding(
            binding_id=binding_id,
            expected_revision=expected_revision,
            selection=selection,
            context_hint=context_hint,
            assertion=assertion,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def suspend_binding(self, **arguments: object) -> DataSourceBinding:
        return self._change_binding_lifecycle(BindingLifecycle.SUSPENDED, **arguments)

    def resume_binding(self, **arguments: object) -> DataSourceBinding:
        return self._change_binding_lifecycle(BindingLifecycle.ACTIVE, **arguments)

    def retire_binding(self, **arguments: object) -> DataSourceBinding:
        return self._change_binding_lifecycle(BindingLifecycle.RETIRED, **arguments)

    def get_data_source(self, source_id: StableId, revision: Revision | None = None) -> DataSource:
        return self._repository.get_data_source(source_id, revision)

    def get_binding(
        self, binding_id: StableId, revision: Revision | None = None
    ) -> DataSourceBinding:
        return self._repository.get_binding(binding_id, revision)

    def list_bindings(self, *, source_id: StableId | None = None) -> tuple[DataSourceBinding, ...]:
        return self._repository.list_bindings(source_id=source_id)

    def list_outbox_events(self) -> tuple[SourceOutboxEvent, ...]:
        return self._repository.list_outbox()

    def resolve_binding_for_execution(
        self,
        *,
        binding_id: StableId,
        expected_binding_revision: Revision,
        expected_source_revision: Revision,
        assertion: ScopeStateAssertion,
        tool_id: str,
        classification: str,
    ) -> BindingEligibilityAssertion:
        self._validate_scope_assertion(assertion, ScopePurpose.SOURCE_EXECUTION)
        binding = self._repository.get_binding(binding_id)
        source = self._repository.get_data_source(binding.source_id)
        if binding.definition_revision != expected_binding_revision:
            raise DomainError(ErrorCode.REVISION_CONFLICT, "binding execution revision is stale")
        if source.definition_revision != expected_source_revision:
            raise DomainError(ErrorCode.REVISION_CONFLICT, "source execution revision is stale")
        if binding.scope_id != assertion.scope_id or binding.observed_scope_revision != assertion.definition_revision:
            raise DomainError(
                ErrorCode.SCOPE_ASSERTION_INVALID,
                "scope assertion does not match the binding definition closure",
            )
        if binding.lifecycle is not BindingLifecycle.ACTIVE or source.lifecycle is not DataSourceLifecycle.ACTIVE:
            raise DomainError(ErrorCode.CONTROL_STATE_DENIED, "source or binding is not active")
        provider = self._providers.resolve(source.provider_type, source.provider_contract_version)
        supported_tools = tuple(getattr(provider, "connector_tools", ()))
        tool_id = _nonempty(tool_id, "tool ID")
        if tool_id not in supported_tools:
            raise DomainError(
                ErrorCode.PROVIDER_CONTRACT_UNAVAILABLE,
                "tool is not included by the exact provider contract",
                {"tool_id": tool_id},
            )
        classification = _nonempty(classification, "classification")
        resolved_at = self._now()
        # resolved_at is diagnostic observation metadata, not part of the
        # authority closure. A retry over the same exact revisions, assertion,
        # configuration, selector, tool, and classification must yield the same
        # eligibility identity so the original source operation can be replayed.
        core = {
            "binding_id": binding.binding_id.value,
            "binding_revision": binding.definition_revision.value,
            "source_id": source.source_id.value,
            "source_revision": source.definition_revision.value,
            "scope_id": binding.scope_id.value,
            "scope_revision": assertion.definition_revision.value,
            "scope_assertion_id": assertion.assertion_id.value,
            "scope_assertion_digest": assertion.digest.value,
            "provider_type": source.provider_type,
            "provider_contract_version": source.provider_contract_version,
            "provider_configuration_fingerprint": digest_of(
                {
                    "configuration": source.provider_configuration,
                    "secret_reference": source.secret_reference,
                }
            ).value,
            "control_fence_revision": source.control_fence_revision.value,
            "selector": binding.selector,
            "context_constraint": binding.context_constraint,
            "tool_id": tool_id,
            "classification": classification,
        }
        assertion_digest = digest_of(core)
        return BindingEligibilityAssertion(
            assertion_id=StableId(f"binding_eligibility_{assertion_digest.value[-32:]}"),
            binding_id=binding.binding_id,
            binding_revision=binding.definition_revision,
            source_id=source.source_id,
            source_revision=source.definition_revision,
            scope_id=binding.scope_id,
            scope_revision=assertion.definition_revision,
            scope_assertion_id=assertion.assertion_id,
            scope_assertion_digest=assertion.digest,
            provider_type=source.provider_type,
            provider_contract_version=source.provider_contract_version,
            provider_configuration_fingerprint=Digest(core["provider_configuration_fingerprint"]),
            control_fence_revision=source.control_fence_revision,
            selector=binding.selector,
            context_constraint=binding.context_constraint,
            tool_id=tool_id,
            classification=classification,
            resolved_at=resolved_at,
            digest=assertion_digest,
        )

    def validate_binding_eligibility(
        self,
        eligibility: BindingEligibilityAssertion,
        scope_assertion: ScopeStateAssertion,
    ) -> bool:
        try:
            current = self.resolve_binding_for_execution(
                binding_id=eligibility.binding_id,
                expected_binding_revision=eligibility.binding_revision,
                expected_source_revision=eligibility.source_revision,
                assertion=scope_assertion,
                tool_id=eligibility.tool_id,
                classification=eligibility.classification,
            )
        except DomainError:
            return False
        # resolved_at and assertion identity are observational; compare the full
        # authority closure that controls dispatch.
        return (
            current.binding_id == eligibility.binding_id
            and current.binding_revision == eligibility.binding_revision
            and current.source_id == eligibility.source_id
            and current.source_revision == eligibility.source_revision
            and current.scope_assertion_id == eligibility.scope_assertion_id
            and current.scope_assertion_digest == eligibility.scope_assertion_digest
            and current.provider_configuration_fingerprint
            == eligibility.provider_configuration_fingerprint
            and current.control_fence_revision == eligibility.control_fence_revision
            and current.selector == eligibility.selector
            and current.context_constraint == eligibility.context_constraint
            and current.tool_id == eligibility.tool_id
        )

    def _change_data_source_lifecycle(
        self,
        target: DataSourceLifecycle,
        *,
        source_id: StableId,
        expected_revision: Revision,
        idempotency_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> DataSource:
        actor = _nonempty(actor, "actor")
        reason = _nonempty(reason, "reason")
        request_digest = digest_of(
            {
                "command": f"{target.value.title()}DataSource@1",
                "source_id": source_id.value,
                "expected_revision": expected_revision.value,
                "target": target.value,
                "actor": actor,
                "reason": reason,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.change_data_source_lifecycle(
            source_id=source_id,
            expected_revision=expected_revision,
            target=target,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def _change_binding_lifecycle(
        self,
        target: BindingLifecycle,
        *,
        binding_id: StableId,
        expected_revision: Revision,
        idempotency_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> DataSourceBinding:
        actor = _nonempty(actor, "actor")
        reason = _nonempty(reason, "reason")
        request_digest = digest_of(
            {
                "command": f"{target.value.title()}Binding@1",
                "binding_id": binding_id.value,
                "expected_revision": expected_revision.value,
                "target": target.value,
                "actor": actor,
                "reason": reason,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.change_binding_lifecycle(
            binding_id=binding_id,
            expected_revision=expected_revision,
            target=target,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            occurred_at=self._now(),
        )

    def _validate_scope_assertion(
        self, assertion: ScopeStateAssertion, purpose: ScopePurpose
    ) -> None:
        if (
            not self._scope_assertions.validate_scope_state_assertion(assertion)
            or assertion.purpose is not purpose
            or assertion.outcome is not AssertionOutcome.ELIGIBLE
            or assertion.lifecycle is not ScopeLifecycle.ACTIVE
        ):
            raise DomainError(
                ErrorCode.SCOPE_ASSERTION_INVALID,
                "scope assertion is unknown, stale in meaning, or ineligible for this command",
            )

    @staticmethod
    def _validate_normalized_source(normalized: NormalizedDataSource) -> NormalizedDataSource:
        return NormalizedDataSource(
            identity_strategy_version=_nonempty(
                normalized.identity_strategy_version, "identity strategy version"
            ),
            identity_domain=_nonempty(normalized.identity_domain, "identity domain"),
            canonical_source_target=_nonempty(
                normalized.canonical_source_target, "canonical source target"
            ),
            provider_configuration=canonical_fields(
                normalized.provider_configuration,
                label="provider configuration",
                reject_credentials=True,
            ),
            secret_reference=(
                _nonempty(normalized.secret_reference, "secret reference")
                if normalized.secret_reference is not None
                else None
            ),
        )

    @staticmethod
    def _validate_selection(selection: NormalizedSelection) -> NormalizedSelection:
        normalized = NormalizedSelection(
            selector=canonical_fields(selection.selector, label="selector"),
            context_constraint=canonical_fields(
                selection.context_constraint, label="context constraint"
            ),
        )
        if not normalized.selector:
            raise DomainError(ErrorCode.SELECTOR_INVALID, "selector cannot be empty")
        return normalized

    @staticmethod
    def _optional_text(value: str | None, label: str) -> str | None:
        return _nonempty(value, label) if value is not None else None

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return a timezone-aware datetime")
        return value.astimezone(timezone.utc)
