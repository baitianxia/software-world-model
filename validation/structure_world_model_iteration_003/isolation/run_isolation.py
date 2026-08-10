#!/usr/bin/env python3
"""Run the ITER-003 G2 macOS process-isolation proof.

This harness has two deliberately different modes:

``plan`` validates a closed staging configuration and emits auditable command
templates.  It never claims that an operating-system boundary ran.

``run`` requires Apple's fixed ``/usr/bin/sandbox-exec`` executable, performs
outside-the-sandbox reachability preflights, then launches the answer worker
and Citation Projector as two separate default-deny processes.  Passing this
harness proves only the OS file/network/process boundary.  It can never mark
the broader V-007 gate complete; product-query coverage is evaluated by the
iteration gate runner that consumes this evidence.
"""

from __future__ import annotations

import argparse
import base64
from contextlib import ExitStack
from dataclasses import dataclass
from hashlib import sha256
import ipaddress
import json
import os
from pathlib import Path
import platform
import secrets
import shutil
import socket
import sqlite3
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import quote

from validation.structure_world_model_iteration_003.isolation import probe_worker
from validation.structure_world_model_iteration_003.isolation import workload_worker


CONFIG_SCHEMA = "iteration-003-g2-isolation-config@1"
PLAN_SCHEMA = "iteration-003-g2-isolation-plan@1"
EVIDENCE_SCHEMA = "iteration-003-g2-isolation-evidence@1"
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
TRUE_EXECUTABLE = Path("/usr/bin/true")
GIT_EXECUTABLE = Path("/usr/bin/git")
HERE = Path(__file__).resolve(strict=True).parent
ANSWER_PROFILE = HERE / "answer.sb"
PROJECTOR_PROFILE = HERE / "projector.sb"
WORKER_SOURCE = HERE / "probe_worker.py"
WORKLOAD_WORKER_SOURCE = HERE / "workload_worker.py"
STAGED_PROBE_WORKER = Path(".iter003-g2-isolation/probe_worker.py")
STAGED_WORKLOAD_WORKER = Path(".iter003-g2-isolation/workload_worker.py")
CLAIM_SCOPE = "OS_FILE_NETWORK_PROCESS_ISOLATION_ONLY"
OUTER_PROCESS_PROBES = (
    "python_control",
    "process_fork",
    "git_process_exec",
    "subprocess_exec",
)
ANCESTOR_PARAMETER_COUNT = 40
SANDBOXED_PYTHON_FLAGS = ("-I", "-S", "-B")
PYTHON_RUNTIME_DEPENDENCY_PARAMETER_COUNT = 3
_XPKG_RUNTIME_DEPENDENCY_ALIASES = (
    Path("openssl.org/v1"),
    Path("sqlite.org/v3"),
    Path("zlib.net/v1"),
)


class ConfigurationError(ValueError):
    """The closed isolation configuration or staged inputs are unsafe."""


@dataclass(frozen=True)
class Endpoint:
    host: str
    port: int


@dataclass(frozen=True)
class Workload:
    entrypoint: str
    argv: tuple[str, ...]
    stdout_output: str
    expected_outputs: tuple[str, ...]

    def payload(self) -> dict[str, object]:
        return {
            "entrypoint": self.entrypoint,
            "argv": list(self.argv),
            "stdout_output": self.stdout_output,
            "expected_outputs": list(self.expected_outputs),
        }


@dataclass(frozen=True)
class AnswerRole:
    package_root: Path
    bundle_root: Path
    output_root: Path
    package_canary: Path
    bundle_canary: Path
    sealed_result: Path
    workload: Workload


@dataclass(frozen=True)
class ProjectorRole:
    package_root: Path
    sealed_result: Path
    store_root: Path
    store_allowlist: tuple[str, ...]
    output_root: Path
    package_canary: Path
    store_canary: Path
    workload: Workload


@dataclass(frozen=True)
class ForbiddenTargets:
    file: Path
    sqlite: Path
    git_root: Path
    git_marker: Path


@dataclass(frozen=True)
class RuntimeDependencyCapability:
    alias: Path
    root: Path


@dataclass(frozen=True)
class IsolationConfig:
    stage_root: Path
    python_executable: Path
    python_runtime: Path
    python_runtime_dependencies: tuple[RuntimeDependencyCapability, ...]
    source_remote: Endpoint
    public_endpoint: Endpoint
    dns_host: str
    forbidden: ForbiddenTargets
    answer: AnswerRole
    projector: ProjectorRole
    timeout_seconds: float


def _require_exact_keys(
    value: object, expected: set[str], label: str
) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{label} must be an object")
    observed = set(value)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise ConfigurationError(
            f"{label} keys are not closed (missing={missing}, extra={extra})"
        )
    return value


def _string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigurationError(f"{label} must be a non-empty string")
    return value


def _canonical_directory(value: object, label: str) -> Path:
    raw = Path(_string(value, label))
    if not raw.is_absolute():
        raise ConfigurationError(f"{label} must be absolute")
    try:
        resolved = raw.resolve(strict=True)
    except OSError as exc:
        raise ConfigurationError(f"{label} does not exist: {raw}") from exc
    if raw != resolved or not resolved.is_dir() or resolved.is_symlink():
        raise ConfigurationError(f"{label} must be a canonical non-symlink directory")
    return resolved


def _canonical_file(value: object, label: str) -> Path:
    raw = Path(_string(value, label))
    if not raw.is_absolute():
        raise ConfigurationError(f"{label} must be absolute")
    try:
        resolved = raw.resolve(strict=True)
    except OSError as exc:
        raise ConfigurationError(f"{label} does not exist: {raw}") from exc
    if raw != resolved or not resolved.is_file() or resolved.is_symlink():
        raise ConfigurationError(f"{label} must be a canonical regular file")
    return resolved


def _canonical_future_file(value: object, label: str) -> Path:
    raw = Path(_string(value, label))
    if not raw.is_absolute():
        raise ConfigurationError(f"{label} must be absolute")
    resolved = raw.resolve(strict=False)
    if raw != resolved:
        raise ConfigurationError(f"{label} must be canonical and contain no symlink")
    try:
        parent = raw.parent.resolve(strict=True)
    except OSError as exc:
        raise ConfigurationError(f"{label} parent does not exist") from exc
    if parent != raw.parent or not parent.is_dir() or parent.is_symlink():
        raise ConfigurationError(f"{label} parent must be canonical")
    if raw.exists() and (not raw.is_file() or raw.is_symlink()):
        raise ConfigurationError(f"{label} must be a regular file when present")
    return raw


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _require_within(path: Path, root: Path, label: str) -> None:
    if not _is_within(path, root) or path == root:
        raise ConfigurationError(f"{label} must be below {root}")


def _paths_overlap(left: Path, right: Path) -> bool:
    return _is_within(left, right) or _is_within(right, left)


def _relative_path(value: object, label: str) -> str:
    text = _string(value, label)
    path = Path(text)
    if path.is_absolute() or path == Path(".") or not path.parts:
        raise ConfigurationError(f"{label} must be a non-empty relative path")
    if any(part in {"", ".", ".."} for part in path.parts):
        raise ConfigurationError(f"{label} must be canonical")
    normalized = path.as_posix()
    if normalized != text:
        raise ConfigurationError(f"{label} must use canonical POSIX separators")
    return normalized


def _endpoint(value: object, label: str, *, numeric_host: bool = False) -> Endpoint:
    mapping = _require_exact_keys(value, {"host", "port"}, label)
    host = _string(mapping["host"], f"{label}.host")
    port = mapping["port"]
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ConfigurationError(f"{label}.port must be an integer from 1 to 65535")
    if numeric_host:
        try:
            address = ipaddress.ip_address(host)
        except ValueError as exc:
            raise ConfigurationError(f"{label}.host must be a numeric IP address") from exc
        if not address.is_global:
            raise ConfigurationError(f"{label}.host must be a public IP address")
    return Endpoint(host=host, port=port)


def _dns_name(value: object) -> str:
    host = _string(value, "dns_host")
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return host
    raise ConfigurationError("dns_host must be a name, not a numeric IP address")


