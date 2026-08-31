from __future__ import annotations

from datetime import datetime, timedelta, timezone
import http.client
import json
from io import StringIO
from types import SimpleNamespace
import unittest
from unittest import mock

from software_world_model.ai_infrastructure import (
    AdapterConformanceLevel,
    DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT,
    DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
    DEFAULT_VOLCENGINE_ARK_CONNECTION_POLICY,
    DEFAULT_VOLCENGINE_ARK_MODEL,
    DEFAULT_VOLCENGINE_ARK_OPENAI_BASE_URL,
    DirectVerifiedVolcengineArkChatTransport,
    OutputSchemaDefinition,
    ProviderHTTPResponse,
    ProviderOutcomeUnknown,
    ProviderOutputRejected,
    ProviderUnavailable,
    RecordingChatCompletionsTransport,
    ReplayClassification,
    VolcengineArkChatCompletionsNoToolsAdapter,
    VolcengineArkModelConfiguration,
    verify_ark_transport_session_audit,
)
from software_world_model.ai_infrastructure.model_gateway import ProviderRequest, RenderedMessage
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of
from software_world_model.ai_infrastructure.direct_https import build_direct_https_opener
from software_world_model.interface.provider_cli import main as provider_main


class StubTransport:
    def __init__(self, response: ProviderHTTPResponse) -> None:
        self.response = response
        self.calls = 0

    def post_json(self, **arguments):
        self.calls += 1
        return self.response


class _Connection:
    def __init__(self, *, response=None) -> None:
        self.response = response or _ConnectionResponse()
        self.sent = b""
        self.closed = False

    def getpeercert(self, *, binary_form=False):
        return b"fixture-ark-certificate" if binary_form else {}

    def sendall(self, value: bytes) -> None:
        self.sent += value

    def close(self) -> None:
        self.closed = True


class _ConnectionResponse:
    status = 200

    def __init__(self, *, body=b"{}", headers=None, begin_error=None) -> None:
        self._body = body
        self._headers = dict(headers or {"Connection": "close"})
        self._begin_error = begin_error

    def begin(self) -> None:
        if self._begin_error is not None:
            raise self._begin_error

    def read(self, maximum) -> bytes:
        self.maximum = maximum
        return self._body

    def getheaders(self):
        return list(self._headers.items())


class UnknownOutcomeTransport:
    def post_json(self, **arguments):
        raise ProviderOutcomeUnknown("fixture unknown", reason_code="CONNECTION_REFUSED")


_DEFAULT_USAGE = object()


