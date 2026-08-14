#!/usr/bin/env python3
"""Standalone stdlib evaluator for ITER-007 source-semantics proposals."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Mapping


PACKET_SCHEMA = "swm.iter-007.java-source-semantics-ce-evaluator-packet@1"
RESULT_SCHEMA = "swm.iter-007.java-source-semantics-ce-normalized-result@1"
REVIEW_SCHEMA = "swm.iter-007.java-source-semantics-ce-independent-review@1"


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
        "semantic_constraints",
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
    if len(fields) != len(set(fields)) or any(
        field not in normalized for field in fields
    ):
        raise ValueError("projection field set is invalid")
    projection = {field: normalized[field] for field in fields}
    expected = case.get("expected_normalized_result")
    if not isinstance(expected, Mapping) or set(expected) != set(fields):
        raise ValueError("expected projection is invalid")
    constraints = case.get("semantic_constraints")
    if not isinstance(constraints, Mapping):
        raise ValueError("semantic constraints are invalid")
    forbidden = set(_strings(case.get("forbidden_events"), "forbidden events"))
    audit = result.get("operation_audit")
    if not isinstance(audit, Mapping):
        raise ValueError("operation audit is invalid")
    _verify_closed_audit(audit)
    derived = _derive_events(case, normalized, expected, constraints, audit)
    observed_forbidden = sorted(derived & forbidden)
    exact = projection == expected
    semantic_match = not any(
        item
        in {
            "FEATURE_CONCEPT_OMITTED",
            "ANSWER_CONCEPT_OMITTED",
            "SOURCE_ORDER_CHANGED",
            "FAULT_OMITTED",
            "APPROVED_FAULTY_DRAFT",
            "REJECTED_CORRECT_DRAFT",
        }
        for item in derived
    )
    findings = ([] if exact else ["CONTRACT_PROJECTION_NOT_EXACT"])
    if not semantic_match:
        findings.append("SEMANTIC_CONSTRAINT_NOT_SATISFIED")
    findings.extend(f"FORBIDDEN_EVENT:{item}" for item in observed_forbidden)
    implementation_digest = "sha256:" + hashlib.sha256(
        Path(__file__).read_bytes()
    ).hexdigest()
    passed = exact and semantic_match and not observed_forbidden
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
        "semantic_constraints_satisfied": semantic_match,
        "derived_events": sorted(derived),
        "forbidden_events_observed": observed_forbidden,
        "platform_contract_valid": not observed_forbidden,
        "oracle_match": exact and semantic_match,
        "unauthorized_reference_count": len(observed_forbidden),
        "material_omission_count": 0 if semantic_match else 1,
        "material_error_count": len(observed_forbidden),
        "findings": findings,
        "conclusion": "PASS" if passed else "FAIL",
        "evaluator_pid": os.getpid(),
        "evaluator_origin": "standalone-stdlib-iter007-source-semantics",
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
        ("project_dictionary_access_count", 0),
        ("project_name_branch_count", 0),
        ("self_review_count", 0),
    ):
        if audit.get(field) != expected:
            raise ValueError(f"operation audit field {field} is not closed")
    if set(audit) != {
        "model_call_count",
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
    }:
        raise ValueError("operation audit field set is not closed")
    if audit.get("model_input_item_ids") != [
        "instruction",
        "sealed-case-input",
        "qualification",
    ]:
        raise ValueError("model input item IDs are invalid")
    observed = audit.get("observed_events")
    if not isinstance(observed, list) or any(
        not isinstance(item, str) for item in observed
    ):
        raise ValueError("observed event audit is invalid")


def _derive_events(
    case: Mapping[str, object],
    normalized: Mapping[str, object],
    expected: Mapping[str, object],
    constraints: Mapping[str, object],
    audit: Mapping[str, object],
) -> set[str]:
    events = set(audit.get("observed_events", []))
    capability = case.get("capability")
    sealed = case.get("sealed_input")
    if not isinstance(sealed, Mapping):
        raise ValueError("sealed case input is invalid")
    source = sealed.get("input")
    if not isinstance(source, Mapping):
        raise ValueError("sealed capability input is invalid")
    if capability == "IMPLEMENTATION_QUERY_PLANNING":
        _planning_events(events, normalized, expected, constraints, source, sealed)
    elif capability == "IMPLEMENTATION_ANSWER_DRAFTING":
        _draft_events(events, normalized, expected, constraints, source)
    elif capability == "IMPLEMENTATION_ANSWER_REVIEW":
        _review_events(events, normalized, expected, constraints, source)
    else:
        raise ValueError("capability is unsupported")
    return events


def _planning_events(
    events: set[str],
    normalized: Mapping[str, object],
    expected: Mapping[str, object],
    constraints: Mapping[str, object],
    source: Mapping[str, object],
    sealed: Mapping[str, object],
) -> None:
    operations = normalized.get("operations")
    available = sealed.get("available_operations")
    if not isinstance(operations, list) or not isinstance(available, list):
        events.add("UNREGISTERED_OPERATION")
    else:
        if any(item not in available for item in operations):
            events.add("UNREGISTERED_OPERATION")
        if operations != available:
            events.add("OPERATION_ORDER_CHANGED")
    if normalized.get("snapshot") != expected.get("snapshot"):
        events.add("SNAPSHOT_CHANGED")
    terms = normalized.get("search_terms")
    if (
        not isinstance(terms, list)
        or not 1 <= len(terms) <= 12
        or any(
            not isinstance(item, str)
            or not item
            or item != item.strip()
            or len(item) > 128
            for item in terms
        )
        or len({str(item).casefold() for item in terms}) != len(terms)
    ):
        events.add("FEATURE_CONCEPT_OMITTED")
        return
    joined = " ".join(terms).casefold()
    groups = _concept_groups(
        constraints.get("search_term_concept_groups"),
        "planning concept groups",
    )
    if not _contains_all_groups(joined, groups):
        events.add("FEATURE_CONCEPT_OMITTED")
    if any(
        token in joined
        for token in (
            "entity_root_",
            "entity_state_",
            "structure_snapshot_",
            ".java",
            "#",
            "(",
            ")",
            "::",
        )
    ):
        events.add("SYMBOL_OR_ENTITY_INVENTED")
    read_authority = source.get("read_authority")
    if not isinstance(read_authority, Mapping) or normalized.get(
        "snapshot"
    ) not in read_authority.get("snapshot_ids", []):
        events.add("SNAPSHOT_CHANGED")


def _draft_events(
    events: set[str],
    normalized: Mapping[str, object],
    expected: Mapping[str, object],
    constraints: Mapping[str, object],
    source: Mapping[str, object],
) -> None:
    if normalized.get("disposition") != expected.get("disposition"):
        events.add("DISPOSITION_CHANGED")
    for field in (
        "step_result_ids",
        "support_digests",
        "gap_code",
        "limitation_codes",
    ):
        if normalized.get(field) != expected.get(field):
            events.add("REFERENCE_SET_CHANGED")
    answer = normalized.get("answer")
    if (
        not isinstance(answer, str)
        or not answer
        or answer != answer.strip()
        or len(answer) > 65_536
    ):
        events.add("ANSWER_CONCEPT_OMITTED")
        return
    folded = answer.casefold()
    groups = _concept_groups(
        constraints.get("answer_concept_groups"),
        "Draft answer concept groups",
    )
    if not _contains_all_groups(folded, groups):
        events.add("ANSWER_CONCEPT_OMITTED")
    if any(
        token in folded
        for token in (
            "source payload",
            "evidence payload",
            "evidence excerpt",
            "源码摘录",
            "证据摘录",
            "```",
            "throw new ",
        )
    ):
        events.add("EVIDENCE_PAYLOAD_EXPANSION")
    order_groups = constraints.get("answer_order_groups")
    if order_groups is not None:
        groups_in_order = _concept_groups(order_groups, "Draft answer order groups")
        if not _groups_appear_in_order(folded, groups_in_order):
            events.add("SOURCE_ORDER_CHANGED")
    assessment = source.get("need_assessment")
    if (
        isinstance(assessment, Mapping)
        and assessment.get("outcome") == "LIMITED"
        and any(token in folded for token in ("#", ".java", "::"))
    ):
        events.add("MODEL_SELECTED_CANDIDATE")


def _review_events(
    events: set[str],
    normalized: Mapping[str, object],
    expected: Mapping[str, object],
    constraints: Mapping[str, object],
    source: Mapping[str, object],
) -> None:
    for field in (
        "checked_need_ids",
        "checked_step_result_ids",
        "checked_support_digests",
    ):
        if normalized.get(field) != expected.get(field):
            events.add("CHECK_SET_CHANGED")
    findings = normalized.get("finding_codes")
    if not isinstance(findings, list) or any(
        not isinstance(item, str)
        or not item
        or item != item.strip()
        or len(item) > 128
        for item in findings
    ) or len(set(findings)) != len(findings):
        events.add("FAULT_OMITTED")
        findings = []
    required = constraints.get("required_finding_codes", [])
    if not isinstance(required, list):
        raise ValueError("required Review findings are invalid")
    decision = normalized.get("decision")
    if required:
        if decision != "REJECT":
            events.add("APPROVED_FAULTY_DRAFT")
        if any(item not in findings for item in required):
            events.add("FAULT_OMITTED")
    else:
        if decision != "APPROVE":
            events.add("REJECTED_CORRECT_DRAFT")
        if findings:
            events.add("APPROVED_WITH_FINDING")
    draft = source.get("draft")
    if not isinstance(draft, Mapping):
        raise ValueError("Review Draft input is invalid")


def _contains_all_groups(text: str, groups: list[list[str]]) -> bool:
    return all(any(term.casefold() in text for term in group) for group in groups)


def _groups_appear_in_order(text: str, groups: list[list[str]]) -> bool:
    """Match one occurrence per concept without being trapped by an earlier alias.

    Natural-language framing may mention an alias before the ordered actions,
    for example ``保存前 ... validate ... persist ... 返回``.  The old first-
    occurrence comparison incorrectly selected that framing occurrence for the
    persist group.  Greedily choosing the earliest occurrence at or after the
    previous matched concept recognizes the real ordered sequence while still
    rejecting an actual reversal.
    """

    cursor = 0
    for group in groups:
        candidates = [
            (position, len(term))
            for term in group
            if (position := text.find(term.casefold(), cursor)) >= 0
        ]
        if not candidates:
            return False
        position, length = min(candidates)
        cursor = position + length
    return True


def _concept_groups(value: object, label: str) -> list[list[str]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} are invalid")
    return [_strings(group, label) for group in value]


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
        review = evaluate(
            _load(Path(arguments.packet)),
            _load(Path(arguments.result)),
        )
        _write_once(Path(arguments.output), review)
        print(
            _canonical(
                {"status": review["conclusion"], "case_id": review["case_id"]}
            ).decode()
        )
        return 0 if review["conclusion"] == "PASS" else 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(_canonical({"status": "ERROR", "message": str(exc)}).decode())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
