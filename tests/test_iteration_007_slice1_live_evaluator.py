from __future__ import annotations

import unittest

from validation.structure_world_model_iteration_007 import slice1_live_evaluator


class Iteration007Slice1LiveEvaluatorTests(unittest.TestCase):
    def _result(self) -> dict[str, object]:
        question = "凭据失败时如何处理，成功时如何建立会话？"
        page = {
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "evaluation_only": True,
            "request": {"original_question": question},
            "read_binding": {"profile_refs": ["JAVA_SOURCE_SEMANTICS@1"]},
            "execution_boundary": {
                "provider_call_count": 3,
                "network_operation_count": 3,
                "source_access_allowed": False,
                "evidence_payload_access_allowed": False,
            },
            "review": {"decision": "APPROVE", "finding_codes": []},
            "assessment": {"needs": [{"outcome": "SATISFIED"}]},
            "answer": {"body": "有证据的回答", "claims": [{"claim_id": "c"}]},
            "authority_chain": {"stages": [{} for _ in range(10)]},
            "views": {
                "method": {"legacy_calls": [], "ordered_atoms": [{}]}
            },
        }
        return {
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "evaluation_subject_status": "CANDIDATE",
            "production_activation": "NOT_EXECUTED",
            "page": page,
            "execution": {
                "attempt_count": 1,
                "provider_call_count": 3,
                "network_operation_count": 3,
                "selective_retry_count": 0,
                "source_access_count": 0,
                "evidence_payload_access_count": 0,
            },
            "citations": [{"result_id": "structure_view_result_" + "1" * 32}],
        }

    def _verdict(self, result_digest: str) -> dict[str, object]:
        question = "凭据失败时如何处理，成功时如何建立会话？"
        core = {
            "schema": slice1_live_evaluator.VERDICT_SCHEMA,
            "status": "PASS",
            "expected_outcome": "SUPPORTED",
            "result_raw_sha256": result_digest,
            "question_digest": slice1_live_evaluator._digest(question),
            "answer_correct": True,
            "cross_domain_calls_and_semantics": True,
            "boundary_honest": False,
            "citation_opened": True,
            "browser_console_clean": True,
            "authorized_by": "user",
            "authorization_ref": "codex-user-message:public-test",
            "production_activation": "NOT_EXECUTED",
        }
        return {
            **core,
            "document_digest": slice1_live_evaluator._digest(
                [slice1_live_evaluator.VERDICT_SCHEMA, core]
            ),
        }

    def test_supported_cross_domain_result_passes(self) -> None:
        digest = "sha256:" + "a" * 64

        report = slice1_live_evaluator.evaluate(
            result=self._result(),
            result_raw_sha256=digest,
            verdict=self._verdict(digest),
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["provider_call_count"], 3)
        self.assertEqual(report["expected_outcome"], "SUPPORTED")

    def test_one_call_result_is_rejected(self) -> None:
        digest = "sha256:" + "b" * 64
        result = self._result()
        result["execution"] = {
            **result["execution"],
            "provider_call_count": 1,
        }

        with self.assertRaisesRegex(
            slice1_live_evaluator.LiveEvaluationError,
            "Slice boundary",
        ):
            slice1_live_evaluator.evaluate(
                result=result,
                result_raw_sha256=digest,
                verdict=self._verdict(digest),
            )


if __name__ == "__main__":
    unittest.main()
