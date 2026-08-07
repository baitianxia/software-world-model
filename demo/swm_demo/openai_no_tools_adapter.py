from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import socket
from typing import Any, Callable, Mapping, Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlsplit

from swm_demo.formal_validation import (
    ContractViolation,
    IsolationReceipt,
    canonical_bytes,
    digest,
    validate_no_tools_request,
)


DEFAULT_RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"
ADAPTER_PROFILE_REF = "SWM-ADAPTER-OAI-RESPONSES-001@0.1.0"
_ALLOWED_OUTPUT_ITEM_TYPES = frozenset({"message", "reasoning"})
_ALLOWED_MESSAGE_KEYS = frozenset({"id", "type", "status", "role", "content"})
_ALLOWED_REASONING_KEYS = frozenset({"id", "type", "summary"})
_ALLOWED_OUTPUT_TEXT_KEYS = frozenset({"type", "text", "annotations"})


class AdapterFailureCode(str, Enum):
    PRE_DISPATCH_REJECTED = "PRE_DISPATCH_REJECTED"
    PROVIDER_HTTP_ERROR = "PROVIDER_HTTP_ERROR"
    OUTCOME_UNKNOWN = "OUTCOME_UNKNOWN"
    PROVIDER_RESPONSE_INVALID = "PROVIDER_RESPONSE_INVALID"
    PROVIDER_OUTPUT_FORBIDDEN = "PROVIDER_OUTPUT_FORBIDDEN"
    PROVIDER_REFUSAL = "PROVIDER_REFUSAL"
    PROVIDER_INCOMPLETE_MAX_TOKENS = "PROVIDER_INCOMPLETE_MAX_TOKENS"
    PROVIDER_INCOMPLETE_CONTENT_FILTER = "PROVIDER_INCOMPLETE_CONTENT_FILTER"
    PROVIDER_INCOMPLETE_OTHER = "PROVIDER_INCOMPLETE_OTHER"
    STRUCTURED_OUTPUT_INVALID = "STRUCTURED_OUTPUT_INVALID"
    MODEL_IDENTITY_UNQUALIFIED = "MODEL_IDENTITY_UNQUALIFIED"
    USAGE_INCOMPLETE = "USAGE_INCOMPLETE"


class ModelIdentityClassification(str, Enum):
    PINNED = "PINNED"
    OBSERVED_MUTABLE = "OBSERVED_MUTABLE"
    UNRESOLVED_MUTABLE = "UNRESOLVED_MUTABLE"


class NoToolsAdapterError(RuntimeError):
    """A sanitized, fail-closed Adapter outcome.

    Provider bodies and authorization material are intentionally excluded from
    the exception so normal telemetry cannot accidentally become a secret or
    source-content sink.
    """

    def __init__(
        self,
        code: AdapterFailureCode,
        *,
        client_request_id: str,
        detail: str = "",
    ) -> None:
        self.code = code
        self.client_request_id = client_request_id
        self.detail = detail
        suffix = f": {detail}" if detail else ""
        super().__init__(f"{code.value} [{client_request_id}]{suffix}")


class TransportFailure(RuntimeError):
    def __init__(self, *, dispatched: bool) -> None:
        self.dispatched = dispatched
        super().__init__("provider transport failed")


@dataclass(frozen=True)
class ProviderHTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


class ResponsesTransport(Protocol):
    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
    ) -> ProviderHTTPResponse: ...


@dataclass(frozen=True)
class RecordedRequest:
    method: str
    endpoint: str
    headers: Mapping[str, str]
    body: bytes
    body_digest: str


class RecordingTransport:
    """Capture the exact non-secret HTTP request before delegating it."""

    def __init__(self, delegate: ResponsesTransport) -> None:
        self.delegate = delegate
        self.requests: list[RecordedRequest] = []

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
    ) -> ProviderHTTPResponse:
        self.requests.append(
            RecordedRequest(
                method="POST",
                endpoint=endpoint,
                headers={
                    "content-type": "application/json",
                    "x-client-request-id": client_request_id,
                },
                body=body,
                body_digest=digest(json.loads(body)),
            )
        )
        return self.delegate.post_json(
            endpoint=endpoint,
            body=body,
            client_request_id=client_request_id,
        )


