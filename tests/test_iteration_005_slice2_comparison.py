from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from software_world_model.ai_infrastructure import VolcengineArkModelConfiguration

from validation.structure_world_model_iteration_005 import slice2_comparison


class Iteration005Slice2ComparisonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        raw = b"<project/>\n"
        self.case = {
            "case_id": "WM-005-UNIT",
            "read_set_id": "read_set_unit",
            "question": "列出模块。",
            "expected_outcome": "SUPPORTED",
            "required_tokens": ["secret-oracle-token"],
            "forbidden_tokens": [],
            "outcome_markers_any": [],
        }
        self.suite = {
            "document_digest": "sha256:" + "a" * 64,
            "evaluation_subject_commit": "c" * 40,
            "evaluation_subject_tree": "d" * 40,
            "cases": [self.case],
            "source_closures": {
                "read_set_unit": {
                    "snapshots": [
                        {
                            "label": "A",
                            "revision": "b" * 40,
                            "files": [
                                {
                                    "path": "pom.xml",
                                    "sha256": "sha256:"
                                    + hashlib.sha256(raw).hexdigest(),
                                    "size": len(raw),
                                }
                            ],
                        }
                    ]
                }
            },
        }

    def _write(self, name: str, value: object) -> Path:
        path = self.root / name
        path.write_bytes(slice2_comparison._canonical(value))
        return path

    def test_pending_authorization_fails_closed(self) -> None:
        pending = slice2_comparison.pending_authorization(self.suite)
        path = self._write("pending.json", pending)

        with self.assertRaisesRegex(
            slice2_comparison.ComparisonFailure,
            "not explicitly authorized",
        ):
            slice2_comparison._require_authorization(path, self.suite)

    def test_current_suite_bound_authorization_loads(self) -> None:
        authorized = slice2_comparison.authorized_document(
            self.suite,
            authorized_at=datetime.now(timezone.utc).isoformat(),
            authorization_ref="unit-test-user-authorization",
        )
        path = self._write("authorized.json", authorized)

        loaded = slice2_comparison._require_authorization(path, self.suite)

        self.assertEqual(
            loaded["disclosure_set_digest"],
            slice2_comparison.disclosure_set_digest(self.suite),
        )

    def test_external_input_packet_excludes_evaluator_oracle(self) -> None:
        authorization = slice2_comparison.authorized_document(
            self.suite,
            authorized_at=datetime.now(timezone.utc).isoformat(),
            authorization_ref="unit-test-user-authorization",
        )
        with patch.object(
            slice2_comparison,
            "_git_show",
            return_value=b"<project/>\n",
        ):
            packet = slice2_comparison._input_packet(
                self.suite,
                self.case,
                self.root,
                authorization,
                surface="CONTROLLED_DIRECT",
            )

        encoded = slice2_comparison._canonical(packet).decode("utf-8")
        self.assertNotIn("expected_outcome", packet)
        self.assertNotIn("required_tokens", packet)
        self.assertNotIn("secret-oracle-token", encoded)
        self.assertIn("<project/>", encoded)

    def test_direct_call_uses_sealed_response_envelope(self) -> None:
        captured = {}

        class StubGateway:
            def __init__(self, *_arguments):
                pass

            def invoke(self, context):
                captured["context"] = context
                return SimpleNamespace(
                    call=SimpleNamespace(
                        state=SimpleNamespace(value="COMPLETED"),
                        failure_code=None,
                        provider_request_id=None,
                        actual_model_fingerprint="glm-5.2",
                        input_tokens=1,
                        output_tokens=1,
                        usage_complete=True,
                    ),
                    eligibility=SimpleNamespace(
                        eligible_for_production_domain_output=False,
                        reason="UNIT_TEST_NO_RESPONSE",
                    ),
                    replayed=False,
                    response=None,
                )

        packet = {
            "schema": slice2_comparison.INPUT_PACKET_SCHEMA,
            "document_digest": "sha256:" + "f" * 64,
        }
        case_root = self.root / "direct-case"
        case_root.mkdir()
        with (
            patch.object(slice2_comparison, "ModelGateway", StubGateway),
            patch.object(
                slice2_comparison,
                "VolcengineArkChatCompletionsNoToolsAdapter",
                return_value=object(),
            ),
        ):
            slice2_comparison._direct_case(
                suite=self.suite,
                case=self.case,
                packet=packet,
                case_root=case_root,
                configuration=VolcengineArkModelConfiguration(),
                qualification=object(),
            )

        context = captured["context"]
        self.assertEqual(context.max_output_tokens, 4096)
        self.assertEqual(
            context.prompt_program_ref,
            "iter-005-controlled-direct-source-answer@2",
        )
        instruction = context.manifest.items[0].content
        self.assertIn('{"answer":"..."}', instruction)
        self.assertIn("Escape every double quote", instruction)

    def test_mature_terminal_claims_are_revalidated_locally(self) -> None:
        with self.assertRaisesRegex(
            slice2_comparison.ComparisonFailure,
            "claim shape",
        ):
            slice2_comparison._mature_answer(
                {
                    "answer": "answer",
                    "claims": [{"claim": "unsupported-extra", "extra": []}],
                    "limitations": [],
                }
            )

    def test_world_health_must_bind_exact_suite_subject(self) -> None:
        digest = "sha256:" + "e" * 64
        health = {
            "status": "ready",
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "evaluation_subject_status": "CANDIDATE",
            "evaluation_subject_commit": self.suite["evaluation_subject_commit"],
            "evaluation_subject_tree": self.suite["evaluation_subject_tree"],
            "evaluation_grant_digest": digest,
            "deterministic_qualification_digest": digest,
            "held_out_suite_digest": self.suite["document_digest"],
            "independent_evaluator_digest": digest,
            "startup_preflight_digest": digest,
            "startup_receipt_digest": digest,
            "stage_manifest_digest": digest,
            "launcher_manifest_digest": digest,
            "provider_subject_digest": digest,
            "gateway_authorization_receipt_digest": digest,
            "dispatch_policy": "ONE_CALL_PER_QUESTION_NO_HIDDEN_RETRY",
            "production_activation": "NOT_EXECUTED",
        }
        self.assertEqual(
            slice2_comparison._validate_world_health(health, self.suite),
            health,
        )
        health["held_out_suite_digest"] = "sha256:" + "f" * 64
        with self.assertRaisesRegex(
            slice2_comparison.ComparisonFailure,
            "exact suite subject",
        ):
            slice2_comparison._validate_world_health(health, self.suite)


if __name__ == "__main__":
    unittest.main()
