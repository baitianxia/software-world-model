"""Provider-neutral model execution boundary.

The application submits one logical interaction to this port.  Candidate
selection, availability decisions, attempt isolation, and provider receipts
are deliberately outside this module's public result.  Concrete adapters may
keep that information in a private audit store, but callers only receive a
terminal logical result and an opaque audit reference.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, Protocol, TypeVar

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of


TRequest = TypeVar("TRequest")
TResult = TypeVar("TResult")


@dataclass(frozen=True, slots=True)
class LogicalModelExecutionRequest(Generic[TRequest]):
    """One immutable product interaction; no provider route is part of it."""

    interaction_digest: Digest
    payload: TRequest

    @classmethod
    def create(cls, *, interaction_digest: Digest, payload: TRequest) -> "LogicalModelExecutionRequest[TRequest]":
        if not isinstance(interaction_digest, Digest):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "logical model execution requires an interaction digest",
            )
        return cls(interaction_digest=interaction_digest, payload=payload)


@dataclass(frozen=True, slots=True)
class LogicalModelExecutionResult(Generic[TResult]):
    """Terminal result exposed to the product boundary."""

    interaction_digest: Digest
    result: TResult
    execution_audit_ref: str
    dispatch_count: int

    def __post_init__(self) -> None:
        if not self.execution_audit_ref or not isinstance(self.execution_audit_ref, str):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "logical model execution requires an opaque audit reference",
            )
        if type(self.dispatch_count) is not int or self.dispatch_count < 0:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "logical model execution dispatch count must be non-negative",
            )


class ModelExecutionPort(Protocol[TRequest, TResult]):
    """The only execution dependency visible to an upper layer."""

    def execute(
        self, request: LogicalModelExecutionRequest[TRequest]
    ) -> LogicalModelExecutionResult[TResult]: ...


class ModelExecutionCoordinator(Generic[TRequest, TResult]):
    """Small runtime-owned facade around a private execution implementation.

    ``runner`` is intentionally injected by the infrastructure composition
    root. It may internally perform qualified candidate selection and a fresh
    full-chain attempt, but those details cannot enter the returned contract.
    """

    def __init__(
        self,
        *,
        runner: Callable[[TRequest], TResult],
        dispatch_counter: Callable[[TResult], int] | None = None,
        audit_ref_factory: Callable[[LogicalModelExecutionRequest[TRequest], TResult], str]
        | None = None,
    ) -> None:
        if not callable(runner):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "execution runner is required")
        if dispatch_counter is not None and not callable(dispatch_counter):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "dispatch counter must be callable")
        if audit_ref_factory is not None and not callable(audit_ref_factory):
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "audit reference factory must be callable")
        self._runner = runner
        self._dispatch_counter = dispatch_counter or (lambda _result: 0)
        self._audit_ref_factory = audit_ref_factory or (
            lambda request, result: digest_of(
                {
                    "schema": "MODEL_EXECUTION_AUDIT_REF@1",
                    "interaction_digest": request.interaction_digest.value,
                    "result_digest": digest_of(result).value,
                }
            ).value
        )

    def execute(
        self, request: LogicalModelExecutionRequest[TRequest]
    ) -> LogicalModelExecutionResult[TResult]:
        result = self._runner(request.payload)
        dispatch_count = self._dispatch_counter(result)
        audit_ref = self._audit_ref_factory(request, result)
        return LogicalModelExecutionResult(
            interaction_digest=request.interaction_digest,
            result=result,
            execution_audit_ref=audit_ref,
            dispatch_count=dispatch_count,
        )


__all__ = [
    "LogicalModelExecutionRequest",
    "LogicalModelExecutionResult",
    "ModelExecutionCoordinator",
    "ModelExecutionPort",
]
