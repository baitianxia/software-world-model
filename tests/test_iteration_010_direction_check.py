from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from validation.iteration_010_mvp import direction_check


MODEL_PATH = Path(
    "src/software_world_model/ai_infrastructure/"
    "conversational_engineering_model.py"
)
MODEL_TEST_PATH = Path("tests/test_conversational_engineering_model.py")


def _run(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        list(arguments),
        cwd=repository,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


class DirectionCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repository = Path(self.temporary.name)
        _run(self.repository, "git", "init", "-q")
        _run(self.repository, "git", "config", "user.name", "Direction Test")
        _run(
            self.repository,
            "git",
            "config",
            "user.email",
            "direction@example.invalid",
        )
        self._write(MODEL_PATH, "legacy = True\n")
        self._write(MODEL_TEST_PATH, "legacy_test = True\n")
        _run(self.repository, "git", "add", ".")
        _run(self.repository, "git", "commit", "-qm", "baseline")
        self.base = _run(self.repository, "git", "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write(self, path: Path, value: str) -> None:
        target = self.repository / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8")

    def _check(self, evidence: Path | None = None) -> dict[str, object]:
        return direction_check.check_repository(
            self.repository,
            base=self.base,
            evidence_path=evidence,
        )

    def test_non_product_only_delta_resets_to_phase_a_without_stopping(self) -> None:
        self._write(Path("validation/iteration_010_mvp/check.py"), "safe = True\n")

        report = self._check()

        self.assertEqual(report["direction_verdict"], "PASS")
        self.assertEqual(report["progress_verdict"], "NO_PRODUCT_PROGRESS")
        self.assertEqual(report["next_phase"], "PHASE_A_SOURCE_ONLY_AGENT")

    def test_rejects_net_growth_in_frozen_legacy_surface(self) -> None:
        self._write(MODEL_PATH, "legacy = True\nlegacy_growth = True\n")

        report = self._check()

        self.assertEqual(report["direction_verdict"], "FAIL")
        self.assertIn(
            "LEGACY_PROTOCOL_NET_GROWTH",
            {item["code"] for item in report["violations"]},
        )

    def test_rejects_new_versioned_legacy_protocol(self) -> None:
        protocol = "ENGINEERING_" + "AGENT_SAMPLE@2"
        self._write(Path("src/software_world_model/new_agent.py"), repr(protocol))

        report = self._check()

        self.assertEqual(report["direction_verdict"], "FAIL")
        self.assertIn(
            "NEW_LEGACY_PROTOCOL_VERSION",
            {item["code"] for item in report["violations"]},
        )

    def test_agent_evidence_advances_next_task_to_world_model(self) -> None:
        self._write(Path("src/software_world_model/new_agent.py"), "agent = True\n")
        evidence = self.repository / "progress.json"
        evidence.write_text(
            json.dumps(
                {
                    "schema": direction_check.EVIDENCE_SCHEMA,
                    "knowledge_evidence": [],
                    "agent_behavior_evidence": ["trajectory:source-only"],
                    "browser_evidence": [],
                    "trajectory_evidence": ["trajectory:source-only"],
                    "replacement_experiment_evidence": [],
                    "verification_cases": ["V-HARNESS-BASELINE-001"],
                }
            ),
            encoding="utf-8",
        )

        report = self._check(evidence)

        self.assertEqual(report["direction_verdict"], "PASS")
        self.assertEqual(report["progress_verdict"], "CAPABILITY_EVIDENCE_PRESENT")
        self.assertEqual(report["next_phase"], "PHASE_B_WORLD_MODEL_COGNITION")

    def test_prompt_delta_requires_trajectory_and_replacement_experiment(self) -> None:
        self._write(MODEL_PATH, "replacement_prompt = True\n")

        report = self._check()

        self.assertEqual(report["direction_verdict"], "FAIL")
        self.assertIn(
            "PROMPT_SCHEMA_WITHOUT_LAYER_EVIDENCE",
            {item["code"] for item in report["violations"]},
        )


if __name__ == "__main__":
    unittest.main()
