from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "docs.py"
SPEC = importlib.util.spec_from_file_location("docs_gate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
docs_gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = docs_gate
SPEC.loader.exec_module(docs_gate)


def reflection_report_digest(body: str) -> str:
    section = docs_gate.markdown_section_body(
        docs_gate.Document(SCRIPT, {}, body),
        "Architecture reflection and continuation decision",
    )
    assert section is not None
    return "sha256:" + hashlib.sha256(section.encode("utf-8")).hexdigest()


def positive_value_report_section(
    metadata: dict[str, object], result_id: str, case_id: str
) -> tuple[str, str]:
    strict_codex_report = docs_gate.requires_strict_codex_baseline(
        metadata.get("iteration", "")
    )
    report = {
        "schema": (
            "software-world-model-positive-value-report/v2"
            if strict_codex_report
            else "software-world-model-positive-value-report/v1"
        ),
        "result_id": result_id,
        "verification_case_id": case_id,
        "metric": metadata["positive_value_metric"],
        "unit": metadata["positive_value_unit"],
        "comparison": metadata["positive_value_comparison"],
        "threshold": metadata["positive_value_threshold"],
        "actual": metadata["positive_value_actual"],
        "reuse_horizon_questions": metadata[
            "positive_value_reuse_horizon_questions"
        ],
        "mature_source_agent_protocol_digest": metadata[
            "mature_source_agent_protocol_digest"
        ],
        "mature_source_agent_rubric_digest": metadata[
            "mature_source_agent_rubric_digest"
        ],
        "mature_source_agent_cache_policy_digest": metadata[
            "mature_source_agent_cache_policy_digest"
        ],
        "positive_value_protocol_digest": metadata[
            "positive_value_protocol_digest"
        ],
        "freeze_receipt_ref": metadata["positive_value_freeze_receipt_ref"],
        "adjudication_owner": metadata["positive_value_adjudication_owner"],
        "adjudication_receipt_ref": metadata[
            "positive_value_adjudication_receipt_ref"
        ],
        "measurement_input_digest": "sha256:" + "9" * 64,
    }
    if strict_codex_report:
        report.update(
            {
                "mature_source_agent_identity_digest": metadata[
                    "mature_source_agent_identity_digest"
                ],
                "system_absolute_quality_verdict": metadata[
                    "system_absolute_quality_verdict"
                ],
                "evaluated_question_count": metadata[
                    "evaluated_question_count"
                ],
                "system_better_question_count": metadata[
                    "system_better_question_count"
                ],
                "tie_question_count": metadata["tie_question_count"],
                "codex_better_question_count": metadata[
                    "codex_better_question_count"
                ],
                "both_fail_question_count": metadata[
                    "both_fail_question_count"
                ],
                "unresolved_or_invalid_question_count": metadata[
                    "unresolved_or_invalid_question_count"
                ],
            }
        )
    body = "## Positive value report\n\n" + json.dumps(
        report, ensure_ascii=False, indent=2, sort_keys=True
    )
    section = docs_gate.markdown_section_body(
        docs_gate.Document(SCRIPT, {}, body), "Positive value report"
    )
    assert section is not None
    digest = "sha256:" + hashlib.sha256(section.encode("utf-8")).hexdigest()
    return body, digest


def product_goal_verification(
    path: Path,
    *,
    evidence: str = "pending",
    status: str = "not-run / blocking",
    claim: str | None = None,
    kind: str = "iteration-verification",
    result_id: str = "pending",
) -> docs_gate.Document:
    metadata = {
        "id": "ITER-007-VERIFICATION",
        "kind": kind,
        "status": "not-run",
        "iteration": "ITER-007",
        **docs_gate.PRODUCT_GOAL_V000_METADATA,
        "product_goal_result_id": result_id,
    }
    body = (
        "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
        "|---|---|---|---|---|---|---|\n"
        f"| V-000 | {claim or docs_gate.PRODUCT_GOAL_V000_CLAIM} | "
        f"{docs_gate.PRODUCT_GOAL_V000_LEVEL} | "
        f"{docs_gate.PRODUCT_GOAL_V000_FROZEN_INPUT} | "
        f"{docs_gate.PRODUCT_GOAL_V000_EXPECTED} | {evidence} | {status} |\n"
    )
    return docs_gate.Document(path, metadata, body)


def generic_provider_route_policy() -> dict[str, object]:
    return {
        "schema": docs_gate.PROVIDER_ROUTE_POLICY_SCHEMA,
        "preferred_execution_profile_ref": "runtime-config:preferred-qualified-profile",
        "fallback_execution_profile_ref": "runtime-config:fallback-qualified-profile",
        "preference_order": ["preferred", "fallback"],
        "availability_owner": "provider-availability-boundary",
        "required_fallback_verdict": docs_gate.PREFERRED_PROFILE_UNAVAILABLE_VERDICT,
        "product_control_flow_allowed_inputs": "route-role,execution-profile-ref-and-digest,availability-verdict",
        "product_control_flow_forbidden_inputs": "provider-identity,model-identity",
        "verification_case_id": "V-MODEL-TRANSPARENT-ROUTING-001",
        "fallback_dispatch_requires_verification_pass": True,
        "preferred_unavailable_evidence_required": True,
        "implementation_gap_counts_as_preferred_unavailable": False,
        "preferred_availability_requires": "credential-reference-configured-current-exact-conformance-current-exact-strategy-capability-qualification-and-no-active-provider-account-or-model-hold",
        "route_freeze_time": "before-conversation-start-and-before-any-interaction-unit-dispatch",
        "ordered_routes_preauthorized_at_session_start": True,
        "ordered_route_disclosure_scopes_preauthorized_at_session_start": True,
        "transparent_logical_interaction_fallback_allowed": True,
        "user_resubmission_or_new_session_required": False,
        "fallback_requires_preferred_attempt_terminal_without_authorized_answer": True,
        "fallback_trigger": "sealed-provider-availability-verdict:PREFERRED_EXECUTION_PROFILE_UNAVAILABLE",
        "fallback_eligible_outcomes": list(
            docs_gate.PROVIDER_FALLBACK_ELIGIBLE_OUTCOMES
        ),
        "structured_output_invalid_allows_fallback": False,
        "model_review_rejected_allows_fallback": False,
        "raw_http_or_outcome_without_availability_verdict_allows_fallback": False,
        "application_source_security_failure_allows_fallback": False,
        "fallback_reason_classification_required": True,
        "capability_failure_must_not_be_misclassified_as_unavailable": True,
        "structured_output_invalid_recovery": "bounded-new-call-on-same-execution-profile-with-new-request-identity-and-receipt",
        "model_review_rejected_recovery": "bounded-rewrite-new-call-on-same-execution-profile-with-new-request-identity-and-receipt-and-fresh-review",
        "same_profile_application_repair_is_transport_request_retry": False,
        "same_profile_application_repair_bound": "current-interaction-safety-and-no-progress-policy",
        "same_profile_application_repair_exhausted_action": "fail-current-turn-with-exact-reason-without-fallback",
        "fallback_attempt_restarts_full_chain": True,
        "fallback_attempt_inputs": "immutable-original-interaction-input-exact-relevant-application-sealed-conversation-context-when-chat-and-exact-cognition",
        "cross_attempt_intermediate_state_reuse_allowed": False,
        "late_preferred_result_policy": "quarantine-audit-only",
        "late_preferred_result_overwrite_allowed": False,
        "post_dispatch_execution_profile_switch_requires": "new-fallback-attempt-under-same-logical-interaction-unit-preauthorized-route-and-required-availability-verdict",
        "maximum_fallback_execution_profile_attempts": 1,
        "transport_request_retry_allowed": False,
        "outcome_unknown_duplicate_cost_risk_recorded": True,
        "peak_urgent_override_requires": "audited-explicit-override",
        "cost_can_reduce_answer_quality": False,
        "cost_gate_scope": "before-interaction-unit-start-only",
        "current_started_interaction_unit_must_keep_full_quality_chain": True,
        "unchanged_current_conformance_reuse_required": True,
    }


class LightweightIter010GateTests(unittest.TestCase):
    @staticmethod
    def _current_manifest() -> dict[str, object]:
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        return docs_gate.safe_load_manifest(manifest_path.read_text(encoding="utf-8"))

    def test_plan_revision_classification_separates_legacy_and_lightweight(self) -> None:
        legacy = {
            "plan_execution_control": {
                "plan_revision_ref": docs_gate.ITER010_PLAN_REVISION_REF,
            }
        }
        lightweight = {
            "plan_execution_control": {
                "plan_revision_ref": docs_gate.ITER010_LIGHTWEIGHT_PLAN_REVISION_REF,
            }
        }
        failure_handoff = {
            "plan_execution_control": {
                "plan_revision_ref": docs_gate.ITER010_FAILURE_HANDOFF_PLAN_REVISION_REF,
            }
        }
        unrelated = {
            "plan_execution_control": {
                "plan_revision_ref": "ITER-010-PDR-012",
            }
        }

        self.assertTrue(docs_gate.uses_legacy_iter010_plan(legacy))
        self.assertFalse(docs_gate.uses_lightweight_iter010_plan(legacy))
        self.assertFalse(docs_gate.uses_legacy_iter010_plan(lightweight))
        self.assertTrue(docs_gate.uses_lightweight_iter010_plan(lightweight))
        self.assertFalse(
            docs_gate.uses_failure_handoff_iter010_plan(lightweight)
        )
        self.assertTrue(
            docs_gate.uses_failure_handoff_iter010_plan(failure_handoff)
        )
        self.assertTrue(
            docs_gate.uses_post_pdr009_iter010_plan(failure_handoff)
        )
        self.assertFalse(docs_gate.uses_legacy_iter010_plan(unrelated))
        self.assertFalse(docs_gate.uses_lightweight_iter010_plan(unrelated))
        self.assertFalse(
            docs_gate.uses_failure_handoff_iter010_plan(unrelated)
        )

        downstream_verification = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/verification-matrix.md",
            {"id": "ITER-010-VERIFICATION"},
            "",
        )
        downstream_errors = docs_gate.validate_historical_gate_catalog(
            {
                **unrelated,
                "critical_assumption_catalog_cutover": {
                    "historical_case_ids": "",
                },
            },
            [],
            downstream_verification,
            "manifest.yaml",
        )
        self.assertFalse(
            any(
                case_id in error
                for error in downstream_errors
                for case_id in docs_gate.ITER010_CURRENT_CHAT_GATE_CASES
            ),
            downstream_errors,
        )
        self.assertFalse(
            any("current ITER-010 Gate contracts" in error for error in downstream_errors),
            downstream_errors,
        )

    def test_experience_policy_dispatches_registered_iter010_revisions(self) -> None:
        arguments = ({}, [], [], "manifest.yaml")
        legacy = {
            "plan_execution_control": {
                "plan_revision_ref": docs_gate.ITER010_PLAN_REVISION_REF,
            },
            "experience_delivery_policy": {},
        }
        lightweight = {
            "plan_execution_control": {
                "plan_revision_ref": docs_gate.ITER010_LIGHTWEIGHT_PLAN_REVISION_REF,
            },
            "experience_delivery_policy": {},
        }
        failure_handoff = {
            "plan_execution_control": {
                "plan_revision_ref": docs_gate.ITER010_FAILURE_HANDOFF_PLAN_REVISION_REF,
            },
            "experience_delivery_policy": {},
        }
        other_iteration = {
            "plan_execution_control": {
                "plan_revision_ref": "ITER-012-PDR-011",
            },
            "experience_delivery_policy": {},
        }

        with patch.object(
            docs_gate,
            "_validate_experience_first_delivery_policy_legacy_or_generic",
            return_value=["legacy-validator"],
        ) as legacy_validator, patch.object(
            docs_gate,
            "_validate_iter010_lightweight_experience_policy",
            return_value=["lightweight-validator"],
        ) as lightweight_validator:
            self.assertEqual(
                docs_gate.validate_experience_first_delivery_policy(
                    legacy, *arguments, required=True
                ),
                ["legacy-validator"],
            )
            legacy_validator.assert_called_once()
            lightweight_validator.assert_not_called()

            legacy_validator.reset_mock()
            self.assertEqual(
                docs_gate.validate_experience_first_delivery_policy(
                    lightweight, *arguments, required=True
                ),
                ["lightweight-validator"],
            )
            legacy_validator.assert_not_called()
            lightweight_validator.assert_called_once()

            lightweight_validator.reset_mock()
            self.assertEqual(
                docs_gate.validate_experience_first_delivery_policy(
                    failure_handoff, *arguments, required=True
                ),
                ["lightweight-validator"],
            )
            legacy_validator.assert_not_called()
            lightweight_validator.assert_called_once()

            lightweight_validator.reset_mock()
            self.assertEqual(
                docs_gate.validate_experience_first_delivery_policy(
                    other_iteration, *arguments, required=True
                ),
                ["legacy-validator"],
            )
            legacy_validator.assert_called_once()
            lightweight_validator.assert_not_called()

    def test_experience_policy_dispatch_rejects_unregistered_pdr012_or_later(
        self,
    ) -> None:
        arguments = ({}, [], [], "manifest.yaml")
        with patch.object(
            docs_gate,
            "_validate_experience_first_delivery_policy_legacy_or_generic",
            return_value=[],
        ) as legacy_validator, patch.object(
            docs_gate,
            "_validate_iter010_lightweight_experience_policy",
            return_value=[],
        ) as lightweight_validator:
            for revision in (12, 100):
                with self.subTest(revision=revision):
                    manifest = {
                        "plan_execution_control": {
                            "plan_revision_ref": f"ITER-010-PDR-{revision:03d}",
                        },
                        "experience_delivery_policy": {},
                    }
                    errors = docs_gate.validate_experience_first_delivery_policy(
                        manifest, *arguments, required=True
                    )
                    self.assertEqual(len(errors), 1, errors)
                    self.assertIn(
                        f"ITER-010-PDR-{revision:03d}", errors[0]
                    )
                    self.assertIn(
                        "no registered experience policy validator", errors[0]
                    )
                    self.assertIn("must not fall back", errors[0])

            legacy_validator.assert_not_called()
            lightweight_validator.assert_not_called()

    def test_lightweight_experience_policy_has_no_machine_deadline(self) -> None:
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = docs_gate.safe_load_manifest(manifest_text)
        blocking = docs_gate.manifest_resolved_sequence_items(
            manifest_text, "product_goal_alignment", "blocking_case_ids"
        )
        new_refs = docs_gate.manifest_resolved_sequence_items(
            manifest_text, "product_goal_alignment", "new_capability_slice_refs"
        )
        assert blocking is not None and new_refs is not None

        self.assertEqual(
            docs_gate.validate_experience_first_delivery_policy(
                manifest,
                manifest["product_goal_alignment"],
                new_refs,
                blocking,
                "manifest.yaml",
                required=True,
                manifest_text=manifest_text,
            ),
            [],
        )

        with_deadline = copy.deepcopy(manifest)
        with_deadline["experience_delivery_policy"][
            "direction_decision_deadline_minutes"
        ] = 480
        errors = docs_gate.validate_experience_first_delivery_policy(
            with_deadline,
            with_deadline["product_goal_alignment"],
            new_refs,
            blocking,
            "manifest.yaml",
            required=True,
            manifest_text=manifest_text,
        )
        self.assertTrue(
            any(
                "machine timebox fields" in error
                and "direction_decision_deadline_minutes" in error
                for error in errors
            ),
            errors,
        )

    def test_lightweight_experience_policy_rejects_every_field_mutation(self) -> None:
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = docs_gate.safe_load_manifest(manifest_text)
        blocking = docs_gate.manifest_resolved_sequence_items(
            manifest_text, "product_goal_alignment", "blocking_case_ids"
        )
        new_refs = docs_gate.manifest_resolved_sequence_items(
            manifest_text, "product_goal_alignment", "new_capability_slice_refs"
        )
        assert blocking is not None and new_refs is not None
        for field, expected in (
            docs_gate.ITER010_LIGHTWEIGHT_EXPERIENCE_POLICY_SEQUENCE_VALUES
        ):
            manifest["experience_delivery_policy"][field] = list(expected)  # type: ignore[index]

        self.assertEqual(
            docs_gate.validate_experience_first_delivery_policy(
                manifest,
                manifest["product_goal_alignment"],
                new_refs,
                blocking,
                "manifest.yaml",
                required=True,
                manifest_text=manifest_text,
            ),
            [],
        )

        for field, original in (
            docs_gate.ITER010_FAILURE_HANDOFF_EXPERIENCE_POLICY_EXACT_VALUES
        ):
            with self.subTest(policy_field=field):
                candidate = copy.deepcopy(manifest)
                if isinstance(original, bool):
                    replacement: object = int(original)
                elif isinstance(original, int):
                    replacement = True if original == 1 else original + 1
                else:
                    replacement = f"{original}-tampered"
                candidate["experience_delivery_policy"][field] = replacement  # type: ignore[index]
                errors = docs_gate.validate_experience_first_delivery_policy(
                    candidate,
                    candidate["product_goal_alignment"],
                    new_refs,
                    blocking,
                    "manifest.yaml",
                    required=True,
                )
                self.assertTrue(any(f".{field}" in error for error in errors), errors)

        sequence_candidate = copy.deepcopy(manifest)
        sequence_candidate["experience_delivery_policy"][  # type: ignore[index]
            "historical_pre_policy_result_refs"
        ] = ["ITER-010-RESULT-COUNTERFEIT"]
        sequence_errors = docs_gate.validate_experience_first_delivery_policy(
            sequence_candidate,
            sequence_candidate["product_goal_alignment"],
            new_refs,
            blocking,
            "manifest.yaml",
            required=True,
        )
        self.assertTrue(
            any("historical_pre_policy_result_refs" in error for error in sequence_errors),
            sequence_errors,
        )

        for path, value, expected_error in (
            (("current_action", "case_id"), "V-CHAT-EXPERIENCE-001", "action.case_id"),
            (
                ("control_locks", "full_regression"),
                False,
                "lock all product and execution work",
            ),
            (
                ("experience_version_binding", "repeatable_start"),
                False,
                "repeatably runnable",
            ),
        ):
            with self.subTest(binding_path=path):
                candidate = copy.deepcopy(manifest)
                if path[0] == "current_action":
                    target = candidate["plan_execution_control"]["current_action"]  # type: ignore[index]
                    keys = path[1:]
                elif path[0] == "control_locks":
                    target = candidate["plan_execution_control"]["locks"]  # type: ignore[index]
                    keys = path[1:]
                else:
                    target = candidate["product_goal_alignment"][path[0]]  # type: ignore[index]
                    keys = path[1:]
                for key in keys[:-1]:
                    target = target[key]  # type: ignore[index]
                target[keys[-1]] = value  # type: ignore[index]
                errors = docs_gate.validate_experience_first_delivery_policy(
                    candidate,
                    candidate["product_goal_alignment"],
                    new_refs,
                    blocking,
                    "manifest.yaml",
                    required=True,
                )
                self.assertTrue(
                    any(expected_error in error for error in errors), errors
                )

        result_backed_first = copy.deepcopy(manifest)
        result_backed_first["plan_execution_control"]["next_action_contracts"][  # type: ignore[index]
            "premature_first_delivery_result"
        ] = {
            "case_id": docs_gate.ITER010_LIGHTWEIGHT_FIRST_OPERABLE_CASE_ID,
            "result_ref": "ITER-010-RESULT-V-CHAT-EXPERIENCE-001",
        }
        result_backed_errors = docs_gate.validate_experience_first_delivery_policy(
            result_backed_first,
            result_backed_first["product_goal_alignment"],
            new_refs,
            blocking,
            "manifest.yaml",
            required=True,
        )
        self.assertTrue(
            any("requires_result=false" in error for error in result_backed_errors),
            result_backed_errors,
        )

    def test_failure_handoff_policy_allows_registered_direction_action(self) -> None:
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = docs_gate.safe_load_manifest(manifest_text)
        for field, expected in (
            docs_gate.ITER010_LIGHTWEIGHT_EXPERIENCE_POLICY_SEQUENCE_VALUES
        ):
            manifest["experience_delivery_policy"][field] = list(expected)  # type: ignore[index]
        contract = manifest["plan_execution_control"]["next_action_contracts"][  # type: ignore[index]
            "user_direction_decision"
        ]
        manifest["plan_execution_control"]["current_action"] = contract  # type: ignore[index]
        manifest["plan_execution_control"]["transition"] = contract["transition"]  # type: ignore[index]
        manifest["plan_execution_control"]["locks"] = contract["locks"]  # type: ignore[index]
        blocking = docs_gate.manifest_resolved_sequence_items(
            manifest_text, "product_goal_alignment", "blocking_case_ids"
        )
        new_refs = docs_gate.manifest_resolved_sequence_items(
            manifest_text, "product_goal_alignment", "new_capability_slice_refs"
        )
        assert blocking is not None and new_refs is not None
        self.assertEqual(
            docs_gate.validate_experience_first_delivery_policy(
                manifest,
                manifest["product_goal_alignment"],
                new_refs,
                blocking,
                "manifest.yaml",
                required=True,
            ),
            [],
        )

    def test_post_experience_comparison_is_two_arm_and_heterogeneous(self) -> None:
        binding: dict[str, object] = {
            "case_id": docs_gate.ITER010_DIRECTION_QUALITY_CASE_ID,
            "new_slice_ref": "ITER-010-SLICE-001",
            "result_role": "post-experience-strict-superiority-direction-evidence",
            "occurs_after_complete_browser_experience": True,
            "question_count": 3,
            "unseen_question_count_minimum": 2,
            "question_set_rule": "heterogeneous-no-pom-only",
            "arms": "complete-world-model-system,current-codex",
            "protocol_digest_ref": "mature_source_agent_protocol_digest",
            "rubric_digest_ref": "mature_source_agent_rubric_digest",
            "identity_digest_ref": "mature_source_agent_identity_digest",
            "pass_rule": docs_gate.STRICT_CODEX_ALPHA_PASS_RULE,
            "all_tie_outcome": "FAIL",
            "secondary_metric_compensation_allowed": False,
            "current_codex_is_oracle_or_reviewer": False,
            "external_codex_runtime": (
                "preserve-actual-model-reasoning-tools-permissions-and-budget"
            ),
            "shared_evaluation_inputs": (
                "same-exact-revision-questions-authorized-source-scope-"
                "output-constraints-and-blind-rubric"
            ),
            "technical_adjudication_owner": "independent-evaluator-not-answer-generator",
            "product_direction_decision_owner": "user",
            "full_four_arm_causal_ablation_requires_user_continue": True,
        }
        alignment = {"alpha_agent_comparison_binding": binding}
        blocking = [docs_gate.ITER010_DIRECTION_QUALITY_CASE_ID]

        self.assertEqual(
            docs_gate.validate_alpha_agent_comparison_binding(
                alignment,
                ["ITER-010-SLICE-001"],
                blocking,
                "manifest.yaml",
            ),
            [],
        )

        invalid_changes = (
            (
                "arms",
                "source-only,complete-world-model-system,current-codex",
                ".arms",
            ),
            ("question_set_rule", "pom-only", ".question_set_rule"),
            ("question_count", 2, "question_count must be at least 3"),
            (
                "unseen_question_count_minimum",
                1,
                "unseen_question_count_minimum must be between 2",
            ),
        )
        for field, value, expected_error in invalid_changes:
            with self.subTest(field=field):
                candidate = copy.deepcopy(alignment)
                candidate["alpha_agent_comparison_binding"][field] = value
                errors = docs_gate.validate_alpha_agent_comparison_binding(
                    candidate,
                    ["ITER-010-SLICE-001"],
                    blocking,
                    "manifest.yaml",
                )
                self.assertTrue(
                    any(expected_error in error for error in errors),
                    errors,
                )

    def test_lightweight_standing_authority_rejects_every_field_mutation(self) -> None:
        manifest = self._current_manifest()
        self.assertEqual(
            docs_gate.validate_iter010_lightweight_standing_authority(
                manifest, "manifest.yaml"
            ),
            [],
        )

        for field, original in (
            docs_gate.ITER010_FAILURE_HANDOFF_STANDING_AUTHORITY_EXACT_VALUES
        ):
            with self.subTest(authority_field=field):
                candidate = copy.deepcopy(manifest)
                candidate["public_oss_evaluation_standing_authority"][field] = (  # type: ignore[index]
                    int(original)
                    if isinstance(original, bool)
                    else f"{original}-tampered"
                )
                errors = docs_gate.validate_iter010_lightweight_standing_authority(
                    candidate, "manifest.yaml"
                )
                self.assertTrue(any(f".{field}" in error for error in errors), errors)

        for field, original in (
            docs_gate.ITER010_FAILURE_HANDOFF_AUTHORIZATION_STATE_EXACT_VALUES
        ):
            with self.subTest(authorization_field=field):
                candidate = copy.deepcopy(manifest)
                candidate["authorization"][field] = (  # type: ignore[index]
                    int(original)
                    if isinstance(original, bool)
                    else f"{original}-tampered"
                )
                errors = docs_gate.validate_iter010_lightweight_standing_authority(
                    candidate, "manifest.yaml"
                )
                self.assertTrue(any(f".{field}" in error for error in errors), errors)

        with_extra_field = copy.deepcopy(manifest)
        with_extra_field["public_oss_evaluation_standing_authority"][  # type: ignore[index]
            "implicit_unregistered_scope"
        ] = True
        extra_errors = docs_gate.validate_iter010_lightweight_standing_authority(
            with_extra_field, "manifest.yaml"
        )
        self.assertTrue(any("closed schema" in error for error in extra_errors), extra_errors)

    def test_dependency_cycles_ignore_only_prior_sealed_result_lineage(self) -> None:
        pdr = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-010/decisions/pdr.md",
            {
                "id": "ITER-010-PDR-010",
                "kind": "project-decision",
                "iteration": "ITER-010",
                "decision": "REWORK",
                "rework_strategy": "COMPLETE_MVP_EXPERIENCE_FIRST",
                "depends_on": ["ITER-010-RESULT-V-PLAN-RECOVERY-001"],
            },
            "",
        )
        prior_result = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-010/results/recovery.md",
            {
                "id": "ITER-010-RESULT-V-PLAN-RECOVERY-001",
                "kind": "iteration-result",
                "status": "sealed",
                "iteration": "ITER-010",
                "plan_revision_ref": "ITER-010-PDR-009",
                "action_ref": "ITER-010-ACTION-USER-PLAN-RECOVERY-001",
                "verification_case_id": "V-PLAN-RECOVERY-001",
                "depends_on": ["ITER-010-PDR-009", "ITER-010-PDR-010"],
            },
            "",
        )
        self.assertEqual(
            docs_gate.validate_dependency_cycles(
                {pdr.identifier: pdr, prior_result.identifier: prior_result}
            ),
            [],
        )

        for field, value in (
            ("id", "ITER-010-RESULT-V-COUNTERFEIT-001"),
            ("status", "draft"),
            ("plan_revision_ref", "ITER-010-PDR-008"),
            ("action_ref", "ITER-010-ACTION-NOT-GOVERNANCE-001"),
            ("verification_case_id", "V-COUNTERFEIT-001"),
        ):
            with self.subTest(counterfeit_result_field=field):
                metadata = {**prior_result.metadata, field: value}
                counterfeit = docs_gate.Document(
                    prior_result.path,
                    metadata,
                    prior_result.body,
                )
                counterfeit_pdr = docs_gate.Document(
                    pdr.path,
                    {
                        **pdr.metadata,
                        "depends_on": [counterfeit.identifier],
                    },
                    pdr.body,
                )
                errors = docs_gate.validate_dependency_cycles(
                    {
                        counterfeit_pdr.identifier: counterfeit_pdr,
                        counterfeit.identifier: counterfeit,
                    }
                )
                self.assertTrue(
                    any("dependency cycle" in error for error in errors), errors
                )

        first = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/system/first.md",
            {"id": "SYS-FIRST", "kind": "system-design", "depends_on": ["SYS-SECOND"]},
            "",
        )
        second = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/system/second.md",
            {"id": "SYS-SECOND", "kind": "system-design", "depends_on": ["SYS-FIRST"]},
            "",
        )
        errors = docs_gate.validate_dependency_cycles(
            {first.identifier: first, second.identifier: second}
        )
        self.assertTrue(any("dependency cycle" in error for error in errors), errors)


class ManifestGateTests(unittest.TestCase):
    def test_later_engineering_qa_result_inherits_source_safety_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.yaml"
            manifest_path.write_text(
                """product_goal_alignment:
  new_capability_slice_refs: []
  blocking_case_ids: []
answer_protocol:
  mode: adaptive-cognition-guided-engineering-investigation
development:
  slices: {}
""",
                encoding="utf-8",
            )
            verification = docs_gate.Document(
                SCRIPT.parents[1]
                / "docs/project/iterations/iteration-012/verification-matrix.md",
                {"id": "ITER-012-VERIFICATION"},
                "",
            )
            result = docs_gate.Document(
                SCRIPT.parents[1]
                / "docs/project/iterations/iteration-012/results/product.md",
                {
                    "id": "ITER-012-RESULT-PRODUCT-GOAL",
                    "kind": "iteration-result",
                    "status": "product-goal-pass",
                    "authority": "execution-evidence",
                    "owners": ["quality"],
                },
                "",
            )
            missing = docs_gate.validate_product_goal_result(
                result, "ITER-012", manifest_path, verification
            )
            required_fields = {
                "authorized_source_retrieval_count",
                "authorized_source_retrieval_bytes",
                "answer_direct_source_access_count",
                "reviewer_direct_source_access_count",
                "repository_write_count",
                "silent_mode_fallback_count",
                "question_evidence_package_manifest_digest",
            }
            self.assertTrue(
                all(any(field in error for error in missing) for field in required_fields)
            )

            secured = docs_gate.Document(
                result.path,
                {
                    **result.metadata,
                    "authorized_source_retrieval_count": 1,
                    "authorized_source_retrieval_bytes": 1,
                    "answer_direct_source_access_count": 0,
                    "reviewer_direct_source_access_count": 0,
                    "repository_write_count": 0,
                    "silent_mode_fallback_count": 0,
                    "question_evidence_package_manifest_digest": "sha256:" + "a" * 64,
                },
                result.body,
            )
            secured_errors = docs_gate.validate_product_goal_result(
                secured, "ITER-012", manifest_path, verification
            )
            self.assertFalse(
                any(field in error for field in required_fields for error in secured_errors),
                secured_errors,
            )

    def test_real_alpha_checkpoint_defers_hardening_gates_until_next_slice(self) -> None:
        iteration_dir = SCRIPT.parents[1] / "docs/project/iterations/iteration-011"
        manifest_text = (iteration_dir / "manifest.yaml").read_text(encoding="utf-8")
        manifest = docs_gate.safe_load_manifest(manifest_text)
        alignment = manifest["product_goal_alignment"]
        refs = docs_gate.manifest_resolved_sequence_items(
            manifest_text, "product_goal_alignment", "new_capability_slice_refs"
        )
        blocking = docs_gate.manifest_resolved_sequence_items(
            manifest_text, "product_goal_alignment", "blocking_case_ids"
        )
        assert isinstance(alignment, dict)
        assert refs is not None
        assert blocking is not None

        self.assertEqual(
            docs_gate.resolved_alpha_direction_slice_ref(alignment, refs), refs[1]
        )
        self.assertEqual(
            docs_gate.validate_alpha_direction_binding(
                alignment, refs, blocking, "manifest.yaml"
            ),
            [],
        )
        self.assertEqual(
            docs_gate.required_early_evaluation_slice_refs(
                alignment, refs, direction_preview_enabled=True
            ),
            {refs[2]},
        )
        self.assertEqual(docs_gate.engineering_qa_hardening_slice_ref(manifest), refs[2])
        self.assertFalse(docs_gate.engineering_qa_hardening_has_started(manifest))
        self.assertEqual(
            docs_gate.validate_alpha_staged_execution_inputs(
                manifest, alignment, refs, "manifest.yaml"
            ),
            [],
        )
        self.assertEqual(
            docs_gate.validate_answer_hierarchy_protocol(manifest, "manifest.yaml"),
            [],
        )

        alpha_started = copy.deepcopy(manifest)
        alpha_alignment = alpha_started["product_goal_alignment"]
        assert isinstance(alpha_alignment, dict)
        alpha_started["development"]["slices"][refs[0]]["status"] = "authorized"
        self.assertEqual(
            docs_gate.validate_alpha_staged_execution_inputs(
                alpha_started, alpha_alignment, refs, "manifest.yaml"
            ),
            [],
        )
        alpha_started["development"]["slices"][refs[1]]["status"] = "authorized"
        self.assertFalse(docs_gate.engineering_qa_hardening_has_started(alpha_started))
        alpha_errors = docs_gate.validate_alpha_staged_execution_inputs(
            alpha_started, alpha_alignment, refs, "manifest.yaml"
        )
        self.assertTrue(
            any("alpha_visible_development_corpus_digest" in error for error in alpha_errors)
        )
        alpha_alignment["alpha_visible_development_corpus_digest"] = "sha256:" + "1" * 64
        self.assertEqual(
            docs_gate.validate_alpha_staged_execution_inputs(
                alpha_started, alpha_alignment, refs, "manifest.yaml"
            ),
            [],
        )

        alpha_started["development"]["slices"][refs[2]]["status"] = "authorized"
        self.assertTrue(docs_gate.engineering_qa_hardening_has_started(alpha_started))
        hardening_errors = docs_gate.validate_alpha_staged_execution_inputs(
            alpha_started, alpha_alignment, refs, "manifest.yaml"
        )
        self.assertTrue(any("positive_value_" in error for error in hardening_errors))
        self.assertTrue(any("hidden_freeze_" in error for error in hardening_errors))
        alpha_alignment.update(
            {
                "positive_value_metric": "normalized-reuse-cost",
                "positive_value_unit": "basis-points",
                "positive_value_comparison": "at-most",
                "positive_value_threshold": 900000,
                "positive_value_reuse_horizon_questions": 1,
                "mature_source_agent_protocol_digest": "sha256:" + "2" * 64,
                "mature_source_agent_rubric_digest": "sha256:" + "3" * 64,
                "mature_source_agent_cache_policy_digest": "sha256:" + "4" * 64,
                "positive_value_protocol_digest": "sha256:" + "5" * 64,
                "positive_value_freeze_receipt_ref": "codex-user-message:sha256:" + "6" * 64,
            }
        )
        hardening_receipt = "codex-user-message:sha256:" + "7" * 64
        alpha_started["development"]["slices"][refs[2]][
            "authorization_ref"
        ] = hardening_receipt
        alpha_started["readiness_inputs"].update(
            {
                "hidden_freeze_protocol_digest": "sha256:" + "8" * 64,
                "hidden_freeze_receipt_ref": hardening_receipt,
            }
        )
        self.assertEqual(
            docs_gate.validate_alpha_staged_execution_inputs(
                alpha_started, alpha_alignment, refs, "manifest.yaml"
            ),
            [],
        )

        hierarchy = alpha_started["answer_hierarchy_protocol"]
        assert isinstance(hierarchy, dict)
        hierarchy["status"] = "frozen"
        alpha_started["readiness_inputs"]["answer_hierarchy_protocol_digest"] = (
            docs_gate.canonical_mapping_digest(
                docs_gate.ENGINEERING_QA_ANSWER_HIERARCHY_SCHEMA,
                "answer_hierarchy_protocol",
                hierarchy,
            )
        )
        self.assertEqual(
            docs_gate.validate_answer_hierarchy_protocol(
                alpha_started, "manifest.yaml", require_frozen=True
            ),
            [],
        )
        hierarchy["direct_user_goal_answer_required"] = False
        self.assertTrue(
            docs_gate.validate_answer_hierarchy_protocol(
                alpha_started, "manifest.yaml", require_frozen=True
            )
        )

    def test_execution_readiness_resolves_safe_yaml_block_sequences(self) -> None:
        text = """\
product_goal_alignment:
  blocking_case_ids:
    - V-001
    - V-002
  readiness_blocking_case_ids:
    - V-PRE-001
source_scope:
  verification_case_ids:
    - V-001
readiness_inputs:
  required_system_contract_refs:
    - SYS-CONTRACT-A
    - SYS-CONTRACT-B
  system_contract_set_paths:
    - docs/system/a.md
    - docs/system/b.md
"""
        manifest = docs_gate.safe_load_manifest(text)

        cases = (
            ("product_goal_alignment", "blocking_case_ids", ["V-001", "V-002"]),
            ("product_goal_alignment", "readiness_blocking_case_ids", ["V-PRE-001"]),
            ("source_scope", "verification_case_ids", ["V-001"]),
            (
                "readiness_inputs",
                "required_system_contract_refs",
                ["SYS-CONTRACT-A", "SYS-CONTRACT-B"],
            ),
            (
                "readiness_inputs",
                "system_contract_set_paths",
                ["docs/system/a.md", "docs/system/b.md"],
            ),
        )
        for section, field, expected in cases:
            with self.subTest(section=section, field=field):
                self.assertEqual(
                    docs_gate._execution_manifest_sequence(
                        manifest=manifest,
                        manifest_text=text,
                        section=section,
                        field=field,
                    ),
                    expected,
                )

    def test_iter010_executable_plan_snapshot_is_fail_closed(self) -> None:
        prerequisites = list(docs_gate.ITER010_DIRECTION_PREREQUISITE_CASE_IDS)
        freeze_case = docs_gate.ITER010_CURRENT_ACTION_CASE_ID
        quality_case = docs_gate.ITER010_DIRECTION_QUALITY_CASE_ID
        action_specs = docs_gate.iter010_plan_action_specs()
        self.assertEqual(len(action_specs), 11)
        action_and_produced_cases = list(
            dict.fromkeys(
                str(case_id)
                for spec in action_specs.values()
                for case_id in (
                    spec["scalars"]["case_id"],  # type: ignore[index]
                    *spec["sequences"]["produced_case_ids"],  # type: ignore[index]
                )
            )
        )
        all_plan_cases = list(
            dict.fromkeys([*prerequisites, *action_and_produced_cases])
        )
        preferred_profile_configuration = {
            "execution_profile_ref": "runtime-config:preferred-qualified-profile",
            "provider_identity": "AURORA",
            "model_identity": "nebula-x1",
        }
        fallback_profile_configuration = {
            "execution_profile_ref": "runtime-config:fallback-qualified-profile",
            "provider_identity": "BOREALIS",
            "model_identity": "quasar-y2",
            "admission_policy_plugin_ref": "fallback_admission_policy",
        }
        fallback_policy_plugin_configuration = {
            "schema": "ROUTE_ADMISSION_POLICY_PLUGIN@1",
            "route_role": "fallback",
            "configured_execution_profile_ref": (
                fallback_profile_configuration["execution_profile_ref"]
            ),
        }

        def action_payload(action_id: str, *, registered: bool) -> dict[str, object]:
            spec = action_specs[action_id]
            scalars = spec["scalars"]
            sequences = spec["sequences"]
            assert isinstance(scalars, dict)
            assert isinstance(sequences, dict)
            payload = copy.deepcopy(scalars)
            payload.update(
                {
                    field: list(items)
                    for field, items in sequences.items()
                    if isinstance(items, tuple)
                }
            )
            if registered:
                payload["transition"] = copy.deepcopy(spec["transition"])
                payload["locks"] = copy.deepcopy(spec["locks"])
            return payload

        def transition_receipt(
            action_id: str,
            verdict: str,
            *,
            outcomes: list[dict[str, str]] | None = None,
        ) -> tuple[docs_gate.Document, str]:
            def canonical_digest(value: object) -> str:
                encoded = json.dumps(
                    value,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode("utf-8")
                return "sha256:" + hashlib.sha256(encoded).hexdigest()

            root_input_set = {
                "schema": "VALUE_GATE_PROVIDER_NEUTRAL_ROOT_INPUT_SET@1",
                "question_ids": ["Q-STRUCTURE", "Q-FLOW", "Q-BEHAVIOR"],
                "system_arm_ids": list(docs_gate.ITER010_DIRECTION_QUALITY_ARMS[:3]),
                "entries": [
                    {
                        "question_id": question_id,
                        "system_arm_id": arm_id,
                        "root_input_digest": canonical_digest(
                            {
                                "question_id": question_id,
                                "system_arm_id": arm_id,
                            }
                        ),
                    }
                    for question_id in ("Q-STRUCTURE", "Q-FLOW", "Q-BEHAVIOR")
                    for arm_id in docs_gate.ITER010_DIRECTION_QUALITY_ARMS[:3]
                ],
            }
            preferred_profile = copy.deepcopy(preferred_profile_configuration)
            fallback_profile = copy.deepcopy(fallback_profile_configuration)
            fallback_policy_plugin = copy.deepcopy(
                fallback_policy_plugin_configuration
            )

            def quality_evidence(route_role: str) -> dict[str, object]:
                profile = (
                    preferred_profile if route_role == "preferred" else fallback_profile
                )
                terminal_classification = (
                    "TERMINAL_UNAVAILABLE"
                    if verdict == "INVALID" and route_role == "preferred"
                    else "OTHER_INVALID"
                    if verdict == "INVALID"
                    else "AVAILABLE"
                )
                admission_receipt = {
                    "schema": "ROUTE_ADMISSION_RECEIPT@1",
                    "route_role": route_role,
                    "decision": "ADMITTED",
                }
                terminal_receipt = {
                    "schema": "ROUTE_TERMINAL_RECEIPT@1",
                    "route_role": route_role,
                    "terminal_classification": terminal_classification,
                }
                return {
                    "provider_neutral_root_input_set": root_input_set,
                    "provider_neutral_root_input_set_digest": canonical_digest(
                        root_input_set
                    ),
                    "route_role": route_role,
                    "execution_profile_ref": profile["execution_profile_ref"],
                    "execution_profile": profile,
                    "execution_profile_digest": canonical_digest(profile),
                    "admission_receipt": admission_receipt,
                    "admission_receipt_digest": canonical_digest(admission_receipt),
                    "terminal_receipt": terminal_receipt,
                    "terminal_receipt_digest": canonical_digest(terminal_receipt),
                    "terminal_classification": terminal_classification,
                    "mixed_execution_profile_batch": False,
                }

            spec = action_specs[action_id]
            scalars = spec["scalars"]
            sequences = spec["sequences"]
            assert isinstance(scalars, dict)
            assert isinstance(sequences, dict)
            produced = list(sequences["produced_case_ids"])
            if outcomes is None:
                outcome_verdicts = ["PASS"] * len(produced)
                if verdict in {"FAIL", "INVALID"}:
                    outcome_verdicts[0] = verdict
                outcomes = [
                    {"case_id": str(case_id), "verdict": outcome_verdict}
                    for case_id, outcome_verdict in zip(
                        produced, outcome_verdicts, strict=True
                    )
                ]
            artifact = {
                "schema": docs_gate.ITER010_PLAN_EVIDENCE_SCHEMA,
                "result_id": scalars["result_ref"],
                "plan_revision_ref": docs_gate.ITER010_PLAN_REVISION_REF,
                "action_ref": action_id,
                "verification_case_id": scalars["case_id"],
                "plan_gate_verdict": verdict,
                "evidence_verifier": docs_gate.ITER010_PLAN_EVIDENCE_VERIFIER,
                "evidence_artifact_path": scalars["evidence_path"],
                "case_outcomes": outcomes,
                "action_evidence": {},
            }
            if action_id == docs_gate.ITER010_CURRENT_ACTION_ID:
                artifact["action_evidence"] = {
                    "provider_neutral_root_input_set": root_input_set,
                    "provider_neutral_root_input_set_digest": canonical_digest(
                        root_input_set
                    ),
                }
            elif action_id == docs_gate.ITER010_PREFERRED_QUALITY_ACTION_ID:
                artifact["action_evidence"] = quality_evidence("preferred")
            elif action_id == docs_gate.ITER010_FALLBACK_REFREEZE_ACTION_ID:
                artifact["action_evidence"] = {
                    "preferred_invalid_predecessor_ref": docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF,
                    "preferred_invalid_predecessor_seal_digest": "sha256:" + "6" * 64,
                    "provider_neutral_root_input_set": root_input_set,
                    "provider_neutral_root_input_set_digest": canonical_digest(
                        root_input_set
                    ),
                    "fallback_execution_profile_ref": fallback_profile[
                        "execution_profile_ref"
                    ],
                    "fallback_execution_profile": fallback_profile,
                    "fallback_execution_profile_digest": canonical_digest(
                        fallback_profile
                    ),
                    "fallback_admission_policy_plugin_ref": "fallback_admission_policy",
                    "fallback_admission_policy_plugin": fallback_policy_plugin,
                    "fallback_admission_policy_plugin_digest": canonical_digest(
                        fallback_policy_plugin
                    ),
                    "preferred_terminal_classification": "TERMINAL_UNAVAILABLE",
                    "mixed_execution_profile_batch": False,
                    "provider_dispatch_count": 0,
                    "new_human_authority_requested": False,
                }
            elif action_id == docs_gate.ITER010_FALLBACK_QUALITY_ACTION_ID:
                fallback_evidence = quality_evidence("fallback")
                fallback_evidence.update(
                    {
                        "fallback_refreeze_predecessor_ref": docs_gate.ITER010_FALLBACK_REFREEZE_RESULT_REF,
                        "fallback_refreeze_predecessor_seal_digest": "sha256:"
                        + "9" * 64,
                        "admission_policy_plugin_ref": "fallback_admission_policy",
                        "admission_policy_plugin": fallback_policy_plugin,
                        "admission_policy_plugin_digest": canonical_digest(
                            fallback_policy_plugin
                        ),
                    }
                )
                artifact["action_evidence"] = fallback_evidence
            # The digest deliberately binds these exact UTF-8 bytes rather than
            # a reconstructed/canonical JSON object.
            evidence_text = json.dumps(
                artifact,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            metadata = {
                "id": scalars["result_ref"],
                "kind": "iteration-result",
                "status": "sealed",
                "authority": "evidence",
                "iteration": "ITER-010",
                "plan_revision_ref": docs_gate.ITER010_PLAN_REVISION_REF,
                "action_ref": action_id,
                "verification_case_id": scalars["case_id"],
                "plan_gate_verdict": verdict,
                "evidence_schema": docs_gate.ITER010_PLAN_EVIDENCE_SCHEMA,
                "evidence_verifier": docs_gate.ITER010_PLAN_EVIDENCE_VERIFIER,
                "evidence_artifact_path": scalars["evidence_path"],
                "evidence_artifact_digest": "sha256:"
                + hashlib.sha256(evidence_text.encode("utf-8")).hexdigest(),
                "execution_input_digest": "sha256:" + "1" * 64,
                "runner_identity_digest": "sha256:" + "2" * 64,
                "runner_receipt_digest": "sha256:" + "3" * 64,
                "verification_report_digest": "sha256:" + "4" * 64,
                "subject_digest": "sha256:" + "5" * 64,
                "external_model_call_count": "0",
            }
            return (
                docs_gate.Document(
                    docs_gate.REPOSITORY / str(scalars["result_path"]),
                    metadata,
                    "# Sealed plan action Result\n",
                ),
                evidence_text,
            )

        def canonical_object_digest(value: object) -> str:
            encoded = json.dumps(
                value,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            return "sha256:" + hashlib.sha256(encoded).hexdigest()

        def reseal_result(
            result: docs_gate.Document, artifact: dict[str, object]
        ) -> tuple[docs_gate.Document, str]:
            evidence_text = json.dumps(
                artifact,
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            )
            return (
                docs_gate.Document(
                    result.path,
                    {
                        **result.metadata,
                        "evidence_artifact_digest": "sha256:"
                        + hashlib.sha256(evidence_text.encode("utf-8")).hexdigest(),
                    },
                    result.body,
                ),
                evidence_text,
            )

        def verification_for(
            verdicts: dict[str, str] | None = None,
        ) -> docs_gate.Document:
            resolved = {case_id: "NOT-RUN" for case_id in all_plan_cases}
            resolved.update({case_id: "PASS" for case_id in prerequisites})
            if verdicts is not None:
                resolved.update(verdicts)
            rows = "".join(
                f"| {case_id} | resolved claim | quality | frozen input | resolved expected | "
                f"{'result-ref' if verdict in {'PASS', 'FAIL', 'INVALID'} else 'not-executed'} | {verdict} / blocking |\n"
                for case_id, verdict in resolved.items()
            )
            return docs_gate.Document(
                docs_gate.REPOSITORY
                / "docs/project/iterations/iteration-010/verification-matrix.md",
                {"id": "ITER-010-VERIFICATION", "iteration": "ITER-010"},
                rows,
            )

        manifest: dict[str, object] = {
            "schema_version": 2,
            "provider_route_policy": generic_provider_route_policy(),
            "execution_profile_configurations": {
                "schema": docs_gate.EXECUTION_PROFILE_CONFIGURATION_SCHEMA,
                "preferred": preferred_profile_configuration,
                "fallback": fallback_profile_configuration,
            },
            "fallback_admission_policy": fallback_policy_plugin_configuration,
            "plan_execution_control": {
                "schema": docs_gate.ITER010_PLAN_EXECUTION_CONTROL_SCHEMA,
                "plan_revision_ref": docs_gate.ITER010_PLAN_REVISION_REF,
                "enforcement_mode": "fail-closed",
                "authorization_refs": list(
                    docs_gate.ITER010_PLAN_AUTHORIZATION_REFS
                ),
                "current_action": action_payload(
                    docs_gate.ITER010_CURRENT_ACTION_ID, registered=False
                ),
                "transition": copy.deepcopy(
                    action_specs[docs_gate.ITER010_CURRENT_ACTION_ID]["transition"]
                ),
                "locks": copy.deepcopy(
                    action_specs[docs_gate.ITER010_CURRENT_ACTION_ID]["locks"]
                ),
                "next_action_contracts": {
                    str(spec["registry_key"]): action_payload(
                        action_id, registered=True
                    )
                    for action_id, spec in action_specs.items()
                    if spec["registry_key"] is not None
                },
            },
            "direction_quality_gate": {
                "schema": docs_gate.ITER010_DIRECTION_QUALITY_GATE_SCHEMA,
                "case_id": quality_case,
                "owner_slice_ref": "ITER-010-SLICE-001",
                "status": "locked-until-direction-freeze-pass",
                "execution_order": docs_gate.ITER010_DIRECTION_MICRO_CHECKPOINT_ORDER,
                "arms": list(docs_gate.ITER010_DIRECTION_QUALITY_ARMS),
                "question_count": 3,
                "question_set_rule": docs_gate.ITER010_DIRECTION_QUESTION_SET_RULE,
                "source_truth_owner": "independent-exact-source-ledger-not-any-model-answer",
                "direct_evidence_arm_is_oracle": False,
                "current_codex_role": docs_gate.STRICT_CODEX_BASELINE_ROLE,
                "current_codex_is_oracle_or_reviewer": False,
                "first_three_arms_same_provider_model_configuration": True,
                "source_only_and_world_model_arms_same_agent_prompt_tools_budget_cache_and_reviewer": True,
                "outputs_sealed_before_cross_arm_disclosure": True,
                "blind_randomized_independent_evaluation": True,
                "absolute_quality_pass_required": True,
                "absolute_quality_rule": docs_gate.ITER010_DIRECTION_ABSOLUTE_QUALITY_RULE,
                "world_model_arm_must_not_lose_to_direct_evidence": True,
                "world_model_arm_must_not_lose_to_source_only": True,
                "world_model_arm_must_not_lose_to_current_codex": True,
                "current_codex_overall_quality_margin_rule": "strictly-positive",
                "non_locator_world_model_contribution_required": True,
                "all_tie_outcome": "FAIL",
                "cost_or_latency_can_compensate_quality": False,
                "product_code_change_before_verdict_allowed": False,
                "preferred_route_execution_profile_ref": "provider_route_policy.preferred_execution_profile_ref",
                "fallback_route_execution_profile_ref": "provider_route_policy.fallback_execution_profile_ref",
                "preferred_quality_action_id": docs_gate.ITER010_PREFERRED_QUALITY_ACTION_ID,
                "preferred_quality_result_ref": docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF,
                "mixed_provider_batch_allowed": False,
                "fallback_refreeze_action_id": docs_gate.ITER010_FALLBACK_REFREEZE_ACTION_ID,
                "fallback_refreeze_case_id": docs_gate.ITER010_FALLBACK_REFREEZE_CASE_ID,
                "fallback_refreeze_requires_new_human_authority": False,
                "fallback_refreeze_provider_dispatch_allowed": False,
                "fallback_refreeze_action_evidence_required": (
                    "preferred-invalid-predecessor-seal,provider-neutral-root-input-set,"
                    "fallback-execution-profile-ref-and-digest,"
                    "fallback-admission-policy-plugin-ref-and-digest,no-mixed-batch,"
                    "zero-provider-dispatch,no-new-human-authority"
                ),
                "fallback_quality_action_id": docs_gate.ITER010_FALLBACK_QUALITY_ACTION_ID,
                "fallback_quality_result_ref": docs_gate.ITER010_FALLBACK_QUALITY_RESULT_REF,
                "fallback_allowed_only_after_refreeze_pass": True,
                "fallback_admission_prerequisite_case_id": "V-FALLBACK-ROUTE-ADMISSION-001",
                "fallback_quality_action_evidence_required": (
                    "fallback-refreeze-predecessor-seal,provider-neutral-root-input-set,"
                    "execution-profile-ref-and-digest,admission-and-terminal-receipts,"
                    "no-mixed-batch"
                ),
                "quality_case_pass_result_cardinality": "at-most-one",
                "preferred_terminal_unavailable_action": (
                    "invalidate-preferred-batch-and-enter-pre-registered-fallback-refreeze"
                ),
                "preferred_other_invalid_action": (
                    "fallback-refreeze-fails-back-to-preferred-quality"
                ),
                "fallback_invalid_action": "fail-closed-at-fallback-quality",
                "target_product_commit": "a" * 40,
                "target_product_tree": "b" * 40,
                "dirty_v7_status": "quarantined-not-input",
            },
            "product_goal_alignment": {
                "blocking_case_ids": all_plan_cases,
                "alpha_agent_comparison_binding": {
                    "case_id": quality_case,
                    "new_slice_ref": "ITER-010-SLICE-001",
                    "arms": ",".join(docs_gate.ITER010_DIRECTION_QUALITY_ARMS),
                    "current_codex_is_oracle_or_reviewer": False,
                    "result_role": "blocking-iter010-strict-superiority-direction-gate",
                },
            },
            "public_oss_evaluation_standing_authority": {
                "owner_decision_ref": "ITER-010-PDR-008",
                "current_plan_amendment_ref": docs_gate.ITER010_PLAN_REVISION_REF,
                "verification_case_id": docs_gate.ITER010_PUBLIC_AUTHORITY_CASE_ID,
                "verification_status": "NOT-RUN",
                "independent_action_entry_allowed": False,
                "next_execution_entry_action_id": docs_gate.ITER010_CURRENT_ACTION_ID,
                "next_execution_entry_case_id": docs_gate.ITER010_CURRENT_ACTION_CASE_ID,
            },
        }
        current = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/current.md",
            {
                "id": "PROJECT-CURRENT",
                "plan_revision_ref": docs_gate.ITER010_PLAN_REVISION_REF,
                "next_action": docs_gate.ITER010_CURRENT_ACTION_ID,
                "next_action_case_id": freeze_case,
                "active_slice": "ITER-010-SLICE-001",
            },
            "",
        )
        verification = verification_for()

        validate = lambda candidate=manifest, current_doc=current, matrix=verification, result_docs=None, evidence_docs=None: (
            docs_gate.validate_iter010_plan_execution_snapshot(
                candidate,
                "manifest.yaml",
                current=current_doc,
                verification=matrix,
                transition_results=result_docs,
                transition_evidence_artifacts=evidence_docs,
                require_external_bindings=True,
            )
        )
        self.assertEqual(validate(), [])

        recovery_candidate = copy.deepcopy(manifest)
        recovery_control = recovery_candidate["plan_execution_control"]
        assert isinstance(recovery_control, dict)
        recovery_control["current_action"] = action_payload(
            docs_gate.ITER010_PLAN_RECOVERY_ACTION_ID, registered=False
        )
        recovery_control["transition"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_PLAN_RECOVERY_ACTION_ID]["transition"]
        )
        recovery_control["locks"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_PLAN_RECOVERY_ACTION_ID]["locks"]
        )
        recovery_candidate["user_plan_recovery"] = {
            "schema": "USER_DIRECTED_PLAN_RECOVERY@1",
            "status": "authorized-recovery-entry-installed",
            "authorization_ref": docs_gate.ITER010_PLAN_RECOVERY_AUTHORIZATION_REF,
            "authorization_reusable": False,
            "trusted_base_commit": docs_gate.ITER010_PLAN_RECOVERY_TRUSTED_COMMIT,
            "trusted_base_tree": docs_gate.ITER010_PLAN_RECOVERY_TRUSTED_TREE,
            "interrupted_plan_revision_ref": docs_gate.ITER010_PLAN_REVISION_REF,
            "interrupted_action_id": docs_gate.ITER010_CURRENT_ACTION_ID,
            "recovery_action_id": docs_gate.ITER010_PLAN_RECOVERY_ACTION_ID,
            "recovery_case_id": docs_gate.ITER010_PLAN_RECOVERY_CASE_ID,
            "target_plan_revision_ref": "ITER-010-PDR-010",
            "scope": "governance-only-no-product-no-external-execution",
            "one_time_recovery": True,
            "product_code_changes_allowed": False,
            "external_execution_allowed": False,
        }
        recovery_public_authority = recovery_candidate[
            "public_oss_evaluation_standing_authority"
        ]
        assert isinstance(recovery_public_authority, dict)
        recovery_public_authority["next_execution_entry_action_id"] = (
            docs_gate.ITER010_PLAN_RECOVERY_ACTION_ID
        )
        recovery_public_authority["next_execution_entry_case_id"] = (
            docs_gate.ITER010_PLAN_RECOVERY_CASE_ID
        )
        recovery_current = docs_gate.Document(
            current.path,
            {
                **current.metadata,
                "next_action": docs_gate.ITER010_PLAN_RECOVERY_ACTION_ID,
                "next_action_case_id": docs_gate.ITER010_PLAN_RECOVERY_CASE_ID,
            },
            "",
        )
        self.assertEqual(
            validate(recovery_candidate, current_doc=recovery_current), []
        )

        recovery_unlocked = copy.deepcopy(recovery_candidate)
        recovery_unlocked["plan_execution_control"]["locks"][  # type: ignore[index]
            "provider_dispatch"
        ] = False
        self.assertTrue(
            any(
                "provider_dispatch" in error
                for error in validate(
                    recovery_unlocked, current_doc=recovery_current
                )
            )
        )

        recovery_scope_widened = copy.deepcopy(recovery_candidate)
        recovery_scope_widened["user_plan_recovery"][  # type: ignore[index]
            "product_code_changes_allowed"
        ] = True
        self.assertTrue(
            any(
                "user_plan_recovery" in error
                for error in validate(
                    recovery_scope_widened, current_doc=recovery_current
                )
            )
        )

        missing_route_policy = copy.deepcopy(manifest)
        missing_route_policy.pop("provider_route_policy")
        self.assertTrue(
            any(
                "provider_route_policy is required for ITER-010" in error
                for error in validate(missing_route_policy)
            )
        )

        missing_profile_configuration = copy.deepcopy(manifest)
        missing_profile_configuration.pop("execution_profile_configurations")
        self.assertTrue(
            any(
                "execution_profile_configurations must be a mapping" in error
                for error in validate(missing_profile_configuration)
            )
        )

        unresolved_plugin_configuration = copy.deepcopy(manifest)
        unresolved_plugin_configuration.pop("fallback_admission_policy")
        self.assertTrue(
            any(
                "must resolve to a configuration object" in error
                for error in validate(unresolved_plugin_configuration)
            )
        )

        missing_control = copy.deepcopy(manifest)
        missing_control.pop("plan_execution_control")
        self.assertTrue(
            any("plan_execution_control" in error for error in validate(missing_control))
        )

        extra_control_override = copy.deepcopy(manifest)
        extra_control_override["plan_execution_control"][  # type: ignore[index]
            "developer_override"
        ] = True
        self.assertTrue(
            any("exactly the frozen control keys" in error for error in validate(extra_control_override))
        )

        csv_authorization_refs = copy.deepcopy(manifest)
        csv_authorization_refs["plan_execution_control"][  # type: ignore[index]
            "authorization_refs"
        ] = ",".join(docs_gate.ITER010_PLAN_AUTHORIZATION_REFS)
        self.assertTrue(
            any("authorization_refs" in error for error in validate(csv_authorization_refs))
        )

        missing_result_ref = copy.deepcopy(manifest)
        missing_result_ref["plan_execution_control"]["current_action"].pop(  # type: ignore[index]
            "result_ref"
        )
        self.assertTrue(
            any("current_action.result_ref" in error for error in validate(missing_result_ref))
        )

        wrong_owner = copy.deepcopy(manifest)
        wrong_owner["plan_execution_control"]["current_action"][  # type: ignore[index]
            "owner_slice_ref"
        ] = "ITER-010-SLICE-002"
        self.assertTrue(any("owner_slice_ref" in error for error in validate(wrong_owner)))

        missing_registered_action = copy.deepcopy(manifest)
        missing_registered_action["plan_execution_control"][  # type: ignore[index]
            "next_action_contracts"
        ].pop("direction_rework")
        self.assertTrue(
            any(
                "pre-registered action keys" in error
                for error in validate(missing_registered_action)
            )
        )

        unregistered_current = copy.deepcopy(manifest)
        unregistered_current["plan_execution_control"]["current_action"][  # type: ignore[index]
            "id"
        ] = "ITER-010-ACTION-UNREGISTERED-001"
        self.assertTrue(
            any("not the initial freeze or a pre-registered" in error for error in validate(unregistered_current))
        )

        csv_prerequisites = copy.deepcopy(manifest)
        csv_prerequisites["plan_execution_control"]["current_action"][  # type: ignore[index]
            "prerequisite_case_ids"
        ] = ",".join(prerequisites)
        self.assertTrue(
            any("exact frozen YAML block sequence" in error for error in validate(csv_prerequisites))
        )

        three_arms = copy.deepcopy(manifest)
        three_arms["direction_quality_gate"]["arms"] = list(  # type: ignore[index]
            docs_gate.ITER010_DIRECTION_QUALITY_ARMS[1:]
        )
        self.assertTrue(any("four-arm order" in error for error in validate(three_arms)))

        grandfathered_three_arm = copy.deepcopy(manifest)
        grandfathered_three_arm["product_goal_alignment"][  # type: ignore[index]
            "alpha_agent_comparison_binding"
        ]["arms"] = (
            "same-agent-source-only,same-agent-world-model-and-source,current-codex"
        )
        self.assertTrue(
            any("same exact four-arm order" in error for error in validate(grandfathered_three_arm))
        )

        codex_judge = copy.deepcopy(manifest)
        codex_judge["direction_quality_gate"][  # type: ignore[index]
            "current_codex_is_oracle_or_reviewer"
        ] = True
        self.assertTrue(
            any("current_codex_is_oracle_or_reviewer" in error for error in validate(codex_judge))
        )

        tie_pass = copy.deepcopy(manifest)
        tie_pass["direction_quality_gate"]["all_tie_outcome"] = "PASS"  # type: ignore[index]
        self.assertTrue(any("all_tie_outcome" in error for error in validate(tie_pass)))

        quality_compensated_by_cost = copy.deepcopy(manifest)
        quality_compensated_by_cost["direction_quality_gate"][  # type: ignore[index]
            "cost_or_latency_can_compensate_quality"
        ] = True
        self.assertTrue(
            any(
                "cost_or_latency_can_compensate_quality" in error
                for error in validate(quality_compensated_by_cost)
            )
        )

        unlocked_product = copy.deepcopy(manifest)
        unlocked_product["plan_execution_control"]["locks"][  # type: ignore[index]
            "product_code_changes"
        ] = False
        unlocked_product["direction_quality_gate"][  # type: ignore[index]
            "product_code_change_before_verdict_allowed"
        ] = True
        unlocked_errors = validate(unlocked_product)
        self.assertTrue(any("product_code_changes" in error for error in unlocked_errors))
        self.assertTrue(
            any("product_code_change_before_verdict_allowed" in error for error in unlocked_errors)
        )

        quality_candidate = copy.deepcopy(manifest)
        quality_control = quality_candidate["plan_execution_control"]
        assert isinstance(quality_control, dict)
        quality_control["current_action"] = action_payload(
            docs_gate.ITER010_PREFERRED_QUALITY_ACTION_ID,
            registered=False,
        )
        quality_control["transition"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_PREFERRED_QUALITY_ACTION_ID]["transition"]
        )
        quality_control["locks"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_PREFERRED_QUALITY_ACTION_ID]["locks"]
        )
        quality_gate = quality_candidate["direction_quality_gate"]
        assert isinstance(quality_gate, dict)
        quality_gate["status"] = "authorized"
        quality_alignment = quality_candidate["product_goal_alignment"]
        assert isinstance(quality_alignment, dict)
        quality_alignment["mature_source_agent_identity_digest"] = "sha256:" + "c" * 64
        quality_current = docs_gate.Document(
            current.path,
            {
                **current.metadata,
                "next_action": docs_gate.ITER010_PREFERRED_QUALITY_ACTION_ID,
                "next_action_case_id": quality_case,
            },
            "",
        )
        freeze_produced = list(
            action_specs[docs_gate.ITER010_CURRENT_ACTION_ID]["sequences"][  # type: ignore[index]
                "produced_case_ids"
            ]
        )
        quality_verification = verification_for(
            {case_id: "PASS" for case_id in freeze_produced}
        )
        freeze_result, freeze_evidence = transition_receipt(
            docs_gate.ITER010_CURRENT_ACTION_ID,
            "PASS",
        )
        quality_results = {
            docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: freeze_result
        }
        quality_evidence = {
            docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: freeze_evidence
        }
        self.assertEqual(
            validate(
                quality_candidate,
                current_doc=quality_current,
                matrix=quality_verification,
                result_docs=quality_results,
                evidence_docs=quality_evidence,
            ),
            [],
        )

        identity_leaked_freeze_artifact = json.loads(freeze_evidence)
        leaked_root = identity_leaked_freeze_artifact["action_evidence"][
            "provider_neutral_root_input_set"
        ]
        leaked_root["execution_hint"] = "use-nebula-x1"
        identity_leaked_freeze_artifact["action_evidence"][
            "provider_neutral_root_input_set_digest"
        ] = canonical_object_digest(leaked_root)
        identity_leaked_freeze_result, identity_leaked_freeze_evidence = (
            reseal_result(freeze_result, identity_leaked_freeze_artifact)
        )
        identity_leak_errors = validate(
            quality_candidate,
            current_doc=quality_current,
            matrix=quality_verification,
            result_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: (
                    identity_leaked_freeze_result
                )
            },
            evidence_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: (
                    identity_leaked_freeze_evidence
                )
            },
        )
        self.assertTrue(
            any(
                "provider_neutral_root_input_set" in error
                and "nebula-x1" in error
                for error in identity_leak_errors
            ),
            identity_leak_errors,
        )

        for forbidden_field in (
            "provider_identity",
            "model_identity",
            "route_role",
            "execution_profile_ref",
            "admission_policy_plugin_ref",
        ):
            with self.subTest(provider_neutral_control_field=forbidden_field):
                attacker_artifact = json.loads(freeze_evidence)
                attacker_root = attacker_artifact["action_evidence"][
                    "provider_neutral_root_input_set"
                ]
                attacker_root[forbidden_field] = "ATTACKER_UNREGISTERED"
                attacker_artifact["action_evidence"][
                    "provider_neutral_root_input_set_digest"
                ] = canonical_object_digest(attacker_root)
                attacker_result, attacker_evidence = reseal_result(
                    freeze_result,
                    attacker_artifact,
                )
                attacker_errors = validate(
                    quality_candidate,
                    current_doc=quality_current,
                    matrix=quality_verification,
                    result_docs={
                        docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: attacker_result
                    },
                    evidence_docs={
                        docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: attacker_evidence
                    },
                )
                self.assertTrue(
                    any(
                        "must contain exactly schema, question_ids, system_arm_ids, and entries"
                        in error
                        for error in attacker_errors
                    ),
                    attacker_errors,
                )

        incomplete_cartesian_artifact = json.loads(freeze_evidence)
        incomplete_cartesian_root = incomplete_cartesian_artifact["action_evidence"][
            "provider_neutral_root_input_set"
        ]
        incomplete_cartesian_root["entries"].pop()
        incomplete_cartesian_artifact["action_evidence"][
            "provider_neutral_root_input_set_digest"
        ] = canonical_object_digest(incomplete_cartesian_root)
        incomplete_cartesian_result, incomplete_cartesian_evidence = reseal_result(
            freeze_result,
            incomplete_cartesian_artifact,
        )
        incomplete_cartesian_errors = validate(
            quality_candidate,
            current_doc=quality_current,
            matrix=quality_verification,
            result_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: (
                    incomplete_cartesian_result
                )
            },
            evidence_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: (
                    incomplete_cartesian_evidence
                )
            },
        )
        self.assertTrue(
            any(
                "complete question_ids x system_arm_ids Cartesian product" in error
                for error in incomplete_cartesian_errors
            ),
            incomplete_cartesian_errors,
        )

        forged_missing_digest_result = docs_gate.Document(
            freeze_result.path,
            {
                key: value
                for key, value in {
                    **freeze_result.metadata,
                    "kind": "forged-result-note",
                }.items()
                if key != "runner_receipt_digest"
            },
            freeze_result.body,
        )
        forged_errors = validate(
            quality_candidate,
            current_doc=quality_current,
            matrix=quality_verification,
            result_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: (
                    forged_missing_digest_result
                )
            },
            evidence_docs=quality_evidence,
        )
        self.assertTrue(any("kind must equal iteration-result" in error for error in forged_errors))
        self.assertTrue(any("runner_receipt_digest" in error for error in forged_errors))

        wrong_artifact_digest_result = docs_gate.Document(
            freeze_result.path,
            {
                **freeze_result.metadata,
                "evidence_artifact_digest": "sha256:" + "0" * 64,
            },
            freeze_result.body,
        )
        wrong_artifact_errors = validate(
            quality_candidate,
            current_doc=quality_current,
            matrix=quality_verification,
            result_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: (
                    wrong_artifact_digest_result
                )
            },
            evidence_docs=quality_evidence,
        )
        self.assertTrue(
            any("must match exact artifact bytes" in error for error in wrong_artifact_errors),
            wrong_artifact_errors,
        )

        missing_case_artifact = json.loads(freeze_evidence)
        missing_case_artifact["case_outcomes"] = missing_case_artifact[
            "case_outcomes"
        ][:-1]
        missing_case_evidence = json.dumps(
            missing_case_artifact,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        missing_case_result = docs_gate.Document(
            freeze_result.path,
            {
                **freeze_result.metadata,
                "evidence_artifact_digest": "sha256:"
                + hashlib.sha256(missing_case_evidence.encode("utf-8")).hexdigest(),
            },
            freeze_result.body,
        )
        missing_produced_errors = validate(
            quality_candidate,
            current_doc=quality_current,
            matrix=quality_verification,
            result_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: missing_case_result
            },
            evidence_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: missing_case_evidence
            },
        )
        self.assertTrue(
            any("exactly cover predecessor produced_case_ids" in error for error in missing_produced_errors),
            missing_produced_errors,
        )

        wrong_aggregate_artifact = json.loads(freeze_evidence)
        wrong_aggregate_artifact["case_outcomes"][0]["verdict"] = "FAIL"
        wrong_aggregate_evidence = json.dumps(
            wrong_aggregate_artifact,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        wrong_aggregate_result = docs_gate.Document(
            freeze_result.path,
            {
                **freeze_result.metadata,
                "evidence_artifact_digest": "sha256:"
                + hashlib.sha256(
                    wrong_aggregate_evidence.encode("utf-8")
                ).hexdigest(),
            },
            freeze_result.body,
        )
        wrong_aggregate_errors = validate(
            quality_candidate,
            current_doc=quality_current,
            matrix=quality_verification,
            result_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: wrong_aggregate_result
            },
            evidence_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: wrong_aggregate_evidence
            },
        )
        self.assertTrue(
            any("INVALID > FAIL > PASS aggregation" in error for error in wrong_aggregate_errors),
            wrong_aggregate_errors,
        )

        no_freeze_result_errors = validate(
            quality_candidate,
            current_doc=quality_current,
            matrix=quality_verification,
        )
        self.assertTrue(
            any("requires exact predecessor Result" in error for error in no_freeze_result_errors)
        )

        failed_freeze_result, failed_freeze_evidence = transition_receipt(
            docs_gate.ITER010_CURRENT_ACTION_ID,
            "FAIL",
        )
        wrong_verdict_errors = validate(
            quality_candidate,
            current_doc=quality_current,
            matrix=quality_verification,
            result_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: failed_freeze_result
            },
            evidence_docs={
                docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: failed_freeze_evidence
            },
        )
        self.assertTrue(any("must equal PASS" in error for error in wrong_verdict_errors))

        pending_quality_identity = copy.deepcopy(quality_candidate)
        pending_quality_identity["product_goal_alignment"][  # type: ignore[index]
            "mature_source_agent_identity_digest"
        ] = docs_gate.ITER010_PENDING_CODEX_IDENTITY
        self.assertTrue(
            any(
                "must be exact sha256 after the freeze action" in error
                for error in validate(
                    pending_quality_identity,
                    current_doc=quality_current,
                    matrix=quality_verification,
                    result_docs=quality_results,
                    evidence_docs=quality_evidence,
                )
            )
        )

        quality_dispatch_locked = copy.deepcopy(quality_candidate)
        quality_dispatch_locked["plan_execution_control"]["locks"][  # type: ignore[index]
            "provider_dispatch"
        ] = True
        self.assertTrue(
            any(
                "locks.provider_dispatch must equal False" in error
                for error in validate(
                    quality_dispatch_locked,
                    current_doc=quality_current,
                    matrix=quality_verification,
                    result_docs=quality_results,
                    evidence_docs=quality_evidence,
                )
            )
        )

        wrong_quality_transition = copy.deepcopy(quality_candidate)
        wrong_quality_transition["plan_execution_control"]["transition"][  # type: ignore[index]
            "fail_next_action_id"
        ] = "ITER-010-ACTION-PATCH-ANSWER-001"
        self.assertTrue(
            any(
                "transition.fail_next_action_id" in error
                for error in validate(
                    wrong_quality_transition,
                    current_doc=quality_current,
                    matrix=quality_verification,
                    result_docs=quality_results,
                    evidence_docs=quality_evidence,
                )
            )
        )

        independent_public_authority = copy.deepcopy(manifest)
        independent_public_authority[
            "public_oss_evaluation_standing_authority"
        ]["independent_action_entry_allowed"] = True  # type: ignore[index]
        self.assertTrue(
            any(
                "independent_action_entry_allowed" in error
                for error in validate(independent_public_authority)
            )
        )
        for field, wrong_value in (
            ("verification_status", "FAIL"),
            (
                "next_execution_entry_action_id",
                "ITER-010-ACTION-PUBLIC-OSS-AUTHORITY-001",
            ),
            ("current_plan_amendment_ref", "ITER-010-PDR-008"),
        ):
            with self.subTest(public_authority_field=field):
                drifted_authority = copy.deepcopy(manifest)
                drifted_authority["public_oss_evaluation_standing_authority"][  # type: ignore[index]
                    field
                ] = wrong_value
                self.assertTrue(
                    any(field in error for error in validate(drifted_authority))
                )

        fallback_refreeze_candidate = copy.deepcopy(quality_candidate)
        fallback_refreeze_control = fallback_refreeze_candidate[
            "plan_execution_control"
        ]
        assert isinstance(fallback_refreeze_control, dict)
        fallback_refreeze_control["current_action"] = action_payload(
            docs_gate.ITER010_FALLBACK_REFREEZE_ACTION_ID,
            registered=False,
        )
        fallback_refreeze_control["transition"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_FALLBACK_REFREEZE_ACTION_ID][
                "transition"
            ]
        )
        fallback_refreeze_control["locks"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_FALLBACK_REFREEZE_ACTION_ID]["locks"]
        )
        fallback_refreeze_candidate["direction_quality_gate"][  # type: ignore[index]
            "status"
        ] = "preferred-invalid-fallback-refreeze-authorized"
        fallback_refreeze_current = docs_gate.Document(
            current.path,
            {
                **current.metadata,
                "next_action": docs_gate.ITER010_FALLBACK_REFREEZE_ACTION_ID,
                "next_action_case_id": docs_gate.ITER010_FALLBACK_REFREEZE_CASE_ID,
            },
            "",
        )
        preferred_invalid_result, preferred_invalid_evidence = transition_receipt(
            docs_gate.ITER010_PREFERRED_QUALITY_ACTION_ID,
            "INVALID",
        )
        fallback_refreeze_verification = verification_for(
            {
                **{str(case_id): "PASS" for case_id in freeze_produced},
                quality_case: "INVALID",
            }
        )
        self.assertEqual(
            validate(
                fallback_refreeze_candidate,
                current_doc=fallback_refreeze_current,
                matrix=fallback_refreeze_verification,
                result_docs={
                    docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: preferred_invalid_result
                },
                evidence_docs={
                    docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: preferred_invalid_evidence
                },
            ),
            [],
        )
        mismatched_preferred_profile_artifact = json.loads(
            preferred_invalid_evidence
        )
        mismatched_preferred_profile = {
            **mismatched_preferred_profile_artifact["action_evidence"][
                "execution_profile"
            ],
            "model_identity": "untrusted-model",
        }
        mismatched_preferred_profile_artifact["action_evidence"][
            "execution_profile"
        ] = mismatched_preferred_profile
        mismatched_preferred_profile_artifact["action_evidence"][
            "execution_profile_digest"
        ] = canonical_object_digest(mismatched_preferred_profile)
        mismatched_preferred_profile_result, mismatched_preferred_profile_evidence = (
            reseal_result(
                preferred_invalid_result,
                mismatched_preferred_profile_artifact,
            )
        )
        mismatched_profile_errors = validate(
            fallback_refreeze_candidate,
            current_doc=fallback_refreeze_current,
            matrix=fallback_refreeze_verification,
            result_docs={
                docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: (
                    mismatched_preferred_profile_result
                )
            },
            evidence_docs={
                docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: (
                    mismatched_preferred_profile_evidence
                )
            },
        )
        self.assertTrue(
            any(
                "execution_profile must exactly equal the trusted preferred" in error
                for error in mismatched_profile_errors
            ),
            mismatched_profile_errors,
        )
        missing_fallback_admission_predecessor = copy.deepcopy(
            fallback_refreeze_candidate
        )
        missing_fallback_admission_predecessor["plan_execution_control"][  # type: ignore[index]
            "current_action"
        ]["prerequisite_case_ids"].remove("V-FALLBACK-ROUTE-ADMISSION-001")
        self.assertTrue(
            any(
                "prerequisite_case_ids" in error
                for error in validate(
                    missing_fallback_admission_predecessor,
                    current_doc=fallback_refreeze_current,
                    matrix=fallback_refreeze_verification,
                    result_docs={
                        docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: preferred_invalid_result
                    },
                    evidence_docs={
                        docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: preferred_invalid_evidence
                    },
                )
            )
        )

        fallback_quality_candidate = copy.deepcopy(fallback_refreeze_candidate)
        fallback_quality_control = fallback_quality_candidate["plan_execution_control"]
        assert isinstance(fallback_quality_control, dict)
        fallback_quality_control["current_action"] = action_payload(
            docs_gate.ITER010_FALLBACK_QUALITY_ACTION_ID,
            registered=False,
        )
        fallback_quality_control["transition"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_FALLBACK_QUALITY_ACTION_ID]["transition"]
        )
        fallback_quality_control["locks"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_FALLBACK_QUALITY_ACTION_ID]["locks"]
        )
        fallback_quality_candidate["direction_quality_gate"][  # type: ignore[index]
            "status"
        ] = "fallback-refreeze-passed-direction-quality-authorized"
        fallback_quality_current = docs_gate.Document(
            current.path,
            {
                **current.metadata,
                "next_action": docs_gate.ITER010_FALLBACK_QUALITY_ACTION_ID,
                "next_action_case_id": quality_case,
            },
            "",
        )
        refreeze_result, refreeze_evidence = transition_receipt(
            docs_gate.ITER010_FALLBACK_REFREEZE_ACTION_ID,
            "PASS",
        )
        fallback_quality_verification = verification_for(
            {
                **{str(case_id): "PASS" for case_id in freeze_produced},
                quality_case: "INVALID",
                docs_gate.ITER010_FALLBACK_REFREEZE_CASE_ID: "PASS",
            }
        )
        self.assertEqual(
            validate(
                fallback_quality_candidate,
                current_doc=fallback_quality_current,
                matrix=fallback_quality_verification,
                result_docs={
                    docs_gate.ITER010_FALLBACK_REFREEZE_RESULT_REF: refreeze_result
                },
                evidence_docs={
                    docs_gate.ITER010_FALLBACK_REFREEZE_RESULT_REF: refreeze_evidence
                },
            ),
            [],
        )
        mismatched_plugin_artifact = json.loads(refreeze_evidence)
        mismatched_plugin = {
            **mismatched_plugin_artifact["action_evidence"][
                "fallback_admission_policy_plugin"
            ],
            "route_role": "preferred",
        }
        mismatched_plugin_artifact["action_evidence"][
            "fallback_admission_policy_plugin"
        ] = mismatched_plugin
        mismatched_plugin_artifact["action_evidence"][
            "fallback_admission_policy_plugin_digest"
        ] = canonical_object_digest(mismatched_plugin)
        mismatched_plugin_result, mismatched_plugin_evidence = reseal_result(
            refreeze_result,
            mismatched_plugin_artifact,
        )
        mismatched_plugin_errors = validate(
            fallback_quality_candidate,
            current_doc=fallback_quality_current,
            matrix=fallback_quality_verification,
            result_docs={
                docs_gate.ITER010_FALLBACK_REFREEZE_RESULT_REF: (
                    mismatched_plugin_result
                )
            },
            evidence_docs={
                docs_gate.ITER010_FALLBACK_REFREEZE_RESULT_REF: (
                    mismatched_plugin_evidence
                )
            },
        )
        self.assertTrue(
            any(
                "fallback_admission_policy_plugin must exactly equal the trusted" in error
                for error in mismatched_plugin_errors
            ),
            mismatched_plugin_errors,
        )
        incomplete_refreeze_artifact = json.loads(refreeze_evidence)
        incomplete_refreeze_artifact["action_evidence"].pop(
            "provider_neutral_root_input_set_digest"
        )
        incomplete_refreeze_evidence = json.dumps(
            incomplete_refreeze_artifact,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        incomplete_refreeze_result = docs_gate.Document(
            refreeze_result.path,
            {
                **refreeze_result.metadata,
                "evidence_artifact_digest": "sha256:"
                + hashlib.sha256(
                    incomplete_refreeze_evidence.encode("utf-8")
                ).hexdigest(),
            },
            refreeze_result.body,
        )
        self.assertTrue(
            any(
                "FallbackRouteRefreeze action_evidence"
                in error
                for error in validate(
                    fallback_quality_candidate,
                    current_doc=fallback_quality_current,
                    matrix=fallback_quality_verification,
                    result_docs={
                        docs_gate.ITER010_FALLBACK_REFREEZE_RESULT_REF: (
                            incomplete_refreeze_result
                        )
                    },
                    evidence_docs={
                        docs_gate.ITER010_FALLBACK_REFREEZE_RESULT_REF: (
                            incomplete_refreeze_evidence
                        )
                    },
                )
            )
        )

        minimum_web_candidate = copy.deepcopy(fallback_quality_candidate)
        minimum_web_control = minimum_web_candidate["plan_execution_control"]
        assert isinstance(minimum_web_control, dict)
        minimum_web_control["current_action"] = action_payload(
            docs_gate.ITER010_MINIMUM_WEB_ACTION_ID,
            registered=False,
        )
        minimum_web_control["transition"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_MINIMUM_WEB_ACTION_ID]["transition"]
        )
        minimum_web_control["locks"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_MINIMUM_WEB_ACTION_ID]["locks"]
        )
        minimum_web_candidate["direction_quality_gate"][  # type: ignore[index]
            "status"
        ] = "direction-quality-passed-minimum-web-authorized"
        minimum_web_current = docs_gate.Document(
            current.path,
            {
                **current.metadata,
                "next_action": docs_gate.ITER010_MINIMUM_WEB_ACTION_ID,
                "next_action_case_id": docs_gate.ITER010_MINIMUM_WEB_CASE_ID,
            },
            "",
        )
        fallback_pass_result, fallback_pass_evidence = transition_receipt(
            docs_gate.ITER010_FALLBACK_QUALITY_ACTION_ID,
            "PASS",
        )
        minimum_web_verification = verification_for(
            {
                **{str(case_id): "PASS" for case_id in freeze_produced},
                quality_case: "PASS",
                docs_gate.ITER010_FALLBACK_REFREEZE_CASE_ID: "PASS",
            }
        )
        fallback_route_results = {
            docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: preferred_invalid_result,
            docs_gate.ITER010_FALLBACK_QUALITY_RESULT_REF: fallback_pass_result,
        }
        fallback_route_evidence = {
            docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: preferred_invalid_evidence,
            docs_gate.ITER010_FALLBACK_QUALITY_RESULT_REF: fallback_pass_evidence,
        }
        self.assertEqual(
            validate(
                minimum_web_candidate,
                current_doc=minimum_web_current,
                matrix=minimum_web_verification,
                result_docs=fallback_route_results,
                evidence_docs=fallback_route_evidence,
            ),
            [],
        )
        preferred_pass_result, preferred_pass_evidence = transition_receipt(
            docs_gate.ITER010_PREFERRED_QUALITY_ACTION_ID,
            "PASS",
        )
        duplicate_quality_pass_errors = validate(
            minimum_web_candidate,
            current_doc=minimum_web_current,
            matrix=minimum_web_verification,
            result_docs={
                docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: preferred_pass_result,
                docs_gate.ITER010_FALLBACK_QUALITY_RESULT_REF: fallback_pass_result,
            },
            evidence_docs={
                docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: preferred_pass_evidence,
                docs_gate.ITER010_FALLBACK_QUALITY_RESULT_REF: fallback_pass_evidence,
            },
        )
        self.assertTrue(
            any(
                "may have at most one PASS Result" in error
                for error in duplicate_quality_pass_errors
            ),
            duplicate_quality_pass_errors,
        )

        freeze_rework_candidate = copy.deepcopy(manifest)
        freeze_rework_control = freeze_rework_candidate["plan_execution_control"]
        assert isinstance(freeze_rework_control, dict)
        freeze_rework_control["current_action"] = action_payload(
            docs_gate.ITER010_DIRECTION_FREEZE_REWORK_ACTION_ID,
            registered=False,
        )
        freeze_rework_control["transition"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_DIRECTION_FREEZE_REWORK_ACTION_ID][
                "transition"
            ]
        )
        freeze_rework_control["locks"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_DIRECTION_FREEZE_REWORK_ACTION_ID][
                "locks"
            ]
        )
        freeze_rework_alignment = freeze_rework_candidate[
            "product_goal_alignment"
        ]
        assert isinstance(freeze_rework_alignment, dict)
        freeze_rework_alignment["mature_source_agent_identity_digest"] = (
            "sha256:" + "d" * 64
        )
        freeze_rework_blocking = freeze_rework_alignment["blocking_case_ids"]
        assert isinstance(freeze_rework_blocking, list)
        self.assertIn(
            docs_gate.ITER010_DIRECTION_FREEZE_REWORK_CASE_ID,
            freeze_rework_blocking,
        )
        freeze_rework_current = docs_gate.Document(
            current.path,
            {
                **current.metadata,
                "next_action": docs_gate.ITER010_DIRECTION_FREEZE_REWORK_ACTION_ID,
                "next_action_case_id": docs_gate.ITER010_DIRECTION_FREEZE_REWORK_CASE_ID,
            },
            "",
        )
        freeze_rework_verification = verification_for(
            {
                str(freeze_produced[0]): "FAIL",
                **{
                    str(case_id): "PASS"
                    for case_id in freeze_produced[1:]
                },
            }
        )
        self.assertEqual(
            validate(
                freeze_rework_candidate,
                current_doc=freeze_rework_current,
                matrix=freeze_rework_verification,
                result_docs={
                    docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: failed_freeze_result
                },
                evidence_docs={
                    docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: (
                        failed_freeze_evidence
                    )
                },
            ),
            [],
        )
        invalid_freeze_result, invalid_freeze_evidence = transition_receipt(
            docs_gate.ITER010_CURRENT_ACTION_ID,
            "INVALID",
        )
        self.assertTrue(
            any(
                "plan_gate_verdict must equal FAIL" in error
                for error in validate(
                    freeze_rework_candidate,
                    current_doc=freeze_rework_current,
                    matrix=freeze_rework_verification,
                    result_docs={
                        docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: invalid_freeze_result
                    },
                    evidence_docs={
                        docs_gate.ITER010_CURRENT_ACTION_RESULT_REF: (
                            invalid_freeze_evidence
                        )
                    },
                )
            )
        )

        direction_rework_candidate = copy.deepcopy(quality_candidate)
        direction_rework_control = direction_rework_candidate[
            "plan_execution_control"
        ]
        assert isinstance(direction_rework_control, dict)
        direction_rework_control["current_action"] = action_payload(
            docs_gate.ITER010_DIRECTION_REWORK_ACTION_ID,
            registered=False,
        )
        direction_rework_control["transition"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_DIRECTION_REWORK_ACTION_ID]["transition"]
        )
        direction_rework_control["locks"] = copy.deepcopy(
            action_specs[docs_gate.ITER010_DIRECTION_REWORK_ACTION_ID]["locks"]
        )
        direction_rework_gate = direction_rework_candidate["direction_quality_gate"]
        assert isinstance(direction_rework_gate, dict)
        direction_rework_gate["status"] = "failed-rework-attribution-authorized"
        direction_rework_alignment = direction_rework_candidate[
            "product_goal_alignment"
        ]
        assert isinstance(direction_rework_alignment, dict)
        direction_rework_blocking = direction_rework_alignment["blocking_case_ids"]
        assert isinstance(direction_rework_blocking, list)
        self.assertIn(
            docs_gate.ITER010_DIRECTION_REWORK_CASE_ID,
            direction_rework_blocking,
        )
        direction_rework_current = docs_gate.Document(
            current.path,
            {
                **current.metadata,
                "next_action": docs_gate.ITER010_DIRECTION_REWORK_ACTION_ID,
                "next_action_case_id": docs_gate.ITER010_DIRECTION_REWORK_CASE_ID,
            },
            "",
        )
        direction_rework_verification = verification_for(
            {
                **{str(case_id): "PASS" for case_id in freeze_produced},
                quality_case: "FAIL",
            }
        )
        quality_failure_result, quality_failure_evidence = transition_receipt(
            docs_gate.ITER010_PREFERRED_QUALITY_ACTION_ID,
            "FAIL",
        )
        self.assertEqual(
            validate(
                direction_rework_candidate,
                current_doc=direction_rework_current,
                matrix=direction_rework_verification,
                result_docs={
                    docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: quality_failure_result
                },
                evidence_docs={
                    docs_gate.ITER010_PREFERRED_QUALITY_RESULT_REF: (
                        quality_failure_evidence
                    )
                },
            ),
            [],
        )

        missing_case = copy.deepcopy(manifest)
        missing_case["product_goal_alignment"]["blocking_case_ids"].remove(  # type: ignore[index]
            quality_case
        )
        self.assertTrue(any(quality_case in error for error in validate(missing_case)))

        stale_current = docs_gate.Document(
            current.path,
            {**current.metadata, "next_action": "ITER-010-ACTION-WEB-CANARY-001"},
            "",
        )
        self.assertTrue(any("next_action" in error for error in validate(current_doc=stale_current)))

        stale_order = copy.deepcopy(manifest)
        stale_order["experience_delivery_policy"] = {
            "direction_discovery_principle_ref": docs_gate.ITER010_DIRECTION_DISCOVERY_PRINCIPLE_REF,
            "micro_checkpoint_count": 4,
            "micro_checkpoint_order": (
                "machine-receipt,web-canary,three-arm-comparison,user-decision"
            ),
            "pdr004_schedule_fields_are_legacy_validator_compatibility_only": True,
            "checkpoint_miss_action": docs_gate.ITER010_DIRECTION_CHECKPOINT_MISS_ACTION,
        }
        order_errors = docs_gate.validate_iter010_direction_checkpoint_policy(
            stale_order, "manifest.yaml"
        )
        self.assertTrue(any("micro_checkpoint_order" in error for error in order_errors))

    def test_iter010_pending_codex_identity_is_owned_only_by_freeze_action(self) -> None:
        alignment = {
            "mature_source_agent_identity_digest": docs_gate.ITER010_PENDING_CODEX_IDENTITY,
            "mature_source_agent_role": docs_gate.STRICT_CODEX_BASELINE_ROLE,
            "mature_source_agent_execution_mode": docs_gate.STRICT_CODEX_BASELINE_EXECUTION_MODE,
            "positive_value_metric": docs_gate.STRICT_CODEX_QUALITY_METRIC,
            "positive_value_unit": docs_gate.STRICT_CODEX_QUALITY_UNIT,
            "positive_value_comparison": docs_gate.STRICT_CODEX_QUALITY_COMPARISON,
            "positive_value_threshold": 1,
            "held_out_evaluation_owner": "independent-evaluator",
            "positive_value_adjudication_owner": "independent-evaluator",
            "secondary_metrics_can_compensate_answer_quality": False,
        }
        self.assertEqual(
            docs_gate.validate_strict_codex_baseline_alignment(
                alignment,
                "manifest.yaml",
                allow_pending_identity=True,
            ),
            [],
        )
        errors = docs_gate.validate_strict_codex_baseline_alignment(
            alignment,
            "manifest.yaml",
        )
        self.assertTrue(any("exact sha256" in error for error in errors), errors)

    COMMIT = "a" * 40

    def validate(self, content: str, iteration: str = "ITER-002") -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.yaml"
            path.write_text(content, encoding="utf-8")
            return docs_gate.validate_active_manifest(path, iteration)

    def test_manifest_reads_only_exact_nested_fields(self) -> None:
        errors = self.validate(
            f"""iteration:
  id: WRONG
  status: proposed
evidence:
  id: ITER-002
  status: authorized
  commit: {self.COMMIT}
"""
        )

        self.assertTrue(any("iteration.id" in error for error in errors))
        self.assertTrue(any("iteration.status" in error for error in errors))
        self.assertTrue(any("baseline must be a mapping" in error for error in errors))

    def test_manifest_rejects_duplicate_mapping_keys(self) -> None:
        errors = self.validate(
            f"""iteration:
  id: ITER-002
  id: WRONG
  status: authorized
baseline:
  commit: {self.COMMIT}
"""
        )

        self.assertTrue(any("duplicate key 'id'" in error for error in errors))

    def test_manifest_accepts_the_documented_safe_subset(self) -> None:
        errors = self.validate(
            f"""schema_version: 1
iteration:
  id: ITER-002
  status: in-progress
baseline:
  commit: {self.COMMIT}
  dirty_worktree_allowed: false
system_inputs:
  ids:
    - SYS-CONTRACT-EXAMPLE
external_inputs: []
"""
        )

        self.assertEqual(errors, [])

    def test_manifest_rejects_placeholders_inside_scalar_sequences(self) -> None:
        errors = self.validate(
            f"""iteration:
  id: ITER-002
  status: authorized
baseline:
  commit: {self.COMMIT}
system_inputs:
  ids:
    - ITER-NNN
"""
        )

        self.assertTrue(any("template placeholders" in error for error in errors))

    def test_manifest_rejects_indented_root_or_inconsistent_siblings(self) -> None:
        for content in (
            f"""  iteration:
    id: ITER-002
    status: authorized
  baseline:
    commit: {self.COMMIT}
""",
            f"""iteration:
  id: ITER-002
    status: authorized
baseline:
  commit: {self.COMMIT}
""",
        ):
            with self.subTest(content=content):
                errors = self.validate(content)
                self.assertTrue(any("indentation" in error for error in errors), errors)

    def test_product_goal_alignment_manifest_is_required_from_iteration_007(self) -> None:
        without_alignment = f"""iteration:
  id: ITER-007
  status: authorized
baseline:
  commit: {self.COMMIT}
"""

        errors = self.validate(without_alignment, "ITER-007")

        self.assertTrue(any("product_goal_alignment" in error for error in errors))
        self.assertEqual(self.validate(without_alignment.replace("ITER-007", "ITER-006"), "ITER-006"), [])

    def test_product_goal_alignment_manifest_requires_resolved_nonempty_fields(self) -> None:
        valid = f"""iteration:
  id: ITER-007
  status: authorized
baseline:
  commit: {self.COMMIT}
product_goal_alignment:
  target_ref: SYS-PRODUCT-SUCCESS
  capability_path_ref: ROADMAP-M-002
  capability_path_step: step-1-general-source-qa
  predecessor_result_refs:
    - ITER-006-RESULT-ACCEPTANCE
  end_of_iteration_web_capability: free-source-questions-from-prebuilt-world-model
  next_blocking_gap: real-project-breadth
  baseline_gap: general-source-qa-not-supported
  accepted_capability_refs:
    - maven-structure
  new_capability_slice_refs:
    - semantic-source-model
  held_out_free_question_delta: two-new-supported-cross-domain-questions
  held_out_evaluation_owner: independent-evaluator
  implementation_question_visibility: hidden
  implementation_project_identity_and_source_visibility: hidden-until-product-code-freeze
  evaluation_project_manifest_digest: sha256:{'1' * 64}
  held_out_suite_digest: sha256:{'2' * 64}
  baseline_result_digest: sha256:{'3' * 64}
  mature_source_agent_protocol_digest: sha256:{'4' * 64}
  authorized_software_sources_digest: sha256:{'5' * 64}
  held_out_question_count: 10
  held_out_answerable_question_count: 8
  held_out_boundary_question_count: 2
  held_out_answerable_without_symbol_count_minimum: 4
  held_out_answerable_without_symbol_per_project_minimum: 2
  held_out_baseline_supported_count: 2
  held_out_target_supported_count: 8
  supported_count_denominator: answerable-only
  boundary_gap_counted_as_supported: false
  cross_domain_cases:
    - V-XD-001
  blocking_case_ids:
    - V-XD-001
    - V-WEB-001
    - V-ADHOC-001
  cross_domain_case_count: 1
  cross_domain_bindings:
    binding_001:
      case_id: V-XD-001
      accepted_capability_ref: maven-structure
      new_slice_ref: semantic-source-model
  first_product_web_checkpoint: V-WEB-001
  web_checkpoint_binding:
    case_id: V-WEB-001
    new_slice_ref: semantic-source-model
    executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_checkpoint: V-ADHOC-001
  live_ad_hoc_checkpoint_binding:
    case_id: V-ADHOC-001
    new_slice_ref: semantic-source-model
    executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_count: 2
  live_ad_hoc_without_symbol_count_minimum: 1
  stop_or_redirect_conditions:
    - no-held-out-quality-delta
"""
        self.assertEqual(self.validate(valid, "ITER-007"), [])

        duplicated_cross_domain = valid.replace(
            "  cross_domain_cases:\n    - V-XD-001\n",
            "  cross_domain_cases:\n    - V-XD-001\n    - V-XD-001\n",
        ).replace("  cross_domain_case_count: 1", "  cross_domain_case_count: 2")
        duplicated_cross_domain_errors = self.validate(
            duplicated_cross_domain, "ITER-007"
        )
        self.assertTrue(
            any(
                "cross_domain_cases must not contain duplicate items" in error
                for error in duplicated_cross_domain_errors
            ),
            duplicated_cross_domain_errors,
        )

        user_held_live = valid.replace(
            "  held_out_free_question_delta:",
            "  evaluation_input_mode: user-held-live-after-product-code-freeze\n"
            "  held_out_free_question_delta:",
        ).replace(
            "held_out_evaluation_owner: independent-evaluator",
            "held_out_evaluation_owner: user",
        )
        for field in docs_gate.PRODUCT_GOAL_ALIGNMENT_MANIFEST_DIGESTS:
            user_held_live = re.sub(
                rf"({field}: )sha256:[0-9a-f]{{64}}",
                rf"\1{docs_gate.USER_HELD_LIVE_UNDISCLOSED}",
                user_held_live,
            )
        user_held_live = user_held_live.replace(
            "held_out_baseline_supported_count: 2",
            "held_out_baseline_supported_count: measured-after-product-code-freeze",
        ).replace(
            "held_out_target_supported_count: 8",
            "held_out_target_supported_count: measured-after-product-code-freeze",
        )
        self.assertEqual(self.validate(user_held_live, "ITER-007"), [])
        wrong_live_owner = user_held_live.replace(
            "held_out_evaluation_owner: user",
            "held_out_evaluation_owner: independent-evaluator",
        )
        self.assertTrue(
            any(
                "user-held live evaluation" in error
                for error in self.validate(wrong_live_owner, "ITER-007")
            )
        )
        unknown_live_marker = user_held_live.replace(
            docs_gate.USER_HELD_LIVE_UNDISCLOSED,
            "unknown-unfrozen-input",
            1,
        )
        self.assertTrue(
            any(
                "closed user-held undisclosed marker" in error
                for error in self.validate(unknown_live_marker, "ITER-007")
            )
        )

        higher_than_minimum = (
            valid.replace("held_out_question_count: 10", "held_out_question_count: 12")
            .replace(
                "held_out_answerable_question_count: 8",
                "held_out_answerable_question_count: 10",
            )
            .replace(
                "held_out_target_supported_count: 8",
                "held_out_target_supported_count: 9",
            )
        )
        self.assertEqual(self.validate(higher_than_minimum, "ITER-007"), [])
        target_above_answerable = higher_than_minimum.replace(
            "held_out_target_supported_count: 9",
            "held_out_target_supported_count: 11",
        )
        self.assertTrue(
            any(
                "held-out target must be above baseline" in error
                for error in self.validate(target_above_answerable, "ITER-007")
            )
        )

        invalid_cases = (
            (
                valid.replace("target_ref: SYS-PRODUCT-SUCCESS", "target_ref: WRONG"),
                "target_ref",
            ),
            (
                valid.replace(
                    "baseline_gap: general-source-qa-not-supported",
                    "baseline_gap: pending",
                ),
                "baseline_gap",
            ),
            (
                valid.replace(
                    "capability_path_step: step-1-general-source-qa",
                    "capability_path_step: pending",
                ),
                "capability_path_step",
            ),
            (
                valid.replace(
                    "predecessor_result_refs:\n    - ITER-006-RESULT-ACCEPTANCE",
                    "predecessor_result_refs: []",
                ),
                "predecessor_result_refs",
            ),
            (
                valid.replace(
                    "implementation_question_visibility: hidden",
                    "implementation_question_visibility: visible",
                ),
                "implementation_question_visibility",
            ),
            (
                valid.replace(
                    "accepted_capability_refs:\n    - maven-structure",
                    "accepted_capability_refs: []",
                ),
                "accepted_capability_refs",
            ),
            (
                valid.replace(
                    "new_capability_slice_refs:\n    - semantic-source-model",
                    "new_capability_slice_refs: []",
                ),
                "new_capability_slice_refs",
            ),
            (
                valid.replace(
                    "cross_domain_cases:\n    - V-XD-001",
                    "cross_domain_cases: []",
                ),
                "cross_domain_cases",
            ),
            (
                valid.replace(
                    "accepted_capability_ref: maven-structure",
                    "accepted_capability_ref: isolated-view",
                ),
                "cross_domain_bindings",
            ),
            (
                valid.replace(
                    "stop_or_redirect_conditions:\n    - no-held-out-quality-delta",
                    "stop_or_redirect_conditions: []",
                ),
                "stop_or_redirect_conditions",
            ),
            (
                valid.replace(
                    "accepted_capability_refs:\n    - maven-structure",
                    "accepted_capability_refs:\n    bogus:\n      - maven-structure",
                ),
                "accepted_capability_refs",
            ),
            (
                valid.replace("    - maven-structure", '    - ""'),
                "accepted_capability_refs",
            ),
            (
                valid.replace(
                    "held_out_evaluation_owner: independent-evaluator",
                    "held_out_evaluation_owner: developer",
                ),
                "held_out_evaluation_owner",
            ),
            (
                valid.replace(
                    "held_out_target_supported_count: 8",
                    "held_out_target_supported_count: 2",
                ),
                "held-out target",
            ),
            (
                valid.replace(
                    "live_ad_hoc_question_count: 2",
                    "live_ad_hoc_question_count: 0",
                ),
                "live_ad_hoc_question_count",
            ),
            (
                valid.replace(
                    "live_ad_hoc_question_checkpoint: V-ADHOC-001",
                    "live_ad_hoc_question_checkpoint: none",
                ),
                "live_ad_hoc_question_checkpoint",
            ),
        )
        for invalid, field in invalid_cases:
            with self.subTest(field=field, invalid=invalid):
                errors = self.validate(invalid, "ITER-007")
                self.assertTrue(any(field in error for error in errors), errors)

    def test_product_goal_alignment_documents_require_target_and_v000(self) -> None:
        proposal = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-007/proposal.md",
            {"kind": "iteration-proposal", "depends_on": []},
            "# Proposal\n",
        )
        verification = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-007/verification-matrix.md",
            {"kind": "iteration-verification"},
            "# Verification\n",
        )

        errors = docs_gate.validate_product_goal_alignment_documents(
            proposal, verification, "ITER-007"
        )

        self.assertTrue(any("SYS-PRODUCT-SUCCESS" in error for error in errors))
        self.assertTrue(any("V-000" in error for error in errors))
        proposal.metadata["depends_on"] = ["SYS-PRODUCT-SUCCESS"]
        verification = product_goal_verification(
            verification.path,
        )
        self.assertEqual(
            docs_gate.validate_product_goal_alignment_documents(
                proposal, verification, "ITER-007"
            ),
            [],
        )
        self.assertEqual(
            docs_gate.validate_product_goal_alignment_documents(
                proposal, docs_gate.Document(verification.path, verification.metadata, ""), "ITER-006"
            ),
            [],
        )

    def test_verification_template_carries_the_exact_v000_contract(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/governance/templates/verification-matrix.md"
        )
        document, parse_errors = docs_gate.parse_document(path)
        self.assertEqual(parse_errors, [])
        assert document is not None
        metadata = {**document.metadata, "iteration": "ITER-012"}
        verification = docs_gate.Document(path, metadata, document.body)
        self.assertEqual(
            docs_gate.validate_product_goal_v000(verification, "ITER-012"), []
        )

    def test_iter010_v000_uses_strict_codex_quality_contract(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/verification-matrix.md"
        )
        metadata = {
            "id": "ITER-010-VERIFICATION",
            "kind": "iteration-verification",
            "status": "not-run",
            "iteration": "ITER-010",
            **docs_gate.PRODUCT_GOAL_V000_METADATA,
            "product_goal_result_id": "not-executed",
        }
        body = (
            "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| V-000 | {docs_gate.STRICT_CODEX_PRODUCT_GOAL_V000_CLAIM} | "
            f"{docs_gate.PRODUCT_GOAL_V000_LEVEL} | "
            f"{docs_gate.STRICT_CODEX_PRODUCT_GOAL_V000_FROZEN_INPUT} | "
            f"{docs_gate.STRICT_CODEX_PRODUCT_GOAL_V000_EXPECTED} | "
            "not-executed | NOT-RUN / blocking |\n"
        )
        verification = docs_gate.Document(path, metadata, body)
        self.assertEqual(
            docs_gate.validate_product_goal_v000(verification, "ITER-010"), []
        )

        stale_source_off = docs_gate.Document(
            path,
            {**metadata, **docs_gate.ENGINEERING_QA_PRODUCT_GOAL_V000_METADATA},
            body.replace(
                docs_gate.STRICT_CODEX_PRODUCT_GOAL_V000_CLAIM,
                docs_gate.ENGINEERING_QA_PRODUCT_GOAL_V000_CLAIM,
            ),
        )
        errors = docs_gate.validate_product_goal_v000(
            stale_source_off, "ITER-010"
        )
        self.assertTrue(any("product_goal_outcome" in error for error in errors), errors)

    def test_iter012_v000_uses_strict_codex_quality_contract(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-012/verification-matrix.md"
        )
        metadata, claim, frozen_input, expected = docs_gate.product_goal_v000_contract(
            "ITER-012"
        )
        verification = docs_gate.Document(
            path,
            {
                "id": "ITER-012-VERIFICATION",
                "kind": "iteration-verification",
                "status": "not-run",
                "iteration": "ITER-012",
                **metadata,
                "product_goal_result_id": "not-executed",
            },
            "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| V-000 | {claim} | {docs_gate.PRODUCT_GOAL_V000_LEVEL} | "
            f"{frozen_input} | {expected} | not-executed | NOT-RUN / blocking |\n",
        )
        self.assertEqual(
            docs_gate.validate_product_goal_v000(verification, "ITER-012"), []
        )
        self.assertTrue(docs_gate.requires_strict_codex_baseline("ITER-010"))
        self.assertFalse(docs_gate.requires_strict_codex_baseline("ITER-011"))
        self.assertTrue(docs_gate.requires_strict_codex_baseline("ITER-012"))

        stale = docs_gate.Document(
            path,
            verification.metadata,
            verification.body.replace(
                docs_gate.STRICT_CODEX_PRODUCT_GOAL_V000_EXPECTED,
                docs_gate.PRODUCT_GOAL_V000_EXPECTED,
            ),
        )
        errors = docs_gate.validate_product_goal_v000(stale, "ITER-012")
        self.assertTrue(any("expected" in error for error in errors), errors)

    def test_experience_first_delivery_policy_is_strict_and_iter010_can_opt_in(
        self,
    ) -> None:
        new_refs = ["ITER-012-SLICE-001", "ITER-012-SLICE-002"]
        blocking = [
            "V-ALPHA-ACCESS-001",
            "V-TIMEBOX-001",
            "V-COMP-ALPHA-001",
            "V-PREVIEW-001",
        ]
        alignment: dict[str, object] = {
            "earliest_web_micro_checkpoint": "V-ALPHA-ACCESS-001",
            "direction_preview_checkpoint": "V-PREVIEW-001",
            "direction_preview_binding": {
                "case_id": "V-PREVIEW-001",
                "web_case_id": "V-EXPERIENCE-001",
                "new_slice_ref": new_refs[0],
                "real_product_entry": "loopback-product-owned-engineering-qa-web",
                "representative_task_count": 3,
                "status_label": "non-acceptance-non-production",
                "decision_owner": "user",
                "allowed_decisions": "CONTINUE,REWORK,REDIRECT,REJECT",
                "hardening_requires_continue": True,
            },
            "experience_version_binding": {"new_slice_ref": new_refs[0]},
        }
        policy: dict[str, object] = {
            "schema": docs_gate.EXPERIENCE_FIRST_DELIVERY_SCHEMA,
            "owner_slice_ref": new_refs[0],
            "historical_pre_policy_result_refs": [],
            "historical_results_do_not_satisfy_experience_gate": True,
            "access_case_id": "V-ALPHA-ACCESS-001",
            "first_user_handoff_case_id": "V-ALPHA-ACCESS-001",
            "timebox_case_id": "V-TIMEBOX-001",
            "quality_case_id": "V-COMP-ALPHA-001",
            "direction_confirmation_case_id": "V-PREVIEW-001",
            "start_event": "first-product-code-change-after-slice-authorization",
            "page_launchable_deadline_minutes": 60,
            "sustained_user_operable_alpha_deadline_minutes": 180,
            "hard_stop_deadline_minutes": 240,
            "hard_stop_action": docs_gate.EXPERIENCE_FIRST_DELIVERY_HARD_STOP_ACTION,
            "access_gate_scope": "user-operable-web-and-request-path-only",
            "provider_readiness_blocks_first_user_handoff": False,
            "quality_gate_scope": "user-visible-answer-quality-only",
            "access_pass_cannot_satisfy_quality_gate": True,
            "availability_requires_quality_pass": False,
            "hardening_requires_quality_pass": True,
            "user_handoff_required_at_each_checkpoint": True,
            "checkpoint_completion_requires_runnable_user_visible_artifact": True,
            "plan_test_or_document_completion_counts_as_user_visible_increment": False,
            "pre_first_experience_allowed_checks": docs_gate.EXPERIENCE_FIRST_DELIVERY_PRE_ACCESS_WORK,
            "pre_first_experience_qualification_limit": 1,
            "pre_first_experience_smoke_question_limit": 1,
            "pre_first_experience_full_regression_allowed": False,
            "live_attempt_unit": docs_gate.EXPERIENCE_FIRST_DELIVERY_LIVE_ATTEMPT_UNIT,
            "same_failure_signature_retry_limit": 1,
            "consecutive_no_user_visible_increment_limit": 2,
            "no_increment_action": docs_gate.EXPERIENCE_FIRST_DELIVERY_NO_INCREMENT_ACTION,
            "failure_diagnosis_order": docs_gate.EXPERIENCE_FIRST_FAILURE_DIAGNOSIS_ORDER,
            "earliest_divergence_required": True,
            "falsifiable_root_cause_hypothesis_required_before_prompt_schema_or_contract_change": True,
            "local_minimal_reproduction_required_before_live_retry": True,
            "unseen_adjacent_local_case_count": 2,
            "live_canary_question_count_after_local_pass": 1,
            "same_failure_signature_fix_limit_before_architecture_responsibility_review": 1,
            "same_failure_signature_recurrence_action": "stop-rule-accumulation-and-review-architecture-responsibilities",
            "pre_first_experience_test_scope": "targeted-impact-startup-and-safety-only",
            "full_regression_before_alpha_continue_allowed": False,
            "full_regression_allowed_stages": "alpha-continue-hardening-and-before-formal-acceptance",
        }
        manifest = {"experience_delivery_policy": policy}

        self.assertFalse(
            docs_gate.requires_experience_first_delivery_policy("ITER-010")
        )
        self.assertTrue(
            docs_gate.requires_experience_first_delivery_policy("ITER-012")
        )
        self.assertEqual(
            docs_gate.validate_experience_first_delivery_policy(
                manifest,
                alignment,
                new_refs,
                blocking,
                "manifest.yaml",
                required=False,
            ),
            [],
        )
        self.assertTrue(
            any(
                "is required" in error
                for error in docs_gate.validate_experience_first_delivery_policy(
                    {},
                    alignment,
                    new_refs,
                    blocking,
                    "manifest.yaml",
                    required=True,
                )
            )
        )
        self.assertEqual(
            docs_gate.validate_experience_first_delivery_policy(
                {},
                alignment,
                new_refs,
                blocking,
                "manifest.yaml",
                required=False,
            ),
            [],
        )

        invalid_changes = (
            ("first_user_handoff_case_id", "V-TIMEBOX-001"),
            ("direction_confirmation_case_id", "V-COMP-ALPHA-001"),
            ("page_launchable_deadline_minutes", 61),
            ("sustained_user_operable_alpha_deadline_minutes", 181),
            ("hard_stop_deadline_minutes", 241),
            ("provider_readiness_blocks_first_user_handoff", True),
            ("access_pass_cannot_satisfy_quality_gate", False),
            ("availability_requires_quality_pass", True),
            ("hardening_requires_quality_pass", False),
            ("user_handoff_required_at_each_checkpoint", False),
            ("checkpoint_completion_requires_runnable_user_visible_artifact", False),
            ("plan_test_or_document_completion_counts_as_user_visible_increment", True),
            ("pre_first_experience_qualification_limit", 2),
            ("pre_first_experience_smoke_question_limit", 2),
            ("pre_first_experience_full_regression_allowed", True),
            ("same_failure_signature_retry_limit", 2),
            ("consecutive_no_user_visible_increment_limit", 3),
            ("earliest_divergence_required", False),
            (
                "falsifiable_root_cause_hypothesis_required_before_prompt_schema_or_contract_change",
                False,
            ),
            ("unseen_adjacent_local_case_count", 1),
            ("live_canary_question_count_after_local_pass", 2),
            (
                "same_failure_signature_fix_limit_before_architecture_responsibility_review",
                2,
            ),
            ("full_regression_before_alpha_continue_allowed", True),
            ("historical_results_do_not_satisfy_experience_gate", False),
        )
        for field, invalid_value in invalid_changes:
            with self.subTest(field=field):
                invalid_manifest = copy.deepcopy(manifest)
                invalid_manifest["experience_delivery_policy"][field] = invalid_value
                errors = docs_gate.validate_experience_first_delivery_policy(
                    invalid_manifest,
                    alignment,
                    new_refs,
                    blocking,
                    "manifest.yaml",
                    required=True,
                )
                self.assertTrue(any(field in error for error in errors), errors)

        aliased_cases = copy.deepcopy(manifest)
        aliased_cases["experience_delivery_policy"]["quality_case_id"] = (
            "V-ALPHA-ACCESS-001"
        )
        aliased_errors = docs_gate.validate_experience_first_delivery_policy(
            aliased_cases,
            alignment,
            new_refs,
            blocking,
            "manifest.yaml",
            required=True,
        )
        self.assertTrue(any("must be distinct" in error for error in aliased_errors))

        late_access_alignment = copy.deepcopy(alignment)
        late_access_alignment["earliest_web_micro_checkpoint"] = "V-TIMEBOX-001"
        late_access_errors = docs_gate.validate_experience_first_delivery_policy(
            manifest,
            late_access_alignment,
            new_refs,
            blocking,
            "manifest.yaml",
            required=True,
        )
        self.assertTrue(
            any("earliest_web_micro_checkpoint" in error for error in late_access_errors),
            late_access_errors,
        )

        mismatched_direction = copy.deepcopy(manifest)
        mismatched_direction["experience_delivery_policy"][
            "direction_confirmation_case_id"
        ] = "V-PREVIEW-002"
        direction_errors = docs_gate.validate_experience_first_delivery_policy(
            mismatched_direction,
            alignment,
            new_refs,
            [*blocking, "V-PREVIEW-002"],
            "manifest.yaml",
            required=True,
        )
        self.assertTrue(
            any("direction_preview_checkpoint" in error for error in direction_errors),
            direction_errors,
        )

    def test_provider_route_policy_accepts_arbitrary_configured_identities_and_keeps_actions_transparent(
        self,
    ) -> None:
        policy = generic_provider_route_policy()
        manifest = {
            "provider_route_policy": policy,
            "execution_profile_configurations": {
                "schema": docs_gate.EXECUTION_PROFILE_CONFIGURATION_SCHEMA,
                "preferred": {
                    "execution_profile_ref": "runtime-config:preferred-qualified-profile",
                    "provider_identity": "AURORA",
                    "model_identity": "nebula-x1",
                },
                "fallback": {
                    "execution_profile_ref": "runtime-config:fallback-qualified-profile",
                    "provider_identity": "BOREALIS",
                    "model_identity": "quasar-y2",
                    "admission_policy_plugin_ref": "fallback_admission_policy",
                },
            },
            "fallback_admission_policy": {
                "schema": "ROUTE_ADMISSION_POLICY_PLUGIN@1",
                "route_role": "fallback",
            },
        }
        self.assertFalse(docs_gate.requires_provider_route_policy("ITER-010"))
        self.assertTrue(docs_gate.requires_provider_route_policy("ITER-012"))
        self.assertEqual(
            docs_gate.validate_provider_route_policy(
                manifest, "manifest.yaml", required=False
            ),
            [],
        )
        _, configured_identities, configured_plugin, configuration_errors = (
            docs_gate._configured_execution_profiles(manifest, "manifest.yaml")
        )
        self.assertEqual(configuration_errors, [])
        self.assertEqual(
            configured_identities,
            ("aurora", "nebula-x1", "borealis", "quasar-y2"),
        )
        self.assertEqual(
            configured_plugin,
            manifest["fallback_admission_policy"],
        )
        self.assertTrue(
            any(
                "is required" in error
                for error in docs_gate.validate_provider_route_policy(
                    {}, "manifest.yaml", required=True
                )
            )
        )
        self.assertEqual(
            docs_gate.validate_provider_route_policy(
                {}, "manifest.yaml", required=False
            ),
            [],
        )

        mismatched_profile_configuration = copy.deepcopy(manifest)
        mismatched_profile_configuration["execution_profile_configurations"][  # type: ignore[index]
            "preferred"
        ]["execution_profile_ref"] = "runtime-config:untrusted-profile"  # type: ignore[index]
        profile_configuration_errors = docs_gate.validate_provider_route_policy(
            mismatched_profile_configuration,
            "manifest.yaml",
            required=True,
        )
        self.assertTrue(
            any(
                "execution_profile_configurations.preferred.execution_profile_ref"
                in error
                and "preferred_execution_profile_ref" in error
                for error in profile_configuration_errors
            ),
            profile_configuration_errors,
        )

        provider_specific_policy_key = copy.deepcopy(manifest)
        provider_specific_policy_key["provider_route_policy"][  # type: ignore[index]
            "borealis_schedule"
        ] = "embedded-in-generic-policy"
        provider_specific_key_errors = docs_gate.validate_provider_route_policy(
            provider_specific_policy_key,
            "manifest.yaml",
            required=True,
        )
        self.assertTrue(
            any(
                "provider_route_policy must remain generic" in error
                and "borealis" in error
                for error in provider_specific_key_errors
            ),
            provider_specific_key_errors,
        )

        transparent_action_graph = {
            **copy.deepcopy(manifest),
            "plan_execution_control": {
                "plan_revision_ref": docs_gate.ITER010_PLAN_REVISION_REF,
                "current_action": {
                    "id": "ITER-010-ACTION-DIRECTION-QUALITY-PREFERRED-001",
                    "kind": "four-arm-direction-quality-gate",
                }
            },
            "direction_quality_gate": {
                "preferred_quality_action_id": (
                    "ITER-010-ACTION-DIRECTION-QUALITY-PREFERRED-001"
                ),
                "fallback_quality_action_id": (
                    "ITER-010-ACTION-DIRECTION-QUALITY-FALLBACK-001"
                ),
            },
        }
        self.assertEqual(
            docs_gate.validate_model_transparent_plan_routing(
                transparent_action_graph, "manifest.yaml"
            ),
            [],
        )
        leaked_action_identity = copy.deepcopy(transparent_action_graph)
        leaked_action_identity["plan_execution_control"]["current_action"][  # type: ignore[index]
            "id"
        ] = "ITER-010-ACTION-AURORA-QUALITY-001"
        action_leak_errors = docs_gate.validate_model_transparent_plan_routing(
            leaked_action_identity, "manifest.yaml"
        )
        self.assertTrue(
            any(
                "plan_execution_control" in error and "aurora" in error
                for error in action_leak_errors
            ),
            action_leak_errors,
        )
        leaked_gate_identity = copy.deepcopy(transparent_action_graph)
        leaked_gate_identity["direction_quality_gate"][  # type: ignore[index]
            "preferred_terminal_unavailable_action"
        ] = "dispatch-to-BOREALIS"
        gate_leak_errors = docs_gate.validate_model_transparent_plan_routing(
            leaked_gate_identity, "manifest.yaml"
        )
        self.assertTrue(
            any(
                "direction_quality_gate" in error and "borealis" in error
                for error in gate_leak_errors
            ),
            gate_leak_errors,
        )
        leaked_model_identity = copy.deepcopy(transparent_action_graph)
        leaked_model_identity["direction_quality_gate"][  # type: ignore[index]
            "fallback_invalid_action"
        ] = "fail-closed-at-quasar-y2"
        model_leak_errors = docs_gate.validate_model_transparent_plan_routing(
            leaked_model_identity, "manifest.yaml"
        )
        self.assertTrue(
            any(
                "direction_quality_gate" in error and "quasar-y2" in error
                for error in model_leak_errors
            ),
            model_leak_errors,
        )

        self.assertEqual(
            docs_gate.validate_model_transparent_governance_templates(
                transparent_action_graph, "manifest.yaml"
            ),
            [],
        )
        with tempfile.TemporaryDirectory() as directory:
            leaked_template = Path(directory) / "manifest.yaml"
            leaked_template.write_text(
                "current_action: dispatch-to-nebula-x1\n",
                encoding="utf-8",
            )
            template_errors = (
                docs_gate.validate_model_transparent_governance_templates(
                    transparent_action_graph,
                    "manifest.yaml",
                    template_paths=[leaked_template],
                )
            )
        self.assertTrue(
            any(
                "reusable governance template" in error
                and "nebula-x1" in error
                for error in template_errors
            ),
            template_errors,
        )

        invalid_changes = (
            ("preference_order", ["BOREALIS", "AURORA"]),
            ("implementation_gap_counts_as_preferred_unavailable", True),
            ("required_fallback_verdict", "MODEL_REVIEW_REJECTED"),
            ("structured_output_invalid_allows_fallback", True),
            ("model_review_rejected_allows_fallback", True),
            (
                "raw_http_or_outcome_without_availability_verdict_allows_fallback",
                True,
            ),
            ("transparent_logical_interaction_fallback_allowed", False),
            ("fallback_attempt_inputs", "immutable-original-question-and-exact-cognition-context"),
            ("user_resubmission_or_new_session_required", True),
            ("fallback_attempt_restarts_full_chain", False),
            ("cross_attempt_intermediate_state_reuse_allowed", True),
            ("late_preferred_result_overwrite_allowed", True),
            ("maximum_fallback_execution_profile_attempts", 2),
            ("transport_request_retry_allowed", True),
            ("application_source_security_failure_allows_fallback", True),
            ("capability_failure_must_not_be_misclassified_as_unavailable", False),
            ("cost_can_reduce_answer_quality", True),
            ("current_started_interaction_unit_must_keep_full_quality_chain", False),
        )
        for field, invalid_value in invalid_changes:
            with self.subTest(field=field):
                invalid_manifest = copy.deepcopy(manifest)
                invalid_manifest["provider_route_policy"][field] = invalid_value
                errors = docs_gate.validate_provider_route_policy(
                    invalid_manifest, "manifest.yaml", required=True
                )
                self.assertTrue(any(field in error for error in errors), errors)

        invalid_outcomes = copy.deepcopy(manifest)
        invalid_outcomes["provider_route_policy"]["fallback_eligible_outcomes"] = [
            "provider-unavailable",
            "application-failure",
        ]
        outcome_errors = docs_gate.validate_provider_route_policy(
            invalid_outcomes, "manifest.yaml", required=True
        )
        self.assertTrue(
            any("fallback_eligible_outcomes" in error for error in outcome_errors),
            outcome_errors,
        )
        legacy = copy.deepcopy(manifest)
        legacy["provider_route_policy"]["request_level_failover_allowed"] = False
        legacy_errors = docs_gate.validate_provider_route_policy(
            legacy, "manifest.yaml", required=True
        )
        self.assertTrue(
            any("closed generic fields" in error for error in legacy_errors),
            legacy_errors,
        )

        for outcome in (
            "STRUCTURED_OUTPUT_INVALID",
            "MODEL_REVIEW_REJECTED",
            "PROVIDER_HTTP_ERROR",
            "PROVIDER_OUTCOME_UNKNOWN",
        ):
            with self.subTest(branch_outcome=outcome):
                branch = copy.deepcopy(transparent_action_graph)
                branch["direction_quality_gate"][  # type: ignore[index]
                    "fallback_branch_input"
                ] = outcome
                branch_errors = docs_gate.validate_model_transparent_plan_routing(
                    branch, "manifest.yaml"
                )
                self.assertTrue(
                    any("must not branch fallback" in error for error in branch_errors),
                    branch_errors,
                )
    def test_iter012_manifest_requires_experience_and_provider_policies(self) -> None:
        manifest: dict[str, object] = {"product_goal_alignment": {}}
        errors = docs_gate.validate_product_goal_alignment_manifest(
            manifest,
            "product_goal_alignment:\n",
            "manifest.yaml",
            "ITER-012",
        )
        self.assertTrue(
            any("experience_delivery_policy is required" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("provider_route_policy is required" in error for error in errors),
            errors,
        )

    def test_experience_delivery_result_audits_timebox_and_provider_attempts(
        self,
    ) -> None:
        experience_policy = {
            "schema": docs_gate.EXPERIENCE_FIRST_DELIVERY_SCHEMA,
            "access_case_id": "V-ALPHA-ACCESS-001",
            "timebox_case_id": "V-TIMEBOX-001",
            "quality_case_id": "V-COMP-ALPHA-001",
        }
        provider_policy = {"schema": docs_gate.PROVIDER_ROUTE_POLICY_SCHEMA}
        metadata: dict[str, object] = {
            "experience_delivery_policy_schema": docs_gate.EXPERIENCE_FIRST_DELIVERY_SCHEMA,
            "experience_delivery_access_case_id": "V-ALPHA-ACCESS-001",
            "experience_delivery_timebox_case_id": "V-TIMEBOX-001",
            "experience_delivery_quality_case_id": "V-COMP-ALPHA-001",
            "experience_delivery_verdict": "PASS",
            "experience_access_gate_verdict": "PASS",
            "experience_quality_gate_verdict": "PASS",
            "experience_timebox_started_at": "2026-08-25T01:00:00Z",
            "experience_elapsed_minutes_at_result_seal": 170,
            "page_launchable_elapsed_minutes": 45,
            "sustained_user_operable_alpha_elapsed_minutes": 150,
            "experience_hard_stop_triggered": False,
            "pre_first_experience_qualification_count": 1,
            "pre_first_experience_smoke_question_count": 1,
            "pre_first_experience_full_regression_count": 0,
            "live_attempt_count": 2,
            "same_failure_signature_maximum_retry_count": 1,
            "maximum_consecutive_no_user_visible_increment_count": 1,
            "external_dispatch_after_required_stop_count": 0,
            "started_question_quality_chain_truncation_count": 0,
            "provider_route_policy_schema": docs_gate.PROVIDER_ROUTE_POLICY_SCHEMA,
            "provider_route_report_digest": "sha256:" + "a" * 64,
            "fallback_provider_attempt_count": 1,
            "same_provider_retry_count": 0,
            "cross_attempt_intermediate_artifact_reuse_count": 0,
            "user_resubmission_or_new_session_count": 0,
            "late_primary_result_overwrite_count": 0,
            "capability_failure_misclassified_as_unavailable_count": 0,
            "application_source_security_failure_fallback_count": 0,
        }
        result = docs_gate.Document(SCRIPT, metadata, "# Result\n")
        self.assertEqual(
            docs_gate.validate_experience_delivery_result(
                result,
                experience_policy,
                provider_policy,
                require_success=True,
            ),
            [],
        )

        late_alpha = docs_gate.Document(
            SCRIPT,
            {
                **metadata,
                "experience_delivery_verdict": "FAIL",
                "experience_quality_gate_verdict": "FAIL",
                "experience_elapsed_minutes_at_result_seal": 210,
                "sustained_user_operable_alpha_elapsed_minutes": 200,
            },
            "# Result\n",
        )
        self.assertEqual(
            docs_gate.validate_experience_delivery_result(
                late_alpha,
                experience_policy,
                provider_policy,
                require_success=False,
            ),
            [],
        )

        invalid = docs_gate.Document(
            SCRIPT,
            {
                **metadata,
                "sustained_user_operable_alpha_elapsed_minutes": 181,
                "same_provider_retry_count": 1,
                "cross_attempt_intermediate_artifact_reuse_count": 1,
                "experience_quality_gate_verdict": "FAIL",
            },
            "# Result\n",
        )
        invalid_errors = docs_gate.validate_experience_delivery_result(
            invalid,
            experience_policy,
            provider_policy,
            require_success=True,
        )
        for expected in (
            "within 180 minutes",
            "experience_quality_gate_verdict",
            "same_provider_retry_count",
            "cross_attempt_intermediate_artifact_reuse_count",
        ):
            self.assertTrue(
                any(expected in error for error in invalid_errors), invalid_errors
            )

        iter010_policy = {
            **experience_policy,
            "direction_discovery_principle_ref": docs_gate.ITER010_DIRECTION_DISCOVERY_PRINCIPLE_REF,
            "direction_alpha_prefix_turn_count": 3,
            "direction_evidence_handoff_deadline_minutes": 360,
            "direction_decision_deadline_minutes": 480,
            "direction_confirmation_case_id": "V-PREVIEW-002",
        }
        iter010_metadata = {
            **metadata,
            "iteration": "ITER-010",
            "experience_elapsed_minutes_at_result_seal": 430,
            "experience_checkpoint_handoff_count": 4,
            "experience_checkpoint_handoff_report_digest": "sha256:" + "b" * 64,
            "completed_live_canary_turn_count": 5,
            "direction_evidence_handoff_elapsed_minutes": 320,
            "direction_decision_elapsed_minutes": 430,
            "reflection_gate_case_id": "V-PREVIEW-002",
            "reflection_gate_status": "PASS",
            "reflection_decision": "CONTINUE",
            "reflection_decision_owner": "user",
            "reflection_decision_ref": "codex-user-message:sha256:" + "c" * 64,
        }
        iter010_result = docs_gate.Document(
            SCRIPT, iter010_metadata, "# Result\n"
        )
        self.assertEqual(
            docs_gate.validate_experience_delivery_result(
                iter010_result,
                iter010_policy,
                provider_policy,
                require_success=True,
            ),
            [],
        )

        stopped_after_prefix = docs_gate.Document(
            SCRIPT,
            {
                **iter010_metadata,
                "experience_delivery_verdict": "FAIL",
                "experience_quality_gate_verdict": "FAIL",
                "experience_elapsed_minutes_at_result_seal": 170,
                "experience_checkpoint_handoff_count": 2,
                "completed_live_canary_turn_count": 3,
                "direction_evidence_handoff_elapsed_minutes": "NOT_ACHIEVED",
                "direction_decision_elapsed_minutes": "NOT_ACHIEVED",
                "reflection_gate_status": "PASS",
                "reflection_decision": "REWORK",
            },
            "# Result\n",
        )
        self.assertEqual(
            docs_gate.validate_experience_delivery_result(
                stopped_after_prefix,
                iter010_policy,
                provider_policy,
                require_success=False,
            ),
            [],
        )

        incomplete_continue = docs_gate.Document(
            SCRIPT,
            {
                **stopped_after_prefix.metadata,
                "experience_quality_gate_verdict": "PASS",
                "reflection_gate_status": "PASS",
                "reflection_decision": "CONTINUE",
            },
            "# Result\n",
        )
        incomplete_errors = docs_gate.validate_experience_delivery_result(
            incomplete_continue,
            iter010_policy,
            provider_policy,
            require_success=False,
        )
        self.assertTrue(
            any("cannot claim PASS or CONTINUE" in error for error in incomplete_errors),
            incomplete_errors,
        )
        self.assertTrue(
            any("cannot claim delivery or quality PASS" in error for error in incomplete_errors),
            incomplete_errors,
        )

        late_alpha_follow_on = docs_gate.Document(
            SCRIPT,
            {
                **stopped_after_prefix.metadata,
                "experience_elapsed_minutes_at_result_seal": 330,
                "sustained_user_operable_alpha_elapsed_minutes": 200,
                "experience_checkpoint_handoff_count": 3,
                "completed_live_canary_turn_count": 5,
                "direction_evidence_handoff_elapsed_minutes": 320,
            },
            "# Result\n",
        )
        late_alpha_errors = docs_gate.validate_experience_delivery_result(
            late_alpha_follow_on,
            iter010_policy,
            provider_policy,
            require_success=False,
        )
        self.assertTrue(
            any("missing or late direction Alpha" in error for error in late_alpha_errors),
            late_alpha_errors,
        )

        late_alpha_without_stop = docs_gate.Document(
            SCRIPT,
            {
                **stopped_after_prefix.metadata,
                "experience_elapsed_minutes_at_result_seal": 240,
                "sustained_user_operable_alpha_elapsed_minutes": 200,
                "experience_hard_stop_triggered": False,
            },
            "# Result\n",
        )
        hard_stop_errors = docs_gate.validate_experience_delivery_result(
            late_alpha_without_stop,
            iter010_policy,
            provider_policy,
            require_success=False,
        )
        self.assertTrue(
            any("absolute stop at 240 minutes" in error for error in hard_stop_errors),
            hard_stop_errors,
        )

        late_evidence_follow_on = docs_gate.Document(
            SCRIPT,
            {
                **iter010_metadata,
                "experience_delivery_verdict": "FAIL",
                "experience_quality_gate_verdict": "FAIL",
                "direction_evidence_handoff_elapsed_minutes": 361,
                "reflection_gate_status": "PASS",
                "reflection_decision": "REWORK",
            },
            "# Result\n",
        )
        late_evidence_errors = docs_gate.validate_experience_delivery_result(
            late_evidence_follow_on,
            iter010_policy,
            provider_policy,
            require_success=False,
        )
        self.assertTrue(
            any("late direction evidence" in error for error in late_evidence_errors),
            late_evidence_errors,
        )

        for field, value in (
            ("experience_checkpoint_handoff_count", 3),
            ("experience_checkpoint_handoff_report_digest", "pending"),
            ("completed_live_canary_turn_count", 4),
            ("direction_evidence_handoff_elapsed_minutes", 361),
            ("direction_decision_elapsed_minutes", 481),
            ("reflection_decision", "REWORK"),
            ("reflection_decision_ref", "pending"),
        ):
            invalid_checkpoint_result = docs_gate.Document(
                SCRIPT,
                {**iter010_metadata, field: value},
                "# Result\n",
            )
            checkpoint_errors = docs_gate.validate_experience_delivery_result(
                invalid_checkpoint_result,
                iter010_policy,
                provider_policy,
                require_success=True,
            )
            self.assertTrue(
                any(field in error or "successful ITER-010 Result" in error for error in checkpoint_errors),
                (field, checkpoint_errors),
            )

    def test_iter012_codex_baseline_and_alpha_binding_are_strict(self) -> None:
        new_refs = ["ITER-012-SLICE-001", "ITER-012-SLICE-002"]
        alpha_case = "V-COMP-ALPHA-001"
        alignment: dict[str, object] = {
            "direction_preview_checkpoint": "V-PREVIEW-001",
            "direction_preview_binding": {
                "case_id": "V-PREVIEW-001",
                "web_case_id": "V-EXPERIENCE-001",
                "new_slice_ref": new_refs[0],
                "real_product_entry": "loopback-product-owned-engineering-qa-web",
                "representative_task_count": 3,
                "status_label": "non-acceptance-non-production",
                "decision_owner": "user",
                "allowed_decisions": "CONTINUE,REWORK,REDIRECT,REJECT",
                "hardening_requires_continue": True,
            },
            "experience_version_binding": {
                "new_slice_ref": new_refs[0],
            },
            "held_out_evaluation_owner": "independent-evaluator",
            "positive_value_adjudication_owner": "independent-evaluator",
            "positive_value_metric": docs_gate.STRICT_CODEX_QUALITY_METRIC,
            "positive_value_unit": docs_gate.STRICT_CODEX_QUALITY_UNIT,
            "positive_value_comparison": docs_gate.STRICT_CODEX_QUALITY_COMPARISON,
            "positive_value_threshold": 1,
            "mature_source_agent_identity_digest": "sha256:" + "1" * 64,
            "mature_source_agent_role": docs_gate.STRICT_CODEX_BASELINE_ROLE,
            "mature_source_agent_execution_mode": docs_gate.STRICT_CODEX_BASELINE_EXECUTION_MODE,
            "secondary_metrics_can_compensate_answer_quality": False,
            "alpha_agent_comparison_binding": {
                "case_id": alpha_case,
                "new_slice_ref": new_refs[0],
                "question_count": 3,
                "post_freeze_live_question_count": 1,
                "question_set_rule": "original-failure-plus-two-heterogeneous-including-post-freeze-live",
                "protocol_digest_ref": "mature_source_agent_protocol_digest",
                "rubric_digest_ref": "mature_source_agent_rubric_digest",
                "identity_digest_ref": "mature_source_agent_identity_digest",
                "pass_rule": docs_gate.STRICT_CODEX_ALPHA_PASS_RULE,
                "all_tie_outcome": "FAIL",
                "secondary_metric_compensation_allowed": False,
            },
        }
        blocking = ["V-PREVIEW-001", "V-EXPERIENCE-001", alpha_case]
        self.assertEqual(
            docs_gate.validate_strict_codex_baseline_alignment(
                alignment, "manifest.yaml"
            ),
            [],
        )
        self.assertEqual(
            docs_gate.validate_alpha_agent_comparison_binding(
                alignment, new_refs, blocking, "manifest.yaml"
            ),
            [],
        )

        invalid_cases = []
        for field, value in (
            ("held_out_evaluation_owner", "user"),
            ("positive_value_metric", "normalized-reuse-cost"),
            ("positive_value_threshold", 0),
            ("secondary_metrics_can_compensate_answer_quality", True),
        ):
            candidate = copy.deepcopy(alignment)
            candidate[field] = value
            invalid_cases.extend(
                docs_gate.validate_strict_codex_baseline_alignment(
                    candidate, "manifest.yaml"
                )
            )
        self.assertTrue(any("held_out_evaluation_owner" in error for error in invalid_cases))
        self.assertTrue(any("positive_value_metric" in error for error in invalid_cases))
        self.assertTrue(any("tie cannot pass" in error for error in invalid_cases))
        self.assertTrue(any("cannot" in error or "must be false" in error for error in invalid_cases))

        too_small = copy.deepcopy(alignment)
        too_small["alpha_agent_comparison_binding"]["question_count"] = 2
        missing_live = copy.deepcopy(alignment)
        del missing_live["alpha_agent_comparison_binding"][
            "post_freeze_live_question_count"
        ]
        excessive_live = copy.deepcopy(alignment)
        excessive_live["alpha_agent_comparison_binding"][
            "post_freeze_live_question_count"
        ] = 4
        legacy_tie_rule = copy.deepcopy(alignment)
        legacy_tie_rule["alpha_agent_comparison_binding"]["tie_outcome"] = (
            legacy_tie_rule["alpha_agent_comparison_binding"].pop(
                "all_tie_outcome"
            )
        )
        mixed_tie_rule = copy.deepcopy(alignment)
        mixed_tie_rule["alpha_agent_comparison_binding"]["tie_outcome"] = "FAIL"
        missing_all_tie_rule = copy.deepcopy(alignment)
        del missing_all_tie_rule["alpha_agent_comparison_binding"][
            "all_tie_outcome"
        ]
        wrong_slice = copy.deepcopy(alignment)
        wrong_slice["alpha_agent_comparison_binding"]["new_slice_ref"] = new_refs[1]
        aggregate_only = copy.deepcopy(alignment)
        aggregate_only["alpha_agent_comparison_binding"]["pass_rule"] = (
            "positive-blind-quality-margin-only"
        )
        self.assertTrue(
            any(
                "at least 3" in error
                for error in docs_gate.validate_alpha_agent_comparison_binding(
                    too_small, new_refs, blocking, "manifest.yaml"
                )
            )
        )
        self.assertTrue(
            any(
                "first sustained Web Alpha" in error
                for error in docs_gate.validate_alpha_agent_comparison_binding(
                    wrong_slice, new_refs, blocking, "manifest.yaml"
                )
            )
        )
        for candidate in (missing_live, excessive_live):
            self.assertTrue(
                any(
                    "post_freeze_live_question_count" in error
                    for error in docs_gate.validate_alpha_agent_comparison_binding(
                        candidate, new_refs, blocking, "manifest.yaml"
                    )
                )
            )
        for candidate in (
            legacy_tie_rule,
            mixed_tie_rule,
            missing_all_tie_rule,
        ):
            self.assertTrue(
                any(
                    "all_tie_outcome" in error
                    for error in docs_gate.validate_alpha_agent_comparison_binding(
                        candidate, new_refs, blocking, "manifest.yaml"
                    )
                )
            )
        self.assertTrue(
            any(
                "pass_rule" in error
                for error in docs_gate.validate_alpha_agent_comparison_binding(
                    aggregate_only, new_refs, blocking, "manifest.yaml"
                )
            )
        )
        self.assertTrue(
            any(
                "blocking" in error
                for error in docs_gate.validate_alpha_agent_comparison_binding(
                    alignment,
                    new_refs,
                    [item for item in blocking if item != alpha_case],
                    "manifest.yaml",
                )
            )
        )

    def test_v000_rejects_nonblocking_and_requires_pass_at_completion(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-007/verification-matrix.md"
        )
        nonblocking = product_goal_verification(
            path, evidence="result-ref", status="PASS / non-blocking"
        )
        errors = docs_gate.validate_product_goal_v000(
            nonblocking, "ITER-007", require_pass=True
        )
        self.assertTrue(any("remain blocking" in error for error in errors), errors)

        for status, evidence in (
            ("not-run / blocking", "pending"),
            ("FAIL / blocking", "result-ref"),
            ("PASS / blocking", "pending"),
            ("PASS / blocking", "none"),
        ):
            with self.subTest(status=status, evidence=evidence):
                document = product_goal_verification(
                    path, evidence=evidence, status=status
                )
                errors = docs_gate.validate_product_goal_v000(
                    document, "ITER-007", require_pass=True
                )
                self.assertTrue(errors)

        risk_only = product_goal_verification(
            path,
            evidence="risk-result",
            status="PASS / blocking",
            claim="仅关闭解析器风险，无用户可见变化",
        )
        errors = docs_gate.validate_product_goal_v000(
            risk_only, "ITER-007", require_pass=True
        )
        self.assertTrue(any("claim" in error for error in errors), errors)

        unbound = product_goal_verification(
            path,
            evidence="risk-result",
            status="PASS / blocking",
            result_id="risk-result",
        )
        errors = docs_gate.validate_product_goal_v000(
            unbound, "ITER-007", require_pass=True, by_id={}
        )
        self.assertTrue(any("same-iteration PASS" in error for error in errors), errors)

        rejected_verification = product_goal_verification(
            path,
            evidence="ITER-007-RESULT-SLICE-001-FAILED",
            status="FAIL / blocking",
            result_id="ITER-007-RESULT-SLICE-001-FAILED",
        )
        self.assertEqual(
            docs_gate.validate_product_goal_v000(
                rejected_verification,
                "ITER-007",
                require_pass=False,
                by_id={},
            ),
            [],
        )

    def test_iter012_alpha_comparison_case_must_be_owned_by_bound_slice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.yaml"
            first_ref = "ITER-012-SLICE-001"
            second_ref = "ITER-012-SLICE-002"
            alpha_case = "V-COMP-ALPHA-001"
            other_case = "V-OTHER-001"
            manifest_path.write_text(
                f"""product_goal_alignment:
  new_capability_slice_refs:
    - {first_ref}
    - {second_ref}
  blocking_case_ids:
    - {alpha_case}
    - {other_case}
  alpha_agent_comparison_binding:
    case_id: {alpha_case}
    new_slice_ref: {first_ref}
development:
  slices: {{}}
""",
                encoding="utf-8",
            )

            def slice_document(reference: str, gate_case: str) -> docs_gate.Document:
                return docs_gate.Document(
                    docs_gate.REPOSITORY
                    / f"docs/project/iterations/iteration-012/development-design/{reference}.md",
                    {
                        "id": reference,
                        "kind": "development-slice",
                        "iteration": "ITER-012",
                        "product_goal_gate": "V-000",
                        "product_goal_accepted_capability_refs": [],
                        "product_goal_cross_domain_case_ids": [],
                        "product_goal_slice_gate_case_ids": [gate_case],
                        "depends_on": ["ITER-012-PROPOSAL"],
                    },
                    "# Slice\n",
                )

            wrong_owner = {
                first_ref: slice_document(first_ref, other_case),
                second_ref: slice_document(second_ref, alpha_case),
            }
            wrong_errors = docs_gate.validate_product_goal_reference_targets(
                manifest_path,
                "ITER-012",
                wrong_owner,
            )
            self.assertTrue(
                any("Alpha Agent comparison" in error for error in wrong_errors),
                wrong_errors,
            )

            correct_owner = {
                first_ref: slice_document(first_ref, alpha_case),
                second_ref: slice_document(second_ref, other_case),
            }
            correct_errors = docs_gate.validate_product_goal_reference_targets(
                manifest_path,
                "ITER-012",
                correct_owner,
            )
            self.assertFalse(
                any("Alpha Agent comparison" in error for error in correct_errors),
                correct_errors,
            )

    def test_manifest_alignment_accepts_safe_yaml_key_whitespace(self) -> None:
        content = f"""iteration:
  id: ITER-007
  status: authorized
baseline:
  commit: {self.COMMIT}
product_goal_alignment :
  target_ref: SYS-PRODUCT-SUCCESS
  capability_path_ref: ROADMAP-M-002
  capability_path_step: step-1-general-source-qa
  predecessor_result_refs:
    - ITER-006-RESULT-ACCEPTANCE
  end_of_iteration_web_capability: free-source-questions-from-prebuilt-world-model
  next_blocking_gap: real-project-breadth
  baseline_gap: general-source-qa-not-supported
  accepted_capability_refs :
    - maven-structure
  new_capability_slice_refs:
    - semantic-source-model
  held_out_free_question_delta: two-new-supported-cross-domain-questions
  held_out_evaluation_owner: independent-evaluator
  implementation_question_visibility: hidden
  implementation_project_identity_and_source_visibility: hidden-until-product-code-freeze
  evaluation_project_manifest_digest: sha256:{'1' * 64}
  held_out_suite_digest: sha256:{'2' * 64}
  baseline_result_digest: sha256:{'3' * 64}
  mature_source_agent_protocol_digest: sha256:{'4' * 64}
  authorized_software_sources_digest: sha256:{'5' * 64}
  held_out_question_count: 10
  held_out_answerable_question_count: 8
  held_out_boundary_question_count: 2
  held_out_answerable_without_symbol_count_minimum: 4
  held_out_answerable_without_symbol_per_project_minimum: 2
  held_out_baseline_supported_count: 2
  held_out_target_supported_count: 8
  supported_count_denominator: answerable-only
  boundary_gap_counted_as_supported: false
  cross_domain_cases:
    - V-XD-001
  blocking_case_ids:
    - V-XD-001
    - V-WEB-001
    - V-ADHOC-001
  cross_domain_case_count: 1
  cross_domain_bindings:
    binding_001:
      case_id: V-XD-001
      accepted_capability_ref: maven-structure
      new_slice_ref: semantic-source-model
  first_product_web_checkpoint: V-WEB-001
  web_checkpoint_binding:
    case_id: V-WEB-001
    new_slice_ref: semantic-source-model
    executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_checkpoint: V-ADHOC-001
  live_ad_hoc_checkpoint_binding:
    case_id: V-ADHOC-001
    new_slice_ref: semantic-source-model
    executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_count: 2
  live_ad_hoc_without_symbol_count_minimum: 1
  stop_or_redirect_conditions:
    - no-held-out-quality-delta
"""
        self.assertEqual(self.validate(content, "ITER-007"), [])

    def test_product_goal_capability_refs_must_resolve_to_old_contract_and_new_slice(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            manifest = repository / "manifest.yaml"
            manifest.write_text(
                """product_goal_alignment:
  capability_path_ref: ROADMAP-M-002
  capability_path_step: step-1-test
  predecessor_result_refs:
    - SYS-CONTRACT-OLD
  accepted_capability_refs:
    - SYS-CONTRACT-OLD
  new_capability_slice_refs:
    - ITER-007-SLICE-001
  cross_domain_cases:
    - V-XD-001
  blocking_case_ids:
    - V-XD-001
    - V-WEB-001
    - V-ADHOC-001
  cross_domain_bindings:
    binding_001:
      case_id: V-XD-001
      accepted_capability_ref: SYS-CONTRACT-OLD
      new_slice_ref: ITER-007-SLICE-001
  first_product_web_checkpoint: V-WEB-001
  web_checkpoint_binding:
    case_id: V-WEB-001
    new_slice_ref: ITER-007-SLICE-001
    executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_checkpoint: V-ADHOC-001
  live_ad_hoc_checkpoint_binding:
    case_id: V-ADHOC-001
    new_slice_ref: ITER-007-SLICE-001
    executes_cross_domain_case_id: V-XD-001
""",
                encoding="utf-8",
            )
            prior_acceptance = docs_gate.Document(
                repository
                / "docs/project/iterations/iteration-006/results/acceptance.md",
                {
                    "id": "ITER-006-RESULT-ACCEPTANCE",
                    "kind": "iteration-acceptance",
                    "status": "completed",
                    "iteration": "ITER-006",
                },
                "# Acceptance\n",
            )
            capability_path = docs_gate.Document(
                repository / "docs/project/roadmap/milestones/M-002.md",
                {
                    "id": "ROADMAP-M-002",
                    "kind": "roadmap-milestone",
                    "status": "planned",
                    "authority": "planning-only",
                },
                "# Capability Path\n\n"
                "| Step ID | Capability |\n"
                "|---|---|\n"
                "| `step-1-test` | test capability |\n",
            )
            new_slice = docs_gate.Document(
                repository
                / "docs/project/iterations/iteration-007/development-design/SLICE-001.md",
                {
                    "id": "ITER-007-SLICE-001",
                    "kind": "development-slice",
                    "status": "proposed",
                    "iteration": "ITER-007",
                    "depends_on": [
                        "ITER-007-PROPOSAL",
                        "ITER-006-RESULT-ACCEPTANCE",
                    ],
                    "product_goal_gate": "V-000",
                    "product_goal_accepted_capability_refs": [
                        "ITER-006-RESULT-ACCEPTANCE"
                    ],
                    "product_goal_cross_domain_case_ids": ["V-XD-001"],
                    "product_goal_slice_gate_case_ids": [
                        "V-XD-001",
                        "V-WEB-001",
                        "V-ADHOC-001",
                    ],
                    "product_goal_web_checkpoint_id": "V-WEB-001",
                    "product_goal_live_ad_hoc_checkpoint_id": "V-ADHOC-001",
                },
                "# Slice\n",
            )
            verification = docs_gate.Document(
                repository
                / "docs/project/iterations/iteration-007/verification-matrix.md",
                {
                    "id": "ITER-007-VERIFICATION",
                    "kind": "iteration-verification",
                    "iteration": "ITER-007",
                },
                "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
                "|---|---|---|---|---|---|---|\n"
                "| V-XD-001 | combine ITER-006-RESULT-ACCEPTANCE and ITER-007-SLICE-001 | product | hidden suite | correct answer | pending | not-run / blocking |\n"
                "| V-WEB-001 | ITER-007-SLICE-001 formal Web executes V-XD-001 | product | exact UI | answer | pending | not-run / blocking |\n"
                "| V-ADHOC-001 | ITER-007-SLICE-001 live ad-hoc probes V-XD-001 | product | user question | answer | pending | not-run / blocking |\n",
            )
            by_id = {
                prior_acceptance.identifier: prior_acceptance,
                capability_path.identifier: capability_path,
                new_slice.identifier: new_slice,
            }
            manifest.write_text(
                manifest.read_text(encoding="utf-8").replace(
                    "SYS-CONTRACT-OLD", "ITER-006-RESULT-ACCEPTANCE"
                ),
                encoding="utf-8",
            )
            with patch.object(docs_gate, "REPOSITORY", repository):
                self.assertEqual(
                    docs_gate.validate_product_goal_reference_targets(
                        manifest,
                        "ITER-007",
                        by_id,
                        verification=verification,
                    ),
                    [],
                )
                manifest.write_text(
                    manifest.read_text(encoding="utf-8").replace(
                        "capability_path_step: step-1-test",
                        "capability_path_step: step-9-unknown",
                    ),
                    encoding="utf-8",
                )
                unknown_step_errors = (
                    docs_gate.validate_product_goal_reference_targets(
                        manifest,
                        "ITER-007",
                        by_id,
                        verification=verification,
                    )
                )
                self.assertTrue(
                    any("registered Step ID" in error for error in unknown_step_errors),
                    unknown_step_errors,
                )
                manifest.write_text(
                    manifest.read_text(encoding="utf-8").replace(
                        "capability_path_step: step-9-unknown",
                        "capability_path_step: step-1-test",
                    ),
                    encoding="utf-8",
                )
                rejected_prior_index = docs_gate.Document(
                    repository
                    / "docs/project/iterations/iteration-006/README.md",
                    {
                        "id": "ITER-006-INDEX",
                        "kind": "iteration-index",
                        "status": "rejected",
                        "iteration": "ITER-006",
                    },
                    "# Rejected iteration\n",
                )
                rejected_reference_errors = (
                    docs_gate.validate_product_goal_reference_targets(
                        manifest,
                        "ITER-007",
                        {
                            **by_id,
                            rejected_prior_index.identifier: rejected_prior_index,
                        },
                        verification=verification,
                    )
                )
                self.assertTrue(
                    any(
                        "earlier accepted iteration" in error
                        for error in rejected_reference_errors
                    ),
                    rejected_reference_errors,
                )
                prose_only_verification = docs_gate.Document(
                    verification.path,
                    verification.metadata,
                    verification.body.replace(
                        "combine ITER-006-RESULT-ACCEPTANCE and ITER-007-SLICE-001",
                        "the prose deliberately does not encode reference bindings",
                    ),
                )
                prose_errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    by_id,
                    verification=prose_only_verification,
                )
                self.assertEqual(prose_errors, [])
                readiness_errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    by_id,
                    require_execution_slice_sequence=True,
                    verification=verification,
                )
                self.assertTrue(
                    any("exactly one" in error for error in readiness_errors),
                    readiness_errors,
                )
                accepted_slice = docs_gate.Document(
                    new_slice.path,
                    {**new_slice.metadata, "status": "accepted"},
                    new_slice.body,
                )
                accepted_errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    {
                        prior_acceptance.identifier: prior_acceptance,
                        accepted_slice.identifier: accepted_slice,
                    },
                    require_execution_slice_sequence=True,
                    verification=verification,
                )
                self.assertTrue(
                    any("status is invalid" in error for error in accepted_errors),
                    accepted_errors,
                )
                wrong_authority_slice = docs_gate.Document(
                    new_slice.path,
                    {
                        **new_slice.metadata,
                        "status": "authorized",
                        "authority": "proposed-development",
                        "coding_input": "false",
                    },
                    new_slice.body,
                )
                authority_errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    {
                        prior_acceptance.identifier: prior_acceptance,
                        wrong_authority_slice.identifier: wrong_authority_slice,
                    },
                    require_execution_slice_sequence=True,
                    verification=verification,
                )
                self.assertTrue(
                    any("current-development" in error for error in authority_errors),
                    authority_errors,
                )
                accepted_future = docs_gate.Document(
                    repository
                    / "docs/project/iterations/iteration-008/results/acceptance.md",
                    {
                        "id": "ITER-008-RESULT-ACCEPTANCE",
                        "kind": "iteration-acceptance",
                        "status": "completed",
                        "iteration": "ITER-008",
                    },
                    "# Acceptance\n",
                )
                manifest.write_text(
                    manifest.read_text(encoding="utf-8").replace(
                        "ITER-006-RESULT-ACCEPTANCE",
                        "ITER-008-RESULT-ACCEPTANCE",
                    ),
                    encoding="utf-8",
                )
                future_errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    {**by_id, accepted_future.identifier: accepted_future},
                    verification=verification,
                )
                self.assertTrue(
                    any("earlier accepted iteration" in error for error in future_errors),
                    future_errors,
                )
                manifest.write_text(
                    manifest.read_text(encoding="utf-8").replace(
                        "ITER-008-RESULT-ACCEPTANCE", "isolated-new-view"
                    ),
                    encoding="utf-8",
                )
                errors = docs_gate.validate_product_goal_reference_targets(
                    manifest,
                    "ITER-007",
                    by_id,
                    verification=verification,
                )
        self.assertTrue(any("isolated-new-view" in error for error in errors), errors)

    def test_product_goal_readiness_requires_exact_user_authorization(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-007/readiness-review.md"
        )
        valid = docs_gate.Document(
            path,
            {
                "authorized_by": "user",
                "authorized_at": "2026-08-12T12:00:00+08:00",
                "product_goal_alignment_verdict": "accepted",
                "product_goal_alignment_reviewed_by": "user",
                "product_goal_alignment_review_ref": "codex-user-message:sha256:"
                + "a" * 64,
            },
            "# Readiness\n",
        )
        self.assertEqual(
            docs_gate.validate_product_goal_readiness_authorization(valid), []
        )
        invalid = docs_gate.Document(
            path,
            {
                **valid.metadata,
                "authorized_by": "none",
                "authorized_at": "none",
            },
            valid.body,
        )
        errors = docs_gate.validate_product_goal_readiness_authorization(invalid)
        self.assertTrue(any("authorized_by" in error for error in errors), errors)
        self.assertTrue(any("authorized_at" in error for error in errors), errors)

    def test_additional_web_checkpoint_binds_the_same_slice_cross_domain_case(self) -> None:
        sequences = {
            "accepted_capability_refs": ["ITER-006-RESULT-ACCEPTANCE"],
            "new_capability_slice_refs": [
                "ITER-007-SLICE-001",
                "ITER-007-SLICE-002",
            ],
            "cross_domain_cases": ["V-XD-001", "V-XD-002"],
        }
        alignment = {
            "first_product_web_checkpoint": "V-WEB-001",
            "live_ad_hoc_question_checkpoint": "V-ADHOC-001",
            "cross_domain_bindings": {
                "first": {
                    "case_id": "V-XD-001",
                    "accepted_capability_ref": "ITER-006-RESULT-ACCEPTANCE",
                    "new_slice_ref": "ITER-007-SLICE-001",
                },
                "second": {
                    "case_id": "V-XD-002",
                    "accepted_capability_ref": "ITER-006-RESULT-ACCEPTANCE",
                    "new_slice_ref": "ITER-007-SLICE-002",
                },
            },
            "web_checkpoint_binding": {
                "case_id": "V-WEB-001",
                "new_slice_ref": "ITER-007-SLICE-001",
                "executes_cross_domain_case_id": "V-XD-001",
            },
            "live_ad_hoc_checkpoint_binding": {
                "case_id": "V-ADHOC-001",
                "new_slice_ref": "ITER-007-SLICE-002",
                "executes_cross_domain_case_id": "V-XD-002",
            },
            "additional_web_checkpoint_bindings": {
                "hardening": {
                    "case_id": "V-WEB-002",
                    "new_slice_ref": "ITER-007-SLICE-002",
                    "executes_cross_domain_case_id": "V-XD-002",
                }
            },
        }
        self.assertEqual(
            docs_gate.validate_product_goal_structured_bindings(
                alignment, sequences, "manifest.yaml"
            ),
            [],
        )
        alignment["additional_web_checkpoint_bindings"]["hardening"][  # type: ignore[index]
            "executes_cross_domain_case_id"
        ] = "V-XD-001"
        errors = docs_gate.validate_product_goal_structured_bindings(
            alignment, sequences, "manifest.yaml"
        )
        self.assertTrue(any("same slice" in error for error in errors), errors)
        alignment["additional_web_checkpoint_bindings"]["hardening"][  # type: ignore[index]
            "case_id"
        ] = "V-WEB-X"
        errors = docs_gate.validate_product_goal_structured_bindings(
            alignment, sequences, "manifest.yaml"
        )
        self.assertTrue(any("unique V-WEB" in error for error in errors), errors)


class ProductGoalSliceSequenceTests(unittest.TestCase):
    def slice_document(
        self,
        ordinal: int,
        status: str,
        *,
        depends_on_previous: bool = True,
    ) -> docs_gate.Document:
        identifier = f"ITER-007-SLICE-{ordinal:03d}"
        if status in docs_gate.ACTIVE_SLICE_STATUSES:
            authority = "current-development"
            coding_input = True
        elif status == "completed":
            authority = "historical-development"
            coding_input = False
        elif status == "blocked":
            authority = "development-evidence"
            coding_input = False
        else:
            authority = "proposed-development"
            coding_input = False
        dependencies = ["ITER-007-PROPOSAL"]
        if ordinal > 1 and depends_on_previous:
            dependencies.append(f"ITER-007-SLICE-{ordinal - 1:03d}")
        return docs_gate.Document(
            docs_gate.REPOSITORY
            / f"docs/project/iterations/iteration-007/development-design/{identifier}.md",
            {
                "id": identifier,
                "kind": "development-slice",
                "status": status,
                "authority": authority,
                "coding_input": coding_input,
                "depends_on": dependencies,
            },
            "# Slice\n",
        )

    def validate(
        self,
        statuses: tuple[str, str, str],
        *,
        missing_dependency_at: int | None = None,
    ) -> list[str]:
        documents = [
            self.slice_document(
                index,
                status,
                depends_on_previous=index != missing_dependency_at,
            )
            for index, status in enumerate(statuses, start=1)
        ]
        refs = [document.identifier for document in documents]
        return docs_gate.validate_product_goal_slice_sequence(
            refs,
            {document.identifier: document for document in documents},
            "manifest.yaml",
        )

    def test_slice_sequence_allows_one_active_after_completed_prefix(self) -> None:
        for statuses in (
            ("authorized", "proposed", "proposed"),
            ("completed", "in-progress", "proposed"),
            ("completed", "completed", "authorized"),
        ):
            with self.subTest(statuses=statuses):
                self.assertEqual(self.validate(statuses), [])

    def test_slice_sequence_rejects_zero_multiple_or_out_of_order_active(self) -> None:
        invalid = (
            ("proposed", "proposed", "proposed"),
            ("authorized", "in-progress", "proposed"),
            ("proposed", "authorized", "proposed"),
            ("authorized", "completed", "proposed"),
        )
        for statuses in invalid:
            with self.subTest(statuses=statuses):
                self.assertTrue(self.validate(statuses))

    def test_slice_sequence_requires_direct_predecessor_dependency(self) -> None:
        errors = self.validate(
            ("completed", "authorized", "proposed"),
            missing_dependency_at=2,
        )
        self.assertTrue(any("must depend on" in error for error in errors), errors)

    def test_completed_sequence_requires_every_slice_completed(self) -> None:
        documents = [
            self.slice_document(index, "completed") for index in range(1, 4)
        ]
        refs = [document.identifier for document in documents]
        by_id = {document.identifier: document for document in documents}
        self.assertEqual(
            docs_gate.validate_product_goal_slice_sequence(
                refs, by_id, "manifest.yaml", require_completed=True
            ),
            [],
        )

        by_id[refs[-1]] = self.slice_document(3, "authorized")
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs, by_id, "manifest.yaml", require_completed=True
        )
        self.assertTrue(any("every" in error for error in errors), errors)

    def test_rejected_sequence_requires_one_preserved_blocked_slice(self) -> None:
        blocked = self.slice_document(1, "blocked")
        proposed = [
            self.slice_document(index, "proposed") for index in range(2, 4)
        ]
        for document in (blocked, *proposed):
            document.metadata["iteration"] = "ITER-007"
        freeze_digest = "sha256:" + "7" * 64
        result = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-007/results/slice-001-failed.md",
            {
                "id": "ITER-007-RESULT-SLICE-001-FAILED",
                "kind": "iteration-result",
                "status": "failed-preserved",
                "authority": "execution-evidence",
                "iteration": "ITER-007",
                "depends_on": [blocked.identifier, "ITER-007-VERIFICATION"],
                "product_code_freeze_digest": freeze_digest,
            },
            "# Failed Result\n",
        )
        slices = [blocked, *proposed]
        refs = [document.identifier for document in slices]
        by_id = {
            document.identifier: document for document in [*slices, result]
        }
        manifest = {
            "authorization": {"active_slice": "none"},
            "development": {
                "slices": {
                    blocked.identifier: {
                        "status": "blocked",
                        "coding_input": False,
                        "result": result.identifier,
                        "product_code_freeze_digest": freeze_digest,
                        "authorized_by": "user",
                        "authorized_at": "2026-08-14T10:00:00+08:00",
                        "authorization_ref": "codex-user-message:sha256:"
                        + "a" * 64,
                    },
                    **{
                        document.identifier: {
                            "status": "proposed",
                            "coding_input": False,
                            "result": "not-executed",
                            "product_code_freeze_digest": "not-executed",
                            "authorized_by": "not-authorized",
                            "authorized_at": "not-authorized",
                            "authorization_ref": "not-authorized",
                        }
                        for document in proposed
                    },
                }
            },
        }

        self.assertEqual(
            docs_gate.validate_product_goal_slice_sequence(
                refs,
                by_id,
                "manifest.yaml",
                manifest=manifest,
                require_rejected=True,
            ),
            [],
        )

        result.metadata["status"] = "accepted"
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs,
            by_id,
            "manifest.yaml",
            manifest=manifest,
            require_rejected=True,
        )
        self.assertTrue(any("failed-preserved" in error for error in errors), errors)
        result.metadata["status"] = "failed-preserved"

        result.metadata["product_code_freeze_digest"] = "sha256:" + "8" * 64
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs,
            by_id,
            "manifest.yaml",
            manifest=manifest,
            require_rejected=True,
        )
        self.assertTrue(any("exact product code freeze" in error for error in errors), errors)
        result.metadata["product_code_freeze_digest"] = freeze_digest

        authorization = manifest["authorization"]
        assert isinstance(authorization, dict)
        authorization["active_slice"] = blocked.identifier
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs,
            by_id,
            "manifest.yaml",
            manifest=manifest,
            require_rejected=True,
        )
        self.assertTrue(any("active_slice" in error for error in errors), errors)

    def test_rejected_sequence_rejects_wrong_order_or_coding_input(self) -> None:
        invalid_sequences = (
            ("proposed", "blocked", "proposed"),
            ("blocked", "completed", "proposed"),
            ("proposed", "proposed", "proposed"),
            ("blocked", "blocked", "proposed"),
        )
        for statuses in invalid_sequences:
            with self.subTest(statuses=statuses):
                documents = [
                    self.slice_document(index, status)
                    for index, status in enumerate(statuses, start=1)
                ]
                refs = [document.identifier for document in documents]
                errors = docs_gate.validate_product_goal_slice_sequence(
                    refs,
                    {
                        document.identifier: document for document in documents
                    },
                    "manifest.yaml",
                    require_rejected=True,
                )
                self.assertTrue(errors)

        blocked = self.slice_document(1, "blocked")
        blocked.metadata["coding_input"] = True
        blocked.metadata["authority"] = "current-development"
        proposed = [self.slice_document(index, "proposed") for index in range(2, 4)]
        errors = docs_gate.validate_product_goal_slice_sequence(
            [blocked.identifier, *(document.identifier for document in proposed)],
            {
                document.identifier: document
                for document in [blocked, *proposed]
            },
            "manifest.yaml",
            require_rejected=True,
        )
        self.assertTrue(any("coding_input false" in error for error in errors), errors)

    def test_completed_prefix_requires_slice_result_and_passed_web_gates(self) -> None:
        completed = self.slice_document(1, "completed")
        active = self.slice_document(2, "authorized")
        proposed = self.slice_document(3, "proposed")
        completed = docs_gate.Document(
            completed.path,
            {
                **completed.metadata,
                "iteration": "ITER-007",
                "product_goal_cross_domain_case_ids": ["V-XD-001"],
                "product_goal_web_checkpoint_id": "V-WEB-001",
                "product_goal_slice_gate_case_ids": ["V-XD-001", "V-WEB-001"],
            },
            completed.body,
        )
        for document in (active, proposed):
            document.metadata["iteration"] = "ITER-007"
        refs = [completed.identifier, active.identifier, proposed.identifier]
        by_id = {item.identifier: item for item in (completed, active, proposed)}
        manifest = {
            "authorization": {"active_slice": active.identifier},
            "development": {
                "slices": {
                    completed.identifier: {
                        "status": "completed",
                        "coding_input": False,
                        "result": "not-executed",
                        "product_code_freeze_digest": "sha256:" + "1" * 64,
                        "authorized_by": "user",
                        "authorized_at": "2026-08-13T11:00:00+08:00",
                        "authorization_ref": "codex-user-message:sha256:" + "b" * 64,
                    },
                    active.identifier: {
                        "status": "authorized",
                        "coding_input": True,
                        "result": "not-executed",
                        "product_code_freeze_digest": "not-executed",
                        "authorized_by": "user",
                        "authorized_at": "2026-08-13T12:00:00+08:00",
                        "authorization_ref": "codex-user-message:sha256:" + "a" * 64,
                    },
                    proposed.identifier: {
                        "status": "proposed",
                        "coding_input": False,
                        "result": "not-executed",
                        "product_code_freeze_digest": "not-executed",
                        "authorized_by": "not-authorized",
                        "authorized_at": "not-authorized",
                        "authorization_ref": "not-authorized",
                    },
                }
            }
        }
        verification = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-007/verification-matrix.md",
            {"id": "ITER-007-VERIFICATION", "kind": "iteration-verification"},
            "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
            "|---|---|---|---|---|---|---|\n"
            "| V-XD-001 | cumulative | product | exact | answer | pending | not-run / blocking |\n"
            "| V-WEB-001 | web | product | exact | answer | pending | not-run / blocking |\n",
        )
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs,
            by_id,
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(any("must bind accepted execution evidence" in error for error in errors), errors)

        result = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-007/results/slice-001.md",
            {
                "id": "ITER-007-RESULT-SLICE-001",
                "kind": "iteration-result",
                "status": "accepted",
                "authority": "execution-evidence",
                "iteration": "ITER-007",
                "depends_on": [completed.identifier, "ITER-007-VERIFICATION"],
                "product_code_freeze_digest": "sha256:" + "1" * 64,
            },
            "# Result\n",
        )
        by_id[result.identifier] = result
        manifest["development"]["slices"][completed.identifier]["result"] = result.identifier  # type: ignore[index]
        errors = docs_gate.validate_product_goal_slice_sequence(
            refs,
            by_id,
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(any("completed V-XD-001 must" in error for error in errors), errors)
        passed_verification = docs_gate.Document(
            verification.path,
            verification.metadata,
            verification.body
            .replace("pending | not-run / blocking", f"{result.identifier}#V-XD-001 | PASS / blocking", 1)
            .replace("pending | not-run / blocking", f"{result.identifier}#V-WEB-001 | PASS / blocking", 1),
        )
        self.assertEqual(
            docs_gate.validate_product_goal_slice_sequence(
                refs,
                by_id,
                "manifest.yaml",
                manifest=manifest,
                verification=passed_verification,
            ),
            [],
        )

    def test_execution_readiness_freezes_source_contract_frontend_and_hidden_canaries(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            iteration_directory = repository / "docs/project/iterations/iteration-007"
            system_directory = repository / "docs/system/contracts"
            system_directory.mkdir(parents=True)

            hidden_directory = (
                repository
                / "validation/structure_world_model_iteration_007"
            )
            hidden_directory.mkdir(parents=True)
            hidden_component_paths = tuple(
                hidden_directory / name
                for name in (
                    "hidden_freeze_protocol.json",
                    "hidden_freeze.py",
                    "hidden_freeze_lifecycle.py",
                )
            )
            for ordinal, path in enumerate(hidden_component_paths):
                path.write_text(f"public component {ordinal}\n", encoding="utf-8")
            hidden_protocol_digest = docs_gate.canonical_raw_component_set_digest(
                hidden_component_paths
            )

            def digest(character: str) -> str:
                return "sha256:" + character * 64

            contract_ids = [
                "SYS-CONTRACT-SEMANTICS",
                "SYS-CONTRACT-QUERY",
                "SYS-CONTRACT-ANSWER",
                "SYS-CONTRACT-UPDATE",
            ]
            contract_documents = {
                identifier: docs_gate.Document(
                    system_directory / f"{identifier.lower()}.md",
                    {
                        "id": identifier,
                        "kind": "system-contract",
                        "status": "current",
                        "authority": "normative",
                    },
                    "# Contract\n",
                )
                for identifier in contract_ids
            }
            for document in contract_documents.values():
                document.path.write_text("# Contract\n", encoding="utf-8")
            contract_set_paths = sorted(
                document.path.relative_to(repository).as_posix()
                for document in contract_documents.values()
            )
            contract_set_schema = "ITER-007-SYSTEM-CONTRACT-SET@1"
            contract_set_digest = docs_gate.canonical_fileset_digest(
                contract_set_schema,
                contract_set_paths,
                repository=repository,
            )
            readiness = docs_gate.Document(
                iteration_directory / "readiness-review.md",
                {
                    "id": "ITER-007-READINESS",
                    "kind": "iteration-readiness",
                    "depends_on": contract_ids,
                },
                "# Readiness\n",
            )
            first_slice = docs_gate.Document(
                iteration_directory / "development-design/SLICE-001.md",
                {
                    "id": "ITER-007-SLICE-001",
                    "kind": "development-slice",
                    "depends_on": ["ITER-007-PROPOSAL", readiness.identifier],
                    "product_goal_slice_gate_case_ids": ["V-CANARY-001"],
                },
                "# Slice\n",
            )
            second_slice = docs_gate.Document(
                iteration_directory / "development-design/SLICE-002.md",
                {
                    "id": "ITER-007-SLICE-002",
                    "kind": "development-slice",
                    "depends_on": [
                        "ITER-007-PROPOSAL",
                        readiness.identifier,
                        first_slice.identifier,
                    ],
                    "product_goal_slice_gate_case_ids": ["V-CANARY-002"],
                },
                "# Slice\n",
            )
            by_id = {
                **contract_documents,
                readiness.identifier: readiness,
                first_slice.identifier: first_slice,
                second_slice.identifier: second_slice,
            }
            verification = docs_gate.Document(
                iteration_directory / "verification-matrix.md",
                {"id": "ITER-007-VERIFICATION", "kind": "iteration-verification"},
                "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
                "|---|---|---|---|---|---|---|\n"
                "| V-PRE-001 | baseline | readiness | exact | accepted | baseline-result#V-PRE-001 | PASS / blocking |\n"
                "| V-UPDATE-001 | pre-question build | update | exact | built | pending | not-run / blocking |\n"
                "| V-UPDATE-002 | no-question revision | update | exact | rebuilt | pending | not-run / blocking |\n",
            )
            manifest: dict[str, object] = {
                "product_goal_alignment": {
                    "blocking_case_ids": [
                        "V-UPDATE-001",
                        "V-UPDATE-002",
                        "V-CANARY-001",
                        "V-CANARY-002",
                    ],
                    "readiness_blocking_case_ids": ["V-PRE-001"],
                    "authorized_software_sources_digest": digest("1"),
                    "visible_development_corpus_digest": digest("2"),
                    "early_hidden_canary_bindings": {
                        "slice_001": {
                            "case_id": "V-CANARY-001",
                            "new_slice_ref": "ITER-007-SLICE-001",
                            "project_manifest_digest": digest("3"),
                            "suite_digest": digest("4"),
                            "evaluation_owner": "independent-evaluator",
                            "implementation_visibility": "hidden-until-slice-code-freeze",
                            "burn_rule": (
                                "product-change-between-disclosure-and-slice-result-seal-"
                                "burns-canary-and-preserves-result"
                            ),
                        },
                        "slice_002": {
                            "case_id": "V-CANARY-002",
                            "new_slice_ref": "ITER-007-SLICE-002",
                            "project_manifest_digest": digest("5"),
                            "suite_digest": digest("6"),
                            "evaluation_owner": "independent-evaluator",
                            "implementation_visibility": "hidden-until-slice-code-freeze",
                            "burn_rule": (
                                "product-change-between-disclosure-and-slice-result-seal-"
                                "burns-canary-and-preserves-result"
                            ),
                        },
                    },
                },
                "source_scope": {
                    "provider": "LOCAL_GIT",
                    "content_kind": "java-source",
                    "contract_ref": "SYS-CONTRACT-UPDATE",
                    "authorized_software_sources_digest": digest("1"),
                    "question_or_suite_driven_update_allowed": False,
                    "verification_case_ids": ["V-UPDATE-001", "V-UPDATE-002"],
                },
                "answer_protocol": {
                    "contract_ref": "SYS-CONTRACT-ANSWER",
                    "planner_model_calls": 1,
                    "draft_model_calls": 1,
                    "independent_reviewer_model_calls": 1,
                    "deterministic_schema_grounding_and_authorization_checks": True,
                    "retries_allowed": False,
                    "exact_total_model_calls_per_question": 3,
                    "status": "frozen",
                },
                "readiness_inputs": {
                    "required_system_contract_refs": contract_ids,
                    "source_semantics_contract_ref": "SYS-CONTRACT-SEMANTICS",
                    "implementation_query_contract_ref": "SYS-CONTRACT-QUERY",
                    "no_payload_contract_ref": "SYS-CONTRACT-SEMANTICS",
                    "answer_protocol_contract_ref": "SYS-CONTRACT-ANSWER",
                    "system_contract_set_schema": contract_set_schema,
                    "system_contract_set_paths": contract_set_paths,
                    "system_contract_set_digest": contract_set_digest,
                    "java_frontend": {
                        "artifact_ref": "tree-sitter-java-offline",
                        "version": "1.2.3",
                        "runtime_version": "tree-sitter==1.2.3",
                        "grammar_version": "tree-sitter-java==1.2.3",
                        "language_abi": 14,
                        "license_ref": "MIT",
                        "runtime_license_digest": digest("7"),
                        "grammar_license_digest": digest("8"),
                        "runtime_fileset_digest": digest("9"),
                        "grammar_fileset_digest": digest("a"),
                        "offline_artifact_digest": digest("8"),
                        "canonicalization_oracle_digest": digest("9"),
                        "information_preservation_oracle_digest": digest("a"),
                        "information_boundary_oracle_digest": digest("b"),
                        "legacy_calls_consistency_oracle_digest": digest("c"),
                        "readiness_oracle_result_digest": digest("d"),
                        "readiness_oracle_result_path": (
                            "var/iteration-007/readiness/oracle-result.json"
                        ),
                    },
                    "hidden_freeze_protocol_digest": hidden_protocol_digest,
                },
            }
            new_refs = [
                "ITER-007-SLICE-001",
                "ITER-007-SLICE-002",
                "ITER-007-SLICE-003",
            ]
            with patch.object(docs_gate, "REPOSITORY", repository):
                self.assertEqual(
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    ),
                    [],
                )

                source_scope = manifest["source_scope"]
                assert isinstance(source_scope, dict)
                source_scope["question_or_suite_driven_update_allowed"] = True
                source_errors = docs_gate.validate_product_goal_execution_readiness(
                    manifest,
                    "manifest.yaml",
                    "ITER-007",
                    by_id,
                    new_refs,
                    verification,
                )
                self.assertTrue(
                    any("question_or_suite_driven" in error for error in source_errors),
                    source_errors,
                )
                source_scope["question_or_suite_driven_update_allowed"] = False

                readiness_inputs = manifest["readiness_inputs"]
                assert isinstance(readiness_inputs, dict)
                frontend = readiness_inputs["java_frontend"]
                assert isinstance(frontend, dict)
                frontend["artifact_ref"] = "pending"
                frontend_errors = docs_gate.validate_product_goal_execution_readiness(
                    manifest,
                    "manifest.yaml",
                    "ITER-007",
                    by_id,
                    new_refs,
                    verification,
                )
                self.assertTrue(
                    any("java_frontend.artifact_ref" in error for error in frontend_errors),
                    frontend_errors,
                )
                frontend["artifact_ref"] = "tree-sitter-java-offline"

                original_contract_digest = readiness_inputs[
                    "system_contract_set_digest"
                ]
                readiness_inputs["system_contract_set_digest"] = digest("f")
                contract_digest_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any(
                        "system_contract_set_digest does not match"
                        in error
                        for error in contract_digest_errors
                    ),
                    contract_digest_errors,
                )
                historical_digest_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                        verify_current_contract_fileset=False,
                    )
                )
                self.assertFalse(
                    any(
                        "system_contract_set_digest does not match" in error
                        for error in historical_digest_errors
                    ),
                    historical_digest_errors,
                )
                readiness_inputs["system_contract_set_digest"] = (
                    original_contract_digest
                )

                original_contract_paths = list(
                    readiness_inputs["system_contract_set_paths"]
                )
                readiness_inputs["system_contract_set_paths"] = list(
                    reversed(original_contract_paths)
                )
                contract_order_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any("canonical lexical order" in error for error in contract_order_errors),
                    contract_order_errors,
                )
                readiness_inputs["system_contract_set_paths"] = (
                    original_contract_paths
                )

                readiness_inputs["system_contract_set_paths"] = (
                    original_contract_paths + [original_contract_paths[-1]]
                )
                duplicate_path_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any("system_contract_set_paths must be unique" in error for error in duplicate_path_errors),
                    duplicate_path_errors,
                )

                outside_path = repository / "README.md"
                outside_path.write_text("outside system\n", encoding="utf-8")
                readiness_inputs["system_contract_set_paths"] = sorted(
                    original_contract_paths + ["README.md"]
                )
                outside_path_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any("system Contract set path is invalid" in error for error in outside_path_errors),
                    outside_path_errors,
                )

                missing_contract_paths = original_contract_paths[1:]
                readiness_inputs["system_contract_set_paths"] = (
                    missing_contract_paths
                )
                readiness_inputs["system_contract_set_digest"] = (
                    docs_gate.canonical_fileset_digest(
                        contract_set_schema,
                        missing_contract_paths,
                        repository=repository,
                    )
                )
                missing_contract_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any("required Contract is absent" in error for error in missing_contract_errors),
                    missing_contract_errors,
                )
                readiness_inputs["system_contract_set_paths"] = (
                    original_contract_paths
                )
                readiness_inputs["system_contract_set_digest"] = (
                    original_contract_digest
                )

                alignment = manifest["product_goal_alignment"]
                assert isinstance(alignment, dict)
                canaries = alignment["early_hidden_canary_bindings"]
                assert isinstance(canaries, dict)
                slice_001_canary = canaries["slice_001"]
                slice_002_canary = canaries["slice_002"]
                assert isinstance(slice_001_canary, dict)
                assert isinstance(slice_002_canary, dict)

                alignment["evaluation_input_mode"] = (
                    docs_gate.USER_HELD_LIVE_EVALUATION_MODE
                )
                alignment["held_out_evaluation_owner"] = "user"
                alignment["authorized_software_sources_digest"] = (
                    docs_gate.USER_HELD_LIVE_UNDISCLOSED
                )
                source_scope["authorized_software_sources_digest"] = (
                    docs_gate.USER_HELD_LIVE_UNDISCLOSED
                )
                for canary in (slice_001_canary, slice_002_canary):
                    canary["evaluation_owner"] = "user"
                    canary["project_manifest_digest"] = (
                        docs_gate.USER_HELD_LIVE_UNDISCLOSED
                    )
                    canary["suite_digest"] = docs_gate.USER_HELD_LIVE_UNDISCLOSED
                self.assertEqual(
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    ),
                    [],
                )
                slice_001_canary["suite_digest"] = "pending"
                live_marker_errors = (
                    docs_gate.validate_product_goal_execution_readiness(
                        manifest,
                        "manifest.yaml",
                        "ITER-007",
                        by_id,
                        new_refs,
                        verification,
                    )
                )
                self.assertTrue(
                    any(
                        "closed user-held undisclosed marker" in error
                        for error in live_marker_errors
                    ),
                    live_marker_errors,
                )
                slice_001_canary["suite_digest"] = (
                    docs_gate.USER_HELD_LIVE_UNDISCLOSED
                )
                slice_001_canary["case_id"] = "V-CANARY-002"
                slice_002_canary["case_id"] = "V-CANARY-001"
                swapped_errors = docs_gate.validate_product_goal_execution_readiness(
                    manifest,
                    "manifest.yaml",
                    "ITER-007",
                    by_id,
                    new_refs,
                    verification,
                )
                self.assertTrue(
                    any("owned by its bound Slice" in error for error in swapped_errors),
                    swapped_errors,
                )

    def test_full_three_slice_final_state_aggregates_slice_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            iteration_directory = (
                repository / "docs/project/iterations/iteration-007"
            )
            (iteration_directory / "development-design").mkdir(parents=True)
            (iteration_directory / "results").mkdir()
            manifest_path = iteration_directory / "manifest.yaml"

            slice_refs = [
                f"ITER-007-SLICE-{ordinal:03d}" for ordinal in range(1, 4)
            ]
            slice_result_refs = [
                f"ITER-007-RESULT-SLICE-{ordinal:03d}"
                for ordinal in range(1, 4)
            ]
            slice_case_ids = ["V-XD-001", "V-WEB-002", "V-ADHOC-001"]
            digest_fields = {
                "evaluation_project_manifest_digest": "sha256:" + "1" * 64,
                "held_out_suite_digest": "sha256:" + "2" * 64,
                "baseline_result_digest": "sha256:" + "3" * 64,
                "mature_source_agent_protocol_digest": "sha256:" + "4" * 64,
                "authorized_software_sources_digest": "sha256:" + "5" * 64,
            }
            manifest_path.write_text(
                f"""product_goal_alignment:
  new_capability_slice_refs:
    - {slice_refs[0]}
    - {slice_refs[1]}
    - {slice_refs[2]}
  blocking_case_ids:
    - {slice_case_ids[0]}
    - {slice_case_ids[1]}
    - {slice_case_ids[2]}
  early_hidden_canary_bindings:
    slice_001:
      case_id: {slice_case_ids[0]}
      new_slice_ref: {slice_refs[0]}
      project_manifest_digest: sha256:{'8' * 64}
      suite_digest: sha256:{'9' * 64}
    slice_002:
      case_id: {slice_case_ids[1]}
      new_slice_ref: {slice_refs[1]}
      project_manifest_digest: sha256:{'a' * 64}
      suite_digest: sha256:{'b' * 64}
  evaluation_project_manifest_digest: {digest_fields['evaluation_project_manifest_digest']}
  held_out_suite_digest: {digest_fields['held_out_suite_digest']}
  baseline_result_digest: {digest_fields['baseline_result_digest']}
  mature_source_agent_protocol_digest: {digest_fields['mature_source_agent_protocol_digest']}
  authorized_software_sources_digest: {digest_fields['authorized_software_sources_digest']}
  held_out_question_count: 3
  held_out_answerable_question_count: 3
  held_out_boundary_question_count: 0
  held_out_answerable_without_symbol_count_minimum: 1
  held_out_baseline_supported_count: 0
  held_out_target_supported_count: 3
  cross_domain_case_count: 3
  live_ad_hoc_question_count: 1
  live_ad_hoc_without_symbol_count_minimum: 1
development:
  slices:
    {slice_refs[0]}:
      status: completed
      coding_input: false
      result: {slice_result_refs[0]}
      product_code_freeze_digest: sha256:{'c' * 64}
      authorized_by: user
      authorized_at: 2026-08-13T10:00:00+08:00
      authorization_ref: codex-user-message:sha256:{'a' * 64}
    {slice_refs[1]}:
      status: completed
      coding_input: false
      result: {slice_result_refs[1]}
      product_code_freeze_digest: sha256:{'d' * 64}
      authorized_by: user
      authorized_at: 2026-08-13T11:00:00+08:00
      authorization_ref: codex-user-message:sha256:{'b' * 64}
    {slice_refs[2]}:
      status: completed
      coding_input: false
      result: {slice_result_refs[2]}
      product_code_freeze_digest: sha256:{'e' * 64}
      authorized_by: user
      authorized_at: 2026-08-13T12:00:00+08:00
      authorization_ref: codex-user-message:sha256:{'c' * 64}
authorization:
  active_slice: none
""",
                encoding="utf-8",
            )
            manifest = docs_gate.safe_load_manifest(
                manifest_path.read_text(encoding="utf-8")
            )

            verification = docs_gate.Document(
                iteration_directory / "verification-matrix.md",
                {
                    "id": "ITER-007-VERIFICATION",
                    "kind": "iteration-verification",
                },
                "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
                "|---|---|---|---|---|---|---|\n"
                + "".join(
                    f"| {case_id} | slice {ordinal} product gate | product | exact frozen input | answer | {result_ref}#{case_id} | PASS / blocking |\n"
                    for ordinal, (case_id, result_ref) in enumerate(
                        zip(slice_case_ids, slice_result_refs, strict=True), start=1
                    )
                ),
            )

            slices: list[docs_gate.Document] = []
            slice_results: list[docs_gate.Document] = []
            for index, (slice_ref, result_ref, case_id) in enumerate(
                zip(slice_refs, slice_result_refs, slice_case_ids, strict=True)
            ):
                dependencies = ["ITER-007-PROPOSAL"]
                if index > 0:
                    dependencies.append(slice_refs[index - 1])
                slice_document = docs_gate.Document(
                    iteration_directory
                    / f"development-design/{slice_ref}.md",
                    {
                        "id": slice_ref,
                        "kind": "development-slice",
                        "status": "completed",
                        "authority": "historical-development",
                        "coding_input": False,
                        "iteration": "ITER-007",
                        "depends_on": dependencies,
                        "product_goal_slice_gate_case_ids": [case_id],
                    },
                    "# Slice\n",
                )
                slice_result = docs_gate.Document(
                    iteration_directory / f"results/slice-{index + 1:03d}.md",
                    {
                        "id": result_ref,
                        "kind": "iteration-result",
                        "status": "accepted",
                        "authority": "execution-evidence",
                        "iteration": "ITER-007",
                        "depends_on": [slice_ref, verification.identifier],
                        "product_code_freeze_digest": "sha256:"
                        + "cde"[index]
                        * 64,
                        **(
                            {
                                "canary_project_manifest_digest": "sha256:"
                                + "8a"[index]
                                * 64,
                                "canary_suite_digest": "sha256:"
                                + "9b"[index]
                                * 64,
                                "canary_disclosure_receipt_digest": "sha256:"
                                + "f0"[index]
                                * 64,
                                "canary_product_change_before_result_seal_count": 0,
                                "canary_capsule_consumption_status": (
                                    "CONSUMED_AFTER_RESULT_SEAL"
                                ),
                            }
                            if index < 2
                            else {}
                        ),
                    },
                    "# Slice Result\n",
                )
                slices.append(slice_document)
                slice_results.append(slice_result)

            by_id = {
                document.identifier: document
                for document in [*slices, *slice_results]
            }
            result_metadata = {
                "id": "ITER-007-RESULT-PRODUCT-GOAL",
                "kind": "iteration-result",
                "status": "product-goal-pass",
                "authority": "execution-evidence",
                "owners": ["quality"],
                "depends_on": [
                    verification.identifier,
                    *slice_refs,
                    *slice_result_refs,
                ],
                "iteration": "ITER-007",
                **docs_gate.PRODUCT_GOAL_V000_METADATA,
                "product_goal_verdict": "PASS",
                "product_goal_subject_digest": "sha256:" + "6" * 64,
                "product_goal_report_digest": "sha256:" + "7" * 64,
                **digest_fields,
                "held_out_question_count": "3",
                "held_out_baseline_supported_count": "0",
                "held_out_actual_supported_count": "3",
                "held_out_boundary_correct_gap_count": "0",
                "held_out_answerable_without_symbol_supported_count": "1",
                "live_ad_hoc_without_symbol_pass_count": "1",
                "major_error_count": "0",
                "source_fallback_count": "0",
                "update_fallback_count": "0",
                "direct_fallback_count": "0",
                "cross_domain_pass_count": "3",
                "live_ad_hoc_pass_count": "1",
                "mature_source_agent_comparison": "non-regression",
                "product_web_manual_verification": "passed",
            }
            result_body = """# Result

## Claim and scope
three completed slices
## Exact inputs / baseline
frozen inputs
## Execution and evidence
slice-owned evidence
## Result, failures and limitations
pass
## Findings and system write-back
dispositioned
## Validity / supersession
exact subject only
"""
            result = docs_gate.Document(
                iteration_directory / "results/product-goal.md",
                result_metadata,
                result_body,
            )

            with patch.object(docs_gate, "REPOSITORY", repository):
                sequence_errors = docs_gate.validate_product_goal_slice_sequence(
                    slice_refs,
                    by_id,
                    "manifest.yaml",
                    manifest=manifest,
                    verification=verification,
                    require_completed=True,
                )
                result_errors = docs_gate.validate_product_goal_result(
                    result,
                    "ITER-007",
                    manifest_path,
                    verification,
                    by_id,
                )
                missing_dependency_result = docs_gate.Document(
                    result.path,
                    {
                        **result.metadata,
                        "depends_on": [
                            reference
                            for reference in result.metadata["depends_on"]
                            if reference != slice_result_refs[1]
                        ],
                    },
                    result.body,
                )
                missing_dependency_errors = docs_gate.validate_product_goal_result(
                    missing_dependency_result,
                    "ITER-007",
                    manifest_path,
                    verification,
                    by_id,
                )
                duplicated_manifest = docs_gate.safe_load_manifest(
                    manifest_path.read_text(encoding="utf-8")
                )
                duplicated_development = duplicated_manifest["development"]
                assert isinstance(duplicated_development, dict)
                duplicated_slices = duplicated_development["slices"]
                assert isinstance(duplicated_slices, dict)
                for slice_ref in slice_refs[1:]:
                    duplicated_slice = duplicated_slices[slice_ref]
                    assert isinstance(duplicated_slice, dict)
                    duplicated_slice["result"] = slice_result_refs[0]
                duplicate_result_errors = docs_gate.validate_product_goal_slice_sequence(
                    slice_refs,
                    by_id,
                    "manifest.yaml",
                    manifest=duplicated_manifest,
                    verification=verification,
                    require_completed=True,
                )
                changed_after_exposure = docs_gate.Document(
                    slice_results[0].path,
                    {
                        **slice_results[0].metadata,
                        "product_code_freeze_digest": "sha256:" + "0" * 64,
                    },
                    slice_results[0].body,
                )
                changed_by_id = {
                    **by_id,
                    changed_after_exposure.identifier: changed_after_exposure,
                }
                changed_after_exposure_errors = (
                    docs_gate.validate_product_goal_slice_sequence(
                        slice_refs,
                        changed_by_id,
                        "manifest.yaml",
                        manifest=manifest,
                        verification=verification,
                        require_completed=True,
                    )
                )

        self.assertEqual(sequence_errors, [])
        self.assertEqual(result_errors, [])
        self.assertTrue(
            any(
                f"must depend on {slice_result_refs[1]}" in error
                for error in missing_dependency_errors
            ),
            missing_dependency_errors,
        )
        self.assertTrue(
            any("unique Slice Result" in error for error in duplicate_result_errors),
            duplicate_result_errors,
        )
        self.assertTrue(
            any(
                "must bind its exact product code freeze" in error
                for error in changed_after_exposure_errors
            ),
            changed_after_exposure_errors,
        )


class FindingGateTests(unittest.TestCase):
    def document(
        self,
        identifier: str,
        kind: str,
        *,
        iteration: str = "",
        path: str | None = None,
        **metadata: object,
    ) -> docs_gate.Document:
        values: dict[str, object] = {
            "id": identifier,
            "kind": kind,
            "status": "current",
            "iteration": iteration,
        }
        values.update(metadata)
        document_path = docs_gate.REPOSITORY / (
            path or f"docs/project/test-fixtures/{identifier}.md"
        )
        return docs_gate.Document(document_path, values, "# Fixture\n")

    def finding(
        self,
        identifier: str,
        classification: object,
        target: object,
        *,
        status: str = "dispositioned",
        iteration: str = "ITER-002",
        disposition: object = "updated",
        **metadata: object,
    ) -> docs_gate.Document:
        code = metadata.pop("code", [])
        tests = metadata.pop("tests", [])
        return self.document(
            identifier,
            "implementation-finding",
            iteration=iteration,
            status=status,
            classification=classification,
            disposition=disposition,
            target=target,
            code=code,
            tests=tests,
            **metadata,
        )

    def fixtures(self) -> tuple[dict[str, docs_gate.Document], dict[str, docs_gate.Document]]:
        iteration = self.document("ITER-002", "iteration-index", iteration="ITER-002")
        other_iteration = self.document("ITER-003", "iteration-index", iteration="ITER-003")
        slice_document = self.document(
            "ITER-002-SLICE-001", "development-slice", iteration="ITER-002"
        )
        verification = self.document(
            "ITER-002-VERIFICATION", "iteration-verification", iteration="ITER-002"
        )
        system_contract = self.document(
            "SYS-CONTRACT-EXAMPLE",
            "system-contract",
            path="docs/system/contracts/example.md",
        )
        system_quality = self.document(
            "SYS-QUALITY-EXAMPLE",
            "system-quality",
            path="docs/system/quality/example.md",
        )
        roadmap = self.document("ROADMAP-EXAMPLE", "roadmap-candidate")
        documents = {
            document.identifier: document
            for document in (
                iteration,
                other_iteration,
                slice_document,
                verification,
                system_contract,
                system_quality,
                roadmap,
            )
        }
        return documents, {"ITER-002": iteration, "ITER-003": other_iteration}

    def test_disposition_and_target_must_be_single_scalars(self) -> None:
        by_id, indexes = self.fixtures()
        finding = self.finding(
            "FINDING-001",
            "system-contract",
            ["SYS-CONTRACT-EXAMPLE"],
            disposition=["updated"],
        )
        by_id[finding.identifier] = finding

        errors = docs_gate.validate_findings([finding], by_id, indexes)

        self.assertTrue(any("disposition must be a single scalar" in error for error in errors))
        self.assertTrue(any("target must be a single scalar" in error for error in errors))

    def test_each_classification_accepts_only_its_destination_type(self) -> None:
        by_id, indexes = self.fixtures()
        valid = [
            self.finding(
                "FINDING-LOCAL",
                "local-implementation",
                "scripts/docs.py",
                code=["scripts/docs.py"],
            ),
            self.finding("FINDING-DESIGN", "iteration-design", "ITER-002-SLICE-001"),
            self.finding("FINDING-SYSTEM", "system-contract", "SYS-CONTRACT-EXAMPLE"),
            self.finding("FINDING-VERIFY", "verification", "ITER-002-VERIFICATION"),
            self.finding("FINDING-QUALITY", "verification", "SYS-QUALITY-EXAMPLE"),
            self.finding("FINDING-ROADMAP", "roadmap", "ROADMAP-EXAMPLE"),
        ]
        by_id.update({document.identifier: document for document in valid})

        self.assertEqual(docs_gate.validate_findings(valid, by_id, indexes), [])

        wrong = self.finding("FINDING-WRONG", "system-contract", "ROADMAP-EXAMPLE")
        by_id[wrong.identifier] = wrong
        errors = docs_gate.validate_findings([wrong], by_id, indexes)
        self.assertTrue(any("non-index System document" in error for error in errors))

    def test_superseded_by_must_be_an_existing_same_iteration_finding(self) -> None:
        by_id, indexes = self.fixtures()
        replacement = self.finding(
            "FINDING-NEW", "system-contract", "pending", status="open"
        )
        cross_iteration = self.finding(
            "FINDING-OTHER",
            "system-contract",
            "pending",
            status="open",
            iteration="ITER-003",
        )
        by_id.update(
            {
                replacement.identifier: replacement,
                cross_iteration.identifier: cross_iteration,
            }
        )

        valid = self.finding(
            "FINDING-OLD",
            "system-contract",
            "pending",
            status="superseded",
            superseded_by="FINDING-NEW",
        )
        by_id[valid.identifier] = valid
        self.assertEqual(docs_gate.validate_findings([valid], by_id, indexes), [])

        for reference, expected in (
            ("FINDING-OLD", "cannot reference the finding itself"),
            ("FINDING-MISSING", "existing Finding"),
            ("FINDING-OTHER", "same iteration"),
        ):
            with self.subTest(reference=reference):
                invalid = self.finding(
                    "FINDING-OLD",
                    "system-contract",
                    "pending",
                    status="superseded",
                    superseded_by=reference,
                )
                candidate_ids = dict(by_id)
                candidate_ids[invalid.identifier] = invalid
                errors = docs_gate.validate_findings([invalid], candidate_ids, indexes)
                self.assertTrue(any(expected in error for error in errors), errors)

    def test_rejected_finding_requires_scalar_none_target(self) -> None:
        by_id, indexes = self.fixtures()
        valid = self.finding(
            "FINDING-REJECTED",
            "invalid",
            "none",
            status="rejected",
            disposition="rejected-with-evidence",
        )
        by_id[valid.identifier] = valid
        self.assertEqual(docs_gate.validate_findings([valid], by_id, indexes), [])

        invalid = self.finding(
            "FINDING-REJECTED",
            "invalid",
            ["none"],
            status="rejected",
            disposition="rejected-with-evidence",
        )
        errors = docs_gate.validate_findings([invalid], by_id, indexes)
        self.assertTrue(any("target must be a single scalar" in error for error in errors))


class PlaceholderAndAcceptanceGateTests(unittest.TestCase):
    ACCEPTANCE_BODY = """# Acceptance

## Exact subject and scope
Exact subject recorded.

## Gate results and limitations
All scoped gates recorded with limitations.

## Finding dispositions and System write-back
All findings were dispositioned.

## Verdict
Accepted for the stated scope.
"""

    def test_body_placeholder_detection_does_not_treat_rule_text_as_pending_input(self) -> None:
        self.assertFalse(
            docs_gate.has_unresolved_placeholder(
                "The field must not remain pending; compare x < y and z > q."
            )
        )
        self.assertTrue(docs_gate.has_unresolved_placeholder("Outcome: <scope>"))
        self.assertTrue(docs_gate.has_unresolved_placeholder("Iteration NNN"))

    def test_required_template_sections_must_have_content(self) -> None:
        document = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-002/proposal.md",
            {"kind": "iteration-proposal"},
            """# Proposal

## Trigger and evidence

## Outcome and users
real outcome
""",
        )

        empty = docs_gate.empty_active_required_sections(document)

        self.assertIn("Trigger and evidence", empty)
        self.assertNotIn("Outcome and users", empty)
        self.assertIn("Authorization decision", empty)

    def test_product_goal_alignment_sections_are_required_from_iteration_007(self) -> None:
        body = "# Proposal\n\n## Outcome and users\nreal outcome\n"
        iteration_006 = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-006/proposal.md",
            {"kind": "iteration-proposal", "iteration": "ITER-006"},
            body,
        )
        iteration_007 = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-007/proposal.md",
            {"kind": "iteration-proposal", "iteration": "ITER-007"},
            body,
        )

        self.assertNotIn(
            "Product-goal alignment and cumulative delta",
            docs_gate.empty_active_required_sections(iteration_006),
        )
        self.assertIn(
            "Product-goal alignment and cumulative delta",
            docs_gate.empty_active_required_sections(iteration_007),
        )

        cases = (
            ("iteration-proposal", "Product-goal alignment and cumulative delta"),
            ("iteration-readiness", "Product-goal alignment gate"),
            (
                "development-slice",
                "Product-goal contribution and cumulative integration",
            ),
        )
        for kind, section in cases:
            with self.subTest(kind=kind):
                present = docs_gate.Document(
                    docs_gate.REPOSITORY / f"docs/project/test-fixtures/{kind}.md",
                    {"kind": kind, "iteration": "ITER-007"},
                    f"# Document\n\n## {section}\nresolved evidence\n",
                )
                self.assertNotIn(
                    section, docs_gate.empty_active_required_sections(present)
                )
                missing = docs_gate.Document(
                    present.path,
                    present.metadata,
                    "# Document\n\n## Other\nresolved evidence\n",
                )
                self.assertIn(
                    section, docs_gate.empty_active_required_sections(missing)
                )

    def test_iteration_path_identity_cannot_downgrade_the_gate_version(self) -> None:
        repository = Path("/repo")
        document = docs_gate.Document(
            repository / "docs/project/iterations/iteration-007/README.md",
            {
                "id": "ITER-000-INDEX",
                "kind": "iteration-index",
                "iteration": "ITER-000",
            },
            "# Iteration\n",
        )
        with patch.object(docs_gate, "REPOSITORY", repository):
            errors = docs_gate.validate_iteration_document_identity(document)

        self.assertTrue(any("match directory ITER-007" in error for error in errors))
        self.assertTrue(any("ITER-007-INDEX" in error for error in errors))

        malformed = docs_gate.Document(
            repository / "docs/project/iterations/iteration-7/README.md",
            {
                "id": "ITER-000-INDEX",
                "kind": "iteration-index",
                "iteration": "ITER-000",
            },
            "# Iteration\n",
        )
        with patch.object(docs_gate, "REPOSITORY", repository):
            errors = docs_gate.validate_iteration_document_identity(malformed)
        self.assertTrue(any("at least three digits" in error for error in errors))

    def test_accepted_proposal_is_gated_even_before_it_becomes_current(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            proposal_path = (
                repository
                / "docs/project/iterations/iteration-007/proposal.md"
            )
            proposal = docs_gate.Document(
                proposal_path,
                {
                    "id": "ITER-007-PROPOSAL",
                    "kind": "iteration-proposal",
                    "status": "accepted",
                    "iteration": "ITER-007",
                    "depends_on": ["SYS-PRODUCT-SUCCESS"],
                },
                "# Proposal\n\n## Outcome and users\nreal outcome\n",
            )
            proposed = docs_gate.Document(
                proposal.path,
                {**proposal.metadata, "status": "proposed"},
                proposal.body,
            )
            wrong_kind = docs_gate.Document(
                proposal.path,
                {**proposal.metadata, "kind": "project-note"},
                proposal.body,
            )
            with patch.object(docs_gate, "REPOSITORY", repository):
                errors = docs_gate.validate_product_goal_alignment_state([proposal])
                proposed_errors = docs_gate.validate_product_goal_alignment_state(
                    [proposed]
                )
                wrong_kind_errors = docs_gate.validate_product_goal_alignment_state(
                    [wrong_kind]
                )

        self.assertTrue(
            any(
                "Product-goal alignment and cumulative delta" in error
                for error in errors
            ),
            errors,
        )
        self.assertEqual(proposed_errors, [])
        self.assertTrue(
            any("expected kind iteration-proposal" in error for error in wrong_kind_errors),
            wrong_kind_errors,
        )

    def test_heading_only_document_has_no_substantive_body(self) -> None:
        document = docs_gate.Document(
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-002/verification-matrix.md",
            {"kind": "iteration-verification"},
            "# Verification\n\n## Cases\n",
        )

        self.assertFalse(docs_gate.has_substantive_body(document))

    def test_completed_acceptance_rejects_pending_or_collection_critical_fields(self) -> None:
        path = docs_gate.REPOSITORY / "docs/project/iterations/iteration-002/results/acceptance.md"
        for field, value in (
            ("accepted_scope", "pending"),
            ("accepted_scope", "<scope>"),
            ("accepted_scope", ["local"]),
            ("iteration", "ITER-NNN"),
        ):
            with self.subTest(field=field, value=value):
                metadata: dict[str, object] = {
                    "id": "ITER-002-RESULT-ACCEPTANCE",
                    "kind": "iteration-acceptance",
                    "status": "completed",
                    "iteration": "ITER-002",
                    "accepted_scope": "local",
                    "subject_identity": "exact-manifest-subject",
                    "baseline_commit": "a" * 40,
                    "baseline_relation": "exact-at-run",
                    "production_activation": "not-executed",
                }
                metadata[field] = value
                document = docs_gate.Document(path, metadata, self.ACCEPTANCE_BODY)
                errors = docs_gate.validate_completed_acceptance(document)
                self.assertTrue(any(field in error for error in errors), errors)

    def test_completed_acceptance_requires_exact_baseline_and_nonempty_sections(self) -> None:
        path = docs_gate.REPOSITORY / "docs/project/iterations/iteration-002/results/acceptance.md"
        metadata = {
            "id": "ITER-002-RESULT-ACCEPTANCE",
            "kind": "iteration-acceptance",
            "status": "completed",
            "iteration": "ITER-002",
            "accepted_scope": "local",
            "subject_identity": "exact-manifest-subject",
            "baseline_commit": "not-a-commit",
            "baseline_relation": "exact-at-run",
            "production_activation": "not-executed",
        }
        body = self.ACCEPTANCE_BODY.replace(
            "All findings were dispositioned.", ""
        )
        document = docs_gate.Document(path, metadata, body)

        errors = docs_gate.validate_completed_acceptance(document)

        self.assertTrue(any("baseline_commit must be" in error for error in errors))
        self.assertTrue(
            any("Finding dispositions and System write-back" in error for error in errors)
        )

    def test_iteration_007_acceptance_requires_resolved_product_goal_delta(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-007/results/acceptance.md"
        )
        metadata = {
            "id": "ITER-007-RESULT-ACCEPTANCE",
            "kind": "iteration-acceptance",
            "status": "completed",
            "iteration": "ITER-007",
            "accepted_scope": "general-source-qa-delta",
            "subject_identity": "exact-manifest-subject",
            "baseline_commit": "a" * 40,
            "baseline_relation": "exact-at-run",
            "production_activation": "not-executed",
        }

        missing = docs_gate.Document(path, metadata, self.ACCEPTANCE_BODY)
        errors = docs_gate.validate_completed_acceptance(missing)
        self.assertTrue(any("Product-goal delta" in error for error in errors))

        unresolved_body = self.ACCEPTANCE_BODY.replace(
            "## Finding dispositions and System write-back",
            "## Product-goal delta and cumulative evidence\n<exact-evidence>\n\n"
            "## Finding dispositions and System write-back",
        )
        errors = docs_gate.validate_completed_acceptance(
            docs_gate.Document(path, metadata, unresolved_body)
        )
        self.assertTrue(any("unresolved product-goal" in error for error in errors))

        resolved_body = unresolved_body.replace(
            "<exact-evidence>", "exact evidence for Map<String, Result>"
        )
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            iteration_directory = (
                repository / "docs/project/iterations/iteration-007"
            )
            (iteration_directory / "results").mkdir(parents=True)
            digest_fields = {
                "evaluation_project_manifest_digest": "sha256:" + "1" * 64,
                "held_out_suite_digest": "sha256:" + "2" * 64,
                "baseline_result_digest": "sha256:" + "3" * 64,
                "mature_source_agent_protocol_digest": "sha256:" + "4" * 64,
                "authorized_software_sources_digest": "sha256:" + "5" * 64,
            }
            (iteration_directory / "manifest.yaml").write_text(
                f"""product_goal_alignment:
  accepted_capability_refs:
    - ITER-006-RESULT-ACCEPTANCE
  new_capability_slice_refs:
    - ITER-007-SLICE-001
  evaluation_project_manifest_digest: {digest_fields['evaluation_project_manifest_digest']}
  held_out_suite_digest: {digest_fields['held_out_suite_digest']}
  baseline_result_digest: {digest_fields['baseline_result_digest']}
  mature_source_agent_protocol_digest: {digest_fields['mature_source_agent_protocol_digest']}
  authorized_software_sources_digest: {digest_fields['authorized_software_sources_digest']}
  held_out_question_count: 10
  held_out_answerable_question_count: 8
  held_out_boundary_question_count: 2
  held_out_answerable_without_symbol_count_minimum: 4
  held_out_answerable_without_symbol_per_project_minimum: 2
  held_out_baseline_supported_count: 2
  held_out_target_supported_count: 8
  supported_count_denominator: answerable-only
  boundary_gap_counted_as_supported: false
  cross_domain_cases:
    - V-XD-001
  blocking_case_ids:
    - V-XD-001
    - V-WEB-001
    - V-WEB-002
    - V-ADHOC-001
  cross_domain_case_count: 1
  first_product_web_checkpoint: V-WEB-001
  additional_web_checkpoint_bindings:
    hardening:
      case_id: V-WEB-002
      new_slice_ref: ITER-007-SLICE-001
      executes_cross_domain_case_id: V-XD-001
  live_ad_hoc_question_checkpoint: V-ADHOC-001
  live_ad_hoc_question_count: 2
  live_ad_hoc_without_symbol_count_minimum: 1
development:
  slices:
    ITER-007-SLICE-001:
      status: completed
      coding_input: false
      result: ITER-007-RESULT-SLICE-001
""",
                encoding="utf-8",
            )
            pending_verification = product_goal_verification(
                iteration_directory / "verification-matrix.md",
                evidence="ITER-007-RESULT-PRODUCT-GOAL",
                status="PASS / blocking",
                result_id="ITER-007-RESULT-PRODUCT-GOAL",
            )
            verification = docs_gate.Document(
                pending_verification.path,
                pending_verification.metadata,
                pending_verification.body
                + "| V-XD-001 | cumulative answer | product | hidden case | correct answer | ITER-007-RESULT-SLICE-001#V-XD-001 | PASS / blocking |\n"
                + "| V-WEB-001 | formal Web answer | product | exact UI | visible answer | ITER-007-RESULT-SLICE-001#V-WEB-001 | PASS / blocking |\n"
                + "| V-WEB-002 | hardening Web answer | product | exact UI | visible answer | ITER-007-RESULT-SLICE-001#V-WEB-002 | PASS / blocking |\n"
                + "| V-ADHOC-001 | live user answer | product | user question | visible answer | ITER-007-RESULT-SLICE-001#V-ADHOC-001 | PASS / blocking |\n",
            )
            result_metadata = {
                "id": "ITER-007-RESULT-PRODUCT-GOAL",
                "kind": "iteration-result",
                "status": "product-goal-pass",
                "authority": "execution-evidence",
                "owners": ["quality"],
                "depends_on": [
                    "ITER-007-VERIFICATION",
                    "ITER-007-SLICE-001",
                    "ITER-007-RESULT-SLICE-001",
                ],
                "iteration": "ITER-007",
                "product_goal_gate": "V-000",
                "product_goal_outcome": "user-visible-general-source-qa-delta",
                "product_goal_evaluation": "independent-hidden-plus-live-ad-hoc",
                "product_goal_verdict": "PASS",
                "product_goal_subject_digest": "sha256:" + "6" * 64,
                "product_goal_report_digest": "sha256:" + "7" * 64,
                **digest_fields,
                "held_out_question_count": "10",
                "held_out_baseline_supported_count": "2",
                "held_out_actual_supported_count": "8",
                "held_out_boundary_correct_gap_count": "2",
                "held_out_answerable_without_symbol_supported_count": "4",
                "live_ad_hoc_without_symbol_pass_count": "1",
                "major_error_count": "0",
                "source_fallback_count": "0",
                "update_fallback_count": "0",
                "direct_fallback_count": "0",
                "cross_domain_pass_count": "1",
                "live_ad_hoc_pass_count": "2",
                "mature_source_agent_comparison": "non-regression",
                "product_web_manual_verification": "passed",
            }
            result_body = """# Result

## Claim and scope
product delta
## Exact inputs / baseline
exact inputs
## Execution and evidence
report digest
## Result, failures and limitations
pass and limitations
## Findings and system write-back
dispositioned
## Validity / supersession
current subject only
"""
            result = docs_gate.Document(
                iteration_directory / "results/product-goal.md",
                result_metadata,
                result_body,
            )
            slice_document = docs_gate.Document(
                iteration_directory / "development-design/SLICE-001.md",
                {
                    "id": "ITER-007-SLICE-001",
                    "kind": "development-slice",
                    "status": "completed",
                    "iteration": "ITER-007",
                    "product_goal_slice_gate_case_ids": [
                        "V-XD-001",
                        "V-WEB-001",
                        "V-WEB-002",
                        "V-ADHOC-001",
                    ],
                },
                "# Slice\n",
            )
            slice_result = docs_gate.Document(
                iteration_directory / "results/slice-001.md",
                {
                    "id": "ITER-007-RESULT-SLICE-001",
                    "kind": "iteration-result",
                    "status": "accepted",
                    "authority": "execution-evidence",
                    "iteration": "ITER-007",
                    "depends_on": ["ITER-007-SLICE-001", "ITER-007-VERIFICATION"],
                },
                "# Slice Result\n",
            )
            result_documents = {
                result.identifier: result,
                slice_document.identifier: slice_document,
                slice_result.identifier: slice_result,
            }
            acceptance_metadata = {
                **metadata,
                "subject_identity": result_metadata["product_goal_subject_digest"],
            }
            with patch.object(docs_gate, "REPOSITORY", repository):
                errors = docs_gate.validate_completed_acceptance(
                    docs_gate.Document(
                        iteration_directory / "results/acceptance.md",
                        acceptance_metadata,
                        resolved_body,
                    ),
                    verification,
                    result_documents,
                )
                invalid_result = docs_gate.Document(
                    iteration_directory / "outside-product-result.md",
                    {**result_metadata, "status": "failed"},
                    "# Result\n",
                )
                invalid_result_errors = docs_gate.validate_product_goal_result(
                    invalid_result,
                    "ITER-007",
                    iteration_directory / "manifest.yaml",
                    verification,
                    result_documents,
                )
                not_run_case_errors = docs_gate.validate_product_goal_result(
                    result,
                    "ITER-007",
                    iteration_directory / "manifest.yaml",
                    docs_gate.Document(
                        verification.path,
                        verification.metadata,
                        verification.body.replace(
                            "ITER-007-RESULT-SLICE-001#V-WEB-001 | PASS / blocking",
                            "pending | not-run / blocking",
                        ),
                    ),
                    result_documents,
                )
                wrong_case_evidence_errors = docs_gate.validate_product_goal_result(
                    result,
                    "ITER-007",
                    iteration_directory / "manifest.yaml",
                    docs_gate.Document(
                        verification.path,
                        verification.metadata,
                        verification.body.replace(
                            "ITER-007-RESULT-SLICE-001#V-ADHOC-001",
                            "ITER-007-RESULT-SLICE-001#V-XD-001",
                        ),
                    ),
                    result_documents,
                )
                not_run_additional_web_errors = docs_gate.validate_product_goal_result(
                    result,
                    "ITER-007",
                    iteration_directory / "manifest.yaml",
                    docs_gate.Document(
                        verification.path,
                        verification.metadata,
                        verification.body.replace(
                            "ITER-007-RESULT-SLICE-001#V-WEB-002 | PASS / blocking",
                            "pending | not-run / blocking",
                        ),
                    ),
                    result_documents,
                )
                overstated_count_result = docs_gate.Document(
                    result.path,
                    {
                        **result.metadata,
                        "cross_domain_pass_count": "999",
                        "live_ad_hoc_pass_count": "999",
                    },
                    result.body,
                )
                overstated_count_errors = docs_gate.validate_product_goal_result(
                    overstated_count_result,
                    "ITER-007",
                    iteration_directory / "manifest.yaml",
                    verification,
                    result_documents,
                )
        self.assertEqual(errors, [])
        self.assertTrue(
            any("results directory" in error for error in invalid_result_errors),
            invalid_result_errors,
        )
        self.assertTrue(
            any("status must be product-goal-pass" in error for error in invalid_result_errors),
            invalid_result_errors,
        )
        self.assertTrue(
            any("section is missing" in error for error in invalid_result_errors),
            invalid_result_errors,
        )
        self.assertTrue(
            any("completed V-WEB-001 must bind resolved evidence" in error for error in not_run_case_errors),
            not_run_case_errors,
        )
        self.assertTrue(
            any("completed V-WEB-001 must be PASS" in error for error in not_run_case_errors),
            not_run_case_errors,
        )
        self.assertTrue(
            any("completed V-ADHOC-001 Evidence must equal" in error for error in wrong_case_evidence_errors),
            wrong_case_evidence_errors,
        )
        self.assertTrue(
            any("completed V-WEB-002 must bind resolved evidence" in error for error in not_run_additional_web_errors),
            not_run_additional_web_errors,
        )
        self.assertTrue(
            any("completed V-WEB-002 must be PASS" in error for error in not_run_additional_web_errors),
            not_run_additional_web_errors,
        )
        self.assertTrue(
            any(
                "cross_domain_pass_count must equal the frozen Manifest count" in error
                for error in overstated_count_errors
            ),
            overstated_count_errors,
        )
        self.assertTrue(
            any(
                "live_ad_hoc_pass_count must equal the frozen Manifest count" in error
                for error in overstated_count_errors
            ),
            overstated_count_errors,
        )


class ReflectionGateTests(unittest.TestCase):
    def valid_alignment(self) -> tuple[dict[str, object], list[str], list[str]]:
        new_refs = ["ITER-008-SLICE-001", "ITER-008-SLICE-002"]
        blocking = ["V-REFLECT-001", "V-REFLECT-002", "V-NEG-EARLY-001"]
        alignment: dict[str, object] = {
            "critical_assumption_ids": ["A1", "A2"],
            "reflection_gate_bindings": {
                "slice_001": {
                    "case_id": "V-REFLECT-001",
                    "new_slice_ref": new_refs[0],
                    "assumption_ids": ["A1"],
                    "conditional_falsifier_bindings": {
                        "deferred_a2": {
                            "assumption_id": "A2",
                            "case_id": "V-NEG-EARLY-001",
                        }
                    },
                    "success_decision": "CONTINUE",
                    "decision_owner": "product-architecture-quality",
                    "required_before_next_authorization_or_acceptance": True,
                },
                "slice_002": {
                    "case_id": "V-REFLECT-002",
                    "new_slice_ref": new_refs[1],
                    "assumption_ids": ["A1", "A2"],
                    "success_decision": "ACCEPT",
                    "decision_owner": "product-architecture-quality",
                    "required_before_next_authorization_or_acceptance": True,
                },
            }
        }
        return alignment, new_refs, blocking

    def valid_engineering_qa_sections(
        self,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
        source_scope: dict[str, object] = {
            "provider": "LOCAL_GIT",
            "content_kind": (
                "exact-revision-java-source-repository-documents-build-configuration-"
                "tests-plus-prebuilt-world-model"
            ),
            "contract_ref": "SYS-CONTRACT-SOURCE-ARTIFACT",
            "question_or_suite_driven_update_allowed": False,
            "question_time_read_only_retrieval_allowed": True,
            "repository_write_allowed": False,
        }
        hybrid_evidence_path: dict[str, object] = {
            "mode": "ENGINEERING_QA",
            "strict_world_model_mode_preserved": True,
            "direct_investigation_mode_preserved": True,
            "silent_mode_fallback_allowed": False,
            "world_model_role": (
                "persistent-versioned-verifiable-updatable-external-software-cognition"
            ),
            "world_model_cognition_dimensions": (
                "context-entities-relations-behavior-constraints-state-evidence-"
                "coverage-and-unknown-boundaries"
            ),
            "world_model_is_only_manual_map_cache_or_retrieval_hints": False,
            "world_model_as_question-time-source-recall_gate_allowed": False,
            "world_model_required_as_source_retrieval_gate": False,
            "investigation_inputs": (
                "immutable-original-question-exact-world-model-cognition-and-prior-"
                "ledger-results"
            ),
            "zero-irrelevant-or-insufficient-snapshot_blocks_exact-revision-retrieval": False,
            "snapshot_source_revision_compatibility": (
                "exact-match-or-explicit-partitioned-version-comparison-otherwise-"
                "unaligned-navigation-only"
            ),
            "investigation_model_role": (
                "independent-adaptive-result-driven-read-operation-proposal"
            ),
            "investigation_model_direct_source_access": "denied",
            "source_broker_role": (
                "policy-compile-and-authorize-allowlisted-read-only-exact-revision-"
                "operations"
            ),
            "retrieval_worker_role": "isolated-execution-only",
            "retrieval_worker_sources": (
                "exact-revision-source-repository-documents-build-configuration-tests"
            ),
            "retrieval_worker_access": "read-only-allowlisted-audited",
            "source_trust": "untrusted-input",
            "live_provider_source-fragment-disclosure": (
                "separately-authorized-exact-provider-model-role-and-allowlist-only"
            ),
            "evidence_ledger": "append-only-per-question-until-seal",
            "evidence_ledger_seal_trigger": (
                "investigation-finish-or-fail-closed-stop"
            ),
            "question_evidence_package_role": (
                "sealed-two-partition-support-citation-and-boundary-audit-set-not-"
                "truth-authority"
            ),
            "package_seal_confers_truth": False,
            "sealed_package_mutation_allowed": False,
            "answer_repository_access": "denied",
            "answer_direct_source_authority": "denied",
            "reviewer_repository_access": "denied",
            "reviewer_direct_source_authority": "denied",
            "reviewer_direct_shell_network_credential_or_tool_access": "denied",
            "answer_input": (
                "immutable-original-question-question-understanding-and-sealed-"
                "question-evidence-package-only"
            ),
            "reviewer_input": (
                "immutable-original-question-question-understanding-sealed-question-"
                "evidence-package-and-draft-only"
            ),
            "reviewer_more_evidence_route": (
                "specific-verifiable-gap-through-independent-verification-"
                "investigation-application-source-broker-worker-new-ledger-revision-"
                "new-package-new-answer-new-review"
            ),
            "reviewer_verification_request_role": (
                "application-derived-versioned-gap-request-from-typed-finding-binding-"
                "checklist-claim-evidence-class-and-need"
            ),
            "reviewer_verification_returns_to_initial_investigation_model": False,
            "knowledge_persistence": (
                "asynchronous-after-delivery-through-normal-admission-and-publication"
            ),
            "status": "frozen",
        }
        answer_protocol: dict[str, object] = {
            "schema": "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3",
            "contract_ref": "SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING",
            "mode": "adaptive-cognition-guided-engineering-investigation",
            "question_understanding_required_fields": (
                "user-goal,audience,requested-abstraction-level,"
                "material-conclusion-checklist,evidence-needs,response-language-and-constraints"
            ),
            "question_understanding_model_call_upper_bound": 1,
            "investigation_model_call_upper_bound": 12,
            "max_investigation_steps_per_question": 24,
            "slice_001_reviewer_verification_investigation_upper_bound": 1,
            "max_source_broker_operations_per_question": 128,
            "max_source_files_per_question": 64,
            "max_source_bytes_per_question": 2097152,
            "max_repository_document_bytes_per_question": 1048576,
            "max_build_configuration_bytes_per_question": 524288,
            "max_test_bytes_per_question": 1048576,
            "max_world_model_result_bytes_per_question": 1048576,
            "max_sealed_evidence_package_bytes_per_question": 4194304,
            "max_support_items_per_question": 1024,
            "max_evidence_ledger_bytes_per_question": 2097152,
            "max_wall_time_milliseconds_per_question": 900000,
            "initial_answer_model_calls": 1,
            "independent_review_model_calls_per_authorizable_draft": 2,
            "final_answer_role_call_reserve": 3,
            "same_package_targeted_rewrite_upper_bound": 1,
            "answer_attempt_upper_bound": 3,
            "review_attempt_upper_bound": 4,
            "provider_output_complete-replacement_upper_bound_per_stage": 2,
            "hard_safety_model_call_upper_bound_per_question": 24,
            "upfront_complete_retrieval_plan_required": False,
            "investigation_proposal_must_consider_prior_results": True,
            "source_broker_policy_compilation_required": True,
            "evidence_ledger_append_only": True,
            "question_evidence_package_sealed_after_investigation": True,
            "finish_material_observations_required": True,
            "provider_finish_disposition_shape": (
                "single-outcome-tagged-finish-dispositions-array"
            ),
            "provider_finish_disposition_partition": (
                "one-list-covers-each-checklist-item-exactly-once"
            ),
            "provider_finish_parent-evidence-references-returned-by-provider": False,
            "provider_finish_parent-evidence-reference-derivation": (
                "trusted-stable-first-occurrence-union-of-child-observation-references"
            ),
            "material_observation_identity_application_owned": True,
            "answer_claim_material_observation_and_evidence_closure_required": True,
            "answer_material_observation_coverage_contract": (
                "exact-id-statement-kind-checklist-and-required-evidence-entry-"
                "table-before-large-role-inputs"
            ),
            "answer_rewrite_preserves_every-supported-material-observation": True,
            "reviewer_independent_package_and_draft_observation_audit_required": True,
            "sealed_package_mutation_allowed": False,
            "safety_budget_reserves_answer-comprehensive-review-and-challenge-review": True,
            "review_focus_order": (
                "comprehensive-then-evidence-boundary-challenge"
            ),
            "reviewer_evidence_boundary_challenge_projection": (
                "cited-configuration-placeholders-plus-claim-status-literals-"
                "absent-from-cited-content-plus-mentioned-same-application-types-"
                "without-mounted-implementation-plus-cited-full-content-java-entry-"
                "material-effect-scans-plus-original-question-fulfillment-scan"
            ),
            "reviewer_evidence_boundary_projection_is-semantic-verdict": False,
            "reviewer_full-content-material-effect-scan-unit": (
                "each-cited-full-content-java-entry"
            ),
            "reviewer_full-content-material-effect-categories": (
                "persistence-write,audit-write,cache-mutation,notification,"
                "external-interaction"
            ),
            "reviewer_full-content-material-effect-application-observations-projected": True,
            "reviewer_original-question-fulfillment-scan-required": True,
            "reviewer_original-question-fulfillment-dimensions": (
                "direct-user-goal,ordered-user-actions,input-output-handoffs,"
                "known-unknown-boundary,material-outcomes"
            ),
            "challenge_review_disposition_vocabulary": (
                "within-evidence-boundary,draft-exceeds-evidence-boundary,"
                "draft-omits-material-effect,draft-omits-material-requirement"
            ),
            "challenge_review_specialized-disposition-kind-match-required": True,
            "challenge_review_assessment_fields": (
                "evidence-boundary,draft-scope,disposition,finding-code-plus-"
                "material-effect-layer-and-exact-statements-for-effect-omission"
            ),
            "challenge_review_material-effect-omission-layer-vocabulary": (
                "application-package,default-draft"
            ),
            "challenge_review_material-effect-application-package-remediation": (
                "same-evidence-class-verification-and-effect-absent-from-exact-"
                "package-observations"
            ),
            "challenge_review_material-effect-default-draft-remediation": (
                "challenged-entry-rewrite-and-effect-present-in-exact-package-"
                "observations"
            ),
            "challenge_review_material-effect-layer-binding-application-verified": True,
            "challenge_review_non-passing-disposition-requires-finding-on-exact-challenged-claim": True,
            "challenge_review_shared-finding-code-requires-claim-in-every-bound-challenge": True,
            "package-material-effect-observation-omission-remediation": (
                "successor-gap-delta-with-predecessor-support-reuse"
            ),
            "verification-successor-may-reuse-predecessor-support": True,
            "configuration_placeholder_proves_concrete_runtime_value": False,
            "caller-import-or-registration-proves-unmounted-fields-validation-or-output": False,
            "quality_checklist_reduction_due_to_remaining_calls_allowed": False,
            "evidence_requirement_reduction_due_to_remaining_calls_allowed": False,
            "review_skipping_due_to_remaining_calls_allowed": False,
            "reviewer_more_evidence_requires_specific_verifiable_gap": True,
            "provider_review_returns-independent-decision-or-verification-request": False,
            "provider_review_finding-remediation-vocabulary": (
                "rewrite-with-existing-evidence,investigate-missing-evidence,"
                "reject-unrecoverable"
            ),
            "reviewer_rewrite-finding-requires-current-package-entry-ids": True,
            "reviewer_missing-evidence-finding-requires-material-checklist-class-and-need": True,
            "reviewer_action-and-verification-request-derivation": (
                "application-owned-reject-then-missing-evidence-then-rewrite-"
                "then-empty-approved"
            ),
            "reviewer_draft-only-scope-expansion-may-trigger-new-evidence-investigation": False,
            "reviewer_verification_request_requires_application_and_source_broker_revalidation": True,
            "reviewer_verification_uses_independent_fresh_context_adaptive_investigation": True,
            "reviewer_verification_returns_to_initial_investigation_model": False,
            "reviewer_verification_fixed_round_cap_after_slice_001_allowed": False,
            "reviewer_verification_creates_new_ledger_revision": True,
            "reviewer_verification_creates_new_package": True,
            "new_answer_after_new_package_required": True,
            "same_package_rewrite_requires_specific_reviewer_finding": True,
            "independent_rereview_after_any_answer_or_package_change_required": True,
            "question_or_project_keyword_symbol_class_method_fixture_or_oracle_special_routing_allowed": False,
            "resource_exhaustion_behavior": (
                "answerable-fail-boundary-limitation-only-if-independently-approved-"
                "otherwise-fail-closed"
            ),
            "deterministic_grounding_authorization_revision-allowlist-and-package-seal_checks": True,
            "provider_request_retries_allowed": False,
            "provider_switch_after_dispatch_allowed": False,
            "status": "frozen",
        }
        return source_scope, hybrid_evidence_path, answer_protocol

    def valid_engineering_qa_adaptive_gate_manifest(self) -> dict[str, object]:
        _, hybrid_evidence_path, answer_protocol = (
            self.valid_engineering_qa_sections()
        )
        proposed_fuse = (
            "must-be-presealed-positive-high-safety-bound-before-slice-002-"
            "authorization"
        )
        return {
            "product_goal_alignment": {
                "positive_value_freeze_receipt_ref": (
                    "codex-user-message:sha256:" + "1" * 64
                ),
                "direction_preview_binding": {
                    "new_slice_ref": "ITER-010-SLICE-001"
                },
            },
            "development": {
                "slices": {
                    "ITER-010-SLICE-001": {"status": "proposed"},
                    "ITER-010-SLICE-002": {"status": "proposed"},
                    "ITER-010-SLICE-003": {"status": "proposed"},
                }
            },
            "hybrid_evidence_path": hybrid_evidence_path,
            "answer_protocol": answer_protocol,
            "question_evidence_package_classes": {
                "support_and_citation": {
                    "admission": "modality-context-coverage-and-support-validated-only",
                    "affirmative_claim_support_allowed": True,
                    "claim_citation_allowed": True,
                },
                "retained_non_support": {
                    "required_entry_kinds": (
                        "boundary,audit-gap,failure,partial,conflict,unknown,"
                        "rejected-decision-and-resource-receipt"
                    ),
                    "retention": "mandatory-in-ledger-and-current-sealed-package",
                    "affirmative_claim_support_allowed": False,
                    "affirmative_claim_citation_allowed": False,
                    "labeled_boundary_or_audit_reference_allowed": True,
                },
                "single_package_identity": True,
                "seal_confers_truth": False,
                "status": "frozen",
            },
            "reviewer_verification_investigation": {
                "role": "independent-verification-investigation-llm",
                "context": "fresh-context-without-initial-investigation-answer-or-review-session-state",
                "inputs": "immutable-specific-review-gap-current-package-and-current-ledger-prefix",
                "reviewer_operation_proposal_allowed": False,
                "adaptive_multi_step_required": True,
                "prior_verification_result_must_drive_next_step": True,
                "application_source_broker_worker_route_required": True,
                "direct_source_filesystem_shell_network_credential_or_tool_access": "denied",
                "returns_to_initial_investigation_model": False,
                "creates_new_ledger_revision_package_answer_and_review": True,
                "slice_001_preview_upper_bound": 1,
                "slice_001_bound_scope": "direction-preview-only-not-a-permanent-protocol-round-cap",
                "hardening_fixed_round_upper_bound_allowed": False,
                "hardening_package_revision_fuse": proposed_fuse,
                "hardening_model_call_fuse": proposed_fuse,
                "hardening_source_broker_operation_fuse": proposed_fuse,
                "hardening_source_byte_fuse": proposed_fuse,
                "hardening_wall_time_fuse": proposed_fuse,
                "hardening_no_progress_fuse": proposed_fuse,
                "answerable_fuse_exhaustion_outcome": "fail",
                "boundary_fuse_exhaustion_outcome": "independently-reviewed-honest-limitation-or-fail",
                "hardening_protocol_status": "proposed-not-frozen-requires-new-user-receipt-before-slice-002",
                "hardening_authorization_status": "not-authorized",
                "hardening_protocol_digest": "not-authorized",
                "hardening_freeze_receipt_ref": "not-authorized",
                "status": "frozen-slice-001-preview-boundary",
            },
            "engineering_qa_ablation": {
                "status": "proposed-not-authorized",
                "authorization_required_before": "ITER-010-SLICE-002-coding-or-execution",
                "authorization_ref": "not-authorized",
                "frozen_protocol_digest": "not-authorized",
                "full_cognition_arm": {
                    "cognition_input": "full-exact-world-model-cognition-context",
                    "investigation_chain": "shared-adaptive-investigation-source-broker-worker-ledger-package-answer-review",
                },
                "locator_only_or_empty_arm": {
                    "cognition_input": "predeclared-locator-only-projection-or-canonical-empty-when-no-locator-exists",
                    "investigation_chain": "same-as-full-cognition-arm",
                },
                "mature_source_agent_arm": {
                    "protocol_ref": "mature_source_agent_protocol_digest",
                    "cognition_input": "none",
                    "investigation_chain": "frozen-mature-source-agent",
                },
                "controlled_inputs": "same-exact-revision-model-questions-model-call-and-resource-budget-cache-policy-and-state-rubric-and-evaluator",
                "quality_gate": "full-cognition-and-mature-source-agent-zero-major-error-boundary-correct-and-full-cognition-no-material-claim-regression-versus-mature-source-agent",
                "locator_control_quality_failure_effect": "may-prove-quality-gain-but-cannot-lower-full-cognition-acceptance-threshold",
                "gain_gate": "full-cognition-must-have-precommitted-quality-gain-or-precommitted-normalized-non-locator-investigation-cost-gain-versus-locator-only-or-empty-arm",
                "proposed_quality_gain_threshold": "at-least-one-predeclared-material-checklist-gain-with-no-regression",
                "proposed_non_locator_cost_ratio_threshold_ppm": 900000,
                "cost_dimensions": "source-bytes-source-broker-operations-model-tokens-wall-time-provider-cost-and-world-model-build-update-storage-cost",
                "modeling_cost_accounting": "exact-world-model-build-update-storage-and-provider-cost-amortized-over-frozen-reuse-horizon",
                "proposed_reuse_horizon_questions": 12,
                "slice_001_required": False,
                "slice_002_case_id": "V-COMP-EARLY-002",
                "slice_003_case_id": "V-COMP-001",
            },
        }

    def test_engineering_qa_adaptive_gate_accepts_only_the_two_package_classes(
        self,
    ) -> None:
        manifest = self.valid_engineering_qa_adaptive_gate_manifest()
        self.assertEqual(
            docs_gate.validate_engineering_qa_adaptive_gate(
                manifest, "manifest.yaml"
            ),
            [],
        )
        package = manifest["question_evidence_package_classes"]
        self.assertIsInstance(package, dict)
        assert isinstance(package, dict)
        invalid_cases = (
            ("support_and_citation", "affirmative_claim_support_allowed", False),
            ("support_and_citation", "claim_citation_allowed", False),
            (
                "retained_non_support",
                "required_entry_kinds",
                "failure,partial,conflict,unknown",
            ),
            ("retained_non_support", "retention", "drop-after-seal"),
            ("retained_non_support", "affirmative_claim_support_allowed", True),
            ("retained_non_support", "affirmative_claim_citation_allowed", True),
            (
                "retained_non_support",
                "labeled_boundary_or_audit_reference_allowed",
                False,
            ),
        )
        for partition, field, invalid_value in invalid_cases:
            with self.subTest(partition=partition, field=field):
                invalid = copy.deepcopy(manifest)
                invalid_partition = invalid[
                    "question_evidence_package_classes"
                ][partition]
                invalid_partition[field] = invalid_value
                errors = docs_gate.validate_engineering_qa_adaptive_gate(
                    invalid, "manifest.yaml"
                )
                self.assertTrue(any(field in error for error in errors), errors)

        unexpected = copy.deepcopy(manifest)
        unexpected["question_evidence_package_classes"][
            "promoted_gap_support"
        ] = {}
        errors = docs_gate.validate_engineering_qa_adaptive_gate(
            unexpected, "manifest.yaml"
        )
        self.assertTrue(any("unexpected fields" in error for error in errors), errors)

    def test_engineering_qa_reviewer_verification_is_independent_and_adaptive(
        self,
    ) -> None:
        manifest = self.valid_engineering_qa_adaptive_gate_manifest()
        preview = copy.deepcopy(manifest)
        preview["development"]["slices"]["ITER-010-SLICE-001"][
            "status"
        ] = "authorized"
        self.assertEqual(
            docs_gate.validate_engineering_qa_adaptive_gate(
                preview, "manifest.yaml"
            ),
            [],
            "Slice 001's one verification-investigation bound is preview-only",
        )

        invalid_cases = (
            ("context", "shared-initial-investigation-context"),
            ("inputs", "review-gap-only"),
            ("reviewer_operation_proposal_allowed", True),
            ("adaptive_multi_step_required", False),
            ("prior_verification_result_must_drive_next_step", False),
            ("application_source_broker_worker_route_required", False),
            (
                "direct_source_filesystem_shell_network_credential_or_tool_access",
                "allowed",
            ),
            ("returns_to_initial_investigation_model", True),
            ("creates_new_ledger_revision_package_answer_and_review", False),
            ("slice_001_preview_upper_bound", 2),
            ("slice_001_bound_scope", "permanent-round-cap"),
            ("hardening_fixed_round_upper_bound_allowed", True),
            ("answerable_fuse_exhaustion_outcome", "limitation"),
        )
        for field, invalid_value in invalid_cases:
            with self.subTest(field=field):
                invalid = copy.deepcopy(manifest)
                invalid["reviewer_verification_investigation"][field] = invalid_value
                errors = docs_gate.validate_engineering_qa_adaptive_gate(
                    invalid, "manifest.yaml"
                )
                self.assertTrue(any(field in error for error in errors), errors)

    def test_engineering_qa_hardening_requires_frozen_fuses_and_ablation(
        self,
    ) -> None:
        manifest = self.valid_engineering_qa_adaptive_gate_manifest()
        receipt = "codex-user-message:sha256:" + "2" * 64
        slice_002 = manifest["development"]["slices"]["ITER-010-SLICE-002"]
        slice_002["status"] = "authorized"
        slice_002["authorization_ref"] = receipt

        proposed_errors = docs_gate.validate_engineering_qa_adaptive_gate(
            manifest, "manifest.yaml"
        )
        self.assertTrue(
            any("hardening_protocol_status" in error for error in proposed_errors),
            proposed_errors,
        )
        self.assertTrue(
            any("engineering_qa_ablation.status" in error for error in proposed_errors),
            proposed_errors,
        )

        verification = manifest["reviewer_verification_investigation"]
        frozen_fuses = {
            "hardening_package_revision_fuse": 3,
            "hardening_model_call_fuse": 4,
            "hardening_source_broker_operation_fuse": 128,
            "hardening_source_byte_fuse": 2097152,
            "hardening_wall_time_fuse": 900000,
            "hardening_no_progress_fuse": 2,
        }
        verification.update(frozen_fuses)
        verification.update(
            {
                "hardening_protocol_status": "frozen",
                "hardening_authorization_status": "user-authorized",
                "hardening_freeze_receipt_ref": receipt,
                "hardening_protocol_digest": docs_gate.canonical_mapping_digest(
                    docs_gate.ENGINEERING_QA_REVIEWER_VERIFICATION_SCHEMA,
                    "hardening_fuses",
                    frozen_fuses,
                ),
            }
        )
        answer_protocol = manifest["answer_protocol"]
        answer_protocol["answer_attempt_upper_bound"] = 5
        answer_protocol["review_attempt_upper_bound"] = 6
        answer_protocol["hard_safety_model_call_upper_bound_per_question"] = 40

        ablation = manifest["engineering_qa_ablation"]
        ablation["status"] = "frozen"
        ablation["authorization_ref"] = receipt
        frozen_ablation = {
            field: value
            for field, value in ablation.items()
            if field not in {"status", "authorization_ref", "frozen_protocol_digest"}
        }
        ablation["frozen_protocol_digest"] = docs_gate.canonical_mapping_digest(
            docs_gate.ENGINEERING_QA_ABLATION_SCHEMA,
            "engineering_qa_ablation",
            frozen_ablation,
        )
        self.assertEqual(
            docs_gate.validate_engineering_qa_adaptive_gate(
                manifest, "manifest.yaml"
            ),
            [],
        )

        one_round = copy.deepcopy(manifest)
        one_round["reviewer_verification_investigation"][
            "hardening_package_revision_fuse"
        ] = 1
        errors = docs_gate.validate_engineering_qa_adaptive_gate(
            one_round, "manifest.yaml"
        )
        self.assertTrue(
            any("must be at least 2" in error for error in errors), errors
        )

        reused_planning_receipt = copy.deepcopy(manifest)
        reused_planning_receipt["reviewer_verification_investigation"][
            "hardening_freeze_receipt_ref"
        ] = "codex-user-message:sha256:" + "3" * 64
        errors = docs_gate.validate_engineering_qa_adaptive_gate(
            reused_planning_receipt, "manifest.yaml"
        )
        self.assertTrue(
            any("current Slice 002 authorization_ref" in error for error in errors),
            errors,
        )

    def test_engineering_qa_ablation_freezes_fairness_quality_and_value(
        self,
    ) -> None:
        manifest = self.valid_engineering_qa_adaptive_gate_manifest()
        invalid_cases = (
            ("authorization_required_before", "after-slice-002"),
            ("controlled_inputs", "same-revision-only"),
            ("quality_gate", "average-score-only"),
            (
                "locator_control_quality_failure_effect",
                "lower-full-cognition-threshold",
            ),
            ("gain_gate", "locator-hit-rate-only"),
            ("proposed_non_locator_cost_ratio_threshold_ppm", 1000000),
            ("cost_dimensions", "model-tokens-only"),
            ("modeling_cost_accounting", "ignore-modeling-cost"),
            ("proposed_reuse_horizon_questions", 0),
        )
        for field, invalid_value in invalid_cases:
            with self.subTest(field=field):
                invalid = copy.deepcopy(manifest)
                invalid["engineering_qa_ablation"][field] = invalid_value
                errors = docs_gate.validate_engineering_qa_adaptive_gate(
                    invalid, "manifest.yaml"
                )
                self.assertTrue(any(field in error for error in errors), errors)

        wrong_arm = copy.deepcopy(manifest)
        wrong_arm["engineering_qa_ablation"]["locator_only_or_empty_arm"][
            "investigation_chain"
        ] = "shortcut-pipeline"
        errors = docs_gate.validate_engineering_qa_adaptive_gate(
            wrong_arm, "manifest.yaml"
        )
        self.assertTrue(
            any("locator_only_or_empty_arm.investigation_chain" in error for error in errors),
            errors,
        )

    def test_iter010_engineering_qa_hybrid_evidence_protocol_is_exact(self) -> None:
        source_scope, hybrid_evidence_path, answer_protocol = (
            self.valid_engineering_qa_sections()
        )
        self.assertEqual(
            docs_gate.validate_engineering_qa_hybrid_evidence_execution_readiness(
                source_scope,
                hybrid_evidence_path,
                answer_protocol,
                "manifest.yaml",
            ),
            [],
        )
        self.assertEqual(
            docs_gate.validate_answer_protocol_execution_readiness(
                answer_protocol, "manifest.yaml", "ITER-010"
            ),
            [],
        )

        invalid_cases = (
            ("source_scope", "provider", "REMOTE_GIT"),
            ("source_scope", "contract_ref", "SYS-CONTRACT-SOURCE-OTHER"),
            ("source_scope", "content_kind", "prebuilt-world-model-only"),
            ("source_scope", "question_or_suite_driven_update_allowed", True),
            ("source_scope", "question_time_read_only_retrieval_allowed", False),
            ("source_scope", "repository_write_allowed", True),
            ("hybrid_evidence_path", "mode", "WORLD_MODEL"),
            ("hybrid_evidence_path", "strict_world_model_mode_preserved", False),
            ("hybrid_evidence_path", "direct_investigation_mode_preserved", False),
            ("hybrid_evidence_path", "silent_mode_fallback_allowed", True),
            ("hybrid_evidence_path", "world_model_role", "plain-text-manual"),
            (
                "hybrid_evidence_path",
                "world_model_cognition_dimensions",
                "files-and-symbols-only",
            ),
            (
                "hybrid_evidence_path",
                "world_model_is_only_manual_map_cache_or_retrieval_hints",
                True,
            ),
            (
                "hybrid_evidence_path",
                "world_model_retrieval_hint_or_candidate_reduction_only",
                True,
            ),
            (
                "hybrid_evidence_path",
                "world_model_required_as_source_retrieval_gate",
                True,
            ),
            (
                "hybrid_evidence_path",
                "world_model_as_question-time-source-recall_gate_allowed",
                True,
            ),
            (
                "hybrid_evidence_path",
                "investigation_inputs",
                "snapshot-hints-only",
            ),
            (
                "hybrid_evidence_path",
                "retrieval_plan_inputs",
                "immutable-original-question-and-snapshot-hints",
            ),
            (
                "hybrid_evidence_path",
                "zero-irrelevant-or-insufficient-snapshot_blocks_exact-revision-retrieval",
                True,
            ),
            (
                "hybrid_evidence_path",
                "snapshot_source_revision_compatibility",
                "unchecked",
            ),
            (
                "hybrid_evidence_path",
                "investigation_model_role",
                "single-upfront-query-plan",
            ),
            ("hybrid_evidence_path", "model_role", "combined-model"),
            ("hybrid_evidence_path", "fact_authority", "sealed-package"),
            (
                "hybrid_evidence_path",
                "investigation_model_direct_source_access",
                "allowed",
            ),
            (
                "hybrid_evidence_path",
                "source_broker_role",
                "optional-pass-through",
            ),
            ("hybrid_evidence_path", "retrieval_worker_role", "model-controlled"),
            ("hybrid_evidence_path", "retrieval_worker_sources", "world-model-only"),
            ("hybrid_evidence_path", "retrieval_worker_access", "read-only"),
            ("hybrid_evidence_path", "source_trust", "trusted-instruction"),
            (
                "hybrid_evidence_path",
                "live_provider_source-fragment-disclosure",
                "implicitly-allowed",
            ),
            ("hybrid_evidence_path", "evidence_ledger", "mutable-buffer"),
            (
                "hybrid_evidence_path",
                "evidence_ledger_seal_trigger",
                "before-investigation",
            ),
            (
                "hybrid_evidence_path",
                "question_evidence_package_role",
                "fact-authority",
            ),
            ("hybrid_evidence_path", "package_seal_confers_truth", True),
            ("hybrid_evidence_path", "sealed_package_mutation_allowed", True),
            ("hybrid_evidence_path", "answer_repository_access", "allowed"),
            (
                "hybrid_evidence_path",
                "answer_direct_source_authority",
                "allowed",
            ),
            ("hybrid_evidence_path", "reviewer_repository_access", "allowed"),
            (
                "hybrid_evidence_path",
                "reviewer_direct_source_authority",
                "allowed",
            ),
            (
                "hybrid_evidence_path",
                "reviewer_direct_shell_network_credential_or_tool_access",
                "allowed",
            ),
            ("hybrid_evidence_path", "answer_input", "repository-and-package"),
            ("hybrid_evidence_path", "reviewer_input", "repository-and-draft"),
            (
                "hybrid_evidence_path",
                "reviewer_more_evidence_route",
                "reviewer-direct-repository-read",
            ),
            (
                "hybrid_evidence_path",
                "reviewer_verification_request_role",
                "executable-tool-command",
            ),
            (
                "hybrid_evidence_path",
                "reviewer_verification_returns_to_initial_investigation_model",
                True,
            ),
            ("hybrid_evidence_path", "knowledge_persistence", "synchronous"),
            ("answer_protocol", "schema", "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@1"),
            ("answer_protocol", "mode", "upfront-engineering-qa-hybrid-evidence"),
            ("answer_protocol", "contract_ref", "SYS-CONTRACT-APPLICATION-EVIDENCE-ANSWERING"),
            (
                "answer_protocol",
                "question_understanding_required_fields",
                "user-goal,audience,evidence-needs",
            ),
            ("answer_protocol", "investigation_model_call_upper_bound", 1),
            ("answer_protocol", "max_investigation_steps_per_question", 1),
            ("answer_protocol", "max_investigation_steps_per_question", 2),
            (
                "answer_protocol",
                "slice_001_reviewer_verification_investigation_upper_bound",
                2,
            ),
            ("answer_protocol", "max_source_broker_operations_per_question", 0),
            ("answer_protocol", "same_package_targeted_rewrite_upper_bound", 2),
            ("answer_protocol", "answer_attempt_upper_bound", 2),
            ("answer_protocol", "review_attempt_upper_bound", 2),
            ("answer_protocol", "max_source_files_per_question", 0),
            (
                "answer_protocol",
                "provider_output_complete-replacement_upper_bound_per_stage",
                0,
            ),
            (
                "answer_protocol",
                "hard_safety_model_call_upper_bound_per_question",
                1,
            ),
            ("answer_protocol", "upfront_complete_retrieval_plan_required", True),
            (
                "answer_protocol",
                "investigation_proposal_must_consider_prior_results",
                False,
            ),
            (
                "answer_protocol",
                "source_broker_policy_compilation_required",
                False,
            ),
            ("answer_protocol", "evidence_ledger_append_only", False),
            (
                "answer_protocol",
                "question_evidence_package_sealed_after_investigation",
                False,
            ),
            ("answer_protocol", "sealed_package_mutation_allowed", True),
            (
                "answer_protocol",
                "safety_budget_reserves_answer-comprehensive-review-and-challenge-review",
                False,
            ),
            (
                "answer_protocol",
                "review_focus_order",
                "comprehensive-only",
            ),
            (
                "answer_protocol",
                "reviewer_evidence_boundary_projection_is-semantic-verdict",
                True,
            ),
            (
                "answer_protocol",
                "quality_checklist_reduction_due_to_remaining_calls_allowed",
                True,
            ),
            (
                "answer_protocol",
                "evidence_requirement_reduction_due_to_remaining_calls_allowed",
                True,
            ),
            (
                "answer_protocol",
                "review_skipping_due_to_remaining_calls_allowed",
                True,
            ),
            (
                "answer_protocol",
                "reviewer_more_evidence_requires_specific_verifiable_gap",
                False,
            ),
            (
                "answer_protocol",
                "provider_finish_disposition_shape",
                "two-redundant-arrays",
            ),
            (
                "answer_protocol",
                "provider_finish_parent-evidence-references-returned-by-provider",
                True,
            ),
            (
                "answer_protocol",
                "provider_review_returns-independent-decision-or-verification-request",
                True,
            ),
            (
                "answer_protocol",
                "reviewer_rewrite-finding-requires-current-package-entry-ids",
                False,
            ),
            (
                "answer_protocol",
                "reviewer_action-and-verification-request-derivation",
                "provider-owned",
            ),
            (
                "answer_protocol",
                "reviewer_draft-only-scope-expansion-may-trigger-new-evidence-investigation",
                True,
            ),
            (
                "answer_protocol",
                "reviewer_verification_request_requires_application_and_source_broker_revalidation",
                False,
            ),
            (
                "answer_protocol",
                "reviewer_verification_uses_independent_fresh_context_adaptive_investigation",
                False,
            ),
            (
                "answer_protocol",
                "reviewer_verification_returns_to_initial_investigation_model",
                True,
            ),
            (
                "answer_protocol",
                "reviewer_verification_fixed_round_cap_after_slice_001_allowed",
                True,
            ),
            (
                "answer_protocol",
                "reviewer_verification_request_round_upper_bound",
                1,
            ),
            ("answer_protocol", "reviewer_verification_uses_source_broker", True),
            (
                "answer_protocol",
                "reviewer_verification_creates_new_ledger_revision",
                False,
            ),
            (
                "answer_protocol",
                "reviewer_verification_creates_new_package",
                False,
            ),
            ("answer_protocol", "new_answer_after_new_package_required", False),
            (
                "answer_protocol",
                "same_package_rewrite_requires_specific_reviewer_finding",
                False,
            ),
            (
                "answer_protocol",
                "independent_rereview_after_any_answer_or_package_change_required",
                False,
            ),
            (
                "answer_protocol",
                "question_or_project_keyword_symbol_class_method_fixture_or_oracle_special_routing_allowed",
                True,
            ),
            ("answer_protocol", "resource_exhaustion_behavior", "best-effort"),
            (
                "answer_protocol",
                "deterministic_grounding_authorization_revision-allowlist-and-package-seal_checks",
                False,
            ),
            ("answer_protocol", "provider_request_retries_allowed", True),
            ("answer_protocol", "provider_switch_after_dispatch_allowed", True),
        )
        original_sections = {
            "source_scope": source_scope,
            "hybrid_evidence_path": hybrid_evidence_path,
            "answer_protocol": answer_protocol,
        }
        for section_name, field, invalid_value in invalid_cases:
            with self.subTest(section=section_name, field=field):
                sections = copy.deepcopy(original_sections)
                sections[section_name][field] = invalid_value
                errors = (
                    docs_gate.validate_engineering_qa_hybrid_evidence_execution_readiness(
                        sections["source_scope"],
                        sections["hybrid_evidence_path"],
                        sections["answer_protocol"],
                        "manifest.yaml",
                    )
                )
                self.assertTrue(
                    any(f"{section_name}.{field}" in error for error in errors),
                    errors,
                )

    def test_pre_iter010_cannot_replace_world_model_protocol_with_hybrid_fields(
        self,
    ) -> None:
        _, _, answer_protocol = self.valid_engineering_qa_sections()
        errors = docs_gate.validate_answer_protocol_execution_readiness(
            answer_protocol, "manifest.yaml", "ITER-009"
        )
        self.assertTrue(
            any("supported only from ITER-010" in error for error in errors),
            errors,
        )

    def test_iter010_rejects_the_replaced_upfront_package_protocol(self) -> None:
        _, _, answer_protocol = self.valid_engineering_qa_sections()
        answer_protocol["mode"] = "upfront-engineering-qa-hybrid-evidence"
        errors = docs_gate.validate_answer_protocol_execution_readiness(
            answer_protocol, "manifest.yaml", "ITER-010"
        )
        self.assertTrue(
            any(
                "adaptive-cognition-guided-engineering-investigation" in error
                for error in errors
            ),
            errors,
        )

    def test_iter008_answer_protocol_uses_bounded_variable_investigation(
        self,
    ) -> None:
        protocol: dict[str, object] = {
            "mode": "bounded-result-driven-world-model-investigation",
            "max_investigation_steps": 6,
            "max_investigation_model_calls": 4,
            "planner_model_call_upper_bound": 4,
            "max_query_bytes_per_step": 2048,
            "max_result_bytes_per_step": 8192,
            "max_total_query_bytes_per_question": 12288,
            "max_total_result_bytes_per_question": 49152,
            "max_wall_time_milliseconds_per_question": 30000,
            "max_support_items_per_question": 64,
            "max_trace_bytes_per_question": 131072,
            "budget_exhaustion_behavior": "fail-closed-with-explicit-limitation",
            "draft_model_calls": 1,
            "independent_reviewer_model_calls": 1,
            "deterministic_schema_grounding_and_authorization_checks": True,
            "retries_allowed": False,
            "total_model_call_upper_bound_per_question": 6,
            "status": "frozen",
        }
        self.assertEqual(
            docs_gate.validate_answer_protocol_execution_readiness(
                protocol, "manifest.yaml", "ITER-008"
            ),
            [],
        )
        self.assertEqual(
            docs_gate.validate_answer_protocol_execution_readiness(
                protocol, "manifest.yaml", "ITER-011"
            ),
            [],
            "later iterations may explicitly retain the strict WORLD_MODEL protocol",
        )

        legacy = {
            **protocol,
            "planner_model_calls": 1,
            "exact_total_model_calls_per_question": 3,
        }
        legacy_errors = docs_gate.validate_answer_protocol_execution_readiness(
            legacy, "manifest.yaml", "ITER-008"
        )
        self.assertTrue(
            any("legacy fixed-call" in error for error in legacy_errors),
            legacy_errors,
        )

        wrong_total = {
            **protocol,
            "total_model_call_upper_bound_per_question": 5,
        }
        total_errors = docs_gate.validate_answer_protocol_execution_readiness(
            wrong_total, "manifest.yaml", "ITER-008"
        )
        self.assertTrue(
            any("plus one Draft" in error for error in total_errors), total_errors
        )

        not_result_driven = {
            **protocol,
            "max_investigation_steps": 1,
            "max_investigation_model_calls": 1,
            "planner_model_call_upper_bound": 1,
            "total_model_call_upper_bound_per_question": 3,
        }
        result_driven_errors = (
            docs_gate.validate_answer_protocol_execution_readiness(
                not_result_driven, "manifest.yaml", "ITER-008"
            )
        )
        self.assertTrue(
            any("must be at least 2" in error for error in result_driven_errors),
            result_driven_errors,
        )

        missing_trace_bound = dict(protocol)
        del missing_trace_bound["max_trace_bytes_per_question"]
        trace_errors = docs_gate.validate_answer_protocol_execution_readiness(
            missing_trace_bound, "manifest.yaml", "ITER-008"
        )
        self.assertTrue(
            any("max_trace_bytes_per_question" in error for error in trace_errors),
            trace_errors,
        )

    def test_positive_value_is_frozen_and_measured_not_self_reported(self) -> None:
        alignment: dict[str, object] = {
            "positive_value_metric": "normalized-reuse-cost",
            "positive_value_unit": "basis-points",
            "positive_value_comparison": "at-most",
            "positive_value_threshold": 8000,
            "positive_value_reuse_horizon_questions": 3,
            "mature_source_agent_protocol_digest": "sha256:" + "1" * 64,
            "mature_source_agent_rubric_digest": "sha256:" + "2" * 64,
            "mature_source_agent_cache_policy_digest": "sha256:" + "3" * 64,
            "positive_value_protocol_digest": "sha256:" + "4" * 64,
            "positive_value_freeze_receipt_ref": (
                "codex-user-message:sha256:" + "5" * 64
            ),
            "positive_value_adjudication_owner": "user",
        }
        self.assertEqual(
            docs_gate.validate_positive_value_execution_readiness(
                alignment, "manifest.yaml"
            ),
            [],
        )
        result_id = "ITER-008-RESULT-PRODUCT"
        value_metadata = {
            "id": result_id,
            "iteration": "ITER-008",
            "positive_value_verdict": "PASS",
            "positive_value_actual": 7500,
            "positive_value_case_id": "V-000",
            "positive_value_report_ref": f"{result_id}#positive-value-report",
            "positive_value_adjudication_receipt_ref": (
                "codex-user-message:sha256:" + "6" * 64
            ),
            **{
                field: alignment[field]
                for field in (
                    "positive_value_metric",
                    "positive_value_unit",
                    "positive_value_comparison",
                    "positive_value_threshold",
                    "positive_value_reuse_horizon_questions",
                    "mature_source_agent_protocol_digest",
                    "mature_source_agent_rubric_digest",
                    "mature_source_agent_cache_policy_digest",
                    "positive_value_protocol_digest",
                    "positive_value_freeze_receipt_ref",
                    "positive_value_adjudication_owner",
                )
            },
        }
        value_report_body, value_report_digest = positive_value_report_section(
            value_metadata, result_id, "V-000"
        )
        result = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/results/product.md",
            {
                **value_metadata,
                "positive_value_report_digest": value_report_digest,
            },
            "# Result\n\n" + value_report_body,
        )
        self.assertEqual(
            docs_gate.validate_positive_value_result(
                result, alignment, "product.md", expected_case_id="V-000"
            ),
            [],
        )

        missed_threshold = docs_gate.Document(
            result.path,
            {**result.metadata, "positive_value_actual": 8001},
            result.body,
        )
        threshold_errors = docs_gate.validate_positive_value_result(
            missed_threshold,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("does not satisfy" in error for error in threshold_errors),
            threshold_errors,
        )

        failed_value_metadata = {
            **value_metadata,
            "positive_value_verdict": "FAIL",
            "positive_value_actual": 8001,
        }
        failed_report_body, failed_report_digest = positive_value_report_section(
            failed_value_metadata, result_id, "V-000"
        )
        failed_value_result = docs_gate.Document(
            result.path,
            {
                **failed_value_metadata,
                "positive_value_report_digest": failed_report_digest,
            },
            "# Result\n\n" + failed_report_body,
        )
        self.assertEqual(
            docs_gate.validate_positive_value_result(
                failed_value_result,
                alignment,
                "product.md",
                require_pass=False,
                expected_case_id="V-000",
            ),
            [],
        )

        forged_digest = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "positive_value_report_digest": "sha256:" + "f" * 64,
            },
            result.body,
        )
        forged_errors = docs_gate.validate_positive_value_result(
            forged_digest,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("exact Positive value report section" in error for error in forged_errors),
            forged_errors,
        )

        duplicate_report_result = docs_gate.Document(
            result.path,
            result.metadata,
            result.body
            + "\n## Positive value report\n\n"
            + '{"actual": 0, "adjudication_receipt_ref": "attacker"}\n',
        )
        duplicate_report_errors = docs_gate.validate_positive_value_result(
            duplicate_report_result,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("exactly one Positive value report" in error for error in duplicate_report_errors),
            duplicate_report_errors,
        )

        duplicate_key_body = result.body.replace(
            '"actual": 7500,',
            '"actual": 9999,\n  "actual": 7500,',
        )
        duplicate_key_section = docs_gate.markdown_section_body(
            docs_gate.Document(result.path, {}, duplicate_key_body),
            "Positive value report",
        )
        assert duplicate_key_section is not None
        duplicate_key_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "positive_value_report_digest": "sha256:"
                + hashlib.sha256(duplicate_key_section.encode("utf-8")).hexdigest(),
            },
            duplicate_key_body,
        )
        duplicate_key_errors = docs_gate.validate_positive_value_result(
            duplicate_key_result,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("duplicate JSON key" in error for error in duplicate_key_errors),
            duplicate_key_errors,
        )

        extra_field_body = result.body.replace(
            '\n}', '\n  ,"verdict": "FAIL"\n}', 1
        )
        extra_field_section = docs_gate.markdown_section_body(
            docs_gate.Document(result.path, {}, extra_field_body),
            "Positive value report",
        )
        assert extra_field_section is not None
        extra_field_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "positive_value_report_digest": "sha256:"
                + hashlib.sha256(extra_field_section.encode("utf-8")).hexdigest(),
            },
            extra_field_body,
        )
        extra_field_errors = docs_gate.validate_positive_value_result(
            extra_field_result,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("exact v1 schema fields" in error for error in extra_field_errors),
            extra_field_errors,
        )

        float_actual_body = result.body.replace(
            '"actual": 7500,', '"actual": 7500.0,', 1
        )
        float_actual_section = docs_gate.markdown_section_body(
            docs_gate.Document(result.path, {}, float_actual_body),
            "Positive value report",
        )
        assert float_actual_section is not None
        float_actual_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "positive_value_report_digest": "sha256:"
                + hashlib.sha256(float_actual_section.encode("utf-8")).hexdigest(),
            },
            float_actual_body,
        )
        float_actual_errors = docs_gate.validate_positive_value_result(
            float_actual_result,
            alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("actual must be an exact JSON integer" in error for error in float_actual_errors),
            float_actual_errors,
        )

        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.yaml"
            manifest_path.write_text(
                "product_goal_alignment:\n"
                "  positive_value_metric: normalized-reuse-cost\n"
                "  positive_value_unit: basis-points\n"
                "  positive_value_comparison: at-most\n"
                "  positive_value_threshold: 8000\n"
                "  positive_value_reuse_horizon_questions: 3\n"
                f"  mature_source_agent_protocol_digest: {'sha256:' + '1' * 64}\n"
                f"  mature_source_agent_rubric_digest: {'sha256:' + '2' * 64}\n"
                f"  mature_source_agent_cache_policy_digest: {'sha256:' + '3' * 64}\n"
                f"  positive_value_protocol_digest: {'sha256:' + '4' * 64}\n"
                f"  positive_value_freeze_receipt_ref: {'codex-user-message:sha256:' + '5' * 64}\n"
                "  positive_value_adjudication_owner: user\n"
                "development:\n"
                "  slices: {}\n"
                "authorization:\n"
                f"  authorization_ref: {'codex-user-message:sha256:' + '6' * 64}\n",
                encoding="utf-8",
            )
            final_freshness_errors = docs_gate.validate_product_goal_result(
                result,
                "ITER-008",
                manifest_path,
                docs_gate.Document(
                    result.path.parent / "verification-matrix.md",
                    {"id": "ITER-008-VERIFICATION"},
                    "# Verification\n",
                ),
            )
        self.assertTrue(
            any(
                "final positive value adjudication must use a new message" in error
                for error in final_freshness_errors
            ),
            final_freshness_errors,
        )

        unfrozen = {
            **alignment,
            "mature_source_agent_protocol_digest": "user-held-not-disclosed",
        }
        freeze_errors = docs_gate.validate_positive_value_execution_readiness(
            unfrozen, "manifest.yaml"
        )
        self.assertTrue(
            any(
                "mature_source_agent_protocol_digest" in error
                for error in freeze_errors
            ),
            freeze_errors,
        )

    def test_iter012_quality_margin_rejects_tie_and_records_negative_failure(
        self,
    ) -> None:
        alignment: dict[str, object] = {
            "held_out_evaluation_owner": "independent-evaluator",
            "positive_value_adjudication_owner": "independent-evaluator",
            "positive_value_metric": docs_gate.STRICT_CODEX_QUALITY_METRIC,
            "positive_value_unit": docs_gate.STRICT_CODEX_QUALITY_UNIT,
            "positive_value_comparison": docs_gate.STRICT_CODEX_QUALITY_COMPARISON,
            "positive_value_threshold": 1,
            "positive_value_reuse_horizon_questions": 3,
            "mature_source_agent_identity_digest": "sha256:" + "0" * 64,
            "mature_source_agent_role": docs_gate.STRICT_CODEX_BASELINE_ROLE,
            "mature_source_agent_execution_mode": docs_gate.STRICT_CODEX_BASELINE_EXECUTION_MODE,
            "secondary_metrics_can_compensate_answer_quality": False,
            "mature_source_agent_protocol_digest": "sha256:" + "1" * 64,
            "mature_source_agent_rubric_digest": "sha256:" + "2" * 64,
            "mature_source_agent_cache_policy_digest": "sha256:" + "3" * 64,
            "positive_value_protocol_digest": "sha256:" + "4" * 64,
            "positive_value_freeze_receipt_ref": (
                "codex-user-message:sha256:" + "5" * 64
            ),
            "alpha_agent_comparison_binding": {
                "case_id": "V-COMP-ALPHA-001",
                "question_count": 3,
            },
        }
        self.assertEqual(
            docs_gate.validate_positive_value_execution_readiness(
                alignment, "manifest.yaml", "ITER-012"
            ),
            [],
        )

        result_id = "ITER-012-RESULT-ALPHA"

        def make_result(
            *,
            actual: int,
            verdict: str,
            case_id: str = "V-COMP-ALPHA-001",
            absolute_verdict: str = "PASS",
            system_better: int = 1,
            evaluated: int = 3,
            tie: int | None = None,
            codex_better: int = 0,
            both_fail: int = 0,
            unresolved_or_invalid: int = 0,
        ) -> docs_gate.Document:
            resolved_tie = (
                evaluated
                - system_better
                - codex_better
                - both_fail
                - unresolved_or_invalid
                if tie is None
                else tie
            )
            metadata = {
                "id": result_id,
                "iteration": "ITER-012",
                "positive_value_verdict": verdict,
                "positive_value_actual": actual,
                "mature_source_agent_comparison": docs_gate.STRICT_CODEX_RESULT_COMPARISON,
                "system_absolute_quality_verdict": absolute_verdict,
                "evaluated_question_count": evaluated,
                "system_better_question_count": system_better,
                "tie_question_count": resolved_tie,
                "codex_better_question_count": codex_better,
                "both_fail_question_count": both_fail,
                "unresolved_or_invalid_question_count": unresolved_or_invalid,
                "positive_value_case_id": case_id,
                "positive_value_report_ref": f"{result_id}#positive-value-report",
                "positive_value_adjudication_receipt_ref": (
                    "independent-evaluator-result:sha256:" + "6" * 64
                ),
                **{
                    field: alignment[field]
                    for field in (
                        "positive_value_metric",
                        "positive_value_unit",
                        "positive_value_comparison",
                        "positive_value_threshold",
                        "positive_value_reuse_horizon_questions",
                        "mature_source_agent_identity_digest",
                        "mature_source_agent_protocol_digest",
                        "mature_source_agent_rubric_digest",
                        "mature_source_agent_cache_policy_digest",
                        "positive_value_protocol_digest",
                        "positive_value_freeze_receipt_ref",
                        "positive_value_adjudication_owner",
                    )
                },
            }
            report_body, report_digest = positive_value_report_section(
                metadata, result_id, case_id
            )
            return docs_gate.Document(
                docs_gate.REPOSITORY
                / "docs/project/iterations/iteration-012/results/alpha.md",
                {**metadata, "positive_value_report_digest": report_digest},
                "# Result\n\n" + report_body,
            )

        passed = make_result(actual=1, verdict="PASS")
        self.assertEqual(
            docs_gate.validate_positive_value_result(
                passed,
                alignment,
                "alpha.md",
                expected_case_id="V-COMP-ALPHA-001",
            ),
            [],
        )

        tied = make_result(actual=0, verdict="FAIL", system_better=0)
        self.assertEqual(
            docs_gate.validate_positive_value_result(
                tied,
                alignment,
                "alpha.md",
                require_pass=False,
                expected_case_id="V-COMP-ALPHA-001",
            ),
            [],
        )
        tied_as_pass = make_result(actual=0, verdict="PASS", system_better=0)
        self.assertTrue(
            docs_gate.validate_positive_value_result(
                tied_as_pass,
                alignment,
                "alpha.md",
                expected_case_id="V-COMP-ALPHA-001",
            )
        )

        lost = make_result(
            actual=-10, verdict="FAIL", system_better=0, codex_better=1
        )
        self.assertEqual(
            docs_gate.validate_positive_value_result(
                lost,
                alignment,
                "alpha.md",
                require_pass=False,
                expected_case_id="V-COMP-ALPHA-001",
            ),
            [],
        )
        aggregate_win_with_question_loss = make_result(
            actual=10,
            verdict="FAIL",
            system_better=2,
            codex_better=1,
        )
        self.assertEqual(
            docs_gate.validate_positive_value_result(
                aggregate_win_with_question_loss,
                alignment,
                "alpha.md",
                require_pass=False,
                expected_case_id="V-COMP-ALPHA-001",
            ),
            [],
        )

        under_evaluated = make_result(
            actual=1,
            verdict="PASS",
            evaluated=2,
            system_better=1,
        )
        under_evaluated_errors = docs_gate.validate_positive_value_result(
            under_evaluated,
            alignment,
            "alpha.md",
            expected_case_id="V-COMP-ALPHA-001",
        )
        self.assertTrue(
            any("frozen question count" in error for error in under_evaluated_errors),
            under_evaluated_errors,
        )

        category_mismatch = make_result(
            actual=1,
            verdict="PASS",
            evaluated=3,
            system_better=1,
            tie=1,
        )
        category_errors = docs_gate.validate_positive_value_result(
            category_mismatch,
            alignment,
            "alpha.md",
            expected_case_id="V-COMP-ALPHA-001",
        )
        self.assertTrue(
            any("classification counts" in error for error in category_errors),
            category_errors,
        )

        final_alignment = {**alignment, "held_out_question_count": 5}
        under_evaluated_final = make_result(
            actual=1,
            verdict="PASS",
            case_id="V-000",
            evaluated=3,
            system_better=1,
        )
        final_count_errors = docs_gate.validate_positive_value_result(
            under_evaluated_final,
            final_alignment,
            "product.md",
            expected_case_id="V-000",
        )
        self.assertTrue(
            any("frozen question count" in error for error in final_count_errors),
            final_count_errors,
        )

        early_alignment = {
            **alignment,
            "early_comparison_binding": {
                "case_id": "V-COMP-EARLY-001",
                "canary_case_id": "V-CANARY-001",
            },
            "early_hidden_canary_bindings": {
                "hardening": {
                    "case_id": "V-CANARY-001",
                    "question_count": 7,
                }
            },
        }
        self.assertEqual(
            docs_gate.strict_codex_frozen_question_count(
                early_alignment, "V-COMP-EARLY-001"
            ),
            7,
        )
        early_pass = make_result(
            actual=1,
            verdict="PASS",
            case_id="V-COMP-EARLY-001",
            evaluated=7,
            system_better=1,
        )
        self.assertEqual(
            docs_gate.validate_positive_value_result(
                early_pass,
                early_alignment,
                "hardening.md",
                expected_case_id="V-COMP-EARLY-001",
            ),
            [],
        )
        both_failed = make_result(
            actual=1,
            verdict="FAIL",
            absolute_verdict="FAIL",
            system_better=1,
            both_fail=1,
        )
        self.assertEqual(
            docs_gate.validate_positive_value_result(
                both_failed,
                alignment,
                "alpha.md",
                require_pass=False,
                expected_case_id="V-COMP-ALPHA-001",
            ),
            [],
        )

        legacy_receipt = make_result(actual=1, verdict="PASS")
        legacy_receipt_metadata = {
            **legacy_receipt.metadata,
            "positive_value_adjudication_receipt_ref": (
                "codex-user-message:sha256:" + "6" * 64
            ),
        }
        legacy_receipt_body, legacy_receipt_digest = positive_value_report_section(
            legacy_receipt_metadata, result_id, "V-COMP-ALPHA-001"
        )
        legacy_receipt_result = docs_gate.Document(
            legacy_receipt.path,
            {
                **legacy_receipt_metadata,
                "positive_value_report_digest": legacy_receipt_digest,
            },
            "# Result\n\n" + legacy_receipt_body,
        )
        self.assertTrue(
            any(
                "independent-evaluator-result" in error
                for error in docs_gate.validate_positive_value_result(
                    legacy_receipt_result,
                    alignment,
                    "alpha.md",
                    expected_case_id="V-COMP-ALPHA-001",
                )
            )
        )
    def test_iter012_final_result_rejects_non_regression_only(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.yaml"
            manifest_path.write_text(
                "product_goal_alignment: {}\ndevelopment:\n  slices: {}\n",
                encoding="utf-8",
            )
            verification = docs_gate.Document(
                docs_gate.REPOSITORY
                / "docs/project/iterations/iteration-012/verification-matrix.md",
                {"id": "ITER-012-VERIFICATION"},
                "",
            )
            base_metadata = {
                "id": "ITER-012-RESULT-PRODUCT",
                "iteration": "ITER-012",
                "mature_source_agent_comparison": "non-regression",
            }
            result = docs_gate.Document(
                docs_gate.REPOSITORY
                / "docs/project/iterations/iteration-012/results/product.md",
                base_metadata,
                "",
            )
            errors = docs_gate.validate_product_goal_result(
                result, "ITER-012", manifest_path, verification
            )
            self.assertTrue(
                any(
                    docs_gate.STRICT_CODEX_RESULT_COMPARISON in error
                    for error in errors
                ),
                errors,
            )
            strict_result = docs_gate.Document(
                result.path,
                {
                    **base_metadata,
                    "mature_source_agent_comparison": docs_gate.STRICT_CODEX_RESULT_COMPARISON,
                },
                result.body,
            )
            strict_errors = docs_gate.validate_product_goal_result(
                strict_result, "ITER-012", manifest_path, verification
            )
            self.assertFalse(
                any("mature_source_agent_comparison must equal" in error for error in strict_errors),
                strict_errors,
            )

    def test_early_evaluation_bindings_are_frozen_before_execution(self) -> None:
        new_refs = ["ITER-008-SLICE-001", "ITER-008-SLICE-002"]
        blocking = [
            "V-CANARY-001",
            "V-NEG-EARLY-001",
            "V-COMP-EARLY-001",
            "V-DIAG-001",
        ]
        alignment: dict[str, object] = {
            "evaluation_input_mode": "user-held-live-after-product-code-freeze",
            "mature_source_agent_protocol_digest": "user-held-not-disclosed",
            "mature_source_agent_rubric_digest": "not-frozen-proposal-only",
            "positive_value_metric": "not-frozen-proposal-only",
            "positive_value_unit": "not-frozen-proposal-only",
            "positive_value_comparison": "not-frozen-proposal-only",
            "positive_value_threshold": "not-frozen-proposal-only",
            "positive_value_reuse_horizon_questions": "not-frozen-proposal-only",
            "mature_source_agent_cache_policy_digest": "not-frozen-proposal-only",
            "positive_value_protocol_digest": "not-frozen-proposal-only",
            "positive_value_freeze_receipt_ref": "not-authorized",
            "positive_value_adjudication_owner": "user",
            "early_hidden_canary_bindings": {
                "slice_001": {
                    "case_id": "V-CANARY-001",
                    "new_slice_ref": new_refs[0],
                    "project_manifest_digest": "user-held-not-disclosed",
                    "suite_digest": "user-held-not-disclosed",
                    "question_count": 3,
                    "answerable_question_count": 1,
                    "boundary_question_count": 2,
                    "bounded_absence_question_count": 1,
                    "coverage_limitation_question_count": 1,
                    "negative_case_id": "V-NEG-EARLY-001",
                    "evaluation_owner": "user",
                    "implementation_visibility": "hidden-until-slice-code-freeze",
                    "burn_rule": "product-change-between-disclosure-and-slice-result-seal-burns-canary-and-preserves-result",
                }
            },
            "early_comparison_binding": {
                "case_id": "V-COMP-EARLY-001",
                "canary_case_id": "V-CANARY-001",
                "new_slice_ref": new_refs[0],
                "protocol_digest_ref": "mature_source_agent_protocol_digest",
                "quality_rule": "zero-major-error-and-no-need-claim-regression",
                "positive_value_rule": "precommitted-measurable-world-model-advantage-must-pass",
                "positive_value_metric_ref": "positive_value_metric",
                "positive_value_unit_ref": "positive_value_unit",
                "positive_value_comparison_ref": "positive_value_comparison",
                "positive_value_threshold_ref": "positive_value_threshold",
                "positive_value_reuse_horizon_ref": "positive_value_reuse_horizon_questions",
                "baseline_cache_policy_digest_ref": "mature_source_agent_cache_policy_digest",
                "positive_value_protocol_digest_ref": "positive_value_protocol_digest",
                "positive_value_adjudication_owner_ref": "positive_value_adjudication_owner",
            },
            "early_diagnostic_binding": {
                "case_id": "V-DIAG-001",
                "canary_case_id": "V-CANARY-001",
                "new_slice_ref": new_refs[0],
                "layer_chain": "source-snapshot-query-trace-draft-review-web",
            },
        }
        self.assertEqual(
            docs_gate.validate_early_evaluation_bindings(
                alignment, new_refs, blocking, "manifest.yaml"
            ),
            [],
        )

        adaptive_alignment = copy.deepcopy(alignment)
        adaptive_alignment["early_diagnostic_binding"][  # type: ignore[index]
            "layer_chain"
        ] = (
            "source-observation-world-model-cognition-conversation-or-task-"
            "understanding-agent-work-state-and-plan-source-broker-retrieval-"
            "worker-evidence-ledger-question-evidence-package-answer-"
            "independent-review-web"
        )
        self.assertEqual(
            docs_gate.validate_early_evaluation_bindings(
                adaptive_alignment,
                new_refs,
                blocking,
                "manifest.yaml",
                adaptive_engineering_qa=True,
            ),
            [],
        )
        self.assertTrue(
            any(
                "layer_chain" in error
                for error in docs_gate.validate_early_evaluation_bindings(
                    adaptive_alignment,
                    new_refs,
                    blocking,
                    "manifest.yaml",
                )
            )
        )

        missing_comparison = copy.deepcopy(alignment)
        del missing_comparison["early_comparison_binding"]
        missing_errors = docs_gate.validate_early_evaluation_bindings(
            missing_comparison, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("early_comparison_binding" in error for error in missing_errors),
            missing_errors,
        )

        wrong_canary = copy.deepcopy(alignment)
        wrong_canary["early_diagnostic_binding"][  # type: ignore[index]
            "canary_case_id"
        ] = "V-CANARY-999"
        canary_errors = docs_gate.validate_early_evaluation_bindings(
            wrong_canary, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("same canary" in error for error in canary_errors), canary_errors
        )

        wrong_layers = copy.deepcopy(alignment)
        wrong_layers["early_diagnostic_binding"][  # type: ignore[index]
            "layer_chain"
        ] = "source-answer"
        layer_errors = docs_gate.validate_early_evaluation_bindings(
            wrong_layers, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("layer_chain" in error for error in layer_errors), layer_errors
        )

    def test_direction_preview_defers_early_gates_to_the_following_slice(
        self,
    ) -> None:
        new_refs = ["ITER-009-SLICE-001", "ITER-009-SLICE-002"]
        preview_case = "V-PREVIEW-001"
        later_cases = [
            "V-CANARY-001",
            "V-NEG-EARLY-001",
            "V-COMP-EARLY-001",
            "V-DIAG-001",
        ]
        blocking = [preview_case, *later_cases]
        alignment: dict[str, object] = {
            "direction_preview_checkpoint": preview_case,
            "direction_preview_binding": {
                "case_id": preview_case,
                "new_slice_ref": new_refs[0],
                "real_product_entry": "loopback-product-owned-world-model-web",
                "representative_task_count": 2,
                "status_label": "non-acceptance-non-production",
                "decision_owner": "user",
                "allowed_decisions": "CONTINUE,REDIRECT,REJECT",
                "hardening_requires_continue": True,
            },
            "evaluation_input_mode": "user-held-live-after-product-code-freeze",
            "mature_source_agent_protocol_digest": "user-held-not-disclosed",
            "mature_source_agent_rubric_digest": "sha256:" + "2" * 64,
            "positive_value_metric": "normalized-reuse-cost",
            "positive_value_unit": "basis-points",
            "positive_value_comparison": "at-most",
            "positive_value_threshold": 8000,
            "positive_value_reuse_horizon_questions": 3,
            "mature_source_agent_cache_policy_digest": "sha256:" + "3" * 64,
            "positive_value_protocol_digest": "sha256:" + "4" * 64,
            "positive_value_freeze_receipt_ref": "codex-user-message:sha256:"
            + "5" * 64,
            "positive_value_adjudication_owner": "user",
        }

        self.assertEqual(
            docs_gate.validate_direction_preview_binding(
                alignment, new_refs, blocking, "manifest.yaml"
            ),
            [],
        )

        engineering_qa_entry = copy.deepcopy(alignment)
        engineering_qa_entry["direction_preview_binding"][  # type: ignore[index]
            "real_product_entry"
        ] = "loopback-product-owned-engineering-qa-web"
        self.assertEqual(
            docs_gate.validate_direction_preview_binding(
                engineering_qa_entry, new_refs, blocking, "manifest.yaml"
            ),
            [],
        )
        self.assertEqual(
            docs_gate.resolved_direction_preview_slice_ref(
                engineering_qa_entry, new_refs
            ),
            new_refs[0],
        )
        _, _, engineering_protocol = self.valid_engineering_qa_sections()
        self.assertEqual(
            docs_gate.validate_direction_preview_answer_entry(
                engineering_qa_entry, engineering_protocol, "manifest.yaml"
            ),
            [],
        )
        mismatched_mode_errors = docs_gate.validate_direction_preview_answer_entry(
            alignment, engineering_protocol, "manifest.yaml"
        )
        self.assertTrue(
            any("must match answer_protocol.mode" in error for error in mismatched_mode_errors),
            mismatched_mode_errors,
        )

        wrong_entry = copy.deepcopy(alignment)
        wrong_entry["direction_preview_binding"]["real_product_entry"] = (
            "https://public.example.test/"
        )
        self.assertTrue(
            any(
                "real_product_entry" in error
                for error in docs_gate.validate_direction_preview_binding(
                    wrong_entry, new_refs, blocking, "manifest.yaml"
                )
            )
        )
        arbitrary_loopback_entry = copy.deepcopy(alignment)
        arbitrary_loopback_entry["direction_preview_binding"][  # type: ignore[index]
            "real_product_entry"
        ] = "loopback-product-owned-engineering-qa-web-preview"
        self.assertTrue(
            any(
                "real_product_entry" in error
                for error in docs_gate.validate_direction_preview_binding(
                    arbitrary_loopback_entry,
                    new_refs,
                    blocking,
                    "manifest.yaml",
                )
            )
        )
        wrong_owner = copy.deepcopy(alignment)
        wrong_owner["direction_preview_binding"]["decision_owner"] = "automation"
        self.assertTrue(
            any(
                "decision_owner" in error
                for error in docs_gate.validate_direction_preview_binding(
                    wrong_owner, new_refs, blocking, "manifest.yaml"
                )
            )
        )
        self.assertEqual(
            docs_gate.required_early_evaluation_slice_refs(
                alignment, new_refs, direction_preview_enabled=True
            ),
            {new_refs[1]},
        )
        self.assertEqual(
            docs_gate.validate_early_evaluation_bindings(
                alignment,
                new_refs,
                blocking,
                "manifest.yaml",
                defer_until_post_preview=True,
                direction_preview_enabled=True,
            ),
            [],
        )

        preview_owns_comparison = copy.deepcopy(alignment)
        preview_owns_comparison["early_comparison_binding"] = {
            "case_id": "V-COMP-EARLY-001",
            "new_slice_ref": new_refs[0],
        }
        preview_errors = docs_gate.validate_early_evaluation_bindings(
            preview_owns_comparison,
            new_refs,
            blocking,
            "manifest.yaml",
            defer_until_post_preview=True,
            direction_preview_enabled=True,
        )
        self.assertTrue(
            any("direction preview Slice must not own" in error for error in preview_errors),
            preview_errors,
        )

        missing_later_errors = docs_gate.validate_early_evaluation_bindings(
            alignment,
            new_refs,
            blocking,
            "manifest.yaml",
            defer_until_post_preview=False,
            direction_preview_enabled=True,
        )
        self.assertTrue(
            any("early_hidden_canary_bindings" in error for error in missing_later_errors),
            missing_later_errors,
        )

        hardened = copy.deepcopy(alignment)
        hardened["early_hidden_canary_bindings"] = {
            "slice_002": {
                "case_id": "V-CANARY-001",
                "new_slice_ref": new_refs[1],
                "project_manifest_digest": "user-held-not-disclosed",
                "suite_digest": "user-held-not-disclosed",
                "question_count": 3,
                "answerable_question_count": 1,
                "boundary_question_count": 2,
                "bounded_absence_question_count": 1,
                "coverage_limitation_question_count": 1,
                "negative_case_id": "V-NEG-EARLY-001",
                "evaluation_owner": "user",
                "implementation_visibility": "hidden-until-slice-code-freeze",
                "burn_rule": "product-change-between-disclosure-and-slice-result-seal-burns-canary-and-preserves-result",
            }
        }
        hardened["early_comparison_binding"] = {
            "case_id": "V-COMP-EARLY-001",
            "canary_case_id": "V-CANARY-001",
            "new_slice_ref": new_refs[1],
            "protocol_digest_ref": "mature_source_agent_protocol_digest",
            "quality_rule": "zero-major-error-and-no-need-claim-regression",
            "positive_value_rule": "precommitted-measurable-world-model-advantage-must-pass",
            "positive_value_metric_ref": "positive_value_metric",
            "positive_value_unit_ref": "positive_value_unit",
            "positive_value_comparison_ref": "positive_value_comparison",
            "positive_value_threshold_ref": "positive_value_threshold",
            "positive_value_reuse_horizon_ref": "positive_value_reuse_horizon_questions",
            "baseline_cache_policy_digest_ref": "mature_source_agent_cache_policy_digest",
            "positive_value_protocol_digest_ref": "positive_value_protocol_digest",
            "positive_value_adjudication_owner_ref": "positive_value_adjudication_owner",
        }
        hardened["early_diagnostic_binding"] = {
            "case_id": "V-DIAG-001",
            "canary_case_id": "V-CANARY-001",
            "new_slice_ref": new_refs[1],
            "layer_chain": "source-snapshot-query-trace-draft-review-web",
        }
        self.assertEqual(
            docs_gate.validate_early_evaluation_bindings(
                hardened,
                new_refs,
                blocking,
                "manifest.yaml",
                defer_until_post_preview=False,
                direction_preview_enabled=True,
            ),
            [],
        )

        legacy_manifest = {
            "development": {
                "slices": {
                    new_refs[0]: {"status": "authorized"},
                    new_refs[1]: {"status": "proposed"},
                }
            }
        }
        self.assertEqual(
            docs_gate.required_early_evaluation_slice_refs(
                alignment, new_refs, direction_preview_enabled=False
            ),
            {new_refs[0]},
        )
        self.assertFalse(
            docs_gate.direction_preview_hardening_is_deferred(
                legacy_manifest,
                alignment,
                new_refs,
                direction_preview_enabled=False,
            )
        )
        legacy_errors = docs_gate.validate_early_evaluation_bindings(
            alignment,
            new_refs,
            blocking,
            "manifest.yaml",
            defer_until_post_preview=True,
            direction_preview_enabled=False,
        )
        self.assertTrue(
            any("early_hidden_canary_bindings" in error for error in legacy_errors),
            legacy_errors,
        )

    def test_direction_preview_does_not_exempt_contract_and_safety_readiness(
        self,
    ) -> None:
        new_refs = ["ITER-009-SLICE-001", "ITER-009-SLICE-002"]
        alignment: dict[str, object] = {
            "direction_preview_checkpoint": "V-PREVIEW-001",
            "direction_preview_binding": {
                "case_id": "V-PREVIEW-001",
                "new_slice_ref": new_refs[0],
                "real_product_entry": "loopback-product-owned-world-model-web",
                "representative_task_count": 2,
                "status_label": "non-acceptance-non-production",
                "decision_owner": "user",
                "allowed_decisions": "CONTINUE,REDIRECT,REJECT",
                "hardening_requires_continue": True,
            },
            "critical_assumption_ids": "A1",
            "critical_assumption_catalog_digest": "sha256:" + "1" * 64,
            "readiness_blocking_case_ids": [],
            "blocking_case_ids": ["V-PREVIEW-001"],
            "authorized_software_sources_digest": "sha256:" + "2" * 64,
        }
        manifest = {
            "product_goal_alignment": alignment,
            "development": {
                "slices": {
                    new_refs[0]: {"status": "authorized"},
                    new_refs[1]: {"status": "proposed"},
                }
            },
        }
        errors = docs_gate.validate_product_goal_execution_readiness(
            manifest,
            "manifest.yaml",
            "ITER-009",
            {},
            new_refs,
            None,
        )
        self.assertFalse(
            any("early_hidden_canary_bindings" in error for error in errors),
            errors,
        )
        self.assertTrue(any("source_scope must be a mapping" in error for error in errors))
        self.assertTrue(any("answer_protocol must be a mapping" in error for error in errors))
        self.assertTrue(any("readiness_inputs must be a mapping" in error for error in errors))

        hardened_manifest = copy.deepcopy(manifest)
        hardened_manifest["development"]["slices"][new_refs[0]]["status"] = (
            "completed"
        )
        hardened_manifest["development"]["slices"][new_refs[1]]["status"] = (
            "authorized"
        )
        hardened_errors = docs_gate.validate_product_goal_execution_readiness(
            hardened_manifest,
            "manifest.yaml",
            "ITER-009",
            {},
            new_refs,
            None,
        )
        self.assertTrue(
            any("positive_value_" in error for error in hardened_errors),
            hardened_errors,
        )
        self.assertTrue(
            any("early_hidden_canary_bindings" in error for error in hardened_errors),
            hardened_errors,
        )

    def test_reflection_bindings_cover_each_slice_and_distinguish_success_decisions(
        self,
    ) -> None:
        alignment, new_refs, blocking = self.valid_alignment()
        self.assertEqual(
            docs_gate.validate_reflection_gate_bindings(
                alignment, new_refs, blocking, "manifest.yaml"
            ),
            [],
        )

        missing = copy.deepcopy(alignment)
        del missing["reflection_gate_bindings"]["slice_002"]  # type: ignore[index]
        missing_errors = docs_gate.validate_reflection_gate_bindings(
            missing, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("every Slice" in error for error in missing_errors), missing_errors
        )

        wrong_decision = copy.deepcopy(alignment)
        wrong_decision["reflection_gate_bindings"]["slice_001"][  # type: ignore[index]
            "success_decision"
        ] = "ACCEPT"
        decision_errors = docs_gate.validate_reflection_gate_bindings(
            wrong_decision, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("must equal CONTINUE" in error for error in decision_errors),
            decision_errors,
        )

        non_blocking = docs_gate.validate_reflection_gate_bindings(
            alignment, new_refs, ["V-REFLECT-001"], "manifest.yaml"
        )
        self.assertTrue(
            any("blocking_case_ids" in error for error in non_blocking),
            non_blocking,
        )

        final_incomplete = copy.deepcopy(alignment)
        final_incomplete["reflection_gate_bindings"]["slice_002"][  # type: ignore[index]
            "assumption_ids"
        ] = ["A1"]
        final_errors = docs_gate.validate_reflection_gate_bindings(
            final_incomplete, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("final Slice" in error for error in final_errors), final_errors
        )

        wrong_order = copy.deepcopy(alignment)
        wrong_order["reflection_gate_bindings"]["slice_002"][  # type: ignore[index]
            "assumption_ids"
        ] = ["A2", "A1"]
        order_errors = docs_gate.validate_reflection_gate_bindings(
            wrong_order, new_refs, blocking, "manifest.yaml"
        )
        self.assertTrue(
            any("ordered subset" in error for error in order_errors), order_errors
        )

    def test_conditional_falsifier_must_be_owned_by_its_current_slice(self) -> None:
        documents, parse_errors = docs_gate.load_documents()
        self.assertEqual(parse_errors, [])
        by_id = {document.identifier: document for document in documents}
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/manifest.yaml"
        )
        manifest_text = manifest_path.read_text(encoding="utf-8")
        moved_falsifier_text = manifest_text.replace(
            "          assumption_id: A7\n          case_id: V-NEG-EARLY-001",
            "          assumption_id: A7\n          case_id: V-HARDEN-001",
        ).replace(
            "          assumption_id: A8\n          case_id: V-WEB-001",
            "          assumption_id: A8\n          case_id: V-WEB-002",
        )
        self.assertNotEqual(moved_falsifier_text, manifest_text)
        with tempfile.TemporaryDirectory() as directory:
            moved_manifest = Path(directory) / "manifest.yaml"
            moved_manifest.write_text(moved_falsifier_text, encoding="utf-8")
            ownership_errors = docs_gate.validate_product_goal_reference_targets(
                moved_manifest,
                "ITER-008",
                by_id,
            )
        self.assertTrue(
            any("conditional-falsifier" in error for error in ownership_errors),
            ownership_errors,
        )

    def test_slice_reflection_result_requires_auditable_process_and_decision(
        self,
    ) -> None:
        target = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/development-design/SLICE-001.md",
            {
                "id": "ITER-008-SLICE-001",
                "kind": "development-slice",
                "iteration": "ITER-008",
                "product_goal_slice_gate_case_ids": [
                    "V-DIAG-001",
                    "V-CANARY-001",
                    "V-REFLECT-001",
                ],
            },
            "# Slice\n",
        )
        result_body = (
            "# Result\n\n"
            "## Architecture reflection and continuation decision\n\n"
            "### Assumption verdicts\n\n"
            "| Assumption | Expected | Exact evidence refs | Verdict | Impact |\n"
            "|---|---|---|---|---|\n"
            "| A1 | query gap | V-DIAG-001 | SUPPORTED | no material deviation |\n"
            "| A2 | typed query closure | V-CANARY-001 | SUPPORTED | bounded scope |\n\n"
            "### Deviation and issue classification\n\n"
            "No material deviation; classification is none.\n\n"
            "### Layer diagnosis and mature-source-Agent comparison\n\n"
            "Every layer has exact evidence and the comparison did not regress.\n\n"
            "### Findings, alternatives and next risk\n\n"
            "Findings are dispositioned; breadth is the next risk.\n\n"
            "### Decision and rationale\n\n"
            "Decision: CONTINUE\n\n"
            "Decision owner: product-architecture-quality\n\n"
            "Decision ref: codex-user-message:sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc\n\n"
            "The frozen assumptions remain supported.\n"
        )
        result = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/results/slice-001.md",
            {
                "id": "ITER-008-RESULT-SLICE-001",
                "kind": "iteration-result",
                "iteration": "ITER-008",
                "reflection_gate_case_id": "V-REFLECT-001",
                "reflection_gate_status": "PASS",
                "reflection_decision": "CONTINUE",
                "reflection_decision_owner": "product-architecture-quality",
                "reflection_decision_ref": "codex-user-message:sha256:" + "c" * 64,
                "reflection_issue_class": "none",
                "reflection_issue_scope": "none",
                "reflection_report_digest": reflection_report_digest(result_body),
                "critical_assumption_catalog_digest": "sha256:" + "9" * 64,
            },
            result_body,
        )
        assumption_expectations = {
            "A1": "query gap",
            "A2": "typed query closure",
        }
        assumption_catalog_digest = "sha256:" + "9" * 64
        binding = {
            "case_id": "V-REFLECT-001",
            "new_slice_ref": target.identifier,
            "assumption_ids": ["A1", "A2"],
            "success_decision": "CONTINUE",
            "decision_owner": "product-architecture-quality",
        }
        manifest_slice = {"reflection_decision": "CONTINUE"}
        verification = docs_gate.Document(
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/verification-matrix.md",
            {"id": "ITER-008-VERIFICATION", "kind": "iteration-verification"},
            "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
            "|---|---|---|---|---|---|---|\n"
            "| V-DIAG-001 | diagnose | architecture / diagnostic | exact result | layer verdicts | ITER-008-RESULT-SLICE-001#V-DIAG-001 | PASS / blocking |\n"
            "| V-CANARY-001 | hidden check | product / hidden | exact result | product verdicts | ITER-008-RESULT-SLICE-001#V-CANARY-001 | PASS / blocking |\n"
            "| V-REFLECT-001 | review assumptions | architecture / reflection | exact result | explicit decision | ITER-008-RESULT-SLICE-001#V-REFLECT-001 | PASS / blocking |\n",
        )
        self.assertEqual(
            docs_gate.validate_slice_reflection_result(
                target,
                result,
                binding,
                manifest_slice,
                verification,
                "manifest.yaml",
                blocked=False,
                assumption_expectations=assumption_expectations,
                assumption_catalog_digest=assumption_catalog_digest,
            ),
            [],
        )

        blocked_supported_body = result.body.replace(
            "Decision: CONTINUE", "Decision: REDIRECT"
        )
        blocked_supported_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_decision": "REDIRECT",
                "reflection_issue_class": "architecture",
                "reflection_issue_scope": "systemic",
                "reflection_report_digest": reflection_report_digest(
                    blocked_supported_body
                ),
            },
            blocked_supported_body,
        )
        blocked_supported_errors = docs_gate.validate_slice_reflection_result(
            target,
            blocked_supported_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            verification,
            "manifest.yaml",
            blocked=True,
        )
        self.assertTrue(
            any(
                "requires at least one FALSIFIED or UNRESOLVED" in error
                for error in blocked_supported_errors
            ),
            blocked_supported_errors,
        )

        missing_decision_ref_metadata = dict(result.metadata)
        del missing_decision_ref_metadata["reflection_decision_ref"]
        missing_decision_ref = docs_gate.Document(
            result.path, missing_decision_ref_metadata, result.body
        )
        decision_ref_errors = docs_gate.validate_slice_reflection_result(
            target,
            missing_decision_ref,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("exact user message digest" in error for error in decision_ref_errors),
            decision_ref_errors,
        )

        redirect_body = result.body.replace(
            "| A1 | query gap | V-DIAG-001 | SUPPORTED | no material deviation |",
            "| A1 | query gap | V-DIAG-001 | FALSIFIED | architecture deviation |",
        ).replace("Decision: CONTINUE", "Decision: REDIRECT")
        redirect_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_decision": "REDIRECT",
                "reflection_issue_class": "architecture",
                "reflection_issue_scope": "systemic",
                "reflection_report_digest": reflection_report_digest(redirect_body),
            },
            redirect_body,
        )
        redirect_verification = docs_gate.Document(
            verification.path,
            verification.metadata,
            verification.body.replace(
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | PASS / blocking",
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | FAIL / blocking",
            ),
        )
        redirect_errors = docs_gate.validate_slice_reflection_result(
            target,
            redirect_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            redirect_verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("success_decision" in error for error in redirect_errors),
            redirect_errors,
        )
        self.assertEqual(
            docs_gate.validate_slice_reflection_result(
                target,
                redirect_result,
                binding,
                {"reflection_decision": "REDIRECT"},
                redirect_verification,
                "manifest.yaml",
                blocked=True,
                assumption_expectations=assumption_expectations,
                assumption_catalog_digest=assumption_catalog_digest,
            ),
            [],
        )

        missing_catalog_input_errors = docs_gate.validate_slice_reflection_result(
            target,
            result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("frozen assumption catalog" in error for error in missing_catalog_input_errors),
            missing_catalog_input_errors,
        )

        not_run_verification = docs_gate.Document(
            redirect_verification.path,
            redirect_verification.metadata,
            redirect_verification.body.replace(
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | FAIL / blocking",
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | NOT-RUN / blocking",
            ),
        )
        not_run_errors = docs_gate.validate_slice_reflection_result(
            target,
            redirect_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            not_run_verification,
            "manifest.yaml",
            blocked=True,
        )
        self.assertTrue(
            any("must be executed" in error for error in not_run_errors),
            not_run_errors,
        )

        conditional_target = docs_gate.Document(
            target.path,
            {
                **target.metadata,
                "product_goal_slice_gate_case_ids": [
                    *target.metadata["product_goal_slice_gate_case_ids"],
                    "V-NEG-EARLY-001",
                ],
            },
            target.body,
        )
        conditional_binding = {
            **binding,
            "conditional_falsifier_bindings": {
                "deferred_a3": {
                    "assumption_id": "A3",
                    "case_id": "V-NEG-EARLY-001",
                }
            },
        }
        conditional_verification = docs_gate.Document(
            redirect_verification.path,
            redirect_verification.metadata,
            redirect_verification.body
            + "| V-NEG-EARLY-001 | early falsifier | product / negative | exact result | stop | ITER-008-RESULT-SLICE-001#V-NEG-EARLY-001 | FAIL / blocking |\n",
        )
        conditional_errors = docs_gate.validate_slice_reflection_result(
            conditional_target,
            redirect_result,
            conditional_binding,
            {"reflection_decision": "REDIRECT"},
            conditional_verification,
            "manifest.yaml",
            blocked=True,
        )
        self.assertTrue(
            any("verdict row for A3" in error for error in conditional_errors),
            conditional_errors,
        )

        for verdict in ("FALSIFIED", "UNRESOLVED"):
            inconsistent_body = result.body.replace(
                "| A1 | query gap | V-DIAG-001 | SUPPORTED | no material deviation |",
                f"| A1 | query gap | V-DIAG-001 | {verdict} | material deviation |",
            )
            inconsistent_result = docs_gate.Document(
                result.path,
                {
                    **result.metadata,
                    "reflection_report_digest": reflection_report_digest(
                        inconsistent_body
                    ),
                },
                inconsistent_body,
            )
            inconsistent_errors = docs_gate.validate_slice_reflection_result(
                target,
                inconsistent_result,
                binding,
                manifest_slice,
                verification,
                "manifest.yaml",
                blocked=False,
            )
            self.assertTrue(
                any(
                    "requires every bound critical assumption verdict to be SUPPORTED"
                    in error
                    for error in inconsistent_errors
                ),
                inconsistent_errors,
            )

        body_mismatch_result = docs_gate.Document(
            result.path,
            {**result.metadata, "reflection_decision": "REDIRECT"},
            result.body,
        )
        body_mismatch_errors = docs_gate.validate_slice_reflection_result(
            target,
            body_mismatch_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            verification,
            "manifest.yaml",
            blocked=True,
        )
        self.assertTrue(
            any("body Decision" in error for error in body_mismatch_errors),
            body_mismatch_errors,
        )

        duplicate_decision_body = result.body.replace(
            "Findings are dispositioned; breadth is the next risk.",
            "Findings are dispositioned; breadth is the next risk.\n\n"
            "Decision: REDIRECT\n\nDecision owner: attacker",
        )
        duplicate_decision_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_report_digest": reflection_report_digest(
                    duplicate_decision_body
                ),
            },
            duplicate_decision_body,
        )
        duplicate_decision_errors = docs_gate.validate_slice_reflection_result(
            target,
            duplicate_decision_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any(
                "exact reflection section must contain exactly one Decision line"
                in error
                for error in duplicate_decision_errors
            ),
            duplicate_decision_errors,
        )
        self.assertTrue(
            any(
                "exact reflection section must contain exactly one Decision owner line"
                in error
                for error in duplicate_decision_errors
            ),
            duplicate_decision_errors,
        )

        indented_duplicate_body = result.body.replace(
            "Findings are dispositioned; breadth is the next risk.",
            "Findings are dispositioned; breadth is the next risk.\n\n"
            " Decision: REDIRECT\n\n Decision owner: attacker\n\n"
            " Decision ref: codex-user-message:sha256:"
            + "e" * 64,
        )
        indented_duplicate_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_report_digest": reflection_report_digest(
                    indented_duplicate_body
                ),
            },
            indented_duplicate_body,
        )
        indented_duplicate_errors = docs_gate.validate_slice_reflection_result(
            target,
            indented_duplicate_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("exactly one Decision line" in error for error in indented_duplicate_errors),
            indented_duplicate_errors,
        )

        duplicate_section_body = (
            result.body
            + "\n## Architecture reflection and continuation decision\n\n"
            + "Decision: REJECT\n\nDecision owner: attacker\n"
        )
        duplicate_section_result = docs_gate.Document(
            result.path,
            result.metadata,
            duplicate_section_body,
        )
        duplicate_section_errors = docs_gate.validate_slice_reflection_result(
            target,
            duplicate_section_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any(
                "exactly one Architecture reflection" in error
                for error in duplicate_section_errors
            ),
            duplicate_section_errors,
        )

        nonblocking_fail_verification = docs_gate.Document(
            redirect_verification.path,
            redirect_verification.metadata,
            redirect_verification.body.replace(
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | FAIL / blocking",
                "ITER-008-RESULT-SLICE-001#V-DIAG-001 | FAIL / not blocking",
            ),
        )
        nonblocking_fail_errors = docs_gate.validate_slice_reflection_result(
            target,
            redirect_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            nonblocking_fail_verification,
            "manifest.yaml",
            blocked=True,
        )
        self.assertTrue(
            any(
                "exact PASS, FAIL, INVALID or NOT-RUN" in error
                for error in nonblocking_fail_errors
            ),
            nonblocking_fail_errors,
        )

        self_evidence_body = result.body.replace(
            "| A1 | query gap | V-DIAG-001 | SUPPORTED | no material deviation |",
            "| A1 | query gap | V-REFLECT-001 | SUPPORTED | no material deviation |",
        )
        self_evidence_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_report_digest": reflection_report_digest(
                    self_evidence_body
                ),
            },
            self_evidence_body,
        )
        self_evidence_errors = docs_gate.validate_slice_reflection_result(
            target,
            self_evidence_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("self-evidence" in error for error in self_evidence_errors),
            self_evidence_errors,
        )

        empty_result = docs_gate.Document(result.path, result.metadata, "# Result\n")
        empty_errors = docs_gate.validate_slice_reflection_result(
            target,
            empty_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("substantive" in error for error in empty_errors), empty_errors
        )

        missing_subsection_result = docs_gate.Document(
            result.path,
            result.metadata,
            result.body.replace(
                "### Findings, alternatives and next risk",
                "### Unstructured notes",
            ),
        )
        subsection_errors = docs_gate.validate_slice_reflection_result(
            target,
            missing_subsection_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("reflection subsection" in error for error in subsection_errors),
            subsection_errors,
        )

        missing_assumption_result = docs_gate.Document(
            result.path,
            result.metadata,
            result.body.replace(
                "| A2 | typed query closure | V-CANARY-001 | SUPPORTED | bounded scope |\n",
                "",
            ),
        )
        assumption_errors = docs_gate.validate_slice_reflection_result(
            target,
            missing_assumption_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("verdict row for A2" in error for error in assumption_errors),
            assumption_errors,
        )

        outside_only_body = result.body.replace(
            "# Result\n\n",
            "# Result\n\n"
            "| A2 | typed query closure | V-CANARY-001 | SUPPORTED | forged outside reflection |\n\n",
        ).replace(
            "| A2 | typed query closure | V-CANARY-001 | SUPPORTED | bounded scope |\n",
            "",
        )
        outside_only_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_report_digest": reflection_report_digest(
                    outside_only_body
                ),
            },
            outside_only_body,
        )
        outside_only_errors = docs_gate.validate_slice_reflection_result(
            target,
            outside_only_result,
            binding,
            manifest_slice,
            verification,
            "manifest.yaml",
            blocked=False,
        )
        self.assertTrue(
            any("verdict row for A2" in error for error in outside_only_errors),
            outside_only_errors,
        )

    def test_critical_assumption_catalog_is_exact_resolved_and_unique(self) -> None:
        path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-008/proposal.md"
        )
        body = (
            "# Proposal\n\n"
            "## Critical assumptions and falsification plan\n\n"
            "| Assumption | Earliest falsifier | Action |\n"
            "|---|---|---|\n"
            "| A1: typed queries close the answer | V-DIAG-001 | redirect query architecture |\n"
        )
        proposal = docs_gate.Document(
            path,
            {"id": "ITER-008-PROPOSAL", "iteration": "ITER-008"},
            body,
        )
        digest, expectations, errors = docs_gate.critical_assumption_catalog(
            proposal
        )
        self.assertEqual(errors, [])
        self.assertRegex(str(digest), r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(
            expectations, {"A1": "typed queries close the answer"}
        )

        duplicate = docs_gate.Document(
            path,
            proposal.metadata,
            body
            + "\n## Critical assumptions and falsification plan\n\n"
            + "| A1: attacker rewrite | V-X | accept |\n",
        )
        _, _, duplicate_errors = docs_gate.critical_assumption_catalog(duplicate)
        self.assertTrue(
            any("exactly one" in error for error in duplicate_errors),
            duplicate_errors,
        )

        unresolved = docs_gate.Document(
            path,
            proposal.metadata,
            body.replace("V-DIAG-001", "pending"),
        )
        _, _, unresolved_errors = docs_gate.critical_assumption_catalog(unresolved)
        self.assertTrue(
            any("resolved three-column" in error for error in unresolved_errors),
            unresolved_errors,
        )

        malformed = docs_gate.Document(
            path,
            proposal.metadata,
            body
            + "| A2 | V-CANARY-001 | continue after rewriting the assumption |\n",
        )
        _, _, malformed_errors = docs_gate.critical_assumption_catalog(malformed)
        self.assertTrue(
            any("malformed critical assumption row" in error for error in malformed_errors),
            malformed_errors,
        )

        invalid_readiness = docs_gate.Document(
            path.parent / "readiness-review.md",
            {
                "id": "ITER-008-READINESS",
                "authorized_by": "user",
                "authorized_at": "2026-99-99T99:99:99+09:00",
                "product_goal_alignment_verdict": "accepted",
                "product_goal_alignment_reviewed_by": "user",
                "product_goal_alignment_review_ref": (
                    "codex-user-message:sha256:" + "8" * 64
                ),
            },
            "# Readiness\n",
        )
        invalid_readiness_errors = (
            docs_gate.validate_product_goal_readiness_authorization(
                invalid_readiness
            )
        )
        self.assertTrue(
            any("real ISO-8601" in error for error in invalid_readiness_errors),
            invalid_readiness_errors,
        )

    def test_proposed_reflection_gate_fails_closed_for_invalid_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            iteration_directory = (
                repository / "docs/project/iterations/iteration-008"
            )
            iteration_directory.mkdir(parents=True)
            proposal = docs_gate.Document(
                iteration_directory / "proposal.md",
                {
                    "id": "ITER-008-PROPOSAL",
                    "kind": "iteration-proposal",
                    "status": "proposed",
                    "iteration": "ITER-008",
                    "depends_on": ["SYS-PRODUCT-SUCCESS"],
                },
                "# Proposal\n\n"
                "## Critical assumptions and falsification plan\n\n"
                "| Assumption | Earliest falsifier | Action |\n"
                "|---|---|---|\n"
                "| A1: first assumption | V-PRE-001 | redirect first risk |\n"
                "| A2: second assumption | V-PRE-002 | reject second risk |\n",
            )
            verification = product_goal_verification(
                iteration_directory / "verification-matrix.md"
            )
            verification = docs_gate.Document(
                verification.path,
                {
                    **verification.metadata,
                    "id": "ITER-008-VERIFICATION",
                    "iteration": "ITER-008",
                },
                verification.body,
            )
            manifest = iteration_directory / "manifest.yaml"
            manifest.write_text("product_goal_alignment: [\n", encoding="utf-8")

            with patch.object(docs_gate, "REPOSITORY", repository):
                invalid_yaml_errors = docs_gate.validate_product_goal_alignment_state(
                    [proposal, verification]
                )
                manifest.write_text("schema_version: 1\n", encoding="utf-8")
                missing_alignment_errors = (
                    docs_gate.validate_product_goal_alignment_state(
                        [proposal, verification]
                    )
                )
                manifest.write_text(
                    "schema_version: 1\n"
                    "iteration:\n"
                    "  id: ITER-008\n"
                    "  status: proposed\n"
                    "product_goal_alignment:\n"
                    "  target_ref: SYS-PRODUCT-SUCCESS\n"
                    "  critical_assumption_ids: A1\n"
                    "  critical_assumption_catalog_digest: not-frozen-proposal-only\n",
                    encoding="utf-8",
                )
                mismatched_catalog_errors = (
                    docs_gate.validate_product_goal_alignment_state(
                        [proposal, verification]
                    )
                )

        self.assertTrue(
            any("cannot be loaded" in error for error in invalid_yaml_errors),
            invalid_yaml_errors,
        )
        self.assertTrue(
            any("product_goal_alignment must be a mapping" in error for error in missing_alignment_errors),
            missing_alignment_errors,
        )
        self.assertTrue(
            any(
                "critical_assumption_ids must exactly match" in error
                for error in mismatched_catalog_errors
            ),
            mismatched_catalog_errors,
        )

    def test_follow_up_slice_requires_exact_prior_reflection_result_dependency(
        self,
    ) -> None:
        iteration_directory = (
            docs_gate.REPOSITORY / "docs/project/iterations/iteration-008"
        )
        proposal = docs_gate.Document(
            iteration_directory / "proposal.md",
            {
                "id": "ITER-008-PROPOSAL",
                "kind": "iteration-proposal",
                "status": "accepted",
                "iteration": "ITER-008",
            },
            "# Proposal\n\n"
            "## Critical assumptions and falsification plan\n\n"
            "| Assumption | Earliest falsifier | Action |\n"
            "|---|---|---|\n"
            "| A1: query closes | V-DIAG-001 in Slice 1 | redirect the query architecture |\n",
        )
        catalog_digest, catalog_expectations, catalog_errors = (
            docs_gate.critical_assumption_catalog(proposal)
        )
        self.assertEqual(catalog_errors, [])
        self.assertEqual(catalog_expectations, {"A1": "query closes"})
        first = docs_gate.Document(
            iteration_directory / "development-design/SLICE-001.md",
            {
                "id": "ITER-008-SLICE-001",
                "kind": "development-slice",
                "status": "completed",
                "authority": "historical-development",
                "coding_input": False,
                "iteration": "ITER-008",
                "depends_on": ["ITER-008-PROPOSAL"],
                "product_goal_slice_gate_case_ids": [
                    "V-DIAG-001",
                    "V-COMP-EARLY-001",
                    "V-REFLECT-001",
                ],
            },
            "# Slice\n",
        )
        reflection_body = (
            "# Result\n\n"
            "## Architecture reflection and continuation decision\n\n"
            "### Assumption verdicts\n\n"
            "| Assumption | Expected | Exact evidence refs | Verdict | Impact |\n"
            "|---|---|---|---|---|\n"
            "| A1 | query closes | V-DIAG-001 | SUPPORTED | bounded evidence |\n\n"
            "### Deviation and issue classification\n\nNo deviation.\n\n"
            "### Layer diagnosis and mature-source-Agent comparison\n\nAll layers and the baseline agree.\n\n"
            "### Findings, alternatives and next risk\n\nFindings closed; breadth remains.\n\n"
            "### Decision and rationale\n\nDecision: CONTINUE\n\n"
            "Decision owner: product-architecture-quality\n\n"
            "Decision ref: codex-user-message:sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd\n\n"
            "The evidence supports continuation.\n"
        )
        result_id = "ITER-008-RESULT-SLICE-001"
        value_metadata = {
            "positive_value_verdict": "PASS",
            "positive_value_metric": "normalized-reuse-cost",
            "positive_value_unit": "basis-points",
            "positive_value_comparison": "at-most",
            "positive_value_threshold": 8000,
            "positive_value_actual": 7500,
            "positive_value_reuse_horizon_questions": 3,
            "mature_source_agent_protocol_digest": "sha256:" + "1" * 64,
            "mature_source_agent_rubric_digest": "sha256:" + "2" * 64,
            "mature_source_agent_cache_policy_digest": "sha256:" + "3" * 64,
            "positive_value_protocol_digest": "sha256:" + "4" * 64,
            "positive_value_freeze_receipt_ref": "codex-user-message:sha256:"
            + "6" * 64,
            "positive_value_case_id": "V-COMP-EARLY-001",
            "positive_value_report_ref": f"{result_id}#positive-value-report",
            "positive_value_adjudication_owner": "user",
            "positive_value_adjudication_receipt_ref": (
                "codex-user-message:sha256:" + "7" * 64
            ),
        }
        value_section, value_digest = positive_value_report_section(
            value_metadata, result_id, "V-COMP-EARLY-001"
        )
        result_body = reflection_body + "\n" + value_section + "\n"
        result = docs_gate.Document(
            iteration_directory / "results/slice-001.md",
            {
                "id": result_id,
                "kind": "iteration-result",
                "status": "accepted",
                "authority": "execution-evidence",
                "iteration": "ITER-008",
                "depends_on": [first.identifier, "ITER-008-VERIFICATION"],
                "product_code_freeze_digest": "sha256:" + "1" * 64,
                "reflection_gate_case_id": "V-REFLECT-001",
                "reflection_gate_status": "PASS",
                "reflection_decision": "CONTINUE",
                "reflection_decision_owner": "product-architecture-quality",
                "reflection_decision_ref": "codex-user-message:sha256:" + "d" * 64,
                "reflection_issue_class": "none",
                "reflection_issue_scope": "none",
                "reflection_report_digest": reflection_report_digest(result_body),
                "critical_assumption_catalog_digest": catalog_digest,
                **value_metadata,
                "positive_value_report_digest": value_digest,
            },
            result_body,
        )
        second = docs_gate.Document(
            iteration_directory / "development-design/SLICE-002.md",
            {
                "id": "ITER-008-SLICE-002",
                "kind": "development-slice",
                "status": "authorized",
                "authority": "current-development",
                "coding_input": True,
                "iteration": "ITER-008",
                "depends_on": [
                    "ITER-008-PROPOSAL",
                    first.identifier,
                    result.identifier,
                ],
                "product_goal_slice_gate_case_ids": ["V-REFLECT-002"],
            },
            "# Slice\n",
        )
        verification = docs_gate.Document(
            iteration_directory / "verification-matrix.md",
            {"id": "ITER-008-VERIFICATION", "kind": "iteration-verification"},
            "| Case | Claim | Level | Frozen input / oracle | Expected | Evidence | Status / blocking meaning |\n"
            "|---|---|---|---|---|---|---|\n"
            f"| V-DIAG-001 | diagnose | architecture / diagnostic | exact result | layer verdicts | {result.identifier}#V-DIAG-001 | PASS / blocking |\n"
            f"| V-COMP-EARLY-001 | compare | product / early comparison | exact result | value verdict | {result.identifier}#V-COMP-EARLY-001 | PASS / blocking |\n"
            f"| V-REFLECT-001 | review | architecture / reflection | exact result | decision | {result.identifier}#V-REFLECT-001 | PASS / blocking |\n",
        )
        binding_owner = "product-architecture-quality"
        manifest = {
            "authorization": {"active_slice": second.identifier},
            "product_goal_alignment": {
                "critical_assumption_ids": ["A1"],
                "critical_assumption_catalog_digest": catalog_digest,
                "positive_value_metric": "normalized-reuse-cost",
                "positive_value_unit": "basis-points",
                "positive_value_comparison": "at-most",
                "positive_value_threshold": 8000,
                "positive_value_reuse_horizon_questions": 3,
                "mature_source_agent_protocol_digest": "sha256:" + "1" * 64,
                "mature_source_agent_rubric_digest": "sha256:" + "2" * 64,
                "mature_source_agent_cache_policy_digest": "sha256:" + "3" * 64,
                "positive_value_protocol_digest": "sha256:" + "4" * 64,
                "positive_value_freeze_receipt_ref": "codex-user-message:sha256:"
                + "6" * 64,
                "positive_value_adjudication_owner": "user",
                "early_comparison_binding": {
                    "case_id": "V-COMP-EARLY-001",
                    "new_slice_ref": first.identifier,
                },
                "reflection_gate_bindings": {
                    "slice_001": {
                        "case_id": "V-REFLECT-001",
                        "new_slice_ref": first.identifier,
                        "assumption_ids": ["A1"],
                        "success_decision": "CONTINUE",
                        "decision_owner": binding_owner,
                    },
                    "slice_002": {
                        "case_id": "V-REFLECT-002",
                        "new_slice_ref": second.identifier,
                        "assumption_ids": ["A1"],
                        "success_decision": "ACCEPT",
                        "decision_owner": binding_owner,
                    },
                },
            },
            "development": {
                "slices": {
                    first.identifier: {
                        "status": "completed",
                        "coding_input": False,
                        "result": result.identifier,
                        "reflection_decision": "CONTINUE",
                        "reflection_prerequisite_result": "none-first-slice",
                        "product_code_freeze_digest": "sha256:" + "1" * 64,
                        "authorized_by": "user",
                        "authorized_at": "2026-08-14T10:00:00+08:00",
                        "authorization_ref": "codex-user-message:sha256:" + "a" * 64,
                    },
                    second.identifier: {
                        "status": "authorized",
                        "coding_input": True,
                        "result": "not-executed",
                        "reflection_decision": "not-executed",
                        "reflection_prerequisite_result": result.identifier,
                        "product_code_freeze_digest": "not-executed",
                        "authorized_by": "user",
                        "authorized_at": "2026-08-14T11:00:00+08:00",
                        "authorization_ref": "codex-user-message:sha256:" + "d" * 64,
                    },
                }
            },
        }
        by_id = {
            item.identifier: item for item in (proposal, first, second, result)
        }
        self.assertEqual(
            docs_gate.validate_product_goal_slice_sequence(
                [first.identifier, second.identifier],
                by_id,
                "manifest.yaml",
                manifest=manifest,
                verification=verification,
            ),
            [],
        )

        changed_proposal = docs_gate.Document(
            proposal.path,
            proposal.metadata,
            proposal.body.replace(
                "A1: query closes", "A1: query may be inferred after the run"
            ),
        )
        changed_catalog_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            {**by_id, proposal.identifier: changed_proposal},
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(
            any(
                "critical_assumption_catalog_digest" in error
                for error in changed_catalog_errors
            ),
            changed_catalog_errors,
        )
        self.assertTrue(
            any("Expected must exactly match" in error for error in changed_catalog_errors),
            changed_catalog_errors,
        )

        reversed_time_manifest = copy.deepcopy(manifest)
        reversed_time_manifest["development"]["slices"][  # type: ignore[index]
            second.identifier
        ]["authorized_at"] = "2026-08-14T09:00:00+08:00"
        reversed_time_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            by_id,
            "manifest.yaml",
            manifest=reversed_time_manifest,
            verification=verification,
        )
        self.assertTrue(
            any("strictly increasing" in error for error in reversed_time_errors),
            reversed_time_errors,
        )

        invalid_time_manifest = copy.deepcopy(manifest)
        invalid_time_manifest["development"]["slices"][  # type: ignore[index]
            second.identifier
        ]["authorized_at"] = "2026-99-99T99:99:99+09:00"
        invalid_time_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            by_id,
            "manifest.yaml",
            manifest=invalid_time_manifest,
            verification=verification,
        )
        self.assertTrue(
            any("real ISO-8601" in error for error in invalid_time_errors),
            invalid_time_errors,
        )

        freeze_receipt = str(value_metadata["positive_value_freeze_receipt_ref"])
        freeze_decision_body = result.body.replace(
            "Decision ref: codex-user-message:sha256:" + "d" * 64,
            "Decision ref: " + freeze_receipt,
        )
        freeze_decision_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_decision_ref": freeze_receipt,
                "reflection_report_digest": reflection_report_digest(
                    freeze_decision_body
                ),
            },
            freeze_decision_body,
        )
        freeze_decision_manifest = copy.deepcopy(manifest)
        freeze_decision_manifest["development"]["slices"][  # type: ignore[index]
            second.identifier
        ]["authorization_ref"] = freeze_receipt
        freeze_decision_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            {**by_id, result.identifier: freeze_decision_result},
            "manifest.yaml",
            manifest=freeze_decision_manifest,
            verification=verification,
        )
        self.assertTrue(
            any(
                "reflection_decision_ref must use a new user message" in error
                for error in freeze_decision_errors
            ),
            freeze_decision_errors,
        )

        reused_readiness_receipt_manifest = copy.deepcopy(manifest)
        reused_readiness_receipt_manifest["authorization"][  # type: ignore[index]
            "authorization_ref"
        ] = result.metadata["reflection_decision_ref"]
        reused_readiness_receipt_errors = (
            docs_gate.validate_product_goal_slice_sequence(
                [first.identifier, second.identifier],
                by_id,
                "manifest.yaml",
                manifest=reused_readiness_receipt_manifest,
                verification=verification,
            )
        )
        self.assertTrue(
            any(
                "new user message after all prior authorizations" in error
                for error in reused_readiness_receipt_errors
            ),
            reused_readiness_receipt_errors,
        )

        reused_adjudication_metadata = {
            **value_metadata,
            "positive_value_adjudication_receipt_ref": (
                "codex-user-message:sha256:" + "a" * 64
            ),
        }
        reused_adjudication_section, reused_adjudication_digest = (
            positive_value_report_section(
                reused_adjudication_metadata,
                result_id,
                "V-COMP-EARLY-001",
            )
        )
        reused_adjudication_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                **reused_adjudication_metadata,
                "positive_value_report_digest": reused_adjudication_digest,
            },
            reflection_body + "\n" + reused_adjudication_section + "\n",
        )
        reused_adjudication_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            {**by_id, result.identifier: reused_adjudication_result},
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(
            any(
                "positive value adjudication must use a new message" in error
                for error in reused_adjudication_errors
            ),
            reused_adjudication_errors,
        )

        completed_second = docs_gate.Document(
            second.path,
            {
                **second.metadata,
                "status": "completed",
                "authority": "historical-development",
                "coding_input": False,
            },
            second.body,
        )
        final_reflection_body = (
            "# Result\n\n"
            "## Architecture reflection and continuation decision\n\n"
            "### Assumption verdicts\n\n"
            "| Assumption | Expected | Exact evidence refs | Verdict | Impact |\n"
            "|---|---|---|---|---|\n"
            "| A1 | query closes | V-FINAL-001 | SUPPORTED | bounded evidence |\n\n"
            "### Deviation and issue classification\n\nNo deviation.\n\n"
            "### Layer diagnosis and mature-source-Agent comparison\n\n"
            "All layers and the baseline agree.\n\n"
            "### Findings, alternatives and next risk\n\n"
            "Findings closed; breadth remains.\n\n"
            "### Decision and rationale\n\nDecision: ACCEPT\n\n"
            "Decision owner: product-architecture-quality\n\n"
            "Decision ref: codex-user-message:sha256:"
            + "d" * 64
            + "\n\nThe final evidence supports acceptance.\n"
        )
        final_result = docs_gate.Document(
            iteration_directory / "results/slice-002.md",
            {
                "id": "ITER-008-RESULT-SLICE-002",
                "kind": "iteration-result",
                "status": "accepted",
                "authority": "execution-evidence",
                "iteration": "ITER-008",
                "depends_on": [
                    completed_second.identifier,
                    "ITER-008-VERIFICATION",
                ],
                "product_code_freeze_digest": "sha256:" + "2" * 64,
                "reflection_gate_case_id": "V-REFLECT-002",
                "reflection_gate_status": "PASS",
                "reflection_decision": "ACCEPT",
                "reflection_decision_owner": "product-architecture-quality",
                "reflection_decision_ref": "codex-user-message:sha256:"
                + "d" * 64,
                "reflection_issue_class": "none",
                "reflection_issue_scope": "none",
                "reflection_report_digest": reflection_report_digest(
                    final_reflection_body
                ),
                "critical_assumption_catalog_digest": catalog_digest,
            },
            final_reflection_body,
        )
        completed_verification = docs_gate.Document(
            verification.path,
            verification.metadata,
            verification.body
            + f"| V-FINAL-001 | final | product / hidden | exact result | answer | {final_result.identifier}#V-FINAL-001 | PASS / blocking |\n"
            + f"| V-REFLECT-002 | review | architecture / reflection | exact result | decision | {final_result.identifier}#V-REFLECT-002 | PASS / blocking |\n",
        )
        completed_manifest = copy.deepcopy(manifest)
        completed_manifest["authorization"]["active_slice"] = "none"  # type: ignore[index]
        completed_manifest["development"]["slices"][  # type: ignore[index]
            second.identifier
        ].update(
            {
                "status": "completed",
                "coding_input": False,
                "result": final_result.identifier,
                "reflection_decision": "ACCEPT",
                "product_code_freeze_digest": "sha256:" + "2" * 64,
            }
        )
        duplicate_final_decision_errors = (
            docs_gate.validate_product_goal_slice_sequence(
                [first.identifier, second.identifier],
                {
                    proposal.identifier: proposal,
                    first.identifier: first,
                    second.identifier: completed_second,
                    result.identifier: result,
                    final_result.identifier: final_result,
                },
                "manifest.yaml",
                manifest=completed_manifest,
                verification=completed_verification,
                require_completed=True,
            )
        )
        self.assertTrue(
            any(
                "reflection_decision_ref must be unique" in error
                or "new user message after all prior authorizations" in error
                for error in duplicate_final_decision_errors
            ),
            duplicate_final_decision_errors,
        )

        missed_early_value = docs_gate.Document(
            result.path,
            {**result.metadata, "positive_value_actual": 8001},
            result.body,
        )
        missed_early_value_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            {**by_id, result.identifier: missed_early_value},
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(
            any(
                "positive_value_actual does not satisfy" in error
                for error in missed_early_value_errors
            ),
            missed_early_value_errors,
        )

        without_result_dependency = docs_gate.Document(
            second.path,
            {
                **second.metadata,
                "depends_on": ["ITER-008-PROPOSAL", first.identifier],
            },
            second.body,
        )
        dependency_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            {**by_id, second.identifier: without_result_dependency},
            "manifest.yaml",
            manifest=manifest,
            verification=verification,
        )
        self.assertTrue(
            any("prior reflection Result" in error for error in dependency_errors),
            dependency_errors,
        )

        reused_authorization_manifest = copy.deepcopy(manifest)
        reused_authorization_manifest["development"]["slices"][  # type: ignore[index]
            second.identifier
        ]["authorization_ref"] = "codex-user-message:sha256:" + "a" * 64
        reused_authorization_errors = docs_gate.validate_product_goal_slice_sequence(
            [first.identifier, second.identifier],
            by_id,
            "manifest.yaml",
            manifest=reused_authorization_manifest,
            verification=verification,
        )
        self.assertTrue(
            any(
                "new user authorization message" in error
                for error in reused_authorization_errors
            ),
            reused_authorization_errors,
        )


class ReworkPlanningGateTests(unittest.TestCase):
    def _documents(self) -> tuple[list[docs_gate.Document], dict[str, docs_gate.Document]]:
        documents, parse_errors = docs_gate.load_documents()
        self.assertEqual(parse_errors, [])
        return documents, {document.identifier: document for document in documents}

    def _assert_lightweight_verification_mutations_rejected(
        self,
        case_id: str,
        mutations: tuple[tuple[str, str, str], ...],
    ) -> None:
        _, by_id = self._documents()
        verification = by_id["ITER-010-VERIFICATION"]
        for field_name, original, replacement in mutations:
            with self.subTest(case_id=case_id, field=field_name):
                lines = verification.body.splitlines(keepends=True)
                matching_indexes = [
                    index
                    for index, line in enumerate(lines)
                    if line.startswith(f"| {case_id} |")
                ]
                self.assertEqual(len(matching_indexes), 1)
                row_index = matching_indexes[0]
                self.assertIn(original, lines[row_index])
                lines[row_index] = lines[row_index].replace(
                    original, replacement, 1
                )
                tampered = docs_gate.Document(
                    verification.path,
                    verification.metadata,
                    "".join(lines),
                )
                errors = docs_gate.validate_iter010_lightweight_verification_semantics(
                    tampered
                )
                self.assertTrue(
                    any(
                        case_id in error
                        and field_name in error
                        and "lightweight-plan phrase" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_file_backed_rework_authorization_history_is_materialized(self) -> None:
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        manifest_text = manifest_path.read_text(encoding="utf-8")

        self.assertEqual(
            docs_gate.manifest_resolved_nested_sequence_items(
                manifest_text,
                (
                    "development",
                    "slices",
                    "ITER-010-SLICE-001",
                    "prior_authorization_refs",
                ),
            ),
            [
                "codex-user-message:sha256:"
                "585f02c4edcf25502b40f880c17a7bdf7f1af71044cd8d1bbe97b055a735ee9e"
            ],
        )

    def test_conversational_cutover_marks_every_fixed_role_section_legacy(
        self,
    ) -> None:
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = docs_gate.safe_load_manifest(
            manifest_text
        )
        self.assertEqual(
            docs_gate.validate_conversational_architecture_cutover(
                manifest, "manifest.yaml", manifest_text=manifest_text
            ),
            [],
        )
        for section_name in (
            "hybrid_evidence_path",
            "reviewer_verification_investigation",
            "answer_hierarchy_protocol",
            "answer_protocol",
        ):
            tampered = copy.deepcopy(manifest)
            tampered[section_name]["protocol_role"] = "current"
            errors = docs_gate.validate_conversational_architecture_cutover(
                tampered, "manifest.yaml", manifest_text=manifest_text
            )
            self.assertTrue(
                any(section_name in error for error in errors),
                (section_name, errors),
            )

    def test_current_readiness_acceptance_is_bound_to_active_authorization(
        self,
    ) -> None:
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = docs_gate.safe_load_manifest(
            manifest_text
        )
        self.assertEqual(
            docs_gate.validate_conversational_architecture_cutover(
                manifest, "manifest.yaml", manifest_text=manifest_text
            ),
            [],
        )

        stale = copy.deepcopy(manifest)
        stale["readiness_inputs"][  # type: ignore[index]
            "current_readiness_status"
        ] = "refresh-required-not-accepted"
        for field in (
            "current_readiness_acceptance_ref",
            "current_readiness_accepted_at",
            "current_readiness_planning_commit",
            "current_readiness_planning_tree",
        ):
            stale["readiness_inputs"].pop(field, None)  # type: ignore[index]
        stale_errors = docs_gate.validate_conversational_architecture_cutover(
            stale, "manifest.yaml"
        )
        self.assertTrue(
            any("paused non-coding iteration" in error for error in stale_errors),
            stale_errors,
        )

        mismatched_receipt = copy.deepcopy(manifest)
        mismatched_receipt["rework"][  # type: ignore[index]
            "authorization_ref"
        ] = "codex-user-message:sha256:" + "0" * 64
        receipt_errors = docs_gate.validate_conversational_architecture_cutover(
            mismatched_receipt, "manifest.yaml"
        )
        self.assertTrue(
            any("active rework authorization" in error for error in receipt_errors),
            receipt_errors,
        )

        mismatched_current_reauthorization = copy.deepcopy(manifest)
        mismatched_current_reauthorization["rework"][  # type: ignore[index]
            "current_reauthorization_ref"
        ] = "codex-user-message:sha256:" + "1" * 64
        current_reauthorization_errors = (
            docs_gate.validate_conversational_architecture_cutover(
                mismatched_current_reauthorization, "manifest.yaml"
            )
        )
        self.assertTrue(
            any(
                "active rework authorization" in error
                for error in current_reauthorization_errors
            ),
            current_reauthorization_errors,
        )

        mismatched_planning = copy.deepcopy(manifest)
        mismatched_planning["readiness_inputs"][  # type: ignore[index]
            "current_readiness_planning_tree"
        ] = "0" * 40
        planning_errors = docs_gate.validate_conversational_architecture_cutover(
            mismatched_planning, "manifest.yaml"
        )
        self.assertTrue(
            any("planning identity" in error for error in planning_errors),
            planning_errors,
        )

        shifted_timestamp = copy.deepcopy(manifest)
        other_timestamp = "2026-08-25T05:06:08Z"
        shifted_timestamp["readiness_inputs"][  # type: ignore[index]
            "current_readiness_accepted_at"
        ] = other_timestamp
        shifted_timestamp["rework"]["authorized_at"] = other_timestamp  # type: ignore[index]
        shifted_timestamp["authorization"][  # type: ignore[index]
            "authorized_at"
        ] = other_timestamp
        shifted_timestamp["development"]["slices"][  # type: ignore[index]
            "ITER-010-SLICE-001"
        ]["authorized_at"] = other_timestamp
        timestamp_errors = docs_gate.validate_conversational_architecture_cutover(
            shifted_timestamp, "manifest.yaml", manifest_text=manifest_text
        )
        self.assertTrue(
            any(
                "exact current PDR-004 activation timestamp" in error
                for error in timestamp_errors
            ),
            timestamp_errors,
        )

        shifted_planning = copy.deepcopy(manifest)
        other_commit = "a" * 40
        other_tree = "b" * 40
        shifted_planning["readiness_inputs"][  # type: ignore[index]
            "current_readiness_planning_commit"
        ] = other_commit
        shifted_planning["readiness_inputs"][  # type: ignore[index]
            "current_readiness_planning_tree"
        ] = other_tree
        shifted_planning["baseline"]["planning_commit"] = other_commit  # type: ignore[index]
        shifted_planning["baseline"]["planning_tree"] = other_tree  # type: ignore[index]
        shifted_planning_errors = (
            docs_gate.validate_conversational_architecture_cutover(
                shifted_planning, "manifest.yaml", manifest_text=manifest_text
            )
        )
        self.assertTrue(
            any(
                "exact PDR-004 planning commit/tree" in error
                for error in shifted_planning_errors
            ),
            shifted_planning_errors,
        )

        prior_design_receipts = docs_gate.manifest_resolved_sequence_items(
            manifest_text,
            "authorization",
            "prior_design_authorization_refs",
        )
        self.assertIsNotNone(prior_design_receipts)
        historical_direction_receipts = (
            "codex-user-message:sha256:"
            "2f8b92d817ae111401eaaad959a5f786dd3a289763d9b258b38f5a12efd66a90",
            "codex-user-message:sha256:"
            "f164d65a815c67b86d427ee8057f41b20d47bbbd0e8febec8ec1e02c28448068",
        )
        old_receipts = (
            manifest["rework"]["prior_rework_authorization_ref"],  # type: ignore[index]
            manifest["authorization"]["planning_request_ref"],  # type: ignore[index]
            manifest["product_goal_alignment"][  # type: ignore[index]
                "positive_value_freeze_receipt_ref"
            ],
            *(prior_design_receipts or []),
            *historical_direction_receipts,
        )
        for old_receipt in old_receipts:
            reused_receipt = copy.deepcopy(manifest)
            reused_receipt["readiness_inputs"][  # type: ignore[index]
                "current_readiness_acceptance_ref"
            ] = old_receipt
            for section_name, field in (
                ("rework", "current_reauthorization_ref"),
                ("rework", "authorization_ref"),
                ("authorization", "authorization_ref"),
            ):
                reused_receipt[section_name][field] = old_receipt  # type: ignore[index]
            reused_receipt["development"]["slices"][  # type: ignore[index]
                "ITER-010-SLICE-001"
            ]["authorization_ref"] = old_receipt
            reused_errors = docs_gate.validate_conversational_architecture_cutover(
                reused_receipt,
                "manifest.yaml",
                manifest_text=manifest_text,
            )
            self.assertTrue(
                any(
                    "must not reuse" in error or "receipt must be new" in error
                    or "exact current PDR-004 activation receipt" in error
                    for error in reused_errors
                ),
                (old_receipt, reused_errors),
            )

        external_authorized = copy.deepcopy(manifest)
        external_authorized["authorization"][  # type: ignore[index]
            "external_execution_authorization_status"
        ] = "authorized"
        external_errors = docs_gate.validate_conversational_architecture_cutover(
            external_authorized, "manifest.yaml"
        )
        self.assertTrue(
            any(
                "no active external authority" in error
                for error in external_errors
            ),
            external_errors,
        )

        missing_consumed_receipt = copy.deepcopy(manifest)
        missing_consumed_receipt["authorization"][  # type: ignore[index]
            "consumed_live_session_authorization_history"
        ].pop(
            "first_live_session_authorization"
        )
        missing_consumed_errors = (
            docs_gate.validate_conversational_architecture_cutover(
                missing_consumed_receipt, "manifest.yaml"
            )
        )
        self.assertTrue(
            any("retain its exact receipt" in error for error in missing_consumed_errors),
            missing_consumed_errors,
        )

        reactivated_consumed_grant = copy.deepcopy(manifest)
        reactivated_consumed_grant["authorization"][  # type: ignore[index]
            "consumed_live_session_authorization_history"
        ]["first_live_session_authorization"]["status"] = "active"
        reactivated_consumed_errors = (
            docs_gate.validate_conversational_architecture_cutover(
                reactivated_consumed_grant, "manifest.yaml"
            )
        )
        self.assertTrue(
            any(
                "remain exact, excluded and evidence-bound" in error
                for error in reactivated_consumed_errors
            ),
            reactivated_consumed_errors,
        )

        docs_sync_expanded = copy.deepcopy(manifest)
        docs_sync_expanded["authorization"][  # type: ignore[index]
            "docs_sync_authorizes_product_code"
        ] = True
        docs_sync_errors = docs_gate.validate_conversational_architecture_cutover(
            docs_sync_expanded, "manifest.yaml"
        )
        self.assertTrue(
            any("docs-only synchronization" in error for error in docs_sync_errors),
            docs_sync_errors,
        )

        expanded_scope = copy.deepcopy(manifest)
        expanded_scope["authorization"][  # type: ignore[index]
            "development_authorization_scope"
        ] = "all"
        scope_errors = docs_gate.validate_conversational_architecture_cutover(
            expanded_scope, "manifest.yaml"
        )
        self.assertTrue(
            any("local deterministic verification" in error for error in scope_errors),
            scope_errors,
        )

        live_authorized = copy.deepcopy(manifest)
        live_authorized["development"]["slices"][  # type: ignore[index]
            "ITER-010-SLICE-001"
        ]["live_question_status"] = "authorized"
        live_errors = docs_gate.validate_conversational_architecture_cutover(
            live_authorized, "manifest.yaml"
        )
        self.assertTrue(
            any("consumed failed conversational live canary" in error for error in live_errors),
            live_errors,
        )

        later_slice_authorized = copy.deepcopy(manifest)
        later_slice_authorized["development"]["slices"][  # type: ignore[index]
            "ITER-010-SLICE-002"
        ]["status"] = "authorized"
        later_slice_errors = (
            docs_gate.validate_conversational_architecture_cutover(
                later_slice_authorized, "manifest.yaml"
            )
        )
        self.assertTrue(
            any(
                "must not authorize ITER-010-SLICE-002" in error
                for error in later_slice_errors
            ),
            later_slice_errors,
        )

        reactivated_root_grant = copy.deepcopy(manifest)
        reactivated_root_grant["authorization"][  # type: ignore[index]
            "slice1_needed_rights_root_authorization"
        ]["status"] = "active"
        root_grant_errors = docs_gate.validate_conversational_architecture_cutover(
            reactivated_root_grant, "manifest.yaml"
        )
        self.assertTrue(
            any("hidden/Production excluded" in error for error in root_grant_errors),
            root_grant_errors,
        )

    def test_current_first_operable_verification_is_immediate_non_result_handoff(
        self,
    ) -> None:
        self._assert_lightweight_verification_mutations_rejected(
            docs_gate.ITER010_LIGHTWEIGHT_FIRST_OPERABLE_CASE_ID,
            (
                (
                    "Claim",
                    "完整浏览器主链",
                    "仅浏览器外壳",
                ),
                (
                    "Frozen input / oracle",
                    "至少三 Turn 语义链",
                    "单次问答",
                ),
                (
                    "Expected",
                    "`requires_result=false`",
                    "`requires_result=true`",
                ),
            ),
        )

    def test_current_mvp_verification_freezes_final_result_handoff_semantics(
        self,
    ) -> None:
        self._assert_lightweight_verification_mutations_rejected(
            docs_gate.ITER010_LIGHTWEIGHT_EXPERIENCE_CASE_ID,
            (
                (
                    "Claim",
                    "最终 Result handoff",
                    "首次浏览器交付",
                ),
                (
                    "Frozen input / oracle",
                    "`V-CHAT-EXPERIENCE-001` 同一 clean candidate",
                    "不同候选",
                ),
                (
                    "Expected",
                    "`requires_result=true`",
                    "`requires_result=false`",
                ),
            ),
        )

    def test_current_preview_verification_freezes_post_experience_direction_semantics(
        self,
    ) -> None:
        self._assert_lightweight_verification_mutations_rejected(
            "V-PREVIEW-002",
            (
                (
                    "Claim",
                    "完整浏览器体验",
                    "单条测试输出",
                ),
                (
                    "Frozen input / oracle",
                    "最早责任层",
                    "最终答案猜测根因",
                ),
                (
                    "Expected",
                    "`CONTINUE` 后仍需新 PDR、明确用户授权和可信父 cutover",
                    "`CONTINUE` 自动进入 full regression",
                ),
            ),
        )

    def test_rework_validates_the_immutable_historical_result(self) -> None:
        _, by_id = self._documents()
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        verification = by_id["ITER-010-VERIFICATION"]
        baseline_errors = docs_gate.validate_product_goal_reference_targets(
            manifest_path,
            "ITER-010",
            by_id,
            require_execution_slice_sequence=True,
            require_paused_slice_sequence=False,
            verification=verification,
        )
        self.assertFalse(
            any(
                "immutable Evidence" in error
                or "reflection_report_digest" in error
                or "Slice gate Cases must include" in error
                for error in baseline_errors
            ),
            baseline_errors,
        )

        historical_evidence = (
            "run-028 证明仅投影/focus 仍可跳过 lead；"
            "`FINDING-010-077/078` deterministic regression closed，fresh live pending"
        )
        self.assertIn(historical_evidence, verification.body)
        rewritten_verification = docs_gate.Document(
            verification.path,
            verification.metadata,
            verification.body.replace(
                historical_evidence,
                "ITER-010-RESULT-SLICE-001-STOP-REDIRECT#V-REVIEW-001",
                1,
            ),
        )
        rewritten_errors = docs_gate.validate_product_goal_reference_targets(
            manifest_path,
            "ITER-010",
            {**by_id, verification.identifier: rewritten_verification},
            require_execution_slice_sequence=True,
            require_paused_slice_sequence=False,
            verification=rewritten_verification,
        )
        self.assertTrue(
            any(
                "historical Case V-REVIEW-001 must preserve its immutable Evidence"
                in error
                for error in rewritten_errors
            ),
            rewritten_errors,
        )

        result = by_id["ITER-010-RESULT-SLICE-001-STOP-REDIRECT"]
        tampered_body = result.body.replace(
            "Decision: REDIRECT",
            "Decision: REDIRECT\n\nTampered reflection evidence.",
            1,
        )
        self.assertNotEqual(tampered_body, result.body)
        tampered_by_id = {
            **by_id,
            result.identifier: docs_gate.Document(
                result.path,
                result.metadata,
                tampered_body,
            ),
        }
        errors = docs_gate.validate_product_goal_reference_targets(
            manifest_path,
            "ITER-010",
            tampered_by_id,
            require_execution_slice_sequence=True,
            require_paused_slice_sequence=False,
            verification=verification,
        )
        self.assertTrue(
            any("reflection_report_digest" in error for error in errors), errors
        )

        # The sustained experience Case belongs to the first Slice.  Merely
        # keeping the Manifest binding on Slice 1 while moving Case ownership
        # to Slice 2 must not preserve a valid partition.
        first_slice = by_id["ITER-010-SLICE-001"]
        second_slice = by_id["ITER-010-SLICE-002"]
        first_cases = list(
            first_slice.metadata["product_goal_slice_gate_case_ids"]
        )
        second_cases = list(
            second_slice.metadata["product_goal_slice_gate_case_ids"]
        )
        first_cases.remove("V-CHAT-EXPERIENCE-001")
        second_cases.append("V-CHAT-EXPERIENCE-001")
        transferred_by_id = {
            **by_id,
            first_slice.identifier: docs_gate.Document(
                first_slice.path,
                {
                    **first_slice.metadata,
                    "product_goal_slice_gate_case_ids": first_cases,
                },
                first_slice.body,
            ),
            second_slice.identifier: docs_gate.Document(
                second_slice.path,
                {
                    **second_slice.metadata,
                    "product_goal_slice_gate_case_ids": second_cases,
                },
                second_slice.body,
            ),
        }
        transfer_errors = docs_gate.validate_product_goal_reference_targets(
            manifest_path,
            "ITER-010",
            transferred_by_id,
            require_execution_slice_sequence=True,
            require_paused_slice_sequence=False,
            verification=verification,
        )
        self.assertTrue(
            any("Slice gate Cases must include" in error for error in transfer_errors),
            transfer_errors,
        )

    def test_authorized_rework_requires_policy_and_sustained_experience_binding(
        self,
    ) -> None:
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = docs_gate.safe_load_manifest(manifest_text)
        manifest["experience_delivery_policy"][  # type: ignore[index]
            "historical_pre_policy_result_refs"
        ] = docs_gate.manifest_resolved_sequence_items(
            manifest_text,
            "experience_delivery_policy",
            "historical_pre_policy_result_refs",
        ) or []
        new_refs = docs_gate.manifest_resolved_sequence_items(
            manifest_text,
            "product_goal_alignment",
            "new_capability_slice_refs",
        )
        blocking = docs_gate.manifest_resolved_sequence_items(
            manifest_text,
            "product_goal_alignment",
            "blocking_case_ids",
        )
        assert new_refs is not None and blocking is not None
        for reference in new_refs:
            state = manifest["development"]["slices"][reference]  # type: ignore[index]
            for field in ("rework_result_refs", "prior_authorization_refs"):
                if isinstance(state.get(field), dict):
                    state[field] = (
                        docs_gate.manifest_resolved_nested_sequence_items(
                            manifest_text,
                            ("development", "slices", reference, field),
                        )
                        or []
                    )

        self.assertEqual(
            docs_gate.validate_rework_policy(
                manifest, "manifest.yaml", required=True
            ),
            [],
        )
        self.assertEqual(
            docs_gate.validate_experience_first_delivery_policy(
                manifest,
                manifest["product_goal_alignment"],
                new_refs,
                blocking,
                "manifest.yaml",
                required=True,
                manifest_text=manifest_text,
            ),
            [],
        )

        # PDR-010 does not use a historical Result as a current experience
        # prerequisite.  Removing the legacy cutover list therefore must not
        # restore the superseded PDR-009 Result audit.
        without_cutover = copy.deepcopy(manifest)
        without_cutover["experience_delivery_policy"][  # type: ignore[index]
            "historical_pre_policy_result_refs"
        ] = []
        cutover_errors = docs_gate.validate_product_goal_alignment_manifest(
            without_cutover,
            manifest_text,
            "manifest.yaml",
            "ITER-010",
        )
        self.assertFalse(
            any(
                "historical_pre_policy_result_refs" in error
                for error in cutover_errors
            ),
            cutover_errors,
        )

        # The lightweight action permits one evidence-backed general repair
        # before responsibility review; zero attempts would silently disable
        # that repair path.
        self.assertEqual(manifest["rework_policy"]["no_progress_attempt_limit"], 1)
        no_general_repair = copy.deepcopy(manifest)
        no_general_repair["rework_policy"]["no_progress_attempt_limit"] = 0
        repair_errors = docs_gate.validate_rework_policy(
            no_general_repair, "manifest.yaml", required=True
        )
        self.assertTrue(
            any("no_progress_attempt_limit" in error for error in repair_errors),
            repair_errors,
        )

        without_policy = copy.deepcopy(manifest)
        without_policy.pop("rework_policy")
        policy_errors = docs_gate.validate_product_goal_alignment_manifest(
            without_policy,
            manifest_text,
            "manifest.yaml",
            "ITER-010",
        )
        self.assertTrue(
            any("rework_policy is required" in error for error in policy_errors),
            policy_errors,
        )

        without_experience = copy.deepcopy(manifest)
        without_experience["product_goal_alignment"].pop(  # type: ignore[index]
            "experience_version_binding"
        )
        experience_errors = docs_gate.validate_product_goal_alignment_manifest(
            without_experience,
            manifest_text,
            "manifest.yaml",
            "ITER-010",
        )
        self.assertTrue(
            any(
                "experience_version_binding is required" in error
                for error in experience_errors
            ),
            experience_errors,
        )

        # Removing every visible repair field from a rejected current-version
        # Manifest must not silently restore the legacy policy.
        stripped_rejected = copy.deepcopy(manifest)
        stripped_rejected.pop("rework_policy")
        stripped_rejected["iteration"]["status"] = "rejected"  # type: ignore[index]
        stripped_rejected["iteration"].pop("current_decision", None)  # type: ignore[index]
        for state in stripped_rejected["development"]["slices"].values():  # type: ignore[index]
            for field in (
                "project_decision_ref",
                "rework_result_refs",
                "rework_attempt_number",
                "rework_prerequisite_result",
                "rework_progress_measure",
            ):
                state.pop(field, None)
        stripped_errors = docs_gate.validate_product_goal_alignment_manifest(
            stripped_rejected,
            manifest_text,
            "manifest.yaml",
            "ITER-010",
        )
        self.assertTrue(
            any("rework_policy is required" in error for error in stripped_errors),
            stripped_errors,
        )

    def test_experience_binding_rejects_invalid_port_and_service_shutdown(
        self,
    ) -> None:
        alignment = {
            "experience_version_binding": {
                "schema": "USER_EXPERIENCE_VERSION@1",
                "case_id": "V-EXPERIENCE-001",
                "new_slice_ref": "ITER-012-SLICE-001",
                "exact_version_visible": True,
                "repeatable_start": True,
                "continuous_same_session_free_questions": True,
                "limitations_visible": True,
                "fixed_loopback_address": "http://127.0.0.1:8765/",
                "question_failure_scope": (
                    "current-question-only-service-remains-available"
                ),
            }
        }
        self.assertEqual(
            docs_gate.validate_experience_version_binding(
                alignment,
                ["ITER-012-SLICE-001"],
                ["V-EXPERIENCE-001"],
                "manifest.yaml",
                required=True,
            ),
            [],
        )
        invalid = copy.deepcopy(alignment)
        invalid["experience_version_binding"][  # type: ignore[index]
            "fixed_loopback_address"
        ] = "http://127.0.0.1:70000/"
        invalid["experience_version_binding"][  # type: ignore[index]
            "question_failure_scope"
        ] = "stop-the-service"
        errors = docs_gate.validate_experience_version_binding(
            invalid,
            ["ITER-012-SLICE-001"],
            ["V-EXPERIENCE-001"],
            "manifest.yaml",
            required=True,
        )
        self.assertTrue(any("127.0.0.1" in error for error in errors), errors)
        self.assertTrue(any("without stopping" in error for error in errors), errors)

    def test_legacy_direction_checkpoint_policy_uses_explicit_pdr009_fixture(
        self,
    ) -> None:
        legacy_manifest: dict[str, object] = {
            "plan_execution_control": {
                "plan_revision_ref": docs_gate.ITER010_PLAN_REVISION_REF,
            },
            "experience_delivery_policy": {
                "direction_discovery_principle_ref": (
                    docs_gate.ITER010_DIRECTION_DISCOVERY_PRINCIPLE_REF
                ),
                "micro_checkpoint_count": 4,
                "micro_checkpoint_order": (
                    docs_gate.ITER010_DIRECTION_MICRO_CHECKPOINT_ORDER
                ),
                "pdr004_schedule_fields_are_legacy_validator_compatibility_only": True,
                "checkpoint_miss_action": (
                    docs_gate.ITER010_DIRECTION_CHECKPOINT_MISS_ACTION
                ),
            },
        }
        self.assertTrue(docs_gate.uses_legacy_iter010_plan(legacy_manifest))
        self.assertFalse(docs_gate.uses_lightweight_iter010_plan(legacy_manifest))
        self.assertEqual(
            docs_gate.validate_iter010_direction_checkpoint_policy(
                legacy_manifest, "manifest.yaml"
            ),
            [],
        )

        invalid = copy.deepcopy(legacy_manifest)
        invalid["experience_delivery_policy"]["micro_checkpoint_count"] = 2
        errors = docs_gate.validate_iter010_direction_checkpoint_policy(
            invalid, "manifest.yaml"
        )
        self.assertTrue(
            any("micro_checkpoint_count" in error for error in errors), errors
        )

    def test_semantic_chat_requires_lead_agent_context_and_turn_isolation(
        self,
    ) -> None:
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = docs_gate.safe_load_manifest(manifest_text)
        alignment = manifest["product_goal_alignment"]
        new_refs = docs_gate.manifest_resolved_sequence_items(
            manifest_text,
            "product_goal_alignment",
            "new_capability_slice_refs",
        )
        blocking = docs_gate.manifest_resolved_sequence_items(
            manifest_text,
            "product_goal_alignment",
            "blocking_case_ids",
        )
        assert new_refs is not None and blocking is not None

        self.assertEqual(
            docs_gate.validate_conversational_engineering_agent(
                manifest,
                alignment,
                new_refs,
                blocking,
                "manifest.yaml",
                required=True,
            ),
            [],
        )
        self.assertEqual(
            docs_gate.validate_experience_version_binding(
                alignment,
                new_refs,
                blocking,
                "manifest.yaml",
                required=True,
            ),
            [],
        )
        self.assertEqual(
            docs_gate.validate_experience_first_delivery_policy(
                manifest,
                alignment,
                new_refs,
                blocking,
                "manifest.yaml",
                required=True,
                manifest_text=manifest_text,
            ),
            [],
        )
        self.assertTrue(docs_gate.uses_post_pdr009_iter010_plan(manifest))
        self.assertTrue(docs_gate.uses_failure_handoff_iter010_plan(manifest))
        self.assertFalse(docs_gate.uses_legacy_iter010_plan(manifest))

        for field, value in (
            ("micro_checkpoint_count", 4),
            ("micro_checkpoint_order", "runnable-access-handoff"),
            ("pdr010_machine_timebox_or_activation_receipt_required", True),
            (
                "current_execution_decision_ref",
                docs_gate.ITER010_PLAN_REVISION_REF,
            ),
        ):
            invalid_direction = copy.deepcopy(manifest)
            invalid_direction["experience_delivery_policy"][field] = value
            errors = docs_gate.validate_experience_first_delivery_policy(
                invalid_direction,
                invalid_direction["product_goal_alignment"],
                new_refs,
                blocking,
                "manifest.yaml",
                required=True,
                manifest_text=manifest_text,
            )
            self.assertTrue(any(field in error for error in errors), (field, errors))

        invalid_turn_count = copy.deepcopy(manifest)
        invalid_turn_count["experience_delivery_policy"]["live_canary_turn_count"] = 2
        turn_count_errors = docs_gate.validate_experience_first_delivery_policy(
            invalid_turn_count,
            invalid_turn_count["product_goal_alignment"],
            new_refs,
            blocking,
            "manifest.yaml",
            required=True,
            manifest_text=manifest_text,
        )
        self.assertTrue(
            any(
                "live_canary_turn_count" in error
                for error in turn_count_errors
            ),
            turn_count_errors,
        )

        invalid_policy_values = (
            ("fixed_multi_role_content_workflow_is_target_agent", True),
            ("provider_hidden_memory_is_authority", True),
            ("conversation_binding_schema", "ENGINEERING_CHAT_BINDING@1"),
            ("conversation_input_policy_ref", "UNREGISTERED@1"),
            ("prior_answer_or_review_reuse_as_fact_allowed", True),
            ("first_chat_canary_turn_count", 4),
            ("new_conversation_context_isolation_required", False),
            ("full_regression_before_direction_confirmation_allowed", True),
            ("first_live_chat_turn_result", "passed"),
            (
                "deterministic_successor_canary_source_file_budget",
                "search-64-plus-read-1",
            ),
        )
        for field, value in invalid_policy_values:
            invalid = copy.deepcopy(manifest)
            invalid["conversational_engineering_agent"][field] = value
            errors = docs_gate.validate_conversational_engineering_agent(
                invalid,
                invalid["product_goal_alignment"],
                new_refs,
                blocking,
                "manifest.yaml",
                required=True,
            )
            self.assertTrue(any(field in error for error in errors), (field, errors))

        missing = copy.deepcopy(manifest)
        missing.pop("conversational_engineering_agent")
        self.assertTrue(
            any(
                "is required" in error
                for error in docs_gate.validate_conversational_engineering_agent(
                    missing,
                    missing["product_goal_alignment"],
                    new_refs,
                    blocking,
                    "manifest.yaml",
                    required=True,
                )
            )
        )

        for field in (
            "semantic_follow_up",
            "user_correction_updates_context",
            "per_turn_evidence_and_review",
            "new_conversation_context_isolation",
        ):
            invalid_alignment = copy.deepcopy(alignment)
            invalid_alignment["experience_version_binding"][field] = False
            errors = docs_gate.validate_experience_version_binding(
                invalid_alignment,
                new_refs,
                blocking,
                "manifest.yaml",
                required=True,
            )
            self.assertTrue(any(field in error for error in errors), (field, errors))

    def test_rework_marker_cannot_be_erased_before_same_slice_reauthorization(
        self,
    ) -> None:
        _, by_id = self._documents()
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = docs_gate.safe_load_manifest(manifest_text)
        new_refs = docs_gate.manifest_resolved_sequence_items(
            manifest_text,
            "product_goal_alignment",
            "new_capability_slice_refs",
        )
        assert new_refs is not None

        erased = copy.deepcopy(manifest)
        erased["iteration"]["status"] = "authorized"  # type: ignore[index]
        erased["iteration"].pop("current_decision", None)  # type: ignore[index]
        state = erased["development"]["slices"]["ITER-010-SLICE-001"]  # type: ignore[index]
        state.update(
            {
                "status": "authorized",
                "coding_input": True,
                "result": "not-executed",
                "product_code_freeze_digest": "not-executed",
                "authorized_by": "user",
                "authorized_at": "2026-08-24T00:00:00Z",
                "authorization_ref": "codex-user-message:sha256:" + "e" * 64,
                "reflection_decision": "not-executed",
            }
        )
        for field in (
            "project_decision_ref",
            "rework_result_refs",
            "rework_attempt_number",
            "rework_prerequisite_result",
            "rework_progress_measure",
        ):
            state.pop(field, None)

        target = by_id["ITER-010-SLICE-001"]
        active_target = docs_gate.Document(
            target.path,
            {
                **target.metadata,
                "status": "authorized",
                "authority": "current-development",
                "coding_input": True,
            },
            target.body,
        )
        errors = docs_gate.validate_product_goal_slice_sequence(
            new_refs,
            {**by_id, target.identifier: active_target},
            "manifest.yaml",
            manifest=erased,
            verification=by_id["ITER-010-VERIFICATION"],
        )
        self.assertTrue(
            any("retain its REWORK project decision" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("retain all failed rework Results" in error for error in errors),
            errors,
        )

    def test_redirect_requires_an_allowed_basis_and_completed_no_progress_limit(
        self,
    ) -> None:
        _, by_id = self._documents()
        manifest_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        manifest = docs_gate.safe_load_manifest(
            manifest_path.read_text(encoding="utf-8")
        )
        target = by_id["ITER-010-SLICE-001"]
        result = by_id["ITER-010-RESULT-SLICE-001-STOP-REDIRECT"]
        verification = by_id["ITER-010-VERIFICATION"]
        proposal = by_id["ITER-010-PROPOSAL"]
        catalog_digest, assumption_expectations, catalog_errors = (
            docs_gate.critical_assumption_catalog(proposal)
        )
        self.assertEqual(catalog_errors, [])
        binding = docs_gate.reflection_gate_bindings_by_slice(
            manifest["product_goal_alignment"]  # type: ignore[arg-type]
        )[target.identifier]
        policy = manifest["rework_policy"]

        invalid_result = docs_gate.Document(
            result.path,
            {**result.metadata, "reflection_redirect_basis": "user-reported-a-bug"},
            result.body,
        )
        invalid_errors = docs_gate.validate_slice_reflection_result(
            target,
            invalid_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            verification,
            "manifest.yaml",
            blocked=True,
            assumption_expectations=assumption_expectations,
            assumption_catalog_digest=catalog_digest,
            rework_policy=policy,  # type: ignore[arg-type]
        )
        self.assertTrue(
            any("allowed explicit redirect basis" in error for error in invalid_errors),
            invalid_errors,
        )

        misclassified_architecture_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_redirect_basis": "core-architecture-falsified",
                "reflection_issue_class": "implementation",
                "reflection_issue_scope": "individual",
            },
            result.body,
        )
        architecture_errors = docs_gate.validate_slice_reflection_result(
            target,
            misclassified_architecture_result,
            binding,
            {"reflection_decision": "REDIRECT"},
            verification,
            "manifest.yaml",
            blocked=True,
            assumption_expectations=assumption_expectations,
            assumption_catalog_digest=catalog_digest,
            rework_policy=policy,  # type: ignore[arg-type]
        )
        self.assertTrue(
            any("architecture/systemic" in error for error in architecture_errors),
            architecture_errors,
        )

        no_progress_result = docs_gate.Document(
            result.path,
            {
                **result.metadata,
                "reflection_redirect_basis": (
                    "precommitted-no-progress-limit-reached"
                ),
                "rework_attempt_number": 2,
                "rework_progress_measure": policy["no_progress_measure"],  # type: ignore[index]
            },
            result.body,
        )
        no_progress_errors = docs_gate.validate_slice_reflection_result(
            target,
            no_progress_result,
            binding,
            {
                "reflection_decision": "REDIRECT",
                "rework_result_refs": ["only-one-failed-result"],
            },
            verification,
            "manifest.yaml",
            blocked=True,
            assumption_expectations=assumption_expectations,
            assumption_catalog_digest=catalog_digest,
            rework_policy=policy,  # type: ignore[arg-type]
        )
        self.assertTrue(
            any("complete failed-Result history count" in error for error in no_progress_errors),
            no_progress_errors,
        )

        wrong_measure_result = docs_gate.Document(
            result.path,
            {
                **no_progress_result.metadata,
                "rework_progress_measure": "a-different-unfrozen-measure",
            },
            result.body,
        )
        wrong_measure_errors = docs_gate.validate_slice_reflection_result(
            target,
            wrong_measure_result,
            binding,
            {
                "reflection_decision": "REDIRECT",
                "rework_result_refs": ["failed-result-1", "failed-result-2"],
            },
            verification,
            "manifest.yaml",
            blocked=True,
            assumption_expectations=assumption_expectations,
            assumption_catalog_digest=catalog_digest,
            rework_policy=policy,  # type: ignore[arg-type]
        )
        self.assertTrue(
            any("frozen no_progress_measure" in error for error in wrong_measure_errors),
            wrong_measure_errors,
        )

    def test_rework_history_is_mandatory_and_superseded_plan_is_non_coding(
        self,
    ) -> None:
        _, by_id = self._documents()
        target = by_id["ITER-010-SLICE-001"]
        valid_state = {
            "project_decision_ref": "ITER-010-PDR-001",
            "rework_attempt_number": 1,
            "rework_result_refs": ["ITER-010-RESULT-SLICE-001-STOP-REDIRECT"],
            "rework_prerequisite_result": (
                "ITER-010-RESULT-SLICE-001-STOP-REDIRECT"
            ),
        }
        self.assertEqual(
            docs_gate.validate_rework_result_history(
                target,
                valid_state,
                by_id,
                "manifest.yaml",
            ),
            [],
        )
        authorized_state = {
            **valid_state,
            "prior_authorization_refs": [
                by_id["ITER-010-READINESS"].metadata[
                    "historical_product_goal_alignment_review_ref"
                ]
            ],
            "authorization_ref": "codex-user-message:sha256:" + "e" * 64,
        }
        self.assertEqual(
            docs_gate.validate_rework_authorization_receipt(
                target,
                authorized_state,
                by_id,
                "manifest.yaml",
            ),
            [],
        )
        reused_decision_receipt = {
            **authorized_state,
            "authorization_ref": by_id["ITER-010-PDR-001"].metadata[
                "decision_ref"
            ],
        }
        receipt_errors = docs_gate.validate_rework_authorization_receipt(
            target,
            reused_decision_receipt,
            by_id,
            "manifest.yaml",
        )
        self.assertTrue(
            any("new user authorization receipt" in error for error in receipt_errors),
            receipt_errors,
        )
        reused_initial_receipt = {
            **authorized_state,
            "authorization_ref": by_id["ITER-010-READINESS"].metadata[
                "historical_product_goal_alignment_review_ref"
            ],
        }
        initial_receipt_errors = docs_gate.validate_rework_authorization_receipt(
            target,
            reused_initial_receipt,
            by_id,
            "manifest.yaml",
        )
        self.assertTrue(
            any(
                "new user authorization receipt" in error
                for error in initial_receipt_errors
            ),
            initial_receipt_errors,
        )

        atomic_readiness_authorization = {
            **authorized_state,
            "authorization_combines_current_readiness_acceptance": True,
            "authorization_ref": by_id["ITER-010-READINESS"].metadata[
                "product_goal_alignment_review_ref"
            ],
        }
        self.assertEqual(
            docs_gate.validate_rework_authorization_receipt(
                target,
                atomic_readiness_authorization,
                by_id,
                "manifest.yaml",
            ),
            [],
        )
        mismatched_atomic = {
            **atomic_readiness_authorization,
            "authorization_ref": "codex-user-message:sha256:" + "f" * 64,
        }
        mismatched_atomic_errors = docs_gate.validate_rework_authorization_receipt(
            target,
            mismatched_atomic,
            by_id,
            "manifest.yaml",
        )
        self.assertTrue(
            any(
                "combined Readiness acceptance and Slice reauthorization"
                in error
                for error in mismatched_atomic_errors
            ),
            mismatched_atomic_errors,
        )

        wrong_attempt = {**valid_state, "rework_attempt_number": 2}
        wrong_attempt_errors = docs_gate.validate_rework_result_history(
            target,
            wrong_attempt,
            by_id,
            "manifest.yaml",
        )
        self.assertTrue(
            any("history count" in error for error in wrong_attempt_errors),
            wrong_attempt_errors,
        )

        first_result = by_id["ITER-010-RESULT-SLICE-001-STOP-REDIRECT"]
        second_result_id = "ITER-010-RESULT-SLICE-001-REWORK-002"
        second_result = docs_gate.Document(
            first_result.path,
            {**first_result.metadata, "id": second_result_id},
            first_result.body,
        )
        multi_by_id = {**by_id, second_result_id: second_result}
        multi_state = {
            **valid_state,
            "rework_attempt_number": 2,
            "rework_result_refs": [first_result.identifier, second_result_id],
            "rework_prerequisite_result": second_result_id,
            "rework_history_freezes": {
                first_result.identifier: {
                    "product_code_freeze_digest": first_result.metadata[
                        "product_code_freeze_digest"
                    ],
                    "reflection_report_digest": first_result.metadata[
                        "reflection_report_digest"
                    ],
                },
                second_result_id: {
                    "product_code_freeze_digest": second_result.metadata[
                        "product_code_freeze_digest"
                    ],
                    "reflection_report_digest": second_result.metadata[
                        "reflection_report_digest"
                    ],
                },
            },
        }
        self.assertEqual(
            docs_gate.validate_rework_result_history(
                target,
                multi_state,
                multi_by_id,
                "manifest.yaml",
            ),
            [],
        )
        tampered_first = docs_gate.Document(
            first_result.path,
            first_result.metadata,
            first_result.body.replace(
                "Decision: REDIRECT",
                "Decision: REDIRECT\n\nTampered older attempt.",
                1,
            ),
        )
        tampered_history_errors = docs_gate.validate_rework_result_history(
            target,
            multi_state,
            {**multi_by_id, first_result.identifier: tampered_first},
            "manifest.yaml",
        )
        self.assertTrue(
            any(
                "reflection_report_digest" in error
                for error in tampered_history_errors
            ),
            tampered_history_errors,
        )
        missing_freeze_state = dict(multi_state)
        missing_freeze_state.pop("rework_history_freezes")
        missing_freeze_errors = docs_gate.validate_rework_result_history(
            target,
            missing_freeze_state,
            multi_by_id,
            "manifest.yaml",
        )
        self.assertTrue(
            any("freeze every Result" in error for error in missing_freeze_errors),
            missing_freeze_errors,
        )
        missing_history = dict(valid_state)
        missing_history.pop("rework_result_refs")
        errors = docs_gate.validate_rework_result_history(
            target,
            missing_history,
            by_id,
            "manifest.yaml",
        )
        self.assertTrue(any("is required" in error for error in errors), errors)

        superseded_path = (
            docs_gate.REPOSITORY
            / "docs/project/iterations/iteration-011/manifest.yaml"
        )
        superseded_text = superseded_path.read_text(encoding="utf-8")
        superseded_manifest = docs_gate.safe_load_manifest(superseded_text)
        new_refs = docs_gate.manifest_resolved_sequence_items(
            superseded_text,
            "product_goal_alignment",
            "new_capability_slice_refs",
        )
        assert new_refs is not None
        self.assertEqual(
            docs_gate.validate_superseded_iteration_plan(
                new_refs,
                by_id,
                superseded_manifest,
                "manifest.yaml",
            ),
            [],
        )
        unsafe_by_id = dict(by_id)
        first = by_id[new_refs[0]]
        unsafe_by_id[first.identifier] = docs_gate.Document(
            first.path,
            {
                **first.metadata,
                "status": "authorized",
                "authority": "current-development",
                "coding_input": True,
            },
            first.body,
        )
        unsafe_errors = docs_gate.validate_superseded_iteration_plan(
            new_refs,
            unsafe_by_id,
            superseded_manifest,
            "manifest.yaml",
        )
        self.assertTrue(
            any("proposed and non-coding" in error for error in unsafe_errors),
            unsafe_errors,
        )

        authorized_superseded = copy.deepcopy(superseded_manifest)
        authorized_superseded["authorization"].update(  # type: ignore[index]
            {
                "authorized_by": "user",
                "authorized_at": "2026-08-24T00:00:00Z",
                "authorization_ref": "codex-user-message:sha256:" + "f" * 64,
            }
        )
        top_authorization_errors = docs_gate.validate_superseded_iteration_plan(
            new_refs,
            by_id,
            authorized_superseded,
            "manifest.yaml",
        )
        self.assertTrue(
            any("top-level authorization" in error for error in top_authorization_errors),
            top_authorization_errors,
        )

        executed_result = docs_gate.Document(
            superseded_path,
            {
                "id": "ITER-011-RESULT-UNSAFE",
                "kind": "iteration-result",
                "status": "accepted",
                "authority": "execution-evidence",
                "iteration": "ITER-011",
            },
            "",
        )
        result_errors = docs_gate.validate_superseded_iteration_plan(
            new_refs,
            {**by_id, executed_result.identifier: executed_result},
            superseded_manifest,
            "manifest.yaml",
        )
        self.assertTrue(
            any("execution or accepted Result" in error for error in result_errors),
            result_errors,
        )


if __name__ == "__main__":
    unittest.main()
