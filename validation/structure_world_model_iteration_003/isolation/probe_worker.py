#!/usr/bin/env python3
"""In-sandbox worker for the ITER-003 G2 OS isolation proof.

The outer harness copies this file into each staged role package before
launch.  It deliberately uses only the Python standard library and emits one
closed JSON report on stdout.  It never imports or executes product workload
code; the workload runs later in a different Seatbelt child and PID.
"""

from __future__ import annotations

import argparse
import errno
from hashlib import sha256
import json
import os
from pathlib import Path
import socket
import sqlite3
import sys
from typing import Callable, Sequence
from urllib.parse import quote


REPORT_SCHEMA = "iteration-003-g2-isolation-worker-report@1"

COMMON_PROBES = (
    "source_remote",
    "public_ip",
    "dns",
    "tcp",
    "unix_socket",
    "out_of_allowlist_open",
    "sqlite",
    "git_repository",
)
ANSWER_PROBES = (*COMMON_PROBES, "answer_to_projector")
PROJECTOR_PROBES = (*COMMON_PROBES, "projector_to_answer")


def required_probes(role: str) -> tuple[str, ...]:
    if role == "answer":
        return ANSWER_PROBES
    if role == "projector":
        return PROJECTOR_PROBES
    raise ValueError(f"unsupported isolation role: {role}")


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _canonical_existing_file(value: str, root: Path, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    resolved = path.resolve(strict=True)
    if path != resolved or not _is_within(resolved, root):
        raise ValueError(f"{label} escapes its authorized root")
    if not resolved.is_file() or resolved.is_symlink():
        raise ValueError(f"{label} must be a regular non-symlink file")
    return resolved


def _exception_payload(exc: Exception) -> dict[str, object]:
    payload: dict[str, object] = {
        "type": type(exc).__name__,
        "message": str(exc)[:500],
    }
    error_number = getattr(exc, "errno", None)
    if isinstance(error_number, int):
        payload["errno"] = error_number
    return payload


def _is_os_denial(name: str, exc: Exception) -> bool:
    if isinstance(exc, PermissionError):
        return True
    if isinstance(exc, OSError) and exc.errno in {errno.EPERM, errno.EACCES}:
        return True
    # The outer runner first resolves both names outside the sandbox.  A
    # resolver error here is therefore evidence that this process could not
    # reach the resolver under its default-deny IPC/network policy.
    if name in {"dns", "source_remote"} and isinstance(exc, socket.gaierror):
        return True
    # sqlite3 does not preserve the underlying EACCES errno.  The outer runner
    # proves that this exact DB is readable and queryable before launch.
    if (
        name == "sqlite"
        and isinstance(exc, sqlite3.OperationalError)
        and "unable to open database file" in str(exc).lower()
    ):
        return True
    return False


def _probe(name: str, operation: Callable[[], None]) -> dict[str, object]:
    try:
        operation()
    except Exception as exc:  # every denial must be reported, never hidden
        return {
            "name": name,
            "outcome": "DENIED" if _is_os_denial(name, exc) else "ERROR",
            "exception": _exception_payload(exc),
        }
    return {"name": name, "outcome": "ALLOWED"}


def _connect_tcp(host: str, port: int) -> None:
    with socket.create_connection((host, port), timeout=1.0):
        return None


def _connect_unix(path: str) -> None:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(1.0)
        connection.connect(path)


def _read_file(path: str) -> None:
    with Path(path).open("rb") as stream:
        stream.read(1)


def _read_sqlite(path: str) -> None:
    uri = f"file:{quote(path, safe='/')}?mode=ro&immutable=1"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()


def _authorized_read(name: str, path: Path) -> dict[str, object]:
    try:
        return {
            "name": name,
            "outcome": "PASS",
            "path": str(path),
            "digest": _sha256_file(path),
        }
    except Exception as exc:
        return {
            "name": name,
            "outcome": "FAIL",
            "path": str(path),
            "exception": _exception_payload(exc),
        }


def _output_canary(output_root: Path, nonce: str) -> dict[str, object]:
    path = output_root / f".iter003-g2-write-canary-{nonce}.json"
    payload = json.dumps(
        {"schema": "iteration-003-g2-write-canary@1", "nonce": nonce},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    try:
        path.write_bytes(payload)
        observed = path.read_bytes()
        path.unlink()
        if observed != payload:
            raise ValueError("output canary changed after write")
        return {
            "name": "result_output_write",
            "outcome": "PASS",
            "digest": "sha256:" + sha256(payload).hexdigest(),
            "removed_after_readback": True,
        }
    except Exception as exc:
        return {
            "name": "result_output_write",
            "outcome": "FAIL",
            "exception": _exception_payload(exc),
        }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=("answer", "projector"), required=True)
    parser.add_argument("--nonce", required=True)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--package-canary", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--bundle-root")
    parser.add_argument("--bundle-canary")
    parser.add_argument("--sealed-result")
    parser.add_argument("--store-root")
    parser.add_argument("--store-canary")
    parser.add_argument("--source-remote-host", required=True)
    parser.add_argument("--source-remote-port", required=True, type=int)
    parser.add_argument("--public-ip", required=True)
    parser.add_argument("--public-port", required=True, type=int)
    parser.add_argument("--dns-host", required=True)
    parser.add_argument("--tcp-host", required=True)
    parser.add_argument("--tcp-port", required=True, type=int)
    parser.add_argument("--unix-socket", required=True)
    parser.add_argument("--callback-host", required=True)
    parser.add_argument("--callback-port", required=True, type=int)
    parser.add_argument("--forbidden-file", required=True)
    parser.add_argument("--forbidden-sqlite", required=True)
    parser.add_argument("--forbidden-git-root", required=True)
    parser.add_argument("--forbidden-git-marker", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    package_root = Path(arguments.package_root).resolve(strict=True)
    output_root = Path(arguments.output_root).resolve(strict=True)
    authorized = [
        _authorized_read(
            "package_read",
            _canonical_existing_file(
                arguments.package_canary, package_root, "package canary"
            ),
        )
    ]
    if arguments.role == "answer":
        if not arguments.bundle_root or not arguments.bundle_canary:
            raise ValueError("answer role requires Bundle root and canary")
        bundle_root = Path(arguments.bundle_root).resolve(strict=True)
        authorized.append(
            _authorized_read(
                "bundle_read",
                _canonical_existing_file(
                    arguments.bundle_canary, bundle_root, "Bundle canary"
                ),
            )
        )
    else:
        if (
            not arguments.sealed_result
            or not arguments.store_root
            or not arguments.store_canary
        ):
            raise ValueError(
                "projector role requires sealed Result, Store root and Store canary"
            )
        sealed_result = Path(arguments.sealed_result).resolve(strict=True)
        if not sealed_result.is_file() or sealed_result.is_symlink():
            raise ValueError("sealed Result must be a regular non-symlink file")
        store_root = Path(arguments.store_root).resolve(strict=True)
        authorized.extend(
            (
                _authorized_read("sealed_result_read", sealed_result),
                _authorized_read(
                    "allowlisted_store_read",
                    _canonical_existing_file(
                        arguments.store_canary, store_root, "Store canary"
                    ),
                ),
            )
        )
    authorized.append(_output_canary(output_root, arguments.nonce))

    callback_name = (
        "answer_to_projector"
        if arguments.role == "answer"
        else "projector_to_answer"
    )
    probe_operations: dict[str, Callable[[], None]] = {
        "source_remote": lambda: _connect_tcp(
            arguments.source_remote_host, arguments.source_remote_port
        ),
        "public_ip": lambda: _connect_tcp(arguments.public_ip, arguments.public_port),
        "dns": lambda: socket.getaddrinfo(
            arguments.dns_host, arguments.public_port, type=socket.SOCK_STREAM
        ),
        "tcp": lambda: _connect_tcp(arguments.tcp_host, arguments.tcp_port),
        "unix_socket": lambda: _connect_unix(arguments.unix_socket),
        "out_of_allowlist_open": lambda: _read_file(arguments.forbidden_file),
        "sqlite": lambda: _read_sqlite(arguments.forbidden_sqlite),
        "git_repository": lambda: _read_file(arguments.forbidden_git_marker),
        callback_name: lambda: _connect_tcp(
            arguments.callback_host, arguments.callback_port
        ),
    }
    probes = [
        _probe(name, probe_operations[name])
        for name in required_probes(arguments.role)
    ]

    authorized_pass = all(item["outcome"] == "PASS" for item in authorized)
    probes_pass = all(item["outcome"] == "DENIED" for item in probes)
    status = "PASS" if authorized_pass and probes_pass else "FAIL"
    report = {
        "schema": REPORT_SCHEMA,
        "role": arguments.role,
        "nonce": arguments.nonce,
        "pid": os.getpid(),
        "status": status,
        "authorized_access": authorized,
        "required_probes": list(required_probes(arguments.role)),
        "probes": probes,
    }
    sys.stdout.write(json.dumps(report, sort_keys=True, separators=(",", ":")))
    sys.stdout.write("\n")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
