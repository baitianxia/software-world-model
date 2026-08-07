"""Sealed fixtures and reviewer-only expectations for six strategy roles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from software_world_model.ai_infrastructure import (
    AgenticEvaluationRole,
    AgenticTaskEvaluationCase,
    create_agentic_task_evaluation_definition,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of


CAPABILITY_SUITE_SCHEMA = "swm.agentic-capability-suite@1"
PINNED_CAPABILITY_SUITE_DIGEST = (
    "sha256:2d1eb05c461ad2efc6d5f5c7f31f9af33de469a79c032d056a1bc1b6468da03d"
)
DEFAULT_CAPABILITY_SUITE_PATH = Path(__file__).with_name("suite.json")


def load_capability_suite(
    path: str | Path = DEFAULT_CAPABILITY_SUITE_PATH,
) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            "capability evaluation suite cannot be loaded",
        ) from exc
    if not isinstance(value, dict):
        _invalid("capability evaluation suite must be an object")
    verify_capability_suite(value)
    return value


def verify_capability_suite(suite: Mapping[str, object]) -> None:
    if set(suite) != {
        "schema",
        "suite_id",
        "suite_version",
        "suite_digest",
        "cases",
    } or suite.get("schema") != CAPABILITY_SUITE_SCHEMA:
        _invalid("capability evaluation suite fields are invalid")
    calculated = digest_of(
        {key: value for key, value in suite.items() if key != "suite_digest"}
    ).value
    if (
        suite.get("suite_digest") != calculated
        or calculated != PINNED_CAPABILITY_SUITE_DIGEST
    ):
        _invalid("capability evaluation suite digest is invalid")
    cases = suite.get("cases")
    if not isinstance(cases, list) or len(cases) != len(AgenticEvaluationRole):
        _invalid("capability evaluation suite must contain six role cases")
    roles = []
    identities = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "role",
            "case_id",
            "fixture",
            "oracle",
        }:
            _invalid("capability evaluation case fields are invalid")
        try:
            role = AgenticEvaluationRole(case["role"])
        except (TypeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "capability evaluation role is invalid",
            ) from exc
        identity = (role, case.get("case_id"))
        if (
            not isinstance(case.get("case_id"), str)
            or not case["case_id"]
            or identity in identities
            or not isinstance(case.get("fixture"), dict)
            or not isinstance(case.get("oracle"), dict)
        ):
            _invalid("capability evaluation case is invalid or duplicated")
        identities.add(identity)
        roles.append(role)
    if set(roles) != set(AgenticEvaluationRole):
        _invalid("capability evaluation suite does not cover every role")


def build_capability_definition(
    suite: Mapping[str, object],
    *,
    conformance_result_ref: str,
    provider_configuration_fingerprint: Digest,
    actual_model_fingerprint: str,
    adapter_version: str,
    valid_for_seconds: int,
):
    verify_capability_suite(suite)
    cases = tuple(
        AgenticTaskEvaluationCase(
            role=AgenticEvaluationRole(case["role"]),
            case_id=case["case_id"],
            case_version=suite["suite_version"],
            fixture_ref=(
                f"{suite['suite_id']}:fixture:{case['role']}:{case['case_id']}"
            ),
            fixture_digest=digest_of(case["fixture"]),
            oracle_ref=(
                f"{suite['suite_id']}:oracle:{case['role']}:{case['case_id']}"
            ),
            oracle_digest=digest_of(case["oracle"]),
        )
        for case in suite["cases"]
    )
    return create_agentic_task_evaluation_definition(
        evaluation_version=suite["suite_version"],
        conformance_result_ref=conformance_result_ref,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        # Evaluation evidence records the identity returned by the provider,
        # rather than the alias placed in the request body.  The generic
        # evaluation authority calls this field ``model_ref`` for historical
        # reasons, but compares it with every observed actual fingerprint.
        model_ref=actual_model_fingerprint,
        adapter_version=adapter_version,
        data_source_revision_ref=f"sealed-fixture:{suite['suite_digest']}",
        environment_ref="isolated-local-capability-evaluation@1",
        reference_strategy_ref="codex-reviewed-sealed-role-oracles@1",
        resource_policy_ref="six-role-bounded-model-calls@1",
        cases=cases,
        valid_for_seconds=valid_for_seconds,
    )


def case_entry(
    suite: Mapping[str, object], role: AgenticEvaluationRole
) -> Mapping[str, object]:
    verify_capability_suite(suite)
    return next(case for case in suite["cases"] if case["role"] == role.value)


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.EVALUATION_DEFINITION_INVALID, message)
