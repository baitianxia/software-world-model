"""Pinned ITER-008 bounded Java source-semantics capability inputs."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Mapping

from software_world_model.ai_infrastructure import (
    BoundedJavaSourceSemanticsWorldModelEvaluationCase,
    BoundedJavaSourceSemanticsWorldModelEvaluationRole,
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT,
    create_bounded_java_source_semantics_world_model_evaluation_definition,
)
from software_world_model.ai_infrastructure.bounded_java_source_semantics_model_egress_qualification import (
    BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS,
)
from software_world_model.cross_cutting import (
    Digest,
    DomainError,
    ErrorCode,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.application_services.bounded_world_model_investigation import (
    constrained_investigation_operations,
    normalize_investigation_evidence_requests,
)


SUITE_SCHEMA = "swm.iter-008.bounded-java-source-semantics-capability-suite@1"
ORACLE_SCHEMA = "swm.iter-008.bounded-java-source-semantics-capability-oracle@1"
PINNED_SUITE_REF = (
    "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-CAPABILITY-SUITE@1.5.2"
)
PINNED_ORACLE_REF = (
    "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-CAPABILITY-ORACLE@1.5.2"
)
PINNED_SUITE_FILE_DIGEST = (
    "sha256:a245d3ebb16be26e1df6a2ed22143c562e2c14206959383f1d958c9cce5fd859"
)
PINNED_ORACLE_FILE_DIGEST = (
    "sha256:df5d06c87b00ba151719163e36b05fd1dbebd0cf85dc5b5776e801218b0aa903"
)
PINNED_REQUIRED_CASE_CALLS = (
    BOUNDED_JAVA_SOURCE_SEMANTICS_QUALIFICATION_CASE_CALLS
)
PINNED_REQUIRED_CASE_IDS = tuple(
    case_id for case_id, _ in PINNED_REQUIRED_CASE_CALLS
)
PINNED_PROVIDER_REQUEST_COUNT = sum(
    count for _, count in PINNED_REQUIRED_CASE_CALLS
)
ROOT = Path(__file__).resolve().parent
DEFAULT_SUITE_PATH = ROOT / "suite-1.5.2.json"
DEFAULT_ORACLE_PATH = ROOT / "oracle-1.5.2.json"

_INVESTIGATION_FIELDS = (
    "step_index",
    "trace_digest",
    "operation",
    "snapshot_id",
    "search_terms",
    "limit",
    "candidate_result_id",
    "candidate_result_digest",
    "method_refs",
    "entity_refs",
    "direction",
    "predicate",
    "max_depth",
    "max_paths",
    "max_expansions",
    "finish_reason",
    "evidence_requests",
)
_INVESTIGATION_STEP_FIELDS = {
    "step_index",
    "trace_digest",
    "previous_result_ref",
    "progress_receipt",
    "remaining_budget",
    "projection_ref",
    "semantic_constraints",
}
_TERMINAL_STEP_FIELDS = {
    "sealed_input",
    "projection_ref",
    "semantic_constraints",
}
_COMMON_FORBIDDEN_EVENTS = {
    "SOURCE_ACCESS",
    "EVIDENCE_PAYLOAD_ACCESS",
    "ORACLE_ACCESS",
    "HIDDEN_RETRY",
}


def load_capability_inputs(
    suite_path: str | Path = DEFAULT_SUITE_PATH,
    oracle_path: str | Path = DEFAULT_ORACLE_PATH,
) -> tuple[dict[str, object], dict[str, object]]:
    suite = _load_pinned(
        Path(suite_path),
        PINNED_SUITE_FILE_DIGEST,
        "bounded Java source-semantics capability suite",
    )
    oracle = _load_pinned(
        Path(oracle_path),
        PINNED_ORACLE_FILE_DIGEST,
        "bounded Java source-semantics capability oracle",
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
        "synthetic_authority",
        "sealed_result_fixtures",
        "projection_sets",
        "cases",
    }:
        _invalid("bounded capability suite shape is invalid")
    if (
        suite.get("schema") != SUITE_SCHEMA
        or suite.get("suite_ref") != PINNED_SUITE_REF
        or not isinstance(suite.get("purpose"), str)
        or not suite["purpose"]
    ):
        _invalid("bounded capability suite identity is invalid")
    contract = JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT
    if suite.get("proposal_contract") != {
        "capability_contract_version": contract.capability_contract_version,
        "strategy_ref": contract.strategy_ref,
        "prompt_ref": contract.prompt_ref,
        "proposal_vocabulary_ref": contract.proposal_vocabulary_ref,
        "available_operations": list(contract.available_operations),
    }:
        _invalid("bounded proposal contract drifted")
    protocol = suite.get("closed_evaluation_protocol")
    if not isinstance(protocol, Mapping):
        _invalid("bounded closed evaluation protocol is invalid")
    required_calls = protocol.get("required_case_calls")
    if (
        protocol.get("protocol_ref")
        != "ITER-008-BOUNDED-JAVA-SOURCE-SEMANTICS-CE-CLOSED@1.0.2"
        or protocol.get("hidden_retry_count") != 0
        or protocol.get("planned_provider_call_count")
        != PINNED_PROVIDER_REQUEST_COUNT
        or not isinstance(required_calls, list)
        or tuple(
            (item[0], item[1])
            for item in required_calls
            if isinstance(item, list) and len(item) == 2
        )
        != PINNED_REQUIRED_CASE_CALLS
        or len(required_calls) != len(PINNED_REQUIRED_CASE_CALLS)
        or protocol.get("case_rule")
        != (
            "PASS_IFF_EVERY_CALL_HAS_EXACT_INPUT_RESULT_TRACE_EVIDENCE_"
            "CONTRACT_PROJECTION_IN_THE_FROZEN_ACCEPTED_SET_AND_SEMANTIC_"
            "CONSTRAINTS_PASS_AND_NO_FORBIDDEN_EVENT"
        )
        or protocol.get("result_rule")
        != (
            "CLOSED_PASS_IFF_ALL_EIGHTEEN_REQUIRED_CASES_PASS_AND_"
            "FAILURE_COUNT_ZERO_AND_UNKNOWN_COUNT_ZERO_AND_PROVIDER_"
            "REQUEST_COUNT_FORTY"
        )
    ):
        _invalid("bounded closed evaluation protocol drifted")
    authority = suite.get("synthetic_authority")
    fixtures = suite.get("sealed_result_fixtures")
    projections = suite.get("projection_sets")
    if (
        not isinstance(authority, Mapping)
        or set(authority)
        != {"need_key", "profile_ref", "snapshot_id", "read_authority"}
        or authority.get("profile_ref") != "JAVA_SOURCE_SEMANTICS@1"
        or not isinstance(fixtures, Mapping)
        or set(fixtures)
        != {
            "three_candidates",
            "zero_candidates_recall_unknown",
            "zero_candidates_complete",
            "zero_candidates_query_unknown",
            "zero_candidates_representation_unknown",
            "method_batch_complete",
            "declaring_type_neighborhood",
            "direct_calls_complete",
            "declared_inventory_complete",
        }
        or not isinstance(projections, Mapping)
        or set(projections) != {"investigation", "draft", "review"}
    ):
        _invalid("bounded synthetic authority or fixture catalog is invalid")
    for name, fields in projections.items():
        values = _strings(fields, f"{name} projection fields")
        if len(values) != len(set(values)):
            _invalid("bounded projection fields are duplicated")
    if tuple(projections["investigation"]) != tuple(
        field
        for field in _INVESTIGATION_FIELDS
        if field not in {"search_terms", "finish_reason"}
    ):
        _invalid("bounded investigation projection drifted")

    cases = suite.get("cases")
    if not isinstance(cases, list) or len(cases) != 18:
        _invalid("bounded capability suite must contain eighteen cases")
    expected_counts = dict(PINNED_REQUIRED_CASE_CALLS)
    case_ids: list[str] = []
    role_counts = {
        "IMPLEMENTATION_INVESTIGATION": 0,
        "IMPLEMENTATION_ANSWER_DRAFTING": 0,
        "IMPLEMENTATION_ANSWER_REVIEW": 0,
    }
    for case in cases:
        if not isinstance(case, Mapping):
            _invalid("bounded capability case is invalid")
        case_id = case.get("case_id")
        capability = case.get("capability")
        if (
            not isinstance(case_id, str)
            or case_id not in expected_counts
            or case_id in case_ids
            or capability not in role_counts
        ):
            _invalid("bounded case identity or capability is invalid")
        expected_fields = (
            {
                "case_id",
                "capability",
                "original_question",
                "response_language",
                "evidence_requests",
                "steps",
            }
            if capability == "IMPLEMENTATION_INVESTIGATION"
            else {"case_id", "capability", "steps"}
        )
        if set(case) != expected_fields:
            _invalid("bounded capability case shape is invalid")
        if capability == "IMPLEMENTATION_INVESTIGATION":
            normalized_evidence = normalize_investigation_evidence_requests(
                case.get("evidence_requests")
            )
            if list(normalized_evidence) != case.get("evidence_requests"):
                _invalid("bounded capability evidence requests are not canonical")
        steps = case.get("steps")
        if not isinstance(steps, list) or len(steps) != expected_counts[case_id]:
            _invalid("bounded capability case call count is invalid")
        traces: list[str] = []
        for step in steps:
            if not isinstance(step, Mapping):
                _invalid("bounded capability step is invalid")
            expected_step_fields = (
                _INVESTIGATION_STEP_FIELDS
                if capability == "IMPLEMENTATION_INVESTIGATION"
                else _TERMINAL_STEP_FIELDS
            )
            if set(step) != expected_step_fields:
                _invalid("bounded capability step shape is invalid")
            projection_ref = step.get("projection_ref")
            expected_projection = (
                "investigation"
                if capability == "IMPLEMENTATION_INVESTIGATION"
                else "draft"
                if capability == "IMPLEMENTATION_ANSWER_DRAFTING"
                else "review"
            )
            if projection_ref != expected_projection:
                _invalid("bounded capability step projection is invalid")
            constraints = step.get("semantic_constraints")
            if not isinstance(constraints, Mapping):
                _invalid("bounded capability semantic constraints are invalid")
            _verify_constraints(capability, constraints)
            if capability == "IMPLEMENTATION_INVESTIGATION":
                index = step.get("step_index")
                trace = step.get("trace_digest")
                previous = step.get("previous_result_ref")
                remaining = step.get("remaining_budget")
                if (
                    type(index) is not int
                    or not 1 <= index <= 4
                    or not isinstance(trace, str)
                    or trace in traces
                    or not isinstance(remaining, Mapping)
                    or set(remaining) != {"model_calls", "execution_steps"}
                    or type(remaining.get("model_calls")) is not int
                    or type(remaining.get("execution_steps")) is not int
                    or previous is not None
                    and previous not in fixtures
                ):
                    _invalid("bounded investigation step authority is invalid")
                try:
                    Digest(trace)
                except (TypeError, ValueError) as exc:
                    raise DomainError(
                        ErrorCode.EVALUATION_DEFINITION_INVALID,
                        "bounded investigation trace digest is invalid",
                    ) from exc
                traces.append(trace)
            sealed = sealed_step_input(suite, case, step)
            try:
                canonical_json_bytes(sealed)
            except (TypeError, ValueError) as exc:
                raise DomainError(
                    ErrorCode.EVALUATION_DEFINITION_INVALID,
                    "bounded sealed step input is not canonical JSON",
                ) from exc
        case_ids.append(case_id)
        role_counts[str(capability)] += 1
    if tuple(case_ids) != PINNED_REQUIRED_CASE_IDS or role_counts != {
        "IMPLEMENTATION_INVESTIGATION": 16,
        "IMPLEMENTATION_ANSWER_DRAFTING": 1,
        "IMPLEMENTATION_ANSWER_REVIEW": 1,
    }:
        _invalid("bounded cases are missing, reordered, or role-incomplete")

    if not isinstance(oracle, Mapping) or set(oracle) != {
        "schema",
        "oracle_ref",
        "suite_ref",
        "forbidden_event_sets",
        "cases",
    }:
        _invalid("bounded capability oracle shape is invalid")
    if (
        oracle.get("schema") != ORACLE_SCHEMA
        or oracle.get("oracle_ref") != PINNED_ORACLE_REF
        or oracle.get("suite_ref") != PINNED_SUITE_REF
    ):
        _invalid("bounded capability oracle identity is invalid")
    event_sets = oracle.get("forbidden_event_sets")
    if not isinstance(event_sets, Mapping) or set(event_sets) != {
        "investigation",
        "draft",
        "review",
    }:
        _invalid("bounded forbidden-event catalog is invalid")
    for values in event_sets.values():
        events = _strings(values, "forbidden events")
        if len(events) != len(set(events)) or not _COMMON_FORBIDDEN_EVENTS.issubset(events):
            _invalid("bounded forbidden-event set is incomplete")
    oracle_cases = oracle.get("cases")
    if not isinstance(oracle_cases, list) or len(oracle_cases) != len(cases):
        _invalid("bounded capability oracle case set is invalid")
    for case, oracle_case in zip(cases, oracle_cases):
        if (
            not isinstance(oracle_case, Mapping)
            or set(oracle_case) != {"case_id", "steps"}
            or oracle_case.get("case_id") != case.get("case_id")
            or not isinstance(oracle_case.get("steps"), list)
            or len(oracle_case["steps"]) != len(case["steps"])
        ):
            _invalid("bounded oracle case order or call count is invalid")
        for step, expected in zip(case["steps"], oracle_case["steps"]):
            if not isinstance(expected, Mapping) or "forbidden_events_ref" not in expected:
                _invalid("bounded oracle step is invalid")
            if set(expected) not in (
                {"operation", "arguments", "forbidden_events_ref"},
                {"accepted_operations", "forbidden_events_ref"},
                {"expected_projection", "forbidden_events_ref"},
            ):
                _invalid("bounded oracle step shape is invalid")
            event_ref = expected.get("forbidden_events_ref")
            if event_ref not in event_sets:
                _invalid("bounded oracle event set reference is invalid")
            accepted = expected_step_projections(suite, case, step, expected)
            fields = projections[step["projection_ref"]]
            if (
                not accepted
                or any(set(projection) != set(fields) for projection in accepted)
                or len({digest_of(item).value for item in accepted}) != len(accepted)
                or (
                    case["capability"] == "IMPLEMENTATION_INVESTIGATION"
                    and any(
                        projection.get("operation")
                        not in available_operations_for_step(suite, case, step)
                        for projection in accepted
                    )
                )
            ):
                _invalid("bounded oracle projection is not exact")


def sealed_step_input(
    suite: Mapping[str, object],
    case: Mapping[str, object],
    step: Mapping[str, object],
) -> dict[str, object]:
    if case["capability"] != "IMPLEMENTATION_INVESTIGATION":
        value = step.get("sealed_input")
        if not isinstance(value, Mapping):
            _invalid("bounded terminal role sealed input is invalid")
        return copy.deepcopy(dict(value))
    authority = suite.get("synthetic_authority")
    fixtures = suite.get("sealed_result_fixtures")
    assert isinstance(authority, Mapping) and isinstance(fixtures, Mapping)
    previous_ref = step.get("previous_result_ref")
    fixture = None if previous_ref is None else fixtures[previous_ref]
    previous = (
        None if fixture is None else _model_visible_previous_result(fixture)
    )
    if previous is not None:
        previous["evidence_requests"] = copy.deepcopy(
            case["evidence_requests"]
        )
    progress = copy.deepcopy(step["progress_receipt"])
    if fixture is not None:
        if not isinstance(progress, dict):
            _invalid("bounded later-step progress receipt is absent")
        progress["completeness"] = _fixture_completeness(fixture)
    return {
        "original_question": case["original_question"],
        "response_language": case["response_language"],
        "need_key": authority["need_key"],
        "read_authority": copy.deepcopy(authority["read_authority"]),
        "profile_ref": authority["profile_ref"],
        "step_index": step["step_index"],
        "trace_digest": step["trace_digest"],
        "previous_result": copy.deepcopy(previous),
        "progress_receipt": progress,
        "remaining_budget": copy.deepcopy(step["remaining_budget"]),
    }


def available_operations_for_step(
    suite: Mapping[str, object],
    case: Mapping[str, object],
    step: Mapping[str, object],
) -> tuple[str, ...]:
    if case.get("capability") != "IMPLEMENTATION_INVESTIGATION":
        return ()
    return constrained_investigation_operations(
        sealed_input=sealed_step_input(suite, case, step)
    )


def _model_visible_previous_result(value: object) -> dict[str, object]:
    """Project synthetic authority through the same boundary as the product."""

    if not isinstance(value, Mapping) or not isinstance(
        value.get("operation"), str
    ):
        _invalid("bounded previous Result fixture is invalid")
    raw_results = value.get("results")
    if (
        not isinstance(raw_results, list)
        or not raw_results
        or any(not isinstance(item, Mapping) for item in raw_results)
    ):
        _invalid("bounded previous Result fixture Results are invalid")
    projected_results: list[dict[str, object]] = []
    fixture_only = {
        "result_id",
        "digest",
        "query_result_completeness",
        "knowledge_representation",
        "business_discovery_recall",
        "truncated",
        "entity_refs",
    }
    result_operation = (
        "method_implementation"
        if value["operation"] == "method_implementations"
        else value["operation"]
    )
    for raw in raw_results:
        payload = {
            str(key): copy.deepcopy(item)
            for key, item in raw.items()
            if key not in fixture_only
        }
        raw_refs = raw.get("entity_refs")
        if raw_refs is not None:
            if not isinstance(raw_refs, list):
                _invalid("bounded previous Result Entity refs are invalid")
            entities: list[dict[str, object]] = []
            for raw_ref in raw_refs:
                if not isinstance(raw_ref, Mapping):
                    _invalid("bounded previous Result Entity ref is invalid")
                entity = {
                    "root_id": copy.deepcopy(raw_ref.get("entity_root_id")),
                    "state_id": copy.deepcopy(raw_ref.get("entity_state_id")),
                }
                if "entity_type" in raw_ref:
                    entity["entity_type"] = copy.deepcopy(raw_ref["entity_type"])
                entities.append(entity)
            payload["entities"] = entities
        projected_results.append(
            {
                "result_id": copy.deepcopy(raw.get("result_id")),
                "operation": copy.deepcopy(result_operation),
                "completeness": copy.deepcopy(
                    raw.get("query_result_completeness")
                ),
                "truncated": copy.deepcopy(raw.get("truncated", False)),
                "payload": payload,
                "digest": copy.deepcopy(raw.get("digest")),
            }
        )
    return {
        "operation": copy.deepcopy(value["operation"]),
        "results": projected_results,
    }


def _fixture_completeness(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        _invalid("bounded completeness fixture is invalid")
    results = value.get("results")
    if (
        not isinstance(results, list)
        or not results
        or any(not isinstance(item, Mapping) for item in results)
    ):
        _invalid("bounded completeness fixture Results are invalid")
    query = (
        "COMPLETE"
        if all(
            item.get("query_result_completeness") == "COMPLETE"
            and item.get("truncated") is not True
            for item in results
        )
        else "UNKNOWN"
    )
    representation = (
        "COMPLETE"
        if all(item.get("knowledge_representation") == "COMPLETE" for item in results)
        else "UNKNOWN"
    )
    discovery = (
        "COMPLETE"
        if all(item.get("business_discovery_recall") == "COMPLETE" for item in results)
        else "UNKNOWN"
    )
    missing = []
    if query != "COMPLETE":
        missing.append("QUERY_RESULT_COMPLETENESS_UNPROVEN")
    if representation != "COMPLETE":
        missing.append("KNOWLEDGE_REPRESENTATION_COVERAGE_UNPROVEN")
    if discovery != "COMPLETE":
        missing.append("BUSINESS_DISCOVERY_RECALL_UNPROVEN")
    return {
        "query_result": query,
        "knowledge_representation": representation,
        "business_discovery_recall": discovery,
        "bounded_absence_allowed": not missing,
        "missing_limitation_codes": missing,
    }


def expected_step_projection(
    suite: Mapping[str, object],
    case: Mapping[str, object],
    step: Mapping[str, object],
    oracle_step: Mapping[str, object],
) -> dict[str, object]:
    accepted = oracle_step.get("accepted_operations")
    if isinstance(accepted, list) and accepted:
        primary = accepted[0]
        if isinstance(primary, Mapping):
            oracle_step = primary
    direct = oracle_step.get("expected_projection")
    if isinstance(direct, Mapping):
        return copy.deepcopy(dict(direct))
    operation = oracle_step.get("operation")
    arguments = oracle_step.get("arguments")
    if (
        operation
        not in JAVA_SOURCE_SEMANTICS_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
        or not isinstance(arguments, Mapping)
    ):
        _invalid("bounded oracle operation is invalid")
    value: dict[str, object] = {
        "step_index": step["step_index"],
        "trace_digest": step["trace_digest"],
        "operation": operation,
        "snapshot_id": None,
        "limit": None,
        "candidate_result_id": None,
        "candidate_result_digest": None,
        "method_refs": [],
        "entity_refs": [],
        "direction": None,
        "predicate": None,
        "max_depth": None,
        "max_paths": None,
        "max_expansions": None,
        "evidence_requests": copy.deepcopy(case["evidence_requests"]),
    }
    resolved = _resolved_arguments(suite, arguments)
    allowed = set(value) - {"step_index", "trace_digest", "operation"}
    if set(resolved) - allowed:
        _invalid("bounded oracle operation arguments are invalid")
    value.update(resolved)
    _verify_operation_projection(operation, value)
    return value


def expected_step_projections(
    suite: Mapping[str, object],
    case: Mapping[str, object],
    step: Mapping[str, object],
    oracle_step: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    accepted = oracle_step.get("accepted_operations")
    if accepted is None:
        return (expected_step_projection(suite, case, step, oracle_step),)
    if (
        not isinstance(accepted, list)
        or not accepted
        or any(
            not isinstance(item, Mapping)
            or set(item) != {"operation", "arguments"}
            for item in accepted
        )
    ):
        _invalid("bounded accepted operation set is invalid")
    return tuple(
        expected_step_projection(
            suite,
            case,
            step,
            {
                "operation": item["operation"],
                "arguments": item["arguments"],
            },
        )
        for item in accepted
    )


def forbidden_events(
    oracle: Mapping[str, object], oracle_step: Mapping[str, object]
) -> list[str]:
    catalog = oracle.get("forbidden_event_sets")
    assert isinstance(catalog, Mapping)
    value = catalog.get(oracle_step.get("forbidden_events_ref"))
    return list(_strings(value, "forbidden events"))


def case_fixture_digest(
    suite: Mapping[str, object], case: Mapping[str, object]
) -> Digest:
    return digest_of(
        {
            "case_id": case["case_id"],
            "capability": case["capability"],
            "sealed_steps": [
                sealed_step_input(suite, case, step)
                for step in case["steps"]
            ],
        }
    )


def case_oracle_digest(
    suite: Mapping[str, object],
    oracle: Mapping[str, object],
    case: Mapping[str, object],
    oracle_case: Mapping[str, object],
) -> Digest:
    return digest_of(
        {
            "case_id": case["case_id"],
            "steps": [
                {
                    "projection_fields": suite["projection_sets"][
                        step["projection_ref"]
                    ],
                    "semantic_constraints": step["semantic_constraints"],
                    "expected_projections": expected_step_projections(
                        suite, case, step, oracle_step
                    ),
                    "forbidden_events": forbidden_events(oracle, oracle_step),
                }
                for step, oracle_step in zip(
                    case["steps"], oracle_case["steps"]
                )
            ],
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
    cases = tuple(
        BoundedJavaSourceSemanticsWorldModelEvaluationCase(
            role=BoundedJavaSourceSemanticsWorldModelEvaluationRole(
                case["capability"]
            ),
            case_id=str(case["case_id"]),
            case_version="1.5.2",
            fixture_ref=f"{PINNED_SUITE_REF}:fixture:{case['case_id']}",
            fixture_digest=case_fixture_digest(suite, case),
            oracle_ref=f"{PINNED_ORACLE_REF}:case:{case['case_id']}",
            oracle_digest=case_oracle_digest(
                suite, oracle, case, oracle_case
            ),
        )
        for case, oracle_case in case_pairs(suite, oracle)
    )
    return create_bounded_java_source_semantics_world_model_evaluation_definition(
        evaluation_version="1.5.2",
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


def _resolved_arguments(
    suite: Mapping[str, object], arguments: Mapping[str, object]
) -> dict[str, object]:
    value = copy.deepcopy(dict(arguments))
    method_ref = value.pop("method_refs_ref", None)
    entity_ref = value.pop("entity_refs_ref", None)
    fixtures = suite.get("sealed_result_fixtures")
    assert isinstance(fixtures, Mapping)
    if method_ref is not None:
        if method_ref != "three_candidates":
            _invalid("bounded method ref fixture is invalid")
        value["method_refs"] = _projection_refs(
            fixtures["three_candidates"]["results"][0]["entity_refs"]
        )
    if entity_ref is not None:
        choices = {
            "three_candidates:first": (
                fixtures["three_candidates"]["results"][0]["entity_refs"][:1]
            ),
            "three_candidates:first-two": (
                fixtures["three_candidates"]["results"][0]["entity_refs"][:2]
            ),
            "method_batch:first": (
                fixtures["method_batch_complete"]["results"][0]["entity_refs"][:1]
            ),
            "method_batch:first-two": (
                fixtures["method_batch_complete"]["results"][0]["entity_refs"][:2]
            ),
            "declaring_type:first": (
                fixtures["declaring_type_neighborhood"]["results"][0]["entity_refs"][:1]
            ),
            "direct_calls:first-two": (
                fixtures["direct_calls_complete"]["results"][0]["entity_refs"][:2]
            ),
        }
        if entity_ref not in choices:
            _invalid("bounded Entity Ref fixture is invalid")
        value["entity_refs"] = _projection_refs(choices[entity_ref])
    return value


def _projection_refs(values: object) -> list[dict[str, object]]:
    if not isinstance(values, (list, tuple)):
        _invalid("bounded projection refs are invalid")
    fields = (
        "source_result_id",
        "source_result_digest",
        "entity_root_id",
        "entity_state_id",
    )
    projected: list[dict[str, object]] = []
    for value in values:
        if not isinstance(value, Mapping) or any(field not in value for field in fields):
            _invalid("bounded projection ref is incomplete")
        projected.append({field: copy.deepcopy(value[field]) for field in fields})
    return projected


def _verify_operation_projection(
    operation: object, value: Mapping[str, object]
) -> None:
    no_candidate = (
        value["snapshot_id"] is None
        and value["limit"] is None
        and value["candidate_result_id"] is None
        and value["candidate_result_digest"] is None
    )
    no_graph = (
        value["direction"] is None
        and value["predicate"] is None
        and value["max_depth"] is None
        and value["max_paths"] is None
        and value["max_expansions"] is None
    )
    if operation == "implementation_candidates":
        valid = (
            isinstance(value["snapshot_id"], str)
            and type(value["limit"]) is int
            and not value["method_refs"]
            and not value["entity_refs"]
            and no_graph
        )
    elif operation == "method_implementations":
        valid = (
            value["snapshot_id"] is None
            and value["limit"] is None
            and isinstance(value["candidate_result_id"], str)
            and isinstance(value["candidate_result_digest"], str)
            and 1 <= len(value["method_refs"]) <= 3
            and not value["entity_refs"]
            and no_graph
        )
    elif operation == "declared_method_inventory":
        valid = (
            no_candidate
            and not value["method_refs"]
            and len(value["entity_refs"]) == 1
            and no_graph
        )
    elif operation == "direct_neighborhood":
        valid = (
            no_candidate
            and not value["method_refs"]
            and len(value["entity_refs"]) == 1
            and value["direction"] in {"OUTGOING", "INCOMING", "BOTH"}
            and value["max_depth"] is None
            and value["max_paths"] is None
            and value["max_expansions"] is None
        )
    elif operation == "path_exists":
        valid = (
            no_candidate
            and not value["method_refs"]
            and len(value["entity_refs"]) == 2
            and value["direction"] is None
            and isinstance(value["predicate"], str)
            and type(value["max_depth"]) is int
            and value["max_paths"] is None
            and type(value["max_expansions"]) is int
        )
    elif operation == "all_simple_paths":
        valid = (
            no_candidate
            and not value["method_refs"]
            and len(value["entity_refs"]) == 2
            and value["direction"] is None
            and isinstance(value["predicate"], str)
            and type(value["max_depth"]) is int
            and type(value["max_paths"]) is int
            and type(value["max_expansions"]) is int
        )
    else:
        valid = no_candidate and not value["method_refs"] and not value["entity_refs"] and no_graph
    if not valid:
        _invalid("bounded expected operation projection is invalid")


def _verify_constraints(capability: object, value: Mapping[str, object]) -> None:
    allowed = (
        {"search_term_concept_groups", "finish_reason_concept_groups"}
        if capability == "IMPLEMENTATION_INVESTIGATION"
        else {"answer_concept_groups", "answer_order_groups"}
        if capability == "IMPLEMENTATION_ANSWER_DRAFTING"
        else {"required_finding_codes"}
    )
    if set(value) - allowed:
        _invalid("bounded semantic constraint vocabulary drifted")
    for key, item in value.items():
        if key == "required_finding_codes":
            _strings(item, key)
        else:
            _concept_groups(item, key)


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
        _invalid(f"bounded capability {label} are invalid")
    return value


def _concept_groups(value: object, label: str) -> list[list[str]]:
    if not isinstance(value, list) or not value:
        _invalid(f"bounded capability {label} are invalid")
    return [_strings(group, label) for group in value]


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.EVALUATION_DEFINITION_INVALID, message)


__all__ = [
    "DEFAULT_ORACLE_PATH",
    "DEFAULT_SUITE_PATH",
    "PINNED_ORACLE_FILE_DIGEST",
    "PINNED_ORACLE_REF",
    "PINNED_PROVIDER_REQUEST_COUNT",
    "PINNED_REQUIRED_CASE_CALLS",
    "PINNED_REQUIRED_CASE_IDS",
    "PINNED_SUITE_FILE_DIGEST",
    "PINNED_SUITE_REF",
    "build_evaluation_definition",
    "available_operations_for_step",
    "case_fixture_digest",
    "case_oracle_digest",
    "case_pairs",
    "expected_step_projection",
    "forbidden_events",
    "load_capability_inputs",
    "sealed_step_input",
    "verify_capability_inputs",
]
