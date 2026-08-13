"""Freeze and deterministically qualify the ITER-006 Java live candidate."""

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
from typing import Mapping, Sequence

from software_world_model.ai_infrastructure import (
    VolcengineArkModelConfiguration,
    load_ark_chat_conformance_qualification,
)
from software_world_model.ai_infrastructure.java_model_egress_qualification import (
    JAVA_MODEL_EGRESS_POLICY_FILE_DIGEST,
    load_java_gateway_qualification_binding,
)

from . import live_comparison, live_evaluator
from validation.structure_world_model_iteration_005 import slice2_freeze as legacy


QUALIFICATION_SCHEMA = "SWM-WORLD-MODEL-DETERMINISTIC-QUALIFICATION@1"
SUITE_SCHEMA = live_evaluator.SUITE_SCHEMA
ORACLE_SCHEMA = "SWM-JAVA-WORLD-MODEL-HELD-OUT-ORACLE@1"
GRANT_SCHEMA = "SWM-WORLD-MODEL-EVALUATION-GRANT@2"
REPORT_SCHEMA = "SWM-JAVA-WORLD-MODEL-CANDIDATE-FREEZE@1"
DISCLOSURE_SCHEMA = "SWM-WORLD-MODEL-DISCLOSURE-AUTHORIZATION@1"
_TEST_COUNT = re.compile(r"Ran ([0-9]+) tests?")
_PROVIDER = live_evaluator._PROVIDER
_ROLE_ENTRYPOINTS = legacy._ROLE_ENTRYPOINTS
_GATEWAY_INPUT_FILES = legacy._GATEWAY_INPUT_FILES


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
        value["document_digest"] = str(json.loads(path.read_text())["document_digest"])
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


def _git(repository: Path, *arguments: str, environment=None) -> str:
    return _run(
        ("git", "-C", str(repository), *arguments),
        cwd=repository,
        environment=environment,
    ).stdout.strip()


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


