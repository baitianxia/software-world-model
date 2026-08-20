from __future__ import annotations

from unittest.mock import patch
import socket
import ssl
import http.client
import unittest

from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
)
from software_world_model.ai_infrastructure.pinned_deepseek_https import (
    DEEPSEEK_PROVIDER_HOST,
    DEEPSEEK_PROVIDER_PORT,
    PinnedIPDeepSeekChatTransport,
)
from software_world_model.cross_cutting import DomainError, ErrorCode
from software_world_model.ai_infrastructure.model_gateway import (
    ProviderOutcomeUnknown,
)


class _RawSocket:
    def __init__(
        self,
        *,
        peer: tuple[str, int] = ("8.8.8.8", DEEPSEEK_PROVIDER_PORT),
    ) -> None:
        self.peer = peer
        self.timeout = None
        self.closed = False

    def settimeout(self, value) -> None:
        self.timeout = value

    def getpeername(self):
        return self.peer

    def close(self) -> None:
        self.closed = True


class _TLSSocket:
    def __init__(self, *, certificate: bytes = b"fixture-certificate") -> None:
        self.certificate = certificate
        self.sent = b""
        self.closed = False

    def getpeercert(self, *, binary_form=False):
        return self.certificate if binary_form else {}

    def sendall(self, value: bytes) -> None:
        self.sent += value

    def settimeout(self, value) -> None:
        self.timeout = value

    def close(self) -> None:
        self.closed = True


class _TLSContext:
    def __init__(
        self,
        *,
        certificate: bytes = b"fixture-certificate",
        wrap_failures=(),
    ) -> None:
        self.certificate = certificate
        self.wrap_failures = list(wrap_failures)
        self.server_names: list[str] = []
        self.sockets: list[_TLSSocket] = []

    def wrap_socket(self, raw, *, server_hostname):
        del raw
        self.server_names.append(server_hostname)
        if self.wrap_failures:
            failure = self.wrap_failures.pop(0)
            if failure is not None:
                raise failure
        secured = _TLSSocket(certificate=self.certificate)
        self.sockets.append(secured)
        return secured


class _HTTPResponse:
    status = 200
    will_close = False

    def __init__(self, connection) -> None:
        self.connection = connection

    def begin(self) -> None:
        return None

    def read(self, maximum: int) -> bytes:
        self.maximum = maximum
        return b'{"fixture":true}'

    def getheaders(self):
        return [
            ("X-Request-Id", "deepseek-fixture-1"),
            ("Connection", "keep-alive"),
        ]


class _ClosingHTTPResponse(_HTTPResponse):
    will_close = True

    def getheaders(self):
        return [("X-Request-Id", "deepseek-fixture-close"), ("Connection", "close")]


class _UnknownHTTPResponse(_HTTPResponse):
    def begin(self) -> None:
        raise http.client.RemoteDisconnected("fixture disconnect")


def _transport(
    *,
    resolver=lambda: "secret-fixture-key",
    context=None,
    audits=None,
) -> PinnedIPDeepSeekChatTransport:
    return PinnedIPDeepSeekChatTransport(
        numeric_address="8.8.8.8",
        api_key_resolver=resolver,
        connected_socket_fds=(17, 18, 19),
        tls_context=context or _TLSContext(),
        audit_writer=(
            (lambda value: audits.append(dict(value)))
            if audits is not None
            else None
        ),
        maximum_calls=6,
    )


