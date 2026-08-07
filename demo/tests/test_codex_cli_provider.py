from __future__ import annotations

import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from swm_demo.codex_cli_provider import (
    CodexCliProvider,
    CodexCliProviderError,
    _CAPABILITY_CONTRACTS,
)


def _event_stream(message: object, *items: dict[str, object]) -> str:
    events: list[dict[str, object]] = [
        {"type": "thread.started", "thread_id": "thread:test"},
        {"type": "turn.started"},
        *items,
        {
            "type": "item.completed",
            "item": {
                "type": "agent_message",
                "text": json.dumps(message, separators=(",", ":")),
            },
        },
        {"type": "turn.completed", "usage": {}},
    ]
    return "\n".join(json.dumps(item, separators=(",", ":")) for item in events)


class CodexCliProviderTest(unittest.TestCase):
    def test_invoke_is_isolated_and_uses_capability_schema(self) -> None:
        observed_paths: list[Path] = []

        def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            working_directory = Path(str(kwargs["cwd"]))
            self.assertTrue(working_directory.is_dir())
            self.assertEqual([], list(working_directory.iterdir()))
            self.assertNotIn("--cd", command)
            self.assertEqual("codex", command[0])
            self.assertEqual("exec", command[1])
            for flag in (
                "--ephemeral",
                "--json",
                "--skip-git-repo-check",
                "--ignore-user-config",
                "--ignore-rules",
                "--output-schema",
            ):
                self.assertIn(flag, command)
            self.assertEqual("read-only", command[command.index("--sandbox") + 1])
            self.assertEqual("gpt-validation", command[command.index("--model") + 1])
            self.assertEqual("-", command[-1])

            schema_path = Path(command[command.index("--output-schema") + 1])
            self.assertTrue(schema_path.is_file())
            self.assertNotEqual(working_directory, schema_path.parent)
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            self.assertEqual("object", schema["type"])
            self.assertFalse(schema["additionalProperties"])
            self.assertEqual(["use_case", "endpoint"], schema["required"])
            serialized_schema = json.dumps(schema, sort_keys=True)
            for unsupported in (
                "maxItems",
                "maximum",
                "minItems",
                "minLength",
                "minimum",
                "uniqueItems",
            ):
                self.assertNotIn(f'"{unsupported}"', serialized_schema)

            prompt = json.loads(str(kwargs["input"]))
            self.assertEqual({"capability_contract", "payload"}, set(prompt))
            self.assertEqual(
                {"request": "explain checkout", "scope_id": "system:shop"},
                prompt["payload"],
            )
            self.assertIn("Capability: route-task", prompt["capability_contract"])
            self.assertTrue(kwargs["text"])
            self.assertTrue(kwargs["capture_output"])
            self.assertFalse(kwargs["check"])
            observed_paths.extend([working_directory, schema_path])
            stdout = _event_stream(
                {"use_case": "structure-view", "endpoint": None},
                {
                    "type": "item.completed",
                    "item": {"type": "reasoning", "text": "internal"},
                },
            )
            return subprocess.CompletedProcess(command, 0, stdout, "")

        provider = CodexCliProvider(
            model="gpt-validation",
            timeout_seconds=12,
            allow_agent_runtime=True,
        )
        with patch("swm_demo.codex_cli_provider.subprocess.run", side_effect=run) as mocked:
            output = provider.invoke(
                "route-task",
                {"request": "explain checkout", "scope_id": "system:shop"},
            )

        self.assertEqual(
            {"use_case": "structure-view", "endpoint": None}, output
        )
        mocked.assert_called_once()
        self.assertTrue(observed_paths)
        self.assertTrue(all(not path.exists() for path in observed_paths))

    def test_all_registered_capabilities_have_strict_object_schemas(self) -> None:
        self.assertEqual(
            {
                "route-task",
                "form-knowledge-requirement",
                "plan-formal-knowledge-step",
                "assess-knowledge-sufficiency",
                "derive-build-intent",
                "propose-knowledge-candidates",
                "draft-answer",
                "review-answer",
            },
            set(_CAPABILITY_CONTRACTS),
        )

        def assert_strict_objects(schema: object) -> None:
            if isinstance(schema, dict):
                if schema.get("type") == "object":
                    self.assertIs(schema.get("additionalProperties"), False)
                    properties = schema.get("properties", {})
                    self.assertEqual(set(properties), set(schema.get("required", [])))
                for nested in schema.values():
                    assert_strict_objects(nested)
            elif isinstance(schema, list):
                for nested in schema:
                    assert_strict_objects(nested)

        for contract in _CAPABILITY_CONTRACTS.values():
            self.assertTrue(contract.instruction)
            assert_strict_objects(contract.output_schema)

    def test_forbidden_codex_action_fails_closed(self) -> None:
        forbidden = {
            "type": "item.started",
            "item": {
                "type": "command_execution",
                "command": "find / -type f",
            },
        }
        completed = subprocess.CompletedProcess(
            ["codex"],
            0,
            _event_stream(
                {"use_case": "structure-view", "endpoint": None}, forbidden
            ),
            "",
        )
        with patch(
            "swm_demo.codex_cli_provider.subprocess.run", return_value=completed
        ):
            with self.assertRaisesRegex(
                CodexCliProviderError, "forbidden item/action: command_execution"
            ):
                CodexCliProvider(allow_agent_runtime=True).invoke(
                    "route-task", {"request": "structure", "scope_id": "scope"}
                )

    def test_formal_step_provider_schema_binds_action_to_arguments_and_unwraps(
        self,
    ) -> None:
        def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
            schema_path = Path(command[command.index("--output-schema") + 1])
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            alternatives = schema["properties"]["selection"]["anyOf"]
            actions = {
                item["properties"]["action"]["enum"][0]: set(
                    item["properties"]["arguments"]["properties"]
                )
                for item in alternatives
            }
            self.assertEqual(
                {"SEARCH", "NEIGHBORHOOD", "EXPLAIN", "STOP"}, set(actions)
            )
            self.assertIn("query", actions["SEARCH"])
            self.assertIn("knowledge_ids", actions["EXPLAIN"])
            self.assertEqual(set(), actions["STOP"])
            return subprocess.CompletedProcess(
                command,
                0,
                _event_stream(
                    {
                        "selection": {
                            "action": "SEARCH",
                            "arguments": {
                                "kind": "INFERENCE",
                                "query": "checkout",
                                "match_mode": "CONTAINS",
                                "type_name": None,
                                "limit": 20,
                                "cursor": 0,
                            },
                        }
                    }
                ),
                "",
            )

        with patch("swm_demo.codex_cli_provider.subprocess.run", side_effect=run):
            output = CodexCliProvider(allow_agent_runtime=True).invoke(
                "plan-formal-knowledge-step", {"tool_trace": []}
            )

        self.assertEqual("SEARCH", output["action"])
        self.assertEqual("checkout", output["arguments"]["query"])

    def test_non_object_agent_message_is_rejected(self) -> None:
        completed = subprocess.CompletedProcess(
            ["codex"], 0, _event_stream(["not", "an", "object"]), ""
        )
        with patch(
            "swm_demo.codex_cli_provider.subprocess.run", return_value=completed
        ):
            with self.assertRaisesRegex(
                CodexCliProviderError, "JSON value must be an object"
            ):
                CodexCliProvider(allow_agent_runtime=True).invoke(
                    "route-task", {"request": "structure", "scope_id": "scope"}
                )

    def test_nonzero_process_exit_reports_failure_without_parsing_stdout(self) -> None:
        completed = subprocess.CompletedProcess(
            ["codex"],
            17,
            "this is not JSONL",
            "authentication unavailable\n",
        )
        with patch(
            "swm_demo.codex_cli_provider.subprocess.run", return_value=completed
        ):
            with self.assertRaisesRegex(
                CodexCliProviderError,
                "status 17: authentication unavailable",
            ):
                CodexCliProvider(allow_agent_runtime=True).invoke(
                    "route-task", {"request": "structure", "scope_id": "scope"}
                )

    def test_oversized_payload_fails_before_starting_codex(self) -> None:
        provider = CodexCliProvider(
            max_input_characters=100,
            allow_agent_runtime=True,
        )
        with patch("swm_demo.codex_cli_provider.subprocess.run") as run:
            with self.assertRaisesRegex(
                CodexCliProviderError, "MODEL_INPUT_BUDGET_EXCEEDED"
            ):
                provider.invoke(
                    "route-task",
                    {"request": "x" * 500, "scope_id": "scope"},
                )
        run.assert_not_called()

    def test_agent_runtime_requires_explicit_validation_only_acknowledgement(self) -> None:
        with patch("swm_demo.codex_cli_provider.subprocess.run") as run:
            with self.assertRaisesRegex(
                CodexCliProviderError, "CODEX_AGENT_RUNTIME_NOT_ISOLATED"
            ):
                CodexCliProvider().invoke(
                    "route-task", {"request": "structure", "scope_id": "scope"}
                )
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