def _workload(value: object, label: str) -> Workload:
    if value is None:
        raise ConfigurationError(f"{label} is required for an executed G2 run")
    mapping = _require_exact_keys(
        value,
        {"entrypoint", "argv", "stdout_output", "expected_outputs"},
        label,
    )
    entrypoint = _relative_path(mapping["entrypoint"], f"{label}.entrypoint")
    stdout_output = _relative_path(
        mapping["stdout_output"], f"{label}.stdout_output"
    )
    argv_value = mapping["argv"]
    outputs_value = mapping["expected_outputs"]
    if not isinstance(argv_value, list) or any(
        not isinstance(item, str) for item in argv_value
    ):
        raise ConfigurationError(f"{label}.argv must be a list of strings")
    if not isinstance(outputs_value, list) or not outputs_value:
        raise ConfigurationError(f"{label}.expected_outputs must be non-empty")
    outputs = tuple(
        _relative_path(item, f"{label}.expected_outputs")
        for item in outputs_value
    )
    if len(set(outputs)) != len(outputs):
        raise ConfigurationError(f"{label}.expected_outputs contains duplicates")
    if stdout_output not in outputs:
        raise ConfigurationError(
            f"{label}.stdout_output must be one of expected_outputs"
        )
    return Workload(entrypoint, tuple(argv_value), stdout_output, outputs)


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return "sha256:" + sha256(value).hexdigest()


def _tree_inventory(
    root: Path,
) -> tuple[list[dict[str, object]], tuple[str, ...]]:
    """Return regular files and directories while rejecting filesystem aliases."""
    result: list[dict[str, object]] = []
    directory_paths: list[str] = []
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in sorted(directories):
            child = current_path / name
            mode = child.lstat().st_mode
            if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
                raise ConfigurationError(f"staged tree contains unsafe directory: {child}")
            resolved = child.resolve(strict=True)
            if resolved != child or not _is_within(resolved, root):
                raise ConfigurationError(f"staged tree contains filesystem alias: {child}")
            directory_paths.append(child.relative_to(root).as_posix())
        for name in sorted(files):
            child = current_path / name
            metadata = child.lstat()
            if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                raise ConfigurationError(f"staged tree contains non-regular file: {child}")
            if metadata.st_nlink != 1:
                raise ConfigurationError(f"staged tree contains hard-linked file: {child}")
            resolved = child.resolve(strict=True)
            if resolved != child or not _is_within(resolved, root):
                raise ConfigurationError(f"staged tree contains filesystem alias: {child}")
            result.append(
                {
                    "path": child.relative_to(root).as_posix(),
                    "size": metadata.st_size,
                    "digest": _sha256_file(child),
                }
            )
    result.sort(key=lambda item: str(item["path"]))
    return result, tuple(sorted(directory_paths))


def _tree_manifest(root: Path) -> list[dict[str, object]]:
    """Return the regular-file portion of a validated physical tree inventory."""
    manifest, _ = _tree_inventory(root)
    return manifest


def _runtime_dependency_manifest(root: Path) -> list[dict[str, object]]:
    """Bind a read-only runtime tree, including its internal aliases."""

    entries: list[dict[str, object]] = []
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        for name in sorted(tuple(directories)):
            child = current_path / name
            metadata = child.lstat()
            relative = child.relative_to(root).as_posix()
            if stat.S_ISLNK(metadata.st_mode):
                directories.remove(name)
                resolved = child.resolve(strict=True)
                if not _is_within(resolved, root):
                    raise ConfigurationError(
                        f"runtime dependency alias escapes its root: {child}"
                    )
                entries.append(
                    {
                        "path": relative,
                        "kind": "symlink",
                        "target": os.readlink(child),
                    }
                )
            elif stat.S_ISDIR(metadata.st_mode):
                entries.append({"path": relative, "kind": "directory"})
            else:
                raise ConfigurationError(
                    f"runtime dependency has unsafe directory entry: {child}"
                )
        for name in sorted(files):
            child = current_path / name
            metadata = child.lstat()
            relative = child.relative_to(root).as_posix()
            if stat.S_ISLNK(metadata.st_mode):
                resolved = child.resolve(strict=True)
                if not _is_within(resolved, root) or not resolved.is_file():
                    raise ConfigurationError(
                        f"runtime dependency alias escapes its root: {child}"
                    )
                entries.append(
                    {
                        "path": relative,
                        "kind": "symlink",
                        "target": os.readlink(child),
                    }
                )
            elif stat.S_ISREG(metadata.st_mode):
                entries.append(
                    {
                        "path": relative,
                        "kind": "file",
                        "size": metadata.st_size,
                        "link_count": metadata.st_nlink,
                        "digest": _sha256_file(child),
                    }
                )
            else:
                raise ConfigurationError(
                    f"runtime dependency has unsafe file entry: {child}"
                )
    entries.sort(key=lambda item: (str(item["path"]), str(item["kind"])))
    return entries


def _manifest_paths(manifest: Iterable[Mapping[str, object]]) -> tuple[str, ...]:
    return tuple(str(item["path"]) for item in manifest)


def _implied_directory_paths(file_paths: Iterable[str]) -> tuple[str, ...]:
    directories: set[str] = set()
    for value in file_paths:
        parent = Path(value).parent
        while parent != Path("."):
            directories.add(parent.as_posix())
            parent = parent.parent
    return tuple(sorted(directories))


def _validate_initial_output(
    role: str, output: Path, expected_outputs: Iterable[str]
) -> None:
    inventory, observed_directories = _tree_inventory(output)
    if inventory:
        raise ConfigurationError(f"{role} output root must be empty before workload run")
    if observed_directories != _implied_directory_paths(expected_outputs):
        raise ConfigurationError(
            f"{role} output root contains undeclared directories before workload run"
        )


def _python_runtime_read_root() -> Path:
    """Return the exact base prefix of the active interpreter."""

    return Path(sys.base_prefix).resolve(strict=True)


def _python_runtime_dependency_capabilities(
    python_runtime: Path,
) -> tuple[RuntimeDependencyCapability, ...]:
    """Resolve only the xpkg siblings loaded by the isolated workers.

    The workers import ``base64``/``hashlib`` and the package's eager SQLite
    adapter.  Their xpkg builds load zlib, OpenSSL and SQLite through stable
    version aliases.  Granting the package-manager root would also expose
    unrelated tools, so each alias is resolved to one canonical version root.
    An xpkg layout change fails closed instead of widening the capability.
    """

    package_manager_root = python_runtime.parent.parent
    executable = Path(sys.executable).resolve(strict=True)
    if (
        package_manager_root.name != "pkgs"
        or python_runtime.parent.name != "python.org"
        or not _is_within(executable, python_runtime)
    ):
        return ()
    capabilities: list[RuntimeDependencyCapability] = []
    for relative_alias in _XPKG_RUNTIME_DEPENDENCY_ALIASES:
        alias = package_manager_root / relative_alias
        try:
            root = alias.resolve(strict=True)
        except OSError as exc:
            raise ConfigurationError(
                f"required Python runtime dependency is missing: {alias}"
            ) from exc
        family_root = alias.parent.resolve(strict=True)
        if (
            not alias.is_symlink()
            or not root.is_dir()
            or root.is_symlink()
            or not _is_within(root, family_root)
            or root == family_root
        ):
            raise ConfigurationError(
                f"Python runtime dependency alias is unsafe: {alias}"
            )
        capabilities.append(
            RuntimeDependencyCapability(alias=alias, root=root)
        )
    return tuple(capabilities)


