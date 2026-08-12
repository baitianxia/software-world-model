from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
G0_SOURCE = ROOT / "validation/structure_world_model_iteration_005/g0.py"
G0_INPUTS = ROOT / "validation/structure_world_model_iteration_005/g0_inputs.json"


class Iteration005G0AssetTests(unittest.TestCase):
    def test_oracle_is_closed_and_runner_does_not_import_product_package(self) -> None:
        inputs = json.loads(G0_INPUTS.read_text(encoding="utf-8"))

        self.assertEqual(inputs["schema"], "ITER-005-G0-INPUTS@1")
        self.assertEqual(len(inputs["supported_cases"]), 2)
        self.assertEqual(
            len({item["repository_path"] for item in inputs["supported_cases"]}),
            2,
        )
        for case in inputs["supported_cases"]:
            self.assertGreaterEqual(len(case["modules"]), 2)
            self.assertTrue(case["internal_dependencies"])
            self.assertTrue(case["absent_dependencies"])
            self.assertRegex(case["commit"], r"^[0-9a-f]{40}$")
            self.assertRegex(case["tree"], r"^[0-9a-f]{40}$")
        sequence = inputs["unsupported_sequence"]
        self.assertNotEqual(sequence["valid"]["commit"], sequence["unsupported"]["commit"])
        self.assertIn("REACTOR_DEPENDENCY_SHAPE_UNSUPPORTED", sequence["unsupported"]["message_contains"])

        source = G0_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("from software_world_model", source)
        self.assertNotIn("import software_world_model", source)

    def test_markdown_report_preserves_pass_and_rejection_evidence(self) -> None:
        specification = importlib.util.spec_from_file_location("iter005_g0", G0_SOURCE)
        assert specification is not None and specification.loader is not None
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        report = {
            "status": "PASS",
            "supported": [
                {
                    "case_id": "A",
                    "commit": "a" * 40,
                    "modules": 2,
                    "dependency_relations": 1,
                    "absence_checks": 1,
                }
            ],
            "unsupported_sequence": {
                "case_id": "B",
                "valid_commit": "b" * 40,
                "unsupported_commit": "c" * 40,
                "rejection_error": "INVALID_ARGUMENT",
                "current_after": "structure_snapshot_" + "d" * 32,
            },
        }

        rendered = module._report_markdown(report)

        self.assertIn("Overall: **PASS**", rendered)
        self.assertIn("INVALID_ARGUMENT", rendered)
        self.assertIn("CURRENT unchanged", rendered)


if __name__ == "__main__":
    unittest.main()
