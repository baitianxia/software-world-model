#!/usr/bin/env python3
"""Verify the frozen ITER-010 failure handoff or user-direction record.

The verifier checks closed schemas, exact Git objects, embedded capture
digests, runtime-count reconciliation, and the absence of fabricated
answer/review/comparison claims. It does not authenticate local captures or
decide semantic answer quality.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any, Mapping, Sequence


EVIDENCE_SCHEMA = "DEVELOPMENT_PLAN_GATE_EVIDENCE@1"
EVIDENCE_VERIFIER = "ITER010_MVP_LIGHT@3"
PLAN_REVISION = "ITER-010-PDR-011"
EXPERIENCE_ACTION = "ITER-010-ACTION-USER-PLAN-RECOVERY-001"
EXPERIENCE_CASE = "V-MVP-EXPERIENCE-001"
EXPERIENCE_RESULT = "ITER-010-RESULT-V-MVP-EXPERIENCE-001"
EXPERIENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/"
    "v-mvp-experience-001.json"
)
USER_DIRECTION_ACTION = "ITER-010-ACTION-USER-DIRECTION-DECISION-001"
USER_DIRECTION_CASE = "V-PREVIEW-002"
USER_DIRECTION_RESULT = "ITER-010-RESULT-V-USER-DIRECTION-DECISION-001"
USER_DIRECTION_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/"
    "v-user-direction-decision-001.json"
)

RECOVERY_AUTHORIZATION_REF = (
    "local-user-message-utf8:sha256:"
    "382638cd16fdbc85c08a4202a94e630fe4c973ce03bb0d8a1671cbe4ee151aa7"
)
PRODUCT_CANDIDATE_COMMIT = "a5c780f51fa5242ee8209766712ad408ed023f80"
PRODUCT_CANDIDATE_TREE = "4dcf8b0eca2f50b7618d0af1c43eca1613bace94"
PRODUCT_CANDIDATE_RAW_COMMIT = (
    "tree 4dcf8b0eca2f50b7618d0af1c43eca1613bace94\n"
    "parent c0d53498f1d1db26d1d3ad20296d8313df452dca\n"
    "author Codex <codex@localhost> 1787910652 +0800\n"
    "committer Codex <codex@localhost> 1787910652 +0800\n"
    "\n"
    "fix: preserve provider qualification for format repair\n"
)
LOOPBACK_BROWSER_URL = "http://127.0.0.1:8765/"

SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
GIT_OBJECT_RE = re.compile(r"[0-9a-f]{40}\Z")
IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,191}\Z")
USER_REF_RE = re.compile(
    r"(?:codex-user-message|local-user-message-utf8):sha256:[0-9a-f]{64}\Z"
)
QUESTION_CATEGORIES = {
    "SYSTEM_PURPOSE_OR_ENTRY",
    "BEHAVIOR_CALL_FLOW_OR_SIDE_EFFECT",
    "FAILURE_AUTHORIZATION_OR_UNKNOWN",
}
STANDING_SCOPE_VALUES = {
    "schema": "PUBLIC_OSS_EVALUATION_STANDING_AUTHORITY@1",
    "authority_owner_ref": "public_oss_evaluation_standing_authority",
    "root_authorization_ref": (
        "codex-user-message:sha256:"
        "f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5"
    ),
    "correction_ref": (
        "local-user-message-utf8:sha256:"
        "6dd1e3f4c444b69539f2c9082e26f605d4b0ff84b5dcf99cfb53b42cdb334bdb"
    ),
    "purpose": "public-open-source-direction-canary-and-web-experience-evaluation",
    "source_origin": "https://github.com/macrozheng/mall.git",
    "source_license": "Apache-2.0",
    "source_commit": "0504e86b1f1b6f1b8aa6a734d37a90fb67346be7",
    "source_tree": "047d79d8588b76013c260f3f1a9565707301a60a",
    "source_clean": True,
    "source_read_only": True,
    "route_policy_ref": "provider_route_policy",
    "fallback_policy_ref": "deepseek_dispatch_admission_policy",
    "scope_delta_detected": False,
}
MACHINE_ATTESTATION = {
    "scope": "SCHEMA_DIGEST_GIT_OBJECT_AND_RUNTIME_RECONCILIATION_ONLY",
    "local_capture_authenticity_verified": False,
    "semantic_answer_quality_verified": False,
    "failed_turn_outputs_are_answers": False,
    "user_direction_required": True,
}

EVIDENCE_KEYS = {
    "schema", "result_id", "plan_revision_ref", "action_ref",
    "verification_case_id", "plan_gate_verdict", "evidence_verifier",
    "evidence_artifact_path", "execution_input_digest",
    "runner_identity_digest", "runner_receipt_digest",
    "verification_report_digest", "subject_digest", "action_evidence",
    "execution_counters", "runner_receipt", "case_outcomes",
}
COUNTER_KEYS = {
    "external_model_call_count", "provider_dispatch_count",
    "credential_resolution_count", "tls_attempt_count",
    "http_dispatch_count", "full_regression_run_count",
}
RUNNER_RECEIPT_KEYS = {
    "runner_id", "runner_identity_digest", "execution_input_digest",
    "exit_code", "completed",
}
CASE_OUTCOME_KEYS = {"case_id", "verdict", "evidence_ref", "evidence_digest"}
LIVE_FIELDS = {
    "evidence_verifier", "action_ref", "verification_case_id",
    "plan_gate_verdict", "execution_input_digest", "runner_identity_digest",
    "verification_report_digest", "subject_digest", "external_model_call_count",
}
EXPERIENCE_KEYS = {
    "schema", "handoff_parent_identity", "product_candidate_identity",
    "standing_scope", "browser_url", "handoff_outcome",
    "recovery_authorization_ref", "machine_attestation", "repair_record",
    "capture_sets", "failure_turns", "execution_reconciliation",
}
IDENTITY_KEYS = {"commit", "tree", "raw_commit", "raw_commit_digest"}
REPAIR_KEYS = {
    "schema", "repair_commit", "root_cause", "general_repair",
    "product_repair_count", "same_material_pre_answer_failure_reproduced",
    "product_repair_stopped",
}
CAPTURE_KEYS = {
    "artifact_session_ref", "product_commit", "product_tree",
    "turn_scope_payload", "turn_scope_payload_digest", "terminal_payload",
    "terminal_payload_digest", "browser_capture_payload",
    "browser_capture_payload_digest", "ark_gateway_database_digest",
    "deepseek_gateway_database_digest", "gateway_calls",
}
GATEWAY_CALL_KEYS = {
    "model_call_id", "current_state", "provider_type", "requested_model_ref",
    "failure_code", "actual_model_fingerprint", "output_digest",
    "termination_reason", "output_normalization",
}
FAILURE_TURN_KEYS = {
    "failure_id", "position", "category", "unseen_during_repair",
    "artifact_session_ref", "conversation_locator", "turn_id", "question_text",
    "initial_model_call_id", "initial_model_output", "initial_model_output_digest",
    "repair_model_call_id", "repair_model_output", "repair_model_output_digest",
    "failure_signature", "failure_detail",
    "raw_model_outputs_are_authorized_answers", "answer_emitted",
    "citation_count", "review_emitted", "current_codex_comparison_performed",
}
RECONCILIATION_KEYS = {
    "artifact_session_count", "ark_external_model_call_count",
    "ark_provider_dispatch_count", "ark_credential_resolution_count",
    "ark_tls_attempt_count", "ark_http_dispatch_count",
    "deepseek_external_model_call_count", "deepseek_provider_dispatch_count",
    "deepseek_credential_resolution_count", "deepseek_tls_attempt_count",
    "deepseek_http_dispatch_count", "request_retry_count",
    "human_approval_request_count", "full_regression_run_count",
}
USER_DIRECTION_KEYS = {
    "schema", "decision", "decision_ref", "decision_evidence",
    "decision_evidence_digest", "local_record_only", "platform_authenticated",
    "known_limitations_acknowledged", "unlocks_followup_work",
    "followup_plan_revision_and_explicit_authorization_required",
}


class EvidenceError(ValueError):
    """Raised when the handoff packet violates its closed contract."""


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def canonical_digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def raw_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _unique_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise EvidenceError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def load_raw_evidence(raw: bytes) -> dict[str, Any]:
    try:
        text = raw.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=lambda token: (_ for _ in ()).throw(
                EvidenceError(f"invalid JSON number: {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError("evidence must be one strict UTF-8 JSON object") from exc
    if type(value) is not dict:
        raise EvidenceError("evidence must be one JSON object")
    return value


def _object(value: Any, label: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise EvidenceError(f"{label} must be an object")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise EvidenceError(f"{label} must use its exact closed schema")


def _digest(value: Any, label: str) -> str:
    if type(value) is not str or SHA256_RE.fullmatch(value) is None:
        raise EvidenceError(f"{label} must be an exact sha256 digest")
    return value


def _identifier(value: Any, label: str) -> str:
    if type(value) is not str or IDENTIFIER_RE.fullmatch(value) is None:
        raise EvidenceError(f"{label} must be a bounded identifier")
    return value


def _count(value: Any, label: str) -> int:
    if type(value) is not int or value < 0:
        raise EvidenceError(f"{label} must be a non-negative integer")
    return value


def _text(value: Any, label: str, *, minimum: int = 8) -> str:
    if type(value) is not str or len(value.strip()) < minimum:
        raise EvidenceError(f"{label} must contain inspectable text")
    return value


def _git_identity(
    value: Any,
    label: str,
    *,
    expected_commit: str | None = None,
    expected_tree: str | None = None,
    expected_raw_commit: str | None = None,
) -> tuple[str, str]:
    identity = _object(value, label)
    _exact_keys(identity, IDENTITY_KEYS, label)
    commit = identity.get("commit")
    tree = identity.get("tree")
    raw_commit = identity.get("raw_commit")
    if type(commit) is not str or GIT_OBJECT_RE.fullmatch(commit) is None:
        raise EvidenceError(f"{label}.commit must be an exact Git object ID")
    if type(tree) is not str or GIT_OBJECT_RE.fullmatch(tree) is None:
        raise EvidenceError(f"{label}.tree must be an exact Git object ID")
    if type(raw_commit) is not str or not raw_commit:
        raise EvidenceError(f"{label}.raw_commit must contain exact Git commit bytes")
    if identity.get("raw_commit_digest") != raw_digest(raw_commit):
        raise EvidenceError(f"{label}.raw_commit_digest is invalid")
    raw = raw_commit.encode("utf-8")
    actual_commit = hashlib.sha1(
        b"commit " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    if commit != actual_commit:
        raise EvidenceError(f"{label}.commit does not bind raw_commit")
    first_line = raw_commit.splitlines()[0] if raw_commit.splitlines() else ""
    if first_line != f"tree {tree}":
        raise EvidenceError(f"{label}.tree does not match raw_commit")
    if expected_commit is not None and commit != expected_commit:
        raise EvidenceError(f"{label}.commit is not the frozen product candidate")
    if expected_tree is not None and tree != expected_tree:
        raise EvidenceError(f"{label}.tree is not the frozen product candidate")
    if expected_raw_commit is not None and raw_commit != expected_raw_commit:
        raise EvidenceError(f"{label}.raw_commit is not the frozen product candidate")
    return commit, tree


def _standing_scope(value: Any) -> None:
    scope = _object(value, "standing_scope")
    expected_keys = set(STANDING_SCOPE_VALUES) | {"binding_digest"}
    _exact_keys(scope, expected_keys, "standing_scope")
    for field, expected in STANDING_SCOPE_VALUES.items():
        if scope.get(field) != expected or type(scope.get(field)) is not type(expected):
            raise EvidenceError(f"standing_scope.{field} is not the frozen value")
    if scope.get("binding_digest") != canonical_digest(STANDING_SCOPE_VALUES):
        raise EvidenceError("standing_scope.binding_digest is invalid")


def _raw_json_payload(raw: Any, digest: Any, label: str) -> dict[str, Any]:
    if type(raw) is not str or not raw.strip():
        raise EvidenceError(f"{label} must embed raw JSON bytes")
    if digest != raw_digest(raw):
        raise EvidenceError(f"{label} digest is invalid")
    try:
        return load_raw_evidence(raw.encode("utf-8"))
    except EvidenceError as exc:
        raise EvidenceError(f"{label} must be strict JSON") from exc


def _provider_audit(terminal: Mapping[str, Any], provider: str) -> dict[str, Any]:
    audits = terminal.get("provider_audits")
    if type(audits) is not list:
        raise EvidenceError("terminal provider_audits must be a list")
    matches = [
        item
        for item in audits
        if type(item) is dict and item.get("provider_type") == provider
    ]
    if len(matches) != 1:
        raise EvidenceError(f"terminal must contain exactly one {provider} audit")
    return matches[0]


def _validate_terminal(terminal: Mapping[str, Any], label: str) -> tuple[int, str]:
    if terminal.get("schema") != "SWM-ENGINEERING-CHAT-ARTIFACT-TERMINAL-RECEIPT@2":
        raise EvidenceError(f"{label} terminal schema is invalid")
    if terminal.get("status") != "STOPPED_AFTER_DISPATCH":
        raise EvidenceError(f"{label} must be a stopped-after-dispatch receipt")
    if (
        terminal.get("request_retry_count") != 0
        or terminal.get("human_approval_request_count") != 0
        or terminal.get("production_activation") != "NOT_EXECUTED"
    ):
        raise EvidenceError(f"{label} terminal safety counters are invalid")
    terminal_digest = _digest(terminal.get("digest"), f"{label}.digest")

    ark = _provider_audit(terminal, "VOLCENGINE_ARK")
    deepseek = _provider_audit(terminal, "DEEPSEEK")
    ark_count = _count(ark.get("provider_dispatch_count"), f"{label}.ark dispatches")
    if ark_count < 1 or terminal.get("provider_dispatch_count") != ark_count:
        raise EvidenceError(f"{label} Ark and terminal dispatch counts do not reconcile")
    for field in ("model_call_receipt_digests", "model_dispatch_audit_digests"):
        values = ark.get(field)
        if (
            type(values) is not list
            or len(values) != ark_count
            or any(
                type(item) is not str or SHA256_RE.fullmatch(item) is None
                for item in values
            )
        ):
            raise EvidenceError(f"{label} Ark {field} does not cover every dispatch")
    if ark.get("request_retry_count") != 0:
        raise EvidenceError(f"{label} Ark request retry count must be zero")
    transport = _object(ark.get("transport_session_audit"), f"{label}.ark transport")
    expected_counts = {
        "credential_resolution_count": ark_count,
        "credential_resolution_success_count": ark_count,
        "tls_handshake_attempt_count": ark_count,
        "tls_handshake_success_count": ark_count,
        "http_dispatch_count": ark_count,
        "request_retry_count": 0,
        "pre_dispatch_tls_handshake_failure_count": 0,
        "post_dispatch_outcome_unknown_count": 0,
    }
    for field, expected in expected_counts.items():
        if transport.get(field) != expected:
            raise EvidenceError(f"{label} Ark transport {field} must equal {expected}")
    for field in ("pre_dispatch_tls_failure_codes", "post_dispatch_failure_codes"):
        if transport.get(field) != []:
            raise EvidenceError(f"{label} Ark transport {field} must be empty")

    if deepseek.get("provider_dispatch_count") != 0 or deepseek.get("request_retry_count") != 0:
        raise EvidenceError(f"{label} DeepSeek dispatch and retry counts must be zero")
    if (
        deepseek.get("model_call_receipt_digests") != []
        or deepseek.get("model_dispatch_audit_digests") != []
    ):
        raise EvidenceError(f"{label} DeepSeek receipt lists must be empty")
    fallback_transport = _object(
        deepseek.get("transport_session_audit"), f"{label}.deepseek transport"
    )
    for field in (
        "credential_resolution_count", "tls_handshake_attempt_count",
        "http_dispatch_count", "request_retry_count",
        "pre_dispatch_tls_handshake_failure_count",
        "post_dispatch_outcome_unknown_count",
    ):
        if fallback_transport.get(field) != 0:
            raise EvidenceError(f"{label} DeepSeek transport {field} must be zero")
    return ark_count, terminal_digest


def _validate_gateway_calls(
    value: Any, expected_count: int, label: str
) -> tuple[dict[str, str], set[str]]:
    if type(value) is not list or len(value) != expected_count:
        raise EvidenceError(f"{label} gateway_calls must cover every Ark dispatch")
    outputs: dict[str, str] = {}
    call_ids: set[str] = set()
    for index, raw in enumerate(value):
        call = _object(raw, f"{label}.gateway_calls[{index}]")
        _exact_keys(call, GATEWAY_CALL_KEYS, f"{label}.gateway_calls[{index}]")
        call_id = _identifier(call.get("model_call_id"), "model_call_id")
        if call_id in call_ids:
            raise EvidenceError(f"{label} gateway call IDs must be unique")
        call_ids.add(call_id)
        if (
            call.get("current_state") != "COMPLETED"
            or call.get("provider_type") != "VOLCENGINE_ARK"
            or call.get("requested_model_ref") != "glm-5-2-260617"
            or call.get("actual_model_fingerprint") != "glm-5.2"
            or call.get("termination_reason") != "stop"
            or call.get("output_normalization") != "IDENTITY"
        ):
            raise EvidenceError(f"{label} gateway call identity or terminal state is invalid")
        failure_code = call.get("failure_code")
        if failure_code is not None and type(failure_code) is not str:
            raise EvidenceError(f"{label} gateway failure_code must be string or null")
        outputs[call_id] = _digest(call.get("output_digest"), "gateway output_digest")
    return outputs, call_ids


def _validate_browser_capture(
    value: Mapping[str, Any], expected_count: int, terminal_digest: str
) -> tuple[set[str], set[str]]:
    if (
        value.get("schema") != "ITER-010-MVP-BROWSER-CAPTURE@1"
        or value.get("candidate_commit") != PRODUCT_CANDIDATE_COMMIT
        or value.get("candidate_tree") != PRODUCT_CANDIDATE_TREE
        or value.get("browser_url") != LOOPBACK_BROWSER_URL
        or value.get("local_capture_authenticity_machine_verified") is not False
        or value.get("new_conversation_isolation_observed") is not True
        or value.get("ark_provider_dispatch_count") != expected_count
        or value.get("ark_credential_resolution_count") != expected_count
        or value.get("ark_tls_attempt_count") != expected_count
        or value.get("ark_tls_success_count") != expected_count
        or value.get("ark_http_dispatch_count") != expected_count
        or value.get("deepseek_provider_dispatch_count") != 0
        or value.get("deepseek_credential_resolution_count") != 0
        or value.get("deepseek_tls_attempt_count") != 0
        or value.get("deepseek_http_dispatch_count") != 0
        or value.get("request_retry_count") != 0
        or value.get("human_approval_request_count") != 0
        or value.get("production_activation") != "NOT_EXECUTED"
        or value.get("terminal_receipt_digest") != terminal_digest
    ):
        raise EvidenceError("browser capture does not reconcile with candidate/runtime")
    conversations = value.get("conversations")
    if type(conversations) is not list or len(conversations) < 2:
        raise EvidenceError("browser capture must show new-conversation isolation")
    turn_ids: set[str] = set()
    messages: set[str] = set()
    for conversation in conversations:
        record = _object(conversation, "browser conversation")
        _identifier(record.get("conversation_id"), "browser conversation_id")
        turns = record.get("turns")
        if type(turns) is not list or not turns:
            raise EvidenceError("browser conversation must contain turns")
        for turn in turns:
            item = _object(turn, "browser turn")
            messages.add(_text(item.get("user_message"), "browser user_message"))
            turn_id = item.get("turn_id")
            if turn_id is not None:
                turn_ids.add(_identifier(turn_id, "browser turn_id"))
            if item.get("status") == "FAILED" and (
                item.get("result_kind") != "AGENT_MODEL_CALL_REJECTED"
                or item.get("provider_dispatch_count", 0) < 1
            ):
                raise EvidenceError("failed browser turns must record truthful Agent closure")
    return turn_ids, messages


def _validate_capture_set(value: Any, index: int) -> dict[str, Any]:
    label = f"capture_sets[{index}]"
    capture = _object(value, label)
    _exact_keys(capture, CAPTURE_KEYS, label)
    session_ref = _identifier(
        capture.get("artifact_session_ref"), f"{label}.artifact_session_ref"
    )
    if (
        capture.get("product_commit") != PRODUCT_CANDIDATE_COMMIT
        or capture.get("product_tree") != PRODUCT_CANDIDATE_TREE
    ):
        raise EvidenceError(f"{label} is not bound to the frozen product candidate")
    turn_scope = _raw_json_payload(
        capture.get("turn_scope_payload"),
        capture.get("turn_scope_payload_digest"),
        f"{label}.turn_scope_payload",
    )
    if (
        turn_scope.get("schema") != "ITER-010-MVP-EXPERIENCE-TURN-SCOPE@1"
        or turn_scope.get("session_ref") != session_ref
        or turn_scope.get("product_commit") != PRODUCT_CANDIDATE_COMMIT
        or turn_scope.get("product_tree") != PRODUCT_CANDIDATE_TREE
    ):
        raise EvidenceError(f"{label} turn scope binding is invalid")
    interactions = turn_scope.get("interactions")
    if type(interactions) is not list or not interactions:
        raise EvidenceError(f"{label} turn scope must contain interactions")
    messages = {
        _text(item.get("message"), f"{label} interaction message")
        for item in interactions
        if type(item) is dict
    }

    terminal = _raw_json_payload(
        capture.get("terminal_payload"),
        capture.get("terminal_payload_digest"),
        f"{label}.terminal_payload",
    )
    ark_count, terminal_digest = _validate_terminal(terminal, label)
    output_digests, call_ids = _validate_gateway_calls(
        capture.get("gateway_calls"), ark_count, label
    )
    _digest(capture.get("ark_gateway_database_digest"), f"{label}.ark database")
    _digest(capture.get("deepseek_gateway_database_digest"), f"{label}.deepseek database")

    browser_raw = capture.get("browser_capture_payload")
    browser_digest = capture.get("browser_capture_payload_digest")
    browser_turn_ids: set[str] = set()
    if browser_raw is None or browser_digest is None:
        if browser_raw is not None or browser_digest is not None:
            raise EvidenceError(f"{label} browser payload and digest must both be null")
        browser_present = False
    else:
        browser = _raw_json_payload(
            browser_raw, browser_digest, f"{label}.browser_capture_payload"
        )
        browser_turn_ids, browser_messages = _validate_browser_capture(
            browser, ark_count, terminal_digest
        )
        messages.update(browser_messages)
        browser_present = True
    return {
        "session_ref": session_ref,
        "ark_count": ark_count,
        "call_ids": call_ids,
        "output_digests": output_digests,
        "messages": messages,
        "browser_turn_ids": browser_turn_ids,
        "browser_present": browser_present,
    }


def _validate_failure_turns(
    value: Any, captures: Mapping[str, Mapping[str, Any]]
) -> None:
    if type(value) is not list or len(value) != 3:
        raise EvidenceError("failure handoff must contain one original and two rechecks")
    failure_ids: set[str] = set()
    categories: set[str] = set()
    positions: list[str] = []
    used_calls: set[str] = set()
    sessions: set[str] = set()
    for index, raw in enumerate(value):
        label = f"failure_turns[{index}]"
        turn = _object(raw, label)
        _exact_keys(turn, FAILURE_TURN_KEYS, label)
        failure_id = _identifier(turn.get("failure_id"), f"{label}.failure_id")
        if failure_id in failure_ids:
            raise EvidenceError("failure IDs must be unique")
        failure_ids.add(failure_id)
        position = turn.get("position")
        if position not in {"ORIGINAL", "HETEROGENEOUS_RECHECK"}:
            raise EvidenceError("failure position is invalid")
        positions.append(str(position))
        unseen = turn.get("unseen_during_repair")
        if type(unseen) is not bool or unseen is not (position == "HETEROGENEOUS_RECHECK"):
            raise EvidenceError("only heterogeneous rechecks may be marked unseen")
        category = turn.get("category")
        if category not in QUESTION_CATEGORIES:
            raise EvidenceError("failure category is invalid")
        categories.add(str(category))
        session_ref = _identifier(
            turn.get("artifact_session_ref"), f"{label}.artifact_session_ref"
        )
        capture = captures.get(session_ref)
        if capture is None:
            raise EvidenceError("failure turn references an unknown artifact session")
        sessions.add(session_ref)
        _text(turn.get("conversation_locator"), f"{label}.conversation_locator", minimum=3)
        turn_id = turn.get("turn_id")
        if turn_id is not None:
            turn_id = _identifier(turn_id, f"{label}.turn_id")
            if turn_id not in capture["browser_turn_ids"]:
                raise EvidenceError("failure turn_id is absent from its browser capture")
        question = _text(turn.get("question_text"), f"{label}.question_text")
        if question not in capture["messages"]:
            raise EvidenceError("failure question is absent from its embedded capture")
        for phase in ("initial", "repair"):
            call_id = _identifier(
                turn.get(f"{phase}_model_call_id"),
                f"{label}.{phase}_model_call_id",
            )
            output = _text(
                turn.get(f"{phase}_model_output"),
                f"{label}.{phase}_model_output",
            )
            if turn.get(f"{phase}_model_output_digest") != raw_digest(output):
                raise EvidenceError(f"{label} {phase} output digest is invalid")
            if capture["output_digests"].get(call_id) != raw_digest(output):
                raise EvidenceError(f"{label} {phase} output is not bound to Gateway")
            if call_id in used_calls:
                raise EvidenceError("failure call IDs must be unique")
            used_calls.add(call_id)
        if turn.get("failure_signature") != "PRE_ANSWER_AGENT_MODEL_CALL_REJECTED":
            raise EvidenceError("failure signature must remain pre-answer Agent rejection")
        _text(turn.get("failure_detail"), f"{label}.failure_detail")
        if (
            turn.get("raw_model_outputs_are_authorized_answers") is not False
            or turn.get("answer_emitted") is not False
            or turn.get("citation_count") != 0
            or turn.get("review_emitted") is not False
            or turn.get("current_codex_comparison_performed") is not False
        ):
            raise EvidenceError(
                "failed turns must not fabricate Answer/Citation/Review/Codex records"
            )
    if positions.count("ORIGINAL") != 1 or positions.count("HETEROGENEOUS_RECHECK") != 2:
        raise EvidenceError("failure handoff requires one original and two rechecks")
    if categories != QUESTION_CATEGORIES:
        raise EvidenceError("failure handoff must cover all three heterogeneous categories")
    if len(sessions) < 2:
        raise EvidenceError("failure handoff must preserve multiple artifact sessions")


def _validate_reconciliation(
    value: Any, captures: Sequence[Mapping[str, Any]], counters: Mapping[str, int]
) -> None:
    record = _object(value, "execution_reconciliation")
    _exact_keys(record, RECONCILIATION_KEYS, "execution_reconciliation")
    ark_count = sum(int(capture["ark_count"]) for capture in captures)
    expected = {
        "artifact_session_count": len(captures),
        "ark_external_model_call_count": ark_count,
        "ark_provider_dispatch_count": ark_count,
        "ark_credential_resolution_count": ark_count,
        "ark_tls_attempt_count": ark_count,
        "ark_http_dispatch_count": ark_count,
        "deepseek_external_model_call_count": 0,
        "deepseek_provider_dispatch_count": 0,
        "deepseek_credential_resolution_count": 0,
        "deepseek_tls_attempt_count": 0,
        "deepseek_http_dispatch_count": 0,
        "request_retry_count": 0,
        "human_approval_request_count": 0,
        "full_regression_run_count": 0,
    }
    if record != expected:
        raise EvidenceError("execution_reconciliation is not derived from captures")
    expected_counters = {
        "external_model_call_count": ark_count,
        "provider_dispatch_count": ark_count,
        "credential_resolution_count": ark_count,
        "tls_attempt_count": ark_count,
        "http_dispatch_count": ark_count,
        "full_regression_run_count": 0,
    }
    if dict(counters) != expected_counters:
        raise EvidenceError("execution counters do not reconcile with captures")


def _validate_experience(value: Any, verdict: str, counters: Mapping[str, int]) -> None:
    experience = _object(value, "action_evidence")
    _exact_keys(experience, EXPERIENCE_KEYS, "action_evidence")
    if experience.get("schema") != "ITER010_MVP_FAILURE_HANDOFF_PACKET@3":
        raise EvidenceError("failure handoff schema is invalid")
    _git_identity(experience.get("handoff_parent_identity"), "handoff_parent_identity")
    _git_identity(
        experience.get("product_candidate_identity"),
        "product_candidate_identity",
        expected_commit=PRODUCT_CANDIDATE_COMMIT,
        expected_tree=PRODUCT_CANDIDATE_TREE,
        expected_raw_commit=PRODUCT_CANDIDATE_RAW_COMMIT,
    )
    _standing_scope(experience.get("standing_scope"))
    if experience.get("browser_url") != LOOPBACK_BROWSER_URL:
        raise EvidenceError("failure handoff browser URL is invalid")
    if experience.get("handoff_outcome") != "QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR":
        raise EvidenceError("PDR-011 admits only the observed failure handoff")
    if experience.get("recovery_authorization_ref") != RECOVERY_AUTHORIZATION_REF:
        raise EvidenceError("failure handoff lacks exact recovery authorization")
    if verdict != "PASS":
        raise EvidenceError("machine PASS means only structurally complete handoff")
    attestation = _object(experience.get("machine_attestation"), "machine_attestation")
    if attestation != MACHINE_ATTESTATION or any(
        type(attestation.get(key)) is not type(expected)
        for key, expected in MACHINE_ATTESTATION.items()
    ):
        raise EvidenceError("machine attestation must preserve its trust boundary")

    repair = _object(experience.get("repair_record"), "repair_record")
    _exact_keys(repair, REPAIR_KEYS, "repair_record")
    if (
        repair.get("schema") != "ITER010_GENERAL_REPAIR_RECORD@1"
        or repair.get("repair_commit") != PRODUCT_CANDIDATE_COMMIT
        or repair.get("product_repair_count") != 1
        or repair.get("same_material_pre_answer_failure_reproduced") is not True
        or repair.get("product_repair_stopped") is not True
    ):
        raise EvidenceError("repair record does not prove the frozen stop condition")
    _text(repair.get("root_cause"), "repair_record.root_cause")
    _text(repair.get("general_repair"), "repair_record.general_repair")

    raw_captures = experience.get("capture_sets")
    if type(raw_captures) is not list or len(raw_captures) < 2:
        raise EvidenceError("failure handoff requires multiple artifact sessions")
    capture_values = [
        _validate_capture_set(capture, index)
        for index, capture in enumerate(raw_captures)
    ]
    sessions = [str(capture["session_ref"]) for capture in capture_values]
    if len(sessions) != len(set(sessions)):
        raise EvidenceError("artifact session refs must be unique")
    if not any(bool(capture["browser_present"]) for capture in capture_values):
        raise EvidenceError("at least one embedded browser capture is required")
    captures_by_session = {
        str(capture["session_ref"]): capture for capture in capture_values
    }
    _validate_failure_turns(experience.get("failure_turns"), captures_by_session)
    _validate_reconciliation(
        experience.get("execution_reconciliation"), capture_values, counters
    )


def _validate_user_direction(value: Any, verdict: str, counters: Mapping[str, int]) -> None:
    record = _object(value, "action_evidence")
    _exact_keys(record, USER_DIRECTION_KEYS, "action_evidence")
    if record.get("schema") != "ITER010_USER_DIRECTION_RECORD@3":
        raise EvidenceError("user direction schema is invalid")
    if record.get("decision") not in {"CONTINUE", "REWORK", "REDIRECT", "REJECT"}:
        raise EvidenceError("user direction is invalid")
    decision_ref = record.get("decision_ref")
    if type(decision_ref) is not str or USER_REF_RE.fullmatch(decision_ref) is None:
        raise EvidenceError("user direction must bind an exact local decision record")
    evidence = record.get("decision_evidence")
    if type(evidence) is not str or not evidence.strip():
        raise EvidenceError("decision evidence must be embedded")
    if record.get("decision_evidence_digest") != raw_digest(evidence):
        raise EvidenceError("decision evidence digest is invalid")
    if (
        record.get("local_record_only") is not True
        or record.get("platform_authenticated") is not False
        or record.get("known_limitations_acknowledged") is not True
        or record.get("unlocks_followup_work") is not False
        or record.get("followup_plan_revision_and_explicit_authorization_required") is not True
    ):
        raise EvidenceError("user direction trust/unlock boundary is invalid")
    if verdict != "PASS" or any(counters.values()):
        raise EvidenceError("user direction records PASS with zero counters")


def _case_spec(action_ref: Any, case_id: Any) -> tuple[str, str, str]:
    if (action_ref, case_id) == (EXPERIENCE_ACTION, EXPERIENCE_CASE):
        return EXPERIENCE_RESULT, EXPERIENCE_PATH, "experience"
    if (action_ref, case_id) == (USER_DIRECTION_ACTION, USER_DIRECTION_CASE):
        return USER_DIRECTION_RESULT, USER_DIRECTION_PATH, "user-direction"
    raise EvidenceError("action and verification case are not registered")


def validate_evidence(artifact: Mapping[str, Any]) -> dict[str, Any]:
    _exact_keys(artifact, EVIDENCE_KEYS, "evidence")
    if artifact.get("schema") != EVIDENCE_SCHEMA:
        raise EvidenceError("evidence schema is invalid")
    if artifact.get("plan_revision_ref") != PLAN_REVISION:
        raise EvidenceError("plan revision is invalid")
    if artifact.get("evidence_verifier") != EVIDENCE_VERIFIER:
        raise EvidenceError("evidence verifier is invalid")
    verdict = artifact.get("plan_gate_verdict")
    if verdict != "PASS":
        raise EvidenceError("PASS means only that the handoff is structurally complete")
    result_id, evidence_path, role = _case_spec(
        artifact.get("action_ref"), artifact.get("verification_case_id")
    )
    if (
        artifact.get("result_id") != result_id
        or artifact.get("evidence_artifact_path") != evidence_path
    ):
        raise EvidenceError("Result or evidence path is invalid")
    for field in (
        "execution_input_digest", "runner_identity_digest", "runner_receipt_digest",
        "verification_report_digest", "subject_digest",
    ):
        _digest(artifact.get(field), field)

    counters = _object(artifact.get("execution_counters"), "execution_counters")
    _exact_keys(counters, COUNTER_KEYS, "execution_counters")
    parsed_counters = {field: _count(counters.get(field), field) for field in COUNTER_KEYS}
    action_evidence = _object(artifact.get("action_evidence"), "action_evidence")
    if artifact.get("subject_digest") != canonical_digest(action_evidence):
        raise EvidenceError("subject_digest does not bind action_evidence")
    expected_input_digest = canonical_digest(
        {
            "plan_revision_ref": PLAN_REVISION,
            "action_ref": artifact.get("action_ref"),
            "verification_case_id": artifact.get("verification_case_id"),
            "subject_digest": artifact.get("subject_digest"),
        }
    )
    if artifact.get("execution_input_digest") != expected_input_digest:
        raise EvidenceError("execution_input_digest does not bind the subject")
    if role == "experience":
        _validate_experience(action_evidence, str(verdict), parsed_counters)
    else:
        _validate_user_direction(action_evidence, str(verdict), parsed_counters)

    receipt = _object(artifact.get("runner_receipt"), "runner_receipt")
    _exact_keys(receipt, RUNNER_RECEIPT_KEYS, "runner_receipt")
    if (
        receipt.get("runner_id") != EVIDENCE_VERIFIER
        or receipt.get("runner_identity_digest") != artifact.get("runner_identity_digest")
        or receipt.get("execution_input_digest") != artifact.get("execution_input_digest")
        or receipt.get("exit_code") != 0
        or receipt.get("completed") is not True
    ):
        raise EvidenceError("runner receipt does not bind a completed verifier run")
    if artifact.get("runner_receipt_digest") != canonical_digest(receipt):
        raise EvidenceError("runner_receipt_digest is invalid")

    outcomes = artifact.get("case_outcomes")
    if type(outcomes) is not list or len(outcomes) != 1:
        raise EvidenceError("exactly one case outcome is required")
    outcome = _object(outcomes[0], "case_outcomes[0]")
    _exact_keys(outcome, CASE_OUTCOME_KEYS, "case_outcomes[0]")
    if (
        outcome.get("case_id") != artifact.get("verification_case_id")
        or outcome.get("verdict") != verdict
    ):
        raise EvidenceError("case outcome does not match the current Case")
    if type(outcome.get("evidence_ref")) is not str or not outcome["evidence_ref"].strip():
        raise EvidenceError("case outcome evidence_ref must be non-empty")
    if outcome.get("evidence_digest") != artifact.get("subject_digest"):
        raise EvidenceError("case outcome does not bind action_evidence")
    if artifact.get("verification_report_digest") != canonical_digest(outcomes):
        raise EvidenceError("verification_report_digest is invalid")

    live = {
        "evidence_verifier": EVIDENCE_VERIFIER,
        "action_ref": artifact["action_ref"],
        "verification_case_id": artifact["verification_case_id"],
        "plan_gate_verdict": verdict,
        "execution_input_digest": artifact["execution_input_digest"],
        "runner_identity_digest": artifact["runner_identity_digest"],
        "verification_report_digest": artifact["verification_report_digest"],
        "subject_digest": artifact["subject_digest"],
        "external_model_call_count": parsed_counters["external_model_call_count"],
    }
    if set(live) != LIVE_FIELDS:
        raise AssertionError("live verifier field contract drifted")
    return live


def _command_verify() -> int:
    try:
        result = validate_evidence(load_raw_evidence(sys.stdin.buffer.read()))
    except EvidenceError:
        return 1
    sys.stdout.buffer.write(canonical_json_bytes(result))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("verify-plan-evidence")
    arguments = parser.parse_args(argv)
    if arguments.command == "verify-plan-evidence":
        return _command_verify()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