class PinnedDeepSeekHTTPSTests(unittest.TestCase):
    def test_requires_exactly_three_unique_inherited_descriptors(self) -> None:
        for descriptors in (
            (17, 18),
            (17, 18, 18),
            (17, 18, 19, 20),
        ):
            with self.subTest(descriptors=descriptors):
                with self.assertRaises(DomainError) as raised:
                    PinnedIPDeepSeekChatTransport(
                        numeric_address="8.8.8.8",
                        api_key_resolver=lambda: "secret",
                        connected_socket_fds=descriptors,
                    )
                self.assertEqual(
                    raised.exception.code,
                    ErrorCode.INVALID_ARGUMENT,
                )

    def test_exact_peer_uses_deepseek_sni_and_late_bearer_credential(self) -> None:
        context = _TLSContext()
        inherited = _RawSocket()
        audits: list[dict[str, object]] = []
        credential_reads = 0

        def resolve() -> str:
            nonlocal credential_reads
            credential_reads += 1
            return "secret-fixture-key"

        transport = _transport(
            resolver=resolve,
            context=context,
            audits=audits,
        )
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.socket.socket",
                return_value=inherited,
            ) as constructor,
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.http.client.HTTPResponse",
                _HTTPResponse,
            ),
        ):
            response = transport.post_json(
                endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                body=b'{"request":true}',
                client_request_id="swm-deepseek-fixture",
                timeout_milliseconds=1000,
            )

        self.assertEqual(response.status_code, 200)
        constructor.assert_called_once_with(
            socket.AF_INET,
            socket.SOCK_STREAM,
            fileno=17,
        )
        self.assertEqual(context.server_names, [DEEPSEEK_PROVIDER_HOST])
        self.assertEqual(credential_reads, 1)
        self.assertIn(b"Host: api.deepseek.com\r\n", context.sockets[0].sent)
        self.assertIn(
            b"Authorization: Bearer secret-fixture-key\r\n",
            context.sockets[0].sent,
        )
        self.assertNotIn("secret-fixture-key", repr(audits))
        self.assertEqual(audits[0]["outcome"], "VERIFIED")
        self.assertEqual(audits[1]["outcome"], "HTTP_RESPONSE")
        self.assertFalse(audits[1]["connection_reused"])

    def test_endpoint_or_peer_drift_is_rejected_before_credential_read(self) -> None:
        credential_reads = 0

        def resolve() -> str:
            nonlocal credential_reads
            credential_reads += 1
            return "secret"

        endpoint_transport = _transport(resolver=resolve)
        with self.assertRaises(DomainError) as endpoint_rejection:
            endpoint_transport.post_json(
                endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT + "?drift=1",
                body=b"{}",
                client_request_id="swm-endpoint-drift",
                timeout_milliseconds=1000,
            )

        peer_transport = _transport(resolver=resolve)
        with patch(
            "software_world_model.ai_infrastructure.pinned_deepseek_https.socket.socket",
            return_value=_RawSocket(
                peer=("1.1.1.1", DEEPSEEK_PROVIDER_PORT)
            ),
        ):
            with self.assertRaises(DomainError) as peer_rejection:
                peer_transport.post_json(
                    endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id="swm-peer-drift",
                    timeout_milliseconds=1000,
                )

        self.assertEqual(
            endpoint_rejection.exception.code,
            ErrorCode.QUALIFICATION_INVALID,
        )
        self.assertEqual(
            peer_rejection.exception.code,
            ErrorCode.QUALIFICATION_INVALID,
        )
        self.assertEqual(credential_reads, 0)

    def test_four_dispatches_reuse_one_tls_and_close_two_unused_descriptors(self) -> None:
        inherited = [_RawSocket() for _ in range(3)]
        audits: list[dict[str, object]] = []
        transport = _transport(audits=audits)
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.socket.socket",
                side_effect=inherited,
            ) as constructor,
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.http.client.HTTPResponse",
                _HTTPResponse,
            ),
        ):
            for ordinal in range(4):
                transport.post_json(
                    endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id=f"swm-deepseek-{ordinal}",
                    timeout_milliseconds=1000,
                )
            unused_closed = transport.close_unused_connected_sockets()

        self.assertEqual(unused_closed, 2)
        self.assertEqual(
            [item.kwargs["fileno"] for item in constructor.call_args_list],
            [17, 18, 19],
        )
        self.assertEqual(
            [item["outcome"] for item in audits],
            ["VERIFIED"]
            + ["HTTP_RESPONSE"] * 4
            + ["ACTIVE_TLS_CLOSED"]
            + ["UNUSED_CLOSED"] * 2,
        )
        self.assertEqual(transport.tls_handshake_attempt_count, 1)
        self.assertEqual(transport.tls_handshake_success_count, 1)
        self.assertEqual(transport.connection_reuse_count, 3)
        self.assertEqual(transport.credential_resolution_count, 4)
        self.assertEqual(transport.credential_resolution_success_count, 4)
        self.assertTrue(inherited[1].closed)
        self.assertTrue(inherited[2].closed)

    def test_tls_failure_consumes_next_descriptor_before_credential_read(self) -> None:
        context = _TLSContext(
            wrap_failures=(ssl.SSLEOFError("fixture EOF"), None)
        )
        inherited = [_RawSocket() for _ in range(2)]
        credential_reads = 0

        def resolve() -> str:
            nonlocal credential_reads
            credential_reads += 1
            return "secret-fixture-key"

        transport = _transport(resolver=resolve, context=context)
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.socket.socket",
                side_effect=inherited,
            ),
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.http.client.HTTPResponse",
                _HTTPResponse,
            ),
        ):
            transport.post_json(
                endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                body=b"{}",
                client_request_id="swm-deepseek-recovered",
                timeout_milliseconds=1000,
            )

        self.assertEqual(credential_reads, 1)
        self.assertEqual(transport.tls_handshake_attempt_count, 2)
        self.assertEqual(transport.tls_handshake_success_count, 1)
        self.assertEqual(transport.provider_call_count, 1)
        self.assertEqual(transport.credential_resolution_count, 1)
        self.assertEqual(transport.credential_resolution_success_count, 1)

    def test_explicit_server_close_uses_a_new_session_for_the_next_request(self) -> None:
        context = _TLSContext()
        inherited = [_RawSocket() for _ in range(3)]
        response_classes = [_ClosingHTTPResponse, _HTTPResponse]
        transport = _transport(context=context)
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.socket.socket",
                side_effect=inherited,
            ),
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.http.client.HTTPResponse",
                side_effect=lambda active: response_classes.pop(0)(active),
            ),
        ):
            for ordinal in range(2):
                transport.post_json(
                    endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id=f"swm-server-close-{ordinal}",
                    timeout_milliseconds=1000,
                )
            unused_closed = transport.close_session_and_unused_connected_sockets()

        self.assertEqual(transport.tls_handshake_attempt_count, 2)
        self.assertEqual(transport.tls_handshake_success_count, 2)
        self.assertEqual(transport.connection_reuse_count, 0)
        self.assertEqual(unused_closed, 1)

    def test_post_dispatch_disconnect_is_unknown_and_never_retried(self) -> None:
        credential_reads = 0

        def resolve() -> str:
            nonlocal credential_reads
            credential_reads += 1
            return "secret-fixture-key"

        transport = _transport(resolver=resolve)
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.socket.socket",
                side_effect=[_RawSocket()],
            ),
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.http.client.HTTPResponse",
                _UnknownHTTPResponse,
            ),
            self.assertRaises(ProviderOutcomeUnknown) as raised,
        ):
            transport.post_json(
                endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                body=b"{}",
                client_request_id="swm-outcome-unknown",
                timeout_milliseconds=1000,
            )

        self.assertEqual(raised.exception.reason_code, "NETWORK_OUTCOME_UNKNOWN")
        self.assertEqual(credential_reads, 1)
        self.assertEqual(transport.tls_handshake_attempt_count, 1)
        self.assertEqual(transport.provider_call_count, 1)
        self.assertEqual(transport.credential_resolution_count, 1)
        self.assertEqual(transport.credential_resolution_success_count, 1)
        self.assertEqual(transport.audits[0].outcome, "OUTCOME_UNKNOWN")

    def test_three_tls_failures_exhaust_without_credential_or_http_dispatch(self) -> None:
        credential_reads = 0

        def resolve() -> str:
            nonlocal credential_reads
            credential_reads += 1
            return "secret-fixture-key"

        context = _TLSContext(
            wrap_failures=(
                ssl.SSLEOFError("fixture EOF 1"),
                ssl.SSLEOFError("fixture EOF 2"),
                ssl.SSLEOFError("fixture EOF 3"),
            )
        )
        transport = _transport(resolver=resolve, context=context)
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.socket.socket",
                side_effect=[_RawSocket() for _ in range(3)],
            ),
            self.assertRaises(DomainError) as raised,
        ):
            transport.post_json(
                endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                body=b"{}",
                client_request_id="swm-tls-exhausted",
                timeout_milliseconds=1000,
            )

        self.assertEqual(raised.exception.code, ErrorCode.LIVE_INTEGRATION_HELD)
        self.assertEqual(credential_reads, 0)
        self.assertEqual(transport.tls_handshake_attempt_count, 3)
        self.assertEqual(transport.provider_call_count, 0)
        self.assertEqual(transport.credential_resolution_count, 0)
        self.assertEqual(transport.credential_resolution_success_count, 0)

    def test_missing_credential_after_verified_tls_is_not_an_http_dispatch(self) -> None:
        transport = _transport(resolver=lambda: "")
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.socket.socket",
                return_value=_RawSocket(),
            ),
            self.assertRaises(DomainError) as raised,
        ):
            transport.post_json(
                endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                body=b"{}",
                client_request_id="swm-missing-credential",
                timeout_milliseconds=1000,
            )

        self.assertEqual(raised.exception.code, ErrorCode.LIVE_INTEGRATION_HELD)
        self.assertEqual(transport.tls_handshake_success_count, 1)
        self.assertEqual(transport.credential_resolution_count, 1)
        self.assertEqual(transport.credential_resolution_success_count, 0)
        self.assertEqual(transport.provider_call_count, 0)
        self.assertEqual(transport.audits, ())

    def test_six_call_fuse_denies_any_seventh_dispatch(self) -> None:
        transport = _transport()
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.socket.socket",
                side_effect=[_RawSocket()],
            ),
            patch(
                "software_world_model.ai_infrastructure.pinned_deepseek_https.http.client.HTTPResponse",
                _HTTPResponse,
            ),
        ):
            for ordinal in range(6):
                transport.post_json(
                    endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id=f"swm-deepseek-{ordinal}",
                    timeout_milliseconds=1000,
                )
            with self.assertRaises(DomainError) as raised:
                transport.post_json(
                    endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id="swm-deepseek-seventh",
                    timeout_milliseconds=1000,
                )

        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(transport.provider_call_count, 6)


if __name__ == "__main__":
    unittest.main()
