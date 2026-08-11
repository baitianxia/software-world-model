#!/usr/bin/env python3
"""Run the frozen 60-run ITER-003 G3b product batch without retries.

Every Answer, Model Egress Gateway, and Citation Projector is a distinct cold
process under its role-specific deny-default macOS Seatbelt profile.  The
evaluator resolves and connects the exact numeric Provider peer before spawn;
the Gateway inherits that connected descriptor plus one exact prebound AF_UNIX
listener, verifies the peer and TLS hostname, injects the credential, and runs
behind a Seatbelt syscall firewall that denies every new socket creation.
"""

from __future__ import annotations

import argparse
import array
import base64
from datetime import datetime, timezone
from hashlib import sha256
import ipaddress
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
from typing import Iterable, Mapping, Sequence

from software_world_model.ai_infrastructure.pinned_ark_https import ARK_PROVIDER_PORT
from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from validation.structure_world_model_iteration_003.isolation.run_isolation import (
    _python_runtime_dependency_capabilities,
    _python_runtime_read_root,
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V009_ROOT = (
    PROJECT_ROOT
    / "var"
    / "iteration-003"
    / "v009"
    / "019f9fced69110c6a7e357a4ea2394ec6742fd2e"
)
CONFORMANCE = (
    V009_ROOT
    / "conformance"
    / "CC-ARK-CHAT-NO-TOOLS-001-ccrun_8226d63fd77f4370b95867f1f4c48be5.json"
)
QUALIFICATION = V009_ROOT / "capability-evaluation" / "capability-qualification.json"
CLOSED_RESULT = V009_ROOT / "capability-evaluation" / "closed-evaluation-result.json"
EGRESS_POLICY = (
    PROJECT_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "v009"
    / "model-egress-policy-1.0.0.json"
)
G3B_FREEZE = HERE / "input-freeze-1.0.0.json"
PRODUCT_SUITE = (
    PROJECT_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "questions"
    / "product-suite-1.0.0.json"
)
PRODUCT_INPUT = PRODUCT_SUITE.with_name("product-input-suite-1.0.0.json")
BASELINES = V009_ROOT / "baselines"
SANDBOX_EXEC = Path("/usr/bin/sandbox-exec")
SANDBOXED_PYTHON_FLAGS = ("-I", "-S", "-B")
ANCESTOR_PARAMETER_COUNT = 64
RUNTIME_DEPENDENCY_PARAMETER_COUNT = 3
RESULT_SCHEMA = "swm.iter-003.g3b-batch@1"
PROVIDER_SOCKET_WORKER = HERE / "provider_socket_worker.py"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-root", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--implementation-commit", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=240.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    implementation_commit = _commit(arguments.implementation_commit)
    tree = _require_clean_checkpoint(implementation_commit)
    prepared_root = _canonical_directory(arguments.prepared_root, "prepared root")
    registry_path = prepared_root / "prepared-inputs.json"
    registry = _load_registry(registry_path, prepared_root, implementation_commit)
    evidence_root = _new_directory(arguments.evidence_root, "evidence root")
    if arguments.timeout_seconds < 1:
        raise ValueError("timeout must be positive")
    if not SANDBOX_EXEC.is_file():
        raise RuntimeError("/usr/bin/sandbox-exec is unavailable")
    evidence_root.mkdir(parents=True, mode=0o700)
    stage_root = evidence_root / "stage"
    stage_root.mkdir(mode=0o700)
    packages = _stage_packages(stage_root)
    gateway_input = _stage_gateway_input(stage_root)
    forbidden = _stage_forbidden_canaries(stage_root, prepared_root, packages)
    runtime = _runtime_capabilities()
    socket_stage_root = Path(
        tempfile.mkdtemp(prefix="iter003-g3b-", dir=os.environ.get("TMPDIR"))
    ).resolve(strict=True)
    if len(str(socket_stage_root / "00" / "gateway.sock").encode("utf-8")) >= 100:
        raise RuntimeError("G3b short socket staging root exceeds AF_UNIX capacity")

    invocation_core = {
        "schema": "swm.iter-003.g3b-invocation@1",
        "sealed_at": _utc_now(),
        "implementation_commit": implementation_commit,
        "implementation_tree": tree,
        "prepared_registry_digest": registry["document_digest"],
        "provider": {
            "endpoint": (
                "https://ark.cn-beijing.volces.com:443/"
                "api/coding/v3/chat/completions"
            ),
            "address_resolution": "NOT_YET_EXECUTED",
            "connection_handoff": "INHERITED_EXACT_CONNECTED_SOCKET",
            "gateway_listener_handoff": (
                "INHERITED_EXACT_BOUND_AF_UNIX_LISTENER"
            ),
            "gateway_child_socket_creation": "DENIED_BY_SEATBELT",
            "credential_reference": "env:ARK_API_KEY",
            "credential_value_recorded": False,
        },
        "profiles": {
            role: _sha256_file(HERE / f"{role}.sb")
            for role in ("answer", "gateway", "projector")
        },
        "workload_worker_digest": _sha256_file(HERE / "role_worker.py"),
        "probe_worker_digest": _sha256_file(HERE / "os_probe_worker.py"),
        "provider_socket_worker_digest": _sha256_file(PROVIDER_SOCKET_WORKER),
        "socket_stage_root": str(socket_stage_root),
        "run_count": 60,
        "retry_policy": "NO_SELECTIVE_RETRY_ONE_ATTEMPT_PER_FROZEN_RUN",
        "environment": "EVALUATION_ONLY",
        "production_activation": "NOT_EXECUTED",
    }
    invocation = {
        **invocation_core,
        "document_digest": digest_of(invocation_core).value,
    }
    _write_new(evidence_root / "invocation.json", canonical_json_bytes(invocation))

    try:
        bootstrap_connection, bootstrap = _provision_provider_socket()
    except Exception as exc:
        _write_new(
            evidence_root / "provider-bootstrap-failure.json",
            canonical_json_bytes(
                {
                    "schema": "swm.iter-003.g3b-provider-bootstrap-failure@1",
                    "failure_type": type(exc).__name__,
                    "errno": getattr(exc, "errno", None),
                    "credential_value_recorded": False,
                    "production_activation": "NOT_EXECUTED",
                }
            ),
        )
        return 2
    bootstrap_connection.close()
    _write_new(
        evidence_root / "provider-bootstrap.json",
        canonical_json_bytes(bootstrap),
    )
    addresses = tuple(bootstrap["resolved_addresses"])
    provider_address = _text(
        bootstrap.get("selected_address"), "selected Provider address"
    )
    preflight = _run_preflight(
        evidence_root=evidence_root,
        stage_root=stage_root,
        socket_stage_root=socket_stage_root,
        packages=packages,
        gateway_input=gateway_input,
        forbidden=forbidden,
        runtime=runtime,
        provider_address=provider_address,
    )
    if preflight["status"] != "PASS":
        batch = _batch_result(
            implementation_commit=implementation_commit,
            tree=tree,
            invocation=invocation,
            registry=registry,
            provider_addresses=addresses,
            provider_address=provider_address,
            preflight=preflight,
            terminals=[],
            stage_root=stage_root,
            socket_stage_root=socket_stage_root,
            status="FAIL_PREFLIGHT",
        )
        _write_new(evidence_root / "batch-result.json", canonical_json_bytes(batch))
        return 2

    terminals: list[dict[str, object]] = []
    runs_root = evidence_root / "runs"
    runs_root.mkdir(mode=0o700)
    for index, run in enumerate(registry["runs"], start=1):
        try:
            terminal = _run_one(
                index=index,
                run=run,
                registry=registry,
                prepared_root=prepared_root,
                runs_root=runs_root,
                socket_stage_root=socket_stage_root,
                packages=packages,
                gateway_input=gateway_input,
                forbidden=forbidden,
                runtime=runtime,
                provider_address=provider_address,
                implementation_commit=implementation_commit,
                timeout_seconds=arguments.timeout_seconds,
            )
        except Exception as exc:
            terminal = _preserve_unhandled_run_failure(
                index=index,
                run=run,
                runs_root=runs_root,
                exc=exc,
            )
        terminals.append(terminal)
        sys.stdout.write(
            canonical_json_bytes(
                {
                    "run": index,
                    "run_key": terminal["run_key"],
                    "status": terminal["status"],
                }
            ).decode("utf-8")
            + "\n"
        )
        sys.stdout.flush()
        if terminal.get("failure_stage") in {
            "ANSWER_STARTUP",
            "ANSWER_OPERATION_AUDIT",
            "GATEWAY_OPERATION_AUDIT",
            "POSTCONDITION",
            "UNHANDLED_RUN_FAILURE",
        }:
            break

    status = "PASS" if all(item["status"] == "SUCCESS" for item in terminals) else "FAIL"
    batch = _batch_result(
        implementation_commit=implementation_commit,
        tree=tree,
        invocation=invocation,
        registry=registry,
        provider_addresses=addresses,
        provider_address=provider_address,
        preflight=preflight,
        terminals=terminals,
        stage_root=stage_root,
        socket_stage_root=socket_stage_root,
        status=status,
    )
    _write_new(evidence_root / "batch-result.json", canonical_json_bytes(batch))
    print(canonical_json_bytes(batch).decode("utf-8"))
    return 0 if batch["status"] == "PASS" else 2


def _run_one(
    *,
    index: int,
    run: Mapping[str, object],
    registry: Mapping[str, object],
    prepared_root: Path,
    runs_root: Path,
    socket_stage_root: Path,
    packages: Mapping[str, Path],
    gateway_input: Path,
    forbidden: Mapping[str, Path],
    runtime: Mapping[str, object],
    provider_address: str,
    implementation_commit: str,
    timeout_seconds: float,
) -> dict[str, object]:
    del registry
    run_key = _text(run.get("run_key"), "run key")
    run_root = runs_root / f"{index:02d}"
    run_root.mkdir(mode=0o700)
    evaluator_root = run_root / "evaluator"
    answer_input = run_root / "answer-input"
    answer_output = run_root / "answer-output"
    gateway_output = run_root / "gateway-output"
    for directory in (evaluator_root, answer_input, answer_output, gateway_output):
        directory.mkdir(mode=0o700)
    citation_seals = answer_output / "citation-seals"
    citation_seals.mkdir(mode=0o700)
    selector = _selector_for_run(run, prepared_root)
    ordered = answer_input / "ordered.json"
    shutil.copy2(selector["ordered_bundle"], ordered)
    snapshots: list[Path] = []
    for number, source in enumerate(selector["snapshot_bundles"], start=1):
        target = answer_input / f"snapshot-{number}.json"
        shutil.copy2(source, target)
        snapshots.append(target)
    if [item.value if hasattr(item, "value") else item for item in run["resolved_snapshot_ids"]] != selector["resolved_snapshot_ids"]:
        raise RuntimeError(f"run {run_key} selector Snapshot IDs drifted")

    socket_root = socket_stage_root / f"{index:02d}"
    socket_root.mkdir(mode=0o700)
    gateway_socket = socket_root / "gateway.sock"
    connected, provisioning = _provision_provider_socket(provider_address)
    try:
        gateway_listener, listener_provisioning = _provision_gateway_listener(
            gateway_socket
        )
    except BaseException:
        connected.close()
        raise
    connection_fd = connected.fileno()
    listener_fd = gateway_listener.fileno()
    try:
        _write_new(
            evaluator_root / "connection-provisioning.json",
            canonical_json_bytes(provisioning),
        )
        _write_new(
            evaluator_root / "gateway-listener-provisioning.json",
            canonical_json_bytes(listener_provisioning),
        )
        gateway_environment = _role_environment(
            gateway_output,
            credential=_required_credential(),
        )
    except BaseException:
        connected.close()
        gateway_listener.close()
        try:
            gateway_socket.unlink()
        except FileNotFoundError:
            pass
        raise
    payload = {
        "case_id": _text(run.get("case_id"), "case ID"),
        "question_variant": _text(run.get("question"), "question"),
        "resolved_snapshot_ids": list(run["resolved_snapshot_ids"]),
    }
    answer_summary = answer_output / "summary.json"
    answer_page = answer_output / "evaluation.html"
    gateway_summary = gateway_output / "summary.json"
    gateway_report = gateway_output / "role-report.json"
    answer_report = answer_output / "role-report.json"
    request_started_ns: int | None = None

    gateway_argv = [
        "--socket-path", str(gateway_socket),
        "--gateway-listener-socket-fd", str(listener_fd),
        "--numeric-provider-address", provider_address,
        "--connected-provider-socket-fd", str(connection_fd),
        "--database", str(gateway_output / "model-gateway.sqlite3"),
        "--conformance-result", str(gateway_input / "conformance.json"),
        "--capability-qualification", str(gateway_input / "qualification.json"),
        "--closed-capability-result", str(gateway_input / "closed-result.json"),
        "--egress-policy", str(gateway_input / "egress-policy.json"),
        "--g3b-freeze", str(gateway_input / "g3b-freeze.json"),
        "--implementation-commit", implementation_commit,
        "--server-audit-output", str(gateway_output / "server-audit.jsonl"),
        "--transport-audit-output", str(gateway_output / "transport-audit.jsonl"),
        "--summary-output", str(gateway_summary),
        "--startup-timeout-seconds", "30",
        "--idle-timeout-seconds", "0.25",
    ]
    gateway_policy = _audit_policy(
        role="gateway",
        package_root=packages["gateway"],
        input_root=gateway_input,
        output_root=gateway_output,
        socket_root=socket_root,
        provider_address=provider_address,
        runtime=runtime,
        forbidden=forbidden,
        other_role_roots=(packages["answer"], packages["projector"]),
    )
    gateway_parameters = _profile_parameters(
        role="gateway",
        package_root=packages["gateway"],
        input_root=gateway_input,
        output_root=gateway_output,
        socket_root=socket_root,
        gateway_socket=gateway_socket,
        runtime=runtime,
    )
    gateway_command = _role_command(
        role="gateway",
        package_root=packages["gateway"],
        output_root=gateway_output,
        entrypoint=".g3b/gateway_workload.py",
        argv=gateway_argv,
        report=gateway_report,
        policy=gateway_policy,
        parameters=gateway_parameters,
        nonce=secrets.token_hex(16),
    )
    cold_process_started_ns = time.monotonic_ns()
    try:
        gateway_process = subprocess.Popen(
            gateway_command,
            cwd=str(packages["gateway"]),
            env=gateway_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(connection_fd, listener_fd),
        )
    except BaseException:
        connected.close()
        gateway_listener.close()
        try:
            gateway_socket.unlink()
        except FileNotFoundError:
            pass
        raise
    else:
        connected.close()
        gateway_listener.close()
    failure_stage: str | None = None
    answer_process_elapsed_milliseconds: int | None = None
    answer_value: Mapping[str, object] | None = None
    try:
        _wait_for_socket(gateway_socket, gateway_process, timeout_seconds=30.0)
        answer_argv = [
            "--product-payload-base64", _encode(payload),
            "--ordered-bundle", str(ordered),
        ]
        for snapshot in snapshots:
            answer_argv.extend(("--snapshot-bundle", str(snapshot)))
        answer_argv.extend(
            (
                "--gateway-socket", str(gateway_socket),
                "--run-ref", run_key,
                "--implementation-commit", implementation_commit,
                "--authority-page-output", str(answer_page),
                "--citation-seal-output-directory", str(citation_seals),
                "--summary-output", str(answer_summary),
            )
        )
        answer_policy = _audit_policy(
            role="answer",
            package_root=packages["answer"],
            input_root=answer_input,
            output_root=answer_output,
            socket_root=socket_root,
            provider_address=provider_address,
            runtime=runtime,
            forbidden=forbidden,
            other_role_roots=(packages["gateway"], packages["projector"]),
            gateway_socket=gateway_socket,
        )
        answer_command = _role_command(
            role="answer",
            package_root=packages["answer"],
            output_root=answer_output,
            entrypoint=".g3b/answer_workload.py",
            argv=answer_argv,
            report=answer_report,
            policy=answer_policy,
            parameters=_profile_parameters(
                role="answer",
                package_root=packages["answer"],
                input_root=answer_input,
                output_root=answer_output,
                socket_root=socket_root,
                gateway_socket=gateway_socket,
                runtime=runtime,
            ),
            nonce=secrets.token_hex(16),
        )
        answer_process_started_ns = time.monotonic_ns()
        request_started_ns = answer_process_started_ns
        answer_completed = subprocess.run(
            answer_command,
            cwd=str(packages["answer"]),
            env=_role_environment(answer_output),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        answer_process_elapsed_milliseconds = (
            time.monotonic_ns() - answer_process_started_ns
        ) // 1_000_000
        _preserve_process_streams(evaluator_root, "answer", answer_completed)
        if answer_completed.returncode != 0:
            failure_stage = (
                "ANSWER_OPERATION_AUDIT"
                if _is_operation_audit_failure(answer_report)
                else "ANSWER"
            )
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        failure_stage = "ANSWER_STARTUP"
        _write_new(
            evaluator_root / "answer-launch-failure.json",
            canonical_json_bytes(
                {"type": type(exc).__name__, "errno": getattr(exc, "errno", None)}
            ),
        )
    gateway_stdout, gateway_stderr = _finish_gateway(gateway_process, timeout_seconds)
    _preserve_stream_bytes(evaluator_root, "gateway", gateway_stdout, gateway_stderr)
    if gateway_process.returncode != 0 and failure_stage is None:
        failure_stage = (
            "GATEWAY_OPERATION_AUDIT"
            if _is_operation_audit_failure(gateway_report)
            else "GATEWAY"
        )

    projections: list[dict[str, object]] = []
    if failure_stage is None and answer_summary.is_file() and gateway_summary.is_file():
        answer_value = _load_json(answer_summary)
        gateway_value = _load_json(gateway_summary)
        postcondition_phase = "ROLE_POSTCONDITION"
        try:
            _verify_role_success(answer_report, "answer")
            _verify_role_success(gateway_report, "gateway")
            _verify_answer_gateway(answer_value, gateway_value, payload, run_key)
            postcondition_phase = "CITATION_PROJECTION"
            projections = _project_all_citations(
                run_root=run_root,
                answer_summary=answer_value,
                citation_seals=citation_seals,
                authority_database=selector["authority_database"],
                packages=packages,
                forbidden=forbidden,
                runtime=runtime,
                provider_address=provider_address,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            failure_stage = postcondition_phase
            _write_new(
                evaluator_root / "postcondition-failure.json",
                canonical_json_bytes(
                    {
                        "phase": postcondition_phase,
                        "type": type(exc).__name__,
                        "errno": getattr(exc, "errno", None),
                    }
                ),
            )
    status = "SUCCESS" if failure_stage is None else "FAILURE"
    terminal_core = {
        "schema": "swm.iter-003.g3b-run-terminal@1",
        "run_key": run_key,
        "case_id": run["case_id"],
        "run_number": run["run_number"],
        "status": status,
        "failure_stage": failure_stage,
        "attempt_count": 1,
        "selective_retry_count": 0,
        "provider_connection_handoff_count": 1,
        "gateway_listener_handoff_count": 1,
        "gateway_listener_provisioning": _file_reference(
            evaluator_root / "gateway-listener-provisioning.json"
        ),
        "performance_timing_receipt": "timing.json",
        "answer_summary": _file_reference(answer_summary),
        "gateway_summary": _file_reference(gateway_summary),
        "answer_role_report": _file_reference(answer_report),
        "gateway_role_report": _file_reference(gateway_report),
        "citation_projection_count": len(projections),
        "citation_projections": projections,
        "completed_at": _utc_now(),
        "production_activation": "NOT_EXECUTED",
    }
    terminal = {**terminal_core, "document_digest": digest_of(terminal_core).value}
    terminal_path = run_root / "terminal.json"
    _write_new(terminal_path, canonical_json_bytes(terminal))
    terminal_persisted_ns = time.monotonic_ns()
    timing_core = {
        "schema": "swm.iter-003.g3b-run-timing@1",
        "run_key": run_key,
        "terminal_document_digest": terminal["document_digest"],
        "terminal_file_digest": _sha256_file(terminal_path),
        "request_elapsed_milliseconds": (
            (terminal_persisted_ns - request_started_ns) // 1_000_000
            if request_started_ns is not None
            else None
        ),
        "cold_process_elapsed_milliseconds": (
            terminal_persisted_ns - cold_process_started_ns
        )
        // 1_000_000,
        "answer_process_elapsed_milliseconds": answer_process_elapsed_milliseconds,
        "answer_worker_request_elapsed_milliseconds": (
            answer_value.get("request_elapsed_milliseconds")
            if answer_value is not None
            else None
        ),
        "answer_worker_cold_process_elapsed_milliseconds": (
            answer_value.get("cold_process_elapsed_milliseconds")
            if answer_value is not None
            else None
        ),
        "request_timing_scope": (
            "ANSWER_REQUEST_DISPATCH_TO_G3B_TERMINAL_PERSISTED_INCLUDING_"
            "GATEWAY_AND_CITATION_PROJECTION"
        ),
        "cold_timing_scope": "GATEWAY_PROCESS_START_TO_G3B_TERMINAL_PERSISTED",
        "persisted_at": _utc_now(),
        "production_activation": "NOT_EXECUTED",
    }
    timing = {**timing_core, "document_digest": digest_of(timing_core).value}
    _write_new(run_root / "timing.json", canonical_json_bytes(timing))
    return {**terminal, "_timing_document_digest": timing["document_digest"]}


def _preserve_unhandled_run_failure(
    *,
    index: int,
    run: Mapping[str, object],
    runs_root: Path,
    exc: Exception,
) -> dict[str, object]:
    run_root = runs_root / f"{index:02d}"
    run_root.mkdir(mode=0o700, exist_ok=True)
    failure = run_root / "unhandled-failure.json"
    if not failure.exists():
        _write_new(
            failure,
            canonical_json_bytes(
                {
                    "type": type(exc).__name__,
                    "errno": getattr(exc, "errno", None),
                }
            ),
        )
    core = {
        "schema": "swm.iter-003.g3b-run-terminal@1",
        "run_key": _text(run.get("run_key"), "run key"),
        "case_id": run.get("case_id"),
        "run_number": run.get("run_number"),
        "status": "FAILURE",
        "failure_stage": "UNHANDLED_RUN_FAILURE",
        "attempt_count": 1,
        "selective_retry_count": 0,
        "provider_connection_handoff_count": 0,
        "gateway_listener_handoff_count": 0,
        "gateway_listener_provisioning": None,
        "performance_timing_receipt": None,
        "answer_summary": None,
        "gateway_summary": None,
        "answer_role_report": None,
        "gateway_role_report": None,
        "citation_projection_count": 0,
        "citation_projections": [],
        "completed_at": _utc_now(),
        "production_activation": "NOT_EXECUTED",
    }
    terminal = {**core, "document_digest": digest_of(core).value}
    terminal_path = run_root / "terminal.json"
    if not terminal_path.exists():
        _write_new(terminal_path, canonical_json_bytes(terminal))
    return terminal


def _project_all_citations(
    *,
    run_root: Path,
    answer_summary: Mapping[str, object],
    citation_seals: Path,
    authority_database: Path,
    packages: Mapping[str, Path],
    forbidden: Mapping[str, Path],
    runtime: Mapping[str, object],
    provider_address: str,
    timeout_seconds: float,
) -> list[dict[str, object]]:
    values = answer_summary.get("citation_seals")
    if not isinstance(values, list):
        raise RuntimeError("Answer citation seal index is invalid")
    citations_root = run_root / "citations"
    citations_root.mkdir(mode=0o700)
    projected: list[dict[str, object]] = []
    for index, value in enumerate(values, start=1):
        if not isinstance(value, dict):
            raise RuntimeError("Answer citation seal entry is invalid")
        root = citations_root / f"{index:02d}"
        input_root = root / "input"
        evaluator_root = root / "evaluator"
        output_root = root / "output"
        for directory in (root, input_root, evaluator_root, output_root):
            if directory == root:
                directory.mkdir(mode=0o700)
            else:
                directory.mkdir(mode=0o700)
        source_seal = citation_seals / _text(value.get("file_name"), "seal file")
        if _sha256_file(source_seal) != value.get("file_digest"):
            raise RuntimeError("Answer citation seal file digest drifted")
        sealed = input_root / "sealed-result.json"
        shutil.copy2(source_seal, sealed)
        store_root = root / "store"
        materialization = evaluator_root / "materialization.json"
        broker = _run_evaluator_entrypoint(
            package_root=packages["broker"],
            entrypoint=packages["broker"] / ".g3b" / "materialize_citations.py",
            argv=(
                "--authority-database", str(authority_database),
                "--sealed-result", str(sealed),
                "--store-root", str(store_root),
                "--summary-output", str(materialization),
            ),
            output_root=evaluator_root,
            label="broker",
            timeout_seconds=timeout_seconds,
        )
        if broker.returncode != 0:
            raise RuntimeError("trusted Citation broker failed")
        projection = output_root / "projection.json"
        report = output_root / "role-report.json"
        policy = _audit_policy(
            role="projector",
            package_root=packages["projector"],
            input_root=input_root,
            output_root=output_root,
            socket_root=root,
            provider_address=provider_address,
            runtime=runtime,
            forbidden=forbidden,
            other_role_roots=(packages["answer"], packages["gateway"]),
            store_root=store_root,
        )
        command = _role_command(
            role="projector",
            package_root=packages["projector"],
            output_root=output_root,
            entrypoint=".g3b/projection_workload.py",
            argv=(
                "--sealed-result", str(sealed),
                "--store", str(store_root),
                "--expected-result-id", _text(value.get("result_id"), "result ID"),
                "--expected-seal-digest", _text(value.get("seal_digest"), "seal digest"),
                "--projection-output", str(projection),
            ),
            report=report,
            policy=policy,
            parameters=_profile_parameters(
                role="projector",
                package_root=packages["projector"],
                input_root=input_root,
                output_root=output_root,
                socket_root=root,
                gateway_socket=root / "forbidden.sock",
                runtime=runtime,
                store_root=store_root,
            ),
            nonce=secrets.token_hex(16),
        )
        completed = subprocess.run(
            command,
            cwd=str(packages["projector"]),
            env=_role_environment(output_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
        _preserve_process_streams(evaluator_root, "projector", completed)
        if completed.returncode != 0:
            raise RuntimeError("sandboxed Citation Projector failed")
        _verify_role_success(report, "projector")
        projection_value = _load_json(projection)
        materialization_value = _load_json(materialization)
        if (
            projection_value.get("status") != "PASS"
            or projection_value.get("network_operation_count") != 0
            or projection_value.get("answer_return_port") is not False
            or materialization_value.get("status") != "PASS"
            or materialization_value.get("result_id") != value.get("result_id")
            or materialization_value.get("seal_digest") != value.get("seal_digest")
        ):
            raise RuntimeError("Citation materialization/projection binding failed")
        projected.append(
            {
                "result_id": value["result_id"],
                "seal_digest": value["seal_digest"],
                "materialization": _file_reference(materialization),
                "projection": _file_reference(projection),
                "role_report": _file_reference(report),
                "store_manifest_digest": materialization_value["store_manifest_digest"],
            }
        )
    return projected


def _run_preflight(
    *,
    evidence_root: Path,
    stage_root: Path,
    socket_stage_root: Path,
    packages: Mapping[str, Path],
    gateway_input: Path,
    forbidden: Mapping[str, Path],
    runtime: Mapping[str, object],
    provider_address: str,
) -> dict[str, object]:
    preflight_root = evidence_root / "preflight"
    preflight_root.mkdir(mode=0o700)
    protected_stage_manifest_before = _tree_manifest(stage_root)
    records: dict[str, object] = {}
    for ordinal, role in enumerate(("answer", "gateway", "projector"), start=1):
        role_root = preflight_root / role
        output_root = role_root / "output"
        input_root = role_root / "input"
        store_root = role_root / "store"
        socket_root = socket_stage_root / f"probe-{ordinal}"
        for directory in (role_root, output_root, input_root, store_root, socket_root):
            directory.mkdir(mode=0o700)
        allowed_read = input_root / "allowed.txt"
        _write_new(allowed_read, b"allowed\n")
        if role == "gateway":
            allowed_read = gateway_input / "conformance.json"
        gateway_socket = socket_root / "gateway.sock"
        other_socket = socket_root / "other.sock"
        local_listener = _TCPListener()
        exact_listener = None
        other_listener = _UnixListener(other_socket)
        if role in {"answer", "projector"}:
            exact_listener = _UnixListener(gateway_socket)
        inherited_connection: socket.socket | None = None
        gateway_listener: socket.socket | None = None
        gateway_probe_client: socket.socket | None = None
        gateway_listener_provisioning: Mapping[str, object] | None = None
        try:
            if role == "gateway":
                inherited_connection, provisioning = _provision_provider_socket(
                    provider_address
                )
                _write_new(
                    role_root / "connection-provisioning.json",
                    canonical_json_bytes(provisioning),
                )
                gateway_listener, gateway_listener_provisioning = (
                    _provision_gateway_listener(gateway_socket)
                )
                _write_new(
                    role_root / "gateway-listener-provisioning.json",
                    canonical_json_bytes(gateway_listener_provisioning),
                )
                gateway_probe_client = socket.socket(
                    socket.AF_UNIX, socket.SOCK_STREAM
                )
                gateway_probe_client.settimeout(10.0)
                gateway_probe_client.connect(str(gateway_socket))
                gateway_probe_client.sendall(b"P")
            inherited_fd = (
                inherited_connection.fileno()
                if inherited_connection is not None
                else -1
            )
            gateway_listener_fd = (
                gateway_listener.fileno() if gateway_listener is not None else -1
            )
            argv = [
                "--role", role,
                "--nonce", secrets.token_hex(16),
                "--allowed-read-file", str(allowed_read),
                "--allowed-write-file", str(output_root / "allowed-write.txt"),
                "--gateway-socket", str(gateway_socket),
                "--other-unix-socket", str(other_socket),
                "--provider-address", provider_address,
                "--connected-provider-socket-fd", str(inherited_fd),
                "--gateway-listener-socket-fd", str(gateway_listener_fd),
                "--local-tcp-port", str(local_listener.port),
                "--output", str(output_root / "probe.json"),
            ]
            for label, path in sorted(forbidden.items()):
                argv.extend(("--forbidden-file", f"{label}={path}"))
            parameters = _profile_parameters(
                role=role,
                package_root=packages[role],
                input_root=gateway_input if role == "gateway" else input_root,
                output_root=output_root,
                socket_root=socket_root,
                gateway_socket=gateway_socket,
                runtime=runtime,
                store_root=store_root,
            )
            command = _sandbox_prefix(role, parameters) + [
                str(runtime["python_executable"]),
                *SANDBOXED_PYTHON_FLAGS,
                str(packages[role] / ".g3b" / "os_probe_worker.py"),
                *argv,
            ]
            inherited_fds = tuple(
                descriptor
                for descriptor in (
                    inherited_fd,
                    gateway_listener_fd,
                )
                if descriptor >= 0
            )
            completed = subprocess.run(
                command,
                cwd=str(packages[role]),
                env=_role_environment(
                    output_root,
                    credential="g3b-probe-sentinel" if role == "gateway" else None,
                ),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=60,
                check=False,
                pass_fds=inherited_fds,
            )
            if inherited_connection is not None:
                inherited_connection.close()
                inherited_connection = None
            _preserve_process_streams(role_root, "probe", completed)
            probe_path = output_root / "probe.json"
            value = _load_json(probe_path) if probe_path.is_file() else None
            gateway_listener_round_trip = None
            if gateway_probe_client is not None:
                try:
                    gateway_listener_round_trip = (
                        gateway_probe_client.recv(1) == b"Q"
                    )
                except OSError:
                    gateway_listener_round_trip = False
            records[role] = {
                "returncode": completed.returncode,
                "profile": str(HERE / f"{role}.sb"),
                "profile_digest": _sha256_file(HERE / f"{role}.sb"),
                "parameters": parameters,
                "probe": value,
                "gateway_listener_provisioning": (
                    gateway_listener_provisioning
                ),
                "gateway_listener_round_trip": gateway_listener_round_trip,
                "status": (
                    "PASS"
                    if completed.returncode == 0
                    and isinstance(value, dict)
                    and value.get("status") == "PASS"
                    and (
                        role != "gateway"
                        or gateway_listener_round_trip is True
                    )
                    else "FAIL"
                ),
            }
        finally:
            if inherited_connection is not None:
                inherited_connection.close()
            if gateway_probe_client is not None:
                gateway_probe_client.close()
            if gateway_listener is not None:
                gateway_listener.close()
                try:
                    gateway_socket.unlink()
                except FileNotFoundError:
                    pass
            if exact_listener is not None:
                exact_listener.close()
            other_listener.close()
            local_listener.close()
    protected_stage_manifest_after = _tree_manifest(stage_root)
    protected_stage_unchanged = (
        protected_stage_manifest_after == protected_stage_manifest_before
    )
    status = (
        "PASS"
        if all(value["status"] == "PASS" for value in records.values())
        and protected_stage_unchanged
        else "FAIL"
    )
    core = {
        "schema": "swm.iter-003.g3b-preflight@1",
        "status": status,
        "provider_address": provider_address,
        "roles": records,
        "protected_stage_manifest_before": protected_stage_manifest_before,
        "protected_stage_manifest_after": protected_stage_manifest_after,
        "protected_stage_unchanged": protected_stage_unchanged,
        "os_enforcement": "MACOS_SEATBELT_DENY_DEFAULT",
        "gateway_external_capability": (
            "INHERITED_EXACT_PROVIDER_AND_AF_UNIX_LISTENER_FDS; "
            "NEW_SOCKET_SYSCALL_DENIED"
        ),
        "ancestor_limitation": (
            "literal ancestor reads may expose direct entry names, not child contents"
        ),
        "production_activation": "NOT_EXECUTED",
    }
    result = {**core, "document_digest": digest_of(core).value}
    _write_new(evidence_root / "preflight.json", canonical_json_bytes(result))
    return result


def _stage_packages(stage_root: Path) -> dict[str, Path]:
    package_root = stage_root / "packages"
    package_root.mkdir(mode=0o700)
    workloads = {
        "answer": "answer_workload.py",
        "gateway": "gateway_workload.py",
        "projector": "projection_workload.py",
        "broker": "materialize_citations.py",
    }
    result: dict[str, Path] = {}
    for role, workload in workloads.items():
        root = package_root / role
        root.mkdir(mode=0o700)
        shutil.copytree(
            PROJECT_ROOT / "src" / "software_world_model",
            root / "software_world_model",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        worker_root = root / ".g3b"
        worker_root.mkdir(mode=0o700)
        shutil.copy2(HERE / workload, worker_root / workload)
        if role != "broker":
            shutil.copy2(HERE / "role_worker.py", worker_root / "role_worker.py")
            shutil.copy2(HERE / "os_probe_worker.py", worker_root / "os_probe_worker.py")
        result[role] = root.resolve(strict=True)
    return result


def _stage_gateway_input(stage_root: Path) -> Path:
    root = stage_root / "gateway-input"
    root.mkdir(mode=0o700)
    for source, name in (
        (CONFORMANCE, "conformance.json"),
        (QUALIFICATION, "qualification.json"),
        (CLOSED_RESULT, "closed-result.json"),
        (EGRESS_POLICY, "egress-policy.json"),
        (G3B_FREEZE, "g3b-freeze.json"),
    ):
        shutil.copy2(source.resolve(strict=True), root / name)
    return root.resolve(strict=True)


def _stage_forbidden_canaries(
    stage_root: Path,
    prepared_root: Path,
    packages: Mapping[str, Path],
) -> dict[str, Path]:
    canaries = stage_root / "forbidden"
    canaries.mkdir(mode=0o700)
    result = {
        "source": (PROJECT_ROOT / "validation-projects" / "mall" / "pom.xml").resolve(strict=True),
        "original_worktree": (PROJECT_ROOT / "src" / "software_world_model" / "__init__.py").resolve(strict=True),
        "git": (PROJECT_ROOT / ".git" / "HEAD").resolve(strict=True),
        "authority_database": next((prepared_root / "authority").glob("*.sqlite3")).resolve(strict=True),
        "product_oracle": PRODUCT_SUITE.resolve(strict=True),
        "baseline_result": next(BASELINES.glob("direct/runs/*/terminal.json")).resolve(strict=True),
        "other_role": (packages["broker"] / "software_world_model" / "__init__.py").resolve(strict=True),
    }
    for name in ("evidence-payload", "evidence-store"):
        path = canaries / f"{name}.txt"
        _write_new(path, f"{name}\n".encode("ascii"))
        result[name.replace("-", "_")] = path
    return result


def _runtime_capabilities() -> dict[str, object]:
    executable = Path(sys.executable).resolve(strict=True)
    runtime = _python_runtime_read_root()
    dependencies = _python_runtime_dependency_capabilities(runtime)
    return {
        "python_executable": executable,
        "python_runtime": runtime,
        "dependencies": dependencies,
    }


def _profile_parameters(
    *,
    role: str,
    package_root: Path,
    input_root: Path,
    output_root: Path,
    socket_root: Path,
    gateway_socket: Path,
    runtime: Mapping[str, object],
    store_root: Path | None = None,
) -> dict[str, str]:
    dependencies = runtime["dependencies"]
    recursive_roots = {
        runtime["python_runtime"],
        *(item.root for item in dependencies),
        Path("/System/Library"),
        Path("/usr/lib"),
        Path("/private/var/db/dyld"),
        package_root,
        input_root,
        output_root,
    }
    if store_root is not None:
        recursive_roots.add(store_root)
    directory_roots = set(recursive_roots)
    directory_roots.add(runtime["python_executable"].parent)
    directory_roots.add(socket_root)
    directory_roots.add(Path("/private/etc"))
    directory_roots.add(Path("/private/etc/ssl"))
    directory_roots.update(item.alias for item in dependencies)
    ancestors = sorted(
        {
            ancestor
            for root in directory_roots
            for ancestor in (root, *root.parents)
        },
        key=lambda item: (len(item.parts), str(item)),
    )
    if len(ancestors) > ANCESTOR_PARAMETER_COUNT:
        raise RuntimeError("G3b profile ancestor set exceeds fixed capacity")
    common = {
        "PYTHON_EXECUTABLE": str(runtime["python_executable"]),
        "PYTHON_RUNTIME": str(runtime["python_runtime"]),
        **{
            f"PYTHON_RUNTIME_DEPENDENCY_{index:02d}": str(
                dependencies[index].root
                if index < len(dependencies)
                else runtime["python_runtime"]
            )
            for index in range(RUNTIME_DEPENDENCY_PARAMETER_COUNT)
        },
        **{
            f"ANCESTOR_{index:02d}": str(
                ancestors[index] if index < len(ancestors) else Path("/")
            )
            for index in range(ANCESTOR_PARAMETER_COUNT)
        },
        "PACKAGE_ROOT": str(package_root),
        "OUTPUT_ROOT": str(output_root),
    }
    if role == "answer":
        return {
            **common,
            "BUNDLE_ROOT": str(input_root),
            "GATEWAY_SOCKET": str(gateway_socket),
        }
    if role == "gateway":
        return {
            **common,
            "INPUT_ROOT": str(input_root),
            "SOCKET_ROOT": str(socket_root),
            "GATEWAY_SOCKET": str(gateway_socket),
        }
    if role == "projector" and store_root is not None:
        return {
            **common,
            "INPUT_ROOT": str(input_root),
            "STORE_ROOT": str(store_root),
        }
    raise ValueError("unsupported G3b profile role")


def _audit_policy(
    *,
    role: str,
    package_root: Path,
    input_root: Path,
    output_root: Path,
    socket_root: Path,
    provider_address: str,
    runtime: Mapping[str, object],
    forbidden: Mapping[str, Path],
    other_role_roots: tuple[Path, ...],
    gateway_socket: Path | None = None,
    store_root: Path | None = None,
) -> dict[str, object]:
    allowed_read = [
        runtime["python_runtime"],
        *(item.root for item in runtime["dependencies"]),
        Path("/System/Library"),
        Path("/usr/lib"),
        Path("/private/var/db/dyld"),
        package_root,
        input_root,
        output_root,
    ]
    if store_root is not None:
        allowed_read.append(store_root)
    categories = {
        "source_operations": [
            str(forbidden["source"]),
            str(forbidden["original_worktree"]),
        ],
        "git_operations": [str(forbidden["git"])],
        "evidence_payload_reads": [str(forbidden["evidence_payload"])],
        "authority_database_operations": [str(forbidden["authority_database"])],
        "evidence_store_operations": [str(forbidden["evidence_store"])],
        "other_role_operations": [str(item) for item in other_role_roots],
        "product_oracle_operations": [str(forbidden["product_oracle"])],
        "baseline_result_operations": [str(forbidden["baseline_result"])],
    }
    return {
        "allowed_read_roots": [str(item) for item in allowed_read],
        "allowed_read_files": [
            "/dev/null",
            "/dev/random",
            "/dev/urandom",
            "/private/etc/localtime",
            "/private/etc/ssl/cert.pem",
            "/etc/ssl/cert.pem",
        ],
        "allowed_write_roots": [
            str(output_root),
            *([str(socket_root)] if role == "gateway" else []),
        ],
        "allowed_write_files": ["/dev/null"],
        "allowed_network": {
            "unix_connect": (
                [str(gateway_socket)]
                if role == "answer" and gateway_socket is not None
                else []
            ),
            "unix_bind": [],
            "provider_connect": [],
        },
        "forbidden_categories": categories,
    }


def _role_command(
    *,
    role: str,
    package_root: Path,
    output_root: Path,
    entrypoint: str,
    argv: Sequence[str],
    report: Path,
    policy: Mapping[str, object],
    parameters: Mapping[str, str],
    nonce: str,
) -> list[str]:
    return _sandbox_prefix(role, parameters) + [
        str(Path(sys.executable).resolve(strict=True)),
        *SANDBOXED_PYTHON_FLAGS,
        str(package_root / ".g3b" / "role_worker.py"),
        "--role", role,
        "--nonce", nonce,
        "--package-root", str(package_root),
        "--output-root", str(output_root),
        "--entrypoint", entrypoint,
        "--argv-base64", _encode(list(argv)),
        "--audit-policy-base64", _encode(policy),
        "--report-output", str(report),
    ]


def _sandbox_prefix(role: str, parameters: Mapping[str, str]) -> list[str]:
    command = [str(SANDBOX_EXEC)]
    for key, value in sorted(parameters.items()):
        command.extend(("-D", f"{key}={value}"))
    command.extend(("-f", str(HERE / f"{role}.sb")))
    return command


def _run_evaluator_entrypoint(
    *,
    package_root: Path,
    entrypoint: Path,
    argv: Sequence[str],
    output_root: Path,
    label: str,
    timeout_seconds: float,
) -> subprocess.CompletedProcess[bytes]:
    loader = (
        "import runpy,sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "sys.argv=sys.argv[2:];"
        "runpy.run_path(sys.argv[0],run_name='__main__')"
    )
    completed = subprocess.run(
        [
            str(Path(sys.executable).resolve(strict=True)),
            *SANDBOXED_PYTHON_FLAGS,
            "-c", loader,
            str(package_root),
            str(entrypoint),
            *argv,
        ],
        cwd=str(package_root),
        env=_role_environment(output_root),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )
    _preserve_process_streams(output_root, label, completed)
    return completed


def _role_environment(output_root: Path, *, credential: str | None = None) -> dict[str, str]:
    value = {
        "TMPDIR": str(output_root),
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }
    if credential is not None:
        value["ARK_API_KEY"] = credential
    return value


def _verify_role_success(path: Path, role: str) -> Mapping[str, object]:
    value = _load_json(path)
    audit = value.get("operation_audit")
    expected_network = {
        "answer": {"unix_connect": 1, "unix_bind": 0, "provider_connect": 0},
        "gateway": {"unix_connect": 0, "unix_bind": 0, "provider_connect": 0},
        "projector": {"unix_connect": 0, "unix_bind": 0, "provider_connect": 0},
    }
    if (
        value.get("status") != "PASS"
        or value.get("role") != role
        or not isinstance(audit, dict)
        or audit.get("status") != "PASS"
        or audit.get("allowed_network_operations") != expected_network[role]
        or any(audit.get("prohibited_counts", {}).values())
    ):
        raise RuntimeError(f"{role} normal workload audit failed")
    return value


def _is_operation_audit_failure(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        value = _load_json(path)
    except (OSError, ValueError):
        return False
    audit = value.get("operation_audit")
    return (
        value.get("exit_code") == 0
        and isinstance(audit, dict)
        and audit.get("status") == "FAIL"
    )


def _verify_answer_gateway(
    answer: Mapping[str, object],
    gateway: Mapping[str, object],
    payload: Mapping[str, object],
    run_key: str,
) -> None:
    if (
        answer.get("status") != "PASS"
        or answer.get("run_ref") != run_key
        or answer.get("provider_call_count") != 1
        or answer.get("network_operation_count") != 1
        or answer.get("source_access_count") != 0
        or answer.get("evidence_payload_access_count") != 0
        or answer.get("authority_database_access_count") != 0
        or answer.get("product_oracle_read_count") != 0
        or answer.get("baseline_result_read_count") != 0
        or answer.get("credential_visible") is not False
        or answer.get("resolved_snapshot_ids") != payload["resolved_snapshot_ids"]
        or gateway.get("status") != "PASS"
        or gateway.get("provider_call_count") != 1
        or gateway.get("https_dispatch_count") != 1
        or gateway.get("server_statuses") != ["RESULT"]
        or gateway.get("dns_operation_count_in_dispatch_process") != 0
        or gateway.get("credential_value_recorded") is not False
        or gateway.get("provider_connection_capability")
        != "INHERITED_EXACT_CONNECTED_SOCKET"
        or gateway.get("gateway_listener_capability")
        != "INHERITED_EXACT_BOUND_AF_UNIX_LISTENER"
        or gateway.get("new_socket_syscall_capability")
        != "DENIED_BY_SEATBELT"
        or gateway.get("numeric_provider_address_scope")
        != _provider_address_scope(
            gateway.get("numeric_provider_address")
        )
    ):
        raise RuntimeError("Answer/Gateway exact postcondition failed")


def _batch_result(
    *,
    implementation_commit: str,
    tree: str,
    invocation: Mapping[str, object],
    registry: Mapping[str, object],
    provider_addresses: Sequence[str],
    provider_address: str,
    preflight: Mapping[str, object],
    terminals: Sequence[Mapping[str, object]],
    stage_root: Path,
    socket_stage_root: Path,
    status: str,
) -> dict[str, object]:
    success = sum(item.get("status") == "SUCCESS" for item in terminals)
    stage_manifest_after = _tree_manifest(stage_root)
    stage_manifest_before = preflight.get("protected_stage_manifest_before")
    stage_unchanged = stage_manifest_after == stage_manifest_before
    effective_status = status if stage_unchanged else "FAIL"
    core = {
        "schema": RESULT_SCHEMA,
        "status": effective_status,
        "environment": "EVALUATION_ONLY",
        "implementation_commit": implementation_commit,
        "implementation_tree": tree,
        "invocation_digest": invocation["document_digest"],
        "prepared_registry_digest": registry["document_digest"],
        "provider_resolved_addresses": list(provider_addresses),
        "selected_provider_address": provider_address,
        "selected_provider_address_scope": _provider_address_scope(
            provider_address
        ),
        "provider_address_is_public": (
            _provider_address_scope(provider_address) == "PUBLIC_UNICAST"
        ),
        "provider_connection_capability": "INHERITED_EXACT_CONNECTED_SOCKET",
        "gateway_listener_capability": (
            "INHERITED_EXACT_BOUND_AF_UNIX_LISTENER"
        ),
        "gateway_new_socket_syscall_capability": "DENIED_BY_SEATBELT",
        "gateway_new_dns_inet_inet6_capability": "DENIED",
        "preflight_digest": preflight["document_digest"],
        "run_count": len(terminals),
        "success_count": success,
        "failure_count": len(terminals) - success,
        "selective_retry_count": 0,
        "terminals": [
            {
                "run_key": item["run_key"],
                "status": item["status"],
                "document_digest": item["document_digest"],
                "timing_document_digest": item.get(
                    "_timing_document_digest"
                ),
            }
            for item in terminals
        ],
        "stage_manifest_before_digest": digest_of(stage_manifest_before).value,
        "stage_manifest_after_digest": digest_of(stage_manifest_after).value,
        "stage_unchanged_after_batch": stage_unchanged,
        "socket_stage_root": str(socket_stage_root),
        "socket_stage_retained": True,
        "completed_at": _utc_now(),
        "production_activation": "NOT_EXECUTED",
    }
    return {**core, "document_digest": digest_of(core).value}


def _selector_for_run(run: Mapping[str, object], prepared_root: Path) -> dict[str, object]:
    registry = _load_json(prepared_root / "prepared-inputs.json")
    selector_name = _text(run.get("selector"), "selector")
    selector = registry.get("selectors", {}).get(selector_name)
    if not isinstance(selector, dict):
        raise RuntimeError("run selector is invalid")
    authority = _authorized_existing_file(selector["authority_database"], prepared_root)
    ordered = _authorized_existing_file(selector["ordered_bundle"], prepared_root)
    snapshots = [
        _authorized_existing_file(item, prepared_root)
        for item in selector["snapshot_bundles"]
    ]
    observed = [_sha256_file(item) for item in snapshots]
    if (
        _sha256_file(ordered) != selector["ordered_bundle_file_digest"]
        or observed != selector["snapshot_bundle_file_digests"]
    ):
        raise RuntimeError("prepared selector Bundle digest drifted")
    return {
        **selector,
        "authority_database": authority,
        "ordered_bundle": ordered,
        "snapshot_bundles": snapshots,
    }


def _load_registry(path: Path, root: Path, implementation_commit: str) -> Mapping[str, object]:
    value = _load_json(path)
    comparison = _load_json(
        _authorized_existing_file(
            str(root / "evaluator" / "baseline-comparison-preflight.json"),
            root,
        )
    )
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if (
        value.get("schema") != "swm.iter-003.g3b-prepared-inputs@1"
        or value.get("implementation_commit") != implementation_commit
        or value.get("document_digest") != digest_of(core).value
        or value.get("run_count") != 60
        or value.get("parity_run_count") != 55
        or value.get("gap_run_count") != 5
        or value.get("product_oracle_paths_mounted") is not False
        or value.get("baseline_result_paths_mounted") is not False
        or value.get("baseline_comparison_preflight_digest")
        != comparison.get("document_digest")
        or comparison.get("product_result_visible_at_seal") is not False
        or not isinstance(value.get("runs"), list)
        or len(value["runs"]) != 60
    ):
        raise RuntimeError("prepared G3b registry is invalid")
    for selector in value.get("selectors", {}).values():
        if isinstance(selector, dict):
            for key in ("authority_database", "ordered_bundle"):
                _authorized_existing_file(selector[key], root)
            for item in selector.get("snapshot_bundles", []):
                _authorized_existing_file(item, root)
    return value


def _load_json(path: Path) -> Mapping[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise ValueError(f"JSON document is not a canonical object: {path}")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON key")
        value[key] = item
    return value


def _require_clean_checkpoint(commit: str) -> str:
    head = _git("rev-parse", "HEAD")
    tree = _git("rev-parse", "HEAD^{tree}")
    status = _git("status", "--porcelain", "--untracked-files=all")
    if head != commit or status:
        raise RuntimeError("G3b requires the exact clean implementation checkpoint")
    return tree


def _git(*arguments: str) -> str:
    completed = subprocess.run(
        ["/usr/bin/git", *arguments],
        cwd=PROJECT_ROOT,
        env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("git checkpoint inspection failed")
    return completed.stdout.strip()


def _provision_provider_socket(
    numeric_address: str | None = None,
) -> tuple[socket.socket, dict[str, object]]:
    """Receive one connected socket from the credential-free supervisor."""

    if numeric_address is not None:
        parsed = ipaddress.ip_address(numeric_address)
        _provider_address_scope(str(parsed))
        if str(parsed) != numeric_address:
            raise ValueError("Provider peer pin must be canonical")
    parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    environment = _provisioner_environment()
    command = [
        str(Path(sys.executable).resolve(strict=True)),
        *SANDBOXED_PYTHON_FLAGS,
        str(PROVIDER_SOCKET_WORKER),
        "--control-fd",
        str(child.fileno()),
        "--timeout-seconds",
        "20",
    ]
    if numeric_address is not None:
        command.extend(("--numeric-address", numeric_address))
    process: subprocess.Popen[bytes] | None = None
    received_descriptors: list[int] = []
    try:
        process = subprocess.Popen(
            command,
            cwd=str(HERE),
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(child.fileno(),),
        )
        child.close()
        parent.settimeout(90.0)
        descriptor_array = array.array("i")
        payload, ancillary, message_flags, _ = parent.recvmsg(
            64 * 1024,
            socket.CMSG_SPACE(descriptor_array.itemsize),
        )
        stdout, stderr = process.communicate(timeout=10.0)
        if message_flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
            raise RuntimeError("Provider descriptor handoff message was truncated")
        for level, kind, data in ancillary:
            if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                usable = len(data) - (len(data) % descriptor_array.itemsize)
                descriptor_array.frombytes(data[:usable])
        received_descriptors.extend(descriptor_array.tolist())
        if (
            process.returncode != 0
            or stdout
            or stderr
            or len(received_descriptors) != 1
            or not payload
        ):
            raise RuntimeError(
                "credential-free Provider socket supervisor failed "
                f"(returncode={process.returncode}, stdout_bytes={len(stdout)}, "
                f"stderr_sha256={sha256(stderr).hexdigest()}, "
                f"stderr_record={stderr.decode('utf-8', errors='replace').strip()}, "
                f"descriptor_count={len(received_descriptors)}, "
                f"payload_bytes={len(payload)})"
            )
        value = json.loads(payload, object_pairs_hook=_unique_object)
        if (
            not isinstance(value, dict)
            or canonical_json_bytes(value) != payload
            or value.get("schema")
            != "swm.iter-003.g3b-provider-socket-provisioning@1"
        ):
            raise RuntimeError("Provider socket supervisor receipt is invalid")
        worker_core = {
            key: item for key, item in value.items() if key != "document_digest"
        }
        selected = value.get("selected_address")
        resolved = value.get("resolved_addresses")
        resolved_scopes = value.get("resolved_address_scopes")
        if (
            value.get("document_digest") != digest_of(worker_core).value
            or value.get("provider_hostname") != "ark.cn-beijing.volces.com"
            or value.get("provider_port") != ARK_PROVIDER_PORT
            or not isinstance(resolved, list)
            or not resolved
            or any(
                not isinstance(item, str)
                or _provider_address_scope(item)
                not in {"PUBLIC_UNICAST", "EXECUTOR_SYNTHETIC_EXTERNAL"}
                for item in resolved
            )
            or resolved_scopes
            != [
                {"address": item, "scope": _provider_address_scope(item)}
                for item in resolved
            ]
            or selected not in resolved
            or value.get("selected_address_scope")
            != _provider_address_scope(selected)
            or value.get("connected_peer_address") != selected
            or value.get("connected_peer_port") != ARK_PROVIDER_PORT
            or value.get("tcp_connect_count") != 1
            or value.get("descriptor_transfer_count") != 1
            or value.get("credential_visible") is not False
            or value.get("product_request_payload_visible") is not False
            or value.get("provider_response_payload_visible") is not False
            or value.get("tls_operation_count") != 0
            or value.get("http_operation_count") != 0
            or value.get("production_activation") != "NOT_EXECUTED"
            or (
                numeric_address is None
                and value.get("dns_operation_count") != 1
            )
            or (
                numeric_address is not None
                and (
                    value.get("dns_operation_count") != 0
                    or resolved != [numeric_address]
                    or selected != numeric_address
                )
            )
        ):
            raise RuntimeError("Provider socket supervisor boundary is invalid")
        connection = socket.socket(fileno=received_descriptors.pop())
        connection.settimeout(20.0)
        peer = connection.getpeername()
        if (
            str(ipaddress.ip_address(peer[0])) != selected
            or peer[1] != ARK_PROVIDER_PORT
        ):
            connection.close()
            raise RuntimeError("received Provider descriptor peer is not exact")
        receipt_core = {
            **worker_core,
            "schema": "swm.iter-003.g3b-provider-socket-handoff@1",
            "worker_receipt_digest": value["document_digest"],
            "worker_script_digest": _sha256_file(PROVIDER_SOCKET_WORKER),
            "worker_environment_keys": sorted(environment),
            "parent_received_descriptor_count": 1,
        }
        return connection, {
            **receipt_core,
            "document_digest": digest_of(receipt_core).value,
        }
    except BaseException:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.communicate(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate(timeout=5.0)
        raise
    finally:
        parent.close()
        child.close()
        for descriptor in received_descriptors:
            os.close(descriptor)


def _provisioner_environment() -> dict[str, str]:
    return {
        "TMPDIR": "/private/tmp",
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }


def _provider_address_scope(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Provider address must be text")
    address = ipaddress.ip_address(value)
    if str(address) != value:
        raise ValueError("Provider address must be canonical")
    if address.is_global:
        return "PUBLIC_UNICAST"
    if address in ipaddress.ip_network("198.18.0.0/15"):
        return "EXECUTOR_SYNTHETIC_EXTERNAL"
    raise ValueError("Provider address is not an accepted external egress peer")


def _required_credential() -> str:
    credential = os.environ.get("ARK_API_KEY")
    if (
        not isinstance(credential, str)
        or not credential
        or "\r" in credential
        or "\n" in credential
    ):
        raise RuntimeError("ARK_API_KEY is required for the authorized G3b batch")
    return credential


def _wait_for_socket(path: Path, process: subprocess.Popen[bytes], *, timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if path.is_socket() and not path.is_symlink():
            return
        if process.poll() is not None:
            raise RuntimeError("Gateway exited before publishing its exact socket")
        time.sleep(0.05)
    raise RuntimeError("Gateway socket startup timed out")


def _finish_gateway(process: subprocess.Popen[bytes], timeout_seconds: float) -> tuple[bytes, bytes]:
    try:
        return process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            return process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.communicate(timeout=5)


def _preserve_process_streams(
    root: Path, label: str, completed: subprocess.CompletedProcess[bytes]
) -> None:
    _preserve_stream_bytes(root, label, completed.stdout, completed.stderr)


def _preserve_stream_bytes(root: Path, label: str, stdout: bytes, stderr: bytes) -> None:
    _write_new(root / f"{label}-stdout.log", stdout)
    _write_new(root / f"{label}-stderr.log", stderr)


def _file_reference(path: Path) -> dict[str, object] | None:
    if not path.is_file() or path.is_symlink():
        return None
    return {
        "path": str(path),
        "digest": _sha256_file(path),
        "size": path.stat().st_size,
    }


def _tree_manifest(root: Path) -> dict[str, object]:
    files: list[dict[str, object]] = []
    directories: list[str] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise RuntimeError(f"symlink in protected G3b tree: {path}")
        if stat.S_ISDIR(metadata.st_mode):
            directories.append(relative)
        elif stat.S_ISREG(metadata.st_mode):
            files.append(
                {"path": relative, "digest": _sha256_file(path), "size": metadata.st_size}
            )
        else:
            raise RuntimeError(f"unsupported entry in protected G3b tree: {path}")
    return {"directories": directories, "files": files}


def _authorized_existing_file(value: object, root: Path) -> Path:
    path = Path(_text(value, "prepared file"))
    if (
        not path.is_absolute()
        or path.resolve(strict=True) != path
        or not path.is_file()
        or path.is_symlink()
        or not _is_within(path, root)
    ):
        raise ValueError("prepared file escapes its exact root")
    return path


def _canonical_directory(value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=True) != path or not path.is_dir() or path.is_symlink():
        raise ValueError(f"{label} must be a canonical directory")
    return path


def _new_directory(value: str, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=False) != path or path.exists():
        raise ValueError(f"{label} must be a new canonical absolute path")
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError(f"{label} parent must be canonical")
    return path


def _write_new(path: Path, payload: bytes) -> None:
    if not path.is_absolute() or path.resolve(strict=False) != path:
        raise ValueError("output path must be canonical and absolute")
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("output parent must be canonical")
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
            raise RuntimeError("output is not a regular file")
    finally:
        os.close(descriptor)


def _encode(value: object) -> str:
    return base64.b64encode(canonical_json_bytes(value)).decode("ascii")


def _sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _commit(value: str) -> str:
    if len(value) != 40 or any(item not in "0123456789abcdef" for item in value):
        raise ValueError("implementation commit must be a full lowercase Git SHA")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _provision_gateway_listener(
    path: Path,
) -> tuple[socket.socket, dict[str, object]]:
    if (
        not path.is_absolute()
        or path.resolve(strict=False) != path
        or path.parent.resolve(strict=True) != path.parent
        or path.exists()
        or path.is_symlink()
    ):
        raise ValueError("Gateway listener path must be new and canonical")
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        listener.bind(str(path))
        path.chmod(0o600)
        listener.listen(1)
        status = path.lstat()
        bound_path = listener.getsockname()
        if isinstance(bound_path, bytes):
            bound_path = bound_path.decode("utf-8")
        if (
            path.is_symlink()
            or not stat.S_ISSOCK(status.st_mode)
            or stat.S_IMODE(status.st_mode) != 0o600
            or bound_path != str(path)
        ):
            raise RuntimeError("trusted evaluator Gateway listener is not exact")
        core = {
            "schema": "swm.iter-003.g3b-gateway-listener-handoff@1",
            "listener_path": str(path),
            "socket_family": "AF_UNIX",
            "socket_type": "SOCK_STREAM",
            "mode": "0600",
            "bound": True,
            "listening": True,
            "socket_creation_owner": "TRUSTED_EVALUATOR",
            "gateway_child_socket_creation": "DENIED_BY_SEATBELT",
            "descriptor_inheritance_count": 1,
            "credential_visible": False,
            "product_request_payload_visible": False,
            "production_activation": "NOT_EXECUTED",
        }
        return listener, {**core, "document_digest": digest_of(core).value}
    except BaseException:
        listener.close()
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


class _UnixListener:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(str(path))
        self.socket.listen(1)
        self.socket.settimeout(30)
        self.thread = threading.Thread(target=self._accept, daemon=True)
        self.thread.start()

    def _accept(self) -> None:
        try:
            connection, _ = self.socket.accept()
            with connection:
                connection.recv(1)
        except OSError:
            pass

    def close(self) -> None:
        self.socket.close()
        self.thread.join(timeout=1)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


class _TCPListener:
    def __init__(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("127.0.0.1", 0))
        self.socket.listen(1)
        self.socket.settimeout(30)
        self.port = self.socket.getsockname()[1]
        self.thread = threading.Thread(target=self._accept, daemon=True)
        self.thread.start()

    def _accept(self) -> None:
        try:
            connection, _ = self.socket.accept()
            connection.close()
        except OSError:
            pass

    def close(self) -> None:
        self.socket.close()
        self.thread.join(timeout=1)


if __name__ == "__main__":
    raise SystemExit(main())
