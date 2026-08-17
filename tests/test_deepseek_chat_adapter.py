from __future__ import annotations

from datetime import datetime, timedelta, timezone
import http.client
import json
import unittest
from types import SimpleNamespace
from urllib import error as urllib_error

from software_world_model.ai_infrastructure.deepseek_chat_adapter import (
    DEFAULT_DEEPSEEK_ACTUAL_MODEL_FINGERPRINT,
    DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
    DEFAULT_DEEPSEEK_MODEL,
    DEFAULT_DEEPSEEK_OPENAI_BASE_URL,
    DeepSeekChatCompletionsNoToolsAdapter,
    DeepSeekModelConfiguration,
    RecordingDeepSeekChatCompletionsTransport,
    UrllibDeepSeekChatTransport,
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


class FailingOpener:
    def open(self, request, timeout):
        raise urllib_error.URLError(ConnectionRefusedError("fixture refusal"))


class RemoteDisconnectingOpener:
    def open(self, request, timeout):
        raise http.client.RemoteDisconnected("fixture remote disconnect")


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
                "response_format",
            },
        )
        self.assertEqual(payload["model"], DEFAULT_DEEPSEEK_MODEL)
        self.assertIn("closed JSON Schema", payload["messages"][0]["content"])
        self.assertIn('"additionalProperties":false', payload["messages"][0]["content"])
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["thinking"], {"type": "disabled"})
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

    def test_transport_classifies_network_failures(self) -> None:
        cases = (
            (FailingOpener(), "CONNECTION_REFUSED"),
            (RemoteDisconnectingOpener(), "REMOTE_DISCONNECTED"),
        )
        for opener, expected in cases:
            transport = UrllibDeepSeekChatTransport(
                api_key_resolver=lambda: "fixture-key",
                opener=opener,
            )
            with self.subTest(expected=expected), self.assertRaises(ProviderOutcomeUnknown) as raised:
                transport.post_json(
                    endpoint=DEFAULT_DEEPSEEK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id="fixture-request",
                    timeout_milliseconds=1000,
                )
            self.assertEqual(raised.exception.reason_code, expected)

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
