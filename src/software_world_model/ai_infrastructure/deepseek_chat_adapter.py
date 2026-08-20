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
DEFAULT_DEEPSEEK_CONNECTION_POLICY = (
    "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@1"
)
DEFAULT_DEEPSEEK_CREDENTIAL_RESOLUTION_POLICY = (
    "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH"
)
DEFAULT_DEEPSEEK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES = 3
SUPPORTED_DEEPSEEK_MODELS = frozenset(
    {"deepseek-v4-pro", "deepseek-v4-flash"}
)
_DEEPSEEK_HOST = "api.deepseek.com"
_DEEPSEEK_PORT = 443
_DEEPSEEK_PATH = "/chat/completions"
_MAX_RESPONSE_BYTES = 16 * 1024 * 1024
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
                "connection_policy": DEFAULT_DEEPSEEK_CONNECTION_POLICY,
                "maximum_pre_dispatch_tls_handshakes": (
                    DEFAULT_DEEPSEEK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES
                ),
                "credential_resolution_policy": (
                    DEFAULT_DEEPSEEK_CREDENTIAL_RESOLUTION_POLICY
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
            "connection_policy": DEFAULT_DEEPSEEK_CONNECTION_POLICY,
            "maximum_pre_dispatch_tls_handshakes": (
                DEFAULT_DEEPSEEK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES
            ),
            "credential_resolution_policy": (
                DEFAULT_DEEPSEEK_CREDENTIAL_RESOLUTION_POLICY
            ),
            "request_retry_allowed": False,
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

    def session_audit(self) -> dict[str, object]:
        return deepseek_transport_session_audit(self._delegate)


class _VerifiedTLSSocket(Protocol):
    def settimeout(self, value: float) -> None: ...

    def getpeercert(self, *, binary_form: bool = False) -> object: ...

    def sendall(self, value: bytes) -> None: ...

    def close(self) -> None: ...


class PersistentDeepSeekChatTransport:
    """Direct exact-host HTTPS with one bounded persistent TLS session.

    Up to three credential-free TLS handshakes may be attempted across the
    transport lifetime.  The credential is resolved only after a verified
    connection exists.  Once HTTP dispatch begins, a network failure is never
    retried and is conservatively reported as outcome unknown.
    """

    def __init__(
        self,
        *,
        api_key_resolver: Callable[[], str],
        connection_factory: Callable[[float], _VerifiedTLSSocket] | None = None,
        tls_context: ssl.SSLContext | None = None,
        maximum_pre_dispatch_tls_handshakes: int = (
            DEFAULT_DEEPSEEK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES
        ),
    ) -> None:
        if (
            type(maximum_pre_dispatch_tls_handshakes) is not int
            or maximum_pre_dispatch_tls_handshakes
            != DEFAULT_DEEPSEEK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek transport requires exactly three pre-dispatch TLS attempts",
            )
        self._api_key_resolver = api_key_resolver
        self._tls_context = tls_context or build_verified_tls_context()
        self._connection_factory = connection_factory or self._new_tls_socket
        self._maximum_tls_handshakes = maximum_pre_dispatch_tls_handshakes
        self._tls_socket: _VerifiedTLSSocket | None = None
        self._tls_handshake_attempt_count = 0
        self._tls_handshake_success_count = 0
        self._connection_reuse_count = 0
        self._http_dispatch_count = 0
        self._pre_dispatch_tls_failure_codes: list[str] = []
        self._peer_certificate_sha256s: list[str] = []
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
    def connection_reuse_count(self) -> int:
        return self._connection_reuse_count

    @property
    def http_dispatch_count(self) -> int:
        return self._http_dispatch_count

    @property
    def pre_dispatch_tls_failure_codes(self) -> tuple[str, ...]:
        return tuple(self._pre_dispatch_tls_failure_codes)

    @property
    def peer_certificate_sha256(self) -> str | None:
        return (
            self._peer_certificate_sha256s[-1]
            if self._peer_certificate_sha256s
            else None
        )

    @property
    def peer_certificate_sha256s(self) -> tuple[str, ...]:
        return tuple(self._peer_certificate_sha256s)

    @property
    def post_dispatch_failure_codes(self) -> tuple[str, ...]:
        return tuple(self._post_dispatch_failure_codes)

    @property
    def credential_resolution_count(self) -> int:
        return self._credential_resolution_count

    @property
    def credential_resolution_success_count(self) -> int:
        return self._credential_resolution_success_count

    def session_audit(self) -> dict[str, object]:
        return {
            "schema": "SWM-DEEPSEEK-TRANSPORT-SESSION-AUDIT@1",
            "connection_policy": DEFAULT_DEEPSEEK_CONNECTION_POLICY,
            "maximum_pre_dispatch_tls_handshake_attempts": (
                self._maximum_tls_handshakes
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
            "connection_reuse_count": self._connection_reuse_count,
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
                DEFAULT_DEEPSEEK_CREDENTIAL_RESOLUTION_POLICY
            ),
        }

    def close(self) -> None:
        tls_socket = self._tls_socket
        self._tls_socket = None
        if tls_socket is not None:
            tls_socket.close()

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse:
        _require_deepseek_https_endpoint(endpoint)
        if not isinstance(body, bytes) or not body:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek request body is empty",
            )
        if (
            not isinstance(client_request_id, str)
            or not client_request_id
            or "\r" in client_request_id
            or "\n" in client_request_id
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek client request ID is invalid",
            )
        if type(timeout_milliseconds) is not int or timeout_milliseconds < 1:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek timeout must be positive",
            )
        reused = self._tls_socket is not None
        tls_socket = self._ensure_tls_socket(timeout_milliseconds / 1000)
        self._credential_resolution_count += 1
        try:
            api_key = self._api_key_resolver()
        except Exception:
            self.close()
            raise
        if (
            not isinstance(api_key, str)
            or not api_key
            or "\r" in api_key
            or "\n" in api_key
        ):
            self.close()
            raise DomainError(
                ErrorCode.LIVE_INTEGRATION_HELD,
                "DeepSeek credential is not configured",
            )
        try:
            api_key.encode("ascii")
            client_request_id.encode("ascii")
        except UnicodeEncodeError as exc:
            self.close()
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "DeepSeek credential or client request ID is not ASCII",
            ) from exc
        self._credential_resolution_success_count += 1
        if reused:
            self._connection_reuse_count += 1
        self._http_dispatch_count += 1
        try:
            request_headers = (
                f"POST {_DEEPSEEK_PATH} HTTP/1.1\r\n".encode("ascii")
                + f"Host: {_DEEPSEEK_HOST}\r\n".encode("ascii")
                + b"Authorization: Bearer "
                + api_key.encode("ascii")
                + b"\r\nContent-Type: application/json\r\n"
                + b"X-Client-Request-Id: "
                + client_request_id.encode("ascii")
                + b"\r\n"
                + f"Content-Length: {len(body)}\r\n".encode("ascii")
                + b"Connection: keep-alive\r\n\r\n"
            )
            tls_socket.sendall(request_headers + body)
            response = http.client.HTTPResponse(tls_socket)
            response.begin()
            response_body = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(response_body) > _MAX_RESPONSE_BYTES:
                self.close()
                raise DomainError(
                    ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
                    "DeepSeek response exceeds the closed size limit",
                )
            headers = {key.lower(): value for key, value in response.getheaders()}
            result = ProviderHTTPResponse(
                status_code=response.status,
                headers=headers,
                body=response_body,
            )
            if (
                response.will_close
                or headers.get("connection", "").lower() == "close"
            ):
                self.close()
            return result
        except (
            OSError,
            TimeoutError,
            socket.timeout,
            ssl.SSLError,
            http.client.HTTPException,
            http.client.RemoteDisconnected,
        ) as exc:
            self._post_dispatch_failure_codes.append(
                _network_failure_reason(exc)
            )
            self.close()
            raise ProviderOutcomeUnknown(
                "DeepSeek Chat Completions outcome is unknown",
                reason_code=_network_failure_reason(exc),
            ) from exc

    def _new_tls_socket(self, timeout_seconds: float) -> _VerifiedTLSSocket:
        raw_socket = socket.create_connection(
            (_DEEPSEEK_HOST, _DEEPSEEK_PORT),
            timeout=timeout_seconds,
        )
        try:
            return self._tls_context.wrap_socket(
                raw_socket,
                server_hostname=_DEEPSEEK_HOST,
            )
        except Exception:
            raw_socket.close()
            raise

    def _ensure_tls_socket(self, timeout_seconds: float) -> _VerifiedTLSSocket:
        if self._tls_socket is not None:
            self._tls_socket.settimeout(timeout_seconds)
            return self._tls_socket
        last_code = "TLS_PRE_DISPATCH_UNAVAILABLE"
        while self._tls_handshake_attempt_count < self._maximum_tls_handshakes:
            self._tls_handshake_attempt_count += 1
            tls_socket: _VerifiedTLSSocket | None = None
            try:
                tls_socket = self._connection_factory(timeout_seconds)
                certificate = tls_socket.getpeercert(binary_form=True)
                if not isinstance(certificate, bytes) or not certificate:
                    raise ssl.SSLError(
                        "DeepSeek peer did not provide a certificate"
                    )
            except (
                OSError,
                TimeoutError,
                socket.timeout,
                ssl.SSLError,
                http.client.HTTPException,
            ) as exc:
                if tls_socket is not None:
                    tls_socket.close()
                last_code = _network_failure_reason(exc)
                self._pre_dispatch_tls_failure_codes.append(last_code)
                continue
            self._tls_handshake_success_count += 1
            self._peer_certificate_sha256s.append(
                "sha256:" + sha256(certificate).hexdigest()
            )
            self._tls_socket = tls_socket
            return tls_socket
        raise DomainError(
            ErrorCode.LIVE_INTEGRATION_HELD,
            "DeepSeek credential-free TLS acquisition exhausted",
            {
                "tls_handshake_attempt_count": self._tls_handshake_attempt_count,
                "last_failure_code": last_code,
            },
        )


