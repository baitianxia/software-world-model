from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

from validation.iteration_010_mvp.value_gate import runner


DIGEST = "sha256:" + "a" * 64
ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "validation/iteration_010_mvp/value_gate/runner.py"


def _attachment(
    artifact_id: str,
    kind: str,
    *,
    question_id: str | None = None,
    payload: str,
) -> dict[str, object]:
    return {
        "artifact_id": artifact_id,
        "kind": kind,
        "question_id": question_id,
        "media_type": "application/json",
        "payload": payload,
        "payload_digest": runner.raw_digest(payload),
    }


def _candidate() -> dict[str, str]:
    tree = "b" * 40
    raw_commit = (
        f"tree {tree}\n"
        "author Test <test@example.com> 0 +0000\n"
        "committer Test <test@example.com> 0 +0000\n\n"
        "ITER-010 candidate\n"
    )
    raw = raw_commit.encode("utf-8")
    commit = hashlib.sha1(
        b"commit " + str(len(raw)).encode("ascii") + b"\0" + raw
    ).hexdigest()
    return {
        "commit": commit,
        "tree": tree,
        "raw_commit": raw_commit,
        "raw_commit_digest": runner.raw_digest(raw_commit),
    }


def _standing_scope() -> dict[str, object]:
    value = copy.deepcopy(runner.STANDING_SCOPE_VALUES)
    value["binding_digest"] = runner.canonical_digest(
        runner.STANDING_SCOPE_VALUES
    )
    return value


