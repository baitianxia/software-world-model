#!/usr/bin/env python3
"""Provision one exact Ark TCP socket without credentials or product payload.

This standard-library-only worker is the narrow public-network supervisor for
G3b.  It resolves only the frozen Ark hostname (or reconnects one previously
sealed numeric address), validates an explicitly classified external numeric
peer on TCP 443, and
transfers exactly one connected descriptor to its parent with ``SCM_RIGHTS``.
It never performs TLS/HTTP dispatch and fails closed if the Ark credential is
visible in its environment.
"""

from __future__ import annotations

import argparse
import array
from hashlib import sha256
import ipaddress
import json
import os
import socket
import sys
from typing import Sequence


ARK_PROVIDER_HOST = "ark.cn-beijing.volces.com"
ARK_PROVIDER_PORT = 443
SCHEMA = "swm.iter-003.g3b-provider-socket-provisioning@1"
_EXECUTOR_SYNTHETIC_EXTERNAL_NETWORK = ipaddress.ip_network("198.18.0.0/15")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control-fd", type=int, required=True)
    parser.add_argument("--numeric-address")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.control_fd < 3:
        raise ValueError("control descriptor is invalid")
    if arguments.timeout_seconds < 1 or arguments.timeout_seconds > 60:
        raise ValueError("connection timeout is outside the closed range")
    if os.environ.get("ARK_API_KEY") is not None:
        raise RuntimeError("Provider socket supervisor received a credential")

    if arguments.numeric_address is None:
        addresses = _resolve_exact_provider()
        dns_operation_count = 1
    else:
        addresses = (str(_external_numeric_address(arguments.numeric_address)),)
        dns_operation_count = 0
    connection, selected = _connect_first(
        addresses,
        timeout_seconds=arguments.timeout_seconds,
    )
    try:
        peer = connection.getpeername()
        peer_address = str(_external_numeric_address(str(peer[0])))
        if peer_address != selected or peer[1] != ARK_PROVIDER_PORT:
            raise RuntimeError("connected Provider peer differs from its exact pin")
        core = {
            "schema": SCHEMA,
            "worker_pid": os.getpid(),
            "provider_hostname": ARK_PROVIDER_HOST,
            "provider_port": ARK_PROVIDER_PORT,
            "resolved_addresses": list(addresses),
            "resolved_address_scopes": [
                {"address": item, "scope": _address_scope(item)}
                for item in addresses
            ],
            "selected_address": selected,
            "selected_address_scope": _address_scope(selected),
            "connected_peer_address": peer_address,
            "connected_peer_port": peer[1],
            "dns_operation_count": dns_operation_count,
            "tcp_connect_count": 1,
            "credential_visible": False,
            "product_request_payload_visible": False,
            "provider_response_payload_visible": False,
            "tls_operation_count": 0,
            "http_operation_count": 0,
            "descriptor_transfer_count": 1,
            "production_activation": "NOT_EXECUTED",
        }
        payload = {**core, "document_digest": _digest(core)}
        payload_bytes = _canonical_json_bytes(payload)
        control = socket.socket(fileno=arguments.control_fd)
        try:
            descriptors = array.array("i", [connection.fileno()])
            sent = control.sendmsg(
                [payload_bytes],
                [(socket.SOL_SOCKET, socket.SCM_RIGHTS, descriptors)],
            )
            if sent != len(payload_bytes):
                raise RuntimeError("connected Provider descriptor transfer failed")
        finally:
            control.close()
    finally:
        connection.close()
    return 0


def _resolve_exact_provider() -> tuple[str, ...]:
    values = socket.getaddrinfo(
        ARK_PROVIDER_HOST,
        ARK_PROVIDER_PORT,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    addresses = tuple(
        sorted(
            {
                str(_external_numeric_address(item[4][0]))
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
        raise RuntimeError("exact Ark DNS resolution returned no external address")
    return addresses


def _connect_first(
    addresses: Sequence[str],
    *,
    timeout_seconds: int,
) -> tuple[socket.socket, str]:
    failures: list[str] = []
    for value in addresses:
        address = _external_numeric_address(value)
        family = socket.AF_INET6 if address.version == 6 else socket.AF_INET
        target = (
            (str(address), ARK_PROVIDER_PORT, 0, 0)
            if family == socket.AF_INET6
            else (str(address), ARK_PROVIDER_PORT)
        )
        connection = socket.socket(family, socket.SOCK_STREAM)
        connection.settimeout(timeout_seconds)
        try:
            connection.connect(target)
        except OSError as exc:
            failures.append(type(exc).__name__)
            connection.close()
            continue
        return connection, str(address)
    raise RuntimeError(f"no resolved Ark address is reachable: {failures}")


def _external_numeric_address(value: object):
    if not isinstance(value, str) or value != value.strip():
        raise ValueError("Provider address is invalid")
    address = ipaddress.ip_address(value)
    _address_scope(address)
    return address


def _address_scope(value: object) -> str:
    address = (
        value
        if isinstance(value, (ipaddress.IPv4Address, ipaddress.IPv6Address))
        else ipaddress.ip_address(value)
    )
    if address.is_global:
        return "PUBLIC_UNICAST"
    if address in _EXECUTOR_SYNTHETIC_EXTERNAL_NETWORK:
        return "EXECUTOR_SYNTHETIC_EXTERNAL"
    raise ValueError("Provider address is not an accepted external egress peer")


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + sha256(_canonical_json_bytes(value)).hexdigest()


if __name__ == "__main__":
    try:
        _exit_code = main()
    except Exception as exc:
        sys.stderr.write(
            _canonical_json_bytes(
                {
                    "failure_type": type(exc).__name__,
                    "errno": getattr(exc, "errno", None),
                }
            ).decode("utf-8")
            + "\n"
        )
        _exit_code = 2
    raise SystemExit(_exit_code)