def _source_snapshot(workspace: Path, destination: Path) -> dict[str, str]:
    shutil.copytree(
        workspace / "src",
        destination / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    shutil.copy2(workspace / "pyproject.toml", destination / "pyproject.toml")
    _git(destination, "init", "-q")
    _git(destination, "config", "user.email", "iter006-live@example.invalid")
    _git(destination, "config", "user.name", "ITER-006 Live Freeze")
    _git(destination, "add", "src", "pyproject.toml")
    _git(destination, "commit", "-q", "-m", "freeze ITER-006 candidate source")
    return {
        "commit": _git(destination, "rev-parse", "HEAD"),
        "tree": _git(destination, "rev-parse", "HEAD^{tree}"),
        "source_manifest_digest": _value_digest(_tree_manifest(destination / "src")),
    }


def _candidate_stage(baseline: Path, producer: Path, destination: Path):
    shutil.copytree(baseline, destination)
    package_root = destination / "packages"
    for role in ("answer", "broker", "gateway", "projector"):
        package = package_root / role
        source_package = producer / "src/software_world_model"
        target_package = package / "software_world_model"
        shutil.rmtree(target_package)
        shutil.copytree(source_package, target_package)
    shutil.copy2(
        producer
        / "src/software_world_model/interface/world_model_runtime_assets/"
        "gateway_authorized_workload.py",
        package_root / "gateway/.g3b/gateway_authorized_workload.py",
    )
    shutil.copy2(
        producer
        / "src/software_world_model/interface/world_model_runtime_assets/"
        "java_gateway_workload.py",
        package_root / "gateway/.g3b/java_gateway_workload.py",
    )
    return _value_digest(_tree_manifest(destination))


def _install_java_gateway_input(
    *,
    stage: Path,
    producer: Path,
    qualification_path: Path,
    closed_result_path: Path,
    conformance_result_path: Path,
) -> dict[str, object]:
    policy_path = (
        producer
        / "src/software_world_model/ai_infrastructure/"
        "java_model_egress_policy.json"
    ).resolve(strict=True)
    qualification = qualification_path.resolve(strict=True)
    closed = closed_result_path.resolve(strict=True)
    conformance_source = conformance_result_path.resolve(strict=True)
    binding = load_java_gateway_qualification_binding(
        qualification_path=qualification,
        closed_result_path=closed,
        policy_path=policy_path,
    )
    configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
        conformance_source, configuration
    )
    gateway_input = (stage / "gateway-input").resolve(strict=True)
    for source, name in (
        (conformance_source, "conformance.json"),
        (qualification, "qualification.json"),
        (closed, "closed-result.json"),
        (policy_path, "egress-policy.json"),
    ):
        target = gateway_input / name
        target.unlink()
        shutil.copy2(source, target)
    permission_digest = _value_digest(
        [
            "ITER-006-JAVA-PRODUCT-CAPABILITY-BASELINE@1",
            binding.capability_qualification_ref,
            binding.capability_qualification_digest.value,
        ]
    )
    freeze_core = {
        "schema": "SWM-ITER-006-JAVA-GATEWAY-FREEZE@1",
        "freeze_ref": "ITER-006-JAVA-PRODUCT-GATEWAY-CANDIDATE@1",
        "environment": "EVALUATION_ONLY",
        "strategy_ref": "model-snapshot-first-world-model-answer@1.1.0",
        "prompt_ref": "snapshot-first-world-model-proposal-prompt@4",
        "proposal_vocabulary_ref": "world-model-authority-proposal-vocabulary@2",
        "capability_qualification_document_digest": (
            binding.qualification_document_digest.value
        ),
        "closed_capability_result_digest": (
            binding.closed_capability_result_digest.value
        ),
        "egress_policy_digest": JAVA_MODEL_EGRESS_POLICY_FILE_DIGEST,
        "conformance_result_ref": conformance.result_ref,
        "conformance_result_digest": conformance.result_digest.value,
        "permission_digest": permission_digest,
        "production_activation": "NOT_EXECUTED",
    }
    freeze = _document(
        "SWM-ITER-006-JAVA-GATEWAY-FREEZE@1", freeze_core
    )
    freeze_path = gateway_input / "g3b-freeze.json"
    freeze_path.unlink()
    _write(freeze_path, freeze)
    return {
        "capability_qualification_ref": binding.capability_qualification_ref,
        "capability_qualification_digest": (
            binding.capability_qualification_digest.value
        ),
        "capability_qualification_document_digest": (
            binding.qualification_document_digest.value
        ),
        "closed_capability_result_digest": (
            binding.closed_capability_result_digest.value
        ),
        "conformance_result_ref": conformance.result_ref,
        "conformance_result_digest": conformance.result_digest.value,
        "java_gateway_freeze_digest": freeze["document_digest"],
        "permission_digest": permission_digest,
    }


