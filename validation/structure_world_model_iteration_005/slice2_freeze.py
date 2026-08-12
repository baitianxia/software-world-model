"""Freeze and deterministically qualify the ITER-005 SLICE-002 candidate."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import stat
import subprocess
import sys
from typing import Iterable, Mapping, Sequence

from . import slice2_comparison, slice2_evaluator


QUALIFICATION_SCHEMA = "SWM-WORLD-MODEL-DETERMINISTIC-QUALIFICATION@1"
SUITE_SCHEMA = "SWM-WORLD-MODEL-HELD-OUT-SUITE@2"
ORACLE_SCHEMA = "SWM-WORLD-MODEL-HELD-OUT-ORACLE@1"
GRANT_SCHEMA = "SWM-WORLD-MODEL-EVALUATION-GRANT@2"
REPORT_SCHEMA = "SWM-WORLD-MODEL-SLICE-002-FREEZE@1"
DISCLOSURE_SCHEMA = "SWM-WORLD-MODEL-DISCLOSURE-AUTHORIZATION@1"
_TEST_COUNT = re.compile(r"Ran ([0-9]+) tests?")
_PROVIDER = {
    "provider_type": "VOLCENGINE_ARK",
    "adapter": "openai-chat-completions-no-tools@8",
    "requested_model": "glm-5-2-260617",
    "observed_model": "glm-5.2",
    "endpoint": (
        "https://ark.cn-beijing.volces.com:443/"
        "api/coding/v3/chat/completions"
    ),
    "credential_reference": "env:ARK_API_KEY",
    "conformance_digest": (
        "sha256:c86aad995802b8dcf687fafcbaf36bccb02768ba55b40151ec9aa4704518cade"
    ),
    "qualification_digest": (
        "sha256:005b1bf43c76a64d123b0184cdac1a9e844331896e7ede6279875881d9bcc62c"
    ),
}
_ROLE_ENTRYPOINTS = {
    "answer": ".g3b/answer_workload.py",
    "gateway": ".g3b/gateway_authorized_workload.py",
    "broker": ".g3b/materialize_citations.py",
    "projector": ".g3b/projection_workload.py",
}
_GATEWAY_INPUT_FILES = {
    "conformance.json",
    "qualification.json",
    "closed-result.json",
    "egress-policy.json",
    "g3b-freeze.json",
}


class FreezeFailure(RuntimeError):
    """A candidate freeze or deterministic gate failed."""


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _value_digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _document(schema: str, core: Mapping[str, object]) -> dict[str, object]:
    return {**core, "document_digest": _value_digest([schema, core])}


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise FreezeFailure(f"output already exists: {path}")
    path.write_bytes(_canonical(value))


def _raw_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha(path: Path) -> str:
    return "sha256:" + _raw_sha(path)


def _reference(path: Path, *, document: bool) -> dict[str, str]:
    value = {"path": str(path.resolve(strict=True)), "raw_sha256": _raw_sha(path)}
    if document:
        loaded = json.loads(path.read_text(encoding="utf-8"))
        value["document_digest"] = str(loaded["document_digest"])
    return value


def _run(
    arguments: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str] | None = None,
    expect: int = 0,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        tuple(arguments),
        cwd=cwd,
        env=dict(environment) if environment is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != expect:
        raise FreezeFailure(
            f"command returned {completed.returncode}, expected {expect}: "
            f"{' '.join(arguments)}\nstdout={completed.stdout}\nstderr={completed.stderr}"
        )
    return completed


def _git(repository: Path, *arguments: str) -> str:
    return _run(("git", "-C", str(repository), *arguments), cwd=repository).stdout.strip()


def _tree_manifest(root: Path) -> dict[str, object]:
    directories: list[str] = []
    files: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise FreezeFailure(f"symlink in protected tree: {path}")
        if stat.S_ISDIR(metadata.st_mode):
            directories.append(relative)
        elif stat.S_ISREG(metadata.st_mode):
            files.append(
                {"path": relative, "digest": _sha(path), "size": metadata.st_size}
            )
        else:
            raise FreezeFailure(f"unsupported protected tree entry: {path}")
    return {"directories": directories, "files": files}


def _file_map(manifest: Mapping[str, object]) -> dict[str, str]:
    return {
        str(item["path"]): str(item["digest"])
        for item in manifest["files"]
    }


def _source_snapshot(workspace: Path, destination: Path) -> dict[str, str]:
    shutil.copytree(
        workspace / "src",
        destination / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    shutil.copy2(workspace / "pyproject.toml", destination / "pyproject.toml")
    _git(destination, "init", "-q")
    _git(destination, "config", "user.email", "iter005-slice2@example.invalid")
    _git(destination, "config", "user.name", "ITER-005 SLICE-002 Freeze")
    _git(destination, "add", "src", "pyproject.toml")
    _git(destination, "commit", "-q", "-m", "freeze SLICE-002 candidate source")
    return {
        "commit": _git(destination, "rev-parse", "HEAD"),
        "tree": _git(destination, "rev-parse", "HEAD^{tree}"),
        "source_manifest_digest": _value_digest(
            _tree_manifest(destination / "src")
        ),
    }


def _candidate_stage(
    baseline: Path,
    expected_baseline_digest: str,
    producer: Path,
    destination: Path,
) -> tuple[str, list[str]]:
    baseline_manifest = _tree_manifest(baseline)
    if _value_digest(baseline_manifest) != expected_baseline_digest:
        raise FreezeFailure("qualified baseline stage digest drifted")
    shutil.copytree(baseline, destination)
    answer_product = (
        destination
        / "packages/answer/software_world_model/interface/world_model_product.py"
    )
    shutil.copy2(
        producer / "src/software_world_model/interface/world_model_product.py",
        answer_product,
    )
    gateway_wrapper = destination / "packages/gateway/.g3b/gateway_authorized_workload.py"
    shutil.copy2(
        producer
        / "src/software_world_model/interface/world_model_runtime_assets/gateway_authorized_workload.py",
        gateway_wrapper,
    )
    candidate_manifest = _tree_manifest(destination)
    baseline_files = _file_map(baseline_manifest)
    candidate_files = _file_map(candidate_manifest)
    changed = sorted(
        path
        for path in set(baseline_files) | set(candidate_files)
        if baseline_files.get(path) != candidate_files.get(path)
    )
    expected = sorted(
        (
            "packages/answer/software_world_model/interface/world_model_product.py",
            "packages/gateway/.g3b/gateway_authorized_workload.py",
        )
    )
    if changed != expected:
        raise FreezeFailure(f"candidate stage changed unexpected paths: {changed}")
    return _value_digest(candidate_manifest), changed


def _pom(
    *,
    group: str,
    artifact: str,
    modules: Sequence[str] = (),
    dependencies: Sequence[tuple[str, str]] = (),
) -> str:
    modules_xml = "".join(f"<module>{item}</module>" for item in modules)
    dependencies_xml = "".join(
        (
            "<dependency>"
            f"<groupId>{dependency_group}</groupId>"
            f"<artifactId>{dependency_artifact}</artifactId>"
            "<version>1.0.0</version>"
            "</dependency>"
        )
        for dependency_group, dependency_artifact in dependencies
    )
    return (
        '<project xmlns="http://maven.apache.org/POM/4.0.0">'
        "<modelVersion>4.0.0</modelVersion>"
        f"<groupId>{group}</groupId><artifactId>{artifact}</artifactId>"
        "<version>1.0.0</version>"
        + ("<packaging>pom</packaging>" if modules else "")
        + (f"<modules>{modules_xml}</modules>" if modules else "")
        + (
            f"<dependencies>{dependencies_xml}</dependencies>"
            if dependencies
            else ""
        )
        + "</project>"
    )


def _write_revision(
    repository: Path,
    *,
    root_group: str,
    root_artifact: str,
    modules: Sequence[Mapping[str, object]],
) -> None:
    active = {str(item["path"]) for item in modules}
    for child in tuple(path for path in repository.iterdir() if path.is_dir() and path.name != ".git"):
        if not any(name == child.name or name.startswith(child.name + "/") for name in active):
            shutil.rmtree(child)
    (repository / "pom.xml").write_text(
        _pom(
            group=root_group,
            artifact=root_artifact,
            modules=[str(item["path"]) for item in modules],
        ),
        encoding="utf-8",
    )
    for item in modules:
        path = repository / str(item["path"])
        path.mkdir(parents=True, exist_ok=True)
        (path / "pom.xml").write_text(
            _pom(
                group=str(item["group"]),
                artifact=str(item["artifact"]),
                dependencies=tuple(item["dependencies"]),
            ),
            encoding="utf-8",
        )


def _invoke_json(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    commands: list[dict[str, object]],
) -> dict[str, object]:
    completed = _run(command, cwd=cwd, environment=environment)
    commands.append(
        {
            "argv": list(command),
            "exit_code": completed.returncode,
            "stdout_sha256": _value_digest(completed.stdout),
            "stderr_sha256": _value_digest(completed.stderr),
        }
    )
    value = json.loads(completed.stdout)
    if not isinstance(value, dict):
        raise FreezeFailure("public CLI did not return a JSON object")
    return value


def _workspace_fixture(
    *,
    workspace: Path,
    producer: Path,
    identity: Mapping[str, str],
    output: Path,
    seed: str,
) -> tuple[dict[str, object], dict[str, object], list[dict[str, object]]]:
    suffix = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8]
    root_group = f"org.generated.r{suffix}"
    root_artifact = f"reactor-{suffix}"
    artifacts = {
        "core": f"core-{suffix}",
        "api": f"api-{suffix}",
        "cli": f"cli-{suffix}",
        "shared": f"shared-{suffix}",
        "worker": f"worker-{suffix}",
        "missing": f"missing-{suffix}",
    }
    alpha_group = f"{root_group}.alpha"
    beta_group = f"{root_group}.beta"
    r1 = [
        {"path": f"libraries/{artifacts['core']}", "group": root_group, "artifact": artifacts["core"], "dependencies": ()},
        {"path": f"services/{artifacts['api']}", "group": root_group, "artifact": artifacts["api"], "dependencies": ((root_group, artifacts["core"]),)},
        {"path": f"tools/{artifacts['cli']}", "group": root_group, "artifact": artifacts["cli"], "dependencies": ((root_group, artifacts["api"]),)},
        {"path": f"alpha/{artifacts['shared']}", "group": alpha_group, "artifact": artifacts["shared"], "dependencies": ((root_group, artifacts["core"]),)},
        {"path": f"beta/{artifacts['shared']}", "group": beta_group, "artifact": artifacts["shared"], "dependencies": ((root_group, artifacts["core"]),)},
    ]
    r2 = [
        r1[0],
        {"path": r1[1]["path"], "group": root_group, "artifact": artifacts["api"], "dependencies": ((alpha_group, artifacts["shared"]),)},
        r1[3],
        r1[4],
        {"path": f"jobs/{artifacts['worker']}", "group": root_group, "artifact": artifacts["worker"], "dependencies": ((root_group, artifacts["api"]), (beta_group, artifacts["shared"]))},
    ]
    repository = output / "source-repository"
    repository.mkdir()
    _write_revision(
        repository,
        root_group=root_group,
        root_artifact=root_artifact,
        modules=r1,
    )
    _git(repository, "init", "-q")
    _git(repository, "config", "user.email", "slice2-fixture@example.invalid")
    _git(repository, "config", "user.name", "SLICE-002 Fixture")
    _git(repository, "add", ".")
    _git(repository, "commit", "-q", "-m", "R1")
    revision_1 = _git(repository, "rev-parse", "HEAD")

    database = output / "authority.sqlite3"
    bundle_root = output / "bundles"
    catalog_root = output / "catalog"
    environment = dict(os.environ)
    environment["PYTHONPATH"] = f"{producer / 'src'}:{workspace}"
    commands: list[dict[str, object]] = []
    base = (
        sys.executable,
        "-m",
        "software_world_model.interface.cli",
        "--database", str(database),
        "--bundle-root", str(bundle_root),
        "--catalog-root", str(catalog_root),
        "--producer-commit", identity["commit"],
        "--producer-tree", identity["tree"],
    )
    registered = _invoke_json(
        (*base, "register-maven-workspace", "--idempotency-key", "slice2-register", "--source-target", str(repository), "--display-name", f"Generated Reactor {suffix}", "--canonical-system-key", f"generated:slice2:{suffix}", "--root-pom", "pom.xml", "--actor", "validation", "--correlation-ref", "slice2-register"),
        cwd=workspace,
        environment=environment,
        commands=commands,
    )
    workspace_id = str(registered["workspace"]["workspace_id"])
    _invoke_json(
        (*base, "update-maven-workspace", "--workspace-id", workspace_id, "--repository-revision", revision_1, "--idempotency-key", "slice2-r1", "--correlation-ref", "slice2-r1"),
        cwd=workspace,
        environment=environment,
        commands=commands,
    )

    _write_revision(
        repository,
        root_group=root_group,
        root_artifact=root_artifact,
        modules=r2,
    )
    _git(repository, "add", "-A")
    _git(repository, "commit", "-q", "-m", "R2")
    revision_2 = _git(repository, "rev-parse", "HEAD")
    _invoke_json(
        (*base, "update-maven-workspace", "--workspace-id", workspace_id, "--repository-revision", revision_2, "--idempotency-key", "slice2-r2", "--correlation-ref", "slice2-r2"),
        cwd=workspace,
        environment=environment,
        commands=commands,
    )
    catalog = _invoke_json(
        (
            sys.executable,
            "-m",
            "software_world_model.interface.read_set_catalog_cli",
            "--catalog-root", str(catalog_root),
            "--bundle-root", str(bundle_root),
            "list-read-sets",
        ),
        cwd=workspace,
        environment=environment,
        commands=commands,
    )
    read_sets = catalog["read_sets"]
    r1_entry = next(item for item in read_sets if item["source_revisions"] == [revision_1])
    r2_entry = next(item for item in read_sets if item["source_revisions"] == [revision_2])
    ordered = next(item for item in read_sets if item["source_revisions"] == [revision_1, revision_2])
    fixture = {
        "seed": seed,
        "suffix": suffix,
        "workspace_id": workspace_id,
        "repository": str(repository),
        "database": str(database),
        "bundle_root": str(bundle_root),
        "catalog_root": str(catalog_root),
        "root_group": root_group,
        "root_artifact": root_artifact,
        "artifacts": artifacts,
        "groups": {"alpha": alpha_group, "beta": beta_group},
        "revisions": {"r1": revision_1, "r2": revision_2},
        "read_sets": {
            "r1": r1_entry["read_set_id"],
            "r2": r2_entry["read_set_id"],
            "ordered": ordered["read_set_id"],
        },
        "modules": {"r1": r1, "r2": r2},
    }
    return fixture, catalog, commands


def _git_blob(repository: Path, revision: str, path: str) -> bytes:
    completed = subprocess.run(
        ("git", "-C", str(repository), "show", f"{revision}:{path}"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout:
        raise FreezeFailure(f"source closure blob is unavailable: {revision}:{path}")
    return completed.stdout


def _sealed_source_snapshot(
    *,
    repository: Path,
    label: str,
    revision: str,
    modules: object,
) -> dict[str, object]:
    if not isinstance(modules, list):
        raise FreezeFailure("source closure modules are invalid")
    paths = ["pom.xml"]
    for module in modules:
        if not isinstance(module, dict) or not isinstance(module.get("path"), str):
            raise FreezeFailure("source closure module is invalid")
        paths.append(f"{module['path']}/pom.xml")
    if len(paths) != len(set(paths)):
        raise FreezeFailure("source closure paths repeat")
    files: list[dict[str, object]] = []
    for path in sorted(paths):
        raw = _git_blob(repository, revision, path)
        files.append(
            {
                "path": path,
                "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "size": len(raw),
            }
        )
    return {"label": label, "revision": revision, "files": files}


def _source_closures(fixture: Mapping[str, object]) -> dict[str, object]:
    repository = Path(str(fixture["repository"])).resolve(strict=True)
    revisions = fixture["revisions"]
    read_sets = fixture["read_sets"]
    modules = fixture["modules"]
    assert isinstance(revisions, dict)
    assert isinstance(read_sets, dict)
    assert isinstance(modules, dict)
    first = _sealed_source_snapshot(
        repository=repository,
        label="A",
        revision=str(revisions["r1"]),
        modules=modules["r1"],
    )
    second_as_a = _sealed_source_snapshot(
        repository=repository,
        label="A",
        revision=str(revisions["r2"]),
        modules=modules["r2"],
    )
    second_as_b = {**second_as_a, "label": "B"}
    return {
        str(read_sets["r1"]): {"snapshots": [first]},
        str(read_sets["r2"]): {"snapshots": [second_as_a]},
        str(read_sets["ordered"]): {"snapshots": [first, second_as_b]},
    }


def _comparison_protocols(runner: Path) -> dict[str, object]:
    if _PROVIDER != slice2_evaluator._PROVIDER:
        raise FreezeFailure("Provider comparison identity drifted")
    mature_agent = json.loads(_canonical(slice2_evaluator._MATURE_AGENT))
    runner_digest = _sha(runner)
    return {
        "execution_order": [
            "CONTROLLED_DIRECT",
            "MATURE_SOURCE_AGENT",
            "SEAL_BASELINE_POPULATIONS",
            "WORLD_MODEL",
        ],
        "failure_policy": (
            "PRESERVE_ALL_TERMINALS_NO_RETRY_NO_SELECTION_NO_INTERPOLATION"
        ),
        "runs_per_case": 1,
        "WORLD_MODEL": {
            "entrypoint": "software_world_model.interface.world_model_http",
            "provider": dict(_PROVIDER),
            "payload_boundary": (
                "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
            ),
            "external_task_count_per_case": 1,
            "provider_call_count_observability": (
                "EXACT_PRODUCT_GATEWAY_COUNTER_ON_VERIFIED_TERMINAL"
            ),
            "provider_call_count_per_case": 1,
            "controller_retry_count_per_case": 0,
            "result_visibility": "AFTER_BOTH_BASELINE_POPULATIONS_ARE_SEALED",
            "production_activation": "NOT_EXECUTED",
        },
        "CONTROLLED_DIRECT": {
            "runner_path": (
                "validation/structure_world_model_iteration_005/"
                "slice2_comparison.py"
            ),
            "runner_digest": runner_digest,
            "provider": dict(_PROVIDER),
            "payload_boundary": (
                "ORIGINAL_QUESTION_AND_EXACT_SEALED_POM_SOURCE_CLOSURE"
            ),
            "external_task_count_per_case": 1,
            "provider_call_count_observability": (
                "EXACT_DIRECT_GATEWAY_COUNTER_ON_TERMINAL"
            ),
            "provider_call_count_per_case": 1,
            "controller_retry_count_per_case": 0,
            "max_output_tokens_per_case": (
                slice2_comparison._DIRECT_MAX_OUTPUT_TOKENS
            ),
            "response_contract": slice2_comparison._DIRECT_RESPONSE_CONTRACT,
            "oracle_visibility": "NONE",
            "result_visibility": "SEALED_BEFORE_FIRST_WORLD_MODEL_RESULT",
            "production_activation": "NOT_EXECUTED",
        },
        "MATURE_SOURCE_AGENT": {
            "runner_path": (
                "validation/structure_world_model_iteration_005/"
                "slice2_comparison.py"
            ),
            "runner_digest": runner_digest,
            "agent": mature_agent,
            "payload_boundary": (
                "ORIGINAL_QUESTION_AND_EXACT_SEALED_POM_SOURCE_CLOSURE"
            ),
            "external_task_count_per_case": 1,
            "provider_call_count_observability": (
                "UNOBSERVABLE_FROM_CODEX_CLI_EVENT_BOUNDARY"
            ),
            "provider_call_count_per_case": None,
            "controller_retry_count_per_case": 0,
            "oracle_visibility": "NONE",
            "result_visibility": "SEALED_BEFORE_FIRST_WORLD_MODEL_RESULT",
            "production_activation": "NOT_EXECUTED",
        },
    }


def _oracle_and_suite(
    output: Path,
    fixture: Mapping[str, object],
    catalog: Mapping[str, object],
    identity: Mapping[str, str],
    evaluator: Path,
    comparison_runner: Path,
) -> tuple[Path, Path]:
    groups = fixture["groups"]
    artifacts = fixture["artifacts"]
    root_group = str(fixture["root_group"])
    ga = {
        "core": f"{root_group}:{artifacts['core']}",
        "api": f"{root_group}:{artifacts['api']}",
        "cli": f"{root_group}:{artifacts['cli']}",
        "worker": f"{root_group}:{artifacts['worker']}",
        "shared_alpha": f"{groups['alpha']}:{artifacts['shared']}",
        "shared_beta": f"{groups['beta']}:{artifacts['shared']}",
    }
    oracle_core = {
        "schema": ORACLE_SCHEMA,
        "fixture_seed": fixture["seed"],
        "revisions": fixture["revisions"],
        "read_sets": fixture["read_sets"],
        "r1_modules": [ga["core"], ga["api"], ga["cli"], ga["shared_alpha"], ga["shared_beta"]],
        "r2_modules": [ga["core"], ga["api"], ga["worker"], ga["shared_alpha"], ga["shared_beta"]],
        "r1_dependencies": [[ga["api"], ga["core"]], [ga["cli"], ga["api"]], [ga["shared_alpha"], ga["core"]], [ga["shared_beta"], ga["core"]]],
        "r2_dependencies": [[ga["api"], ga["shared_alpha"]], [ga["worker"], ga["api"]], [ga["worker"], ga["shared_beta"]], [ga["shared_alpha"], ga["core"]], [ga["shared_beta"], ga["core"]]],
        "same_artifact_candidates": [ga["shared_alpha"], ga["shared_beta"]],
        "production_activation": "NOT_EXECUTED",
    }
    oracle = _document(ORACLE_SCHEMA, oracle_core)
    oracle_path = output / "oracle.json"
    _write(oracle_path, oracle)
    reads = fixture["read_sets"]
    cases = [
        {"case_id": "WM-005-001", "read_set_id": reads["r1"], "question": "列出这个 exact Snapshot 中全部递归 reactor 子模块。", "expected_outcome": "SUPPORTED", "required_tokens": oracle_core["r1_modules"], "forbidden_tokens": [ga["worker"]], "outcome_markers_any": []},
        {"case_id": "WM-005-002", "read_set_id": reads["r2"], "question": f"`{artifacts['worker']}` 是否直接依赖 `{artifacts['api']}` 和 `{artifacts['shared']}`？", "expected_outcome": "SUPPORTED", "required_tokens": [ga["worker"], ga["api"], ga["shared_alpha"], ga["shared_beta"]], "forbidden_tokens": [ga["cli"]], "outcome_markers_any": []},
        {"case_id": "WM-005-003", "read_set_id": reads["r2"], "question": f"列出 `{artifacts['worker']}` 到 `{artifacts['core']}` 的全部简单内部依赖路径。", "expected_outcome": "SUPPORTED", "required_tokens": [ga["worker"], ga["api"], ga["shared_alpha"], ga["shared_beta"], ga["core"]], "forbidden_tokens": [ga["cli"]], "outcome_markers_any": []},
        {"case_id": "WM-005-004", "read_set_id": reads["r2"], "question": f"{ga['shared_alpha']} 到 {ga['worker']} 是否存在本 Profile 内的内部依赖路径？", "expected_outcome": "SUPPORTED_NEGATIVE", "required_tokens": [ga["shared_alpha"], ga["worker"]], "forbidden_tokens": ["路径存在"], "outcome_markers_any": ["不存在", "no path", "does not exist"]},
        {"case_id": "WM-005-005", "read_set_id": reads["ordered"], "question": "列出 A 和 B 各自的 reactor 子模块，并说明 A 到 B 的节点和边的增删变化。", "expected_outcome": "SUPPORTED", "required_tokens": [ga["cli"], ga["worker"], ga["api"], ga["core"]], "forbidden_tokens": [], "outcome_markers_any": []},
        {"case_id": "WM-005-006", "read_set_id": reads["ordered"], "question": f"分别列出 A 和 B 中 `{artifacts['api']}` 到 `{artifacts['core']}` 的全部简单内部依赖路径，并指出新增路径变化。", "expected_outcome": "SUPPORTED", "required_tokens": [ga["api"], ga["shared_alpha"], ga["core"]], "forbidden_tokens": [], "outcome_markers_any": []},
        {"case_id": "WM-005-007", "read_set_id": reads["r2"], "question": f"同名 artifact `{artifacts['shared']}` 有哪些候选？", "expected_outcome": "ENTITY_RESOLUTION_LIMITATION", "required_tokens": ["AMBIGUOUS", ga["shared_alpha"], ga["shared_beta"]], "forbidden_tokens": ["next_operation_allowed\":true"], "outcome_markers_any": ["limitation", "限制"]},
        {"case_id": "WM-005-008", "read_set_id": reads["r2"], "question": f"同名 artifact `{artifacts['missing']}` 有哪些候选？", "expected_outcome": "ENTITY_RESOLUTION_LIMITATION", "required_tokens": ["ZERO", artifacts["missing"]], "forbidden_tokens": ["next_operation_allowed\":true"], "outcome_markers_any": ["limitation", "限制"]},
        {"case_id": "WM-005-009", "read_set_id": reads["r2"], "question": f"为什么 `{artifacts['api']}` 改用这个依赖？请结合 Maven plugin、parent 和设计动机解释。", "expected_outcome": "KNOWLEDGE_GAP", "required_tokens": ["Knowledge Gap"], "forbidden_tokens": ["确定是因为"], "outcome_markers_any": ["knowledge gap", "无法", "cannot"]},
    ]
    suite_core = {
        "schema": SUITE_SCHEMA,
        "environment": "EVALUATION_ONLY",
        "evaluation_subject_commit": identity["commit"],
        "evaluation_subject_tree": identity["tree"],
        "sealed_before_world_model_results": True,
        "world_model_result_count_at_seal": 0,
        "controlled_direct_result_count_at_seal": 0,
        "mature_source_agent_result_count_at_seal": 0,
        "fixture": {key: fixture[key] for key in ("seed", "suffix", "workspace_id", "revisions", "read_sets")},
        "catalog_digest": catalog["catalog_digest"],
        "product_oracle_digest": oracle["document_digest"],
        "independent_evaluator_digest": _sha(evaluator),
        "comparison_surfaces": ["WORLD_MODEL", "CONTROLLED_DIRECT", "MATURE_SOURCE_AGENT"],
        "comparison_protocols": _comparison_protocols(comparison_runner),
        "source_closures": _source_closures(fixture),
        "cases": cases,
        "production_activation": "NOT_EXECUTED",
    }
    suite = _document(SUITE_SCHEMA, suite_core)
    suite_path = output / "held-out-suite.json"
    _write(suite_path, suite)
    return oracle_path, suite_path


def _launcher_files(producer: Path) -> dict[str, Path]:
    interface = producer / "src/software_world_model/interface"
    assets = interface / "world_model_runtime_assets"
    return {
        "world_model_runtime.py": interface / "world_model_runtime.py",
        "world_model_http.py": interface / "world_model_http.py",
        "world_model_browser.py": interface / "world_model_browser.py",
        "world_model_browser_ui.py": interface / "world_model_browser_ui.py",
        "runtime_assets/answer.sb": assets / "answer.sb",
        "runtime_assets/gateway.sb": assets / "gateway.sb",
        "runtime_assets/gateway_authorized_workload.py": assets / "gateway_authorized_workload.py",
        "runtime_assets/projector.sb": assets / "projector.sb",
        "runtime_assets/role_worker.py": assets / "role_worker.py",
        "runtime_assets/os_probe_worker.py": assets / "os_probe_worker.py",
        "runtime_assets/provider_socket_worker.py": assets / "provider_socket_worker.py",
    }


def _test_result(
    command: Sequence[str],
    *,
    workspace: Path,
    environment: Mapping[str, str],
) -> dict[str, object]:
    completed = _run(command, cwd=workspace, environment=environment)
    combined = completed.stdout + completed.stderr
    match = _TEST_COUNT.search(combined)
    return {
        "argv": list(command),
        "pass": True,
        "test_count": int(match.group(1)) if match else None,
        "stdout_sha256": _value_digest(completed.stdout),
        "stderr_sha256": _value_digest(completed.stderr),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--output", required=True)
    parser.add_argument("--baseline-stage", required=True)
    parser.add_argument("--baseline-stage-digest", required=True)
    parser.add_argument("--seed")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    workspace = Path(arguments.workspace).resolve(strict=True)
    output = Path(arguments.output)
    if not output.is_absolute():
        output = workspace / output
    if output.exists() or output.is_symlink():
        raise FreezeFailure("output root must not already exist")
    output.mkdir(parents=True, mode=0o700)
    producer = output / "producer-source"
    producer.mkdir()
    identity = _source_snapshot(workspace, producer)
    stage = output / "candidate-stage"
    stage_digest, stage_changes = _candidate_stage(
        Path(arguments.baseline_stage).resolve(strict=True),
        arguments.baseline_stage_digest,
        producer,
        stage,
    )
    seed = arguments.seed or secrets.token_hex(16)
    fixture, catalog, commands = _workspace_fixture(
        workspace=workspace,
        producer=producer,
        identity=identity,
        output=output,
        seed=seed,
    )
    evaluator = (
        workspace
        / "validation/structure_world_model_iteration_005/slice2_evaluator.py"
    ).resolve(strict=True)
    comparison_runner = (
        workspace
        / "validation/structure_world_model_iteration_005/slice2_comparison.py"
    ).resolve(strict=True)
    oracle, suite = _oracle_and_suite(
        output,
        fixture,
        catalog,
        identity,
        evaluator,
        comparison_runner,
    )
    suite_document = json.loads(suite.read_text(encoding="utf-8"))
    comparison_authorization = output / "comparison-authorization.NOT_AUTHORIZED.json"
    _write(
        comparison_authorization,
        slice2_comparison.pending_authorization(suite_document),
    )
    mature_schema = output / "mature-agent-answer-schema.json"
    _write(mature_schema, slice2_comparison._MATURE_OUTPUT_SCHEMA)
    if _sha(mature_schema) != slice2_evaluator._MATURE_AGENT["answer_schema_sha256"]:
        raise FreezeFailure("mature Agent answer schema digest drifted")
    mature_workspace = output / "mature-agent-parse-smoke"
    mature_workspace.mkdir()
    mature_last_message = output / "mature-agent-parse-smoke.last-message.json"
    mature_command = slice2_comparison._mature_command(
        workspace=mature_workspace,
        schema=mature_schema,
        last_message=mature_last_message,
        prompt="PARSE_SMOKE_ONLY",
    )
    mature_command[-1] = "--help"
    mature_parse = _run(mature_command, cwd=workspace)
    mature_binary = Path(
        str(slice2_evaluator._MATURE_AGENT["binary_path"])
    ).resolve(strict=True)
    mature_version = _run((str(mature_binary), "--version"), cwd=workspace)
    if (
        _sha(mature_binary)
        != slice2_evaluator._MATURE_AGENT["binary_sha256"]
        or mature_version.stdout.strip()
        != slice2_evaluator._MATURE_AGENT["version"]
        or "Run Codex non-interactively" not in mature_parse.stdout
    ):
        raise FreezeFailure("mature Agent exact binary or argv parse smoke drifted")
    environment = dict(os.environ)
    environment["PYTHONPATH"] = f"{producer / 'src'}:{workspace}"
    environment["PYTHONWARNINGS"] = "ignore"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    blocked_comparison_output = output / "blocked-comparison"
    blocked_comparison = _run(
        (
            sys.executable,
            "-B",
            "-m",
            "validation.structure_world_model_iteration_005.slice2_comparison",
            "run-controlled-direct",
            "--suite",
            str(suite),
            "--source-repository",
            str(fixture["repository"]),
            "--authorization",
            str(comparison_authorization),
            "--conformance-result",
            str(stage / "gateway-input/conformance.json"),
            "--output",
            str(blocked_comparison_output),
        ),
        cwd=workspace,
        environment=environment,
        expect=2,
    )
    if (
        "exact comparison disclosure is not explicitly authorized"
        not in blocked_comparison.stderr
        or blocked_comparison_output.exists()
    ):
        raise FreezeFailure("comparison authorization did not fail before dispatch")
    probe = output / "adapter-probe.json"
    _run(
        (
            sys.executable,
            "-m",
            "validation.structure_world_model_iteration_005.slice2_probe",
            "--database", fixture["database"],
            "--catalog-root", fixture["catalog_root"],
            "--bundle-root", fixture["bundle_root"],
            "--implementation-commit", identity["commit"],
            "--implementation-tree", identity["tree"],
            "--output", str(probe),
        ),
        cwd=workspace,
        environment=environment,
    )
    product_probe = output / "deterministic-product-probe.json"
    _run(
        (
            sys.executable,
            "-B",
            "-m",
            "validation.structure_world_model_iteration_005.slice2_product_probe",
            "--suite", str(suite),
            "--catalog-root", fixture["catalog_root"],
            "--bundle-root", fixture["bundle_root"],
            "--output", str(product_probe),
        ),
        cwd=workspace,
        environment=environment,
    )
    focused = _test_result(
        (
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "tests.test_world_model_http",
            "tests.test_world_model_browser",
            "tests.test_iteration_004_interactive_browser",
            "tests.test_world_model_gateway_authorization",
            "tests.test_world_model_evaluation_grant",
            "tests.test_world_model_product",
            "tests.test_iteration_005_slice2_evaluator",
            "tests.test_iteration_005_slice2_comparison",
        ),
        workspace=workspace,
        environment=environment,
    )
    candidate_answer_environment = dict(environment)
    candidate_answer_environment["PYTHONPATH"] = (
        f"{stage / 'packages/answer'}:{workspace}"
    )
    candidate_answer = _test_result(
        (
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "tests.test_world_model_product",
        ),
        workspace=workspace,
        environment=candidate_answer_environment,
    )
    full = _test_result(
        (
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-q",
        ),
        workspace=workspace,
        environment=environment,
    )
    docs = _run(
        (sys.executable, "scripts/docs.py", "check"),
        cwd=workspace,
        environment=environment,
    )
    docs_result = {
        "argv": [sys.executable, "scripts/docs.py", "check"],
        "pass": True,
        "stdout_sha256": _value_digest(docs.stdout),
        "stderr_sha256": _value_digest(docs.stderr),
    }
    launcher_hashes = {
        label: _raw_sha(path) for label, path in _launcher_files(producer).items()
    }
    launcher_manifest_digest = _value_digest(
        ["SWM-WORLD-MODEL-LAUNCHER-MANIFEST@1", launcher_hashes]
    )
    if _value_digest(_tree_manifest(stage)) != stage_digest:
        raise FreezeFailure("candidate stage changed during deterministic tests")
    qualification_core = {
        "schema": QUALIFICATION_SCHEMA,
        "status": "PASS",
        "evaluation_subject_status": "CANDIDATE",
        "implementation_commit": identity["commit"],
        "implementation_tree": identity["tree"],
        "stage_manifest_digest": stage_digest,
        "launcher_manifest_digest": launcher_manifest_digest,
        "held_out_suite_digest": json.loads(suite.read_text())["document_digest"],
        "independent_evaluator_digest": _sha(evaluator),
        "comparison_runner_digest": _sha(comparison_runner),
        "comparison_protocols_sealed": True,
        "comparison_authorization_digest": json.loads(
            comparison_authorization.read_text(encoding="utf-8")
        )["document_digest"],
        "comparison_authorization_status": "NOT_AUTHORIZED",
        "comparison_unauthorized_pre_dispatch_pass": True,
        "mature_agent_binary_digest": _sha(mature_binary),
        "mature_agent_version": mature_version.stdout.strip(),
        "mature_agent_argv_parse_pass": True,
        "mature_agent_argv_parse_stdout_sha256": _value_digest(
            mature_parse.stdout
        ),
        "adapter_probe_digest": json.loads(probe.read_text())["document_digest"],
        "deterministic_product_probe_digest": json.loads(
            product_probe.read_text()
        )["document_digest"],
        "focused_tests_pass": True,
        "deterministic_product_probe_pass": True,
        "candidate_answer_package_tests_pass": True,
        "full_regression_pass": True,
        "docs_check_pass": True,
        "focused_test_result": focused,
        "candidate_answer_package_test_result": candidate_answer,
        "full_regression_result": full,
        "docs_check_result": docs_result,
        "external_model_called": False,
        "production_activation": "NOT_EXECUTED",
    }
    qualification = _document(QUALIFICATION_SCHEMA, qualification_core)
    qualification_path = output / "deterministic-qualification.json"
    _write(qualification_path, qualification)
    baseline_placeholder = output / "baseline-results-at-seal.json"
    _write(
        baseline_placeholder,
        {
            "schema": "SWM-WORLD-MODEL-BASELINE-PLACEHOLDER@1",
            "result_count": 0,
            "sealed_before_world_model_results": True,
            "production_activation": "NOT_EXECUTED",
        },
    )
    gateway_input = stage / "gateway-input"
    gateway_hashes = {
        name: _raw_sha(gateway_input / name) for name in sorted(_GATEWAY_INPUT_FILES)
    }
    packages = stage / "packages"
    role_hashes = {
        role: _raw_sha(packages / role / relative)
        for role, relative in _ROLE_ENTRYPOINTS.items()
    }
    disclosure_core = {
        "status": "NOT_AUTHORIZED",
        "authorized_by": "user",
        "authorized_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "authorization_ref": "PENDING_EXPLICIT_USER_DISCLOSURE_AUTHORIZATION",
        "payload_boundary": "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE",
    }
    disclosure = _document(DISCLOSURE_SCHEMA, disclosure_core)
    subject = {
        "status": "CANDIDATE",
        "commit": identity["commit"],
        "tree": identity["tree"],
        "stage_root": str(stage.resolve(strict=True)),
        "stage_manifest_digest": stage_digest,
        "deterministic_qualification": _reference(qualification_path, document=True),
        "held_out_suite": _reference(suite, document=True),
        "independent_evaluator": _reference(evaluator, document=False),
        "gateway_input_sha256": gateway_hashes,
        "role_entrypoint_sha256": role_hashes,
    }
    grant_core = {
        "schema": GRANT_SCHEMA,
        "environment": "EVALUATION_ONLY",
        "live_dispatch_authorized": False,
        "disclosure_authorization": disclosure,
        "evaluation_subject": subject,
        "provider": _PROVIDER,
        "launcher_files": launcher_hashes,
        "forbidden_inputs": {
            "product_oracle": _reference(oracle, document=False),
            "baseline_result": _reference(baseline_placeholder, document=False),
            "independent_evaluator": _reference(evaluator, document=False),
        },
        "production_activation": "NOT_EXECUTED",
    }
    grant = _document(GRANT_SCHEMA, grant_core)
    grant_path = output / "evaluation-grant.NOT_AUTHORIZED.json"
    _write(grant_path, grant)
    blocked_session = output / "blocked-session"
    blocked_sockets = output / "blocked-sockets"
    blocked = _run(
        (
            sys.executable,
            "-m",
            "software_world_model.interface.world_model_http",
            "--database", fixture["database"],
            "--catalog-root", fixture["catalog_root"],
            "--bundle-root", fixture["bundle_root"],
            "--evaluation-grant", str(grant_path),
            "--session-root", str(blocked_session),
            "--socket-root", str(blocked_sockets),
        ),
        cwd=workspace,
        environment=environment,
        expect=1,
    )
    if (
        "LIVE_DISPATCH_NOT_AUTHORIZED" not in blocked.stderr
        or blocked_session.exists()
        or blocked_sockets.exists()
    ):
        raise FreezeFailure("unauthorized product command did not fail before startup")
    _write(output / "commands.json", commands)
    report_core = {
        "schema": REPORT_SCHEMA,
        "status": "PASS",
        "evaluation_subject_status": "CANDIDATE",
        "producer": identity,
        "candidate_stage_manifest_digest": stage_digest,
        "candidate_stage_changed_paths": stage_changes,
        "launcher_manifest_digest": launcher_manifest_digest,
        "fixture": {key: fixture[key] for key in ("seed", "suffix", "workspace_id", "revisions", "read_sets")},
        "catalog_digest": catalog["catalog_digest"],
        "held_out_suite_digest": json.loads(suite.read_text())["document_digest"],
        "independent_evaluator_digest": _sha(evaluator),
        "comparison_runner_digest": _sha(comparison_runner),
        "comparison_authorization_digest": json.loads(
            comparison_authorization.read_text(encoding="utf-8")
        )["document_digest"],
        "comparison_authorization": "NOT_AUTHORIZED_NOT_EXECUTED",
        "comparison_unauthorized_pre_dispatch_gate": "PASS",
        "mature_agent_binary_digest": _sha(mature_binary),
        "mature_agent_version": mature_version.stdout.strip(),
        "mature_agent_argv_parse_gate": "PASS",
        "deterministic_qualification_digest": qualification["document_digest"],
        "adapter_probe_digest": json.loads(probe.read_text())["document_digest"],
        "deterministic_product_probe_digest": json.loads(
            product_probe.read_text()
        )["document_digest"],
        "focused_test_count": focused["test_count"],
        "candidate_answer_package_test_count": candidate_answer["test_count"],
        "full_regression_test_count": full["test_count"],
        "docs_check": "PASS",
        "unauthorized_prelisten_gate": "PASS",
        "live_external_dispatch": "NOT_AUTHORIZED_NOT_EXECUTED",
        "production_activation": "NOT_EXECUTED",
    }
    report = _document(REPORT_SCHEMA, report_core)
    _write(output / "report.json", report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
