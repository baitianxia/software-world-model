from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.cross_cutting import DomainError, ErrorCode, digest_of
from validation.product_holdout_iteration_002 import (
    HoldoutAnswerPath,
    HoldoutPathResult,
    HoldoutTaskAnswerPair,
    SealedAnswerClaim,
    build_task_input,
    load_holdout_suite,
    load_path_result,
    save_answer_pair,
    save_path_result,
    verify_answer_pair_document,
)


class ProductHoldoutExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        suite = load_holdout_suite()
        self.task_input = build_task_input(
            suite, task_id=suite["tasks"][0]["task_id"]
        )

    def result(self, path: HoldoutAnswerPath, **overrides) -> HoldoutPathResult:
        values = {
            "result_ref": f"result:{path.value.lower()}:1",
            "run_id": f"run:{path.value.lower()}:1",
            "path": path,
            "origin": (
                "direct-source-agent"
                if path is HoldoutAnswerPath.DIRECT
                else "formal-knowledge-system"
            ),
            "implementation_digest": digest_of({"path": path.value}),
            "task_input": self.task_input,
            "answer": "The exact source supports this bounded claim.",
            "claims": (
                SealedAnswerClaim(
                    "The exact source supports this bounded claim.",
                    ("source-observation:1",),
                ),
            ),
            "actual_model_fingerprint": "glm-5.2",
            "provider_request_ids": (f"provider:{path.value.lower()}:1",),
            "model_call_count": 1,
            "source_action_count": 1,
            "source_byte_count": 1024,
            "input_tokens": 500,
            "output_tokens": 100,
            "usage_complete": True,
        }
        values.update(overrides)
        return HoldoutPathResult.create(**values)

    def test_same_task_resources_and_model_form_a_pair(self) -> None:
        pair = HoldoutTaskAnswerPair.create(
            direct=self.result(HoldoutAnswerPath.DIRECT),
            world_assisted=self.result(HoldoutAnswerPath.WORLD_ASSISTED),
        )

        self.assertEqual(pair.direct.task_input_digest, pair.world_assisted.task_input_digest)
        self.assertNotEqual(pair.direct.origin, pair.world_assisted.origin)

    def test_answer_cannot_include_text_outside_its_sealed_claims(self) -> None:
        with self.assertRaises(DomainError) as raised:
            self.result(
                HoldoutAnswerPath.DIRECT,
                answer="The exact source supports this bounded claim.\nUnbound addition.",
            )

        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )

    def test_incomplete_usage_or_missing_request_identity_is_rejected(self) -> None:
        for overrides in (
            {"usage_complete": False},
            {"provider_request_ids": (), "model_call_count": 1},
        ):
            with self.subTest(overrides=overrides), self.assertRaises(DomainError):
                self.result(HoldoutAnswerPath.DIRECT, **overrides)

    def test_resource_overrun_is_rejected(self) -> None:
        maximum = self.task_input["resource_policy"]["maximum_model_calls"]
        request_ids = tuple(f"provider:{index}" for index in range(maximum + 1))

        with self.assertRaises(DomainError) as raised:
            self.result(
                HoldoutAnswerPath.DIRECT,
                model_call_count=maximum + 1,
                provider_request_ids=request_ids,
            )

        self.assertEqual(raised.exception.code, ErrorCode.BUDGET_EXHAUSTED)

    def test_paths_must_use_the_same_actual_model(self) -> None:
        with self.assertRaises(DomainError) as raised:
            HoldoutTaskAnswerPair.create(
                direct=self.result(HoldoutAnswerPath.DIRECT),
                world_assisted=self.result(
                    HoldoutAnswerPath.WORLD_ASSISTED,
                    actual_model_fingerprint="another-model",
                ),
            )

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_tampered_path_result_cannot_enter_pair(self) -> None:
        direct = self.result(HoldoutAnswerPath.DIRECT)
        tampered = replace(direct, answer="tampered")

        with self.assertRaises(DomainError) as raised:
            HoldoutTaskAnswerPair.create(
                direct=tampered,
                world_assisted=self.result(HoldoutAnswerPath.WORLD_ASSISTED),
            )

        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )

    def test_path_results_and_pair_are_written_once_and_recoverable(self) -> None:
        direct = self.result(HoldoutAnswerPath.DIRECT)
        world = self.result(HoldoutAnswerPath.WORLD_ASSISTED)
        pair = HoldoutTaskAnswerPair.create(
            direct=direct, world_assisted=world
        )
        with tempfile.TemporaryDirectory() as directory:
            direct_path = save_path_result(
                direct, task_input=self.task_input, result_directory=directory
            )
            world_path = save_path_result(
                world, task_input=self.task_input, result_directory=directory
            )
            pair_path = save_answer_pair(
                pair,
                direct_result_path=direct_path,
                world_result_path=world_path,
                result_directory=directory,
            )
            replayed_path = save_path_result(
                direct, task_input=self.task_input, result_directory=directory
            )
            loaded, loaded_task = load_path_result(direct_path)

            self.assertEqual(replayed_path, direct_path)
            self.assertEqual(loaded, direct)
            self.assertEqual(loaded_task, self.task_input)
            self.assertEqual(verify_answer_pair_document(pair_path), pair)

    def test_changed_or_tampered_sealed_result_file_is_rejected(self) -> None:
        direct = self.result(HoldoutAnswerPath.DIRECT)
        with tempfile.TemporaryDirectory() as directory:
            path = save_path_result(
                direct, task_input=self.task_input, result_directory=directory
            )
            changed = self.result(
                HoldoutAnswerPath.DIRECT,
                answer="A different bounded claim.",
                claims=(
                    SealedAnswerClaim(
                        "A different bounded claim.", ("source-observation:1",)
                    ),
                ),
            )
            with self.assertRaises(DomainError) as raised:
                save_path_result(
                    changed,
                    task_input=self.task_input,
                    result_directory=directory,
                )
            self.assertEqual(raised.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)

            document = json.loads(Path(path).read_text(encoding="utf-8"))
            document["result"]["answer"] = "tampered"
            Path(path).write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(DomainError) as raised:
                load_path_result(path)
            self.assertEqual(
                raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
            )


if __name__ == "__main__":
    unittest.main()
