from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
import subprocess
import tempfile
import unittest

from software_world_model.ai_infrastructure import (
    AdapterResponse,
    AgenticModelStrategyConfiguration,
    ReplayClassification,
)
from software_world_model.cross_cutting import Digest, DomainError, ErrorCode, digest_of
from software_world_model.source_integration import LocalGitConnector
from validation.product_holdout_iteration_002 import (
    DirectSourceAnswerExecutor,
    HoldoutAnswerPath,
)
from validation.product_holdout_iteration_002.direct_answer import _parse_action


class SequencedGateway:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.contexts = []

    def invoke(self, context):
        self.contexts.append(context)
        output = self.outputs.pop(0)
        ordinal = len(self.contexts)
        response = AdapterResponse.create(
            provider_request_id=f"provider-request:{ordinal}",
            actual_model_fingerprint="model-fingerprint",
            replay_classification=ReplayClassification.PINNED,
            output_text=json.dumps(output),
            input_tokens=100,
            output_tokens=25,
            usage_complete=True,
            termination_reason="stop",
        )
        if output is None:
            return SimpleNamespace(
                call=SimpleNamespace(
                    failure_code=ErrorCode.STRUCTURED_OUTPUT_INVALID.value
                ),
                eligibility=SimpleNamespace(
                    eligible_for_production_domain_output=False,
                    reason="MODEL_OUTPUT_REJECTED_STRUCTURED_OUTPUT_INVALID",
                ),
                response=response,
            )
        return SimpleNamespace(
            call=SimpleNamespace(failure_code=None),
            eligibility=SimpleNamespace(
                eligible_for_production_domain_output=True,
                reason="ELIGIBLE",
            ),
            response=response,
        )


def task_input(commit: str) -> dict[str, object]:
    core = {
        "schema": "swm.product-holdout-task-input@1",
        "suite_id": "test-suite",
        "suite_version": "1.0.0",
        "suite_digest": "sha256:" + "1" * 64,
        "task_id": "read-app",
        "repository": {
            "repository_id": "test",
            "remote": "local",
            "frozen_tag": "test",
            "frozen_commit": commit,
            "frozen_tree": "2" * 40,
        },
        "question": "App.value 的源码初始值是什么？",
        "revision_scope": {
            "kind": "FROZEN_SNAPSHOT",
            "parent": None,
            "target": commit,
        },
        "allowed_paths": ["src/App.java"],
        "source_policy": "LOCAL_GIT_READ_ONLY_ALLOWED_PATHS_ONLY",
        "resource_policy": {
            "maximum_model_calls": 34,
            "maximum_source_actions": 12,
            "maximum_source_bytes_per_action": 16000,
            "maximum_total_input_tokens": 300000,
            "maximum_total_output_tokens": 48000,
            "maximum_output_tokens_per_call": 1200,
            "timeout_per_call_milliseconds": 180000,
        },
    }
    return {**core, "task_input_digest": digest_of(core).value}


class DirectSourceAnswerExecutorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name) / "repo"
        self.repository.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "Test")
        (self.repository / "src").mkdir()
        (self.repository / "src/App.java").write_text(
            "public class App { int value = 3; }\n", encoding="utf-8"
        )
        self.git("add", ".")
        self.git("commit", "-q", "-m", "initial")
        self.commit = self.git("rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def configuration(self) -> AgenticModelStrategyConfiguration:
        return AgenticModelStrategyConfiguration(
            provider_type="TEST",
            adapter_version="1",
            model_ref="model-alias",
            provider_configuration_fingerprint=Digest("sha256:" + "0" * 64),
            qualification_ref="live-conformance:test",
            max_output_tokens=1200,
            timeout_milliseconds=180000,
            classification="INTERNAL",
        )

    def test_bounded_source_read_then_cited_answer_is_sealed(self) -> None:
        run_id = "direct-test-run"
        gateway = SequencedGateway(
            (
                {
                    "decision": "EXECUTE",
                    "tool": "READ",
                    "revision": self.commit,
                    "base": "",
                    "path": "src/App.java",
                    "query": "",
                    "cursor": "",
                    "offset": "",
                    "max_bytes": "16000",
                    "page_size": "",
                    "rationale": "Read the exact declaration.",
                    "claims": [],
                },
                {
                    "decision": "FINISH",
                    "tool": "NONE",
                    "revision": self.commit,
                    "base": "",
                    "path": "",
                    "query": "",
                    "cursor": "",
                    "offset": "",
                    "max_bytes": "",
                    "page_size": "",
                    "rationale": "The source directly answers the question.",
                    "claims": [
                        {
                            "claim": "App.value 的源码初始值是 3。",
                            "support_references": [
                                f"direct-observation:{run_id}:1"
                            ],
                        }
                    ],
                },
            )
        )
        result = DirectSourceAnswerExecutor(
            gateway=gateway,
            configuration=self.configuration(),
            expected_model_fingerprint="model-fingerprint",
        ).execute(
            task_input=task_input(self.commit),
            connector=LocalGitConnector(str(self.repository)),
            run_id=run_id,
        )

        self.assertEqual(result.path, HoldoutAnswerPath.DIRECT)
        self.assertEqual(result.answer, "App.value 的源码初始值是 3。")
        self.assertEqual(result.model_call_count, 2)
        self.assertEqual(result.source_action_count, 1)
        self.assertTrue(result.verify_digest())
        observations = json.loads(gateway.contexts[1].manifest.items[2].content)
        self.assertIn("int value = 3", observations[0]["content"])

    def test_finish_waits_until_every_allowed_target_path_is_fully_read(self) -> None:
        (self.repository / "src/Other.java").write_text(
            "x" * 17000 + "\n", encoding="utf-8"
        )
        self.git("add", "src/Other.java")
        self.git("commit", "-q", "-m", "add other")
        revision = self.git("rev-parse", "HEAD")
        task = task_input(revision)
        task["allowed_paths"] = ["src/App.java", "src/Other.java"]
        task["task_input_digest"] = digest_of(
            {
                key: value
                for key, value in task.items()
                if key != "task_input_digest"
            }
        ).value
        run_id = "direct-complete-boundary"
        app_reference = f"direct-observation:{run_id}:1"
        other_reference = f"direct-observation:{run_id}:2"
        other_tail_reference = f"direct-observation:{run_id}:3"
        gateway = SequencedGateway(
            (
                {
                    "decision": "EXECUTE",
                    "tool": "READ",
                    "revision": revision,
                    "base": "",
                    "path": "src/App.java",
                    "query": "",
                    "cursor": "",
                    "offset": "",
                    "max_bytes": "16000",
                    "page_size": "",
                    "rationale": "Read the first allowed target path.",
                    "claims": [],
                },
                {
                    "decision": "FINISH",
                    "tool": "NONE",
                    "revision": revision,
                    "base": "",
                    "path": "",
                    "query": "",
                    "cursor": "",
                    "offset": "",
                    "max_bytes": "",
                    "page_size": "",
                    "rationale": "Premature finish after one path.",
                    "claims": [
                        {
                            "claim": "App.value 的源码初始值是 3。",
                            "support_references": [app_reference],
                        }
                    ],
                },
                {
                    "decision": "EXECUTE",
                    "tool": "READ",
                    "revision": revision,
                    "base": "",
                    "path": "src/Other.java",
                    "query": "",
                    "cursor": "",
                    "offset": "",
                    "max_bytes": "16000",
                    "page_size": "",
                    "rationale": "Read the remaining allowed target path.",
                    "claims": [],
                },
                {
                    "decision": "EXECUTE",
                    "tool": "READ",
                    "revision": revision,
                    "base": "",
                    "path": "src/Other.java",
                    "query": "",
                    "cursor": "",
                    "offset": "16000",
                    "max_bytes": "16000",
                    "page_size": "",
                    "rationale": "Continue from the exact next byte offset.",
                    "claims": [],
                },
                {
                    "decision": "FINISH",
                    "tool": "NONE",
                    "revision": revision,
                    "base": "",
                    "path": "",
                    "query": "",
                    "cursor": "",
                    "offset": "",
                    "max_bytes": "",
                    "page_size": "",
                    "rationale": "Every allowed path is now fully observed.",
                    "claims": [
                        {
                            "claim": "两个允许文件均已完整读取。",
                            "support_references": [
                                app_reference,
                                other_reference,
                                other_tail_reference,
                            ],
                        }
                    ],
                },
            )
        )

        result = DirectSourceAnswerExecutor(
            gateway=gateway,
            configuration=self.configuration(),
            expected_model_fingerprint="model-fingerprint",
        ).execute(
            task_input=task,
            connector=LocalGitConnector(str(self.repository)),
            run_id=run_id,
        )

        self.assertEqual(result.model_call_count, 5)
        self.assertEqual(result.source_action_count, 3)
        incomplete = json.loads(gateway.contexts[1].manifest.items[3].content)
        continuation = json.loads(gateway.contexts[3].manifest.items[3].content)
        complete = json.loads(gateway.contexts[4].manifest.items[3].content)
        self.assertFalse(incomplete["finish_allowed"])
        self.assertEqual(incomplete["missing"][0]["path"], "src/Other.java")
        self.assertEqual(
            continuation["missing"][0]["next_action"]["offset"], "16000"
        )
        self.assertTrue(complete["finish_allowed"])

    def test_complete_structured_rejection_is_counted_and_retried_within_budget(self) -> None:
        run_id = "direct-retry-run"
        gateway = SequencedGateway(
            (
                None,
                {
                    "decision": "EXECUTE",
                    "tool": "READ",
                    "revision": self.commit,
                    "base": "",
                    "path": "src/App.java",
                    "query": "",
                    "cursor": "",
                    "offset": "",
                    "max_bytes": "16000",
                    "page_size": "",
                    "rationale": "Read the exact declaration.",
                    "claims": [],
                },
                {
                    "decision": "FINISH",
                    "tool": "NONE",
                    "revision": "",
                    "base": "",
                    "path": "",
                    "query": "",
                    "cursor": "",
                    "offset": "",
                    "max_bytes": "",
                    "page_size": "",
                    "rationale": "The declaration answers the question.",
                    "claims": [
                        {
                            "claim": "App.value 的源码初始值是 3。",
                            "support_references": [
                                f"direct-observation:{run_id}:1"
                            ],
                        }
                    ],
                },
            )
        )

        result = DirectSourceAnswerExecutor(
            gateway=gateway,
            configuration=self.configuration(),
            expected_model_fingerprint="model-fingerprint",
        ).execute(
            task_input=task_input(self.commit),
            connector=LocalGitConnector(str(self.repository)),
            run_id=run_id,
        )

        self.assertEqual(result.model_call_count, 3)
        self.assertEqual(result.input_tokens, 300)
        self.assertEqual(result.output_tokens, 75)
        self.assertEqual(len(result.provider_request_ids), 3)
        self.assertTrue(result.usage_complete)
        self.assertIn(
            "contract-repair",
            [item.item_id for item in gateway.contexts[1].manifest.items],
        )
        self.assertNotIn(
            "contract-repair",
            [item.item_id for item in gateway.contexts[2].manifest.items],
        )
        observations = json.loads(gateway.contexts[2].manifest.items[2].content)
        self.assertIn("int value = 3", observations[0]["content"])

    def test_finish_cannot_cite_an_observation_that_was_not_supplied(self) -> None:
        invalid = {
                    "decision": "FINISH",
                    "tool": "NONE",
                    "revision": "",
                    "base": "",
                    "path": "",
                    "query": "",
                    "cursor": "",
                    "offset": "",
                    "max_bytes": "",
                    "page_size": "",
                    "rationale": "Unsupported finish.",
                    "claims": [
                        {
                            "claim": "Unsupported.",
                            "support_references": ["direct-observation:missing"],
                        }
                    ],
                }
        gateway = SequencedGateway((invalid, invalid, invalid))

        with self.assertRaises(DomainError) as raised:
            DirectSourceAnswerExecutor(
                gateway=gateway,
                configuration=self.configuration(),
                expected_model_fingerprint="model-fingerprint",
            ).execute(
                task_input=task_input(self.commit),
                connector=LocalGitConnector(str(self.repository)),
                run_id="unsupported",
            )

        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)
        self.assertEqual(len(gateway.contexts), 3)

    def test_invalid_finish_reference_is_retried_after_a_valid_read(self) -> None:
        run_id = "direct-reference-repair"
        finish = {
            "decision": "FINISH",
            "tool": "NONE",
            "revision": self.commit,
            "base": "",
            "path": "",
            "query": "",
            "cursor": "",
            "offset": "",
            "max_bytes": "",
            "page_size": "",
            "rationale": "The source directly answers the question.",
            "claims": [
                {
                    "claim": "App.value 的源码初始值是 3。",
                    "support_references": ["src/App.java"],
                }
            ],
        }
        corrected = {
            **finish,
            "claims": [
                {
                    "claim": "App.value 的源码初始值是 3。",
                    "support_references": [
                        f"direct-observation:{run_id}:1"
                    ],
                }
            ],
        }
        gateway = SequencedGateway(
            (
                {
                    "decision": "EXECUTE",
                    "tool": "READ",
                    "revision": self.commit,
                    "base": "",
                    "path": "src/App.java",
                    "query": "",
                    "cursor": "",
                    "offset": "",
                    "max_bytes": "16000",
                    "page_size": "",
                    "rationale": "Read the exact declaration.",
                    "claims": [],
                },
                finish,
                corrected,
            )
        )

        result = DirectSourceAnswerExecutor(
            gateway=gateway,
            configuration=self.configuration(),
            expected_model_fingerprint="model-fingerprint",
        ).execute(
            task_input=task_input(self.commit),
            connector=LocalGitConnector(str(self.repository)),
            run_id=run_id,
        )

        self.assertEqual(result.model_call_count, 3)
        self.assertEqual(result.source_action_count, 1)

    def test_empty_rationale_is_repaired_as_model_contract_output(self) -> None:
        run_id = "direct-rationale-repair"
        read = {
            "decision": "EXECUTE",
            "tool": "READ",
            "revision": self.commit,
            "base": "",
            "path": "src/App.java",
            "query": "",
            "cursor": "",
            "offset": "",
            "max_bytes": "16000",
            "page_size": "",
            "rationale": "",
            "claims": [],
        }
        corrected_read = {
            **read,
            "rationale": "Read the exact declaration.",
        }
        finish = {
            **corrected_read,
            "decision": "FINISH",
            "tool": "NONE",
            "revision": self.commit,
            "path": "",
            "max_bytes": "",
            "rationale": "The source directly answers the question.",
            "claims": [
                {
                    "claim": "App.value 的源码初始值是 3。",
                    "support_references": [
                        f"direct-observation:{run_id}:1"
                    ],
                }
            ],
        }
        gateway = SequencedGateway((read, corrected_read, finish))

        result = DirectSourceAnswerExecutor(
            gateway=gateway,
            configuration=self.configuration(),
            expected_model_fingerprint="model-fingerprint",
        ).execute(
            task_input=task_input(self.commit),
            connector=LocalGitConnector(str(self.repository)),
            run_id=run_id,
        )

        self.assertEqual(result.model_call_count, 3)
        self.assertEqual(result.source_action_count, 1)
        repair_state = next(
            item.content
            for item in gateway.contexts[1].manifest.items
            if item.item_id == "contract-repair"
        )
        self.assertIn(
            "direct answer rationale must be non-empty",
            repair_state,
        )

    def test_action_cannot_escape_the_sealed_revision(self) -> None:
        invalid = {
                    "decision": "EXECUTE",
                    "tool": "READ",
                    "revision": "f" * 40,
                    "base": "",
                    "path": "src/App.java",
                    "query": "",
                    "cursor": "",
                    "offset": "",
                    "max_bytes": "16000",
                    "page_size": "",
                    "rationale": "Try another revision.",
                    "claims": [],
                }
        gateway = SequencedGateway((invalid, invalid, invalid))

        with self.assertRaises(DomainError) as raised:
            DirectSourceAnswerExecutor(
                gateway=gateway,
                configuration=self.configuration(),
                expected_model_fingerprint="model-fingerprint",
            ).execute(
                task_input=task_input(self.commit),
                connector=LocalGitConnector(str(self.repository)),
                run_id="revision-escape",
            )

        self.assertEqual(raised.exception.code, ErrorCode.STRUCTURED_OUTPUT_INVALID)
        self.assertEqual(len(gateway.contexts), 3)

    def test_finish_accepts_only_the_exact_comparison_range_echo(self) -> None:
        parent = "a" * 40
        task = task_input(self.commit)
        task["revision_scope"] = {
            "kind": "PARENT_TO_TARGET",
            "parent": parent,
            "target": self.commit,
        }
        task["task_input_digest"] = digest_of(
            {
                key: value
                for key, value in task.items()
                if key != "task_input_digest"
            }
        ).value
        reference = "direct-observation:comparison:1"

        action = _parse_action(
            {
                "decision": "FINISH",
                "tool": "NONE",
                "revision": f"{parent}..{self.commit}",
                "base": parent,
                "path": "",
                "query": "",
                "cursor": "",
                "offset": "",
                "max_bytes": "",
                "page_size": "",
                "rationale": "The exact comparison answers the task.",
                "claims": [
                    {
                        "claim": "The exact comparison contains the change.",
                        "support_references": [reference],
                    }
                ],
            },
            task_input=task,
            observation_refs={reference},
        )

        self.assertTrue(action.finish)

    def test_execute_ignores_only_exact_scope_echoes(self) -> None:
        parent = "a" * 40
        task = task_input(self.commit)
        task["revision_scope"] = {
            "kind": "PARENT_TO_TARGET",
            "parent": parent,
            "target": self.commit,
        }
        task["task_input_digest"] = digest_of(
            {
                key: value
                for key, value in task.items()
                if key != "task_input_digest"
            }
        ).value

        action = _parse_action(
            {
                "decision": "EXECUTE",
                "tool": "COMPARE",
                "revision": self.commit,
                "base": parent,
                "path": "src/App.java",
                "query": "",
                "cursor": "",
                "offset": "",
                "max_bytes": "",
                "page_size": "",
                "rationale": "Compare the exact sealed range.",
                "claims": [],
            },
            task_input=task,
            observation_refs=set(),
        )

        self.assertFalse(action.finish)
        self.assertEqual(
            action.parameters,
            {"base": parent, "revision": self.commit},
        )


if __name__ == "__main__":
    unittest.main()