def success_response(
    *,
    content='{"answer":"ok"}',
    model=DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT,
    usage=_DEFAULT_USAGE,
    finish_reason="stop",
    delta_extra=None,
    response_id="chatcmpl_1",
):
    if usage is _DEFAULT_USAGE:
        usage = {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16}
    content_delta = {"content": content}
    content_delta.update(delta_extra or {})
    chunks = [
        {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": 1785974400,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": ""},
                    "finish_reason": None,
                }
            ],
            "usage": None,
        },
        {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": 1785974400,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": content_delta,
                    "finish_reason": None,
                }
            ],
            "usage": None,
        },
        {
            "id": response_id,
            "object": "chat.completion.chunk",
            "created": 1785974400,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": finish_reason,
                }
            ],
            "usage": None,
        },
    ]
    if usage is not None:
        chunks.append(
            {
                "id": response_id,
                "object": "chat.completion.chunk",
                "created": 1785974400,
                "model": model,
                "choices": [],
                "usage": usage,
            }
        )
    body = b"".join(
        b"data: "
        + json.dumps(chunk, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        + b"\n\n"
        for chunk in chunks
    ) + b"data: [DONE]\n\n"
    return ProviderHTTPResponse(
        status_code=200,
        headers={
            "X-Tt-Logid": "ark-request-1",
            "Content-Type": "text/event-stream; charset=utf-8",
        },
        body=body,
    )


class VolcengineArkChatAdapterTests(unittest.TestCase):
    def request(self, **changes):
        values = {
            "model_ref": DEFAULT_VOLCENGINE_ARK_MODEL,
            "messages": (
                RenderedMessage("system", "Return JSON.", "instruction", digest_of("Return JSON.")),
                RenderedMessage("user", "Authorized facts only.", "facts", digest_of("Authorized facts only.")),
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

    def adapter(self, response, **changes):
        stub = StubTransport(response)
        recording = RecordingChatCompletionsTransport(stub)
        values = {
            "transport": recording,
            "configuration": VolcengineArkModelConfiguration(),
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
                {
                    DEFAULT_VOLCENGINE_ARK_MODEL,
                    DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT,
                }
            ),
        }
        values.update(changes)
        return VolcengineArkChatCompletionsNoToolsAdapter(**values), stub, recording

    def test_configuration_is_sanitized_and_uses_environment_reference(self) -> None:
        configuration = VolcengineArkModelConfiguration()

        missing = configuration.public_status({})
        present = configuration.public_status({"ARK_API_KEY": "do-not-expose"})

        self.assertEqual(configuration.endpoint, DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT)
        self.assertEqual(configuration.base_url, DEFAULT_VOLCENGINE_ARK_OPENAI_BASE_URL)
        self.assertEqual(missing["base_url"], DEFAULT_VOLCENGINE_ARK_OPENAI_BASE_URL)
        self.assertEqual(configuration.model_ref, DEFAULT_VOLCENGINE_ARK_MODEL)
        self.assertEqual(
            configuration.actual_model_fingerprint,
            DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT,
        )
        self.assertEqual(missing["secret_reference"], "env:ARK_API_KEY")
        self.assertFalse(missing["credential_configured"])
        self.assertTrue(present["credential_configured"])
        self.assertNotIn("do-not-expose", json.dumps(present))

    def test_wire_request_is_openai_compatible_stateless_no_tools_and_strict(self) -> None:
        adapter, stub, recording = self.adapter(success_response())

        result = adapter.invoke(self.request())

        payload = json.loads(recording.requests[0].body)
        self.assertEqual(recording.requests[0].endpoint, DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT)
        self.assertEqual(payload["model"], DEFAULT_VOLCENGINE_ARK_MODEL)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertIn("closed JSON Schema", payload["messages"][0]["content"])
        self.assertIn('"additionalProperties":false', payload["messages"][0]["content"])
        self.assertEqual(payload["messages"][1], {"role": "system", "content": "Return JSON."})
        self.assertEqual(payload["tools"], [])
        self.assertEqual(payload["tool_choice"], "none")
        self.assertFalse(payload["parallel_tool_calls"])
        self.assertTrue(payload["stream"])
        self.assertEqual(payload["stream_options"], {"include_usage": True})
        self.assertEqual(payload["n"], 1)
        self.assertNotIn("thinking", payload)
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertNotIn("store", payload)
        self.assertNotIn("metadata", payload)
        self.assertEqual(stub.calls, 1)
        self.assertEqual(result.provider_request_id, "ark-request-1")
        self.assertEqual(result.replay_classification, ReplayClassification.PINNED)
        self.assertTrue(result.usage_complete)
        self.assertEqual(result.output_normalization, "IDENTITY")

    def test_stream_reassembles_content_and_discards_reasoning_channel(self) -> None:
        adapter, _, _ = self.adapter(
            success_response(
                delta_extra={"reasoning_content": "private reasoning"}
            )
        )

        result = adapter.invoke(self.request())

        self.assertEqual(result.output_text, '{"answer":"ok"}')
        self.assertNotIn("private reasoning", result.output_text)

    def test_stream_requires_consistent_identity_terminal_marker_and_content_type(self) -> None:
        valid = success_response()
        inconsistent_body = valid.body.replace(
            b'"id":"chatcmpl_1"', b'"id":"chatcmpl_2"', 1
        )
        cases = (
            ProviderHTTPResponse(200, valid.headers, valid.body.removesuffix(b"data: [DONE]\n\n")),
            ProviderHTTPResponse(200, valid.headers, inconsistent_body),
            ProviderHTTPResponse(200, {"Content-Type": "application/json"}, valid.body),
        )
        for response in cases:
            adapter, _, _ = self.adapter(response)
            with self.subTest(response=response), self.assertRaises(DomainError) as raised:
                adapter.invoke(self.request())
            self.assertEqual(raised.exception.code, ErrorCode.PROVIDER_RESPONSE_INVALID)

    def test_exact_json_markdown_fence_is_normalized_before_schema_validation(self) -> None:
        adapter, _, _ = self.adapter(
            success_response(content='```json\n{"answer":"ok"}\n```')
        )

        result = adapter.invoke(self.request())

        self.assertEqual(result.output_text, '{"answer":"ok"}')
        self.assertEqual(result.output_normalization, "MARKDOWN_JSON_FENCE_V1")

    def test_short_non_structural_prefix_before_fence_is_normalized(self) -> None:
        adapter, _, _ = self.adapter(
            success_response(content='Result:\n```json\n{"answer":"ok"}\n```')
        )

        result = adapter.invoke(self.request())

        self.assertEqual(result.output_text, '{"answer":"ok"}')
        self.assertEqual(
            result.output_normalization,
            "MARKDOWN_JSON_FENCE_WITH_PREFIX_V1",
        )

    def test_caller_may_defer_closed_schema_validation_but_not_json_object_shape(self) -> None:
        adapter, _, _ = self.adapter(
            success_response(content='{"unexpected":"value"}'),
            enforce_output_schema=False,
        )

        result = adapter.invoke(self.request())

        self.assertEqual(result.output_text, '{"unexpected":"value"}')

        non_object, _, _ = self.adapter(
            success_response(content='["not-an-object"]'),
            enforce_output_schema=False,
        )
        with self.assertRaises(DomainError) as raised:
            non_object.invoke(self.request())
        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

    def test_unsafe_markdown_wrappers_fail_closed(self) -> None:
        contents = (
            '```json\n{"answer":"ok"}\n```\nResult.',
            '```json\n{"answer":"ok"}\n```\n```json\n{"answer":"ok"}\n```',
            '```JSON\n{"answer":"ok"}\n```',
            'Candidate {object}:\n```json\n{"answer":"ok"}\n```',
            f'{"x" * 513}\n```json\n{{"answer":"ok"}}\n```',
        )
        for content in contents:
            adapter, _, _ = self.adapter(success_response(content=content))
            with self.subTest(content=content), self.assertRaises(DomainError) as raised:
                adapter.invoke(self.request())
            self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

    def test_requested_model_must_match_frozen_configuration(self) -> None:
        adapter, stub, _ = self.adapter(success_response())
        with self.assertRaises(DomainError) as raised:
            adapter.invoke(self.request(model_ref="another-model"))
        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)
        self.assertEqual(stub.calls, 0)

    def test_tool_output_refusal_and_incomplete_choice_fail_closed(self) -> None:
        cases = (
            (
                success_response(delta_extra={"tool_calls": [{"id": "call_1"}]}),
                "stop",
                ErrorCode.PROVIDER_OUTPUT_FORBIDDEN,
            ),
            (
                success_response(content="", delta_extra={"refusal": "no"}),
                "stop",
                ErrorCode.PROVIDER_REFUSAL,
            ),
            (
                success_response(content='{"answer":"partial"}', finish_reason="length"),
                "length",
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
            ),
        )
        for response, finish_reason, expected in cases:
            adapter, _, _ = self.adapter(response)
            with self.subTest(expected=expected), self.assertRaises(DomainError) as raised:
                adapter.invoke(self.request())
            self.assertEqual(raised.exception.code, expected)
            if finish_reason == "length":
                self.assertIsInstance(raised.exception, ProviderOutputRejected)
                self.assertEqual(raised.exception.response.termination_reason, "length")
                self.assertTrue(raised.exception.response.usage_complete)

    def test_application_revalidates_closed_schema(self) -> None:
        adapter, _, _ = self.adapter(success_response(content='{"answer":"ok","extra":true}'))
        with self.assertRaises(DomainError) as raised:
            adapter.invoke(self.request())
        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

    def test_inconsistent_or_missing_usage_is_not_reported_as_zero(self) -> None:
        for usage in (None, {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 99}):
            response = success_response(usage=usage)
            adapter, _, _ = self.adapter(response)
            result = adapter.invoke(self.request())
            self.assertFalse(result.usage_complete)
            self.assertIsNone(result.input_tokens)
            self.assertIsNone(result.output_tokens)

    def test_live_level_requires_current_verified_exact_model_qualification(self) -> None:
        with self.assertRaises(DomainError) as raised:
            self.adapter(
                success_response(),
                live_qualification=SimpleNamespace(
                    result_ref="CC-ARK-CHAT-NO-TOOLS-001:sha256:" + "a" * 64,
                    qualified_model_fingerprints=("another-model",),
                    valid_until=datetime.now(timezone.utc) + timedelta(days=1),
                ),
            )
        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_configuration_rejects_secret_exfiltration_endpoint(self) -> None:
        with self.assertRaises(DomainError) as raised:
            VolcengineArkModelConfiguration(endpoint="https://example.com/api/coding/v3/chat/completions")
        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_configuration_rejects_unexpanded_coding_plan_base_url(self) -> None:
        with self.assertRaises(DomainError) as raised:
            VolcengineArkModelConfiguration(
                endpoint=DEFAULT_VOLCENGINE_ARK_OPENAI_BASE_URL
            )
        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_provider_cli_status_and_probe_never_expose_credential(self) -> None:
        status_output = StringIO()
        status_code = provider_main(
            ["status"],
            stdout=status_output,
            environment={"ARK_API_KEY": "do-not-expose"},
        )
        status = json.loads(status_output.getvalue())
        self.assertEqual(status_code, 0)
        self.assertTrue(status["credential_configured"])
        self.assertNotIn("do-not-expose", status_output.getvalue())

        probe_output = StringIO()
        probe_code = provider_main(
            ["probe"],
            stdout=probe_output,
            environment={"ARK_API_KEY": "do-not-expose"},
            transport=StubTransport(
                success_response(content='{"status":"ok"}')
            ),
        )
        probe = json.loads(probe_output.getvalue())
        self.assertEqual(probe_code, 0)
        self.assertEqual(probe["transport_probe"], "PASS")
        self.assertFalse(probe["production_eligible"])
        self.assertNotIn("do-not-expose", probe_output.getvalue())

    def test_transport_resolves_credential_only_after_verified_tls(self) -> None:
        events = []
        connection = _Connection()

        def factory(_):
            events.append("verified-tls")
            return connection

        def resolve_key():
            events.append("credential")
            return "fixture-key"

        transport = DirectVerifiedVolcengineArkChatTransport(
            api_key_resolver=resolve_key,
            connection_factory=factory,
        )
        with mock.patch(
            "software_world_model.ai_infrastructure.volcengine_ark_chat_adapter.http.client.HTTPResponse",
            side_effect=lambda active: active.response,
        ):
            response = transport.post_json(
                endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
                body=b"{}",
                client_request_id="fixture-request",
                timeout_milliseconds=1000,
            )

        audit = verify_ark_transport_session_audit(transport.session_audit())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(events, ["verified-tls", "credential"])
        self.assertTrue(connection.closed)
        self.assertIn(b"Authorization: Bearer fixture-key\r\n", connection.sent)
        self.assertIn(b"Accept: text/event-stream\r\n", connection.sent)
        self.assertIn(b"Connection: close\r\n", connection.sent)
        self.assertEqual(audit["connection_policy"], DEFAULT_VOLCENGINE_ARK_CONNECTION_POLICY)
        self.assertEqual(audit["tls_handshake_success_count"], 1)
        self.assertEqual(audit["credential_resolution_success_count"], 1)
        self.assertEqual(audit["http_dispatch_count"], 1)
        self.assertEqual(audit["connection_reuse_count"], 0)
        self.assertEqual(audit["request_retry_count"], 0)

    def test_transport_pre_dispatch_tls_failure_never_reads_credential(self) -> None:
        credential_reads = 0

        def resolve_key():
            nonlocal credential_reads
            credential_reads += 1
            return "fixture-key"

        def fail_connection(_):
            raise ConnectionRefusedError("fixture refusal")

        transport = DirectVerifiedVolcengineArkChatTransport(
            api_key_resolver=resolve_key,
            connection_factory=fail_connection,
        )
        with self.assertRaises(ProviderUnavailable) as raised:
            transport.post_json(
                endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
                body=b"{}",
                client_request_id="fixture-request",
                timeout_milliseconds=1000,
            )
        self.assertEqual(raised.exception.reason_code, "CONNECTION_REFUSED")
        self.assertEqual(credential_reads, 0)
        audit = verify_ark_transport_session_audit(transport.session_audit())
        self.assertEqual(audit["tls_handshake_attempt_count"], 1)
        self.assertEqual(audit["pre_dispatch_tls_handshake_failure_count"], 1)
        self.assertEqual(audit["pre_dispatch_tls_failure_codes"], ["CONNECTION_REFUSED"])
        self.assertEqual(audit["credential_resolution_count"], 0)
        self.assertEqual(audit["http_dispatch_count"], 0)

        output = StringIO()
        code = provider_main(
            ["probe"],
            stdout=output,
            environment={"ARK_API_KEY": "do-not-expose"},
            transport=transport,
        )
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 3)
        self.assertEqual(payload["error"], "PROVIDER_UNAVAILABLE")
        self.assertEqual(payload["reason"], "CONNECTION_REFUSED")
        self.assertNotIn("do-not-expose", output.getvalue())

    def test_transport_uses_a_distinct_verified_session_for_each_request(self) -> None:
        connections = [_Connection(), _Connection()]
        created = []

        def factory(_):
            connection = connections[len(created)]
            created.append(connection)
            return connection

        transport = DirectVerifiedVolcengineArkChatTransport(
            api_key_resolver=lambda: "fixture-key",
            connection_factory=factory,
        )
        with mock.patch(
            "software_world_model.ai_infrastructure.volcengine_ark_chat_adapter.http.client.HTTPResponse",
            side_effect=lambda active: active.response,
        ):
            for ordinal in range(2):
                transport.post_json(
                    endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
                    body=b"{}",
                    client_request_id=f"fixture-request-{ordinal}",
                    timeout_milliseconds=1000,
                )

        audit = verify_ark_transport_session_audit(transport.session_audit())
        self.assertEqual(created, connections)
        self.assertTrue(all(connection.closed for connection in connections))
        self.assertEqual(audit["tls_handshake_attempt_count"], 2)
        self.assertEqual(audit["tls_handshake_success_count"], 2)
        self.assertEqual(audit["http_dispatch_count"], 2)
        self.assertEqual(audit["connection_reuse_count"], 0)

    def test_transport_classifies_remote_disconnect_as_unknown_outcome(self) -> None:
        connection = _Connection(
            response=_ConnectionResponse(
                begin_error=http.client.RemoteDisconnected(
                    "fixture remote disconnect"
                )
            )
        )
        transport = DirectVerifiedVolcengineArkChatTransport(
            api_key_resolver=lambda: "fixture-key",
            connection_factory=lambda _: connection,
        )
        with (
            mock.patch(
                "software_world_model.ai_infrastructure.volcengine_ark_chat_adapter.http.client.HTTPResponse",
                side_effect=lambda active: active.response,
            ),
            self.assertRaises(ProviderOutcomeUnknown) as raised,
        ):
            transport.post_json(
                endpoint=DEFAULT_VOLCENGINE_ARK_CHAT_COMPLETIONS_ENDPOINT,
                body=b"{}",
                client_request_id="fixture-request",
                timeout_milliseconds=1000,
            )
        self.assertEqual(raised.exception.reason_code, "REMOTE_DISCONNECTED")
        self.assertTrue(connection.closed)
        audit = verify_ark_transport_session_audit(transport.session_audit())
        self.assertEqual(audit["http_dispatch_count"], 1)
        self.assertEqual(audit["post_dispatch_outcome_unknown_count"], 1)
        self.assertEqual(audit["post_dispatch_failure_codes"], ["REMOTE_DISCONNECTED"])

    def test_transport_session_audit_rejects_dispatch_without_verified_tls(self) -> None:
        audit = DirectVerifiedVolcengineArkChatTransport(
            api_key_resolver=lambda: "fixture-key",
            connection_factory=lambda _: _Connection(),
        ).session_audit()
        audit["http_dispatch_count"] = 1
        audit["credential_resolution_success_count"] = 1

        with self.assertRaises(DomainError) as raised:
            verify_ark_transport_session_audit(audit)

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_direct_https_ignores_proxy_and_loads_system_ca_fallback(self) -> None:
        context = mock.Mock()
        expected_opener = object()
        with (
            mock.patch(
                "software_world_model.ai_infrastructure.direct_https.ssl.create_default_context",
                return_value=context,
            ),
            mock.patch(
                "software_world_model.ai_infrastructure.direct_https.ssl.get_default_verify_paths",
                return_value=SimpleNamespace(cafile=None, capath=None),
            ),
            mock.patch(
                "software_world_model.ai_infrastructure.direct_https.os.path.isfile",
                side_effect=lambda path: path == "/etc/ssl/cert.pem",
            ),
            mock.patch(
                "software_world_model.ai_infrastructure.direct_https.urllib_request.build_opener",
                return_value=expected_opener,
            ) as opener_builder,
        ):
            actual_opener = build_direct_https_opener()

        self.assertIs(actual_opener, expected_opener)
        context.load_verify_locations.assert_called_once_with(cafile="/etc/ssl/cert.pem")
        proxy_handler, https_handler = opener_builder.call_args.args
        self.assertEqual(proxy_handler.proxies, {})
        self.assertIsNotNone(https_handler)

    def test_provider_cli_projects_unknown_outcome_without_traceback(self) -> None:
        output = StringIO()
        code = provider_main(
            ["probe"],
            stdout=output,
            environment={"ARK_API_KEY": "do-not-expose"},
            transport=UnknownOutcomeTransport(),
        )
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 3)
        self.assertEqual(payload["error"], "PROVIDER_OUTCOME_UNKNOWN")
        self.assertEqual(payload["reason"], "CONNECTION_REFUSED")
        self.assertNotIn("Traceback", output.getvalue())
        self.assertNotIn("do-not-expose", output.getvalue())

    def test_provider_cli_preserves_safe_http_status(self) -> None:
        output = StringIO()
        code = provider_main(
            ["probe"],
            stdout=output,
            environment={"ARK_API_KEY": "do-not-expose"},
            transport=StubTransport(ProviderHTTPResponse(401, {}, b'{"error":"unauthorized"}')),
        )
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertEqual(payload["error"], "PROVIDER_HTTP_ERROR")
        self.assertEqual(payload["http_status"], 401)
        self.assertNotIn("do-not-expose", output.getvalue())

    def test_provider_cli_projects_safe_provider_error_fields_only(self) -> None:
        output = StringIO()
        response = ProviderHTTPResponse(
            404,
            {"X-Tt-Logid": "request-safe-1"},
            json.dumps(
                {
                    "error": {
                        "code": "model_not_found",
                        "type": "invalid_request_error",
                        "param": "model",
                        "message": "sensitive provider diagnostic must not be projected",
                    }
                }
            ).encode(),
        )
        code = provider_main(
            ["probe"],
            stdout=output,
            environment={"ARK_API_KEY": "do-not-expose"},
            transport=StubTransport(response),
        )
        payload = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertEqual(payload["http_status"], 404)
        self.assertEqual(payload["provider_error_code"], "model_not_found")
        self.assertEqual(payload["provider_error_type"], "invalid_request_error")
        self.assertEqual(payload["provider_error_parameter"], "model")
        self.assertEqual(payload["provider_request_id"], "request-safe-1")
        self.assertNotIn("sensitive provider diagnostic", output.getvalue())
        self.assertNotIn("do-not-expose", output.getvalue())

    def test_provider_cli_rejects_unsafe_provider_error_parameter(self) -> None:
        output = StringIO()
        response = ProviderHTTPResponse(
            400,
            {},
            json.dumps(
                {
                    "error": {
                        "code": "InvalidParameter",
                        "type": "BadRequest",
                        "param": "response format\nunsafe",
                    }
                }
            ).encode(),
        )

        code = provider_main(
            ["probe"],
            stdout=output,
            environment={"ARK_API_KEY": "do-not-expose"},
            transport=StubTransport(response),
        )
        payload = json.loads(output.getvalue())

        self.assertEqual(code, 2)
        self.assertNotIn("provider_error_parameter", payload)
        self.assertNotIn("unsafe", output.getvalue())


if __name__ == "__main__":
    unittest.main()
