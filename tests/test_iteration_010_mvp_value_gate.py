from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from validation.iteration_010_mvp.value_gate import runner


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "validation/iteration_010_mvp/value_gate/runner.py"
DIGEST = "sha256:" + "a" * 64
ORIGINAL = "请解释后台登录调用链、密码校验、JWT 生成和登录日志写入。"
PURPOSE = "请说明后台管理员商品列表入口并比较 portal 商品查询的职责边界。"
AUTHORIZATION = "请区分后台接口未登录与权限不足的认证授权路径和未知边界。"


def _identity(tree: str = "b" * 40) -> dict[str, str]:
    raw = (
        f"tree {tree}\n"
        "author Test <test@example.com> 0 +0000\n"
        "committer Test <test@example.com> 0 +0000\n\n"
        "frozen parent\n"
    )
    encoded = raw.encode("utf-8")
    commit = hashlib.sha1(
        b"commit " + str(len(encoded)).encode("ascii") + b"\0" + encoded
    ).hexdigest()
    return {
        "commit": commit,
        "tree": tree,
        "raw_commit": raw,
        "raw_commit_digest": runner.raw_digest(raw),
    }


def _product_identity() -> dict[str, str]:
    return {
        "commit": runner.PRODUCT_CANDIDATE_COMMIT,
        "tree": runner.PRODUCT_CANDIDATE_TREE,
        "raw_commit": runner.PRODUCT_CANDIDATE_RAW_COMMIT,
        "raw_commit_digest": runner.raw_digest(runner.PRODUCT_CANDIDATE_RAW_COMMIT),
    }


def _standing_scope() -> dict[str, object]:
    value = copy.deepcopy(runner.STANDING_SCOPE_VALUES)
    value["binding_digest"] = runner.canonical_digest(runner.STANDING_SCOPE_VALUES)
    return value


def _transport(count: int) -> dict[str, object]:
    return {
        "credential_resolution_count": count,
        "credential_resolution_success_count": count,
        "tls_handshake_attempt_count": count,
        "tls_handshake_success_count": count,
        "http_dispatch_count": count,
        "request_retry_count": 0,
        "pre_dispatch_tls_handshake_failure_count": 0,
        "post_dispatch_outcome_unknown_count": 0,
        "pre_dispatch_tls_failure_codes": [],
        "post_dispatch_failure_codes": [],
    }


def _fallback_transport() -> dict[str, object]:
    return {
        "credential_resolution_count": 0,
        "tls_handshake_attempt_count": 0,
        "http_dispatch_count": 0,
        "request_retry_count": 0,
        "pre_dispatch_tls_handshake_failure_count": 0,
        "post_dispatch_outcome_unknown_count": 0,
    }


