"""Capability registry and fail-closed Strategy Activation control."""

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


ActivationScope = tuple[tuple[str, str], ...]


def _nonempty(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value


def normalize_activation_scope(scope: Mapping[str, str]) -> ActivationScope:
    normalized: list[tuple[str, str]] = []
    for key, value in scope.items():
        normalized.append(
            (_nonempty(key, "activation scope key"), _nonempty(value, "activation scope value"))
        )
    normalized.sort(key=lambda item: item[0])
    if not normalized or len({key for key, _ in normalized}) != len(normalized):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "activation scope must have at least one unique stable dimension",
        )
    return tuple(normalized)


class StrategyKind(str, Enum):
    DETERMINISTIC = "DETERMINISTIC"
    MODEL_PRIMARY = "MODEL_PRIMARY"
    HYBRID = "HYBRID"


@dataclass(frozen=True, slots=True)
class CapabilityDefinition:
    capability_id: str
    contract_version: str
    purpose: str
    input_contract_digest: Digest
    output_contract_digest: Digest


@dataclass(frozen=True, slots=True)
class StrategyDefinition:
    strategy_id: str
    strategy_version: str
    capability_id: str
    capability_contract_version: str
    kind: StrategyKind
    implementation_digest: Digest
    requires_model: bool

    def __post_init__(self) -> None:
        if self.kind is StrategyKind.MODEL_PRIMARY and not self.requires_model:
            raise ValueError("MODEL_PRIMARY strategies must require a model")
        if self.kind is StrategyKind.DETERMINISTIC and self.requires_model:
            raise ValueError("DETERMINISTIC strategies cannot require a model")


class CapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities: dict[tuple[str, str], CapabilityDefinition] = {}
        self._strategies: dict[tuple[str, str], StrategyDefinition] = {}

    def register_capability(self, definition: CapabilityDefinition) -> None:
        key = (
            _nonempty(definition.capability_id, "capability ID"),
            _nonempty(definition.contract_version, "capability contract version"),
        )
        existing = self._capabilities.get(key)
        if existing is not None and existing != definition:
            raise DomainError(
                ErrorCode.CAPABILITY_CONTRACT_CONFLICT,
                "capability version was registered with different semantics",
            )
        self._capabilities[key] = definition

    def register_strategy(self, definition: StrategyDefinition) -> None:
        capability_key = (definition.capability_id, definition.capability_contract_version)
        if capability_key not in self._capabilities:
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "strategy references an unregistered capability contract",
            )
        key = (
            _nonempty(definition.strategy_id, "strategy ID"),
            _nonempty(definition.strategy_version, "strategy version"),
        )
        existing = self._strategies.get(key)
        if existing is not None and existing != definition:
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "strategy version was registered with different semantics",
            )
        self._strategies[key] = definition

    def resolve_capability(self, capability_id: str, contract_version: str) -> CapabilityDefinition:
        definition = self._capabilities.get((capability_id, contract_version))
        if definition is None:
            raise DomainError(
                ErrorCode.CAPABILITY_CONTRACT_CONFLICT,
                "exact capability contract is not registered",
            )
        return definition

    def resolve_strategy(self, strategy_id: str, strategy_version: str) -> StrategyDefinition:
        definition = self._strategies.get((strategy_id, strategy_version))
        if definition is None:
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "exact strategy version is not registered",
            )
        return definition


@dataclass(frozen=True, slots=True)
class QualificationProof:
    proof_ref: str
    capability_id: str
    capability_contract_version: str
    strategy_id: str
    strategy_version: str
    result_ref: str
    validity_ref: str
    qualification_kind: str
    digest: Digest

    def core(self) -> dict[str, str]:
        return {
            "proof_ref": self.proof_ref,
            "capability_id": self.capability_id,
            "capability_contract_version": self.capability_contract_version,
            "strategy_id": self.strategy_id,
            "strategy_version": self.strategy_version,
            "result_ref": self.result_ref,
            "validity_ref": self.validity_ref,
            "qualification_kind": self.qualification_kind,
        }

    def verify_digest(self) -> bool:
        return digest_of(self.core()) == self.digest


class QualificationVerifier(Protocol):
    def validate(self, proof: QualificationProof) -> bool: ...


class RejectAllQualifications:
    """Safe default until an evaluation owner is wired."""

    def validate(self, proof: QualificationProof) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class LiveIntegrationPolicy:
    model_strategy_activation_enabled: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.model_strategy_activation_enabled, bool):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "model strategy activation policy must be boolean",
            )


class ActivationDecisionType(str, Enum):
    ACTIVATE = "ACTIVATE"
    REPLACE = "REPLACE"
    DEACTIVATE = "DEACTIVATE"


@dataclass(frozen=True, slots=True)
class ActivationDecision:
    decision_id: StableId
    capability_id: str
    capability_contract_version: str
    activation_scope: ActivationScope
    decision_type: ActivationDecisionType
    activation_revision: Revision
    strategy_id: str | None
    strategy_version: str | None
    qualification: QualificationProof | None
    previous_decision_id: StableId | None
    actor: str
    reason: str
    decided_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class ResolvedStrategy:
    capability: CapabilityDefinition
    strategy: StrategyDefinition
    decision: ActivationDecision


class StrategyActivationRepository(Protocol):
    def append_decision(
        self,
        *,
        capability_id: str,
        capability_contract_version: str,
        activation_scope: ActivationScope,
        decision_type: ActivationDecisionType,
        expected_revision: Revision | None,
        strategy: StrategyDefinition | None,
        qualification: QualificationProof | None,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
        decided_at: datetime,
    ) -> ActivationDecision: ...

    def get_current(
        self,
        *,
        capability_id: str,
        capability_contract_version: str,
        activation_scope: ActivationScope,
    ) -> ActivationDecision | None: ...


