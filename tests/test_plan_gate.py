"""Tests for the minimal plan gate in ``scripts/plan_gate.py``."""

from __future__ import annotations

import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from scripts import plan_gate


def _manifest(kind: str = "mvp-experience-development", allowed=("src/**", "docs/project/**"), forbidden=("scripts/docs.py",)) -> dict[str, object]:
    return {
        "plan_execution_control": {
            "current_action": {
                "id": "ACTION-1",
                "kind": kind,
                "status": "authorized",
                "coding_allowed": True,
                "allowed_change_paths": list(allowed),
                "forbidden_change_paths": list(forbidden),
            }
        }
    }


class PathPolicyTests(unittest.TestCase):
    def test_allowed_path_passes(self) -> None:
        self.assertEqual(plan_gate.validate_transition(_manifest(), _manifest(), ["src/a.py"]), [])

    def test_path_outside_allow_list_is_rejected(self) -> None:
        errors = plan_gate.validate_transition(_manifest(), _manifest(), ["docs/system/x.md"])
        self.assertTrue(any("not allowed by the base action" in error for error in errors))

    def test_deny_list_wins(self) -> None:
        base = _manifest(allowed=("scripts/docs.py",), forbidden=("scripts/docs.py",))
        errors = plan_gate.validate_transition(base, _manifest(), ["scripts/docs.py"])
        self.assertTrue(any("forbidden by the base action" in error for error in errors))

    def test_prefix_rule_matches_directory(self) -> None:
        base = _manifest(allowed=("docs/system/",), forbidden=())
        self.assertEqual(plan_gate.validate_transition(base, _manifest(), ["docs/system/a/b.md"]), [])

    def test_gate_files_require_governance_action(self) -> None:
        base = _manifest(allowed=("scripts/plan_gate.py",), forbidden=())
        errors = plan_gate.validate_transition(base, _manifest(), ["scripts/plan_gate.py"])
        self.assertTrue(any("governance base action" in error for error in errors))
        governance = _manifest(kind="governance", allowed=("scripts/plan_gate.py",), forbidden=())
        self.assertEqual(plan_gate.validate_transition(governance, _manifest(), ["scripts/plan_gate.py"]), [])

    def test_missing_base_control_uses_bootstrap_paths(self) -> None:
        errors = plan_gate.validate_transition(None, _manifest(), ["src/software_world_model/a.py"])
        self.assertTrue(errors)


class SnapshotAndSecretTests(unittest.TestCase):
    def test_snapshot_requires_action_fields(self) -> None:
        errors = plan_gate.validate_snapshot({"plan_execution_control": {"current_action": {}}})
        self.assertTrue(any("current_action.id" in error for error in errors))
        self.assertTrue(any("allowed_change_paths" in error for error in errors))

    def test_snapshot_rejects_unnormalized_rule(self) -> None:
        errors = plan_gate.validate_snapshot(_manifest(allowed=("../outside",)))
        self.assertTrue(errors)

    def test_secret_is_detected(self) -> None:
        errors = plan_gate.validate_transition(
            _manifest(), _manifest(), ["src/a.py"], [("src/a.py", 'API_KEY = "sk-' + "a" * 32 + '"')]
        )
        self.assertTrue(any("possible secret" in error for error in errors))

    def test_yaml_loader_reads_lists(self) -> None:
        loaded = plan_gate.load_safe_yaml("a:\n  b:\n    - x\n    - y\n  c: true\n")
        self.assertEqual(loaded, {"a": {"b": ["x", "y"], "c": True}})


class GitIntegrationTests(unittest.TestCase):
    def _git(self, root: Path, *arguments: str) -> None:
        subprocess.run(["git", *arguments], cwd=root, check=True, capture_output=True)

    def test_diff_uses_base_action_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs/project/iterations/iteration-001").mkdir(parents=True)
            (root / "docs/project/current.md").write_text(
                "---\nid: PROJECT-CURRENT\nactive_iteration: ITER-001-INDEX\n---\n", encoding="utf-8"
            )
            (root / "docs/project/iterations/iteration-001/manifest.yaml").write_text(
                textwrap.dedent(
                    """\
                    plan_execution_control:
                      current_action:
                        id: ACTION-1
                        kind: mvp-experience-development
                        status: authorized
                        coding_allowed: true
                        allowed_change_paths:
                          - src/**
                        forbidden_change_paths: []
                    """
                ),
                encoding="utf-8",
            )
            (root / "src").mkdir()
            (root / "src/a.py").write_text("x = 1\n", encoding="utf-8")
            self._git(root, "init", "-q")
            self._git(root, "add", "-A")
            self._git(root, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base")
            (root / "src/a.py").write_text("x = 2\n", encoding="utf-8")
            self.assertEqual(plan_gate.main(["--repository", str(root), "diff", "--base", "HEAD"]), 0)
            (root / "README.md").write_text("new\n", encoding="utf-8")
            self.assertEqual(plan_gate.main(["--repository", str(root), "diff", "--base", "HEAD"]), 1)


class RepositorySnapshotTests(unittest.TestCase):
    def test_current_repository_snapshot_passes(self) -> None:
        self.assertEqual(plan_gate.main(["snapshot"]), 0)


if __name__ == "__main__":
    unittest.main()
