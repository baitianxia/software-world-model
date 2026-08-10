"""Frozen V-009 suite and evaluation-definition bindings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from software_world_model.ai_infrastructure import (
    WorldModelEvaluationCase,
    WorldModelEvaluationRole,
    create_world_model_evaluation_definition,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SUITE_PATH = (
    REPOSITORY_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "questions"
    / "capability-suite-1.0.0.json"
)
PINNED_SUITE_REF = "ITER-003-WORLD-MODEL-CAPABILITY-SUITE@1.0.0"
PINNED_SUITE_FILE_DIGEST = (
    "sha256:b9118d83aa40e58ade6e3c947ea86d1d6d73ebd50d3b1ae0797d5caa7e415ad6"
)
PINNED_REQUIRED_CASE_IDS = (
    "WM-CE-REQ-001",
    "WM-CE-PLAN-002",
    "WM-CE-NEGATIVE-003",
    "WM-CE-GAP-004",
    "WM-CE-DIFF-005",
    "WM-CE-REVIEW-006",
    "WM-CE-RESOLVE-007",
)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_capability_suite(path: str | Path = DEFAULT_SUITE_PATH) -> dict[str, object]:
    source = Path(path)
    try:
        encoded = source.read_bytes()
        value = json.loads(encoded, object_pairs_hook=_unique_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            "ITER-003 world-model capability suite cannot be loaded",
        ) from exc
    if not isinstance(value, dict):
        _invalid("world-model capability suite must contain one object")
    actual = "sha256:" + hashlib.sha256(encoded).hexdigest()
    if actual != PINNED_SUITE_FILE_DIGEST:
        _invalid("world-model capability suite file digest drifted")
    verify_capability_suite(value)
    return value


def verify_capability_suite(suite: object) -> None:
    if not isinstance(suite, Mapping):
        _invalid("world-model capability suite must be an object")
    if set(suite) != {
        "suite_ref",
        "purpose",
        "must_not_include_product_case_ids",
        "closed_evaluation_protocol",
        "cases",
    }:
        _invalid("world-model capability suite fields are invalid")
    if suite.get("suite_ref") != PINNED_SUITE_REF:
        _invalid("world-model capability suite reference is invalid")
    protocol = suite.get("closed_evaluation_protocol")
    if not isinstance(protocol, Mapping):
        _invalid("world-model capability protocol is invalid")
    if tuple(protocol.get("required_case_ids", ())) != PINNED_REQUIRED_CASE_IDS:
        _invalid("world-model capability required case order is invalid")
    if protocol.get("case_rule") != "PASS_IFF_PROJECTION_EXACT_AND_NO_FORBIDDEN_EVENT_OTHERWISE_FAIL":
        _invalid("world-model capability exact case rule drifted")
    if protocol.get("result_rule") != "CLOSED_PASS_IFF_EVERY_REQUIRED_CASE_PASS_AND_FAILURE_COUNT_ZERO_AND_UNKNOWN_COUNT_ZERO":
        _invalid("world-model capability closed result rule drifted")
    cases = suite.get("cases")
    if not isinstance(cases, list) or len(cases) != len(PINNED_REQUIRED_CASE_IDS):
        _invalid("world-model capability case count is invalid")
    case_ids: list[str] = []
    roles: list[WorldModelEvaluationRole] = []
    for case in cases:
        if not isinstance(case, Mapping):
            _invalid("world-model capability case is invalid")
        required = {
            "case_id",
            "capability",
            "input",
            "projection_fields",
            "expected_normalized_result",
            "forbidden_events",
        }
        allowed = required | {"available_operations"}
        if not required.issubset(case) or not set(case).issubset(allowed):
            _invalid("world-model capability case fields are invalid")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            _invalid("world-model capability case ID is invalid")
        try:
            role = WorldModelEvaluationRole(case.get("capability"))
        except (TypeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "world-model capability role is invalid",
            ) from exc
        projection_fields = case.get("projection_fields")
        expected = case.get("expected_normalized_result")
        forbidden = case.get("forbidden_events")
        if (
            not isinstance(projection_fields, list)
            or not projection_fields
            or any(not isinstance(item, str) or not item for item in projection_fields)
            or len(set(projection_fields)) != len(projection_fields)
            or not isinstance(expected, Mapping)
            or set(expected) != set(projection_fields)
            or not isinstance(forbidden, list)
            or not forbidden
            or any(not isinstance(item, str) or not item for item in forbidden)
        ):
            _invalid("world-model capability case oracle is invalid")
        operations = case.get("available_operations", [])
        if (
            not isinstance(operations, list)
            or any(not isinstance(item, str) or not item for item in operations)
            or len(set(operations)) != len(operations)
        ):
            _invalid("world-model available operations are invalid")
        case_ids.append(case_id)
        roles.append(role)
    if tuple(case_ids) != PINNED_REQUIRED_CASE_IDS:
        _invalid("world-model capability cases are missing or reordered")
    if set(roles) != set(WorldModelEvaluationRole):
        _invalid("world-model capability role coverage is incomplete")
    product_ids = suite.get("must_not_include_product_case_ids")
    if not isinstance(product_ids, list) or set(case_ids) & set(product_ids):
        _invalid("world-model capability suite overlaps the product suite")


def sealed_case_input(case: Mapping[str, object]) -> dict[str, object]:
    value = {
        "input": case["input"],
        "available_operations": list(case.get("available_operations", [])),
    }
    return value


def case_fixture_digest(case: Mapping[str, object]) -> Digest:
    return digest_of(
        {
            "case_id": case["case_id"],
            "capability": case["capability"],
            "sealed_input": sealed_case_input(case),
        }
    )


def case_oracle_digest(case: Mapping[str, object]) -> Digest:
    return digest_of(
        {
            "projection_fields": case["projection_fields"],
            "expected_normalized_result": case["expected_normalized_result"],
            "forbidden_events": case["forbidden_events"],
        }
    )


def build_evaluation_definition(
    suite: Mapping[str, object],
    *,
    conformance_result_ref: str,
    provider_configuration_fingerprint: Digest,
    actual_model_fingerprint: str,
    adapter_version: str,
    exact_g3a_checkpoint_ref: str,
    environment_ref: str,
    reference_strategy_ref: str,
    resource_policy_ref: str,
    valid_for_seconds: int,
):
    verify_capability_suite(suite)
    raw_cases = suite["cases"]
    assert isinstance(raw_cases, list)
    cases = tuple(
        WorldModelEvaluationCase(
            role=WorldModelEvaluationRole(case["capability"]),
            case_id=case["case_id"],
            case_version="1.0.0",
            fixture_ref=f"{PINNED_SUITE_REF}:fixture:{case['case_id']}",
            fixture_digest=case_fixture_digest(case),
            oracle_ref=f"{PINNED_SUITE_REF}:oracle:{case['case_id']}",
            oracle_digest=case_oracle_digest(case),
        )
        for case in raw_cases
    )
    return create_world_model_evaluation_definition(
        evaluation_version="1.0.0",
        conformance_result_ref=conformance_result_ref,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        model_ref=actual_model_fingerprint,
        adapter_version=adapter_version,
        exact_g3a_checkpoint_ref=exact_g3a_checkpoint_ref,
        environment_ref=environment_ref,
        reference_strategy_ref=reference_strategy_ref,
        resource_policy_ref=resource_policy_ref,
        cases=cases,
        valid_for_seconds=valid_for_seconds,
    )


def case_by_id(suite: Mapping[str, object], case_id: str) -> Mapping[str, object]:
    verify_capability_suite(suite)
    cases = suite["cases"]
    assert isinstance(cases, list)
    value = next((item for item in cases if item["case_id"] == case_id), None)
    if value is None:
        _invalid("world-model capability case is not registered")
    return value


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.EVALUATION_DEFINITION_INVALID, message)


__all__ = [
    "DEFAULT_SUITE_PATH",
    "PINNED_REQUIRED_CASE_IDS",
    "PINNED_SUITE_FILE_DIGEST",
    "PINNED_SUITE_REF",
    "build_evaluation_definition",
    "case_by_id",
    "case_fixture_digest",
    "case_oracle_digest",
    "load_capability_suite",
    "sealed_case_input",
    "verify_capability_suite",
]
