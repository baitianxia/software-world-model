from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from validation.iteration_010_mvp import independent_supervision as supervision


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


def _digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class IndependentSupervisionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.candidate = root / "candidate"
        self.source = root / "source"
        self.candidate.mkdir()
        self.source.mkdir()
        self._init_repository(self.candidate, "codex/development")
        self._init_repository(self.source, "source-main")

        self._write(self.candidate, "README.md", "product baseline\n")
        self._commit(self.candidate, "product baseline")
        self.product_baseline = _run(self.candidate, "git", "rev-parse", "HEAD")

        self._write(self.candidate, "docs/plan.md", "phase B\n")
        self._commit(self.candidate, "trusted plan")
        self.plan_commit = _run(self.candidate, "git", "rev-parse", "HEAD")

        self._write(
            self.candidate,
            "src/software_world_model/knowledge_engine/cognition.py",
            "relation = 'inherit'\n",
        )
        self._write(self.candidate, "evidence/phase-b.json", '{"checked":true}\n')
        self._commit(self.candidate, "candidate")

        self._write(self.source, "Truth.java", "interface Truth {}\n")
        self._commit(self.source, "source")
        self.source_commit = _run(self.source, "git", "rev-parse", "HEAD")

        self.control = {
            "schema": supervision.CONTROL_SCHEMA,
            "iteration": "ITER-010",
            "candidate_branch": "codex/development",
            "supervision_branch": "codex/supervision",
            "trusted_product_baseline_commit": self.product_baseline,
            "trusted_plan_commit": self.plan_commit,
            "source_commit": self.source_commit,
            "active_phase": "B",
            "next_phase": "C",
            "phase_exit_case_id": "V-WORLD-MODEL-COGNITION-001",
            "phase_exit_requirements": [
                "declaration-inheritance-closure",
                "bounded-cognition-retrieval",
                "truthful-coverage-and-source",
                "five-independent-unseen-tasks",
            ],
            "objective": "close reusable cognition before browser integration",
            "check_interval_minutes": 30,
        }
        self.state = supervision.capture_candidate(self.candidate, self.control)
        self.assessment = {
            "schema": supervision.ASSESSMENT_SCHEMA,
            "iteration": "ITER-010",
            "candidate_branch": "codex/development",
            "candidate_commit": self.state.head,
            "candidate_tree": self.state.tree,
            "candidate_worktree_digest": self.state.worktree_digest,
            "source_commit": self.source_commit,
            "phase": "B",
            "verdict": "REWORK",
            "assessor": "independent-supervisor",
            "assessed_at": "2026-09-01T21:00:00+08:00",
            "evidence": [
                {
                    "id": "candidate-evidence",
                    "scope": "candidate",
                    "path": "evidence/phase-b.json",
                    "sha256": _digest(self.candidate / "evidence/phase-b.json"),
                },
                {
                    "id": "source-truth",
                    "scope": "source",
                    "path": "Truth.java",
                    "sha256": _digest(self.source / "Truth.java"),
                },
            ],
            "completed_requirements": ["truthful-coverage-and-source"],
            "unresolved_requirements": [
                "declaration-inheritance-closure",
                "bounded-cognition-retrieval",
                "five-independent-unseen-tasks",
            ],
            "defects": [
                {
                    "severity": "MAJOR",
                    "owner_layer": "cognition-retrieval",
                    "summary": "declaration closure is incomplete",
                    "evidence_ids": ["candidate-evidence", "source-truth"],
                }
            ],
            "earliest_divergence": "cognition-retrieval",
            "next_action": "repair general declaration retrieval",
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def _init_repository(repository: Path, branch: str) -> None:
        _run(repository, "git", "init", "-q")
        _run(repository, "git", "config", "user.name", "Supervisor Test")
        _run(
            repository,
            "git",
            "config",
            "user.email",
            "supervisor@example.invalid",
        )
        _run(repository, "git", "switch", "-qc", branch)

    @staticmethod
    def _write(repository: Path, relative: str, value: str) -> None:
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8")

    @staticmethod
    def _commit(repository: Path, message: str) -> None:
        _run(repository, "git", "add", ".")
        _run(repository, "git", "commit", "-qm", message)

    def _audit(
        self,
        assessment: dict[str, object] | None = None,
        *,
        supervisor_branch: str | None = "codex/supervision",
    ) -> dict[str, object]:
        return supervision.audit(
            self.control,
            assessment or self.assessment,
            self.candidate,
            self.source,
            supervisor_branch=supervisor_branch,
            supervisor_commit="f" * 40,
        )

    def _passing_assessment(self) -> dict[str, object]:
        assessment = copy.deepcopy(self.assessment)
        assessment.update(
            {
                "verdict": "PASS",
                "completed_requirements": list(
                    self.control["phase_exit_requirements"]
                ),
                "unresolved_requirements": [],
                "defects": [],
                "earliest_divergence": "none",
                "next_action": "advance",
            }
        )
        return assessment

    def test_rework_corrects_without_stopping_or_authorization(self) -> None:
        report = self._audit()

        self.assertEqual(report["decision"], "CORRECT")
        self.assertEqual(report["active_phase"], "B")
        self.assertFalse(report["phase_change_allowed"])
        self.assertFalse(report["candidate_self_report_used"])
        self.assertFalse(report["task_should_stop"])
        self.assertFalse(report["authorization_required"])

    def test_clean_independent_pass_is_the_only_advance_path(self) -> None:
        report = self._audit(self._passing_assessment())

        self.assertEqual(report["decision"], "ADVANCE")
        self.assertEqual(report["advance_to"], "C")
        self.assertTrue(report["phase_change_allowed"])
        self.assertFalse(report["task_should_stop"])

    def test_uncommitted_change_is_observed_and_stales_old_assessment(self) -> None:
        self._write(
            self.candidate,
            "src/software_world_model/knowledge_engine/cognition.py",
            "relation = 'implements'\n",
        )

        report = self._audit()
        current = supervision.capture_candidate(self.candidate, self.control)

        self.assertFalse(current.clean)
        self.assertNotEqual(current.worktree_digest, self.state.worktree_digest)
        self.assertEqual(report["decision"], "CONTINUE")
        self.assertIn("candidate-worktree-changed", report["stale_reasons"])
        self.assertFalse(report["task_should_stop"])

    def test_even_fresh_pass_for_dirty_worktree_cannot_advance(self) -> None:
        self._write(
            self.candidate,
            "src/software_world_model/knowledge_engine/cognition.py",
            "relation = 'implements'\n",
        )
        state = supervision.capture_candidate(self.candidate, self.control)
        assessment = self._passing_assessment()
        assessment["candidate_worktree_digest"] = state.worktree_digest

        report = self._audit(assessment)

        self.assertEqual(report["decision"], "CONTINUE")
        self.assertEqual(report["assessment_status"], "FRESH-NOT-ADVANCEABLE")
        self.assertFalse(report["phase_change_allowed"])

    def test_wrong_candidate_branch_recovers_supervision_not_development(self) -> None:
        _run(self.candidate, "git", "switch", "-qc", "codex/wrong-target")

        report = self._audit()

        self.assertEqual(report["decision"], "RECOVER_SUPERVISION")
        self.assertIn("candidate-branch-mismatch", report["binding_errors"])
        self.assertFalse(report["task_should_stop"])
        self.assertFalse(report["authorization_required"])

    def test_wrong_supervision_branch_recovers_supervision(self) -> None:
        report = self._audit(supervisor_branch="codex/old-supervision")

        self.assertEqual(report["decision"], "RECOVER_SUPERVISION")
        self.assertIn("supervision-branch-mismatch", report["binding_errors"])
        self.assertFalse(report["task_should_stop"])

    def test_changed_evidence_cannot_reuse_assessment(self) -> None:
        self._write(self.candidate, "evidence/phase-b.json", '{"checked":false}\n')
        state = supervision.capture_candidate(self.candidate, self.control)
        assessment = copy.deepcopy(self.assessment)
        assessment["candidate_worktree_digest"] = state.worktree_digest

        report = self._audit(assessment)

        self.assertEqual(report["decision"], "CONTINUE")
        self.assertIn("candidate-evidence", report["evidence_mismatched"])
        self.assertFalse(report["phase_change_allowed"])

    def test_heartbeat_records_exact_observed_state(self) -> None:
        report = self._audit()
        heartbeat = Path(self.temporary.name) / "heartbeat.json"

        supervision.write_heartbeat(heartbeat, report)
        value = json.loads(heartbeat.read_text(encoding="utf-8"))

        self.assertEqual(value["schema"], supervision.HEARTBEAT_SCHEMA)
        self.assertEqual(value["candidate_branch"], "codex/development")
        self.assertEqual(value["candidate_commit"], self.state.head)
        self.assertEqual(value["candidate_worktree_digest"], self.state.worktree_digest)
        self.assertFalse(value["task_should_stop"])
        self.assertFalse(value["authorization_required"])


if __name__ == "__main__":
    unittest.main()
