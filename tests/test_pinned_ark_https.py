from __future__ import annotations

from unittest.mock import patch
import unittest

from software_world_model.ai_infrastructure.pinned_ark_https import (
    ARK_PROVIDER_HOST,
    ARK_PROVIDER_PORT,
    PinnedIPVolcengineArkChatTransport,
)
from software_world_model.ai_infrastructure.volcengine_ark_chat_adapter import (
    DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
)
from software_world_model.cross_cutting import DomainError, ErrorCode, digest_of


class _RawSocket:
    def __init__(self, *, peer=("8.8.8.8", ARK_PROVIDER_PORT)) -> None:
        self.timeout = None
        self.target = None
        self.closed = False
        self.peer = peer

    def settimeout(self, value) -> None:
        self.timeout = value

    def connect(self, target) -> None:
        self.target = target

    def getpeername(self):
        return self.peer

    def close(self) -> None:
        self.closed = True


class _TLSSocket:
    def __init__(self) -> None:
        self.sent = b""
        self.closed = False

    def getpeercert(self, *, binary_form=False):
        return b"fixture-certificate" if binary_form else {}

    def sendall(self, value: bytes) -> None:
        self.sent += value

    def close(self) -> None:
        self.closed = True


class _TLSContext:
    def __init__(self) -> None:
        self.server_names: list[str] = []
        self.sockets: list[_TLSSocket] = []

    def wrap_socket(self, raw, *, server_hostname):
        del raw
        self.server_names.append(server_hostname)
        value = _TLSSocket()
        self.sockets.append(value)
        return value


class _HTTPResponse:
    status = 200

    def __init__(self, connection) -> None:
        self.connection = connection

    def begin(self) -> None:
        return None

    def read(self, maximum: int) -> bytes:
        self.maximum = maximum
        return b'{"fixture":true}'

    def getheaders(self):
        return [("X-Request-Id", "provider-1")]


