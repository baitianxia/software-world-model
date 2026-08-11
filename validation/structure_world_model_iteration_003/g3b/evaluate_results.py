#!/usr/bin/env python3
"""Independently evaluate G3b product, isolation, oracle, and baseline results."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import stat
import subprocess
from typing import Iterable, Mapping, Sequence

from software_world_model.cross_cutting import canonical_json_bytes, digest_of


PROJECT_ROOT = Path(__file__).resolve().parents[3]
V009_ROOT = (
    PROJECT_ROOT
    / "var"
    / "iteration-003"
    / "v009"
    / "019f9fced69110c6a7e357a4ea2394ec6742fd2e"
)
BASELINES = V009_ROOT / "baselines"
BASELINE_SEAL = BASELINES / "baseline-seal.json"
PRODUCT_SUITE = (
    PROJECT_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "questions"
    / "product-suite-1.0.0.json"
)
MALL_ORACLE = (
    PROJECT_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "oracles"
    / "mall-structure-1.0.0.json"
)
IDENTITY_ORACLE = (
    PROJECT_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "fixtures"
    / "maven-identity"
    / "oracle.json"
)
BASELINE_SEAL_DIGEST = (
    "sha256:7be049fe746a71cb3b9c3941d81e8e51076256d0f8dac61ba5a5c88c873ecbdd"
)
BASELINE_SEAL_FILE_DIGEST = (
    "sha256:b29c3c228a7f9a55aa6d042e1ca99a4a0a12f6293ab333dda224996cd9f6828a"
)
PROVIDER_HOST = "ark.cn-beijing.volces.com"
PROVIDER_PORT = 443
PROVIDER_POLICY_ENDPOINT = (
    "https://ark.cn-beijing.volces.com:443/api/coding/v3/chat/completions"
)
PROVIDER_TRANSPORT_ENDPOINT = (
    "https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions"
)
GATEWAY_POLICY_REF = "ITER-003-MODEL-EGRESS-GATEWAY@1.0.0"
GATEWAY_POLICY_DIGEST = (
    "sha256:3e0bfcbf6f1b85d350db167d1bc71ff55f35a76546f15d4d7f14a871aa0326e0"
)
PRODUCT_SUITE_DIGEST = (
    "sha256:c165af6beb5ce66d45f035c3155ef4cb7d39b488fb6fe29af4b61e77217aaf2c"
)
MALL_ORACLE_DIGEST = (
    "sha256:412d2e0381ab46cfc84c95e9769f1227733ac2a523487119a15130bcca74b625"
)
IDENTITY_ORACLE_DIGEST = (
    "sha256:b02e4414f2c03fb38da433b343ddeebb8a381a23dad3e0ba3e89792bc468b268"
)
_ALLOWED_POST_PRODUCT_EVALUATOR_DELTA = frozenset(
    {
        "docs/_generated/catalog.json",
        "docs/_generated/dependency-graph.json",
        "docs/_generated/traceability.json",
        (
            "docs/project/iterations/iteration-003/development-design/"
            "SLICE-001-structure-world-model-vertical-closure.md"
        ),
        (
            "docs/project/iterations/iteration-003/findings/"
            "FINDING-003-027.md"
        ),
        (
            "docs/project/iterations/iteration-003/findings/"
            "FINDING-003-028.md"
        ),
        "docs/project/iterations/iteration-003/findings/README.md",
        "docs/project/iterations/iteration-003/verification-matrix.md",
        "tests/test_iteration_003_g3b.py",
        (
            "validation/structure_world_model_iteration_003/g3b/"
            "evaluate_results.py"
        ),
    }
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-root", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--evaluator-implementation-commit", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    prepared_root = _directory(arguments.prepared_root)
    evidence_root = _directory(arguments.evidence_root)
    output = _future_file(arguments.output)
    evaluator_commit = _commit(arguments.evaluator_implementation_commit)
    evaluator_tree = _require_clean_checkpoint(evaluator_commit)
    registry = _load(prepared_root / "prepared-inputs.json")
    batch = _load(evidence_root / "batch-result.json")
    product_commit = _commit(batch.get("implementation_commit"))
    evaluator_delta = _evaluator_delta_paths(product_commit, evaluator_commit)
    invocation = _load(evidence_root / "invocation.json")
    bootstrap = _load(evidence_root / "provider-bootstrap.json")
    preflight = _load(evidence_root / "preflight.json")
    preflight_provisioning = _load(
        evidence_root
        / "preflight"
        / "gateway"
        / "connection-provisioning.json"
    )
    preflight_listener_provisioning = _load(
        evidence_root
        / "preflight"
        / "gateway"
        / "gateway-listener-provisioning.json"
    )
    product_suite = _load_relaxed(PRODUCT_SUITE)
    oracle_digests = _verify_frozen_product_oracles(product_suite)
    mall = _load_relaxed(MALL_ORACLE)
    identity = _load_relaxed(IDENTITY_ORACLE)
    generation = _load(prepared_root / "evaluator" / "generation-report.json")
    comparison_preflight = _load(
        prepared_root / "evaluator" / "baseline-comparison-preflight.json"
    )
    baseline_seal = _load_relaxed(BASELINE_SEAL)
    baseline_product_plan = _load_relaxed(
        BASELINES / "operator" / "product-plan.json"
    )
    baseline_seal_file_digest = _verify_frozen_baseline_seal(baseline_seal)

    evaluation_invocation_path = _future_file(
        str(output.with_name(f"{output.stem}-invocation.json"))
    )
    evaluation_invocation_core = {
        "schema": "swm.iter-003.g3b-evaluation-invocation@1",
        "sealed_at": _utc_now(),
        "evaluator_process_pid": os.getpid(),
        "evaluator_implementation_commit": evaluator_commit,
        "evaluator_implementation_tree": evaluator_tree,
        "evaluator_script_digest": _sha256(Path(__file__).resolve(strict=True)),
        "product_implementation_commit": product_commit,
        "product_implementation_tree": batch.get("implementation_tree"),
        "post_product_evaluator_delta_paths": list(evaluator_delta),
        "batch_result_digest": batch.get("document_digest"),
        "prepared_registry_digest": registry.get("document_digest"),
        "product_suite_and_oracle_file_digests": oracle_digests,
        "baseline_seal_digest": baseline_seal.get("document_digest"),
        "baseline_seal_file_digest": baseline_seal_file_digest,
        "baseline_comparison_preflight_digest": comparison_preflight.get(
            "document_digest"
        ),
        "batch_terminal_index_read_before_seal": True,
        "individual_terminal_files_read_before_seal": False,
        "external_model_called": False,
        "production_activation": "NOT_EXECUTED",
    }
    evaluation_invocation = {
        **evaluation_invocation_core,
        "document_digest": digest_of(evaluation_invocation_core).value,
    }
    _write_new(
        evaluation_invocation_path,
        canonical_json_bytes(evaluation_invocation),
    )

    planned = {item["run_key"]: item for item in registry["runs"]}
    terminals = {
        item["run_key"]: item
        for item in (
            _load(path)
            for path in sorted((evidence_root / "runs").glob("*/terminal.json"))
        )
    }
    if set(terminals) != set(planned) or len(terminals) != 60:
        raise RuntimeError("G3b terminal set differs from the frozen 60-run plan")
    timings = {
        item["run_key"]: item
        for item in (
            _load(path)
            for path in sorted((evidence_root / "runs").glob("*/timing.json"))
        )
    }
    if set(timings) != set(planned) or len(timings) != 60:
        raise RuntimeError("G3b timing receipt set differs from the frozen plan")
    batch_terminals = {
        item["run_key"]: item for item in batch.get("terminals", [])
    }
    direct = _baseline_terminals("direct")
    mature = _baseline_terminals("mature")
    if len(direct) != 55 or len(mature) != 55:
        raise RuntimeError("sealed baseline terminal population drifted")
    expected_comparison_preflight = build_baseline_comparison_preflight(
        product_plan=baseline_product_plan,
        mall=mall,
        identity=identity,
        generation=generation,
    )
    if comparison_preflight != expected_comparison_preflight:
        raise RuntimeError("sealed baseline comparison preflight drifted")
    comparison_by_key = {
        item["run_key"]: item for item in comparison_preflight["runs"]
    }
    socket_stage_root = _validated_socket_stage_root(invocation, batch)

    run_evaluations: list[dict[str, object]] = []
    for run_key in sorted(planned):
        run = planned[run_key]
        terminal = terminals[run_key]
        timing = timings[run_key]
        index = _run_index(evidence_root, run_key)
        run_root = evidence_root / "runs" / index
        terminal_path = run_root / "terminal.json"
        terminal_core = {
            key: item for key, item in terminal.items() if key != "document_digest"
        }
        timing_core = {
            key: item for key, item in timing.items() if key != "document_digest"
        }
        if (
            terminal.get("document_digest") != digest_of(terminal_core).value
            or terminal.get("document_digest")
            != batch_terminals.get(run_key, {}).get("document_digest")
            or timing.get("document_digest") != digest_of(timing_core).value
            or timing.get("terminal_document_digest")
            != terminal.get("document_digest")
            or timing.get("terminal_file_digest") != _sha256(terminal_path)
            or timing.get("document_digest")
            != batch_terminals.get(run_key, {}).get("timing_document_digest")
            or timing.get("request_timing_scope")
            != (
                "ANSWER_REQUEST_DISPATCH_TO_G3B_TERMINAL_PERSISTED_INCLUDING_"
                "GATEWAY_AND_CITATION_PROJECTION"
            )
        ):
            raise RuntimeError(f"G3b timing receipt is not exact: {run_key}")
        evaluation = _evaluate_world_run(
            run=run,
            terminal=terminal,
            timing=timing,
            run_root=run_root,
            expected_gateway_listener_path=(
                str(socket_stage_root / index / "gateway.sock")
                if socket_stage_root is not None
                else None
            ),
            mall=mall,
            identity=identity,
            generation=generation,
        )
        if run["case_id"] != "WM-PRODUCT-008-GAP":
            comparison = comparison_by_key[run_key]
            tokens = comparison["token_checklist"]
            world_text = str(evaluation.get("answer_body", ""))
            world_score = _token_score(world_text, tokens)
            direct_score = comparison["direct_completeness_ppm"]
            mature_score = comparison["mature_completeness_ppm"]
            eligible_scores = [mature_score]
            if direct_score is not None:
                eligible_scores.append(direct_score)
            stronger = max(eligible_scores)
            evaluation["baseline_comparison"] = {
                "token_checklist": tokens,
                "world_model_completeness_ppm": world_score,
                "direct_completeness_ppm": direct_score,
                "direct_output_eligible": comparison["direct_output_eligible"],
                "mature_completeness_ppm": mature_score,
                "stronger_observed_comparator_ppm": stronger,
                "world_model_not_lower": world_score >= stronger,
                "mature_used_for_latency": False,
            }
            if world_score < stronger:
                evaluation["status"] = "FAIL"
                evaluation["findings"].append(
                    "WORLD_MODEL_COMPLETENESS_BELOW_STRONGER_BASELINE"
                )
        run_evaluations.append(evaluation)

    performance = _performance(timings, planned, direct)
    direct_statuses = [item.get("status") for item in direct.values()]
    mature_statuses = [item.get("status") for item in mature.values()]
    all_runs_pass = all(item["status"] == "PASS" for item in run_evaluations)
    boundary_pass = _batch_boundary_pass(
        batch=batch,
        registry=registry,
        invocation=invocation,
        bootstrap=bootstrap,
        preflight=preflight,
        preflight_provisioning=preflight_provisioning,
        preflight_listener_provisioning=preflight_listener_provisioning,
    )
    baseline_population_pass = (
        direct_statuses.count("SUCCESS") == 15
        and sum(item != "SUCCESS" for item in direct_statuses) == 40
        and mature_statuses.count("SUCCESS") == 55
    )
    status = (
        "PASS"
        if all_runs_pass
        and boundary_pass
        and baseline_population_pass
        and performance["status"] == "PASS"
        else "FAIL"
    )
    core = {
        "schema": "swm.iter-003.g3b-product-evaluation@2",
        "status": status,
        "environment": "EVALUATION_ONLY",
        "implementation_commit": batch.get("implementation_commit"),
        "product_implementation_commit": product_commit,
        "evaluator_implementation_commit": evaluator_commit,
        "evaluator_implementation_tree": evaluator_tree,
        "evaluator_script_digest": evaluation_invocation[
            "evaluator_script_digest"
        ],
        "evaluation_invocation_digest": evaluation_invocation[
            "document_digest"
        ],
        "post_product_evaluator_delta_paths": list(evaluator_delta),
        "batch_result_digest": batch.get("document_digest"),
        "prepared_registry_digest": registry.get("document_digest"),
        "baseline_seal_digest": baseline_seal["document_digest"],
        "baseline_seal_file_digest": baseline_seal_file_digest,
        "baseline_comparison_preflight_digest": comparison_preflight[
            "document_digest"
        ],
        "run_count": len(run_evaluations),
        "run_pass_count": sum(item["status"] == "PASS" for item in run_evaluations),
        "major_error_count": sum(bool(item["findings"]) for item in run_evaluations),
        "batch_and_preflight_boundary_pass": boundary_pass,
        "direct_population": {
            "terminal_count": len(direct),
            "success_count": direct_statuses.count("SUCCESS"),
            "failure_count": direct_statuses.count("FAILURE"),
            "failures_preserved": True,
            "missing_outputs_interpolated": False,
        },
        "mature_population": {
            "terminal_count": len(mature),
            "success_count": mature_statuses.count("SUCCESS"),
            "failure_count": mature_statuses.count("FAILURE"),
            "latency_comparator": False,
        },
        "performance": performance,
        "runs": run_evaluations,
        "product_oracle_visibility": "EVALUATOR_ONLY_AFTER_PRODUCT_TERMINAL",
        "product_oracle_read_count_in_answer": 0,
        "baseline_result_read_count_in_answer": 0,
        "selective_retry_count": 0,
        "production_activation": "NOT_EXECUTED",
    }
    result = {**core, "document_digest": digest_of(core).value}
    _write_new(output, canonical_json_bytes(result))
    print(canonical_json_bytes(result).decode("utf-8"))
    return 0 if status == "PASS" else 2


def _evaluate_world_run(
    *,
    run: Mapping[str, object],
    terminal: Mapping[str, object],
    timing: Mapping[str, object],
    run_root: Path,
    expected_gateway_listener_path: str | None,
    mall: Mapping[str, object],
    identity: Mapping[str, object],
    generation: Mapping[str, object],
) -> dict[str, object]:
    findings: list[str] = []
    if terminal.get("status") != "SUCCESS":
        return {
            "run_key": run["run_key"],
            "case_id": run["case_id"],
            "status": "FAIL",
            "terminal_status": terminal.get("status"),
            "findings": ["PRODUCT_TERMINAL_NOT_SUCCESS"],
            "answer_body": None,
        }
    summary = _load(
        _verified_reference(
            terminal.get("answer_summary"), run_root, "Answer summary"
        )
    )
    gateway_summary = _load(
        _verified_reference(
            terminal.get("gateway_summary"), run_root, "Gateway summary"
        )
    )
    gateway_listener_provisioning = _load(
        _verified_reference(
            terminal.get("gateway_listener_provisioning"),
            run_root,
            "Gateway listener provisioning",
        )
    )
    server_audits = _load_json_lines(
        _existing_descendant_file(
            run_root / "gateway-output" / "server-audit.jsonl", run_root
        )
    )
    transport_audits = _load_json_lines(
        _existing_descendant_file(
            run_root / "gateway-output" / "transport-audit.jsonl", run_root
        )
    )
    envelope = _load(
        _existing_descendant_file(
            run_root / "answer-output" / "evaluation.html", run_root
        )
    )
    page = envelope.get("page")
    if (
        envelope.get("page_digest") != summary.get("page_digest")
        or envelope.get("page_digest")
        != digest_of(
            ["WORLD_MODEL_EVALUATION_PAGE_PAYLOAD@1", page]
        ).value
        or not isinstance(page, dict)
        or page.get("evaluation_only") is not True
        or page.get("environment") != "EVALUATION_ONLY"
        or page.get("mode") != "WORLD_MODEL"
        or page.get("execution_boundary", {}).get("provider_call_count") != 1
        or page.get("execution_boundary", {}).get("network_operation_count") != 1
        or page.get("execution_boundary", {}).get("source_access_allowed") is not False
        or page.get("execution_boundary", {}).get("evidence_payload_access_allowed") is not False
        or len(page.get("authority_chain", {}).get("stages", [])) != 10
        or page.get("review", {}).get("decision") != "APPROVE"
        or page.get("delivery", {}).get("state") != "DELIVERED"
        or summary.get("provider_call_count") != 1
        or summary.get("source_access_count") != 0
        or summary.get("evidence_payload_access_count") != 0
        or summary.get("product_oracle_read_count") != 0
        or summary.get("baseline_result_read_count") != 0
        or gateway_summary.get("status") != "PASS"
        or gateway_summary.get("provider_call_count") != 1
        or gateway_summary.get("https_dispatch_count") != 1
        or gateway_summary.get("dns_operation_count_in_dispatch_process") != 0
        or gateway_summary.get("credential_value_recorded") is not False
        or gateway_summary.get("provider_connection_capability")
        != "INHERITED_EXACT_CONNECTED_SOCKET"
        or gateway_summary.get("gateway_listener_capability")
        != "INHERITED_EXACT_BOUND_AF_UNIX_LISTENER"
        or gateway_summary.get("new_socket_syscall_capability")
        != "DENIED_BY_SEATBELT"
        or terminal.get("provider_connection_handoff_count") != 1
        or terminal.get("gateway_listener_handoff_count") != 1
        or not _gateway_listener_provisioning_pass(
            gateway_listener_provisioning,
            expected_path=expected_gateway_listener_path,
        )
        or gateway_summary.get("numeric_provider_address_scope")
        not in {"PUBLIC_UNICAST", "EXECUTOR_SYNTHETIC_EXTERNAL"}
        or len(server_audits) != 1
        or server_audits[0].get("status") != "RESULT"
        or server_audits[0].get("policy_ref") != GATEWAY_POLICY_REF
        or server_audits[0].get("policy_digest") != GATEWAY_POLICY_DIGEST
        or len(transport_audits) != 1
        or not _transport_audit_pass(
            transport_audits[0],
            gateway_summary=gateway_summary,
        )
    ):
        findings.append("AUTHORITY_OR_EXECUTION_BOUNDARY_INVALID")
    role_answer = _load(
        _verified_reference(
            terminal.get("answer_role_report"), run_root, "Answer role report"
        )
    )
    role_gateway = _load(
        _verified_reference(
            terminal.get("gateway_role_report"), run_root, "Gateway role report"
        )
    )
    if not _role_report_pass(role_answer) or not _role_report_pass(role_gateway):
        findings.append("NORMAL_WORKLOAD_OPERATION_AUDIT_FAILED")
    if terminal.get("citation_projection_count") != len(terminal.get("citation_projections", [])):
        findings.append("CITATION_PROJECTION_COUNT_MISMATCH")
    for projection in terminal.get("citation_projections", []):
        value = _load(
            _verified_reference(
                projection.get("projection"), run_root, "Citation projection"
            )
        )
        role = _load(
            _verified_reference(
                projection.get("role_report"), run_root, "Projector role report"
            )
        )
        materialization = _load(
            _verified_reference(
                projection.get("materialization"),
                run_root,
                "Citation materialization",
            )
        )
        if (
            value.get("status") != "PASS"
            or value.get("result_id") != projection.get("result_id")
            or value.get("seal_digest") != projection.get("seal_digest")
            or value.get("network_operation_count") != 0
            or value.get("answer_return_port") is not False
            or materialization.get("status") != "PASS"
            or materialization.get("result_id") != projection.get("result_id")
            or materialization.get("seal_digest") != projection.get("seal_digest")
            or materialization.get("store_manifest_digest")
            != projection.get("store_manifest_digest")
            or not _role_report_pass(role)
        ):
            findings.append("CITATION_PROJECTOR_BOUNDARY_INVALID")
            break
    provisioning = _load(
        _existing_descendant_file(
            run_root / "evaluator" / "connection-provisioning.json",
            run_root,
        )
    )
    if (
        not _provider_provisioning_pass(provisioning)
        or provisioning.get("selected_address")
        != gateway_summary.get("numeric_provider_address")
        or provisioning.get("selected_address_scope")
        != gateway_summary.get("numeric_provider_address_scope")
    ):
        findings.append("PROVIDER_SOCKET_PROVISIONING_BOUNDARY_INVALID")
    if isinstance(page, dict):
        findings.extend(
            _oracle_findings(
                case_id=str(run["case_id"]),
                page=page,
                mall=mall,
                identity=identity,
                generation=generation,
            )
        )
    answer_body = page.get("answer", {}).get("body") if isinstance(page, dict) else None
    return {
        "run_key": run["run_key"],
        "case_id": run["case_id"],
        "status": "PASS" if not findings else "FAIL",
        "terminal_status": terminal["status"],
        "findings": findings,
        "page_digest": envelope.get("page_digest"),
        "chain_digest": summary.get("chain_digest"),
        "model_capability": summary.get("model_capability"),
        "citation_projection_count": terminal.get("citation_projection_count"),
        "request_elapsed_milliseconds": timing.get(
            "request_elapsed_milliseconds"
        ),
        "cold_process_elapsed_milliseconds": timing.get(
            "cold_process_elapsed_milliseconds"
        ),
        "answer_body": answer_body,
    }


def _batch_boundary_pass(
    *,
    batch: Mapping[str, object],
    registry: Mapping[str, object],
    invocation: Mapping[str, object],
    bootstrap: Mapping[str, object],
    preflight: Mapping[str, object],
    preflight_provisioning: Mapping[str, object],
    preflight_listener_provisioning: Mapping[str, object],
) -> bool:
    batch_core = {
        key: item for key, item in batch.items() if key != "document_digest"
    }
    registry_core = {
        key: item for key, item in registry.items() if key != "document_digest"
    }
    invocation_core = {
        key: item for key, item in invocation.items() if key != "document_digest"
    }
    preflight_core = {
        key: item for key, item in preflight.items() if key != "document_digest"
    }
    scope = batch.get("selected_provider_address_scope")
    terminals = batch.get("terminals")
    socket_stage_root = _validated_socket_stage_root(invocation, batch)
    return (
        batch.get("document_digest") == digest_of(batch_core).value
        and registry.get("document_digest") == digest_of(registry_core).value
        and batch.get("status") == "PASS"
        and batch.get("environment") == "EVALUATION_ONLY"
        and batch.get("run_count") == 60
        and batch.get("success_count") == 60
        and batch.get("failure_count") == 0
        and batch.get("selective_retry_count") == 0
        and batch.get("prepared_registry_digest")
        == registry.get("document_digest")
        and registry.get("product_suite_sha256") == PRODUCT_SUITE_DIGEST
        and batch.get("implementation_commit")
        == registry.get("implementation_commit")
        and batch.get("stage_unchanged_after_batch") is True
        and batch.get("gateway_new_dns_inet_inet6_capability") == "DENIED"
        and batch.get("provider_connection_capability")
        == "INHERITED_EXACT_CONNECTED_SOCKET"
        and batch.get("gateway_listener_capability")
        == "INHERITED_EXACT_BOUND_AF_UNIX_LISTENER"
        and batch.get("gateway_new_socket_syscall_capability")
        == "DENIED_BY_SEATBELT"
        and scope in {"PUBLIC_UNICAST", "EXECUTOR_SYNTHETIC_EXTERNAL"}
        and batch.get("provider_address_is_public")
        is (scope == "PUBLIC_UNICAST")
        and isinstance(terminals, list)
        and len(terminals) == 60
        and all(
            isinstance(item, dict)
            and item.get("status") == "SUCCESS"
            and isinstance(item.get("timing_document_digest"), str)
            for item in terminals
        )
        and invocation.get("document_digest") == digest_of(invocation_core).value
        and batch.get("invocation_digest") == invocation.get("document_digest")
        and invocation.get("run_count") == 60
        and invocation.get("environment") == "EVALUATION_ONLY"
        and invocation.get("production_activation") == "NOT_EXECUTED"
        and invocation.get("provider", {}).get("connection_handoff")
        == "INHERITED_EXACT_CONNECTED_SOCKET"
        and invocation.get("provider", {}).get("endpoint")
        == PROVIDER_POLICY_ENDPOINT
        and invocation.get("provider", {}).get("gateway_listener_handoff")
        == "INHERITED_EXACT_BOUND_AF_UNIX_LISTENER"
        and invocation.get("provider", {}).get("gateway_child_socket_creation")
        == "DENIED_BY_SEATBELT"
        and socket_stage_root is not None
        and _provider_provisioning_pass(bootstrap)
        and bootstrap.get("worker_script_digest")
        == invocation.get("provider_socket_worker_digest")
        and bootstrap.get("selected_address")
        == batch.get("selected_provider_address")
        and bootstrap.get("selected_address_scope") == scope
        and _provider_provisioning_pass(preflight_provisioning)
        and preflight_provisioning.get("worker_script_digest")
        == invocation.get("provider_socket_worker_digest")
        and preflight_provisioning.get("selected_address")
        == batch.get("selected_provider_address")
        and _gateway_listener_provisioning_pass(
            preflight_listener_provisioning,
            expected_path=str(
                socket_stage_root / "probe-2" / "gateway.sock"
            ),
        )
        and preflight.get("roles", {}).get("gateway", {}).get(
            "gateway_listener_provisioning"
        )
        == preflight_listener_provisioning
        and preflight.get("document_digest") == digest_of(preflight_core).value
        and batch.get("preflight_digest") == preflight.get("document_digest")
        and _preflight_pass(
            preflight,
            expected_gateway_listener_path=str(
                socket_stage_root / "probe-2" / "gateway.sock"
            ),
        )
        and all(
            preflight.get("roles", {}).get(role, {}).get("profile_digest")
            == invocation.get("profiles", {}).get(role)
            for role in ("answer", "gateway", "projector")
        )
        and batch.get("production_activation") == "NOT_EXECUTED"
    )


def _provider_provisioning_pass(value: Mapping[str, object]) -> bool:
    core = {key: item for key, item in value.items() if key != "document_digest"}
    selected = value.get("selected_address")
    scope = value.get("selected_address_scope")
    scopes = value.get("resolved_address_scopes")
    environment_keys = value.get("worker_environment_keys")
    return (
        value.get("schema") == "swm.iter-003.g3b-provider-socket-handoff@1"
        and value.get("document_digest") == digest_of(core).value
        and isinstance(selected, str)
        and value.get("provider_hostname") == PROVIDER_HOST
        and value.get("provider_port") == PROVIDER_PORT
        and value.get("connected_peer_address") == selected
        and value.get("connected_peer_port") == PROVIDER_PORT
        and scope in {"PUBLIC_UNICAST", "EXECUTOR_SYNTHETIC_EXTERNAL"}
        and isinstance(scopes, list)
        and {item.get("address") for item in scopes if isinstance(item, dict)}
        == set(value.get("resolved_addresses", []))
        and any(
            isinstance(item, dict)
            and item.get("address") == selected
            and item.get("scope") == scope
            for item in scopes
        )
        and value.get("tcp_connect_count") == 1
        and value.get("descriptor_transfer_count") == 1
        and value.get("parent_received_descriptor_count") == 1
        and value.get("credential_visible") is False
        and value.get("product_request_payload_visible") is False
        and value.get("provider_response_payload_visible") is False
        and value.get("tls_operation_count") == 0
        and value.get("http_operation_count") == 0
        and isinstance(environment_keys, list)
        and "ARK_API_KEY" not in environment_keys
        and value.get("production_activation") == "NOT_EXECUTED"
    )


def _transport_audit_pass(
    value: Mapping[str, object],
    *,
    gateway_summary: Mapping[str, object],
) -> bool:
    return (
        value.get("outcome") == "HTTP_RESPONSE"
        and value.get("failure_code") is None
        and value.get("endpoint") == PROVIDER_TRANSPORT_ENDPOINT
        and value.get("numeric_address")
        == gateway_summary.get("numeric_provider_address")
        and value.get("address_scope")
        == gateway_summary.get("numeric_provider_address_scope")
        and isinstance(value.get("peer_certificate_sha256"), str)
        and gateway_summary.get("policy_ref") == GATEWAY_POLICY_REF
        and gateway_summary.get("policy_digest") == GATEWAY_POLICY_DIGEST
    )


def _gateway_listener_provisioning_pass(
    value: Mapping[str, object],
    *,
    expected_path: str | None = None,
) -> bool:
    core = {key: item for key, item in value.items() if key != "document_digest"}
    listener_path = value.get("listener_path")
    return (
        value.get("schema")
        == "swm.iter-003.g3b-gateway-listener-handoff@1"
        and value.get("document_digest") == digest_of(core).value
        and isinstance(listener_path, str)
        and listener_path.startswith("/private/")
        and listener_path.endswith("/gateway.sock")
        and (expected_path is None or listener_path == expected_path)
        and value.get("socket_family") == "AF_UNIX"
        and value.get("socket_type") == "SOCK_STREAM"
        and value.get("mode") == "0600"
        and value.get("bound") is True
        and value.get("listening") is True
        and value.get("socket_creation_owner") == "TRUSTED_EVALUATOR"
        and value.get("gateway_child_socket_creation")
        == "DENIED_BY_SEATBELT"
        and value.get("descriptor_inheritance_count") == 1
        and value.get("credential_visible") is False
        and value.get("product_request_payload_visible") is False
        and value.get("production_activation") == "NOT_EXECUTED"
    )


def _preflight_pass(
    value: Mapping[str, object],
    *,
    expected_gateway_listener_path: str,
) -> bool:
    roles = value.get("roles")
    if (
        value.get("status") != "PASS"
        or value.get("os_enforcement") != "MACOS_SEATBELT_DENY_DEFAULT"
        or value.get("protected_stage_unchanged") is not True
        or value.get("protected_stage_manifest_before")
        != value.get("protected_stage_manifest_after")
        or value.get("gateway_external_capability")
        != (
            "INHERITED_EXACT_PROVIDER_AND_AF_UNIX_LISTENER_FDS; "
            "NEW_SOCKET_SYSCALL_DENIED"
        )
        or not isinstance(roles, dict)
        or set(roles) != {"answer", "gateway", "projector"}
    ):
        return False
    required = {
        "answer": {
            "allowed_exact_gateway_connect",
            "denied_other_unix_connect",
            "denied_provider_inet_connect",
            "denied_local_inet_connect",
            "denied_dns_resolution",
            "denied_process_fork",
            "credential_role_boundary",
        },
        "gateway": {
            "inherited_provider_descriptor_is_already_connected",
            "allowed_inherited_exact_gateway_listener_round_trip",
            "allowed_inherited_exact_provider_tls",
            "denied_new_inet_socket_creation",
            "denied_new_unix_socket_creation",
            "denied_new_provider_connect",
            "denied_other_unix_connect",
            "denied_local_inet_connect",
            "denied_dns_resolution",
            "denied_process_fork",
            "credential_role_boundary",
        },
        "projector": {
            "denied_gateway_unix_connect",
            "denied_other_unix_connect",
            "denied_provider_inet_connect",
            "denied_local_inet_connect",
            "denied_dns_resolution",
            "denied_process_fork",
            "credential_role_boundary",
        },
    }
    for role, expected in required.items():
        record = roles.get(role)
        if not isinstance(record, dict) or record.get("status") != "PASS":
            return False
        if role == "gateway" and (
            record.get("gateway_listener_round_trip") is not True
            or not isinstance(record.get("gateway_listener_provisioning"), dict)
            or not _gateway_listener_provisioning_pass(
                record["gateway_listener_provisioning"],
                expected_path=expected_gateway_listener_path,
            )
        ):
            return False
        probe = record.get("probe")
        probes = probe.get("probes") if isinstance(probe, dict) else None
        if (
            not isinstance(probe, dict)
            or probe.get("role") != role
            or probe.get("status") != "PASS"
            or probe.get("credential_value_recorded") is not False
            or not isinstance(probes, list)
            or any(
                not isinstance(item, dict) or item.get("status") != "PASS"
                for item in probes
            )
            or not expected.issubset(
                {
                    item.get("name")
                    for item in probes
                    if isinstance(item, dict)
                }
            )
            or not any(
                isinstance(item, dict)
                and str(item.get("name", "")).startswith("denied_file:")
                for item in probes
            )
        ):
            return False
    return True


def _validated_socket_stage_root(
    invocation: Mapping[str, object],
    batch: Mapping[str, object],
) -> Path | None:
    value = invocation.get("socket_stage_root")
    if (
        not isinstance(value, str)
        or not value.startswith("/private/")
        or os.path.normpath(value) != value
        or batch.get("socket_stage_root") != value
        or batch.get("socket_stage_retained") is not True
    ):
        return None
    return Path(value)


def _oracle_findings(
    *,
    case_id: str,
    page: Mapping[str, object],
    mall: Mapping[str, object],
    identity: Mapping[str, object],
    generation: Mapping[str, object],
) -> list[str]:
    findings: list[str] = []
    views = page.get("views", {}).get("query_result_views", [])
    if not isinstance(views, list):
        return ["QUERY_RESULT_VIEWS_INVALID"]
    payloads = [item.get("view", {}).get("result_payload", {}) for item in views]
    view_values = [item.get("view", {}) for item in views]
    if case_id != "WM-PRODUCT-008-GAP" and any(
        item.get("completeness") != "COMPLETE" or item.get("truncated") is not False
        for item in view_values
    ):
        findings.append("SUPPORTED_VIEW_NOT_COMPLETE")
    if case_id == "WM-PRODUCT-001":
        inventories = [item for item in payloads if "modules" in item]
        observed = [
            sorted(value["canonical_ga"].split(":", 1)[1] for value in item["modules"])
            for item in inventories
        ]
        expected = [
            sorted(mall["revision_a_oracle"]["reactor_child_modules"]),
            sorted(mall["revision_b_oracle"]["reactor_child_modules"]),
        ]
        if observed != expected:
            findings.append("MALL_INVENTORY_ORACLE_MISMATCH")
    elif case_id == "WM-PRODUCT-002":
        paths = [item for item in payloads if "paths" in item]
        if [item.get("path_count") for item in paths] != [1, 2]:
            findings.append("MALL_PATH_ORACLE_MISMATCH")
        body = str(page.get("answer", {}).get("body", ""))
        if "mall-admin" not in body or "mall-security" not in body or "mall-common" not in body:
            findings.append("MALL_NEW_PATH_NOT_DELIVERED")
    elif case_id == "WM-PRODUCT-003":
        diff = next((item for item in payloads if "entities" in item and "relations" in item), None)
        if (
            not isinstance(diff, dict)
            or diff["entities"]["counts"]
            != {"added": 1, "removed": 0, "state_changed": 7, "unchanged": 0}
            or diff["relations"]["counts"]
            != {"added": 3, "removed": 0, "state_changed": 11, "unchanged": 0}
        ):
            findings.append("MALL_ORDERED_DIFF_ORACLE_MISMATCH")
    elif case_id == "WM-PRODUCT-004":
        body = str(page.get("answer", {}).get("body", ""))
        if '"com.macro.mall:mall-security":false' not in body or '"dependency_management_forms_edge":false' not in body:
            findings.append("MALL_ROOT_DIRECT_DEPENDENCY_ORACLE_MISMATCH")
    elif case_id == "WM-PRODUCT-005":
        path = next((item for item in payloads if "path_count" in item), None)
        if not isinstance(path, dict) or path.get("path_count") != 0 or path.get("negative_conclusion_supported") is not True:
            findings.append("MALL_NEGATIVE_PATH_ORACLE_MISMATCH")
    elif case_id == "WM-PRODUCT-006":
        body = str(page.get("answer", {}).get("body", ""))
        expected = identity["valid"]["billing_common_lib_answer"]
        for token in (
            expected["source_ga"],
            expected["actual_target_ga"],
            expected["other_same_artifact_ga"],
            '"org.example.shared:common-lib":true',
            '"org.example.legacy:common-lib":false',
        ):
            if token not in body:
                findings.append("IDENTITY_BILLING_ORACLE_MISMATCH")
                break
    elif case_id == "WM-PRODUCT-007":
        body = str(page.get("answer", {}).get("body", ""))
        if '"org.example.shared:common-lib":true' not in body or '"dependency_management_forms_edge":false' not in body:
            findings.append("IDENTITY_ROOT_ORACLE_MISMATCH")
    elif case_id == "WM-PRODUCT-008-GAP":
        needs = page.get("assessment", {}).get("needs", [])
        if (
            views
            or len(needs) != 1
            or needs[0].get("outcome") != "KNOWLEDGE_GAP"
            or needs[0].get("gap_code") != "CHANGE_INTENT_OUTSIDE_STRUCTURE_COVERAGE"
            or "Knowledge Gap" not in str(page.get("answer", {}).get("body", ""))
        ):
            findings.append("CHANGE_INTENT_GAP_ORACLE_MISMATCH")
    elif case_id.startswith("WM-META-"):
        body = str(page.get("answer", {}).get("body", ""))
        for token in _quality_tokens(case_id, mall, identity, generation):
            if token not in body:
                findings.append("METAMORPHIC_ORACLE_MISMATCH")
                break
    else:
        findings.append("UNKNOWN_PRODUCT_CASE")
    return findings


def _quality_tokens(
    case_id: str,
    mall: Mapping[str, object],
    identity: Mapping[str, object],
    generation: Mapping[str, object],
) -> list[str]:
    if case_id == "WM-PRODUCT-001":
        modules = {
            *mall["revision_a_oracle"]["reactor_child_modules"],
            *mall["revision_b_oracle"]["reactor_child_modules"],
        }
        return sorted(f"com.macro.mall:{item}" for item in modules)
    if case_id == "WM-PRODUCT-002":
        return ["mall-admin", "mall-mbg", "mall-security", "mall-common", "[[ADDED]]"]
    if case_id == "WM-PRODUCT-003":
        return ["mall-security", "mall-admin", "mall-common", "CONTAINS_MODULE", "DEPENDS_ON"]
    if case_id == "WM-PRODUCT-004":
        return ["mall-security", "[[NEGATIVE]]", "[[DEPENDENCY_MANAGEMENT]]"]
    if case_id == "WM-PRODUCT-005":
        return ["mall-admin", "mall-search", "[[NEGATIVE]]"]
    if case_id == "WM-PRODUCT-006":
        expected = identity["valid"]["billing_common_lib_answer"]
        return [
            expected["source_ga"],
            expected["actual_target_ga"],
            expected["other_same_artifact_ga"],
            "[[NEGATIVE]]",
        ]
    if case_id == "WM-PRODUCT-007":
        return [
            "org.example.root:structure-fixture",
            "org.example.shared:common-lib",
            "[[NEGATIVE]]",
        ]
    if case_id == "WM-META-001":
        return sorted(
            {
                *(item["ga"] for item in generation["revision_a_oracle"]["nodes"]),
                *(item["ga"] for item in generation["revision_b_oracle"]["nodes"]),
            }
        )
    if case_id == "WM-META-002":
        return sorted(
            {
                *(
                    ga
                    for path in generation["revision_a_oracle"]["all_simple_paths"]
                    for ga in path
                ),
                *(
                    ga
                    for path in generation["revision_b_oracle"]["all_simple_paths"]
                    for ga in path
                ),
            }
        )
    if case_id == "WM-META-003":
        return sorted(
            {
                *generation["identity_state_counterexamples"].values(),
                *generation["a_to_b"]["added_nodes"],
            }
        )
    if case_id == "WM-META-004":
        return list(generation["question_selectors"]["same_artifact_distinct_ga"])
    raise RuntimeError(f"quality checklist is undefined for {case_id}")


def build_baseline_comparison_preflight(
    *,
    product_plan: Mapping[str, object],
    mall: Mapping[str, object],
    identity: Mapping[str, object],
    generation: Mapping[str, object],
) -> dict[str, object]:
    """Seal exact per-run quality comparators before any product result exists."""

    runs = product_plan.get("runs")
    if not isinstance(runs, list) or len(runs) != 55:
        raise RuntimeError("baseline comparison plan must contain exactly 55 runs")
    direct = _baseline_terminals("direct")
    mature = _baseline_terminals("mature")
    rows: list[dict[str, object]] = []
    for run in runs:
        if not isinstance(run, dict):
            raise RuntimeError("baseline comparison run is invalid")
        run_key = str(run.get("run_key"))
        case_id = str(run.get("case_id"))
        if run_key not in direct or run_key not in mature:
            raise RuntimeError(f"baseline comparison terminal missing: {run_key}")
        tokens = _quality_tokens(case_id, mall, identity, generation)
        direct_text = _baseline_answer("direct", run_key, direct[run_key])
        mature_text = _baseline_answer("mature", run_key, mature[run_key])
        if mature_text is None:
            raise RuntimeError(f"Mature baseline output missing: {run_key}")
        direct_score = (
            _token_score(direct_text, tokens) if direct_text is not None else None
        )
        rows.append(
            {
                "run_key": run_key,
                "case_id": case_id,
                "token_checklist": tokens,
                "mature_completeness_ppm": _token_score(mature_text, tokens),
                "direct_completeness_ppm": direct_score,
                "direct_output_eligible": direct_text is not None,
            }
        )
    direct_statuses = [item.get("status") for item in direct.values()]
    mature_statuses = [item.get("status") for item in mature.values()]
    core = {
        "schema": "swm.iter-003.g3b-baseline-comparison-preflight@1",
        "status": "PASS",
        "baseline_seal_digest": BASELINE_SEAL_DIGEST,
        "method": (
            "case-specific frozen token checklist; Unicode casefold substring "
            "presence; equal token weight; integer parts-per-million score"
        ),
        "run_count": len(rows),
        "direct_terminal_count": len(direct),
        "direct_success_count": direct_statuses.count("SUCCESS"),
        "direct_failure_count": sum(item != "SUCCESS" for item in direct_statuses),
        "mature_terminal_count": len(mature),
        "mature_success_count": mature_statuses.count("SUCCESS"),
        "mature_failure_count": sum(item != "SUCCESS" for item in mature_statuses),
        "failures_preserved": True,
        "missing_outputs_interpolated": False,
        "runs": rows,
        "product_result_visible_at_seal": False,
        "production_activation": "NOT_EXECUTED",
    }
    if (
        len(direct) != 55
        or direct_statuses.count("SUCCESS") != 15
        or sum(item != "SUCCESS" for item in direct_statuses) != 40
        or len(mature) != 55
        or mature_statuses.count("SUCCESS") != 55
        or any(item != "SUCCESS" for item in mature_statuses)
    ):
        raise RuntimeError("sealed baseline population is not exact")
    return {**core, "document_digest": digest_of(core).value}


def _performance(
    terminals: Mapping[str, Mapping[str, object]],
    plan: Mapping[str, Mapping[str, object]],
    direct: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    parity_keys = sorted(
        key for key, run in plan.items() if run["case_id"] != "WM-PRODUCT-008-GAP"
    )
    first = [key for key in parity_keys if plan[key]["run_number"] == 1]
    repeated = [key for key in parity_keys if plan[key]["run_number"] > 1]
    world_first = _numeric_values(terminals, first, "request_elapsed_milliseconds")
    world_repeated = _numeric_values(terminals, repeated, "request_elapsed_milliseconds")
    world_all = _numeric_values(terminals, parity_keys, "request_elapsed_milliseconds")
    world_cold = _numeric_values(terminals, parity_keys, "cold_process_elapsed_milliseconds")
    direct_first = _numeric_values(direct, first, "executor_elapsed_milliseconds")
    direct_repeated = _numeric_values(direct, repeated, "executor_elapsed_milliseconds")
    direct_all = _numeric_values(direct, parity_keys, "executor_elapsed_milliseconds")
    direct_success_keys = [key for key in parity_keys if direct[key].get("status") == "SUCCESS"]
    direct_success = _numeric_values(direct, direct_success_keys, "executor_elapsed_milliseconds")
    populations_complete = all(
        (
            len(world_first) == len(first),
            len(world_repeated) == len(repeated),
            len(direct_first) == len(first),
            len(direct_repeated) == len(repeated),
        )
    )
    world_first_p95 = _p95(world_first)
    world_repeated_p95 = _p95(world_repeated)
    direct_first_p95 = _p95(direct_first)
    direct_repeated_p95 = _p95(direct_repeated)
    first_ratio_ppm = (
        round(world_first_p95 * 1_000_000 / direct_first_p95)
        if populations_complete
        and world_first_p95 is not None
        and direct_first_p95 not in {None, 0}
        else None
    )
    repeated_ratio_ppm = (
        round(world_repeated_p95 * 1_000_000 / direct_repeated_p95)
        if populations_complete
        and world_repeated_p95 is not None
        and direct_repeated_p95 not in {None, 0}
        else None
    )
    status = (
        "PASS"
        if first_ratio_ppm is not None
        and repeated_ratio_ppm is not None
        and first_ratio_ppm <= 1_500_000
        and repeated_ratio_ppm <= 500_000
        else "FAIL"
    )
    return {
        "status": status,
        "method": "linear inclusive P95 over frozen terminal populations",
        "world_model_all_terminal": _population(world_all),
        "world_model_cold_process": _population(world_cold),
        "world_model_first_request": _population(world_first),
        "world_model_repeated_request": _population(world_repeated),
        "direct_all_terminal": _population(direct_all),
        "direct_eligible_success": _population(direct_success),
        "direct_first_request": _population(direct_first),
        "direct_repeated_request": _population(direct_repeated),
        "direct_provider_failure_count": sum(direct[key].get("status") != "SUCCESS" for key in parity_keys),
        "first_request_ratio_ppm": first_ratio_ppm,
        "first_request_limit_ppm": 1_500_000,
        "repeated_request_ratio_ppm": repeated_ratio_ppm,
        "repeated_request_limit_ppm": 500_000,
        "failures_filtered": False,
        "mature_cross_model_latency_compared": False,
    }


def _baseline_terminals(kind: str) -> dict[str, Mapping[str, object]]:
    return {
        value["run_key"]: value
        for value in (
            _load_relaxed(path)
            for path in (BASELINES / kind / "runs").glob("*/terminal.json")
        )
    }


def _baseline_answer(
    kind: str,
    run_key: str,
    terminal: Mapping[str, object],
) -> str | None:
    if terminal.get("status") != "SUCCESS":
        return None
    root = BASELINES / kind / "runs" / run_key
    path = root / ("result.json" if kind == "direct" else "answer.json")
    value = _load_relaxed(path)
    if kind == "direct":
        result = value.get("result", {})
        for key in ("answer", "body", "response"):
            text = result.get(key) if isinstance(result, dict) else None
            if isinstance(text, str):
                return text
        return json.dumps(result, ensure_ascii=False, sort_keys=True)
    answer = value.get("answer", {})
    return answer.get("answer") if isinstance(answer, dict) else None


def _token_score(text: str, tokens: Sequence[str]) -> int:
    if not tokens:
        return 1_000_000
    folded = text.casefold()
    alternatives = {
        "[[NEGATIVE]]": ("false", "不存在", "没有", "不形成", "不算", "否"),
        "[[ADDED]]": ("新增", "added"),
        "[[DEPENDENCY_MANAGEMENT]]": (
            "dependencymanagement",
            "dependency_management",
        ),
    }
    matched = 0
    for token in tokens:
        candidates = alternatives.get(token, (token.casefold(),))
        matched += any(candidate in folded for candidate in candidates)
    return round(matched * 1_000_000 / len(tokens))


def _numeric_values(
    values: Mapping[str, Mapping[str, object]],
    keys: Iterable[str],
    field: str,
) -> list[float]:
    result: list[float] = []
    for key in keys:
        value = values[key].get(field)
        if type(value) not in {int, float} or value < 0:
            continue
        result.append(float(value))
    return result


def _p95(values: Sequence[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * 0.95
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _population(values: Sequence[float]) -> dict[str, object]:
    return {
        "count": len(values),
        "p50_milliseconds": _rounded(_percentile(values, 0.5)),
        "p95_milliseconds": _rounded(_p95(values)),
    }


def _rounded(value: float | None) -> int | None:
    return round(value) if value is not None else None


def _percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    part = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * part


def _role_report_pass(value: Mapping[str, object]) -> bool:
    audit = value.get("operation_audit")
    return (
        value.get("status") == "PASS"
        and isinstance(audit, dict)
        and audit.get("status") == "PASS"
        and not any(audit.get("prohibited_counts", {}).values())
    )


def _run_index(root: Path, run_key: str) -> str:
    for path in (root / "runs").glob("*/terminal.json"):
        if _load(path).get("run_key") == run_key:
            return path.parent.name
    raise RuntimeError(f"missing terminal directory for {run_key}")


def _verified_reference(
    value: object,
    root: Path,
    label: str,
) -> Path:
    if not isinstance(value, dict) or set(value) != {"path", "digest", "size"}:
        raise ValueError(f"{label} reference is not closed")
    path = _existing_descendant_file(Path(str(value["path"])), root)
    if value["digest"] != _sha256(path) or value["size"] != path.stat().st_size:
        raise RuntimeError(f"{label} reference drifted")
    return path


def _existing_descendant_file(path: Path, root: Path) -> Path:
    if (
        not path.is_absolute()
        or path.resolve(strict=True) != path
        or not path.is_file()
        or path.is_symlink()
        or not _is_within(path, root)
    ):
        raise ValueError("evaluation input file escapes its evidence root")
    return path


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _load(path: Path) -> Mapping[str, object]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"document is not a regular file: {path}")
    raw = path.read_bytes()
    value = json.loads(raw, object_pairs_hook=_unique_object)
    if not isinstance(value, dict) or canonical_json_bytes(value) != raw:
        raise ValueError(f"document is not canonical JSON: {path}")
    return value


def _load_json_lines(path: Path) -> list[Mapping[str, object]]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"JSONL input is not a regular file: {path}")
    raw = path.read_bytes()
    if not raw.endswith(b"\n"):
        raise ValueError(f"JSONL input has no terminal newline: {path}")
    values: list[Mapping[str, object]] = []
    for line in raw.splitlines():
        value = json.loads(line, object_pairs_hook=_unique_object)
        if not isinstance(value, dict) or canonical_json_bytes(value) != line:
            raise ValueError(f"JSONL record is not canonical: {path}")
        values.append(value)
    return values


def _load_relaxed(path: Path) -> Mapping[str, object]:
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"document is not a regular file: {path}")
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
    )
    if not isinstance(value, dict):
        raise ValueError(f"document is not a JSON object: {path}")
    return value


def _verify_frozen_product_oracles(
    product_suite: Mapping[str, object],
) -> dict[str, str]:
    expected_registry = {
        "MALL-MAVEN-STRUCTURE@1.0.0": {
            "path": (
                "validation/structure_world_model_iteration_003/oracles/"
                "mall-structure-1.0.0.json"
            ),
            "digest": MALL_ORACLE_DIGEST,
        },
        "maven-identity-anti-name-stitch@1": {
            "path": (
                "validation/structure_world_model_iteration_003/fixtures/"
                "maven-identity/oracle.json"
            ),
            "digest": IDENTITY_ORACLE_DIGEST,
        },
    }
    actual = {
        "product_suite": _sha256(PRODUCT_SUITE),
        "mall_oracle": _sha256(MALL_ORACLE),
        "identity_oracle": _sha256(IDENTITY_ORACLE),
    }
    if (
        actual["product_suite"] != PRODUCT_SUITE_DIGEST
        or product_suite.get("oracle_registry") != expected_registry
        or actual["mall_oracle"] != MALL_ORACLE_DIGEST
        or actual["identity_oracle"] != IDENTITY_ORACLE_DIGEST
    ):
        raise RuntimeError("frozen Product suite/oracle file digest drifted")
    return actual


def _verify_frozen_baseline_seal(
    baseline_seal: Mapping[str, object],
) -> str:
    core = {
        key: value
        for key, value in baseline_seal.items()
        if key != "document_digest"
    }
    file_digest = _sha256(BASELINE_SEAL)
    if (
        file_digest != BASELINE_SEAL_FILE_DIGEST
        or baseline_seal.get("document_digest") != BASELINE_SEAL_DIGEST
        or digest_of(core).value != BASELINE_SEAL_DIGEST
    ):
        raise RuntimeError("V-009 baseline seal is not exact")
    return file_digest


def _validate_evaluator_delta_paths(paths: Sequence[str]) -> tuple[str, ...]:
    value = tuple(sorted(paths))
    if (
        not value
        or len(value) != len(set(value))
        or not set(value).issubset(_ALLOWED_POST_PRODUCT_EVALUATOR_DELTA)
        or (
            "validation/structure_world_model_iteration_003/g3b/"
            "evaluate_results.py"
        )
        not in value
    ):
        raise RuntimeError("post-product evaluator delta is not closed")
    return value


def _evaluator_delta_paths(
    product_commit: str,
    evaluator_commit: str,
) -> tuple[str, ...]:
    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", product_commit, evaluator_commit),
        cwd=PROJECT_ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if ancestor.returncode != 0:
        raise RuntimeError("evaluator checkpoint does not descend from product")
    completed = subprocess.run(
        ("git", "diff", "--name-only", product_commit, evaluator_commit),
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return _validate_evaluator_delta_paths(completed.stdout.splitlines())


def _commit(value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError("commit must be a full lowercase Git SHA")
    return value


def _require_clean_checkpoint(expected: str) -> str:
    head = subprocess.run(
        ("git", "rev-parse", "HEAD"),
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ("git", "rev-parse", "HEAD^{tree}"),
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ("git", "status", "--porcelain=v1"),
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if head != expected or status:
        raise RuntimeError("evaluation requires its exact clean checkpoint")
    return tree


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _directory(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=True) != path or not path.is_dir() or path.is_symlink():
        raise ValueError("input directory must be canonical")
    return path


def _future_file(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=False) != path or path.exists():
        raise ValueError("output must be a new canonical absolute file")
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError("output parent must be canonical")
    return path


def _write_new(path: Path, payload: bytes) -> None:
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
            raise RuntimeError("evaluation output is not a regular file")
    finally:
        os.close(descriptor)


def _sha256(path: Path) -> str:
    return "sha256:" + sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
