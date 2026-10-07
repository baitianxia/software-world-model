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
        self._write(
            Path("docs/project/current.md"),
            "---\ncurrent_task: TASK-1-MINIMUM-COMPLETE-EXPERIENCE\n---\n",
        )
        self._write(
            direction_check.CURRENT_PLAN_PATH,
            "current task plan\n",
        )
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

    def test_non_product_only_delta_keeps_current_vertical_task_without_stopping(self) -> None:
        self._write(Path("validation/iteration_010_mvp/check.py"), "safe = True\n")

        report = self._check()

        self.assertEqual(report["direction_verdict"], "NO_STATIC_RISK")
        self.assertEqual(report["progress_verdict"], "NOT_ASSESSED")
        self.assertEqual(report["decision"], "NO_STATIC_RISK_SIGNALS")
        self.assertEqual(report["next_action"], direction_check.TASK_1)
        self.assertEqual(report["earliest_layer"], "not-assessed")

    def test_rejects_net_growth_in_frozen_legacy_surface(self) -> None:
        self._write(MODEL_PATH, "legacy = True\nlegacy_growth = True\n")

        report = self._check()

        self.assertEqual(report["direction_verdict"], "STATIC_RISK")
        self.assertIn(
            "LEGACY_PROTOCOL_NET_GROWTH",
            {item["code"] for item in report["violations"]},
        )

    def test_rejects_new_versioned_legacy_protocol(self) -> None:
        protocol = "ENGINEERING_" + "AGENT_SAMPLE@2"
        self._write(Path("src/software_world_model/new_agent.py"), repr(protocol))

        report = self._check()

        self.assertEqual(report["direction_verdict"], "STATIC_RISK")
        self.assertIn(
            "NEW_LEGACY_PROTOCOL_VERSION",
            {item["code"] for item in report["violations"]},
        )

    def test_allows_thin_reference_to_protocol_already_present_at_base(self) -> None:
        protocol = "ENGINEERING_" + "AGENT_EXISTING@1"
        self._write(MODEL_PATH, f"legacy = True\nprotocol = {protocol!r}\n")
        _run(self.repository, "git", "add", ".")
        _run(self.repository, "git", "commit", "-qm", "protocol baseline")
        self.base = _run(self.repository, "git", "rev-parse", "HEAD")
        self._write(
            Path("src/software_world_model/new_agent.py"),
            f"thin_adapter = {protocol!r}\n",
        )

        report = self._check()

        self.assertEqual(report["direction_verdict"], "NO_STATIC_RISK")

    def test_agent_evidence_does_not_create_a_second_phase(self) -> None:
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

        self.assertEqual(report["direction_verdict"], "NO_STATIC_RISK")
        self.assertEqual(report["progress_verdict"], "NOT_ASSESSED")
        self.assertEqual(report["decision"], "NO_STATIC_RISK_SIGNALS")
        self.assertEqual(report["next_action"], direction_check.TASK_1)
        self.assertEqual(report["earliest_layer"], "not-assessed")

    def test_agent_and_knowledge_evidence_without_browser_stays_in_task_one(self) -> None:
        self._write(Path("src/software_world_model/new_agent.py"), "agent = True\n")
        self._write(Path("src/software_world_model/new_cognition.py"), "cognition = True\n")
        evidence = self.repository / "progress.json"
        evidence.write_text(
            json.dumps(
                {
                    "schema": direction_check.EVIDENCE_SCHEMA,
                    "knowledge_evidence": ["cognition:five-tasks"],
                    "agent_behavior_evidence": ["trajectory:source-only"],
                    "browser_evidence": [],
                    "trajectory_evidence": ["trajectory:source-only"],
                    "replacement_experiment_evidence": [],
                    "verification_cases": [
                        "V-HARNESS-BASELINE-001",
                        "V-WORLD-MODEL-COGNITION-001",
                    ],
                }
            ),
            encoding="utf-8",
        )

        report = self._check(evidence)

        self.assertEqual(report["direction_verdict"], "NO_STATIC_RISK")
        self.assertEqual(report["progress_verdict"], "NOT_ASSESSED")
        self.assertEqual(report["decision"], "NO_STATIC_RISK_SIGNALS")
        self.assertEqual(report["next_action"], direction_check.TASK_1)
        self.assertEqual(report["earliest_layer"], "not-assessed")

    def test_prompt_delta_requires_trajectory_and_replacement_experiment(self) -> None:
        self._write(MODEL_PATH, "replacement_prompt = True\n")

        report = self._check()

        self.assertEqual(report["direction_verdict"], "STATIC_RISK")
        self.assertIn(
            "PROMPT_SCHEMA_WITHOUT_LAYER_EVIDENCE",
            {item["code"] for item in report["violations"]},
        )

    def test_stale_report_is_rejected_after_current_plan_changes(self) -> None:
        report = self._check()
        report_path = self.repository / "report.json"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        self.assertTrue(
            direction_check.validate_report(self.repository, report_path)["valid"]
        )
        self._write(direction_check.CURRENT_PLAN_PATH, "changed current task plan\n")
        validation = direction_check.validate_report(self.repository, report_path)
        self.assertFalse(validation["valid"])
        self.assertIn("current_plan_digest", validation["mismatches"])

    def test_current_task_is_read_from_project_context_not_evidence(self) -> None:
        self._write(
            Path("docs/project/current.md"),
            "---\ncurrent_task: TASK-2-DIRECTION-AND-ATTRIBUTION\n---\n",
        )
        evidence = self.repository / "progress.json"
        evidence.write_text(
            json.dumps(
                {
                    "schema": direction_check.EVIDENCE_SCHEMA,
                    "knowledge_evidence": ["declared"],
                    "agent_behavior_evidence": ["declared"],
                    "browser_evidence": ["declared"],
                    "trajectory_evidence": ["declared"],
                    "replacement_experiment_evidence": ["declared"],
                    "verification_cases": ["declared"],
                }
            ),
            encoding="utf-8",
        )
        report = self._check(evidence)
        self.assertEqual(report["current_task"], direction_check.TASK_2)
        self.assertEqual(report["next_action"], direction_check.TASK_2)
        self.assertEqual(report["progress_verdict"], "NOT_ASSESSED")

    def test_default_base_is_head_and_uncommitted_workspace_is_reported(self) -> None:
        self._write(Path("validation/iteration_010_mvp/check.py"), "safe = True\n")
        report = direction_check.check_repository(self.repository)
        self.assertEqual(report["baseline"], report["head"])
        self.assertTrue(report["changed_paths"])
        self.assertTrue(report["candidate_delta_digest"].startswith("sha256:"))

    def test_report_validation_detects_head_change(self) -> None:
        report = self._check()
        report_path = self.repository / "report.json"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        self._write(Path("new.txt"), "new\n")
        _run(self.repository, "git", "add", "new.txt")
        _run(self.repository, "git", "commit", "-qm", "next")
        validation = direction_check.validate_report(self.repository, report_path)
        self.assertFalse(validation["valid"])
        self.assertIn("head", validation["mismatches"])

    def test_report_validation_detects_workspace_change(self) -> None:
        report = self._check()
        report_path = self.repository / "report.json"
        report_path.write_text(json.dumps(report), encoding="utf-8")
        self._write(Path("validation/iteration_010_mvp/check.py"), "changed = True\n")
        validation = direction_check.validate_report(self.repository, report_path)
        self.assertFalse(validation["valid"])
        self.assertIn("workspace_digest", validation["mismatches"])

    def test_static_signal_is_non_blocking_cli_output(self) -> None:
        self._write(MODEL_PATH, "legacy = True\nlegacy_growth = True\n")
        self.assertEqual(
            direction_check.main(["--repository", str(self.repository)]),
            0,
        )


if __name__ == "__main__":
    unittest.main()