def deepseek_transport_session_audit(
    transport: object,
) -> dict[str, object]:
    method = getattr(transport, "session_audit", None)
    if not callable(method):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek transport does not expose the required session audit",
        )
    return verify_deepseek_transport_session_audit(method())


def verify_deepseek_transport_session_audit(
    value: object,
) -> dict[str, object]:
    required = {
        "schema",
        "connection_policy",
        "maximum_pre_dispatch_tls_handshake_attempts",
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
            "DeepSeek transport session audit shape is invalid",
        )
    integers = (
        "maximum_pre_dispatch_tls_handshake_attempts",
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
    if any(type(value.get(field)) is not int for field in integers):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek transport session audit counters are invalid",
        )
    attempts = int(value["tls_handshake_attempt_count"])
    successes = int(value["tls_handshake_success_count"])
    pre_dispatch_failures = int(
        value["pre_dispatch_tls_handshake_failure_count"]
    )
    dispatches = int(value["http_dispatch_count"])
    reuse = int(value["connection_reuse_count"])
    unknown = int(value["post_dispatch_outcome_unknown_count"])
    credential_reads = int(value["credential_resolution_count"])
    credential_successes = int(value["credential_resolution_success_count"])
    pre_dispatch_codes = value["pre_dispatch_tls_failure_codes"]
    post_dispatch_codes = value["post_dispatch_failure_codes"]
    certificate_digests = value["verified_peer_certificate_sha256s"]
    if (
        value.get("schema") != "SWM-DEEPSEEK-TRANSPORT-SESSION-AUDIT@1"
        or value.get("connection_policy") != DEFAULT_DEEPSEEK_CONNECTION_POLICY
        or value.get("maximum_pre_dispatch_tls_handshake_attempts")
        != DEFAULT_DEEPSEEK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES
        or value.get("credential_resolution_policy")
        != DEFAULT_DEEPSEEK_CREDENTIAL_RESOLUTION_POLICY
        or value.get("request_retry_count") != 0
        or not 0 <= successes <= attempts <= 3
        or pre_dispatch_failures != attempts - successes
        or not 0 <= reuse <= max(0, dispatches - 1)
        or not 0 <= unknown <= dispatches
        or credential_successes != dispatches
        or successes > credential_reads
        or dispatches - reuse > successes
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
            "DeepSeek transport session audit is internally inconsistent",
        )
    try:
        tuple(Digest(str(item)) for item in certificate_digests)
    except ValueError as exc:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "DeepSeek transport certificate audit is invalid",
        ) from exc
    return dict(value)


