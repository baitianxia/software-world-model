from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.cross_cutting import canonical_json_bytes, digest_of
from validation.structure_world_model_iteration_007 import slice1_freeze
from validation.structure_world_model_iteration_007 import slice1_live_authorize
from validation.structure_world_model_iteration_007 import slice1_live_evaluator


class Iteration007Slice1LiveAuthorizationTests(unittest.TestCase):
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
        disclosure_core = {
            "status": "NOT_AUTHORIZED",
            "authorized_by": "user",
            "authorized_at": "2026-08-13T08:00:00+00:00",
            "authorization_ref": "PENDING_POST_FREEZE_USER_AUTHORIZATION",
            "payload_boundary": (
                "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
            ),
        }
        disclosure = self._document(
            slice1_freeze.DISCLOSURE_SCHEMA, disclosure_core
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
            "frozen_at": "2026-08-13T08:00:00Z",
            "pending_evaluation_grant_digest": grant["document_digest"],
            "external_model_dispatch_during_freeze": "NOT_EXECUTED",
            "live_question_status": "AWAITING_USER_AFTER_CODE_FREEZE",
            "production_activation": "NOT_EXECUTED",
        }
        report = self._document(slice1_freeze.REPORT_SCHEMA, report_core)
        report_path = self.root / "report.json"
        report_path.write_bytes(canonical_json_bytes(report))
        return report_path, grant_path

    def test_authorization_postdating_freeze_only_changes_authority_fields(self) -> None:
        report_path, pending_path = self._pending_documents()
        output = self.root / "evaluation-grant.AUTHORIZED.json"

        value = slice1_live_authorize.authorize_grant(
            freeze_report_path=report_path,
            pending_grant_path=pending_path,
            output_path=output,
            authorized_at="2026-08-13T16:01:00+08:00",
            authorization_ref=self.message_ref,
            authorization_message_digest=self.message_digest,
        )

        pending = json.loads(pending_path.read_bytes())
        self.assertTrue(value["live_dispatch_authorized"])
        self.assertEqual(
            value["disclosure_authorization"]["authorization_ref"],
            self.message_ref,
        )
        for field in (
            "evaluation_subject",
            "provider",
            "launcher_files",
            "forbidden_inputs",
        ):
            self.assertEqual(value[field], pending[field])
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)

    def test_authorization_at_freeze_time_is_rejected(self) -> None:
        report_path, pending_path = self._pending_documents()

        with self.assertRaisesRegex(
            slice1_live_authorize.LiveAuthorizationError,
            "must postdate",
        ):
            slice1_live_authorize.authorize_grant(
                freeze_report_path=report_path,
                pending_grant_path=pending_path,
                output_path=self.root / "authorized.json",
                authorized_at="2026-08-13T16:00:00+08:00",
                authorization_ref=self.message_ref,
                authorization_message_digest=self.message_digest,
            )

    def test_supported_user_verdict_is_bound_to_exact_result_and_question(self) -> None:
        question = "How does the implementation handle invalid credentials?"
        result_path = self.root / "result.json"
        result_path.write_bytes(
            canonical_json_bytes(
                {"page": {"request": {"original_question": question}}}
            )
        )
        output = self.root / "verdict.json"

        verdict = slice1_live_authorize.seal_verdict(
            result_path=result_path,
            output_path=output,
            status="PASS",
            expected_outcome="SUPPORTED",
            answer_correct=True,
            cross_domain_calls_and_semantics=True,
            boundary_honest=False,
            citation_opened=True,
            browser_console_clean=True,
            authorization_ref=self.message_ref,
            authorization_message_digest=self.message_digest,
        )

        self.assertEqual(verdict["schema"], slice1_live_evaluator.VERDICT_SCHEMA)
        self.assertEqual(verdict["question_digest"], digest_of(question).value)
        self.assertEqual(
            verdict["result_raw_sha256"],
            "sha256:"
            + hashlib.sha256(result_path.read_bytes()).hexdigest(),
        )

    def test_pass_cannot_hide_a_negative_user_judgement(self) -> None:
        result_path = self.root / "result.json"
        result_path.write_bytes(
            canonical_json_bytes(
                {"page": {"request": {"original_question": "question"}}}
            )
        )

        with self.assertRaisesRegex(
            slice1_live_authorize.LiveAuthorizationError,
            "requires correctness",
        ):
            slice1_live_authorize.seal_verdict(
                result_path=result_path,
                output_path=self.root / "verdict.json",
                status="PASS",
                expected_outcome="SUPPORTED",
                answer_correct=False,
                cross_domain_calls_and_semantics=True,
                boundary_honest=False,
                citation_opened=True,
                browser_console_clean=True,
                authorization_ref=self.message_ref,
                authorization_message_digest=self.message_digest,
            )


if __name__ == "__main__":
    unittest.main()
