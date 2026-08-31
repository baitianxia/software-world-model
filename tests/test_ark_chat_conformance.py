from __future__ import annotations

from datetime import datetime, timezone
from io import StringIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from software_world_model.ai_infrastructure import (
    AdapterConformanceLevel,
    ARK_CHAT_CONFORMANCE_FIXTURE_VERSION,
    ARK_CHAT_CONFORMANCE_RESULT_SCHEMA,
    DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT,
    ProviderHTTPResponse,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    load_ark_chat_conformance_qualification,
    run_ark_chat_conformance,
    seal_ark_chat_conformance_result,
)
from software_world_model.cross_cutting import DomainError, ErrorCode, digest_of
from software_world_model.interface.provider_cli import main as provider_main


class EchoingArkTransport:
    def __init__(self, *, duplicate_request_id: bool = False) -> None:
        self.calls = 0
        self.duplicate_request_id = duplicate_request_id

    def post_json(self, **arguments):
        self.calls += 1
        body = json.loads(arguments["body"])
        schema = json.loads(
            body["messages"][0]["content"].rsplit("Schema: ", 1)[1]
        )
        properties = schema["properties"]
        content = json.dumps(
            {
                "case": properties["case"]["enum"][0],
                "nonce": properties["nonce"]["enum"][0],
                "status": "ok",
            },
            separators=(",", ":"),
        )
        request_number = 1 if self.duplicate_request_id else self.calls
        return ProviderHTTPResponse(
            status_code=200,
            headers={"x-tt-logid": f"ark-live-{request_number}"},
            body=json.dumps(
                {
                    "id": f"chatcmpl_{self.calls}",
                    "object": "chat.completion",
                    "model": DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT,
                    "choices": [
                        {
                            "index": 0,
                            "message": {"role": "assistant", "content": content},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    },
                }
            ).encode(),
        )

    def session_audit(self):
        return {
            "schema": "SWM-VOLCENGINE-ARK-TRANSPORT-SESSION-AUDIT@1",
            "connection_policy": (
                "DIRECT_VERIFIED_TLS_HTTP11_ONE_REQUEST_PER_SESSION@1"
            ),
            "maximum_pre_dispatch_tls_handshake_attempts_per_request": 1,
            "maximum_http_dispatches_per_tls_session": 1,
            "tls_handshake_attempt_count": self.calls,
            "tls_handshake_success_count": self.calls,
            "pre_dispatch_tls_handshake_failure_count": 0,
            "pre_dispatch_tls_failure_codes": [],
            "http_dispatch_count": self.calls,
            "connection_reuse_count": 0,
            "verified_peer_certificate_sha256s": [
                "sha256:" + f"{ordinal:064x}"
                for ordinal in range(1, self.calls + 1)
            ],
            "post_dispatch_outcome_unknown_count": 0,
            "post_dispatch_failure_codes": [],
            "request_retry_count": 0,
            "credential_resolution_count": self.calls,
            "credential_resolution_success_count": self.calls,
            "credential_resolution_policy": (
                "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH"
            ),
        }


class ArkChatConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration = VolcengineArkModelConfiguration()
        self.clock_value = datetime(2026, 8, 6, 8, 0, tzinfo=timezone.utc)

    def run_result(self, transport=None):
        return run_ark_chat_conformance(
            configuration=self.configuration,
            transport=transport or EchoingArkTransport(),
            environment={"ARK_API_KEY": "fixture-secret-never-persist"},
            operator="test-operator",
            timeout_milliseconds=1000,
            max_output_tokens=64,
            clock=lambda: self.clock_value,
            monotonic=lambda: 10.0,
            nonce_factory=iter(("nonce-first", "nonce-second")).__next__,
            run_id_factory=lambda: "ccrun_" + "1" * 32,
        )

    def test_live_and_negative_oracles_produce_sanitized_pass(self) -> None:
        result = self.run_result()

        self.assertEqual(result["outcome"], "PASS")
        self.assertEqual(ARK_CHAT_CONFORMANCE_FIXTURE_VERSION, "1.8.0")
        self.assertEqual(
            ARK_CHAT_CONFORMANCE_RESULT_SCHEMA,
            "swm.ark-chat-conformance-result@2",
        )
        self.assertEqual(len(result["cases"]), 13)
        self.assertTrue(all(case["outcome"] == "PASS" for case in result["cases"]))
        self.assertEqual(result["execution"]["request_count"], 2)
        self.assertEqual(result["execution"]["input_tokens"], 20)
        self.assertEqual(result["execution"]["output_tokens"], 10)
        self.assertEqual(
            result["execution"]["transport_session"][
                "tls_handshake_success_count"
            ],
            2,
        )
        self.assertEqual(
            result["execution"]["transport_session"]["connection_reuse_count"],
            0,
        )
        serialized = json.dumps(result)
        self.assertNotIn("fixture-secret-never-persist", serialized)
        self.assertNotIn("nonce-first", serialized)
        self.assertNotIn("nonce-second", serialized)

    def test_result_is_exclusive_and_loads_as_live_qualification(self) -> None:
        result = self.run_result()
        with tempfile.TemporaryDirectory() as directory:
            path = seal_ark_chat_conformance_result(result, directory)
            qualification = load_ark_chat_conformance_qualification(
                path, self.configuration, now=self.clock_value
            )
            adapter = VolcengineArkChatCompletionsNoToolsAdapter(
                transport=EchoingArkTransport(),
                configuration=self.configuration,
                output_schemas={},
                live_qualification=qualification,
            )

            self.assertTrue(path.is_file())
            self.assertEqual(
                adapter.capabilities.conformance_level,
                AdapterConformanceLevel.LIVE_CURRENT,
            )
            self.assertEqual(
                adapter.capabilities.qualified_model_fingerprints,
                self.configuration.qualified_model_identities,
            )
            self.assertTrue(
                qualification.validate(
                    SimpleNamespace(
                        conformance_result_ref=qualification.result_ref,
                        adapter_version=self.configuration.adapter_version,
                        provider_configuration_fingerprint=self.configuration.fingerprint,
                        model_ref=self.configuration.model_ref,
                    ),
                    self.clock_value,
                )
            )
            with self.assertRaises(DomainError) as raised:
                seal_ark_chat_conformance_result(result, directory)
            self.assertEqual(raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT)

    def test_tampering_or_failed_case_cannot_load_as_qualification(self) -> None:
        duplicate = self.run_result(EchoingArkTransport(duplicate_request_id=True))
        self.assertEqual(duplicate["outcome"], "FAIL")
        with tempfile.TemporaryDirectory() as directory:
            failed_path = seal_ark_chat_conformance_result(duplicate, directory)
            with self.assertRaises(DomainError) as failed:
                load_ark_chat_conformance_qualification(
                    failed_path, self.configuration, now=self.clock_value
                )
            self.assertEqual(failed.exception.code, ErrorCode.QUALIFICATION_INVALID)

            passed = self.run_result()
            passed_path = seal_ark_chat_conformance_result(passed, Path(directory) / "passed")
            document = json.loads(passed_path.read_text())
            document["model"]["requested_model_ref"] = "tampered-model"
            passed_path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(DomainError) as tampered:
                load_ark_chat_conformance_qualification(
                    passed_path, self.configuration, now=self.clock_value
                )
            self.assertEqual(tampered.exception.code, ErrorCode.QUALIFICATION_INVALID)

            session_path = seal_ark_chat_conformance_result(
                self.run_result(), Path(directory) / "session"
            )
            session_document = json.loads(session_path.read_text())
            session_document["execution"]["transport_session"][
                "connection_reuse_count"
            ] = 1
            session_document["result_digest"] = digest_of(
                {
                    key: value
                    for key, value in session_document.items()
                    if key != "result_digest"
                }
            ).value
            session_path.write_text(
                json.dumps(session_document), encoding="utf-8"
            )
            with self.assertRaises(DomainError) as session_tampered:
                load_ark_chat_conformance_qualification(
                    session_path,
                    self.configuration,
                    now=self.clock_value,
                )
            self.assertEqual(
                session_tampered.exception.code,
                ErrorCode.QUALIFICATION_INVALID,
            )

            credential_path = seal_ark_chat_conformance_result(
                self.run_result(), Path(directory) / "credential"
            )
            credential_document = json.loads(credential_path.read_text())
            credential_document["provider"]["credential_configured"] = False
            credential_document["result_digest"] = digest_of(
                {
                    key: value
                    for key, value in credential_document.items()
                    if key != "result_digest"
                }
            ).value
            credential_path.write_text(
                json.dumps(credential_document), encoding="utf-8"
            )
            with self.assertRaises(DomainError) as credential_tampered:
                load_ark_chat_conformance_qualification(
                    credential_path,
                    self.configuration,
                    now=self.clock_value,
                )
            self.assertEqual(
                credential_tampered.exception.code,
                ErrorCode.QUALIFICATION_INVALID,
            )

    def test_cli_seals_summary_without_secret_or_raw_content(self) -> None:
        output = StringIO()
        with tempfile.TemporaryDirectory() as directory:
            code = provider_main(
                [
                    "conformance",
                    "--result-directory",
                    directory,
                    "--operator",
                    "test-operator",
                ],
                stdout=output,
                environment={"ARK_API_KEY": "fixture-secret-never-persist"},
                transport=EchoingArkTransport(),
            )
            summary = json.loads(output.getvalue())
            result_path = Path(summary["result_path"])

            self.assertEqual(code, 0)
            self.assertEqual(summary["conformance"], "PASS")
            self.assertTrue(result_path.is_file())
            self.assertFalse(summary["production_eligible"])
            self.assertNotIn("fixture-secret-never-persist", output.getvalue())

if __name__ == "__main__":
    unittest.main()