def parse_config(value: object) -> IsolationConfig:
    top = _require_exact_keys(
        value,
        {
            "schema",
            "stage_root",
            "python_executable",
            "source_remote",
            "public_endpoint",
            "dns_host",
            "forbidden",
            "answer",
            "projector",
            "timeout_seconds",
        },
        "configuration",
    )
    if top["schema"] != CONFIG_SCHEMA:
        raise ConfigurationError(f"configuration.schema must equal {CONFIG_SCHEMA}")
    stage_root = _canonical_directory(top["stage_root"], "stage_root")
    python_executable = _canonical_file(
        top["python_executable"], "python_executable"
    )
    running_python = Path(sys.executable).resolve(strict=True)
    if python_executable != running_python:
        raise ConfigurationError(
            "python_executable must be the interpreter running this trusted harness"
        )
    python_runtime = _python_runtime_read_root()
    python_runtime_dependencies = _python_runtime_dependency_capabilities(
        python_runtime
    )
    timeout = top["timeout_seconds"]
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        raise ConfigurationError("timeout_seconds must be numeric")
    timeout = float(timeout)
    if not 1.0 <= timeout <= 300.0:
        raise ConfigurationError("timeout_seconds must be between 1 and 300")

    forbidden_map = _require_exact_keys(
        top["forbidden"], {"file", "sqlite", "git_root", "git_marker"}, "forbidden"
    )
    forbidden = ForbiddenTargets(
        file=_canonical_file(forbidden_map["file"], "forbidden.file"),
        sqlite=_canonical_file(forbidden_map["sqlite"], "forbidden.sqlite"),
        git_root=_canonical_directory(forbidden_map["git_root"], "forbidden.git_root"),
        git_marker=_canonical_file(forbidden_map["git_marker"], "forbidden.git_marker"),
    )
    _require_within(forbidden.git_marker, forbidden.git_root, "forbidden.git_marker")

    answer_map = _require_exact_keys(
        top["answer"],
        {
            "package_root",
            "bundle_root",
            "output_root",
            "package_canary",
            "bundle_canary",
            "sealed_result",
            "workload",
        },
        "answer",
    )
    answer_workload = _workload(answer_map["workload"], "answer.workload")
    answer = AnswerRole(
        package_root=_canonical_directory(answer_map["package_root"], "answer.package_root"),
        bundle_root=_canonical_directory(answer_map["bundle_root"], "answer.bundle_root"),
        output_root=_canonical_directory(answer_map["output_root"], "answer.output_root"),
        package_canary=_canonical_file(answer_map["package_canary"], "answer.package_canary"),
        bundle_canary=_canonical_file(answer_map["bundle_canary"], "answer.bundle_canary"),
        sealed_result=_canonical_future_file(answer_map["sealed_result"], "answer.sealed_result"),
        workload=answer_workload,
    )

    projector_map = _require_exact_keys(
        top["projector"],
        {
            "package_root",
            "sealed_result",
            "store_root",
            "store_allowlist",
            "output_root",
            "package_canary",
            "store_canary",
            "workload",
        },
        "projector",
    )
    allowlist_value = projector_map["store_allowlist"]
    if not isinstance(allowlist_value, list) or not allowlist_value:
        raise ConfigurationError("projector.store_allowlist must be non-empty")
    allowlist = tuple(
        _relative_path(item, "projector.store_allowlist") for item in allowlist_value
    )
    if len(set(allowlist)) != len(allowlist):
        raise ConfigurationError("projector.store_allowlist contains duplicates")
    projector = ProjectorRole(
        package_root=_canonical_directory(
            projector_map["package_root"], "projector.package_root"
        ),
        sealed_result=_canonical_future_file(
            projector_map["sealed_result"], "projector.sealed_result"
        ),
        store_root=_canonical_directory(projector_map["store_root"], "projector.store_root"),
        store_allowlist=allowlist,
        output_root=_canonical_directory(
            projector_map["output_root"], "projector.output_root"
        ),
        package_canary=_canonical_file(
            projector_map["package_canary"], "projector.package_canary"
        ),
        store_canary=_canonical_file(
            projector_map["store_canary"], "projector.store_canary"
        ),
        workload=_workload(projector_map["workload"], "projector.workload"),
    )

    role_roots = {
        "answer.package_root": answer.package_root,
        "answer.bundle_root": answer.bundle_root,
        "answer.output_root": answer.output_root,
        "projector.package_root": projector.package_root,
        "projector.store_root": projector.store_root,
        "projector.output_root": projector.output_root,
    }
    for label, root in role_roots.items():
        _require_within(root, stage_root, label)
    items = list(role_roots.items())
    for index, (left_label, left) in enumerate(items):
        for right_label, right in items[index + 1 :]:
            if _paths_overlap(left, right):
                raise ConfigurationError(f"role roots overlap: {left_label}, {right_label}")

    _require_within(answer.package_canary, answer.package_root, "answer.package_canary")
    _require_within(answer.bundle_canary, answer.bundle_root, "answer.bundle_canary")
    _require_within(answer.sealed_result, answer.output_root, "answer.sealed_result")
    _require_within(projector.store_canary, projector.store_root, "projector.store_canary")
    _require_within(projector.sealed_result, stage_root, "projector.sealed_result")
    if any(_is_within(projector.sealed_result, root) for root in role_roots.values()):
        raise ConfigurationError("projector.sealed_result must have its own staging path")
    if projector.sealed_result.exists():
        raise ConfigurationError("projector.sealed_result must not exist before one-way transfer")

    entrypoint = answer.package_root / answer.workload.entrypoint
    _canonical_file(str(entrypoint), "answer.workload.entrypoint")
    sealed_relative = answer.sealed_result.relative_to(answer.output_root).as_posix()
    if sealed_relative not in answer.workload.expected_outputs:
        raise ConfigurationError(
            "answer workload must declare sealed_result in expected_outputs"
        )
    _canonical_file(
        str(projector.package_root / projector.workload.entrypoint),
        "projector.workload.entrypoint",
    )

    for forbidden_label, forbidden_path in {
        "forbidden.file": forbidden.file,
        "forbidden.sqlite": forbidden.sqlite,
        "forbidden.git_root": forbidden.git_root,
        "forbidden.git_marker": forbidden.git_marker,
    }.items():
        for role_label, role_root in role_roots.items():
            if _is_within(forbidden_path, role_root):
                raise ConfigurationError(
                    f"{forbidden_label} is accidentally authorized by {role_label}"
                )
        if forbidden_path == projector.sealed_result:
            raise ConfigurationError(f"{forbidden_label} aliases projector.sealed_result")

    runtime_roots = (
        python_runtime,
        *(item.root for item in python_runtime_dependencies),
    )
    for runtime_root in runtime_roots:
        if _paths_overlap(runtime_root, stage_root):
            raise ConfigurationError(
                "Python runtime capability overlaps the staged role boundary"
            )
        for forbidden_path in (
            forbidden.file,
            forbidden.sqlite,
            forbidden.git_root,
            forbidden.git_marker,
        ):
            if _is_within(forbidden_path, runtime_root):
                raise ConfigurationError(
                    "forbidden target is inside a Python runtime capability"
                )

    package_manifest = _tree_manifest(answer.package_root)
    bundle_manifest = _tree_manifest(answer.bundle_root)
    projector_package_manifest = _tree_manifest(projector.package_root)
    store_manifest, store_directories = _tree_inventory(projector.store_root)
    if not package_manifest or not bundle_manifest or not projector_package_manifest:
        raise ConfigurationError("package and Bundle roots must not be empty")
    if (
        _manifest_paths(store_manifest) != tuple(sorted(allowlist))
        or store_directories != _implied_directory_paths(allowlist)
    ):
        raise ConfigurationError(
            "projector Store physical inventory must exactly equal store_allowlist"
        )
    store_canary_relative = projector.store_canary.relative_to(projector.store_root).as_posix()
    if store_canary_relative not in allowlist:
        raise ConfigurationError("projector.store_canary must be allowlisted")

    _validate_initial_output(
        "answer", answer.output_root, answer.workload.expected_outputs
    )
    _validate_initial_output(
        "projector", projector.output_root, projector.workload.expected_outputs
    )

    return IsolationConfig(
        stage_root=stage_root,
        python_executable=python_executable,
        python_runtime=python_runtime,
        python_runtime_dependencies=python_runtime_dependencies,
        source_remote=_endpoint(top["source_remote"], "source_remote"),
        public_endpoint=_endpoint(
            top["public_endpoint"], "public_endpoint", numeric_host=True
        ),
        dns_host=_dns_name(top["dns_host"]),
        forbidden=forbidden,
        answer=answer,
        projector=projector,
        timeout_seconds=timeout,
    )


