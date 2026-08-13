"""Pinned ITER-006 Java proposal suite, oracle, and definition bindings."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from software_world_model.ai_infrastructure import (
    JAVA_WORLD_MODEL_ANSWER_PROMPT_REF,
    JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
    JAVA_WORLD_MODEL_PROPOSAL_VOCABULARY_REF,
    WorldModelEvaluationCase,
    WorldModelEvaluationRole,
    create_java_world_model_evaluation_definition,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of


SUITE_SCHEMA = "swm.iter-006.java-world-model-capability-suite@1"
ORACLE_SCHEMA = "swm.iter-006.java-world-model-capability-oracle@1"
PINNED_SUITE_REF = "ITER-006-JAVA-WORLD-MODEL-CAPABILITY-SUITE@1.1.0"
PINNED_ORACLE_REF = "ITER-006-JAVA-WORLD-MODEL-CAPABILITY-ORACLE@1.1.0"
PINNED_SUITE_FILE_DIGEST = (
    "sha256:93be2f872fe8531d09ca220b67aa493d8f929cbca1b27309b2d05775684d6716"
)
PINNED_ORACLE_FILE_DIGEST = (
    "sha256:0d563879c5bf53606082d669b9f5650c7a07c7fb2f59d96d741c7a0cf84facb7"
)
PINNED_REQUIRED_CASE_IDS = (
    "WM-JAVA-CE-REQ-001",
    "WM-JAVA-CE-PLAN-METHOD-002",
    "WM-JAVA-CE-PLAN-PATH-003",
    "WM-JAVA-CE-NEGATIVE-004",
    "WM-JAVA-CE-GAP-005",
    "WM-JAVA-CE-DIFF-006",
    "WM-JAVA-CE-REVIEW-007",
    "WM-JAVA-CE-RESOLVE-008",
)
ROOT = Path(__file__).resolve().parent
DEFAULT_SUITE_PATH = ROOT / "suite-1.1.0.json"
DEFAULT_ORACLE_PATH = ROOT / "oracle-1.1.0.json"


def load_capability_inputs(
    suite_path: str | Path = DEFAULT_SUITE_PATH,
    oracle_path: str | Path = DEFAULT_ORACLE_PATH,
) -> tuple[dict[str, object], dict[str, object]]:
    suite = _load_pinned(
        Path(suite_path), PINNED_SUITE_FILE_DIGEST, "Java capability suite"
    )
    oracle = _load_pinned(
        Path(oracle_path), PINNED_ORACLE_FILE_DIGEST, "Java capability oracle"
    )
    verify_capability_inputs(suite, oracle)
    return suite, oracle


def verify_capability_inputs(suite: object, oracle: object) -> None:
    if not isinstance(suite, Mapping) or set(suite) != {
        "schema",
        "suite_ref",
        "purpose",
        "proposal_contract",
        "closed_evaluation_protocol",
        "cases",
    }:
        _invalid("Java capability suite shape is invalid")
    if (
        suite.get("schema") != SUITE_SCHEMA
        or suite.get("suite_ref") != PINNED_SUITE_REF
    ):
        _invalid("Java capability suite identity is invalid")
    expected_contract = {
        "capability_contract_version": (
            JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.capability_contract_version
        ),
        "strategy_ref": JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.strategy_ref,
        "prompt_ref": JAVA_WORLD_MODEL_ANSWER_PROMPT_REF,
        "proposal_vocabulary_ref": JAVA_WORLD_MODEL_PROPOSAL_VOCABULARY_REF,
        "available_operations": list(
            JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
        ),
    }
    if suite.get("proposal_contract") != expected_contract:
        _invalid("Java capability suite proposal contract drifted")
    protocol = suite.get("closed_evaluation_protocol")
    if (
        not isinstance(protocol, Mapping)
        or tuple(protocol.get("required_case_ids", ())) != PINNED_REQUIRED_CASE_IDS
        or protocol.get("provider_calls_per_case") != 1
        or protocol.get("hidden_retry_count") != 0
        or protocol.get("case_rule")
        != "PASS_IFF_PROJECTION_EXACT_AND_NO_FORBIDDEN_EVENT_OTHERWISE_FAIL"
        or protocol.get("result_rule")
        != "CLOSED_PASS_IFF_ALL_EIGHT_REQUIRED_CASES_PASS_AND_FAILURE_COUNT_ZERO_AND_UNKNOWN_COUNT_ZERO"
    ):
        _invalid("Java capability closed protocol drifted")

    cases = suite.get("cases")
    if not isinstance(cases, list) or len(cases) != 8:
        _invalid("Java capability suite must contain eight cases")
    case_ids: list[str] = []
    roles: list[WorldModelEvaluationRole] = []
    for case in cases:
        if not isinstance(case, Mapping):
            _invalid("Java capability suite case is invalid")
        required = {"case_id", "capability", "input", "projection_fields"}
        if not required.issubset(case) or not set(case).issubset(
            required | {"available_operations"}
        ):
            _invalid("Java capability suite case fields are invalid")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id.startswith("WM-JAVA-CE-"):
            _invalid("Java capability case ID is invalid")
        try:
            role = WorldModelEvaluationRole(case.get("capability"))
        except (TypeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "Java capability role is invalid",
            ) from exc
        fields = _strings(case.get("projection_fields"), "projection fields")
        if len(fields) != len(set(fields)):
            _invalid("Java capability projection fields are duplicated")
        operations = case.get("available_operations")
        if role is WorldModelEvaluationRole.GENERIC_QUERY_PLANNING:
            if operations != list(
                JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
            ):
                _invalid("Java planning case operation vocabulary drifted")
        elif operations is not None:
            _invalid("non-planning Java capability case declares operations")
        case_ids.append(case_id)
        roles.append(role)
    if tuple(case_ids) != PINNED_REQUIRED_CASE_IDS:
        _invalid("Java capability suite cases are missing or reordered")
    if set(roles) != set(WorldModelEvaluationRole):
        _invalid("Java capability suite does not cover all seven roles")
    if roles.count(WorldModelEvaluationRole.GENERIC_QUERY_PLANNING) != 2:
        _invalid("Java capability suite must contain both planning cases")

    if not isinstance(oracle, Mapping) or set(oracle) != {
        "schema",
        "oracle_ref",
        "suite_ref",
        "cases",
    }:
        _invalid("Java capability oracle shape is invalid")
    if (
        oracle.get("schema") != ORACLE_SCHEMA
        or oracle.get("oracle_ref") != PINNED_ORACLE_REF
        or oracle.get("suite_ref") != PINNED_SUITE_REF
    ):
        _invalid("Java capability oracle identity is invalid")
    oracle_cases = oracle.get("cases")
    if not isinstance(oracle_cases, list) or len(oracle_cases) != 8:
        _invalid("Java capability oracle must contain eight cases")
    for case, expected in zip(cases, oracle_cases):
        if not isinstance(expected, Mapping) or set(expected) != {
            "case_id",
            "expected_normalized_result",
            "forbidden_events",
        }:
            _invalid("Java capability oracle case shape is invalid")
        if expected.get("case_id") != case.get("case_id"):
            _invalid("Java capability oracle case order differs from suite")
        projection = expected.get("expected_normalized_result")
        if (
            not isinstance(projection, Mapping)
            or set(projection) != set(case["projection_fields"])
        ):
            _invalid("Java capability expected projection is invalid")
        _strings(expected.get("forbidden_events"), "forbidden events")


def sealed_case_input(case: Mapping[str, object]) -> dict[str, object]:
    value: dict[str, object] = {"input": case["input"]}
    if "available_operations" in case:
        value["available_operations"] = list(case["available_operations"])
    return value


def case_fixture_digest(case: Mapping[str, object]) -> Digest:
    return digest_of(
        {
            "case_id": case["case_id"],
            "capability": case["capability"],
            "sealed_input": sealed_case_input(case),
        }
    )


def case_oracle_digest(oracle_case: Mapping[str, object]) -> Digest:
    return digest_of(
        {
            "case_id": oracle_case["case_id"],
            "expected_normalized_result": oracle_case[
                "expected_normalized_result"
            ],
            "forbidden_events": oracle_case["forbidden_events"],
        }
    )


def build_evaluation_definition(
    suite: Mapping[str, object],
    oracle: Mapping[str, object],
    *,
    conformance_result_ref: str,
    provider_configuration_fingerprint: Digest,
    actual_model_fingerprint: str,
    adapter_version: str,
    exact_candidate_checkpoint_ref: str,
    environment_ref: str,
    reference_strategy_ref: str,
    resource_policy_ref: str,
    valid_for_seconds: int,
):
    verify_capability_inputs(suite, oracle)
    raw_cases = suite["cases"]
    oracle_cases = oracle["cases"]
    assert isinstance(raw_cases, list) and isinstance(oracle_cases, list)
    cases = tuple(
        WorldModelEvaluationCase(
            role=WorldModelEvaluationRole(case["capability"]),
            case_id=str(case["case_id"]),
            case_version="1.1.0",
            fixture_ref=f"{PINNED_SUITE_REF}:fixture:{case['case_id']}",
            fixture_digest=case_fixture_digest(case),
            oracle_ref=f"{PINNED_ORACLE_REF}:case:{case['case_id']}",
            oracle_digest=case_oracle_digest(oracle_case),
        )
        for case, oracle_case in zip(raw_cases, oracle_cases)
    )
    return create_java_world_model_evaluation_definition(
        evaluation_version="1.1.0",
        conformance_result_ref=conformance_result_ref,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        model_ref=actual_model_fingerprint,
        adapter_version=adapter_version,
        exact_candidate_checkpoint_ref=exact_candidate_checkpoint_ref,
        environment_ref=environment_ref,
        reference_strategy_ref=reference_strategy_ref,
        resource_policy_ref=resource_policy_ref,
        cases=cases,
        valid_for_seconds=valid_for_seconds,
    )


def case_pairs(
    suite: Mapping[str, object], oracle: Mapping[str, object]
) -> tuple[tuple[Mapping[str, object], Mapping[str, object]], ...]:
    verify_capability_inputs(suite, oracle)
    cases = suite["cases"]
    oracle_cases = oracle["cases"]
    assert isinstance(cases, list) and isinstance(oracle_cases, list)
    return tuple(zip(cases, oracle_cases))


def _load_pinned(path: Path, expected_digest: str, label: str) -> dict[str, object]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw, object_pairs_hook=_unique_object)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            f"{label} cannot be loaded",
        ) from exc
    actual = "sha256:" + hashlib.sha256(raw).hexdigest()
    if actual != expected_digest or not isinstance(value, dict):
        _invalid(f"{label} digest or root shape is invalid")
    return value


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value: dict[str, object] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def _strings(value: object, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
    ):
        _invalid(f"Java capability {label} are invalid")
    return value


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.EVALUATION_DEFINITION_INVALID, message)


__all__ = [
    "DEFAULT_ORACLE_PATH",
    "DEFAULT_SUITE_PATH",
    "PINNED_ORACLE_FILE_DIGEST",
    "PINNED_ORACLE_REF",
    "PINNED_REQUIRED_CASE_IDS",
    "PINNED_SUITE_FILE_DIGEST",
    "PINNED_SUITE_REF",
    "build_evaluation_definition",
    "case_fixture_digest",
    "case_oracle_digest",
    "case_pairs",
    "load_capability_inputs",
    "sealed_case_input",
    "verify_capability_inputs",
]
