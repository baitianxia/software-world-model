#!/usr/bin/env python3
"""Independent authorized/denied OS capability probes for ITER-003 G3b."""

from __future__ import annotations

import argparse
import errno
import json
import os
from pathlib import Path
import socket
import ssl
import stat
import sys
from typing import Callable, Sequence


SCHEMA = "swm.iter-003.g3b-os-probe@1"
_DENIED_ERRNOS = {errno.EACCES, errno.EPERM}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--role", choices=("answer", "gateway", "projector"), required=True
    )
    parser.add_argument("--nonce", required=True)
    parser.add_argument("--allowed-read-file", required=True)
    parser.add_argument("--allowed-write-file", required=True)
    parser.add_argument("--forbidden-file", action="append", default=[])
    parser.add_argument("--gateway-socket", required=True)
    parser.add_argument("--other-unix-socket", required=True)
    parser.add_argument("--provider-address", required=True)
    parser.add_argument("--connected-provider-socket-fd", type=int, default=-1)
    parser.add_argument("--gateway-listener-socket-fd", type=int, default=-1)
    parser.add_argument("--local-tcp-port", type=int, required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    role = arguments.role
    results: list[dict[str, object]] = []
    results.append(
        _expect_allowed(
            "allowed_file_read",
            lambda: Path(arguments.allowed_read_file).read_bytes()[:1],
        )
    )
    results.append(
        _expect_allowed(
            "allowed_file_write",
            lambda: _write_new(Path(arguments.allowed_write_file), b"allowed\n"),
        )
    )
    for value in arguments.forbidden_file:
        label, separator, path = value.partition("=")
        if not separator or not label or not path:
            raise ValueError("forbidden file probe must be label=absolute-path")
        results.append(
            _expect_denied(
                f"denied_file:{label}", lambda path=path: _read_one(path)
            )
        )

    if role == "answer":
        results.append(
            _expect_allowed(
                "allowed_exact_gateway_connect",
                lambda: _unix_connect(arguments.gateway_socket),
            )
        )
        results.append(
            _expect_denied(
                "denied_other_unix_connect",
                lambda: _unix_connect(arguments.other_unix_socket),
            )
        )
    elif role == "gateway":
        results.append(
            _expect_connected_state(
                "inherited_provider_descriptor_is_already_connected",
                lambda: _reconnect_connected_provider(
                    arguments.connected_provider_socket_fd,
                    arguments.provider_address,
                ),
            )
        )
        results.append(
            _expect_allowed(
                "allowed_inherited_exact_gateway_listener_round_trip",
                lambda: _inherited_unix_round_trip(
                    arguments.gateway_listener_socket_fd,
                    arguments.gateway_socket,
                ),
            )
        )
        results.append(
            _expect_denied(
                "denied_new_inet_socket_creation",
                lambda: _new_socket(socket.AF_INET),
            )
        )
        results.append(
            _expect_denied(
                "denied_new_unix_socket_creation",
                lambda: _new_socket(socket.AF_UNIX),
            )
        )
        results.append(
            _expect_denied(
                "denied_new_provider_connect",
                lambda: _tcp_connect(arguments.provider_address, 443),
            )
        )
        results.append(
            _expect_allowed(
                "allowed_inherited_exact_provider_tls",
                lambda: _inherited_tls(
                    arguments.connected_provider_socket_fd,
                    arguments.provider_address,
                ),
            )
        )
        results.append(
            _expect_denied(
                "denied_other_unix_connect",
                lambda: _unix_connect(arguments.other_unix_socket),
            )
        )
    else:
        results.append(
            _expect_denied(
                "denied_gateway_unix_connect",
                lambda: _unix_connect(arguments.gateway_socket),
            )
        )
        results.append(
            _expect_denied(
                "denied_other_unix_connect",
                lambda: _unix_connect(arguments.other_unix_socket),
            )
        )

    if role != "gateway":
        results.append(
            _expect_denied(
                "denied_provider_inet_connect",
                lambda: _tcp_connect(arguments.provider_address, 443),
            )
        )
    results.append(
        _expect_denied(
            "denied_local_inet_connect",
            lambda: _tcp_connect("127.0.0.1", arguments.local_tcp_port),
        )
    )
    results.append(
        _expect_denied(
            "denied_dns_resolution",
            lambda: socket.getaddrinfo(
                "ark.cn-beijing.volces.com",
                443,
                type=socket.SOCK_STREAM,
            ),
            accept_any_failure=True,
        )
    )
    results.append(_expect_denied("denied_process_fork", _fork_once))

    credential_visible = os.environ.get("ARK_API_KEY") is not None
    credential_expected = role == "gateway"
    results.append(
        {
            "name": "credential_role_boundary",
            "expected": "VISIBLE" if credential_expected else "ABSENT",
            "observed": "VISIBLE" if credential_visible else "ABSENT",
            "status": "PASS" if credential_visible == credential_expected else "FAIL",
        }
    )
    status = "PASS" if all(item["status"] == "PASS" for item in results) else "FAIL"
    payload = {
        "schema": SCHEMA,
        "role": role,
        "nonce": arguments.nonce,
        "pid": os.getpid(),
        "status": status,
        "probes": results,
        "credential_value_recorded": False,
        "production_activation": "NOT_EXECUTED",
    }
    _write_new(Path(arguments.output), _canonical_json_bytes(payload))
    sys.stdout.write(_canonical_json_bytes(payload).decode("utf-8"))
    sys.stdout.write("\n")
    return 0 if status == "PASS" else 2


def _expect_allowed(name: str, action: Callable[[], object]) -> dict[str, object]:
    try:
        action()
    except BaseException as exc:
        return {
            "name": name,
            "expected": "ALLOWED",
            "observed": "DENIED_OR_FAILED",
            "status": "FAIL",
            "exception_type": type(exc).__name__,
            "errno": getattr(exc, "errno", None),
        }
    return {
        "name": name,
        "expected": "ALLOWED",
        "observed": "ALLOWED",
        "status": "PASS",
    }


def _expect_denied(
    name: str,
    action: Callable[[], object],
    *,
    accept_any_failure: bool = False,
) -> dict[str, object]:
    try:
        action()
    except BaseException as exc:
        error_number = getattr(exc, "errno", None)
        denied = accept_any_failure or error_number in _DENIED_ERRNOS
        return {
            "name": name,
            "expected": "DENIED",
            "observed": "DENIED" if denied else "FAILED_NON_POLICY",
            "status": "PASS" if denied else "FAIL",
            "exception_type": type(exc).__name__,
            "errno": error_number,
        }
    return {
        "name": name,
        "expected": "DENIED",
        "observed": "ALLOWED",
        "status": "FAIL",
    }


def _expect_connected_state(
    name: str,
    action: Callable[[], object],
) -> dict[str, object]:
    try:
        action()
    except BaseException as exc:
        error_number = getattr(exc, "errno", None)
        already_connected = error_number == errno.EISCONN
        return {
            "name": name,
            "expected": "ALREADY_CONNECTED",
            "observed": (
                "ALREADY_CONNECTED" if already_connected else "FAILED_OTHER"
            ),
            "status": "PASS" if already_connected else "FAIL",
            "exception_type": type(exc).__name__,
            "errno": error_number,
        }
    return {
        "name": name,
        "expected": "ALREADY_CONNECTED",
        "observed": "CONNECT_SUCCEEDED",
        "status": "FAIL",
    }


def _read_one(value: str) -> bytes:
    with Path(value).open("rb") as stream:
        return stream.read(1)


def _unix_connect(value: str) -> None:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(5.0)
        connection.connect(value)
        connection.sendall(b"P")


def _inherited_unix_round_trip(descriptor: int, expected_path: str) -> None:
    if descriptor < 0:
        raise ValueError("inherited Gateway listener descriptor is missing")
    path = Path(expected_path)
    status = path.lstat()
    listener = socket.socket(
        socket.AF_UNIX,
        socket.SOCK_STREAM,
        fileno=descriptor,
    )
    listener.settimeout(10.0)
    bound_path = listener.getsockname()
    if isinstance(bound_path, bytes):
        bound_path = bound_path.decode("utf-8")
    if (
        path.is_symlink()
        or not stat.S_ISSOCK(status.st_mode)
        or stat.S_IMODE(status.st_mode) != 0o600
        or bound_path != expected_path
    ):
        raise RuntimeError("inherited Gateway listener is not exact")
    with listener:
        connection, _ = listener.accept()
        with connection:
            if connection.recv(1) != b"P":
                raise RuntimeError("inherited Gateway listener probe is invalid")
            connection.sendall(b"Q")


def _reconnect_connected_provider(descriptor: int, target_address: str) -> None:
    if descriptor < 0:
        raise ValueError("inherited connected Provider descriptor is missing")
    family = socket.AF_INET6 if ":" in target_address else socket.AF_INET
    duplicate = os.dup(descriptor)
    with socket.socket(
        family,
        socket.SOCK_STREAM,
        fileno=duplicate,
    ) as inherited:
        peer = inherited.getpeername()
        if peer[0] != target_address or peer[1] != 443:
            raise RuntimeError("inherited Provider peer differs from its exact pin")
        address: tuple[object, ...]
        if family == socket.AF_INET6:
            address = (target_address, 443, 0, 0)
        else:
            address = (target_address, 443)
        inherited.connect(address)


def _new_socket(family: int) -> None:
    with socket.socket(family, socket.SOCK_STREAM):
        pass


def _tcp_connect(host: str, port: int) -> None:
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    address: tuple[object, ...]
    if family == socket.AF_INET6:
        address = (host, port, 0, 0)
    else:
        address = (host, port)
    with socket.socket(family, socket.SOCK_STREAM) as connection:
        connection.settimeout(10.0)
        connection.connect(address)


def _inherited_tls(descriptor: int, expected_address: str) -> None:
    if descriptor < 0:
        raise ValueError("inherited Provider descriptor is missing")
    family = socket.AF_INET6 if ":" in expected_address else socket.AF_INET
    raw = socket.socket(family, socket.SOCK_STREAM, fileno=descriptor)
    raw.settimeout(20.0)
    peer = raw.getpeername()
    if peer[0] != expected_address or peer[1] != 443:
        raise RuntimeError("inherited Provider peer differs from its exact pin")
    context = ssl.create_default_context()
    defaults = ssl.get_default_verify_paths()
    if defaults.cafile is None and defaults.capath is None:
        context.load_verify_locations(cafile="/private/etc/ssl/cert.pem")
    with context.wrap_socket(
        raw,
        server_hostname="ark.cn-beijing.volces.com",
    ) as secured:
        if not secured.getpeercert(binary_form=True):
            raise RuntimeError("inherited Provider TLS peer has no certificate")


def _fork_once() -> None:
    child = os.fork()
    if child == 0:  # pragma: no cover - only reached if the policy is broken
        os._exit(0)
    os.waitpid(child, 0)


def _write_new(path: Path, payload: bytes) -> None:
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise ValueError("probe output path must be canonical and absolute")
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("probe output parent must be canonical")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        remaining = memoryview(payload)
        while remaining:
            remaining = remaining[os.write(descriptor, remaining) :]
        os.fsync(descriptor)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError("probe output is not a regular file")
    finally:
        os.close(descriptor)


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