def _terminal(count: int, suffix: str) -> str:
    return json.dumps(
        {
            "schema": "SWM-ENGINEERING-CHAT-ARTIFACT-TERMINAL-RECEIPT@2",
            "status": "STOPPED_AFTER_DISPATCH",
            "digest": "sha256:" + suffix * 64,
            "provider_dispatch_count": count,
            "request_retry_count": 0,
            "human_approval_request_count": 0,
            "production_activation": "NOT_EXECUTED",
            "provider_audits": [
                {
                    "provider_type": "VOLCENGINE_ARK",
                    "provider_dispatch_count": count,
                    "request_retry_count": 0,
                    "model_call_receipt_digests": [DIGEST] * count,
                    "model_dispatch_audit_digests": [DIGEST] * count,
                    "transport_session_audit": _transport(count),
                },
                {
                    "provider_type": "DEEPSEEK",
                    "provider_dispatch_count": 0,
                    "request_retry_count": 0,
                    "model_call_receipt_digests": [],
                    "model_dispatch_audit_digests": [],
                    "transport_session_audit": _fallback_transport(),
                },
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _turn_scope(session: str, messages: list[str]) -> str:
    return json.dumps(
        {
            "schema": "ITER-010-MVP-EXPERIENCE-TURN-SCOPE@1",
            "product_commit": runner.PRODUCT_CANDIDATE_COMMIT,
            "product_tree": runner.PRODUCT_CANDIDATE_TREE,
            "session_ref": session,
            "interactions": [
                {"ordinal": index, "message": message}
                for index, message in enumerate(messages, start=1)
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _browser(count: int, terminal_digest: str) -> str:
    return json.dumps(
        {
            "schema": "ITER-010-MVP-BROWSER-CAPTURE@1",
            "candidate_commit": runner.PRODUCT_CANDIDATE_COMMIT,
            "candidate_tree": runner.PRODUCT_CANDIDATE_TREE,
            "browser_url": runner.LOOPBACK_BROWSER_URL,
            "local_capture_authenticity_machine_verified": False,
            "new_conversation_isolation_observed": True,
            "conversations": [
                {
                    "conversation_id": "conversation-purpose",
                    "turns": [
                        {
                            "turn_id": "turn-purpose",
                            "user_message": PURPOSE,
                            "status": "FAILED",
                            "result_kind": "AGENT_MODEL_CALL_REJECTED",
                            "provider_dispatch_count": 2,
                        }
                    ],
                },
                {
                    "conversation_id": "conversation-authorization",
                    "turns": [
                        {
                            "turn_id": "turn-authorization",
                            "user_message": AUTHORIZATION,
                            "status": "FAILED",
                            "result_kind": "AGENT_MODEL_CALL_REJECTED",
                            "provider_dispatch_count": 2,
                        }
                    ],
                },
            ],
            "ark_provider_dispatch_count": count,
            "ark_credential_resolution_count": count,
            "ark_tls_attempt_count": count,
            "ark_tls_success_count": count,
            "ark_http_dispatch_count": count,
            "deepseek_provider_dispatch_count": 0,
            "deepseek_credential_resolution_count": 0,
            "deepseek_tls_attempt_count": 0,
            "deepseek_http_dispatch_count": 0,
            "request_retry_count": 0,
            "human_approval_request_count": 0,
            "production_activation": "NOT_EXECUTED",
            "terminal_receipt_digest": terminal_digest,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _gateway_call(call_id: str) -> tuple[dict[str, object], str]:
    output = f"raw model proposal output for {call_id}"
    return (
        {
            "model_call_id": call_id,
            "current_state": "COMPLETED",
            "provider_type": "VOLCENGINE_ARK",
            "requested_model_ref": "glm-5-2-260617",
            "failure_code": "STRUCTURED_OUTPUT_INVALID",
            "actual_model_fingerprint": "glm-5.2",
            "output_digest": runner.raw_digest(output),
            "termination_reason": "stop",
            "output_normalization": "IDENTITY",
        },
        output,
    )


def _capture(
    session: str,
    call_ids: list[str],
    messages: list[str],
    *,
    browser: bool,
    suffix: str,
) -> tuple[dict[str, object], dict[str, str]]:
    terminal = _terminal(len(call_ids), suffix)
    terminal_value = json.loads(terminal)
    calls: list[dict[str, object]] = []
    outputs: dict[str, str] = {}
    for call_id in call_ids:
        call, output = _gateway_call(call_id)
        calls.append(call)
        outputs[call_id] = output
    browser_payload = (
        _browser(len(call_ids), str(terminal_value["digest"])) if browser else None
    )
    turn_scope = _turn_scope(session, messages)
    return (
        {
            "artifact_session_ref": session,
            "product_commit": runner.PRODUCT_CANDIDATE_COMMIT,
            "product_tree": runner.PRODUCT_CANDIDATE_TREE,
            "turn_scope_payload": turn_scope,
            "turn_scope_payload_digest": runner.raw_digest(turn_scope),
            "terminal_payload": terminal,
            "terminal_payload_digest": runner.raw_digest(terminal),
            "browser_capture_payload": browser_payload,
            "browser_capture_payload_digest": (
                runner.raw_digest(browser_payload) if browser_payload is not None else None
            ),
            "ark_gateway_database_digest": DIGEST,
            "deepseek_gateway_database_digest": DIGEST,
            "gateway_calls": calls,
        },
        outputs,
    )


def _failure(
    failure_id: str,
    position: str,
    category: str,
    session: str,
    question: str,
    initial: str,
    repair: str,
    outputs: dict[str, str],
    *,
    turn_id: str | None,
) -> dict[str, object]:
    return {
        "failure_id": failure_id,
        "position": position,
        "category": category,
        "unseen_during_repair": position == "HETEROGENEOUS_RECHECK",
        "artifact_session_ref": session,
        "conversation_locator": f"{session}:conversation",
        "turn_id": turn_id,
        "question_text": question,
        "initial_model_call_id": initial,
        "initial_model_output": outputs[initial],
        "initial_model_output_digest": runner.raw_digest(outputs[initial]),
        "repair_model_call_id": repair,
        "repair_model_output": outputs[repair],
        "repair_model_output_digest": runner.raw_digest(outputs[repair]),
        "failure_signature": "PRE_ANSWER_AGENT_MODEL_CALL_REJECTED",
        "failure_detail": "Initial and fresh same-profile repair outputs failed the closed contract.",
        "raw_model_outputs_are_authorized_answers": False,
        "answer_emitted": False,
        "citation_count": 0,
        "review_emitted": False,
        "current_codex_comparison_performed": False,
    }


def _experience() -> dict[str, object]:
    capture_1, outputs_1 = _capture(
        "iteration-010-mvp-experience-run-052",
        ["model-call-original", "model-call-original-repair"],
        [ORIGINAL],
        browser=False,
        suffix="b",
    )
    capture_2, outputs_2 = _capture(
        "iteration-010-mvp-experience-run-053",
        ["model-call-purpose", "model-call-purpose-repair", "model-call-auth", "model-call-auth-repair"],
        [PURPOSE, AUTHORIZATION],
        browser=True,
        suffix="c",
    )
    total = 6
    return {
        "schema": "ITER010_MVP_FAILURE_HANDOFF_PACKET@3",
        "handoff_parent_identity": _identity(),
        "product_candidate_identity": _product_identity(),
        "standing_scope": _standing_scope(),
        "browser_url": runner.LOOPBACK_BROWSER_URL,
        "handoff_outcome": "QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR",
        "recovery_authorization_ref": runner.RECOVERY_AUTHORIZATION_REF,
        "machine_attestation": copy.deepcopy(runner.MACHINE_ATTESTATION),
        "repair_record": {
            "schema": "ITER010_GENERAL_REPAIR_RECORD@1",
            "repair_commit": runner.PRODUCT_CANDIDATE_COMMIT,
            "root_cause": "Structured model output was incorrectly classified as provider unavailability.",
            "general_repair": "Preserve provider qualification and run one fresh same-profile format repair.",
            "product_repair_count": 1,
            "same_material_pre_answer_failure_reproduced": True,
            "product_repair_stopped": True,
        },
        "capture_sets": [capture_1, capture_2],
        "failure_turns": [
            _failure(
                "original-login", "ORIGINAL", "BEHAVIOR_CALL_FLOW_OR_SIDE_EFFECT",
                "iteration-010-mvp-experience-run-052", ORIGINAL,
                "model-call-original", "model-call-original-repair", outputs_1,
                turn_id=None,
            ),
            _failure(
                "recheck-purpose", "HETEROGENEOUS_RECHECK", "SYSTEM_PURPOSE_OR_ENTRY",
                "iteration-010-mvp-experience-run-053", PURPOSE,
                "model-call-purpose", "model-call-purpose-repair", outputs_2,
                turn_id="turn-purpose",
            ),
            _failure(
                "recheck-authorization", "HETEROGENEOUS_RECHECK", "FAILURE_AUTHORIZATION_OR_UNKNOWN",
                "iteration-010-mvp-experience-run-053", AUTHORIZATION,
                "model-call-auth", "model-call-auth-repair", outputs_2,
                turn_id="turn-authorization",
            ),
        ],
        "execution_reconciliation": {
            "artifact_session_count": 2,
            "ark_external_model_call_count": total,
            "ark_provider_dispatch_count": total,
            "ark_credential_resolution_count": total,
            "ark_tls_attempt_count": total,
            "ark_http_dispatch_count": total,
            "deepseek_external_model_call_count": 0,
            "deepseek_provider_dispatch_count": 0,
            "deepseek_credential_resolution_count": 0,
            "deepseek_tls_attempt_count": 0,
            "deepseek_http_dispatch_count": 0,
            "request_retry_count": 0,
            "human_approval_request_count": 0,
            "full_regression_run_count": 0,
        },
    }


def _seal(action_evidence: dict[str, object], *, direction: bool = False) -> dict[str, object]:
    action = runner.USER_DIRECTION_ACTION if direction else runner.EXPERIENCE_ACTION
    case = runner.USER_DIRECTION_CASE if direction else runner.EXPERIENCE_CASE
    result = runner.USER_DIRECTION_RESULT if direction else runner.EXPERIENCE_RESULT
    path = runner.USER_DIRECTION_PATH if direction else runner.EXPERIENCE_PATH
    count = 0 if direction else int(
        action_evidence["execution_reconciliation"]["ark_external_model_call_count"]  # type: ignore[index]
    )
    counters = {
        "external_model_call_count": count,
        "provider_dispatch_count": count,
        "credential_resolution_count": count,
        "tls_attempt_count": count,
        "http_dispatch_count": count,
        "full_regression_run_count": 0,
    }
    subject = runner.canonical_digest(action_evidence)
    execution_input = runner.canonical_digest(
        {
            "plan_revision_ref": runner.PLAN_REVISION,
            "action_ref": action,
            "verification_case_id": case,
            "subject_digest": subject,
        }
    )
    receipt = {
        "runner_id": runner.EVIDENCE_VERIFIER,
        "runner_identity_digest": DIGEST,
        "execution_input_digest": execution_input,
        "exit_code": 0,
        "completed": True,
    }
    outcomes = [
        {
            "case_id": case,
            "verdict": "PASS",
            "evidence_ref": f"{path}#action_evidence",
            "evidence_digest": subject,
        }
    ]
    return {
        "schema": runner.EVIDENCE_SCHEMA,
        "result_id": result,
        "plan_revision_ref": runner.PLAN_REVISION,
        "action_ref": action,
        "verification_case_id": case,
        "plan_gate_verdict": "PASS",
        "evidence_verifier": runner.EVIDENCE_VERIFIER,
        "evidence_artifact_path": path,
        "execution_input_digest": execution_input,
        "runner_identity_digest": DIGEST,
        "runner_receipt_digest": runner.canonical_digest(receipt),
        "verification_report_digest": runner.canonical_digest(outcomes),
        "subject_digest": subject,
        "action_evidence": action_evidence,
        "execution_counters": counters,
        "runner_receipt": receipt,
        "case_outcomes": outcomes,
    }


class Iter010MvpValueGateTests(unittest.TestCase):
    def test_truthful_multi_session_failure_handoff_passes(self) -> None:
        live = runner.validate_evidence(_seal(_experience()))
        self.assertEqual(live["plan_gate_verdict"], "PASS")
        self.assertEqual(live["external_model_call_count"], 6)

    def test_cli_emits_only_live_verifier_fields(self) -> None:
        artifact = _seal(_experience())
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "verify-plan-evidence"],
            input=runner.canonical_json_bytes(artifact),
            stdout=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(set(json.loads(completed.stdout)), runner.LIVE_FIELDS)

    def test_failure_turn_cannot_claim_an_answer(self) -> None:
        artifact = _seal(_experience())
        artifact["action_evidence"]["failure_turns"][0]["answer_emitted"] = True  # type: ignore[index]
        artifact = _seal(artifact["action_evidence"])  # type: ignore[arg-type]
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_failure_packet_rejects_answer_attachment_field(self) -> None:
        experience = _experience()
        experience["system_answers"] = []
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(_seal(experience))

    def test_failure_requires_all_three_categories(self) -> None:
        experience = _experience()
        experience["failure_turns"][2]["category"] = "SYSTEM_PURPOSE_OR_ENTRY"  # type: ignore[index]
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(_seal(experience))

    def test_failure_requires_multiple_artifact_sessions(self) -> None:
        experience = _experience()
        experience["failure_turns"][0]["artifact_session_ref"] = "iteration-010-mvp-experience-run-053"  # type: ignore[index]
        experience["failure_turns"][0]["question_text"] = PURPOSE  # type: ignore[index]
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(_seal(experience))

    def test_failure_call_output_must_bind_gateway_digest(self) -> None:
        experience = _experience()
        experience["failure_turns"][0]["initial_model_output"] += " tampered"  # type: ignore[index,operator]
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(_seal(experience))

    def test_deepseek_dispatch_is_rejected(self) -> None:
        experience = _experience()
        terminal = json.loads(experience["capture_sets"][0]["terminal_payload"])  # type: ignore[index]
        terminal["provider_audits"][1]["provider_dispatch_count"] = 1
        raw = json.dumps(terminal, ensure_ascii=False, sort_keys=True)
        experience["capture_sets"][0]["terminal_payload"] = raw  # type: ignore[index]
        experience["capture_sets"][0]["terminal_payload_digest"] = runner.raw_digest(raw)  # type: ignore[index]
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(_seal(experience))

    def test_product_candidate_is_exact(self) -> None:
        experience = _experience()
        experience["product_candidate_identity"] = _identity()
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(_seal(experience))

    def test_non_pass_envelope_is_rejected(self) -> None:
        artifact = _seal(_experience())
        artifact["plan_gate_verdict"] = "FAIL"
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_user_direction_remains_zero_execution_pass(self) -> None:
        evidence = "CONTINUE after inspecting the failed handoff"
        record = {
            "schema": "ITER010_USER_DIRECTION_RECORD@3",
            "decision": "CONTINUE",
            "decision_ref": "local-user-message-utf8:sha256:" + "d" * 64,
            "decision_evidence": evidence,
            "decision_evidence_digest": runner.raw_digest(evidence),
            "local_record_only": True,
            "platform_authenticated": False,
            "known_limitations_acknowledged": True,
            "unlocks_followup_work": False,
            "followup_plan_revision_and_explicit_authorization_required": True,
        }
        live = runner.validate_evidence(_seal(record, direction=True))
        self.assertEqual(live["external_model_call_count"], 0)


if __name__ == "__main__":
    unittest.main()
