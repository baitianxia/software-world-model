"""Recoverable application orchestration for cross-owner management commands.

This module owns only command execution history.  Scope, source, and binding
state remain behind their owner services.
"""

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
    KnowledgeScopeService,
    ScopeLifecycle,
    ScopePurpose,
    ScopeStateAssertion,
    ScopeType,
)
from software_world_model.source_integration import SourceConfigurationService


class ManagementAttemptState(str, Enum):
    PREPARED = "PREPARED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    PARTIALLY_SUCCEEDED = "PARTIALLY_SUCCEEDED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    OUTCOME_PENDING = "OUTCOME_PENDING"


class ManagementStepState(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    DISPATCHED = "DISPATCHED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELED_BEFORE_DISPATCH = "CANCELED_BEFORE_DISPATCH"
    OUTCOME_PENDING = "OUTCOME_PENDING"


@dataclass(frozen=True, slots=True)
class ConfigureSystemSourceCommand:
    idempotency_key: IdempotencyKey
    caller: str
    purpose: str
    classification: str
    request_context: tuple[tuple[str, str], ...]
    scope_type: ScopeType
    scope_metadata: tuple[tuple[str, str], ...]
    provider_type: str
    provider_contract_version: str
    identity_domain: str
    source_target: str
    provider_configuration: tuple[tuple[str, str], ...]
    secret_reference: str | None
    selector: tuple[tuple[str, str], ...]
    context_constraint: tuple[tuple[str, str], ...]
    context_hint: str | None
    actor: str
    reason: str
    correlation_ref: CorrelationRef

    @classmethod
    def create(
        cls,
        *,
        idempotency_key: IdempotencyKey,
        caller: str,
        purpose: str,
        classification: str,
        request_context: Mapping[str, str] | None,
        scope_type: ScopeType,
        scope_metadata: Mapping[str, str] | None,
        provider_type: str,
        provider_contract_version: str,
        identity_domain: str,
        source_target: str,
        provider_configuration: Mapping[str, str] | None,
        secret_reference: str | None,
        selector: Mapping[str, str],
        context_constraint: Mapping[str, str] | None,
        context_hint: str | None,
        actor: str,
        reason: str,
        correlation_ref: CorrelationRef,
    ) -> "ConfigureSystemSourceCommand":
        return cls(
            idempotency_key=idempotency_key,
            caller=_text(caller, "caller"),
            purpose=_text(purpose, "purpose"),
            classification=_text(classification, "classification"),
            request_context=_fields(request_context),
            scope_type=scope_type,
            scope_metadata=_fields(scope_metadata),
            provider_type=_text(provider_type, "provider type"),
            provider_contract_version=_text(
                provider_contract_version, "provider contract version"
            ),
            identity_domain=_text(identity_domain, "identity domain"),
            source_target=_text(source_target, "source target"),
            provider_configuration=_fields(provider_configuration),
            secret_reference=secret_reference,
            selector=_fields(selector),
            context_constraint=_fields(context_constraint),
            context_hint=context_hint,
            actor=_text(actor, "actor"),
            reason=_text(reason, "reason"),
            correlation_ref=correlation_ref,
        )

    @property
    def request_digest(self) -> Digest:
        return digest_of({"command": "ConfigureSystemSource@1", "body": self})


@dataclass(frozen=True, slots=True)
class ManagementStep:
    step_id: StableId
    attempt_id: StableId
    ordinal: int
    name: str
    owner_contract: str
    owner_idempotency_key: IdempotencyKey
    request_digest: Digest
    revision: Revision
    state: ManagementStepState
    dispatch_attempt: int
    result_reference: str | None
    result_digest: Digest | None
    output: tuple[tuple[str, str], ...]
    failure_code: str | None
    failure_message: str | None
    retryable: bool
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ManagementAttempt:
    attempt_id: StableId
    command_id: StableId
    revision: Revision
    state: ManagementAttemptState
    cancel_requested: bool
    cancellation_reason: str | None
    created_at: datetime
    revised_at: datetime


@dataclass(frozen=True, slots=True)
class ManagementResult:
    result_id: StableId
    revision: Revision
    supersedes_revision: Revision | None
    command_id: StableId
    attempt_id: StableId
    request_digest: Digest
    caller: str
    overall_state: ManagementAttemptState
    steps: tuple[ManagementStep, ...]
    result_digest: Digest
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class ManagementExecution:
    command: ConfigureSystemSourceCommand
    attempt: ManagementAttempt
    result: ManagementResult


class OwnerOutcomePending(RuntimeError):
    """The call crossed dispatch but its authoritative outcome is unknown."""


class ManagementRepository(Protocol):
    def prepare(
        self,
        *,
        command: ConfigureSystemSourceCommand,
        steps: tuple[tuple[str, str, IdempotencyKey, Digest], ...],
        occurred_at: datetime,
    ) -> ManagementExecution: ...

    def get_by_attempt(self, attempt_id: StableId) -> ManagementExecution: ...

    def transition_step(
        self,
        *,
        step_id: StableId,
        expected_revision: Revision,
        target: ManagementStepState,
        result_reference: str | None,
        result_digest: Digest | None,
        output: Mapping[str, str] | None,
        failure_code: str | None,
        failure_message: str | None,
        retryable: bool,
        occurred_at: datetime,
    ) -> ManagementExecution: ...

    def request_cancel(
        self, *, attempt_id: StableId, reason: str, occurred_at: datetime
    ) -> ManagementExecution: ...


class ManagementApplicationService:
    _STEP_SPECS = (
        ("CREATE_SCOPE", "KNW-CREATE-SCOPE@1"),
        ("REGISTER_SOURCE", "SRC-REGISTER-DATA-SOURCE@1"),
        ("READ_BIND_ASSERTION", "KNW-READ-SCOPE-STATE-ASSERTION@1"),
        ("BIND_SOURCE", "SRC-BIND-SOURCE-TO-SCOPE@1"),
    )

    def __init__(
        self,
        repository: ManagementRepository,
        scopes: KnowledgeScopeService,
        sources: SourceConfigurationService,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._scopes = scopes
        self._sources = sources
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def prepare(self, command: ConfigureSystemSourceCommand) -> ManagementExecution:
        steps = tuple(
            (
                name,
                contract,
                IdempotencyKey(f"{command.idempotency_key.value}:{name.casefold()}"),
                digest_of(
                    {
                        "management_request": command.request_digest.value,
                        "owner_contract": contract,
                        "step": name,
                    }
                ),
            )
            for name, contract in self._STEP_SPECS
        )
        return self._repository.prepare(command=command, steps=steps, occurred_at=self._now())

    def configure(self, command: ConfigureSystemSourceCommand) -> ManagementExecution:
        prepared = self.prepare(command)
        if prepared.attempt.state in {
            ManagementAttemptState.SUCCEEDED,
            ManagementAttemptState.CANCELED,
        }:
            return prepared
        return self.execute(prepared.attempt.attempt_id)

    def execute(self, attempt_id: StableId) -> ManagementExecution:
        execution = self._repository.get_by_attempt(attempt_id)
        for step in execution.result.steps:
            execution = self._repository.get_by_attempt(attempt_id)
            step = next(item for item in execution.result.steps if item.step_id == step.step_id)
            if step.state in {
                ManagementStepState.SUCCEEDED,
                ManagementStepState.CANCELED_BEFORE_DISPATCH,
            }:
                continue
            if execution.attempt.cancel_requested:
                if step.state is ManagementStepState.NOT_STARTED:
                    execution = self._cancel_step(step)
                    continue
                if step.state is ManagementStepState.FAILED:
                    continue
            if step.state is ManagementStepState.FAILED:
                # A retry is explicit: calling execute again retains the same step root
                # and owner idempotency key.
                pass
            if step.state is not ManagementStepState.OUTCOME_PENDING:
                execution = self._repository.transition_step(
                    step_id=step.step_id,
                    expected_revision=step.revision,
                    target=ManagementStepState.DISPATCHED,
                    result_reference=None,
                    result_digest=None,
                    output=None,
                    failure_code=None,
                    failure_message=None,
                    retryable=False,
                    occurred_at=self._now(),
                )
                step = next(item for item in execution.result.steps if item.step_id == step.step_id)
            try:
                result_reference, result_digest, output = self._invoke(
                    execution.command, step.name, execution.result.steps
                )
            except DomainError as exc:
                execution = self._repository.transition_step(
                    step_id=step.step_id,
                    expected_revision=step.revision,
                    target=ManagementStepState.FAILED,
                    result_reference=None,
                    result_digest=None,
                    output=None,
                    failure_code=exc.code.value,
                    failure_message=exc.message,
                    retryable=exc.code not in {ErrorCode.INVALID_ARGUMENT, ErrorCode.IDEMPOTENCY_MISMATCH},
                    occurred_at=self._now(),
                )
                break
            except OwnerOutcomePending as exc:
                execution = self._repository.transition_step(
                    step_id=step.step_id,
                    expected_revision=step.revision,
                    target=ManagementStepState.OUTCOME_PENDING,
                    result_reference=None,
                    result_digest=None,
                    output=None,
                    failure_code="OUTCOME_PENDING",
                    failure_message=str(exc),
                    retryable=True,
                    occurred_at=self._now(),
                )
                break
            execution = self._repository.transition_step(
                step_id=step.step_id,
                expected_revision=step.revision,
                target=ManagementStepState.SUCCEEDED,
                result_reference=result_reference,
                result_digest=result_digest,
                output=output,
                failure_code=None,
                failure_message=None,
                retryable=False,
                occurred_at=self._now(),
            )
        return execution

    def cancel(self, attempt_id: StableId, *, reason: str) -> ManagementExecution:
        execution = self._repository.request_cancel(
            attempt_id=attempt_id, reason=_text(reason, "cancellation reason"), occurred_at=self._now()
        )
        for step in execution.result.steps:
            current = self._repository.get_by_attempt(attempt_id)
            live = next(item for item in current.result.steps if item.step_id == step.step_id)
            if live.state is ManagementStepState.NOT_STARTED:
                execution = self._cancel_step(live)
        return execution

    def get(self, attempt_id: StableId) -> ManagementExecution:
        return self._repository.get_by_attempt(attempt_id)

    def _cancel_step(self, step: ManagementStep) -> ManagementExecution:
        return self._repository.transition_step(
            step_id=step.step_id,
            expected_revision=step.revision,
            target=ManagementStepState.CANCELED_BEFORE_DISPATCH,
            result_reference=None,
            result_digest=None,
            output=None,
            failure_code=None,
            failure_message=None,
            retryable=False,
            occurred_at=self._now(),
        )

    def _invoke(
        self,
        command: ConfigureSystemSourceCommand,
        name: str,
        steps: tuple[ManagementStep, ...],
    ) -> tuple[str, Digest, dict[str, str]]:
        owner_key = next(step.owner_idempotency_key for step in steps if step.name == name)
        if name == "CREATE_SCOPE":
            scope = self._scopes.create_scope(
                scope_type=command.scope_type,
                metadata=dict(command.scope_metadata),
                idempotency_key=owner_key,
                actor=command.actor,
                reason=command.reason,
                correlation_ref=command.correlation_ref,
            )
            return (
                scope.scope_id.value,
                scope.definition_digest,
                {
                    "scope_id": scope.scope_id.value,
                    "scope_revision": str(scope.definition_revision.value),
                },
            )
        if name == "REGISTER_SOURCE":
            source = self._sources.register_data_source(
                provider_type=command.provider_type,
                provider_contract_version=command.provider_contract_version,
                identity_domain=command.identity_domain,
                source_target=command.source_target,
                provider_configuration=dict(command.provider_configuration),
                secret_reference=command.secret_reference,
                idempotency_key=owner_key,
                actor=command.actor,
                reason=command.reason,
                correlation_ref=command.correlation_ref,
            )
            return (
                source.source_id.value,
                source.definition_digest,
                {
                    "source_id": source.source_id.value,
                    "source_revision": str(source.definition_revision.value),
                },
            )
        scope_output = _successful_output(steps, "CREATE_SCOPE")
        if name == "READ_BIND_ASSERTION":
            assertion = self._scopes.read_scope_state_assertion(
                scope_id=StableId(scope_output["scope_id"]),
                expected_revision=Revision(int(scope_output["scope_revision"])),
                purpose=ScopePurpose.BIND_CONFIGURATION,
                caller_ref="application-services/management",
                request_ref=command.idempotency_key.value,
                classification=command.classification,
            )
            return (
                assertion.assertion_id.value,
                assertion.digest,
                _serialize_assertion(assertion),
            )
        if name == "BIND_SOURCE":
            source_output = _successful_output(steps, "REGISTER_SOURCE")
            assertion_output = _successful_output(steps, "READ_BIND_ASSERTION")
            assertion = _deserialize_assertion(assertion_output)
            binding = self._sources.bind_source_to_scope(
                source_id=StableId(source_output["source_id"]),
                assertion=assertion,
                selector=dict(command.selector),
                context_constraint=dict(command.context_constraint),
                context_hint=command.context_hint,
                idempotency_key=owner_key,
                actor=command.actor,
                reason=command.reason,
                correlation_ref=command.correlation_ref,
            )
            return (
                binding.binding_id.value,
                binding.definition_digest,
                {
                    "binding_id": binding.binding_id.value,
                    "binding_revision": str(binding.definition_revision.value),
                },
            )
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "unknown management step")

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None or value.utcoffset() is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "clock must return an aware datetime")
        return value.astimezone(timezone.utc)