class PinnedArkHTTPSTests(unittest.TestCase):
    def test_exact_numeric_route_uses_tls_hostname_and_redacted_audit(self) -> None:
        contexts = _TLSContext()
        raw_sockets: list[_RawSocket] = []
        audits: list[dict[str, object]] = []

        def raw_socket(*_):
            value = _RawSocket()
            raw_sockets.append(value)
            return value

        transport = PinnedIPVolcengineArkChatTransport(
            numeric_address="8.8.8.8",
            api_key_resolver=lambda: "secret-fixture-key",
            tls_context=contexts,
            audit_writer=lambda value: audits.append(dict(value)),
        )
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_ark_https.socket.socket",
                side_effect=raw_socket,
            ),
            patch(
                "software_world_model.ai_infrastructure.pinned_ark_https.http.client.HTTPResponse",
                _HTTPResponse,
            ),
        ):
            response = transport.post_json(
                endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
                body=b'{"request":true}',
                client_request_id="swm-fixture",
                timeout_milliseconds=1000,
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(raw_sockets[0].target, ("8.8.8.8", ARK_PROVIDER_PORT))
        self.assertEqual(contexts.server_names, [ARK_PROVIDER_HOST])
        wire = contexts.sockets[0].sent
        self.assertIn(b"Host: ark.cn-beijing.volces.com\r\n", wire)
        self.assertIn(b"Authorization: Bearer secret-fixture-key\r\n", wire)
        self.assertNotIn("secret-fixture-key", repr(audits))
        self.assertEqual(
            audits[0]["client_request_id_digest"],
            digest_of("swm-fixture").value,
        )
        self.assertEqual(audits[0]["address_scope"], "PUBLIC_UNICAST")
        self.assertEqual(transport.provider_call_count, 1)
        self.assertEqual(transport.network_operation_count, 1)

    def test_endpoint_drift_is_rejected_before_credential_resolution(self) -> None:
        credential_reads = 0

        def resolve() -> str:
            nonlocal credential_reads
            credential_reads += 1
            return "secret"

        transport = PinnedIPVolcengineArkChatTransport(
            numeric_address="8.8.8.8",
            api_key_resolver=resolve,
            tls_context=_TLSContext(),
        )
        with self.assertRaises(DomainError) as raised:
            transport.post_json(
                endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT + "?drift=1",
                body=b"{}",
                client_request_id="swm-fixture",
                timeout_milliseconds=1000,
            )
        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)
        self.assertEqual(credential_reads, 0)
        self.assertEqual(transport.provider_call_count, 0)

    def test_inherited_connected_socket_is_peer_pinned_without_new_connect(self) -> None:
        contexts = _TLSContext()
        inherited = _RawSocket()
        credential_reads = 0

        def resolve() -> str:
            nonlocal credential_reads
            credential_reads += 1
            return "secret"

        transport = PinnedIPVolcengineArkChatTransport(
            numeric_address="8.8.8.8",
            api_key_resolver=resolve,
            connected_socket_fd=17,
            tls_context=contexts,
        )
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_ark_https.socket.socket",
                return_value=inherited,
            ) as constructor,
            patch(
                "software_world_model.ai_infrastructure.pinned_ark_https.http.client.HTTPResponse",
                _HTTPResponse,
            ),
        ):
            transport.post_json(
                endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
                body=b"{}",
                client_request_id="swm-inherited",
                timeout_milliseconds=1000,
            )
        constructor.assert_called_once_with(
            __import__("socket").AF_INET,
            __import__("socket").SOCK_STREAM,
            fileno=17,
        )
        self.assertIsNone(inherited.target)
        self.assertEqual(credential_reads, 1)

    def test_three_inherited_sockets_support_three_isolated_dispatches(self) -> None:
        contexts = _TLSContext()
        inherited = [_RawSocket(), _RawSocket(), _RawSocket()]
        transport = PinnedIPVolcengineArkChatTransport(
            numeric_address="8.8.8.8",
            api_key_resolver=lambda: "secret",
            connected_socket_fds=(17, 18, 19),
            tls_context=contexts,
        )
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_ark_https.socket.socket",
                side_effect=inherited,
            ) as constructor,
            patch(
                "software_world_model.ai_infrastructure.pinned_ark_https.http.client.HTTPResponse",
                _HTTPResponse,
            ),
        ):
            for ordinal in range(3):
                transport.post_json(
                    endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id=f"swm-inherited-{ordinal}",
                    timeout_milliseconds=1000,
                )

        self.assertEqual(
            [item.kwargs["fileno"] for item in constructor.call_args_list],
            [17, 18, 19],
        )
        self.assertTrue(all(item.target is None for item in inherited))
        self.assertEqual(transport.provider_call_count, 3)

    def test_wrong_inherited_peer_is_rejected_before_credential_resolution(self) -> None:
        credential_reads = 0

        def resolve() -> str:
            nonlocal credential_reads
            credential_reads += 1
            return "secret"

        transport = PinnedIPVolcengineArkChatTransport(
            numeric_address="8.8.8.8",
            api_key_resolver=resolve,
            connected_socket_fd=19,
            tls_context=_TLSContext(),
        )
        with patch(
            "software_world_model.ai_infrastructure.pinned_ark_https.socket.socket",
            return_value=_RawSocket(peer=("1.1.1.1", ARK_PROVIDER_PORT)),
        ):
            with self.assertRaises(DomainError) as raised:
                transport.post_json(
                    endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id="swm-wrong-peer",
                    timeout_milliseconds=1000,
                )
        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)
        self.assertEqual(credential_reads, 0)

    def test_non_external_or_non_numeric_address_is_rejected(self) -> None:
        for address in ("localhost", "127.0.0.1", "::1", "10.0.0.1"):
            with self.subTest(address=address):
                with self.assertRaises(DomainError):
                    PinnedIPVolcengineArkChatTransport(
                        numeric_address=address,
                        api_key_resolver=lambda: "secret",
                    )

    def test_executor_synthetic_external_address_is_accepted(self) -> None:
        transport = PinnedIPVolcengineArkChatTransport(
            numeric_address="198.18.0.26",
            api_key_resolver=lambda: "secret",
            connected_socket_fd=23,
            tls_context=_TLSContext(),
        )
        self.assertEqual(transport.provider_call_count, 0)

    def test_five_call_fuse_counts_exact_dispatches(self) -> None:
        contexts = _TLSContext()
        transport = PinnedIPVolcengineArkChatTransport(
            numeric_address="8.8.8.8",
            api_key_resolver=lambda: "secret",
            tls_context=contexts,
        )
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_ark_https.socket.socket",
                side_effect=lambda *_: _RawSocket(),
            ),
            patch(
                "software_world_model.ai_infrastructure.pinned_ark_https.http.client.HTTPResponse",
                _HTTPResponse,
            ),
        ):
            for ordinal in range(5):
                transport.post_json(
                    endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id=f"swm-{ordinal}",
                    timeout_milliseconds=1000,
                )
            with self.assertRaises(DomainError) as raised:
                transport.post_json(
                    endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id="swm-sixth",
                    timeout_milliseconds=1000,
                )
        self.assertEqual(raised.exception.code, ErrorCode.CONTROL_STATE_DENIED)
        self.assertEqual(transport.provider_call_count, 5)

    def test_bounded_transport_closes_and_audits_unused_descriptors(self) -> None:
        contexts = _TLSContext()
        inherited = [_RawSocket() for _ in range(6)]
        audits: list[dict[str, object]] = []
        transport = PinnedIPVolcengineArkChatTransport(
            numeric_address="8.8.8.8",
            api_key_resolver=lambda: "secret",
            connected_socket_fds=(17, 18, 19, 20, 21, 22),
            tls_context=contexts,
            audit_writer=lambda value: audits.append(dict(value)),
            maximum_calls=6,
        )
        with (
            patch(
                "software_world_model.ai_infrastructure.pinned_ark_https.socket.socket",
                side_effect=inherited,
            ) as constructor,
            patch(
                "software_world_model.ai_infrastructure.pinned_ark_https.http.client.HTTPResponse",
                _HTTPResponse,
            ),
        ):
            for ordinal in range(4):
                transport.post_json(
                    endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id=f"swm-bounded-{ordinal}",
                    timeout_milliseconds=1000,
                )
            unused_closed = transport.close_unused_connected_sockets()

        self.assertEqual(unused_closed, 2)
        self.assertEqual(
            [item.kwargs["fileno"] for item in constructor.call_args_list],
            [17, 18, 19, 20, 21, 22],
        )
        self.assertTrue(inherited[4].closed)
        self.assertTrue(inherited[5].closed)
        self.assertEqual(
            [item["outcome"] for item in audits[-2:]],
            ["UNUSED_CLOSED", "UNUSED_CLOSED"],
        )


if __name__ == "__main__":
    unittest.main()
