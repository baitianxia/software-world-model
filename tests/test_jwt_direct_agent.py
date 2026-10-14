from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.ai_infrastructure import (
    ArkChatConformanceQualification,
    ProviderHTTPResponse,
    ProviderOutcomeUnknown,
    VolcengineArkModelConfiguration,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode
from validation.jwt_iteration_001.direct_agent import (
    _diagnose_structured_output_response,
    run_direct_agent,
)
from validation.jwt_iteration_001.manifest import seal_direct_oracle
from tests._environment import requires_mall_checkout


class ScriptedTransport:
    def __init__(self, steps):
        self.steps = list(steps)
        self.calls = []

    def post_json(self, **arguments):
        self.calls.append(arguments)
        step = self.steps[len(self.calls) - 1]
        if callable(step):
            step = step(arguments)
        return _response(step, len(self.calls))


class UnknownTransport:
    def post_json(self, **arguments):
        raise ProviderOutcomeUnknown("unknown", reason_code="TLS_FAILURE")


def _action(kind, *, role="NONE", path="", query="", start=0, end=0):
    return {
        "action": kind,
        "revision_role": role,
        "path": path,
        "query": query,
        "start_line": start,
        "end_line": end,
        "rationale": "bounded next action",
        "answer": "",
        "claims": [],
    }


def _finish(arguments):
    wire = json.loads(arguments["body"])
    state = json.loads(wire["messages"][-1]["content"])
    observation_ref = state["observations"][0]["observation_ref"]
    return {
        "action": "FINISH",
        "revision_role": "NONE",
        "path": "",
        "query": "",
        "start_line": 0,
        "end_line": 0,
        "rationale": "the changed-file observation supports a bounded answer",
        "answer": "The frozen comparison changes three files in the root and mall-security module.",
        "claims": [
            {
                "semantic_key": "claim:changed-files",
                "claim": "the frozen comparison reports three changed files",
                "target": "dacce5f28dfc1734f2db09668d928d7fac2a3a7a",
                "context": "PARENT_TO_TARGET",
                "modality": "ESTABLISHED",
                "condition": None,
                "limitation": None,
                "coverage": "DIRECT",
                "source_observation_refs": [observation_ref],
                "need_ids": ["JWT-N01"],
                "obligation_ids": ["JWT-N01-O02"],
                "material": True,
            }
        ],
    }


def _response(content, ordinal):
    return ProviderHTTPResponse(
        status_code=200,
        headers={"x-tt-logid": f"ark-direct-{ordinal}"},
        body=json.dumps(
            {
                "id": f"chatcmpl-direct-{ordinal}",
                "object": "chat.completion",
                "model": "glm-5.2",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": json.dumps(content),
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


@requires_mall_checkout()
class JwtDirectAgentTests(unittest.TestCase):
    def setUp(self):
        self.configuration = VolcengineArkModelConfiguration()
        self.qualification = ArkChatConformanceQualification(
            result_ref="CC-ARK-CHAT-NO-TOOLS-001:sha256:" + "a" * 64,
            result_digest=Digest("sha256:" + "a" * 64),
            qualified_model_fingerprints=self.configuration.qualified_model_identities,
            adapter_version=self.configuration.adapter_version,
            provider_configuration_fingerprint=self.configuration.fingerprint,
            valid_until=datetime(2099, 1, 1, tzinfo=timezone.utc),
        )
        self.repository = (
            Path(__file__).resolve().parents[1] / "validation-projects" / "mall"
        )

    def test_direct_agent_executes_bounded_git_action_and_creates_private_draft(self):
        transport = ScriptedTransport([_action("COMPARE"), _finish])
        with tempfile.TemporaryDirectory() as directory:
            draft_path = run_direct_agent(
                repository_path=self.repository,
                result_directory=directory,
                qualification=self.qualification,
                configuration=self.configuration,
                transport=transport,
                max_tool_steps=1,
                max_model_calls=2,
                now=datetime(2026, 8, 6, tzinfo=timezone.utc),
            )
            draft = json.loads(draft_path.read_text(encoding="utf-8"))
            self.assertEqual(draft_path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(len(draft["trace"]), 1)
            self.assertEqual(len(draft["observations"]), 1)
            self.assertEqual(draft["trace"][0]["tool"], "COMPARE")
            self.assertIn("mall-security/pom.xml", draft["observations"][0]["content"])
            self.assertIn("@@", draft["observations"][0]["content"])
            self.assertIn("JWTUtil.createToken", draft["observations"][0]["content"])
            self.assertEqual(draft["provider_request_ids"], ["ark-direct-1", "ark-direct-2"])
            self.assertEqual(draft["output_normalizations"], ["IDENTITY", "IDENTITY"])
            recorded_wire = b"\n".join(call["body"] for call in transport.calls)
            self.assertNotIn(b"Authorization", recorded_wire)
            first_wire = json.loads(transport.calls[0]["body"])
            schema_prompt = first_wire["messages"][0]["content"]
            system_prompt = first_wire["messages"][1]["content"]
            self.assertIn("closed JSON Schema", schema_prompt)
            self.assertIn("Return exactly one JSON object", system_prompt)
            self.assertIn("Do not emit Markdown fences", system_prompt)
            self.assertIn("action, revision_role, path, query", system_prompt)
            self.assertIn("at most six claims total", system_prompt)
            self.assertIn("explicitly answer every mapped Obligation", system_prompt)
            self.assertIn("repository-wide absence claim", system_prompt)
            self.assertIn("derived, stripped, converted", system_prompt)
            self.assertIn("comments only as comment-modality evidence", system_prompt)
            self.assertIn("verify=false returns null", system_prompt)
            self.assertIn("do not claim every invalid signature", system_prompt)

            oracle_path = seal_direct_oracle(
                draft_path=draft_path,
                result_directory=Path(directory) / "oracle",
                qualification=self.qualification,
                configuration=self.configuration,
                operator="direct-operator",
                reviewer="independent-reviewer",
                now=datetime(2026, 8, 6, 1, tzinfo=timezone.utc),
            )
            self.assertEqual(oracle_path.stat().st_mode & 0o777, 0o600)

    def test_repeated_source_action_is_recorded_and_model_can_finish(self):
        transport = ScriptedTransport(
            [_action("COMPARE"), _action("COMPARE"), _finish]
        )
        with tempfile.TemporaryDirectory() as directory:
            draft_path = run_direct_agent(
                repository_path=self.repository,
                result_directory=directory,
                qualification=self.qualification,
                configuration=self.configuration,
                transport=transport,
                max_tool_steps=2,
                max_model_calls=3,
                now=datetime(2026, 8, 6, tzinfo=timezone.utc),
            )
            draft = json.loads(draft_path.read_text(encoding="utf-8"))

        self.assertEqual([item["tool"] for item in draft["trace"]], ["COMPARE", "DENIED"])
        self.assertIn("identical source action", draft["observations"][1]["content"])

    def test_invalid_tool_proposal_is_recorded_and_model_can_retry(self):
        def finish_with_latest_observation(arguments):
            step = _finish(arguments)
            wire = json.loads(arguments["body"])
            state = json.loads(wire["messages"][-1]["content"])
            step["claims"][0]["source_observation_refs"] = [
                state["observations"][-1]["observation_ref"]
            ]
            return step

        transport = ScriptedTransport(
            [
                _action(
                    "READ",
                    role="TARGET",
                    path="pom.xml",
                    query="invalid-for-read",
                    start=1,
                    end=10,
                ),
                _action("COMPARE"),
                finish_with_latest_observation,
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            draft_path = run_direct_agent(
                repository_path=self.repository,
                result_directory=directory,
                qualification=self.qualification,
                configuration=self.configuration,
                transport=transport,
                max_tool_steps=2,
                max_model_calls=3,
                now=datetime(2026, 8, 6, tzinfo=timezone.utc),
            )
            draft = json.loads(draft_path.read_text(encoding="utf-8"))

        self.assertEqual([item["tool"] for item in draft["trace"]], ["DENIED", "COMPARE"])
        self.assertEqual(draft["observations"][0]["tool"], "DENIED")
        self.assertIn('"outcome":"DENIED"', draft["observations"][0]["content"])
        self.assertEqual(len(draft["provider_request_ids"]), 3)

    def test_invalid_finish_shape_is_recorded_and_model_can_retry(self):
        def invalid_finish(arguments):
            step = _finish(arguments)
            step["revision_role"] = "TARGET"
            return step

        transport = ScriptedTransport(
            [_action("COMPARE"), invalid_finish, _finish]
        )
        with tempfile.TemporaryDirectory() as directory:
            draft_path = run_direct_agent(
                repository_path=self.repository,
                result_directory=directory,
                qualification=self.qualification,
                configuration=self.configuration,
                transport=transport,
                max_tool_steps=2,
                max_model_calls=3,
                now=datetime(2026, 8, 6, tzinfo=timezone.utc),
            )
            draft = json.loads(draft_path.read_text(encoding="utf-8"))

        self.assertEqual([item["tool"] for item in draft["trace"]], ["COMPARE", "DENIED"])
        self.assertEqual(draft["trace"][1]["request"]["action"], "FINISH")
        self.assertIn("FINISH payload is invalid", draft["observations"][1]["content"])

    def test_schema_invalid_json_object_is_denied_and_model_can_retry(self):
        def finish_with_latest_observation(arguments):
            step = _finish(arguments)
            wire = json.loads(arguments["body"])
            state = json.loads(wire["messages"][-1]["content"])
            step["claims"][0]["source_observation_refs"] = [
                state["observations"][-1]["observation_ref"]
            ]
            return step

        transport = ScriptedTransport(
            [
                {"unexpected": "schema-invalid-object"},
                _action("COMPARE"),
                finish_with_latest_observation,
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            draft_path = run_direct_agent(
                repository_path=self.repository,
                result_directory=directory,
                qualification=self.qualification,
                configuration=self.configuration,
                transport=transport,
                max_tool_steps=2,
                max_model_calls=3,
                now=datetime(2026, 8, 6, tzinfo=timezone.utc),
            )
            draft = json.loads(draft_path.read_text(encoding="utf-8"))

        self.assertEqual(
            [item["tool"] for item in draft["trace"]],
            ["DENIED", "COMPARE"],
        )
        self.assertEqual(
            draft["trace"][0]["request"]["action"],
            "INVALID_OUTPUT",
        )
        self.assertIn(
            "object fields do not match the closed schema",
            draft["observations"][0]["content"],
        )
        self.assertNotIn("schema-invalid-object", draft["observations"][0]["content"])

    def test_read_outside_changed_file_set_is_rejected(self):
        transport = ScriptedTransport(
            [_action("READ", role="TARGET", path="README.md", start=1, end=10)]
        )
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(DomainError) as raised:
            run_direct_agent(
                repository_path=self.repository,
                result_directory=directory,
                qualification=self.qualification,
                configuration=self.configuration,
                transport=transport,
                max_model_calls=1,
            )
        self.assertEqual(raised.exception.code, ErrorCode.SOURCE_TARGET_OUT_OF_SCOPE)

    def test_unknown_provider_outcome_is_not_converted_to_a_draft(self):
        with tempfile.TemporaryDirectory() as directory:
            result_directory = Path(directory) / "result"
            with self.assertRaises(ProviderOutcomeUnknown):
                run_direct_agent(
                    repository_path=self.repository,
                    result_directory=result_directory,
                    qualification=self.qualification,
                    configuration=self.configuration,
                    transport=UnknownTransport(),
                    max_model_calls=1,
                )
            self.assertFalse(result_directory.exists())

    def test_invalid_structured_step_identifies_call_and_creates_no_draft(self):
        transport = ScriptedTransport(["not-an-object"])
        with tempfile.TemporaryDirectory() as directory:
            result_directory = Path(directory) / "result"
            with self.assertRaises(DomainError) as raised:
                run_direct_agent(
                    repository_path=self.repository,
                    result_directory=result_directory,
                    qualification=self.qualification,
                    configuration=self.configuration,
                    transport=transport,
                    max_model_calls=1,
                )
            self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)
            self.assertIn("model call 1", raised.exception.message)
            self.assertIn("no draft was created", raised.exception.message)
            self.assertEqual(raised.exception.details["content_json_parse"], "NON_OBJECT")
            self.assertFalse(result_directory.exists())

    def test_structured_output_diagnostic_never_exposes_fenced_content(self):
        private_content = "```json\n{\"private\":\"do-not-expose\"}\n```"
        response = ProviderHTTPResponse(
            status_code=200,
            headers={"x-tt-logid": "ark-diagnostic-1"},
            body=json.dumps(
                {
                    "choices": [
                        {
                            "finish_reason": "stop",
                            "message": {
                                "role": "assistant",
                                "reasoning_content": "private reasoning",
                                "content": private_content,
                            },
                        }
                    ]
                }
            ).encode("utf-8"),
        )

        diagnostic = _diagnose_structured_output_response(response)

        self.assertEqual(diagnostic["assistant_content_prefix_class"], "MARKDOWN_FENCE")
        self.assertEqual(diagnostic["content_json_parse"], "INVALID")
        self.assertEqual(diagnostic["reasoning_content_present"], "YES")
        serialized = json.dumps(diagnostic)
        self.assertNotIn(private_content, serialized)
        self.assertNotIn("private reasoning", serialized)


if __name__ == "__main__":
    unittest.main()