def _runtime_receipt(
    candidate_commit: str, *, index: int = 1
) -> dict[str, object]:
    configuration = copy.deepcopy(runner.EXECUTION_PROFILES["preferred"])
    input_payload = json.dumps(
        {
            "schema": "ITER010_RUNTIME_INPUT@1",
            "session_id": "session-001",
            "conversation_id": "conversation-001",
            "turn_id": f"turn-{index:03d}",
            "role": "answer",
            "question_id": f"q{index}",
            "content": "回答公开源码工程问题并保留证据。",
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    input_digest = runner.raw_digest(input_payload)
    disclosure = {
        "schema": "ITER010_PUBLIC_SOURCE_DISCLOSURE@1",
        "public_source_only": True,
        "secret_values_included": False,
        "source_origin": runner.STANDING_SCOPE_VALUES["source_origin"],
        "source_commit": runner.STANDING_SCOPE_VALUES["source_commit"],
        "input_payload_digest": input_digest,
    }
    budget = {
        "maximum_calls": 1,
        "maximum_input_tokens": 16_000,
        "maximum_output_tokens": 4_000,
        "timeout_milliseconds": 180_000,
    }
    value: dict[str, object] = {
        "receipt_id": f"dispatch-{index:03d}",
        "parent_authority_binding_digest": runner.canonical_digest(
            runner.STANDING_SCOPE_VALUES
        ),
        "candidate_commit": candidate_commit,
        "source_commit": runner.STANDING_SCOPE_VALUES["source_commit"],
        "source_tree": runner.STANDING_SCOPE_VALUES["source_tree"],
        "browser_url": runner.LOOPBACK_BROWSER_URL,
        "session_id": "session-001",
        "conversation_id": "conversation-001",
        "turn_id": f"turn-{index:03d}",
        "role": "answer",
        "route_role": "preferred",
        "provider_configuration": configuration,
        "provider_configuration_digest": runner.canonical_digest(configuration),
        "input_payload": input_payload,
        "input_digest": input_digest,
        "disclosure": disclosure,
        "disclosure_digest": runner.canonical_digest(disclosure),
        "budget": budget,
        "budget_digest": runner.canonical_digest(budget),
        "one_use": True,
        "consumed": True,
        "expired": False,
        "external_model_call_count": 1,
        "provider_dispatch_count": 1,
        "credential_resolution_count": 1,
        "tls_attempt_count": 1,
        "http_dispatch_count": 1,
    }
    value["receipt_digest"] = runner.canonical_digest(value)
    return value


def _experience(outcome: str = "QUALITY_PASS") -> dict[str, object]:
    candidate = _candidate()
    question_ids = ["q1", "q2", "q3"]
    question_texts = {
        "q1": "这个工程的用途和浏览器入口是什么？",
        "q2": "登录请求的主要调用链和副作用是什么？",
        "q3": "认证失败时系统如何区分未知、401 和 403？",
    }
    major_errors = 0 if outcome == "QUALITY_PASS" else 1
    regressions = 0 if outcome == "QUALITY_PASS" else 1
    system_total = 30 if outcome == "QUALITY_PASS" else 22
    codex_total = 24
    contributions = 1 if outcome == "QUALITY_PASS" else 0
    attachments = [
        _attachment(
            "browser",
            "browser-session",
            payload=json.dumps(
                {
                    "schema": "ITER010_BROWSER_SESSION_CAPTURE@1",
                    "candidate_commit": candidate["commit"],
                    "browser_url": runner.LOOPBACK_BROWSER_URL,
                    "operable": True,
                    "authentication_required": False,
                    "semantic_turn_count": 3,
                    "new_conversation_isolation_checked": True,
                    "session_id": "session-001",
                    "conversation_ids": ["conversation-001", "conversation-isolation"],
                    "turn_ids": ["turn-001", "turn-002", "turn-003"],
                },
                ensure_ascii=False,
            ),
        ),
        _attachment(
            "truth",
            "source-truth",
            payload=json.dumps(
                {
                    "schema": "ITER010_SOURCE_TRUTH_RECORD@1",
                    "source_commit": runner.STANDING_SCOPE_VALUES["source_commit"],
                    "records": [
                        {
                            "question_id": question_id,
                            "conclusion": f"源码事实结论 {question_id}",
                            "citations": [
                                {
                                    "label": f"{question_id}-source",
                                    "path": f"mall/source/{question_id}.java",
                                    "line_start": 10,
                                    "line_end": 12,
                                    "excerpt": f"公开源码证据片段 {question_id}",
                                    "excerpt_digest": runner.raw_digest(
                                        f"公开源码证据片段 {question_id}"
                                    ),
                                }
                            ],
                        }
                        for question_id in question_ids
                    ],
                },
                ensure_ascii=False,
            ),
        ),
        _attachment(
            "cognition",
            "world-model-cognition",
            payload=json.dumps(
                {
                    "schema": "ITER010_WORLD_MODEL_COGNITION_RECORD@1",
                    "records": [
                        {
                            "question_id": question_id,
                            "cognition_summary": f"世界模型认知 {question_id}",
                            "non_locator_contribution": outcome == "QUALITY_PASS" and question_id == "q1",
                        }
                        for question_id in question_ids
                    ],
                },
                ensure_ascii=False,
            ),
        ),
        _attachment(
            "comparison",
            "comparison-summary",
            payload=json.dumps(
                {
                    "schema": "ITER010_COMPARISON_SUMMARY_RECORD@1",
                    "question_ids": question_ids,
                    "declared_quality_outcome": outcome,
                    "major_error_count": major_errors,
                    "material_omission_count": 0,
                    "unsupported_citation_count": 0,
                    "material_regression_count": regressions,
                    "system_total_score": system_total,
                    "codex_total_score": codex_total,
                    "non_locator_world_model_contribution_count": contributions,
                    "assessment_text": "独立比较的原始结论，机器不认证其语义真实性。",
                },
                ensure_ascii=False,
            ),
        ),
    ]
    questions: list[dict[str, object]] = []
    categories = [
        "SYSTEM_PURPOSE_OR_ENTRY",
        "BEHAVIOR_CALL_FLOW_OR_SIDE_EFFECT",
        "FAILURE_AUTHORIZATION_OR_UNKNOWN",
    ]
    for index, category in enumerate(categories, start=1):
        question_id = f"q{index}"
        references: dict[str, str] = {}
        for field, kind in (
            ("system_answer_artifact_id", "system-answer"),
            ("current_codex_answer_artifact_id", "current-codex-answer"),
            ("independent_review_artifact_id", "independent-review"),
            ("question_comparison_artifact_id", "question-comparison"),
        ):
            artifact_id = f"{kind}-{question_id}"
            if kind == "system-answer":
                payload_value = {
                    "schema": "ITER010_SYSTEM_ANSWER_RECORD@1",
                    "question_id": question_id,
                    "question_text": question_texts[question_id],
                    "answer_text": f"系统回答 {question_id}，包含可检查的工程结论。",
                    "citation_labels": [f"{question_id}-source"],
                }
            elif kind == "current-codex-answer":
                payload_value = {
                    "schema": "ITER010_CURRENT_CODEX_ANSWER_RECORD@1",
                    "question_id": question_id,
                    "question_text": question_texts[question_id],
                    "answer_text": f"current Codex 独立回答 {question_id}。",
                    "client_identity": "actual-current-codex-client",
                }
            elif kind == "independent-review":
                payload_value = {
                    "schema": "ITER010_INDEPENDENT_REVIEW_RECORD@1",
                    "question_id": question_id,
                    "question_text": question_texts[question_id],
                    "review_text": f"独立审核记录 {question_id}。",
                    "major_error_count": 1 if outcome != "QUALITY_PASS" and question_id == "q1" else 0,
                    "material_omission_count": 0,
                    "unsupported_citation_count": 0,
                    "fresh_context": True,
                }
            else:
                payload_value = {
                    "schema": "ITER010_QUESTION_COMPARISON_RECORD@1",
                    "question_id": question_id,
                    "question_text": question_texts[question_id],
                    "evaluation_text": f"逐题盲评记录 {question_id}。",
                    "system_score": 10 if outcome == "QUALITY_PASS" else (4 if question_id == "q1" else 9),
                    "codex_score": 8,
                    "material_regression": outcome != "QUALITY_PASS" and question_id == "q1",
                    "blinded": True,
                }
            attachments.append(
                _attachment(
                    artifact_id,
                    kind,
                    question_id=question_id,
                    payload=json.dumps(payload_value, ensure_ascii=False),
                )
            )
            references[field] = artifact_id
        questions.append(
            {
                "question_id": question_id,
                "category": category,
                "unseen_during_repair": index > 1,
                **references,
            }
        )
    if outcome == "QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR":
        attachments.extend(
            [
                _attachment(
                    "failure",
                    "failure-analysis",
                    payload=json.dumps(
                        {
                            "schema": "ITER010_FAILURE_ANALYSIS_RECORD@1",
                            "earliest_layer": "world-model-cognition",
                            "falsifiable_hypothesis": "行为认知缺失导致后续调查遗漏。",
                            "general_repair": "修复通用行为认知构建和准入。",
                        },
                        ensure_ascii=False,
                    ),
                ),
                _attachment(
                    "rechecks",
                    "general-repair-rechecks",
                    payload=json.dumps(
                        {
                            "schema": "ITER010_GENERAL_REPAIR_RECHECK_RECORD@1",
                            "original_question_id": "q1",
                            "heterogeneous_recheck_question_ids": ["q2", "q3"],
                            "same_material_failure_reproduced": True,
                        }
                    ),
                ),
            ]
        )
    return {
        "schema": "ITER010_MVP_HANDOFF_PACKET@2",
        "candidate_identity": candidate,
        "standing_scope": _standing_scope(),
        "browser_url": runner.LOOPBACK_BROWSER_URL,
        "handoff_outcome": outcome,
        "machine_attestation": copy.deepcopy(runner.MACHINE_ATTESTATION),
        "attachments": attachments,
        "questions": questions,
        "runtime_receipts": [
            _runtime_receipt(candidate["commit"], index=index)
            for index in range(1, 4)
        ],
    }


def _envelope(
    *,
    action_evidence: dict[str, object] | None = None,
    verdict: str = "PASS",
    direction: bool = False,
) -> dict[str, object]:
    if direction:
        action_ref = runner.USER_DIRECTION_ACTION
        case_id = runner.USER_DIRECTION_CASE
        result_id = runner.USER_DIRECTION_RESULT
        path = runner.USER_DIRECTION_PATH
        counters = {field: 0 for field in runner.COUNTER_KEYS}
    else:
        action_ref = runner.EXPERIENCE_ACTION
        case_id = runner.EXPERIENCE_CASE
        result_id = runner.EXPERIENCE_RESULT
        path = runner.EXPERIENCE_PATH
        counters = {
            "external_model_call_count": 3,
            "provider_dispatch_count": 3,
            "credential_resolution_count": 3,
            "tls_attempt_count": 3,
            "http_dispatch_count": 3,
            "full_regression_run_count": 0,
        }
    subject = action_evidence or _experience()
    subject_digest = runner.canonical_digest(subject)
    execution_input_digest = runner.canonical_digest(
        {
            "plan_revision_ref": runner.PLAN_REVISION,
            "action_ref": action_ref,
            "verification_case_id": case_id,
            "subject_digest": subject_digest,
        }
    )
    runner_receipt = {
        "runner_id": runner.EVIDENCE_VERIFIER,
        "runner_identity_digest": DIGEST,
        "execution_input_digest": execution_input_digest,
        "exit_code": 0,
        "completed": True,
    }
    outcomes = [
        {
            "case_id": case_id,
            "verdict": verdict,
            "evidence_ref": "embedded:action-evidence",
            "evidence_digest": subject_digest,
        }
    ]
    return {
        "schema": runner.EVIDENCE_SCHEMA,
        "result_id": result_id,
        "plan_revision_ref": runner.PLAN_REVISION,
        "action_ref": action_ref,
        "verification_case_id": case_id,
        "plan_gate_verdict": verdict,
        "evidence_verifier": runner.EVIDENCE_VERIFIER,
        "evidence_artifact_path": path,
        "execution_input_digest": execution_input_digest,
        "runner_identity_digest": DIGEST,
        "runner_receipt_digest": runner.canonical_digest(runner_receipt),
        "verification_report_digest": runner.canonical_digest(outcomes),
        "subject_digest": subject_digest,
        "action_evidence": subject,
        "execution_counters": counters,
        "runner_receipt": runner_receipt,
        "case_outcomes": outcomes,
    }


def _reseal(envelope: dict[str, object]) -> None:
    subject_digest = runner.canonical_digest(envelope["action_evidence"])
    envelope["subject_digest"] = subject_digest
    envelope["execution_input_digest"] = runner.canonical_digest(
        {
            "plan_revision_ref": envelope["plan_revision_ref"],
            "action_ref": envelope["action_ref"],
            "verification_case_id": envelope["verification_case_id"],
            "subject_digest": subject_digest,
        }
    )
    receipt = envelope["runner_receipt"]
    assert isinstance(receipt, dict)
    receipt["execution_input_digest"] = envelope["execution_input_digest"]
    envelope["runner_receipt_digest"] = runner.canonical_digest(receipt)
    outcomes = envelope["case_outcomes"]
    assert isinstance(outcomes, list)
    outcomes[0]["evidence_digest"] = subject_digest
    envelope["verification_report_digest"] = runner.canonical_digest(outcomes)


class Iteration010MvpValueGateTest(unittest.TestCase):
    def test_accepts_complete_pass_handoff(self) -> None:
        artifact = _envelope()
        live = runner.validate_evidence(artifact)
        self.assertEqual("PASS", live["plan_gate_verdict"])
        self.assertEqual(3, live["external_model_call_count"])

    def test_accepts_complete_handoff_with_quality_failure(self) -> None:
        artifact = _envelope(
            action_evidence=_experience("QUALITY_FAIL_AFTER_ONE_GENERAL_REPAIR")
        )
        live = runner.validate_evidence(artifact)
        self.assertEqual("PASS", live["plan_gate_verdict"])

    def test_rejects_nonexistent_reference_style_evidence(self) -> None:
        artifact = _envelope()
        evidence = artifact["action_evidence"]
        assert isinstance(evidence, dict)
        attachments = evidence["attachments"]
        assert isinstance(attachments, list)
        attachments[0].pop("payload")
        attachments[0]["artifact_ref"] = "var/iteration-010/missing.json"
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_tampered_embedded_bytes(self) -> None:
        artifact = _envelope()
        attachments = artifact["action_evidence"]["attachments"]
        attachments[0]["payload"] = "tampered"
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_digest_valid_placeholder_payload(self) -> None:
        artifact = _envelope()
        attachments = artifact["action_evidence"]["attachments"]
        payload = '{"artifact":"browser"}'
        attachments[0]["payload"] = payload
        attachments[0]["payload_digest"] = runner.raw_digest(payload)
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_placeholder_answer_text(self) -> None:
        artifact = _envelope()
        attachments = artifact["action_evidence"]["attachments"]
        answer = next(item for item in attachments if item["kind"] == "system-answer")
        payload = json.loads(answer["payload"])
        payload["answer_text"] = "placeholder answer"
        answer["payload"] = json.dumps(payload)
        answer["payload_digest"] = runner.raw_digest(answer["payload"])
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_per_question_and_summary_contradiction(self) -> None:
        artifact = _envelope()
        attachments = artifact["action_evidence"]["attachments"]
        review = next(item for item in attachments if item["kind"] == "independent-review")
        payload = json.loads(review["payload"])
        payload["major_error_count"] = 999
        review["payload"] = json.dumps(payload)
        review["payload_digest"] = runner.raw_digest(review["payload"])
        comparison = next(item for item in attachments if item["kind"] == "question-comparison")
        payload = json.loads(comparison["payload"])
        payload["system_score"] = 0
        payload["codex_score"] = 999
        payload["material_regression"] = True
        comparison["payload"] = json.dumps(payload)
        comparison["payload_digest"] = runner.raw_digest(comparison["payload"])
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_overall_win_with_one_question_score_regression(self) -> None:
        artifact = _envelope()
        attachments = artifact["action_evidence"]["attachments"]
        comparisons = [
            item for item in attachments if item["kind"] == "question-comparison"
        ]
        scores = [(0, 100), (100, 0), (100, 0)]
        for item, (system_score, codex_score) in zip(comparisons, scores, strict=True):
            payload = json.loads(item["payload"])
            payload["system_score"] = system_score
            payload["codex_score"] = codex_score
            payload["material_regression"] = False
            item["payload"] = json.dumps(payload)
            item["payload_digest"] = runner.raw_digest(item["payload"])
        summary = next(
            item for item in attachments if item["kind"] == "comparison-summary"
        )
        payload = json.loads(summary["payload"])
        payload["system_total_score"] = 200
        payload["codex_total_score"] = 100
        payload["material_regression_count"] = 0
        summary["payload"] = json.dumps(payload)
        summary["payload_digest"] = runner.raw_digest(summary["payload"])
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_missing_question_attachment(self) -> None:
        artifact = _envelope()
        attachments = artifact["action_evidence"]["attachments"]
        attachments.pop()
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_attacker_defined_authority(self) -> None:
        artifact = _envelope()
        scope = artifact["action_evidence"]["standing_scope"]
        scope["authority_owner_ref"] = "attacker-defined-authority"
        body = {key: value for key, value in scope.items() if key != "binding_digest"}
        scope["binding_digest"] = runner.canonical_digest(body)
        receipt = artifact["action_evidence"]["runtime_receipts"][0]
        receipt["parent_authority_binding_digest"] = scope["binding_digest"]
        receipt_body = {key: value for key, value in receipt.items() if key != "receipt_digest"}
        receipt["receipt_digest"] = runner.canonical_digest(receipt_body)
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_source_revision_drift(self) -> None:
        artifact = _envelope()
        receipt = artifact["action_evidence"]["runtime_receipts"][0]
        receipt["source_commit"] = "e" * 40
        receipt_body = {key: value for key, value in receipt.items() if key != "receipt_digest"}
        receipt["receipt_digest"] = runner.canonical_digest(receipt_body)
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_unfrozen_execution_profile(self) -> None:
        artifact = _envelope()
        receipt = artifact["action_evidence"]["runtime_receipts"][0]
        receipt["provider_configuration"]["provider_identity"] = "ATTACKER"
        receipt["provider_configuration_digest"] = runner.canonical_digest(
            receipt["provider_configuration"]
        )
        receipt_body = {key: value for key, value in receipt.items() if key != "receipt_digest"}
        receipt["receipt_digest"] = runner.canonical_digest(receipt_body)
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_unbound_candidate_commit(self) -> None:
        artifact = _envelope()
        candidate = artifact["action_evidence"]["candidate_identity"]
        candidate["commit"] = "e" * 40
        receipt = artifact["action_evidence"]["runtime_receipts"][0]
        receipt["candidate_commit"] = candidate["commit"]
        receipt_body = {key: value for key, value in receipt.items() if key != "receipt_digest"}
        receipt["receipt_digest"] = runner.canonical_digest(receipt_body)
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_machine_semantic_quality_claim(self) -> None:
        artifact = _envelope()
        artifact["action_evidence"]["machine_attestation"][
            "semantic_answer_quality_verified"
        ] = True
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_counter_mismatch_and_full_regression(self) -> None:
        artifact = _envelope()
        artifact["execution_counters"]["provider_dispatch_count"] = 2
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)
        artifact = _envelope()
        artifact["execution_counters"]["full_regression_run_count"] = 1
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_unbound_disclosure_and_budget_values(self) -> None:
        artifact = _envelope()
        receipt = artifact["action_evidence"]["runtime_receipts"][0]
        receipt["disclosure"]["secret_values_included"] = True
        receipt["disclosure_digest"] = runner.canonical_digest(receipt["disclosure"])
        receipt_body = {
            key: value for key, value in receipt.items() if key != "receipt_digest"
        }
        receipt["receipt_digest"] = runner.canonical_digest(receipt_body)
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

        artifact = _envelope()
        receipt = artifact["action_evidence"]["runtime_receipts"][0]
        receipt["budget"]["maximum_calls"] = 2
        receipt["budget_digest"] = runner.canonical_digest(receipt["budget"])
        receipt_body = {
            key: value for key, value in receipt.items() if key != "receipt_digest"
        }
        receipt["receipt_digest"] = runner.canonical_digest(receipt_body)
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_rejects_receipt_session_or_role_not_bound_to_input(self) -> None:
        artifact = _envelope()
        receipt = artifact["action_evidence"]["runtime_receipts"][0]
        receipt["session_id"] = "attacker-session"
        receipt["conversation_id"] = "attacker-conversation"
        receipt["turn_id"] = "attacker-turn"
        receipt["role"] = "attacker-role"
        receipt_body = {
            key: value for key, value in receipt.items() if key != "receipt_digest"
        }
        receipt["receipt_digest"] = runner.canonical_digest(receipt_body)
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_user_direction_is_record_only(self) -> None:
        evidence = "用户基于完整体验选择继续，但这不是后续开发授权。"
        direction = {
            "schema": "ITER010_USER_DIRECTION_RECORD@2",
            "decision": "CONTINUE",
            "decision_ref": "local-user-message-utf8:sha256:" + "b" * 64,
            "decision_evidence": evidence,
            "decision_evidence_digest": runner.raw_digest(evidence),
            "local_record_only": True,
            "platform_authenticated": False,
            "known_limitations_acknowledged": True,
            "unlocks_followup_work": False,
            "followup_plan_revision_and_explicit_authorization_required": True,
        }
        artifact = _envelope(action_evidence=direction, direction=True)
        self.assertEqual("PASS", runner.validate_evidence(artifact)["plan_gate_verdict"])
        direction["unlocks_followup_work"] = True
        _reseal(artifact)
        with self.assertRaises(runner.EvidenceError):
            runner.validate_evidence(artifact)

    def test_duplicate_json_key_is_rejected(self) -> None:
        with self.assertRaises(runner.EvidenceError):
            runner.load_raw_evidence(b'{"schema":"a","schema":"b"}')

    def test_isolated_cli_emits_only_registered_fields(self) -> None:
        artifact = _envelope()
        completed = subprocess.run(
            [sys.executable, "-I", "-S", str(RUNNER), "verify-plan-evidence"],
            input=json.dumps(artifact, ensure_ascii=False).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(0, completed.returncode)
        self.assertEqual(b"", completed.stderr)
        self.assertEqual(runner.LIVE_FIELDS, set(json.loads(completed.stdout)))


if __name__ == "__main__":
    unittest.main()