def load_config(path: Path) -> IsolationConfig:
    config_path = _canonical_file(str(path.resolve(strict=True)), "config")
    try:
        value = json.loads(config_path.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigurationError("configuration is not valid UTF-8 JSON") from exc
    return parse_config(value)


def _profile_recursive_read_roots(
    config: IsolationConfig, role: str
) -> tuple[Path, ...]:
    role_config = config.answer if role == "answer" else config.projector
    roots = {
        config.python_runtime,
        *(item.root for item in config.python_runtime_dependencies),
        Path("/System/Library"),
        Path("/usr/lib"),
        Path("/private/var/db/dyld"),
        role_config.package_root,
        role_config.output_root,
    }
    if role == "answer":
        roots.add(config.answer.bundle_root)
    else:
        roots.add(config.projector.store_root)
    return tuple(sorted(roots, key=str))


def _profile_parameters(config: IsolationConfig, role: str) -> dict[str, str]:
    directory_roots = set(_profile_recursive_read_roots(config, role))
    directory_roots.add(config.python_executable.parent)
    directory_roots.update(
        item.alias for item in config.python_runtime_dependencies
    )
    if role == "projector":
        directory_roots.add(config.projector.sealed_result.parent)
    ancestors = sorted(
        {
            ancestor
            for root in directory_roots
            for ancestor in (root, *root.parents)
        },
        key=lambda item: (len(item.parts), str(item)),
    )
    if len(ancestors) > ANCESTOR_PARAMETER_COUNT:
        raise ConfigurationError("runtime directory ancestor set exceeds profile capacity")
    common = {
        "PYTHON_EXECUTABLE": str(config.python_executable),
        "PYTHON_RUNTIME": str(config.python_runtime),
        **{
            f"PYTHON_RUNTIME_DEPENDENCY_{index:02d}": str(
                config.python_runtime_dependencies[index].root
                if index < len(config.python_runtime_dependencies)
                else config.python_runtime
            )
            for index in range(PYTHON_RUNTIME_DEPENDENCY_PARAMETER_COUNT)
        },
        **{
            f"ANCESTOR_{index:02d}": str(
                ancestors[index] if index < len(ancestors) else Path("/")
            )
            for index in range(ANCESTOR_PARAMETER_COUNT)
        },
    }
    if role == "answer":
        return {
            **common,
            "PACKAGE_ROOT": str(config.answer.package_root),
            "BUNDLE_ROOT": str(config.answer.bundle_root),
            "OUTPUT_ROOT": str(config.answer.output_root),
        }
    return {
        **common,
        "PACKAGE_ROOT": str(config.projector.package_root),
        "SEALED_RESULT": str(config.projector.sealed_result),
        "STORE_ROOT": str(config.projector.store_root),
        "OUTPUT_ROOT": str(config.projector.output_root),
    }


def _profile_capability_evidence(
    config: IsolationConfig, role: str
) -> dict[str, object]:
    parameters = _profile_parameters(config, role)
    ancestors = [
        parameters[f"ANCESTOR_{index:02d}"]
        for index in range(ANCESTOR_PARAMETER_COUNT)
    ]
    role_config = config.answer if role == "answer" else config.projector
    return {
        "profile_parameters": parameters,
        "ancestor_literals": ancestors,
        "recursive_read_roots": [
            str(path) for path in _profile_recursive_read_roots(config, role)
        ],
        "recursive_executable_map_roots": [
            "/System/Library",
            "/usr/lib",
            str(config.python_runtime),
            *(
                str(item.root)
                for item in config.python_runtime_dependencies
            ),
            str(role_config.package_root),
        ],
        "python_runtime_dependencies": [
            {"alias": str(item.alias), "root": str(item.root)}
            for item in config.python_runtime_dependencies
        ],
        "recursive_write_roots": [str(role_config.output_root)],
        "literal_read_files": [
            "/dev/null",
            "/dev/random",
            "/dev/urandom",
            "/private/etc/localtime",
            *(
                [str(config.projector.sealed_result)]
                if role == "projector"
                else []
            ),
        ],
        "literal_write_files": ["/dev/null"],
        "process_exec_literals": [str(config.python_executable)],
        "network_policy": "DENY_ALL",
        "process_fork_policy": "DENY",
        "normal_workload_audit_policy": _workload_audit_policy(config, role),
    }


def _encoded_workload(workload: Workload) -> str:
    encoded = json.dumps(
        workload.payload(), sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return base64.b64encode(encoded).decode("ascii")


def _workload_audit_policy(config: IsolationConfig, role: str) -> dict[str, object]:
    role_config = config.answer if role == "answer" else config.projector
    other_role = config.projector if role == "answer" else config.answer
    allowed_read_files = [
        "/dev/null",
        "/dev/random",
        "/dev/urandom",
        "/private/etc/localtime",
    ]
    if role == "projector":
        allowed_read_files.append(str(config.projector.sealed_result))
    other_role_paths = [
        str(other_role.package_root),
        str(other_role.output_root),
    ]
    if role == "answer":
        other_role_paths.extend(
            (
                str(config.projector.store_root),
                str(config.projector.sealed_result),
            )
        )
    else:
        other_role_paths.append(str(config.answer.bundle_root))
    return {
        "allowed_read_roots": [
            str(path) for path in _profile_recursive_read_roots(config, role)
        ],
        "allowed_read_files": sorted(allowed_read_files),
        "allowed_write_roots": [str(role_config.output_root)],
        "allowed_write_files": ["/dev/null"],
        "forbidden_categories": {
            "source_operations": [
                str(config.forbidden.file),
                str(config.forbidden.git_root),
            ],
            "git_operations": [str(config.forbidden.git_root)],
            "evidence_payload_reads": (
                [str(config.projector.store_root)] if role == "answer" else []
            ),
            "authority_database_operations": [str(config.forbidden.sqlite)],
            "evidence_store_operations": [str(config.forbidden.sqlite)],
            "other_role_operations": sorted(other_role_paths),
        },
    }


def _encoded_audit_policy(config: IsolationConfig, role: str) -> str:
    encoded = json.dumps(
        _workload_audit_policy(config, role),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.b64encode(encoded).decode("ascii")


def _probe_worker_arguments(
    config: IsolationConfig,
    role: str,
    worker: Path,
    nonce: str,
    local_tcp: Endpoint,
    unix_socket: Path,
    callback: Endpoint,
) -> list[str]:
    role_config: AnswerRole | ProjectorRole
    role_config = config.answer if role == "answer" else config.projector
    arguments = [
        str(config.python_executable),
        *SANDBOXED_PYTHON_FLAGS,
        str(worker),
        "--role",
        role,
        "--nonce",
        nonce,
        "--package-root",
        str(role_config.package_root),
        "--package-canary",
        str(role_config.package_canary),
        "--output-root",
        str(role_config.output_root),
        "--source-remote-host",
        config.source_remote.host,
        "--source-remote-port",
        str(config.source_remote.port),
        "--public-ip",
        config.public_endpoint.host,
        "--public-port",
        str(config.public_endpoint.port),
        "--dns-host",
        config.dns_host,
        "--tcp-host",
        local_tcp.host,
        "--tcp-port",
        str(local_tcp.port),
        "--unix-socket",
        str(unix_socket),
        "--callback-host",
        callback.host,
        "--callback-port",
        str(callback.port),
        "--forbidden-file",
        str(config.forbidden.file),
        "--forbidden-sqlite",
        str(config.forbidden.sqlite),
        "--forbidden-git-root",
        str(config.forbidden.git_root),
        "--forbidden-git-marker",
        str(config.forbidden.git_marker),
    ]
    if role == "answer":
        arguments.extend(
            (
                "--bundle-root",
                str(config.answer.bundle_root),
                "--bundle-canary",
                str(config.answer.bundle_canary),
            )
        )
    else:
        arguments.extend(
            (
                "--sealed-result",
                str(config.projector.sealed_result),
                "--store-root",
                str(config.projector.store_root),
                "--store-canary",
                str(config.projector.store_canary),
            )
        )
    return arguments


def _workload_worker_arguments(
    config: IsolationConfig,
    role: str,
    worker: Path,
    nonce: str,
) -> list[str]:
    role_config = config.answer if role == "answer" else config.projector
    return [
        str(config.python_executable),
        *SANDBOXED_PYTHON_FLAGS,
        str(worker),
        "--role",
        role,
        "--nonce",
        nonce,
        "--package-root",
        str(role_config.package_root),
        "--output-root",
        str(role_config.output_root),
        "--workload-spec-b64",
        _encoded_workload(role_config.workload),
        "--audit-policy-b64",
        _encoded_audit_policy(config, role),
    ]


def probe_sandbox_command(
    config: IsolationConfig,
    role: str,
    worker: Path,
    nonce: str,
    local_tcp: Endpoint,
    unix_socket: Path,
    callback: Endpoint,
) -> list[str]:
    if role not in {"answer", "projector"}:
        raise ValueError(f"unsupported isolation role: {role}")
    profile = ANSWER_PROFILE if role == "answer" else PROJECTOR_PROFILE
    command = [str(SANDBOX_EXEC)]
    for key, value in sorted(_profile_parameters(config, role).items()):
        command.extend(("-D", f"{key}={value}"))
    command.extend(("-f", str(profile)))
    command.extend(
        _probe_worker_arguments(
            config, role, worker, nonce, local_tcp, unix_socket, callback
        )
    )
    return command


def workload_sandbox_command(
    config: IsolationConfig,
    role: str,
    worker: Path,
    nonce: str,
) -> list[str]:
    if role not in {"answer", "projector"}:
        raise ValueError(f"unsupported isolation role: {role}")
    profile = ANSWER_PROFILE if role == "answer" else PROJECTOR_PROFILE
    command = [str(SANDBOX_EXEC)]
    for key, value in sorted(_profile_parameters(config, role).items()):
        command.extend(("-D", f"{key}={value}"))
    command.extend(("-f", str(profile)))
    command.extend(_workload_worker_arguments(config, role, worker, nonce))
    return command


# Kept as the public helper name used by earlier plan tooling.  It now always
# builds the trusted probe child; product workloads use a distinct command.
sandbox_command = probe_sandbox_command


def _input_manifests(config: IsolationConfig) -> dict[str, object]:
    manifests: dict[str, object] = {
        "answer_package": _tree_manifest(config.answer.package_root),
        "answer_bundles": _tree_manifest(config.answer.bundle_root),
        "answer_initial_output": _tree_manifest(config.answer.output_root),
        "projector_package": _tree_manifest(config.projector.package_root),
        "projector_store": _tree_manifest(config.projector.store_root),
        "projector_initial_output": _tree_manifest(config.projector.output_root),
    }
    manifests["python_runtime_dependencies"] = [
        {
            "alias": str(item.alias),
            "root": str(item.root),
            "manifest": _runtime_dependency_manifest(item.root),
        }
        for item in config.python_runtime_dependencies
    ]
    return manifests


def _protected_manifests(config: IsolationConfig) -> dict[str, object]:
    manifests: dict[str, object] = {
        "answer_package": _tree_manifest(config.answer.package_root),
        "answer_bundles": _tree_manifest(config.answer.bundle_root),
        "projector_package": _tree_manifest(config.projector.package_root),
        "projector_store": _tree_manifest(config.projector.store_root),
    }
    for index, item in enumerate(config.python_runtime_dependencies):
        manifests[f"python_runtime_dependency_{index:02d}"] = {
            "alias": str(item.alias),
            "root": str(item.root),
            "manifest": _runtime_dependency_manifest(item.root),
        }
    return manifests


def _manifest_digest(manifest: object) -> str:
    encoded = json.dumps(
        manifest, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _manifest_entry_count(manifest: object) -> int:
    if isinstance(manifest, list):
        return len(manifest)
    if isinstance(manifest, dict) and isinstance(manifest.get("manifest"), list):
        return len(manifest["manifest"])
    raise TypeError("unsupported protected manifest")


def _integrity_check(
    expected: Mapping[str, object], config: IsolationConfig
) -> tuple[dict[str, object], bool]:
    observed = _protected_manifests(config)
    roots: dict[str, object] = {}
    passed = True
    for name in sorted(expected):
        unchanged = expected[name] == observed[name]
        passed = passed and unchanged
        roots[name] = {
            "status": "PASS" if unchanged else "FAIL",
            "before_digest": _manifest_digest(expected[name]),
            "after_digest": _manifest_digest(observed[name]),
        }
    return {"status": "PASS" if passed else "FAIL", "roots": roots}, passed


def build_plan(config: IsolationConfig) -> dict[str, object]:
    local = Endpoint("127.0.0.1", 1)
    answer_probe_worker = config.answer.package_root / STAGED_PROBE_WORKER
    projector_probe_worker = config.projector.package_root / STAGED_PROBE_WORKER
    answer_workload_worker = config.answer.package_root / STAGED_WORKLOAD_WORKER
    projector_workload_worker = config.projector.package_root / STAGED_WORKLOAD_WORKER
    return {
        "schema": PLAN_SCHEMA,
        "isolation_status": "NOT_EXECUTED",
        "v007_gate_status": "NOT_EVALUATED",
        "claim_scope": CLAIM_SCOPE,
        "os_enforcement": {
            "executed": False,
            "required_platform": "Darwin",
            "mechanism": str(SANDBOX_EXEC),
        },
        "input_manifests": _input_manifests(config),
        "capability_profiles": {
            role: _profile_capability_evidence(config, role)
            for role in ("answer", "projector")
        },
        "required_probes": {
            "answer": {
                "worker": list(probe_worker.required_probes("answer")),
                "outer_process": list(OUTER_PROCESS_PROBES),
            },
            "projector": {
                "worker": list(probe_worker.required_probes("projector")),
                "outer_process": list(OUTER_PROCESS_PROBES),
            },
        },
        "commands": {
            "answer": {
                "probe": probe_sandbox_command(
                    config,
                    "answer",
                    answer_probe_worker,
                    "<ANSWER_RUN_NONCE>",
                    local,
                    Path("/private/tmp/<LIVE_UNIX_SOCKET>"),
                    local,
                ),
                "workload": workload_sandbox_command(
                    config,
                    "answer",
                    answer_workload_worker,
                    "<ANSWER_RUN_NONCE>",
                ),
            },
            "projector": {
                "probe": probe_sandbox_command(
                    config,
                    "projector",
                    projector_probe_worker,
                    "<PROJECTOR_RUN_NONCE>",
                    local,
                    Path("/private/tmp/<LIVE_UNIX_SOCKET>"),
                    local,
                ),
                "workload": workload_sandbox_command(
                    config,
                    "projector",
                    projector_workload_worker,
                    "<PROJECTOR_RUN_NONCE>",
                ),
            },
        },
        "limitations": [
            "No child process was launched by plan mode.",
            "A unit test or mocked report cannot establish OS isolation.",
            "V-007 additionally requires the real query and projector gate run.",
            "Literal ancestor file-read traversal may disclose each ancestor's "
            "direct directory entry names; it does not authorize reading child "
            "file contents.",
        ],
    }


def worker_report_is_os_pass(
    report: object, *, role: str, nonce: str, os_enforced: bool
) -> bool:
    """Validate a worker report, gated by non-forgeable outer-run state.

    ``os_enforced`` must only be supplied as true by :func:`run_isolation`
    after a real fixed-path ``sandbox-exec`` child returned.  This argument is
    intentionally mandatory so policy/report unit tests cannot become an OS
    PASS by accident.
    """
    if not os_enforced or not isinstance(report, dict):
        return False
    if set(report) != {
        "schema",
        "role",
        "nonce",
        "pid",
        "status",
        "authorized_access",
        "required_probes",
        "probes",
    }:
        return False
    if (
        report.get("schema") != probe_worker.REPORT_SCHEMA
        or report.get("role") != role
        or report.get("nonce") != nonce
        or report.get("status") != "PASS"
    ):
        return False
    pid = report.get("pid")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    required = list(probe_worker.required_probes(role))
    if report.get("required_probes") != required:
        return False
    probes = report.get("probes")
    if not isinstance(probes, list) or len(probes) != len(required):
        return False
    if [item.get("name") for item in probes if isinstance(item, dict)] != required:
        return False
    if any(
        not isinstance(item, dict)
        or set(item) != {"name", "outcome", "exception"}
        or item.get("outcome") != "DENIED"
        or not isinstance(item.get("exception"), dict)
        or not isinstance(item["exception"].get("type"), str)
        or not isinstance(item["exception"].get("message"), str)
        for item in probes
    ):
        return False
    authorized = report.get("authorized_access")
    expected_authorized = (
        ["package_read", "bundle_read", "result_output_write"]
        if role == "answer"
        else [
            "package_read",
            "sealed_result_read",
            "allowlisted_store_read",
            "result_output_write",
        ]
    )
    if not isinstance(authorized, list):
        return False
    if [item.get("name") for item in authorized if isinstance(item, dict)] != expected_authorized:
        return False
    if any(
        not isinstance(item, dict) or item.get("outcome") != "PASS"
        for item in authorized
    ):
        return False
    return True


class _TcpListener:
    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("127.0.0.1", 0))
        self.socket.listen(16)
        host, port = self.socket.getsockname()
        self.endpoint = Endpoint(str(host), int(port))

    def close(self) -> None:
        self.socket.close()

    def __enter__(self) -> _TcpListener:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class _UnixListener:
    def __init__(self, root: Path) -> None:
        self.path = root / "denied.sock"
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(str(self.path))
        self.socket.listen(16)

    def close(self) -> None:
        self.socket.close()
        self.path.unlink(missing_ok=True)

    def __enter__(self) -> _UnixListener:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def _network_preflight(endpoint: Endpoint, label: str) -> dict[str, object]:
    addresses = socket.getaddrinfo(
        endpoint.host, endpoint.port, type=socket.SOCK_STREAM
    )
    with socket.create_connection((endpoint.host, endpoint.port), timeout=5.0) as stream:
        peer = stream.getpeername()
    return {
        "label": label,
        "status": "PASS",
        "resolved_address_count": len(addresses),
        "connected_peer": [str(peer[0]), int(peer[1])],
    }


def _preflight(config: IsolationConfig) -> dict[str, object]:
    with config.forbidden.file.open("rb") as stream:
        stream.read(1)
    sqlite_uri = f"file:{quote(str(config.forbidden.sqlite), safe='/')}?mode=ro&immutable=1"
    with sqlite3.connect(sqlite_uri, uri=True) as connection:
        connection.execute("PRAGMA query_only = ON")
        connection.execute("SELECT name FROM sqlite_master LIMIT 1").fetchone()
    with config.forbidden.git_marker.open("rb") as stream:
        stream.read(1)
    git = subprocess.run(
        (str(GIT_EXECUTABLE), "-C", str(config.forbidden.git_root), "status", "--porcelain"),
        check=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=min(config.timeout_seconds, 30.0),
    )
    if git.returncode != 0:
        raise RuntimeError("outer Git preflight could not inspect forbidden repository")
    dns = socket.getaddrinfo(
        config.dns_host, config.public_endpoint.port, type=socket.SOCK_STREAM
    )
    return {
        "status": "PASS",
        "forbidden_file": {
            "path": str(config.forbidden.file),
            "digest": _sha256_file(config.forbidden.file),
        },
        "forbidden_sqlite": {
            "path": str(config.forbidden.sqlite),
            "digest": _sha256_file(config.forbidden.sqlite),
            "read_only_query": "PASS",
        },
        "forbidden_git": {
            "root": str(config.forbidden.git_root),
            "marker": str(config.forbidden.git_marker),
            "marker_digest": _sha256_file(config.forbidden.git_marker),
            "git_status": "PASS",
            "stdout_digest": _sha256_bytes(git.stdout),
            "stderr_digest": _sha256_bytes(git.stderr),
        },
        "dns": {
            "host": config.dns_host,
            "status": "PASS",
            "resolved_address_count": len(dns),
        },
        "source_remote": _network_preflight(config.source_remote, "source_remote"),
        "public_endpoint": _network_preflight(config.public_endpoint, "public_endpoint"),
    }


def _install_worker(package_root: Path, source_path: Path, staged_path: Path) -> Path:
    source = source_path.read_bytes()
    directory = package_root / staged_path.parent
    if directory.exists() and (directory.is_symlink() or not directory.is_dir()):
        raise ConfigurationError(f"unsafe staged worker directory: {directory}")
    directory.mkdir(mode=0o700, parents=False, exist_ok=True)
    target = package_root / staged_path
    if target.exists():
        if target.is_symlink() or not target.is_file() or target.read_bytes() != source:
            raise ConfigurationError(f"staged worker collision: {target}")
    else:
        target.write_bytes(source)
    target.chmod(0o444)
    return target.resolve(strict=True)


def _sanitized_environment(output_root: Path) -> dict[str, str]:
    return {
        "TMPDIR": str(output_root),
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }


def _profiled_process_command(
    config: IsolationConfig,
    role: str,
    argv: Sequence[str],
) -> list[str]:
    profile = ANSWER_PROFILE if role == "answer" else PROJECTOR_PROFILE
    command = [str(SANDBOX_EXEC)]
    for key, value in sorted(_profile_parameters(config, role).items()):
        command.extend(("-D", f"{key}={value}"))
    command.extend(("-f", str(profile), *argv))
    return command


def _invoke_outer_process_probes(
    config: IsolationConfig,
    role: str,
) -> tuple[dict[str, object], bool]:
    role_config = config.answer if role == "answer" else config.projector
    specifications = (
        (
            "python_control",
            (
                str(config.python_executable),
                *SANDBOXED_PYTHON_FLAGS,
                "-c",
                "pass",
            ),
            True,
        ),
        (
            "process_fork",
            (
                str(config.python_executable),
                *SANDBOXED_PYTHON_FLAGS,
                "-c",
                "import os; os.fork()",
            ),
            False,
        ),
        ("git_process_exec", (str(GIT_EXECUTABLE), "--version"), False),
        ("subprocess_exec", (str(TRUE_EXECUTABLE),), False),
    )
    probes: list[dict[str, object]] = []
    passed = True
    for name, argv, should_succeed in specifications:
        command = _profiled_process_command(config, role, argv)
        completed = subprocess.run(
            command,
            cwd=role_config.package_root,
            env=_sanitized_environment(role_config.output_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=min(config.timeout_seconds, 30.0),
            check=False,
        )
        observed = completed.returncode == 0
        probe_pass = observed is should_succeed
        passed = passed and probe_pass
        probes.append(
            {
                "name": name,
                "outcome": (
                    "PASS"
                    if name == "python_control" and probe_pass
                    else "DENIED"
                    if not should_succeed and probe_pass
                    else "FAIL"
                ),
                "command": command,
                "exit_code": completed.returncode,
                "stdout_digest": _sha256_bytes(completed.stdout),
                "stderr_digest": _sha256_bytes(completed.stderr),
                "stderr_preview": completed.stderr.decode(
                    "utf-8", errors="replace"
                )[:2000],
            }
        )
    return {
        "status": "PASS" if passed else "FAIL",
        "required_probes": list(OUTER_PROCESS_PROBES),
        "probes": probes,
    }, passed


def workload_report_is_pass(
    report: object,
    *,
    role: str,
    nonce: str,
    workload: Workload,
) -> bool:
    if not isinstance(report, dict) or set(report) != {
        "schema",
        "role",
        "nonce",
        "pid",
        "status",
        "workload",
    }:
        return False
    pid = report.get("pid")
    if (
        report.get("schema") != workload_worker.REPORT_SCHEMA
        or report.get("role") != role
        or report.get("nonce") != nonce
        or report.get("status") != "PASS"
        or isinstance(pid, bool)
        or not isinstance(pid, int)
        or pid <= 0
    ):
        return False
    result = report.get("workload")
    if not isinstance(result, dict) or set(result) != {
        "status",
        "entrypoint",
        "exit_code",
        "stdout_digest",
        "stderr_digest",
        "outputs",
        "operation_audit",
    }:
        return False
    if (
        result.get("status") != "PASS"
        or result.get("entrypoint") != workload.entrypoint
        or result.get("exit_code") != 0
        or not isinstance(result.get("stdout_digest"), str)
        or not isinstance(result.get("stderr_digest"), str)
    ):
        return False
    outputs = result.get("outputs")
    if not isinstance(outputs, list) or len(outputs) != len(workload.expected_outputs):
        return False
    if any(
        not isinstance(item, dict)
        or set(item) != {"path", "digest", "size"}
        or not isinstance(item.get("path"), str)
        or not isinstance(item.get("digest"), str)
        or isinstance(item.get("size"), bool)
        or not isinstance(item.get("size"), int)
        or item["size"] < 0
        for item in outputs
    ):
        return False
    if [item["path"] for item in outputs] != list(workload.expected_outputs):
        return False
    audit = result.get("operation_audit")
    if not isinstance(audit, dict) or set(audit) != {
        "schema",
        "status",
        "prohibited_counts",
        "audited_event_count",
        "authorized_file_operation_count",
        "violations",
    }:
        return False
    expected_counters = set(workload_worker.PROHIBITED_COUNTERS)
    counts = audit.get("prohibited_counts")
    if (
        audit.get("schema") != workload_worker.AUDIT_SCHEMA
        or audit.get("status") != "PASS"
        or not isinstance(counts, dict)
        or set(counts) != expected_counters
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value != 0
            for value in counts.values()
        )
        or audit.get("violations") != []
    ):
        return False
    for key in ("audited_event_count", "authorized_file_operation_count"):
        value = audit.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            return False
    return True


def _parse_json_child_stdout(
    completed: subprocess.CompletedProcess[bytes],
) -> tuple[object, str | None]:
    report: object = None
    parse_error: str | None = None
    try:
        decoded = completed.stdout.decode("utf-8")
        if decoded.count("\n") != 1 or not decoded.endswith("\n"):
            raise ValueError("worker stdout is not exactly one JSON line")
        report = json.loads(decoded)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        parse_error = f"{type(exc).__name__}: {str(exc)[:500]}"
    return report, parse_error


def _child_evidence(
    *,
    completed: subprocess.CompletedProcess[bytes],
    command: Sequence[str],
    role_config: AnswerRole | ProjectorRole,
    report: object,
    parse_error: str | None,
    passed: bool,
    launcher_pid: int,
) -> dict[str, object]:
    environment = _sanitized_environment(role_config.output_root)
    evidence: dict[str, object] = {
        "status": "PASS" if passed else "FAIL",
        "command": list(command),
        "cwd": str(role_config.package_root),
        "environment": environment,
        "launcher_observed_pid": launcher_pid,
        "exit_code": completed.returncode,
        "stdout_digest": _sha256_bytes(completed.stdout),
        "stderr_digest": _sha256_bytes(completed.stderr),
        "stderr_preview": completed.stderr.decode("utf-8", errors="replace")[:2000],
        "worker_report": report,
    }
    if parse_error is not None:
        evidence["report_parse_error"] = parse_error
    return evidence


def _run_json_child(
    *,
    command: Sequence[str],
    role_config: AnswerRole | ProjectorRole,
    timeout: float,
) -> tuple[subprocess.CompletedProcess[bytes], int, object, str | None]:
    process = subprocess.Popen(
        command,
        cwd=role_config.package_root,
        env=_sanitized_environment(role_config.output_root),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate()
        raise
    completed = subprocess.CompletedProcess(
        args=list(command),
        returncode=process.returncode,
        stdout=stdout,
        stderr=stderr,
    )
    report, parse_error = _parse_json_child_stdout(completed)
    return completed, process.pid, report, parse_error


def _report_pid_matches_launcher(report: object, launcher_pid: int) -> bool:
    if (
        not isinstance(report, dict)
        or isinstance(launcher_pid, bool)
        or not isinstance(launcher_pid, int)
        or launcher_pid <= 0
    ):
        return False
    reported_pid = report.get("pid")
    return (
        not isinstance(reported_pid, bool)
        and isinstance(reported_pid, int)
        and reported_pid == launcher_pid
    )


def _invoke_probe_role(
    *,
    config: IsolationConfig,
    role: str,
    worker: Path,
    nonce: str,
    local_tcp: Endpoint,
    unix_socket: Path,
    callback: Endpoint,
) -> tuple[dict[str, object], bool]:
    command = probe_sandbox_command(
        config, role, worker, nonce, local_tcp, unix_socket, callback
    )
    role_config = config.answer if role == "answer" else config.projector
    completed, launcher_pid, report, parse_error = _run_json_child(
        command=command,
        role_config=role_config,
        timeout=config.timeout_seconds,
    )
    passed = completed.returncode == 0 and worker_report_is_os_pass(
        report, role=role, nonce=nonce, os_enforced=True
    )
    passed = passed and _report_pid_matches_launcher(report, launcher_pid)
    return _child_evidence(
        completed=completed,
        command=command,
        role_config=role_config,
        report=report,
        parse_error=parse_error,
        passed=passed,
        launcher_pid=launcher_pid,
    ), passed


def _invoke_workload_role(
    *,
    config: IsolationConfig,
    role: str,
    worker: Path,
    nonce: str,
) -> tuple[dict[str, object], bool]:
    command = workload_sandbox_command(config, role, worker, nonce)
    role_config = config.answer if role == "answer" else config.projector
    completed, launcher_pid, report, parse_error = _run_json_child(
        command=command,
        role_config=role_config,
        timeout=config.timeout_seconds,
    )
    passed = completed.returncode == 0 and workload_report_is_pass(
        report,
        role=role,
        nonce=nonce,
        workload=role_config.workload,
    )
    passed = passed and _report_pid_matches_launcher(report, launcher_pid)
    return _child_evidence(
        completed=completed,
        command=command,
        role_config=role_config,
        report=report,
        parse_error=parse_error,
        passed=passed,
        launcher_pid=launcher_pid,
    ), passed


def _closed_output_manifest(
    config: IsolationConfig, role: str, workload_evidence: Mapping[str, object]
) -> tuple[dict[str, object], bool]:
    role_config = config.answer if role == "answer" else config.projector
    observed, observed_directories = _tree_inventory(role_config.output_root)
    expected_paths = tuple(sorted(role_config.workload.expected_outputs))
    expected_directories = _implied_directory_paths(expected_paths)
    file_paths_match = _manifest_paths(observed) == expected_paths
    directories_match = observed_directories == expected_directories
    paths_match = file_paths_match and directories_match
    report = workload_evidence.get("worker_report")
    reported_outputs: object = None
    reported_stdout_digest: object = None
    if isinstance(report, dict) and isinstance(report.get("workload"), dict):
        reported_outputs = report["workload"].get("outputs")
        reported_stdout_digest = report["workload"].get("stdout_digest")
    sorted_reported = (
        sorted(reported_outputs, key=lambda item: str(item.get("path")))
        if isinstance(reported_outputs, list)
        and all(isinstance(item, dict) for item in reported_outputs)
        else None
    )
    report_matches = sorted_reported == observed
    stdout_entry = next(
        (
            item
            for item in observed
            if item["path"] == role_config.workload.stdout_output
        ),
        None,
    )
    stdout_matches = (
        stdout_entry is not None
        and reported_stdout_digest == stdout_entry["digest"]
    )
    passed = paths_match and report_matches and stdout_matches
    return {
        "status": "PASS" if passed else "FAIL",
        "expected_paths": list(expected_paths),
        "expected_directories": list(expected_directories),
        "observed": observed,
        "observed_directories": list(observed_directories),
        "file_paths_exact": file_paths_match,
        "directories_exact": directories_match,
        "paths_exact": paths_match,
        "worker_report_exact": report_matches,
        "stdout_digest_exact": stdout_matches,
    }, passed


def _copy_sealed_result(config: IsolationConfig) -> dict[str, object]:
    source = config.answer.sealed_result.resolve(strict=True)
    if (
        source != config.answer.sealed_result
        or not source.is_file()
        or source.is_symlink()
        or source.stat().st_nlink != 1
    ):
        raise RuntimeError("answer did not produce a canonical sealed Result")
    target = config.projector.sealed_result
    if target.exists():
        raise RuntimeError("projector sealed Result target appeared before transfer")
    digest = _sha256_file(source)
    with source.open("rb") as source_stream, target.open("xb") as target_stream:
        shutil.copyfileobj(source_stream, target_stream)
    target.chmod(0o444)
    if _sha256_file(target) != digest:
        raise RuntimeError("sealed Result digest changed during one-way transfer")
    return {
        "status": "PASS",
        "direction": "answer_to_projector",
        "source": str(source),
        "target": str(target),
        "digest": digest,
        "target_mode": "0444",
    }


def _platform_guard(config: IsolationConfig) -> None:
    if platform.system() != "Darwin":
        raise RuntimeError("OS isolation execution requires macOS (Darwin)")
    if SANDBOX_EXEC.resolve(strict=True) != SANDBOX_EXEC or not os.access(SANDBOX_EXEC, os.X_OK):
        raise RuntimeError("fixed /usr/bin/sandbox-exec is unavailable or not executable")
    for path, label in (
        (ANSWER_PROFILE, "answer profile"),
        (PROJECTOR_PROFILE, "projector profile"),
        (WORKER_SOURCE, "probe worker"),
        (WORKLOAD_WORKER_SOURCE, "workload worker"),
        (TRUE_EXECUTABLE, "/usr/bin/true"),
        (GIT_EXECUTABLE, "/usr/bin/git"),
    ):
        _canonical_file(str(path), label)
    if Path(sys.executable).resolve(strict=True) != config.python_executable:
        raise RuntimeError("trusted Python executable changed after configuration load")


def run_isolation(config: IsolationConfig) -> tuple[dict[str, object], bool]:
    """Execute independent probe and workload children for both roles."""
    evidence: dict[str, object] = {
        "schema": EVIDENCE_SCHEMA,
        "isolation_status": "FAIL",
        "v007_gate_status": "NOT_EVALUATED",
        "claim_scope": CLAIM_SCOPE,
        "os_enforcement": {
            "executed": False,
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "mechanism": {
                "path": str(SANDBOX_EXEC),
                "digest": _sha256_file(SANDBOX_EXEC),
            },
            "python_executable": {
                "path": str(config.python_executable),
                "digest": _sha256_file(config.python_executable),
            },
            "python_runtime": str(config.python_runtime),
            "python_runtime_dependencies": [
                {
                    "alias": str(item.alias),
                    "root": str(item.root),
                    "manifest_digest": _manifest_digest(
                        _runtime_dependency_manifest(item.root)
                    ),
                }
                for item in config.python_runtime_dependencies
            ],
            "sandboxed_python_flags": list(SANDBOXED_PYTHON_FLAGS),
            "answer_profile": {
                "path": str(ANSWER_PROFILE),
                "digest": _sha256_file(ANSWER_PROFILE),
            },
            "projector_profile": {
                "path": str(PROJECTOR_PROFILE),
                "digest": _sha256_file(PROJECTOR_PROFILE),
            },
            "probe_worker": {
                "path": str(WORKER_SOURCE),
                "digest": _sha256_file(WORKER_SOURCE),
            },
            "workload_worker": {
                "path": str(WORKLOAD_WORKER_SOURCE),
                "digest": _sha256_file(WORKLOAD_WORKER_SOURCE),
            },
        },
        "capability_profiles": {
            role: _profile_capability_evidence(config, role)
            for role in ("answer", "projector")
        },
        "input_manifests": _input_manifests(config),
        "roles": {},
        "outer_process_denial_probes": {"status": "NOT_EXECUTED"},
        "sealed_result_transfer": {"status": "NOT_EXECUTED"},
        "workloads_executed": {
            "answer": False,
            "projector": False,
        },
        "limitations": [
            "PASS establishes only OS file/network/process isolation.",
            "V-007 remains NOT_EVALUATED until the product gate consumes this evidence.",
            "Literal ancestor file-read traversal may disclose each ancestor's "
            "direct directory entry names; it does not authorize reading child "
            "file contents.",
        ],
    }
    try:
        _platform_guard(config)
        answer_probe_worker = _install_worker(
            config.answer.package_root, WORKER_SOURCE, STAGED_PROBE_WORKER
        )
        projector_probe_worker = _install_worker(
            config.projector.package_root, WORKER_SOURCE, STAGED_PROBE_WORKER
        )
        answer_workload_worker = _install_worker(
            config.answer.package_root,
            WORKLOAD_WORKER_SOURCE,
            STAGED_WORKLOAD_WORKER,
        )
        projector_workload_worker = _install_worker(
            config.projector.package_root,
            WORKLOAD_WORKER_SOURCE,
            STAGED_WORKLOAD_WORKER,
        )
        evidence["staged_workers"] = {
            "answer": {
                "probe": {
                    "path": str(answer_probe_worker),
                    "digest": _sha256_file(answer_probe_worker),
                },
                "workload": {
                    "path": str(answer_workload_worker),
                    "digest": _sha256_file(answer_workload_worker),
                },
            },
            "projector": {
                "probe": {
                    "path": str(projector_probe_worker),
                    "digest": _sha256_file(projector_probe_worker),
                },
                "workload": {
                    "path": str(projector_workload_worker),
                    "digest": _sha256_file(projector_workload_worker),
                },
            },
        }
        protected_before = _protected_manifests(config)
        evidence["protected_inputs_after_worker_staging"] = {
            name: {
                "manifest_digest": _manifest_digest(manifest),
                "file_count": _manifest_entry_count(manifest),
                "manifest": manifest,
            }
            for name, manifest in sorted(protected_before.items())
        }
        evidence["preflight"] = _preflight(config)
        process_probe_evidence: dict[str, object] = {}
        process_probes_pass = True
        for role in ("answer", "projector"):
            role_evidence, role_pass = _invoke_outer_process_probes(config, role)
            evidence["os_enforcement"]["executed"] = True
            process_probe_evidence[role] = role_evidence
            process_probes_pass = process_probes_pass and role_pass
        evidence["outer_process_denial_probes"] = process_probe_evidence
        if not process_probes_pass:
            return evidence, False
        answer_nonce = secrets.token_hex(16)
        projector_nonce = secrets.token_hex(16)
        while projector_nonce == answer_nonce:
            projector_nonce = secrets.token_hex(16)
        evidence["role_nonces"] = {
            "answer": answer_nonce,
            "projector": projector_nonce,
            "distinct": True,
            "relationship": (
                "probe and workload share one nonce within each role; "
                "answer and projector nonces are distinct"
            ),
        }
        observed_pids: set[int] = set()
        with tempfile.TemporaryDirectory(prefix="iter003-g2-isolation-") as temporary:
            temporary_root = Path(temporary).resolve(strict=True)
            with ExitStack() as stack:
                tcp_listener = stack.enter_context(_TcpListener())
                answer_callback = stack.enter_context(_TcpListener())
                projector_callback = stack.enter_context(_TcpListener())
                unix_listener = stack.enter_context(_UnixListener(temporary_root))
                answer_probe, answer_probe_pass = _invoke_probe_role(
                    config=config,
                    role="answer",
                    worker=answer_probe_worker,
                    nonce=answer_nonce,
                    local_tcp=tcp_listener.endpoint,
                    unix_socket=unix_listener.path,
                    callback=projector_callback.endpoint,
                )
                evidence["roles"] = {
                    "answer": {
                        "status": "FAIL",
                        "nonce": answer_nonce,
                        "probe": answer_probe,
                        "workload": {"status": "NOT_EXECUTED"},
                        "final_output_manifest": {"status": "NOT_EXECUTED"},
                    }
                }
                if not answer_probe_pass:
                    return evidence, False
                answer_probe_pid = int(answer_probe["worker_report"]["pid"])
                observed_pids.add(answer_probe_pid)
                answer_workload, answer_workload_pass = _invoke_workload_role(
                    config=config,
                    role="answer",
                    worker=answer_workload_worker,
                    nonce=answer_nonce,
                )
                evidence["roles"]["answer"]["workload"] = answer_workload
                answer_output, answer_output_pass = _closed_output_manifest(
                    config, "answer", answer_workload
                )
                evidence["roles"]["answer"]["final_output_manifest"] = answer_output
                answer_workload_pid = (
                    int(answer_workload["worker_report"]["pid"])
                    if answer_workload_pass
                    else -1
                )
                answer_pid_distinct = (
                    answer_workload_pid > 0
                    and answer_workload_pid not in observed_pids
                )
                evidence["roles"]["answer"]["process_identity"] = {
                    "probe_pid": answer_probe_pid,
                    "workload_pid": answer_workload_pid,
                    "distinct": answer_pid_distinct,
                }
                if answer_pid_distinct:
                    observed_pids.add(answer_workload_pid)
                answer_integrity, answer_inputs_unchanged = _integrity_check(
                    protected_before, config
                )
                evidence["protected_input_integrity_after_answer"] = answer_integrity
                answer_pass = (
                    answer_probe_pass
                    and answer_workload_pass
                    and answer_output_pass
                    and answer_pid_distinct
                    and answer_inputs_unchanged
                )
                evidence["roles"]["answer"]["status"] = (
                    "PASS" if answer_pass else "FAIL"
                )
                evidence["workloads_executed"]["answer"] = (
                    answer_workload_pass and answer_output_pass
                )
                if not answer_pass:
                    return evidence, False
                transfer = _copy_sealed_result(config)
                evidence["sealed_result_transfer"] = transfer
                projector_probe, projector_probe_pass = _invoke_probe_role(
                    config=config,
                    role="projector",
                    worker=projector_probe_worker,
                    nonce=projector_nonce,
                    local_tcp=tcp_listener.endpoint,
                    unix_socket=unix_listener.path,
                    callback=answer_callback.endpoint,
                )
                evidence["roles"]["projector"] = {
                    "status": "FAIL",
                    "nonce": projector_nonce,
                    "probe": projector_probe,
                    "workload": {"status": "NOT_EXECUTED"},
                    "final_output_manifest": {"status": "NOT_EXECUTED"},
                }
                if not projector_probe_pass:
                    return evidence, False
                projector_probe_pid = int(projector_probe["worker_report"]["pid"])
                projector_probe_distinct = projector_probe_pid not in observed_pids
                if projector_probe_distinct:
                    observed_pids.add(projector_probe_pid)
                projector_workload, projector_workload_pass = _invoke_workload_role(
                    config=config,
                    role="projector",
                    worker=projector_workload_worker,
                    nonce=projector_nonce,
                )
                evidence["roles"]["projector"]["workload"] = projector_workload
                projector_output, projector_output_pass = _closed_output_manifest(
                    config, "projector", projector_workload
                )
                evidence["roles"]["projector"]["final_output_manifest"] = projector_output
                projector_workload_pid = (
                    int(projector_workload["worker_report"]["pid"])
                    if projector_workload_pass
                    else -1
                )
                projector_workload_distinct = (
                    projector_workload_pid > 0
                    and projector_workload_pid not in observed_pids
                )
                if projector_workload_distinct:
                    observed_pids.add(projector_workload_pid)
                projector_pid_distinct = (
                    projector_probe_distinct and projector_workload_distinct
                )
                evidence["roles"]["projector"]["process_identity"] = {
                    "probe_pid": projector_probe_pid,
                    "workload_pid": projector_workload_pid,
                    "distinct": projector_pid_distinct,
                }
                final_integrity, final_inputs_unchanged = _integrity_check(
                    protected_before, config
                )
                evidence["protected_input_integrity_after_projector"] = final_integrity
                projector_pass = (
                    projector_probe_pass
                    and projector_workload_pass
                    and projector_output_pass
                    and projector_pid_distinct
                    and final_inputs_unchanged
                )
                evidence["roles"]["projector"]["status"] = (
                    "PASS" if projector_pass else "FAIL"
                )
                evidence["workloads_executed"]["projector"] = (
                    projector_workload_pass and projector_output_pass
                )
                evidence["process_identity"] = {
                    "status": "PASS" if len(observed_pids) == 4 else "FAIL",
                    "all_worker_pids": sorted(observed_pids),
                    "all_distinct": len(observed_pids) == 4,
                }
                if not projector_pass or len(observed_pids) != 4:
                    return evidence, False
        evidence["isolation_status"] = "PASS"
        return evidence, True
    except Exception as exc:
        evidence["failure"] = {
            "type": type(exc).__name__,
            "message": str(exc)[:1000],
        }
        return evidence, False


def _write_new_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(encoded)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    plan = subparsers.add_parser("plan", help="validate and emit a non-executed plan")
    plan.add_argument("--config", type=Path, required=True)
    plan.add_argument("--output", type=Path)
    run = subparsers.add_parser("run", help="execute real macOS Seatbelt workers")
    run.add_argument("--config", type=Path, required=True)
    run.add_argument("--evidence-output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        config = load_config(arguments.config)
        if arguments.command == "plan":
            payload = build_plan(config)
            if arguments.output is not None:
                _write_new_json(arguments.output, payload)
            sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
            sys.stdout.write("\n")
            return 0
        evidence, passed = run_isolation(config)
        _write_new_json(arguments.evidence_output, evidence)
        sys.stdout.write(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
        sys.stdout.write("\n")
        return 0 if passed else 2
    except (ConfigurationError, OSError, ValueError) as exc:
        sys.stderr.write(f"isolation harness error: {exc}\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
