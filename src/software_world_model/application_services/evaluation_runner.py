"""Reusable execution loop for frozen capability-evaluation suites."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    digest_of,
)

from .evaluation import (
    CapabilityEvaluationService,
    CaseExecutionEvidence,
    EvaluationAttemptState,
    EvaluationCaseAttempt,
    EvaluationCaseDefinition,
    EvaluationCompletion,
    EvaluationDefinition,
    EvaluationRun,
    EvaluationRunState,
)


@dataclass(frozen=True, slots=True)
class EvaluationCaseExecutionRequest:
    definition: EvaluationDefinition
    case: EvaluationCaseDefinition
    run: EvaluationRun
    attempt: EvaluationCaseAttempt
    request_digest: Digest


class EvaluationCaseExecutor(Protocol):
    def execute(
        self, request: EvaluationCaseExecutionRequest
    ) -> CaseExecutionEvidence: ...


class EvaluationCaseOutcomeUnknown(RuntimeError):
    """The external dispatch may have completed and must not be repeated."""

    def __init__(self, provider_request_id: str | None = None) -> None:
        super().__init__("evaluation case outcome is unknown")
        self.provider_request_id = provider_request_id


class EvaluationCaseExecutionFailed(RuntimeError):
    """A definitive infrastructure failure that prevents suite completion."""

    def __init__(self, failure_code: str) -> None:
        if (
            not isinstance(failure_code, str)
            or not failure_code
            or failure_code != failure_code.strip()
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "evaluation case failure code must be non-empty",
            )
        super().__init__(failure_code)
        self.failure_code = failure_code


@dataclass(frozen=True, slots=True)
class EvaluationSuiteExecution:
    run: EvaluationRun
    attempts: tuple[EvaluationCaseAttempt, ...]
    completion: EvaluationCompletion | None


class CapabilityEvaluationRunner:
    """Execute each frozen case once and recover without hidden redispatch."""

    def __init__(self, service: CapabilityEvaluationService) -> None:
        self._service = service

    def run_suite(
        self,
        *,
        definition: EvaluationDefinition,
        evaluation_sink_ref: str,
        root_allocation_ref: str,
        idempotency_key: IdempotencyKey,
        executor: EvaluationCaseExecutor,
        actor: str,
        correlation_ref: CorrelationRef,
        completion_reason: str,
    ) -> EvaluationSuiteExecution:
        reason = _text(completion_reason, "evaluation completion reason")
        registered = self._service.register_definition(definition)
        run = self._service.prepare_run(
            definition=registered,
            evaluation_sink_ref=evaluation_sink_ref,
            root_allocation_ref=root_allocation_ref,
            idempotency_key=idempotency_key,
            actor=actor,
            correlation_ref=correlation_ref,
        )
        if run.state is EvaluationRunState.COMPLETED:
            completion = self._service.finalize_run(
                run,
                actor=actor,
                reason=reason,
            )
            return EvaluationSuiteExecution(
                completion.run,
                self._recover_attempts(
                    completion.run, registered
                ),
                completion,
            )
        if run.state in {
            EvaluationRunState.OUTCOME_PENDING,
            EvaluationRunState.FAILED,
            EvaluationRunState.CANCELED,
        }:
            return EvaluationSuiteExecution(
                run,
                self._recover_attempts(run, registered),
                None,
            )
        if run.state is EvaluationRunState.PREPARED:
            run = self._service.start_run(run)

        attempts: list[EvaluationCaseAttempt] = []
        for case in registered.cases:
            request_digest = _case_request_digest(registered, run, case)
            run, attempt = self._service.dispatch_case(
                run=run,
                case_id=case.case_id,
                attempt_key=_attempt_key(run, case.case_id),
                request_digest=request_digest,
            )
            if attempt.state is EvaluationAttemptState.SUCCEEDED:
                attempts.append(attempt)
                continue
            if attempt.state in {
                EvaluationAttemptState.OUTCOME_UNKNOWN,
                EvaluationAttemptState.FAILED,
            }:
                attempts.append(attempt)
                return EvaluationSuiteExecution(
                    self._service.get_run(run.run_id), tuple(attempts), None
                )
            request = EvaluationCaseExecutionRequest(
                definition=registered,
                case=case,
                run=run,
                attempt=attempt,
                request_digest=request_digest,
            )
            try:
                evidence = executor.execute(request)
            except EvaluationCaseOutcomeUnknown as exc:
                attempts.append(
                    self._service.mark_case_outcome_unknown(
                        attempt, exc.provider_request_id
                    )
                )
                return EvaluationSuiteExecution(
                    self._service.get_run(run.run_id), tuple(attempts), None
                )
            except EvaluationCaseExecutionFailed as exc:
                attempts.append(
                    self._service.resolve_case_failure(
                        attempt, exc.failure_code
                    )
                )
                return EvaluationSuiteExecution(
                    self._service.get_run(run.run_id), tuple(attempts), None
                )
            except DomainError as exc:
                attempts.append(
                    self._service.resolve_case_failure(
                        attempt, f"DOMAIN_{exc.code.value}"
                    )
                )
                return EvaluationSuiteExecution(
                    self._service.get_run(run.run_id), tuple(attempts), None
                )
            attempts.append(self._service.complete_case(attempt, evidence))

        current = self._service.get_run(run.run_id)
        completion = self._service.finalize_run(
            current,
            actor=actor,
            reason=reason,
        )
        return EvaluationSuiteExecution(
            completion.run,
            tuple(attempts),
            completion,
        )

    def _recover_attempts(
        self,
        run: EvaluationRun,
        definition: EvaluationDefinition,
    ) -> tuple[EvaluationCaseAttempt, ...]:
        attempts: list[EvaluationCaseAttempt] = []
        for case in definition.cases:
            request_digest = _case_request_digest(definition, run, case)
            try:
                _, attempt = self._service.dispatch_case(
                    run=run,
                    case_id=case.case_id,
                    attempt_key=_attempt_key(run, case.case_id),
                    request_digest=request_digest,
                )
            except DomainError as exc:
                if exc.code is ErrorCode.EVALUATION_RUN_CONFLICT:
                    continue
                raise
            attempts.append(attempt)
        return tuple(attempts)


def _case_request_digest(
    definition: EvaluationDefinition,
    run: EvaluationRun,
    case: EvaluationCaseDefinition,
) -> Digest:
    return digest_of(
        {
            "command": "ExecuteEvaluationCase@1",
            "definition_digest": definition.digest.value,
            "run_id": run.run_id.value,
            "evaluation_only_qualification_digest": (
                run.evaluation_only_qualification.digest.value
            ),
            "case_id": case.case_id,
            "case_version": case.case_version,
            "fixture_ref": case.fixture_ref,
            "fixture_digest": case.fixture_digest.value,
            "oracle_ref": case.oracle_ref,
            "oracle_digest": case.oracle_digest.value,
        }
    )


def _attempt_key(run: EvaluationRun, case_id: str) -> str:
    return f"evaluation:{run.run_id.value}:{digest_of(case_id).value[-24:]}"


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, f"{label} must be non-empty")
    return value
