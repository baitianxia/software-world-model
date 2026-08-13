from __future__ import annotations

from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from validation.structure_world_model_iteration_006 import (
    live_comparison,
    live_evaluator,
    live_freeze,
)


class Iteration006LiveEvaluatorTests(TestCase):
    def test_protocol_accepts_new_qualification_only_when_surfaces_match(self) -> None:
        provider = dict(live_evaluator._PROVIDER)
        provider["qualification_digest"] = "sha256:" + "9" * 64
        protocols = live_freeze._comparison_protocols(
            Path(live_comparison.__file__).resolve(strict=True), provider
        )

        live_evaluator._validate_protocols(protocols)

        protocols["CONTROLLED_DIRECT"]["provider"] = dict(
            live_evaluator._PROVIDER
        )
        with self.assertRaisesRegex(
            live_evaluator.EvaluationFailure,
            "controlled Direct protocol drifted",
        ):
            live_evaluator._validate_protocols(protocols)

    def test_failed_world_model_terminal_produces_fail_report(self) -> None:
        case_id = "WM-TEST-001"
        case = {
            "case_id": case_id,
            "expected_outcome": "SUPPORTED",
            "required_tokens": ["expected-token"],
            "forbidden_tokens": [],
            "outcome_markers_any": [],
        }
        populations = {
            "WORLD_MODEL": {"surface": "WORLD_MODEL"},
            "CONTROLLED_DIRECT": {"surface": "CONTROLLED_DIRECT"},
            "MATURE_SOURCE_AGENT": {"surface": "MATURE_SOURCE_AGENT"},
        }
        indexed = {
            "WORLD_MODEL": {
                case_id: {
                    "status": "FAILURE",
                    "answer_body": None,
                    "failure_code": "HTTPERROR",
                    "external_task_count": 1,
                    "provider_call_count": None,
                }
            },
            "CONTROLLED_DIRECT": {
                case_id: {
                    "status": "SUCCESS",
                    "answer_body": "expected-token",
                    "failure_code": None,
                    "external_task_count": 1,
                    "provider_call_count": 1,
                }
            },
            "MATURE_SOURCE_AGENT": {
                case_id: {
                    "status": "SUCCESS",
                    "answer_body": "expected-token",
                    "failure_code": None,
                    "external_task_count": 1,
                    "provider_call_count": None,
                }
            },
        }

        def population_map(
            _population: object,
            *,
            expected_surface: str,
            suite_digest: str,
            case_ids: set[str],
        ) -> dict[str, object]:
            self.assertEqual(suite_digest, "sha256:" + "0" * 64)
            self.assertEqual(case_ids, {case_id})
            return indexed[expected_surface]

        with (
            patch.object(live_evaluator, "validate_suite"),
            patch.object(live_evaluator, "_case_map", return_value={case_id: case}),
            patch.object(
                live_evaluator,
                "_population_map",
                side_effect=population_map,
            ),
        ):
            report = live_evaluator.evaluate(
                {
                    "document_digest": "sha256:" + "0" * 64,
                    "cases": [case],
                },
                populations,
            )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn(
            f"{case_id}: World Model terminal failed", report["blockers"]
        )
        self.assertIn(
            f"{case_id}: World Model call count is not exactly one",
            report["blockers"],
        )
        self.assertNotIn(
            f"{case_id}: World Model completeness regressed",
            report["blockers"],
        )
        self.assertIsNone(
            report["rows"][0]["scores"]["WORLD_MODEL"]["completeness_ppm"]
        )
