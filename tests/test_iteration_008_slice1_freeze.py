from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json
import sys
import tempfile
import unittest
from unittest import mock

from software_world_model.cross_cutting import Digest
from software_world_model.interface import world_model_runtime
from validation.structure_world_model_iteration_008 import slice1_freeze


class Iteration008Slice1FreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.workspace = Path(__file__).resolve().parents[1]

    @staticmethod
    def _full_regression_command() -> tuple[str, ...]:
        return (
            sys.executable,
            "-B",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-v",
        )

    @staticmethod
    def _preserved_hold_output() -> str:
        lines: list[str] = []
        for outcome, test_id in slice1_freeze._PRESERVED_HOLD_TESTS:
            method = test_id.rsplit(".", 1)[-1]
            lines.append(f"{method} ({test_id}) ... {outcome}")
        for outcome, test_id in slice1_freeze._PRESERVED_HOLD_TESTS:
            method = test_id.rsplit(".", 1)[-1]
            marker = slice1_freeze._PRESERVED_HOLD_MARKERS[test_id][0]
            lines.extend(
                [
                    "=" * 70,
                    f"{outcome}: {method} ({test_id})",
                    "-" * 70,
                    "Traceback (most recent call last):",
                    marker,
                    "",
                ]
            )
        lines.extend(
            [
                "-" * 70,
                "Ran 100 tests in 1.000s",
                "",
                "FAILED (failures=4, errors=1)",
                "",
            ]
        )
        return "\n".join(lines)

    def test_launcher_file_closure_matches_the_bounded_runtime(self) -> None:
        frozen = slice1_freeze._launcher_files(self.workspace)
        runtime = world_model_runtime._launcher_files(include_bounded=True)

        self.assertEqual(set(frozen), set(runtime))
        self.assertEqual(
            {key: path.read_bytes() for key, path in frozen.items()},
            {key: path.read_bytes() for key, path in runtime.items()},
        )

    def test_candidate_stage_uses_the_bounded_answer_and_gateway(self) -> None:
        destination = self.root / "candidate-stage"
        slice1_freeze._candidate_stage(
            baseline=(
                self.workspace
                / "var/iteration-006/live/run-008/candidate-stage"
            ),
            producer=self.workspace,
            destination=destination,
        )

        assets = (
            self.workspace
            / "src/software_world_model/interface/world_model_runtime_assets"
        )
        self.assertEqual(
            (
                destination / "packages/answer/.g3b/answer_workload.py"
            ).read_bytes(),
            (
                assets / "bounded_java_source_semantics_answer_workload.py"
            ).read_bytes(),
        )
        self.assertEqual(
            (
                destination
                / "packages/gateway/.g3b/"
                "bounded_java_source_semantics_gateway_workload.py"
            ).read_bytes(),
            (
                assets / "bounded_java_source_semantics_gateway_workload.py"
            ).read_bytes(),
        )

    def test_gateway_freeze_binds_one_deepseek_authority_chain(self) -> None:
        stage = self.root / "stage"
        gateway_input = stage / "gateway-input"
        gateway_input.mkdir(parents=True)
        for name in world_model_runtime._GATEWAY_INPUT_FILES:
            (gateway_input / name).write_bytes(b"baseline")
        qualification = self.root / "qualification.json"
        closed = self.root / "closed.json"
        conformance_path = self.root / "conformance.json"
        for path in (qualification, closed, conformance_path):
            path.write_bytes(b"mocked")
        conformance_ref = (
            "CC-DEEPSEEK-CHAT-NO-TOOLS-001:sha256:" + "1" * 64
        )
        binding = SimpleNamespace(
            capability_qualification_ref=(
                "capability-evaluation:evaluation_result_" + "2" * 32
            ),
            capability_qualification_digest=Digest("sha256:" + "3" * 64),
            qualification_document_digest=Digest("sha256:" + "4" * 64),
            closed_capability_result_digest=Digest("sha256:" + "5" * 64),
            conformance_result_ref=conformance_ref,
        )
        conformance = SimpleNamespace(
            result_ref=conformance_ref,
            result_digest=Digest("sha256:" + "1" * 64),
        )

        with (
            mock.patch.object(
                slice1_freeze,
                "load_bounded_java_source_semantics_gateway_qualification_binding",
                return_value=binding,
            ),
            mock.patch.object(
                slice1_freeze,
                "load_deepseek_chat_conformance_qualification",
                return_value=conformance,
            ),
        ):
            value = slice1_freeze._install_gateway_input(
                stage=stage,
                qualification_path=qualification,
                closed_result_path=closed,
                conformance_result_path=conformance_path,
            )

        freeze = json.loads((gateway_input / "g3b-freeze.json").read_bytes())
        self.assertEqual(
            freeze["conformance_result_ref"],
            conformance_ref,
        )
        self.assertEqual(
            value["capability_qualification_digest"],
            binding.capability_qualification_digest.value,
        )
        self.assertEqual(
            freeze["egress_policy_digest"],
            slice1_freeze.BOUNDED_JAVA_SOURCE_SEMANTICS_MODEL_EGRESS_POLICY_FILE_DIGEST,
        )

    def test_user_held_suite_seals_variable_calls_and_no_question(self) -> None:
        path = slice1_freeze._user_held_suite(
            self.root,
            {"commit": "a" * 40, "tree": "b" * 40},
            {"read_set_id": "read_set_" + "c" * 32},
        )

        suite = json.loads(path.read_bytes())
        protocol = suite["comparison_protocols"]
        self.assertEqual(suite["cases"], [])
        self.assertEqual(protocol["minimum_model_calls_per_question"], 4)
        self.assertEqual(protocol["maximum_model_calls_per_question"], 6)
        self.assertEqual(protocol["selected_provider_type"], "DEEPSEEK")
        self.assertEqual(
            protocol["question_visibility_at_seal"],
            "NOT_DISCLOSED",
        )

    def test_full_regression_gate_accepts_only_the_exact_preserved_hold(
        self,
    ) -> None:
        value = slice1_freeze._full_regression_result(
            self._full_regression_command(),
            return_code=1,
            stdout="",
            stderr=self._preserved_hold_output(),
        )

        self.assertFalse(value["pass"])
        self.assertTrue(value["gate_pass"])
        self.assertEqual(
            value["gate_status"],
            "PASS_WITH_EXACT_PRESERVED_HISTORICAL_HOLD",
        )
        self.assertEqual(value["test_count"], 100)
        self.assertEqual(value["passed_test_count"], 95)

    def test_full_regression_gate_accepts_a_raw_full_pass(self) -> None:
        output = "\n".join(
            [
                *(
                    f"{test_id.rsplit('.', 1)[-1]} ({test_id}) ... ok"
                    for _, test_id in slice1_freeze._PRESERVED_HOLD_TESTS
                ),
                "-" * 70,
                "Ran 100 tests in 1.000s",
                "",
                "OK",
                "",
            ]
        )

        value = slice1_freeze._full_regression_result(
            self._full_regression_command(),
            return_code=0,
            stdout="",
            stderr=output,
        )

        self.assertTrue(value["pass"])
        self.assertEqual(value["gate_status"], "PASS")
        self.assertEqual(value["passed_test_count"], 100)
        self.assertEqual(value["preserved_hold_tests"], [])

    def test_full_regression_gate_rejects_any_additional_failure(self) -> None:
        output = self._preserved_hold_output().replace(
            "Ran 100 tests in 1.000s",
            "=" * 70
            + "\nFAIL: test_new_regression "
            "(test_new.NewTests.test_new_regression)\n"
            + "-" * 70
            + "\nAssertionError: new regression\n\n"
            "Ran 100 tests in 1.000s",
        ).replace(
            "FAILED (failures=4, errors=1)",
            "FAILED (failures=5, errors=1)",
        )

        with self.assertRaisesRegex(
            slice1_freeze.SliceFreezeError,
            "differs from the exact preserved historical hold",
        ):
            slice1_freeze._full_regression_result(
                self._full_regression_command(),
                return_code=1,
                stdout="",
                stderr=output,
            )

    def test_full_regression_gate_rejects_a_hold_reason_drift(self) -> None:
        output = self._preserved_hold_output().replace(
            "QUALIFICATION_INVALID: V-009 Adapter Conformance "
            "implementation drifted",
            "QUALIFICATION_INVALID: unrelated failure",
            1,
        )

        with self.assertRaisesRegex(
            slice1_freeze.SliceFreezeError,
            "reason marker drifted",
        ):
            slice1_freeze._full_regression_result(
                self._full_regression_command(),
                return_code=1,
                stdout="",
                stderr=output,
            )


if __name__ == "__main__":
    unittest.main()
