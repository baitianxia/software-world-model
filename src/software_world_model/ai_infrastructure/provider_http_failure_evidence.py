"""Sanitized Provider HTTP failure evidence at the Gateway decoration boundary.

The provider-conformance identity owns request rendering, transport, and the
generic Model Gateway core.  This module decorates that unchanged qualified
path: it observes only a terminal ``PROVIDER_HTTP_ERROR``, persists a minimal
sealed record, and enriches the returned result for the Application-owned
availability decision.  It never changes a Provider request or grants fallback.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from threading import local
from typing import Mapping, Protocol

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    StableId,
    digest_of,
)

from .model_gateway import (
    AdapterResponse,
    ModelCallState,
    ModelExecutionContext,
    ModelGatewayResult,
    ProviderAdapterCapabilities,
    ProviderRequest,
)


MODEL_PROVIDER_HTTP_FAILURE_EVIDENCE_SCHEMA = (
    "MODEL_PROVIDER_HTTP_FAILURE_EVIDENCE@1"
)


@dataclass(frozen=True, slots=True)
class ModelProviderHTTPFailureEvidence:
    """Gateway-sealed, sanitized evidence for one terminal HTTP response."""

    schema: str
    model_call_id: StableId
    provider_request_digest: Digest
    isolation_receipt_digest: Digest
    failure_code: str
    http_status: int
    provider_error_code: str | None
    provider_error_type: str | None
    provider_request_id: str | None
    digest: Digest

    @classmethod
    def seal(
        cls,
        *,
        model_call_id: StableId,
        provider_request_digest: Digest,
        isolation_receipt_digest: Digest,
        details: Mapping[str, object],
    ) -> "ModelProviderHTTPFailureEvidence | None":
        sanitized = _sanitized_http_failure_details(details)
        if sanitized is None:
            return None
        core = {
            "schema": MODEL_PROVIDER_HTTP_FAILURE_EVIDENCE_SCHEMA,
            "model_call_id": model_call_id.value,
            "provider_request_digest": provider_request_digest.value,
            "isolation_receipt_digest": isolation_receipt_digest.value,
            "failure_code": ErrorCode.PROVIDER_HTTP_ERROR.value,
            **sanitized,
        }
        return cls(
            schema=MODEL_PROVIDER_HTTP_FAILURE_EVIDENCE_SCHEMA,
            model_call_id=model_call_id,
            provider_request_digest=provider_request_digest,
            isolation_receipt_digest=isolation_receipt_digest,
            failure_code=ErrorCode.PROVIDER_HTTP_ERROR.value,
            http_status=sanitized["http_status"],
            provider_error_code=sanitized["provider_error_code"],
            provider_error_type=sanitized["provider_error_type"],
            provider_request_id=sanitized["provider_request_id"],
            digest=digest_of(core),
        )

    def require_exact(self) -> None:
        expected = self.seal(
            model_call_id=self.model_call_id,
            provider_request_digest=self.provider_request_digest,
            isolation_receipt_digest=self.isolation_receipt_digest,
            details={
                "http_status": self.http_status,
                **(
                    {"provider_error_code": self.provider_error_code}
                    if self.provider_error_code is not None
                    else {}
                ),
                **(
                    {"provider_error_type": self.provider_error_type}
                    if self.provider_error_type is not None
                    else {}
                ),
                **(
                    {"provider_request_id": self.provider_request_id}
                    if self.provider_request_id is not None
                    else {}
                ),
            },
        )
        if expected is None or self != expected:
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Model Provider HTTP failure evidence is inconsistent",
            )


@dataclass(frozen=True, slots=True)
class ProviderHTTPFailureEvidenceModelGatewayResult(ModelGatewayResult):
    """A generic Gateway result plus separately persisted raw HTTP evidence."""

    provider_http_failure_evidence: ModelProviderHTTPFailureEvidence | None = None


class ProviderHTTPFailureEvidenceRepository(Protocol):
    def record_provider_http_failure_evidence(
        self, evidence: ModelProviderHTTPFailureEvidence
    ) -> None: ...

    def get_provider_http_failure_evidence(
        self, model_call_id: StableId
    ) -> ModelProviderHTTPFailureEvidence | None: ...


@dataclass(frozen=True, slots=True)
class _CapturedProviderHTTPFailure:
    provider_request_digest: Digest
    details: Mapping[str, object]


class ProviderHTTPFailureCapturingAdapter:
    """Observe a sanitized terminal HTTP error without changing adapter bytes."""

    def __init__(self, delegate: object) -> None:
        provider_type = getattr(delegate, "provider_type", None)
        adapter_version = getattr(delegate, "adapter_version", None)
        capabilities = getattr(delegate, "capabilities", None)
        if (
            not isinstance(provider_type, str)
            or not isinstance(adapter_version, str)
            or not isinstance(capabilities, ProviderAdapterCapabilities)
            or not callable(getattr(delegate, "invoke", None))
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Provider HTTP failure capture requires one exact adapter",
            )
        self.provider_type = provider_type
        self.adapter_version = adapter_version
        self.capabilities = capabilities
        self._delegate = delegate
        self._state = local()

    def clear_current_capture(self) -> None:
        self._state.capture = None

    def invoke(self, request: ProviderRequest) -> AdapterResponse:
        self.clear_current_capture()
        try:
            return self._delegate.invoke(request)
        except DomainError as exc:
            if exc.code is ErrorCode.PROVIDER_HTTP_ERROR:
                details = _sanitized_http_failure_details(exc.details)
                if details is not None:
                    self._state.capture = _CapturedProviderHTTPFailure(
                        provider_request_digest=request.digest,
                        details=details,
                    )
            raise

    def take_current_capture(
        self, provider_request_digest: Digest
    ) -> _CapturedProviderHTTPFailure | None:
        capture = getattr(self._state, "capture", None)
        self.clear_current_capture()
        if (
            isinstance(capture, _CapturedProviderHTTPFailure)
            and capture.provider_request_digest == provider_request_digest
        ):
            return capture
        return None


class ProviderHTTPFailureEvidenceGateway:
    """Persist and replay exact evidence around an unchanged Model Gateway."""

    def __init__(
        self,
        *,
        gateway: object,
        adapter: ProviderHTTPFailureCapturingAdapter,
        repository: ProviderHTTPFailureEvidenceRepository,
    ) -> None:
        if (
            not callable(getattr(gateway, "preflight", None))
            or not callable(getattr(gateway, "invoke", None))
            or not callable(
                getattr(repository, "record_provider_http_failure_evidence", None)
            )
            or not callable(
                getattr(repository, "get_provider_http_failure_evidence", None)
            )
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Provider HTTP failure Gateway requires an exact store",
            )
        self._gateway = gateway
        self._adapter = adapter
        self._repository = repository

    def preflight(self, context: ModelExecutionContext) -> None:
        self._gateway.preflight(context)

    def invoke(
        self, context: ModelExecutionContext
    ) -> ProviderHTTPFailureEvidenceModelGatewayResult:
        self._adapter.clear_current_capture()
        result = self._gateway.invoke(context)
        if not isinstance(result, ModelGatewayResult):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Provider HTTP failure Gateway received an invalid result",
            )
        capture = self._adapter.take_current_capture(
            result.call.provider_request_digest
        )
        if capture is not None:
            evidence = ModelProviderHTTPFailureEvidence.seal(
                model_call_id=result.call.model_call_id,
                provider_request_digest=result.call.provider_request_digest,
                isolation_receipt_digest=result.call.isolation_receipt_digest,
                details=capture.details,
            )
            if evidence is None:
                raise DomainError(
                    ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                    "captured Provider HTTP failure evidence became invalid",
                )
            _require_evidence_call_binding(result, evidence)
            self._repository.record_provider_http_failure_evidence(evidence)
        evidence = self._repository.get_provider_http_failure_evidence(
            result.call.model_call_id
        )
        if evidence is not None:
            _require_evidence_call_binding(result, evidence)
        return ProviderHTTPFailureEvidenceModelGatewayResult(
            call=result.call,
            response=result.response,
            isolation_receipt=result.isolation_receipt,
            eligibility=result.eligibility,
            replayed=result.replayed,
            provider_http_failure_evidence=evidence,
        )


def _require_evidence_call_binding(
    result: ModelGatewayResult,
    evidence: ModelProviderHTTPFailureEvidence,
) -> None:
    evidence.require_exact()
    if (
        result.call.state is not ModelCallState.FAILED
        or result.call.failure_code != ErrorCode.PROVIDER_HTTP_ERROR.value
        or evidence.model_call_id != result.call.model_call_id
        or evidence.provider_request_digest != result.call.provider_request_digest
        or evidence.isolation_receipt_digest
        != result.call.isolation_receipt_digest
        or result.response is not None
    ):
        raise DomainError(
            ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            "Provider HTTP failure evidence does not bind its Gateway result",
        )


def _safe_provider_error_token(value: object) -> str | None:
    if (
        isinstance(value, str)
        and 0 < len(value) <= 128
        and re.fullmatch(r"[A-Za-z0-9._-]+", value)
    ):
        return value
    return None


def _sanitized_http_failure_details(
    details: Mapping[str, object],
) -> dict[str, object] | None:
    status = details.get("http_status")
    if type(status) is not int or not 100 <= status <= 599:
        return None
    return {
        "http_status": status,
        "provider_error_code": _safe_provider_error_token(
            details.get("provider_error_code")
        ),
        "provider_error_type": _safe_provider_error_token(
            details.get("provider_error_type")
        ),
        "provider_request_id": _safe_provider_request_id(
            details.get("provider_request_id")
        ),
    }


def _safe_provider_request_id(value: object) -> str | None:
    if (
        isinstance(value, str)
        and value == value.strip()
        and 0 < len(value) <= 256
        and all(0x20 <= ord(character) <= 0x7E for character in value)
    ):
        return value
    return None


__all__ = [
    "MODEL_PROVIDER_HTTP_FAILURE_EVIDENCE_SCHEMA",
    "ModelProviderHTTPFailureEvidence",
    "ProviderHTTPFailureCapturingAdapter",
    "ProviderHTTPFailureEvidenceGateway",
    "ProviderHTTPFailureEvidenceModelGatewayResult",
    "ProviderHTTPFailureEvidenceRepository",
]
