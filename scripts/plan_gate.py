#!/usr/bin/env python3
"""Mechanical gate for the active development plan.

This module is intentionally independent from ``scripts/docs.py`` and product
code.  Snapshot mode validates the current manifest and pointers.  Diff mode
uses the action in the base tree as the authority for base-to-target paths and
permits at most one result-driven action transition.

``plan_execution_control`` contract (all keys are exact)::

    schema: DEVELOPMENT_PLAN_EXECUTION_CONTROL@1
    plan_revision_ref: ITER-010-PDR-009
    enforcement_mode: fail-closed
    authorization_refs:
      - local-user-message-utf8:sha256:<64 lowercase hex>
    current_action:
      id: ITER-010-ACTION-DIRECTION-FREEZE-001
      owner_slice_ref: ITER-010-SLICE-001
      kind: four-arm-direction-gate-freeze
      status: authorized
      case_id: V-DIRECTION-FREEZE-001
      coding_allowed: true
      external_execution_allowed: false
      result_ref: ITER-010-RESULT-V-DIRECTION-FREEZE-001
      result_path: docs/project/iterations/iteration-010/results/v-direction-freeze-001.md
      evidence_schema: DEVELOPMENT_PLAN_GATE_EVIDENCE@1
      evidence_path: docs/project/iterations/iteration-010/results/evidence/v-direction-freeze-001.json
      evidence_verifier: ITER010_VALUE_GATE@1
      runner_identity_paths:
        - scripts/plan_gate.py
        - validation/structure_world_model_iteration_010/value_gate/runner.py
        - tests/test_iteration_010_value_gate.py
      produced_case_ids:
        - V-DIRECTION-FREEZE-001
        - V-PUBLIC-OSS-AUTHORITY-ADMISSION-001
      prerequisite_case_ids: []
      allowed_change_paths: []
      forbidden_change_paths: []
    transition:
      pass_next_action_id: ITER-010-ACTION-DIRECTION-QUALITY-PREFERRED-001
      fail_next_action_id: ITER-010-ACTION-DIRECTION-FREEZE-REWORK-001
      invalid_next_action_id: ITER-010-ACTION-DIRECTION-FREEZE-001
    locks:
      product_code_changes: true
      prompt_or_reviewer_changes: true
      web_canary: true
      hardening: true
      full_regression: true
      provider_dispatch: true
    next_action_contracts:
      direction_quality:
        # all current_action fields, plus its transition and locks

The referenced Result is only an index.  A transition also requires the
pre-registered JSON evidence artifact, exact raw-byte and canonical report
digests, a recomputed protected-runner identity, exact produced-Case coverage,
and ``INVALID > FAIL > PASS`` aggregation.  The trusted base's self-contained
value-gate runner is then re-executed in isolation against those exact bytes;
runner changes must land in an earlier commit.  Handwritten front matter alone
can never advance the action cursor.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Mapping, Sequence


REPOSITORY = Path(__file__).resolve().parents[1]
MANIFEST_SCHEMA_VERSION = 2
CONTROL_SCHEMA = "DEVELOPMENT_PLAN_EXECUTION_CONTROL@1"
CONTROL_KEYS = {
    "schema",
    "plan_revision_ref",
    "enforcement_mode",
    "authorization_refs",
    "current_action",
    "transition",
    "locks",
    "next_action_contracts",
}
ACTION_KEYS = {
    "id",
    "owner_slice_ref",
    "kind",
    "status",
    "case_id",
    "coding_allowed",
    "external_execution_allowed",
    "result_ref",
    "result_path",
    "evidence_schema",
    "evidence_path",
    "evidence_verifier",
    "runner_identity_paths",
    "produced_case_ids",
    "prerequisite_case_ids",
    "allowed_change_paths",
    "forbidden_change_paths",
}
TRANSITION_KEYS = {
    "pass_next_action_id",
    "fail_next_action_id",
    "invalid_next_action_id",
}
LOCK_KEYS = {
    "product_code_changes",
    "prompt_or_reviewer_changes",
    "web_canary",
    "hardening",
    "full_regression",
    "provider_dispatch",
}
ACTION_CONTRACT_KEYS = ACTION_KEYS | {"transition", "locks"}
RESULT_GATE_FIELDS = {
    "id",
    "kind",
    "status",
    "authority",
    "iteration",
    "plan_revision_ref",
    "action_ref",
    "verification_case_id",
    "plan_gate_verdict",
    "evidence_schema",
    "evidence_verifier",
    "evidence_artifact_path",
    "evidence_artifact_digest",
    "execution_input_digest",
    "runner_identity_digest",
    "runner_receipt_digest",
    "verification_report_digest",
    "subject_digest",
    "external_model_call_count",
}
RESULT_VERDICT_ALIASES = {
    "verdict",
    "result_verdict",
    "gate_verdict",
    "transition_verdict",
}
VERDICT_TO_TRANSITION_FIELD = {
    "PASS": "pass_next_action_id",
    "FAIL": "fail_next_action_id",
    "INVALID": "invalid_next_action_id",
}
EVIDENCE_SCHEMA = "DEVELOPMENT_PLAN_GATE_EVIDENCE@1"
ITER010_VALUE_GATE_VERIFIER = "ITER010_VALUE_GATE@1"
ITER010_PLAN_RECOVERY_VERIFIER = "ITER010_PLAN_RECOVERY@1"
ITER010_MVP_LIGHT_VERIFIER = "ITER010_MVP_LIGHT@3"
ITER010_MVP_LIGHT_EXPERIENCE_ACTION_ID = (
    "ITER-010-ACTION-USER-PLAN-RECOVERY-001"
)
ITER010_MVP_LIGHT_EXPERIENCE_CASE_ID = "V-MVP-EXPERIENCE-001"
ITER010_MVP_LIGHT_DIRECTION_ACTION_ID = (
    "ITER-010-ACTION-USER-DIRECTION-DECISION-001"
)
ITER010_MVP_LIGHT_DIRECTION_CASE_ID = "V-PREVIEW-002"
ITER010_PLAN_RECOVERY_ACTION_ID = "ITER-010-ACTION-USER-PLAN-RECOVERY-001"
ITER010_PLAN_RECOVERY_RESULT_ID = "ITER-010-RESULT-V-PLAN-RECOVERY-001"
ITER010_PLAN_RECOVERY_CASE_ID = "V-PLAN-RECOVERY-001"
ITER010_PLAN_RECOVERY_BASE_REVISION = "ITER-010-PDR-009"
ITER010_PLAN_RECOVERY_TARGET_REVISION = "ITER-010-PDR-010"
ITER010_PLAN_CHANGE_AUTHORIZATION_REF = (
    "local-user-message-utf8:"
    "sha256:5ced06d2604020248c5baf69421ccbb4e5c047288b6db5b2202675c558c38cf6"
)
ITER010_PLAN_RECOVERY_AUTHORIZATION_REF = (
    "local-user-message-utf8:"
    "sha256:6cf2531ab1119b67ad2010040ae1ac73f817785684fccc26111b3b70ef5fcbe5"
)
ITER010_FAILURE_HANDOFF_RECOVERY_SCHEMA = (
    "USER_DIRECTED_FAILURE_HANDOFF_RECOVERY@1"
)
ITER010_FAILURE_HANDOFF_RECOVERY_AUTHORIZATION_REF = (
    "local-user-message-utf8:"
    "sha256:382638cd16fdbc85c08a4202a94e630fe4c973ce03bb0d8a1671cbe4ee151aa7"
)
ITER010_FAILURE_HANDOFF_RECOVERY_BASE_COMMIT = (
    "120a8903462caf04fbf7bda0c1afa07e3133d448"
)
ITER010_FAILURE_HANDOFF_RECOVERY_BASE_TREE = (
    "883bdde37eec62856139e7fc00ee38691d311b73"
)
ITER010_FAILURE_HANDOFF_RECOVERY_TARGET_REVISION = "ITER-010-PDR-011"
PLAN_RESULT_SEAL_SCHEMA = "DEVELOPMENT_PLAN_RESULT_SEAL@1"
PROVIDER_ROUTE_POLICY_SCHEMA = "QUALIFIED_EXECUTION_PROFILE_PREFERENCE@2"
LEGACY_PROVIDER_ROUTE_POLICY_SCHEMA = "QUALIFIED_PROVIDER_PREFERENCE@1"
EXECUTION_PROFILE_CONFIGURATION_SCHEMA = "MODEL_TRANSPARENT_EXECUTION_PROFILES@2"
LEGACY_EXECUTION_PROFILE_CONFIGURATION_SCHEMA = (
    "MODEL_TRANSPARENT_EXECUTION_PROFILES@1"
)
ROUTE_POLICY_MIGRATION_SCHEMA = "TRUSTED_PARENT_ROUTE_POLICY_MIGRATION@1"
ROUTE_POLICY_MIGRATION_STATE = "trusted-parent-bridge"
ROUTE_POLICY_MIGRATION_KEYS = {
    "schema",
    "state",
    "from_schema",
    "to_schema",
    "plan_revision_ref",
    "only_next_change",
    "external_dispatch_allowed",
}
ROUTE_POLICY_MIGRATION_EXPECTED = {
    "schema": ROUTE_POLICY_MIGRATION_SCHEMA,
    "state": ROUTE_POLICY_MIGRATION_STATE,
    "from_schema": LEGACY_PROVIDER_ROUTE_POLICY_SCHEMA,
    "to_schema": PROVIDER_ROUTE_POLICY_SCHEMA,
    "plan_revision_ref": ITER010_PLAN_RECOVERY_TARGET_REVISION,
    "only_next_change": "finalize-model-transparent-route-policy",
    "external_dispatch_allowed": False,
}
PREFERRED_EXECUTION_PROFILE_CONFIGURATION_KEYS = {
    "execution_profile_ref",
    "provider_identity",
    "model_identity",
}
FALLBACK_EXECUTION_PROFILE_CONFIGURATION_KEYS = (
    PREFERRED_EXECUTION_PROFILE_CONFIGURATION_KEYS
    | {"admission_policy_plugin_ref"}
)
PREFERRED_PROFILE_UNAVAILABLE_VERDICT = "PREFERRED_EXECUTION_PROFILE_UNAVAILABLE"
PREFERRED_PROFILE_UNAVAILABLE_OUTCOME = "preferred-execution-profile-unavailable"
PROVIDER_ROUTE_POLICY_KEYS = {
    "schema",
    "preferred_execution_profile_ref",
    "fallback_execution_profile_ref",
    "preference_order",
    "availability_owner",
    "required_fallback_verdict",
    "product_control_flow_allowed_inputs",
    "product_control_flow_forbidden_inputs",
    "verification_case_id",
    "fallback_dispatch_requires_verification_pass",
    "preferred_unavailable_evidence_required",
    "implementation_gap_counts_as_preferred_unavailable",
    "preferred_availability_requires",
    "route_freeze_time",
    "ordered_routes_preauthorized_at_session_start",
    "ordered_route_disclosure_scopes_preauthorized_at_session_start",
    "transparent_logical_interaction_fallback_allowed",
    "user_resubmission_or_new_session_required",
    "fallback_requires_preferred_attempt_terminal_without_authorized_answer",
    "fallback_trigger",
    "fallback_eligible_outcomes",
    "structured_output_invalid_allows_fallback",
    "model_review_rejected_allows_fallback",
    "raw_http_or_outcome_without_availability_verdict_allows_fallback",
    "application_source_security_failure_allows_fallback",
    "fallback_reason_classification_required",
    "capability_failure_must_not_be_misclassified_as_unavailable",
    "structured_output_invalid_recovery",
    "model_review_rejected_recovery",
    "same_profile_application_repair_is_transport_request_retry",
    "same_profile_application_repair_bound",
    "same_profile_application_repair_exhausted_action",
    "fallback_attempt_restarts_full_chain",
    "fallback_attempt_inputs",
    "cross_attempt_intermediate_state_reuse_allowed",
    "late_preferred_result_policy",
    "late_preferred_result_overwrite_allowed",
    "post_dispatch_execution_profile_switch_requires",
    "maximum_fallback_execution_profile_attempts",
    "transport_request_retry_allowed",
    "outcome_unknown_duplicate_cost_risk_recorded",
    "peak_urgent_override_requires",
    "cost_can_reduce_answer_quality",
    "cost_gate_scope",
    "current_started_interaction_unit_must_keep_full_quality_chain",
    "unchanged_current_conformance_reuse_required",
}
PROVIDER_NEUTRAL_ROOT_INPUT_SCHEMA = (
    "VALUE_GATE_PROVIDER_NEUTRAL_ROOT_INPUT_SET@1"
)
PROVIDER_NEUTRAL_SYSTEM_ARM_IDS = (
    "direct-relevant-evidence",
    "same-agent-source-only",
    "same-agent-world-model-and-source",
)
EVIDENCE_KEYS = {
    "schema",
    "result_id",
    "plan_revision_ref",
    "action_ref",
    "verification_case_id",
    "plan_gate_verdict",
    "evidence_verifier",
    "evidence_artifact_path",
    "execution_input_digest",
    "runner_identity_digest",
    "runner_receipt_digest",
    "verification_report_digest",
    "subject_digest",
    "action_evidence",
    "execution_counters",
    "runner_receipt",
    "case_outcomes",
}
CASE_OUTCOME_KEYS = {"case_id", "verdict", "evidence_ref", "evidence_digest"}
EXECUTION_COUNTER_KEYS = {
    "external_model_call_count",
    "provider_dispatch_count",
    "credential_resolution_count",
    "tls_attempt_count",
    "http_dispatch_count",
    "full_regression_run_count",
}
RUNNER_RECEIPT_KEYS = {
    "runner_id",
    "runner_identity_digest",
    "execution_input_digest",
    "exit_code",
    "completed",
}
LIVE_VERIFICATION_FIELDS = {
    "evidence_verifier",
    "action_ref",
    "verification_case_id",
    "plan_gate_verdict",
    "execution_input_digest",
    "runner_identity_digest",
    "verification_report_digest",
    "subject_digest",
    "external_model_call_count",
}
RUNNER_TIMEOUT_SECONDS = 5
SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}")
PUBLIC_SOURCE_AUTHORITY_CASE_ID = "V-PUBLIC-OSS-AUTHORITY-ADMISSION-001"
ACTIVE_SLICE_STATUSES = {"authorized", "in-progress"}
ACTION_ID_RE = re.compile(r"ITER-[0-9]{3,}-ACTION-[A-Z0-9._-]+")
SLICE_ID_RE = re.compile(r"ITER-[0-9]{3,}-SLICE-[0-9]{3,}(?:-[A-Z0-9._-]+)?")
RESULT_ID_RE = re.compile(r"ITER-[0-9]{3,}-RESULT-[A-Z0-9._-]+")
CASE_ID_RE = re.compile(r"V-[A-Z0-9._-]+")
PDR_ID_RE = re.compile(r"ITER-[0-9]{3,}-PDR-[0-9]{3,}(?:-[A-Z0-9._-]+)?")
PDR_SEQUENCE_RE = re.compile(
    r"(?P<iteration>ITER-[0-9]{3,})-PDR-(?P<sequence>[0-9]{3,})"
    r"(?:-[A-Z0-9._-]+)?"
)
FINDING_ID_RE = re.compile(r"FINDING-[0-9]{3,}-[0-9]{3,}(?:-[A-Z0-9._-]+)?")
AUTHORIZATION_RE = re.compile(
    r"(?:codex-user-message|local-user-message-utf8):sha256:[0-9a-f]{64}"
)
AUTHORIZATION_BYTES_RE = re.compile(
    rb"(?:codex-user-message|local-user-message-utf8):sha256:[0-9a-f]{64}"
)

# A first cut-over may install only the governance contract, its validators,
# their exact tests, and the CI workflow.  Broad test/validation prefixes are
# intentionally excluded so bootstrap cannot carry product behavior indirectly.
BOOTSTRAP_ALLOWED_PATHS = (
    "AGENTS.md",
    ".githooks/plan-pre-commit",
    "scripts/docs.py",
    "scripts/plan_gate.py",
    "tests/test_docs_gate.py",
    "tests/test_plan_gate.py",
    ".github/workflows/plan-compliance.yml",
    "docs/system/",
    "docs/project/current.md",
    "docs/project/governance/",
    "docs/project/iterations/",
    "docs/_generated/",
)
BOOTSTRAP_FORBIDDEN_PATHS = ("src/software_world_model/",)
PROTECTED_GATE_PATHS = {
    ".githooks/plan-pre-commit",
    "scripts/docs.py",
    "scripts/plan_gate.py",
    "tests/test_docs_gate.py",
    "tests/test_plan_gate.py",
    ".github/workflows/plan-compliance.yml",
}


class PlanGateError(ValueError):
    """Raised when data cannot be parsed or inspected safely."""


@dataclass(frozen=True)
class _YamlLine:
    indentation: int
    content: str
    number: int


@dataclass(frozen=True)
class VerificationCase:
    case_id: str
    evidence: str
    verdict: str


def _parse_scalar(value: str, line_number: int) -> object:
    value = value.strip()
    if value.startswith(("!", "&", "*", "|", ">")):
        raise PlanGateError(
            f"line {line_number}: tags, anchors, aliases, and block scalars are forbidden"
        )
    if value == "[]":
        return []
    if value == "{}":
        return {}
    if value.startswith(("[", "{")):
        raise PlanGateError(
            f"line {line_number}: non-empty inline collections are forbidden"
        )
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise PlanGateError(
                f"line {line_number}: invalid double-quoted scalar"
            ) from error
        if not isinstance(parsed, str):
            raise PlanGateError(f"line {line_number}: quoted scalar must be a string")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise PlanGateError(f"line {line_number}: invalid single-quoted scalar")
        return value[1:-1].replace("''", "'")
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value):
        return int(value)
    return value


def load_safe_yaml(text: str) -> dict[str, object]:
    """Parse the inert YAML subset used by manifests, including scalar lists."""

    lines: list[_YamlLine] = []
    for number, raw in enumerate(text.splitlines(), 1):
        if "\t" in raw:
            raise PlanGateError(f"line {number}: tabs are forbidden")
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if re.search(r"\s+#", raw):
            raise PlanGateError(f"line {number}: inline comments are forbidden")
        indentation = len(raw) - len(raw.lstrip(" "))
        lines.append(_YamlLine(indentation, raw[indentation:].rstrip(), number))
    if not lines:
        raise PlanGateError("manifest is empty")

    def parse_block(index: int, indentation: int) -> tuple[object, int]:
        if lines[index].indentation != indentation:
            raise PlanGateError(
                f"line {lines[index].number}: inconsistent indentation"
            )
        is_sequence = lines[index].content == "-" or lines[index].content.startswith("- ")
        if is_sequence:
            values: list[object] = []
            while index < len(lines) and lines[index].indentation == indentation:
                line = lines[index]
                if not (line.content == "-" or line.content.startswith("- ")):
                    raise PlanGateError(
                        f"line {line.number}: cannot mix mappings and sequences"
                    )
                item = line.content[1:].strip()
                if not item:
                    raise PlanGateError(
                        f"line {line.number}: nested sequence items are unsupported"
                    )
                values.append(_parse_scalar(item, line.number))
                index += 1
                if index < len(lines) and lines[index].indentation > indentation:
                    raise PlanGateError(
                        f"line {lines[index].number}: scalar sequence item has children"
                    )
            return values, index

        values_map: dict[str, object] = {}
        while index < len(lines) and lines[index].indentation == indentation:
            line = lines[index]
            if line.content == "-" or line.content.startswith("- "):
                raise PlanGateError(
                    f"line {line.number}: cannot mix mappings and sequences"
                )
            if ":" not in line.content:
                raise PlanGateError(f"line {line.number}: expected mapping entry")
            key, raw_value = line.content.split(":", 1)
            key = key.strip()
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.-]*", key) or key == "<<":
                raise PlanGateError(f"line {line.number}: invalid mapping key")
            if key in values_map:
                raise PlanGateError(f"line {line.number}: duplicate key {key!r}")
            raw_value = raw_value.strip()
            index += 1
            if raw_value:
                values_map[key] = _parse_scalar(raw_value, line.number)
                if index < len(lines) and lines[index].indentation > indentation:
                    raise PlanGateError(
                        f"line {lines[index].number}: scalar mapping value has children"
                    )
                continue
            if index >= len(lines) or lines[index].indentation <= indentation:
                values_map[key] = {}
            else:
                values_map[key], index = parse_block(
                    index, lines[index].indentation
                )
        return values_map, index

    if lines[0].indentation != 0:
        raise PlanGateError(f"line {lines[0].number}: root indentation must be zero")
    parsed, index = parse_block(0, 0)
    if index != len(lines) or not isinstance(parsed, dict):
        raise PlanGateError("manifest root must be one mapping")
    return parsed


def parse_front_matter(text: str) -> dict[str, object]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise PlanGateError("document is missing front matter")
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration as error:
        raise PlanGateError("document front matter is not closed") from error
    metadata: dict[str, object] = {}
    for number, raw in enumerate(lines[1:end], 2):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            raise PlanGateError(f"front matter line {number}: expected key:value")
        key, value = raw.split(":", 1)
        key = key.strip()
        if key in metadata:
            raise PlanGateError(f"front matter line {number}: duplicate key {key!r}")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            metadata[key] = [
                item.strip().strip("'\"")
                for item in value[1:-1].split(",")
                if item.strip()
            ]
        else:
            metadata[key] = value.strip("'\"")
    return metadata


def parse_verification_cases(text: str) -> dict[str, list[VerificationCase]]:
    """Extract Case, Evidence, and the leading status verdict from Markdown rows."""

    cases: dict[str, list[VerificationCase]] = {}
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in stripped[1:-1].split("|")]
        if len(cells) < 3 or CASE_ID_RE.fullmatch(cells[0]) is None:
            continue
        status = cells[-1]
        match = re.match(r"\*{0,2}(PASS|FAIL|INVALID|NOT-RUN)\b", status, re.I)
        verdict = match.group(1).upper() if match is not None else "UNKNOWN"
        cases.setdefault(cells[0], []).append(
            VerificationCase(cells[0], cells[-2], verdict)
        )
    return cases


def _mapping(value: object, label: str, errors: list[str]) -> dict[str, object]:
    if not isinstance(value, dict):
        errors.append(f"{label} must be a mapping")
        return {}
    return value


def _exact_keys(value: Mapping[str, object], expected: set[str], label: str) -> list[str]:
    errors: list[str] = []
    missing = sorted(expected.difference(value))
    extra = sorted(set(value).difference(expected))
    if missing:
        errors.append(f"{label} is missing fields: {', '.join(missing)}")
    if extra:
        errors.append(f"{label} has unexpected fields: {', '.join(extra)}")
    return errors


def _validate_path_rule(value: object, label: str) -> list[str]:
    if not isinstance(value, str) or not value:
        return [f"{label} must be a non-empty repository-relative path"]
    if "\\" in value:
        return [f"{label} must not contain backslashes"]
    prefix_rule = value.endswith("/**")
    raw = value[:-3] if prefix_rule else value[:-1] if value.endswith("/") else value
    if any(character in raw for character in "*?[]"):
        return [f"{label} supports only a terminal /** prefix rule"]
    path = PurePosixPath(raw)
    if path.is_absolute() or raw in {"", "."} or ".." in path.parts:
        return [f"{label} must be a normalized repository-relative path"]
    if path.as_posix() != raw:
        return [f"{label} must be normalized"]
    return []


def _path_matches(path: str, rule: str) -> bool:
    if rule.endswith("/**"):
        directory = rule[:-3]
        return path == directory or path.startswith(directory + "/")
    return path.startswith(rule) if rule.endswith("/") else path == rule


def validate_changed_paths(
    action: Mapping[str, object], changed_paths: Iterable[str]
) -> list[str]:
    """Apply allow/deny policy from the base action; deny always wins."""

    errors: list[str] = []
    allowed = action.get("allowed_change_paths")
    forbidden = action.get("forbidden_change_paths")
    if not isinstance(allowed, list) or not all(isinstance(item, str) for item in allowed):
        return ["base current_action.allowed_change_paths must be a scalar list"]
    if not isinstance(forbidden, list) or not all(
        isinstance(item, str) for item in forbidden
    ):
        return ["base current_action.forbidden_change_paths must be a scalar list"]
    coding_allowed = action.get("coding_allowed") is True
    for path in sorted(set(changed_paths)):
        errors.extend(_validate_path_rule(path, f"changed path {path!r}"))
        if not any(_path_matches(path, rule) for rule in allowed):
            errors.append(f"changed path is not allowed by the base action: {path}")
        if any(_path_matches(path, rule) for rule in forbidden):
            errors.append(f"changed path is forbidden by the base action: {path}")
        if not coding_allowed and _path_matches(path, "src/software_world_model/"):
            errors.append(f"base action does not authorize product code changes: {path}")
    return errors


def validate_bootstrap_paths(changed_paths: Iterable[str]) -> list[str]:
    return validate_changed_paths(
        {
            "coding_allowed": False,
            "allowed_change_paths": list(BOOTSTRAP_ALLOWED_PATHS),
            "forbidden_change_paths": list(BOOTSTRAP_FORBIDDEN_PATHS),
        },
        changed_paths,
    )


def _control(manifest: Mapping[str, object]) -> dict[str, object] | None:
    value = manifest.get("plan_execution_control")
    return value if isinstance(value, dict) else None


def _value_gate_runner_paths(paths: object) -> list[str]:
    if not isinstance(paths, list):
        return []
    return [
        path
        for path in paths
        if isinstance(path, str)
        and PurePosixPath(path).name == "runner.py"
        and PurePosixPath(path).parent.name == "value_gate"
    ]


def _registered_action_contracts(
    control: Mapping[str, object], errors: list[str]
) -> dict[str, dict[str, object]]:
    raw_contracts = _mapping(
        control.get("next_action_contracts"),
        "plan_execution_control.next_action_contracts",
        errors,
    )
    by_id: dict[str, dict[str, object]] = {}
    for name, raw_contract in raw_contracts.items():
        label = f"plan_execution_control.next_action_contracts.{name}"
        if re.fullmatch(r"[a-z][a-z0-9_]*", name) is None:
            errors.append(f"{label} must use a lowercase snake-case key")
        contract = _mapping(raw_contract, label, errors)
        errors.extend(_exact_keys(contract, ACTION_CONTRACT_KEYS, label))
        identifier = contract.get("id")
        if not isinstance(identifier, str) or ACTION_ID_RE.fullmatch(identifier) is None:
            errors.append(f"{label}.id must be an exact action ID")
        elif identifier in by_id:
            errors.append(f"next_action_contracts contains duplicate action ID {identifier}")
        else:
            by_id[identifier] = contract
        runner_paths = contract.get("runner_identity_paths")
        if not isinstance(runner_paths, list) or not all(
            isinstance(path, str) for path in runner_paths
        ):
            errors.append(f"{label}.runner_identity_paths must be a scalar list")
        elif len(_value_gate_runner_paths(runner_paths)) != 1:
            errors.append(
                f"{label}.runner_identity_paths must contain exactly one */value_gate/runner.py"
            )
        transition = _mapping(contract.get("transition"), f"{label}.transition", errors)
        errors.extend(_exact_keys(transition, TRANSITION_KEYS, f"{label}.transition"))
        for field in TRANSITION_KEYS:
            value = transition.get(field)
            if not isinstance(value, str) or ACTION_ID_RE.fullmatch(value) is None:
                errors.append(f"{label}.transition.{field} must be an exact action ID")
        locks = _mapping(contract.get("locks"), f"{label}.locks", errors)
        errors.extend(_exact_keys(locks, LOCK_KEYS, f"{label}.locks"))
        for field in LOCK_KEYS:
            if type(locks.get(field)) is not bool:
                errors.append(f"{label}.locks.{field} must be boolean")
    return by_id


def _action_fields(contract: Mapping[str, object]) -> dict[str, object]:
    return {field: copy.deepcopy(contract.get(field)) for field in ACTION_KEYS}


def _active_slice_id(manifest: Mapping[str, object], errors: list[str]) -> str | None:
    development = _mapping(manifest.get("development"), "development", errors)
    slices = _mapping(development.get("slices"), "development.slices", errors)
    active: list[str] = []
    for identifier, raw_slice in slices.items():
        if not isinstance(raw_slice, dict):
            continue
        if (
            raw_slice.get("status") in ACTIVE_SLICE_STATUSES
            and raw_slice.get("coding_input") is True
        ):
            active.append(identifier)
    if len(active) != 1:
        errors.append(
            "manifest must have exactly one authorized/in-progress coding_input=true Slice"
        )
        return None
    return active[0]


def _resolved_pass(
    cases: Mapping[str, Sequence[VerificationCase]] | None,
    case_id: str,
    label: str,
    *,
    documents: Mapping[str, Mapping[str, object]] | None = None,
    plan_revision_ref: object = None,
    control: Mapping[str, object] | None = None,
    result_evidence_artifacts: Mapping[str, str | bytes] | None = None,
    runner_files: Mapping[str, str] | None = None,
    configured_identities: Sequence[str] = (),
) -> list[str]:
    if cases is None:
        return [f"{label} cannot be checked without the Verification Matrix"]
    rows = list(cases.get(case_id, ()))
    if len(rows) != 1:
        return [f"{label} must resolve to exactly one Verification row"]
    row = rows[0]
    result_matches: list[str] = []
    registered: dict[str, dict[str, object]] = {}
    if control is not None:
        current = control.get("current_action")
        if isinstance(current, dict) and isinstance(current.get("id"), str):
            registered[str(current["id"])] = current
        contract_errors: list[str] = []
        registered.update(_registered_action_contracts(control, contract_errors))
        if contract_errors:
            return contract_errors
    mechanically_produced = any(
        isinstance(action.get("produced_case_ids"), list)
        and case_id in action["produced_case_ids"]
        for action in registered.values()
    )
    if row.verdict == "PASS":
        if row.evidence.strip().lower() in {
            "",
            "pending",
            "not-executed",
            "none",
            "n/a",
        }:
            return [f"{label} PASS must bind non-pending evidence"]
        if not mechanically_produced:
            return []
    if row.verdict in {"FAIL", "INVALID"}:
        return [f"{label} must be PASS before the current action is authorized"]

    # A newly completed mechanical Gate need not edit the matrix in the same
    # transition.  Its exact, version-bound Result is the authorization truth;
    # the Matrix remains an index and may still say NOT-RUN until governance
    # write-back.  Explicit Matrix FAIL/INVALID above always wins.
    if documents is not None and isinstance(plan_revision_ref, str):
        for identifier, metadata in documents.items():
            action_ref = metadata.get("action_ref")
            action = registered.get(str(action_ref))
            if RESULT_ID_RE.fullmatch(identifier) is None or action is None:
                continue
            if metadata.get("__path__") != action.get("result_path"):
                continue
            _, outcomes, result_errors = validate_gate_result(
                metadata,
                action,
                plan_revision_ref,
                (result_evidence_artifacts or {}).get(identifier),
                runner_files,
                configured_identities,
            )
            if not result_errors and outcomes.get(case_id) == "PASS":
                result_matches.append(identifier)
    if len(result_matches) == 1:
        return []
    if len(result_matches) > 1:
        return [f"{label} has multiple exact PASS Results"]
    return [f"{label} must be PASS before the current action is authorized"]


def _validate_plan_revision_ref(
    reference: object,
    documents: Mapping[str, Mapping[str, object]] | None,
    label: str,
    authorization_refs: object = None,
) -> list[str]:
    if not isinstance(reference, str) or PDR_ID_RE.fullmatch(reference) is None:
        return [f"{label} must be an exact PDR ID"]
    if documents is None:
        return []
    pdr = documents.get(reference)
    if pdr is None:
        return [f"{label} does not resolve: {reference}"]
    errors: list[str] = []
    if pdr.get("kind") != "project-decision" or pdr.get("status") != "accepted":
        errors.append(f"{label} must resolve to an accepted project-decision")
    dependencies = pdr.get("depends_on")
    finding_dependencies = (
        [
            item
            for item in dependencies
            if isinstance(item, str) and FINDING_ID_RE.fullmatch(item) is not None
        ]
        if isinstance(dependencies, list)
        else []
    )
    if not finding_dependencies:
        errors.append(f"{label} PDR must depend on at least one exact Finding")
    else:
        unresolved = [
            item
            for item in finding_dependencies
            if documents.get(item, {}).get("kind") != "implementation-finding"
        ]
        if unresolved:
            errors.append(
                f"{label} PDR Finding refs do not resolve: {', '.join(unresolved)}"
            )
    decision_ref = pdr.get("decision_ref")
    if not isinstance(decision_ref, str) or AUTHORIZATION_RE.fullmatch(decision_ref) is None:
        errors.append(f"{label} PDR must bind an exact authorization decision_ref")
    if isinstance(authorization_refs, list) and all(
        isinstance(item, str) for item in authorization_refs
    ):
        declared = set(authorization_refs)
        bound = {
            value
            for key, value in pdr.items()
            if key.endswith("_ref")
            and isinstance(value, str)
            and AUTHORIZATION_RE.fullmatch(value) is not None
        }
        if declared != bound:
            errors.append(
                f"{label} authorization_refs must exactly match the PDR authorization references"
            )
    return errors


def _validate_plan_revision_lineage(
    base_manifest: Mapping[str, object],
    base_control: Mapping[str, object],
    target_control: Mapping[str, object],
    base_action: Mapping[str, object],
    base_documents: Mapping[str, Mapping[str, object]] | None,
    target_documents: Mapping[str, Mapping[str, object]] | None,
    base_document_authorization_refs: Iterable[str] | None = None,
    base_result_evidence_artifacts: Mapping[str, str | bytes] | None = None,
) -> list[str]:
    """Require a forward-only PDR with fresh authority and base Result lineage."""

    errors: list[str] = []
    base_reference = base_control.get("plan_revision_ref")
    target_reference = target_control.get("plan_revision_ref")
    base_match = (
        PDR_SEQUENCE_RE.fullmatch(base_reference)
        if isinstance(base_reference, str)
        else None
    )
    target_match = (
        PDR_SEQUENCE_RE.fullmatch(target_reference)
        if isinstance(target_reference, str)
        else None
    )
    if base_match is None or target_match is None:
        return errors
    if target_match.group("iteration") != base_match.group("iteration"):
        errors.append("target plan revision PDR must remain in the base iteration")
    elif int(target_match.group("sequence")) <= int(base_match.group("sequence")):
        errors.append(
            "target plan revision PDR sequence must be strictly greater than the base PDR sequence"
        )

    target_pdr = (
        target_documents.get(target_reference)
        if target_documents is not None
        else None
    )
    if target_pdr is None:
        return errors
    base_result_ref = base_action.get("result_ref")
    dependencies = target_pdr.get("depends_on")
    if (
        not isinstance(base_result_ref, str)
        or not isinstance(dependencies, list)
        or base_result_ref not in dependencies
    ):
        errors.append(
            "target plan revision PDR depends_on must include the base governance action sealed Result ref"
        )

    decision_ref = target_pdr.get("decision_ref")
    base_authorization_refs = base_control.get("authorization_refs")
    if (
        isinstance(base_authorization_refs, list)
        and decision_ref in base_authorization_refs
    ):
        errors.append(
            "target plan revision PDR decision_ref must be new and absent from base authorization_refs"
        )
    def authorization_values(value: object) -> set[str]:
        if isinstance(value, str):
            return {match.group(0) for match in AUTHORIZATION_RE.finditer(value)}
        if isinstance(value, Mapping):
            found: set[str] = set()
            for nested in value.values():
                found.update(authorization_values(nested))
            return found
        if isinstance(value, (list, tuple, set, frozenset)):
            found = set()
            for nested in value:
                found.update(authorization_values(nested))
            return found
        return set()

    recovery_pre_registration = False
    recovery_artifact_raw = (base_result_evidence_artifacts or {}).get(
        ITER010_PLAN_RECOVERY_RESULT_ID
    )
    if isinstance(recovery_artifact_raw, bytes):
        try:
            recovery_artifact_raw = recovery_artifact_raw.decode(
                "utf-8", errors="strict"
            )
        except UnicodeDecodeError:
            recovery_artifact_raw = None
    recovery_artifact: object = None
    if isinstance(recovery_artifact_raw, str):
        try:
            recovery_artifact = json.loads(recovery_artifact_raw)
        except json.JSONDecodeError:
            recovery_artifact = None
    expected_recovery_action_evidence = {
        "schema": "ITER010_USER_PLAN_RECOVERY_EVIDENCE@1",
        "target_plan_revision_ref": ITER010_PLAN_RECOVERY_TARGET_REVISION,
        "authorization_refs": [
            ITER010_PLAN_CHANGE_AUTHORIZATION_REF,
            ITER010_PLAN_RECOVERY_AUTHORIZATION_REF,
        ],
        "change_boundary": {
            "plan_governance_change_authorized": True,
            "product_code_change_authorized": False,
            "external_execution_authorized": False,
        },
    }
    recovery_pre_registration = (
        base_reference == ITER010_PLAN_RECOVERY_BASE_REVISION
        and target_reference == ITER010_PLAN_RECOVERY_TARGET_REVISION
        and base_action.get("id") == ITER010_PLAN_RECOVERY_ACTION_ID
        and base_action.get("kind") == "governance"
        and base_action.get("case_id") == ITER010_PLAN_RECOVERY_CASE_ID
        and base_action.get("result_ref") == ITER010_PLAN_RECOVERY_RESULT_ID
        and base_action.get("evidence_verifier")
        == ITER010_PLAN_RECOVERY_VERIFIER
        and decision_ref == ITER010_PLAN_CHANGE_AUTHORIZATION_REF
        and target_control.get("authorization_refs")
        == [
            ITER010_PLAN_CHANGE_AUTHORIZATION_REF,
            ITER010_PLAN_RECOVERY_AUTHORIZATION_REF,
        ]
        and isinstance(recovery_artifact, Mapping)
        and recovery_artifact.get("result_id")
        == ITER010_PLAN_RECOVERY_RESULT_ID
        and recovery_artifact.get("plan_revision_ref")
        == ITER010_PLAN_RECOVERY_BASE_REVISION
        and recovery_artifact.get("action_ref")
        == ITER010_PLAN_RECOVERY_ACTION_ID
        and recovery_artifact.get("verification_case_id")
        == ITER010_PLAN_RECOVERY_CASE_ID
        and recovery_artifact.get("plan_gate_verdict") == "PASS"
        and recovery_artifact.get("evidence_verifier")
        == ITER010_PLAN_RECOVERY_VERIFIER
        and recovery_artifact.get("action_evidence")
        == expected_recovery_action_evidence
    )

    previously_used_authority = set(base_document_authorization_refs or ())
    previously_used_authority.update(authorization_values(base_manifest))
    for metadata in (base_documents or {}).values():
        previously_used_authority.update(authorization_values(metadata))
    if (
        isinstance(decision_ref, str)
        and decision_ref in previously_used_authority
        and not recovery_pre_registration
    ):
        errors.append(
            "target plan revision PDR decision_ref must never have appeared in the trusted base documents"
        )
    if isinstance(decision_ref, str) and AUTHORIZATION_RE.fullmatch(decision_ref):
        decision_digest = decision_ref.rsplit(":", 1)[-1]
        historical_digests = {
            reference.rsplit(":", 1)[-1]
            for reference in previously_used_authority
            if AUTHORIZATION_RE.fullmatch(reference) is not None
        }
        if decision_digest in historical_digests and not recovery_pre_registration:
            errors.append(
                "target plan revision PDR decision_ref content digest must never have appeared under any authority scheme in the trusted base documents"
            )
    return errors


def _route_policy_migration_bridge_errors(
    manifest: Mapping[str, object],
) -> list[str]:
    """Validate the one-commit bridge required by the trusted @1 parent gate."""

    migration = manifest.get("provider_route_policy_migration")
    if migration is None:
        return []
    if not isinstance(migration, Mapping):
        return ["provider_route_policy_migration must be a mapping"]
    errors = _exact_keys(
        migration,
        ROUTE_POLICY_MIGRATION_KEYS,
        "provider_route_policy_migration",
    )
    for field, expected in ROUTE_POLICY_MIGRATION_EXPECTED.items():
        if migration.get(field) != expected:
            errors.append(
                f"provider_route_policy_migration.{field} must equal {expected}"
            )
    control = _control(manifest)
    if not isinstance(control, Mapping) or control.get("plan_revision_ref") != (
        ITER010_PLAN_RECOVERY_TARGET_REVISION
    ):
        errors.append(
            "provider_route_policy_migration is limited to ITER-010-PDR-010"
        )
    action = control.get("current_action") if isinstance(control, Mapping) else None
    if not isinstance(action, Mapping) or action.get("id") != (
        ITER010_MVP_LIGHT_EXPERIENCE_ACTION_ID
    ):
        errors.append(
            "provider_route_policy_migration requires the ITER-010 experience action"
        )
    policy = manifest.get("provider_route_policy")
    configurations = manifest.get("execution_profile_configurations")
    if not isinstance(policy, Mapping) or policy.get("schema") != (
        LEGACY_PROVIDER_ROUTE_POLICY_SCHEMA
    ):
        errors.append(
            "provider_route_policy_migration requires the trusted legacy route schema"
        )
    if not isinstance(configurations, Mapping) or configurations.get("schema") != (
        LEGACY_EXECUTION_PROFILE_CONFIGURATION_SCHEMA
    ):
        errors.append(
            "provider_route_policy_migration requires the trusted legacy execution-profile schema"
        )
    return errors


def _failure_handoff_recovery_errors(
    manifest: Mapping[str, object],
) -> list[str]:
    """Keep the one-use PDR-011 recovery root exact after its trust cut-over."""

    control = _control(manifest)
    pdr011_active = (
        isinstance(control, Mapping)
        and control.get("plan_revision_ref")
        == ITER010_FAILURE_HANDOFF_RECOVERY_TARGET_REVISION
    )
    recovery = manifest.get("mvp_failure_handoff_recovery")
    if recovery is None:
        return (
            ["ITER-010-PDR-011 requires mvp_failure_handoff_recovery"]
            if pdr011_active
            else []
        )
    if not isinstance(recovery, Mapping):
        return ["mvp_failure_handoff_recovery must be a mapping"]
    expected = {
        "schema": ITER010_FAILURE_HANDOFF_RECOVERY_SCHEMA,
        "status": "authorized-recovery-root-installed",
        "authorization_ref": ITER010_FAILURE_HANDOFF_RECOVERY_AUTHORIZATION_REF,
        "authorization_reusable": False,
        "trusted_base_commit": ITER010_FAILURE_HANDOFF_RECOVERY_BASE_COMMIT,
        "trusted_base_tree": ITER010_FAILURE_HANDOFF_RECOVERY_BASE_TREE,
        "interrupted_plan_revision_ref": "ITER-010-PDR-010",
        "interrupted_action_id": ITER010_MVP_LIGHT_EXPERIENCE_ACTION_ID,
        "target_plan_revision_ref": (
            ITER010_FAILURE_HANDOFF_RECOVERY_TARGET_REVISION
        ),
        "scope": "governance-only-failure-handoff-contract-recovery",
        "old_gate_compliance_claimed": False,
        "product_code_changes_allowed": False,
        "external_execution_allowed": False,
        "one_time_recovery": True,
    }
    errors = _exact_keys(
        recovery,
        set(expected),
        "mvp_failure_handoff_recovery",
    )
    for field, value in expected.items():
        if recovery.get(field) != value or type(recovery.get(field)) is not type(value):
            errors.append(
                f"mvp_failure_handoff_recovery.{field} must equal {value}"
            )

    if not isinstance(control, Mapping):
        return errors + [
            "mvp_failure_handoff_recovery requires plan_execution_control"
        ]
    if control.get("plan_revision_ref") != (
        ITER010_FAILURE_HANDOFF_RECOVERY_TARGET_REVISION
    ):
        errors.append("failure handoff recovery is limited to ITER-010-PDR-011")
    if control.get("authorization_refs") != [
        ITER010_FAILURE_HANDOFF_RECOVERY_AUTHORIZATION_REF
    ]:
        errors.append(
            "failure handoff recovery must bind only its exact one-use authorization"
        )
    action = control.get("current_action")
    if isinstance(action, Mapping):
        action_identity = (action.get("id"), action.get("case_id"))
        allowed_action_identities = {
            (
                ITER010_MVP_LIGHT_EXPERIENCE_ACTION_ID,
                ITER010_MVP_LIGHT_EXPERIENCE_CASE_ID,
            ): "mvp-failure-handoff",
            (
                ITER010_MVP_LIGHT_DIRECTION_ACTION_ID,
                ITER010_MVP_LIGHT_DIRECTION_CASE_ID,
            ): "governance",
        }
        if action_identity not in allowed_action_identities or (
            action.get("kind")
            != allowed_action_identities.get(action_identity)
        ) or action.get("evidence_verifier") != ITER010_MVP_LIGHT_VERIFIER:
            errors.append(
                "failure handoff recovery must preserve a registered PDR-011 action and use ITER010_MVP_LIGHT@3"
            )
        if (
            action.get("coding_allowed") is not False
            or action.get("external_execution_allowed") is not False
        ):
            errors.append(
                "failure handoff recovery must stop coding and external execution"
            )
    else:
        errors.append("failure handoff recovery current_action must be a mapping")
    locks = control.get("locks")
    if not isinstance(locks, Mapping) or any(
        locks.get(field) is not True for field in LOCK_KEYS
    ):
        errors.append("failure handoff recovery must keep every execution lock closed")
    return errors


def _is_route_policy_migration_bridge(manifest: Mapping[str, object]) -> bool:
    return (
        manifest.get("provider_route_policy_migration") is not None
        and not _route_policy_migration_bridge_errors(manifest)
    )


def _fallback_admission_policy_plugin_ref(
    manifest: Mapping[str, object],
) -> object:
    """Resolve the configured fallback plugin without leaking it into route policy."""

    configurations = manifest.get("execution_profile_configurations")
    if isinstance(configurations, Mapping):
        fallback = configurations.get("fallback")
        if isinstance(fallback, Mapping) and "admission_policy_plugin_ref" in fallback:
            return fallback.get("admission_policy_plugin_ref")
    # Historical trusted plans stored this configuration ref in policy.  It is
    # read only so an already-sealed trusted parent can authorize its cutover.
    policy = manifest.get("provider_route_policy")
    return (
        policy.get("fallback_admission_policy_plugin_ref")
        if isinstance(policy, Mapping)
        else None
    )


def _configured_execution_profiles(
    manifest: Mapping[str, object],
) -> tuple[dict[str, Mapping[str, object]], tuple[str, ...], list[str]]:
    """Resolve concrete identities only from execution-profile configuration."""

    errors: list[str] = []
    policy = manifest.get("provider_route_policy")
    if not isinstance(policy, Mapping):
        return {}, (), ["provider_route_policy must be a mapping"]
    configurations = manifest.get("execution_profile_configurations")
    if not isinstance(configurations, Mapping):
        return {}, (), ["execution_profile_configurations must be a mapping"]
    for field in (
        "preferred_execution_profile_ref",
        "fallback_execution_profile_ref",
    ):
        value = policy.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"provider_route_policy.{field} must be a non-empty string"
            )

    configuration_schema = configurations.get("schema")
    if configuration_schema not in {
        EXECUTION_PROFILE_CONFIGURATION_SCHEMA,
        LEGACY_EXECUTION_PROFILE_CONFIGURATION_SCHEMA,
    }:
        errors.append(
            "execution_profile_configurations.schema must equal "
            f"{EXECUTION_PROFILE_CONFIGURATION_SCHEMA}"
        )
    if set(configurations) != {"schema", "preferred", "fallback"}:
        errors.append(
            "execution_profile_configurations must contain exactly schema, preferred, and fallback"
        )

    resolved: dict[str, Mapping[str, object]] = {}
    identities: list[str] = []
    legacy_configuration = (
        configuration_schema == LEGACY_EXECUTION_PROFILE_CONFIGURATION_SCHEMA
    )
    for role, profile_field in (
        ("preferred", "preferred_execution_profile_ref"),
        ("fallback", "fallback_execution_profile_ref"),
    ):
        profile = configurations.get(role)
        if not isinstance(profile, Mapping):
            errors.append(f"execution_profile_configurations.{role} must be a mapping")
            continue
        expected_keys = PREFERRED_EXECUTION_PROFILE_CONFIGURATION_KEYS
        if role == "fallback" and not legacy_configuration:
            expected_keys = FALLBACK_EXECUTION_PROFILE_CONFIGURATION_KEYS
        if set(profile) != expected_keys:
            errors.append(
                f"execution_profile_configurations.{role} must contain exactly the model-transparent configuration fields"
            )
        resolved[role] = profile
        for field in expected_keys:
            value = profile.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"execution_profile_configurations.{role}.{field} must be a non-empty string"
                )
        if profile.get("execution_profile_ref") != policy.get(profile_field):
            errors.append(
                f"execution_profile_configurations.{role}.execution_profile_ref must equal provider_route_policy.{profile_field}"
            )
        for field in ("provider_identity", "model_identity"):
            value = profile.get(field)
            if isinstance(value, str) and value.strip():
                identities.append(value.strip().lower())

    plugin_ref = _fallback_admission_policy_plugin_ref(manifest)
    if not isinstance(plugin_ref, str) or not plugin_ref.strip():
        errors.append(
            "execution_profile_configurations.fallback.admission_policy_plugin_ref must be a non-empty configuration reference"
        )
    elif not isinstance(manifest.get(plugin_ref), Mapping):
        errors.append(
            "execution_profile_configurations.fallback.admission_policy_plugin_ref must resolve to a configuration object"
        )
    preferred_ref = policy.get("preferred_execution_profile_ref")
    fallback_ref = policy.get("fallback_execution_profile_ref")
    if (
        isinstance(preferred_ref, str)
        and isinstance(fallback_ref, str)
        and preferred_ref == fallback_ref
    ):
        errors.append("preferred and fallback execution profile refs must differ")
    preferred_profile = resolved.get("preferred")
    fallback_profile = resolved.get("fallback")
    preferred_provider = (
        preferred_profile.get("provider_identity")
        if isinstance(preferred_profile, Mapping)
        else None
    )
    fallback_provider = (
        fallback_profile.get("provider_identity")
        if isinstance(fallback_profile, Mapping)
        else None
    )
    if (
        isinstance(preferred_provider, str)
        and isinstance(fallback_provider, str)
        and preferred_provider.lower() == fallback_provider.lower()
    ):
        errors.append("preferred and fallback Provider identities must differ")
    return resolved, tuple(dict.fromkeys(identities)), errors


_GENERIC_ROUTE_IDENTITY_TOKENS = {
    "configured",
    "primary",
    "preferred",
    "fallback",
    "provider",
    "identity",
    "model",
    "route",
}

_CONCRETE_IDENTITY_FIELD_NAMES = {
    "provider_identity",
    "model_identity",
    "provider_name",
    "model_name",
    "provider_id",
    "model_id",
    "model_ref",
    "provider_type",
    "actual_model_fingerprint",
    "primary_provider",
    "preferred_provider",
    "fallback_provider",
    "preferred_model_identity",
    "fallback_model_identity",
}
_NON_AVAILABILITY_FALLBACK_TOKENS = {
    "provider-unavailable",
    "provider-http-error",
    "provider-outcome-unknown",
    "provider-output-invalid",
    "structured-output-invalid",
    "model-review-rejected",
}


def _identity_is_present(value: object, identity: str) -> bool:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    rendered_tokens = {
        token for token in re.split(r"[^a-z0-9]+", rendered) if token
    }
    normalized_identity = re.sub(r"[^a-z0-9]+", "", identity)
    normalized_rendered = re.sub(r"[^a-z0-9]+", "", rendered)
    identity_tokens = {
        token
        for token in re.split(r"[^a-z0-9]+", identity)
        if len(token) >= 3
        and not token.isdigit()
        and token not in _GENERIC_ROUTE_IDENTITY_TOKENS
    }
    return (
        identity in rendered
        or (normalized_identity and normalized_identity in normalized_rendered)
        or bool(identity_tokens.intersection(rendered_tokens))
    )


def _configured_identity_errors(
    value: object, identities: Sequence[str], label: str
) -> list[str]:
    return [
        f"{label} must not contain configured Provider/model identity {identity}"
        for identity in identities
        if _identity_is_present(value, identity)
    ]


def _concrete_identity_field_errors(value: object, label: str) -> list[str]:
    """Reject concrete identity-bearing inputs outside profile configuration."""

    errors: list[str] = []

    def visit(candidate: object, path: str) -> None:
        if isinstance(candidate, Mapping):
            for key, item in candidate.items():
                field = str(key).lower().replace("-", "_")
                child_path = f"{path}.{key}"
                if field in _CONCRETE_IDENTITY_FIELD_NAMES:
                    errors.append(
                        f"{child_path} is a concrete Provider/model identity input; use an execution-profile ref"
                    )
                visit(item, child_path)
        elif isinstance(candidate, list):
            for index, item in enumerate(candidate):
                visit(item, f"{path}[{index}]")

    visit(value, label)
    return errors


def _non_availability_fallback_input_errors(
    value: object, label: str
) -> list[str]:
    """Reject application-output or review outcomes as executable fallback inputs."""

    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    normalized = re.sub(r"[_\s]+", "-", rendered)
    return [
        f"{label} must not branch fallback on {token}"
        for token in sorted(_NON_AVAILABILITY_FALLBACK_TOKENS)
        if token in normalized
    ]


def _validate_current_provider_route_policy(
    manifest: Mapping[str, object],
    identities: Sequence[str],
    *,
    allow_legacy: bool,
) -> list[str]:
    """Validate the closed, identity-free, availability-only route policy."""

    policy = manifest.get("provider_route_policy")
    if not isinstance(policy, Mapping):
        return ["provider_route_policy must be a mapping"]
    if allow_legacy and policy.get("schema") == LEGACY_PROVIDER_ROUTE_POLICY_SCHEMA:
        return []

    errors = _exact_keys(policy, PROVIDER_ROUTE_POLICY_KEYS, "provider_route_policy")
    exact_values: tuple[tuple[str, object], ...] = (
        ("schema", PROVIDER_ROUTE_POLICY_SCHEMA),
        ("preference_order", ["preferred", "fallback"]),
        ("availability_owner", "provider-availability-boundary"),
        ("required_fallback_verdict", PREFERRED_PROFILE_UNAVAILABLE_VERDICT),
        (
            "product_control_flow_allowed_inputs",
            "route-role,execution-profile-ref-and-digest,availability-verdict",
        ),
        (
            "product_control_flow_forbidden_inputs",
            "provider-identity,model-identity",
        ),
        ("verification_case_id", "V-MODEL-TRANSPARENT-ROUTING-001"),
        ("fallback_dispatch_requires_verification_pass", True),
        ("preferred_unavailable_evidence_required", True),
        ("implementation_gap_counts_as_preferred_unavailable", False),
        (
            "fallback_requires_preferred_attempt_terminal_without_authorized_answer",
            True,
        ),
        (
            "fallback_trigger",
            "sealed-provider-availability-verdict:"
            + PREFERRED_PROFILE_UNAVAILABLE_VERDICT,
        ),
        ("fallback_eligible_outcomes", [PREFERRED_PROFILE_UNAVAILABLE_OUTCOME]),
        ("structured_output_invalid_allows_fallback", False),
        ("model_review_rejected_allows_fallback", False),
        (
            "raw_http_or_outcome_without_availability_verdict_allows_fallback",
            False,
        ),
        ("application_source_security_failure_allows_fallback", False),
        ("capability_failure_must_not_be_misclassified_as_unavailable", True),
        ("same_profile_application_repair_is_transport_request_retry", False),
        (
            "same_profile_application_repair_exhausted_action",
            "fail-current-turn-with-exact-reason-without-fallback",
        ),
        ("late_preferred_result_overwrite_allowed", False),
        ("maximum_fallback_execution_profile_attempts", 1),
        ("transport_request_retry_allowed", False),
        ("cost_can_reduce_answer_quality", False),
        ("current_started_interaction_unit_must_keep_full_quality_chain", True),
    )
    for field, expected in exact_values:
        if policy.get(field) != expected:
            errors.append(
                f"provider_route_policy.{field} must equal {expected}"
            )
    for field in (
        "preferred_execution_profile_ref",
        "fallback_execution_profile_ref",
    ):
        value = policy.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"provider_route_policy.{field} must be non-empty")
    configurations = manifest.get("execution_profile_configurations")
    if not isinstance(configurations, Mapping) or configurations.get(
        "schema"
    ) != EXECUTION_PROFILE_CONFIGURATION_SCHEMA:
        errors.append(
            "current provider_route_policy requires "
            f"execution_profile_configurations.schema {EXECUTION_PROFILE_CONFIGURATION_SCHEMA}"
        )
    errors.extend(
        _configured_identity_errors(
            policy,
            identities,
            "provider_route_policy",
        )
    )
    errors.extend(_concrete_identity_field_errors(policy, "provider_route_policy"))
    return errors


def _provider_neutral_root_input_errors(value: object, label: str) -> list[str]:
    """Validate a closed, route-agnostic index of frozen evaluation inputs."""

    if not isinstance(value, Mapping):
        return [f"{label} must be an object"]
    errors = _exact_keys(
        value,
        {"schema", "question_ids", "system_arm_ids", "entries"},
        label,
    )
    if value.get("schema") != PROVIDER_NEUTRAL_ROOT_INPUT_SCHEMA:
        errors.append(
            f"{label}.schema must equal {PROVIDER_NEUTRAL_ROOT_INPUT_SCHEMA}"
        )

    question_ids = value.get("question_ids")
    valid_question_ids = (
        isinstance(question_ids, list)
        and len(question_ids) == 3
        and len(set(map(str, question_ids))) == 3
        and all(
            isinstance(item, str)
            and re.fullmatch(r"Q-[A-Z0-9][A-Z0-9._-]*", item) is not None
            for item in question_ids
        )
    )
    if not valid_question_ids:
        errors.append(
            f"{label}.question_ids must contain exactly three unique question IDs"
        )

    system_arm_ids = value.get("system_arm_ids")
    if system_arm_ids != list(PROVIDER_NEUTRAL_SYSTEM_ARM_IDS):
        errors.append(
            f"{label}.system_arm_ids must exactly equal the provider-neutral system arms"
        )

    entries = value.get("entries")
    if not isinstance(entries, list):
        errors.append(f"{label}.entries must be a list")
        return errors
    pairs: list[tuple[str, str]] = []
    for index, entry in enumerate(entries):
        entry_label = f"{label}.entries[{index}]"
        if not isinstance(entry, Mapping):
            errors.append(f"{entry_label} must be an object")
            continue
        errors.extend(
            _exact_keys(
                entry,
                {"question_id", "system_arm_id", "root_input_digest"},
                entry_label,
            )
        )
        question_id = entry.get("question_id")
        system_arm_id = entry.get("system_arm_id")
        if not isinstance(question_id, str) or (
            valid_question_ids and question_id not in question_ids
        ):
            errors.append(f"{entry_label}.question_id is not in question_ids")
        if (
            not isinstance(system_arm_id, str)
            or system_arm_id not in PROVIDER_NEUTRAL_SYSTEM_ARM_IDS
        ):
            errors.append(
                f"{entry_label}.system_arm_id is not a provider-neutral system arm"
            )
        root_digest = entry.get("root_input_digest")
        if not isinstance(root_digest, str) or SHA256_RE.fullmatch(root_digest) is None:
            errors.append(
                f"{entry_label}.root_input_digest must be an exact sha256 digest"
            )
        if isinstance(question_id, str) and isinstance(system_arm_id, str):
            pairs.append((question_id, system_arm_id))

    if valid_question_ids:
        expected_pairs = {
            (question_id, system_arm_id)
            for question_id in question_ids
            for system_arm_id in PROVIDER_NEUTRAL_SYSTEM_ARM_IDS
        }
        if len(pairs) != len(set(pairs)) or set(pairs) != expected_pairs:
            errors.append(
                f"{label}.entries must contain the exact question-by-system-arm Cartesian product without duplicates"
            )
    return errors


def _validate_model_transparent_action_graph(
    manifest: Mapping[str, object],
    *,
    allow_legacy_route_policy: bool = False,
) -> list[str]:
    """Enforce profile-role routing and availability-only fallback branches."""

    migration_errors = _route_policy_migration_bridge_errors(manifest)
    migration_bridge = (
        manifest.get("provider_route_policy_migration") is not None
        and not migration_errors
    )
    _, identities, errors = _configured_execution_profiles(manifest)
    errors.extend(migration_errors)
    errors.extend(
        _validate_current_provider_route_policy(
            manifest,
            identities,
            allow_legacy=allow_legacy_route_policy or migration_bridge,
        )
    )
    for scope_name in ("plan_execution_control", "direction_quality_gate"):
        scope = manifest.get(scope_name)
        if scope is None:
            continue
        errors.extend(
            _configured_identity_errors(
                scope,
                identities,
                f"{scope_name} must use preferred/fallback route roles and",
            )
        )
        errors.extend(_concrete_identity_field_errors(scope, scope_name))
        errors.extend(_non_availability_fallback_input_errors(scope, scope_name))
    return errors


def validate_snapshot(
    manifest: Mapping[str, object],
    *,
    current_metadata: Mapping[str, object] | None = None,
    verification_cases: Mapping[str, Sequence[VerificationCase]] | None = None,
    documents: Mapping[str, Mapping[str, object]] | None = None,
    result_evidence_artifacts: Mapping[str, str | bytes] | None = None,
    runner_files: Mapping[str, str] | None = None,
    allow_legacy_route_policy: bool = False,
) -> list[str]:
    """Validate the single current action and its already-due prerequisites."""

    errors: list[str] = []
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        errors.append("manifest schema_version must equal 2")
    errors.extend(
        _validate_model_transparent_action_graph(
            manifest,
            allow_legacy_route_policy=allow_legacy_route_policy,
        )
    )
    errors.extend(_failure_handoff_recovery_errors(manifest))
    _, configured_identities, _ = _configured_execution_profiles(manifest)
    control = _control(manifest)
    if control is None:
        return sorted(set(errors + ["plan_execution_control must be a mapping"]))
    errors.extend(_exact_keys(control, CONTROL_KEYS, "plan_execution_control"))
    if control.get("schema") != CONTROL_SCHEMA:
        errors.append(f"plan_execution_control.schema must equal {CONTROL_SCHEMA}")
    if control.get("enforcement_mode") != "fail-closed":
        errors.append("plan_execution_control.enforcement_mode must equal fail-closed")
    authorization_refs = control.get("authorization_refs")
    if not isinstance(authorization_refs, list) or not authorization_refs:
        errors.append("plan_execution_control.authorization_refs must be a non-empty scalar list")
    elif not all(
        isinstance(item, str) and AUTHORIZATION_RE.fullmatch(item) is not None
        for item in authorization_refs
    ):
        errors.append(
            "plan_execution_control.authorization_refs must contain only exact authorization refs"
        )
    elif len(authorization_refs) != len(set(authorization_refs)):
        errors.append("plan_execution_control.authorization_refs must not contain duplicates")
    plan_revision_ref = control.get("plan_revision_ref")
    errors.extend(
        _validate_plan_revision_ref(
            plan_revision_ref,
            documents,
            "plan_execution_control.plan_revision_ref",
            authorization_refs,
        )
    )

    action = _mapping(
        control.get("current_action"), "plan_execution_control.current_action", errors
    )
    registered_contracts = _registered_action_contracts(control, errors)
    errors.extend(_exact_keys(action, ACTION_KEYS, "plan_execution_control.current_action"))
    action_id = action.get("id")
    if not isinstance(action_id, str) or ACTION_ID_RE.fullmatch(action_id) is None:
        errors.append("current_action.id must be an exact action ID")
    owner_slice = action.get("owner_slice_ref")
    if not isinstance(owner_slice, str) or SLICE_ID_RE.fullmatch(owner_slice) is None:
        errors.append("current_action.owner_slice_ref must be an exact Slice ID")
    if not isinstance(action.get("kind"), str) or re.fullmatch(
        r"[a-z][a-z0-9-]*", str(action.get("kind", ""))
    ) is None:
        errors.append("current_action.kind must be a lowercase action kind")
    if action.get("status") != "authorized":
        errors.append("current_action.status must equal authorized")
    case_id = action.get("case_id")
    if not isinstance(case_id, str) or CASE_ID_RE.fullmatch(case_id) is None:
        errors.append("current_action.case_id must be an exact Verification Case ID")
    for field in ("coding_allowed", "external_execution_allowed"):
        if type(action.get(field)) is not bool:
            errors.append(f"current_action.{field} must be boolean")
    result_ref = action.get("result_ref")
    if not isinstance(result_ref, str) or RESULT_ID_RE.fullmatch(result_ref) is None:
        errors.append("current_action.result_ref must be an exact Result ID")
    result_path = action.get("result_path")
    errors.extend(_validate_path_rule(result_path, "current_action.result_path"))
    if action.get("evidence_schema") != EVIDENCE_SCHEMA:
        errors.append(f"current_action.evidence_schema must equal {EVIDENCE_SCHEMA}")
    evidence_path = action.get("evidence_path")
    errors.extend(_validate_path_rule(evidence_path, "current_action.evidence_path"))
    evidence_verifier = action.get("evidence_verifier")
    if not isinstance(evidence_verifier, str) or re.fullmatch(
        r"[A-Z][A-Z0-9._-]+@[1-9][0-9]*", evidence_verifier
    ) is None:
        errors.append("current_action.evidence_verifier must be a versioned verifier ID")
    iteration_prefix = (
        owner_slice.split("-SLICE-", 1)[0]
        if isinstance(owner_slice, str) and "-SLICE-" in owner_slice
        else None
    )
    if iteration_prefix is not None:
        if isinstance(action_id, str) and not action_id.startswith(
            iteration_prefix + "-ACTION-"
        ):
            errors.append("current_action.id must belong to owner_slice_ref's Iteration")
        if isinstance(result_ref, str) and not result_ref.startswith(
            iteration_prefix + "-RESULT-"
        ):
            errors.append(
                "current_action.result_ref must belong to owner_slice_ref's Iteration"
            )
        iteration_number = iteration_prefix.removeprefix("ITER-")
        expected_result_prefix = (
            f"docs/project/iterations/iteration-{iteration_number}/results/"
        )
        for field, value in (
            ("result_path", result_path),
            ("evidence_path", evidence_path),
        ):
            if isinstance(value, str) and not value.startswith(expected_result_prefix):
                errors.append(
                    f"current_action.{field} must be inside the owner Iteration results directory"
                )
        if isinstance(plan_revision_ref, str) and not plan_revision_ref.startswith(
            iteration_prefix + "-PDR-"
        ):
            errors.append(
                "plan_execution_control.plan_revision_ref must belong to the owner Iteration"
            )

    for field in (
        "produced_case_ids",
        "runner_identity_paths",
        "prerequisite_case_ids",
        "allowed_change_paths",
        "forbidden_change_paths",
    ):
        values = action.get(field)
        if not isinstance(values, list) or not all(isinstance(item, str) for item in values):
            errors.append(f"current_action.{field} must be a scalar list")
            continue
        if len(values) != len(set(values)):
            errors.append(f"current_action.{field} must not contain duplicates")
        if field == "allowed_change_paths" and not values:
            errors.append("current_action.allowed_change_paths must not be empty")
        if field == "runner_identity_paths" and not values:
            errors.append("current_action.runner_identity_paths must not be empty")
        if field.endswith("change_paths"):
            for index, value in enumerate(values):
                errors.extend(
                    _validate_path_rule(value, f"current_action.{field}[{index}]")
                )
        if field == "runner_identity_paths":
            for index, value in enumerate(values):
                errors.extend(
                    _validate_path_rule(value, f"current_action.runner_identity_paths[{index}]")
                )
            if len(_value_gate_runner_paths(values)) != 1:
                errors.append(
                    "current_action.runner_identity_paths must contain exactly one */value_gate/runner.py"
                )
    produced_cases = action.get("produced_case_ids")
    if isinstance(produced_cases, list):
        if case_id not in produced_cases:
            errors.append("current_action.produced_case_ids must include current_action.case_id")
        for produced_case in produced_cases:
            if (
                not isinstance(produced_case, str)
                or CASE_ID_RE.fullmatch(produced_case) is None
            ):
                errors.append("current_action.produced_case_ids contains an invalid Case ID")

    prerequisites = action.get("prerequisite_case_ids")
    if isinstance(prerequisites, list):
        for prerequisite in prerequisites:
            if not isinstance(prerequisite, str) or CASE_ID_RE.fullmatch(prerequisite) is None:
                errors.append("current_action.prerequisite_case_ids contains an invalid Case ID")
            else:
                errors.extend(
                    _resolved_pass(
                        verification_cases,
                        prerequisite,
                        f"current_action prerequisite {prerequisite}",
                        documents=documents,
                        plan_revision_ref=plan_revision_ref,
                        control=control,
                        result_evidence_artifacts=result_evidence_artifacts,
                        runner_files=runner_files,
                        configured_identities=configured_identities,
                    )
                )
    if verification_cases is not None and isinstance(case_id, str):
        if len(verification_cases.get(case_id, ())) != 1:
            errors.append("current_action.case_id must resolve to exactly one Verification row")

    allowed = action.get("allowed_change_paths")
    forbidden = action.get("forbidden_change_paths")
    for field, value in (("result_path", result_path), ("evidence_path", evidence_path)):
        if isinstance(value, str) and isinstance(allowed, list) and not any(
            isinstance(rule, str) and _path_matches(value, rule) for rule in allowed
        ):
            errors.append(f"current_action.{field} must be included by allowed_change_paths")
        if isinstance(value, str) and isinstance(forbidden, list) and any(
            isinstance(rule, str) and _path_matches(value, rule) for rule in forbidden
        ):
            errors.append(f"current_action.{field} must not be forbidden")

    transition = _mapping(
        control.get("transition"), "plan_execution_control.transition", errors
    )
    errors.extend(_exact_keys(transition, TRANSITION_KEYS, "plan_execution_control.transition"))
    for field in TRANSITION_KEYS:
        value = transition.get(field)
        if not isinstance(value, str) or ACTION_ID_RE.fullmatch(value) is None:
            errors.append(f"plan_execution_control.transition.{field} must be an exact action ID")

    all_actions = {action_id: action} if isinstance(action_id, str) else {}
    all_actions.update(registered_contracts)
    for source_id, source in all_actions.items():
        source_transition = (
            transition if source_id == action_id else source.get("transition")
        )
        if not isinstance(source_transition, dict):
            continue
        for field in TRANSITION_KEYS:
            target_id = source_transition.get(field)
            if target_id != source_id and target_id not in registered_contracts:
                errors.append(
                    f"action graph target {target_id} from {source_id}.{field} must have a pre-registered contract"
                )

    governance_contracts = [
        contract
        for contract in registered_contracts.values()
        if contract.get("kind") == "governance"
    ]
    if not governance_contracts:
        errors.append("next_action_contracts must include a governance plan-revision action")
    for contract in governance_contracts:
        if (
            contract.get("coding_allowed") is not False
            or contract.get("external_execution_allowed") is not False
        ):
            errors.append("governance plan-revision actions must forbid coding and external execution")
        contract_locks = contract.get("locks")
        if not isinstance(contract_locks, dict) or any(
            contract_locks.get(field) is not True for field in LOCK_KEYS
        ):
            errors.append("governance plan-revision actions must keep every execution lock closed")

    if action.get("external_execution_allowed") is True:
        if not isinstance(prerequisites, list) or PUBLIC_SOURCE_AUTHORITY_CASE_ID not in prerequisites:
            errors.append(
                f"external current actions must require {PUBLIC_SOURCE_AUTHORITY_CASE_ID}"
            )

    locks = _mapping(control.get("locks"), "plan_execution_control.locks", errors)
    errors.extend(_exact_keys(locks, LOCK_KEYS, "plan_execution_control.locks"))
    for field in LOCK_KEYS:
        if type(locks.get(field)) is not bool:
            errors.append(f"plan_execution_control.locks.{field} must be boolean")

    promoted_contract = (
        registered_contracts.get(action_id) if isinstance(action_id, str) else None
    )
    if promoted_contract is not None:
        if action != _action_fields(promoted_contract):
            errors.append("current_action must exactly match its pre-registered contract")
        if transition != promoted_contract.get("transition"):
            errors.append("current transition must exactly match its pre-registered contract")
        if locks != promoted_contract.get("locks"):
            errors.append("current locks must exactly match its pre-registered contract")
    else:
        for field in LOCK_KEYS:
            if locks.get(field) is not True:
                errors.append(
                    f"unregistered current action keeps plan_execution_control.locks.{field} locked"
                )

    active_slice = _active_slice_id(manifest, errors)
    if active_slice is not None and owner_slice != active_slice:
        errors.append("current_action.owner_slice_ref must equal the unique active Slice")
    if current_metadata is not None:
        if current_metadata.get("plan_revision_ref") != plan_revision_ref:
            errors.append("PROJECT-CURRENT plan_revision_ref must match the manifest")
        if current_metadata.get("next_action") != action_id:
            errors.append("PROJECT-CURRENT next_action must match current_action.id")
        if current_metadata.get("next_action_case_id") != case_id:
            errors.append("PROJECT-CURRENT next_action_case_id must match current_action.case_id")
        if current_metadata.get("active_slice") != owner_slice:
            errors.append("PROJECT-CURRENT active_slice must match current_action.owner_slice_ref")
    return sorted(set(errors))


def _parse_nonnegative_integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]*", value):
        return int(value)
    return None


def _load_evidence_json(text: str) -> dict[str, object]:
    def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise PlanGateError(f"evidence artifact contains duplicate key {key!r}")
            value[key] = item
        return value

    try:
        value = json.loads(
            text,
            object_pairs_hook=unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                PlanGateError(f"evidence artifact contains invalid number {token}")
            ),
        )
    except json.JSONDecodeError as error:
        raise PlanGateError(f"evidence artifact is not valid JSON: {error.msg}") from error
    if not isinstance(value, dict):
        raise PlanGateError("evidence artifact root must be an object")
    return value


def _validate_lightweight_handoff_parent_binding(
    action: Mapping[str, object],
    evidence_text: str | bytes | None,
    trusted_parent_commit: str | None,
    trusted_parent_tree: str | None,
) -> list[str]:
    """Bind an MVP handoff to the actual trusted Git parent, not a claimed SHA."""

    if action.get("evidence_verifier") != ITER010_MVP_LIGHT_VERIFIER:
        return []
    if (
        action.get("id") != ITER010_MVP_LIGHT_EXPERIENCE_ACTION_ID
        or action.get("case_id") != ITER010_MVP_LIGHT_EXPERIENCE_CASE_ID
    ):
        return []
    if not isinstance(trusted_parent_commit, str) or re.fullmatch(
        r"[0-9a-f]{40}", trusted_parent_commit
    ) is None:
        return ["lightweight handoff requires the exact trusted parent commit"]
    if not isinstance(trusted_parent_tree, str) or re.fullmatch(
        r"[0-9a-f]{40}", trusted_parent_tree
    ) is None:
        return ["lightweight handoff requires the exact trusted parent tree"]
    if evidence_text is None:
        return ["lightweight handoff evidence is missing"]
    try:
        text = (
            evidence_text.decode("utf-8", errors="strict")
            if isinstance(evidence_text, bytes)
            else evidence_text
        )
        artifact = _load_evidence_json(text)
    except (UnicodeDecodeError, PlanGateError) as error:
        return [f"lightweight handoff evidence cannot bind the trusted parent: {error}"]
    action_evidence = artifact.get("action_evidence")
    candidate = (
        action_evidence.get("handoff_parent_identity")
        if isinstance(action_evidence, Mapping)
        else None
    )
    if not isinstance(candidate, Mapping):
        return ["lightweight handoff handoff_parent_identity is missing"]
    errors: list[str] = []
    if candidate.get("commit") != trusted_parent_commit:
        errors.append(
            "lightweight handoff parent commit must equal the actual trusted parent commit"
        )
    if candidate.get("tree") != trusted_parent_tree:
        errors.append(
            "lightweight handoff parent tree must equal the actual trusted parent tree"
        )
    return errors


def _canonical_json_digest(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _bound_object_errors(
    evidence: Mapping[str, object],
    object_field: str,
    digest_field: str,
    label: str,
) -> list[str]:
    value = evidence.get(object_field)
    if not isinstance(value, Mapping) or not value:
        return [f"{label}.{object_field} must be a non-empty object"]
    if evidence.get(digest_field) != _canonical_json_digest(value):
        return [
            f"{label}.{digest_field} must match canonical {object_field} values"
        ]
    return []


def _iter010_action_evidence_role(action: Mapping[str, object]) -> str | None:
    if action.get("evidence_verifier") != ITER010_VALUE_GATE_VERIFIER:
        return None
    kind = action.get("kind")
    identifier = str(action.get("id", "")).upper()
    if kind == "four-arm-direction-gate-freeze":
        return "freeze"
    if kind == "fallback-route-batch-refreeze":
        return "fallback-refreeze"
    if kind == "four-arm-direction-quality-gate":
        if "-PREFERRED-" in identifier:
            return "preferred-quality"
        if "-FALLBACK-" in identifier:
            return "fallback-quality"
    return "other"


def _validate_iter010_action_evidence(
    action: Mapping[str, object],
    verdict: str | None,
    evidence: Mapping[str, object],
    configured_identities: Sequence[str] = (),
) -> list[str]:
    """Validate only role/profile contracts; concrete identities remain receipt data."""

    role = _iter010_action_evidence_role(action)
    if role is None:
        return []
    label = "transition evidence artifact action_evidence"
    root_keys = {
        "provider_neutral_root_input_set",
        "provider_neutral_root_input_set_digest",
    }
    quality_keys = root_keys | {
        "route_role",
        "execution_profile_ref",
        "execution_profile",
        "execution_profile_digest",
        "admission_receipt",
        "admission_receipt_digest",
        "terminal_receipt",
        "terminal_receipt_digest",
        "terminal_classification",
        "mixed_execution_profile_batch",
    }
    errors: list[str] = []
    if not configured_identities:
        errors.append(
            "ITER-010 action evidence validation requires trusted configured Provider/model identities"
        )
    if role in {"freeze", "preferred-quality", "fallback-quality", "fallback-refreeze"}:
        errors.extend(
            _provider_neutral_root_input_errors(
                evidence.get("provider_neutral_root_input_set"),
                f"{label}.provider_neutral_root_input_set",
            )
        )
    if role == "freeze":
        errors.extend(_exact_keys(evidence, root_keys, label))
        errors.extend(
            _bound_object_errors(
                evidence,
                "provider_neutral_root_input_set",
                "provider_neutral_root_input_set_digest",
                label,
            )
        )
        errors.extend(
            _configured_identity_errors(
                evidence.get("provider_neutral_root_input_set"),
                configured_identities,
                f"{label}.provider_neutral_root_input_set",
            )
        )
        return errors
    if role in {"preferred-quality", "fallback-quality"}:
        expected_keys = set(quality_keys)
        expected_role = "preferred" if role == "preferred-quality" else "fallback"
        if role == "fallback-quality":
            expected_keys.update(
                {
                    "fallback_refreeze_predecessor_ref",
                    "fallback_refreeze_predecessor_seal_digest",
                    "admission_policy_plugin_ref",
                    "admission_policy_plugin",
                    "admission_policy_plugin_digest",
                }
            )
        errors.extend(_exact_keys(evidence, expected_keys, label))
        if evidence.get("route_role") != expected_role:
            errors.append(f"{label}.route_role must equal {expected_role}")
        if evidence.get("mixed_execution_profile_batch") is not False:
            errors.append(
                f"{label}.mixed_execution_profile_batch must equal false"
            )
        terminal = evidence.get("terminal_classification")
        if terminal not in {"AVAILABLE", "TERMINAL_UNAVAILABLE", "OTHER_INVALID"}:
            errors.append(f"{label}.terminal_classification is invalid")
        if verdict == "PASS" and terminal != "AVAILABLE":
            errors.append(f"{label}.terminal_classification must be AVAILABLE for PASS")
        if verdict == "INVALID" and terminal == "AVAILABLE":
            errors.append(
                f"{label}.terminal_classification must identify the invalid terminal class"
            )
        for object_field, digest_field in (
            (
                "provider_neutral_root_input_set",
                "provider_neutral_root_input_set_digest",
            ),
            ("execution_profile", "execution_profile_digest"),
            ("admission_receipt", "admission_receipt_digest"),
            ("terminal_receipt", "terminal_receipt_digest"),
        ):
            errors.extend(
                _bound_object_errors(evidence, object_field, digest_field, label)
            )
        if not isinstance(evidence.get("execution_profile_ref"), str) or not str(
            evidence.get("execution_profile_ref")
        ).strip():
            errors.append(f"{label}.execution_profile_ref must be non-empty")
        if role == "fallback-quality":
            for field in (
                "fallback_refreeze_predecessor_seal_digest",
                "admission_policy_plugin_digest",
            ):
                if not isinstance(evidence.get(field), str) or SHA256_RE.fullmatch(
                    str(evidence.get(field))
                ) is None:
                    errors.append(f"{label}.{field} must be an exact sha256 digest")
            for field in (
                "fallback_refreeze_predecessor_ref",
                "admission_policy_plugin_ref",
            ):
                if not isinstance(evidence.get(field), str) or not str(
                    evidence.get(field)
                ).strip():
                    errors.append(f"{label}.{field} must be non-empty")
            errors.extend(
                _bound_object_errors(
                    evidence,
                    "admission_policy_plugin",
                    "admission_policy_plugin_digest",
                    label,
                )
            )
        errors.extend(
            _configured_identity_errors(
                evidence.get("provider_neutral_root_input_set"),
                configured_identities,
                f"{label}.provider_neutral_root_input_set",
            )
        )
        return errors
    if role == "fallback-refreeze":
        expected_keys = root_keys | {
            "preferred_invalid_predecessor_ref",
            "preferred_invalid_predecessor_seal_digest",
            "fallback_execution_profile_ref",
            "fallback_execution_profile",
            "fallback_execution_profile_digest",
            "fallback_admission_policy_plugin_ref",
            "fallback_admission_policy_plugin",
            "fallback_admission_policy_plugin_digest",
            "preferred_terminal_classification",
            "mixed_execution_profile_batch",
            "provider_dispatch_count",
            "new_human_authority_requested",
        }
        errors.extend(_exact_keys(evidence, expected_keys, label))
        for field in (
            "preferred_invalid_predecessor_ref",
            "fallback_execution_profile_ref",
            "fallback_admission_policy_plugin_ref",
        ):
            if not isinstance(evidence.get(field), str) or not str(
                evidence.get(field)
            ).strip():
                errors.append(f"{label}.{field} must be non-empty")
        seal = evidence.get("preferred_invalid_predecessor_seal_digest")
        if not isinstance(seal, str) or SHA256_RE.fullmatch(seal) is None:
            errors.append(
                f"{label}.preferred_invalid_predecessor_seal_digest must be an exact sha256 digest"
            )
        terminal = evidence.get("preferred_terminal_classification")
        if terminal not in {"TERMINAL_UNAVAILABLE", "OTHER_INVALID"}:
            errors.append(
                f"{label}.preferred_terminal_classification must identify the preferred route invalid class"
            )
        if verdict == "PASS" and terminal != "TERMINAL_UNAVAILABLE":
            errors.append(
                f"{label}.preferred_terminal_classification must be TERMINAL_UNAVAILABLE for PASS"
            )
        if evidence.get("mixed_execution_profile_batch") is not False:
            errors.append(
                f"{label}.mixed_execution_profile_batch must equal false"
            )
        if evidence.get("provider_dispatch_count") != 0:
            errors.append(f"{label}.provider_dispatch_count must equal zero")
        if evidence.get("new_human_authority_requested") is not False:
            errors.append(
                f"{label}.new_human_authority_requested must equal false"
            )
        for object_field, digest_field in (
            (
                "provider_neutral_root_input_set",
                "provider_neutral_root_input_set_digest",
            ),
            ("fallback_execution_profile", "fallback_execution_profile_digest"),
            (
                "fallback_admission_policy_plugin",
                "fallback_admission_policy_plugin_digest",
            ),
        ):
            errors.extend(
                _bound_object_errors(evidence, object_field, digest_field, label)
            )
        errors.extend(
            _configured_identity_errors(
                evidence.get("provider_neutral_root_input_set"),
                configured_identities,
                f"{label}.provider_neutral_root_input_set",
            )
        )
        return errors
    if evidence:
        errors.append(f"{label} must be empty for this action role")
    return errors


def _runner_identity_digest(
    paths: object, runner_files: Mapping[str, str] | None
) -> tuple[str | None, list[str]]:
    if not isinstance(paths, list) or not paths or not all(
        isinstance(path, str) for path in paths
    ):
        return None, ["current_action.runner_identity_paths must be a non-empty scalar list"]
    errors: list[str] = []
    digest = hashlib.sha256()
    digest.update(b"DEVELOPMENT_PLAN_RUNNER_IDENTITY@1\0")
    for path in paths:
        content = (runner_files or {}).get(path)
        if content is None:
            errors.append(f"runner identity file is missing: {path}")
            continue
        digest.update(path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(content.encode("utf-8"))
        digest.update(b"\0")
    return (None if errors else "sha256:" + digest.hexdigest()), errors


def _rerun_evidence_verifier(
    action: Mapping[str, object],
    evidence_bytes: bytes,
    artifact: Mapping[str, object],
    runner_files: Mapping[str, str] | None,
    runner_identity_digest: str,
    external_model_call_count: int | None,
) -> list[str]:
    """Execute the trusted, self-contained verifier and compare its live output."""

    runner_paths = _value_gate_runner_paths(action.get("runner_identity_paths"))
    if len(runner_paths) != 1:
        return [
            "current_action.runner_identity_paths must contain exactly one */value_gate/runner.py"
        ]
    runner_path = runner_paths[0]
    runner_source = (runner_files or {}).get(runner_path)
    if runner_source is None:
        return [f"trusted base evidence verifier runner is missing: {runner_path}"]
    try:
        with tempfile.TemporaryDirectory(prefix="plan-gate-verifier-") as directory:
            executable = Path(directory) / "runner.py"
            executable.write_bytes(runner_source.encode("utf-8"))
            completed = subprocess.run(
                [
                    str(Path(sys.executable).resolve()),
                    "-I",
                    "-S",
                    str(executable),
                    "verify-plan-evidence",
                ],
                input=evidence_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=directory,
                env={"LANG": "C", "LC_ALL": "C", "PATH": os.defpath},
                timeout=RUNNER_TIMEOUT_SECONDS,
                check=False,
            )
    except subprocess.TimeoutExpired:
        return ["trusted base evidence verifier timed out"]
    except OSError as error:
        return [f"trusted base evidence verifier could not execute: {error}"]
    if completed.returncode != 0:
        return [
            f"trusted base evidence verifier exited with status {completed.returncode}"
        ]
    if completed.stderr:
        return ["trusted base evidence verifier wrote unexpected stderr"]
    if len(completed.stdout) > 1_000_000:
        return ["trusted base evidence verifier stdout exceeded the size limit"]
    try:
        stdout_text = completed.stdout.decode("utf-8", errors="strict")
        live_result = _load_evidence_json(stdout_text)
    except (UnicodeDecodeError, PlanGateError) as error:
        return [f"trusted base evidence verifier stdout is not one exact JSON object: {error}"]

    expected = {
        "evidence_verifier": artifact.get("evidence_verifier"),
        "action_ref": artifact.get("action_ref"),
        "verification_case_id": artifact.get("verification_case_id"),
        "plan_gate_verdict": artifact.get("plan_gate_verdict"),
        "execution_input_digest": artifact.get("execution_input_digest"),
        "runner_identity_digest": runner_identity_digest,
        "verification_report_digest": artifact.get("verification_report_digest"),
        "subject_digest": artifact.get("subject_digest"),
        "external_model_call_count": external_model_call_count,
    }
    missing = sorted(LIVE_VERIFICATION_FIELDS.difference(live_result))
    unexpected = sorted(set(live_result).difference(LIVE_VERIFICATION_FIELDS))
    errors: list[str] = []
    if missing:
        errors.append(
            "trusted base evidence verifier stdout is missing fields: "
            + ", ".join(missing)
        )
    if unexpected:
        errors.append(
            "trusted base evidence verifier stdout contains unexpected fields: "
            + ", ".join(unexpected)
        )
    for field, expected_value in expected.items():
        if field in live_result and (
            live_result.get(field) != expected_value
            or type(live_result.get(field)) is not type(expected_value)
        ):
            errors.append(
                f"trusted base evidence verifier stdout {field} does not match the Result/evidence"
            )
    return errors


def validate_gate_result(
    result: Mapping[str, object] | None,
    action: Mapping[str, object],
    plan_revision_ref: object,
    evidence_text: str | bytes | None,
    runner_files: Mapping[str, str] | None = None,
    configured_identities: Sequence[str] = (),
) -> tuple[str | None, dict[str, str], list[str]]:
    """Validate one Result and its digest-bound machine evidence artifact."""

    errors: list[str] = []
    if result is None:
        return None, {}, [f"transition Result is missing at {action.get('result_path')}"]
    missing = sorted(RESULT_GATE_FIELDS.difference(result))
    if missing:
        errors.append("transition Result is missing fields: " + ", ".join(missing))
    aliases = sorted(RESULT_VERDICT_ALIASES.intersection(result))
    if aliases:
        errors.append("transition Result uses forbidden verdict aliases: " + ", ".join(aliases))

    owner_slice = action.get("owner_slice_ref")
    expected_iteration = (
        str(owner_slice).split("-SLICE-", 1)[0]
        if isinstance(owner_slice, str) and "-SLICE-" in owner_slice
        else None
    )
    exact_fields = {
        "id": action.get("result_ref"),
        "kind": "iteration-result",
        "status": "sealed",
        "authority": "evidence",
        "iteration": expected_iteration,
        "plan_revision_ref": plan_revision_ref,
        "action_ref": action.get("id"),
        "verification_case_id": action.get("case_id"),
        "evidence_schema": action.get("evidence_schema"),
        "evidence_verifier": action.get("evidence_verifier"),
        "evidence_artifact_path": action.get("evidence_path"),
    }
    for field, expected in exact_fields.items():
        if result.get(field) != expected:
            errors.append(f"transition Result {field} must equal {expected}")

    verdict = result.get("plan_gate_verdict")
    if verdict not in VERDICT_TO_TRANSITION_FIELD:
        errors.append("transition Result plan_gate_verdict must be PASS, FAIL, or INVALID")
        verdict_value: str | None = None
    else:
        verdict_value = str(verdict)

    digest_fields = (
        "evidence_artifact_digest",
        "execution_input_digest",
        "runner_identity_digest",
        "runner_receipt_digest",
        "verification_report_digest",
        "subject_digest",
    )
    for field in digest_fields:
        if not isinstance(result.get(field), str) or SHA256_RE.fullmatch(str(result.get(field))) is None:
            errors.append(f"transition Result {field} must be an exact sha256 digest")
    result_call_count = _parse_nonnegative_integer(result.get("external_model_call_count"))
    if result_call_count is None:
        errors.append("transition Result external_model_call_count must be a non-negative integer")

    if evidence_text is None:
        errors.append(f"transition evidence artifact is missing at {action.get('evidence_path')}")
        return verdict_value, {}, errors
    evidence_bytes = (
        evidence_text.encode("utf-8")
        if isinstance(evidence_text, str)
        else evidence_text
    )
    actual_evidence_digest = "sha256:" + hashlib.sha256(
        evidence_bytes
    ).hexdigest()
    if result.get("evidence_artifact_digest") != actual_evidence_digest:
        errors.append("transition Result evidence_artifact_digest does not match the exact artifact bytes")
    try:
        decoded_evidence = evidence_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        errors.append(f"transition evidence artifact is not strict UTF-8: {error}")
        return verdict_value, {}, errors
    try:
        artifact = _load_evidence_json(decoded_evidence)
    except PlanGateError as error:
        errors.append(str(error))
        return verdict_value, {}, errors
    errors.extend(_exact_keys(artifact, EVIDENCE_KEYS, "transition evidence artifact"))

    artifact_bindings = {
        "schema": action.get("evidence_schema"),
        "result_id": action.get("result_ref"),
        "plan_revision_ref": plan_revision_ref,
        "action_ref": action.get("id"),
        "verification_case_id": action.get("case_id"),
        "plan_gate_verdict": verdict_value,
        "evidence_verifier": action.get("evidence_verifier"),
        "evidence_artifact_path": action.get("evidence_path"),
    }
    for field, expected in artifact_bindings.items():
        if artifact.get(field) != expected:
            errors.append(f"transition evidence artifact {field} must equal {expected}")
    for field in digest_fields[1:]:
        if artifact.get(field) != result.get(field):
            errors.append(f"transition evidence artifact {field} must match the Result")
    counters = artifact.get("execution_counters")
    action_evidence = artifact.get("action_evidence")
    if not isinstance(action_evidence, dict):
        errors.append("transition evidence artifact action_evidence must be an object")
    else:
        errors.extend(
            _validate_iter010_action_evidence(
                action,
                verdict_value,
                action_evidence,
                configured_identities,
            )
        )
    parsed_counters: dict[str, int] = {}
    if not isinstance(counters, dict):
        errors.append("transition evidence artifact execution_counters must be an object")
    else:
        errors.extend(
            _exact_keys(
                counters,
                EXECUTION_COUNTER_KEYS,
                "transition evidence artifact execution_counters",
            )
        )
        for field in EXECUTION_COUNTER_KEYS:
            value = _parse_nonnegative_integer(counters.get(field))
            if value is None:
                errors.append(
                    f"transition evidence artifact execution_counters.{field} must be a non-negative integer"
                )
            else:
                parsed_counters[field] = value
    artifact_call_count = parsed_counters.get("external_model_call_count")
    if result_call_count is not None and artifact_call_count != result_call_count:
        errors.append("transition evidence artifact external_model_call_count must match the Result")
    if action.get("external_execution_allowed") is not True and any(
        parsed_counters.values()
    ):
        errors.append("non-external action evidence must report zero external execution counters")
    if action.get("external_execution_allowed") is True and verdict_value == "PASS":
        for field in (
            "external_model_call_count",
            "provider_dispatch_count",
            "http_dispatch_count",
        ):
            if parsed_counters.get(field, 0) <= 0:
                errors.append(
                    f"external PASS evidence must report a positive {field}"
                )
        if parsed_counters.get("full_regression_run_count") != 0:
            errors.append(
                "external PASS evidence must report full_regression_run_count equal to zero"
            )

    runner_digest, runner_errors = _runner_identity_digest(
        action.get("runner_identity_paths"), runner_files
    )
    errors.extend(runner_errors)
    if runner_digest is not None and result.get("runner_identity_digest") != runner_digest:
        errors.append("transition Result runner_identity_digest does not match protected runner files")

    runner_receipt = artifact.get("runner_receipt")
    if not isinstance(runner_receipt, dict):
        errors.append("transition evidence artifact runner_receipt must be an object")
    else:
        errors.extend(
            _exact_keys(
                runner_receipt,
                RUNNER_RECEIPT_KEYS,
                "transition evidence artifact runner_receipt",
            )
        )
        if runner_receipt.get("runner_id") != action.get("evidence_verifier"):
            errors.append("transition evidence runner_receipt.runner_id must match the action verifier")
        if runner_receipt.get("runner_identity_digest") != runner_digest:
            errors.append("transition evidence runner_receipt.runner_identity_digest must match protected runner files")
        if runner_receipt.get("execution_input_digest") != result.get("execution_input_digest"):
            errors.append("transition evidence runner_receipt.execution_input_digest must match the Result")
        if runner_receipt.get("exit_code") != 0 or runner_receipt.get("completed") is not True:
            errors.append("transition evidence runner_receipt must record a completed zero-exit verifier run")
        if result.get("runner_receipt_digest") != _canonical_json_digest(runner_receipt):
            errors.append("transition Result runner_receipt_digest does not match the canonical runner receipt")

    outcomes: dict[str, str] = {}
    raw_outcomes = artifact.get("case_outcomes")
    if not isinstance(raw_outcomes, list) or not raw_outcomes:
        errors.append("transition evidence artifact case_outcomes must be a non-empty list")
    else:
        for index, raw_outcome in enumerate(raw_outcomes):
            label = f"transition evidence artifact case_outcomes[{index}]"
            if not isinstance(raw_outcome, dict):
                errors.append(f"{label} must be an object")
                continue
            errors.extend(_exact_keys(raw_outcome, CASE_OUTCOME_KEYS, label))
            outcome_case = raw_outcome.get("case_id")
            outcome_verdict = raw_outcome.get("verdict")
            if not isinstance(outcome_case, str) or CASE_ID_RE.fullmatch(outcome_case) is None:
                errors.append(f"{label}.case_id must be an exact Verification Case ID")
                continue
            if outcome_case in outcomes:
                errors.append(f"transition evidence artifact repeats Case {outcome_case}")
            if outcome_verdict not in VERDICT_TO_TRANSITION_FIELD:
                errors.append(f"{label}.verdict must be PASS, FAIL, or INVALID")
            else:
                outcomes[outcome_case] = str(outcome_verdict)
            evidence_ref = raw_outcome.get("evidence_ref")
            if not isinstance(evidence_ref, str) or evidence_ref.strip().lower() in {
                "", "pending", "not-executed", "none", "n/a"
            }:
                errors.append(f"{label}.evidence_ref must identify executed evidence")
            if (
                not isinstance(raw_outcome.get("evidence_digest"), str)
                or SHA256_RE.fullmatch(str(raw_outcome.get("evidence_digest"))) is None
            ):
                errors.append(f"{label}.evidence_digest must be an exact sha256 digest")

    if result.get("verification_report_digest") != _canonical_json_digest(raw_outcomes):
        errors.append(
            "transition Result verification_report_digest does not match canonical case_outcomes"
        )

    produced = action.get("produced_case_ids")
    if isinstance(produced, list) and all(isinstance(item, str) for item in produced):
        if set(outcomes) != set(produced):
            errors.append("transition evidence case_outcomes must exactly cover current_action.produced_case_ids")
    primary_case = action.get("case_id")
    if isinstance(primary_case, str) and verdict_value is not None:
        if outcomes.get(primary_case) != verdict_value:
            errors.append("transition evidence primary Case verdict must equal plan_gate_verdict")
    aggregate_verdict = (
        "INVALID"
        if "INVALID" in outcomes.values()
        else "FAIL"
        if "FAIL" in outcomes.values()
        else "PASS"
        if outcomes
        else None
    )
    if verdict_value is not None and aggregate_verdict != verdict_value:
        errors.append(
            "transition Result verdict must equal INVALID > FAIL > PASS aggregation across produced Cases"
        )
    if runner_digest is not None:
        errors.extend(
            _rerun_evidence_verifier(
                action,
                evidence_bytes,
                artifact,
                runner_files,
                runner_digest,
                artifact_call_count,
            )
        )
    return verdict_value, outcomes, errors


def validate_result_for_transition(
    result: Mapping[str, object] | None,
    base_control: Mapping[str, object],
    evidence_text: str | bytes | None = None,
    runner_files: Mapping[str, str] | None = None,
    configured_identities: Sequence[str] = (),
) -> tuple[str | None, list[str]]:
    """Validate exact Result identity, its artifact, and return its verdict."""

    action = base_control.get("current_action")
    if not isinstance(action, dict):
        return None, ["base current_action must be a mapping"]
    verdict, _, errors = validate_gate_result(
        result,
        action,
        base_control.get("plan_revision_ref"),
        evidence_text,
        runner_files,
        configured_identities,
    )
    return verdict, errors


def _plan_result_seal_digest(
    result_ref: str,
    result_metadata: Mapping[str, object],
    result_blob_digest: str,
    evidence_bytes: bytes,
) -> str:
    """Seal the trusted-base Result bytes and evidence bytes as one predecessor."""

    return _canonical_json_digest(
        {
            "schema": PLAN_RESULT_SEAL_SCHEMA,
            "result_ref": result_ref,
            "result_blob_digest": result_blob_digest,
            "evidence_blob_digest": "sha256:"
            + hashlib.sha256(evidence_bytes).hexdigest(),
            "action_ref": result_metadata.get("action_ref"),
            "plan_revision_ref": result_metadata.get("plan_revision_ref"),
            "plan_gate_verdict": result_metadata.get("plan_gate_verdict"),
        }
    )


def _contract_for_iter010_role(
    control: Mapping[str, object], role: str
) -> Mapping[str, object] | None:
    candidates: list[Mapping[str, object]] = []
    current = control.get("current_action")
    if isinstance(current, Mapping):
        candidates.append(current)
    contracts = control.get("next_action_contracts")
    if isinstance(contracts, Mapping):
        candidates.extend(
            value for value in contracts.values() if isinstance(value, Mapping)
        )
    for candidate in candidates:
        if _iter010_action_evidence_role(candidate) == role:
            return candidate
    return None


def _trusted_predecessor_artifact(
    action: Mapping[str, object],
    expected_verdict: str,
    control: Mapping[str, object],
    documents: Mapping[str, Mapping[str, object]] | None,
    document_blob_digests: Mapping[str, str] | None,
    evidence_artifacts: Mapping[str, str | bytes] | None,
    runner_files: Mapping[str, str] | None,
    configured_identities: Sequence[str] = (),
) -> tuple[dict[str, object] | None, str | None, list[str]]:
    result_ref = action.get("result_ref")
    if not isinstance(result_ref, str):
        return None, None, ["trusted predecessor action result_ref is invalid"]
    result = (documents or {}).get(result_ref)
    raw_evidence = (evidence_artifacts or {}).get(result_ref)
    verdict, _, errors = validate_gate_result(
        result,
        action,
        control.get("plan_revision_ref"),
        raw_evidence,
        runner_files,
        configured_identities,
    )
    errors = [f"trusted predecessor {result_ref}: {error}" for error in errors]
    if verdict != expected_verdict:
        errors.append(
            f"trusted predecessor {result_ref} must have verdict {expected_verdict}"
        )
    if raw_evidence is None:
        return None, None, errors
    evidence_bytes = (
        raw_evidence.encode("utf-8")
        if isinstance(raw_evidence, str)
        else raw_evidence
    )
    try:
        artifact = _load_evidence_json(
            evidence_bytes.decode("utf-8", errors="strict")
        )
    except (UnicodeDecodeError, PlanGateError) as error:
        errors.append(f"trusted predecessor {result_ref} evidence cannot be read: {error}")
        return None, None, errors
    blob_digest = (document_blob_digests or {}).get(result_ref)
    if not isinstance(blob_digest, str) or SHA256_RE.fullmatch(blob_digest) is None:
        errors.append(
            f"trusted predecessor {result_ref} raw Result blob digest is unavailable"
        )
        return artifact, None, errors
    if result is None:
        return artifact, None, errors
    return (
        artifact,
        _plan_result_seal_digest(
            result_ref,
            result,
            blob_digest,
            evidence_bytes,
        ),
        errors,
    )


def _validate_iter010_cross_action_bindings(
    base_manifest: Mapping[str, object],
    base_control: Mapping[str, object],
    base_action: Mapping[str, object],
    target_evidence_text: str | bytes | None,
    base_documents: Mapping[str, Mapping[str, object]] | None,
    base_document_blob_digests: Mapping[str, str] | None,
    base_result_evidence_artifacts: Mapping[str, str | bytes] | None,
    base_runner_files: Mapping[str, str] | None,
) -> list[str]:
    """Bind route-role evidence to trusted predecessor bytes, never model names."""

    role = _iter010_action_evidence_role(base_action)
    if role in {None, "other", "freeze"} or target_evidence_text is None:
        return []
    evidence_bytes = (
        target_evidence_text.encode("utf-8")
        if isinstance(target_evidence_text, str)
        else target_evidence_text
    )
    try:
        target_artifact = _load_evidence_json(
            evidence_bytes.decode("utf-8", errors="strict")
        )
    except (UnicodeDecodeError, PlanGateError) as error:
        return [f"cross-action evidence cannot be read: {error}"]
    target_evidence = target_artifact.get("action_evidence")
    if not isinstance(target_evidence, Mapping):
        return ["cross-action evidence action_evidence must be an object"]

    profile_configurations, configured_identities, configuration_errors = (
        _configured_execution_profiles(base_manifest)
    )
    errors: list[str] = list(configuration_errors)
    freeze_action = _contract_for_iter010_role(base_control, "freeze")
    if freeze_action is None:
        errors.append("cross-action binding cannot resolve the registered Freeze action")
    else:
        freeze_artifact, _, predecessor_errors = _trusted_predecessor_artifact(
            freeze_action,
            "PASS",
            base_control,
            base_documents,
            base_document_blob_digests,
            base_result_evidence_artifacts,
            base_runner_files,
            configured_identities,
        )
        errors.extend(predecessor_errors)
        freeze_evidence = (
            freeze_artifact.get("action_evidence")
            if isinstance(freeze_artifact, Mapping)
            else None
        )
        if isinstance(freeze_evidence, Mapping):
            for field in (
                "provider_neutral_root_input_set",
                "provider_neutral_root_input_set_digest",
            ):
                if target_evidence.get(field) != freeze_evidence.get(field):
                    errors.append(
                        f"cross-action evidence {field} must exactly match the trusted Freeze Result"
                    )

    route_role = "preferred" if role == "preferred-quality" else "fallback"
    expected_profile = profile_configurations.get(route_role)
    evidence_profile_ref_field = (
        "execution_profile_ref"
        if role in {"preferred-quality", "fallback-quality"}
        else "fallback_execution_profile_ref"
    )
    evidence_profile_object_field = (
        "execution_profile"
        if role in {"preferred-quality", "fallback-quality"}
        else "fallback_execution_profile"
    )
    if isinstance(expected_profile, Mapping):
        if target_evidence.get(evidence_profile_ref_field) != expected_profile.get(
            "execution_profile_ref"
        ):
            errors.append(
                f"cross-action evidence {evidence_profile_ref_field} must equal the trusted {route_role} execution profile ref"
            )
        if target_evidence.get(evidence_profile_object_field) != expected_profile:
            errors.append(
                f"cross-action evidence {evidence_profile_object_field} must exactly equal the trusted {route_role} execution profile configuration"
            )

    if role in {"fallback-refreeze", "fallback-quality"}:
        plugin_ref = _fallback_admission_policy_plugin_ref(base_manifest)
        plugin_ref_field = (
            "fallback_admission_policy_plugin_ref"
            if role == "fallback-refreeze"
            else "admission_policy_plugin_ref"
        )
        plugin_object_field = (
            "fallback_admission_policy_plugin"
            if role == "fallback-refreeze"
            else "admission_policy_plugin"
        )
        if target_evidence.get(plugin_ref_field) != plugin_ref:
            errors.append(
                f"cross-action evidence {plugin_ref_field} must equal the trusted fallback execution-profile admission policy plugin ref"
            )
        expected_plugin = (
            base_manifest.get(plugin_ref) if isinstance(plugin_ref, str) else None
        )
        if not isinstance(expected_plugin, Mapping):
            errors.append(
                "trusted fallback admission policy plugin configuration is unavailable"
            )
        elif target_evidence.get(plugin_object_field) != expected_plugin:
            errors.append(
                f"cross-action evidence {plugin_object_field} must exactly equal the trusted admission plugin configuration"
            )

    if role == "fallback-refreeze":
        preferred_action = _contract_for_iter010_role(
            base_control, "preferred-quality"
        )
        if preferred_action is None:
            errors.append(
                "cross-action binding cannot resolve the preferred quality action"
            )
        else:
            preferred_artifact, seal, predecessor_errors = (
                _trusted_predecessor_artifact(
                    preferred_action,
                    "INVALID",
                    base_control,
                    base_documents,
                    base_document_blob_digests,
                    base_result_evidence_artifacts,
                    base_runner_files,
                    configured_identities,
                )
            )
            errors.extend(predecessor_errors)
            if target_evidence.get("preferred_invalid_predecessor_ref") != preferred_action.get(
                "result_ref"
            ):
                errors.append(
                    "cross-action evidence preferred_invalid_predecessor_ref must identify the trusted preferred Result"
                )
            if target_evidence.get("preferred_invalid_predecessor_seal_digest") != seal:
                errors.append(
                    "cross-action evidence preferred_invalid_predecessor_seal_digest must match the trusted preferred Result seal"
                )
            preferred_evidence = (
                preferred_artifact.get("action_evidence")
                if isinstance(preferred_artifact, Mapping)
                else None
            )
            if isinstance(preferred_evidence, Mapping) and target_evidence.get(
                "preferred_terminal_classification"
            ) != preferred_evidence.get("terminal_classification"):
                errors.append(
                    "cross-action evidence preferred_terminal_classification must match the trusted preferred Result"
                )

    if role == "fallback-quality":
        refreeze_action = _contract_for_iter010_role(
            base_control, "fallback-refreeze"
        )
        if refreeze_action is None:
            errors.append(
                "cross-action binding cannot resolve the fallback Refreeze action"
            )
        else:
            refreeze_artifact, seal, predecessor_errors = (
                _trusted_predecessor_artifact(
                    refreeze_action,
                    "PASS",
                    base_control,
                    base_documents,
                    base_document_blob_digests,
                    base_result_evidence_artifacts,
                    base_runner_files,
                    configured_identities,
                )
            )
            errors.extend(predecessor_errors)
            if target_evidence.get("fallback_refreeze_predecessor_ref") != refreeze_action.get(
                "result_ref"
            ):
                errors.append(
                    "cross-action evidence fallback_refreeze_predecessor_ref must identify the trusted Refreeze Result"
                )
            if target_evidence.get("fallback_refreeze_predecessor_seal_digest") != seal:
                errors.append(
                    "cross-action evidence fallback_refreeze_predecessor_seal_digest must match the trusted Refreeze Result seal"
                )
            refreeze_evidence = (
                refreeze_artifact.get("action_evidence")
                if isinstance(refreeze_artifact, Mapping)
                else None
            )
            if isinstance(refreeze_evidence, Mapping):
                for target_field, refreeze_field in (
                    ("execution_profile_ref", "fallback_execution_profile_ref"),
                    ("execution_profile", "fallback_execution_profile"),
                    ("execution_profile_digest", "fallback_execution_profile_digest"),
                    (
                        "admission_policy_plugin_ref",
                        "fallback_admission_policy_plugin_ref",
                    ),
                    (
                        "admission_policy_plugin",
                        "fallback_admission_policy_plugin",
                    ),
                    (
                        "admission_policy_plugin_digest",
                        "fallback_admission_policy_plugin_digest",
                    ),
                ):
                    if target_evidence.get(target_field) != refreeze_evidence.get(
                        refreeze_field
                    ):
                        errors.append(
                            f"cross-action evidence {target_field} must exactly match the trusted Refreeze Result"
                        )
    return errors


def _plan_semantics_without_revision(
    manifest: Mapping[str, object], control: Mapping[str, object]
) -> object:
    """Bind route configuration and its selected plugin to the governed plan."""

    control_value = copy.deepcopy(dict(control))
    control_value.pop("plan_revision_ref", None)
    control_value.pop("authorization_refs", None)
    return {
        "control": control_value,
        **_route_configuration_semantics(manifest),
    }


def _route_configuration_semantics(manifest: Mapping[str, object]) -> object:
    """Return route/profile/plugin values that no action transition may rewrite."""

    policy = manifest.get("provider_route_policy")
    plugin_ref = _fallback_admission_policy_plugin_ref(manifest)
    return {
        "provider_route_policy": copy.deepcopy(policy),
        "execution_profile_configurations": copy.deepcopy(
            manifest.get("execution_profile_configurations")
        ),
        "fallback_admission_policy_plugin": copy.deepcopy(
            manifest.get(plugin_ref) if isinstance(plugin_ref, str) else None
        ),
    }


def _is_exact_route_policy_migration_cutover(
    base_manifest: Mapping[str, object],
    target_manifest: Mapping[str, object],
) -> bool:
    """Allow only the exact legacy bridge -> identity-free @2 cutover."""

    if not _is_route_policy_migration_bridge(base_manifest):
        return False
    if target_manifest.get("provider_route_policy_migration") is not None:
        return False
    if _control(base_manifest) != _control(target_manifest):
        return False

    base_policy = base_manifest.get("provider_route_policy")
    target_policy = target_manifest.get("provider_route_policy")
    base_configurations = base_manifest.get("execution_profile_configurations")
    target_configurations = target_manifest.get("execution_profile_configurations")
    if not all(
        isinstance(value, Mapping)
        for value in (
            base_policy,
            target_policy,
            base_configurations,
            target_configurations,
        )
    ):
        return False
    assert isinstance(base_policy, Mapping)
    assert isinstance(target_policy, Mapping)
    assert isinstance(base_configurations, Mapping)
    assert isinstance(target_configurations, Mapping)
    if target_policy.get("schema") != PROVIDER_ROUTE_POLICY_SCHEMA:
        return False
    if set(target_policy) != PROVIDER_ROUTE_POLICY_KEYS:
        return False
    if target_configurations.get("schema") != EXECUTION_PROFILE_CONFIGURATION_SCHEMA:
        return False

    base_preferred = base_configurations.get("preferred")
    base_fallback = base_configurations.get("fallback")
    target_preferred = target_configurations.get("preferred")
    target_fallback = target_configurations.get("fallback")
    if not all(
        isinstance(value, Mapping)
        for value in (
            base_preferred,
            base_fallback,
            target_preferred,
            target_fallback,
        )
    ):
        return False
    assert isinstance(base_preferred, Mapping)
    assert isinstance(base_fallback, Mapping)
    assert isinstance(target_preferred, Mapping)
    assert isinstance(target_fallback, Mapping)

    if dict(base_preferred) != dict(target_preferred):
        return False
    if any(
        base_fallback.get(field) != target_fallback.get(field)
        for field in PREFERRED_EXECUTION_PROFILE_CONFIGURATION_KEYS
    ):
        return False
    base_plugin_ref = _fallback_admission_policy_plugin_ref(base_manifest)
    target_plugin_ref = _fallback_admission_policy_plugin_ref(target_manifest)
    if (
        base_plugin_ref != target_plugin_ref
        or target_fallback.get("admission_policy_plugin_ref") != base_plugin_ref
    ):
        return False
    if base_manifest.get(base_plugin_ref) != target_manifest.get(target_plugin_ref):
        return False

    aliases = (
        (
            base_policy.get("preferred_execution_profile_ref"),
            target_policy.get("preferred_execution_profile_ref"),
            target_preferred.get("execution_profile_ref"),
        ),
        (
            base_policy.get("fallback_execution_profile_ref"),
            target_policy.get("fallback_execution_profile_ref"),
            target_fallback.get("execution_profile_ref"),
        ),
        (
            base_policy.get("primary_provider"),
            base_preferred.get("provider_identity"),
            target_preferred.get("provider_identity"),
        ),
        (
            base_policy.get("preferred_model_identity"),
            base_preferred.get("model_identity"),
            target_preferred.get("model_identity"),
        ),
        (
            base_policy.get("fallback_provider"),
            base_fallback.get("provider_identity"),
            target_fallback.get("provider_identity"),
        ),
        (
            base_policy.get("fallback_model_identity"),
            base_fallback.get("model_identity"),
            target_fallback.get("model_identity"),
        ),
    )
    return all(first == second == third for first, second, third in aliases)


def validate_transition(
    base_manifest: Mapping[str, object],
    target_manifest: Mapping[str, object],
    changed_paths: Sequence[str],
    *,
    base_current_metadata: Mapping[str, object] | None = None,
    target_current_metadata: Mapping[str, object] | None = None,
    base_verification_cases: Mapping[str, Sequence[VerificationCase]] | None = None,
    target_verification_cases: Mapping[str, Sequence[VerificationCase]] | None = None,
    base_documents: Mapping[str, Mapping[str, object]] | None = None,
    target_documents: Mapping[str, Mapping[str, object]] | None = None,
    base_document_authorization_refs: Iterable[str] | None = None,
    base_document_blob_digests: Mapping[str, str] | None = None,
    target_result_metadata: Mapping[str, object] | None = None,
    base_result_evidence_artifacts: Mapping[str, str | bytes] | None = None,
    target_result_evidence_artifacts: Mapping[str, str | bytes] | None = None,
    target_result_evidence_text: str | bytes | None = None,
    base_runner_files: Mapping[str, str] | None = None,
    target_runner_files: Mapping[str, str] | None = None,
    trusted_parent_commit: str | None = None,
    trusted_parent_tree: str | None = None,
) -> list[str]:
    """Validate one base-to-target change using only base action authority."""

    target_errors = validate_snapshot(
        target_manifest,
        current_metadata=target_current_metadata,
        verification_cases=target_verification_cases,
        documents=target_documents,
        result_evidence_artifacts=target_result_evidence_artifacts,
        runner_files=base_runner_files,
    )
    base_control = _control(base_manifest)
    target_control = _control(target_manifest)
    if base_control is None:
        return sorted(set(target_errors + validate_bootstrap_paths(changed_paths)))
    errors = list(target_errors)
    errors.extend(
        validate_snapshot(
            base_manifest,
            current_metadata=base_current_metadata,
            verification_cases=base_verification_cases,
            documents=base_documents,
            result_evidence_artifacts=base_result_evidence_artifacts,
            runner_files=base_runner_files,
            allow_legacy_route_policy=True,
        )
    )
    if target_control is None:
        return sorted(set(errors + ["target removed plan_execution_control"]))
    base_action = base_control.get("current_action")
    target_action = target_control.get("current_action")
    if not isinstance(base_action, dict) or not isinstance(target_action, dict):
        return sorted(set(errors))

    errors.extend(validate_changed_paths(base_action, changed_paths))
    base_action_id = base_action.get("id")
    target_action_id = target_action.get("id")
    action_changed = base_action_id != target_action_id
    result_path = base_action.get("result_path")
    result_changed = isinstance(result_path, str) and result_path in changed_paths
    evidence_path = base_action.get("evidence_path")
    evidence_changed = isinstance(evidence_path, str) and evidence_path in changed_paths
    transition_attempted = action_changed or result_changed or evidence_changed
    base_runner_paths = base_action.get("runner_identity_paths")
    changed_runner_paths = (
        set(changed_paths).intersection(base_runner_paths)
        if isinstance(base_runner_paths, list)
        else set()
    )
    revision_changed = base_control.get("plan_revision_ref") != target_control.get(
        "plan_revision_ref"
    )
    semantics_changed = (
        _plan_semantics_without_revision(base_manifest, base_control)
        != _plan_semantics_without_revision(target_manifest, target_control)
    )
    route_configuration_changed = (
        _route_configuration_semantics(base_manifest)
        != _route_configuration_semantics(target_manifest)
    )
    route_policy_migration_cutover = _is_exact_route_policy_migration_cutover(
        base_manifest,
        target_manifest,
    )
    if _is_route_policy_migration_bridge(base_manifest):
        if not route_policy_migration_cutover:
            errors.append(
                "trusted-parent route-policy bridge permits only its exact @2 finalization"
            )
        unexpected_migration_paths = sorted(
            path
            for path in changed_paths
            if path
            != "docs/project/iterations/iteration-010/manifest.yaml"
            and not path.startswith("docs/_generated/")
        )
        if unexpected_migration_paths:
            errors.append(
                "route-policy bridge finalization may change only the Manifest and generated indexes: "
                + ", ".join(unexpected_migration_paths)
            )

    protected = PROTECTED_GATE_PATHS.intersection(changed_paths)
    if protected and not (
        base_action.get("kind") == "governance"
        and revision_changed
        and semantics_changed
    ):
        errors.append(
            "installed plan-gate files require a governance action with a plan revision: "
            + ", ".join(sorted(protected))
        )

    if transition_attempted:
        if changed_runner_paths:
            errors.append(
                "runner identity files must be committed before a later Result/action transition: "
                + ", ".join(sorted(changed_runner_paths))
            )
        if not result_changed or not evidence_changed:
            errors.append(
                "action transition must change both the exact Result and evidence artifact in the same commit"
            )
        if revision_changed:
            errors.append("action transition and plan revision must be separate changes")
        _, configured_identities, _ = _configured_execution_profiles(base_manifest)
        verdict, result_errors = validate_result_for_transition(
            target_result_metadata,
            base_control,
            target_result_evidence_text,
            base_runner_files,
            configured_identities,
        )
        errors.extend(result_errors)
        errors.extend(
            _validate_lightweight_handoff_parent_binding(
                base_action,
                target_result_evidence_text,
                trusted_parent_commit,
                trusted_parent_tree,
            )
        )
        errors.extend(
            _validate_iter010_cross_action_bindings(
                base_manifest,
                base_control,
                base_action,
                target_result_evidence_text,
                base_documents,
                base_document_blob_digests,
                base_result_evidence_artifacts,
                base_runner_files,
            )
        )
        if verdict is not None:
            transition = base_control.get("transition")
            expected = (
                transition.get(VERDICT_TO_TRANSITION_FIELD[verdict])
                if isinstance(transition, dict)
                else None
            )
            if target_action_id != expected:
                errors.append(
                    f"{verdict} Result permits only next action {expected}, not {target_action_id}"
                )
            base_contract_errors: list[str] = []
            registered = _registered_action_contracts(base_control, base_contract_errors)
            errors.extend(base_contract_errors)
            if expected == base_action_id:
                if target_action != base_action:
                    errors.append("self-loop transition must preserve the base current_action")
                if target_control.get("transition") != base_control.get("transition"):
                    errors.append("self-loop transition must preserve the base transition")
                if target_control.get("locks") != base_control.get("locks"):
                    errors.append("self-loop transition must preserve the base locks")
            else:
                contract = registered.get(expected) if isinstance(expected, str) else None
                if contract is None:
                    errors.append(
                        f"next action {expected} has no pre-registered base action contract"
                    )
                else:
                    if target_action != _action_fields(contract):
                        errors.append(
                            "target current_action must exactly match the pre-registered base contract"
                        )
                    if target_control.get("transition") != contract.get("transition"):
                        errors.append(
                            "target transition must exactly match the pre-registered base contract"
                        )
                    if target_control.get("locks") != contract.get("locks"):
                        errors.append(
                            "target locks must exactly match the pre-registered base contract"
                        )
            if target_control.get("next_action_contracts") != base_control.get(
                "next_action_contracts"
            ):
                errors.append("action transition must preserve pre-registered contracts")
        if route_configuration_changed:
            errors.append(
                "action transition must preserve route, execution-profile, plugin, and plan semantics"
            )
        if not action_changed and semantics_changed:
            errors.append("self-loop transition must not revise plan semantics")
    else:
        if (
            semantics_changed
            and not revision_changed
            and not route_policy_migration_cutover
        ):
            errors.append("plan semantics changed without a new plan_revision_ref")
        if revision_changed and not semantics_changed:
            errors.append("plan_revision_ref changed without a semantic plan revision")
        if revision_changed:
            if base_action.get("kind") != "governance":
                errors.append("plan revision requires the base current action to be governance")
            result_ref = base_action.get("result_ref")
            base_result = (
                base_documents.get(str(result_ref))
                if base_documents is not None and isinstance(result_ref, str)
                else None
            )
            _, configured_identities, _ = _configured_execution_profiles(
                base_manifest
            )
            base_verdict, _, base_result_errors = validate_gate_result(
                base_result,
                base_action,
                base_control.get("plan_revision_ref"),
                (base_result_evidence_artifacts or {}).get(str(result_ref)),
                base_runner_files,
                configured_identities,
            )
            errors.extend(
                f"governance plan revision prerequisite: {error}"
                for error in base_result_errors
            )
            if base_verdict != "PASS":
                errors.append(
                    "governance plan revision requires a previously sealed PASS Result for the base action"
                )
            errors.extend(
                _validate_plan_revision_ref(
                    target_control.get("plan_revision_ref"),
                    target_documents,
                    "target plan_execution_control.plan_revision_ref",
                    target_control.get("authorization_refs"),
                )
            )
            errors.extend(
                _validate_plan_revision_lineage(
                    base_manifest,
                    base_control,
                    target_control,
                    base_action,
                    base_documents,
                    target_documents,
                    base_document_authorization_refs,
                    base_result_evidence_artifacts,
                )
            )
    return sorted(set(errors))


def _run_git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if completed.returncode != 0:
        raise PlanGateError(
            f"git {' '.join(arguments)} failed: {completed.stderr.strip()}"
        )
    return completed.stdout


def _run_git_bytes(repository: Path, *arguments: str) -> bytes:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise PlanGateError(f"git {' '.join(arguments)} failed: {stderr}")
    return completed.stdout


def _read_text(repository: Path, reference: str, path: str) -> str:
    if reference == "WORKTREE":
        return (repository / path).read_text(encoding="utf-8")
    return _run_git(repository, "show", f"{reference}:{path}")


def _read_bytes(repository: Path, reference: str, path: str) -> bytes:
    if reference == "WORKTREE":
        return (repository / path).read_bytes()
    return _run_git_bytes(repository, "show", f"{reference}:{path}")


def _list_document_files(repository: Path, reference: str) -> list[str]:
    if reference == "WORKTREE":
        return [
            path.relative_to(repository).as_posix()
            for path in sorted((repository / "docs").rglob("*"))
            if path.is_file()
        ]
    return [
        line
        for line in _run_git(
            repository, "ls-tree", "-r", "--name-only", reference, "--", "docs"
        ).splitlines()
        if line
    ]


def _list_docs(repository: Path, reference: str) -> list[str]:
    return [
        path for path in _list_document_files(repository, reference) if path.endswith(".md")
    ]


def _document_authorization_refs(repository: Path, reference: str) -> frozenset[str]:
    refs: set[str] = set()
    for path in _list_document_files(repository, reference):
        raw = _read_bytes(repository, reference, path)
        refs.update(
            match.group(0).decode("ascii")
            for match in AUTHORIZATION_BYTES_RE.finditer(raw)
        )
    return frozenset(refs)


def _document_metadata(
    repository: Path, reference: str
) -> tuple[
    dict[str, dict[str, object]],
    frozenset[str],
    dict[str, str],
    list[str],
]:
    documents: dict[str, dict[str, object]] = {}
    authorization_refs = set(_document_authorization_refs(repository, reference))
    document_blob_digests: dict[str, str] = {}
    errors: list[str] = []
    for path in _list_docs(repository, reference):
        try:
            raw = _read_bytes(repository, reference, path)
            text = raw.decode("utf-8", errors="strict")
            # Repository prose and generated README files need not carry an ID.
            # Once a file opts into front matter, malformed metadata remains a
            # hard error so referenced PDR/Finding identity cannot be ambiguous.
            if not text.startswith("---\n") and text.strip() != "---":
                continue
            metadata = parse_front_matter(text)
        except (OSError, UnicodeError, PlanGateError) as error:
            errors.append(f"{path}: {error}")
            continue
        identifier = metadata.get("id")
        if not isinstance(identifier, str) or not identifier:
            continue
        if identifier in documents:
            errors.append(f"duplicate document ID: {identifier}")
        else:
            metadata = dict(metadata)
            metadata["__path__"] = path
            documents[identifier] = metadata
            document_blob_digests[identifier] = "sha256:" + hashlib.sha256(raw).hexdigest()
    return (
        documents,
        frozenset(authorization_refs),
        document_blob_digests,
        errors,
    )


def _active_manifest_path(current_metadata: Mapping[str, object]) -> str:
    active = str(current_metadata.get("active_iteration", ""))
    match = re.fullmatch(r"ITER-([0-9]{3,})-INDEX", active)
    if match is None:
        raise PlanGateError(
            "PROJECT-CURRENT active_iteration must be an exact ITER-NNN-INDEX ID"
        )
    return f"docs/project/iterations/iteration-{match.group(1)}/manifest.yaml"


@dataclass(frozen=True)
class TreeState:
    manifest: dict[str, object]
    current: dict[str, object]
    verification_cases: dict[str, list[VerificationCase]]
    documents: dict[str, dict[str, object]]
    document_authorization_refs: frozenset[str]
    document_blob_digests: dict[str, str]
    result: dict[str, object] | None
    result_evidence_artifacts: dict[str, bytes]
    runner_files: dict[str, str]


def _tree_state(
    repository: Path, reference: str, explicit_manifest: str | None
) -> tuple[TreeState, list[str]]:
    current = parse_front_matter(
        _read_text(repository, reference, "docs/project/current.md")
    )
    manifest_path = explicit_manifest or _active_manifest_path(current)
    manifest = load_safe_yaml(_read_text(repository, reference, manifest_path))
    verification_path = str(PurePosixPath(manifest_path).parent / "verification-matrix.md")
    verification = parse_verification_cases(
        _read_text(repository, reference, verification_path)
    )
    (
        documents,
        document_authorization_refs,
        document_blob_digests,
        errors,
    ) = _document_metadata(repository, reference)
    control = _control(manifest)
    result: dict[str, object] | None = None
    result_evidence_artifacts: dict[str, bytes] = {}
    runner_files: dict[str, str] = {}
    if control is not None:
        action = control.get("current_action")
        if isinstance(action, dict) and isinstance(action.get("result_path"), str):
            try:
                result = parse_front_matter(
                    _read_text(repository, reference, str(action["result_path"]))
                )
            except (OSError, UnicodeError, PlanGateError):
                result = None
        action_candidates: list[Mapping[str, object]] = []
        if isinstance(action, dict):
            action_candidates.append(action)
        raw_contracts = control.get("next_action_contracts")
        if isinstance(raw_contracts, dict):
            action_candidates.extend(
                contract
                for contract in raw_contracts.values()
                if isinstance(contract, dict)
            )
        for candidate in action_candidates:
            result_ref = candidate.get("result_ref")
            evidence_path = candidate.get("evidence_path")
            if not isinstance(result_ref, str) or not isinstance(evidence_path, str):
                continue
            try:
                result_evidence_artifacts[result_ref] = _read_bytes(
                    repository, reference, evidence_path
                )
            except (OSError, UnicodeError, PlanGateError):
                continue
        for candidate in action_candidates:
            paths = candidate.get("runner_identity_paths")
            if not isinstance(paths, list):
                continue
            for path in paths:
                if not isinstance(path, str) or path in runner_files:
                    continue
                try:
                    runner_files[path] = _read_text(repository, reference, path)
                except (OSError, UnicodeError, PlanGateError):
                    continue
    return TreeState(
        manifest,
        current,
        verification,
        documents,
        document_authorization_refs,
        document_blob_digests,
        result,
        result_evidence_artifacts,
        runner_files,
    ), errors


def _changed_paths(repository: Path, base: str, target: str) -> list[str]:
    if target == "WORKTREE":
        tracked = _run_git(repository, "diff", "--name-only", base, "--")
        untracked = _run_git(
            repository, "ls-files", "--others", "--exclude-standard"
        )
        output = tracked + untracked
    else:
        output = _run_git(repository, "diff", "--name-only", base, target, "--")
    return sorted({line.strip() for line in output.splitlines() if line.strip()})


def _transition_result_from_target(
    repository: Path,
    target_reference: str,
    base_manifest: Mapping[str, object],
) -> dict[str, object] | None:
    """Read the old action's declared Result from the target tree.

    The target current action owns a *different* future Result after a normal
    transition, so looking up the target action's result path would validate the
    wrong object.
    """

    control = _control(base_manifest)
    action = control.get("current_action") if control is not None else None
    result_path = action.get("result_path") if isinstance(action, dict) else None
    if not isinstance(result_path, str):
        return None
    try:
        return parse_front_matter(
            _read_text(repository, target_reference, result_path)
        )
    except (OSError, UnicodeError, PlanGateError):
        return None


def _transition_evidence_from_target(
    repository: Path,
    target_reference: str,
    base_manifest: Mapping[str, object],
) -> bytes | None:
    control = _control(base_manifest)
    action = control.get("current_action") if control is not None else None
    evidence_path = action.get("evidence_path") if isinstance(action, dict) else None
    if not isinstance(evidence_path, str):
        return None
    try:
        return _read_bytes(repository, target_reference, evidence_path)
    except (OSError, UnicodeError, PlanGateError):
        return None


def _print_errors(errors: Sequence[str]) -> int:
    if errors:
        for error in sorted(set(errors)):
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("plan compliance check passed")
    return 0


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, default=REPOSITORY)
    commands = parser.add_subparsers(dest="command", required=True)
    snapshot = commands.add_parser("snapshot")
    snapshot.add_argument("--manifest")
    diff = commands.add_parser("diff")
    diff.add_argument("--base", required=True)
    diff.add_argument(
        "--target",
        default="WORKTREE",
        help="candidate git ref; defaults to the current worktree",
    )
    diff.add_argument("--manifest")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _argument_parser().parse_args(argv)
    repository = args.repository.resolve()
    try:
        if args.command == "snapshot":
            state, load_errors = _tree_state(repository, "WORKTREE", args.manifest)
            return _print_errors(
                load_errors
                + validate_snapshot(
                    state.manifest,
                    current_metadata=state.current,
                    verification_cases=state.verification_cases,
                    documents=state.documents,
                    result_evidence_artifacts=state.result_evidence_artifacts,
                    runner_files=state.runner_files,
                )
            )
        base, base_errors = _tree_state(repository, args.base, args.manifest)
        target, target_errors = _tree_state(repository, args.target, args.manifest)
        errors = base_errors + target_errors
        errors.extend(
            validate_transition(
                base.manifest,
                target.manifest,
                _changed_paths(repository, args.base, args.target),
                base_current_metadata=base.current,
                target_current_metadata=target.current,
                base_verification_cases=base.verification_cases,
                target_verification_cases=target.verification_cases,
                base_documents=base.documents,
                target_documents=target.documents,
                base_document_authorization_refs=base.document_authorization_refs,
                base_document_blob_digests=base.document_blob_digests,
                base_result_evidence_artifacts=base.result_evidence_artifacts,
                target_result_evidence_artifacts=target.result_evidence_artifacts,
                base_runner_files=base.runner_files,
                target_runner_files=target.runner_files,
                target_result_metadata=_transition_result_from_target(
                    repository, args.target, base.manifest
                ),
                target_result_evidence_text=_transition_evidence_from_target(
                    repository, args.target, base.manifest
                ),
                trusted_parent_commit=_run_git(
                    repository, "rev-parse", f"{args.base}^{{commit}}"
                ).strip(),
                trusted_parent_tree=_run_git(
                    repository, "rev-parse", f"{args.base}^{{tree}}"
                ).strip(),
            )
        )
        return _print_errors(errors)
    except (OSError, UnicodeError, PlanGateError) as error:
        return _print_errors([str(error)])


if __name__ == "__main__":
    raise SystemExit(main())
