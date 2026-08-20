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
    DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT,
    DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_VERSION,
    DEEPSEEK_CHAT_CONFORMANCE_RESULT_SCHEMA,
    DeepSeekChatCompletionsNoToolsAdapter,
    DeepSeekModelConfiguration,
    ProviderHTTPResponse,
    current_deepseek_implementation_manifest,
    load_deepseek_chat_conformance_qualification,
    run_deepseek_chat_conformance,
    seal_deepseek_chat_conformance_result,
)
from software_world_model.cross_cutting import DomainError, ErrorCode, digest_of
from software_world_model.interface.deepseek_provider_cli import (
    main as deepseek_provider_main,
)


class EchoingDeepSeekTransport:
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
            headers={"x-request-id": f"deepseek-live-{request_number}"},
            body=json.dumps(
                {
                    "id": f"chatcmpl_deepseek_{self.calls}",
                    "object": "chat.completion",
                    "model": DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT,
                    "system_fingerprint": "fp_fixture",
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": content,
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                        "prompt_cache_hit_tokens": 0,
                        "prompt_cache_miss_tokens": 10,
                    },
                }
            ).encode("utf-8"),
        )

    def session_audit(self):
        return {
            "schema": "SWM-DEEPSEEK-TRANSPORT-SESSION-AUDIT@2",
            "connection_policy": "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@2",
            "maximum_pre_dispatch_tls_handshake_attempts": 3,
            "maximum_http_dispatches_per_tls_session": 20,
            "tls_handshake_attempt_count": 1 if self.calls else 0,
            "tls_handshake_success_count": 1 if self.calls else 0,
            "pre_dispatch_tls_handshake_failure_count": 0,
            "pre_dispatch_tls_failure_codes": [],
            "http_dispatch_count": self.calls,
            "connection_reuse_count": max(0, self.calls - 1),
            "verified_peer_certificate_sha256s": (
                ["sha256:" + "c" * 64] if self.calls else []
            ),
            "post_dispatch_outcome_unknown_count": 0,
            "post_dispatch_failure_codes": [],
            "request_retry_count": 0,
            "credential_resolution_count": self.calls,
            "credential_resolution_success_count": self.calls,
            "credential_resolution_policy": (
                "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH"
            ),
        }