def _successful_output(steps: tuple[ManagementStep, ...], name: str) -> dict[str, str]:
    step = next((item for item in steps if item.name == name), None)
    if step is None or step.state is not ManagementStepState.SUCCEEDED:
        raise DomainError(ErrorCode.AUTHORITY_RECORD_INCONSISTENT, f"{name} has no success output")
    return dict(step.output)


def _serialize_assertion(assertion: ScopeStateAssertion) -> dict[str, str]:
    return {
        "assertion_id": assertion.assertion_id.value,
        "scope_id": assertion.scope_id.value,
        "scope_type": assertion.scope_type.value,
        "definition_revision": str(assertion.definition_revision.value),
        "lifecycle": assertion.lifecycle.value,
        "purpose": assertion.purpose.value,
        "outcome": assertion.outcome.value,
        "caller_ref": assertion.caller_ref,
        "request_ref": assertion.request_ref,
        "classification": assertion.classification,
        "read_at": assertion.read_at.isoformat(),
        "digest": assertion.digest.value,
    }


def _deserialize_assertion(values: Mapping[str, str]) -> ScopeStateAssertion:
    return ScopeStateAssertion(
        assertion_id=StableId(values["assertion_id"]),
        scope_id=StableId(values["scope_id"]),
        scope_type=ScopeType(values["scope_type"]),
        definition_revision=Revision(int(values["definition_revision"])),
        lifecycle=ScopeLifecycle(values["lifecycle"]),
        purpose=ScopePurpose(values["purpose"]),
        outcome=AssertionOutcome(values["outcome"]),
        caller_ref=values["caller_ref"],
        request_ref=values["request_ref"],
        classification=values["classification"],
        read_at=datetime.fromisoformat(values["read_at"]),
        digest=Digest(values["digest"]),
    )


def _fields(values: Mapping[str, str] | None) -> tuple[tuple[str, str], ...]:
    if not values:
        return ()
    result = tuple(sorted((_text(key, "field key"), value) for key, value in values.items()))
    if any(not isinstance(value, str) for _, value in result):
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "field values must be strings")
    return result


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value