def _fixture_repository(
    *, workspace: Path, output: Path, seed: str
) -> tuple[Path, dict[str, object]]:
    suffix = hashlib.sha256(seed.encode()).hexdigest()[:8]
    source = workspace / "validation/structure_world_model_iteration_006/fixtures"
    repository = output / "source-repository"
    repository.mkdir()
    environment = {
        **os.environ,
        "GIT_AUTHOR_DATE": "2026-08-12T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-08-12T00:00:00+00:00",
    }
    _git(repository, "init", "-q", "--object-format=sha1", environment=environment)
    _git(
        repository,
        "config",
        "user.email",
        "iter006-live-fixture@example.invalid",
        environment=environment,
    )
    _git(
        repository,
        "config",
        "user.name",
        "ITER-006 Live Fixture",
        environment=environment,
    )

    package = f"com.acme.live{suffix}"
    audit = f"Audit{suffix}"
    flow = f"Flow{suffix}"
    source_root = "src/main/java"

    def install(revision: str) -> None:
        root = repository / source_root / Path(*package.split("."))
        if (repository / "src").exists():
            shutil.rmtree(repository / "src")
        root.mkdir(parents=True)
        (root / f"{audit}.java").write_text(
            f"package {package};\n\n"
            f"public class {audit} {{\n"
            "    public static String record(String value) {\n"
            "        return value;\n"
            "    }\n"
            "}\n",
            encoding="utf-8",
        )
        if revision == "r1":
            body = (
                f"package {package};\n\n"
                f"public class {flow} {{\n"
                "    public String start(String input) {\n"
                "        // validate(input) and finish(input) are comment decoys.\n"
                f"        String decoy = \"{audit}.record(input)\";\n"
                f"        {audit}.record(input);\n"
                "        return validate(input);\n"
                "    }\n\n"
                "    private String validate(String input) {\n"
                "        return finish(input);\n"
                "    }\n\n"
                "    private String finish(String input) {\n"
                "        return input;\n"
                "    }\n"
                "}\n"
            )
        else:
            body = (
                f"package {package};\n\n"
                f"public class {flow} {{\n"
                "    public String start(String input) {\n"
                f"        {audit}.record(input);\n"
                "        return normalize(input);\n"
                "    }\n\n"
                "    private String normalize(String input) {\n"
                "        return validate(input);\n"
                "    }\n\n"
                "    private String validate(String input) {\n"
                "        return finish(input);\n"
                "    }\n\n"
                "    private String finish(String input) {\n"
                "        return input;\n"
                "    }\n"
                "}\n"
            )
        (root / f"{flow}.java").write_text(body, encoding="utf-8")

    install("r1")
    _git(repository, "add", ".", environment=environment)
    _git(repository, "commit", "-q", "-m", "R1", environment=environment)
    r1 = _git(repository, "rev-parse", "HEAD", environment=environment)
    install("r2")
    _git(repository, "add", "-A", environment=environment)
    _git(repository, "commit", "-q", "-m", "R2", environment=environment)
    r2 = _git(repository, "rev-parse", "HEAD", environment=environment)
    return repository, {
        "seed": seed,
        "suffix": suffix,
        "package": package,
        "audit_type": audit,
        "flow_type": flow,
        "source_root": source_root,
        "revisions": {"r1": r1, "r2": r2},
    }


def _invoke_json(command, *, cwd, environment, commands):
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
        raise FreezeFailure("public CLI did not return one JSON object")
    return value


def _workspace_fixture(
    *, workspace: Path, producer: Path, identity, output: Path, seed: str
):
    repository, fixture = _fixture_repository(
        workspace=workspace, output=output, seed=seed
    )
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
        "--database",
        str(database),
        "--bundle-root",
        str(bundle_root),
        "--catalog-root",
        str(catalog_root),
        "--producer-commit",
        identity["commit"],
        "--producer-tree",
        identity["tree"],
    )
    registered = _invoke_json(
        (
            *base,
            "register-maven-workspace",
            "--idempotency-key",
            "iter006-live-register",
            "--source-target",
            str(repository),
            "--display-name",
            f"Java Live Fixture {fixture['suffix']}",
            "--canonical-system-key",
            f"generated:iter006:{fixture['suffix']}",
            "--source-root",
            str(fixture["source_root"]),
            "--knowledge-profile",
            "JAVA_STATIC_CALL_GRAPH@1",
            "--actor",
            "validation",
            "--correlation-ref",
            "iter006-live-register",
        ),
        cwd=workspace,
        environment=environment,
        commands=commands,
    )
    workspace_id = str(registered["workspace"]["workspace_id"])
    for label in ("r1", "r2"):
        _invoke_json(
            (
                *base,
                "update-maven-workspace",
                "--workspace-id",
                workspace_id,
                "--repository-revision",
                fixture["revisions"][label],
                "--idempotency-key",
                f"iter006-live-{label}",
                "--correlation-ref",
                f"iter006-live-{label}",
            ),
            cwd=workspace,
            environment=environment,
            commands=commands,
        )
    catalog = _invoke_json(
        (
            sys.executable,
            "-m",
            "software_world_model.interface.read_set_catalog_cli",
            "--catalog-root",
            str(catalog_root),
            "--bundle-root",
            str(bundle_root),
            "list-read-sets",
        ),
        cwd=workspace,
        environment=environment,
        commands=commands,
    )
    read_sets = catalog["read_sets"]
    r1_entry = next(
        item
        for item in read_sets
        if item["source_revisions"] == [fixture["revisions"]["r1"]]
    )
    r2_entry = next(
        item
        for item in read_sets
        if item["source_revisions"] == [fixture["revisions"]["r2"]]
    )
    ordered = next(
        item
        for item in read_sets
        if item["source_revisions"]
        == [fixture["revisions"]["r1"], fixture["revisions"]["r2"]]
    )
    fixture.update(
        {
            "workspace_id": workspace_id,
            "repository": str(repository),
            "database": str(database),
            "bundle_root": str(bundle_root),
            "catalog_root": str(catalog_root),
            "read_sets": {
                "r1": r1_entry["read_set_id"],
                "r2": r2_entry["read_set_id"],
                "ordered": ordered["read_set_id"],
            },
        }
    )
    return fixture, catalog, commands


