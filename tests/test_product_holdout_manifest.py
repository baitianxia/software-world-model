from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from software_world_model.cross_cutting import DomainError, ErrorCode, digest_of
from validation.product_holdout_iteration_002 import (
    build_task_input,
    load_holdout_suite,
    verify_answer_path_parity,
    verify_frozen_checkouts,
    verify_holdout_suite,
)
from validation.product_holdout_iteration_002.manifest import (
    verify_repository_checkout,
)


WORKSPACE_ROOT = Path(__file__).resolve().parents[1]


def reseal_for_tamper(suite: dict[str, object]) -> None:
    suite["suite_digest"] = digest_of(
        {key: value for key, value in suite.items() if key != "suite_digest"}
    ).value


class ProductHoldoutManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.suite = load_holdout_suite()

    def test_sealed_suite_has_two_repositories_and_six_balanced_tasks(self) -> None:
        verify_holdout_suite(self.suite)

        self.assertEqual(len(self.suite["repositories"]), 2)
        self.assertEqual(len(self.suite["tasks"]), 6)
        counts = {
            repository["repository_id"]: sum(
                task["repository_id"] == repository["repository_id"]
                for task in self.suite["tasks"]
            )
            for repository in self.suite["repositories"]
        }
        self.assertEqual(set(counts.values()), {3})

    def test_recomputed_digest_cannot_authorize_a_modified_question(self) -> None:
        changed = deepcopy(self.suite)
        changed["tasks"][0]["question"] = "changed after sealing"
        reseal_for_tamper(changed)

        with self.assertRaises(DomainError) as raised:
            verify_holdout_suite(changed)

        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )

    def test_answer_paths_must_have_identical_limits(self) -> None:
        changed = deepcopy(self.suite)
        changed["answer_paths"]["world_assisted"]["maximum_model_calls"] = 9
        reseal_for_tamper(changed)

        with self.assertRaises(DomainError) as raised:
            verify_holdout_suite(changed)

        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )

    def test_task_input_is_path_neutral_and_hides_evaluator_material(self) -> None:
        task_id = self.suite["tasks"][0]["task_id"]
        direct = build_task_input(self.suite, task_id=task_id)
        world_assisted = build_task_input(self.suite, task_id=task_id)

        verify_answer_path_parity(direct, world_assisted)
        serialized = json.dumps(direct, ensure_ascii=False)
        self.assertNotIn("acceptance_dimensions", serialized)
        self.assertNotIn("independent_evaluator", serialized)
        self.assertNotIn("oracle", serialized.lower())

    def test_parity_check_rejects_even_one_changed_resource_limit(self) -> None:
        task_id = self.suite["tasks"][0]["task_id"]
        direct = build_task_input(self.suite, task_id=task_id)
        world_assisted = deepcopy(direct)
        world_assisted["resource_policy"]["maximum_source_actions"] += 1

        with self.assertRaises(DomainError) as raised:
            verify_answer_path_parity(direct, world_assisted)

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_repository_head_drift_fails_closed(self) -> None:
        repository = self.suite["repositories"][0]
        tasks = [
            task
            for task in self.suite["tasks"]
            if task["repository_id"] == repository["repository_id"]
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / repository["local_path"]).mkdir(parents=True)
            with patch(
                "validation.product_holdout_iteration_002.manifest._git",
                return_value="0" * 40,
            ):
                with self.assertRaises(DomainError) as raised:
                    verify_repository_checkout(
                        repository,
                        tasks,
                        workspace_root=root,
                    )

        self.assertEqual(
            raised.exception.code, ErrorCode.SOURCE_REVISION_INCONSISTENT
        )

    @unittest.skipUnless(
        (WORKSPACE_ROOT / "validation-projects/transmittable-thread-local/.git").exists()
        and (WORKSPACE_ROOT / "validation-projects/poi-tl/.git").exists(),
        "sealed validation checkouts are not present",
    )
    def test_local_validation_checkouts_match_the_sealed_suite(self) -> None:
        verify_frozen_checkouts(self.suite, workspace_root=WORKSPACE_ROOT)


if __name__ == "__main__":
    unittest.main()
