"""Pinned-address DeepSeek HTTPS transport for the isolated Model Gateway.

DNS resolution and TCP connection belong to the credential-free runtime
supervisor.  This dispatch transport receives three exact connected descriptors,
revalidates their numeric peer, verifies TLS for ``api.deepseek.com``, and only
then resolves ``DEEPSEEK_API_KEY``.  A verified TLS session is reused within the
authorized run; it never retries a Provider request after HTTP dispatch begins.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import http.client
import ipaddress
import os
import socket
import ssl
from typing import Callable, Mapping
from urllib.parse import urlsplit

from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    digest_of,
)

from .deepseek_chat_adapter import DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT
from .model_gateway import ProviderOutcomeUnknown
from .openai_responses_adapter import ProviderHTTPResponse


DEEPSEEK_PROVIDER_HOST = "api.deepseek.com"
DEEPSEEK_PROVIDER_PORT = 443
DEEPSEEK_PROVIDER_PATH = "/chat/completions"
_MAX_RESPONSE_BYTES = 16 * 1024 * 1024
_PROVISIONED_CONNECTED_DESCRIPTOR_COUNT = 3
_SYSTEM_CA_FILE_CANDIDATES = (
    "/private/etc/ssl/cert.pem",
    "/etc/ssl/cert.pem",
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
)
_EXECUTOR_SYNTHETIC_EXTERNAL_NETWORK = ipaddress.ip_network("198.18.0.0/15")


@dataclass(frozen=True, slots=True)
class PinnedDeepSeekTLSHandshakeAudit:
    ordinal: int
    numeric_address: str
    address_scope: str
    address_family: str
    outcome: str
    peer_certificate_sha256: str | None
    failure_code: str | None

    def canonical_value(self) -> dict[str, object]:
        return {
            "schema": "SWM-PINNED-DEEPSEEK-TLS-HANDSHAKE-AUDIT@1",
            "ordinal": self.ordinal,
            "numeric_address": self.numeric_address,
            "address_scope": self.address_scope,
            "address_family": self.address_family,
            "outcome": self.outcome,
            "peer_certificate_sha256": self.peer_certificate_sha256,
            "failure_code": self.failure_code,
        }


@dataclass(frozen=True, slots=True)
class PinnedDeepSeekDispatchAudit:
    ordinal: int
    endpoint: str
    numeric_address: str
    address_scope: str
    address_family: str
    client_request_id_digest: Digest
    request_body_digest: Digest
    status_code: int | None
    response_body_digest: Digest | None
    peer_certificate_sha256: str | None
    tls_connection_ordinal: int
    connection_reused: bool
    outcome: str
    failure_code: str | None

    def canonical_value(self) -> dict[str, object]:
        return {
            "schema": "SWM-PINNED-DEEPSEEK-DISPATCH-AUDIT@2",
            "ordinal": self.ordinal,
            "endpoint": self.endpoint,
            "numeric_address": self.numeric_address,
            "address_scope": self.address_scope,
            "address_family": self.address_family,
            "client_request_id_digest": self.client_request_id_digest.value,
            "request_body_digest": self.request_body_digest.value,
            "status_code": self.status_code,
            "response_body_digest": (
                self.response_body_digest.value
                if self.response_body_digest is not None
                else None
            ),
            "peer_certificate_sha256": self.peer_certificate_sha256,
            "tls_connection_ordinal": self.tls_connection_ordinal,
            "connection_reused": self.connection_reused,
            "outcome": self.outcome,
            "failure_code": self.failure_code,
        }


class PinnedIPDeepSeekChatTransport:
    """Exact DeepSeek transport with a persistent inherited TLS session."""

    def __init__(
        self,
        *,
        numeric_address: str,
        api_key_resolver: Callable[[], str],
        connected_socket_fds: tuple[int, ...],
        tls_context: ssl.SSLContext | None = None,
        audit_writer: Callable[[Mapping[str, object]], None] | None = None,
        maximum_calls: int = 6,
    ) -> None:
        self._address = _numeric_address(numeric_address)
        self._api_key_resolver = api_key_resolver
        if (
            not isinstance(connected_socket_fds, tuple)
            or any(
                type(item) is not int or item < 0
                for item in connected_socket_fds
            )
            or len(set(connected_socket_fds)) != len(connected_socket_fds)
            or type(maximum_calls) is not int
            or maximum_calls != 6
            or len(connected_socket_fds)
            != _PROVISIONED_CONNECTED_DESCRIPTOR_COUNT
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "pinned DeepSeek transport requires three unique connected descriptors",
            )
        self._connected_socket_fds = list(connected_socket_fds)
        self._tls_context = tls_context or _verified_tls_context()
        self._audit_writer = audit_writer or (lambda _: None)
        self._maximum_calls = maximum_calls
        self._audits: list[PinnedDeepSeekDispatchAudit] = []
        self._tls_handshake_audits: list[PinnedDeepSeekTLSHandshakeAudit] = []
        self._active_tls_socket: ssl.SSLSocket | None = None
        self._active_certificate_digest: str | None = None
        self._active_connection_ordinal: int | None = None
        self._credential_resolution_count = 0
        self._credential_resolution_success_count = 0

    @property
    def provider_call_count(self) -> int:
        return len(self._audits)

    @property
    def network_operation_count(self) -> int:
        return len(self._audits)

    @property
    def audits(self) -> tuple[PinnedDeepSeekDispatchAudit, ...]:
        return tuple(self._audits)

    @property
    def tls_handshake_audits(self) -> tuple[PinnedDeepSeekTLSHandshakeAudit, ...]:
        return tuple(self._tls_handshake_audits)

    @property
    def tls_handshake_attempt_count(self) -> int:
        return len(self._tls_handshake_audits)

    @property
    def tls_handshake_success_count(self) -> int:
        return sum(
            item.outcome == "VERIFIED" for item in self._tls_handshake_audits
        )

    @property
    def connection_reuse_count(self) -> int:
        return sum(item.connection_reused for item in self._audits)

    @property
    def descriptor_consumed_count(self) -> int:
        return len(self._tls_handshake_audits)

    @property
    def descriptor_unused_count(self) -> int:
        return len(self._connected_socket_fds)

    @property
    def credential_resolution_count(self) -> int:
        return self._credential_resolution_count

    @property
    def credential_resolution_success_count(self) -> int:
        return self._credential_resolution_success_count

    def close_unused_connected_sockets(self) -> int:
        return self.close_session_and_unused_connected_sockets()

    def close_session_and_unused_connected_sockets(self) -> int:
        if self._active_tls_socket is not None:
            self._active_tls_socket.close()
            self._active_tls_socket = None
            self._active_certificate_digest = None
            self._active_connection_ordinal = None
            self._audit_writer(
                {
                    "schema": "SWM-PINNED-DEEPSEEK-TLS-SESSION-AUDIT@1",
                    "outcome": "ACTIVE_TLS_CLOSED",
                    "failure_code": None,
                }
            )
        closed = 0
        family = socket.AF_INET6 if self._address.version == 6 else socket.AF_INET
        while self._connected_socket_fds:
            descriptor = self._connected_socket_fds.pop(0)
            try:
                socket.socket(family, socket.SOCK_STREAM, fileno=descriptor).close()
            except OSError as exc:
                raise DomainError(
                    ErrorCode.CONTROL_STATE_DENIED,
                    "unused inherited DeepSeek descriptor could not be closed",
                ) from exc
            closed += 1
            self._audit_writer(
                {
                    "schema": "SWM-PINNED-DEEPSEEK-DESCRIPTOR-AUDIT@1",
                    "ordinal": self.descriptor_consumed_count + closed,
                    "numeric_address": str(self._address),
                    "outcome": "UNUSED_CLOSED",
                    "failure_code": None,
                }
            )
        return closed

    def post_json(
        self,
        *,
        endpoint: str,
        body: bytes,
        client_request_id: str,
        timeout_milliseconds: int,
    ) -> ProviderHTTPResponse:
        _require_exact_endpoint(endpoint)
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
        if len(self._audits) >= self._maximum_calls:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "pinned DeepSeek Provider call fuse exceeded six calls",
            )

        ordinal = len(self._audits) + 1
        body_digest = _bytes_digest(body)
        status_code: int | None = None
        response_digest: Digest | None = None
        reused_connection = self._active_tls_socket is not None
        tls_socket = self._ensure_tls_socket(
            timeout_milliseconds=timeout_milliseconds
        )
        certificate_digest = self._active_certificate_digest
        connection_ordinal = self._required_active_connection_ordinal()
        close_after_response = False
        self._credential_resolution_count += 1
        try:
            api_key = self._api_key_resolver()
            if (
                not isinstance(api_key, str)
                or not api_key
                or "\r" in api_key
                or "\n" in api_key
            ):
                raise DomainError(
                    ErrorCode.LIVE_INTEGRATION_HELD,
                    "DeepSeek credential reference is not configured",
                )
            try:
                authorization = f"Bearer {api_key}".encode("ascii")
                request_id = client_request_id.encode("ascii")
            except UnicodeEncodeError as exc:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "DeepSeek credential or client request ID is not ASCII",
                ) from exc
        except Exception:
            self._close_active_tls_socket()
            raise
        self._credential_resolution_success_count += 1
        try:
            headers = (
                f"POST {DEEPSEEK_PROVIDER_PATH} HTTP/1.1\r\n".encode("ascii")
                + f"Host: {DEEPSEEK_PROVIDER_HOST}\r\n".encode("ascii")
                + b"Authorization: "
                + authorization
                + b"\r\nContent-Type: application/json\r\n"
                + b"X-Client-Request-Id: "
                + request_id
                + b"\r\n"
                + f"Content-Length: {len(body)}\r\n".encode("ascii")
                + b"Connection: keep-alive\r\n\r\n"
            )
            tls_socket.sendall(headers + body)
            response = http.client.HTTPResponse(tls_socket)
            response.begin()
            response_body = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(response_body) > _MAX_RESPONSE_BYTES:
                raise DomainError(
                    ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
                    "DeepSeek response exceeds the closed size limit",
                )
            status_code = response.status
            response_digest = _bytes_digest(response_body)
            response_headers = {
                key.lower(): value for key, value in response.getheaders()
            }
            result = ProviderHTTPResponse(
                status_code=status_code,
                headers=response_headers,
                body=response_body,
            )
            if (
                response.will_close
                or response_headers.get("connection", "").lower() == "close"
            ):
                close_after_response = True
        except DomainError as exc:
            self._record_audit(
                ordinal,
                body_digest,
                client_request_id,
                status_code,
                response_digest,
                certificate_digest,
                connection_ordinal,
                reused_connection,
                "REJECTED",
                exc.code.value,
            )
            self._close_active_tls_socket()
            raise
        except (OSError, TimeoutError, ssl.SSLError, http.client.HTTPException) as exc:
            failure_code = _network_failure_code(exc)
            self._record_audit(
                ordinal,
                body_digest,
                client_request_id,
                status_code,
                response_digest,
                certificate_digest,
                connection_ordinal,
                reused_connection,
                "OUTCOME_UNKNOWN",
                failure_code,
            )
            self._close_active_tls_socket()
            raise ProviderOutcomeUnknown(
                "DeepSeek Chat Completions outcome is unknown",
                reason_code=failure_code,
            ) from exc
        self._record_audit(
            ordinal,
            body_digest,
            client_request_id,
            status_code,
            response_digest,
            certificate_digest,
            connection_ordinal,
            reused_connection,
            "HTTP_RESPONSE",
            None,
        )
        if close_after_response:
            self._close_active_tls_socket()
        return result

    def _ensure_tls_socket(self, *, timeout_milliseconds: int) -> ssl.SSLSocket:
        if self._active_tls_socket is not None:
            self._active_tls_socket.settimeout(timeout_milliseconds / 1000)
            return self._active_tls_socket
        family = socket.AF_INET6 if self._address.version == 6 else socket.AF_INET
        while self._connected_socket_fds:
            descriptor = self._connected_socket_fds.pop(0)
            ordinal = len(self._tls_handshake_audits) + 1
            raw_socket: socket.socket | None = None
            tls_socket: ssl.SSLSocket | None = None
            try:
                raw_socket = socket.socket(
                    family,
                    socket.SOCK_STREAM,
                    fileno=descriptor,
                )
                raw_socket.settimeout(timeout_milliseconds / 1000)
                peer = raw_socket.getpeername()
                if (
                    peer[1] != DEEPSEEK_PROVIDER_PORT
                    or _numeric_address(str(peer[0])) != self._address
                ):
                    raise DomainError(
                        ErrorCode.QUALIFICATION_INVALID,
                        "DeepSeek socket peer is not the exact inherited pin",
                    )
                tls_socket = self._tls_context.wrap_socket(
                    raw_socket,
                    server_hostname=DEEPSEEK_PROVIDER_HOST,
                )
                raw_socket = None
                certificate = tls_socket.getpeercert(binary_form=True)
                if not certificate:
                    raise ssl.SSLError(
                        "DeepSeek peer did not provide a certificate"
                    )
                certificate_digest = (
                    "sha256:" + sha256(certificate).hexdigest()
                )
            except DomainError as exc:
                self._record_tls_handshake(
                    ordinal=ordinal,
                    outcome="REJECTED",
                    certificate_digest=None,
                    failure_code=exc.code.value,
                )
                if tls_socket is not None:
                    tls_socket.close()
                if raw_socket is not None:
                    raw_socket.close()
                raise
            except (
                OSError,
                TimeoutError,
                ssl.SSLError,
                http.client.HTTPException,
            ) as exc:
                self._record_tls_handshake(
                    ordinal=ordinal,
                    outcome="FAILED_BEFORE_CREDENTIAL",
                    certificate_digest=None,
                    failure_code=_network_failure_code(exc),
                )
                if tls_socket is not None:
                    tls_socket.close()
                if raw_socket is not None:
                    raw_socket.close()
                continue
            self._record_tls_handshake(
                ordinal=ordinal,
                outcome="VERIFIED",
                certificate_digest=certificate_digest,
                failure_code=None,
            )
            self._active_tls_socket = tls_socket
            self._active_certificate_digest = certificate_digest
            self._active_connection_ordinal = ordinal
            return tls_socket
        raise DomainError(
            ErrorCode.LIVE_INTEGRATION_HELD,
            "DeepSeek credential-free TLS acquisition exhausted",
            {
                "tls_handshake_attempt_count": self.tls_handshake_attempt_count,
                "provider_request_count": self.provider_call_count,
            },
        )

    def _record_tls_handshake(
        self,
        *,
        ordinal: int,
        outcome: str,
        certificate_digest: str | None,
        failure_code: str | None,
    ) -> None:
        audit = PinnedDeepSeekTLSHandshakeAudit(
            ordinal=ordinal,
            numeric_address=str(self._address),
            address_scope=_numeric_address_scope(self._address),
            address_family=(
                "AF_INET6" if self._address.version == 6 else "AF_INET"
            ),
            outcome=outcome,
            peer_certificate_sha256=certificate_digest,
            failure_code=failure_code,
        )
        self._tls_handshake_audits.append(audit)
        self._audit_writer(audit.canonical_value())

    def _close_active_tls_socket(self) -> None:
        if self._active_tls_socket is not None:
            self._active_tls_socket.close()
        self._active_tls_socket = None
        self._active_certificate_digest = None
        self._active_connection_ordinal = None

    def _required_active_connection_ordinal(self) -> int:
        if self._active_connection_ordinal is None:
            return max(1, self.tls_handshake_attempt_count)
        return self._active_connection_ordinal

    def _record_audit(
        self,
        ordinal: int,
        body_digest: Digest,
        client_request_id: str,
        status_code: int | None,
        response_digest: Digest | None,
        certificate_digest: str | None,
        tls_connection_ordinal: int,
        connection_reused: bool,
        outcome: str,
        failure_code: str | None,
    ) -> None:
        audit = PinnedDeepSeekDispatchAudit(
            ordinal=ordinal,
            endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
            numeric_address=str(self._address),
            address_scope=_numeric_address_scope(self._address),
            address_family=(
                "AF_INET6" if self._address.version == 6 else "AF_INET"
            ),
            client_request_id_digest=digest_of(client_request_id),
            request_body_digest=body_digest,
            status_code=status_code,
            response_body_digest=response_digest,
            peer_certificate_sha256=certificate_digest,
            tls_connection_ordinal=tls_connection_ordinal,
            connection_reused=connection_reused,
            outcome=outcome,
            failure_code=failure_code,
        )
        self._audits.append(audit)
        self._audit_writer(audit.canonical_value())


def _require_exact_endpoint(endpoint: object) -> None:
    parsed = urlsplit(str(endpoint))
    if (
        endpoint != DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT
        or parsed.scheme != "https"
        or parsed.hostname != DEEPSEEK_PROVIDER_HOST
        or parsed.port not in {None, DEEPSEEK_PROVIDER_PORT}
        or parsed.path != DEEPSEEK_PROVIDER_PATH
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "pinned DeepSeek transport endpoint is not exact",
        )


def _numeric_address(value: object) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    if not isinstance(value, str) or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "provider address is invalid")
    try:
        address = ipaddress.ip_address(value)
        _numeric_address_scope(address)
    except ValueError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "provider address must be public or an executor synthetic external peer",
        ) from exc
    return address


def _numeric_address_scope(
    address: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> str:
    if address.is_global:
        return "PUBLIC_UNICAST"
    if address in _EXECUTOR_SYNTHETIC_EXTERNAL_NETWORK:
        return "EXECUTOR_SYNTHETIC_EXTERNAL"
    raise ValueError("numeric address is not an accepted external peer")


def _verified_tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    defaults = ssl.get_default_verify_paths()
    if defaults.cafile is None and defaults.capath is None:
        for candidate in _SYSTEM_CA_FILE_CANDIDATES:
            if os.path.isfile(candidate):
                context.load_verify_locations(cafile=candidate)
                break
    if context.verify_mode != ssl.CERT_REQUIRED or not context.check_hostname:
        raise DomainError(
            ErrorCode.LIVE_INTEGRATION_HELD,
            "verified TLS context is unavailable",
        )
    return context


def _network_failure_code(exc: BaseException) -> str:
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return "NETWORK_TIMEOUT"
    if isinstance(exc, ssl.SSLCertVerificationError):
        return "TLS_CERTIFICATE_REJECTED"
    if isinstance(exc, ssl.SSLError):
        return "TLS_FAILURE"
    if isinstance(exc, ConnectionRefusedError):
        return "CONNECTION_REFUSED"
    return "NETWORK_OUTCOME_UNKNOWN"


def _bytes_digest(value: bytes) -> Digest:
    return Digest("sha256:" + sha256(value).hexdigest())


__all__ = [
    "DEEPSEEK_PROVIDER_HOST",
    "DEEPSEEK_PROVIDER_PATH",
    "DEEPSEEK_PROVIDER_PORT",
    "PinnedDeepSeekDispatchAudit",
    "PinnedDeepSeekTLSHandshakeAudit",
    "PinnedIPDeepSeekChatTransport",
]