class ProbeDeepSeekTransport:
    def post_json(self, **arguments):
        return ProviderHTTPResponse(
            status_code=200,
            headers={"x-request-id": "deepseek-probe-1"},
            body=json.dumps(
                {
                    "id": "chatcmpl_deepseek_probe",
                    "object": "chat.completion",
                    "model": DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT,
                    "system_fingerprint": "fp_fixture",
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


class DeepSeekChatConformanceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configuration = DeepSeekModelConfiguration()
        self.clock_value = datetime(2026, 8, 17, 8, 0, tzinfo=timezone.utc)

    def run_result(self, transport=None):
        return run_deepseek_chat_conformance(
            configuration=self.configuration,
            transport=transport or EchoingDeepSeekTransport(),
            environment={"DEEPSEEK_API_KEY": "fixture-secret-never-persist"},
            operator="test-operator",
            timeout_milliseconds=1000,
            max_output_tokens=64,
            clock=lambda: self.clock_value,
            monotonic=lambda: 10.0,
            nonce_factory=iter(("nonce-first", "nonce-second")).__next__,
            run_id_factory=lambda: "ccrun_" + "2" * 32,
        )

    def test_live_and_negative_oracles_produce_sanitized_pass(self) -> None:
        result = self.run_result()

        self.assertEqual(result["outcome"], "PASS")
        self.assertEqual(DEEPSEEK_CHAT_CONFORMANCE_FIXTURE_VERSION, "1.2.0")
        self.assertEqual(
            DEEPSEEK_CHAT_CONFORMANCE_RESULT_SCHEMA,
            "swm.deepseek-chat-conformance-result@2",
        )
        self.assertEqual(result["fixture_version"], "1.2.0")
        self.assertEqual(result["provider"]["provider_type"], "DEEPSEEK")
        self.assertEqual(len(result["cases"]), 12)
        self.assertTrue(all(case["outcome"] == "PASS" for case in result["cases"]))
        self.assertEqual(result["execution"]["request_count"], 2)
        self.assertEqual(result["execution"]["input_tokens"], 20)
        self.assertEqual(result["execution"]["output_tokens"], 10)
        self.assertEqual(
            result["execution"]["transport_session"]["connection_reuse_count"],
            1,
        )
        self.assertEqual(result["model"]["thinking_mode"], "DISABLED")
        self.assertEqual(result["model"]["temperature"], 0)
        serialized = json.dumps(result)
        self.assertNotIn("fixture-secret-never-persist", serialized)
        self.assertNotIn("nonce-first", serialized)
        self.assertNotIn("nonce-second", serialized)

    def test_result_is_exclusive_and_loads_as_live_qualification(self) -> None:
        result = self.run_result()
        with tempfile.TemporaryDirectory() as directory:
            path = seal_deepseek_chat_conformance_result(result, directory)
            qualification = load_deepseek_chat_conformance_qualification(
                path,
                self.configuration,
                now=self.clock_value,
            )
            adapter = DeepSeekChatCompletionsNoToolsAdapter(
                transport=EchoingDeepSeekTransport(),
                configuration=self.configuration,
                output_schemas={},
                live_qualification=qualification,
            )

            self.assertEqual(
                adapter.capabilities.conformance_level,
                AdapterConformanceLevel.LIVE_CURRENT,
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
                seal_deepseek_chat_conformance_result(result, directory)
            self.assertEqual(
                raised.exception.code,
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
            )

    def test_failed_or_tampered_result_cannot_qualify(self) -> None:
        failed = self.run_result(
            EchoingDeepSeekTransport(duplicate_request_id=True)
        )
        self.assertEqual(failed["outcome"], "FAIL")
        with tempfile.TemporaryDirectory() as directory:
            failed_path = seal_deepseek_chat_conformance_result(failed, directory)
            with self.assertRaises(DomainError) as raised:
                load_deepseek_chat_conformance_qualification(
                    failed_path,
                    self.configuration,
                    now=self.clock_value,
                )
            self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

            passed_path = seal_deepseek_chat_conformance_result(
                self.run_result(), Path(directory) / "passed"
            )
            document = json.loads(passed_path.read_text())
            document["model"]["thinking_mode"] = "ENABLED"
            passed_path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(DomainError) as tampered:
                load_deepseek_chat_conformance_qualification(
                    passed_path,
                    self.configuration,
                    now=self.clock_value,
                )
            self.assertEqual(tampered.exception.code, ErrorCode.QUALIFICATION_INVALID)

            temperature_path = seal_deepseek_chat_conformance_result(
                self.run_result(), Path(directory) / "temperature"
            )
            temperature_document = json.loads(temperature_path.read_text())
            temperature_document["model"]["temperature"] = 1
            temperature_document["result_digest"] = digest_of(
                {
                    key: value
                    for key, value in temperature_document.items()
                    if key != "result_digest"
                }
            ).value
            temperature_path.write_text(
                json.dumps(temperature_document), encoding="utf-8"
            )
            with self.assertRaises(DomainError) as temperature_tampered:
                load_deepseek_chat_conformance_qualification(
                    temperature_path,
                    self.configuration,
                    now=self.clock_value,
                )
            self.assertEqual(
                temperature_tampered.exception.code,
                ErrorCode.QUALIFICATION_INVALID,
            )

            session_path = seal_deepseek_chat_conformance_result(
                self.run_result(), Path(directory) / "session"
            )
            session_document = json.loads(session_path.read_text())
            session_document["execution"]["transport_session"][
                "connection_reuse_count"
            ] = 0
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
                load_deepseek_chat_conformance_qualification(
                    session_path,
                    self.configuration,
                    now=self.clock_value,
                )
            self.assertEqual(
                session_tampered.exception.code,
                ErrorCode.QUALIFICATION_INVALID,
            )

    def test_implementation_manifest_is_deepseek_specific(self) -> None:
        manifest = current_deepseek_implementation_manifest()
        paths = {item["path"] for item in manifest["files"]}
        self.assertIn("ai_infrastructure/deepseek_chat_adapter.py", paths)
        self.assertIn("interface/deepseek_provider_cli.py", paths)
        self.assertNotIn("ai_infrastructure/volcengine_ark_chat_adapter.py", paths)

    def test_cli_status_probe_and_conformance_never_expose_secret(self) -> None:
        status_output = StringIO()
        status_code = deepseek_provider_main(
            ["status"],
            stdout=status_output,
            environment={"DEEPSEEK_API_KEY": "fixture-secret-never-persist"},
        )
        self.assertEqual(status_code, 0)
        self.assertTrue(json.loads(status_output.getvalue())["credential_configured"])
        self.assertNotIn("fixture-secret-never-persist", status_output.getvalue())

        probe_output = StringIO()
        probe_code = deepseek_provider_main(
            ["probe"],
            stdout=probe_output,
            environment={"DEEPSEEK_API_KEY": "fixture-secret-never-persist"},
            transport=ProbeDeepSeekTransport(),
        )
        self.assertEqual(probe_code, 0)
        self.assertEqual(
            json.loads(probe_output.getvalue())["transport_probe"],
            "PASS",
        )
        self.assertNotIn("fixture-secret-never-persist", probe_output.getvalue())

        conformance_output = StringIO()
        with tempfile.TemporaryDirectory() as directory:
            conformance_code = deepseek_provider_main(
                [
                    "conformance",
                    "--result-directory",
                    directory,
                    "--operator",
                    "test-operator",
                ],
                stdout=conformance_output,
                environment={
                    "DEEPSEEK_API_KEY": "fixture-secret-never-persist"
                },
                transport=EchoingDeepSeekTransport(),
            )
            summary = json.loads(conformance_output.getvalue())
            self.assertEqual(conformance_code, 0)
            self.assertEqual(summary["conformance"], "PASS")
            self.assertTrue(Path(summary["result_path"]).is_file())
            self.assertFalse(summary["production_eligible"])
            self.assertNotIn(
                "fixture-secret-never-persist",
                conformance_output.getvalue(),
            )


if __name__ == "__main__":
    unittest.main()
