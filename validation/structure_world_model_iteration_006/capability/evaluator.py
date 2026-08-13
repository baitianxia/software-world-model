#!/usr/bin/env python3
"""Standalone stdlib-only evaluator for the ITER-006 Java capability suite."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping


PACKET_SCHEMA = "swm.iter-006.java-world-model-ce-evaluator-packet@1"
RESULT_SCHEMA = "swm.iter-006.java-world-model-ce-normalized-result@1"
REVIEW_SCHEMA = "swm.iter-006.java-world-model-ce-independent-review@1"


def evaluate(packet: object, result: object) -> dict[str, object]:
    if not isinstance(packet, Mapping) or set(packet) != {
        "schema",
        "suite_ref",
        "suite_digest",
        "oracle_ref",
        "oracle_digest",
        "case",
        "document_digest",
    }:
        raise ValueError("evaluator packet shape is invalid")
    _verify_document(packet, PACKET_SCHEMA)
    case = packet.get("case")
    if not isinstance(case, Mapping) or set(case) != {
        "case_id",
        "capability",
        "sealed_input",
        "case_input_digest",
        "projection_fields",
        "expected_normalized_result",
        "forbidden_events",
    }:
        raise ValueError("evaluator case shape is invalid")
    if not isinstance(result, Mapping) or set(result) != {
        "schema",
        "suite_ref",
        "suite_digest",
        "case_id",
        "capability",
        "case_input_digest",
        "normalized_result",
        "normalized_result_digest",
        "operation_audit",
        "document_digest",
    }:
        raise ValueError("normalized result shape is invalid")
    _verify_document(result, RESULT_SCHEMA)
    if (
        result.get("suite_ref") != packet.get("suite_ref")
        or result.get("suite_digest") != packet.get("suite_digest")
        or result.get("case_id") != case.get("case_id")
        or result.get("capability") != case.get("capability")
        or result.get("case_input_digest") != case.get("case_input_digest")
    ):
        raise ValueError("normalized result uses another sealed case")
    normalized = result.get("normalized_result")
    if not isinstance(normalized, Mapping):
        raise ValueError("normalized result is not an object")
    if result.get("normalized_result_digest") != _digest(normalized):
        raise ValueError("normalized result digest does not verify")
    fields = _strings(case.get("projection_fields"), "projection fields")
    if len(fields) != len(set(fields)) or any(field not in normalized for field in fields):
        raise ValueError("projection field set is invalid")
    projection = {field: normalized[field] for field in fields}
    expected = case.get("expected_normalized_result")
    if not isinstance(expected, Mapping) or set(expected) != set(fields):
        raise ValueError("expected projection is invalid")
    forbidden = set(_strings(case.get("forbidden_events"), "forbidden events"))
    audit = result.get("operation_audit")
    if not isinstance(audit, Mapping):
        raise ValueError("operation audit is invalid")
    _verify_closed_audit(audit)
    derived = _derive_events(case, normalized, expected, audit)
    observed_forbidden = sorted(derived & forbidden)
    exact = projection == expected
    findings = ([] if exact else ["PROJECTION_NOT_EXACT"]) + [
        f"FORBIDDEN_EVENT:{item}" for item in observed_forbidden
    ]
    implementation_digest = "sha256:" + hashlib.sha256(
        Path(__file__).read_bytes()
    ).hexdigest()
    core = {
        "schema": REVIEW_SCHEMA,
        "suite_ref": packet["suite_ref"],
        "suite_digest": packet["suite_digest"],
        "oracle_ref": packet["oracle_ref"],
        "oracle_digest": packet["oracle_digest"],
        "case_id": case["case_id"],
        "capability": case["capability"],
        "case_input_digest": case["case_input_digest"],
        "normalized_result_digest": result["normalized_result_digest"],
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
        "evaluator_origin": "standalone-stdlib-iter006-java-capability",
        "evaluator_implementation_digest": implementation_digest,
        "evaluated_strategy_import_count": 0,
        "product_import_count": 0,
    }
    return {**core, "document_digest": _document_digest(core)}


def _verify_closed_audit(audit: Mapping[str, object]) -> None:
    for field, expected in (
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
        if audit.get(field) != expected:
            raise ValueError(f"operation audit field {field} is not closed")
    _strings(audit.get("model_input_item_ids"), "model input item IDs")
    observed = audit.get("observed_events")
    if not isinstance(observed, list) or any(not isinstance(item, str) for item in observed):
        raise ValueError("observed event audit is invalid")


def _derive_events(
    case: Mapping[str, object],
    normalized: Mapping[str, object],
    expected: Mapping[str, object],
    audit: Mapping[str, object],
) -> set[str]:
    events = set(audit.get("observed_events", []))
    capability = case.get("capability")
    sealed = case.get("sealed_input")
    if not isinstance(sealed, Mapping):
        raise ValueError("sealed case input is invalid")
    source = sealed.get("input")
    available = sealed.get("available_operations", [])
    if capability == "GENERIC_QUERY_PLANNING":
        if not isinstance(source, Mapping) or not isinstance(available, list):
            raise ValueError("planning input is invalid")
        operations = normalized.get("operations")
        if not isinstance(operations, list):
            events.add("UNREGISTERED_OPERATION")
        else:
            names = [
                item.get("operation") if isinstance(item, Mapping) else None
                for item in operations
            ]
            if any(name not in available for name in names):
                events.add("UNREGISTERED_OPERATION")
            needs = source.get("needs")
            if isinstance(needs, list) and any(
                str(need).startswith("method_inventory_") for need in needs
            ) and "inventory" in names:
                events.add("INVENTORY_OPERATION_SUBSTITUTED")
            expected_operations = expected.get("operations")
            if operations != expected_operations:
                events.add("OPERATION_ORDER_CHANGED")
            source_ref = source.get("source_entity_ref")
            target_ref = source.get("target_entity_ref")
            for operation in operations:
                if not isinstance(operation, Mapping):
                    continue
                if operation.get("operation") == "all_simple_paths" and (
                    operation.get("source_ref") != source_ref
                    or operation.get("target_ref") != target_ref
                ):
                    events.add("ENTITY_REF_CHANGED")
            read_set = source.get("read_set")
            if (
                isinstance(read_set, list)
                and len(read_set) == 2
                and any(
                    isinstance(operation, Mapping)
                    and operation.get("operation") == "ordered_snapshot_diff"
                    and (
                        operation.get("base") != read_set[0]
                        or operation.get("target") != read_set[1]
                    )
                    for operation in operations
                )
            ):
                events.add("SNAPSHOT_ID_SORT_DIRECTION")
    elif capability == "COMPLETE_NEGATIVE_ANSWER":
        if normalized.get("need_status") != "SATISFIED_SUPPORTED_NEGATIVE":
            events.add("COVERAGE_OMITTED")
        if not str(normalized.get("claim_scope", "")).endswith(
            "_FOR_EXACT_READ_SET"
        ):
            events.add("GLOBAL_ABSENCE_CLAIM")
    elif capability == "VIEW_LIMITATION_AND_KNOWLEDGE_GAP":
        if normalized.get("view_result") != expected.get("view_result"):
            events.add("LIMITATION_HIDDEN")
        if normalized.get("need_assessment") != expected.get("need_assessment"):
            events.add("VIEW_CREATED_KNOWLEDGE_GAP")
    elif capability == "ORDERED_DIFF_EXPRESSION":
        if isinstance(source, Mapping):
            direction = normalized.get("direction")
            if not isinstance(direction, Mapping) or (
                direction.get("base") != source.get("base")
                or direction.get("target") != source.get("target")
            ):
                events.add("BASE_TARGET_REVERSED")
    elif capability == "INDEPENDENT_ANSWER_REVIEW":
        if normalized.get("decision") != "REJECT":
            events.add("APPROVED_WITH_FINDING")
        if normalized.get("finding_codes") != expected.get("finding_codes"):
            events.add("FAULT_OMITTED")
    elif capability == "ENTITY_CANDIDATE_RESOLUTION":
        if isinstance(source, Mapping) and normalized.get("candidate_refs") != source.get(
            "candidate_refs"
        ):
            events.add("MODEL_SELECTED_CANDIDATE")
        if normalized.get("next_operation_allowed") is not False:
            events.add("TYPED_OPERATION_WITH_AMBIGUOUS_REF")
    return events


def _verify_document(value: Mapping[str, object], schema: str) -> None:
    if value.get("schema") != schema:
        raise ValueError("document schema is invalid")
    core = {key: item for key, item in value.items() if key != "document_digest"}
    if value.get("document_digest") != _document_digest(core):
        raise ValueError("document digest does not verify")


def _document_digest(core: object) -> str:
    return _digest([core.get("schema"), core] if isinstance(core, Mapping) else core)


def _digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _strings(value: object, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        raise ValueError(f"{label} are invalid")
    return value


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_bytes(), object_pairs_hook=_unique_object)
    if not isinstance(value, dict):
        raise ValueError("input document must be an object")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--output", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        review = evaluate(_load(Path(arguments.packet)), _load(Path(arguments.result)))
        _write_once(Path(arguments.output), review)
        print(_canonical({"status": review["conclusion"], "case_id": review["case_id"]}).decode())
        return 0 if review["conclusion"] == "PASS" else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(_canonical({"status": "ERROR", "message": str(exc)}).decode())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
