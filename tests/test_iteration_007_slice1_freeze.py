from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from validation.structure_world_model_iteration_007 import slice1_freeze
from software_world_model.interface import world_model_runtime
from tests._environment import requires_path


class Iteration007Slice1FreezeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.workspace = Path(__file__).resolve().parents[1]

    def test_launcher_file_closure_matches_the_runtime(self) -> None:
        frozen = slice1_freeze._launcher_files(self.workspace)
        runtime = world_model_runtime._launcher_files()

        self.assertEqual(set(frozen), set(runtime))
        self.assertTrue(all(path.is_file() for path in frozen.values()))
        self.assertEqual(
            {key: path.read_bytes() for key, path in frozen.items()},
            {key: path.read_bytes() for key, path in runtime.items()},
        )

    def test_user_held_suite_seals_no_question(self) -> None:
        path = slice1_freeze._user_held_suite(
            self.root,
            {"commit": "a" * 40, "tree": "b" * 40},
            {"read_set_id": "read_set_" + "c" * 32},
        )

        suite = json.loads(path.read_bytes())
        self.assertEqual(suite["cases"], [])
        self.assertEqual(
            suite["comparison_protocols"]["question_visibility_at_seal"],
            "NOT_DISCLOSED",
        )
        self.assertEqual(
            suite["source_closures"]["user_canary"],
            "NOT_DISCLOSED_UNTIL_AFTER_PRODUCT_CODE_FREEZE",
        )
        self.assertEqual(suite["world_model_result_count_at_seal"], 0)

    @requires_path("var/iteration-006/live/run-008/candidate-stage", "ITER-006 accepted candidate stage")
    def test_candidate_stage_replaces_each_role_with_the_frozen_source(self) -> None:
        destination = self.root / "candidate-stage"
        slice1_freeze._candidate_stage(
            baseline=(
                self.workspace
                / "var/iteration-006/live/run-008/candidate-stage"
            ),
            producer=self.workspace,
            destination=destination,
        )

        expected_init = (
            self.workspace / "src/software_world_model/__init__.py"
        ).read_bytes()
        for role in ("answer", "broker", "gateway", "projector"):
            self.assertEqual(
                (
                    destination
                    / "packages"
                    / role
                    / "software_world_model/__init__.py"
                ).read_bytes(),
                expected_init,
            )
        self.assertEqual(
            (
                destination
                / "packages/answer/.g3b/answer_workload.py"
            ).read_bytes(),
            (
                self.workspace
                / "src/software_world_model/interface/"
                "world_model_runtime_assets/"
                "java_source_semantics_answer_workload.py"
            ).read_bytes(),
        )
        self.assertTrue(
            (
                destination
                / "packages/gateway/.g3b/"
                "java_source_semantics_gateway_workload.py"
            ).is_file()
        )

        package_root = destination / "packages/answer"
        entrypoint = package_root / ".g3b/answer_workload.py"
        import_probe = subprocess.run(
            (
                sys.executable,
                *world_model_runtime.SANDBOXED_PYTHON_FLAGS,
                "-c",
                (
                    "import runpy,sys;"
                    "sys.path.insert(0,sys.argv[1]);"
                    "runpy.run_path(sys.argv[2],run_name='answer_import_probe');"
                    "print(int('tree_sitter' in sys.modules));"
                    "print(int('tree_sitter_java' in sys.modules))"
                ),
                str(package_root),
                str(entrypoint),
            ),
            cwd=package_root,
            env=world_model_runtime._role_environment(self.root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        self.assertEqual(
            import_probe.returncode,
            0,
            msg=f"stdout={import_probe.stdout}\nstderr={import_probe.stderr}",
        )
        self.assertEqual(import_probe.stdout.splitlines(), ["0", "0"])

    def test_visible_fixture_builds_and_queries_source_off(self) -> None:
        producer = self.root / "producer-source"
        producer.mkdir()
        identity = slice1_freeze._source_snapshot(self.workspace, producer)
        output = self.root / "visible-product"
        output.mkdir()

        fixture, commands = slice1_freeze._visible_workspace(
            workspace=self.workspace,
            producer=producer,
            output=output,
            identity=identity,
        )

        self.assertEqual(len(commands), 5)
        self.assertTrue(Path(str(fixture["database"])).is_file())
        self.assertTrue(Path(str(fixture["bundle_root"])).is_dir())
        probe = json.loads(
            (output / "deterministic-product-probe.json").read_bytes()
        )
        self.assertEqual(probe["status"], "PASS")
        self.assertEqual(probe["ordered_atom_count"], 6)
        self.assertEqual(probe["legacy_call_count"], 2)
        self.assertEqual(probe["source_off_query"], "PASS")


if __name__ == "__main__":
    unittest.main()