def _git_blob(repository: Path, revision: str, path: str) -> bytes:
    completed = subprocess.run(
        ("git", "-C", str(repository), "show", f"{revision}:{path}"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0 or not completed.stdout:
        raise FreezeFailure(f"source blob is unavailable: {revision}:{path}")
    return completed.stdout


def _source_closures(fixture: Mapping[str, object]) -> dict[str, object]:
    repository = Path(str(fixture["repository"])).resolve(strict=True)
    source_root = str(fixture["source_root"])
    package_path = str(fixture["package"]).replace(".", "/")
    paths = [
        f"{source_root}/{package_path}/{fixture['audit_type']}.java",
        f"{source_root}/{package_path}/{fixture['flow_type']}.java",
    ]

    def snapshot(label: str, revision: str) -> dict[str, object]:
        files = []
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

    revisions = fixture["revisions"]
    reads = fixture["read_sets"]
    assert isinstance(revisions, dict) and isinstance(reads, dict)
    r1 = snapshot("A", str(revisions["r1"]))
    r2_a = snapshot("A", str(revisions["r2"]))
    r2_b = {**r2_a, "label": "B"}
    return {
        str(reads["r1"]): {"snapshots": [r1]},
        str(reads["r2"]): {"snapshots": [r2_a]},
        str(reads["ordered"]): {"snapshots": [r1, r2_b]},
    }


def _comparison_protocols(
    runner: Path, provider: Mapping[str, object]
) -> dict[str, object]:
    mature = json.loads(_canonical(live_evaluator._MATURE_AGENT))
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
            "provider": dict(provider),
            "payload_boundary": "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE",
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
                "validation/structure_world_model_iteration_006/live_comparison.py"
            ),
            "runner_digest": runner_digest,
            "provider": dict(provider),
            "payload_boundary": (
                "ORIGINAL_QUESTION_AND_EXACT_SEALED_JAVA_SOURCE_CLOSURE"
            ),
            "external_task_count_per_case": 1,
            "provider_call_count_observability": (
                "EXACT_DIRECT_GATEWAY_COUNTER_ON_TERMINAL"
            ),
            "provider_call_count_per_case": 1,
            "controller_retry_count_per_case": 0,
            "max_output_tokens_per_case": live_comparison._DIRECT_MAX_OUTPUT_TOKENS,
            "response_contract": live_comparison._DIRECT_RESPONSE_CONTRACT,
            "oracle_visibility": "NONE",
            "result_visibility": "SEALED_BEFORE_FIRST_WORLD_MODEL_RESULT",
            "production_activation": "NOT_EXECUTED",
        },
        "MATURE_SOURCE_AGENT": {
            "runner_path": (
                "validation/structure_world_model_iteration_006/live_comparison.py"
            ),
            "runner_digest": runner_digest,
            "agent": mature,
            "payload_boundary": (
                "ORIGINAL_QUESTION_AND_EXACT_SEALED_JAVA_SOURCE_CLOSURE"
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
    output, fixture, catalog, identity, evaluator, runner, provider
):
    package = str(fixture["package"])
    audit = str(fixture["audit_type"])
    flow = str(fixture["flow_type"])
    audit_record = f"{package}.{audit}#record(String)"
    start = f"{package}.{flow}#start(String)"
    normalize = f"{package}.{flow}#normalize(String)"
    validate = f"{package}.{flow}#validate(String)"
    finish = f"{package}.{flow}#finish(String)"
    oracle_core = {
        "schema": ORACLE_SCHEMA,
        "fixture_seed": fixture["seed"],
        "revisions": fixture["revisions"],
        "read_sets": fixture["read_sets"],
        "r1_methods": [audit_record, start, validate, finish],
        "r2_methods": [audit_record, start, normalize, validate, finish],
        "r1_calls": [[start, audit_record], [start, validate], [validate, finish]],
        "r2_calls": [
            [start, audit_record],
            [start, normalize],
            [normalize, validate],
            [validate, finish],
        ],
        "production_activation": "NOT_EXECUTED",
    }
    oracle = _document(ORACLE_SCHEMA, oracle_core)
    oracle_path = output / "oracle.json"
    _write(oracle_path, oracle)
    reads = fixture["read_sets"]
    cases = [
        {
            "case_id": "WM-006-001",
            "read_set_id": reads["r1"],
            "question": f"`{flow}` 在这个 exact Snapshot 中有哪些方法？",
            "expected_outcome": "SUPPORTED",
            "required_tokens": [start, validate, finish],
            "forbidden_tokens": [normalize],
            "outcome_markers_any": ["JAVA_SOURCE_DECLARATION@1"],
        },
        {
            "case_id": "WM-006-002",
            "read_set_id": reads["r1"],
            "question": f"`{flow}#start(String)` 直接调用哪些方法？",
            "expected_outcome": "SUPPORTED",
            "required_tokens": [start, audit_record, validate],
            "forbidden_tokens": [normalize],
            "outcome_markers_any": ["JAVA_SOURCE_STATIC_CALL@1"],
        },
        {
            "case_id": "WM-006-003",
            "read_set_id": reads["r2"],
            "question": (
                f"列出 `{flow}#start(String)` 到 `{flow}#finish(String)` 的全部"
                "简单静态调用路径。"
            ),
            "expected_outcome": "SUPPORTED",
            "required_tokens": [start, normalize, validate, finish],
            "forbidden_tokens": [],
            "outcome_markers_any": ["静态调用路径", "static call path"],
        },
        {
            "case_id": "WM-006-004",
            "read_set_id": reads["r2"],
            "question": (
                f"`{audit}#record(String)` 到 `{flow}#finish(String)` 是否存在"
                "本 Profile 内的静态调用路径？"
            ),
            "expected_outcome": "SUPPORTED_NEGATIVE",
            "required_tokens": [audit_record, finish],
            "forbidden_tokens": ["路径存在"],
            "outcome_markers_any": ["不存在", "no path", "does not exist"],
        },
        {
            "case_id": "WM-006-005",
            "read_set_id": reads["ordered"],
            "question": "说明 A 到 B 的 Java 静态调用图变化。",
            "expected_outcome": "SUPPORTED",
            "required_tokens": [normalize, start, validate],
            "forbidden_tokens": [],
            "outcome_markers_any": ["added", "新增"],
        },
        {
            "case_id": "WM-006-006",
            "read_set_id": reads["r2"],
            "question": f"`{flow}#start(String)` 实际运行时会调用哪个实现？",
            "expected_outcome": "KNOWLEDGE_GAP",
            "required_tokens": ["KNOWLEDGE_NOT_MODELED"],
            "forbidden_tokens": ["确定会调用"],
            "outcome_markers_any": ["Knowledge Gap", "不证明运行时分派"],
        },
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
        "fixture": {
            key: fixture[key]
            for key in ("seed", "suffix", "workspace_id", "revisions", "read_sets")
        },
        "catalog_digest": catalog["catalog_digest"],
        "product_oracle_digest": oracle["document_digest"],
        "independent_evaluator_digest": _sha(evaluator),
        "comparison_surfaces": list(live_evaluator.SURFACES),
        "comparison_protocols": _comparison_protocols(runner, provider),
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
        "runtime_assets/gateway_authorized_workload.py": (
            assets / "gateway_authorized_workload.py"
        ),
        "runtime_assets/java_gateway_workload.py": (
            assets / "java_gateway_workload.py"
        ),
        "runtime_assets/projector.sb": assets / "projector.sb",
        "runtime_assets/role_worker.py": assets / "role_worker.py",
        "runtime_assets/os_probe_worker.py": assets / "os_probe_worker.py",
        "runtime_assets/provider_socket_worker.py": assets / "provider_socket_worker.py",
    }


def _test_result(command, *, workspace, environment):
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
    parser.add_argument("--java-capability-qualification", required=True)
    parser.add_argument("--java-closed-capability-result", required=True)
    parser.add_argument("--java-conformance-result", required=True)
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
    stage_digest = _candidate_stage(
        Path(arguments.baseline_stage).resolve(strict=True), producer, stage
    )
    java_qualification = _install_java_gateway_input(
        stage=stage,
        producer=producer,
        qualification_path=Path(arguments.java_capability_qualification),
        closed_result_path=Path(arguments.java_closed_capability_result),
        conformance_result_path=Path(arguments.java_conformance_result),
    )
    provider = dict(_PROVIDER)
    provider["qualification_digest"] = java_qualification[
        "capability_qualification_digest"
    ]
    stage_digest = _value_digest(_tree_manifest(stage))
    seed = arguments.seed or secrets.token_hex(16)
    fixture, catalog, commands = _workspace_fixture(
        workspace=workspace,
        producer=producer,
        identity=identity,
        output=output,
        seed=seed,
    )
    evaluator = Path(live_evaluator.__file__).resolve(strict=True)
    runner = Path(live_comparison.__file__).resolve(strict=True)
    oracle, suite = _oracle_and_suite(
        output, fixture, catalog, identity, evaluator, runner, provider
    )
    suite_document = json.loads(suite.read_text())
    authorization = output / "comparison-authorization.NOT_AUTHORIZED.json"
    _write(authorization, live_comparison.pending_authorization(suite_document))
    mature_schema = output / "mature-agent-answer-schema.json"
    _write(mature_schema, live_comparison._MATURE_OUTPUT_SCHEMA)
    if _sha(mature_schema) != live_evaluator._MATURE_AGENT["answer_schema_sha256"]:
        raise FreezeFailure("mature Agent answer schema digest drifted")
    mature_workspace = output / "mature-agent-parse-smoke"
    mature_workspace.mkdir()
    mature_message = output / "mature-agent-parse-smoke.last-message.json"
    command = live_comparison._mature_command(
        workspace=mature_workspace,
        schema=mature_schema,
        last_message=mature_message,
        prompt="PARSE_SMOKE_ONLY",
    )
    command[-1] = "--help"
    mature_parse = _run(command, cwd=workspace)
    live_comparison._verify_mature_binary()

    environment = dict(os.environ)
    environment["PYTHONPATH"] = f"{producer / 'src'}:{workspace}"
    environment["PYTHONWARNINGS"] = "ignore"
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    blocked_output = output / "blocked-comparison"
    blocked = _run(
        (
            sys.executable,
            "-B",
            "-m",
            "validation.structure_world_model_iteration_006.live_comparison",
            "run-controlled-direct",
            "--suite",
            str(suite),
            "--source-repository",
            str(fixture["repository"]),
            "--authorization",
            str(authorization),
            "--conformance-result",
            str(stage / "gateway-input/conformance.json"),
            "--output",
            str(blocked_output),
        ),
        cwd=workspace,
        environment=environment,
        expect=2,
    )
    if (
        "exact Java comparison disclosure is not explicitly authorized"
        not in blocked.stderr
        or blocked_output.exists()
    ):
        raise FreezeFailure("comparison authorization did not fail before dispatch")

    adapter_probe = output / "adapter-probe.json"
    _run(
        (
            sys.executable,
            "-B",
            "-m",
            "validation.structure_world_model_iteration_005.slice2_probe",
            "--database",
            str(fixture["database"]),
            "--catalog-root",
            str(fixture["catalog_root"]),
            "--bundle-root",
            str(fixture["bundle_root"]),
            "--implementation-commit",
            identity["commit"],
            "--implementation-tree",
            identity["tree"],
            "--output",
            str(adapter_probe),
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
            "validation.structure_world_model_iteration_006.live_product_probe",
            "--suite",
            str(suite),
            "--catalog-root",
            str(fixture["catalog_root"]),
            "--bundle-root",
            str(fixture["bundle_root"]),
            "--output",
            str(product_probe),
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
            "tests.test_java_static_call",
            "tests.test_java_static_call_update",
            "tests.test_behavior_view",
            "tests.test_world_model_product",
            "tests.test_world_model_http",
            "tests.test_world_model_browser",
            "tests.test_world_model_gateway_authorization",
            "tests.test_world_model_evaluation_grant",
        ),
        workspace=workspace,
        environment=environment,
    )
    stage_environment = dict(environment)
    stage_environment["PYTHONPATH"] = f"{stage / 'packages/answer'}:{workspace}"
    candidate = _test_result(
        (
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "tests.test_behavior_view",
            "tests.test_world_model_product",
        ),
        workspace=workspace,
        environment=stage_environment,
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
    launcher_hashes = {
        label: _raw_sha(path) for label, path in _launcher_files(producer).items()
    }
    launcher_digest = _value_digest(
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
        "java_capability_qualification": java_qualification,
        "launcher_manifest_digest": launcher_digest,
        "held_out_suite_digest": suite_document["document_digest"],
        "independent_evaluator_digest": _sha(evaluator),
        "comparison_runner_digest": _sha(runner),
        "comparison_protocols_sealed": True,
        "comparison_authorization_digest": json.loads(authorization.read_text())[
            "document_digest"
        ],
        "comparison_authorization_status": "NOT_AUTHORIZED",
        "comparison_unauthorized_pre_dispatch_pass": True,
        "mature_agent_binary_digest": live_evaluator._MATURE_AGENT["binary_sha256"],
        "mature_agent_version": live_evaluator._MATURE_AGENT["version"],
        "mature_agent_argv_parse_pass": True,
        "mature_agent_argv_parse_stdout_sha256": _value_digest(mature_parse.stdout),
        "adapter_probe_digest": json.loads(adapter_probe.read_text())[
            "document_digest"
        ],
        "deterministic_product_probe_digest": json.loads(
            product_probe.read_text()
        )["document_digest"],
        "focused_tests_pass": True,
        "deterministic_product_probe_pass": True,
        "candidate_answer_package_tests_pass": True,
        "full_regression_pass": True,
        "docs_check_pass": True,
        "focused_test_result": focused,
        "candidate_answer_package_test_result": candidate,
        "full_regression_result": full,
        "docs_check_result": {
            "argv": [sys.executable, "scripts/docs.py", "check"],
            "pass": True,
            "stdout_sha256": _value_digest(docs.stdout),
            "stderr_sha256": _value_digest(docs.stderr),
        },
        "external_model_called": False,
        "production_activation": "NOT_EXECUTED",
    }
    qualification = _document(QUALIFICATION_SCHEMA, qualification_core)
    qualification_path = output / "deterministic-qualification.json"
    _write(qualification_path, qualification)
    placeholder = output / "baseline-results-at-seal.json"
    _write(
        placeholder,
        {
            "schema": "SWM-JAVA-WORLD-MODEL-BASELINE-PLACEHOLDER@1",
            "result_count": 0,
            "sealed_before_world_model_results": True,
            "production_activation": "NOT_EXECUTED",
        },
    )
    gateway_input = stage / "gateway-input"
    gateway_hashes = {
        name: _raw_sha(gateway_input / name) for name in sorted(_GATEWAY_INPUT_FILES)
    }
    role_hashes = {
        role: _raw_sha(stage / "packages" / role / relative)
        for role, relative in _ROLE_ENTRYPOINTS.items()
    }
    disclosure = _document(
        DISCLOSURE_SCHEMA,
        {
            "status": "NOT_AUTHORIZED",
            "authorized_by": "user",
            "authorized_at": datetime.now(timezone.utc).isoformat().replace(
                "+00:00", "Z"
            ),
            "authorization_ref": "PENDING_EXPLICIT_USER_DISCLOSURE_AUTHORIZATION",
            "payload_boundary": "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE",
        },
    )
    grant_core = {
        "schema": GRANT_SCHEMA,
        "environment": "EVALUATION_ONLY",
        "live_dispatch_authorized": False,
        "disclosure_authorization": disclosure,
        "evaluation_subject": {
            "status": "CANDIDATE",
            "commit": identity["commit"],
            "tree": identity["tree"],
            "stage_root": str(stage.resolve(strict=True)),
            "stage_manifest_digest": stage_digest,
            "deterministic_qualification": _reference(
                qualification_path, document=True
            ),
            "held_out_suite": _reference(suite, document=True),
            "independent_evaluator": _reference(evaluator, document=False),
            "gateway_input_sha256": gateway_hashes,
            "role_entrypoint_sha256": role_hashes,
        },
        "provider": provider,
        "launcher_files": launcher_hashes,
        "forbidden_inputs": {
            "product_oracle": _reference(oracle, document=False),
            "baseline_result": _reference(placeholder, document=False),
            "independent_evaluator": _reference(evaluator, document=False),
        },
        "production_activation": "NOT_EXECUTED",
    }
    grant = _document(GRANT_SCHEMA, grant_core)
    grant_path = output / "evaluation-grant.NOT_AUTHORIZED.json"
    _write(grant_path, grant)
    blocked_session = output / "blocked-session"
    blocked_sockets = output / "blocked-sockets"
    blocked_product = _run(
        (
            sys.executable,
            "-m",
            "software_world_model.interface.world_model_http",
            "--database",
            str(fixture["database"]),
            "--catalog-root",
            str(fixture["catalog_root"]),
            "--bundle-root",
            str(fixture["bundle_root"]),
            "--evaluation-grant",
            str(grant_path),
            "--session-root",
            str(blocked_session),
            "--socket-root",
            str(blocked_sockets),
        ),
        cwd=workspace,
        environment=environment,
        expect=1,
    )
    if (
        "LIVE_DISPATCH_NOT_AUTHORIZED" not in blocked_product.stderr
        or blocked_session.exists()
        or blocked_sockets.exists()
    ):
        raise FreezeFailure("unauthorized product did not fail before startup")
    _write(output / "commands.json", commands)
    report_core = {
        "schema": REPORT_SCHEMA,
        "status": "PASS",
        "evaluation_subject_status": "CANDIDATE",
        "producer": identity,
        "candidate_stage_manifest_digest": stage_digest,
        "java_capability_qualification": java_qualification,
        "launcher_manifest_digest": launcher_digest,
        "fixture": {
            key: fixture[key]
            for key in ("seed", "suffix", "workspace_id", "revisions", "read_sets")
        },
        "catalog_digest": catalog["catalog_digest"],
        "held_out_suite_digest": suite_document["document_digest"],
        "independent_evaluator_digest": _sha(evaluator),
        "comparison_runner_digest": _sha(runner),
        "comparison_authorization_digest": json.loads(authorization.read_text())[
            "document_digest"
        ],
        "deterministic_qualification_digest": qualification["document_digest"],
        "deterministic_product_probe_digest": json.loads(product_probe.read_text())[
            "document_digest"
        ],
        "focused_test_count": focused["test_count"],
        "candidate_answer_package_test_count": candidate["test_count"],
        "full_regression_test_count": full["test_count"],
        "docs_check": "PASS",
        "comparison_unauthorized_pre_dispatch_gate": "PASS",
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
