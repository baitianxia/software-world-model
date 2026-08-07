from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.cross_cutting import DomainError, ErrorCode, digest_of
from validation.product_holdout_iteration_002 import (
    DimensionAssessment,
    DimensionStatus,
    HoldoutAnswerPath,
    HoldoutPathResult,
    HoldoutTaskAnswerPair,
    IndependentCaseReview,
    INDEPENDENT_REVIEW_DRAFT_SCHEMA,
    SealedAnswerClaim,
    build_task_input,
    load_holdout_suite,
    load_independent_review,
    save_answer_pair,
    save_independent_review,
    save_path_result,
    seal_independent_review_draft,
)


class IndependentProductReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.suite = load_holdout_suite()
        self.task = self.suite["tasks"][0]
        self.task_input = build_task_input(
            self.suite, task_id=self.task["task_id"]
        )
        self.pair = HoldoutTaskAnswerPair.create(
            direct=self.result(HoldoutAnswerPath.DIRECT),
            world_assisted=self.result(HoldoutAnswerPath.WORLD_ASSISTED),
        )

    def result(self, path: HoldoutAnswerPath) -> HoldoutPathResult:
        return HoldoutPathResult.create(
            result_ref=f"result:{path.value.lower()}",
            run_id=f"run:{path.value.lower()}",
            path=path,
            origin=(
                "direct-source-answer"
                if path is HoldoutAnswerPath.DIRECT
                else "formal-knowledge-system-answer"
            ),
            implementation_digest=digest_of({"path": path.value}),
            task_input=self.task_input,
            answer="A source-grounded answer.",
            claims=(
                SealedAnswerClaim(
                    "A source-grounded answer.", ("source-reference:1",)
                ),
            ),
            actual_model_fingerprint="glm-5.2",
            provider_request_ids=(f"provider:{path.value.lower()}",),
            model_call_count=1,
            source_action_count=1,
            source_byte_count=100,
            input_tokens=100,
            output_tokens=20,
            usage_complete=True,
        )

    def assessments(
        self,
        *,
        direct: DimensionStatus = DimensionStatus.CORRECT_COMPLETE,
        world: DimensionStatus = DimensionStatus.CORRECT_COMPLETE,
    ) -> tuple[DimensionAssessment, ...]:
        return tuple(
            DimensionAssessment(
                dimension=dimension,
                direct_status=direct,
                world_status=world,
                finding=f"Reviewed against frozen source: {dimension}",
            )
            for dimension in self.task["acceptance_dimensions"]
        )

    def review(self, **overrides) -> IndependentCaseReview:
        values = {
            "suite": self.suite,
            "pair": self.pair,
            "evaluator_identity": "Codex review session 2026-08-07",
            "evaluator_origin": "codex-independent-source-review",
            "assessments": self.assessments(),
            "findings": (),
            "reviewed_at": datetime(2026, 8, 7, tzinfo=timezone.utc),
        }
        values.update(overrides)
        return IndependentCaseReview.create(**values)

    def test_complete_independent_review_creates_product_comparison(self) -> None:
        review = self.review()
        comparison = review.to_product_comparison()

        self.assertTrue(review.verify_digest())
        self.assertTrue(review.passed)
        self.assertTrue(comparison.passed)
        self.assertEqual(comparison.direct_model_fingerprint, "glm-5.2")
        self.assertEqual(comparison.case_id, self.task["task_id"])

    def test_every_sealed_dimension_must_be_reviewed_in_exact_order(self) -> None:
        with self.assertRaises(DomainError) as raised:
            self.review(assessments=self.assessments()[:-1])

        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )

    def test_evaluator_cannot_reuse_either_answer_origin(self) -> None:
        with self.assertRaises(DomainError) as raised:
            self.review(evaluator_origin=self.pair.direct.origin)

        self.assertEqual(raised.exception.code, ErrorCode.QUALIFICATION_INVALID)

    def test_regression_is_sealed_with_findings_but_cannot_pass(self) -> None:
        review = self.review(
            assessments=self.assessments(
                direct=DimensionStatus.CORRECT_COMPLETE,
                world=DimensionStatus.CORRECT_PARTIAL,
            ),
            findings=("The system answer omitted material conditions.",),
        )

        self.assertFalse(review.passed)
        self.assertFalse(review.to_product_comparison().passed)

    def test_tampered_review_digest_is_rejected(self) -> None:
        review = replace(self.review(), world_completion_milli=0)

        self.assertFalse(review.verify_digest())
        with self.assertRaises(DomainError) as raised:
            review.to_product_comparison()
        self.assertEqual(
            raised.exception.code, ErrorCode.AUTHORITY_RECORD_INCONSISTENT
        )

    def test_review_draft_is_sealed_only_after_pair_and_dimensions_are_bound(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            direct_path = save_path_result(
                self.pair.direct,
                task_input=self.task_input,
                result_directory=directory,
            )
            world_path = save_path_result(
                self.pair.world_assisted,
                task_input=self.task_input,
                result_directory=directory,
            )
            save_answer_pair(
                self.pair,
                direct_result_path=direct_path,
                world_result_path=world_path,
                result_directory=directory,
            )
            draft = {
                "schema": INDEPENDENT_REVIEW_DRAFT_SCHEMA,
                "suite_digest": self.pair.direct.suite_digest.value,
                "task_id": self.pair.direct.task_id,
                "pair_digest": self.pair.digest.value,
                "evaluator_identity": "Codex review session 2026-08-07",
                "evaluator_origin": "codex-independent-source-review",
                "assessments": [
                    {
                        "dimension": item.dimension,
                        "direct_status": item.direct_status.value,
                        "world_status": item.world_status.value,
                        "finding": item.finding,
                    }
                    for item in self.assessments()
                ],
                "findings": [],
                "reviewed_at": "2026-08-07T00:00:00+00:00",
            }
            draft_path = Path(directory) / "review-draft.json"
            draft_path.write_text(json.dumps(draft), encoding="utf-8")

            sealed_path = seal_independent_review_draft(
                draft_path,
                suite=self.suite,
                pair=self.pair,
                result_directory=directory,
            )
            review = load_independent_review(
                sealed_path, suite=self.suite, pair=self.pair
            )
            replayed = save_independent_review(
                review,
                suite=self.suite,
                pair=self.pair,
                result_directory=directory,
            )

            self.assertEqual(replayed, sealed_path)
            self.assertTrue(review.passed)


if __name__ == "__main__":
    unittest.main()
