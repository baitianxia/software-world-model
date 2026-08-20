"""Build and deterministically qualify the ITER-008 SLICE-001 candidate."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Mapping, Sequence

from software_world_model.ai_infrastructure import (
    BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST,
    BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_PATH,
    DeepSeekModelConfiguration,
    load_bounded_java_source_semantics_gateway_qualification_binding,
    load_deepseek_chat_conformance_qualification,
)
from software_world_model.cross_cutting import digest_of
from software_world_model.interface import world_model_runtime
from validation.structure_world_model_iteration_007 import (
    slice1_freeze as _shared,
)

from . import slice1_live_evaluator


QUALIFICATION_SCHEMA = "SWM-WORLD-MODEL-DETERMINISTIC-QUALIFICATION@2"
SUITE_SCHEMA = "SWM-WORLD-MODEL-HELD-OUT-SUITE@2"
GRANT_SCHEMA = "SWM-WORLD-MODEL-EVALUATION-GRANT@2"
DISCLOSURE_SCHEMA = "SWM-WORLD-MODEL-DISCLOSURE-AUTHORIZATION@1"
REPORT_SCHEMA = "SWM-ITER-008-SLICE-001-CANDIDATE-FREEZE@2"
GATEWAY_FREEZE_SCHEMA = (
    "SWM-ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-GATEWAY-FREEZE@1"
)
ACCEPTED_BASELINE_STAGE_DIGEST = _shared.ACCEPTED_BASELINE_STAGE_DIGEST
_FIXED_GIT_DATE = "2026-08-20T08:30:00+00:00"
_TEST_COUNT = re.compile(r"^Ran ([0-9]+) tests? in ", re.MULTILINE)
_FAILURE_HEADER = re.compile(
    r"^(ERROR|FAIL): [^\n]+ \(([^)\n]+)\)$",
    re.MULTILINE,
)
_FAILED_SUMMARY = re.compile(r"^FAILED \(([^)]+)\)$", re.MULTILINE)
_OK_SUMMARY = re.compile(r"^OK$", re.MULTILINE)
_PRESERVED_HOLD_TESTS = (
    world_model_runtime._FULL_REGRESSION_PRESERVED_HOLD_TESTS
)
_PRESERVED_HOLD_REF = (
    world_model_runtime._FULL_REGRESSION_PRESERVED_HOLD_REF
)
_PRESERVED_HOLD_STATUS = (
    world_model_runtime._FULL_REGRESSION_EXACT_PRESERVED_HOLD
)
_RAW_PASS_STATUS = world_model_runtime._FULL_REGRESSION_PASS
_PRESERVED_HOLD_MARKERS = {
    _PRESERVED_HOLD_TESTS[0][1]: (
        "QUALIFICATION_INVALID: V-009 Adapter Conformance implementation "
        "drifted",
    ),
    _PRESERVED_HOLD_TESTS[1][1]: (
        '"message": "V-009 Adapter Conformance implementation drifted"',
    ),
    _PRESERVED_HOLD_TESTS[2][1]: (
        '"message": "V-009 Adapter Conformance implementation drifted"',
    ),
    _PRESERVED_HOLD_TESTS[3][1]: ("AssertionError: 2 != 3",),
    _PRESERVED_HOLD_TESTS[4][1]: (
        "9f6748b4ab10ffc92c28b9ccedae89e61a302bbc011df7d276ee38f55906e481",
    ),
}


class SliceFreezeError(RuntimeError):
    pass


_canonical = _shared._canonical
_document = _shared._document
_write = _shared._write
_raw_sha = _shared._raw_sha
_sha = _shared._sha
_reference = _shared._reference
_run = _shared._run
_tree_manifest = _shared._tree_manifest
_test_result = _shared._test_result


def _git(repository: Path, *arguments: str, environment=None) -> str:
    return _shared._git(
        repository,
        *arguments,
        environment=environment,
    )


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
        "iter008-slice1@example.invalid",
        environment=environment,
    )
    _git(
        destination,
        "config",
        "user.name",
        "ITER-008 SLICE-001 Freeze",
        environment=environment,
    )
    _git(destination, "add", "src", "pyproject.toml", environment=environment)
    _git(
        destination,
        "commit",
        "-q",
        "-m",
        "freeze ITER-008 SLICE-001 candidate",
        environment=environment,
    )
    return {
        "commit": _git(destination, "rev-parse", "HEAD", environment=environment),
        "tree": _git(
            destination,
            "rev-parse",
            "HEAD^{tree}",
            environment=environment,
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
        assets / "bounded_java_source_semantics_answer_workload.py",
        package_root / "answer/.g3b/answer_workload.py",
    )
    shutil.copy2(
        assets / "gateway_authorized_workload.py",
        package_root / "gateway/.g3b/gateway_authorized_workload.py",
    )
    shutil.copy2(
        assets / "bounded_java_source_semantics_gateway_workload.py",
        package_root
        / "gateway/.g3b/bounded_java_source_semantics_gateway_workload.py",
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
    policy = (
        BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_PATH.resolve(
            strict=True
        )
    )
    binding = load_bounded_java_source_semantics_gateway_qualification_binding(
        qualification_path=qualification,
        closed_result_path=closed,
        policy_path=policy,
    )
    configuration = DeepSeekModelConfiguration()
    conformance = load_deepseek_chat_conformance_qualification(
        conformance_source,
        configuration,
    )
    if binding.conformance_result_ref != conformance.result_ref:
        raise SliceFreezeError(
            "Capability and Conformance qualifications are not one authority chain"
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
            "ITER-008-SLICE-001-FORMAL-WEB-PERMISSION@1",
            "PRE_DISPATCH_FIRST_CURRENTLY_QUALIFIED_NO_REQUEST_RETRY",
            ["VOLCENGINE_ARK", "DEEPSEEK"],
            configuration.provider_type,
            binding.capability_qualification_ref,
            binding.capability_qualification_digest.value,
            binding.closed_capability_result_digest.value,
            conformance.result_ref,
        ]
    ).value
    freeze_core = {
        "schema": GATEWAY_FREEZE_SCHEMA,
        "freeze_ref": (
            "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-PRODUCT-"
            "GATEWAY-CANDIDATE@1"
        ),
        "environment": "EVALUATION_ONLY",
        "strategy_ref": "model-snapshot-first-world-model-answer@1.5.11",
        "prompt_ref": "java-source-semantics-world-model-prompt@20",
        "proposal_vocabulary_ref": (
            "java-source-semantics-world-model-vocabulary@20"
        ),
        "capability_qualification_document_digest": (
            binding.qualification_document_digest.value
        ),
        "closed_capability_result_digest": (
            binding.closed_capability_result_digest.value
        ),
        "egress_policy_digest": (
            BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST
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
        "bounded_java_source_semantics_gateway_freeze_digest": (
            freeze["document_digest"]
        ),
        "permission_digest": permission_digest,
    }


def _launcher_files(producer: Path) -> dict[str, Path]:
    current_source_root = Path(world_model_runtime.__file__).resolve().parents[2]
    producer_source_root = producer / "src"
    return {
        label: producer_source_root / path.relative_to(current_source_root)
        for label, path in world_model_runtime._launcher_files(
            include_bounded=True
        ).items()
    }


def _user_held_suite(
    output: Path,
    identity: Mapping[str, str],
    fixture: Mapping[str, object],
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
            "provider_selection_policy": (
                "PRE_DISPATCH_FIRST_CURRENTLY_QUALIFIED_NO_REQUEST_RETRY"
            ),
            "provider_preference_order": ["VOLCENGINE_ARK", "DEEPSEEK"],
            "selected_provider_type": "DEEPSEEK",
            "minimum_model_calls_per_question": 4,
            "maximum_model_calls_per_question": 6,
            "provisioned_provider_descriptors": 6,
            "controller_retries": 0,
            "question_visibility_at_seal": "NOT_DISCLOSED",
        },
        "source_closures": {
            "visible_development_read_set_id": fixture["read_set_id"],
            "early_canary": "NOT_DISCLOSED_UNTIL_AFTER_PRODUCT_CODE_FREEZE",
        },
        "cases": [],
        "production_activation": "NOT_EXECUTED",
    }
    path = output / "user-held-live-suite.json"
    _write(path, _document(SUITE_SCHEMA, core))
    return path


def _full_regression_result(
    command: Sequence[str],
    *,
    return_code: int,
    stdout: str,
    stderr: str,
) -> dict[str, object]:
    combined = stdout + stderr
    count_matches = _TEST_COUNT.findall(combined)
    if len(count_matches) != 1:
        raise SliceFreezeError("full regression test count is not exact")
    test_count = int(count_matches[0])
    headers = list(_FAILURE_HEADER.finditer(combined))
    observed_failures = [(item.group(1), item.group(2)) for item in headers]

    verbose_statuses: dict[str, str] = {}
    for outcome, test_id in _PRESERVED_HOLD_TESTS:
        method = test_id.rsplit(".", 1)[-1]
        status_pattern = re.compile(
            rf"^{re.escape(method)} \({re.escape(test_id)}\) "
            rf"\.\.\. (ok|FAIL|ERROR)$",
            re.MULTILINE,
        )
        statuses = status_pattern.findall(combined)
        if len(statuses) != 1:
            raise SliceFreezeError(
                "preserved historical regression test was not executed exactly once"
            )
        verbose_statuses[test_id] = statuses[0]

    preserved_tests: list[dict[str, str]] = []
    preserved_ref: str | None = None
    if return_code == 0:
        if (
            headers
            or _FAILED_SUMMARY.search(combined)
            or len(_OK_SUMMARY.findall(combined)) != 1
            or any(status != "ok" for status in verbose_statuses.values())
        ):
            raise SliceFreezeError(
                "successful full regression output is internally inconsistent"
            )
        raw_pass = True
        gate_status = _RAW_PASS_STATUS
        failure_count = 0
        error_count = 0
    elif return_code == 1:
        expected = set(_PRESERVED_HOLD_TESTS)
        if (
            len(observed_failures) != len(expected)
            or set(observed_failures) != expected
            or len(_FAILED_SUMMARY.findall(combined)) != 1
            or _FAILED_SUMMARY.findall(combined)[0]
            != "failures=4, errors=1"
            or _OK_SUMMARY.search(combined)
            or any(
                verbose_statuses[test_id] != outcome
                for outcome, test_id in _PRESERVED_HOLD_TESTS
            )
        ):
            raise SliceFreezeError(
                "full regression differs from the exact preserved historical hold"
            )
        blocks = {
            header.group(2): combined[
                header.start() : (
                    headers[index + 1].start()
                    if index + 1 < len(headers)
                    else len(combined)
                )
            ]
            for index, header in enumerate(headers)
        }
        if any(
            marker not in blocks[test_id]
            for test_id, markers in _PRESERVED_HOLD_MARKERS.items()
            for marker in markers
        ):
            raise SliceFreezeError(
                "preserved historical hold reason marker drifted"
            )
        raw_pass = False
        gate_status = _PRESERVED_HOLD_STATUS
        failure_count = 4
        error_count = 1
        preserved_ref = _PRESERVED_HOLD_REF
        preserved_tests = [
            {"outcome": outcome, "test_id": test_id}
            for outcome, test_id in _PRESERVED_HOLD_TESTS
        ]
    else:
        raise SliceFreezeError(
            "full regression command returned an unsupported status"
        )

    held_count = failure_count + error_count
    if test_count < held_count:
        raise SliceFreezeError("full regression counts are inconsistent")
    return {
        "argv": list(command),
        "pass": raw_pass,
        "gate_pass": True,
        "gate_status": gate_status,
        "return_code": return_code,
        "test_count": test_count,
        "passed_test_count": test_count - held_count,
        "failure_count": failure_count,
        "error_count": error_count,
        "preserved_hold_ref": preserved_ref,
        "preserved_hold_tests": preserved_tests,
        "stdout_sha256": digest_of(stdout).value,
        "stderr_sha256": digest_of(stderr).value,
    }


def _run_full_regression(
    command: Sequence[str],
    *,
    workspace: Path,
    environment: Mapping[str, str],
) -> dict[str, object]:
    completed = subprocess.run(
        tuple(command),
        cwd=workspace,
        env=dict(environment),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return _full_regression_result(
        command,
        return_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        default=str(Path(__file__).resolve().parents[2]),
    )
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
    bounded_qualification = _install_gateway_input(
        stage=stage,
        qualification_path=Path(arguments.capability_qualification),
        closed_result_path=Path(arguments.closed_capability_result),
        conformance_result_path=Path(arguments.conformance_result),
    )
    fixture, commands = _shared._visible_workspace(
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
            "tests.test_iteration_008_capability_harness",
            "tests.test_iteration_008_capability_qualification",
            "tests.test_pinned_deepseek_https",
            "tests.test_model_egress_gateway",
            "tests.test_java_source_semantics",
            "tests.test_world_model_evaluation_grant",
            "tests.test_world_model_gateway_authorization",
            "tests.test_iteration_008_slice1_freeze",
            "tests.test_iteration_008_slice1_live_authorize",
            "tests.test_iteration_008_slice1_live_evaluator",
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
            "tests.test_model_egress_gateway",
            "tests.test_world_model_evaluation_grant",
        ),
        workspace=workspace,
        environment=candidate_environment,
    )
    full = _run_full_regression(
        (
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
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
        "bounded_java_source_semantics_capability_qualification": (
            bounded_qualification
        ),
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
        "full_regression_pass": full["pass"],
        "full_regression_gate_pass": full["gate_pass"],
        "full_regression_gate_status": full["gate_status"],
        "full_regression_preserved_hold_ref": full[
            "preserved_hold_ref"
        ],
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
            "schema": "SWM-ITER-008-EARLY-CANARY-ORACLE-MARKER@1",
            "status": "NOT_DISCLOSED_UNTIL_AFTER_PRODUCT_CODE_FREEZE",
            "production_activation": "NOT_EXECUTED",
        },
    )
    baseline = output / "baseline-results-at-seal.json"
    _write(
        baseline,
        {
            "schema": "SWM-ITER-008-EARLY-BASELINE-PLACEHOLDER@1",
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
    configuration = DeepSeekModelConfiguration()
    provider = {
        "provider_type": configuration.provider_type,
        "adapter": configuration.adapter_version,
        "requested_model": configuration.model_ref,
        "observed_model": configuration.actual_model_fingerprint,
        "endpoint": configuration.endpoint,
        "credential_reference": configuration.secret_reference,
        "conformance_digest": bounded_qualification[
            "conformance_result_digest"
        ],
        "qualification_digest": bounded_qualification[
            "capability_qualification_digest"
        ],
    }
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
                qualification_path,
                document=True,
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
        "bounded_capability_qualification": bounded_qualification,
        "provider_selection_policy": (
            "PRE_DISPATCH_FIRST_CURRENTLY_QUALIFIED_NO_REQUEST_RETRY"
        ),
        "provider_preference_order": ["VOLCENGINE_ARK", "DEEPSEEK"],
        "selected_provider_type": "DEEPSEEK",
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
        "full_regression_pass": full["pass"],
        "full_regression_gate_pass": full["gate_pass"],
        "full_regression_gate_status": full["gate_status"],
        "full_regression_preserved_hold_ref": full[
            "preserved_hold_ref"
        ],
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
