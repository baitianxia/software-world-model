#!/usr/bin/env python3
"""Independently evaluate G3b product, isolation, oracle, and baseline results."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import stat
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-root", required=True)
    parser.add_argument("--evidence-root", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    prepared_root = _directory(arguments.prepared_root)
    evidence_root = _directory(arguments.evidence_root)
    output = _future_file(arguments.output)
    registry = _load(prepared_root / "prepared-inputs.json")
    batch = _load(evidence_root / "batch-result.json")
    invocation = _load(evidence_root / "invocation.json")
    bootstrap = _load(evidence_root / "provider-bootstrap.json")
    preflight = _load(evidence_root / "preflight.json")
    preflight_provisioning = _load(
        evidence_root
        / "preflight"
        / "gateway"
        / "connection-provisioning.json"
    )
    mall = _load(MALL_ORACLE)
    identity = _load(IDENTITY_ORACLE)
    generation = _load(prepared_root / "evaluator" / "generation-report.json")
    comparison_preflight = _load(
        prepared_root / "evaluator" / "baseline-comparison-preflight.json"
    )
    baseline_seal = _load(BASELINES / "baseline-seal.json")
    baseline_product_plan = _load_relaxed(
        BASELINES / "operator" / "product-plan.json"
    )
    if baseline_seal.get("document_digest") != BASELINE_SEAL_DIGEST:
        raise RuntimeError("V-009 baseline seal is not exact")

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
        "schema": "swm.iter-003.g3b-product-evaluation@1",
        "status": status,
        "environment": "EVALUATION_ONLY",
        "implementation_commit": batch.get("implementation_commit"),
        "batch_result_digest": batch.get("document_digest"),
        "prepared_registry_digest": registry.get("document_digest"),
        "baseline_seal_digest": baseline_seal["document_digest"],
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
        or gateway_summary.get("numeric_provider_address_scope")
        not in {"PUBLIC_UNICAST", "EXECUTOR_SYNTHETIC_EXTERNAL"}
        or len(server_audits) != 1
        or server_audits[0].get("status") != "RESULT"
        or len(transport_audits) != 1
        or transport_audits[0].get("outcome") != "HTTP_RESPONSE"
        or transport_audits[0].get("failure_code") is not None
        or transport_audits[0].get("endpoint")
        != (
            "https://ark.cn-beijing.volces.com:443/"
            "api/coding/v3/chat/completions"
        )
        or transport_audits[0].get("numeric_address")
        != gateway_summary.get("numeric_provider_address")
        or transport_audits[0].get("address_scope")
        != gateway_summary.get("numeric_provider_address_scope")
        or not isinstance(
            transport_audits[0].get("peer_certificate_sha256"), str
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
        and batch.get("implementation_commit")
        == registry.get("implementation_commit")
        and batch.get("stage_unchanged_after_batch") is True
        and batch.get("gateway_new_dns_inet_inet6_capability") == "DENIED"
        and batch.get("provider_connection_capability")
        == "INHERITED_EXACT_CONNECTED_SOCKET"
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
        and preflight.get("document_digest") == digest_of(preflight_core).value
        and batch.get("preflight_digest") == preflight.get("document_digest")
        and _preflight_pass(preflight)
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
        and value.get("connected_peer_address") == selected
        and value.get("connected_peer_port") == 443
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


def _preflight_pass(value: Mapping[str, object]) -> bool:
    roles = value.get("roles")
    if (
        value.get("status") != "PASS"
        or value.get("os_enforcement") != "MACOS_SEATBELT_DENY_DEFAULT"
        or value.get("protected_stage_unchanged") is not True
        or value.get("protected_stage_manifest_before")
        != value.get("protected_stage_manifest_after")
        or value.get("gateway_external_capability")
        != "ONE_EVALUATOR_CONNECTED_EXACT_PEER_FD; NEW_DNS_INET_INET6_DENIED"
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
            "allowed_exact_gateway_bind",
            "allowed_inherited_exact_provider_tls",
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
            or diff["entities"]["counts"] != {"added": 1, "removed": 0, "state_changed": 7}
            or diff["relations"]["counts"] != {"added": 3, "removed": 0, "state_changed": 11}
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
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
    )
    if not isinstance(value, dict):
        raise ValueError(f"document is not a JSON object: {path}")
    return value


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
