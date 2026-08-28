#!/usr/bin/env python3
"""Verify a structurally complete ITER-010 user handoff packet.

The runner is deliberately narrow. It verifies closed schemas, exact frozen
authority/source bindings, content-addressed evidence bytes, Git object
identity, runtime-receipt reconciliation, and Result bindings. It does not
claim to authenticate local captures or decide whether an engineering answer
is semantically correct. Those judgments remain visible evidence for
independent review and the user's direction decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from typing import Any, Mapping, Sequence


EVIDENCE_SCHEMA = "DEVELOPMENT_PLAN_GATE_EVIDENCE@1"
EVIDENCE_VERIFIER = "ITER010_MVP_LIGHT@2"
PLAN_REVISION = "ITER-010-PDR-010"
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

LOOPBACK_BROWSER_URL = "http://127.0.0.1:8765/"
SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
GIT_OBJECT_RE = re.compile(r"[0-9a-f]{40}\Z")
IDENTIFIER_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")
USER_REF_RE = re.compile(
    r"(?:codex-user-message|local-user-message-utf8):sha256:[0-9a-f]{64}\Z"
)
CREDENTIAL_REF_RE = re.compile(r"(?:env|secret|keychain):[A-Za-z0-9_.:/-]+\Z")

QUESTION_CATEGORIES = {
    "SYSTEM_PURPOSE_OR_ENTRY",
    "BEHAVIOR_CALL_FLOW_OR_SIDE_EFFECT",
    "FAILURE_AUTHORIZATION_OR_UNKNOWN",
}
PER_QUESTION_ARTIFACT_KINDS = {
    "system-answer",
    "current-codex-answer",
    "independent-review",
    "question-comparison",
}
GLOBAL_ARTIFACT_KINDS = {
    "browser-session",
    "source-truth",
    "world-model-cognition",
    "comparison-summary",
}
FAILURE_ARTIFACT_KINDS = {"failure-analysis", "general-repair-rechecks"}

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
EXECUTION_PROFILES = {
    "preferred": {
        "execution_profile_ref": "runtime-config:preferred-qualified-profile",
        "provider_identity": "VOLCENGINE_ARK",
        "model_identity": "glm-5-2-260617",
        "endpoint": "https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions",
        "credential_reference": "env:ARK_API_KEY",
    },
    "fallback": {
        "execution_profile_ref": "runtime-config:fallback-qualified-profile",
        "provider_identity": "DEEPSEEK",
        "model_identity": "deepseek-v4-pro",
        "endpoint": "https://api.deepseek.com/chat/completions",
        "credential_reference": "env:DEEPSEEK_API_KEY",
    },
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
    "schema", "candidate_identity", "standing_scope", "browser_url",
    "handoff_outcome", "machine_attestation", "attachments", "questions",
    "runtime_receipts",
}
CANDIDATE_KEYS = {"commit", "tree", "raw_commit", "raw_commit_digest"}
MACHINE_ATTESTATION = {
    "scope": "SCHEMA_DIGEST_GIT_OBJECT_AND_FROZEN_SCOPE_ONLY",
    "local_capture_authenticity_verified": False,
    "semantic_answer_quality_verified": False,
    "user_direction_required": True,
}
ATTACHMENT_KEYS = {
    "artifact_id", "kind", "question_id", "media_type", "payload",
    "payload_digest",
}
QUESTION_KEYS = {
    "question_id", "category", "unseen_during_repair",
    "system_answer_artifact_id", "current_codex_answer_artifact_id",
    "independent_review_artifact_id", "question_comparison_artifact_id",
}
RUNTIME_RECEIPT_KEYS = {
    "receipt_id", "parent_authority_binding_digest", "candidate_commit",
    "source_commit", "source_tree", "browser_url", "session_id",
    "conversation_id", "turn_id", "role", "route_role",
    "provider_configuration", "provider_configuration_digest", "input_payload",
    "input_digest", "disclosure", "disclosure_digest", "budget", "budget_digest",
    "one_use", "consumed", "expired",
    "external_model_call_count", "provider_dispatch_count",
    "credential_resolution_count", "tls_attempt_count", "http_dispatch_count",
    "receipt_digest",
}
PROVIDER_CONFIGURATION_KEYS = {
    "execution_profile_ref", "provider_identity", "model_identity", "endpoint",
    "credential_reference",
}
DISCLOSURE_KEYS = {
    "schema", "public_source_only", "secret_values_included", "source_origin",
    "source_commit", "input_payload_digest",
}
BUDGET_KEYS = {
    "maximum_calls", "maximum_input_tokens", "maximum_output_tokens",
    "timeout_milliseconds",
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
        value = json.loads(text, object_pairs_hook=_unique_object)
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
    normalized = value.strip().lower()
    if re.fullmatch(
        r"(?:(?:placeholder|pending|todo|not[- ]?executed|n/?a|dummy|sample|test|example|lorem ipsum)"
        r"(?:[ _-]*(?:answer|response|text|value|content|record|result|summary|evidence))?"
        r"|(?:占位|待补|待填写|示例|测试)(?:答案|响应|文本|内容|记录|结果|摘要|证据)?)",
        normalized,
    ):
        raise EvidenceError(f"{label} cannot be a placeholder")
    return value


def _string_list(value: Any, label: str, *, minimum: int = 1) -> list[str]:
    if (
        type(value) is not list
        or len(value) < minimum
        or not all(type(item) is str and item.strip() for item in value)
    ):
        raise EvidenceError(f"{label} must contain non-empty strings")
    if len(value) != len(set(value)):
        raise EvidenceError(f"{label} must be unique")
    return value


def _validate_candidate(value: Any) -> tuple[str, str]:
    candidate = _object(value, "candidate_identity")
    _exact_keys(candidate, CANDIDATE_KEYS, "candidate_identity")
    commit = candidate.get("commit")
    tree = candidate.get("tree")
    raw_commit = candidate.get("raw_commit")
    if type(commit) is not str or GIT_OBJECT_RE.fullmatch(commit) is None:
        raise EvidenceError("candidate commit must be an exact Git object ID")
    if type(tree) is not str or GIT_OBJECT_RE.fullmatch(tree) is None:
        raise EvidenceError("candidate tree must be an exact Git object ID")
    if type(raw_commit) is not str or not raw_commit:
        raise EvidenceError("candidate raw_commit must contain the exact Git commit bytes")
    if candidate.get("raw_commit_digest") != raw_digest(raw_commit):
        raise EvidenceError("candidate raw_commit_digest is invalid")
    raw = raw_commit.encode("utf-8")
    actual_commit = hashlib.sha1(
        b"commit " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    if actual_commit != commit:
        raise EvidenceError("candidate commit does not bind raw_commit")
    first_line = raw_commit.splitlines()[0] if raw_commit.splitlines() else ""
    if first_line != f"tree {tree}":
        raise EvidenceError("candidate tree does not match raw_commit")
    return commit, tree


def _validate_standing_scope(value: Any) -> str:
    scope = _object(value, "standing_scope")
    expected_keys = set(STANDING_SCOPE_VALUES) | {"binding_digest"}
    _exact_keys(scope, expected_keys, "standing_scope")
    for field, expected in STANDING_SCOPE_VALUES.items():
        if type(scope.get(field)) is not type(expected) or scope.get(field) != expected:
            raise EvidenceError(f"standing_scope.{field} is not the frozen value")
    expected_digest = canonical_digest(STANDING_SCOPE_VALUES)
    if scope.get("binding_digest") != expected_digest:
        raise EvidenceError("standing_scope.binding_digest is invalid")
    return expected_digest


def _validate_attachments(value: Any) -> dict[str, dict[str, Any]]:
    if type(value) is not list or not value:
        raise EvidenceError("attachments must be a non-empty list")
    attachments: dict[str, dict[str, Any]] = {}
    allowed_kinds = (
        GLOBAL_ARTIFACT_KINDS | PER_QUESTION_ARTIFACT_KINDS | FAILURE_ARTIFACT_KINDS
    )
    for index, raw in enumerate(value):
        item = _object(raw, f"attachments[{index}]")
        _exact_keys(item, ATTACHMENT_KEYS, f"attachments[{index}]")
        artifact_id = _identifier(
            item.get("artifact_id"), f"attachments[{index}].artifact_id"
        )
        if artifact_id in attachments:
            raise EvidenceError("attachment artifact IDs must be unique")
        if item.get("kind") not in allowed_kinds:
            raise EvidenceError("attachment kind is not registered")
        question_id = item.get("question_id")
        if question_id is not None:
            _identifier(question_id, f"attachments[{index}].question_id")
        if item.get("kind") in GLOBAL_ARTIFACT_KINDS | FAILURE_ARTIFACT_KINDS:
            if question_id is not None:
                raise EvidenceError("global attachments cannot bind a question")
        elif question_id is None:
            raise EvidenceError("per-question attachments must bind a question")
        if item.get("media_type") not in {"application/json", "text/plain"}:
            raise EvidenceError("attachment media_type is not allowed")
        payload = item.get("payload")
        if type(payload) is not str or not payload.strip():
            raise EvidenceError("attachment payload must contain embedded evidence bytes")
        if item.get("payload_digest") != raw_digest(payload):
            raise EvidenceError("attachment payload_digest is invalid")
        attachments[artifact_id] = item
    return attachments


def _validate_questions(
    value: Any, attachments: Mapping[str, Mapping[str, Any]]
) -> tuple[set[str], set[str]]:
    if type(value) is not list or len(value) < 3:
        raise EvidenceError("at least three heterogeneous questions are required")
    seen_ids: set[str] = set()
    categories: set[str] = set()
    unseen_count = 0
    referenced: set[str] = set()
    fields = {
        "system_answer_artifact_id": "system-answer",
        "current_codex_answer_artifact_id": "current-codex-answer",
        "independent_review_artifact_id": "independent-review",
        "question_comparison_artifact_id": "question-comparison",
    }
    for index, raw in enumerate(value):
        question = _object(raw, f"questions[{index}]")
        _exact_keys(question, QUESTION_KEYS, f"questions[{index}]")
        question_id = _identifier(
            question.get("question_id"), f"questions[{index}].question_id"
        )
        if question_id in seen_ids:
            raise EvidenceError("question IDs must be unique")
        seen_ids.add(question_id)
        category = question.get("category")
        if category not in QUESTION_CATEGORIES:
            raise EvidenceError("question category is not registered")
        categories.add(str(category))
        if type(question.get("unseen_during_repair")) is not bool:
            raise EvidenceError("unseen_during_repair must be boolean")
        unseen_count += int(question["unseen_during_repair"])
        for field, expected_kind in fields.items():
            artifact_id = _identifier(
                question.get(field), f"questions[{index}].{field}"
            )
            artifact = attachments.get(artifact_id)
            if artifact is None:
                raise EvidenceError("question references a missing embedded attachment")
            if (
                artifact.get("kind") != expected_kind
                or artifact.get("question_id") != question_id
            ):
                raise EvidenceError("question attachment kind or binding is invalid")
            referenced.add(artifact_id)
    if categories != QUESTION_CATEGORIES:
        raise EvidenceError("the handoff must cover all three question categories")
    if unseen_count < 2:
        raise EvidenceError("at least two questions must be unseen during repair")
    return referenced, seen_ids


def _payload_object(
    attachment: Mapping[str, Any], expected_keys: set[str], schema: str
) -> dict[str, Any]:
    artifact_id = str(attachment.get("artifact_id"))
    try:
        value = load_raw_evidence(str(attachment.get("payload")).encode("utf-8"))
    except EvidenceError as exc:
        raise EvidenceError(f"attachment {artifact_id} payload must be JSON") from exc
    _exact_keys(value, expected_keys, f"attachment {artifact_id} payload")
    if value.get("schema") != schema:
        raise EvidenceError(f"attachment {artifact_id} payload schema is invalid")
    return value


def _validate_attachment_payloads(
    attachments: Mapping[str, Mapping[str, Any]],
    question_ids: set[str],
    candidate_commit: str,
    outcome: str,
) -> dict[str, Any]:
    per_question_seen: dict[str, set[str]] = {
        question_id: set() for question_id in question_ids
    }
    browser_binding: dict[str, Any] | None = None
    review_totals = {
        "major_error_count": 0,
        "material_omission_count": 0,
        "unsupported_citation_count": 0,
    }
    comparison_totals = {
        "material_regression_count": 0,
        "system_total_score": 0,
        "codex_total_score": 0,
    }
    world_model_contributions = 0
    comparison_summary: dict[str, Any] | None = None
    source_citation_labels: dict[str, set[str]] = {}
    answer_citation_labels: dict[str, set[str]] = {}
    question_texts: dict[str, str] = {}
    for attachment in attachments.values():
        kind = str(attachment.get("kind"))
        question_id = attachment.get("question_id")
        if kind == "browser-session":
            value = _payload_object(
                attachment,
                {
                    "schema", "candidate_commit", "browser_url", "operable",
                    "authentication_required", "semantic_turn_count",
                    "new_conversation_isolation_checked", "session_id",
                    "conversation_ids", "turn_ids",
                },
                "ITER010_BROWSER_SESSION_CAPTURE@1",
            )
            if (
                value.get("candidate_commit") != candidate_commit
                or value.get("browser_url") != LOOPBACK_BROWSER_URL
                or value.get("operable") is not True
                or value.get("authentication_required") is not False
                or type(value.get("semantic_turn_count")) is not int
                or int(value["semantic_turn_count"]) < 3
                or value.get("new_conversation_isolation_checked") is not True
            ):
                raise EvidenceError("browser capture does not record the minimum operable Chat")
            session_id = _identifier(value.get("session_id"), "browser session_id")
            conversation_ids = _string_list(
                value.get("conversation_ids"), "browser conversation_ids", minimum=2
            )
            turn_ids = _string_list(
                value.get("turn_ids"), "browser turn_ids", minimum=3
            )
            if len(turn_ids) != value["semantic_turn_count"]:
                raise EvidenceError("browser turn IDs must match semantic_turn_count")
            browser_binding = {
                "session_id": session_id,
                "conversation_ids": set(conversation_ids),
                "turn_ids": set(turn_ids),
            }
        elif kind == "source-truth":
            value = _payload_object(
                attachment,
                {"schema", "source_commit", "records"},
                "ITER010_SOURCE_TRUTH_RECORD@1",
            )
            if value.get("source_commit") != STANDING_SCOPE_VALUES["source_commit"]:
                raise EvidenceError("source-truth record uses the wrong source commit")
            records = value.get("records")
            if type(records) is not list or len(records) != len(question_ids):
                raise EvidenceError("source-truth record must cover every question")
            covered: set[str] = set()
            for record in records:
                item = _object(record, "source-truth record")
                _exact_keys(item, {"question_id", "conclusion", "citations"}, "source-truth record")
                record_id = _identifier(item.get("question_id"), "source-truth question_id")
                _text(item.get("conclusion"), "source-truth conclusion")
                citations = item.get("citations")
                if type(citations) is not list or not citations:
                    raise EvidenceError("source-truth citations must be non-empty")
                labels: set[str] = set()
                for citation in citations:
                    cited = _object(citation, "source-truth citation")
                    _exact_keys(
                        cited,
                        {"label", "path", "line_start", "line_end", "excerpt", "excerpt_digest"},
                        "source-truth citation",
                    )
                    label = _identifier(cited.get("label"), "source-truth citation label")
                    path = _text(cited.get("path"), "source-truth citation path", minimum=3)
                    if path.startswith("/") or ".." in path.split("/"):
                        raise EvidenceError("source-truth citation path must be repository-relative")
                    line_start = _count(cited.get("line_start"), "citation line_start")
                    line_end = _count(cited.get("line_end"), "citation line_end")
                    if line_start < 1 or line_end < line_start:
                        raise EvidenceError("source-truth citation line range is invalid")
                    excerpt = _text(cited.get("excerpt"), "source-truth citation excerpt")
                    if cited.get("excerpt_digest") != raw_digest(excerpt):
                        raise EvidenceError("source-truth citation excerpt digest is invalid")
                    labels.add(label)
                if len(labels) != len(citations):
                    raise EvidenceError("source-truth citation labels must be unique")
                source_citation_labels[record_id] = labels
                covered.add(record_id)
            if covered != question_ids:
                raise EvidenceError("source-truth records do not exactly cover the questions")
        elif kind == "world-model-cognition":
            value = _payload_object(
                attachment,
                {"schema", "records"},
                "ITER010_WORLD_MODEL_COGNITION_RECORD@1",
            )
            records = value.get("records")
            if type(records) is not list or len(records) != len(question_ids):
                raise EvidenceError("world-model record must cover every question")
            covered: set[str] = set()
            contributions = 0
            for record in records:
                item = _object(record, "world-model record")
                _exact_keys(
                    item,
                    {"question_id", "cognition_summary", "non_locator_contribution"},
                    "world-model record",
                )
                record_id = _identifier(item.get("question_id"), "world-model question_id")
                _text(item.get("cognition_summary"), "world-model cognition_summary")
                if type(item.get("non_locator_contribution")) is not bool:
                    raise EvidenceError("non_locator_contribution must be boolean")
                contributions += int(item["non_locator_contribution"])
                covered.add(record_id)
            if covered != question_ids:
                raise EvidenceError("world-model records do not exactly cover the questions")
            world_model_contributions = contributions
            if outcome == "QUALITY_PASS" and contributions < 1:
                raise EvidenceError("declared quality pass needs a non-locator contribution")
        elif kind in PER_QUESTION_ARTIFACT_KINDS:
            assert isinstance(question_id, str)
            common = {"schema", "question_id", "question_text"}
            if kind == "system-answer":
                value = _payload_object(
                    attachment,
                    common | {"answer_text", "citation_labels"},
                    "ITER010_SYSTEM_ANSWER_RECORD@1",
                )
                _text(value.get("answer_text"), "system answer_text")
                answer_citation_labels[question_id] = set(
                    _string_list(value.get("citation_labels"), "system citation_labels")
                )
            elif kind == "current-codex-answer":
                value = _payload_object(
                    attachment,
                    common | {"answer_text", "client_identity"},
                    "ITER010_CURRENT_CODEX_ANSWER_RECORD@1",
                )
                _text(value.get("answer_text"), "Codex answer_text")
                _text(value.get("client_identity"), "Codex client_identity")
            elif kind == "independent-review":
                value = _payload_object(
                    attachment,
                    common
                    | {
                        "review_text", "major_error_count", "material_omission_count",
                        "unsupported_citation_count", "fresh_context",
                    },
                    "ITER010_INDEPENDENT_REVIEW_RECORD@1",
                )
                _text(value.get("review_text"), "review_text")
                for field in (
                    "major_error_count", "material_omission_count",
                    "unsupported_citation_count",
                ):
                    review_totals[field] += _count(value.get(field), field)
                if value.get("fresh_context") is not True:
                    raise EvidenceError("independent review must record fresh context")
            else:
                value = _payload_object(
                    attachment,
                    common
                    | {
                        "evaluation_text", "system_score", "codex_score",
                        "material_regression", "blinded",
                    },
                    "ITER010_QUESTION_COMPARISON_RECORD@1",
                )
                _text(value.get("evaluation_text"), "comparison evaluation_text")
                comparison_totals["system_total_score"] += _count(
                    value.get("system_score"), "system_score"
                )
                comparison_totals["codex_total_score"] += _count(
                    value.get("codex_score"), "codex_score"
                )
                if type(value.get("material_regression")) is not bool:
                    raise EvidenceError("material_regression must be boolean")
                if (
                    value["system_score"] < value["codex_score"]
                    and value["material_regression"] is not True
                ):
                    raise EvidenceError("a lower per-question system score must record regression")
                if outcome == "QUALITY_PASS" and (
                    value["system_score"] < value["codex_score"]
                    or value["material_regression"] is not False
                ):
                    raise EvidenceError("quality pass requires no per-question score regression")
                comparison_totals["material_regression_count"] += int(
                    value["material_regression"]
                )
                if value.get("blinded") is not True:
                    raise EvidenceError("question comparison must record blinded evaluation")
            if value.get("question_id") != question_id:
                raise EvidenceError("attachment payload question identity is invalid")
            question_text = _text(value.get("question_text"), "question_text")
            previous_text = question_texts.setdefault(question_id, question_text)
            if previous_text != question_text:
                raise EvidenceError("per-question records must bind the same question text")
            per_question_seen[question_id].add(kind)
        elif kind == "comparison-summary":
            value = _payload_object(
                attachment,
                {
                    "schema", "question_ids", "declared_quality_outcome",
                    "major_error_count", "material_regression_count",
                    "material_omission_count", "unsupported_citation_count",
                    "system_total_score", "codex_total_score",
                    "non_locator_world_model_contribution_count", "assessment_text",
                },
                "ITER010_COMPARISON_SUMMARY_RECORD@1",
            )
            if set(_string_list(value.get("question_ids"), "comparison question_ids")) != question_ids:
                raise EvidenceError("comparison summary does not cover every question")
            if value.get("declared_quality_outcome") != outcome:
                raise EvidenceError("comparison summary outcome is inconsistent")
            for field in (
                "major_error_count", "material_regression_count", "system_total_score",
                "codex_total_score", "non_locator_world_model_contribution_count",
            ):
                _count(value.get(field), field)
            _text(value.get("assessment_text"), "comparison assessment_text")
            comparison_summary = value
        elif kind == "failure-analysis":
            value = _payload_object(
                attachment,
                {"schema", "earliest_layer", "falsifiable_hypothesis", "general_repair"},
                "ITER010_FAILURE_ANALYSIS_RECORD@1",
            )
            for field in ("earliest_layer", "falsifiable_hypothesis", "general_repair"):
                _text(value.get(field), field)
        elif kind == "general-repair-rechecks":
            value = _payload_object(
                attachment,
                {
                    "schema", "original_question_id", "heterogeneous_recheck_question_ids",
                    "same_material_failure_reproduced",
                },
                "ITER010_GENERAL_REPAIR_RECHECK_RECORD@1",
            )
            if value.get("original_question_id") not in question_ids:
                raise EvidenceError("failure recheck original question is invalid")
            rechecks = set(
                _string_list(
                    value.get("heterogeneous_recheck_question_ids"),
                    "heterogeneous_recheck_question_ids",
                    minimum=2,
                )
            )
            if not rechecks.issubset(question_ids - {str(value["original_question_id"])}):
                raise EvidenceError("failure rechecks must use other registered questions")
            if value.get("same_material_failure_reproduced") is not True:
                raise EvidenceError("failure handoff must record the repeated material failure")
    if any(kinds != PER_QUESTION_ARTIFACT_KINDS for kinds in per_question_seen.values()):
        raise EvidenceError("every question must include answer, Codex, review, and comparison records")
    if set(source_citation_labels) != question_ids or set(answer_citation_labels) != question_ids:
        raise EvidenceError("source and answer citations must cover every question")
    for question_id in question_ids:
        if not answer_citation_labels[question_id].issubset(
            source_citation_labels[question_id]
        ):
            raise EvidenceError("answer citation labels must resolve to source-truth citations")
    if browser_binding is None or comparison_summary is None:
        raise EvidenceError("browser and comparison summary records are required")
    expected_summary = {
        **review_totals,
        **comparison_totals,
        "non_locator_world_model_contribution_count": world_model_contributions,
    }
    for field, expected in expected_summary.items():
        if comparison_summary.get(field) != expected:
            raise EvidenceError(f"comparison summary {field} must be derived from per-question records")
    if outcome == "QUALITY_PASS" and not (
        review_totals["major_error_count"] == 0
        and review_totals["material_omission_count"] == 0
        and review_totals["unsupported_citation_count"] == 0
        and comparison_totals["material_regression_count"] == 0
        and comparison_totals["system_total_score"]
        > comparison_totals["codex_total_score"]
        and world_model_contributions > 0
    ):
        raise EvidenceError("declared quality pass does not meet the derived strict threshold")
    return browser_binding


def _validate_runtime_receipts(
    value: Any,
    authority_digest: str,
    candidate_commit: str,
    question_ids: set[str],
    browser_binding: Mapping[str, Any],
    counters: Mapping[str, int],
) -> None:
    if type(value) is not list or not value:
        raise EvidenceError("runtime_receipts must contain executed dispatch receipts")
    totals = {field: 0 for field in COUNTER_KEYS}
    receipt_ids: set[str] = set()
    receipt_turn_ids: set[str] = set()
    for index, raw in enumerate(value):
        receipt = _object(raw, f"runtime_receipts[{index}]")
        _exact_keys(receipt, RUNTIME_RECEIPT_KEYS, f"runtime_receipts[{index}]")
        receipt_id = _identifier(
            receipt.get("receipt_id"), f"runtime_receipts[{index}].receipt_id"
        )
        if receipt_id in receipt_ids:
            raise EvidenceError("runtime receipt IDs must be unique")
        receipt_ids.add(receipt_id)
        if receipt.get("parent_authority_binding_digest") != authority_digest:
            raise EvidenceError("runtime receipt is not bound to the standing authority")
        if receipt.get("candidate_commit") != candidate_commit:
            raise EvidenceError("runtime receipt candidate commit is invalid")
        if receipt.get("source_commit") != STANDING_SCOPE_VALUES["source_commit"]:
            raise EvidenceError("runtime receipt source commit is invalid")
        if receipt.get("source_tree") != STANDING_SCOPE_VALUES["source_tree"]:
            raise EvidenceError("runtime receipt source tree is invalid")
        if receipt.get("browser_url") != LOOPBACK_BROWSER_URL:
            raise EvidenceError("runtime receipt browser URL is invalid")
        session_id = _identifier(
            receipt.get("session_id"), f"runtime_receipts[{index}].session_id"
        )
        conversation_id = _identifier(
            receipt.get("conversation_id"),
            f"runtime_receipts[{index}].conversation_id",
        )
        turn_id = _identifier(
            receipt.get("turn_id"), f"runtime_receipts[{index}].turn_id"
        )
        role = receipt.get("role")
        if role not in {"question-understanding", "investigation", "answer", "review"}:
            raise EvidenceError("runtime receipt role is not registered")
        if (
            session_id != browser_binding.get("session_id")
            or conversation_id not in browser_binding.get("conversation_ids", set())
            or turn_id not in browser_binding.get("turn_ids", set())
        ):
            raise EvidenceError("runtime receipt is not bound to the browser session/turn")
        receipt_turn_ids.add(turn_id)
        route_role = receipt.get("route_role")
        if route_role not in EXECUTION_PROFILES:
            raise EvidenceError("runtime receipt route role is invalid")
        configuration = _object(
            receipt.get("provider_configuration"), "provider_configuration"
        )
        _exact_keys(
            configuration, PROVIDER_CONFIGURATION_KEYS, "provider_configuration"
        )
        expected_configuration = EXECUTION_PROFILES[str(route_role)]
        if configuration != expected_configuration:
            raise EvidenceError("runtime receipt provider configuration is not frozen")
        if receipt.get("provider_configuration_digest") != canonical_digest(configuration):
            raise EvidenceError("provider_configuration_digest is invalid")

        input_payload = receipt.get("input_payload")
        if type(input_payload) is not str or not input_payload.strip():
            raise EvidenceError("runtime receipt must embed its exact input payload")
        input_digest = raw_digest(input_payload)
        if receipt.get("input_digest") != input_digest:
            raise EvidenceError("runtime receipt input_digest is invalid")
        try:
            input_record = load_raw_evidence(input_payload.encode("utf-8"))
        except EvidenceError as exc:
            raise EvidenceError("runtime input_payload must use its closed JSON schema") from exc
        _exact_keys(
            input_record,
            {
                "schema", "session_id", "conversation_id", "turn_id", "role",
                "question_id", "content",
            },
            "runtime input_payload",
        )
        if input_record.get("schema") != "ITER010_RUNTIME_INPUT@1":
            raise EvidenceError("runtime input schema is invalid")
        expected_input_bindings = {
            "session_id": session_id,
            "conversation_id": conversation_id,
            "turn_id": turn_id,
            "role": role,
        }
        for field, expected in expected_input_bindings.items():
            if input_record.get(field) != expected:
                raise EvidenceError(f"runtime input {field} is not bound to its receipt")
        if input_record.get("question_id") not in question_ids:
            raise EvidenceError("runtime input question_id is not registered")
        _text(input_record.get("content"), "runtime input content")

        disclosure = _object(receipt.get("disclosure"), "disclosure")
        _exact_keys(disclosure, DISCLOSURE_KEYS, "disclosure")
        if disclosure != {
            "schema": "ITER010_PUBLIC_SOURCE_DISCLOSURE@1",
            "public_source_only": True,
            "secret_values_included": False,
            "source_origin": STANDING_SCOPE_VALUES["source_origin"],
            "source_commit": STANDING_SCOPE_VALUES["source_commit"],
            "input_payload_digest": input_digest,
        }:
            raise EvidenceError("runtime receipt disclosure is outside standing scope")
        if receipt.get("disclosure_digest") != canonical_digest(disclosure):
            raise EvidenceError("disclosure_digest is invalid")

        budget = _object(receipt.get("budget"), "budget")
        _exact_keys(budget, BUDGET_KEYS, "budget")
        maximum_calls = _count(budget.get("maximum_calls"), "budget.maximum_calls")
        maximum_input = _count(
            budget.get("maximum_input_tokens"), "budget.maximum_input_tokens"
        )
        maximum_output = _count(
            budget.get("maximum_output_tokens"), "budget.maximum_output_tokens"
        )
        timeout = _count(
            budget.get("timeout_milliseconds"), "budget.timeout_milliseconds"
        )
        if (
            maximum_calls != 1
            or not 1 <= maximum_input <= 200_000
            or not 1 <= maximum_output <= 64_000
            or not 1 <= timeout <= 900_000
        ):
            raise EvidenceError("runtime receipt budget exceeds the frozen per-dispatch bounds")
        if receipt.get("budget_digest") != canonical_digest(budget):
            raise EvidenceError("budget_digest is invalid")
        if receipt.get("one_use") is not True or receipt.get("consumed") is not True:
            raise EvidenceError("runtime receipt must be one-use and consumed")
        if receipt.get("expired") is not False:
            raise EvidenceError("runtime receipt must not expire before consumption")
        for field in (
            "external_model_call_count", "provider_dispatch_count",
            "credential_resolution_count", "tls_attempt_count", "http_dispatch_count",
        ):
            count = _count(receipt.get(field), f"runtime_receipts[{index}].{field}")
            if field in {
                "external_model_call_count", "provider_dispatch_count",
                "http_dispatch_count",
            } and count != 1:
                raise EvidenceError("each receipt must bind exactly one dispatch")
            if field in {"credential_resolution_count", "tls_attempt_count"} and count > 1:
                raise EvidenceError("credential/TLS counts must be zero or one")
            totals[field] += count
        receipt_body = {
            key: item for key, item in receipt.items() if key != "receipt_digest"
        }
        if receipt.get("receipt_digest") != canonical_digest(receipt_body):
            raise EvidenceError("runtime receipt digest is invalid")
    totals["full_regression_run_count"] = 0
    if not set(browser_binding.get("turn_ids", set())).issubset(receipt_turn_ids):
        raise EvidenceError("every browser semantic turn must have an exact dispatch receipt")
    if dict(counters) != totals:
        raise EvidenceError("execution counters do not reconcile with receipts")


def _validate_experience(
    value: Any, verdict: str, counters: Mapping[str, int]
) -> None:
    experience = _object(value, "action_evidence")
    _exact_keys(experience, EXPERIENCE_KEYS, "action_evidence")
    if experience.get("schema") != "ITER010_MVP_HANDOFF_PACKET@2":
        raise EvidenceError("experience handoff schema is invalid")
    candidate_commit, _ = _validate_candidate(experience.get("candidate_identity"))
    authority_digest = _validate_standing_scope(experience.get("standing_scope"))
    if experience.get("browser_url") != LOOPBACK_BROWSER_URL:
        raise EvidenceError("experience browser URL must be the fixed loopback URL")
    outcome = experience.get("handoff_outcome")
    if outcome not in {"QUALITY_PASS", "QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR"}:
        raise EvidenceError("handoff outcome is invalid")
    if verdict != "PASS":
        raise EvidenceError("plan PASS means the user handoff packet is complete, not quality PASS")
    attestation = _object(
        experience.get("machine_attestation"), "machine_attestation"
    )
    if attestation != MACHINE_ATTESTATION or any(
        type(attestation.get(key)) is not type(expected)
        for key, expected in MACHINE_ATTESTATION.items()
    ):
        raise EvidenceError("machine_attestation must preserve its narrow boundary")

    attachments = _validate_attachments(experience.get("attachments"))
    referenced, question_ids = _validate_questions(
        experience.get("questions"), attachments
    )
    browser_binding = _validate_attachment_payloads(
        attachments, question_ids, candidate_commit, str(outcome)
    )
    required_global_ids: set[str] = set()
    for kind in GLOBAL_ARTIFACT_KINDS:
        matches = [item for item in attachments.values() if item.get("kind") == kind]
        if len(matches) != 1:
            raise EvidenceError(f"exactly one embedded {kind} attachment is required")
        required_global_ids.add(str(matches[0]["artifact_id"]))
    required_failure_ids: set[str] = set()
    for kind in FAILURE_ARTIFACT_KINDS:
        matches = [item for item in attachments.values() if item.get("kind") == kind]
        required_count = 1 if outcome == "QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR" else 0
        if len(matches) != required_count:
            raise EvidenceError(f"{kind} attachment count is invalid")
        required_failure_ids.update(str(item["artifact_id"]) for item in matches)
    if set(attachments) != referenced | required_global_ids | required_failure_ids:
        raise EvidenceError("attachments must be exactly the records used by the handoff")

    parsed_counters = {
        field: _count(counters.get(field), f"execution_counters.{field}")
        for field in COUNTER_KEYS
    }
    if parsed_counters["full_regression_run_count"] != 0:
        raise EvidenceError("the experience handoff must not run full regression")
    _validate_runtime_receipts(
        experience.get("runtime_receipts"),
        authority_digest,
        candidate_commit,
        question_ids,
        browser_binding,
        parsed_counters,
    )


def _validate_user_direction(
    value: Any, verdict: str, counters: Mapping[str, int]
) -> None:
    record = _object(value, "action_evidence")
    _exact_keys(record, USER_DIRECTION_KEYS, "action_evidence")
    if record.get("schema") != "ITER010_USER_DIRECTION_RECORD@2":
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
    ):
        raise EvidenceError("a local digest cannot claim platform authentication")
    if record.get("known_limitations_acknowledged") is not True:
        raise EvidenceError("user direction must acknowledge known limitations")
    if record.get("unlocks_followup_work") is not False:
        raise EvidenceError("a direction record cannot authorize follow-up work")
    if record.get("followup_plan_revision_and_explicit_authorization_required") is not True:
        raise EvidenceError("follow-up requires a new plan and explicit authorization")
    if verdict != "PASS" or any(counters.values()):
        raise EvidenceError("user direction records PASS with zero execution counters")


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
        raise EvidenceError("PASS means only that the user handoff record is structurally complete")
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
    parsed_counters = {
        field: _count(counters.get(field), field) for field in COUNTER_KEYS
    }
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
        raise EvidenceError("execution_input_digest does not bind the handoff subject")
    if role == "experience":
        _validate_experience(action_evidence, str(verdict), parsed_counters)
    else:
        _validate_user_direction(action_evidence, str(verdict), parsed_counters)

    receipt = _object(artifact.get("runner_receipt"), "runner_receipt")
    _exact_keys(receipt, RUNNER_RECEIPT_KEYS, "runner_receipt")
    if receipt.get("runner_id") != EVIDENCE_VERIFIER:
        raise EvidenceError("runner receipt ID is invalid")
    if receipt.get("runner_identity_digest") != artifact.get("runner_identity_digest"):
        raise EvidenceError("runner identity is not consistently bound")
    if receipt.get("execution_input_digest") != artifact.get("execution_input_digest"):
        raise EvidenceError("runner execution input is not consistently bound")
    if receipt.get("exit_code") != 0 or receipt.get("completed") is not True:
        raise EvidenceError("runner receipt must be completed with zero exit")
    if artifact.get("runner_receipt_digest") != canonical_digest(receipt):
        raise EvidenceError("runner receipt digest is invalid")

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
    evidence_ref = outcome.get("evidence_ref")
    if type(evidence_ref) is not str or not evidence_ref.strip():
        raise EvidenceError("case outcome evidence_ref must be non-empty")
    if outcome.get("evidence_digest") != artifact.get("subject_digest"):
        raise EvidenceError("case outcome does not bind action_evidence")
    if artifact.get("verification_report_digest") != canonical_digest(outcomes):
        raise EvidenceError("verification report digest is invalid")

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
