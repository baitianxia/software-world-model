"""Capability Evaluation runs, immutable results, validity, and qualification."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Protocol

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

from .activation import CapabilityRegistry, QualificationProof


class EvaluationConclusion(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class EvaluationRunState(str, Enum):
    PREPARED = "PREPARED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    OUTCOME_PENDING = "OUTCOME_PENDING"


class EvaluationAttemptState(str, Enum):
    DISPATCHED = "DISPATCHED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"


class EvaluationValidityStatus(str, Enum):
    VALID = "VALID"
    STALE = "STALE"
    REVOKED = "REVOKED"


@dataclass(frozen=True, slots=True)
class EvaluationQualificationDependencies:
    strategy_implementation_digest: Digest
    conformance_result_ref: str
    provider_configuration_fingerprint: Digest
    model_ref: str
    adapter_version: str

    @classmethod
    def from_definition(
        cls, definition: "EvaluationDefinition"
    ) -> "EvaluationQualificationDependencies":
        return cls(
            strategy_implementation_digest=definition.implementation_digest,
            conformance_result_ref=definition.conformance_result_ref,
            provider_configuration_fingerprint=(
                definition.provider_configuration_fingerprint
            ),
            model_ref=definition.model_ref,
            adapter_version=definition.adapter_version,
        )

    def __post_init__(self) -> None:
        _text(self.conformance_result_ref, "conformance result reference")
        _text(self.model_ref, "model reference")
        _text(self.adapter_version, "adapter version")


@dataclass(frozen=True, slots=True)
class EvaluationCaseDefinition:
    case_id: str
    case_version: str
    fixture_ref: str
    fixture_digest: Digest
    oracle_ref: str
    oracle_digest: Digest
    required: bool = True

    def __post_init__(self) -> None:
        for value, label in (
            (self.case_id, "evaluation case ID"),
            (self.case_version, "evaluation case version"),
            (self.fixture_ref, "fixture reference"),
            (self.oracle_ref, "oracle reference"),
        ):
            _text(value, label)


@dataclass(frozen=True, slots=True)
class EvaluationDefinition:
    evaluation_id: str
    evaluation_version: str
    capability_id: str
    capability_contract_version: str
    strategy_id: str
    strategy_version: str
    design_baseline_ref: str
    implementation_digest: Digest
    conformance_result_ref: str
    provider_configuration_fingerprint: Digest
    model_ref: str
    adapter_version: str
    prompt_program_ref: str
    prompt_program_digest: Digest
    output_schema_ref: str
    output_schema_digest: Digest
    tool_policy_ref: str
    data_source_revision_ref: str
    environment_ref: str
    reference_strategy_ref: str
    resource_policy_ref: str
    metric_contract_digest: Digest
    threshold_ref: str
    cases: tuple[EvaluationCaseDefinition, ...]
    valid_for_seconds: int
    digest: Digest

    @classmethod
    def create(
        cls,
        *,
        evaluation_id: str,
        evaluation_version: str,
        capability_id: str,
        capability_contract_version: str,
        strategy_id: str,
        strategy_version: str,
        design_baseline_ref: str,
        implementation_digest: Digest,
        conformance_result_ref: str,
        provider_configuration_fingerprint: Digest,
        model_ref: str,
        adapter_version: str,
        prompt_program_ref: str,
        prompt_program_digest: Digest,
        output_schema_ref: str,
        output_schema_digest: Digest,
        tool_policy_ref: str,
        data_source_revision_ref: str,
        environment_ref: str,
        reference_strategy_ref: str,
        resource_policy_ref: str,
        metric_contract_digest: Digest,
        threshold_ref: str,
        cases: tuple[EvaluationCaseDefinition, ...],
        valid_for_seconds: int,
    ) -> "EvaluationDefinition":
        values = {
            "evaluation_id": evaluation_id,
            "evaluation_version": evaluation_version,
            "capability_id": capability_id,
            "capability_contract_version": capability_contract_version,
            "strategy_id": strategy_id,
            "strategy_version": strategy_version,
            "design_baseline_ref": design_baseline_ref,
            "conformance_result_ref": conformance_result_ref,
            "model_ref": model_ref,
            "adapter_version": adapter_version,
            "prompt_program_ref": prompt_program_ref,
            "output_schema_ref": output_schema_ref,
            "tool_policy_ref": tool_policy_ref,
            "data_source_revision_ref": data_source_revision_ref,
            "environment_ref": environment_ref,
            "reference_strategy_ref": reference_strategy_ref,
            "resource_policy_ref": resource_policy_ref,
            "threshold_ref": threshold_ref,
        }
        for label, value in values.items():
            _text(value, label.replace("_", " "))
        if not cases or not any(item.required for item in cases):
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "evaluation definition requires at least one required case",
            )
        if len({item.case_id for item in cases}) != len(cases):
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "evaluation case IDs must be unique",
            )
        if isinstance(valid_for_seconds, bool) or valid_for_seconds < 1:
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "evaluation validity duration must be positive",
            )
        core = {
            **values,
            "implementation_digest": implementation_digest.value,
            "provider_configuration_fingerprint": provider_configuration_fingerprint.value,
            "prompt_program_digest": prompt_program_digest.value,
            "output_schema_digest": output_schema_digest.value,
            "metric_contract_digest": metric_contract_digest.value,
            "cases": cases,
            "valid_for_seconds": valid_for_seconds,
        }
        return cls(
            **values,
            implementation_digest=implementation_digest,
            provider_configuration_fingerprint=provider_configuration_fingerprint,
            prompt_program_digest=prompt_program_digest,
            output_schema_digest=output_schema_digest,
            metric_contract_digest=metric_contract_digest,
            cases=cases,
            valid_for_seconds=valid_for_seconds,
            digest=digest_of(core),
        )


@dataclass(frozen=True, slots=True)
class EvaluationRun:
    run_id: StableId
    revision: Revision
    state: EvaluationRunState
    definition_digest: Digest
    evaluation_id: str
    evaluation_version: str
    strategy_id: str
    strategy_version: str
    evaluation_sink_ref: str
    root_allocation_ref: str
    evaluation_only_qualification: QualificationProof
    request_digest: Digest
    created_at: datetime
    revised_at: datetime


@dataclass(frozen=True, slots=True)
class EvaluationCaseAttempt:
    attempt_id: StableId
    revision: Revision
    run_id: StableId
    case_id: str
    attempt_key: str
    request_digest: Digest
    state: EvaluationAttemptState
    conclusion: EvaluationConclusion | None
    output_ref: str | None
    output_digest: Digest | None
    sink_manifest_ref: str | None
    sink_manifest_digest: Digest | None
    oracle_ref: str | None
    oracle_digest: Digest | None
    actual_model_fingerprint: str | None
    provider_request_id: str | None
    input_tokens: int | None
    output_tokens: int | None
    usage_complete: bool
    failure_code: str | None
    created_at: datetime
    revised_at: datetime


@dataclass(frozen=True, slots=True)
class CaseExecutionEvidence:
    conclusion: EvaluationConclusion
    output_ref: str
    output_digest: Digest
    sink_manifest_ref: str
    sink_manifest_digest: Digest
    oracle_ref: str
    oracle_digest: Digest
    actual_model_fingerprint: str
    provider_request_id: str
    input_tokens: int
    output_tokens: int
    usage_complete: bool

    def __post_init__(self) -> None:
        for value, label in (
            (self.output_ref, "evaluation output reference"),
            (self.sink_manifest_ref, "evaluation sink manifest reference"),
            (self.oracle_ref, "evaluation oracle reference"),
            (self.actual_model_fingerprint, "actual model fingerprint"),
            (self.provider_request_id, "provider request ID"),
        ):
            _text(value, label)
        for value, label in (
            (self.input_tokens, "input tokens"),
            (self.output_tokens, "output tokens"),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-negative")


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    result_id: StableId
    run_id: StableId
    definition_digest: Digest
    conclusion: EvaluationConclusion
    case_attempt_ids: tuple[StableId, ...]
    passed_case_ids: tuple[str, ...]
    failed_case_ids: tuple[str, ...]
    inconclusive_case_ids: tuple[str, ...]
    actual_model_fingerprints: tuple[str, ...]
    input_tokens: int
    output_tokens: int
    completed_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class EvaluationValidityDecision:
    validity_id: StableId
    result_id: StableId
    revision: Revision
    status: EvaluationValidityStatus
    dependency_digest: Digest
    valid_until: datetime
    authority: str
    reason: str
    decided_at: datetime
    digest: Digest


@dataclass(frozen=True, slots=True)
class EvaluationCompletion:
    run: EvaluationRun
    result: EvaluationResult
    validity: EvaluationValidityDecision
    qualification: QualificationProof | None


class CapabilityEvaluationRepository(Protocol):
    def register_definition(self, definition: EvaluationDefinition) -> EvaluationDefinition: ...

    def prepare_run(
        self,
        *,
        definition: EvaluationDefinition,
        evaluation_sink_ref: str,
        root_allocation_ref: str,
        idempotency_key: IdempotencyKey,
        request_digest: Digest,
        actor: str,
        correlation_ref: CorrelationRef,
        occurred_at: datetime,
    ) -> EvaluationRun: ...

    def start_run(
        self, *, run_id: StableId, expected_revision: Revision, occurred_at: datetime
    ) -> EvaluationRun: ...

    def dispatch_case(
        self,
        *,
        run_id: StableId,
        expected_run_revision: Revision,
        case_id: str,
        attempt_key: str,
        request_digest: Digest,
        occurred_at: datetime,
    ) -> tuple[EvaluationRun, EvaluationCaseAttempt]: ...

    def complete_case(
        self,
        *,
        attempt_id: StableId,
        expected_attempt_revision: Revision,
        evidence: CaseExecutionEvidence,
        occurred_at: datetime,
    ) -> EvaluationCaseAttempt: ...

    def mark_case_outcome_unknown(
        self,
        *,
        attempt_id: StableId,
        expected_attempt_revision: Revision,
        provider_request_id: str | None,
        occurred_at: datetime,
    ) -> EvaluationCaseAttempt: ...

    def resolve_case_failure(
        self,
        *,
        attempt_id: StableId,
        expected_attempt_revision: Revision,
        failure_code: str,
        occurred_at: datetime,
    ) -> EvaluationCaseAttempt: ...

    def finalize_run(
        self,
        *,
        run_id: StableId,
        expected_run_revision: Revision,
        actor: str,
        reason: str,
        occurred_at: datetime,
    ) -> EvaluationCompletion: ...

    def invalidate_result(
        self,
        *,
        result_id: StableId,
        expected_validity_revision: Revision,
        status: EvaluationValidityStatus,
        authority: str,
        reason: str,
        occurred_at: datetime,
    ) -> EvaluationValidityDecision: ...

    def validate_qualification(
        self,
        proof: QualificationProof,
        at: datetime,
        dependencies: EvaluationQualificationDependencies,
    ) -> bool: ...

    def get_run(self, run_id: StableId) -> EvaluationRun: ...

    def get_attempt(self, attempt_id: StableId) -> EvaluationCaseAttempt: ...

    def get_definition(self, digest: Digest) -> EvaluationDefinition: ...


class AdapterConformanceVerifier(Protocol):
    def validate(self, definition: EvaluationDefinition, at: datetime) -> bool: ...


class RejectAllAdapterConformance:
    def validate(self, definition: EvaluationDefinition, at: datetime) -> bool:
        return False


class CapabilityEvaluationService:
    def __init__(
        self,
        repository: CapabilityEvaluationRepository,
        registry: CapabilityRegistry,
        conformance_verifier: AdapterConformanceVerifier | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._registry = registry
        self._conformance = conformance_verifier or RejectAllAdapterConformance()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def register_definition(self, definition: EvaluationDefinition) -> EvaluationDefinition:
        capability = self._registry.resolve_capability(
            definition.capability_id, definition.capability_contract_version
        )
        strategy = self._registry.resolve_strategy(
            definition.strategy_id, definition.strategy_version
        )
        if (
            strategy.capability_id != capability.capability_id
            or strategy.capability_contract_version != capability.contract_version
            or strategy.implementation_digest != definition.implementation_digest
            or not strategy.requires_model
        ):
            raise DomainError(
                ErrorCode.STRATEGY_CONTRACT_MISMATCH,
                "evaluation definition does not match the registered model strategy",
            )
        if not self._conformance.validate(definition, self._now()):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "evaluation definition does not reference current live adapter conformance",
            )
        return self._repository.register_definition(definition)

    def get_run(self, run_id: StableId) -> EvaluationRun:
        return self._repository.get_run(run_id)

    def get_attempt(self, attempt_id: StableId) -> EvaluationCaseAttempt:
        return self._repository.get_attempt(attempt_id)

    def prepare_run(
        self,
        *,
        definition: EvaluationDefinition,
        evaluation_sink_ref: str,
        root_allocation_ref: str,
        idempotency_key: IdempotencyKey,
        actor: str,
        correlation_ref: CorrelationRef,
    ) -> EvaluationRun:
        _text(evaluation_sink_ref, "evaluation sink reference")
        _text(root_allocation_ref, "root allocation reference")
        _text(actor, "actor")
        occurred_at = self._now()
        if not self._conformance.validate(definition, occurred_at):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "adapter conformance is not current for a new evaluation run",
            )
        request_digest = digest_of(
            {
                "command": "PrepareEvaluationRun@1",
                "definition_digest": definition.digest.value,
                "evaluation_sink_ref": evaluation_sink_ref,
                "root_allocation_ref": root_allocation_ref,
                "actor": actor,
                "correlation_ref": correlation_ref.value,
            }
        )
        return self._repository.prepare_run(
            definition=definition,
            evaluation_sink_ref=evaluation_sink_ref,
            root_allocation_ref=root_allocation_ref,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            actor=actor,
            correlation_ref=correlation_ref,
            occurred_at=occurred_at,
        )

    def start_run(self, run: EvaluationRun) -> EvaluationRun:
        return self._repository.start_run(
            run_id=run.run_id,
            expected_revision=run.revision,
            occurred_at=self._now(),
        )

    def dispatch_case(
        self,
        *,
        run: EvaluationRun,
        case_id: str,
        attempt_key: str,
        request_digest: Digest,
    ) -> tuple[EvaluationRun, EvaluationCaseAttempt]:
        _text(case_id, "evaluation case ID")
        _text(attempt_key, "evaluation attempt key")
        return self._repository.dispatch_case(
            run_id=run.run_id,
            expected_run_revision=run.revision,
            case_id=case_id,
            attempt_key=attempt_key,
            request_digest=request_digest,
            occurred_at=self._now(),
        )

    def complete_case(
        self, attempt: EvaluationCaseAttempt, evidence: CaseExecutionEvidence
    ) -> EvaluationCaseAttempt:
        return self._repository.complete_case(
            attempt_id=attempt.attempt_id,
            expected_attempt_revision=attempt.revision,
            evidence=evidence,
            occurred_at=self._now(),
        )

    def mark_case_outcome_unknown(
        self, attempt: EvaluationCaseAttempt, provider_request_id: str | None
    ) -> EvaluationCaseAttempt:
        return self._repository.mark_case_outcome_unknown(
            attempt_id=attempt.attempt_id,
            expected_attempt_revision=attempt.revision,
            provider_request_id=provider_request_id,
            occurred_at=self._now(),
        )

    def resolve_case_failure(
        self, attempt: EvaluationCaseAttempt, failure_code: str
    ) -> EvaluationCaseAttempt:
        _text(failure_code, "evaluation failure code")
        return self._repository.resolve_case_failure(
            attempt_id=attempt.attempt_id,
            expected_attempt_revision=attempt.revision,
            failure_code=failure_code,
            occurred_at=self._now(),
        )

    def finalize_run(
        self, run: EvaluationRun, *, actor: str, reason: str
    ) -> EvaluationCompletion:
        definition = self._repository.get_definition(run.definition_digest)
        occurred_at = self._now()
        if not self._conformance.validate(definition, occurred_at):
            raise DomainError(
                ErrorCode.QUALIFICATION_INVALID,
                "adapter conformance became stale before evaluation result sealing",
            )
        return self._repository.finalize_run(
            run_id=run.run_id,
            expected_run_revision=run.revision,
            actor=_text(actor, "actor"),
            reason=_text(reason, "reason"),
            occurred_at=occurred_at,
        )

    def invalidate_result(
        self,
        *,
        result_id: StableId,
        expected_validity_revision: Revision,
        status: EvaluationValidityStatus,
        authority: str,
        reason: str,
    ) -> EvaluationValidityDecision:
        if status is EvaluationValidityStatus.VALID:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "validity cannot be restored to VALID; run a new evaluation",
            )
        return self._repository.invalidate_result(
            result_id=result_id,
            expected_validity_revision=expected_validity_revision,
            status=status,
            authority=_text(authority, "validity authority"),
            reason=_text(reason, "validity reason"),
            occurred_at=self._now(),
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "evaluation clock must be timezone-aware")
        return value.astimezone(timezone.utc)


class CurrentEvaluationQualificationVerifier:
    """Activation verifier backed by the latest monotonic validity decision."""

    def __init__(
        self,
        repository: CapabilityEvaluationRepository,
        dependencies: EvaluationQualificationDependencies,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._dependencies = dependencies
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def validate(self, proof: QualificationProof) -> bool:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            return False
        return (
            proof.qualification_kind == "CAPABILITY_EVALUATION"
            and proof.verify_digest()
            and self._repository.validate_qualification(
                proof,
                value.astimezone(timezone.utc),
                self._dependencies,
            )
        )


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value
