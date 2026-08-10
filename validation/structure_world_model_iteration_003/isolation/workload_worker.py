#!/usr/bin/env python3
"""Trusted wrapper for one ITER-003 G2 product workload.

This process is deliberately separate from :mod:`probe_worker`.  Product code
therefore cannot alter or forge the denial-probe report used as OS-isolation
evidence.  The outer harness independently verifies the closed output tree;
this worker report is only workload execution evidence.
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
from typing import Sequence


REPORT_SCHEMA = "iteration-003-g2-isolation-workload-report@1"
AUDIT_SCHEMA = "iteration-003-g2-normal-workload-operation-audit@1"
PROHIBITED_COUNTERS = (
    "source_operations",
    "git_operations",
    "evidence_payload_reads",
    "authority_database_operations",
    "evidence_store_operations",
    "other_role_operations",
    "out_of_allowlist_file_operations",
    "network_operations",
    "process_operations",
)


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


def _safe_relative_file(root: Path, value: str, label: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or not relative.parts or relative == Path("."):
        raise ValueError(f"{label} must be a non-empty relative path")
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"{label} is not canonical")
    candidate = root.joinpath(relative)
    parent = candidate.parent.resolve(strict=True)
    if not _is_within(parent, root):
        raise ValueError(f"{label} escapes the output root")
    return candidate


def _exception_payload(exc: Exception) -> dict[str, object]:
    payload: dict[str, object] = {
        "type": type(exc).__name__,
        "message": str(exc)[:500],
    }
    error_number = getattr(exc, "errno", None)
    if isinstance(error_number, int):
        payload["errno"] = error_number
    return payload


def _decode_workload(value: str) -> dict[str, object]:
    try:
        decoded = base64.b64decode(value.encode("ascii"), validate=True)
        payload = json.loads(decoded.decode("utf-8"))
    except (ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("workload specification is not canonical base64 JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("workload specification must be an object")
    return payload


def _decode_audit_policy(value: str) -> dict[str, object]:
    payload = _decode_workload(value)
    expected = {
        "allowed_read_roots",
        "allowed_read_files",
        "allowed_write_roots",
        "allowed_write_files",
        "forbidden_categories",
    }
    if set(payload) != expected:
        raise ValueError("workload audit policy keys are not closed")
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
            raise ValueError(f"workload audit policy {key} is invalid")
    categories = payload["forbidden_categories"]
    expected_categories = set(PROHIBITED_COUNTERS) - {
        "out_of_allowlist_file_operations",
        "network_operations",
        "process_operations",
    }
    if not isinstance(categories, dict) or set(categories) != expected_categories:
        raise ValueError("workload audit forbidden categories are not closed")
    if any(
        not isinstance(values, list)
        or any(not isinstance(item, str) or not Path(item).is_absolute() for item in values)
        for values in categories.values()
    ):
        raise ValueError("workload audit forbidden category paths are invalid")
    return payload


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


def _path_matches(path: Path, candidate: str) -> bool:
    expected = Path(candidate)
    return path == expected or _is_within(path, expected)


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

    def __init__(self, policy: dict[str, object]) -> None:
        self.policy = policy
        self.counts = {name: 0 for name in PROHIBITED_COUNTERS}
        self.audited_event_count = 0
        self.authorized_file_operation_count = 0
        self.violations: list[dict[str, object]] = []

    def _record_violation(self, event: str, path: Path | None) -> None:
        if len(self.violations) < 100:
            item: dict[str, object] = {"event": event}
            if path is not None:
                item["path"] = str(path)
            self.violations.append(item)

    def _file_access(self, event: str, arguments: tuple[object, ...]) -> None:
        path = _absolute_lexical_path(arguments[0] if arguments else None)
        if path is None:
            self.counts["out_of_allowlist_file_operations"] += 1
            self._record_violation(event, None)
            return
        write = event in self._WRITE_EVENTS
        if event == "open":
            mode = arguments[1] if len(arguments) > 1 else None
            flags = arguments[2] if len(arguments) > 2 else 0
            write = (
                isinstance(mode, str)
                and any(character in mode for character in "wax+")
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
        allowed = any(
            _path_matches(path, item) for item in self.policy[roots_key]
        ) or str(path) in self.policy[files_key]
        if allowed:
            self.authorized_file_operation_count += 1
        else:
            self.counts["out_of_allowlist_file_operations"] += 1
            self._record_violation(event, path)
        for category, targets in self.policy["forbidden_categories"].items():
            if any(_path_matches(path, item) for item in targets):
                self.counts[category] += 1
                self._record_violation(event, path)

    def hook(self, event: str, arguments: tuple[object, ...]) -> None:
        try:
            if event == "sqlite3.connect":
                self.audited_event_count += 1
                self._file_access(event, arguments)
                return
            if event == "open" or event in self._READ_EVENTS or event in self._WRITE_EVENTS:
                self.audited_event_count += 1
                if event in self._MULTI_PATH_EVENTS:
                    for path_argument in arguments[:2]:
                        self._file_access(event, (path_argument,))
                else:
                    self._file_access(event, arguments)
                return
            if event.startswith("socket."):
                self.audited_event_count += 1
                self.counts["network_operations"] += 1
                self._record_violation(event, None)
                return
            if (
                event == "subprocess.Popen"
                or event in {"os.system", "os.fork", "os.forkpty", "pty.spawn"}
                or event.startswith("os.exec")
                or event.startswith("os.posix_spawn")
            ):
                self.audited_event_count += 1
                self.counts["process_operations"] += 1
                self._record_violation(event, None)
        except Exception:
            self.counts["out_of_allowlist_file_operations"] += 1
            self._record_violation("AUDIT_CLASSIFICATION_ERROR", None)

    def payload(self) -> dict[str, object]:
        passed = all(self.counts[name] == 0 for name in PROHIBITED_COUNTERS)
        return {
            "schema": AUDIT_SCHEMA,
            "status": "PASS" if passed else "FAIL",
            "prohibited_counts": dict(self.counts),
            "audited_event_count": self.audited_event_count,
            "authorized_file_operation_count": self.authorized_file_operation_count,
            "violations": list(self.violations),
        }


def _write_new(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError(errno.EIO, "zero-byte workload output write")
            view = view[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    metadata = path.lstat()
    if (
        not stat.S_ISREG(metadata.st_mode)
        or path.is_symlink()
        or metadata.st_nlink != 1
    ):
        raise RuntimeError("workload stdout output is not a unique regular file")


def _execute_workload(
    specification: dict[str, object],
    *,
    package_root: Path,
    output_root: Path,
    role: str,
    audit_policy: dict[str, object],
) -> dict[str, object]:
    expected_keys = {"entrypoint", "argv", "stdout_output", "expected_outputs"}
    if set(specification) != expected_keys:
        return {
            "status": "FAIL",
            "reason": "WORKLOAD_SCHEMA_INVALID",
            "keys": sorted(specification),
        }
    entrypoint_value = specification["entrypoint"]
    argv_value = specification["argv"]
    stdout_value = specification["stdout_output"]
    outputs_value = specification["expected_outputs"]
    if (
        not isinstance(entrypoint_value, str)
        or not isinstance(argv_value, list)
        or any(not isinstance(item, str) for item in argv_value)
        or not isinstance(stdout_value, str)
        or not isinstance(outputs_value, list)
        or not outputs_value
        or any(not isinstance(item, str) for item in outputs_value)
    ):
        return {"status": "FAIL", "reason": "WORKLOAD_TYPES_INVALID"}

    try:
        entrypoint = _canonical_existing_file(
            str(package_root / entrypoint_value),
            package_root,
            "workload entrypoint",
        )
        stdout_path = _safe_relative_file(
            output_root, stdout_value, "workload stdout output"
        )
        expected_paths = tuple(
            _safe_relative_file(output_root, item, "expected workload output")
            for item in outputs_value
        )
        if stdout_path not in expected_paths:
            raise ValueError("stdout output must be one of the expected outputs")
        if len(set(expected_paths)) != len(expected_paths):
            raise ValueError("expected workload outputs contain duplicates")
    except (OSError, ValueError) as exc:
        return {
            "status": "FAIL",
            "reason": "WORKLOAD_PATH_INVALID",
            "exception": _exception_payload(exc),
        }

    stdout_buffer = StringIO()
    stderr_buffer = StringIO()
    old_argv = sys.argv
    old_path = list(sys.path)
    exit_code = 0
    failure: Exception | None = None
    operation_audit = _OperationAudit(audit_policy)
    sys.addaudithook(operation_audit.hook)
    try:
        sys.argv = [str(entrypoint), *argv_value]
        sys.path.insert(0, str(package_root))
        os.environ["ITER003_G2_ISOLATION_ROLE"] = role
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            runpy.run_path(str(entrypoint), run_name="__main__")
    except SystemExit as exc:
        if exc.code not in {None, 0}:
            exit_code = exc.code if isinstance(exc.code, int) else 1
    except Exception as exc:
        exit_code = 1
        failure = exc
    finally:
        sys.argv = old_argv
        sys.path[:] = old_path

    stdout_bytes = stdout_buffer.getvalue().encode("utf-8")
    stderr_bytes = stderr_buffer.getvalue().encode("utf-8")
    if exit_code == 0:
        try:
            _write_new(stdout_path, stdout_bytes)
        except Exception as exc:
            exit_code = 1
            failure = exc

    outputs: list[dict[str, object]] = []
    if exit_code == 0:
        for path in expected_paths:
            try:
                resolved = path.resolve(strict=True)
                metadata = path.lstat()
                if (
                    resolved != path
                    or not stat.S_ISREG(metadata.st_mode)
                    or path.is_symlink()
                    or metadata.st_nlink != 1
                ):
                    raise ValueError("expected output is not a unique regular file")
                outputs.append(
                    {
                        "path": str(path.relative_to(output_root)),
                        "digest": _sha256_file(path),
                        "size": metadata.st_size,
                    }
                )
            except Exception as exc:
                exit_code = 1
                failure = exc
                break

    result: dict[str, object] = {
        "status": "PASS" if exit_code == 0 else "FAIL",
        "entrypoint": str(entrypoint.relative_to(package_root)),
        "exit_code": exit_code,
        "stdout_digest": "sha256:" + sha256(stdout_bytes).hexdigest(),
        "stderr_digest": "sha256:" + sha256(stderr_bytes).hexdigest(),
        "outputs": outputs,
        "operation_audit": operation_audit.payload(),
    }
    if result["operation_audit"]["status"] != "PASS":
        result["status"] = "FAIL"
        if result["exit_code"] == 0:
            result["exit_code"] = 1
    if failure is not None:
        result["exception"] = _exception_payload(failure)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--role", choices=("answer", "projector"), required=True)
    parser.add_argument("--nonce", required=True)
    parser.add_argument("--package-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--workload-spec-b64", required=True)
    parser.add_argument("--audit-policy-b64", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    package_root = Path(arguments.package_root).resolve(strict=True)
    output_root = Path(arguments.output_root).resolve(strict=True)
    workload = _execute_workload(
        _decode_workload(arguments.workload_spec_b64),
        package_root=package_root,
        output_root=output_root,
        role=arguments.role,
        audit_policy=_decode_audit_policy(arguments.audit_policy_b64),
    )
    status = "PASS" if workload["status"] == "PASS" else "FAIL"
    report = {
        "schema": REPORT_SCHEMA,
        "role": arguments.role,
        "nonce": arguments.nonce,
        "pid": os.getpid(),
        "status": status,
        "workload": workload,
    }
    sys.stdout.write(json.dumps(report, sort_keys=True, separators=(",", ":")))
    sys.stdout.write("\n")
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
