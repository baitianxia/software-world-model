from __future__ import annotations

from dataclasses import replace
import json
import unittest

from swm_demo.formal_validation import (
    AuthorizedInputItem,
    AuthorizedInputManifest,
    ContractViolation,
    IsolationReceipt,
    build_no_tools_request,
    digest,
    render_manifest,
)
from swm_demo.openai_no_tools_adapter import (
    AdapterFailureCode,
    ModelIdentityClassification,
    ModelIdentityPolicy,
    NoToolsAdapterError,
    OpenAIResponsesNoToolsAdapter,
    ProviderHTTPResponse,
    RecordingTransport,
    TransportFailure,
)


MODEL = "gpt-validation-2026-08-01"
CONFORMANCE_RESULT_REF = "validation-fixture:not-a-live-pass"


class StubTransport:
    def __init__(self, outcome: ProviderHTTPResponse | Exception) -> None:
        self.outcome = outcome
        self.calls = 0

    def post_json(
        self, *, endpoint: str, body: bytes, client_request_id: str
    ) -> ProviderHTTPResponse:
        self.calls += 1
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


def successful_response(
    output: object | None = None,
    *,
    model: str = MODEL,
    output_items: list[dict[str, object]] | None = None,
) -> ProviderHTTPResponse:
    if output_items is None:
        output_items = [
            {"id": "rs_1", "type": "reasoning", "summary": []},
            {
                "id": "msg_1",
                "type": "message",
                "status": "completed",
                "role": "assistant",
                "content": [
                    {
                        "type": "output_text",
                        "text": json.dumps(
                            output if output is not None else {"answer": "ok"},
                            separators=(",", ":"),
                        ),
                        "annotations": [],
                    }
                ],
            },
        ]
    payload = {
        "id": "resp_1",
        "status": "completed",
        "model": model,
        "tools": [],
        "output": output_items,
        "usage": {
            "input_tokens": 10,
            "output_tokens": 5,
            "total_tokens": 15,
            "input_tokens_details": {"cached_tokens": 0},
            "output_tokens_details": {"reasoning_tokens": 2},
        },
    }
    return ProviderHTTPResponse(
        200,
        {"x-request-id": "provider-request-1"},
        json.dumps(payload, separators=(",", ":")).encode(),
    )


class OpenAIResponsesNoToolsAdapterConformanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = AuthorizedInputManifest(
            role="ANSWER_GENERATOR",
            capability_ref="answer-generator@1",
            strategy_ref="strategy@1",
            prompt_contract_ref="prompt@1",
            output_contract_ref="answer-output@1",
            items=(
                AuthorizedInputItem(
                    "PROMPT_INSTRUCTION",
                    "prompt@1#0",
                    {"instruction": "Return the authorized answer as JSON."},
                ),
                AuthorizedInputItem(
                    "FORMAL_KNOWLEDGE",
                    "snapshot@1",
                    {"claims": ["authorized"]},
                ),
            ),
        )
        self.policy = ModelIdentityPolicy(
            pinned_models=frozenset({MODEL}),
            observed_revisions_by_alias={
                "gpt-validation": frozenset({MODEL}),
            },
            qualified_models=frozenset({MODEL}),
        )

    def make_request(
        self,
        *,
        manifest: AuthorizedInputManifest | None = None,
        call_id: str = "model-call-1",
        model: str = MODEL,
    ) -> dict[str, object]:
        selected = manifest or self.manifest
        rendered = render_manifest(
            selected,
            rendering_step_ref="renderer@1",
            allowed_kinds={"PROMPT_INSTRUCTION", "FORMAL_KNOWLEDGE"},
        )
        return build_no_tools_request(
            selected,
            rendered,
            model=model,
            max_output_tokens=200,
            reasoning={"effort": "low"},
            metadata={
                "call_id": call_id,
                "capability_id": "answer-generator@1",
                "manifest_digest": digest(selected),
                "baseline_id": "SWM-DBM-ITER-001-REV-002",
            },
            output_schema={
                "type": "json_schema",
                "name": "answer",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {"answer": {"type": "string"}},
                    "required": ["answer"],
                    "additionalProperties": False,
                },
            },
        )

    @staticmethod
    def receipt(request: dict[str, object]) -> IsolationReceipt:
        return IsolationReceipt.issue(
            request,
            adapter_profile_ref="SWM-ADAPTER-OAI-RESPONSES-001@0.1.0",
            live_conformance_result_ref=CONFORMANCE_RESULT_REF,
        )

    @staticmethod
    def decode_answer(value: object) -> dict[str, str]:
        if not isinstance(value, dict) or set(value) != {"answer"}:
            raise ValueError("answer shape mismatch")
        answer = value["answer"]
        if not isinstance(answer, str):
            raise ValueError("answer must be a string")
        return {"answer": answer}

    def adapter(
        self, outcome: ProviderHTTPResponse | Exception
    ) -> tuple[OpenAIResponsesNoToolsAdapter, StubTransport, RecordingTransport]:
        stub = StubTransport(outcome)
        recording = RecordingTransport(stub)
        return (
            OpenAIResponsesNoToolsAdapter(
                transport=recording,
                model_identity_policy=self.policy,
                valid_conformance_result_refs=frozenset({CONFORMANCE_RESULT_REF}),
            ),
            stub,
            recording,
        )

    def test_cc_nt_01_envelope_allowlist_rejects_hidden_input_before_dispatch(self) -> None:
        request = self.make_request()
        receipt = self.receipt(request)
        for field, value in (
            ("instructions", "unmanifested canary"),
            ("conversation", "conv_1"),
            ("prompt", {"id": "pmpt_1"}),
        ):
            adapter, stub, recording = self.adapter(successful_response())
            with self.subTest(field=field), self.assertRaises(NoToolsAdapterError) as caught:
                adapter.execute(
                    {**request, field: value},
                    receipt,
                    output_decoder=self.decode_answer,
                )
            self.assertEqual(AdapterFailureCode.PRE_DISPATCH_REJECTED, caught.exception.code)
            self.assertEqual(0, stub.calls)
            self.assertEqual([], recording.requests)
        adapter, stub, recording = self.adapter(successful_response())
        with self.assertRaises(NoToolsAdapterError) as caught:
            adapter.execute(
                request,
                replace(receipt, live_conformance_result_ref="cc:stale-or-unknown"),
                output_decoder=self.decode_answer,
            )
        self.assertEqual(AdapterFailureCode.PRE_DISPATCH_REJECTED, caught.exception.code)
        self.assertEqual(0, stub.calls)
        self.assertEqual([], recording.requests)

    def test_cc_nt_02_transport_captures_explicit_empty_tool_configuration(self) -> None:
        request = self.make_request()
        adapter, stub, recording = self.adapter(successful_response())
        result = adapter.execute(
            request, self.receipt(request), output_decoder=self.decode_answer
        )
        captured = json.loads(recording.requests[0].body)
        self.assertEqual([], captured["tools"])
        self.assertEqual("none", captured["tool_choice"])
        self.assertIs(captured["parallel_tool_calls"], False)
        self.assertEqual("PASS", result.eligibility)
        self.assertEqual(1, stub.calls)

    def test_cc_nt_03_calls_are_stateless_and_do_not_reuse_prior_input(self) -> None:
        first_manifest = replace(
            self.manifest,
            items=self.manifest.items
            + (
                AuthorizedInputItem(
                    "FORMAL_KNOWLEDGE",
                    "snapshot@first-only",
                    {"canary": "first-context-only-5f927e"},
                ),
            ),
        )
        first = self.make_request(manifest=first_manifest, call_id="model-call-first")
        second = self.make_request(call_id="model-call-second")
        adapter, stub, recording = self.adapter(successful_response())
        adapter.execute(first, self.receipt(first), output_decoder=self.decode_answer)
        adapter.execute(second, self.receipt(second), output_decoder=self.decode_answer)
        second_body = recording.requests[1].body.decode()
        self.assertNotIn("first-context-only-5f927e", second_body)
        for forbidden in ("conversation", "previous_response_id", "context_management"):
            self.assertNotIn(f'"{forbidden}"', second_body)
        self.assertEqual(2, stub.calls)

    def test_cc_nt_04_capture_digest_matches_receipt_and_excludes_canary(self) -> None:
        request = self.make_request()
        adapter, _, recording = self.adapter(successful_response())
        receipt = self.receipt(request)
        result = adapter.execute(
            request, receipt, output_decoder=self.decode_answer
        )
        self.assertEqual(receipt.request_digest, recording.requests[0].body_digest)
        self.assertEqual(receipt.request_digest, result.request_digest)
        self.assertNotIn(b"unmanifested-canary-8d2d", recording.requests[0].body)

    def test_cc_nt_05_attachment_shapes_cannot_reach_transport(self) -> None:
        request = self.make_request()
        receipt = self.receipt(request)
        mutated = json.loads(json.dumps(request))
        mutated["input"][0]["content"] = [
            {"type": "input_file", "file_id": "file-secret"}
        ]
        adapter, stub, recording = self.adapter(successful_response())
        with self.assertRaises(NoToolsAdapterError) as caught:
            adapter.execute(mutated, receipt, output_decoder=self.decode_answer)
        self.assertEqual(AdapterFailureCode.PRE_DISPATCH_REJECTED, caught.exception.code)
        self.assertEqual(0, stub.calls)
        self.assertEqual([], recording.requests)

    def test_cc_nt_06_tool_and_unknown_output_items_are_quarantined(self) -> None:
        request = self.make_request()
        for output_type in (
            "function_call",
            "web_search_call",
            "file_search_call",
            "computer_call",
            "mcp_call",
            "future_unknown_item",
        ):
            adapter, _, _ = self.adapter(
                successful_response(output_items=[{"type": output_type}])
            )
            with self.subTest(output_type=output_type), self.assertRaises(
                NoToolsAdapterError
            ) as caught:
                adapter.execute(
                    request,
                    self.receipt(request),
                    output_decoder=self.decode_answer,
                )
            self.assertEqual(
                AdapterFailureCode.PROVIDER_OUTPUT_FORBIDDEN,
                caught.exception.code,
            )

    def test_cc_nt_07_structured_outcomes_are_classified_without_domain_output(self) -> None:
        request = self.make_request()
        valid_adapter, _, _ = self.adapter(successful_response())
        valid = valid_adapter.execute(
            request, self.receipt(request), output_decoder=self.decode_answer
        )
        self.assertEqual({"answer": "ok"}, valid.output)

        invalid_json = successful_response(
            output_items=[
                {
                    "id": "msg",
                    "type": "message",
                    "status": "completed",
                    "role": "assistant",
                    "content": [
                        {"type": "output_text", "text": "not-json", "annotations": []}
                    ],
                }
            ]
        )
        refusal = successful_response(
            output_items=[
                {
                    "id": "msg",
                    "type": "message",
                    "status": "completed",
                    "role": "assistant",
                    "content": [{"type": "refusal", "refusal": "declined"}],
                }
            ]
        )
        for response, expected in (
            (invalid_json, AdapterFailureCode.STRUCTURED_OUTPUT_INVALID),
            (refusal, AdapterFailureCode.PROVIDER_REFUSAL),
            (
                self.incomplete_response("max_output_tokens"),
                AdapterFailureCode.PROVIDER_INCOMPLETE_MAX_TOKENS,
            ),
            (
                self.incomplete_response("content_filter"),
                AdapterFailureCode.PROVIDER_INCOMPLETE_CONTENT_FILTER,
            ),
        ):
            adapter, _, _ = self.adapter(response)
            with self.subTest(expected=expected), self.assertRaises(
                NoToolsAdapterError
            ) as caught:
                adapter.execute(
                    request,
                    self.receipt(request),
                    output_decoder=self.decode_answer,
                )
            self.assertEqual(expected, caught.exception.code)

    @staticmethod
    def incomplete_response(reason: str) -> ProviderHTTPResponse:
        return ProviderHTTPResponse(
            200,
            {},
            json.dumps(
                {
                    "id": "resp_incomplete",
                    "status": "incomplete",
                    "incomplete_details": {"reason": reason},
                    "model": MODEL,
                    "tools": [],
                    "output": [],
                    "usage": None,
                }
            ).encode(),
        )

    def test_cc_nt_08_model_identity_requires_explicit_policy_and_qualification(self) -> None:
        self.assertEqual(
            ModelIdentityClassification.PINNED,
            self.policy.classify(MODEL, MODEL),
        )
        self.assertEqual(
            ModelIdentityClassification.OBSERVED_MUTABLE,
            self.policy.classify("gpt-validation", MODEL),
        )
        self.assertEqual(
            ModelIdentityClassification.UNRESOLVED_MUTABLE,
            self.policy.classify("gpt-rolling", "gpt-rolling"),
        )
        request = self.make_request(model="gpt-rolling")
        adapter, _, _ = self.adapter(
            successful_response(model="gpt-rolling")
        )
        with self.assertRaises(NoToolsAdapterError) as caught:
            adapter.execute(
                request, self.receipt(request), output_decoder=self.decode_answer
            )
        self.assertEqual(AdapterFailureCode.MODEL_IDENTITY_UNQUALIFIED, caught.exception.code)

    def test_cc_nt_09_post_dispatch_transport_failure_is_outcome_unknown_and_not_retried(self) -> None:
        request = self.make_request(call_id="model-call-unknown")
        adapter, stub, recording = self.adapter(TransportFailure(dispatched=True))
        with self.assertRaises(NoToolsAdapterError) as caught:
            adapter.execute(
                request, self.receipt(request), output_decoder=self.decode_answer
            )
        self.assertEqual(AdapterFailureCode.OUTCOME_UNKNOWN, caught.exception.code)
        self.assertEqual("model-call-unknown", caught.exception.client_request_id)
        self.assertEqual(1, stub.calls)
        self.assertEqual(1, len(recording.requests))

    def test_cc_nt_10_secret_material_is_absent_from_capture_and_error(self) -> None:
        secret = "sk-validation-secret-must-not-appear"

        class SecretHoldingTransport(StubTransport):
            def __init__(self) -> None:
                self.api_key = secret
                super().__init__(TransportFailure(dispatched=True))

        request = self.make_request()
        delegate = SecretHoldingTransport()
        recording = RecordingTransport(delegate)
        adapter = OpenAIResponsesNoToolsAdapter(
            transport=recording,
            model_identity_policy=self.policy,
            valid_conformance_result_refs=frozenset({CONFORMANCE_RESULT_REF}),
        )
        with self.assertRaises(NoToolsAdapterError) as caught:
            adapter.execute(
                request, self.receipt(request), output_decoder=self.decode_answer
            )
        self.assertNotIn(secret, repr(recording.requests))
        self.assertNotIn(secret, str(caught.exception))
        self.assertNotIn(secret.encode(), recording.requests[0].body)

    def test_cc_nt_11_recorded_provider_fixture_normalizes_echo_without_claiming_live_cc(self) -> None:
        request = self.make_request()
        adapter, _, recording = self.adapter(successful_response())
        result = adapter.execute(
            request, self.receipt(request), output_decoder=self.decode_answer
        )
        self.assertEqual("provider-request-1", result.provider_request_id)
        self.assertEqual("resp_1", result.provider_response_id)
        self.assertEqual(MODEL, result.actual_model)
        self.assertEqual(ModelIdentityClassification.PINNED, result.model_identity)
        self.assertEqual(10, result.usage.input_tokens)
        self.assertEqual(2, result.usage.reasoning_tokens)
        self.assertNotEqual("", recording.requests[0].body_digest)

    def test_cc_nt_12_failed_execution_cannot_produce_an_eligible_sink_value(self) -> None:
        request = self.make_request()
        adapter, _, _ = self.adapter(
            successful_response(output_items=[{"type": "web_search_call"}])
        )
        production_sink: list[object] = []
        with self.assertRaises(NoToolsAdapterError):
            result = adapter.execute(
                request, self.receipt(request), output_decoder=self.decode_answer
            )
            production_sink.append(result)
        self.assertEqual([], production_sink)

    def test_receipt_rejects_attachment_even_when_authorized_text_mentions_prompt(self) -> None:
        request = self.make_request()
        request["input"][0]["content"][0]["text"] = (
            'Authorized discussion of the literal field name "prompt": is allowed.'
        )
        receipt = self.receipt(request)
        self.assertEqual(digest(request), receipt.request_digest)
        mutated = json.loads(json.dumps(request))
        mutated["input"][0]["content"][0] = {
            "type": "input_image",
            "image_url": "https://example.invalid/canary.png",
        }
        with self.assertRaises(ContractViolation):
            self.receipt(mutated)


if __name__ == "__main__":
    unittest.main()
