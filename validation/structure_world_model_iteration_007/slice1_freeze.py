"""Build and deterministically qualify the ITER-007 SLICE-001 product candidate."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
from typing import Mapping, Sequence

from software_world_model.ai_infrastructure import (
    JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST,
    JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_PATH,
    VolcengineArkModelConfiguration,
    load_ark_chat_conformance_qualification,
    load_java_source_semantics_gateway_qualification_binding,
)
from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from software_world_model.interface import world_model_runtime

from . import slice1_live_evaluator


QUALIFICATION_SCHEMA = "SWM-WORLD-MODEL-DETERMINISTIC-QUALIFICATION@1"
SUITE_SCHEMA = "SWM-WORLD-MODEL-HELD-OUT-SUITE@2"
GRANT_SCHEMA = "SWM-WORLD-MODEL-EVALUATION-GRANT@2"
DISCLOSURE_SCHEMA = "SWM-WORLD-MODEL-DISCLOSURE-AUTHORIZATION@1"
REPORT_SCHEMA = "SWM-ITER-007-SLICE-001-CANDIDATE-FREEZE@1"
GATEWAY_FREEZE_SCHEMA = (
    "SWM-ITER-007-JAVA-SOURCE-SEMANTICS-GATEWAY-FREEZE@1"
)
ACCEPTED_BASELINE_STAGE_DIGEST = (
    "sha256:862fdb8d91006555d6b6f40a9ca4d7a520871dfa3baea248f1f4b02ef6de213b"
)
_FIXED_GIT_DATE = "2026-08-13T08:30:00+00:00"
_TEST_COUNT = re.compile(r"Ran ([0-9]+) tests?")


class SliceFreezeError(RuntimeError):
    pass


def _canonical(value: object) -> bytes:
    return canonical_json_bytes(value)


def _document(schema: str, core: Mapping[str, object]) -> dict[str, object]:
    return {**core, "document_digest": digest_of([schema, core]).value}


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        raise SliceFreezeError(f"output already exists: {path}")
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
    exact = path.resolve(strict=True)
    value = {"path": str(exact), "raw_sha256": _raw_sha(exact)}
    if document:
        loaded = json.loads(exact.read_bytes())
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
        raise SliceFreezeError(
            f"command returned {completed.returncode}, expected {expect}: "
            f"{' '.join(arguments)}\nstdout={completed.stdout}\n"
            f"stderr={completed.stderr}"
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
            raise SliceFreezeError(f"symlink in protected tree: {path}")
        if stat.S_ISDIR(metadata.st_mode):
            directories.append(relative)
        elif stat.S_ISREG(metadata.st_mode):
            files.append(
                {"path": relative, "digest": _sha(path), "size": metadata.st_size}
            )
        else:
            raise SliceFreezeError(f"unsupported protected tree entry: {path}")
    return {"directories": directories, "files": files}


def _source_snapshot(workspace: Path, destination: Path) -> dict[str, str]:
    shutil.copytree(
        workspace / "src",
        destination / "src",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
    )
    shutil.copy2(workspace / "pyproject.toml", destination / "pyproject.toml")
    environment = {
        **os.environ,
        "GIT_AUTHOR_DATE": _FIXED_GIT_DATE,
        "GIT_COMMITTER_DATE": _FIXED_GIT_DATE,
    }
    _git(destination, "init", "-q", "--object-format=sha1", environment=environment)
    _git(
        destination,
        "config",
        "user.email",
        "iter007-slice1@example.invalid",
        environment=environment,
    )
    _git(
        destination,
        "config",
        "user.name",
        "ITER-007 SLICE-001 Freeze",
        environment=environment,
    )
    _git(destination, "add", "src", "pyproject.toml", environment=environment)
    _git(
        destination,
        "commit",
        "-q",
        "-m",
        "freeze ITER-007 SLICE-001 candidate",
        environment=environment,
    )
    return {
        "commit": _git(destination, "rev-parse", "HEAD", environment=environment),
        "tree": _git(
            destination, "rev-parse", "HEAD^{tree}", environment=environment
        ),
        "source_manifest_digest": digest_of(
            _tree_manifest(destination / "src")
        ).value,
    }


def _candidate_stage(
    *, baseline: Path, producer: Path, destination: Path
) -> None:
    baseline_digest = digest_of(_tree_manifest(baseline)).value
    if baseline_digest != ACCEPTED_BASELINE_STAGE_DIGEST:
        raise SliceFreezeError("accepted ITER-006 baseline stage digest drifted")
    shutil.copytree(baseline, destination)
    package_root = destination / "packages"
    source_package = producer / "src/software_world_model"
    for role in ("answer", "broker", "gateway", "projector"):
        target_package = package_root / role / "software_world_model"
        shutil.rmtree(target_package)
        shutil.copytree(
            source_package,
            target_package,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
    assets = source_package / "interface/world_model_runtime_assets"
    shutil.copy2(
        assets / "java_source_semantics_answer_workload.py",
        package_root / "answer/.g3b/answer_workload.py",
    )
    shutil.copy2(
        assets / "gateway_authorized_workload.py",
        package_root / "gateway/.g3b/gateway_authorized_workload.py",
    )
    shutil.copy2(
        assets / "java_source_semantics_gateway_workload.py",
        package_root / "gateway/.g3b/java_source_semantics_gateway_workload.py",
    )
    for role in ("answer", "gateway", "projector"):
        for name in ("os_probe_worker.py", "role_worker.py"):
            shutil.copy2(assets / name, package_root / role / ".g3b" / name)


def _install_gateway_input(
    *,
    stage: Path,
    qualification_path: Path,
    closed_result_path: Path,
    conformance_result_path: Path,
) -> dict[str, object]:
    qualification = qualification_path.resolve(strict=True)
    closed = closed_result_path.resolve(strict=True)
    conformance_source = conformance_result_path.resolve(strict=True)
    policy = JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_PATH.resolve(strict=True)
    binding = load_java_source_semantics_gateway_qualification_binding(
        qualification_path=qualification,
        closed_result_path=closed,
        policy_path=policy,
    )
    configuration = VolcengineArkModelConfiguration()
    conformance = load_ark_chat_conformance_qualification(
        conformance_source, configuration
    )
    gateway_input = stage / "gateway-input"
    for source, name in (
        (conformance_source, "conformance.json"),
        (qualification, "qualification.json"),
        (closed, "closed-result.json"),
        (policy, "egress-policy.json"),
    ):
        target = gateway_input / name
        target.unlink()
        shutil.copy2(source, target)
    permission_digest = digest_of(
        [
            "ITER-007-SLICE-001-FORMAL-WEB-PERMISSION@1",
            binding.capability_qualification_ref,
            binding.capability_qualification_digest.value,
            binding.closed_capability_result_digest.value,
        ]
    ).value
    freeze_core = {
        "schema": GATEWAY_FREEZE_SCHEMA,
        "freeze_ref": (
            "ITER-007-JAVA-SOURCE-SEMANTICS-PRODUCT-GATEWAY-CANDIDATE@1"
        ),
        "environment": "EVALUATION_ONLY",
        "strategy_ref": "model-snapshot-first-world-model-answer@1.2.2",
        "prompt_ref": "java-source-semantics-world-model-prompt@3",
        "proposal_vocabulary_ref": (
            "java-source-semantics-world-model-vocabulary@3"
        ),
        "capability_qualification_document_digest": (
            binding.qualification_document_digest.value
        ),
        "closed_capability_result_digest": (
            binding.closed_capability_result_digest.value
        ),
        "egress_policy_digest": (
            JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST
        ),
        "conformance_result_ref": conformance.result_ref,
        "conformance_result_digest": conformance.result_digest.value,
        "permission_digest": permission_digest,
        "production_activation": "NOT_EXECUTED",
    }
    freeze = _document(GATEWAY_FREEZE_SCHEMA, freeze_core)
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
        "java_source_semantics_gateway_freeze_digest": freeze["document_digest"],
        "permission_digest": permission_digest,
    }


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
            "stdout_sha256": digest_of(completed.stdout).value,
            "stderr_sha256": digest_of(completed.stderr).value,
        }
    )
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise SliceFreezeError("public CLI did not return JSON") from exc
    if not isinstance(value, dict):
        raise SliceFreezeError("public CLI did not return one object")
    return value


def _visible_workspace(
    *, workspace: Path, producer: Path, output: Path, identity: Mapping[str, str]
) -> tuple[dict[str, object], list[dict[str, object]]]:
    repository = output / "visible-source-repository"
    shutil.copytree(
        workspace / "validation/structure_world_model_iteration_007/fixtures/development",
        repository,
    )
    git_environment = {
        **os.environ,
        "GIT_AUTHOR_DATE": _FIXED_GIT_DATE,
        "GIT_COMMITTER_DATE": _FIXED_GIT_DATE,
    }
    _git(repository, "init", "-q", "--object-format=sha1", environment=git_environment)
    _git(
        repository,
        "config",
        "user.email",
        "iter007-visible@example.invalid",
        environment=git_environment,
    )
    _git(
        repository,
        "config",
        "user.name",
        "ITER-007 Visible Fixture",
        environment=git_environment,
    )
    _git(repository, "add", ".", environment=git_environment)
    _git(
        repository,
        "commit",
        "-q",
        "-m",
        "visible development semantics",
        environment=git_environment,
    )
    revision = _git(repository, "rev-parse", "HEAD", environment=git_environment)
    database = output / "authority.sqlite3"
    bundle_root = output / "bundles"
    catalog_root = output / "catalog"
    environment = {
        **os.environ,
        "PYTHONPATH": f"{producer / 'src'}:{workspace}",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    commands: list[dict[str, object]] = []
    base = (
        sys.executable,
        "-B",
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
            "iter007-slice1-register",
            "--source-target",
            str(repository),
            "--display-name",
            "ITER-007 Visible Java Semantics",
            "--canonical-system-key",
            "iter007:visible:source-semantics",
            "--source-root",
            "src/main/java",
            "--knowledge-profile",
            "JAVA_SOURCE_SEMANTICS@1",
            "--actor",
            "validation",
            "--correlation-ref",
            "iter007-slice1-register",
        ),
        cwd=workspace,
        environment=environment,
        commands=commands,
    )
    workspace_id = str(registered["workspace"]["workspace_id"])
    updated = _invoke_json(
        (
            *base,
            "update-maven-workspace",
            "--workspace-id",
            workspace_id,
            "--repository-revision",
            revision,
            "--idempotency-key",
            "iter007-slice1-update",
            "--correlation-ref",
            "iter007-slice1-update",
        ),
        cwd=workspace,
        environment=environment,
        commands=commands,
    )
    read_set_id = str(updated["single_read_set"]["read_set_id"])
    snapshot_id = str(updated["version"]["snapshot_id"])
    catalog = _invoke_json(
        (
            sys.executable,
            "-B",
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
    candidate = _invoke_json(
        (
            sys.executable,
            "-B",
            "-m",
            "software_world_model.interface.read_set_catalog_cli",
            "--catalog-root",
            str(catalog_root),
            "--bundle-root",
            str(bundle_root),
            "view",
            "--read-set-id",
            read_set_id,
            "--",
            "implementation-candidates",
            "--snapshot-id",
            snapshot_id,
            "--search-term",
            "credentials",
            "--search-term",
            "failure",
            "--search-term",
            "session",
            "--limit",
            "5",
        ),
        cwd=workspace,
        environment=environment,
        commands=commands,
    )
    candidates = candidate.get("payload", {}).get("candidates", [])
    if (
        candidate.get("payload", {}).get("query_status") != "SUPPORTED"
        or not isinstance(candidates, list)
        or not candidates
        or candidates[0].get("canonical_signature")
        != "dev.acme.auth.LoginService#authenticate(boolean)"
    ):
        raise SliceFreezeError("visible feature discovery did not select the method")
    method = candidates[0]["method"]
    implementation = _invoke_json(
        (
            sys.executable,
            "-B",
            "-m",
            "software_world_model.interface.read_set_catalog_cli",
            "--catalog-root",
            str(catalog_root),
            "--bundle-root",
            str(bundle_root),
            "view",
            "--read-set-id",
            read_set_id,
            "--",
            "method-implementation",
            "--method-snapshot-id",
            snapshot_id,
            "--method-root-id",
            str(method["root_id"]),
            "--method-state-id",
            str(method["state_id"]),
        ),
        cwd=workspace,
        environment=environment,
        commands=commands,
    )
    implementation_payload = implementation.get("payload", {})
    if (
        implementation_payload.get("query_status") != "SUPPORTED"
        or implementation_payload.get("legacy_calls_direction") != "OUTGOING"
        or len(implementation_payload.get("ordered_atoms", [])) != 6
        or len(implementation_payload.get("legacy_calls", [])) != 2
    ):
        raise SliceFreezeError("visible method implementation projection drifted")
    probe_core = {
        "schema": "SWM-ITER-007-SLICE-001-DETERMINISTIC-PROBE@1",
        "status": "PASS",
        "workspace_id": workspace_id,
        "source_revision": revision,
        "read_set_id": read_set_id,
        "snapshot_id": snapshot_id,
        "catalog_digest": catalog["catalog_digest"],
        "candidate_result_digest": candidate["digest"],
        "implementation_result_digest": implementation["digest"],
        "selected_signature": candidates[0]["canonical_signature"],
        "ordered_atom_count": 6,
        "legacy_call_count": 2,
        "source_off_query": "PASS",
        "production_activation": "NOT_EXECUTED",
    }
    probe = _document(str(probe_core["schema"]), probe_core)
    _write(output / "deterministic-product-probe.json", probe)
    fixture = {
        "repository": str(repository.resolve(strict=True)),
        "database": str(database.resolve(strict=True)),
        "bundle_root": str(bundle_root.resolve(strict=True)),
        "catalog_root": str(catalog_root.resolve(strict=True)),
        "workspace_id": workspace_id,
        "source_revision": revision,
        "read_set_id": read_set_id,
        "snapshot_id": snapshot_id,
        "catalog_digest": catalog["catalog_digest"],
        "deterministic_product_probe_digest": probe["document_digest"],
    }
    return fixture, commands


def _test_result(
    command: Sequence[str], *, workspace: Path, environment: Mapping[str, str]
) -> dict[str, object]:
    completed = _run(command, cwd=workspace, environment=environment)
    combined = completed.stdout + completed.stderr
    matched = _TEST_COUNT.search(combined)
    return {
        "argv": list(command),
        "pass": True,
        "test_count": int(matched.group(1)) if matched else None,
        "stdout_sha256": digest_of(completed.stdout).value,
        "stderr_sha256": digest_of(completed.stderr).value,
    }


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
        "runtime_assets/java_source_semantics_gateway_workload.py": (
            assets / "java_source_semantics_gateway_workload.py"
        ),
        "runtime_assets/java_source_semantics_answer_workload.py": (
            assets / "java_source_semantics_answer_workload.py"
        ),
        "runtime_assets/projector.sb": assets / "projector.sb",
        "runtime_assets/role_worker.py": assets / "role_worker.py",
        "runtime_assets/os_probe_worker.py": assets / "os_probe_worker.py",
        "runtime_assets/provider_socket_worker.py": (
            assets / "provider_socket_worker.py"
        ),
    }


def _user_held_suite(
    output: Path, identity: Mapping[str, str], fixture: Mapping[str, object]
) -> Path:
    core = {
        "schema": SUITE_SCHEMA,
        "environment": "EVALUATION_ONLY",
        "evaluation_subject_commit": identity["commit"],
        "evaluation_subject_tree": identity["tree"],
        "sealed_before_world_model_results": True,
        "world_model_result_count_at_seal": 0,
        "controlled_direct_result_count_at_seal": 0,
        "mature_source_agent_result_count_at_seal": 0,
        "comparison_surfaces": [
            "WORLD_MODEL",
            "CONTROLLED_DIRECT",
            "MATURE_SOURCE_AGENT",
        ],
        "comparison_protocols": {
            "mode": "USER_HELD_LIVE_AFTER_PRODUCT_CODE_FREEZE",
            "world_model_entrypoint": (
                "software_world_model.interface.world_model_http"
            ),
            "model_calls_per_question": 3,
            "controller_retries": 0,
            "question_visibility_at_seal": "NOT_DISCLOSED",
        },
        "source_closures": {
            "visible_development_read_set_id": fixture["read_set_id"],
            "user_canary": "NOT_DISCLOSED_UNTIL_AFTER_PRODUCT_CODE_FREEZE",
        },
        "cases": [],
        "production_activation": "NOT_EXECUTED",
    }
    path = output / "user-held-live-suite.json"
    _write(path, _document(SUITE_SCHEMA, core))
    return path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", default=str(Path(__file__).resolve().parents[2]))
    parser.add_argument("--output", required=True)
    parser.add_argument("--baseline-stage", required=True)
    parser.add_argument("--capability-qualification", required=True)
    parser.add_argument("--closed-capability-result", required=True)
    parser.add_argument("--conformance-result", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    workspace = Path(arguments.workspace).resolve(strict=True)
    output = Path(arguments.output)
    if not output.is_absolute():
        output = workspace / output
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.is_symlink():
        raise SliceFreezeError("output root must be one future path")
    output.mkdir(mode=0o700)

    producer = output / "producer-source"
    producer.mkdir()
    identity = _source_snapshot(workspace, producer)
    stage = output / "candidate-stage"
    _candidate_stage(
        baseline=Path(arguments.baseline_stage).resolve(strict=True),
        producer=producer,
        destination=stage,
    )
    semantic_qualification = _install_gateway_input(
        stage=stage,
        qualification_path=Path(arguments.capability_qualification),
        closed_result_path=Path(arguments.closed_capability_result),
        conformance_result_path=Path(arguments.conformance_result),
    )
    fixture, commands = _visible_workspace(
        workspace=workspace,
        producer=producer,
        output=output,
        identity=identity,
    )
    suite_path = _user_held_suite(output, identity, fixture)
    suite = json.loads(suite_path.read_bytes())
    evaluator = Path(slice1_live_evaluator.__file__).resolve(strict=True)
    authorization_helper = Path(__file__).resolve(strict=True).with_name(
        "slice1_live_authorize.py"
    )

    environment = {
        **os.environ,
        "PYTHONPATH": f"{producer / 'src'}:{workspace}",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONWARNINGS": "ignore",
    }
    focused = _test_result(
        (
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "tests.test_iteration_007_readiness",
            "tests.test_iteration_007_hidden_freeze",
            "tests.test_java_source_semantics",
            "tests.test_java_source_semantics_update",
            "tests.test_world_model_answer_strategy",
            "tests.test_world_model_capability_evaluation",
            "tests.test_iteration_007_capability_qualification",
            "tests.test_world_model_evaluation_grant",
            "tests.test_world_model_gateway_authorization",
            "tests.test_iteration_007_slice1_freeze",
            "tests.test_iteration_007_slice1_live_authorize",
            "tests.test_iteration_007_slice1_live_evaluator",
        ),
        workspace=workspace,
        environment=environment,
    )
    candidate_environment = {
        **environment,
        "PYTHONPATH": f"{stage / 'packages/answer'}:{workspace}",
    }
    candidate = _test_result(
        (
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "tests.test_java_source_semantics",
            "tests.test_world_model_answer_strategy",
            "tests.test_world_model_evaluation_grant",
        ),
        workspace=workspace,
        environment=candidate_environment,
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

    stage_digest = digest_of(_tree_manifest(stage)).value
    launcher_hashes = {
        label: _raw_sha(path) for label, path in _launcher_files(producer).items()
    }
    launcher_manifest_digest = digest_of(
        ["SWM-WORLD-MODEL-LAUNCHER-MANIFEST@1", launcher_hashes]
    ).value
    qualification_core = {
        "schema": QUALIFICATION_SCHEMA,
        "status": "PASS",
        "evaluation_subject_status": "CANDIDATE",
        "implementation_commit": identity["commit"],
        "implementation_tree": identity["tree"],
        "stage_manifest_digest": stage_digest,
        "java_source_semantics_capability_qualification": semantic_qualification,
        "launcher_manifest_digest": launcher_manifest_digest,
        "held_out_suite_digest": suite["document_digest"],
        "independent_evaluator_digest": _sha(evaluator),
        "live_authorization_helper_digest": _sha(authorization_helper),
        "focused_tests_pass": True,
        "candidate_answer_package_tests_pass": True,
        "deterministic_product_probe_pass": True,
        "deterministic_product_probe_digest": fixture[
            "deterministic_product_probe_digest"
        ],
        "full_regression_pass": True,
        "docs_check_pass": True,
        "focused_test_result": focused,
        "candidate_answer_package_test_result": candidate,
        "full_regression_test_result": full,
        "docs_check_result": {
            "pass": True,
            "stdout_sha256": digest_of(docs.stdout).value,
            "stderr_sha256": digest_of(docs.stderr).value,
        },
        "external_model_called": False,
        "production_activation": "NOT_EXECUTED",
    }
    qualification = _document(QUALIFICATION_SCHEMA, qualification_core)
    qualification_path = output / "deterministic-qualification.json"
    _write(qualification_path, qualification)

    oracle = output / "user-held-oracle.NOT_DISCLOSED.json"
    _write(
        oracle,
        {
            "schema": "SWM-ITER-007-USER-HELD-ORACLE-MARKER@1",
            "status": "NOT_DISCLOSED_UNTIL_AFTER_PRODUCT_CODE_FREEZE",
            "production_activation": "NOT_EXECUTED",
        },
    )
    baseline = output / "baseline-results-at-seal.json"
    _write(
        baseline,
        {
            "schema": "SWM-ITER-007-BASELINE-PLACEHOLDER@1",
            "result_count": 0,
            "sealed_before_world_model_results": True,
            "production_activation": "NOT_EXECUTED",
        },
    )
    gateway_input = stage / "gateway-input"
    gateway_hashes = {
        name: _raw_sha(gateway_input / name)
        for name in sorted(world_model_runtime._GATEWAY_INPUT_FILES)
    }
    role_hashes = {
        role: _raw_sha(stage / "packages" / role / relative)
        for role, relative in world_model_runtime._ROLE_ENTRYPOINTS.items()
    }
    frozen_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    disclosure = _document(
        DISCLOSURE_SCHEMA,
        {
            "status": "NOT_AUTHORIZED",
            "authorized_by": "user",
            "authorized_at": frozen_at,
            "authorization_ref": "PENDING_POST_FREEZE_USER_AUTHORIZATION",
            "payload_boundary": (
                "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
            ),
        },
    )
    provider = dict(world_model_runtime._EXPECTED_PROVIDER)
    provider["qualification_digest"] = semantic_qualification[
        "capability_qualification_digest"
    ]
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
            "held_out_suite": _reference(suite_path, document=True),
            "independent_evaluator": _reference(evaluator, document=False),
            "gateway_input_sha256": gateway_hashes,
            "role_entrypoint_sha256": role_hashes,
        },
        "provider": provider,
        "launcher_files": launcher_hashes,
        "forbidden_inputs": {
            "product_oracle": _reference(oracle, document=False),
            "baseline_result": _reference(baseline, document=False),
            "independent_evaluator": _reference(evaluator, document=False),
        },
        "production_activation": "NOT_EXECUTED",
    }
    grant = _document(GRANT_SCHEMA, grant_core)
    grant_path = output / "evaluation-grant.NOT_AUTHORIZED.json"
    _write(grant_path, grant)
    blocked = _run(
        (
            sys.executable,
            "-B",
            "-m",
            "software_world_model.interface.world_model_http",
            "--database",
            fixture["database"],
            "--catalog-root",
            fixture["catalog_root"],
            "--bundle-root",
            fixture["bundle_root"],
            "--evaluation-grant",
            str(grant_path),
            "--session-root",
            str(output / "blocked-session"),
            "--socket-root",
            str(output / "blocked-sockets"),
        ),
        cwd=workspace,
        environment=environment,
        expect=1,
    )
    if (
        "LIVE_DISPATCH_NOT_AUTHORIZED" not in blocked.stderr
        or (output / "blocked-session").exists()
        or (output / "blocked-sockets").exists()
    ):
        raise SliceFreezeError("pending Web grant did not fail before startup")
    if digest_of(_tree_manifest(stage)).value != stage_digest:
        raise SliceFreezeError("candidate stage changed after deterministic gates")

    _write(output / "commands.json", commands)
    report_core = {
        "schema": REPORT_SCHEMA,
        "status": "PASS",
        "evaluation_subject_status": "CANDIDATE",
        "frozen_at": frozen_at,
        "producer": identity,
        "candidate_stage_manifest_digest": stage_digest,
        "semantic_capability_qualification": semantic_qualification,
        "launcher_manifest_digest": launcher_manifest_digest,
        "fixture": fixture,
        "user_held_live_suite_digest": suite["document_digest"],
        "deterministic_qualification_digest": qualification["document_digest"],
        "pending_evaluation_grant_digest": grant["document_digest"],
        "independent_evaluator_digest": _sha(evaluator),
        "live_authorization_helper_digest": _sha(authorization_helper),
        "focused_test_count": focused["test_count"],
        "candidate_answer_package_test_count": candidate["test_count"],
        "full_regression_test_count": full["test_count"],
        "docs_check": "PASS",
        "unauthorized_prelisten_gate": "PASS",
        "external_model_dispatch_during_freeze": "NOT_EXECUTED",
        "live_question_status": "AWAITING_USER_AFTER_CODE_FREEZE",
        "production_activation": "NOT_EXECUTED",
        "git_stage_commit_push": "NOT_EXECUTED",
    }
    report = _document(REPORT_SCHEMA, report_core)
    _write(output / "report.json", report)
    print(_canonical(report).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
