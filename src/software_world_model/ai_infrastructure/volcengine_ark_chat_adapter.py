"""Volcengine Ark OpenAI-compatible Chat Completions no-tools adapter.

Only non-secret provider settings are held by the configuration object.  The
API key is resolved from its named environment variable only after the exact
peer TLS certificate is verified and immediately before HTTP dispatch.  It is
never added to request recordings or configuration fingerprints.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import http.client
import json
import os
import re
import socket
import ssl
from typing import Callable, Mapping, Protocol
from urllib.parse import urlsplit

from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of

from .direct_https import build_verified_tls_context
from .model_gateway import (
    AdapterConformanceLevel,
    AdapterResponse,
    ProviderAdapterCapabilities,
    ProviderOutputRejected,
    ProviderOutcomeUnknown,
    ProviderUnavailable,
    ProviderRequest,
    ReplayClassification,
)
from .openai_responses_adapter import OutputSchemaDefinition, ProviderHTTPResponse


DEFAULT_VOLCENGINE_ARK_OPENAI_BASE_URL = (
    "https://ark.cn-beijing.volces.com/api/coding/v3"
)
DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT = (
    f"{DEFAULT_VOLCENGINE_ARK_OPENAI_BASE_URL}/chat/completions"
)
DEFAULT_VOLCENGINE_ARK_MODEL = "glm-5-2-260617"
DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT = "glm-5.3"
DEFAULT_VOLCENGINE_ARK_API_KEY_ENV = "ARK_API_KEY"
DEFAULT_VOLCENGINE_ARK_CONNECTION_POLICY = (
    "DIRECT_VERIFIED_TLS_HTTP11_ONE_REQUEST_PER_SESSION@1"
)
DEFAULT_VOLCENGINE_ARK_CREDENTIAL_RESOLUTION_POLICY = (
    "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH"
)
DEFAULT_VOLCENGINE_ARK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES_PER_REQUEST = 1
DEFAULT_VOLCENGINE_ARK_MAXIMUM_HTTP_DISPATCHES_PER_TLS_SESSION = 1
_VOLCENGINE_ARK_HOST = "ark.cn-beijing.volces.com"
_VOLCENGINE_ARK_PORT = 443
_VOLCENGINE_ARK_PATH = "/api/coding/v3/chat/completions"
_MAX_RESPONSE_BYTES = 16 * 1024 * 1024
_ENVIRONMENT_NAME = re.compile(r"^[A-Z_][A-Z0-9_]*$")
_MARKDOWN_JSON_FENCE = re.compile(
    r"\A(?P<prefix>[\s\S]*?)```json[ \t]*\r?\n(?P<body>[\s\S]*?)\r?\n```\Z"
)
_MAX_MARKDOWN_JSON_PREFIX_BYTES = 512


@dataclass(frozen=True, slots=True)
class VolcengineArkModelConfiguration:
    """Auditable provider settings containing a secret reference, never a key."""

    endpoint: str = DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT
    model_ref: str = DEFAULT_VOLCENGINE_ARK_MODEL
    actual_model_fingerprint: str = DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT
    api_key_environment_variable: str = DEFAULT_VOLCENGINE_ARK_API_KEY_ENV

    def __post_init__(self) -> None:
        _require_ark_https_endpoint(self.endpoint)
        if not self.model_ref or self.model_ref != self.model_ref.strip():
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Ark model reference is required")
        if (
            not self.actual_model_fingerprint
            or self.actual_model_fingerprint != self.actual_model_fingerprint.strip()
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Ark actual model fingerprint is required",
            )
        if not _ENVIRONMENT_NAME.fullmatch(self.api_key_environment_variable):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Ark API key environment variable name is invalid",
            )

    @property
    def provider_type(self) -> str:
        return VolcengineArkChatCompletionsNoToolsAdapter.provider_type

    @property
    def base_url(self) -> str:
        return self.endpoint.removesuffix("/chat/completions")

    @property
    def adapter_version(self) -> str:
        return VolcengineArkChatCompletionsNoToolsAdapter.adapter_version

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
                "protocol": "OPENAI_COMPATIBLE_CHAT_COMPLETIONS",
                "base_url": self.base_url,
                "endpoint": self.endpoint,
                "model_ref": self.model_ref,
                "actual_model_fingerprint": self.actual_model_fingerprint,
                "connection_policy": DEFAULT_VOLCENGINE_ARK_CONNECTION_POLICY,
                "maximum_pre_dispatch_tls_handshakes_per_request": (
                    DEFAULT_VOLCENGINE_ARK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES_PER_REQUEST
                ),
                "maximum_http_dispatches_per_tls_session": (
                    DEFAULT_VOLCENGINE_ARK_MAXIMUM_HTTP_DISPATCHES_PER_TLS_SESSION
                ),
                "credential_resolution_policy": (
                    DEFAULT_VOLCENGINE_ARK_CREDENTIAL_RESOLUTION_POLICY
                ),
                "request_retry_allowed": False,
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
                f"Ark credential reference {self.secret_reference} is not configured",
            )
        return api_key

    def public_status(self, environment: Mapping[str, str] | None = None) -> dict[str, object]:
        return {
            "provider_type": self.provider_type,
            "protocol": "OPENAI_COMPATIBLE_CHAT_COMPLETIONS",
            "adapter_version": self.adapter_version,
            "base_url": self.base_url,
            "endpoint": self.endpoint,
            "model_ref": self.model_ref,
            "actual_model_fingerprint": self.actual_model_fingerprint,
            "connection_policy": DEFAULT_VOLCENGINE_ARK_CONNECTION_POLICY,
            "maximum_pre_dispatch_tls_handshakes_per_request": (
                DEFAULT_VOLCENGINE_ARK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES_PER_REQUEST
            ),
            "maximum_http_dispatches_per_tls_session": (
                DEFAULT_VOLCENGINE_ARK_MAXIMUM_HTTP_DISPATCHES_PER_TLS_SESSION
            ),
            "credential_resolution_policy": (
                DEFAULT_VOLCENGINE_ARK_CREDENTIAL_RESOLUTION_POLICY
            ),
            "request_retry_allowed": False,
            "secret_reference": self.secret_reference,
            "credential_configured": self.credential_configured(environment),
            "configuration_fingerprint": self.fingerprint.value,
            "live_conformance": "NOT_RUN",
        }


class ChatCompletionsTransport(Protocol):
    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse: ...


class ArkChatLiveQualification(Protocol):
    """Structural boundary that avoids a conformance-module import cycle."""

    result_ref: str
    qualified_model_fingerprints: tuple[str, ...]
    valid_until: datetime


@dataclass(frozen=True, slots=True)
class RecordedChatCompletionsRequest:
    endpoint: str
    body: bytes
    client_request_id: str
    timeout_milliseconds: int


class RecordingChatCompletionsTransport:
    """Record only the non-secret wire body before delegating."""

    def __init__(self, delegate: ChatCompletionsTransport) -> None:
        self._delegate = delegate
        self.requests: list[RecordedChatCompletionsRequest] = []

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse:
        self.requests.append(
            RecordedChatCompletionsRequest(
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

    def session_audit(self) -> dict[str, object]:
        return ark_transport_session_audit(self._delegate)


class _VerifiedTLSSocket(Protocol):
    def getpeercert(self, *, binary_form: bool = False) -> object: ...

    def sendall(self, value: bytes) -> None: ...

    def close(self) -> None: ...


class DirectVerifiedVolcengineArkChatTransport:
    """Direct exact-host HTTPS with one verified TLS session per request.

    A request performs exactly one credential-free TLS acquisition.  The API
    key is resolved only after the peer certificate has been verified, and the
    verified session carries exactly one HTTP dispatch.  No connection or
    request retry is performed.  A network failure after HTTP dispatch begins
    is conservatively reported as outcome unknown.
    """

    def __init__(
        self,
        *,
        api_key_resolver: Callable[[], str],
        connection_factory: Callable[[float], _VerifiedTLSSocket] | None = None,
        tls_context: ssl.SSLContext | None = None,
        maximum_pre_dispatch_tls_handshakes_per_request: int = (
            DEFAULT_VOLCENGINE_ARK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES_PER_REQUEST
        ),
    ) -> None:
        if (
            type(maximum_pre_dispatch_tls_handshakes_per_request) is not int
            or maximum_pre_dispatch_tls_handshakes_per_request
            != DEFAULT_VOLCENGINE_ARK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES_PER_REQUEST
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Ark transport requires exactly one pre-dispatch TLS attempt per request",
            )
        self._api_key_resolver = api_key_resolver
        self._tls_context = tls_context or build_verified_tls_context()
        self._connection_factory = connection_factory or self._new_tls_socket
        self._tls_handshake_attempt_count = 0
        self._tls_handshake_success_count = 0
        self._pre_dispatch_tls_failure_codes: list[str] = []
        self._peer_certificate_sha256s: list[str] = []
        self._http_dispatch_count = 0
        self._post_dispatch_failure_codes: list[str] = []
        self._credential_resolution_count = 0
        self._credential_resolution_success_count = 0

    @property
    def tls_handshake_attempt_count(self) -> int:
        return self._tls_handshake_attempt_count

    @property
    def tls_handshake_success_count(self) -> int:
        return self._tls_handshake_success_count

    @property
    def http_dispatch_count(self) -> int:
        return self._http_dispatch_count

    def session_audit(self) -> dict[str, object]:
        return {
            "schema": "SWM-VOLCENGINE-ARK-TRANSPORT-SESSION-AUDIT@1",
            "connection_policy": DEFAULT_VOLCENGINE_ARK_CONNECTION_POLICY,
            "maximum_pre_dispatch_tls_handshake_attempts_per_request": (
                DEFAULT_VOLCENGINE_ARK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES_PER_REQUEST
            ),
            "maximum_http_dispatches_per_tls_session": (
                DEFAULT_VOLCENGINE_ARK_MAXIMUM_HTTP_DISPATCHES_PER_TLS_SESSION
            ),
            "tls_handshake_attempt_count": self._tls_handshake_attempt_count,
            "tls_handshake_success_count": self._tls_handshake_success_count,
            "pre_dispatch_tls_handshake_failure_count": len(
                self._pre_dispatch_tls_failure_codes
            ),
            "pre_dispatch_tls_failure_codes": list(
                self._pre_dispatch_tls_failure_codes
            ),
            "http_dispatch_count": self._http_dispatch_count,
            "connection_reuse_count": 0,
            "verified_peer_certificate_sha256s": list(
                self._peer_certificate_sha256s
            ),
            "post_dispatch_outcome_unknown_count": len(
                self._post_dispatch_failure_codes
            ),
            "post_dispatch_failure_codes": list(
                self._post_dispatch_failure_codes
            ),
            "request_retry_count": 0,
            "credential_resolution_count": self._credential_resolution_count,
            "credential_resolution_success_count": (
                self._credential_resolution_success_count
            ),
            "credential_resolution_policy": (
                DEFAULT_VOLCENGINE_ARK_CREDENTIAL_RESOLUTION_POLICY
            ),
        }

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse:
        _require_ark_https_endpoint(endpoint)
        if not isinstance(body, bytes) or not body:
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Ark request body is empty")
        if (
            not isinstance(client_request_id, str)
            or not client_request_id
            or "\r" in client_request_id
            or "\n" in client_request_id
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Ark client request ID is invalid",
            )
        if type(timeout_milliseconds) is not int or timeout_milliseconds < 1:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Ark timeout must be positive",
            )

        tls_socket = self._acquire_tls_socket(timeout_milliseconds / 1000)
        self._credential_resolution_count += 1
        try:
            api_key = self._api_key_resolver()
        except Exception:
            tls_socket.close()
            raise
        if (
            not isinstance(api_key, str)
            or not api_key
            or "\r" in api_key
            or "\n" in api_key
        ):
            tls_socket.close()
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "Ark credential is not configured",
            )
        try:
            api_key_bytes = api_key.encode("ascii")
            client_request_id_bytes = client_request_id.encode("ascii")
        except UnicodeEncodeError as exc:
            tls_socket.close()
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "Ark credential or client request ID is not ASCII",
            ) from exc
        self._credential_resolution_success_count += 1
        self._http_dispatch_count += 1
        try:
            request_headers = (
                f"POST {_VOLCENGINE_ARK_PATH} HTTP/1.1\r\n".encode("ascii")
                + f"Host: {_VOLCENGINE_ARK_HOST}\r\n".encode("ascii")
                + b"Authorization: Bearer "
                + api_key_bytes
                + b"\r\nContent-Type: application/json\r\n"
                + b"Accept: text/event-stream\r\n"
                + b"X-Client-Request-Id: "
                + client_request_id_bytes
                + b"\r\n"
                + f"Content-Length: {len(body)}\r\n".encode("ascii")
                + b"Connection: close\r\n\r\n"
            )
            tls_socket.sendall(request_headers + body)
            response = http.client.HTTPResponse(tls_socket)
            response.begin()
            response_body = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(response_body) > _MAX_RESPONSE_BYTES:
                raise DomainError(
                    ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
                    "Ark response exceeds the closed size limit",
                )
            return ProviderHTTPResponse(
                status_code=response.status,
                headers={key.lower(): value for key, value in response.getheaders()},
                body=response_body,
            )
        except (
            OSError,
            TimeoutError,
            socket.timeout,
            ssl.SSLError,
            http.client.HTTPException,
            http.client.RemoteDisconnected,
        ) as exc:
            reason = _network_failure_reason(exc)
            self._post_dispatch_failure_codes.append(reason)
            raise ProviderOutcomeUnknown(
                "Ark Chat Completions outcome is unknown",
                reason_code=reason,
            ) from exc
        finally:
            tls_socket.close()

    def _new_tls_socket(self, timeout_seconds: float) -> _VerifiedTLSSocket:
        raw_socket = socket.create_connection(
            (_VOLCENGINE_ARK_HOST, _VOLCENGINE_ARK_PORT),
            timeout=timeout_seconds,
        )
        try:
            return self._tls_context.wrap_socket(
                raw_socket,
                server_hostname=_VOLCENGINE_ARK_HOST,
            )
        except Exception:
            raw_socket.close()
            raise

    def _acquire_tls_socket(self, timeout_seconds: float) -> _VerifiedTLSSocket:
        self._tls_handshake_attempt_count += 1
        tls_socket: _VerifiedTLSSocket | None = None
        try:
            tls_socket = self._connection_factory(timeout_seconds)
            certificate = tls_socket.getpeercert(binary_form=True)
            if not isinstance(certificate, bytes) or not certificate:
                raise ssl.SSLError("Ark peer did not provide a certificate")
        except (
            OSError,
            TimeoutError,
            socket.timeout,
            ssl.SSLError,
            http.client.HTTPException,
        ) as exc:
            if tls_socket is not None:
                tls_socket.close()
            reason = _network_failure_reason(exc)
            self._pre_dispatch_tls_failure_codes.append(reason)
            raise ProviderUnavailable(
                "Ark credential-free TLS acquisition failed",
                reason_code=reason,
            ) from exc
        self._tls_handshake_success_count += 1
        self._peer_certificate_sha256s.append(
            "sha256:" + sha256(certificate).hexdigest()
        )
        return tls_socket


def ark_transport_session_audit(transport: object) -> dict[str, object]:
    method = getattr(transport, "session_audit", None)
    if not callable(method):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark transport does not expose the required session audit",
        )
    return verify_ark_transport_session_audit(method())


def verify_ark_transport_session_audit(value: object) -> dict[str, object]:
    required = {
        "schema",
        "connection_policy",
        "maximum_pre_dispatch_tls_handshake_attempts_per_request",
        "maximum_http_dispatches_per_tls_session",
        "tls_handshake_attempt_count",
        "tls_handshake_success_count",
        "pre_dispatch_tls_handshake_failure_count",
        "pre_dispatch_tls_failure_codes",
        "http_dispatch_count",
        "connection_reuse_count",
        "verified_peer_certificate_sha256s",
        "post_dispatch_outcome_unknown_count",
        "post_dispatch_failure_codes",
        "request_retry_count",
        "credential_resolution_count",
        "credential_resolution_success_count",
        "credential_resolution_policy",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark transport session audit shape is invalid",
        )
    integer_fields = (
        "maximum_pre_dispatch_tls_handshake_attempts_per_request",
        "maximum_http_dispatches_per_tls_session",
        "tls_handshake_attempt_count",
        "tls_handshake_success_count",
        "pre_dispatch_tls_handshake_failure_count",
        "http_dispatch_count",
        "connection_reuse_count",
        "post_dispatch_outcome_unknown_count",
        "request_retry_count",
        "credential_resolution_count",
        "credential_resolution_success_count",
    )
    if any(type(value.get(field)) is not int for field in integer_fields):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark transport session audit counters are invalid",
        )
    attempts = int(value["tls_handshake_attempt_count"])
    successes = int(value["tls_handshake_success_count"])
    pre_dispatch_failures = int(
        value["pre_dispatch_tls_handshake_failure_count"]
    )
    dispatches = int(value["http_dispatch_count"])
    unknown = int(value["post_dispatch_outcome_unknown_count"])
    credential_reads = int(value["credential_resolution_count"])
    credential_successes = int(value["credential_resolution_success_count"])
    pre_dispatch_codes = value["pre_dispatch_tls_failure_codes"]
    post_dispatch_codes = value["post_dispatch_failure_codes"]
    certificate_digests = value["verified_peer_certificate_sha256s"]
    if (
        value.get("schema")
        != "SWM-VOLCENGINE-ARK-TRANSPORT-SESSION-AUDIT@1"
        or value.get("connection_policy")
        != DEFAULT_VOLCENGINE_ARK_CONNECTION_POLICY
        or value.get("maximum_pre_dispatch_tls_handshake_attempts_per_request")
        != DEFAULT_VOLCENGINE_ARK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES_PER_REQUEST
        or value.get("maximum_http_dispatches_per_tls_session")
        != DEFAULT_VOLCENGINE_ARK_MAXIMUM_HTTP_DISPATCHES_PER_TLS_SESSION
        or value.get("credential_resolution_policy")
        != DEFAULT_VOLCENGINE_ARK_CREDENTIAL_RESOLUTION_POLICY
        or value.get("request_retry_count") != 0
        or value.get("connection_reuse_count") != 0
        or not 0 <= successes <= attempts
        or pre_dispatch_failures != attempts - successes
        or credential_reads != successes
        or not 0 <= credential_successes <= credential_reads
        or dispatches != credential_successes
        or not 0 <= unknown <= dispatches
        or not isinstance(pre_dispatch_codes, list)
        or len(pre_dispatch_codes) != pre_dispatch_failures
        or not isinstance(post_dispatch_codes, list)
        or len(post_dispatch_codes) != unknown
        or not isinstance(certificate_digests, list)
        or len(certificate_digests) != successes
        or any(
            not isinstance(code, str)
            or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,127}", code)
            for code in (*pre_dispatch_codes, *post_dispatch_codes)
        )
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark transport session audit is internally inconsistent",
        )
    try:
        tuple(Digest(str(item)) for item in certificate_digests)
    except ValueError as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "Ark transport certificate audit is invalid",
        ) from exc
    return dict(value)


# Compatibility name retained for callers outside the active ITER-010 path.
UrllibVolcengineArkChatTransport = DirectVerifiedVolcengineArkChatTransport


class VolcengineArkChatCompletionsNoToolsAdapter:
    provider_type = "VOLCENGINE_ARK"
    adapter_version = "openai-chat-completions-no-tools@10"

    def __init__(
        self,
        *,
        transport: ChatCompletionsTransport,
        configuration: VolcengineArkModelConfiguration,
        output_schemas: Mapping[str, OutputSchemaDefinition],
        pinned_models: frozenset[str] = frozenset(),
        observed_revisions_by_alias: Mapping[str, frozenset[str]] | None = None,
        live_qualification: ArkChatLiveQualification | None = None,
        enforce_output_schema: bool = True,
    ) -> None:
        if live_qualification is None:
            conformance_level = AdapterConformanceLevel.OFFLINE_FIXTURE
            conformance_result_ref = "CC-ARK-CHAT-NO-TOOLS-001:NOT-RUN"
            qualified_model_fingerprints: tuple[str, ...] = ()
        else:
            if (
                live_qualification.qualified_model_fingerprints
                != configuration.qualified_model_identities
                or live_qualification.valid_until.tzinfo is None
                or live_qualification.valid_until.utcoffset() is None
                or datetime.now(timezone.utc) >= live_qualification.valid_until
                or not live_qualification.result_ref.startswith(
                    "CC-ARK-CHAT-NO-TOOLS-001:sha256:"
                )
            ):
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "live adapter qualification is invalid, stale, or for another model",
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
                "requested model does not match the frozen Ark configuration",
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
            "tools": [],
            "tool_choice": "none",
            "parallel_tool_calls": False,
            "stream": True,
            "stream_options": {"include_usage": True},
            "n": 1,
            "max_tokens": request.max_output_tokens,
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
                "Ark Chat Completions request returned a non-success status",
                details,
            )
        payload = _streaming_chat_completion(response)
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
        provider_request_id = headers.get("x-request-id") or headers.get("x-tt-logid") or response_id
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


def _require_ark_https_endpoint(endpoint: str) -> None:
    parsed = urlsplit(endpoint)
    if (
        parsed.scheme != "https"
        or parsed.hostname != _VOLCENGINE_ARK_HOST
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path != "/api/coding/v3/chat/completions"
    ):
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "Ark endpoint must be the direct cn-beijing Coding Plan Chat Completions HTTPS endpoint",
        )


def _json_object_schema_instruction(
    definition: OutputSchemaDefinition,
) -> str:
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
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "output text is not JSON",
        ) from exc
    if not isinstance(decoded, dict):
        raise DomainError(
            ErrorCode.STRUCTURED_OUTPUT_INVALID,
            "structured output root is not an object",
        )


def _streaming_chat_completion(
    response: ProviderHTTPResponse,
) -> Mapping[str, object]:
    """Reconstruct one terminal completion from the qualified Ark SSE wire.

    The Gateway contract remains terminal and non-streaming.  SSE is confined
    to this Provider adapter so that long generations produce network traffic
    while no partial output crosses the adapter boundary.
    """

    headers = {key.lower(): value for key, value in response.headers.items()}
    content_type = headers.get("content-type")
    if (
        not isinstance(content_type, str)
        or content_type.split(";", 1)[0].strip().lower() != "text/event-stream"
    ):
        raise DomainError(
            ErrorCode.PROVIDER_RESPONSE_INVALID,
            "Ark streaming response content type is invalid",
        )

    chunks = _sse_json_chunks(response.body)
    response_id: str | None = None
    actual_model: str | None = None
    content_parts: list[str] = []
    finish_reason: str | None = None
    usage: object = None
    usage_received = False
    choice_received = False

    for chunk in chunks:
        if chunk.get("object") != "chat.completion.chunk":
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE event is not a chat completion chunk",
            )
        chunk_id = chunk.get("id")
        chunk_model = chunk.get("model")
        if not isinstance(chunk_id, str) or not chunk_id:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "provider response identity is missing",
            )
        if not isinstance(chunk_model, str) or not chunk_model:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "provider model identity is missing",
            )
        if response_id is None:
            response_id = chunk_id
            actual_model = chunk_model
        elif chunk_id != response_id or chunk_model != actual_model:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE response identity changed between chunks",
            )

        choices = chunk.get("choices")
        chunk_usage = chunk.get("usage")
        if not isinstance(choices, list):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE choices are invalid",
            )
        if not choices:
            if chunk_usage is None or finish_reason is None or usage_received:
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "Ark SSE usage chunk is invalid or out of order",
                )
            usage = chunk_usage
            usage_received = True
            continue
        if usage_received or finish_reason is not None:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE choice arrived after terminal output",
            )
        if len(choices) != 1 or not isinstance(choices[0], dict):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "provider must return exactly one streaming choice",
            )
        choice = choices[0]
        if choice.get("index") != 0:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "provider choice index is invalid",
            )
        delta = choice.get("delta")
        if not isinstance(delta, dict):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE assistant delta is missing",
            )
        role = delta.get("role")
        if role not in (None, "assistant"):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE assistant role is invalid",
            )
        for field in ("tool_calls", "function_call", "audio"):
            if delta.get(field) not in (None, []):
                raise DomainError(
                    ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
                    f"provider returned {field}",
                )
        refusal = delta.get("refusal")
        if isinstance(refusal, str) and refusal:
            raise DomainError(
                ErrorCode.PROVIDER_REFUSAL,
                "provider refused the request",
            )
        if refusal is not None and not isinstance(refusal, str):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE refusal field is invalid",
            )
        reasoning_content = delta.get("reasoning_content")
        if reasoning_content is not None and not isinstance(reasoning_content, str):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE reasoning field is invalid",
            )
        content = delta.get("content")
        if content is not None and not isinstance(content, str):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE assistant content is invalid",
            )
        if isinstance(content, str):
            content_parts.append(content)
        choice_received = True

        terminal = choice.get("finish_reason")
        if terminal is not None:
            if not isinstance(terminal, str) or not terminal:
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "provider finish reason is invalid",
                )
            finish_reason = terminal
            if chunk_usage is not None:
                usage = chunk_usage
                usage_received = True
        elif chunk_usage is not None:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE usage preceded terminal output",
            )

    if (
        not choice_received
        or finish_reason is None
        or response_id is None
        or actual_model is None
    ):
        raise DomainError(
            ErrorCode.PROVIDER_RESPONSE_INVALID,
            "Ark SSE response did not contain one terminal completion",
        )
    return {
        "id": response_id,
        "object": "chat.completion",
        "model": actual_model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "".join(content_parts),
                },
                "finish_reason": finish_reason,
            }
        ],
        "usage": usage,
    }


def _sse_json_chunks(body: bytes) -> tuple[Mapping[str, object], ...]:
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DomainError(
            ErrorCode.PROVIDER_RESPONSE_INVALID,
            "Ark SSE response is not UTF-8",
        ) from exc
    if not text or text.startswith("\ufeff") or "\r" in text.replace("\r\n", ""):
        raise DomainError(
            ErrorCode.PROVIDER_RESPONSE_INVALID,
            "Ark SSE framing is invalid",
        )
    records = text.replace("\r\n", "\n").split("\n\n")
    while records and records[-1] == "":
        records.pop()
    if not records:
        raise DomainError(
            ErrorCode.PROVIDER_RESPONSE_INVALID,
            "Ark SSE response is empty",
        )

    chunks: list[Mapping[str, object]] = []
    done = False
    for index, record in enumerate(records):
        lines = record.split("\n")
        if len(lines) != 1 or not lines[0].startswith("data:"):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE event framing is invalid",
            )
        data = lines[0][5:]
        if data.startswith(" "):
            data = data[1:]
        if data == "[DONE]":
            if done or index != len(records) - 1:
                raise DomainError(
                    ErrorCode.PROVIDER_RESPONSE_INVALID,
                    "Ark SSE terminal marker is invalid",
                )
            done = True
            continue
        if done or not data:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE event payload is invalid",
            )
        try:
            value = json.loads(data)
        except json.JSONDecodeError as exc:
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE event payload is not JSON",
            ) from exc
        if not isinstance(value, dict):
            raise DomainError(
                ErrorCode.PROVIDER_RESPONSE_INVALID,
                "Ark SSE event payload is not an object",
            )
        chunks.append(value)
    if not done or not chunks:
        raise DomainError(
            ErrorCode.PROVIDER_RESPONSE_INVALID,
            "Ark SSE response is missing its terminal marker",
        )
    return tuple(chunks)


def _provider_error_details(response: ProviderHTTPResponse) -> dict[str, str | int]:
    details: dict[str, str | int] = {}
    headers = {key.lower(): value for key, value in response.headers.items()}
    request_id = headers.get("x-request-id") or headers.get("x-tt-logid")
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
    for source, target in (
        ("code", "provider_error_code"),
        ("type", "provider_error_type"),
        ("param", "provider_error_parameter"),
    ):
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
        raise DomainError(
            ErrorCode.PROVIDER_RESPONSE_INVALID,
            "provider finish reason is missing",
        )
    message = choice.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "assistant message is missing")
    for field in ("tool_calls", "function_call", "audio"):
        if message.get(field) not in (None, []):
            raise DomainError(ErrorCode.PROVIDER_OUTPUT_FORBIDDEN, f"provider returned {field}")
    refusal = message.get("refusal")
    if isinstance(refusal, str) and refusal:
        raise DomainError(ErrorCode.PROVIDER_REFUSAL, "provider refused the request")
    content = message.get("content")
    if not isinstance(content, str) or not content:
        raise DomainError(ErrorCode.PROVIDER_RESPONSE_INVALID, "assistant content is empty")
    return content, finish_reason


def _normalize_structured_output_text(output_text: str) -> tuple[str, str]:
    """Unwrap one JSON Markdown fence around one JSON object.

    This is a deliberately narrow compatibility rule for providers that honor
    the requested schema but serialize the JSON object inside a Markdown code
    fence.  A short non-structural prefix is tolerated because some reasoning
    models introduce the fenced answer despite explicit JSON-only instructions.
    Trailing text, multiple fences, another language tag, structural prefix
    characters, or malformed JSON remains unchanged and is rejected by the
    closed-schema validator.
    """

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
    if isinstance(exc, http.client.RemoteDisconnected):
        return "REMOTE_DISCONNECTED"
    if isinstance(exc, socket.gaierror):
        return "DNS_RESOLUTION_FAILED"
    if isinstance(exc, ConnectionRefusedError):
        return "CONNECTION_REFUSED"
    if isinstance(exc, ssl.SSLCertVerificationError):
        return "TLS_CERTIFICATE_VERIFY_FAILED"
    if isinstance(exc, ssl.SSLError):
        return "TLS_FAILURE"
    return "NETWORK_FAILURE"
