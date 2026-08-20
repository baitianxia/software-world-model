from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from validation.structure_world_model_iteration_008 import slice1_freeze
from validation.structure_world_model_iteration_008 import slice1_live_authorize
from validation.structure_world_model_iteration_008 import slice1_live_evaluator


class Iteration008Slice1LiveAuthorizationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.message_digest = "sha256:" + "a" * 64
        self.message_ref = "codex-user-message:" + self.message_digest

    @staticmethod
    def _document(schema: str, core: dict[str, object]) -> dict[str, object]:
        return {**core, "document_digest": digest_of([schema, core]).value}

    def _pending_documents(self) -> tuple[Path, Path]:
        disclosure = self._document(
            slice1_freeze.DISCLOSURE_SCHEMA,
            {
                "status": "NOT_AUTHORIZED",
                "authorized_by": "user",
                "authorized_at": "2026-08-20T08:00:00+00:00",
                "authorization_ref": "PENDING_POST_FREEZE_USER_AUTHORIZATION",
                "payload_boundary": (
                    "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
                ),
            },
        )
        grant_core = {
            "schema": slice1_freeze.GRANT_SCHEMA,
            "environment": "EVALUATION_ONLY",
            "live_dispatch_authorized": False,
            "disclosure_authorization": disclosure,
            "evaluation_subject": {"sealed": True},
            "provider": {"sealed": True},
            "launcher_files": {"sealed": True},
            "forbidden_inputs": {"sealed": True},
            "production_activation": "NOT_EXECUTED",
        }
        grant = self._document(slice1_freeze.GRANT_SCHEMA, grant_core)
        grant_path = self.root / "evaluation-grant.NOT_AUTHORIZED.json"
        grant_path.write_bytes(canonical_json_bytes(grant))
        report_core = {
            "schema": slice1_freeze.REPORT_SCHEMA,
            "status": "PASS",
            "evaluation_subject_status": "CANDIDATE",
            "frozen_at": "2026-08-20T08:00:00Z",
            "pending_evaluation_grant_digest": grant["document_digest"],
            "external_model_dispatch_during_freeze": "NOT_EXECUTED",
            "live_question_status": "AWAITING_USER_AFTER_CODE_FREEZE",
            "production_activation": "NOT_EXECUTED",
        }
        report = self._document(slice1_freeze.REPORT_SCHEMA, report_core)
        report_path = self.root / "report.json"
        report_path.write_bytes(canonical_json_bytes(report))
        return report_path, grant_path

    def test_authorization_only_changes_the_grant_authority_fields(self) -> None:
        report_path, pending_path = self._pending_documents()
        value = slice1_live_authorize.authorize_grant(
            freeze_report_path=report_path,
            pending_grant_path=pending_path,
            output_path=self.root / "evaluation-grant.AUTHORIZED.json",
            authorized_at="2026-08-20T16:01:00+08:00",
            authorization_ref=self.message_ref,
            authorization_message_digest=self.message_digest,
        )

        pending = json.loads(pending_path.read_bytes())
        self.assertTrue(value["live_dispatch_authorized"])
        for field in (
            "evaluation_subject",
            "provider",
            "launcher_files",
            "forbidden_inputs",
        ):
            self.assertEqual(value[field], pending[field])

    def test_boundary_verdict_is_bound_to_exact_result_and_question(self) -> None:
        question = "这个不存在的流程能否被完整证明？"
        result_path = self.root / "result.json"
        result_path.write_bytes(
            canonical_json_bytes(
                {"page": {"request": {"original_question": question}}}
            )
        )
        verdict = slice1_live_authorize.seal_verdict(
            result_path=result_path,
            output_path=self.root / "verdict.json",
            status="PASS",
            expected_outcome="BOUNDED_ABSENCE",
            answer_correct=True,
            cross_domain_calls_and_semantics=False,
            boundary_honest=True,
            citation_opened=True,
            browser_console_clean=True,
            authorization_ref=self.message_ref,
            authorization_message_digest=self.message_digest,
        )

        self.assertEqual(verdict["schema"], slice1_live_evaluator.VERDICT_SCHEMA)
        self.assertEqual(verdict["question_digest"], digest_of(question).value)
        self.assertEqual(
            verdict["result_raw_sha256"],
            "sha256:" + hashlib.sha256(result_path.read_bytes()).hexdigest(),
        )


if __name__ == "__main__":
    unittest.main()
