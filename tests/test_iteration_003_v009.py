from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import re
import tempfile
import unittest

from software_world_model.ai_infrastructure import (
    DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT,
    ProviderHTTPResponse,
    ProviderOutcomeUnknown,
    VolcengineArkModelConfiguration,
)
from software_world_model.cross_cutting import digest_of
from tests.test_ark_chat_conformance import EchoingArkTransport
from validation.structure_world_model_iteration_003.v009.cli import main as v009_main
from validation.structure_world_model_iteration_003.v009.inputs import (
    load_input_freeze,
    verify_input_freeze_runtime,
)
from validation.structure_world_model_iteration_003.v009.live_runner import (
    EVALUATOR_SCRIPT,
    verify_evaluator_source,
)


class PerfectWorldModelTransport:
    def __init__(self) -> None:
        self.calls = 0
        self.model_inputs = []

    def post_json(self, **arguments):
        self.calls += 1
        body = json.loads(arguments["body"])
        self.assert_closed_wire_request(body)
        state = json.loads(body["messages"][2]["content"])
        self.model_inputs.append(state)
        output = self.output(state)
        return ProviderHTTPResponse(
            status_code=200,
            headers={"x-tt-logid": f"v009-live-{self.calls}"},
            body=json.dumps(
                {
                    "id": f"chatcmpl_v009_{self.calls}",
                    "object": "chat.completion",
                    "model": DEFAULT_VOLCENGINE_ARK_ACTUAL_MODEL_FINGERPRINT,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": json.dumps(
                                    output,
                                    ensure_ascii=False,
                                    separators=(",", ":"),
                                ),
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 100,
                        "completion_tokens": 40,
                        "total_tokens": 140,
                    },
                }
            ).encode("utf-8"),
        )

    @staticmethod
    def assert_closed_wire_request(body):
        assert body["tools"] == []
        assert body["tool_choice"] == "none"
        assert body["stream"] is False
        serialized = json.dumps(body["messages"], ensure_ascii=False)
        assert "expected_normalized_result" not in serialized
        assert "projection_fields" not in serialized
        assert "forbidden_events" not in serialized
        assert "WM-PRODUCT-" not in serialized

    @staticmethod
    def output(state):
        capability = state["capability"]
        value = state["input"]
        if capability == "REQUIREMENT_FIDELITY":
            return {
                "need_keys": [
                    "inventory_left",
                    "inventory_right",
                    "paths_left",
                    "paths_right",
                    "new_paths",
                ],
                "joint_constraints": [
                    {
                        "kind": "ORDERED_READ_SET",
                        "base": "snapshot_left",
                        "target": "snapshot_right",
                    }
                ],
            }
        if capability == "GENERIC_QUERY_PLANNING":
            left, right = value["read_set"]
            source = value["source_entity_ref"]
            target = value["target_entity_ref"]
            return {
                "operations": [
                    {"operation": "inventory", "snapshot": left},
                    {"operation": "inventory", "snapshot": right},
                    {
                        "operation": "all_simple_paths",
                        "snapshot": left,
                        "source_ref": source,
                        "target_ref": target,
                    },
                    {
                        "operation": "all_simple_paths",
                        "snapshot": right,
                        "source_ref": source,
                        "target_ref": target,
                    },
                    {
                        "operation": "ordered_snapshot_diff",
                        "base": left,
                        "target": right,
                    },
                ]
            }
        if capability == "COMPLETE_NEGATIVE_ANSWER":
            relation = re.sub(
                r"[^A-Za-z0-9]",
                "_",
                value["modeled_relation"].split("@", 1)[0].upper(),
            )
            return {
                "need_status": "SATISFIED_SUPPORTED_NEGATIVE",
                "claim_scope": f"NO_PATH_IN_{relation}_FOR_EXACT_READ_SET",
            }
        if capability == "VIEW_LIMITATION_AND_KNOWLEDGE_GAP":
            return {
                "view_result": {
                    "status": "LIMITED",
                    "code": "COVERAGE_PARTIAL",
                    "owner": "STRUCTURE_VIEW",
                },
                "need_assessment": {
                    "status": "KNOWLEDGE_GAP",
                    "code": "INSUFFICIENT_COMPLETE_COVERAGE",
                    "owner": "KNOWLEDGE_USE",
                },
            }
        if capability == "ORDERED_DIFF_EXPRESSION":
            return {
                "direction": {"base": value["base"], "target": value["target"]},
                "added_entities": value["target_added"],
            }
        if capability == "INDEPENDENT_ANSWER_REVIEW":
            codes = {
                "omitted_need": "NEED_OMITTED",
                "wrong_snapshot_reference": "WRONG_READ_SET",
                "unsupported_reason": "UNSUPPORTED_REASON",
                "evidence_excerpt_expansion": "EVIDENCE_PAYLOAD_EXPANSION",
            }
            return {
                "decision": "REJECT",
                "finding_codes": [codes[item] for item in value["draft_faults"]],
            }
        if capability == "ENTITY_CANDIDATE_RESOLUTION":
            return {
                "resolution_status": "AMBIGUOUS",
                "candidate_refs": value["candidate_refs"],
                "next_operation_allowed": False,
            }
        raise AssertionError(f"unexpected capability: {capability}")