# Compatibility name retained for callers outside the active ITER-008 path.
UrllibDeepSeekChatTransport = PersistentDeepSeekChatTransport


class DeepSeekChatCompletionsNoToolsAdapter:
    provider_type = "DEEPSEEK"
    adapter_version = "deepseek-chat-completions-no-tools@3"

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
    reason = exc
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
    "DEFAULT_DEEPSEEK_CONNECTION_POLICY",
    "DEFAULT_DEEPSEEK_CREDENTIAL_RESOLUTION_POLICY",
    "DEFAULT_DEEPSEEK_MAXIMUM_PRE_DISPATCH_TLS_HANDSHAKES",
    "DEFAULT_DEEPSEEK_MODEL",
    "DEFAULT_DEEPSEEK_OPENAI_BASE_URL",
    "DEFAULT_DEEPSEEK_TEMPERATURE",
    "SUPPORTED_DEEPSEEK_MODELS",
    "DeepSeekChatCompletionsNoToolsAdapter",
    "DeepSeekChatCompletionsTransport",
    "DeepSeekModelConfiguration",
    "PersistentDeepSeekChatTransport",
    "RecordedDeepSeekChatCompletionsRequest",
    "RecordingDeepSeekChatCompletionsTransport",
    "UrllibDeepSeekChatTransport",
    "deepseek_transport_session_audit",
    "verify_deepseek_transport_session_audit",
]
