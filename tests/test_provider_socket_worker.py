from __future__ import annotations

from contextlib import redirect_stderr
from io import StringIO
import os
import socket
import unittest
from unittest.mock import patch

from software_world_model.interface.world_model_runtime_assets import (
    os_probe_worker,
    provider_socket_worker,
)


class ProviderSocketWorkerTests(unittest.TestCase):
    def test_internal_registry_selects_exact_deepseek_dns_target(self) -> None:
        with patch.object(
            provider_socket_worker.socket,
            "getaddrinfo",
            return_value=[
                (
                    socket.AF_INET,
                    socket.SOCK_STREAM,
                    socket.IPPROTO_TCP,
                    "",
                    ("8.8.8.8", 443),
                )
            ],
        ) as resolver:
            addresses = provider_socket_worker._resolve_exact_provider(
                "api.deepseek.com",
                443,
            )

        self.assertEqual(addresses, ("8.8.8.8",))
        resolver.assert_called_once_with(
            "api.deepseek.com",
            443,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
        )

    def test_worker_rejects_either_provider_credential_before_dns(self) -> None:
        for name in ("ARK_API_KEY", "DEEPSEEK_API_KEY"):
            with self.subTest(name=name):
                with (
                    patch.dict(os.environ, {name: "secret"}, clear=True),
                    patch.object(
                        provider_socket_worker,
                        "_resolve_exact_provider",
                    ) as resolver,
                ):
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "received a credential",
                    ):
                        provider_socket_worker.main(
                            [
                                "--control-fd",
                                "3",
                                "--provider-type",
                                "DEEPSEEK",
                            ]
                        )
                resolver.assert_not_called()

    def test_arbitrary_provider_type_is_not_a_cli_option(self) -> None:
        with redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit):
                provider_socket_worker._parser().parse_args(
                    [
                        "--control-fd",
                        "3",
                        "--provider-type",
                        "REQUEST_SUPPLIED_PROVIDER",
                    ]
                )
            with self.assertRaises(SystemExit):
                os_probe_worker._parser().parse_args(
                    [
                        "--role",
                        "gateway",
                        "--nonce",
                        "nonce",
                        "--allowed-read-file",
                        "/tmp/read",
                        "--allowed-write-file",
                        "/tmp/write",
                        "--gateway-socket",
                        "/tmp/gateway.sock",
                        "--other-unix-socket",
                        "/tmp/other.sock",
                        "--provider-address",
                        "8.8.8.8",
                        "--provider-type",
                        "REQUEST_SUPPLIED_PROVIDER",
                        "--local-tcp-port",
                        "1",
                        "--output",
                        "/tmp/output.json",
                    ]
                )


if __name__ == "__main__":
    unittest.main()