class UnknownTransport:
    def post_json(self, **arguments):
        raise ProviderOutcomeUnknown(
            "fixture unknown outcome",
            reason_code="FIXTURE_PROVIDER_OUTCOME_UNKNOWN",
        )


class Iteration003V009Tests(unittest.TestCase):
    def test_input_freeze_and_evaluator_are_mechanically_closed(self):
        frozen = load_input_freeze()
        verify_input_freeze_runtime(
            frozen,
            configuration=VolcengineArkModelConfiguration(),
            repository_state={
                "head": "a" * 40,
                "tree": "b" * 40,
                "clean": True,
                "g3a_result_is_ancestor": True,
            },
            environment={"ARK_API_KEY": "fixture-secret-never-persist"},
        )
        verify_evaluator_source(EVALUATOR_SCRIPT)
        source = EVALUATOR_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("software_world_model", source)
        self.assertEqual(
            frozen["freeze_ref"], "ITER-003-V009-EXACT-INPUTS@1.0.3"
        )
        self.assertEqual(
            frozen["predecessor"]["outcome"],
            "PASS_VALID_BASELINE_BLOCKED",
        )
        self.assertEqual(
            frozen["predecessor"]["capability_result_id"],
            "evaluation_result_0319e8c9c3254c92a59b89f9c32ac0c6",
        )
        self.assertEqual(frozen["predecessor"]["blocked_by"], "FINDING-003-017")
        self.assertFalse(frozen["disclosure"]["g3b_product_dispatch_included"])

    def test_conformance_unknown_seals_pre_dispatch_intent_and_stays_blocking(self):
        output = StringIO()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "conformance"
            code = v009_main(
                [
                    "run-conformance",
                    "--result-directory",
                    str(root),
                    "--freeze-checkpoint",
                    "a" * 40,
                ],
                stdout=output,
                environment={"ARK_API_KEY": "fixture-secret-never-persist"},
                transport=UnknownTransport(),
                repository_state={
                    "head": "a" * 40,
                    "tree": "b" * 40,
                    "clean": True,
                    "g3a_result_is_ancestor": True,
                },
            )
            summary = json.loads(output.getvalue())
            self.assertEqual(code, 3)
            self.assertEqual(summary["status"], "PROVIDER_OUTCOME_UNKNOWN")
            self.assertTrue((root / "conformance-invocation.json").is_file())
            self.assertTrue((root / "conformance-unknown.json").is_file())
            self.assertFalse((root / "conformance-binding.json").exists())

    def test_closed_live_harness_seals_all_seven_cases_and_valid_qualification(self):
        environment = {"ARK_API_KEY": "fixture-secret-never-persist"}
        transport = PerfectWorldModelTransport()
        output = StringIO()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            freeze_checkpoint = "a" * 40
            repository_state = {
                "head": freeze_checkpoint,
                "tree": "b" * 40,
                "clean": True,
                "g3a_result_is_ancestor": True,
            }
            conformance_output = StringIO()
            conformance_code = v009_main(
                [
                    "run-conformance",
                    "--result-directory",
                    str(root / "conformance"),
                    "--freeze-checkpoint",
                    freeze_checkpoint,
                ],
                stdout=conformance_output,
                environment=environment,
                transport=EchoingArkTransport(),
                repository_state=repository_state,
            )
            conformance_summary = json.loads(conformance_output.getvalue())
            self.assertEqual(conformance_code, 0, conformance_output.getvalue())
            self.assertEqual(conformance_summary["status"], "CONFORMANCE_PASS")
            invocation = json.loads(
                (root / "conformance" / "conformance-invocation.json").read_text()
            )
            self.assertEqual(
                invocation["conformance"]["execution_protocol"],
                "V009_PRECALL_SEALED_INVOCATION_AND_EXACT_RESULT_BINDING@1",
            )
            self.assertEqual(
                invocation["conformance"]["timeout_milliseconds"], 30_000
            )
            self.assertEqual(invocation["conformance"]["max_output_tokens"], 96)

            result_directory = root / "ce"
            code = v009_main(
                [
                    "run-all",
                    "--conformance-binding",
                    str(conformance_summary["binding_path"]),
                    "--result-directory",
                    str(result_directory),
                    "--freeze-checkpoint",
                    freeze_checkpoint,
                ],
                stdout=output,
                environment=environment,
                transport=transport,
                repository_state=repository_state,
            )
            summary = json.loads(output.getvalue())

            self.assertEqual(code, 0, output.getvalue())
            self.assertEqual(summary["status"], "CAPABILITY_EVALUATION_PASS")
            self.assertEqual(summary["case_count"], 7)
            self.assertEqual(summary["passed_case_count"], 7)
            self.assertEqual(summary["failed_case_count"], 0)
            self.assertEqual(summary["unknown_case_count"], 0)
            self.assertEqual(summary["provider_request_count"], 7)
            self.assertTrue(summary["g3b_unblocked"])
            self.assertFalse(summary["production_eligible"])
            self.assertTrue(Path(summary["result_path"]).is_file())
            self.assertTrue(Path(summary["qualification_path"]).is_file())
            closed = json.loads(Path(summary["result_path"]).read_text())
            self.assertEqual(closed["closed_result_status"], "PASS_VALID")
            self.assertEqual(closed["failure_count"], 0)
            self.assertEqual(closed["unknown_count"], 0)
            self.assertEqual(
                closed["provider"]["conformance_binding_digest"],
                conformance_summary["binding_digest"],
            )
            self.assertEqual(len(closed["attempts"]), 7)
            for case_id in closed["result"]["passed_case_ids"]:
                evidence = json.loads(
                    (result_directory / "cases" / case_id / "case-evidence.json").read_text()
                )
                self.assertEqual(
                    evidence["independent_review"]["conclusion"], "PASS"
                )
                self.assertNotEqual(
                    evidence["sink_manifest"]["evaluator_pid"],
                    evidence["sink_manifest"]["generator_pid"],
                )

        self.assertEqual(transport.calls, 7)
        self.assertTrue(
            all(
                "expected_normalized_result" not in json.dumps(item)
                for item in transport.model_inputs
            )
        )
        self.assertNotIn("fixture-secret-never-persist", output.getvalue())

    def test_closed_evaluation_rejects_semantically_tampered_conformance_binding(self):
        environment = {"ARK_API_KEY": "fixture-secret-never-persist"}
        repository_state = {
            "head": "a" * 40,
            "tree": "b" * 40,
            "clean": True,
            "g3a_result_is_ancestor": True,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            conformance_output = StringIO()
            code = v009_main(
                [
                    "run-conformance",
                    "--result-directory",
                    str(root / "conformance"),
                    "--freeze-checkpoint",
                    "a" * 40,
                ],
                stdout=conformance_output,
                environment=environment,
                transport=EchoingArkTransport(),
                repository_state=repository_state,
            )
            self.assertEqual(code, 0, conformance_output.getvalue())
            conformance_summary = json.loads(conformance_output.getvalue())
            invocation_path = root / "conformance" / "conformance-invocation.json"
            invocation = json.loads(invocation_path.read_text())
            invocation["conformance"]["timeout_milliseconds"] = 1
            invocation_core = {
                key: value
                for key, value in invocation.items()
                if key != "document_digest"
            }
            invocation["document_digest"] = digest_of(invocation_core).value
            invocation_path.write_text(
                json.dumps(invocation, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            binding_path = Path(conformance_summary["binding_path"])
            binding = json.loads(binding_path.read_text())
            binding["invocation_document_digest"] = invocation["document_digest"]
            binding_core = {
                key: value for key, value in binding.items() if key != "document_digest"
            }
            binding["document_digest"] = digest_of(binding_core).value
            binding_path.write_text(
                json.dumps(binding, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            transport = PerfectWorldModelTransport()
            evaluation_output = StringIO()
            code = v009_main(
                [
                    "run-all",
                    "--conformance-binding",
                    str(binding_path),
                    "--result-directory",
                    str(root / "ce"),
                    "--freeze-checkpoint",
                    "a" * 40,
                ],
                stdout=evaluation_output,
                environment=environment,
                transport=transport,
                repository_state=repository_state,
            )
            summary = json.loads(evaluation_output.getvalue())
            self.assertEqual(code, 2)
            self.assertEqual(summary["error"], "QUALIFICATION_INVALID")
            self.assertEqual(transport.calls, 0)


if __name__ == "__main__":
    unittest.main()
