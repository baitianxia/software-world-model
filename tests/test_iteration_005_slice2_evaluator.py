from __future__ import annotations

from pathlib import Path
import unittest

from validation.structure_world_model_iteration_005 import slice2_evaluator


class Iteration005Slice2EvaluatorTests(unittest.TestCase):
    def _protocols(self):
        runner_digest = "sha256:" + "e" * 64
        return {
            "execution_order": [
                "CONTROLLED_DIRECT",
                "MATURE_SOURCE_AGENT",
                "SEAL_BASELINE_POPULATIONS",
                "WORLD_MODEL",
            ],
            "failure_policy": (
                "PRESERVE_ALL_TERMINALS_NO_RETRY_NO_SELECTION_NO_INTERPOLATION"
            ),
            "runs_per_case": 1,
            "WORLD_MODEL": {
                "entrypoint": "software_world_model.interface.world_model_http",
                "provider": dict(slice2_evaluator._PROVIDER),
                "payload_boundary": (
                    "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
                ),
                "external_task_count_per_case": 1,
                "provider_call_count_observability": (
                    "EXACT_PRODUCT_GATEWAY_COUNTER_ON_VERIFIED_TERMINAL"
                ),
                "provider_call_count_per_case": 1,
                "controller_retry_count_per_case": 0,
                "result_visibility": (
                    "AFTER_BOTH_BASELINE_POPULATIONS_ARE_SEALED"
                ),
                "production_activation": "NOT_EXECUTED",
            },
            "CONTROLLED_DIRECT": {
                "runner_path": (
                    "validation/structure_world_model_iteration_005/"
                    "slice2_comparison.py"
                ),
                "runner_digest": runner_digest,
                "provider": dict(slice2_evaluator._PROVIDER),
                "payload_boundary": (
                    "ORIGINAL_QUESTION_AND_EXACT_SEALED_POM_SOURCE_CLOSURE"
                ),
                "external_task_count_per_case": 1,
                "provider_call_count_observability": (
                    "EXACT_DIRECT_GATEWAY_COUNTER_ON_TERMINAL"
                ),
                "provider_call_count_per_case": 1,
                "controller_retry_count_per_case": 0,
                "max_output_tokens_per_case": 4096,
                "response_contract": (
                    "STRICT_JSON_OBJECT_ANSWER_STRING_NO_TRAILING_TEXT"
                ),
                "oracle_visibility": "NONE",
                "result_visibility": (
                    "SEALED_BEFORE_FIRST_WORLD_MODEL_RESULT"
                ),
                "production_activation": "NOT_EXECUTED",
            },
            "MATURE_SOURCE_AGENT": {
                "runner_path": (
                    "validation/structure_world_model_iteration_005/"
                    "slice2_comparison.py"
                ),
                "runner_digest": runner_digest,
                "agent": dict(slice2_evaluator._MATURE_AGENT),
                "payload_boundary": (
                    "ORIGINAL_QUESTION_AND_EXACT_SEALED_POM_SOURCE_CLOSURE"
                ),
                "external_task_count_per_case": 1,
                "provider_call_count_observability": (
                    "UNOBSERVABLE_FROM_CODEX_CLI_EVENT_BOUNDARY"
                ),
                "provider_call_count_per_case": None,
                "controller_retry_count_per_case": 0,
                "oracle_visibility": "NONE",
                "result_visibility": (
                    "SEALED_BEFORE_FIRST_WORLD_MODEL_RESULT"
                ),
                "production_activation": "NOT_EXECUTED",
            },
        }

    def _suite(self):
        core = {
            "schema": slice2_evaluator.SUITE_SCHEMA,
            "environment": "EVALUATION_ONLY",
            "evaluation_subject_commit": "a" * 40,
            "evaluation_subject_tree": "b" * 40,
            "sealed_before_world_model_results": True,
            "world_model_result_count_at_seal": 0,
            "controlled_direct_result_count_at_seal": 0,
            "mature_source_agent_result_count_at_seal": 0,
            "fixture": {
                "seed": "unit-test",
                "suffix": "unit",
                "workspace_id": "maven_workspace_unit",
                "revisions": {"r1": "f" * 40, "r2": "9" * 40},
                "read_sets": {
                    "r1": "read_set_" + "c" * 32,
                    "r2": "read_set_" + "d" * 32,
                    "ordered": "read_set_" + "e" * 32,
                },
            },
            "catalog_digest": "sha256:" + "c" * 64,
            "product_oracle_digest": "sha256:" + "d" * 64,
            "independent_evaluator_digest": slice2_evaluator._file_digest(
                Path(slice2_evaluator.__file__).resolve(strict=True)
            ),
            "comparison_surfaces": list(slice2_evaluator.SURFACES),
            "comparison_protocols": self._protocols(),
            "source_closures": {
                "read_set_" + "c" * 32: {
                    "snapshots": [
                        {
                            "label": "A",
                            "revision": "f" * 40,
                            "files": [
                                {
                                    "path": "pom.xml",
                                    "sha256": "sha256:" + "1" * 64,
                                    "size": 10,
                                }
                            ],
                        }
                    ]
                },
                "read_set_" + "d" * 32: {
                    "snapshots": [
                        {
                            "label": "A",
                            "revision": "9" * 40,
                            "files": [
                                {
                                    "path": "pom.xml",
                                    "sha256": "sha256:" + "2" * 64,
                                    "size": 10,
                                }
                            ],
                        }
                    ]
                },
                "read_set_" + "e" * 32: {
                    "snapshots": [
                        {
                            "label": "A",
                            "revision": "f" * 40,
                            "files": [
                                {
                                    "path": "pom.xml",
                                    "sha256": "sha256:" + "1" * 64,
                                    "size": 10,
                                }
                            ],
                        },
                        {
                            "label": "B",
                            "revision": "9" * 40,
                            "files": [
                                {
                                    "path": "pom.xml",
                                    "sha256": "sha256:" + "2" * 64,
                                    "size": 10,
                                }
                            ],
                        },
                    ]
                },
            },
            "cases": [
                {
                    "case_id": "CASE-1",
                    "read_set_id": "read_set_" + "c" * 32,
                    "question": "Which module exists?",
                    "expected_outcome": "SUPPORTED",
                    "required_tokens": ["module-a", "module-b"],
                    "forbidden_tokens": ["module-z"],
                    "outcome_markers_any": [],
                }
            ],
            "production_activation": "NOT_EXECUTED",
        }
        return {
            **core,
            "document_digest": slice2_evaluator._digest(
                slice2_evaluator.SUITE_SCHEMA, core
            ),
        }

    def _population(self, suite, surface, answer):
        core = {
            "schema": slice2_evaluator.POPULATION_SCHEMA,
            "surface": surface,
            "suite_digest": suite["document_digest"],
            "results": [
                {
                    "case_id": "CASE-1",
                    "status": "SUCCESS",
                    "answer_body": answer,
                    "failure_code": None,
                    "external_task_count": 1,
                    "provider_call_count": (
                        None if surface == "MATURE_SOURCE_AGENT" else 1
                    ),
                    "terminal_digest": "sha256:" + "d" * 64,
                }
            ],
            "failures_preserved": True,
            "missing_outputs_interpolated": False,
            "production_activation": "NOT_EXECUTED",
        }
        return {
            **core,
            "document_digest": slice2_evaluator._digest(
                slice2_evaluator.POPULATION_SCHEMA, core
            ),
        }

    def test_pass_requires_no_per_case_completeness_regression(self):
        suite = self._suite()
        report = slice2_evaluator.evaluate(
            suite,
            {
                "WORLD_MODEL": self._population(
                    suite, "WORLD_MODEL", "module-a and module-b"
                ),
                "CONTROLLED_DIRECT": self._population(
                    suite, "CONTROLLED_DIRECT", "module-a"
                ),
                "MATURE_SOURCE_AGENT": self._population(
                    suite, "MATURE_SOURCE_AGENT", "module-a and module-b"
                ),
            },
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["blockers"], [])
        self.assertFalse(report["failures_filtered"])

    def test_controlled_direct_response_envelope_is_exact(self):
        protocols = self._protocols()
        protocols["CONTROLLED_DIRECT"]["max_output_tokens_per_case"] = 1000

        with self.assertRaisesRegex(
            slice2_evaluator.EvaluationFailure,
            "controlled Direct comparison protocol drifted",
        ):
            slice2_evaluator._validate_comparison_protocols(protocols)

    def test_major_error_and_stronger_baseline_regression_both_block(self):
        suite = self._suite()
        report = slice2_evaluator.evaluate(
            suite,
            {
                "WORLD_MODEL": self._population(
                    suite, "WORLD_MODEL", "module-a and module-z"
                ),
                "CONTROLLED_DIRECT": self._population(
                    suite, "CONTROLLED_DIRECT", "module-a and module-b"
                ),
                "MATURE_SOURCE_AGENT": self._population(
                    suite, "MATURE_SOURCE_AGENT", "module-a and module-b"
                ),
            },
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(
            any("major error" in item for item in report["blockers"])
        )
        self.assertTrue(
            any("completeness regressed" in item for item in report["blockers"])
        )

    def test_mature_provider_call_count_must_remain_unobservable(self):
        suite = self._suite()
        population = self._population(
            suite,
            "MATURE_SOURCE_AGENT",
            "module-a and module-b",
        )
        population["results"][0]["provider_call_count"] = 1
        core = {
            key: value
            for key, value in population.items()
            if key != "document_digest"
        }
        population["document_digest"] = slice2_evaluator._digest(
            slice2_evaluator.POPULATION_SCHEMA,
            core,
        )

        with self.assertRaisesRegex(
            slice2_evaluator.EvaluationFailure,
            "not observable",
        ):
            slice2_evaluator._population_map(
                population,
                expected_surface="MATURE_SOURCE_AGENT",
                suite_digest=suite["document_digest"],
                case_ids={"CASE-1"},
            )


if __name__ == "__main__":
    unittest.main()
