"""Pinned ITER-007 Java source-semantics capability inputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

from software_world_model.ai_infrastructure import (
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    JavaSourceSemanticsWorldModelEvaluationCase,
    JavaSourceSemanticsWorldModelEvaluationRole,
    create_java_source_semantics_world_model_evaluation_definition,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    digest_of,
)


SUITE_SCHEMA = "swm.iter-007.java-source-semantics-capability-suite@1"
ORACLE_SCHEMA = "swm.iter-007.java-source-semantics-capability-oracle@1"
PINNED_SUITE_REF = (
    "ITER-007-JAVA-SOURCE-SEMANTICS-CAPABILITY-SUITE@1.2.2"
)
PINNED_ORACLE_REF = (
    "ITER-007-JAVA-SOURCE-SEMANTICS-CAPABILITY-ORACLE@1.2.2"
)
PINNED_SUITE_FILE_DIGEST = (
    "sha256:f6a38dc1357dfdb895d6ad02121705190f5fad32c869862c131e08633c170965"
)
PINNED_ORACLE_FILE_DIGEST = (
    "sha256:e07d06639b39f7daf05a5c8e8728f79a0028c155eeb6016dfac46317d47abe56"
)
PINNED_REQUIRED_CASE_IDS = (
    "WM-JSS-CE-PLAN-ZH-001",
    "WM-JSS-CE-PLAN-EN-002",
    "WM-JSS-CE-PLAN-ORDER-003",
    "WM-JSS-CE-PLAN-BOUNDARY-004",
    "WM-JSS-CE-DRAFT-SUPPORTED-005",
    "WM-JSS-CE-DRAFT-GAP-006",
    "WM-JSS-CE-DRAFT-LIMITATION-007",
    "WM-JSS-CE-DRAFT-DIRECTION-008",
    "WM-JSS-CE-REVIEW-APPROVE-009",
    "WM-JSS-CE-REVIEW-OMISSION-010",
    "WM-JSS-CE-REVIEW-UNSUPPORTED-011",
    "WM-JSS-CE-REVIEW-PAYLOAD-012",
)
ROOT = Path(__file__).resolve().parent
DEFAULT_SUITE_PATH = ROOT / "suite-1.2.2.json"
DEFAULT_ORACLE_PATH = ROOT / "oracle-1.2.2.json"


def load_capability_inputs(
    suite_path: str | Path = DEFAULT_SUITE_PATH,
    oracle_path: str | Path = DEFAULT_ORACLE_PATH,
) -> tuple[dict[str, object], dict[str, object]]:
    suite = _load_pinned(
        Path(suite_path),
        PINNED_SUITE_FILE_DIGEST,
        "Java source-semantics capability suite",
    )
    oracle = _load_pinned(
        Path(oracle_path),
        PINNED_ORACLE_FILE_DIGEST,
        "Java source-semantics capability oracle",
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
        _invalid("Java source-semantics capability suite shape is invalid")
    if (
        suite.get("schema") != SUITE_SCHEMA
        or suite.get("suite_ref") != PINNED_SUITE_REF
    ):
        _invalid("Java source-semantics capability suite identity is invalid")
    contract = JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
    if suite.get("proposal_contract") != {
        "capability_contract_version": contract.capability_contract_version,
        "strategy_ref": contract.strategy_ref,
        "prompt_ref": contract.prompt_ref,
        "proposal_vocabulary_ref": contract.proposal_vocabulary_ref,
        "available_operations": list(contract.available_operations),
    }:
        _invalid("Java source-semantics proposal contract drifted")
    protocol = suite.get("closed_evaluation_protocol")
    if (
        not isinstance(protocol, Mapping)
        or tuple(protocol.get("required_case_ids", ()))
        != PINNED_REQUIRED_CASE_IDS
        or protocol.get("provider_calls_per_case") != 1
        or protocol.get("hidden_retry_count") != 0
        or protocol.get("case_rule")
        != (
            "PASS_IFF_CONTRACT_FIELDS_EXACT_SEMANTIC_CONSTRAINTS_PASS_"
            "AND_NO_FORBIDDEN_EVENT_OTHERWISE_FAIL"
        )
        or protocol.get("result_rule")
        != (
            "CLOSED_PASS_IFF_ALL_TWELVE_REQUIRED_CASES_PASS_AND_"
            "FAILURE_COUNT_ZERO_AND_UNKNOWN_COUNT_ZERO"
        )
    ):
        _invalid("Java source-semantics closed protocol drifted")

    cases = suite.get("cases")
    if not isinstance(cases, list) or len(cases) != 12:
        _invalid("Java source-semantics suite must contain twelve cases")
    case_ids: list[str] = []
    roles: list[JavaSourceSemanticsWorldModelEvaluationRole] = []
    for case in cases:
        if not isinstance(case, Mapping) or set(case) - {
            "case_id",
            "capability",
            "available_operations",
            "input",
            "projection_fields",
            "semantic_constraints",
        }:
            _invalid("Java source-semantics suite case fields are invalid")
        if not {
            "case_id",
            "capability",
            "input",
            "projection_fields",
            "semantic_constraints",
        }.issubset(case):
            _invalid("Java source-semantics suite case is incomplete")
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id.startswith("WM-JSS-CE-"):
            _invalid("Java source-semantics case ID is invalid")
        try:
            role = JavaSourceSemanticsWorldModelEvaluationRole(
                case.get("capability")
            )
        except (TypeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "Java source-semantics capability role is invalid",
            ) from exc
        fields = _strings(case.get("projection_fields"), "projection fields")
        if len(fields) != len(set(fields)):
            _invalid("Java source-semantics projection fields are duplicated")
        constraints = case.get("semantic_constraints")
        if not isinstance(constraints, Mapping):
            _invalid("Java source-semantics constraints are invalid")
        operations = case.get("available_operations")
        if role is JavaSourceSemanticsWorldModelEvaluationRole.IMPLEMENTATION_QUERY_PLANNING:
            if operations != list(contract.available_operations):
                _invalid("Java source-semantics planning vocabulary drifted")
            if set(constraints) != {"search_term_concept_groups"}:
                _invalid("Java source-semantics planning constraints drifted")
            _concept_groups(
                constraints.get("search_term_concept_groups"),
                "planning concept groups",
            )
        elif operations is not None:
            _invalid("non-planning source-semantics case declares operations")
        elif role is JavaSourceSemanticsWorldModelEvaluationRole.IMPLEMENTATION_ANSWER_DRAFTING:
            if set(constraints) - {
                "answer_concept_groups",
                "answer_order_groups",
            } or "answer_concept_groups" not in constraints:
                _invalid("Java source-semantics Draft constraints drifted")
            _concept_groups(
                constraints.get("answer_concept_groups"),
                "Draft answer concept groups",
            )
            if "answer_order_groups" in constraints:
                _concept_groups(
                    constraints["answer_order_groups"],
                    "Draft answer order groups",
                )
        else:
            if set(constraints) - {"required_finding_codes"}:
                _invalid("Java source-semantics Review constraints drifted")
            if "required_finding_codes" in constraints:
                _strings(
                    constraints["required_finding_codes"],
                    "required Review finding codes",
                )
        case_ids.append(case_id)
        roles.append(role)
    if tuple(case_ids) != PINNED_REQUIRED_CASE_IDS:
        _invalid("Java source-semantics cases are missing or reordered")
    if any(roles.count(role) != 4 for role in type(roles[0])):
        _invalid("Java source-semantics suite must contain four cases per role")

    if not isinstance(oracle, Mapping) or set(oracle) != {
        "schema",
        "oracle_ref",
        "suite_ref",
        "cases",
    }:
        _invalid("Java source-semantics oracle shape is invalid")
    if (
        oracle.get("schema") != ORACLE_SCHEMA
        or oracle.get("oracle_ref") != PINNED_ORACLE_REF
        or oracle.get("suite_ref") != PINNED_SUITE_REF
    ):
        _invalid("Java source-semantics oracle identity is invalid")
    oracle_cases = oracle.get("cases")
    if not isinstance(oracle_cases, list) or len(oracle_cases) != 12:
        _invalid("Java source-semantics oracle must contain twelve cases")
    for case, expected in zip(cases, oracle_cases):
        if not isinstance(expected, Mapping) or set(expected) != {
            "case_id",
            "expected_normalized_result",
            "forbidden_events",
        }:
            _invalid("Java source-semantics oracle case shape is invalid")
        if expected.get("case_id") != case.get("case_id"):
            _invalid("Java source-semantics oracle case order differs")
        projection = expected.get("expected_normalized_result")
        if (
            not isinstance(projection, Mapping)
            or set(projection) != set(case["projection_fields"])
        ):
            _invalid("Java source-semantics expected projection is invalid")
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


def case_oracle_digest(
    case: Mapping[str, object], oracle_case: Mapping[str, object]
) -> Digest:
    return digest_of(
        {
            "case_id": oracle_case["case_id"],
            "semantic_constraints": case["semantic_constraints"],
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
        JavaSourceSemanticsWorldModelEvaluationCase(
            role=JavaSourceSemanticsWorldModelEvaluationRole(
                case["capability"]
            ),
            case_id=str(case["case_id"]),
            case_version="1.2.2",
            fixture_ref=f"{PINNED_SUITE_REF}:fixture:{case['case_id']}",
            fixture_digest=case_fixture_digest(case),
            oracle_ref=f"{PINNED_ORACLE_REF}:case:{case['case_id']}",
            oracle_digest=case_oracle_digest(case, oracle_case),
        )
        for case, oracle_case in zip(raw_cases, oracle_cases)
    )
    return create_java_source_semantics_world_model_evaluation_definition(
        evaluation_version="1.2.2",
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
        _invalid(f"Java source-semantics capability {label} are invalid")
    return value


def _concept_groups(value: object, label: str) -> list[list[str]]:
    if not isinstance(value, list) or not value:
        _invalid(f"Java source-semantics {label} are invalid")
    groups: list[list[str]] = []
    for group in value:
        groups.append(_strings(group, label))
    return groups


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
