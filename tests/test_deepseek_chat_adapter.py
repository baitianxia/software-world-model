from __future__ import annotations

from datetime import datetime, timedelta, timezone
import http.client
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT,
    DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
    DEFAULT_DEEPSEEK_MODEL,
    DEFAULT_DEEPSEEK_OPENAI_BASE_URL,
    DEFAULT_DEEPSEEK_TEMPERATURE,
    DeepSeekChatCompletionsNoToolsAdapter,
    DeepSeekModelConfiguration,
    PersistentDeepSeekChatTransport,
    RecordingDeepSeekChatCompletionsTransport,
    verify_deepseek_transport_session_audit,
)
from software_world_model.ai_infrastructure.model_gateway import (
    AdapterConformanceLevel,
    ProviderOutputRejected,
    ProviderOutcomeUnknown,
    ProviderRequest,
    RenderedMessage,
    ReplayClassification,
)
from software_world_model.ai_infrastructure.openai_responses_adapter import (
    OutputSchemaDefinition,
    ProviderHTTPResponse,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of


class StubTransport:
    def __init__(self, response: ProviderHTTPResponse) -> None:
        self.response = response
        self.calls = 0

    def post_json(self, **arguments):
        self.calls += 1
        return self.response


class _Connection:
    def __init__(self, *, response=None) -> None:
        self.timeout = None
        self.response = response or _ConnectionResponse()
        self.sent = b""
        self.closed = False

    def settimeout(self, value) -> None:
        self.timeout = value

    def getpeercert(self, *, binary_form=False):
        return b"fixture-certificate" if binary_form else {}

    def sendall(self, value: bytes) -> None:
        self.sent += value

    def close(self) -> None:
        self.closed = True


class _ConnectionResponse:
    status = 200
    will_close = False

    def __init__(
        self,
        *,
        body=b"{}",
        headers=None,
        begin_error=None,
        will_close=False,
    ) -> None:
        self._body = body
        self._headers = dict(headers or {"Connection": "keep-alive"})
        self._begin_error = begin_error
        self.will_close = will_close

    def begin(self) -> None:
        if self._begin_error is not None:
            raise self._begin_error

    def read(self, maximum) -> bytes:
        self.maximum = maximum
        return self._body

    def getheaders(self):
        return list(self._headers.items())


def success_response(
    *,
    content: str = '{"answer":"ok"}',
    model: str = DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT,
    finish_reason: str = "stop",
    message_extensions: dict[str, object] | None = None,
    usage: object = None,
) -> ProviderHTTPResponse:
    if usage is None:
        usage = {
            "prompt_tokens": 12,
            "completion_tokens": 4,
            "total_tokens": 16,
            "prompt_cache_hit_tokens": 0,
            "prompt_cache_miss_tokens": 12,
        }
    message = {"role": "assistant", "content": content}
    message.update(message_extensions or {})
    return ProviderHTTPResponse(
        status_code=200,
        headers={"X-Request-Id": "deepseek-request-1"},
        body=json.dumps(
            {
                "id": "chatcmpl_deepseek_1",
                "object": "chat.completion",
                "created": 1786924800,
                "model": model,
                "system_fingerprint": "fp_fixture",
                "choices": [
                    {
                        "index": 0,
                        "message": message,
                        "finish_reason": finish_reason,
                    }
                ],
                "usage": usage,
            }
        ).encode("utf-8"),
    )


class DeepSeekChatAdapterTests(unittest.TestCase):
    def request(self, **changes) -> ProviderRequest:
        values = {
            "model_ref": DEFAULT_DEEPSEEK_MODEL,
            "messages": (
                RenderedMessage(
                    "system",
                    "Return JSON.",
                    "instruction",
                    digest_of("Return JSON."),
                ),
                RenderedMessage(
                    "user",
                    "Authorized facts only.",
                    "facts",
                    digest_of("Authorized facts only."),
                ),
            ),
            "output_schema_ref": "answer@1",
            "tools": (),
            "store": False,
            "stream": False,
            "max_output_tokens": 128,
            "timeout_milliseconds": 2500,
            "metadata": (("manifest_digest", "sha256:" + "a" * 64),),
            "digest": Digest("sha256:" + "b" * 64),
        }
        values.update(changes)
        return ProviderRequest(**values)

    def adapter(self, response: ProviderHTTPResponse, **changes):
        stub = StubTransport(response)
        recording = RecordingDeepSeekChatCompletionsTransport(stub)
        values = {
            "transport": recording,
            "configuration": DeepSeekModelConfiguration(),
            "output_schemas": {
                "answer@1": OutputSchemaDefinition(
                    "answer",
                    {
                        "type": "object",
                        "properties": {"answer": {"type": "string"}},
                        "required": ["answer"],
                        "additionalProperties": False,
                    },
                )
            },
            "pinned_models": frozenset(
                {DEFAULT_DEEPSEEK_MODEL, DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT}
            ),
        }
        values.update(changes)
        return DeepSeekChatCompletionsNoToolsAdapter(**values), stub, recording

    def test_configuration_is_sanitized_and_uses_environment_reference(self) -> None:
        configuration = DeepSeekModelConfiguration()

        missing = configuration.public_status({})
        present = configuration.public_status(
            {"DEEPSEEK_API_KEY": "do-not-expose"}
        )

        self.assertEqual(
            configuration.endpoint,
            DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
        )
        self.assertEqual(configuration.base_url, DEFAULT_DEEPSEEK_OPENAI_BASE_URL)
        self.assertEqual(configuration.model_ref, "deepseek-v4-pro")
        self.assertEqual(missing["secret_reference"], "env:DEEPSEEK_API_KEY")
        self.assertEqual(missing["thinking_mode"], "DISABLED")
        self.assertEqual(missing["temperature"], DEFAULT_DEEPSEEK_TEMPERATURE)
        self.assertEqual(
            configuration.adapter_version,
            "deepseek-chat-completions-no-tools@5",
        )
        self.assertEqual(
            missing["connection_policy"],
            "PERSISTENT_VERIFIED_TLS_HTTP11_KEEP_ALIVE@1",
        )
        self.assertEqual(missing["maximum_pre_dispatch_tls_handshakes"], 3)
        self.assertEqual(
            missing["credential_resolution_policy"],
            "AFTER_VERIFIED_TLS_BEFORE_EACH_HTTP_DISPATCH",
        )
        self.assertFalse(missing["request_retry_allowed"])
        self.assertFalse(missing["credential_configured"])
        self.assertTrue(present["credential_configured"])
        self.assertNotIn("do-not-expose", json.dumps(present))

    def test_flash_is_supported_but_deprecated_aliases_are_rejected(self) -> None:
        flash = DeepSeekModelConfiguration(
            model_ref="deepseek-v4-flash",
            actual_model_fingerprint="deepseek-v4-flash",
        )
        self.assertEqual(flash.model_ref, "deepseek-v4-flash")

        for model in ("deepseek-chat", "deepseek-reasoner", "unknown"):
            with self.subTest(model=model), self.assertRaises(DomainError) as raised:
                DeepSeekModelConfiguration(
                    model_ref=model,
                    actual_model_fingerprint=model,
                )
            self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

        with self.assertRaises(DomainError) as raised:
            DeepSeekModelConfiguration(
                model_ref="deepseek-v4-pro",
                actual_model_fingerprint="deepseek-v4-flash",
            )
        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_wire_request_uses_the_deepseek_json_no_tools_contract(self) -> None:
        adapter, stub, recording = self.adapter(success_response())

        result = adapter.invoke(self.request())

        payload = json.loads(recording.requests[0].body)
        self.assertEqual(
            set(payload),
            {
                "model",
                "messages",
                "stream",
                "max_tokens",
                "thinking",
                "temperature",
                "response_format",
            },
        )
        self.assertEqual(payload["model"], DEFAULT_DEEPSEEK_MODEL)
        self.assertEqual(len(payload["messages"]), 2)
        self.assertEqual(
            [message["role"] for message in payload["messages"]],
            ["system", "user"],
        )
        self.assertIn("closed JSON Schema", payload["messages"][0]["content"])
        self.assertIn('"additionalProperties":false', payload["messages"][0]["content"])
        self.assertIn("TASK AND SEMANTIC AUTHORITY", payload["messages"][0]["content"])
        self.assertIn("Return JSON.", payload["messages"][0]["content"])
        self.assertNotIn(
            "PROVIDER EXECUTION ADAPTATION",
            payload["messages"][0]["content"],
        )
        self.assertEqual(payload["messages"][1]["content"], "Authorized facts only.")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["thinking"], {"type": "disabled"})
        self.assertEqual(payload["temperature"], 0)
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertNotIn("tools", payload)
        self.assertNotIn("store", payload)
        self.assertEqual(stub.calls, 1)
        self.assertEqual(result.provider_request_id, "deepseek-request-1")
        self.assertEqual(result.replay_classification, ReplayClassification.PINNED)
        self.assertTrue(result.usage_complete)

    def test_model_mismatch_is_rejected_before_dispatch(self) -> None:
        adapter, stub, _ = self.adapter(success_response())

        with self.assertRaises(DomainError) as raised:
            adapter.invoke(self.request(model_ref="deepseek-v4-flash"))

        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)
        self.assertEqual(stub.calls, 0)

    def test_user_only_request_gets_one_schema_system_without_reordering(self) -> None:
        adapter, _, recording = self.adapter(success_response())
        user = RenderedMessage(
            "user",
            "Authorized facts only.",
            "facts",
            digest_of("Authorized facts only."),
        )

        adapter.invoke(self.request(messages=(user,)))

        messages = json.loads(recording.requests[0].body)["messages"]
        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        self.assertIn("closed JSON Schema", messages[0]["content"])
        self.assertNotIn("TASK AND SEMANTIC AUTHORITY", messages[0]["content"])
        self.assertEqual(messages[1]["content"], user.content)

    def test_investigation_schema_adds_lossless_lexical_coverage_adaptation(self) -> None:
        adapter, _, recording = self.adapter(
            success_response(content='{"search_terms":["authentication","methods"]}'),
            output_schemas={
                "investigation@1": OutputSchemaDefinition(
                    "java_bounded_implementation_investigation_intent",
                    {
                        "type": "object",
                        "properties": {
                            "search_terms": {
                                "type": "array",
                                "items": {"type": "string"},
                            }
                        },
                        "required": ["search_terms"],
                        "additionalProperties": False,
                    },
                )
            },
        )

        adapter.invoke(self.request(output_schema_ref="investigation@1"))

        messages = json.loads(recording.requests[0].body)["messages"]
        self.assertEqual([message["role"] for message in messages], ["system", "user"])
        authority = messages[0]["content"]
        self.assertEqual(authority.count("PROVIDER EXECUTION ADAPTATION"), 1)
        self.assertIn("independent lexical-coverage list", authority)
        self.assertIn("Do not count operation or evidence_requests", authority)
        self.assertIn("Never add a concept absent from original_question", authority)

    def test_reasoning_tool_and_incomplete_outputs_fail_closed(self) -> None:
        cases = (
            (
                success_response(
                    message_extensions={"reasoning_content": "hidden reasoning"}
                ),
                ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
            ),
            (
                success_response(
                    message_extensions={"tool_calls": [{"id": "call-1"}]}
                ),
                ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
            ),
            (
                success_response(finish_reason="length"),
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
            ),
        )
        for response, expected in cases:
            adapter, _, _ = self.adapter(response)
            with self.subTest(expected=expected), self.assertRaises(DomainError) as raised:
                adapter.invoke(self.request())
            self.assertEqual(raised.exception.code, expected)
            if expected is ErrorCode.STRUCTURED_OUTPUT_INVALID:
                self.assertIsInstance(raised.exception, ProviderOutputRejected)

    def test_schema_and_json_shape_are_revalidated(self) -> None:
        adapter, _, _ = self.adapter(
            success_response(content='{"answer":"ok","extra":true}')
        )
        with self.assertRaises(DomainError) as raised:
            adapter.invoke(self.request())
        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

        deferred, _, _ = self.adapter(
            success_response(content='{"unexpected":"value"}'),
            enforce_output_schema=False,
        )
        self.assertEqual(
            deferred.invoke(self.request()).output_text,
            '{"unexpected":"value"}',
        )

    def test_exact_json_markdown_fence_is_narrowly_normalized(self) -> None:
        adapter, _, _ = self.adapter(
            success_response(content='```json\n{"answer":"ok"}\n```')
        )
        result = adapter.invoke(self.request())
        self.assertEqual(result.output_text, '{"answer":"ok"}')
        self.assertEqual(result.output_normalization, "MARKDOWN_JSON_FENCE_V1")

    def test_live_level_requires_current_exact_deepseek_qualification(self) -> None:
        configuration = DeepSeekModelConfiguration()
        valid = SimpleNamespace(
            result_ref="CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:" + "a" * 64,
            qualified_model_fingerprints=configuration.qualified_model_identities,
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
        )
        adapter, _, _ = self.adapter(success_response(), live_qualification=valid)
        self.assertEqual(
            adapter.capabilities.conformance_level,
            AdapterConformanceLevel.LIVE_CURRENT,
        )

        wrong = SimpleNamespace(
            result_ref="CC-ARK-CHAT-NO-TOOLS-001:sha256:" + "a" * 64,
            qualified_model_fingerprints=configuration.qualified_model_identities,
            valid_until=datetime.now(timezone.utc) + timedelta(days=1),
        )
        with self.assertRaises(DomainError) as raised:
            self.adapter(success_response(), live_qualification=wrong)
        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_configuration_rejects_endpoint_or_port_drift(self) -> None:
        endpoints = (
            "https://example.com/chat/completions",
            "https://api.deepseek.com/v1/chat/completions",
            "https://api.deepseek.com:444/chat/completions",
            "https://api.deepseek.com/chat/completions?target=other",
        )
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint), self.assertRaises(DomainError) as raised:
                DeepSeekModelConfiguration(endpoint=endpoint)
            self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_configuration_rejects_temperature_drift(self) -> None:
        self.assertEqual(DeepSeekModelConfiguration().temperature, 0)

        for temperature in (
            True,
            -1,
            1,
            0.0,
            0.5,
            float("nan"),
            float("inf"),
            "0",
        ):
            with self.subTest(temperature=temperature), self.assertRaises(
                DomainError
            ) as raised:
                DeepSeekModelConfiguration(temperature=temperature)  # type: ignore[arg-type]
            self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_transport_retries_only_credential_free_tls_acquisition(self) -> None:
        failures = [ConnectionRefusedError("fixture refusal") for _ in range(3)]
        credential_reads = 0

        def resolve() -> str:
            nonlocal credential_reads
            credential_reads += 1
            return "fixture-key"

        transport = PersistentDeepSeekChatTransport(
            api_key_resolver=resolve,
            connection_factory=lambda _: (_ for _ in ()).throw(failures.pop(0)),
        )
        with self.assertRaises(DomainError) as raised:
            transport.post_json(
                endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                body=b"{}",
                client_request_id="fixture-request",
                timeout_milliseconds=1000,
            )

        self.assertEqual(raised.exception.code, ErrorCode.LIVE_INTEGRATION_HELD)
        self.assertEqual(credential_reads, 0)
        self.assertEqual(transport.tls_handshake_attempt_count, 3)
        self.assertEqual(transport.http_dispatch_count, 0)
        self.assertEqual(
            transport.pre_dispatch_tls_failure_codes,
            ("CONNECTION_REFUSED",) * 3,
        )

    def test_transport_reuses_tls_but_never_retries_http_dispatch(self) -> None:
        connection = _Connection()
        factory_calls = 0

        def factory(_):
            nonlocal factory_calls
            factory_calls += 1
            return connection

        transport = PersistentDeepSeekChatTransport(
            api_key_resolver=lambda: "fixture-key",
            connection_factory=factory,
        )
        with patch(
            "software_world_model.ai_infrastructure.deepseek_chat_adapter.http.client.HTTPResponse",
            side_effect=lambda active: active.response,
        ):
            for ordinal in range(2):
                transport.post_json(
                    endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id=f"fixture-request-{ordinal}",
                    timeout_milliseconds=1000,
                )

        self.assertEqual(factory_calls, 1)
        self.assertEqual(transport.tls_handshake_attempt_count, 1)
        self.assertEqual(transport.tls_handshake_success_count, 1)
        self.assertEqual(transport.connection_reuse_count, 1)
        self.assertEqual(transport.http_dispatch_count, 2)
        self.assertEqual(connection.sent.count(b"Connection: keep-alive\r\n"), 2)
        self.assertEqual(
            transport.session_audit()["connection_reuse_count"], 1
        )

        failing = _Connection(
            response=_ConnectionResponse(
                begin_error=http.client.RemoteDisconnected("fixture disconnect")
            )
        )
        failed_transport = PersistentDeepSeekChatTransport(
            api_key_resolver=lambda: "fixture-key",
            connection_factory=lambda _: failing,
        )
        with (
            patch(
                "software_world_model.ai_infrastructure.deepseek_chat_adapter.http.client.HTTPResponse",
                side_effect=lambda active: active.response,
            ),
            self.assertRaises(ProviderOutcomeUnknown) as raised,
        ):
            failed_transport.post_json(
                endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                body=b"{}",
                client_request_id="fixture-unknown",
                timeout_milliseconds=1000,
            )
        self.assertEqual(raised.exception.reason_code, "REMOTE_DISCONNECTED")
        self.assertEqual(failed_transport.tls_handshake_attempt_count, 1)
        self.assertEqual(failed_transport.http_dispatch_count, 1)
        self.assertEqual(
            failed_transport.session_audit()[
                "post_dispatch_outcome_unknown_count"
            ],
            1,
        )

    def test_transport_reacquires_only_for_a_later_request_after_clean_close(self) -> None:
        connections = [
            _Connection(
                response=_ConnectionResponse(
                    headers={"Connection": "close"},
                    will_close=True,
                )
            ),
            _Connection(),
        ]
        transport = PersistentDeepSeekChatTransport(
            api_key_resolver=lambda: "fixture-key",
            connection_factory=lambda _: connections.pop(0),
        )
        with patch(
            "software_world_model.ai_infrastructure.deepseek_chat_adapter.http.client.HTTPResponse",
            side_effect=lambda active: active.response,
        ):
            for ordinal in range(2):
                transport.post_json(
                    endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id=f"fixture-clean-close-{ordinal}",
                    timeout_milliseconds=1000,
                )

        audit = transport.session_audit()
        self.assertEqual(audit["tls_handshake_attempt_count"], 2)
        self.assertEqual(audit["tls_handshake_success_count"], 2)
        self.assertEqual(audit["http_dispatch_count"], 2)
        self.assertEqual(audit["connection_reuse_count"], 0)

    def test_transport_session_audit_rejects_dispatch_without_verified_tls(self) -> None:
        audit = PersistentDeepSeekChatTransport(
            api_key_resolver=lambda: "fixture-key",
            connection_factory=lambda _: _Connection(),
        ).session_audit()
        audit["http_dispatch_count"] = 1
        audit["credential_resolution_count"] = 1
        audit["credential_resolution_success_count"] = 1

        with self.assertRaises(DomainError) as raised:
            verify_deepseek_transport_session_audit(audit)

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_safe_http_error_fields_are_projected_without_message(self) -> None:
        response = ProviderHTTPResponse(
            401,
            {"X-Request-Id": "request-safe-1"},
            json.dumps(
                {
                    "error": {
                        "code": "invalid_api_key",
                        "type": "authentication_error",
                        "message": "sensitive diagnostic",
                    }
                }
            ).encode("utf-8"),
        )
        adapter, _, _ = self.adapter(response)

        with self.assertRaises(DomainError) as raised:
            adapter.invoke(self.request())

        self.assertEqual(raised.exception.code, ErrorCode.PROVIDER_HTTP_ERROR)
        self.assertEqual(raised.exception.details["http_status"], 401)
        self.assertEqual(
            raised.exception.details["provider_error_code"],
            "invalid_api_key",
        )
        self.assertEqual(
            raised.exception.details["provider_error_type"],
            "authentication_error",
        )
        self.assertNotIn("message", raised.exception.details)


if __name__ == "__main__":
    unittest.main()
