#!/usr/bin/env python3
"""Standalone stdlib evaluator for ITER-008 bounded proposals."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping


PACKET_SCHEMA = "swm.iter-008.bounded-java-source-semantics-ce-evaluator-packet@2"
RESULT_SCHEMA = "swm.iter-008.bounded-java-source-semantics-ce-normalized-result@2"
REVIEW_SCHEMA = "swm.iter-008.bounded-java-source-semantics-ce-independent-review@2"


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
        "steps",
    }:
        raise ValueError("evaluator case shape is invalid")
    packet_steps = case.get("steps")
    if not isinstance(packet_steps, list) or not packet_steps:
        raise ValueError("evaluator case steps are invalid")
    if not isinstance(result, Mapping) or set(result) != {
        "schema",
        "suite_ref",
        "suite_digest",
        "case_id",
        "capability",
        "step_results",
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
    ):
        raise ValueError("normalized result uses another sealed case")
    result_steps = result.get("step_results")
    if not isinstance(result_steps, list) or len(result_steps) != len(packet_steps):
        raise ValueError("normalized result call count is invalid")
    audit = result.get("operation_audit")
    if not isinstance(audit, Mapping):
        raise ValueError("operation audit is invalid")
    _verify_closed_audit(audit, len(packet_steps))

    projections: list[dict[str, object]] = []
    projection_digests: list[str] = []
    expected_digests: list[str] = []
    normalized_digests: list[str] = []
    trace_digests: list[str] = []
    findings: list[str] = []
    derived_events: set[str] = set(audit["observed_events"])
    forbidden_observed: set[str] = set()
    semantic_failures = 0
    exact_failures = 0
    for expected_step, actual_step in zip(packet_steps, result_steps):
        if not isinstance(expected_step, Mapping) or set(expected_step) != {
            "call_index",
            "case_call_id",
            "sealed_input",
            "sealed_input_digest",
            "projection_fields",
            "semantic_constraints",
            "expected_projections",
            "forbidden_events",
        }:
            raise ValueError("evaluator packet step shape is invalid")
        if not isinstance(actual_step, Mapping) or set(actual_step) != {
            "call_index",
            "case_call_id",
            "sealed_input_digest",
            "normalized_result",
            "normalized_result_digest",
            "evidence_trace_digest",
        }:
            raise ValueError("normalized result step shape is invalid")
        call_index = expected_step.get("call_index")
        if (
            actual_step.get("call_index") != call_index
            or actual_step.get("case_call_id") != expected_step.get("case_call_id")
            or actual_step.get("sealed_input_digest")
            != expected_step.get("sealed_input_digest")
            or expected_step.get("sealed_input_digest")
            != _digest(expected_step.get("sealed_input"))
        ):
            raise ValueError("normalized result step uses another sealed input")
        normalized = actual_step.get("normalized_result")
        if not isinstance(normalized, Mapping):
            raise ValueError("normalized step result is not an object")
        normalized_digest = _digest(normalized)
        if actual_step.get("normalized_result_digest") != normalized_digest:
            raise ValueError("normalized step result digest does not verify")
        evidence_trace = _step_trace_digest(
            str(case["case_id"]),
            int(call_index),
            str(expected_step["sealed_input_digest"]),
            normalized_digest,
        )
        if actual_step.get("evidence_trace_digest") != evidence_trace:
            raise ValueError("per-call evidence trace digest does not verify")
        fields = _strings(expected_step.get("projection_fields"), "projection fields")
        if len(fields) != len(set(fields)) or any(field not in normalized for field in fields):
            raise ValueError("projection field set is invalid")
        projection = {field: normalized[field] for field in fields}
        expected = expected_step.get("expected_projections")
        if (
            not isinstance(expected, list)
            or not expected
            or any(
                not isinstance(item, Mapping) or set(item) != set(fields)
                for item in expected
            )
            or len({_digest(item) for item in expected}) != len(expected)
        ):
            raise ValueError("accepted projection set is invalid")
        exact = projection in expected
        if not exact:
            exact_failures += 1
            findings.append(f"CALL_{call_index}:CONTRACT_PROJECTION_NOT_EXACT")
        constraints = expected_step.get("semantic_constraints")
        if not isinstance(constraints, Mapping):
            raise ValueError("semantic constraints are invalid")
        semantic = _semantic_match(normalized, constraints)
        if not semantic:
            semantic_failures += 1
            findings.append(f"CALL_{call_index}:SEMANTIC_CONSTRAINT_NOT_SATISFIED")
        sealed_input = expected_step.get("sealed_input", {})
        if not isinstance(sealed_input, Mapping):
            raise ValueError("sealed evaluator input is invalid")
        if normalized.get("trace_digest") != sealed_input.get("trace_digest"):
            derived_events.add("TRACE_DIGEST_CHANGED")
        if normalized.get("step_index") != sealed_input.get("step_index"):
            derived_events.add("STEP_INDEX_CHANGED")
        forbidden = set(
            _strings(expected_step.get("forbidden_events"), "forbidden events")
        )
        forbidden_observed.update(derived_events & forbidden)
        projections.append(projection)
        projection_digests.append(_digest(projection))
        expected_digests.append(_digest(expected))
        normalized_digests.append(normalized_digest)
        trace_digests.append(evidence_trace)

    findings.extend(
        f"FORBIDDEN_EVENT:{item}" for item in sorted(forbidden_observed)
    )
    passed = not exact_failures and not semantic_failures and not forbidden_observed
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
        "model_call_count": len(packet_steps),
        "normalized_result_digests": normalized_digests,
        "evidence_trace_digests": trace_digests,
        "projections": projections,
        "projection_digests": projection_digests,
        "expected_projection_digests": expected_digests,
        "projection_exact": exact_failures == 0,
        "semantic_constraints_satisfied": semantic_failures == 0,
        "derived_events": sorted(derived_events),
        "forbidden_events_observed": sorted(forbidden_observed),
        "platform_contract_valid": not forbidden_observed,
        "oracle_match": exact_failures == 0 and semantic_failures == 0,
        "unauthorized_reference_count": len(forbidden_observed),
        "material_omission_count": semantic_failures,
        "material_error_count": exact_failures + len(forbidden_observed),
        "findings": findings,
        "conclusion": "PASS" if passed else "FAIL",
        "evaluator_pid": os.getpid(),
        "evaluator_origin": "standalone-stdlib-iter008-bounded-source-semantics",
        "evaluator_implementation_digest": implementation_digest,
        "evaluated_strategy_import_count": 0,
        "product_import_count": 0,
    }
    return {**core, "document_digest": _document_digest(core)}


def _verify_closed_audit(audit: Mapping[str, object], call_count: int) -> None:
    expected_fields = {
        "model_call_count",
        "provider_request_count",
        "unique_model_call_id_count",
        "hidden_retry_count",
        "product_oracle_read_count",
        "product_suite_read_count",
        "repository_read_count",
        "source_access_count",
        "evidence_payload_access_count",
        "project_dictionary_access_count",
        "project_name_branch_count",
        "self_review_count",
        "observed_events",
        "model_input_item_ids",
    }
    if set(audit) != expected_fields:
        raise ValueError("operation audit field set is not closed")
    for field, expected in (
        ("model_call_count", call_count),
        ("provider_request_count", call_count),
        ("unique_model_call_id_count", call_count),
        ("hidden_retry_count", 0),
        ("product_oracle_read_count", 0),
        ("product_suite_read_count", 0),
        ("repository_read_count", 0),
        ("source_access_count", 0),
        ("evidence_payload_access_count", 0),
        ("project_dictionary_access_count", 0),
        ("project_name_branch_count", 0),
        ("self_review_count", 0),
    ):
        if audit.get(field) != expected:
            raise ValueError(f"operation audit field {field} is not closed")
    input_ids = audit.get("model_input_item_ids")
    expected_ids = ["instruction", "sealed-case-input", "qualification"]
    if not isinstance(input_ids, list) or input_ids != [expected_ids] * call_count:
        raise ValueError("model input item IDs are invalid")
    observed = audit.get("observed_events")
    if not isinstance(observed, list) or any(
        not isinstance(item, str) for item in observed
    ):
        raise ValueError("observed event audit is invalid")


def _semantic_match(
    normalized: Mapping[str, object], constraints: Mapping[str, object]
) -> bool:
    for field, value in constraints.items():
        if field == "search_term_concept_groups":
            terms = normalized.get("search_terms")
            if not isinstance(terms, list) or not _contains_all_groups(
                " ".join(str(item) for item in terms),
                _concept_groups(value, field),
            ):
                return False
        elif field == "finish_reason_concept_groups":
            reason = normalized.get("finish_reason")
            if not isinstance(reason, str) or not _contains_all_groups(
                reason, _concept_groups(value, field)
            ):
                return False
        elif field == "answer_concept_groups":
            answer = normalized.get("answer")
            if not isinstance(answer, str) or not _contains_all_groups(
                answer, _concept_groups(value, field)
            ):
                return False
        elif field == "answer_order_groups":
            answer = normalized.get("answer")
            if not isinstance(answer, str) or not _groups_appear_in_order(
                answer, _concept_groups(value, field)
            ):
                return False
        elif field == "required_finding_codes":
            required = _strings(value, field)
            findings = normalized.get("finding_codes")
            if not isinstance(findings, list) or any(
                item not in findings for item in required
            ):
                return False
        else:
            raise ValueError("semantic constraint vocabulary is invalid")
    return True


def _contains_all_groups(text: str, groups: list[list[str]]) -> bool:
    folded = text.casefold()
    return all(any(term.casefold() in folded for term in group) for group in groups)


def _groups_appear_in_order(text: str, groups: list[list[str]]) -> bool:
    folded = text.casefold()
    cursor = 0
    for group in groups:
        positions = [
            (folded.find(term.casefold(), cursor), len(term))
            for term in group
            if folded.find(term.casefold(), cursor) >= 0
        ]
        if not positions:
            return False
        position, length = min(positions)
        cursor = position + length
    return True


def _concept_groups(value: object, label: str) -> list[list[str]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} are invalid")
    return [_strings(group, label) for group in value]


def _step_trace_digest(
    case_id: str,
    call_index: int,
    input_digest: str,
    normalized_digest: str,
) -> str:
    return _digest(
        [
            "ITER-008-BOUNDED-CAPABILITY-STEP-EVIDENCE@1",
            case_id,
            call_index,
            input_digest,
            normalized_digest,
        ]
    )


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
