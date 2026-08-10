"""Standalone deterministic evaluator for ITER-003 V-009.

The process intentionally uses only the Python standard library and does not
import the evaluated strategy, application code, Provider adapter, product
suite, repository, Source, or Evidence implementations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


PACKET_SCHEMA = "swm.iter-003.world-model-ce-evaluator-packet@1"
RESULT_SCHEMA = "swm.iter-003.world-model-ce-normalized-result@1"
REVIEW_SCHEMA = "swm.iter-003.world-model-ce-independent-review@1"


def _parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(prog="v009-independent-evaluator")
    value.add_argument("--packet", required=True)
    value.add_argument("--result", required=True)
    value.add_argument("--output", required=True)
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _load(path: Path) -> dict[str, object]:
    value = json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_unique_object,
    )
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _verify_document(value: dict[str, object], schema: str) -> None:
    if value.get("schema") != schema:
        raise ValueError("document schema is invalid")
    recorded = value.get("document_digest")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if recorded != _digest(core):
        raise ValueError("document digest is invalid")


def _string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise ValueError(f"{label} must be an array of non-empty strings")
    return value


def _derive_events(
    *,
    capability: str,
    sealed_input: object,
    normalized: dict[str, object],
    expected: dict[str, object],
    operation_audit: dict[str, object],
) -> set[str]:
    events = set(_string_list(operation_audit.get("observed_events"), "observed events"))
    audit_event = {
        "source_access_count": "SOURCE_ACCESS",
        "evidence_payload_access_count": "EVIDENCE_PAYLOAD_ACCESS",
        "project_name_branch_count": "PROJECT_NAME_BRANCH",
        "self_review_count": "SELF_REVIEW",
    }
    for field, event in audit_event.items():
        count = operation_audit.get(field)
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"operation audit field {field} is invalid")
        if count:
            events.add(event)

    case_value = sealed_input
    if isinstance(sealed_input, dict) and "input" in sealed_input:
        case_value = sealed_input["input"]

    if capability == "REQUIREMENT_FIDELITY":
        expected_needs = expected.get("need_keys")
        actual_needs = normalized.get("need_keys")
        if isinstance(expected_needs, list) and isinstance(actual_needs, list):
            if any(item not in actual_needs for item in expected_needs):
                events.add("NEED_OMITTED")
        if normalized.get("joint_constraints") != expected.get("joint_constraints"):
            events.add("ORDER_REVERSED")
    elif capability == "GENERIC_QUERY_PLANNING":
        available = set()
        if isinstance(sealed_input, dict):
            raw = sealed_input.get("available_operations")
            if isinstance(raw, list):
                available = {item for item in raw if isinstance(item, str)}
        operations = normalized.get("operations")
        if isinstance(operations, list):
            for operation in operations:
                if (
                    not isinstance(operation, dict)
                    or operation.get("operation") not in available
                ):
                    events.add("UNREGISTERED_OPERATION")
    elif capability == "COMPLETE_NEGATIVE_ANSWER":
        if normalized.get("need_status") != "SATISFIED_SUPPORTED_NEGATIVE":
            events.add("COVERAGE_OMITTED")
        scope = normalized.get("claim_scope")
        if not isinstance(scope, str) or not scope.endswith("_FOR_EXACT_READ_SET"):
            events.add("GLOBAL_ABSENCE_CLAIM")
    elif capability == "VIEW_LIMITATION_AND_KNOWLEDGE_GAP":
        view = normalized.get("view_result")
        need = normalized.get("need_assessment")
        if isinstance(need, dict) and need.get("status") == "SATISFIED_SUPPORTED_NEGATIVE":
            events.add("SUPPORTED_NEGATIVE")
        if isinstance(view, dict) and view.get("owner") == "KNOWLEDGE_USE":
            events.add("VIEW_CREATED_KNOWLEDGE_GAP")
        if normalized != expected:
            events.add("LIMITATION_HIDDEN")
    elif capability == "ORDERED_DIFF_EXPRESSION":
        if normalized.get("direction") != expected.get("direction"):
            events.add("BASE_TARGET_REVERSED")
            events.add("SNAPSHOT_ID_SORT_DIRECTION")
    elif capability == "INDEPENDENT_ANSWER_REVIEW":
        if normalized.get("decision") != "REJECT":
            events.add("APPROVED_WITH_FINDING")
        expected_findings = expected.get("finding_codes")
        actual_findings = normalized.get("finding_codes")
        if isinstance(expected_findings, list) and isinstance(actual_findings, list):
            if any(item not in actual_findings for item in expected_findings):
                events.add("FAULT_OMITTED")
    elif capability == "ENTITY_CANDIDATE_RESOLUTION":
        candidates = []
        if isinstance(case_value, dict):
            raw_candidates = case_value.get("candidate_refs")
            if isinstance(raw_candidates, list):
                candidates = raw_candidates
        if len(candidates) > 1 and normalized.get("resolution_status") == "RESOLVED":
            events.add("MODEL_SELECTED_CANDIDATE")
            events.add("LABEL_STITCH")
        if len(candidates) > 1 and normalized.get("next_operation_allowed") is True:
            events.add("TYPED_OPERATION_WITH_AMBIGUOUS_REF")
    return events


def evaluate(packet: dict[str, object], result: dict[str, object]) -> dict[str, object]:
    _verify_document(packet, PACKET_SCHEMA)
    _verify_document(result, RESULT_SCHEMA)
    case = packet.get("case")
    if not isinstance(case, dict):
        raise ValueError("evaluator packet case is invalid")
    normalized = result.get("normalized_result")
    if not isinstance(normalized, dict):
        raise ValueError("normalized result is invalid")
    if result.get("case_id") != case.get("case_id"):
        raise ValueError("normalized result belongs to another case")
    if result.get("capability") != case.get("capability"):
        raise ValueError("normalized result capability is invalid")
    if result.get("case_input_digest") != case.get("case_input_digest"):
        raise ValueError("normalized result uses another sealed input")

    fields = _string_list(case.get("projection_fields"), "projection fields")
    if len(fields) != len(set(fields)) or any(field not in normalized for field in fields):
        raise ValueError("projection field set is invalid")
    projection = {field: normalized[field] for field in fields}
    expected = case.get("expected_normalized_result")
    if not isinstance(expected, dict) or set(expected) != set(fields):
        raise ValueError("expected projection is invalid")
    forbidden = set(_string_list(case.get("forbidden_events"), "forbidden events"))
    audit = result.get("operation_audit")
    if not isinstance(audit, dict):
        raise ValueError("operation audit is invalid")
    for field, expected_value in (
        ("model_call_count", 1),
        ("hidden_retry_count", 0),
        ("product_oracle_read_count", 0),
        ("product_suite_read_count", 0),
        ("repository_read_count", 0),
        ("source_access_count", 0),
        ("evidence_payload_access_count", 0),
        ("project_name_branch_count", 0),
        ("self_review_count", 0),
    ):
        if audit.get(field) != expected_value:
            raise ValueError(f"operation audit field {field} is not closed")
    events = _derive_events(
        capability=str(case["capability"]),
        sealed_input=case.get("sealed_input"),
        normalized=normalized,
        expected=expected,
        operation_audit=audit,
    )
    observed_forbidden = sorted(events & forbidden)
    exact = projection == expected
    findings: list[str] = []
    if not exact:
        findings.append("PROJECTION_NOT_EXACT")
    findings.extend(f"FORBIDDEN_EVENT:{item}" for item in observed_forbidden)
    implementation_digest = "sha256:" + hashlib.sha256(
        Path(__file__).read_bytes()
    ).hexdigest()
    core = {
        "schema": REVIEW_SCHEMA,
        "suite_ref": packet.get("suite_ref"),
        "suite_digest": packet.get("suite_digest"),
        "case_id": case.get("case_id"),
        "capability": case.get("capability"),
        "case_input_digest": case.get("case_input_digest"),
        "normalized_result_digest": result.get("normalized_result_digest"),
        "projection": projection,
        "projection_digest": _digest(projection),
        "expected_projection_digest": _digest(expected),
        "projection_exact": exact,
        "forbidden_events_observed": observed_forbidden,
        "platform_contract_valid": not observed_forbidden,
        "oracle_match": exact,
        "unauthorized_reference_count": len(observed_forbidden),
        "material_omission_count": 0 if exact else 1,
        "material_error_count": len(observed_forbidden),
        "findings": findings,
        "conclusion": "PASS" if exact and not observed_forbidden else "FAIL",
        "evaluator_pid": os.getpid(),
        "evaluator_origin": "standalone-stdlib-v009-evaluator",
        "evaluator_implementation_digest": implementation_digest,
        "evaluated_strategy_import_count": 0,
    }
    return {**core, "document_digest": _digest(core)}


def _write_once(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_canonical(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        packet = _load(Path(arguments.packet))
        result = _load(Path(arguments.result))
        review = evaluate(packet, result)
        _write_once(Path(arguments.output), review)
        json.dump(
            {
                "status": review["conclusion"],
                "case_id": review["case_id"],
                "review_path": str(Path(arguments.output)),
                "review_digest": review["document_digest"],
            },
            sys.stdout,
            ensure_ascii=False,
            sort_keys=True,
        )
        sys.stdout.write("\n")
        return 0 if review["conclusion"] == "PASS" else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        json.dump(
            {"status": "ERROR", "message": str(exc)},
            sys.stdout,
            ensure_ascii=False,
            sort_keys=True,
        )
        sys.stdout.write("\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
