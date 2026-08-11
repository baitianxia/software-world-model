#!/usr/bin/env python3
"""Trusted wrapper for one sandboxed ITER-003 G3b role workload.

The wrapper is staged beside, but remains separate from, the product
entrypoint.  It installs a process audit hook before loading product code and
records only closed counters/digests.  Seatbelt is the enforcement boundary;
this report proves what the normal workload attempted inside that boundary.
"""

from __future__ import annotations

import argparse
import base64
from contextlib import redirect_stderr, redirect_stdout
import errno
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import runpy
import stat
import sys
from typing import Mapping, Sequence


REPORT_SCHEMA = "swm.iter-003.g3b-role-workload-report@1"
AUDIT_SCHEMA = "swm.iter-003.g3b-normal-operation-audit@1"
ROLES = ("answer", "gateway", "projector")
PROHIBITED_COUNTERS = (
    "source_operations",
    "git_operations",
    "evidence_payload_reads",
    "authority_database_operations",
    "evidence_store_operations",
    "other_role_operations",
    "product_oracle_operations",
    "baseline_result_operations",
    "out_of_allowlist_file_operations",
    "out_of_allowlist_network_operations",
    "dns_operations",
    "process_operations",
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=ROLES, required=True)
    parser.add_argument("--nonce", required=True)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--entrypoint", required=True)
    parser.add_argument("--argv-base64", required=True)
    parser.add_argument("--audit-policy-base64", required=True)
    parser.add_argument("--report-output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    package_root = _canonical_directory(arguments.package_root, "package root")
    output_root = _canonical_directory(arguments.output_root, "output root")
    entrypoint = _entrypoint(package_root, arguments.entrypoint)
    workload_argv = _decode_string_array(arguments.argv_base64, "workload argv")
    policy = _decode_policy(arguments.audit_policy_base64)
    report_path = _future_output(
        output_root, arguments.report_output, "role report"
    )

    audit = _OperationAudit(policy)
    sys.addaudithook(audit.hook)
    stdout_buffer = StringIO()
    stderr_buffer = StringIO()
    old_argv = sys.argv
    old_path = list(sys.path)
    exit_code = 0
    failure: BaseException | None = None
    try:
        sys.argv = [str(entrypoint), *workload_argv]
        sys.path.insert(0, str(package_root))
        os.environ["ITER003_G3B_ROLE"] = arguments.role
        audit.active = True
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            runpy.run_path(str(entrypoint), run_name="__main__")
    except SystemExit as exc:
        if exc.code not in {None, 0}:
            exit_code = exc.code if isinstance(exc.code, int) else 1
    except BaseException as exc:  # keep the wrapper alive to seal failure evidence
        exit_code = 1
        failure = exc
    finally:
        audit.active = False
        sys.argv = old_argv
        sys.path[:] = old_path

    stdout_bytes = stdout_buffer.getvalue().encode("utf-8")
    stderr_bytes = stderr_buffer.getvalue().encode("utf-8")
    audit_payload = audit.payload()
    status = (
        "PASS"
        if exit_code == 0 and audit_payload["status"] == "PASS"
        else "FAIL"
    )
    report: dict[str, object] = {
        "schema": REPORT_SCHEMA,
        "role": arguments.role,
        "nonce": _closed_text(arguments.nonce, "nonce"),
        "pid": os.getpid(),
        "status": status,
        "entrypoint": str(entrypoint.relative_to(package_root)),
        "exit_code": exit_code,
        "stdout_digest": _bytes_digest(stdout_bytes),
        "stderr_digest": _bytes_digest(stderr_bytes),
        "stdout_size": len(stdout_bytes),
        "stderr_size": len(stderr_bytes),
        "operation_audit": audit_payload,
    }
    if failure is not None:
        report["failure"] = {
            "type": type(failure).__name__,
            "errno": (
                failure.errno
                if isinstance(getattr(failure, "errno", None), int)
                else None
            ),
        }
    _write_new(report_path, _canonical_json_bytes(report))
    sys.stdout.write(_canonical_json_bytes(report).decode("utf-8"))
    sys.stdout.write("\n")
    return 0 if status == "PASS" else 2


class _OperationAudit:
    _WRITE_EVENTS = {
        "os.remove",
        "os.rename",
        "os.renames",
        "os.rmdir",
        "os.mkdir",
        "os.link",
        "os.symlink",
        "os.truncate",
        "os.chmod",
        "os.chown",
        "os.utime",
    }
    _READ_EVENTS = {"os.listdir", "os.scandir", "os.chdir"}
    _MULTI_PATH_EVENTS = {"os.rename", "os.renames", "os.link", "os.symlink"}

    def __init__(self, policy: Mapping[str, object]) -> None:
        self.policy = policy
        self.active = False
        self.prohibited = {name: 0 for name in PROHIBITED_COUNTERS}
        self.allowed_file_operations = 0
        self.allowed_network_operations = {
            "unix_connect": 0,
            "unix_bind": 0,
            "provider_connect": 0,
        }
        self.socket_event_count = 0
        self.audited_event_count = 0
        self.violations: list[dict[str, object]] = []

    def hook(self, event: str, arguments: tuple[object, ...]) -> None:
        if not self.active:
            return
        try:
            if event == "sqlite3.connect":
                self.audited_event_count += 1
                self._file_event(event, arguments)
            elif event == "open" or event in self._READ_EVENTS or event in self._WRITE_EVENTS:
                self.audited_event_count += 1
                if event in self._MULTI_PATH_EVENTS:
                    for value in arguments[:2]:
                        self._file_event(event, (value,))
                else:
                    self._file_event(event, arguments)
            elif event.startswith("socket."):
                self.audited_event_count += 1
                self.socket_event_count += 1
                self._network_event(event, arguments)
            elif (
                event == "subprocess.Popen"
                or event in {"os.system", "os.fork", "os.forkpty", "pty.spawn"}
                or event.startswith("os.exec")
                or event.startswith("os.posix_spawn")
            ):
                self.audited_event_count += 1
                self.prohibited["process_operations"] += 1
                self._violation("process_operations", event)
        except Exception:
            self.prohibited["out_of_allowlist_file_operations"] += 1
            self._violation("AUDIT_CLASSIFICATION_ERROR", event)

    def _file_event(self, event: str, arguments: tuple[object, ...]) -> None:
        path = _absolute_lexical_path(arguments[0] if arguments else None)
        if path is None:
            self.prohibited["out_of_allowlist_file_operations"] += 1
            self._violation("out_of_allowlist_file_operations", event)
            return
        write = event in self._WRITE_EVENTS
        if event == "open":
            mode = arguments[1] if len(arguments) > 1 else None
            flags = arguments[2] if len(arguments) > 2 else 0
            write = (
                isinstance(mode, str) and any(item in mode for item in "wax+")
            ) or (
                isinstance(flags, int)
                and bool(
                    flags
                    & (
                        os.O_WRONLY
                        | os.O_RDWR
                        | os.O_CREAT
                        | os.O_TRUNC
                        | os.O_APPEND
                    )
                )
            )
        roots_key = "allowed_write_roots" if write else "allowed_read_roots"
        files_key = "allowed_write_files" if write else "allowed_read_files"
        if any(_path_matches(path, item) for item in self.policy[roots_key]) or str(path) in self.policy[files_key]:
            self.allowed_file_operations += 1
        else:
            self.prohibited["out_of_allowlist_file_operations"] += 1
            self._violation("out_of_allowlist_file_operations", event)
        for category, targets in self.policy["forbidden_categories"].items():
            if any(_path_matches(path, item) for item in targets):
                self.prohibited[category] += 1
                self._violation(category, event)

    def _network_event(self, event: str, arguments: tuple[object, ...]) -> None:
        if event == "socket.getaddrinfo":
            self.prohibited["dns_operations"] += 1
            self._violation("dns_operations", event)
            return
        if event not in {"socket.connect", "socket.bind"}:
            return
        address = arguments[1] if len(arguments) > 1 else None
        network = self.policy["allowed_network"]
        if isinstance(address, str):
            expected = network[
                "unix_connect" if event == "socket.connect" else "unix_bind"
            ]
            counter = "unix_connect" if event == "socket.connect" else "unix_bind"
            if address in expected:
                self.allowed_network_operations[counter] += 1
                return
        elif event == "socket.connect" and isinstance(address, tuple) and len(address) >= 2:
            endpoint = [str(address[0]), int(address[1])]
            if endpoint in network["provider_connect"]:
                self.allowed_network_operations["provider_connect"] += 1
                return
        self.prohibited["out_of_allowlist_network_operations"] += 1
        self._violation("out_of_allowlist_network_operations", event)

    def _violation(self, category: str, event: str) -> None:
        if len(self.violations) < 100:
            self.violations.append({"category": category, "event": event})

    def payload(self) -> dict[str, object]:
        status = "PASS" if all(value == 0 for value in self.prohibited.values()) else "FAIL"
        return {
            "schema": AUDIT_SCHEMA,
            "status": status,
            "prohibited_counts": dict(self.prohibited),
            "allowed_file_operation_count": self.allowed_file_operations,
            "allowed_network_operations": dict(self.allowed_network_operations),
            "socket_event_count": self.socket_event_count,
            "audited_event_count": self.audited_event_count,
            "violations": list(self.violations),
        }


def _decode_policy(value: str) -> Mapping[str, object]:
    payload = _decode_json_base64(value, "audit policy")
    expected = {
        "allowed_read_roots",
        "allowed_read_files",
        "allowed_write_roots",
        "allowed_write_files",
        "allowed_network",
        "forbidden_categories",
    }
    if not isinstance(payload, dict) or set(payload) != expected:
        raise ValueError("audit policy keys are not closed")
    for key in (
        "allowed_read_roots",
        "allowed_read_files",
        "allowed_write_roots",
        "allowed_write_files",
    ):
        values = payload[key]
        if not isinstance(values, list) or any(
            not isinstance(item, str) or not Path(item).is_absolute()
            for item in values
        ):
            raise ValueError(f"audit policy {key} is invalid")
    categories = payload["forbidden_categories"]
    expected_categories = set(PROHIBITED_COUNTERS) - {
        "out_of_allowlist_file_operations",
        "out_of_allowlist_network_operations",
        "dns_operations",
        "process_operations",
    }
    if not isinstance(categories, dict) or set(categories) != expected_categories:
        raise ValueError("audit policy forbidden categories are not closed")
    if any(
        not isinstance(values, list)
        or any(not isinstance(item, str) or not Path(item).is_absolute() for item in values)
        for values in categories.values()
    ):
        raise ValueError("audit policy forbidden category paths are invalid")
    network = payload["allowed_network"]
    if not isinstance(network, dict) or set(network) != {
        "unix_connect",
        "unix_bind",
        "provider_connect",
    }:
        raise ValueError("audit policy allowed network keys are not closed")
    if any(
        not isinstance(network[key], list)
        for key in ("unix_connect", "unix_bind", "provider_connect")
    ):
        raise ValueError("audit policy allowed network values are invalid")
    return payload


def _decode_string_array(value: str, label: str) -> list[str]:
    payload = _decode_json_base64(value, label)
    if not isinstance(payload, list) or any(not isinstance(item, str) for item in payload):
        raise ValueError(f"{label} must be a string array")
    return list(payload)


def _decode_json_base64(value: str, label: str) -> object:
    try:
        raw = base64.b64decode(value.encode("ascii"), validate=True)
        payload = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not canonical base64 JSON") from exc
    if _canonical_json_bytes(payload) != raw:
        raise ValueError(f"{label} JSON is not canonical")
    return payload


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _canonical_directory(value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=True) != path or not path.is_dir() or path.is_symlink():
        raise ValueError(f"{label} must be a canonical directory")
    return path


def _entrypoint(root: Path, value: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError("entrypoint must be a canonical relative path")
    path = root / relative
    if path.resolve(strict=True) != path or not path.is_file() or path.is_symlink():
        raise ValueError("entrypoint must be a canonical package file")
    return path


def _future_output(root: Path, value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise ValueError(f"{label} must be absolute and canonical")
    if path.parent.resolve(strict=True) != path.parent or not _is_within(path, root):
        raise ValueError(f"{label} escapes output root")
    return path


def _absolute_lexical_path(value: object) -> Path | None:
    if isinstance(value, bytes):
        try:
            text = os.fsdecode(value)
        except UnicodeError:
            return None
    elif isinstance(value, str):
        text = value
    else:
        return None
    path = Path(text)
    if not path.is_absolute():
        path = Path.cwd() / path
    return Path(os.path.abspath(path))


def _path_matches(path: Path, value: str) -> bool:
    target = Path(value)
    return path == target or _is_within(path, target)


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _write_new(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        remaining = memoryview(payload)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError(errno.EIO, "zero-byte report write")
            remaining = remaining[written:]
        os.fsync(descriptor)
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError("role report is not a regular file")
    finally:
        os.close(descriptor)


def _closed_text(value: str, label: str) -> str:
    if not value or len(value) > 200 or any(ord(character) < 32 for character in value):
        raise ValueError(f"{label} is invalid")
    return value


def _bytes_digest(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