class UrllibResponsesTransport:
    """Minimal direct-HTTPS transport whose secret never enters a capture."""

    def __init__(
        self,
        *,
        api_key: str,
        timeout_seconds: float = 120.0,
        organization: str | None = None,
        project: str | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("api_key must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.organization = organization
        self.project = project

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
    ) -> ProviderHTTPResponse:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "X-Client-Request-Id": client_request_id,
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        if self.project:
            headers["OpenAI-Project"] = self.project
        request = urllib_request.Request(
            endpoint,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib_request.urlopen(
                request, timeout=self.timeout_seconds
            ) as response:
                return ProviderHTTPResponse(
                    status_code=response.status,
                    headers={key.lower(): value for key, value in response.headers.items()},
                    body=response.read(),
                )
        except urllib_error.HTTPError as exc:
            return ProviderHTTPResponse(
                status_code=exc.code,
                headers={key.lower(): value for key, value in exc.headers.items()},
                body=exc.read(),
            )
        except (urllib_error.URLError, TimeoutError, socket.timeout) as exc:
            # Once urlopen begins, the transport cannot prove whether the
            # provider accepted the request. Preserve the original Attempt.
            raise TransportFailure(dispatched=True) from exc


@dataclass(frozen=True)
class ModelIdentityPolicy:
    pinned_models: frozenset[str]
    observed_revisions_by_alias: Mapping[str, frozenset[str]]
    qualified_models: frozenset[str]

    def classify(
        self, requested_model: str, actual_model: str
    ) -> ModelIdentityClassification:
        if requested_model == actual_model and requested_model in self.pinned_models:
            return ModelIdentityClassification.PINNED
        observed = self.observed_revisions_by_alias.get(requested_model, frozenset())
        if actual_model in observed:
            return ModelIdentityClassification.OBSERVED_MUTABLE
        return ModelIdentityClassification.UNRESOLVED_MUTABLE

    def is_qualified(
        self,
        actual_model: str,
        classification: ModelIdentityClassification,
    ) -> bool:
        return (
            classification is not ModelIdentityClassification.UNRESOLVED_MUTABLE
            and actual_model in self.qualified_models
        )


@dataclass(frozen=True)
class ModelUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cached_tokens: int | None
    reasoning_tokens: int | None


@dataclass(frozen=True)
class EligibleModelOutput:
    client_request_id: str
    provider_request_id: str | None
    provider_response_id: str
    requested_model: str
    actual_model: str
    model_identity: ModelIdentityClassification
    request_digest: str
    response_digest: str
    output: Any
    usage: ModelUsage
    eligibility: str = "PASS"


class OpenAIResponsesNoToolsAdapter:
    """Validation-only implementation of the selected no-tools profile."""

    def __init__(
        self,
        *,
        transport: ResponsesTransport,
        model_identity_policy: ModelIdentityPolicy,
        valid_conformance_result_refs: frozenset[str],
        endpoint: str = DEFAULT_RESPONSES_ENDPOINT,
        adapter_profile_ref: str = ADAPTER_PROFILE_REF,
    ) -> None:
        parsed = urlsplit(endpoint)
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError("Responses endpoint must use direct HTTPS")
        self.transport = transport
        self.model_identity_policy = model_identity_policy
        self.valid_conformance_result_refs = valid_conformance_result_refs
        self.endpoint = endpoint
        self.adapter_profile_ref = adapter_profile_ref

    def execute(
        self,
        request: Mapping[str, Any],
        receipt: IsolationReceipt,
        *,
        output_decoder: Callable[[Any], Any],
    ) -> EligibleModelOutput:
        metadata = request.get("metadata")
        provisional_request_id = (
            str(metadata.get("call_id", "unknown"))
            if isinstance(metadata, Mapping)
            else "unknown"
        )
        try:
            validate_no_tools_request(request)
            if receipt.adapter_profile_ref != self.adapter_profile_ref:
                raise ContractViolation("Isolation Receipt uses another Adapter Profile")
            if (
                receipt.live_conformance_result_ref
                not in self.valid_conformance_result_refs
            ):
                raise ContractViolation(
                    "Isolation Receipt Conformance Result is not currently valid"
                )
            receipt.verify_dispatched_body(request)
        except (ContractViolation, TypeError, ValueError) as exc:
            raise NoToolsAdapterError(
                AdapterFailureCode.PRE_DISPATCH_REJECTED,
                client_request_id=provisional_request_id,
                detail=type(exc).__name__,
            ) from exc

        client_request_id = str(request["metadata"]["call_id"])
        body = canonical_bytes(request)
        try:
            response = self.transport.post_json(
                endpoint=self.endpoint,
                body=body,
                client_request_id=client_request_id,
            )
        except TransportFailure as exc:
            code = (
                AdapterFailureCode.OUTCOME_UNKNOWN
                if exc.dispatched
                else AdapterFailureCode.PRE_DISPATCH_REJECTED
            )
            raise NoToolsAdapterError(
                code,
                client_request_id=client_request_id,
            ) from exc

        if not 200 <= response.status_code < 300:
            raise NoToolsAdapterError(
                AdapterFailureCode.PROVIDER_HTTP_ERROR,
                client_request_id=client_request_id,
                detail=f"http_status={response.status_code}",
            )

        payload = self._parse_response(response.body, client_request_id)
        status = payload.get("status")
        if status == "incomplete":
            details = payload.get("incomplete_details")
            reason = details.get("reason") if isinstance(details, Mapping) else None
            code = {
                "max_output_tokens": AdapterFailureCode.PROVIDER_INCOMPLETE_MAX_TOKENS,
                "content_filter": AdapterFailureCode.PROVIDER_INCOMPLETE_CONTENT_FILTER,
            }.get(reason, AdapterFailureCode.PROVIDER_INCOMPLETE_OTHER)
            raise NoToolsAdapterError(
                code,
                client_request_id=client_request_id,
                detail=f"reason={reason or 'unknown'}",
            )
        if status != "completed":
            raise NoToolsAdapterError(
                AdapterFailureCode.PROVIDER_RESPONSE_INVALID,
                client_request_id=client_request_id,
                detail=f"status={status}",
            )
        if payload.get("tools") != []:
            raise NoToolsAdapterError(
                AdapterFailureCode.PROVIDER_OUTPUT_FORBIDDEN,
                client_request_id=client_request_id,
                detail="response tools are not empty",
            )

        output_text = self._extract_output_text(payload, client_request_id)
        output_format = request["text"]["format"]
        if output_format["type"] == "json_schema":
            try:
                decoded_json = json.loads(output_text)
            except (json.JSONDecodeError, TypeError) as exc:
                raise NoToolsAdapterError(
                    AdapterFailureCode.STRUCTURED_OUTPUT_INVALID,
                    client_request_id=client_request_id,
                    detail="response text is not JSON",
                ) from exc
            if not isinstance(decoded_json, dict):
                raise NoToolsAdapterError(
                    AdapterFailureCode.STRUCTURED_OUTPUT_INVALID,
                    client_request_id=client_request_id,
                    detail="structured output root is not an object",
                )
            candidate_output: Any = decoded_json
        else:
            candidate_output = output_text
        requested_model = str(request["model"])
        actual_model = payload.get("model")
        if not isinstance(actual_model, str) or not actual_model:
            raise NoToolsAdapterError(
                AdapterFailureCode.PROVIDER_RESPONSE_INVALID,
                client_request_id=client_request_id,
                detail="missing provider model identity",
            )
        classification = self.model_identity_policy.classify(
            requested_model, actual_model
        )
        if not self.model_identity_policy.is_qualified(actual_model, classification):
            raise NoToolsAdapterError(
                AdapterFailureCode.MODEL_IDENTITY_UNQUALIFIED,
                client_request_id=client_request_id,
                detail=f"classification={classification.value}",
            )

        usage = self._parse_usage(payload.get("usage"), client_request_id)
        response_id = payload.get("id")
        if not isinstance(response_id, str) or not response_id:
            raise NoToolsAdapterError(
                AdapterFailureCode.PROVIDER_RESPONSE_INVALID,
                client_request_id=client_request_id,
                detail="missing provider response identity",
            )
        try:
            decoded_output = output_decoder(candidate_output)
        except Exception as exc:
            raise NoToolsAdapterError(
                AdapterFailureCode.STRUCTURED_OUTPUT_INVALID,
                client_request_id=client_request_id,
                detail=type(exc).__name__,
            ) from exc
        response_headers = {key.lower(): value for key, value in response.headers.items()}
        return EligibleModelOutput(
            client_request_id=client_request_id,
            provider_request_id=response_headers.get("x-request-id"),
            provider_response_id=response_id,
            requested_model=requested_model,
            actual_model=actual_model,
            model_identity=classification,
            request_digest=receipt.request_digest,
            response_digest=digest(payload),
            output=decoded_output,
            usage=usage,
        )

    @staticmethod
    def _parse_response(body: bytes, client_request_id: str) -> Mapping[str, Any]:
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
            raise NoToolsAdapterError(
                AdapterFailureCode.PROVIDER_RESPONSE_INVALID,
                client_request_id=client_request_id,
                detail="provider body is not a JSON object",
            ) from exc
        if not isinstance(payload, Mapping):
            raise NoToolsAdapterError(
                AdapterFailureCode.PROVIDER_RESPONSE_INVALID,
                client_request_id=client_request_id,
                detail="provider body is not a JSON object",
            )
        return payload

    @staticmethod
    def _extract_output_text(
        payload: Mapping[str, Any], client_request_id: str
    ) -> str:
        output = payload.get("output")
        if not isinstance(output, list) or not output:
            raise NoToolsAdapterError(
                AdapterFailureCode.PROVIDER_RESPONSE_INVALID,
                client_request_id=client_request_id,
                detail="provider output is empty",
            )
        output_texts: list[str] = []
        message_count = 0
        for item in output:
            if not isinstance(item, Mapping):
                raise NoToolsAdapterError(
                    AdapterFailureCode.PROVIDER_OUTPUT_FORBIDDEN,
                    client_request_id=client_request_id,
                    detail="non-object output item",
                )
            item_type = item.get("type")
            if item_type not in _ALLOWED_OUTPUT_ITEM_TYPES:
                raise NoToolsAdapterError(
                    AdapterFailureCode.PROVIDER_OUTPUT_FORBIDDEN,
                    client_request_id=client_request_id,
                    detail=f"output_type={item_type}",
                )
            if item_type == "reasoning":
                if not set(item).issubset(_ALLOWED_REASONING_KEYS):
                    raise NoToolsAdapterError(
                        AdapterFailureCode.PROVIDER_OUTPUT_FORBIDDEN,
                        client_request_id=client_request_id,
                        detail="reasoning item has an unrequested field",
                    )
                continue
            message_count += 1
            if not set(item).issubset(_ALLOWED_MESSAGE_KEYS):
                raise NoToolsAdapterError(
                    AdapterFailureCode.PROVIDER_OUTPUT_FORBIDDEN,
                    client_request_id=client_request_id,
                    detail="message item has an unknown field",
                )
            if item.get("status") != "completed" or item.get("role") != "assistant":
                raise NoToolsAdapterError(
                    AdapterFailureCode.PROVIDER_RESPONSE_INVALID,
                    client_request_id=client_request_id,
                    detail="message is not a completed assistant output",
                )
            content = item.get("content")
            if not isinstance(content, list) or not content:
                raise NoToolsAdapterError(
                    AdapterFailureCode.PROVIDER_RESPONSE_INVALID,
                    client_request_id=client_request_id,
                    detail="message content is empty",
                )
            for content_item in content:
                if not isinstance(content_item, Mapping):
                    raise NoToolsAdapterError(
                        AdapterFailureCode.PROVIDER_OUTPUT_FORBIDDEN,
                        client_request_id=client_request_id,
                        detail="non-object message content",
                    )
                if content_item.get("type") == "refusal":
                    raise NoToolsAdapterError(
                        AdapterFailureCode.PROVIDER_REFUSAL,
                        client_request_id=client_request_id,
                    )
                if (
                    content_item.get("type") != "output_text"
                    or not set(content_item).issubset(_ALLOWED_OUTPUT_TEXT_KEYS)
                    or content_item.get("annotations", []) != []
                    or not isinstance(content_item.get("text"), str)
                ):
                    raise NoToolsAdapterError(
                        AdapterFailureCode.PROVIDER_OUTPUT_FORBIDDEN,
                        client_request_id=client_request_id,
                        detail="message content is not unannotated output_text",
                    )
                output_texts.append(str(content_item["text"]))
        if message_count != 1 or len(output_texts) != 1:
            raise NoToolsAdapterError(
                AdapterFailureCode.PROVIDER_RESPONSE_INVALID,
                client_request_id=client_request_id,
                detail="expected exactly one output_text message",
            )
        return output_texts[0]

    @staticmethod
    def _parse_usage(value: Any, client_request_id: str) -> ModelUsage:
        if not isinstance(value, Mapping):
            raise NoToolsAdapterError(
                AdapterFailureCode.USAGE_INCOMPLETE,
                client_request_id=client_request_id,
            )
        required = ("input_tokens", "output_tokens", "total_tokens")
        if any(
            isinstance(value.get(key), bool)
            or not isinstance(value.get(key), int)
            or value[key] < 0
            for key in required
        ):
            raise NoToolsAdapterError(
                AdapterFailureCode.USAGE_INCOMPLETE,
                client_request_id=client_request_id,
            )
        input_details = value.get("input_tokens_details")
        output_details = value.get("output_tokens_details")
        cached_tokens = (
            input_details.get("cached_tokens")
            if isinstance(input_details, Mapping)
            and isinstance(input_details.get("cached_tokens"), int)
            else None
        )
        reasoning_tokens = (
            output_details.get("reasoning_tokens")
            if isinstance(output_details, Mapping)
            and isinstance(output_details.get("reasoning_tokens"), int)
            else None
        )
        return ModelUsage(
            input_tokens=value["input_tokens"],
            output_tokens=value["output_tokens"],
            total_tokens=value["total_tokens"],
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
        )