class StrategyActivationService:
    def __init__(
        self,
        repository: StrategyActivationRepository,
        registry: CapabilityRegistry,
        qualification_verifier: QualificationVerifier | None = None,
        *,
        live_policy: LiveIntegrationPolicy | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._registry = registry
        self._qualifications = qualification_verifier or RejectAllQualifications()
        self._live_policy = live_policy or LiveIntegrationPolicy()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def activate_strategy(self, **arguments: object) -> ActivationDecision:
        return self._activate(ActivationDecisionType.ACTIVATE, **arguments)

    def replace_strategy(self, **arguments: object) -> ActivationDecision:
        return self._activate(ActivationDecisionType.REPLACE, **arguments)

    def deactivate_strategy(
        self,
        *,
        capability_id: str,
        capability_contract_version: str,
        activation_scope: Mapping[str, str],
        expected_revision: Revision,
        idempotency_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> ActivationDecision:
        scope = normalize_activation_scope(activation_scope)
        self._registry.resolve_capability(capability_id, capability_contract_version)
        actor = _nonempty(actor, "actor")
        reason = _nonempty(reason, "reason")
        request_digest = digest_of(
            {
                "command": "DeactivateStrategy@1",
                "capability_id": capability_id,
                "capability_contract_version": capability_contract_version,
                "activation_scope": scope,
                "expected_revision": expected_revision.value,
                "actor": actor,
                "reason": reason,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.append_decision(
            capability_id=capability_id,
            capability_contract_version=capability_contract_version,
            activation_scope=scope,
            decision_type=ActivationDecisionType.DEACTIVATE,
            expected_revision=expected_revision,
            strategy=None,
            qualification=None,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            decided_at=self._now(),
        )

    def resolve_strategy(
        self,
        *,
        capability_id: str,
        capability_contract_version: str,
        activation_scope: Mapping[str, str],
    ) -> ResolvedStrategy:
        scope = normalize_activation_scope(activation_scope)
        capability = self._registry.resolve_capability(
            capability_id, capability_contract_version
        )
        decision = self._repository.get_current(
            capability_id=capability_id,
            capability_contract_version=capability_contract_version,
            activation_scope=scope,
        )
        if decision is None or decision.decision_type is ActivationDecisionType.DEACTIVATE:
            raise DomainError(ErrorCode.NO_ACTIVE_STRATEGY, "activation scope has no active strategy")
        assert decision.strategy_id is not None
        assert decision.strategy_version is not None
        assert decision.qualification is not None
        strategy = self._registry.resolve_strategy(
            decision.strategy_id, decision.strategy_version
        )
        self._validate_strategy(capability, strategy, decision.qualification)
        return ResolvedStrategy(capability=capability, strategy=strategy, decision=decision)

    def _activate(
        self,
        decision_type: ActivationDecisionType,
        *,
        capability_id: str,
        capability_contract_version: str,
        activation_scope: Mapping[str, str],
        expected_revision: Revision | None,
        strategy_id: str,
        strategy_version: str,
        qualification: QualificationProof,
        idempotency_key: IdempotencyKey,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> ActivationDecision:
        capability = self._registry.resolve_capability(
            capability_id, capability_contract_version
        )
        strategy = self._registry.resolve_strategy(strategy_id, strategy_version)
        self._validate_strategy(capability, strategy, qualification)
        if decision_type is ActivationDecisionType.REPLACE and expected_revision is None:
            raise DomainError(
                ErrorCode.ACTIVATION_CONFLICT,
                "replacement requires the exact current activation revision",
            )
        scope = normalize_activation_scope(activation_scope)
        actor = _nonempty(actor, "actor")
        reason = _nonempty(reason, "reason")
        request_digest = digest_of(
            {
                "command": f"{decision_type.value.title()}Strategy@1",
                "capability_id": capability_id,
                "capability_contract_version": capability_contract_version,
                "activation_scope": scope,
                "expected_revision": expected_revision.value if expected_revision else None,
                "strategy_id": strategy_id,
                "strategy_version": strategy_version,
                "qualification_digest": qualification.digest.value,
                "actor": actor,
                "reason": reason,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.append_decision(
            capability_id=capability_id,
            capability_contract_version=capability_contract_version,
            activation_scope=scope,
            decision_type=decision_type,
            expected_revision=expected_revision,
            strategy=strategy,
            qualification=qualification,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            reason=reason,
            correlation_ref=correlation_ref,
            decided_at=self._now(),
        )

    def _validate_strategy(
        self,
        capability: CapabilityDefinition,
        strategy: StrategyDefinition,
        qualification: QualificationProof,
    ) -> None:
        if (
            strategy.capability_id != capability.capability_id
            or strategy.capability_contract_version != capability.contract_version
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "strategy does not implement the requested capability contract",
            )
        if strategy.requires_model and not self._live_policy.model_strategy_activation_enabled:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "model strategy activation is disabled until live integration passes",
            )
        if strategy.requires_model and qualification.qualification_kind != "CAPABILITY_EVALUATION":
            raise DomainError(
                ErrorCode.ACTIVATION_WITHOUT_PASS,
                "model strategy activation requires a current PASS capability evaluation",
            )
        if (
            not qualification.verify_digest()
            or qualification.capability_id != capability.capability_id
            or qualification.capability_contract_version != capability.contract_version
            or qualification.strategy_id != strategy.strategy_id
            or qualification.strategy_version != strategy.strategy_version
            or not self._qualifications.validate(qualification)
        ):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "strategy qualification is absent, invalid, or no longer current",
            )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return a timezone-aware datetime")
        return value.astimezone(timezone.utc)
