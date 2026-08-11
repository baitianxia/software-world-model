"""Pinned-address Ark HTTPS transport for the isolated Model Egress Gateway.

DNS resolution and TCP connection are performed by a credential- and
payload-free evaluator supervisor.  The dispatch process inherits exactly one
connected socket, revalidates its numeric peer on port 443, and still verifies
the TLS certificate against the qualified Ark hostname.  The credential is
resolved only after every public endpoint, peer, and TLS check has passed.
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

from .model_gateway import ProviderOutcomeUnknown
from .openai_responses_adapter import ProviderHTTPResponse
from .volcengine_ark_chat_adapter import (
    DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
)


ARK_PROVIDER_HOST = "ark.cn-beijing.volces.com"
ARK_PROVIDER_PORT = 443
ARK_PROVIDER_PATH = "/api/coding/v3/chat/completions"
_MAX_RESPONSE_BYTES = 16 * 1024 * 1024
_MAX_PROVIDER_CALLS = 5
_SYSTEM_CA_FILE_CANDIDATES = (
    "/private/etc/ssl/cert.pem",
    "/etc/ssl/cert.pem",
    "/etc/ssl/certs/ca-certificates.crt",
    "/etc/pki/tls/certs/ca-bundle.crt",
)
_EXECUTOR_SYNTHETIC_EXTERNAL_NETWORK = ipaddress.ip_network("198.18.0.0/15")


@dataclass(frozen=True, slots=True)
class PinnedArkDispatchAudit:
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
    outcome: str
    failure_code: str | None

    def canonical_value(self) -> dict[str, object]:
        return {
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
            "outcome": self.outcome,
            "failure_code": self.failure_code,
        }


class PinnedIPVolcengineArkChatTransport:
    """Bearer-authenticated exact Ark transport with no runtime DNS call."""

    def __init__(
        self,
        *,
        numeric_address: str,
        api_key_resolver: Callable[[], str],
        connected_socket_fd: int | None = None,
        tls_context: ssl.SSLContext | None = None,
        audit_writer: Callable[[Mapping[str, object]], None] | None = None,
        maximum_calls: int = _MAX_PROVIDER_CALLS,
    ) -> None:
        self._address = _numeric_address(numeric_address)
        self._api_key_resolver = api_key_resolver
        if connected_socket_fd is not None and (
            type(connected_socket_fd) is not int or connected_socket_fd < 0
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "connected Provider socket descriptor is invalid",
            )
        self._connected_socket_fd = connected_socket_fd
        self._tls_context = tls_context or _verified_tls_context()
        self._audit_writer = audit_writer or (lambda _: None)
        if type(maximum_calls) is not int or maximum_calls != _MAX_PROVIDER_CALLS:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "pinned Ark transport call cap must be exactly five",
            )
        self._maximum_calls = maximum_calls
        self._audits: list[PinnedArkDispatchAudit] = []

    @property
    def provider_call_count(self) -> int:
        return len(self._audits)

    @property
    def network_operation_count(self) -> int:
        return len(self._audits)

    @property
    def audits(self) -> tuple[PinnedArkDispatchAudit, ...]:
        return tuple(self._audits)

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
            raise DomainError(ErrorCode.INVALID_ARGUMENT, "Ark request body is empty")
        if (
            not isinstance(client_request_id, str)
            or not client_request_id
            or "\r" in client_request_id
            or "\n" in client_request_id
        ):
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "Ark client request ID is invalid"
            )
        if type(timeout_milliseconds) is not int or timeout_milliseconds < 1:
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT, "Ark timeout must be positive"
            )
        if len(self._audits) >= self._maximum_calls:
            raise DomainError(
                ErrorCode.CONTROL_STATE_DENIED,
                "pinned Ark Provider call fuse exceeded five calls",
            )

        ordinal = len(self._audits) + 1
        body_digest = _bytes_digest(body)
        status_code: int | None = None
        response_digest: Digest | None = None
        certificate_digest: str | None = None
        failure_code: str | None = None
        raw_socket: socket.socket | None = None
        tls_socket: ssl.SSLSocket | None = None
        try:
            family = (
                socket.AF_INET6
                if self._address.version == 6
                else socket.AF_INET
            )
            inherited_connection = self._connected_socket_fd is not None
            if not inherited_connection:
                raw_socket = socket.socket(family, socket.SOCK_STREAM)
            else:
                raw_socket = socket.socket(
                    family,
                    socket.SOCK_STREAM,
                    fileno=self._connected_socket_fd,
                )
                self._connected_socket_fd = None
            raw_socket.settimeout(timeout_milliseconds / 1000)
            if not inherited_connection:
                target = (
                    (str(self._address), ARK_PROVIDER_PORT, 0, 0)
                    if family == socket.AF_INET6
                    else (str(self._address), ARK_PROVIDER_PORT)
                )
                raw_socket.connect(target)
            peer = raw_socket.getpeername()
            if peer[1] != ARK_PROVIDER_PORT:
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "Provider socket peer port is not exact",
                )
            if _numeric_address(str(peer[0])) != self._address:
                raise DomainError(
                    ErrorCode.QUALIFICATION_INVALID,
                    "Provider socket peer address is not exact",
                )
            tls_socket = self._tls_context.wrap_socket(
                raw_socket,
                server_hostname=ARK_PROVIDER_HOST,
            )
            raw_socket = None
            certificate = tls_socket.getpeercert(binary_form=True)
            if not certificate:
                raise ssl.SSLError("Ark peer did not provide a certificate")
            certificate_digest = "sha256:" + sha256(certificate).hexdigest()
            api_key = self._api_key_resolver()
            if (
                not isinstance(api_key, str)
                or not api_key
                or "\r" in api_key
                or "\n" in api_key
            ):
                raise DomainError(
                    ErrorCode.LIVE_INTEGRATION_HELD,
                    "Ark credential reference is not configured",
                )
            try:
                authorization = f"Bearer {api_key}".encode("ascii")
                request_id = client_request_id.encode("ascii")
            except UnicodeEncodeError as exc:
                raise DomainError(
                    ErrorCode.INVALID_ARGUMENT,
                    "Ark credential or client request ID is not ASCII",
                ) from exc
            headers = (
                f"POST {ARK_PROVIDER_PATH} HTTP/1.1\r\n".encode("ascii")
                + f"Host: {ARK_PROVIDER_HOST}\r\n".encode("ascii")
                + b"Authorization: "
                + authorization
                + b"\r\n"
                + b"Content-Type: application/json\r\n"
                + b"X-Client-Request-Id: "
                + request_id
                + b"\r\n"
                + f"Content-Length: {len(body)}\r\n".encode("ascii")
                + b"Connection: close\r\n\r\n"
            )
            tls_socket.sendall(headers + body)
            response = http.client.HTTPResponse(tls_socket)
            response.begin()
            response_body = response.read(_MAX_RESPONSE_BYTES + 1)
            if len(response_body) > _MAX_RESPONSE_BYTES:
                raise DomainError(
                    ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
                    "Ark response exceeds the closed size limit",
                )
            status_code = response.status
            response_digest = _bytes_digest(response_body)
            headers_value = {
                key.lower(): value for key, value in response.getheaders()
            }
            result = ProviderHTTPResponse(
                status_code=status_code,
                headers=headers_value,
                body=response_body,
            )
        except DomainError as exc:
            failure_code = exc.code.value
            self._record_audit(
                ordinal=ordinal,
                body_digest=body_digest,
                client_request_id=client_request_id,
                status_code=status_code,
                response_digest=response_digest,
                certificate_digest=certificate_digest,
                outcome="REJECTED",
                failure_code=failure_code,
            )
            raise
        except (
            OSError,
            TimeoutError,
            ssl.SSLError,
            http.client.HTTPException,
        ) as exc:
            failure_code = _network_failure_code(exc)
            self._record_audit(
                ordinal=ordinal,
                body_digest=body_digest,
                client_request_id=client_request_id,
                status_code=status_code,
                response_digest=response_digest,
                certificate_digest=certificate_digest,
                outcome="OUTCOME_UNKNOWN",
                failure_code=failure_code,
            )
            raise ProviderOutcomeUnknown(
                "Ark Chat Completions outcome is unknown",
                reason_code=failure_code,
            ) from exc
        finally:
            if tls_socket is not None:
                tls_socket.close()
            if raw_socket is not None:
                raw_socket.close()

        self._record_audit(
            ordinal=ordinal,
            body_digest=body_digest,
            client_request_id=client_request_id,
            status_code=status_code,
            response_digest=response_digest,
            certificate_digest=certificate_digest,
            outcome="HTTP_RESPONSE",
            failure_code=None,
        )
        return result

    def _record_audit(
        self,
        *,
        ordinal: int,
        body_digest: Digest,
        client_request_id: str,
        status_code: int | None,
        response_digest: Digest | None,
        certificate_digest: str | None,
        outcome: str,
        failure_code: str | None,
    ) -> None:
        audit = PinnedArkDispatchAudit(
            ordinal=ordinal,
            endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
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
            outcome=outcome,
            failure_code=failure_code,
        )
        self._audits.append(audit)
        self._audit_writer(audit.canonical_value())


def resolve_ark_provider_addresses() -> tuple[str, ...]:
    """Resolve the exact Ark host for a gateway-owned preflight record."""

    try:
        values = socket.getaddrinfo(
            ARK_PROVIDER_HOST,
            ARK_PROVIDER_PORT,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )
    except OSError as exc:
        raise DomainError(
            ErrorCode.LIVE_INTEGRATION_HELD,
            "Ark provider DNS preflight failed",
        ) from exc
    addresses = tuple(
        sorted(
            {
                str(_numeric_address(item[4][0]))
                for item in values
                if item[0] in {socket.AF_INET, socket.AF_INET6}
            },
            key=lambda value: (
                ipaddress.ip_address(value).version,
                ipaddress.ip_address(value).packed,
            ),
        )
    )
    if not addresses:
        raise DomainError(
            ErrorCode.LIVE_INTEGRATION_HELD,
            "Ark provider DNS preflight returned no numeric addresses",
        )
    return addresses


def _require_exact_endpoint(endpoint: object) -> None:
    if endpoint != DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT:
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "pinned Ark transport endpoint is not exact",
        )
    parsed = urlsplit(str(endpoint))
    if (
        parsed.scheme != "https"
        or parsed.hostname != ARK_PROVIDER_HOST
        or parsed.port not in {None, ARK_PROVIDER_PORT}
        or parsed.path != ARK_PROVIDER_PATH
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise DomainError(
            ErrorCode.QUALIFICATION_INVALID,
            "pinned Ark transport endpoint components are not exact",
        )


def _numeric_address(value: object) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    if not isinstance(value, str) or value != value.strip():
        raise DomainError(ErrorCode.INVALID_ARGUMENT, "provider address is invalid")
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise DomainError(
            ErrorCode.INVALID_ARGUMENT,
            "provider address must be a numeric IPv4 or IPv6 literal",
        ) from exc
    try:
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
    "ARK_PROVIDER_HOST",
    "ARK_PROVIDER_PATH",
    "ARK_PROVIDER_PORT",
    "PinnedArkDispatchAudit",
    "PinnedIPVolcengineArkChatTransport",
    "resolve_ark_provider_addresses",
]
