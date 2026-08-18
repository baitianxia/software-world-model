"""DeepSeek OpenAI-format Chat Completions no-tools adapter.

This adapter deliberately has its own provider identity and wire contract.  It
does not inherit Volcengine Ark conformance merely because both providers expose
an OpenAI-compatible Chat Completions surface.  Only non-secret settings enter
the configuration fingerprint; the API key is resolved immediately before the
exact HTTPS dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import http.client
import json
import os
import re
import socket
import ssl
from typing import Callable, Mapping, Protocol
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlsplit

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .direct_https import build_direct_https_opener
from .model_gateway import (
    AdapterConformanceLevel,
    AdapterResponse,
    ProviderAdapterCapabilities,
    ProviderOutputRejected,
    ProviderOutcomeUnknown,
    ProviderRequest,
    ReplayClassification,
)
from .openai_responses_adapter import OutputSchemaDefinition, ProviderHTTPResponse


DEFAULT_DEEPSEEK_OPENAI_BASE_URL = "https://api.deepseek.com"
DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT = (
    f"{DEFAULT_DEEPSEEK_OPENAI_BASE_URL}/chat/completions"
)
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-pro"
DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT = "deepseek-v4-pro"
DEFAULT_DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"
DEFAULT_DEEPSEEK_TEMPERATURE = 0
SUPPORTED_DEEPSEEK_MODELS = frozenset(
    {"deepseek-v4-pro", "deepseek-v4-flash"}
)
_DEEPSEEK_HOST = "api.deepseek.com"
_DEEPSEEK_PORT = 443
_DEEPSEEK_PATH = "/chat/completions"
_ENVIRONMENT_NAME = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_MARKDOWN_JSON_FENCE = re.compile(
    r"\A(?P<prefix>[\s\S]*?)```json[ \t]*\r?\n(?P<body>[\s\S]*?)\r?\n```\Z"
)
_MAX_MARKDOWN_JSON_PREFIX_BYTES = 512


@dataclass(frozen=True, slots=True)
class DeepSeekModelConfiguration:
    """Exact, auditable DeepSeek settings containing only a secret reference."""

    endpoint: str = DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT
    model_ref: str = DEFAULT_DEEPSEEK_MODEL
    actual_model_fingerprint: str = DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT
    api_key_environment_variable: str = DEFAULT_DEEPSEEK_API_KEY_ENV
    temperature: int = DEFAULT_DEEPSEEK_TEMPERATURE

    def __post_init__(self) -> None:
        _require_deepseek_https_endpoint(self.endpoint)
        if self.model_ref not in SUPPORTED_DEEPSEEK_MODELS:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek model reference is not in the supported exact model set",
            )
        if self.actual_model_fingerprint not in SUPPORTED_DEEPSEEK_MODELS:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek actual model fingerprint is not in the supported exact model set",
            )
        if self.actual_model_fingerprint != self.model_ref:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek requested and expected response model identities must match",
            )
        if not _ENVIRONMENT_NAME.fullmatch(self.api_key_environment_variable):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek API key environment variable name is invalid",
            )
        if (
            type(self.temperature) is not int
            or self.temperature != DEFAULT_DEEPSEEK_TEMPERATURE
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek no-tools adapter requires the exact frozen temperature 0",
            )

    @property
    def provider_type(self) -> str:
        return DeepSeekChatCompletionsNoToolsAdapter.provider_type

    @property
    def base_url(self) -> str:
        return self.endpoint.removesuffix(_DEEPSEEK_PATH)

    @property
    def adapter_version(self) -> str:
        return DeepSeekChatCompletionsNoToolsAdapter.adapter_version

    @property
    def qualified_model_identities(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys((self.model_ref, self.actual_model_fingerprint)))

    @property
    def secret_reference(self) -> str:
        return f"env:{self.api_key_environment_variable}"

    @property
    def fingerprint(self) -> Digest:
        return digest_of(
            {
                "provider_type": self.provider_type,
                "adapter_version": self.adapter_version,
                "protocol": "DEEPSEEK_OPENAI_FORMAT_CHAT_COMPLETIONS",
                "base_url": self.base_url,
                "endpoint": self.endpoint,
                "model_ref": self.model_ref,
                "actual_model_fingerprint": self.actual_model_fingerprint,
                "thinking_mode": "DISABLED",
                "temperature": self.temperature,
                "secret_reference": self.secret_reference,
            }
        )

    def credential_configured(self, environment: Mapping[str, str] | None = None) -> bool:
        values = os.environ if environment is None else environment
        return bool(values.get(self.api_key_environment_variable))

    def resolve_api_key(self, environment: Mapping[str, str] | None = None) -> str:
        values = os.environ if environment is None else environment
        api_key = values.get(self.api_key_environment_variable, "")
        if not api_key:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                f"DeepSeek credential reference {self.secret_reference} is not configured",
            )
        return api_key

    def public_status(self, environment: Mapping[str, str] | None = None) -> dict[str, object]:
        return {
            "provider_type": self.provider_type,
            "protocol": "DEEPSEEK_OPENAI_FORMAT_CHAT_COMPLETIONS",
            "adapter_version": self.adapter_version,
            "base_url": self.base_url,
            "endpoint": self.endpoint,
            "model_ref": self.model_ref,
            "actual_model_fingerprint": self.actual_model_fingerprint,
            "thinking_mode": "DISABLED",
            "temperature": self.temperature,
            "secret_reference": self.secret_reference,
            "credential_configured": self.credential_configured(environment),
            "configuration_fingerprint": self.fingerprint.value,
            "live_conformance": "NOT_RUN",
        }


class DeepSeekChatCompletionsTransport(Protocol):
    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse: ...


class DeepSeekChatLiveQualification(Protocol):
    result_ref: str
    qualified_model_fingerprints: tuple[str, ...]
    valid_until: datetime


@dataclass(frozen=True, slots=True)
class RecordedDeepSeekChatCompletionsRequest:
    endpoint: str
    body: bytes
    client_request_id: str
    timeout_milliseconds: int


class RecordingDeepSeekChatCompletionsTransport:
    """Record only non-secret wire data before delegating."""

    def __init__(self, delegate: DeepSeekChatCompletionsTransport) -> None:
        self._delegate = delegate
        self.requests: list[RecordedDeepSeekChatCompletionsRequest] = []

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse:
        self.requests.append(
            RecordedDeepSeekChatCompletionsRequest(
                endpoint=endpoint,
                body=body,
                client_request_id=client_request_id,
                timeout_milliseconds=timeout_milliseconds,
            )
        )
        return self._delegate.post_json(
            endpoint=endpoint,
            body=body,
            client_request_id=client_request_id,
            timeout_milliseconds=timeout_milliseconds,
        )


class UrllibDeepSeekChatTransport:
    """Bearer-authenticated direct HTTPS transport with an exact host boundary."""

    def __init__(self, *, api_key_resolver: Callable[[], str], opener: object | None = None) -> None:
        self._api_key_resolver = api_key_resolver
        self._opener = opener or build_direct_https_opener()

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse:
        _require_deepseek_https_endpoint(endpoint)
        api_key = self._api_key_resolver()
        if not api_key:
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "DeepSeek credential is not configured",
            )
        request = urllib_request.Request(
            endpoint,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-Client-Request-Id": client_request_id,
            },
            method="POST",
        )
        try:
            with self._opener.open(request, timeout=timeout_milliseconds / 1000) as response:
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
        except (
            urllib_error.URLError,
            TimeoutError,
            socket.timeout,
            http.client.RemoteDisconnected,
        ) as exc:
            raise ProviderOutcomeUnknown(
                "DeepSeek Chat Completions outcome is unknown",
                reason_code=_network_failure_reason(exc),
            ) from exc


class DeepSeekChatCompletionsNoToolsAdapter:
    provider_type = "DEEPSEEK"
    adapter_version = "deepseek-chat-completions-no-tools@2"

    def __init__(
        self,
        *,
        transport: DeepSeekChatCompletionsTransport,
        configuration: DeepSeekModelConfiguration,
        output_schemas: Mapping[str, OutputSchemaDefinition],
        pinned_models: frozenset[str] = frozenset(),
        observed_revisions_by_alias: Mapping[str, frozenset[str]] | None = None,
        live_qualification: DeepSeekChatLiveQualification | None = None,
        enforce_output_schema: bool = True,
    ) -> None:
        if live_qualification is None:
            conformance_level = AdapterConformanceLevel.OFFLINE_FIXTURE
            conformance_result_ref = "CC-DEEPSEEK-CHAT-NO-TOOLS-001:NOT-RUN"
            qualified_model_fingerprints: tuple[str, ...] = ()
        else:
            if (
                live_qualification.qualified_model_fingerprints
                != configuration.qualified_model_identities
                or live_qualification.valid_until.tzinfo is None
                or live_qualification.valid_until.utcoffset() is None
                or datetime.now(timezone.utc) >= live_qualification.valid_until
                or not live_qualification.result_ref.startswith(
                    "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:"
                )
            ):
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "live DeepSeek adapter qualification is invalid, stale, or for another model",
                )
            conformance_level = AdapterConformanceLevel.LIVE_CURRENT
            conformance_result_ref = live_qualification.result_ref
            qualified_model_fingerprints = live_qualification.qualified_model_fingerprints
            pinned_models = pinned_models | frozenset(qualified_model_fingerprints)
        self._transport = transport
        self._configuration = configuration
        self._output_schemas = dict(output_schemas)
        self._pinned_models = pinned_models
        self._enforce_output_schema = enforce_output_schema
        self._observed = dict(observed_revisions_by_alias or {})
        self._observed.setdefault(
            configuration.model_ref,
            frozenset({configuration.actual_model_fingerprint}),
        )
        self.capabilities = ProviderAdapterCapabilities(
            no_external_access=True,
            hidden_context_disabled=True,
            stateless_session=True,
            structured_output=True,
            actual_fingerprint_reported=True,
            conformance_level=conformance_level,
            conformance_result_ref=conformance_result_ref,
            qualified_model_fingerprints=qualified_model_fingerprints,
        )

    def invoke(self, request: ProviderRequest) -> AdapterResponse:
        if request.model_ref != self._configuration.model_ref:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "requested model does not match the frozen DeepSeek configuration",
            )
        if request.tools or request.store or request.stream:
            raise DomainError(
                ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
                "no-tools adapter requires empty tools, store=false, and stream=false",
            )
        definition = self._output_schemas.get(request.output_schema_ref)
        if definition is None:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "output schema reference is not registered")
        schema_instruction = _json_object_schema_instruction(definition)
        payload: dict[str, object] = {
            "model": request.model_ref,
            "messages": [{"role": "system", "content": schema_instruction}] + [
                {"role": message.role, "content": message.content}
                for message in request.messages
            ],
            "stream": False,
            "max_tokens": request.max_output_tokens,
            "thinking": {"type": "disabled"},
            "temperature": self._configuration.temperature,
            "response_format": {"type": "json_object"},
        }
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        client_request_id = f"swm-{request.digest.value.removeprefix('sha256:')[:32]}"
        response = self._transport.post_json(
            endpoint=self._configuration.endpoint,
            body=body,
            client_request_id=client_request_id,
            timeout_milliseconds=request.timeout_milliseconds,
        )
        if not 200 <= response.status_code < 300:
            details = _provider_error_details(response)
            details["http_status"] = response.status_code
            raise DomainError(
                ErrorCode.PROVIDER_HTTP_ERROR,
                "DeepSeek Chat Completions request returned a non-success status",
                details,
            )
        payload = _json_object(response.body)
        if payload.get("object") != "chat.completion":
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "DeepSeek response is not a non-streaming chat completion",
            )
        raw_output_text, finish_reason = _extract_choice(payload)
        output_text, output_normalization = _normalize_structured_output_text(raw_output_text)
        actual_model = payload.get("model")
        if not isinstance(actual_model, str) or not actual_model:
            raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider model identity is missing")
        response_id = payload.get("id")
        if not isinstance(response_id, str) or not response_id:
            raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider response identity is missing")
        input_tokens, output_tokens, usage_complete = _usage(payload.get("usage"))
        headers = {key.lower(): value for key, value in response.headers.items()}
        provider_request_id = headers.get("x-request-id") or response_id
        adapter_response = AdapterResponse.create(
            provider_request_id=provider_request_id,
            actual_model_fingerprint=actual_model,
            replay_classification=self._classify(request.model_ref, actual_model),
            output_text=output_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            usage_complete=usage_complete,
            termination_reason=finish_reason,
            output_normalization=output_normalization,
        )
        if finish_reason != "stop":
            error = DomainError(
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
                "provider response ended before the structured output completed",
                {"finish_reason": finish_reason},
            )
            raise ProviderOutputRejected(error, adapter_response)
        try:
            if self._enforce_output_schema:
                definition.validate_output_text(output_text)
            else:
                _validate_json_object_text(output_text)
        except DomainError as exc:
            if exc.code is ErrorCode.STRUCTURED_OUTPUT_INVALID:
                raise ProviderOutputRejected(exc, adapter_response) from exc
            raise
        return adapter_response

    def _classify(self, requested: str, actual: str) -> ReplayClassification:
        if (
            requested in self._pinned_models
            and actual in self._pinned_models
            and (
                requested == actual
                or actual in self._observed.get(requested, frozenset())
            )
        ):
            return ReplayClassification.PINNED
        if actual in self._observed.get(requested, frozenset()):
            return ReplayClassification.OBSERVED_MUTABLE
        return ReplayClassification.UNRESOLVED_MUTABLE


def _require_deepseek_https_endpoint(endpoint: str) -> None:
    parsed = urlsplit(endpoint)
    try:
        port = parsed.port
    except ValueError as exc:
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "DeepSeek endpoint port is invalid") from exc
    if (
        parsed.scheme != "https"
        or parsed.hostname != _DEEPSEEK_HOST
        or port not in {None, _DEEPSEEK_PORT}
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path != _DEEPSEEK_PATH
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "DeepSeek endpoint must be the exact direct Chat Completions HTTPS endpoint",
        )


def _json_object_schema_instruction(definition: OutputSchemaDefinition) -> str:
    schema = json.dumps(
        definition.schema,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (
        "Return exactly one JSON object matching the following closed JSON Schema. "
        "Do not emit Markdown fences or text outside the object. Schema name: "
        f"{definition.name}. Schema: {schema}"
    )


def _validate_json_object_text(output_text: str) -> None:
    try:
        decoded = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise DomainError(ErrorCode.STRUCTURED_OUTPUT_INVALID, "output text is not JSON") from exc
    if not isinstance(decoded, dict):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "structured output root is not an object",
        )


def _json_object(body: bytes) -> Mapping[str, object]:
    try:
        value = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider response is not JSON") from exc
    if not isinstance(value, dict):
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider response is not an object")
    return value


def _provider_error_details(response: ProviderHTTPResponse) -> dict[str, str | int]:
    details: dict[str, str | int] = {}
    headers = {key.lower(): value for key, value in response.headers.items()}
    request_id = headers.get("x-request-id")
    if isinstance(request_id, str) and 0 < len(request_id) <= 256:
        details["provider_request_id"] = request_id
    try:
        payload = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return details
    if not isinstance(payload, dict):
        return details
    error = payload.get("error")
    if not isinstance(error, dict):
        return details
    for source, target in (("code", "provider_error_code"), ("type", "provider_error_type")):
        value = error.get(source)
        if (
            isinstance(value, str)
            and 0 < len(value) <= 128
            and re.fullmatch(r"[A-Za-z0-9._-]+", value)
        ):
            details[target] = value
    return details


def _extract_choice(payload: Mapping[str, object]) -> tuple[str, str]:
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider must return exactly one choice")
    choice = choices[0]
    if choice.get("index") != 0:
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider choice index is invalid")
    finish_reason = choice.get("finish_reason")
    if finish_reason == "content_filter":
        raise DomainError(ErrorCode.PROVIDER_REFUSAL, "provider content filter refused the request")
    if not isinstance(finish_reason, str) or not finish_reason:
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "provider finish reason is missing")
    message = choice.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "assistant message is missing")
    for field in ("tool_calls", "function_call", "audio"):
        if message.get(field) not in (None, []):
            raise DomainError(ErrorCode.PROVIDER_OUTPUT_FORBIDDEN, f"provider returned {field}")
    if message.get("reasoning_content") not in (None, ""):
        raise DomainError(
            ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
            "provider returned reasoning content while thinking is disabled",
        )
    refusal = message.get("refusal")
    if isinstance(refusal, str) and refusal:
        raise DomainError(ErrorCode.PROVIDER_REFUSAL, "provider refused the request")
    content = message.get("content")
    if not isinstance(content, str) or not content:
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "assistant content is empty")
    return content, finish_reason


def _normalize_structured_output_text(output_text: str) -> tuple[str, str]:
    match = _MARKDOWN_JSON_FENCE.fullmatch(output_text.strip())
    if match is None:
        return output_text, "IDENTITY"
    prefix = match.group("prefix").strip()
    if (
        len(prefix.encode("utf-8")) > _MAX_MARKDOWN_JSON_PREFIX_BYTES
        or "```" in prefix
        or any(character in prefix for character in "{}[]")
    ):
        return output_text, "IDENTITY"
    candidate = match.group("body").strip()
    try:
        decoded = json.loads(candidate)
    except json.JSONDecodeError:
        return output_text, "IDENTITY"
    if not isinstance(decoded, dict):
        return output_text, "IDENTITY"
    normalization = (
        "MARKDOWN_JSON_FENCE_V1"
        if not prefix
        else "MARKDOWN_JSON_FENCE_WITH_PREFIX_V1"
    )
    return candidate, normalization


def _usage(value: object) -> tuple[int | None, int | None, bool]:
    if not isinstance(value, dict):
        return None, None, False
    input_tokens = value.get("prompt_tokens")
    output_tokens = value.get("completion_tokens")
    total_tokens = value.get("total_tokens")
    if (
        not isinstance(input_tokens, int)
        or input_tokens < 0
        or not isinstance(output_tokens, int)
        or output_tokens < 0
        or not isinstance(total_tokens, int)
        or total_tokens != input_tokens + output_tokens
    ):
        return None, None, False
    return input_tokens, output_tokens, True


def _network_failure_reason(exc: BaseException) -> str:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "TIMEOUT"
    reason = exc.reason if isinstance(exc, urllib_error.URLError) else exc
    if isinstance(reason, http.client.RemoteDisconnected):
        return "REMOTE_DISCONNECTED"
    if isinstance(reason, socket.gaierror):
        return "DNS_RESOLUTION_FAILED"
    if isinstance(reason, ConnectionRefusedError):
        return "CONNECTION_REFUSED"
    if isinstance(reason, ssl.SSLCertVerificationError):
        return "TLS_CERTIFICATE_VERIFY_FAILED"
    if isinstance(reason, ssl.SSLError):
        return "TLS_FAILURE"
    return "NETWORK_FAILURE"


__all__ = [
    "DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT",
    "DEFAULT_DEEPSEEK_API_KEY_ENV",
    "DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT",
    "DEFAULT_DEEPSEEK_MODEL",
    "DEFAULT_DEEPSEEK_OPENAI_BASE_URL",
    "DEFAULT_DEEPSEEK_TEMPERATURE",
    "SUPPORTED_DEEPSEEK_MODELS",
    "DeepSeekChatCompletionsNoToolsAdapter",
    "DeepSeekChatCompletionsTransport",
    "DeepSeekModelConfiguration",
    "RecordedDeepSeekChatCompletionsRequest",
    "RecordingDeepSeekChatCompletionsTransport",
    "UrllibDeepSeekChatTransport",
]
