"""Pinned fixtures for evidence-first capability evaluation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping

from software_world_model.ai_infrastructure import (
    EvidenceEvaluationRole,
    EvidenceTaskEvaluationCase,
    create_evidence_task_evaluation_definition,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of


CAPABILITY_SUITE_SCHEMA = "swm.evidence-answer-capability-suite@1"
PINNED_CAPABILITY_SUITE_DIGEST = (
    "sha256:0f06bd1572df8c7996b8a6c4eccd908e7193dcd12c06a0aa0b7296bedbdbb421"
)
DEFAULT_CAPABILITY_SUITE_PATH = Path(__file__).with_name("suite.json")


def load_capability_suite(path: str | Path = DEFAULT_CAPABILITY_SUITE_PATH):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DomainError(
            ErrorCode.EVALUATION_DEFINITION_INVALID,
            "evidence capability suite cannot be loaded",
        ) from exc
    verify_capability_suite(value)
    return value


def verify_capability_suite(suite: object) -> None:
    if (
        not isinstance(suite, Mapping)
        or set(suite) != {
            "schema", "suite_id", "suite_version", "suite_digest", "cases"
        }
        or suite.get("schema") != CAPABILITY_SUITE_SCHEMA
        or suite.get("suite_digest") != PINNED_CAPABILITY_SUITE_DIGEST
        or digest_of(
            {key: value for key, value in suite.items() if key != "suite_digest"}
        ).value
        != PINNED_CAPABILITY_SUITE_DIGEST
    ):
        _invalid("evidence capability suite digest or fields are invalid")
    cases = suite["cases"]
    if not isinstance(cases, list) or len(cases) != len(EvidenceEvaluationRole):
        _invalid("evidence capability suite must contain every role exactly once")
    roles = []
    identities = set()
    for case in cases:
        if not isinstance(case, Mapping) or set(case) != {
            "role", "case_id", "fixture", "oracle"
        }:
            _invalid("evidence capability case fields are invalid")
        try:
            role = EvidenceEvaluationRole(case["role"])
        except (TypeError, ValueError) as exc:
            raise DomainError(
                ErrorCode.EVALUATION_DEFINITION_INVALID,
                "evidence capability role is invalid",
            ) from exc
        identity = (role, case["case_id"])
        if (
            not isinstance(case["case_id"], str)
            or not case["case_id"]
            or identity in identities
            or not isinstance(case["fixture"], Mapping)
            or not isinstance(case["oracle"], Mapping)
        ):
            _invalid("evidence capability case is invalid or duplicated")
        identities.add(identity)
        roles.append(role)
    if set(roles) != set(EvidenceEvaluationRole):
        _invalid("evidence capability suite has incomplete role coverage")


def build_capability_definition(
    suite,
    *,
    conformance_result_ref: str,
    provider_configuration_fingerprint: Digest,
    actual_model_fingerprint: str,
    adapter_version: str,
    valid_for_seconds: int,
):
    verify_capability_suite(suite)
    cases = tuple(
        EvidenceTaskEvaluationCase(
            role=EvidenceEvaluationRole(case["role"]),
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
    return create_evidence_task_evaluation_definition(
        evaluation_version=suite["suite_version"],
        conformance_result_ref=conformance_result_ref,
        provider_configuration_fingerprint=provider_configuration_fingerprint,
        model_ref=actual_model_fingerprint,
        adapter_version=adapter_version,
        data_source_revision_ref=f"sealed-fixture:{suite['suite_digest']}",
        environment_ref="isolated-local-evidence-capability-evaluation@1",
        reference_strategy_ref="codex-reviewed-evidence-role-oracles@1",
        resource_policy_ref="evidence-role-bounded-model-calls@1",
        cases=cases,
        valid_for_seconds=valid_for_seconds,
    )


def case_entry(suite, role: EvidenceEvaluationRole):
    verify_capability_suite(suite)
    return next(case for case in suite["cases"] if case["role"] == role.value)


def _invalid(message: str) -> None:
    raise DomainError(ErrorCode.EVALUATION_DEFINITION_INVALID, message)
