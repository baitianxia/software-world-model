from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from software_world_model.ai_infrastructure import (
    DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT,
    ProviderHTTPResponse,
    ProviderOutcomeUnknown,
)
from validation.structure_world_model_iteration_008.capability import (
    authorize,
    cli,
    freeze,
)


def _session_audit(calls: int, *, unknown: int = 0):
    return {
        "schema": "SWM-DEEPSEEK-TRANSPORT-SESSION-AUDIT@2",
        "connection_policy": "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2",
        "maximum_pre_dispatch_tls_handshake_attempts": 3,
        "maximum_http_dispatches_per_tls_session": 20,
        "tls_handshake_attempt_count": 1 if calls else 0,
        "tls_handshake_success_count": 1 if calls else 0,
        "pre_dispatch_tls_handshake_failure_count": 0,
        "pre_dispatch_tls_failure_codes": [],
        "http_dispatch_count": calls,
        "connection_reuse_count": max(0, calls - 1),
        "verified_peer_certificate_sha256s": (
            ["sha256:" + "d" * 64] if calls else []
        ),
        "post_dispatch_outcome_unknown_count": unknown,
        "post_dispatch_failure_codes": ["TIMEOUT"] * unknown,
        "request_retry_count": 0,
        "credential_resolution_count": calls,
        "credential_resolution_success_count": calls,
        "credential_resolution_policy": (
            "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH"
        ),
    }


class _PassingDiagnosticTransport:
    def __init__(self) -> None:
        self.calls = 0

    def post_json(self, **_arguments):
        self.calls += 1
        return ProviderHTTPResponse(
            status_code=200,
            headers={"x-request-id": "deepseek-diagnostic-request-1"},
            body=json.dumps(
                {
                    "id": "chatcmpl_deepseek_diagnostic_1",
                    "object": "chat.completion",
                    "model": DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": '{"status":"ok"}',
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    },
                }
            ).encode("utf-8"),
        )

    def session_audit(self):
        return _session_audit(self.calls)


class _UnknownDiagnosticTransport:
    def __init__(self) -> None:
        self.calls = 0

    def post_json(self, **_arguments):
        self.calls += 1
        raise ProviderOutcomeUnknown(
            "fixture diagnostic outcome unknown", reason_code="TIMEOUT"
        )

    def session_audit(self):
        return _session_audit(self.calls, unknown=self.calls)


class Iteration008DeepSeekDiagnosticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = {
            "commit": "1" * 40,
            "tree": "2" * 40,
            "worktree_status": "CLEAN",
            "identity_scope": "EXACT_GIT_COMMIT_AND_TREE@1",
        }
        self.created = datetime(2026, 8, 17, tzinfo=timezone.utc)

    def _freeze_and_authorize(self, root: Path):
        with patch.object(
            freeze, "_candidate_identity", return_value=self.identity
        ):
            freeze_path, request_path, frozen = (
                freeze.create_model_diagnostic_freeze(
                    output_directory=root / "freeze",
                    created_at=self.created,
                )
            )
        authorization_path, authorization = authorize.create_authorization(
            request_path=request_path,
            output_path=root / "authorization.json",
            authorized_at=self.created + timedelta(seconds=1),
            authorization_ref="codex-user-message:sha256:" + "a" * 64,
            single_use_result_directory=root / "result",
        )
        return freeze_path, request_path, frozen, authorization_path, authorization

    def test_freeze_is_zero_network_and_binds_one_exact_call(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            freeze_path, request_path, frozen, _, authorization = (
                self._freeze_and_authorize(root)
            )
            request = authorize._load_request(request_path)

            self.assertTrue(freeze_path.is_file())
            self.assertEqual(request["phase"], "DEEPSEEK_MODEL_DIAGNOSTIC")
            self.assertEqual(
                request["authorization_scope"]["planned_provider_call_count"],
                1,
            )
            self.assertEqual(
                request["authorization_scope"]["connection_policy"],
                "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2",
            )
            self.assertEqual(
                request["authorization_scope"][
                    "maximum_pre_dispatch_tls_handshake_attempts"
                ],
                3,
            )
            self.assertEqual(
                request["authorization_scope"]["credential_resolution_policy"],
                "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH",
            )
            self.assertFalse(
                request["authorization_scope"]["request_retry_allowed"]
            )
            self.assertEqual(
                frozen["dispatch_contract"]["credential_read_before_authorization"],
                False,
            )
            self.assertEqual(authorization["authorization_scope"], request["authorization_scope"])
            self.assertFalse((root / "result").exists())

    def test_authorized_probe_consumes_one_call_and_seals_sanitized_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            freeze_path, _, _, authorization_path, _ = self._freeze_and_authorize(
                root
            )
            transport = _PassingDiagnosticTransport()
            with patch.object(
                cli, "_candidate_identity", return_value=self.identity
            ):
                payload, code = cli._run_authorized_model_diagnostic(
                    freeze_path=freeze_path,
                    authorization_path=authorization_path,
                    environment={
                        "DEEPSEEK_API_KEY": "fixture-secret-never-persist"
                    },
                    transport=transport,
                )

            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "MODEL_DIAGNOSTIC_PASS")
            self.assertEqual(payload["provider_request_count"], 1)
            self.assertEqual(transport.calls, 1)
            result = json.loads((root / "result" / "result.json").read_text())
            terminal = json.loads(
                (root / "result" / "terminal.json").read_text()
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(terminal["provider_request_count"], 1)
            persisted = "".join(
                path.read_text()
                for path in (root / "result").iterdir()
                if path.is_file()
            )
            self.assertNotIn("fixture-secret-never-persist", persisted)
            self.assertNotIn('{"status":"ok"}', persisted)

    def test_unknown_outcome_is_sealed_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            freeze_path, _, _, authorization_path, _ = self._freeze_and_authorize(
                root
            )
            transport = _UnknownDiagnosticTransport()
            with patch.object(
                cli, "_candidate_identity", return_value=self.identity
            ), self.assertRaises(ProviderOutcomeUnknown):
                cli._run_authorized_model_diagnostic(
                    freeze_path=freeze_path,
                    authorization_path=authorization_path,
                    environment={
                        "DEEPSEEK_API_KEY": "fixture-secret-never-persist"
                    },
                    transport=transport,
                )

            self.assertEqual(transport.calls, 1)
            failure = json.loads(
                (root / "result" / "failure.json").read_text()
            )
            terminal = json.loads(
                (root / "result" / "terminal.json").read_text()
            )
            self.assertEqual(failure["failure_code"], "TIMEOUT")
            self.assertEqual(failure["attempted_provider_request_count"], 1)
            self.assertEqual(terminal["status"], "PROVIDER_OUTCOME_UNKNOWN")
            self.assertFalse(terminal["retry_permitted_with_same_authorization"])


if __name__ == "__main__":
    unittest.main()
