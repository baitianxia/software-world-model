from __future__ import annotations

import json
import unittest

from software_world_model.ai_infrastructure import (
    AdapterConformanceLevel,
    OpenAIResponsesNoToolsAdapter,
    OutputSchemaDefinition,
    ProviderHTTPResponse,
    RecordingResponsesTransport,
    ReplayClassification,
)
from software_world_model.ai_infrastructure.model_gateway import ProviderRequest, RenderedMessage
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of


MODEL = "gpt-test-pinned-2026-08-06"


class StubTransport:
    def __init__(self, response: ProviderHTTPResponse) -> None:
        self.response = response
        self.calls = 0

    def post_json(self, **arguments):
        self.calls += 1
        return self.response


def success_response(*, output_items=None, usage=None, model=MODEL):
    if output_items is None:
        output_items = [
            {"id": "reasoning_1", "type": "reasoning", "summary": []},
            {
                "id": "message_1",
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": '{"answer":"ok"}',
                        "annotations": [],
                    }
                ],
            },
        ]
    if usage is None:
        usage = {"input_tokens": 12, "output_tokens": 4, "total_tokens": 16}
    return ProviderHTTPResponse(
        status_code=200,
        headers={"X-Request-Id": "provider-request-1"},
        body=json.dumps(
            {
                "id": "response_1",
                "status": "completed",
                "model": model,
                "tools": [],
                "output": output_items,
                "usage": usage,
            }
        ).encode(),
    )


class OpenAIResponsesAdapterTests(unittest.TestCase):
    def request(self, **changes):
        values = {
            "model_ref": MODEL,
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
        recording = RecordingResponsesTransport(stub)
        values = {
            "transport": recording,
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
            "pinned_models": frozenset({MODEL}),
        }
        values.update(changes)
        return OpenAIResponsesNoToolsAdapter(**values), stub, recording

    def test_wire_request_is_stateless_no_tools_and_schema_constrained(self) -> None:
        adapter, stub, recording = self.adapter(success_response())
        result = adapter.invoke(self.request())

        payload = json.loads(recording.requests[0].body)
        self.assertEqual(payload["tools"], [])
        self.assertEqual(payload["tool_choice"], "none")
        self.assertFalse(payload["parallel_tool_calls"])
        self.assertFalse(payload["store"])
        self.assertFalse(payload["stream"])
        self.assertNotIn("previous_response_id", payload)
        self.assertEqual(payload["text"]["format"]["type"], "json_schema")
        self.assertEqual(stub.calls, 1)
        self.assertEqual(result.replay_classification, ReplayClassification.PINNED)
        self.assertEqual(result.provider_request_id, "provider-request-1")
        self.assertTrue(result.usage_complete)

    def test_forbidden_tools_fail_before_transport(self) -> None:
        adapter, stub, recording = self.adapter(success_response())
        with self.assertRaises(DomainError) as raised:
            adapter.invoke(self.request(tools=({"type": "web_search"},)))
        self.assertEqual(raised.exception.code, ErrorCode.PROVIDER_OUTPUT_FORBIDDEN)
        self.assertEqual(stub.calls, 0)
        self.assertEqual(recording.requests, [])

    def test_tool_output_and_refusal_are_quarantined(self) -> None:
        cases = (
            ([{"type": "web_search_call"}], ErrorCode.PROVIDER_OUTPUT_FORBIDDEN),
            (
                [
                    {
                        "type": "message",
                        "status": "completed",
                        "role": "assistant",
                        "content": [{"type": "refusal", "refusal": "no"}],
                    }
                ],
                ErrorCode.PROVIDER_REFUSAL,
            ),
        )
        for output, expected in cases:
            adapter, _, _ = self.adapter(success_response(output_items=output))
            with self.subTest(expected=expected), self.assertRaises(DomainError) as raised:
                adapter.invoke(self.request())
            self.assertEqual(raised.exception.code, expected)

    def test_missing_usage_is_recorded_as_incomplete_not_zero(self) -> None:
        adapter, _, _ = self.adapter(success_response(usage="missing"))
        result = adapter.invoke(self.request())
        self.assertFalse(result.usage_complete)
        self.assertIsNone(result.input_tokens)
        self.assertIsNone(result.output_tokens)

    def test_application_revalidates_closed_structured_output(self) -> None:
        output = [
            {
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": '{"answer":"ok","hidden":"extra"}',
                        "annotations": [],
                    }
                ],
            }
        ]
        adapter, _, _ = self.adapter(success_response(output_items=output))
        with self.assertRaises(DomainError) as raised:
            adapter.invoke(self.request())
        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)

    def test_schema_registration_requires_all_fields_and_closed_objects(self) -> None:
        with self.assertRaises(DomainError) as raised:
            OutputSchemaDefinition(
                "invalid",
                {
                    "type": "object",
                    "properties": {"answer": {"type": "string"}},
                    "required": [],
                    "additionalProperties": False,
                },
            )
        self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_array_cardinality_and_uniqueness_are_revalidated(self) -> None:
        definition = OutputSchemaDefinition(
            "references",
            {
                "type": "object",
                "properties": {
                    "references": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 1,
                        "uniqueItems": True,
                    }
                },
                "required": ["references"],
                "additionalProperties": False,
            },
        )

        self.assertEqual(
            definition.validate_output_text('{"references":["entry-1"]}'),
            {"references": ["entry-1"]},
        )
        for invalid in (
            '{"references":[]}',
            '{"references":["entry-1","entry-1"]}',
        ):
            with self.subTest(invalid=invalid), self.assertRaises(
                DomainError
            ) as raised:
                definition.validate_output_text(invalid)
            self.assertEqual(
                raised.exception.code,
                ErrorCode.STRUCTURED_OUTPUT_INVALID,
            )

    def test_array_cardinality_schema_bounds_must_be_valid(self) -> None:
        for constraint in (
            {"minItems": -1},
            {"maxItems": -1},
            {"minItems": 2, "maxItems": 1},
            {"uniqueItems": "yes"},
        ):
            schema = {
                "type": "object",
                "properties": {
                    "references": {
                        "type": "array",
                        "items": {"type": "string"},
                        **constraint,
                    }
                },
                "required": ["references"],
                "additionalProperties": False,
            }
            with self.subTest(constraint=constraint), self.assertRaises(
                DomainError
            ) as raised:
                OutputSchemaDefinition("invalid-array-bound", schema)
            self.assertEqual(raised.exception.code, ErrorCode.INVALID_ARGUMENT)

    def test_live_level_cannot_be_declared_without_qualified_exact_model(self) -> None:
        with self.assertRaises(DomainError) as raised:
            self.adapter(
                success_response(),
                conformance_level=AdapterConformanceLevel.LIVE_CURRENT,
            )
        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)


if __name__ == "__main__":
    unittest.main()
