#!/usr/bin/env python3
"""Fail-closed verifier for the one-time ITER-010 plan recovery.

The trusted plan gate copies this file to an isolated directory and executes::

    python -I -S runner.py verify-plan-evidence

The verifier therefore uses only the Python standard library and treats the
exact bytes received on stdin as the evidence artifact.  It recognizes only
the user-authorized plan recovery receipt under PDR-009 and the corresponding
PDR-010 activation receipt.  Neither receipt grants product-code or external
execution authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any, Mapping, Sequence


EVIDENCE_SCHEMA = "DEVELOPMENT_PLAN_GATE_EVIDENCE@1"
EVIDENCE_VERIFIER = "ITER010_PLAN_RECOVERY@1"
ACTION_REF = "ITER-010-ACTION-USER-PLAN-RECOVERY-001"
TARGET_PLAN_REVISION_REF = "ITER-010-PDR-010"

PLAN_CHANGE_AUTHORIZATION_REF = (
    "local-user-message-utf8:"
    "sha256:5ced06d2604020248c5baf69421ccbb4e5c047288b6db5b2202675c558c38cf6"
)
RECOVERY_AUTHORIZATION_REF = (
    "local-user-message-utf8:"
    "sha256:6cf2531ab1119b67ad2010040ae1ac73f817785684fccc26111b3b70ef5fcbe5"
)
AUTHORIZATION_REFS = (
    PLAN_CHANGE_AUTHORIZATION_REF,
    RECOVERY_AUTHORIZATION_REF,
)

RECOVERY_CASE_ID = "V-PLAN-RECOVERY-001"
ACTIVATION_CASE_ID = "V-PDR010-ACTIVATION-001"
CASE_SPECS: Mapping[str, Mapping[str, str]] = {
    RECOVERY_CASE_ID: {
        "plan_revision_ref": "ITER-010-PDR-009",
        "result_id": "ITER-010-RESULT-V-PLAN-RECOVERY-001",
        "evidence_artifact_path": (
            "docs/project/iterations/iteration-010/results/evidence/"
            "v-plan-recovery-001.json"
        ),
    },
    ACTIVATION_CASE_ID: {
        "plan_revision_ref": TARGET_PLAN_REVISION_REF,
        "result_id": "ITER-010-RESULT-V-PDR010-ACTIVATION-001",
        "evidence_artifact_path": (
            "docs/project/iterations/iteration-010/results/evidence/"
            "v-pdr010-activation-001.json"
        ),
    },
}

ACTION_EVIDENCE_SCHEMA = "ITER010_USER_PLAN_RECOVERY_EVIDENCE@1"
EXECUTION_INPUT_SCHEMA = "ITER010_USER_PLAN_RECOVERY_INPUT@1"
SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")

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
ACTION_EVIDENCE_KEYS = {
    "schema",
    "target_plan_revision_ref",
    "authorization_refs",
    "change_boundary",
}
CHANGE_BOUNDARY_KEYS = {
    "plan_governance_change_authorized",
    "product_code_change_authorized",
    "external_execution_authorized",
}
COUNTER_KEYS = {
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
CASE_OUTCOME_KEYS = {"case_id", "verdict", "evidence_ref", "evidence_digest"}
LIVE_FIELDS = {
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


class EvidenceError(ValueError):
    """Raised when recovery evidence is not exactly authorized."""


def canonical_json_bytes(value: Any) -> bytes:
    """Return the canonical bytes used for every internal evidence digest."""

    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _unique_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_raw_evidence(raw: bytes) -> dict[str, Any]:
    """Decode one strict JSON object without normalizing the supplied bytes."""

    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                EvidenceError(f"invalid JSON number: {token}")
            ),
        )
    except UnicodeDecodeError as error:
        raise EvidenceError("evidence is not strict UTF-8") from error
    except json.JSONDecodeError as error:
        raise EvidenceError("evidence is not one valid JSON value") from error
    if type(value) is not dict:
        raise EvidenceError("evidence root must be an object")
    return value


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise EvidenceError(f"{label} must be an object")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unexpected = sorted(actual - expected)
        details: list[str] = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if unexpected:
            details.append("unexpected=" + ",".join(unexpected))
        raise EvidenceError(f"{label} is not closed ({'; '.join(details)})")


def _require_digest(value: Any, label: str) -> str:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise EvidenceError(f"{label} must be an exact sha256 digest")
    return value


def _require_zero(value: Any, label: str) -> None:
    if type(value) is not int or value != 0:
        raise EvidenceError(f"{label} must equal integer zero")


def _expected_action_evidence() -> dict[str, Any]:
    return {
        "schema": ACTION_EVIDENCE_SCHEMA,
        "target_plan_revision_ref": TARGET_PLAN_REVISION_REF,
        "authorization_refs": list(AUTHORIZATION_REFS),
        "change_boundary": {
            "plan_governance_change_authorized": True,
            "product_code_change_authorized": False,
            "external_execution_authorized": False,
        },
    }


def _execution_input(case_id: str, subject_digest: str) -> dict[str, str]:
    spec = CASE_SPECS[case_id]
    return {
        "schema": EXECUTION_INPUT_SCHEMA,
        "plan_revision_ref": spec["plan_revision_ref"],
        "target_plan_revision_ref": TARGET_PLAN_REVISION_REF,
        "action_ref": ACTION_REF,
        "verification_case_id": case_id,
        "result_id": spec["result_id"],
        "evidence_artifact_path": spec["evidence_artifact_path"],
        "subject_digest": subject_digest,
    }


def build_evidence(case_id: str, runner_identity_digest: str) -> dict[str, Any]:
    """Build deterministic valid evidence for tests and the sealing workflow."""

    spec = CASE_SPECS.get(case_id)
    if spec is None:
        raise EvidenceError("verification case is not registered")
    _require_digest(runner_identity_digest, "runner_identity_digest")
    action_evidence = _expected_action_evidence()
    subject = canonical_digest(action_evidence)
    execution_input_digest = canonical_digest(_execution_input(case_id, subject))
    receipt = {
        "runner_id": EVIDENCE_VERIFIER,
        "runner_identity_digest": runner_identity_digest,
        "execution_input_digest": execution_input_digest,
        "exit_code": 0,
        "completed": True,
    }
    outcomes = [
        {
            "case_id": case_id,
            "verdict": "PASS",
            "evidence_ref": spec["evidence_artifact_path"] + "#action_evidence",
            "evidence_digest": subject,
        }
    ]
    return {
        "schema": EVIDENCE_SCHEMA,
        "result_id": spec["result_id"],
        "plan_revision_ref": spec["plan_revision_ref"],
        "action_ref": ACTION_REF,
        "verification_case_id": case_id,
        "plan_gate_verdict": "PASS",
        "evidence_verifier": EVIDENCE_VERIFIER,
        "evidence_artifact_path": spec["evidence_artifact_path"],
        "execution_input_digest": execution_input_digest,
        "runner_identity_digest": runner_identity_digest,
        "runner_receipt_digest": canonical_digest(receipt),
        "verification_report_digest": canonical_digest(outcomes),
        "subject_digest": subject,
        "action_evidence": action_evidence,
        "execution_counters": {key: 0 for key in sorted(COUNTER_KEYS)},
        "runner_receipt": receipt,
        "case_outcomes": outcomes,
    }


def validate_evidence(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Validate closed recovery evidence and return the exact live receipt."""

    _exact_keys(artifact, EVIDENCE_KEYS, "evidence")
    if artifact.get("schema") != EVIDENCE_SCHEMA:
        raise EvidenceError("evidence schema is invalid")
    if artifact.get("evidence_verifier") != EVIDENCE_VERIFIER:
        raise EvidenceError("evidence verifier is invalid")
    if artifact.get("action_ref") != ACTION_REF:
        raise EvidenceError("action_ref is invalid")

    case_id = artifact.get("verification_case_id")
    if type(case_id) is not str or case_id not in CASE_SPECS:
        raise EvidenceError("verification case is not registered")
    spec = CASE_SPECS[case_id]
    for field in ("plan_revision_ref", "result_id", "evidence_artifact_path"):
        if artifact.get(field) != spec[field]:
            raise EvidenceError(f"{field} does not match the verification case")
    if artifact.get("plan_gate_verdict") != "PASS":
        raise EvidenceError("authorized recovery evidence must have verdict PASS")

    for field in (
        "execution_input_digest",
        "runner_identity_digest",
        "runner_receipt_digest",
        "verification_report_digest",
        "subject_digest",
    ):
        _require_digest(artifact.get(field), field)

    action_evidence = _require_object(
        artifact.get("action_evidence"), "action_evidence"
    )
    _exact_keys(action_evidence, ACTION_EVIDENCE_KEYS, "action_evidence")
    if action_evidence.get("schema") != ACTION_EVIDENCE_SCHEMA:
        raise EvidenceError("action evidence schema is invalid")
    if action_evidence.get("target_plan_revision_ref") != TARGET_PLAN_REVISION_REF:
        raise EvidenceError("target plan revision is invalid")
    refs = action_evidence.get("authorization_refs")
    if type(refs) is not list or refs != list(AUTHORIZATION_REFS):
        raise EvidenceError("authorization refs do not bind both exact user messages")
    boundary = _require_object(
        action_evidence.get("change_boundary"), "action_evidence.change_boundary"
    )
    _exact_keys(boundary, CHANGE_BOUNDARY_KEYS, "action_evidence.change_boundary")
    if boundary != _expected_action_evidence()["change_boundary"]:
        raise EvidenceError("recovery may authorize plan governance only")
    expected_subject = canonical_digest(action_evidence)
    if artifact.get("subject_digest") != expected_subject:
        raise EvidenceError("subject_digest does not bind exact action_evidence")
    expected_input = canonical_digest(_execution_input(case_id, expected_subject))
    if artifact.get("execution_input_digest") != expected_input:
        raise EvidenceError("execution_input_digest does not bind recovery inputs")

    counters = _require_object(
        artifact.get("execution_counters"), "execution_counters"
    )
    _exact_keys(counters, COUNTER_KEYS, "execution_counters")
    for field in COUNTER_KEYS:
        _require_zero(counters.get(field), f"execution_counters.{field}")

    receipt = _require_object(artifact.get("runner_receipt"), "runner_receipt")
    _exact_keys(receipt, RUNNER_RECEIPT_KEYS, "runner_receipt")
    if receipt.get("runner_id") != EVIDENCE_VERIFIER:
        raise EvidenceError("runner receipt verifier is invalid")
    if receipt.get("runner_identity_digest") != artifact.get(
        "runner_identity_digest"
    ):
        raise EvidenceError("runner receipt identity is not consistently bound")
    if receipt.get("execution_input_digest") != expected_input:
        raise EvidenceError("runner receipt input is not consistently bound")
    if receipt.get("exit_code") != 0 or receipt.get("completed") is not True:
        raise EvidenceError("runner receipt must record completed zero exit")
    if artifact.get("runner_receipt_digest") != canonical_digest(receipt):
        raise EvidenceError("runner_receipt_digest does not match")

    outcomes = artifact.get("case_outcomes")
    if type(outcomes) is not list or len(outcomes) != 1:
        raise EvidenceError("case_outcomes must contain exactly the selected case")
    outcome = _require_object(outcomes[0], "case_outcomes[0]")
    _exact_keys(outcome, CASE_OUTCOME_KEYS, "case_outcomes[0]")
    expected_outcome = {
        "case_id": case_id,
        "verdict": "PASS",
        "evidence_ref": spec["evidence_artifact_path"] + "#action_evidence",
        "evidence_digest": expected_subject,
    }
    if outcome != expected_outcome:
        raise EvidenceError("case outcome is not the exact recovery receipt")
    if artifact.get("verification_report_digest") != canonical_digest(outcomes):
        raise EvidenceError("verification_report_digest does not match")

    live = {
        "evidence_verifier": EVIDENCE_VERIFIER,
        "action_ref": ACTION_REF,
        "verification_case_id": case_id,
        "plan_gate_verdict": "PASS",
        "execution_input_digest": expected_input,
        "runner_identity_digest": artifact["runner_identity_digest"],
        "verification_report_digest": artifact["verification_report_digest"],
        "subject_digest": expected_subject,
        "external_model_call_count": 0,
    }
    if set(live) != LIVE_FIELDS:
        raise AssertionError("live verifier field contract drifted")
    return live


def _command_verify() -> int:
    try:
        raw = sys.stdin.buffer.read(1_000_001)
        if len(raw) > 1_000_000:
            raise EvidenceError("evidence exceeds one megabyte")
        artifact = load_raw_evidence(raw)
        live = validate_evidence(artifact)
    except (EvidenceError, KeyError, TypeError, ValueError, RecursionError):
        return 2
    sys.stdout.buffer.write(canonical_json_bytes(live))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("verify-plan-evidence")
    arguments = parser.parse_args(argv)
    if arguments.command == "verify-plan-evidence":
        return _command_verify()
    raise AssertionError(arguments.command)


if __name__ == "__main__":
    raise SystemExit(main())
