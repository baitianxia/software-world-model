#!/usr/bin/env python3
"""Validate current documentation and generate agent-oriented indexes."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Iterable


REPOSITORY = Path(__file__).resolve().parents[1]
DOCS = REPOSITORY / "docs"
GENERATED = DOCS / "_generated"
SCAN_ROOTS = (DOCS / "system", DOCS / "project")
PLAIN_LINK_FILES = (
    REPOSITORY / "README.md",
    REPOSITORY / "AGENTS.md",
    DOCS / "README.md",
    DOCS / "_generated" / "README.md",
    DOCS / "archive" / "README.md",
)
REQUIRED = ("id", "kind", "status", "authority", "owners", "depends_on", "code", "tests")
LIST_FIELDS = {
    "owners",
    "depends_on",
    "code",
    "tests",
    "derived_from",
    "product_goal_accepted_capability_refs",
    "product_goal_cross_domain_case_ids",
    "product_goal_slice_gate_case_ids",
}
LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
ACTIVE_ITERATION_STATUSES = {"authorized", "in-progress"}
ACTIVE_SLICE_STATUSES = {"authorized", "in-progress"}
PAUSED_ITERATION_STATUSES = {"paused"}
PAUSED_SLICE_STATUSES = {"paused"}
ACCEPTED_PROPOSAL_STATUSES = {"accepted", "authorized"}
ACCEPTED_READINESS_STATUSES = {"accepted", "authorized"}
FINAL_ITERATION_STATUSES = {"completed", "accepted"}
REFLECTION_DECISIONS = {"CONTINUE", "ACCEPT", "REWORK", "REDIRECT", "REJECT"}
DIRECTION_DECISION_SETS = {
    "CONTINUE,REDIRECT,REJECT",  # Historical manifests before REWORK existed.
    "CONTINUE,REWORK,REDIRECT,REJECT",
}
FINDING_CLASSIFICATIONS = {
    "local-implementation",
    "iteration-design",
    "system-contract",
    "verification",
    "roadmap",
    "invalid",
}
PENDING_VALUES = {"", "pending", "unclassified"}
PLACEHOLDER_RE = re.compile(
    r"(?:\b(?:ITER|SLICE|FINDING)-NNN\b|\bNNN\b|"
    r"<(?!https?://|mailto:)[A-Za-z][^<>\n]*>)",
    re.IGNORECASE,
)
HEX_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
MANIFEST_PENDING_RE = re.compile(
    r'''(?mix)^\s*(?:-\s*)?(?:[A-Za-z_][A-Za-z0-9_-]*:\s*)?
    (?:pending|"pending"|'pending')\s*$'''
)
PRODUCT_GOAL_ALIGNMENT_START_ITERATION = 7
REFLECTION_GATE_START_ITERATION = 8
DIRECTION_PREVIEW_START_ITERATION = 9
ENGINEERING_QA_HYBRID_START_ITERATION = 10
REWORK_LIFECYCLE_START_ITERATION = 10
STRICT_CODEX_BASELINE_START_ITERATION = 12
EXPERIENCE_FIRST_DELIVERY_START_ITERATION = 12
PROVIDER_ROUTE_POLICY_START_ITERATION = 12
EXPERIENCE_FIRST_DELIVERY_SCHEMA = "EXPERIENCE_FIRST_DELIVERY@1"
PROVIDER_ROUTE_POLICY_SCHEMA = "QUALIFIED_EXECUTION_PROFILE_PREFERENCE@2"
LEGACY_PROVIDER_ROUTE_POLICY_SCHEMA = "QUALIFIED_PROVIDER_PREFERENCE@1"
EXECUTION_PROFILE_CONFIGURATION_SCHEMA = "MODEL_TRANSPARENT_EXECUTION_PROFILES@2"
LEGACY_EXECUTION_PROFILE_CONFIGURATION_SCHEMA = (
    "MODEL_TRANSPARENT_EXECUTION_PROFILES@1"
)
ROUTE_POLICY_MIGRATION_SCHEMA = "TRUSTED_PARENT_ROUTE_POLICY_MIGRATION@1"
ROUTE_POLICY_MIGRATION_EXPECTED = {
    "schema": ROUTE_POLICY_MIGRATION_SCHEMA,
    "state": "trusted-parent-bridge",
    "from_schema": LEGACY_PROVIDER_ROUTE_POLICY_SCHEMA,
    "to_schema": PROVIDER_ROUTE_POLICY_SCHEMA,
    "plan_revision_ref": "ITER-010-PDR-010",
    "only_next_change": "finalize-model-transparent-route-policy",
    "external_dispatch_allowed": False,
}
PREFERRED_EXECUTION_PROFILE_CONFIGURATION_KEYS = {
    "execution_profile_ref",
    "provider_identity",
    "model_identity",
}
FALLBACK_EXECUTION_PROFILE_CONFIGURATION_KEYS = (
    PREFERRED_EXECUTION_PROFILE_CONFIGURATION_KEYS
    | {"admission_policy_plugin_ref"}
)
ENGINEERING_CHAT_EXPERIENCE_SCHEMA = "ENGINEERING_CHAT_EXPERIENCE@1"
CONVERSATIONAL_ENGINEERING_AGENT_SCHEMA = "CONVERSATIONAL_ENGINEERING_AGENT@1"
EXPERIENCE_FIRST_FAILURE_DIAGNOSIS_ORDER = (
    "source-truth-world-model-cognition-conversation-or-task-understanding-"
    "agent-work-state-and-plan-tool-observation-and-evidence-answer-"
    "independent-review-web"
)
EXPERIENCE_FIRST_DELIVERY_PRE_ACCESS_WORK = (
    "targeted-impact-startup-safety-failure-truth-one-qualification-one-smoke-only"
)
EXPERIENCE_FIRST_DELIVERY_LIVE_ATTEMPT_UNIT = (
    "one-sealed-version-bounded-user-interaction-unit-reaching-any-external-"
    "dispatch-chat-counts-each-turn"
)
EXPERIENCE_FIRST_DELIVERY_HARD_STOP_ACTION = (
    "stop-scope-expansion-and-external-calls-narrow-and-review"
)
EXPERIENCE_FIRST_DELIVERY_NO_INCREMENT_ACTION = (
    "stop-external-reruns-and-return-to-local-diagnosis"
)
ITER010_DIRECTION_MICRO_CHECKPOINT_ORDER = (
    "direction-freeze-PASS->preferred-quality;preferred-quality-PASS->minimum-web;"
    "preferred-quality-FAIL->direction-rework;"
    "preferred-quality-INVALID->fallback-refreeze;"
    "fallback-refreeze-PASS->fallback-quality;"
    "fallback-refreeze-FAIL->preferred-quality;"
    "fallback-refreeze-INVALID->fallback-refreeze;"
    "fallback-quality-PASS->minimum-web;"
    "fallback-quality-FAIL->direction-rework;"
    "fallback-quality-INVALID->fallback-quality;"
    "minimum-web-PASS->user-direction-decision"
)
ITER010_DIRECTION_CHECKPOINT_MISS_ACTION = (
    "handoff-last-runnable-version-and-earliest-root-cause-stop-scope-expansion"
)
ITER010_PLAN_EXECUTION_CONTROL_SCHEMA = "DEVELOPMENT_PLAN_EXECUTION_CONTROL@1"
ITER010_PLAN_REVISION_REF = "ITER-010-PDR-009"
ITER010_LIGHTWEIGHT_PLAN_REVISION_REF = "ITER-010-PDR-010"
ITER010_FAILURE_HANDOFF_PLAN_REVISION_REF = "ITER-010-PDR-011"
ITER010_LIGHTWEIGHT_EXPERIENCE_CASE_ID = "V-MVP-EXPERIENCE-001"
ITER010_LIGHTWEIGHT_FIRST_OPERABLE_CASE_ID = "V-CHAT-EXPERIENCE-001"
ITER010_LIGHTWEIGHT_EXPERIENCE_POLICY_EXACT_VALUES: tuple[
    tuple[str, object], ...
] = (
    ("schema", EXPERIENCE_FIRST_DELIVERY_SCHEMA),
    ("owner_slice_ref", "ITER-010-SLICE-001"),
    ("current_execution_decision_ref", ITER010_LIGHTWEIGHT_PLAN_REVISION_REF),
    ("current_gate_decision_ref", ITER010_LIGHTWEIGHT_PLAN_REVISION_REF),
    (
        "direction_discovery_principle_ref",
        "codex-user-message:sha256:"
        "27ad0abac79f239eb13793fed79f65b8a5dfd7042e1c828b63e7d8545577d88f",
    ),
    (
        "first_operable_browser_delivery_case_id",
        ITER010_LIGHTWEIGHT_FIRST_OPERABLE_CASE_ID,
    ),
    ("first_operable_browser_delivery_requires_result", False),
    ("first_operable_browser_delivery_moves_plan_cursor", False),
    (
        "first_operable_browser_delivery_requires_current_codex_comparison",
        False,
    ),
    ("final_experience_handoff_case_id", ITER010_LIGHTWEIGHT_EXPERIENCE_CASE_ID),
    ("final_experience_handoff_requires_result", True),
    ("final_experience_handoff_moves_plan_cursor", True),
    (
        "final_experience_handoff_success_path_requires_current_codex_comparison",
        True,
    ),
    (
        "final_experience_handoff_failure_path_requires_one_general_repair_still_failed",
        True,
    ),
    (
        "final_experience_handoff_alternate_trigger",
        "one-evidence-backed-general-repair-still-has-same-material-failure",
    ),
    ("direction_confirmation_case_id", "V-PREVIEW-002"),
    ("micro_checkpoint_count", 2),
    (
        "micro_checkpoint_order",
        "first-operable-browser-delivery->same-candidate-quality-comparison->"
        "final-experience-result-handoff->user-direction",
    ),
    ("user_handoff_required_at_each_checkpoint", True),
    ("checkpoint_completion_requires_runnable_user_visible_artifact", True),
    ("plan_test_or_document_completion_counts_as_user_visible_increment", False),
    (
        "checkpoint_miss_action",
        "handoff-last-runnable-version-and-earliest-root-cause-stop-scope-expansion",
    ),
    ("checkpoint_miss_continues_minimum_experience_recovery", True),
    ("historical_results_do_not_satisfy_experience_gate", True),
    ("alpha_comparison_case_id", "V-DIRECTION-QUALITY-001"),
    ("provider_readiness_blocks_first_user_handoff", False),
    ("quality_gate_scope", "user-visible-answer-quality-only"),
    ("access_pass_cannot_satisfy_quality_gate", True),
    ("availability_requires_quality_pass", False),
    ("hardening_requires_quality_pass", True),
    (
        "pre_first_experience_allowed_checks",
        EXPERIENCE_FIRST_DELIVERY_PRE_ACCESS_WORK,
    ),
    ("pre_first_experience_full_regression_allowed", False),
    ("failure_diagnosis_order", EXPERIENCE_FIRST_FAILURE_DIAGNOSIS_ORDER),
    ("earliest_divergence_required", True),
    (
        "falsifiable_root_cause_hypothesis_required_before_prompt_schema_or_contract_change",
        True,
    ),
    ("local_minimal_reproduction_required_before_live_retry", True),
    ("unseen_adjacent_local_case_count", 2),
    ("live_canary_conversation_count_after_local_pass", 1),
    ("live_canary_turn_count", 3),
    (
        "same_failure_signature_fix_limit_before_architecture_responsibility_review",
        1,
    ),
    (
        "same_failure_signature_recurrence_action",
        "stop-rule-accumulation-and-review-architecture-responsibilities",
    ),
    ("pre_first_experience_test_scope", "targeted-impact-startup-and-safety-only"),
    ("full_regression_before_alpha_continue_allowed", False),
    (
        "full_regression_allowed_stages",
        "alpha-continue-hardening-and-before-formal-acceptance",
    ),
    ("live_attempt_unit", EXPERIENCE_FIRST_DELIVERY_LIVE_ATTEMPT_UNIT),
    ("same_failure_signature_retry_limit", 1),
    ("consecutive_no_user_visible_increment_limit", 2),
    ("no_increment_action", EXPERIENCE_FIRST_DELIVERY_NO_INCREMENT_ACTION),
    (
        "pdr010_current_action_id",
        "ITER-010-ACTION-USER-PLAN-RECOVERY-001",
    ),
    ("pdr010_current_action_name", "complete-mvp-experience-development"),
    ("pdr010_current_case_id", ITER010_LIGHTWEIGHT_EXPERIENCE_CASE_ID),
    ("pdr010_first_browser_experience_precedes_quality_comparison", True),
    ("pdr010_machine_timebox_or_activation_receipt_required", False),
    (
        "pdr010_failure_stays_in_same_action_until_general-repair-or-user-direction",
        True,
    ),
    ("pdr010_hardening_and_full_regression_locked_until_user_continue", True),
    ("direction_receipt_records_decision_only", True),
    ("direction_action_self_loop_until_new_pdr_cutover", True),
    ("continue_unlock_requires_new_pdr", True),
    ("continue_unlock_requires_explicit_user_authorization", True),
    ("continue_unlock_requires_trusted_parent_cutover", True),
    ("local_message_digest_is_platform_authenticated_authority", False),
)
ITER010_LIGHTWEIGHT_EXPERIENCE_POLICY_SEQUENCE_VALUES: tuple[
    tuple[str, tuple[str, ...]], ...
] = (
    (
        "historical_pre_policy_result_refs",
        ("ITER-010-RESULT-SLICE-001-STOP-REDIRECT",),
    ),
)
ITER010_FAILURE_HANDOFF_EXPERIENCE_POLICY_EXACT_VALUES: tuple[
    tuple[str, object], ...
] = tuple(
    (
        field,
        ITER010_FAILURE_HANDOFF_PLAN_REVISION_REF
        if field in {"current_execution_decision_ref", "current_gate_decision_ref"}
        else expected,
    )
    for field, expected in ITER010_LIGHTWEIGHT_EXPERIENCE_POLICY_EXACT_VALUES
) + (
    ("pdr011_failure_handoff_only", True),
    ("pdr011_product_candidate_commit", "a5c780f51fa5242ee8209766712ad408ed023f80"),
    ("pdr011_multi_artifact_session_failure_records_allowed", True),
    (
        "pdr011_missing_answer_citation_review_or_codex_records_must_not_be_fabricated",
        True,
    ),
    ("pdr011_new_external_dispatch_allowed", False),
)
ITER010_LIGHTWEIGHT_STANDING_AUTHORITY_EXACT_VALUES: tuple[
    tuple[str, object], ...
] = (
    ("schema", "PUBLIC_OSS_EVALUATION_STANDING_AUTHORITY@1"),
    ("generic_schema", "PUBLIC_SOURCE_MODEL_STANDING_AUTHORITY@1"),
    ("system_contract_ref", "SYS-ADR-019"),
    ("owner_decision_ref", "ITER-010-PDR-008"),
    ("current_plan_amendment_ref", ITER010_LIGHTWEIGHT_PLAN_REVISION_REF),
    ("owner_finding_ref", "FINDING-010-140"),
    ("authority_status", "active"),
    (
        "human_authority_source",
        "existing-iter010-slice001-root-development-authorization",
    ),
    ("root_authorization_field_ref", "authorization.authorization_ref"),
    (
        "correction_ref",
        "local-user-message-utf8:sha256:"
        "6dd1e3f4c444b69539f2c9082e26f605d4b0ff84b5dcf99cfb53b42cdb334bdb",
    ),
    ("iteration_ref", "ITER-010"),
    ("slice_ref", "ITER-010-SLICE-001"),
    (
        "purpose",
        "public-open-source-direction-canary-and-web-experience-evaluation",
    ),
    ("source_origin", "https://github.com/macrozheng/mall.git"),
    ("source_license", "Apache-2.0"),
    ("source_commit", "0504e86b1f1b6f1b8aa6a734d37a90fb67346be7"),
    ("source_tree", "047d79d8588b76013c260f3f1a9565707301a60a"),
    (
        "source_revision_selection_policy",
        "same-approved-public-upstream-clean-exact-commit-after-source-authority-reverification",
    ),
    ("source_clean_required", True),
    ("source_read_only_required", True),
    ("current_provider_route_ref", "provider_route_policy"),
    (
        "fallback_admission_policy_plugin_ref",
        "deepseek_dispatch_admission_policy",
    ),
    ("preferred_current_route_budget_requires_new_human_approval", False),
    (
        "fallback_admitted_current_route_budget_requires_new_human_approval",
        False,
    ),
    ("fallback_policy_exception_requires_exact_user_override", True),
    ("clean_product_successor_requires_new_human_approval", False),
    (
        "run_turn_or_dispatch_identity_change_requires_new_human_approval",
        False,
    ),
    (
        "machine_receipt_derivation_required_per_run_turn_and_dispatch",
        True,
    ),
    ("machine_receipt_parent_digest_required", True),
    ("machine_receipt_one_use_expiry_and_consumption_required", True),
    (
        "machine_receipt_fields",
        "exact-product-source-session,provider-model-role-input-digest,disclosure,"
        "budget,time,fallback-reason,parent-authority-digest",
    ),
    (
        "invalid_or_drifted_machine_receipt_action",
        "fail-before-source-disclosure-credential-or-provider-network",
    ),
    (
        "unverified_source_revision_drift_action",
        "fail-closed-until-source-authority-reverification-not-automatic-human-request",
    ),
    (
        "same_approved_upstream_clean_revision_after_reverification_requires_new_human_approval",
        False,
    ),
    (
        "scope_delta_requires_exact_user_authorization",
        "private-unknown-dirty-or-nonpublic-source,different-upstream,"
        "provider-model-endpoint-or-credential-account-change,"
        "expanded-disclosure-or-budget,fallback-admission-policy-exception,hidden,"
        "slice2-or-slice3,write-or-nonloopback-or-production",
    ),
    ("historical_grants_and_runs_are_immutable", True),
    ("runtime_implementation_status", "not-yet-implemented-or-verified"),
    ("verification_case_id", "V-PUBLIC-OSS-AUTHORITY-001"),
    ("verification_status", "NOT-RUN"),
    ("independent_action_entry_allowed", False),
    (
        "next_execution_entry_action_id",
        "ITER-010-ACTION-USER-PLAN-RECOVERY-001",
    ),
    ("next_execution_entry_case_id", ITER010_LIGHTWEIGHT_EXPERIENCE_CASE_ID),
    (
        "current_external_execution_status",
        "standing-authority-active-runtime-receipt-required-per-dispatch",
    ),
)
ITER010_FAILURE_HANDOFF_STANDING_AUTHORITY_EXACT_VALUES: tuple[
    tuple[str, object], ...
] = tuple(
    (
        field,
        (
            ITER010_FAILURE_HANDOFF_PLAN_REVISION_REF
            if field == "current_plan_amendment_ref"
            else "locked-by-pdr011-no-new-dispatch"
        )
        if field in {"current_plan_amendment_ref", "current_external_execution_status"}
        else expected,
    )
    for field, expected in ITER010_LIGHTWEIGHT_STANDING_AUTHORITY_EXACT_VALUES
)
ITER010_LIGHTWEIGHT_AUTHORIZATION_STATE_EXACT_VALUES: tuple[
    tuple[str, object], ...
] = (
    ("current_authority_owner_ref", "public_oss_evaluation_standing_authority"),
    ("external_execution_reauthorization_required", False),
    ("human_reauthorization_required_for_current_direction_canary", False),
    ("human_reauthorization_trigger", "standing-scope-delta-only"),
    ("external_execution_authorization_status", "standing-authority-active"),
    (
        "external_execution_authorization_status_scope",
        "exact-runtime-receipt-required-per-dispatch",
    ),
    (
        "current_successor_authority_status",
        "public-oss-standing-human-authority-active-no-new-approval-required",
    ),
    (
        "current_successor_runtime_gate_status",
        "machine-receipt-required-before-each-dispatch",
    ),
)
ITER010_FAILURE_HANDOFF_AUTHORIZATION_STATE_EXACT_VALUES: tuple[
    tuple[str, object], ...
] = tuple(
    (
        field,
        (
            "not-authorized"
            if field == "external_execution_authorization_status"
            else "locked-by-pdr011-no-new-dispatch"
        ),
    )
    if field
    in {
        "external_execution_authorization_status",
        "external_execution_authorization_status_scope",
    }
    else (field, expected)
    for field, expected in ITER010_LIGHTWEIGHT_AUTHORIZATION_STATE_EXACT_VALUES
)
ITER010_PLAN_AUTHORIZATION_REFS = (
    "local-user-message-utf8:sha256:612341017bef3d98db372608d22b0d57744a96883e23dd51a6552c13da183989",
    "local-user-message-utf8:sha256:63962a3f18667dd3727dd76d72c45ae8224e40a06be2d8c12622aca3a4ef0ae5",
)
ITER010_CURRENT_ACTION_ID = "ITER-010-ACTION-DIRECTION-FREEZE-001"
ITER010_CURRENT_ACTION_CASE_ID = "V-DIRECTION-FREEZE-001"
ITER010_CURRENT_ACTION_RESULT_REF = "ITER-010-RESULT-V-DIRECTION-FREEZE-001"
ITER010_CURRENT_ACTION_RESULT_PATH = (
    "docs/project/iterations/iteration-010/results/v-direction-freeze-001.md"
)
ITER010_CURRENT_ACTION_EVIDENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/v-direction-freeze-001.json"
)
ITER010_PLAN_RECOVERY_ACTION_ID = "ITER-010-ACTION-USER-PLAN-RECOVERY-001"
ITER010_PLAN_RECOVERY_CASE_ID = "V-PLAN-RECOVERY-001"
ITER010_PLAN_RECOVERY_RESULT_REF = "ITER-010-RESULT-V-PLAN-RECOVERY-001"
ITER010_PLAN_RECOVERY_RESULT_PATH = (
    "docs/project/iterations/iteration-010/results/v-plan-recovery-001.md"
)
ITER010_PLAN_RECOVERY_EVIDENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/v-plan-recovery-001.json"
)
ITER010_PLAN_RECOVERY_VERIFIER = "ITER010_PLAN_RECOVERY@1"
ITER010_PLAN_RECOVERY_RUNNER_IDENTITY_PATHS = (
    "scripts/plan_gate.py",
    "validation/iteration_010_plan_recovery/value_gate/runner.py",
    "tests/test_iteration_010_plan_recovery.py",
)
ITER010_PLAN_RECOVERY_AUTHORIZATION_REF = (
    "local-user-message-utf8:"
    "sha256:6cf2531ab1119b67ad2010040ae1ac73f817785684fccc26111b3b70ef5fcbe5"
)
ITER010_PLAN_RECOVERY_TRUSTED_COMMIT = (
    "04e8b6cc3df2c9335b9cd6fb4e4f5a8a955c8c4e"
)
ITER010_PLAN_RECOVERY_TRUSTED_TREE = (
    "aca4b4718724d8e2b49f58c35e7ed15256d47635"
)
ITER010_PREFERRED_QUALITY_ACTION_ID = "ITER-010-ACTION-DIRECTION-QUALITY-PREFERRED-001"
ITER010_PREFERRED_QUALITY_RESULT_REF = (
    "ITER-010-RESULT-V-DIRECTION-QUALITY-PREFERRED-001"
)
ITER010_PREFERRED_QUALITY_RESULT_PATH = (
    "docs/project/iterations/iteration-010/results/v-direction-quality-preferred-001.md"
)
ITER010_PREFERRED_QUALITY_EVIDENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/v-direction-quality-preferred-001.json"
)
ITER010_FALLBACK_REFREEZE_ACTION_ID = (
    "ITER-010-ACTION-DIRECTION-FALLBACK-REFREEZE-001"
)
ITER010_FALLBACK_REFREEZE_CASE_ID = "V-DIRECTION-FALLBACK-REFREEZE-001"
ITER010_FALLBACK_REFREEZE_RESULT_REF = (
    "ITER-010-RESULT-V-DIRECTION-FALLBACK-REFREEZE-001"
)
ITER010_FALLBACK_REFREEZE_RESULT_PATH = (
    "docs/project/iterations/iteration-010/results/"
    "v-direction-fallback-refreeze-001.md"
)
ITER010_FALLBACK_REFREEZE_EVIDENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/"
    "v-direction-fallback-refreeze-001.json"
)
ITER010_FALLBACK_QUALITY_ACTION_ID = (
    "ITER-010-ACTION-DIRECTION-QUALITY-FALLBACK-001"
)
ITER010_FALLBACK_QUALITY_RESULT_REF = (
    "ITER-010-RESULT-V-DIRECTION-QUALITY-FALLBACK-001"
)
ITER010_FALLBACK_QUALITY_RESULT_PATH = (
    "docs/project/iterations/iteration-010/results/"
    "v-direction-quality-fallback-001.md"
)
ITER010_FALLBACK_QUALITY_EVIDENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/"
    "v-direction-quality-fallback-001.json"
)
ITER010_DIRECTION_FREEZE_REWORK_ACTION_ID = (
    "ITER-010-ACTION-DIRECTION-FREEZE-REWORK-001"
)
ITER010_DIRECTION_FREEZE_REWORK_CASE_ID = "V-DIRECTION-FREEZE-REWORK-001"
ITER010_DIRECTION_FREEZE_REWORK_RESULT_REF = (
    "ITER-010-RESULT-V-DIRECTION-FREEZE-REWORK-001"
)
ITER010_DIRECTION_FREEZE_REWORK_RESULT_PATH = (
    "docs/project/iterations/iteration-010/results/v-direction-freeze-rework-001.md"
)
ITER010_DIRECTION_FREEZE_REWORK_EVIDENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/v-direction-freeze-rework-001.json"
)
ITER010_DIRECTION_REWORK_ACTION_ID = "ITER-010-ACTION-DIRECTION-REWORK-001"
ITER010_DIRECTION_REWORK_CASE_ID = "V-DIRECTION-REWORK-001"
ITER010_DIRECTION_REWORK_RESULT_REF = "ITER-010-RESULT-V-DIRECTION-REWORK-001"
ITER010_DIRECTION_REWORK_RESULT_PATH = (
    "docs/project/iterations/iteration-010/results/v-direction-rework-001.md"
)
ITER010_DIRECTION_REWORK_EVIDENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/v-direction-rework-001.json"
)
ITER010_MINIMUM_WEB_ACTION_ID = "ITER-010-ACTION-MINIMUM-WEB-CHAT-001"
ITER010_MINIMUM_WEB_CASE_ID = "V-CHAT-EXPERIENCE-001"
ITER010_MINIMUM_WEB_RESULT_REF = "ITER-010-RESULT-V-MINIMUM-WEB-CHAT-001"
ITER010_MINIMUM_WEB_RESULT_PATH = (
    "docs/project/iterations/iteration-010/results/v-minimum-web-chat-001.md"
)
ITER010_MINIMUM_WEB_EVIDENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/v-minimum-web-chat-001.json"
)
ITER010_WEB_FAILURE_ACTION_ID = "ITER-010-ACTION-WEB-FAILURE-ATTRIBUTION-001"
ITER010_WEB_FAILURE_CASE_ID = "V-WEB-FAILURE-ATTRIBUTION-001"
ITER010_WEB_FAILURE_RESULT_REF = (
    "ITER-010-RESULT-V-WEB-FAILURE-ATTRIBUTION-001"
)
ITER010_WEB_FAILURE_RESULT_PATH = (
    "docs/project/iterations/iteration-010/results/v-web-failure-attribution-001.md"
)
ITER010_WEB_FAILURE_EVIDENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/v-web-failure-attribution-001.json"
)
ITER010_USER_DIRECTION_ACTION_ID = "ITER-010-ACTION-USER-DIRECTION-DECISION-001"
ITER010_USER_DIRECTION_CASE_ID = "V-PREVIEW-002"
ITER010_USER_DIRECTION_RESULT_REF = "ITER-010-RESULT-V-USER-DIRECTION-DECISION-001"
ITER010_USER_DIRECTION_RESULT_PATH = (
    "docs/project/iterations/iteration-010/results/v-user-direction-decision-001.md"
)
ITER010_USER_DIRECTION_EVIDENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/v-user-direction-decision-001.json"
)
ITER010_RESPONSIBILITY_PLAN_ACTION_ID = "ITER-010-ACTION-RESPONSIBILITY-PLAN-001"
ITER010_RESPONSIBILITY_PLAN_CASE_ID = "V-RESPONSIBILITY-PLAN-001"
ITER010_RESPONSIBILITY_PLAN_RESULT_REF = (
    "ITER-010-RESULT-V-RESPONSIBILITY-PLAN-001"
)
ITER010_RESPONSIBILITY_PLAN_RESULT_PATH = (
    "docs/project/iterations/iteration-010/results/v-responsibility-plan-001.md"
)
ITER010_RESPONSIBILITY_PLAN_EVIDENCE_PATH = (
    "docs/project/iterations/iteration-010/results/evidence/v-responsibility-plan-001.json"
)
ITER010_PUBLIC_AUTHORITY_ADMISSION_CASE_ID = (
    "V-PUBLIC-OSS-AUTHORITY-ADMISSION-001"
)
ITER010_PUBLIC_AUTHORITY_CASE_ID = "V-PUBLIC-OSS-AUTHORITY-001"
ITER010_DIRECTION_QUALITY_GATE_SCHEMA = "VALUE_FIRST_FOUR_ARM_DIRECTION_GATE@1"
ITER010_DIRECTION_QUALITY_CASE_ID = "V-DIRECTION-QUALITY-001"
ITER010_DIRECTION_QUALITY_ARMS = (
    "direct-relevant-evidence",
    "same-agent-source-only",
    "same-agent-world-model-and-source",
    "current-codex",
)
ITER010_DIRECTION_ABSOLUTE_QUALITY_RULE = (
    "zero-major-errors-material-omissions-unsupported-or-wrong-citations-"
    "false-limitations-or-boundary-errors"
)
ITER010_PLAN_LOCK_FIELDS = (
    "product_code_changes",
    "prompt_or_reviewer_changes",
    "web_canary",
    "hardening",
    "full_regression",
    "provider_dispatch",
)
ITER010_PLAN_EVIDENCE_SCHEMA = "DEVELOPMENT_PLAN_GATE_EVIDENCE@1"
ITER010_PLAN_EVIDENCE_VERIFIER = "ITER010_VALUE_GATE@1"
ITER010_PLAN_RUNNER_IDENTITY_PATHS = (
    "scripts/plan_gate.py",
    "validation/structure_world_model_iteration_010/value_gate/runner.py",
    "tests/test_iteration_010_value_gate.py",
)
ITER010_DIRECTION_PREREQUISITE_CASE_IDS = (
    "V-LAYER-ATTRIBUTION-001",
    "V-COGNITION-ELIGIBILITY-001",
    "V-FALLBACK-ROUTE-ADMISSION-001",
    "V-ALPHA-ACCESS-001",
)
ITER010_DIRECTION_FREEZE_ALLOWED_CHANGE_PATHS = (
    "validation/structure_world_model_iteration_010/value_gate/**",
    "tests/test_iteration_010_value_gate.py",
    ITER010_CURRENT_ACTION_RESULT_PATH,
    ITER010_CURRENT_ACTION_EVIDENCE_PATH,
    "docs/project/iterations/iteration-010/results/README.md",
    "docs/project/iterations/iteration-010/findings/FINDING-010-142.md",
    "docs/project/iterations/iteration-010/findings/README.md",
    "docs/project/current.md",
    "docs/project/iterations/iteration-010/manifest.yaml",
)
ITER010_DIRECTION_FREEZE_FORBIDDEN_CHANGE_PATHS = (
    "src/software_world_model/**",
    "tests/test_conversational_engineering_model.py",
    "docs/system/**",
    "docs/project/iterations/iteration-010/proposal.md",
    "docs/project/iterations/iteration-010/readiness-review.md",
    "docs/project/iterations/iteration-010/development-design/**",
    "scripts/docs.py",
    "scripts/plan_gate.py",
    ".github/workflows/**",
)
ITER010_PLAN_RECOVERY_ALLOWED_CHANGE_PATHS = (
    "validation/iteration_010_plan_recovery/value_gate/**",
    "validation/iteration_010_mvp/value_gate/**",
    "tests/test_iteration_010_plan_recovery.py",
    "tests/test_iteration_010_mvp_value_gate.py",
    "scripts/plan_gate.py",
    "tests/test_plan_gate.py",
    "scripts/docs.py",
    "tests/test_docs_gate.py",
    "AGENTS.md",
    "docs/_generated/**",
    "docs/system/**",
    "docs/project/governance/**",
    "docs/project/current.md",
    "docs/project/iterations/iteration-010/manifest.yaml",
    "docs/project/iterations/iteration-010/verification-matrix.md",
    "docs/project/iterations/iteration-010/proposal.md",
    "docs/project/iterations/iteration-010/readiness-review.md",
    "docs/project/iterations/iteration-010/development-design/**",
    "docs/project/iterations/iteration-010/README.md",
    "docs/project/iterations/iteration-010/decisions/PDR-010-complete-mvp-vertical-slice.md",
    "docs/project/iterations/iteration-010/decisions/README.md",
    "docs/project/iterations/iteration-010/findings/FINDING-010-153.md",
    "docs/project/iterations/iteration-010/findings/README.md",
    ITER010_PLAN_RECOVERY_RESULT_PATH,
    ITER010_PLAN_RECOVERY_EVIDENCE_PATH,
    "docs/project/iterations/iteration-010/results/v-pdr010-activation-001.md",
    "docs/project/iterations/iteration-010/results/evidence/v-pdr010-activation-001.json",
    "docs/project/iterations/iteration-010/results/README.md",
)
ITER010_PLAN_RECOVERY_FORBIDDEN_CHANGE_PATHS = (
    "src/**",
    "tests/test_conversational_engineering_model.py",
    "validation/structure_world_model_iteration_010/**",
    ".githooks/**",
    ".github/workflows/**",
)
ITER010_PREFERRED_QUALITY_ALLOWED_CHANGE_PATHS = (
    ITER010_PREFERRED_QUALITY_RESULT_PATH,
    ITER010_PREFERRED_QUALITY_EVIDENCE_PATH,
    "docs/project/iterations/iteration-010/results/README.md",
    "docs/project/iterations/iteration-010/findings/FINDING-010-143.md",
    "docs/project/iterations/iteration-010/findings/README.md",
    "docs/project/current.md",
    "docs/project/iterations/iteration-010/manifest.yaml",
)
ITER010_FALLBACK_REFREEZE_ALLOWED_CHANGE_PATHS = (
    ITER010_FALLBACK_REFREEZE_RESULT_PATH,
    ITER010_FALLBACK_REFREEZE_EVIDENCE_PATH,
    "docs/project/iterations/iteration-010/results/README.md",
    "docs/project/iterations/iteration-010/findings/FINDING-010-151.md",
    "docs/project/iterations/iteration-010/findings/README.md",
    "docs/project/current.md",
    "docs/project/iterations/iteration-010/manifest.yaml",
)
ITER010_FALLBACK_QUALITY_ALLOWED_CHANGE_PATHS = (
    ITER010_FALLBACK_QUALITY_RESULT_PATH,
    ITER010_FALLBACK_QUALITY_EVIDENCE_PATH,
    "docs/project/iterations/iteration-010/results/README.md",
    "docs/project/iterations/iteration-010/findings/FINDING-010-152.md",
    "docs/project/iterations/iteration-010/findings/README.md",
    "docs/project/current.md",
    "docs/project/iterations/iteration-010/manifest.yaml",
)
ITER010_DIRECTION_QUALITY_FORBIDDEN_CHANGE_PATHS = (
    "src/software_world_model/**",
    "tests/test_conversational_engineering_model.py",
    "validation/structure_world_model_iteration_010/value_gate/**",
    "tests/test_iteration_010_value_gate.py",
    "docs/system/**",
    "docs/project/iterations/iteration-010/proposal.md",
    "docs/project/iterations/iteration-010/readiness-review.md",
    "docs/project/iterations/iteration-010/development-design/**",
    "scripts/docs.py",
    "scripts/plan_gate.py",
    ".github/workflows/**",
)
ITER010_DIRECTION_FREEZE_REWORK_ALLOWED_CHANGE_PATHS = (
    "validation/structure_world_model_iteration_010/value_gate/**",
    "tests/test_iteration_010_value_gate.py",
    ITER010_DIRECTION_FREEZE_REWORK_RESULT_PATH,
    ITER010_DIRECTION_FREEZE_REWORK_EVIDENCE_PATH,
    "docs/project/iterations/iteration-010/results/README.md",
    "docs/project/iterations/iteration-010/findings/FINDING-010-144.md",
    "docs/project/iterations/iteration-010/findings/README.md",
    "docs/project/current.md",
    "docs/project/iterations/iteration-010/manifest.yaml",
)
ITER010_DIRECTION_REWORK_ALLOWED_CHANGE_PATHS = (
    ITER010_DIRECTION_REWORK_RESULT_PATH,
    ITER010_DIRECTION_REWORK_EVIDENCE_PATH,
    "docs/project/iterations/iteration-010/results/README.md",
    "docs/project/iterations/iteration-010/findings/FINDING-010-145.md",
    "docs/project/iterations/iteration-010/findings/README.md",
    "docs/project/current.md",
    "docs/project/iterations/iteration-010/manifest.yaml",
)
ITER010_DIRECTION_REWORK_FORBIDDEN_CHANGE_PATHS = (
    ITER010_DIRECTION_QUALITY_FORBIDDEN_CHANGE_PATHS
)
ITER010_MINIMUM_WEB_ALLOWED_CHANGE_PATHS = (
    ITER010_MINIMUM_WEB_RESULT_PATH,
    ITER010_MINIMUM_WEB_EVIDENCE_PATH,
    "docs/project/iterations/iteration-010/results/README.md",
    "docs/project/iterations/iteration-010/findings/FINDING-010-146.md",
    "docs/project/iterations/iteration-010/findings/README.md",
    "docs/project/current.md",
    "docs/project/iterations/iteration-010/manifest.yaml",
)
ITER010_USER_DIRECTION_ALLOWED_CHANGE_PATHS = (
    ITER010_USER_DIRECTION_RESULT_PATH,
    ITER010_USER_DIRECTION_EVIDENCE_PATH,
    "docs/project/iterations/iteration-010/results/README.md",
    "docs/project/iterations/iteration-010/findings/FINDING-010-147.md",
    "docs/project/iterations/iteration-010/findings/README.md",
    "docs/project/current.md",
    "docs/project/iterations/iteration-010/manifest.yaml",
)
ITER010_WEB_FAILURE_ALLOWED_CHANGE_PATHS = (
    ITER010_WEB_FAILURE_RESULT_PATH,
    ITER010_WEB_FAILURE_EVIDENCE_PATH,
    "docs/project/iterations/iteration-010/results/README.md",
    "docs/project/iterations/iteration-010/findings/FINDING-010-148.md",
    "docs/project/iterations/iteration-010/findings/README.md",
    "docs/project/current.md",
    "docs/project/iterations/iteration-010/manifest.yaml",
)
ITER010_GOVERNANCE_REVISION_ALLOWED_PATHS = (
    "AGENTS.md",
    "docs/_generated/**",
    "docs/system/**",
    "docs/project/current.md",
    "docs/project/governance/**",
    "docs/project/iterations/iteration-010/README.md",
    "docs/project/iterations/iteration-010/proposal.md",
    "docs/project/iterations/iteration-010/readiness-review.md",
    "docs/project/iterations/iteration-010/verification-matrix.md",
    "docs/project/iterations/iteration-010/development-design/**",
    "docs/project/iterations/iteration-010/decisions/PDR-010-post-direction-plan.md",
    "docs/project/iterations/iteration-010/decisions/README.md",
    "docs/project/iterations/iteration-010/findings/FINDING-010-150.md",
    "docs/project/iterations/iteration-010/findings/README.md",
    "docs/project/iterations/iteration-010/results/README.md",
    "docs/project/iterations/iteration-010/manifest.yaml",
    "scripts/docs.py",
    "scripts/plan_gate.py",
    "tests/test_docs_gate.py",
    "tests/test_plan_gate.py",
    ".github/workflows/plan-compliance.yml",
)
ITER010_USER_DIRECTION_GOVERNANCE_ALLOWED_CHANGE_PATHS = tuple(
    dict.fromkeys(
        (*ITER010_USER_DIRECTION_ALLOWED_CHANGE_PATHS, *ITER010_GOVERNANCE_REVISION_ALLOWED_PATHS)
    )
)
ITER010_WEB_FAILURE_GOVERNANCE_ALLOWED_CHANGE_PATHS = tuple(
    dict.fromkeys(
        (*ITER010_WEB_FAILURE_ALLOWED_CHANGE_PATHS, *ITER010_GOVERNANCE_REVISION_ALLOWED_PATHS)
    )
)
ITER010_RESPONSIBILITY_PLAN_ALLOWED_CHANGE_PATHS = tuple(
    dict.fromkeys(
        (
            ITER010_RESPONSIBILITY_PLAN_RESULT_PATH,
            ITER010_RESPONSIBILITY_PLAN_EVIDENCE_PATH,
            "docs/project/iterations/iteration-010/results/README.md",
            "docs/project/iterations/iteration-010/findings/FINDING-010-149.md",
            "docs/project/iterations/iteration-010/findings/README.md",
            *ITER010_GOVERNANCE_REVISION_ALLOWED_PATHS,
        )
    )
)
ITER010_RESPONSIBILITY_PLAN_FORBIDDEN_CHANGE_PATHS = (
    "src/software_world_model/**",
    "tests/test_conversational_engineering_model.py",
    "validation/**",
)
ITER010_DIRECTION_QUESTION_SET_RULE = (
    "system-purpose-or-entry,behavior-call-flow-and-material-side-effect,"
    "failure-authorization-or-unknown;at-least-two-unseen;no-pom-only-question"
)
ITER010_PENDING_CODEX_IDENTITY = "not-yet-frozen-by-current-action"
PROVIDER_FALLBACK_ELIGIBLE_OUTCOMES = (
    "preferred-execution-profile-unavailable",
)
PREFERRED_PROFILE_UNAVAILABLE_VERDICT = "PREFERRED_EXECUTION_PROFILE_UNAVAILABLE"
PROVIDER_ROUTE_POLICY_KEYS = {
    "schema",
    "preferred_execution_profile_ref",
    "fallback_execution_profile_ref",
    "preference_order",
    "availability_owner",
    "required_fallback_verdict",
    "product_control_flow_allowed_inputs",
    "product_control_flow_forbidden_inputs",
    "verification_case_id",
    "fallback_dispatch_requires_verification_pass",
    "preferred_unavailable_evidence_required",
    "implementation_gap_counts_as_preferred_unavailable",
    "preferred_availability_requires",
    "route_freeze_time",
    "ordered_routes_preauthorized_at_session_start",
    "ordered_route_disclosure_scopes_preauthorized_at_session_start",
    "transparent_logical_interaction_fallback_allowed",
    "user_resubmission_or_new_session_required",
    "fallback_requires_preferred_attempt_terminal_without_authorized_answer",
    "fallback_trigger",
    "fallback_eligible_outcomes",
    "structured_output_invalid_allows_fallback",
    "model_review_rejected_allows_fallback",
    "raw_http_or_outcome_without_availability_verdict_allows_fallback",
    "application_source_security_failure_allows_fallback",
    "fallback_reason_classification_required",
    "capability_failure_must_not_be_misclassified_as_unavailable",
    "structured_output_invalid_recovery",
    "model_review_rejected_recovery",
    "same_profile_application_repair_is_transport_request_retry",
    "same_profile_application_repair_bound",
    "same_profile_application_repair_exhausted_action",
    "fallback_attempt_restarts_full_chain",
    "fallback_attempt_inputs",
    "cross_attempt_intermediate_state_reuse_allowed",
    "late_preferred_result_policy",
    "late_preferred_result_overwrite_allowed",
    "post_dispatch_execution_profile_switch_requires",
    "maximum_fallback_execution_profile_attempts",
    "transport_request_retry_allowed",
    "outcome_unknown_duplicate_cost_risk_recorded",
    "peak_urgent_override_requires",
    "cost_can_reduce_answer_quality",
    "cost_gate_scope",
    "current_started_interaction_unit_must_keep_full_quality_chain",
    "unchanged_current_conformance_reuse_required",
}
STRICT_CODEX_BASELINE_ROLE = (
    "strong-external-baseline-not-oracle-not-adjudicator"
)
STRICT_CODEX_BASELINE_EXECUTION_MODE = (
    "fresh-isolated-same-question-answer-sealed-before-disclosure"
)
STRICT_CODEX_QUALITY_METRIC = "blind-paired-answer-quality-margin"
STRICT_CODEX_QUALITY_UNIT = "quality-basis-points"
STRICT_CODEX_QUALITY_COMPARISON = "at-least"
STRICT_CODEX_ALPHA_PASS_RULE = (
    "system-absolute-pass-no-per-question-regression-and-positive-blind-quality-margin"
)
STRICT_CODEX_RESULT_COMPARISON = "strict-answer-quality-superiority"
ENGINEERING_QA_ADAPTIVE_PROTOCOL_SCHEMA = (
    "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3"
)
ENGINEERING_QA_ADAPTIVE_PROTOCOL_MODE = (
    "adaptive-cognition-guided-engineering-investigation"
)
ENGINEERING_QA_REVIEWER_VERIFICATION_SCHEMA = (
    "ENGINEERING_QA_REVIEWER_VERIFICATION_INVESTIGATION@1"
)
ENGINEERING_QA_ANSWER_HIERARCHY_SCHEMA = "ENGINEERING_QA_ANSWER_HIERARCHY@3"
ENGINEERING_QA_ABLATION_SCHEMA = "ENGINEERING_QA_COGNITION_ABLATION@1"
CONVERSATIONAL_AGENT_ABLATION_SCHEMA = "CONVERSATIONAL_AGENT_ABLATION@1"
CRITICAL_ASSUMPTION_CUTOVER_SCHEMA = (
    "ITERATION_CRITICAL_ASSUMPTION_CATALOG_CUTOVER@1"
)
CRITICAL_ASSUMPTION_CURRENT_SCHEMA = (
    "ITERATION_CRITICAL_ASSUMPTION_CATALOG@1"
)
ENGINEERING_QA_NOT_AUTHORIZED = "not-authorized"
DIRECTION_PREVIEW_PRODUCT_ENTRIES = frozenset(
    {
        "loopback-product-owned-world-model-web",
        "loopback-product-owned-engineering-qa-web",
    }
)

ITER010_CURRENT_ASSUMPTIONS: dict[str, str] = {
    "A1": "软件世界模型保持为持久、版本化、可验证、可更新的软件外部认知，提问期 Source 调查只核实、补充或纠正本 Turn 认知",
    "A2": "主工程 Agent 能持续维护目标、假设、子任务和计划，依据每次观察选择 World Model/Source 受控工具并重规划，不取得直接权限",
    "A3": "每个 Turn 的 Evidence Package、自然答案与 fresh independent Review 同时保证直接答案、Citation、失败关闭和可返工性，Reviewer Finding 只回到主 Agent",
    "A4": "相同 Conversation—主 Agent—受控工具—逐 Turn Evidence/Review 协议能跨第二工程、来源组合和复杂失败泛化",
    "A5": "完整体验候选先与保留真实客户端、model、reasoning、tools 和权限的 current Codex 做严格外部比较；用户 CONTINUE 后再用同 Agent、同 Provider/model/config 且只改变认知输入的受控对照做 World Model 因果消融",
    "A6": "产品具有真正语义多轮 Conversation，而不是同 Session 的独立问答",
}
ITER010_HISTORICAL_ASSUMPTION_DIGEST = (
    "sha256:26769498135692067597a1f59e0fbbc8b82502ebd5336f7fdb033a80e3baff82"
)
ITER010_PDR004_ACTIVATION_RECEIPT = (
    "codex-user-message:sha256:"
    "f76ba3e864f6612b3dcc14c83392ec54db686fdb5653e408fa300785b97ceef5"
)
ITER010_PDR004_ACTIVATION_TIMESTAMP = "2026-08-25T05:06:07Z"
ITER010_PDR004_PLANNING_COMMIT = "b66ff9f058b92cebd78d5644ffef042753567b4d"
ITER010_PDR004_PLANNING_TREE = "30e437eea83e048e3fb59ddd90a8d1b76242d82c"
ITER010_DIRECTION_DISCOVERY_PRINCIPLE_REF = (
    "codex-user-message:sha256:"
    "27ad0abac79f239eb13793fed79f65b8a5dfd7042e1c828b63e7d8545577d88f"
)
ITER010_HISTORICAL_ASSUMPTIONS: dict[str, str] = {
    "A1": "保持软件世界模型作为持久、版本化外部认知而非手册或缓存，同时可让提问期 Source 调查核实、补充或纠正本题认知，并能证明完整认知不只是 locator 装饰",
    "A2": "独立 Investigation LLM 可以依据不可变原问题、exact World Model Cognition Context 和先前 Ledger 结果自适应提出下一步，而 Source Broker/Worker 能在不授予模型直接权限的情况下执行",
    "A3": "调查后密封、包内 Answer 和 Reviewer 独立补证可以同时保证直接答案、正确 Citation、失败关闭与真实首版体验",
    "A4": "相同认知—调查—Broker—Ledger—Package 协议能跨第二工程、来源组合和复杂失败模式泛化，不依赖问题、项目、关键词、符号、类、方法、fixture 或 Oracle 路由",
    "A5": "在不因调用次数裁剪调查或审核质量的前提下，完整认知与成熟源码 Agent 先通过零重大错误、boundary 正确且完整认知逐结论不退步的质量门；再以 locator-only/empty 同链为消融 control，证明完整认知有预提交质量或非 locator 调查成本增益，并计入建模成本与复用周期",
}
ITER010_HISTORICAL_GATE_CASES: dict[str, str] = {
    "V-ANSWER-001": "FAIL",
    "V-REVIEW-001": "FAIL",
    "V-XD-001": "FAIL",
    "V-EXPERIENCE-001": "FAIL",
    "V-WEB-000": "PASS",
    "V-WEB-001": "PASS",
    "V-PREVIEW-001": "FAIL",
    "V-REFLECT-001": "PASS",
}
IMMUTABLE_HISTORICAL_CASE_EVIDENCE: dict[tuple[str, str], str] = {
    (
        "ITER-010-RESULT-SLICE-001-STOP-REDIRECT",
        "V-REVIEW-001",
    ): (
        "run-028 证明仅投影/focus 仍可跳过 lead；"
        "`FINDING-010-077/078` deterministic regression closed，fresh live pending"
    ),
}
ITER010_CURRENT_CHAT_GATE_CASES = frozenset(
    {
        ITER010_PLAN_RECOVERY_CASE_ID,
        ITER010_CURRENT_ACTION_CASE_ID,
        ITER010_FALLBACK_REFREEZE_CASE_ID,
        ITER010_DIRECTION_QUALITY_CASE_ID,
        "V-CHAT-EXPERIENCE-001",
        "V-TIMEBOX-CHAT-001",
        "V-CHAT-QUALITY-001",
    }
)
ITER010_CURRENT_VERIFICATION_REQUIRED_PHRASES: dict[
    str, dict[str, tuple[str, ...]]
] = {
    ITER010_PLAN_RECOVERY_CASE_ID: {
        "Claim": ("用户显式改变开发计划",),
        "Frozen input / oracle": (
            "trusted `04e8b6cc3df2c9335b9cd6fb4e4f5a8a955c8c4e`",
            "exact recovery authorization",
        ),
        "Expected": (
            "runner 与自己的 Result 分提交",
            "产品代码、旧四路 runner、Provider dispatch、Web、hardening、full regression 均保持锁定",
            "PDR-010 必须在独立提交依赖该 sealed Result",
        ),
    },
    ITER010_CURRENT_ACTION_CASE_ID: {
        "Claim": ("四路方向 Gate 输入冻结",),
        "Frozen input / oracle": (
            "current Codex actual identity",
            "三道异质问题",
        ),
        "Expected": (
            "产品代码、Prompt/Reviewer、Web canary、hardening、full regression、Provider dispatch 保持锁定",
        ),
    },
    ITER010_DIRECTION_QUALITY_CASE_ID: {
        "Claim": ("四路价值比较",),
        "Frozen input / oracle": (
            "direct relevant evidence",
            "same-agent source-only",
            "same-agent World Model + source",
            "current Codex",
        ),
        "Expected": (
            "绝对质量 PASS",
            "不得输给任一对照臂",
            "总体严格超过 current Codex",
            "至少一项非 locator 世界模型贡献",
            "全体打平 FAIL",
            "成本或延迟不能补偿答案质量",
            "不得混批或合并首选与备用路线输出",
        ),
    },
    ITER010_FALLBACK_REFREEZE_CASE_ID: {
        "Claim": ("首选路线 INVALID 后把三个系统路统一冻结到备用执行配置",),
        "Frozen input / oracle": (
            "exact preferred-route Quality `INVALID` Result seal",
            "fallback admission policy plugin ref and digest",
        ),
        "Expected": (
            "人工授权请求=0",
            "三个系统路 input digest 集合",
            "no mixed batch",
            "Provider dispatch=0",
        ),
    },
    "V-ALPHA-ACCESS-001": {
        "Expected": (
            "Provider 未配置/未资格/失败如实显示而不阻塞页面",
            "立即把命令、URL、版本和限制交给用户",
            "不等待 Chat/Quality/Comparison",
        ),
    },
    "V-TIMEBOX-CHAT-001": {
        "Claim": ("逐 Turn live-attempt",),
        "Frozen input / oracle": (
            "四个微检查点",
            "实际 Quality Route PASS 后",
            "Conversation/Turn/provider dispatch",
        ),
        "Expected": (
            "60 分钟页面",
            "180 分钟同一五轮脚本前三轮方向 Alpha 交付线，未交即 timebox FAIL",
            "181—239 分钟迟到 Alpha 只作 `FAIL / REWORK` 证据",
            "240 分钟绝对停止",
            "每个检查点立即交付用户",
            "三轮停止时五轮 canary 为 `INCOMPLETE / FAIL`",
            "计划/测试/文档完成不算用户可见增量",
            "每个 Provider-dispatched Turn 分别计 live attempt",
        ),
    },
    "V-PREVIEW-002": {
        "Claim": (
            "用户基于四路严格价值 Gate、最小 Web Chat 和 A1—A6 复盘决定是否进入夯实",
        ),
        "Frozen input / oracle": ("真实 Result、限制、Findings 和假设证据",),
        "Expected": (
            "独立技术复核给出 A1—A6 exact Verdict",
            "用户实际追问、纠正、深入、总结并查看四路严格价值 Gate 后决定 CONTINUE/REWORK/REDIRECT/REJECT",
            "只有 CONTINUE 解锁 hardening",
        ),
    },
}
ACTIVE_REQUIRED_SECTIONS = {
    "iteration-index": ("Status and authorization", "Required inputs"),
    "iteration-proposal": (
        "Trigger and evidence",
        "Outcome and users",
        "Scope / non-goals",
        "Adopted system IDs",
        "Development slices and dependencies",
        "Risks and unknowns",
        "Verification and acceptance",
        "Authorization decision",
    ),
    "iteration-readiness": (
        "Reviewed exact inputs",
        "Outcome, scope and non-goals",
        "System contracts and unresolved decisions",
        "Slice, dependency and risk closure",
        "Verification readiness",
        "Authorization decision",
    ),
    "development-slice": (
        "Status and dependencies",
        "Current vs expected behavior",
        "System contracts and invariants",
        "Interfaces and affected code",
        "Compatibility, data and security boundaries",
        "Open questions and implementation risks",
        "Acceptance scenarios",
        "Findings",
    ),
}
PRODUCT_GOAL_ALIGNMENT_SECTIONS = {
    "iteration-proposal": ("Product-goal alignment and cumulative delta",),
    "iteration-readiness": ("Product-goal alignment gate",),
    "development-slice": (
        "Product-goal contribution and cumulative integration",
    ),
}
REFLECTION_GATE_REQUIRED_SECTIONS = {
    "iteration-proposal": ("Critical assumptions and falsification plan",),
    "iteration-readiness": ("Architecture reflection gate readiness",),
    "development-slice": ("Architecture reflection checkpoint",),
}
REFLECTION_RESULT_REQUIRED_SUBSECTIONS = (
    "Assumption verdicts",
    "Deviation and issue classification",
    "Layer diagnosis and mature-source-Agent comparison",
    "Findings, alternatives and next risk",
    "Decision and rationale",
)
REFLECTION_ISSUE_CLASSES = {
    "architecture",
    "implementation",
    "configuration-environment",
    "requirement-usage",
    "verification-design",
    "none",
}
REFLECTION_ISSUE_SCOPES = {"individual", "systemic", "none"}
REFLECTION_ASSUMPTION_VERDICTS = {"SUPPORTED", "FALSIFIED", "UNRESOLVED"}
PRODUCT_GOAL_ALIGNMENT_MANIFEST_SCALARS = (
    "capability_path_ref",
    "capability_path_step",
    "end_of_iteration_web_capability",
    "next_blocking_gap",
    "baseline_gap",
    "held_out_free_question_delta",
    "held_out_evaluation_owner",
    "implementation_question_visibility",
    "first_product_web_checkpoint",
    "live_ad_hoc_question_checkpoint",
)
PRODUCT_GOAL_ALIGNMENT_MANIFEST_SEQUENCES = (
    "predecessor_result_refs",
    "accepted_capability_refs",
    "new_capability_slice_refs",
    "cross_domain_cases",
    "blocking_case_ids",
    "stop_or_redirect_conditions",
)
PRODUCT_GOAL_ALIGNMENT_MANIFEST_COUNTS = (
    "held_out_question_count",
    "held_out_answerable_question_count",
    "held_out_boundary_question_count",
    "held_out_answerable_without_symbol_count_minimum",
    "held_out_answerable_without_symbol_per_project_minimum",
    "held_out_baseline_supported_count",
    "held_out_target_supported_count",
    "cross_domain_case_count",
    "live_ad_hoc_question_count",
    "live_ad_hoc_without_symbol_count_minimum",
)
PRODUCT_GOAL_ALIGNMENT_MANIFEST_DIGESTS = (
    "evaluation_project_manifest_digest",
    "held_out_suite_digest",
    "baseline_result_digest",
    "mature_source_agent_protocol_digest",
    "authorized_software_sources_digest",
)
USER_HELD_LIVE_EVALUATION_MODE = "user-held-live-after-product-code-freeze"
USER_HELD_LIVE_UNDISCLOSED = "user-held-not-disclosed"
USER_HELD_LIVE_UNMEASURED = "measured-after-product-code-freeze"
COMPLETED_ACCEPTANCE_FIELDS = (
    "accepted_scope",
    "subject_identity",
    "baseline_commit",
    "baseline_relation",
    "production_activation",
)
COMPLETED_ACCEPTANCE_SECTIONS = (
    "Exact subject and scope",
    "Gate results and limitations",
    "Finding dispositions and System write-back",
    "Verdict",
)
PRODUCT_GOAL_ALIGNMENT_ACCEPTANCE_SECTIONS = (
    "Product-goal delta and cumulative evidence",
)
PRODUCT_GOAL_ACCEPTANCE_PLACEHOLDERS = (
    "<exact-measures-and-evidence>",
    "<exact-cases-and-evidence>",
    "<exact-evidence>",
)
GOAL_ALIGNED_PROPOSAL_STATUSES = {"accepted", "authorized", "completed"}
GOAL_ALIGNED_READINESS_STATUSES = {"accepted", "authorized", "completed"}
GOAL_ALIGNED_ITERATION_STATUSES = {
    "authorized",
    "in-progress",
    "accepted",
    "completed",
    "rejected",
    "paused",
    "superseded",
}
GOAL_ALIGNED_SLICE_STATUSES = {
    "authorized",
    "in-progress",
    "completed",
    "blocked",
    "paused",
}
PRODUCT_GOAL_V000_CLAIM = (
    "本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并与既有能力完成跨域组合"
)
PRODUCT_GOAL_V000_LEVEL = "product / comparison"
PRODUCT_GOAL_V000_FROZEN_INPUT = (
    "未参与实现的真实工程；独立评测方/用户持有且实现阶段不可见的 held-out 自由问题；"
    "验收现场临时问题；旧+新知识跨域问题；成熟源码 Agent protocol"
)
PRODUCT_GOAL_V000_EXPECTED = (
    "支持率提高；重大错误为 0；逐题完整性不退步；提问时 "
    "Source/Update/Direct fallback=0；同一正式 Web 可人工验证"
)
PRODUCT_GOAL_V000_METADATA = {
    "product_goal_gate": "V-000",
    "product_goal_outcome": "user-visible-general-source-qa-delta",
    "product_goal_evaluation": "independent-hidden-plus-live-ad-hoc",
}
ENGINEERING_QA_PRODUCT_GOAL_V000_CLAIM = (
    "本轮相对 rejected baseline 可测缩短通用工程问答差距并证明完整 World Model Cognition 的独立价值"
)
ENGINEERING_QA_PRODUCT_GOAL_V000_FROZEN_INPUT = (
    "三个唯一 Slice Result；最终隐藏 10+2；现场题；完整认知、locator-only/empty 同链、成熟源码 Agent 三臂；新收据预提交 protocol"
)
ENGINEERING_QA_PRODUCT_GOAL_V000_EXPECTED = (
    "完整认知与成熟 Agent 先过零重大错误/boundary/逐结论质量门；完整认知再相对 locator control 达到预提交质量或非 locator 调查成本增益；"
    "计建模成本/复用周期；同一 Web/Citation/Source 隔离成立"
)
ENGINEERING_QA_PRODUCT_GOAL_V000_METADATA = {
    "product_goal_gate": "V-000",
    "product_goal_outcome": "user-visible-general-engineering-qa-delta",
    "product_goal_evaluation": "independent-hidden-plus-live-ad-hoc",
}
STRICT_CODEX_PRODUCT_GOAL_V000_CLAIM = (
    "本轮相对 baseline 可测缩短通用源码问答 MVP 差距，并在答案质量上严格超过 current Codex"
)
STRICT_CODEX_PRODUCT_GOAL_V000_FROZEN_INPUT = (
    "未参与实现的真实工程；独立持有的 held-out 和现场问题；exact current Codex identity/protocol；"
    "双方密封答案；随机匿名映射；独立盲评量表"
)
STRICT_CODEX_PRODUCT_GOAL_V000_EXPECTED = (
    "系统绝对质量 PASS；逐题无物质退步；总体答案质量差值严格为正；全体打平 FAIL；"
    "次级效率指标不得补偿；同一正式 Web 可人工验证"
)
PRODUCT_GOAL_RESULT_DIGEST_FIELDS = (
    "evaluation_project_manifest_digest",
    "held_out_suite_digest",
    "baseline_result_digest",
    "mature_source_agent_protocol_digest",
    "authorized_software_sources_digest",
)
PRODUCT_GOAL_RESULT_COUNT_FIELDS = (
    "held_out_question_count",
    "held_out_baseline_supported_count",
    "held_out_actual_supported_count",
    "held_out_boundary_correct_gap_count",
    "held_out_answerable_without_symbol_supported_count",
    "live_ad_hoc_without_symbol_pass_count",
    "major_error_count",
    "source_fallback_count",
    "update_fallback_count",
    "direct_fallback_count",
    "cross_domain_pass_count",
    "live_ad_hoc_pass_count",
)
PRODUCT_GOAL_RESULT_REQUIRED_SECTIONS = (
    "Claim and scope",
    "Exact inputs / baseline",
    "Execution and evidence",
    "Result, failures and limitations",
    "Findings and system write-back",
    "Validity / supersession",
)
ABSENT_EVIDENCE_VALUES = {
    "none",
    "n/a",
    "na",
    "not-applicable",
    "no-change",
    "no-evidence",
    "unknown",
    "tbd",
}


@dataclass(frozen=True)
class Document:
    path: Path
    metadata: dict[str, object]
    body: str

    @property
    def relative_path(self) -> str:
        return self.path.relative_to(REPOSITORY).as_posix()

    @property
    def identifier(self) -> str:
        return str(self.metadata["id"])


def parse_inline_list(value: str) -> list[str]:
    inner = value[1:-1].strip()
    if not inner:
        return []
    return [part.strip().strip("'\"") for part in inner.split(",") if part.strip()]


def parse_document(path: Path) -> tuple[Document | None, list[str]]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, [f"{path.relative_to(REPOSITORY)}: missing front matter"]

    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None, [f"{path.relative_to(REPOSITORY)}: unclosed front matter"]

    metadata: dict[str, object] = {}
    for number, line in enumerate(lines[1:end], 2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            errors.append(f"{path.relative_to(REPOSITORY)}:{number}: malformed metadata")
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        if not key or key in metadata:
            errors.append(f"{path.relative_to(REPOSITORY)}:{number}: invalid or duplicate key")
            continue
        if raw.startswith("[") and raw.endswith("]"):
            metadata[key] = parse_inline_list(raw)
        else:
            metadata[key] = raw.strip("'\"")

    for field in REQUIRED:
        if field not in metadata:
            errors.append(f"{path.relative_to(REPOSITORY)}: missing metadata field '{field}'")
    for field in LIST_FIELDS:
        if field in metadata and not isinstance(metadata[field], list):
            errors.append(f"{path.relative_to(REPOSITORY)}: '{field}' must be an inline list")

    body = "\n".join(lines[end + 1 :]) + "\n"
    return Document(path=path, metadata=metadata, body=body), errors


def source_paths() -> Iterable[Path]:
    for root in SCAN_ROOTS:
        for path in sorted(root.rglob("*.md")):
            relative = path.relative_to(DOCS).as_posix()
            if "/governance/templates/" in f"/{relative}":
                continue
            yield path


def load_documents() -> tuple[list[Document], list[str]]:
    documents: list[Document] = []
    errors: list[str] = []
    for path in source_paths():
        document, parse_errors = parse_document(path)
        errors.extend(parse_errors)
        if document is not None:
            documents.append(document)
    return documents, errors


def validate_markdown_links(path: Path, body: str) -> list[str]:
    errors: list[str] = []
    relative_path = path.relative_to(REPOSITORY).as_posix()
    for match in LINK_RE.finditer(body):
        target = match.group(1).strip()
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        resolved = (path.parent / target).resolve()
        try:
            resolved.relative_to(REPOSITORY)
        except ValueError:
            errors.append(f"{relative_path}: link escapes repository: {target}")
            continue
        if not resolved.exists():
            errors.append(f"{relative_path}: broken link: {target}")
    return errors


def validate_links(document: Document) -> list[str]:
    errors = validate_markdown_links(document.path, document.body)
    if not document.relative_path.startswith("docs/system/"):
        return errors

    for match in LINK_RE.finditer(document.body):
        target = match.group(1).strip().split("#", 1)[0]
        if not target or target.startswith(("http://", "https://", "mailto:")):
            continue
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        resolved = (document.path.parent / target).resolve()
        try:
            resolved.relative_to(DOCS / "project")
        except ValueError:
            continue
        errors.append(
            f"{document.relative_path}: system document links to project document: {target}"
        )
    return errors


def is_true(value: object) -> bool:
    return str(value).strip().lower() == "true"


def is_pending(value: object) -> bool:
    return str(value).strip().lower() in PENDING_VALUES


def is_absent_evidence(value: object) -> bool:
    return str(value).strip().lower() in ABSENT_EVIDENCE_VALUES


def has_unresolved_placeholder(value: object) -> bool:
    """Return whether a current-development value still contains template input."""

    if isinstance(value, dict):
        return any(
            has_unresolved_placeholder(key) or has_unresolved_placeholder(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(has_unresolved_placeholder(item) for item in value)
    return isinstance(value, str) and PLACEHOLDER_RE.search(value) is not None


def has_pending_marker(value: object) -> bool:
    if isinstance(value, dict):
        return any(has_pending_marker(item) for item in value.values())
    if isinstance(value, list):
        return any(has_pending_marker(item) for item in value)
    return isinstance(value, str) and is_pending(value)


def empty_required_sections(document: Document, required: Iterable[str]) -> list[str]:
    required = tuple(required)
    if not required:
        return []

    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in document.body.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).rstrip("#").strip()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)

    empty: list[str] = []
    for name in required:
        content = sections.get(name)
        if content is None or not any(
            line.strip() and re.match(r"^#{1,6}\s", line) is None
            for line in content
        ):
            empty.append(name)
    return empty


def markdown_section_body(document: Document, name: str) -> str | None:
    lines: list[str] = []
    active = False
    for line in document.body.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            heading_name = heading.group(1).rstrip("#").strip()
            if active:
                break
            active = heading_name == name
            continue
        if active:
            lines.append(line)
    return "\n".join(lines) if active else None


def markdown_subsection_body(text: str, name: str) -> str | None:
    lines: list[str] = []
    active = False
    for line in text.splitlines():
        heading = re.match(r"^#{1,3}\s+(.+?)\s*$", line)
        if heading:
            level = len(line) - len(line.lstrip("#"))
            heading_name = heading.group(1).rstrip("#").strip()
            if active and level <= 3:
                break
            if level == 3:
                active = heading_name == name
            continue
        if active:
            lines.append(line)
    return "\n".join(lines) if active else None


def has_substantive_markdown_content(text: str | None) -> bool:
    if text is None:
        return False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if re.fullmatch(r"\|?(?:\s*:?-+:?\s*\|)+", stripped):
            continue
        return True
    return False


def iteration_number(identifier: object) -> int | None:
    match = re.fullmatch(r"ITER-([0-9]{3,})", str(identifier).strip())
    return int(match.group(1)) if match else None


def iteration_from_document_path(path: Path) -> str | None:
    try:
        relative = path.relative_to(REPOSITORY).as_posix()
    except ValueError:
        return None
    match = re.match(
        r"^docs/project/iterations/iteration-([0-9]{3,})(?:/|$)", relative
    )
    return None if match is None else f"ITER-{match.group(1)}"


def validate_iteration_document_identity(document: Document) -> list[str]:
    try:
        relative = document.path.relative_to(REPOSITORY).as_posix()
    except ValueError:
        return []
    directory_match = re.match(
        r"^docs/project/iterations/iteration-([^/]+)(?:/|$)", relative
    )
    if directory_match is not None and re.fullmatch(
        r"[0-9]{3,}", directory_match.group(1)
    ) is None:
        return [
            f"{document.relative_path}: iteration directory must use at least three digits"
        ]

    expected = iteration_from_document_path(document.path)
    if expected is None:
        return []

    errors: list[str] = []
    actual = str(document.metadata.get("iteration", ""))
    if actual != expected:
        errors.append(
            f"{document.relative_path}: iteration must match directory {expected}"
        )
    if (
        document.metadata.get("kind") == "iteration-index"
        and document.identifier != f"{expected}-INDEX"
    ):
        errors.append(
            f"{document.relative_path}: iteration-index id must equal {expected}-INDEX"
        )
    return errors


def requires_product_goal_alignment(identifier: object) -> bool:
    number = iteration_number(identifier)
    return number is not None and number >= PRODUCT_GOAL_ALIGNMENT_START_ITERATION


def requires_reflection_gate(identifier: object) -> bool:
    number = iteration_number(identifier)
    return number is not None and number >= REFLECTION_GATE_START_ITERATION


def requires_direction_preview(identifier: object) -> bool:
    number = iteration_number(identifier)
    return number is not None and number >= DIRECTION_PREVIEW_START_ITERATION


def supports_engineering_qa_hybrid(identifier: object) -> bool:
    number = iteration_number(identifier)
    return number is not None and number >= ENGINEERING_QA_HYBRID_START_ITERATION


def requires_engineering_qa_hybrid(identifier: object) -> bool:
    """Bind the accepted ITER-010 plan without constraining later iterations."""

    return iteration_number(identifier) == ENGINEERING_QA_HYBRID_START_ITERATION


def requires_strict_codex_baseline(identifier: object) -> bool:
    """Apply the strong Codex baseline to PDR-009 and later new iterations.

    ITER-011 is a superseded planning record.  ITER-010 opted into the strict
    contract through PDR-009; ITER-012 remains the default cut-over for newly
    numbered iterations.
    """

    number = iteration_number(identifier)
    return number == 10 or (
        number is not None and number >= STRICT_CODEX_BASELINE_START_ITERATION
    )


def requires_experience_first_delivery_policy(identifier: object) -> bool:
    """Require the experience-first timebox for newly planned product iterations."""

    number = iteration_number(identifier)
    return (
        number is not None
        and number >= EXPERIENCE_FIRST_DELIVERY_START_ITERATION
    )


def requires_provider_route_policy(identifier: object) -> bool:
    """Require qualified preferred/fallback routing for planned iterations."""

    number = iteration_number(identifier)
    return number is not None and number >= PROVIDER_ROUTE_POLICY_START_ITERATION


def is_engineering_qa_adaptive_protocol(
    answer_protocol: dict[str, object],
) -> bool:
    """Identify the explicit adaptive engineering-QA protocol only."""

    return (
        answer_protocol.get("mode")
        == ENGINEERING_QA_ADAPTIVE_PROTOCOL_MODE
    )


def product_goal_v000_contract(
    iteration: object,
) -> tuple[dict[str, str], str, str, str]:
    """Return the exact user-visible product gate for the selected architecture."""

    if requires_strict_codex_baseline(iteration):
        return (
            PRODUCT_GOAL_V000_METADATA,
            STRICT_CODEX_PRODUCT_GOAL_V000_CLAIM,
            STRICT_CODEX_PRODUCT_GOAL_V000_FROZEN_INPUT,
            STRICT_CODEX_PRODUCT_GOAL_V000_EXPECTED,
        )
    if requires_engineering_qa_hybrid(iteration):
        return (
            ENGINEERING_QA_PRODUCT_GOAL_V000_METADATA,
            ENGINEERING_QA_PRODUCT_GOAL_V000_CLAIM,
            ENGINEERING_QA_PRODUCT_GOAL_V000_FROZEN_INPUT,
            ENGINEERING_QA_PRODUCT_GOAL_V000_EXPECTED,
        )
    return (
        PRODUCT_GOAL_V000_METADATA,
        PRODUCT_GOAL_V000_CLAIM,
        PRODUCT_GOAL_V000_FROZEN_INPUT,
        PRODUCT_GOAL_V000_EXPECTED,
    )


def active_required_sections(document: Document) -> tuple[str, ...]:
    kind = str(document.metadata.get("kind", ""))
    required = ACTIVE_REQUIRED_SECTIONS.get(kind, ())
    if requires_product_goal_alignment(document.metadata.get("iteration", "")):
        required += PRODUCT_GOAL_ALIGNMENT_SECTIONS.get(kind, ())
    if requires_reflection_gate(document.metadata.get("iteration", "")):
        required += REFLECTION_GATE_REQUIRED_SECTIONS.get(kind, ())
    return required


def empty_active_required_sections(document: Document) -> list[str]:
    required = active_required_sections(document)
    return empty_required_sections(document, required)


def has_substantive_body(document: Document) -> bool:
    return any(
        line.strip() and re.match(r"^#{1,6}\s", line) is None
        for line in document.body.splitlines()
    )


class SafeYamlError(ValueError):
    """Raised when a manifest is outside the deliberately small safe YAML subset."""


def _parse_yaml_scalar(value: str, line_number: int) -> object:
    value = value.strip()
    if value.startswith(("!", "&", "*", "|", ">")):
        raise SafeYamlError(
            f"line {line_number}: tags, aliases, anchors, and block scalars are not allowed"
        )
    if value.startswith(("[", "{")):
        if value in {"[]", "{}"}:
            return [] if value == "[]" else {}
        raise SafeYamlError(
            f"line {line_number}: non-empty inline collections are not supported"
        )
    if value.startswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError as error:
            raise SafeYamlError(
                f"line {line_number}: invalid double-quoted scalar"
            ) from error
        if not isinstance(parsed, str):
            raise SafeYamlError(f"line {line_number}: quoted scalar must be a string")
        return parsed
    if value.startswith("'"):
        if len(value) < 2 or not value.endswith("'"):
            raise SafeYamlError(f"line {line_number}: invalid single-quoted scalar")
        return value[1:-1].replace("''", "'")
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if re.fullmatch(r"-?(?:0|[1-9][0-9]*)", value):
        return int(value)
    return value


def safe_load_manifest(text: str) -> dict[str, object]:
    """Load a manifest as inert data and reject duplicate keys or YAML features.

    Manifests intentionally use only mappings, scalar sequences, and empty inline
    collections. Rejecting the rest keeps this gate dependency-free and fail-closed.
    """

    root: dict[str, object] = {}
    stack: list[tuple[int, dict[str, object]]] = [(-1, root)]
    sequence_containers: set[int] = set()
    collection_indents: dict[int, int | None] = {id(root): 0}
    for line_number, raw_line in enumerate(text.splitlines(), 1):
        if "\t" in raw_line:
            raise SafeYamlError(f"line {line_number}: tabs are not allowed")
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if re.search(r"\s+#", raw_line):
            raise SafeYamlError(f"line {line_number}: inline comments are not supported")
        indentation = len(raw_line) - len(raw_line.lstrip(" "))
        content = raw_line[indentation:].rstrip()
        while indentation <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        expected_indent = collection_indents[id(parent)]
        if expected_indent is None:
            collection_indents[id(parent)] = indentation
        elif indentation != expected_indent:
            raise SafeYamlError(f"line {line_number}: inconsistent indentation")

        if content == "-" or content.startswith("- "):
            item = content[1:].strip()
            if (
                len(stack) == 1
                or parent
                or not item
                or re.match(r"^[A-Za-z_][A-Za-z0-9_-]*:(?:\s|$)", item)
            ):
                raise SafeYamlError(
                    f"line {line_number}: only scalar sequence items are supported"
                )
            _parse_yaml_scalar(item, line_number)
            sequence_containers.add(id(parent))
            continue
        if ":" not in content:
            raise SafeYamlError(f"line {line_number}: expected a mapping entry")

        key, raw_value = content.split(":", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", key) or key == "<<":
            raise SafeYamlError(f"line {line_number}: invalid mapping key")
        if id(parent) in sequence_containers:
            raise SafeYamlError(f"line {line_number}: mixed mapping and sequence")
        if key in parent:
            raise SafeYamlError(f"line {line_number}: duplicate key '{key}'")

        raw_value = raw_value.strip()
        if raw_value:
            parent[key] = _parse_yaml_scalar(raw_value, line_number)
        else:
            child: dict[str, object] = {}
            parent[key] = child
            collection_indents[id(child)] = None
            stack.append((indentation, child))

    if not root:
        raise SafeYamlError("manifest is empty")
    return root


def _path_label(path: Path) -> str:
    try:
        return path.relative_to(REPOSITORY).as_posix()
    except ValueError:
        return path.as_posix()


def manifest_resolved_sequence_items(
    text: str, section: str, field: str
) -> list[str] | None:
    """Return a direct safe-YAML scalar sequence, or None when invalid/empty."""

    lines = text.splitlines()
    section_index: int | None = None
    for index, raw_line in enumerate(lines):
        if re.fullmatch(rf"{re.escape(section)}\s*:\s*", raw_line):
            section_index = index
            break
    if section_index is None:
        return None

    direct_indent: int | None = None
    field_index: int | None = None
    field_indent: int | None = None
    for index in range(section_index + 1, len(lines)):
        raw_line = lines[index]
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indentation = len(raw_line) - len(raw_line.lstrip(" "))
        if indentation == 0:
            break
        if direct_indent is None:
            direct_indent = indentation
        if indentation != direct_indent:
            continue
        match = re.fullmatch(
            rf"{re.escape(field)}\s*:\s*(.*)", raw_line.strip()
        )
        if match is None:
            continue
        if match.group(1):
            return None
        field_index = index
        field_indent = indentation
        break
    if field_index is None or field_indent is None:
        return None

    item_indent: int | None = None
    items: list[str] = []
    for raw_line in lines[field_index + 1 :]:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indentation = len(raw_line) - len(raw_line.lstrip(" "))
        if indentation <= field_indent:
            break
        content = raw_line.strip()
        if item_indent is None:
            item_indent = indentation
        if indentation != item_indent or not content.startswith("- "):
            return None
        raw_value = content[2:].strip()
        try:
            value = _parse_yaml_scalar(raw_value, 0)
        except SafeYamlError:
            return None
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            return None
        items.append(value)
    return items or None


def manifest_resolved_nested_sequence_items(
    text: str, keys: tuple[str, ...]
) -> list[str] | None:
    """Resolve a scalar block sequence at an exact nested safe-YAML key path."""

    lines = text.splitlines()
    search_start = 0
    parent_indent = -1
    field_index: int | None = None
    field_indent: int | None = None
    for key_index, key in enumerate(keys):
        found = False
        for index in range(search_start, len(lines)):
            raw_line = lines[index]
            if not raw_line.strip() or raw_line.lstrip().startswith("#"):
                continue
            indentation = len(raw_line) - len(raw_line.lstrip(" "))
            if parent_indent >= 0 and indentation <= parent_indent:
                break
            match = re.fullmatch(rf"{re.escape(key)}\s*:\s*(.*)", raw_line.strip())
            if match is None or indentation <= parent_indent:
                continue
            if match.group(1):
                return None
            found = True
            search_start = index + 1
            parent_indent = indentation
            if key_index == len(keys) - 1:
                field_index = index
                field_indent = indentation
            break
        if not found:
            return None
    if field_index is None or field_indent is None:
        return None

    item_indent: int | None = None
    items: list[str] = []
    for raw_line in lines[field_index + 1 :]:
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indentation = len(raw_line) - len(raw_line.lstrip(" "))
        if indentation <= field_indent:
            break
        content = raw_line.strip()
        if item_indent is None:
            item_indent = indentation
        if indentation != item_indent or not content.startswith("- "):
            return None
        try:
            value = _parse_yaml_scalar(content[2:].strip(), 0)
        except SafeYamlError:
            return None
        if not isinstance(value, str) or has_unresolved_placeholder(value):
            return None
        items.append(value)
    return items or None


def validate_product_goal_structured_bindings(
    alignment: dict[str, object],
    sequences: dict[str, list[str]],
    label: str,
) -> list[str]:
    errors: list[str] = []
    accepted_refs = sequences.get("accepted_capability_refs", [])
    new_refs = sequences.get("new_capability_slice_refs", [])
    cross_cases = sequences.get("cross_domain_cases", [])

    bindings = alignment.get("cross_domain_bindings")
    bound_cases: dict[str, tuple[str, str]] = {}
    if not isinstance(bindings, dict) or not bindings:
        errors.append(f"{label}: cross_domain_bindings must be a non-empty mapping")
    else:
        for binding_name, binding in bindings.items():
            if not isinstance(binding, dict):
                errors.append(
                    f"{label}: cross_domain_bindings.{binding_name} must be a mapping"
                )
                continue
            case_id = binding.get("case_id")
            accepted_ref = binding.get("accepted_capability_ref")
            new_ref = binding.get("new_slice_ref")
            if not isinstance(case_id, str) or case_id not in cross_cases:
                errors.append(
                    f"{label}: cross_domain_bindings.{binding_name}.case_id must reference cross_domain_cases"
                )
                continue
            if case_id in bound_cases:
                errors.append(
                    f"{label}: cross-domain case must have exactly one structured binding: {case_id}"
                )
            if not isinstance(accepted_ref, str) or accepted_ref not in accepted_refs:
                errors.append(
                    f"{label}: cross_domain_bindings.{binding_name}.accepted_capability_ref must reference accepted_capability_refs"
                )
            if not isinstance(new_ref, str) or new_ref not in new_refs:
                errors.append(
                    f"{label}: cross_domain_bindings.{binding_name}.new_slice_ref must reference new_capability_slice_refs"
                )
            if (
                isinstance(accepted_ref, str)
                and accepted_ref in accepted_refs
                and isinstance(new_ref, str)
                and new_ref in new_refs
            ):
                bound_cases[case_id] = (accepted_ref, new_ref)
    for case_id in cross_cases:
        if case_id not in bound_cases:
            errors.append(
                f"{label}: cross-domain case is missing a valid structured binding: {case_id}"
            )
    for new_ref in new_refs:
        if not any(bound_new_ref == new_ref for _, bound_new_ref in bound_cases.values()):
            errors.append(
                f"{label}: new slice must participate in a structured cross-domain binding: {new_ref}"
            )

    for field, expected_case_field in (
        ("web_checkpoint_binding", "first_product_web_checkpoint"),
        ("live_ad_hoc_checkpoint_binding", "live_ad_hoc_question_checkpoint"),
    ):
        binding = alignment.get(field)
        if not isinstance(binding, dict):
            errors.append(f"{label}: {field} must be a mapping")
            continue
        case_id = binding.get("case_id")
        new_ref = binding.get("new_slice_ref")
        cross_case_id = binding.get("executes_cross_domain_case_id")
        if case_id != alignment.get(expected_case_field):
            errors.append(f"{label}: {field}.case_id must match {expected_case_field}")
        if not isinstance(new_ref, str) or new_ref not in new_refs:
            errors.append(f"{label}: {field}.new_slice_ref must reference a new slice")
        if (
            not isinstance(cross_case_id, str)
            or cross_case_id not in bound_cases
        ):
            errors.append(
                f"{label}: {field}.executes_cross_domain_case_id must reference a structured cross-domain binding"
            )
        elif isinstance(new_ref, str) and bound_cases[cross_case_id][1] != new_ref:
            errors.append(
                f"{label}: {field} must execute a cross-domain case bound to the same new slice"
            )

    additional_web_bindings = alignment.get("additional_web_checkpoint_bindings")
    if additional_web_bindings is not None:
        if not isinstance(additional_web_bindings, dict):
            errors.append(
                f"{label}: additional_web_checkpoint_bindings must be a mapping"
            )
        else:
            seen_additional_cases: set[str] = set()
            for binding_name, binding in additional_web_bindings.items():
                if not isinstance(binding, dict):
                    errors.append(
                        f"{label}: additional_web_checkpoint_bindings.{binding_name} must be a mapping"
                    )
                    continue
                case_id = binding.get("case_id")
                new_ref = binding.get("new_slice_ref")
                cross_case_id = binding.get("executes_cross_domain_case_id")
                if (
                    not isinstance(case_id, str)
                    or re.fullmatch(r"V-WEB-[0-9]{3,}", case_id) is None
                    or case_id in seen_additional_cases
                    or case_id == alignment.get("first_product_web_checkpoint")
                ):
                    errors.append(
                        f"{label}: additional Web checkpoint case IDs must be unique V-WEB cases"
                    )
                else:
                    seen_additional_cases.add(case_id)
                if not isinstance(new_ref, str) or new_ref not in new_refs:
                    errors.append(
                        f"{label}: additional Web checkpoint must reference a new slice"
                    )
                if (
                    not isinstance(cross_case_id, str)
                    or cross_case_id not in bound_cases
                ):
                    errors.append(
                        f"{label}: additional Web checkpoint must execute a structured cross-domain case"
                    )
                elif (
                    isinstance(new_ref, str)
                    and bound_cases[cross_case_id][1] != new_ref
                ):
                    errors.append(
                        f"{label}: additional Web checkpoint and cross-domain case must bind the same slice"
                    )
    return errors


def reflection_gate_bindings_by_slice(
    alignment: dict[str, object],
) -> dict[str, dict[str, object]]:
    bindings = alignment.get("reflection_gate_bindings")
    if not isinstance(bindings, dict):
        return {}
    by_slice: dict[str, dict[str, object]] = {}
    for binding in bindings.values():
        if not isinstance(binding, dict):
            continue
        new_slice_ref = binding.get("new_slice_ref")
        if isinstance(new_slice_ref, str) and new_slice_ref not in by_slice:
            by_slice[new_slice_ref] = binding
    return by_slice


def critical_assumption_catalog(
    proposal: Document | None,
) -> tuple[str | None, dict[str, str], list[str]]:
    """Bind exact assumption statements to the proposal section that owns them."""

    if proposal is None:
        return None, {}, ["missing Proposal for critical assumption catalog"]
    heading_count = len(
        re.findall(
            r"(?m)^[ ]{0,3}##[ \t]+Critical assumptions and falsification plan[ \t]*#*[ \t]*$",
            proposal.body,
        )
    )
    if heading_count != 1:
        return None, {}, [
            f"{proposal.relative_path}: must contain exactly one Critical assumptions and falsification plan section"
        ]
    section = markdown_section_body(
        proposal, "Critical assumptions and falsification plan"
    )
    if not has_substantive_markdown_content(section):
        return None, {}, [
            f"{proposal.relative_path}: critical assumption catalog section is missing or empty"
        ]
    expectations: dict[str, str] = {}
    errors: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", stripped[1:-1])]
        if not cells:
            continue
        match = re.fullmatch(r"(A[1-9][0-9]*)[：:]\s*(.+)", cells[0])
        if match is None:
            if re.match(r"A[0-9]+(?=[\s：:]|$)", cells[0]):
                errors.append(
                    f"{proposal.relative_path}: malformed critical assumption row: {cells[0]}"
                )
            continue
        assumption_id, statement = match.groups()
        if assumption_id in expectations:
            errors.append(
                f"{proposal.relative_path}: duplicate critical assumption {assumption_id}"
            )
        elif len(cells) != 3 or any(
            not value.strip()
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
            for value in (statement, *cells[1:])
        ):
            errors.append(
                f"{proposal.relative_path}: {assumption_id} must use the exact resolved three-column assumption schema"
            )
        else:
            expectations[assumption_id] = statement.strip()
    if not expectations:
        errors.append(
            f"{proposal.relative_path}: critical assumption catalog must contain A-number rows"
        )
    digest = "sha256:" + hashlib.sha256(section.encode("utf-8")).hexdigest()
    return digest, expectations, errors


def conversational_agent_cutover_active(manifest: dict[str, object]) -> bool:
    policy = manifest.get("conversational_engineering_agent")
    return (
        isinstance(policy, dict)
        and policy.get("schema") == CONVERSATIONAL_ENGINEERING_AGENT_SCHEMA
        and policy.get("architecture_decision_ref") == "SYS-ADR-018"
    )


def resolved_csv_values(value: object) -> list[str]:
    if isinstance(value, str):
        values = [item.strip() for item in value.split(",")]
    elif isinstance(value, list):
        values = [str(item).strip() for item in value]
    else:
        return []
    if not values or any(not item for item in values) or len(values) != len(set(values)):
        return []
    return values


def critical_assumption_catalogs(
    proposal: Document | None,
    manifest: dict[str, object],
    label: str,
) -> tuple[
    str | None,
    dict[str, str],
    str | None,
    dict[str, str],
    list[str],
]:
    """Resolve current and historical catalogs without rewriting prior evidence."""

    proposal_digest, proposal_expectations, errors = critical_assumption_catalog(proposal)
    cutover = manifest.get("critical_assumption_catalog_cutover")
    if cutover is None:
        return (
            proposal_digest,
            proposal_expectations,
            proposal_digest,
            proposal_expectations,
            errors,
        )
    if not isinstance(cutover, dict):
        errors.append(
            f"{label}: critical_assumption_catalog_cutover must be a mapping"
        )
        return None, {}, proposal_digest, proposal_expectations, errors

    expected_keys = {
        "schema",
        "current_catalog_schema",
        "current_owner_ref",
        "current_assumption_ids",
        "current_assumptions",
        "current_catalog_digest",
        "historical_owner_ref",
        "historical_assumption_ids",
        "historical_assumptions",
        "historical_catalog_digest",
        "historical_readiness_ref",
        "historical_result_ref",
        "historical_case_ids",
        "historical_documents_immutable",
        "current_gate_reuses_historical_case_ids",
        "status",
    }
    errors.extend(
        validate_exact_mapping_keys(
            cutover,
            expected_keys,
            f"{label}: critical_assumption_catalog_cutover",
        )
    )
    exact_values: tuple[tuple[str, object], ...] = (
        ("schema", CRITICAL_ASSUMPTION_CUTOVER_SCHEMA),
        ("current_catalog_schema", CRITICAL_ASSUMPTION_CURRENT_SCHEMA),
        ("current_owner_ref", "SYS-ADR-018"),
        ("historical_owner_ref", "ITER-010-PROPOSAL@pre-PDR-004"),
        ("historical_readiness_ref", "ITER-010-READINESS"),
        (
            "historical_result_ref",
            "ITER-010-RESULT-SLICE-001-STOP-REDIRECT",
        ),
        ("historical_documents_immutable", True),
        ("current_gate_reuses_historical_case_ids", False),
        ("status", "current-catalog-active-history-preserved"),
    )
    for field, expected in exact_values:
        if cutover.get(field) != expected:
            errors.append(
                f"{label}: critical_assumption_catalog_cutover.{field} must equal {expected}"
            )

    current_assumptions = cutover.get("current_assumptions")
    if not isinstance(current_assumptions, dict):
        errors.append(
            f"{label}: critical_assumption_catalog_cutover.current_assumptions must be a mapping"
        )
        parsed_current: dict[str, str] = {}
    else:
        parsed_current = {
            str(key): str(value) for key, value in current_assumptions.items()
        }
        if (
            parsed_current != ITER010_CURRENT_ASSUMPTIONS
            or parsed_current != proposal_expectations
        ):
            errors.append(
                f"{label}: current assumption catalog must equal the frozen A1-A6 conversational architecture catalog"
            )
    current_ids = resolved_assumption_ids(cutover.get("current_assumption_ids"))
    if current_ids != list(ITER010_CURRENT_ASSUMPTIONS):
        errors.append(
            f"{label}: critical_assumption_catalog_cutover.current_assumption_ids must equal A1,A2,A3,A4,A5,A6"
        )
    current_digest = proposal_digest
    if cutover.get("current_catalog_digest") != current_digest:
        errors.append(
            f"{label}: critical_assumption_catalog_cutover.current_catalog_digest must bind the exact current A1-A6 catalog"
        )

    historical_assumptions = cutover.get("historical_assumptions")
    if not isinstance(historical_assumptions, dict) or {
        str(key): str(value) for key, value in historical_assumptions.items()
    } != ITER010_HISTORICAL_ASSUMPTIONS:
        errors.append(
            f"{label}: historical_assumptions must preserve the exact pre-PDR-004 A1-A5 catalog"
        )
    historical_ids = resolved_assumption_ids(
        cutover.get("historical_assumption_ids")
    )
    if historical_ids != list(ITER010_HISTORICAL_ASSUMPTIONS):
        errors.append(
            f"{label}: historical_assumption_ids must exactly match the preserved Proposal catalog"
        )
    if (
        cutover.get("historical_catalog_digest")
        != ITER010_HISTORICAL_ASSUMPTION_DIGEST
    ):
        errors.append(
            f"{label}: historical_catalog_digest must exactly match the preserved Proposal catalog"
        )
    historical_case_ids = resolved_csv_values(cutover.get("historical_case_ids"))
    if historical_case_ids != list(ITER010_HISTORICAL_GATE_CASES):
        errors.append(
            f"{label}: historical_case_ids must preserve the exact executed ITER-010 Case catalog"
        )
    return (
        current_digest,
        ITER010_CURRENT_ASSUMPTIONS.copy(),
        ITER010_HISTORICAL_ASSUMPTION_DIGEST,
        ITER010_HISTORICAL_ASSUMPTIONS.copy(),
        errors,
    )


def validate_planned_assumption_catalog(
    proposal: Document | None,
    manifest: dict[str, object],
    label: str,
) -> list[str]:
    """Reject malformed or drifting assumptions while an iteration is still proposed."""

    digest, expectations, _, _, errors = critical_assumption_catalogs(
        proposal, manifest, label
    )
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return errors
    critical_assumption_ids = resolved_assumption_ids(
        alignment.get("critical_assumption_ids")
    )
    if critical_assumption_ids != list(expectations):
        errors.append(
            f"{label}: critical_assumption_ids must exactly match the current assumption catalog order"
        )
    supplied_digest = alignment.get("critical_assumption_catalog_digest")
    if supplied_digest != "not-frozen-proposal-only" and supplied_digest != digest:
        errors.append(
            f"{label}: proposed critical_assumption_catalog_digest must match the exact current catalog or remain the proposal-only marker"
        )
    return errors


def resolved_direction_preview_slice_ref(
    alignment: dict[str, object], new_refs: list[str]
) -> str | None:
    """Resolve only a fully formed first-Slice direction preview binding."""

    binding = alignment.get("direction_preview_binding")
    if not isinstance(binding, dict) or len(new_refs) < 2:
        return None
    case_id = binding.get("case_id")
    new_slice_ref = binding.get("new_slice_ref")
    representative_task_count = binding.get("representative_task_count")
    decision_owner = binding.get("decision_owner")
    has_alpha = isinstance(alignment.get("alpha_direction_binding"), dict)
    status_label = (
        "direction-probe-non-acceptance-non-production"
        if has_alpha
        else "non-acceptance-non-production"
    )
    continuation_field = (
        "next_slice_requires_continue" if has_alpha else "hardening_requires_continue"
    )
    if (
        not isinstance(case_id, str)
        or re.fullmatch(r"V-PREVIEW-[0-9]{3,}", case_id) is None
        or alignment.get("direction_preview_checkpoint") != case_id
        or new_slice_ref != new_refs[0]
        or binding.get("real_product_entry")
        not in DIRECTION_PREVIEW_PRODUCT_ENTRIES
        or isinstance(representative_task_count, bool)
        or not isinstance(representative_task_count, int)
        or representative_task_count < 1
        or binding.get("status_label") != status_label
        or decision_owner != "user"
        or binding.get("allowed_decisions") not in DIRECTION_DECISION_SETS
        or binding.get(continuation_field) is not True
    ):
        return None
    return str(new_slice_ref)


def resolved_alpha_direction_slice_ref(
    alignment: dict[str, object], new_refs: list[str]
) -> str | None:
    """Resolve an optional second feedback checkpoint before hardening."""

    binding = alignment.get("alpha_direction_binding")
    preview_ref = resolved_direction_preview_slice_ref(alignment, new_refs)
    if not isinstance(binding, dict) or preview_ref is None:
        return None
    preview_index = new_refs.index(preview_ref)
    alpha_ref = binding.get("new_slice_ref")
    case_id = binding.get("case_id")
    if (
        preview_index + 2 >= len(new_refs)
        or alpha_ref != new_refs[preview_index + 1]
        or not isinstance(case_id, str)
        or re.fullmatch(r"V-PREVIEW-[0-9]{3,}", case_id) is None
        or alignment.get("alpha_direction_checkpoint") != case_id
        or binding.get("decision_owner") != "user"
        or binding.get("allowed_decisions") not in DIRECTION_DECISION_SETS
        or binding.get("engineering_hardening_requires_continue") is not True
    ):
        return None
    return str(alpha_ref)


def resolved_sustained_alpha_slice_ref(
    alignment: dict[str, object], new_refs: list[str]
) -> str | None:
    """Resolve the first sustained Web Alpha that owns the Codex comparison."""

    alpha_ref = resolved_alpha_direction_slice_ref(alignment, new_refs)
    if alpha_ref is not None:
        return alpha_ref
    experience_binding = alignment.get("experience_version_binding")
    if isinstance(experience_binding, dict):
        experience_ref = experience_binding.get("new_slice_ref")
        if isinstance(experience_ref, str) and experience_ref in new_refs:
            return experience_ref
    return resolved_direction_preview_slice_ref(alignment, new_refs)


def _validate_experience_first_delivery_policy_legacy_or_generic(
    manifest: dict[str, object],
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
    *,
    required: bool,
) -> list[str]:
    """Freeze an experience-first clock without confusing access and quality."""

    policy = manifest.get("experience_delivery_policy")
    if policy is None:
        return (
            [f"{label}: experience_delivery_policy is required"]
            if required
            else []
        )
    if not isinstance(policy, dict):
        return [f"{label}: experience_delivery_policy must be a mapping"]

    errors: list[str] = []
    if policy.get("schema") != EXPERIENCE_FIRST_DELIVERY_SCHEMA:
        errors.append(
            f"{label}: experience_delivery_policy.schema must equal "
            f"{EXPERIENCE_FIRST_DELIVERY_SCHEMA}"
        )
    historical_refs = policy.get("historical_pre_policy_result_refs")
    if isinstance(historical_refs, dict):
        # ``safe_load_manifest`` validates block-sequence syntax but leaves its
        # values opaque. File-backed validation resolves them from inert text
        # before the Result boundary is evaluated.
        pass
    elif not isinstance(historical_refs, list):
        errors.append(
            f"{label}: experience_delivery_policy.historical_pre_policy_result_refs "
            "must be a sequence"
        )
    elif len(historical_refs) != len(set(map(str, historical_refs))):
        errors.append(
            f"{label}: experience_delivery_policy.historical_pre_policy_result_refs "
            "must be unique"
        )
    else:
        for reference in historical_refs:
            if not isinstance(reference, str) or re.fullmatch(
                r"ITER-[0-9]{3}-RESULT-[A-Z0-9]+(?:-[A-Z0-9]+)*", reference
            ) is None:
                errors.append(
                    f"{label}: experience_delivery_policy.historical_pre_policy_result_refs "
                    "must contain exact Iteration Result IDs"
                )
                break
    if policy.get("historical_results_do_not_satisfy_experience_gate") is not True:
        errors.append(
            f"{label}: experience_delivery_policy."
            "historical_results_do_not_satisfy_experience_gate must be true"
        )
    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    required_historical_refs: set[str] = set()
    if isinstance(slices, dict):
        for state in slices.values():
            if not isinstance(state, dict):
                continue
            rework_refs = state.get("rework_result_refs")
            if isinstance(rework_refs, list):
                required_historical_refs.update(map(str, rework_refs))
    if isinstance(historical_refs, list):
        missing_historical_refs = sorted(
            required_historical_refs - set(map(str, historical_refs))
        )
        if missing_historical_refs:
            errors.append(
                f"{label}: experience_delivery_policy.historical_pre_policy_result_refs "
                "must preserve every failed Result predating the current experience policy: "
                + ", ".join(missing_historical_refs)
            )

    alpha_ref = resolved_sustained_alpha_slice_ref(alignment, new_refs)
    if alpha_ref is None or policy.get("owner_slice_ref") != alpha_ref:
        errors.append(
            f"{label}: experience_delivery_policy.owner_slice_ref must equal "
            "the first sustained Web Alpha Slice"
        )

    chat_cutover = conversational_agent_cutover_active(manifest)
    case_contracts = (
        ("access_case_id", r"V-ALPHA-ACCESS-[0-9]{3,}"),
        (
            "timebox_case_id",
            r"V-TIMEBOX-CHAT-[0-9]{3,}" if chat_cutover else r"V-TIMEBOX-[0-9]{3,}",
        ),
        (
            "quality_case_id",
            r"V-CHAT-QUALITY-[0-9]{3,}"
            if chat_cutover
            else r"V-(?:PRE-)?[A-Z0-9]+(?:-[A-Z0-9]+)*",
        ),
    )
    resolved_cases: dict[str, str] = {}
    for field, pattern in case_contracts:
        case_id = policy.get(field)
        if (
            not isinstance(case_id, str)
            or re.fullmatch(pattern, case_id) is None
            or case_id not in blocking_case_ids
        ):
            errors.append(
                f"{label}: experience_delivery_policy.{field} must be a "
                "matching blocking Case"
            )
        else:
            resolved_cases[field] = case_id
    if len(set(resolved_cases.values())) != len(resolved_cases):
        errors.append(
            f"{label}: experience access, timebox and quality Cases must be distinct"
        )
    if policy.get("first_user_handoff_case_id") != resolved_cases.get(
        "access_case_id"
    ):
        errors.append(
            f"{label}: experience_delivery_policy.first_user_handoff_case_id must equal access_case_id"
        )
    if alignment.get("earliest_web_micro_checkpoint") != resolved_cases.get(
        "access_case_id"
    ):
        errors.append(
            f"{label}: product_goal_alignment.earliest_web_micro_checkpoint must equal the experience access Case"
        )
    direction_confirmation_case_id = policy.get("direction_confirmation_case_id")
    if (
        not isinstance(direction_confirmation_case_id, str)
        or re.fullmatch(r"V-PREVIEW-[0-9]{3,}", direction_confirmation_case_id)
        is None
        or direction_confirmation_case_id not in blocking_case_ids
    ):
        errors.append(
            f"{label}: experience_delivery_policy.direction_confirmation_case_id must be a blocking V-PREVIEW Case"
        )
    elif direction_confirmation_case_id != alignment.get(
        "direction_preview_checkpoint"
    ):
        errors.append(
            f"{label}: experience_delivery_policy.direction_confirmation_case_id must equal product_goal_alignment.direction_preview_checkpoint"
        )
    if direction_confirmation_case_id in set(resolved_cases.values()):
        errors.append(
            f"{label}: first handoff, timebox, quality, and direction confirmation Cases must remain distinct"
        )

    exact_values: tuple[tuple[str, object], ...] = (
        (
            "start_event",
            "first-product-code-change-after-slice-authorization",
        ),
        ("page_launchable_deadline_minutes", 60),
        ("sustained_user_operable_alpha_deadline_minutes", 180),
        ("hard_stop_deadline_minutes", 240),
        ("hard_stop_action", EXPERIENCE_FIRST_DELIVERY_HARD_STOP_ACTION),
        ("access_gate_scope", "user-operable-web-and-request-path-only"),
        ("provider_readiness_blocks_first_user_handoff", False),
        ("quality_gate_scope", "user-visible-answer-quality-only"),
        ("access_pass_cannot_satisfy_quality_gate", True),
        ("availability_requires_quality_pass", False),
        ("hardening_requires_quality_pass", True),
        ("user_handoff_required_at_each_checkpoint", True),
        ("checkpoint_completion_requires_runnable_user_visible_artifact", True),
        (
            "plan_test_or_document_completion_counts_as_user_visible_increment",
            False,
        ),
        (
            "pre_first_experience_allowed_checks",
            EXPERIENCE_FIRST_DELIVERY_PRE_ACCESS_WORK,
        ),
        ("pre_first_experience_qualification_limit", 1),
        ("pre_first_experience_smoke_question_limit", 1),
        ("pre_first_experience_full_regression_allowed", False),
        ("live_attempt_unit", EXPERIENCE_FIRST_DELIVERY_LIVE_ATTEMPT_UNIT),
        ("same_failure_signature_retry_limit", 1),
        ("consecutive_no_user_visible_increment_limit", 2),
        ("no_increment_action", EXPERIENCE_FIRST_DELIVERY_NO_INCREMENT_ACTION),
        (
            "failure_diagnosis_order",
            EXPERIENCE_FIRST_FAILURE_DIAGNOSIS_ORDER,
        ),
        ("earliest_divergence_required", True),
        (
            "falsifiable_root_cause_hypothesis_required_before_prompt_schema_or_contract_change",
            True,
        ),
        ("local_minimal_reproduction_required_before_live_retry", True),
        ("unseen_adjacent_local_case_count", 2),
        (
            "live_canary_conversation_count_after_local_pass"
            if chat_cutover
            else "live_canary_question_count_after_local_pass",
            1,
        ),
        (
            "same_failure_signature_fix_limit_before_architecture_responsibility_review",
            1,
        ),
        (
            "same_failure_signature_recurrence_action",
            "stop-rule-accumulation-and-review-architecture-responsibilities",
        ),
        (
            "pre_first_experience_test_scope",
            "targeted-impact-startup-and-safety-only",
        ),
        ("full_regression_before_alpha_continue_allowed", False),
        (
            "full_regression_allowed_stages",
            "alpha-continue-hardening-and-before-formal-acceptance",
        ),
    )
    for field, expected in exact_values:
        if policy.get(field) != expected:
            errors.append(
                f"{label}: experience_delivery_policy.{field} must equal {expected}"
            )
    if chat_cutover:
        if policy.get("live_canary_turn_count") != 5:
            errors.append(
                f"{label}: experience_delivery_policy.live_canary_turn_count must equal 5 for Chat"
            )
        control = manifest.get("plan_execution_control")
        pdr009_four_arm_gate = (
            isinstance(control, dict)
            and control.get("plan_revision_ref") == ITER010_PLAN_REVISION_REF
        )
        for field, pattern in (
            ("chat_case_id", r"V-CHAT-[0-9]{3,}"),
            (
                "alpha_comparison_case_id",
                re.escape(ITER010_DIRECTION_QUALITY_CASE_ID)
                if pdr009_four_arm_gate
                else r"V-COMP-ALPHA-[0-9]{3,}",
            ),
        ):
            case_id = policy.get(field)
            if (
                not isinstance(case_id, str)
                or re.fullmatch(pattern, case_id) is None
                or case_id not in blocking_case_ids
            ):
                errors.append(
                    f"{label}: experience_delivery_policy.{field} must be a matching blocking Case"
                )
        for forbidden_field in (
            "live_canary_question_count_after_local_pass",
            "live_canary_turn_count_after_local_pass",
        ):
            if forbidden_field not in policy:
                continue
            errors.append(
                f"{label}: {forbidden_field} cannot define a Chat live-attempt unit"
            )
    return errors


def _validate_iter010_lightweight_experience_policy(
    manifest: dict[str, object],
    alignment: dict[str, object],
    blocking_case_ids: list[str],
    label: str,
    *,
    manifest_text: str | None,
) -> list[str]:
    """Validate the PDR-010/PDR-011 experience policy as a closed contract."""

    policy = manifest.get("experience_delivery_policy")
    if not isinstance(policy, dict):
        return [f"{label}: experience_delivery_policy must be a mapping"]

    errors: list[str] = []
    failure_handoff = uses_failure_handoff_iter010_plan(manifest)
    scalar_contract = (
        ITER010_FAILURE_HANDOFF_EXPERIENCE_POLICY_EXACT_VALUES
        if failure_handoff
        else ITER010_LIGHTWEIGHT_EXPERIENCE_POLICY_EXACT_VALUES
    )
    expected_scalar_values = dict(scalar_contract)
    expected_sequence_fields = {
        field
        for field, _ in ITER010_LIGHTWEIGHT_EXPERIENCE_POLICY_SEQUENCE_VALUES
    }
    expected_fields = set(expected_scalar_values) | expected_sequence_fields
    actual_fields = set(map(str, policy))
    if actual_fields != expected_fields:
        missing = sorted(expected_fields - actual_fields)
        extra = sorted(actual_fields - expected_fields)
        errors.append(
            f"{label}: lightweight experience_delivery_policy must use its closed schema"
            + (f"; missing={','.join(missing)}" if missing else "")
            + (f"; unexpected={','.join(extra)}" if extra else "")
        )
    for field, expected in scalar_contract:
        if not _exact_plan_scalar(policy.get(field), expected):
            errors.append(
                f"{label}: lightweight experience_delivery_policy.{field} "
                f"must equal {expected}"
            )

    for field, expected in ITER010_LIGHTWEIGHT_EXPERIENCE_POLICY_SEQUENCE_VALUES:
        direct = policy.get(field)
        if manifest_text is not None:
            actual = manifest_resolved_sequence_items(
                manifest_text, "experience_delivery_policy", field
            )
        elif isinstance(direct, list):
            actual = [str(item) for item in direct]
        else:
            actual = None
        if actual != list(expected):
            errors.append(
                f"{label}: lightweight experience_delivery_policy.{field} "
                f"must equal {','.join(expected)}"
            )

    forbidden_machine_clock_fields = sorted(
        str(field)
        for field in policy
        if str(field).endswith("_minutes")
        or str(field) in {"start_event", "timebox_case_id"}
    )
    if forbidden_machine_clock_fields:
        errors.append(
            f"{label}: lightweight experience policy must not retain machine timebox fields: "
            + ", ".join(forbidden_machine_clock_fields)
        )

    for field in (
        "first_operable_browser_delivery_case_id",
        "final_experience_handoff_case_id",
        "alpha_comparison_case_id",
        "direction_confirmation_case_id",
    ):
        case_id = policy.get(field)
        if case_id not in blocking_case_ids:
            errors.append(
                f"{label}: lightweight experience_delivery_policy.{field} "
                "must be a blocking Case"
            )

    first_case = policy.get("first_operable_browser_delivery_case_id")
    final_case = policy.get("final_experience_handoff_case_id")
    if first_case == final_case:
        errors.append(
            f"{label}: first operable browser delivery and final Result handoff "
            "must use distinct Cases"
        )
    if alignment.get("first_product_web_checkpoint") != first_case:
        errors.append(
            f"{label}: product_goal_alignment.first_product_web_checkpoint must "
            "equal first_operable_browser_delivery_case_id"
        )
    for field, expected in (
        ("first_operable_browser_delivery_case_id", first_case),
        ("final_experience_handoff_case_id", final_case),
    ):
        if alignment.get(field) != expected:
            errors.append(
                f"{label}: product_goal_alignment.{field} must equal {expected}"
            )
    experience_binding = alignment.get("experience_version_binding")
    if not isinstance(experience_binding, dict) or (
        experience_binding.get("case_id") != first_case
    ):
        errors.append(
            f"{label}: experience_version_binding.case_id must equal the first "
            "operable browser delivery Case"
        )
    elif (
        experience_binding.get("exact_version_visible") is not True
        or experience_binding.get("repeatable_start") is not True
        or experience_binding.get("listener_browser_execution_status")
        != "passed-and-stopped"
    ):
        errors.append(
            f"{label}: first operable browser delivery must bind a repeatably "
            "runnable, exact-version browser artifact"
        )

    control = manifest.get("plan_execution_control")
    current_action = (
        control.get("current_action") if isinstance(control, dict) else None
    )
    if not isinstance(current_action, dict):
        errors.append(
            f"{label}: lightweight ITER-010 current experience action must be a mapping"
        )
    else:
        if failure_handoff and current_action.get("id") == (
            "ITER-010-ACTION-USER-DIRECTION-DECISION-001"
        ):
            expected_action = (
                ("id", "ITER-010-ACTION-USER-DIRECTION-DECISION-001"),
                ("kind", "governance"),
                ("case_id", "V-PREVIEW-002"),
                ("result_ref", "ITER-010-RESULT-V-USER-DIRECTION-DECISION-001"),
                ("evidence_verifier", "ITER010_MVP_LIGHT@3"),
                ("coding_allowed", False),
                ("external_execution_allowed", False),
            )
        elif failure_handoff:
            expected_action = (
                ("id", "ITER-010-ACTION-USER-PLAN-RECOVERY-001"),
                ("kind", "mvp-failure-handoff"),
                ("case_id", final_case),
                ("result_ref", "ITER-010-RESULT-V-MVP-EXPERIENCE-001"),
                ("evidence_verifier", "ITER010_MVP_LIGHT@3"),
                ("coding_allowed", False),
                ("external_execution_allowed", False),
            )
        else:
            expected_action = (
                ("id", "ITER-010-ACTION-USER-PLAN-RECOVERY-001"),
                ("kind", "mvp-experience-development"),
                ("case_id", final_case),
                ("result_ref", "ITER-010-RESULT-V-MVP-EXPERIENCE-001"),
                ("coding_allowed", True),
                ("external_execution_allowed", True),
            )
        for field, expected in expected_action:
            if not _exact_plan_scalar(current_action.get(field), expected):
                errors.append(
                    f"{label}: lightweight current experience action.{field} "
                    f"must equal {expected}"
                )
        locks = control.get("locks") if isinstance(control, dict) else None
        required_locks = (
            {
                "product_code_changes",
                "prompt_or_reviewer_changes",
                "web_canary",
                "hardening",
                "full_regression",
                "provider_dispatch",
            }
            if failure_handoff
            else {"hardening", "full_regression"}
        )
        if not isinstance(locks, dict) or any(
            locks.get(lock) is not True for lock in required_locks
        ):
            errors.append(
                f"{label}: lightweight current experience action must lock "
                + (
                    "all product and execution work during the PDR-011 failure handoff"
                    if failure_handoff
                    else "hardening and full regression until user CONTINUE"
                )
            )

    action_contracts = (
        control.get("next_action_contracts") if isinstance(control, dict) else None
    )
    if isinstance(action_contracts, dict):
        result_backed_first_cases = [
            str(name)
            for name, contract in action_contracts.items()
            if isinstance(contract, dict)
            and contract.get("case_id") == first_case
            and any(
                contract.get(field)
                for field in ("result_ref", "result_path", "evidence_path")
            )
        ]
        if result_backed_first_cases:
            errors.append(
                f"{label}: first operable browser delivery requires_result=false "
                "and must not be registered as a Result-backed action: "
                + ", ".join(sorted(result_backed_first_cases))
            )
    return errors


def validate_experience_first_delivery_policy(
    manifest: dict[str, object],
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
    *,
    required: bool,
    manifest_text: str | None = None,
) -> list[str]:
    """Select the exact current policy without falling back to PDR-009."""

    policy = manifest.get("experience_delivery_policy")
    errors: list[str] = []
    if policy is None:
        if required:
            errors.append(f"{label}: experience_delivery_policy is required")
    elif not isinstance(policy, dict):
        errors.append(f"{label}: experience_delivery_policy must be a mapping")
    elif uses_lightweight_iter010_plan(manifest) or (
        uses_failure_handoff_iter010_plan(manifest)
    ):
        errors.extend(
            _validate_iter010_lightweight_experience_policy(
                manifest,
                alignment,
                blocking_case_ids,
                label,
                manifest_text=manifest_text,
            )
        )
    elif (
        isinstance(manifest.get("plan_execution_control"), dict)
        and isinstance(
            manifest["plan_execution_control"].get("plan_revision_ref"),
            str,
        )
        and (
            match := re.fullmatch(
                r"ITER-010-PDR-([0-9]{3,})",
                manifest["plan_execution_control"]["plan_revision_ref"],
            )
        )
        is not None
        and int(match.group(1)) > 10
    ):
        plan_revision_ref = manifest["plan_execution_control"][
            "plan_revision_ref"
        ]
        errors.append(
            f"{label}: {plan_revision_ref} has no registered experience policy "
            "validator; later ITER-010 revisions must define their own contract "
            "and must not fall back to the PDR-009 60/180/240-minute policy"
        )
    else:
        errors.extend(
            _validate_experience_first_delivery_policy_legacy_or_generic(
                manifest,
                alignment,
                new_refs,
                blocking_case_ids,
                label,
                required=required,
            )
        )
    return errors


def _route_policy_migration_bridge_errors(
    manifest: dict[str, object], label: str
) -> list[str]:
    """Validate the non-operable bridge required by the trusted @1 gate."""

    migration = manifest.get("provider_route_policy_migration")
    if migration is None:
        return []
    if not isinstance(migration, dict):
        return [f"{label}: provider_route_policy_migration must be a mapping"]
    errors: list[str] = []
    if set(map(str, migration)) != set(ROUTE_POLICY_MIGRATION_EXPECTED):
        errors.append(
            f"{label}: provider_route_policy_migration must contain exactly the trusted bridge fields"
        )
    for field, expected in ROUTE_POLICY_MIGRATION_EXPECTED.items():
        if migration.get(field) != expected:
            errors.append(
                f"{label}: provider_route_policy_migration.{field} must equal {expected}"
            )
    control = manifest.get("plan_execution_control")
    if not isinstance(control, dict) or control.get("plan_revision_ref") != (
        "ITER-010-PDR-010"
    ):
        errors.append(
            f"{label}: provider_route_policy_migration is limited to ITER-010-PDR-010"
        )
    action = control.get("current_action") if isinstance(control, dict) else None
    if not isinstance(action, dict) or action.get("id") != (
        "ITER-010-ACTION-USER-PLAN-RECOVERY-001"
    ):
        errors.append(
            f"{label}: provider_route_policy_migration requires the ITER-010 experience action"
        )
    policy = manifest.get("provider_route_policy")
    configurations = manifest.get("execution_profile_configurations")
    if not isinstance(policy, dict) or policy.get("schema") != (
        LEGACY_PROVIDER_ROUTE_POLICY_SCHEMA
    ):
        errors.append(
            f"{label}: provider_route_policy_migration requires the trusted legacy route schema"
        )
    if not isinstance(configurations, dict) or configurations.get("schema") != (
        LEGACY_EXECUTION_PROFILE_CONFIGURATION_SCHEMA
    ):
        errors.append(
            f"{label}: provider_route_policy_migration requires the trusted legacy execution-profile schema"
        )
    return errors


def _is_route_policy_migration_bridge(
    manifest: dict[str, object], label: str
) -> bool:
    return (
        manifest.get("provider_route_policy_migration") is not None
        and not _route_policy_migration_bridge_errors(manifest, label)
    )


def _configured_execution_profiles(
    manifest: dict[str, object], label: str
) -> tuple[dict[str, dict[str, object]], tuple[str, ...], dict[str, object] | None, list[str]]:
    """Resolve concrete identities only from immutable profile configurations."""

    errors = _route_policy_migration_bridge_errors(manifest, label)
    migration_bridge = (
        manifest.get("provider_route_policy_migration") is not None
        and not errors
    )
    policy = manifest.get("provider_route_policy")
    if not isinstance(policy, dict):
        return {}, (), None, [f"{label}: provider_route_policy must be a mapping"]

    for field in (
        "preferred_execution_profile_ref",
        "fallback_execution_profile_ref",
    ):
        value = policy.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"{label}: provider_route_policy.{field} must be a non-empty string"
            )

    configurations = manifest.get("execution_profile_configurations")
    if not isinstance(configurations, dict):
        return (
            {},
            (),
            None,
            errors
            + [f"{label}: execution_profile_configurations must be a mapping"],
        )
    expected_configuration_schema = (
        LEGACY_EXECUTION_PROFILE_CONFIGURATION_SCHEMA
        if migration_bridge
        else EXECUTION_PROFILE_CONFIGURATION_SCHEMA
    )
    if configurations.get("schema") != expected_configuration_schema:
        errors.append(
            f"{label}: execution_profile_configurations.schema must equal "
            f"{expected_configuration_schema}"
        )
    if set(map(str, configurations)) != {"schema", "preferred", "fallback"}:
        errors.append(
            f"{label}: execution_profile_configurations must contain exactly schema, preferred, and fallback"
        )

    resolved: dict[str, dict[str, object]] = {}
    identities: list[str] = []
    for role, profile_field in (
        ("preferred", "preferred_execution_profile_ref"),
        ("fallback", "fallback_execution_profile_ref"),
    ):
        profile = configurations.get(role)
        if not isinstance(profile, dict):
            errors.append(
                f"{label}: execution_profile_configurations.{role} must be a mapping"
            )
            continue
        expected_keys = PREFERRED_EXECUTION_PROFILE_CONFIGURATION_KEYS
        if role == "fallback" and not migration_bridge:
            expected_keys = FALLBACK_EXECUTION_PROFILE_CONFIGURATION_KEYS
        if set(map(str, profile)) != expected_keys:
            errors.append(
                f"{label}: execution_profile_configurations.{role} must contain exactly the model-transparent configuration fields"
            )
        resolved[role] = profile
        for field in expected_keys:
            value = profile.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(
                    f"{label}: execution_profile_configurations.{role}.{field} must be a non-empty string"
                )
        if profile.get("execution_profile_ref") != policy.get(profile_field):
            errors.append(
                f"{label}: execution_profile_configurations.{role}.execution_profile_ref "
                f"must equal provider_route_policy.{profile_field}"
            )
        for field in ("provider_identity", "model_identity"):
            value = profile.get(field)
            if isinstance(value, str) and value.strip():
                identities.append(value.strip().lower())

    preferred_ref = policy.get("preferred_execution_profile_ref")
    fallback_ref = policy.get("fallback_execution_profile_ref")
    if (
        isinstance(preferred_ref, str)
        and isinstance(fallback_ref, str)
        and preferred_ref == fallback_ref
    ):
        errors.append(
            f"{label}: preferred and fallback execution profile refs must differ"
        )
    preferred_profile = resolved.get("preferred")
    fallback_profile = resolved.get("fallback")
    primary_provider = (
        preferred_profile.get("provider_identity")
        if isinstance(preferred_profile, dict)
        else None
    )
    fallback_provider = (
        fallback_profile.get("provider_identity")
        if isinstance(fallback_profile, dict)
        else None
    )
    if (
        isinstance(primary_provider, str)
        and isinstance(fallback_provider, str)
        and primary_provider.lower() == fallback_provider.lower()
    ):
        errors.append(
            f"{label}: preferred and fallback Provider identities must differ"
        )

    plugin: dict[str, object] | None = None
    plugin_ref = None
    if isinstance(fallback_profile, dict):
        plugin_ref = fallback_profile.get("admission_policy_plugin_ref")
    if migration_bridge:
        plugin_ref = policy.get("fallback_admission_policy_plugin_ref")
    if not isinstance(plugin_ref, str) or not plugin_ref.strip():
        errors.append(
            f"{label}: execution_profile_configurations.fallback.admission_policy_plugin_ref "
            "must be a non-empty configuration reference"
        )
    else:
        candidate = manifest.get(plugin_ref)
        if not isinstance(candidate, dict):
            errors.append(
                f"{label}: execution_profile_configurations.fallback.admission_policy_plugin_ref "
                "must resolve to a configuration object"
            )
        else:
            plugin = candidate
    return resolved, tuple(dict.fromkeys(identities)), plugin, errors


_GENERIC_ROUTE_IDENTITY_TOKENS = {
    "configured",
    "primary",
    "preferred",
    "fallback",
    "provider",
    "identity",
    "model",
    "route",
}


def _configured_identity_is_present(value: object, identity: str) -> bool:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    rendered_tokens = {
        token for token in re.split(r"[^a-z0-9]+", rendered) if token
    }
    normalized_identity = re.sub(r"[^a-z0-9]+", "", identity)
    normalized_rendered = re.sub(r"[^a-z0-9]+", "", rendered)
    identity_tokens = {
        token
        for token in re.split(r"[^a-z0-9]+", identity)
        if len(token) >= 3
        and not token.isdigit()
        and token not in _GENERIC_ROUTE_IDENTITY_TOKENS
    }
    return (
        identity in rendered
        or (normalized_identity and normalized_identity in normalized_rendered)
        or bool(identity_tokens.intersection(rendered_tokens))
    )


def _configured_identity_errors(
    value: object, identities: Iterable[str], label: str
) -> list[str]:
    return [
        f"{label} must not contain configured Provider/model identity {identity}"
        for identity in identities
        if _configured_identity_is_present(value, identity)
    ]


_CONCRETE_IDENTITY_FIELD_NAMES = {
    "provider_identity",
    "model_identity",
    "provider_name",
    "model_name",
    "provider_id",
    "model_id",
    "model_ref",
    "provider_type",
    "actual_model_fingerprint",
    "primary_provider",
    "preferred_provider",
    "fallback_provider",
    "preferred_model_identity",
    "fallback_model_identity",
}
_NON_AVAILABILITY_FALLBACK_TOKENS = {
    "provider-unavailable",
    "provider-http-error",
    "provider-outcome-unknown",
    "provider-output-invalid",
    "structured-output-invalid",
    "model-review-rejected",
}


def _concrete_identity_field_errors(value: object, label: str) -> list[str]:
    errors: list[str] = []

    def visit(candidate: object, path: str) -> None:
        if isinstance(candidate, dict):
            for key, item in candidate.items():
                field = str(key).lower().replace("-", "_")
                child_path = f"{path}.{key}"
                if field in _CONCRETE_IDENTITY_FIELD_NAMES:
                    errors.append(
                        f"{child_path} is a concrete Provider/model identity input; use an execution-profile ref"
                    )
                visit(item, child_path)
        elif isinstance(candidate, list):
            for index, item in enumerate(candidate):
                visit(item, f"{path}[{index}]")

    visit(value, label)
    return errors


def _non_availability_fallback_input_errors(
    value: object, label: str
) -> list[str]:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True).lower()
    normalized = re.sub(r"[_\s]+", "-", rendered)
    return [
        f"{label} must not branch fallback on {token}"
        for token in sorted(_NON_AVAILABILITY_FALLBACK_TOKENS)
        if token in normalized
    ]


def validate_provider_route_policy(
    manifest: dict[str, object],
    text_or_label: str,
    label: str | None = None,
    *,
    required: bool,
) -> list[str]:
    """Require closed profile-role routing and availability-only fallback."""

    text = text_or_label if label is not None else None
    label = label if label is not None else text_or_label

    policy = manifest.get("provider_route_policy")
    if policy is None:
        return [f"{label}: provider_route_policy is required"] if required else []
    if not isinstance(policy, dict):
        return [f"{label}: provider_route_policy must be a mapping"]

    migration_errors = _route_policy_migration_bridge_errors(manifest, label)
    migration_bridge = (
        manifest.get("provider_route_policy_migration") is not None
        and not migration_errors
    )
    if migration_bridge:
        profiles, _, _, configuration_errors = _configured_execution_profiles(
            manifest, label
        )
        errors = list(configuration_errors)
        preferred = profiles.get("preferred")
        fallback = profiles.get("fallback")
        aliases = (
            (
                "primary_provider",
                preferred.get("provider_identity")
                if isinstance(preferred, dict)
                else None,
            ),
            (
                "preferred_model_identity",
                preferred.get("model_identity")
                if isinstance(preferred, dict)
                else None,
            ),
            (
                "fallback_provider",
                fallback.get("provider_identity")
                if isinstance(fallback, dict)
                else None,
            ),
            (
                "fallback_model_identity",
                fallback.get("model_identity")
                if isinstance(fallback, dict)
                else None,
            ),
        )
        for field, expected in aliases:
            if policy.get(field) != expected:
                errors.append(
                    f"{label}: migration bridge provider_route_policy.{field} must match execution-profile configuration"
                )
        if not isinstance(policy.get("fallback_admission_policy_plugin_ref"), str):
            errors.append(
                f"{label}: migration bridge requires the legacy fallback plugin reference"
            )
        return sorted(set(errors))
    if migration_errors:
        return migration_errors

    errors: list[str] = []
    actual_keys = set(map(str, policy))
    if actual_keys != PROVIDER_ROUTE_POLICY_KEYS:
        missing = sorted(PROVIDER_ROUTE_POLICY_KEYS - actual_keys)
        extra = sorted(actual_keys - PROVIDER_ROUTE_POLICY_KEYS)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        errors.append(
            f"{label}: provider_route_policy must contain exactly the closed generic fields"
            + (": " + "; ".join(details) if details else "")
        )
    for field in (
        "preferred_execution_profile_ref",
        "fallback_execution_profile_ref",
    ):
        value = policy.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(
                f"{label}: provider_route_policy.{field} must be a non-empty runtime configuration reference"
            )
    if (
        isinstance(policy.get("preferred_execution_profile_ref"), str)
        and policy.get("preferred_execution_profile_ref")
        == policy.get("fallback_execution_profile_ref")
    ):
        errors.append(
            f"{label}: preferred and fallback execution profile refs must be distinct"
        )

    preference_order = policy.get("preference_order")
    if not isinstance(preference_order, list) and text is not None:
        preference_order = manifest_resolved_sequence_items(
            text, "provider_route_policy", "preference_order"
        )
    if preference_order != ["preferred", "fallback"]:
        errors.append(
            f"{label}: provider_route_policy.preference_order must exactly equal preferred, fallback"
        )

    exact_values: tuple[tuple[str, object], ...] = (
        ("schema", PROVIDER_ROUTE_POLICY_SCHEMA),
        ("availability_owner", "provider-availability-boundary"),
        ("required_fallback_verdict", PREFERRED_PROFILE_UNAVAILABLE_VERDICT),
        (
            "product_control_flow_allowed_inputs",
            "route-role,execution-profile-ref-and-digest,availability-verdict",
        ),
        (
            "product_control_flow_forbidden_inputs",
            "provider-identity,model-identity",
        ),
        ("verification_case_id", "V-MODEL-TRANSPARENT-ROUTING-001"),
        ("fallback_dispatch_requires_verification_pass", True),
        (
            "fallback_requires_preferred_attempt_terminal_without_authorized_answer",
            True,
        ),
        ("preferred_unavailable_evidence_required", True),
        ("implementation_gap_counts_as_preferred_unavailable", False),
        (
            "preferred_availability_requires",
            "credential-reference-configured-current-exact-conformance-current-exact-strategy-capability-qualification-and-no-active-provider-account-or-model-hold",
        ),
        (
            "fallback_trigger",
            "sealed-provider-availability-verdict:"
            + PREFERRED_PROFILE_UNAVAILABLE_VERDICT,
        ),
        ("structured_output_invalid_allows_fallback", False),
        ("model_review_rejected_allows_fallback", False),
        (
            "raw_http_or_outcome_without_availability_verdict_allows_fallback",
            False,
        ),
        ("application_source_security_failure_allows_fallback", False),
        ("fallback_reason_classification_required", True),
        (
            "capability_failure_must_not_be_misclassified_as_unavailable",
            True,
        ),
        (
            "structured_output_invalid_recovery",
            "bounded-new-call-on-same-execution-profile-with-new-request-identity-and-receipt",
        ),
        (
            "model_review_rejected_recovery",
            "bounded-rewrite-new-call-on-same-execution-profile-with-new-request-identity-and-receipt-and-fresh-review",
        ),
        ("same_profile_application_repair_is_transport_request_retry", False),
        (
            "same_profile_application_repair_bound",
            "current-interaction-safety-and-no-progress-policy",
        ),
        (
            "same_profile_application_repair_exhausted_action",
            "fail-current-turn-with-exact-reason-without-fallback",
        ),
        (
            "route_freeze_time",
            "before-conversation-start-and-before-any-interaction-unit-dispatch",
        ),
        ("ordered_routes_preauthorized_at_session_start", True),
        (
            "ordered_route_disclosure_scopes_preauthorized_at_session_start",
            True,
        ),
        ("transparent_logical_interaction_fallback_allowed", True),
        ("user_resubmission_or_new_session_required", False),
        ("fallback_attempt_restarts_full_chain", True),
        (
            "fallback_attempt_inputs",
            "immutable-original-interaction-input-exact-relevant-application-sealed-conversation-context-when-chat-and-exact-cognition",
        ),
        ("cross_attempt_intermediate_state_reuse_allowed", False),
        ("late_preferred_result_policy", "quarantine-audit-only"),
        ("late_preferred_result_overwrite_allowed", False),
        ("maximum_fallback_execution_profile_attempts", 1),
        ("transport_request_retry_allowed", False),
        ("outcome_unknown_duplicate_cost_risk_recorded", True),
        (
            "post_dispatch_execution_profile_switch_requires",
            "new-fallback-attempt-under-same-logical-interaction-unit-preauthorized-route-and-required-availability-verdict",
        ),
        ("peak_urgent_override_requires", "audited-explicit-override"),
        ("cost_can_reduce_answer_quality", False),
        ("cost_gate_scope", "before-interaction-unit-start-only"),
        ("current_started_interaction_unit_must_keep_full_quality_chain", True),
        ("unchanged_current_conformance_reuse_required", True),
    )
    for field, expected in exact_values:
        if policy.get(field) != expected:
            errors.append(
                f"{label}: provider_route_policy.{field} must equal {expected}"
            )
    fallback_eligible_outcomes = policy.get("fallback_eligible_outcomes")
    if not isinstance(fallback_eligible_outcomes, list) and text is not None:
        fallback_eligible_outcomes = manifest_resolved_sequence_items(
            text, "provider_route_policy", "fallback_eligible_outcomes"
        )
    if fallback_eligible_outcomes != list(PROVIDER_FALLBACK_ELIGIBLE_OUTCOMES):
        errors.append(
            f"{label}: provider_route_policy.fallback_eligible_outcomes must "
            "equal the trusted preferred execution-profile unavailable outcome"
        )
    _, identities, _, configuration_errors = _configured_execution_profiles(
        manifest, label
    )
    errors.extend(configuration_errors)
    errors.extend(
        _configured_identity_errors(
            policy,
            identities,
            f"{label}: provider_route_policy must remain generic and",
        )
    )
    errors.extend(
        _concrete_identity_field_errors(
            policy,
            f"{label}: provider_route_policy",
        )
    )
    return errors


def validate_model_transparent_plan_routing(
    manifest: dict[str, object], label: str
) -> list[str]:
    """Keep configured Provider/model identities out of executable semantics."""

    policy = manifest.get("provider_route_policy")
    if not isinstance(policy, dict):
        control = manifest.get("plan_execution_control")
        if (
            isinstance(control, dict)
            and control.get("plan_revision_ref") == ITER010_PLAN_REVISION_REF
        ):
            return [f"{label}: provider_route_policy is required for ITER-010"]
        return []
    _, identities, _, errors = _configured_execution_profiles(manifest, label)

    scopes = {
        "plan_execution_control": manifest.get("plan_execution_control"),
        "direction_quality_gate": manifest.get("direction_quality_gate"),
    }
    for scope_name, scope in scopes.items():
        if scope is None:
            continue
        errors.extend(
            _configured_identity_errors(
                scope,
                identities,
                f"{label}: {scope_name} must use preferred/fallback route roles and",
            )
        )
        errors.extend(
            _concrete_identity_field_errors(
                scope,
                f"{label}: {scope_name}",
            )
        )
        errors.extend(
            _non_availability_fallback_input_errors(
                scope,
                f"{label}: {scope_name}",
            )
        )
    return errors


def validate_model_transparent_governance_templates(
    manifest: dict[str, object],
    label: str,
    *,
    template_paths: Iterable[Path] | None = None,
) -> list[str]:
    """Keep configured Provider/model identities out of reusable templates."""

    _, identities, _, errors = _configured_execution_profiles(manifest, label)
    if not identities:
        return errors

    if template_paths is None:
        template_root = DOCS / "project" / "governance" / "templates"
        template_paths = sorted(
            path
            for path in template_root.rglob("*")
            if path.is_file() and path.suffix.lower() in {".md", ".yaml", ".yml"}
        )

    for path in template_paths:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            errors.append(f"{label}: cannot read governance template {path}: {error}")
            continue
        for identity in identities:
            if _configured_identity_is_present(content, identity):
                try:
                    path_label = path.relative_to(REPOSITORY).as_posix()
                except ValueError:
                    path_label = path.as_posix()
                errors.append(
                    f"{label}: reusable governance template {path_label} must not "
                    f"contain configured Provider/model identity {identity}"
                )
    return errors


def iter010_pending_codex_identity_allowed(
    manifest: dict[str, object] | None,
) -> bool:
    """Return whether the active plan has not reached its comparison freeze yet."""

    if not isinstance(manifest, dict):
        return False
    control = manifest.get("plan_execution_control")
    gate = manifest.get("direction_quality_gate")
    if not isinstance(control, dict) or not isinstance(gate, dict):
        return False
    current_action = control.get("current_action")
    legacy_current_identity = (
        (ITER010_CURRENT_ACTION_ID, ITER010_CURRENT_ACTION_CASE_ID),
        (ITER010_PLAN_RECOVERY_ACTION_ID, ITER010_PLAN_RECOVERY_CASE_ID),
    )
    legacy_pending = (
        control.get("plan_revision_ref") == ITER010_PLAN_REVISION_REF
        and isinstance(current_action, dict)
        and (current_action.get("id"), current_action.get("case_id"))
        in legacy_current_identity
        and current_action.get("status") == "authorized"
        and gate.get("status") == "locked-until-direction-freeze-pass"
    )
    experience_first_pending = (
        control.get("plan_revision_ref") == ITER010_LIGHTWEIGHT_PLAN_REVISION_REF
        and isinstance(current_action, dict)
        and current_action.get("case_id") == ITER010_LIGHTWEIGHT_EXPERIENCE_CASE_ID
        and current_action.get("status") == "authorized"
        and gate.get("status") == "post-experience-quality-policy-not-current-action"
    )
    failure_handoff_pending = (
        control.get("plan_revision_ref")
        == ITER010_FAILURE_HANDOFF_PLAN_REVISION_REF
        and isinstance(current_action, dict)
        and current_action.get("status") == "authorized"
        and gate.get("status") == "post-experience-quality-policy-not-current-action"
    )
    return legacy_pending or experience_first_pending or failure_handoff_pending


def validate_strict_codex_baseline_alignment(
    alignment: dict[str, object],
    label: str,
    *,
    allow_pending_identity: bool = False,
) -> list[str]:
    """Freeze a blind answer-quality gate that secondary metrics cannot replace."""

    errors: list[str] = []
    identity_digest = alignment.get("mature_source_agent_identity_digest")
    identity_is_pending_freeze = (
        allow_pending_identity
        and identity_digest == ITER010_PENDING_CODEX_IDENTITY
    )
    if not identity_is_pending_freeze and (
        not isinstance(identity_digest, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", identity_digest) is None
    ):
        errors.append(
            f"{label}: mature_source_agent_identity_digest must be an exact sha256 digest"
            + (
                f" or {ITER010_PENDING_CODEX_IDENTITY} before the active ITER-010 plan reaches its comparison freeze"
                if allow_pending_identity
                else ""
            )
        )
    for field, expected in (
        ("mature_source_agent_role", STRICT_CODEX_BASELINE_ROLE),
        (
            "mature_source_agent_execution_mode",
            STRICT_CODEX_BASELINE_EXECUTION_MODE,
        ),
        ("positive_value_metric", STRICT_CODEX_QUALITY_METRIC),
        ("positive_value_unit", STRICT_CODEX_QUALITY_UNIT),
        ("positive_value_comparison", STRICT_CODEX_QUALITY_COMPARISON),
        ("held_out_evaluation_owner", "independent-evaluator"),
        ("positive_value_adjudication_owner", "independent-evaluator"),
    ):
        if alignment.get(field) != expected:
            errors.append(f"{label}: {field} must equal {expected}")
    threshold = alignment.get("positive_value_threshold")
    if (
        isinstance(threshold, bool)
        or not isinstance(threshold, int)
        or threshold < 1
    ):
        errors.append(
            f"{label}: positive_value_threshold must be a positive integer so a tie cannot pass"
        )
    if alignment.get("secondary_metrics_can_compensate_answer_quality") is not False:
        errors.append(
            f"{label}: secondary_metrics_can_compensate_answer_quality must be false"
        )
    return errors


def validate_alpha_agent_comparison_binding(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
) -> list[str]:
    """Bind a blocking blind Codex comparison to the first sustained Web Alpha."""

    binding = alignment.get("alpha_agent_comparison_binding")
    if not isinstance(binding, dict):
        return [f"{label}: alpha_agent_comparison_binding must be a mapping"]
    errors: list[str] = []
    case_id = binding.get("case_id")
    if binding.get("result_role") == (
        "post-experience-strict-superiority-direction-evidence"
    ):
        required_values: tuple[tuple[str, object], ...] = (
            ("case_id", ITER010_DIRECTION_QUALITY_CASE_ID),
            ("new_slice_ref", "ITER-010-SLICE-001"),
            ("occurs_after_complete_browser_experience", True),
            ("question_set_rule", "heterogeneous-no-pom-only"),
            ("arms", "complete-world-model-system,current-codex"),
            ("protocol_digest_ref", "mature_source_agent_protocol_digest"),
            ("rubric_digest_ref", "mature_source_agent_rubric_digest"),
            ("identity_digest_ref", "mature_source_agent_identity_digest"),
            ("pass_rule", STRICT_CODEX_ALPHA_PASS_RULE),
            ("all_tie_outcome", "FAIL"),
            ("secondary_metric_compensation_allowed", False),
            ("current_codex_is_oracle_or_reviewer", False),
            (
                "external_codex_runtime",
                "preserve-actual-model-reasoning-tools-permissions-and-budget",
            ),
            (
                "shared_evaluation_inputs",
                "same-exact-revision-questions-authorized-source-scope-output-constraints-and-blind-rubric",
            ),
            (
                "technical_adjudication_owner",
                "independent-evaluator-not-answer-generator",
            ),
            ("product_direction_decision_owner", "user"),
            ("full_four_arm_causal_ablation_requires_user_continue", True),
        )
        for field, expected in required_values:
            if binding.get(field) != expected:
                errors.append(
                    f"{label}: post-experience alpha_agent_comparison_binding.{field} must equal {expected}"
                )
        question_count = binding.get("question_count")
        unseen_count = binding.get("unseen_question_count_minimum")
        if (
            isinstance(question_count, bool)
            or not isinstance(question_count, int)
            or question_count < 3
        ):
            errors.append(
                f"{label}: post-experience comparison question_count must be at least 3"
            )
        if (
            isinstance(unseen_count, bool)
            or not isinstance(unseen_count, int)
            or unseen_count < 2
            or not isinstance(question_count, int)
            or isinstance(question_count, bool)
            or unseen_count > question_count
        ):
            errors.append(
                f"{label}: post-experience comparison unseen_question_count_minimum must be between 2 and question_count"
            )
        if case_id not in blocking_case_ids:
            errors.append(
                f"{label}: post-experience comparison Case must remain blocking"
            )
        return errors
    if binding.get("result_role") == (
        "blocking-iter010-strict-superiority-direction-gate"
    ):
        if (
            case_id != ITER010_DIRECTION_QUALITY_CASE_ID
            or case_id not in blocking_case_ids
        ):
            errors.append(
                f"{label}: ITER-010 four-arm comparison case_id must equal "
                f"{ITER010_DIRECTION_QUALITY_CASE_ID} and remain blocking"
            )
        if binding.get("new_slice_ref") != "ITER-010-SLICE-001":
            errors.append(
                f"{label}: ITER-010 four-arm comparison must belong to ITER-010-SLICE-001"
            )
        if binding.get("arms") != ",".join(ITER010_DIRECTION_QUALITY_ARMS):
            errors.append(
                f"{label}: ITER-010 alpha_agent_comparison_binding.arms must equal the exact four-arm order"
            )
        if binding.get("current_codex_is_oracle_or_reviewer") is not False:
            errors.append(
                f"{label}: current Codex must not be Oracle or reviewer"
            )
        return errors
    if (
        not isinstance(case_id, str)
        or re.fullmatch(r"V-COMP-ALPHA-[0-9]{3,}", case_id) is None
        or case_id not in blocking_case_ids
    ):
        errors.append(
            f"{label}: Alpha Agent comparison case_id must be a blocking V-COMP-ALPHA-NNN Case"
        )
    alpha_ref = resolved_sustained_alpha_slice_ref(alignment, new_refs)
    if alpha_ref is None or binding.get("new_slice_ref") != alpha_ref:
        errors.append(
            f"{label}: Alpha Agent comparison must belong to the first sustained Web Alpha"
        )
    if binding.get("result_role") == (
        "direction-signal-not-iteration-012-strict-superiority-gate"
    ):
        exact_values: tuple[tuple[str, object], ...] = (
            ("occurs_after_chat_access_and_five_turn_canary", True),
            (
                "arms",
                "same-agent-source-only,same-agent-full-world-model-cognition-and-source,current-codex-external-baseline",
            ),
            ("current_codex_is_oracle_or_reviewer", False),
            (
                "system_arm_shared_runtime",
                "same-lead-agent-model-tools-permissions-budget-cache-policy-and-state",
            ),
            (
                "external_codex_runtime",
                "preserve-actual-model-reasoning-tools-permissions-and-budget",
            ),
            (
                "shared_evaluation_inputs",
                "same-exact-revision-questions-authorized-source-scope-output-constraints-and-blind-rubric",
            ),
            ("forced_runtime_identity_across_all_three_arms", False),
            (
                "technical_adjudication_owner",
                "independent-evaluator-not-answer-generator",
            ),
            ("product_direction_decision_owner", "user"),
        )
        for field, expected in exact_values:
            if binding.get(field) != expected:
                errors.append(
                    f"{label}: alpha_agent_comparison_binding.{field} must equal {expected}"
                )
        return errors
    question_count = binding.get("question_count")
    if (
        isinstance(question_count, bool)
        or not isinstance(question_count, int)
        or question_count < 3
    ):
        errors.append(
            f"{label}: Alpha Agent comparison question_count must be at least 3"
        )
    for field, expected in (
        (
            "question_set_rule",
            "original-failure-plus-two-heterogeneous-including-post-freeze-live",
        ),
        ("protocol_digest_ref", "mature_source_agent_protocol_digest"),
        ("rubric_digest_ref", "mature_source_agent_rubric_digest"),
        ("identity_digest_ref", "mature_source_agent_identity_digest"),
        ("pass_rule", STRICT_CODEX_ALPHA_PASS_RULE),
        ("all_tie_outcome", "FAIL"),
    ):
        if binding.get(field) != expected:
            errors.append(
                f"{label}: alpha_agent_comparison_binding.{field} must equal {expected}"
            )
    if "tie_outcome" in binding:
        errors.append(
            f"{label}: alpha_agent_comparison_binding.tie_outcome is ambiguous; "
            "use all_tie_outcome only"
        )
    post_freeze_live_question_count = binding.get(
        "post_freeze_live_question_count"
    )
    if (
        isinstance(post_freeze_live_question_count, bool)
        or not isinstance(post_freeze_live_question_count, int)
        or post_freeze_live_question_count < 1
        or not isinstance(question_count, int)
        or isinstance(question_count, bool)
        or post_freeze_live_question_count > question_count
    ):
        errors.append(
            f"{label}: alpha_agent_comparison_binding.post_freeze_live_question_count "
            "must be a positive integer no greater than question_count"
        )
    if binding.get("secondary_metric_compensation_allowed") is not False:
        errors.append(
            f"{label}: Alpha Agent comparison cannot allow secondary metrics to compensate answer quality"
        )
    return errors


def validate_direction_preview_binding(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
) -> list[str]:
    """Require an auditable, non-acceptance preview before hardening."""

    errors: list[str] = []
    binding = alignment.get("direction_preview_binding")
    if not isinstance(binding, dict):
        return [f"{label}: direction_preview_binding must be a mapping"]
    if len(new_refs) < 2:
        errors.append(
            f"{label}: direction preview requires a later hardening or final Slice"
        )
    case_id = binding.get("case_id")
    if (
        not isinstance(case_id, str)
        or re.fullmatch(r"V-PREVIEW-[0-9]{3,}", case_id) is None
    ):
        errors.append(
            f"{label}: direction_preview_binding.case_id must match V-PREVIEW-NNN"
        )
    else:
        if alignment.get("direction_preview_checkpoint") != case_id:
            errors.append(
                f"{label}: direction_preview_checkpoint must match direction_preview_binding.case_id"
            )
        if case_id not in blocking_case_ids:
            errors.append(f"{label}: direction preview Case must be blocking")
    new_slice_ref = binding.get("new_slice_ref")
    if not new_refs or new_slice_ref != new_refs[0]:
        errors.append(
            f"{label}: direction_preview_binding.new_slice_ref must equal the first new capability Slice"
        )
    real_product_entry = binding.get("real_product_entry")
    if real_product_entry not in DIRECTION_PREVIEW_PRODUCT_ENTRIES:
        errors.append(
            f"{label}: direction_preview_binding.real_product_entry must equal "
            "loopback-product-owned-world-model-web or "
            "loopback-product-owned-engineering-qa-web"
        )
    representative_task_count = binding.get("representative_task_count")
    if (
        isinstance(representative_task_count, bool)
        or not isinstance(representative_task_count, int)
        or representative_task_count < 1
    ):
        errors.append(
            f"{label}: direction preview representative_task_count must be positive"
        )
    has_alpha = isinstance(alignment.get("alpha_direction_binding"), dict)
    status_label = (
        "direction-probe-non-acceptance-non-production"
        if has_alpha
        else "non-acceptance-non-production"
    )
    if binding.get("status_label") != status_label:
        errors.append(
            f"{label}: direction preview status_label must equal {status_label}"
        )
    decision_owner = binding.get("decision_owner")
    if decision_owner != "user":
        errors.append(
            f"{label}: direction preview decision_owner must equal user"
        )
    if binding.get("allowed_decisions") not in DIRECTION_DECISION_SETS:
        errors.append(
            f"{label}: direction preview allowed_decisions must include CONTINUE, REWORK, REDIRECT and REJECT (legacy manifests may omit REWORK)"
        )
    continuation_field = (
        "next_slice_requires_continue" if has_alpha else "hardening_requires_continue"
    )
    if binding.get(continuation_field) is not True:
        errors.append(
            f"{label}: direction preview must require CONTINUE before its next Slice"
        )
    return errors


def validate_alpha_direction_binding(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
) -> list[str]:
    """Validate an optional user-visible checkpoint between probe and hardening."""

    binding = alignment.get("alpha_direction_binding")
    if binding is None:
        return []
    if not isinstance(binding, dict):
        return [f"{label}: alpha_direction_binding must be a mapping"]
    errors: list[str] = []
    if resolved_alpha_direction_slice_ref(alignment, new_refs) is None:
        errors.append(f"{label}: Alpha checkpoint must immediately follow the direction probe and precede hardening")
    for field, pattern in (
        ("case_id", r"V-PREVIEW-[0-9]{3,}"),
        ("web_case_id", r"V-WEB-[0-9]{3,}"),
        ("live_ad_hoc_case_id", r"V-ADHOC-[0-9]{3,}"),
    ):
        value = binding.get(field)
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None or value not in blocking_case_ids:
            errors.append(f"{label}: Alpha {field} must be a blocking Case matching {pattern}")
    return errors


def validate_experience_version_binding(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
    *,
    required: bool = False,
) -> list[str]:
    """Validate the opt-in contract that distinguishes a usable Web version from a one-shot run."""

    binding = alignment.get("experience_version_binding")
    if binding is None:  # Historical manifests predate this contract.
        return [f"{label}: experience_version_binding is required"] if required else []
    if not isinstance(binding, dict):
        return [f"{label}: experience_version_binding must be a mapping"]
    errors: list[str] = []
    schema = binding.get("schema")
    if schema not in {"USER_EXPERIENCE_VERSION@1", ENGINEERING_CHAT_EXPERIENCE_SCHEMA}:
        errors.append(
            f"{label}: experience_version_binding.schema must equal "
            "USER_EXPERIENCE_VERSION@1 or ENGINEERING_CHAT_EXPERIENCE@1"
        )
    case_id = binding.get("case_id")
    case_pattern = (
        r"V-CHAT-EXPERIENCE-[0-9]{3,}"
        if schema == ENGINEERING_CHAT_EXPERIENCE_SCHEMA
        else r"V-EXPERIENCE-[0-9]{3,}"
    )
    if (
        not isinstance(case_id, str)
        or re.fullmatch(case_pattern, case_id) is None
        or case_id not in blocking_case_ids
    ):
        errors.append(
            f"{label}: experience version case_id must be a matching blocking experience Case"
        )
    if not new_refs or binding.get("new_slice_ref") != new_refs[0]:
        errors.append(
            f"{label}: experience version must be delivered by the first new capability Slice"
        )
    for field in ("exact_version_visible", "repeatable_start", "limitations_visible"):
        if binding.get(field) is not True:
            errors.append(f"{label}: experience version {field} must equal true")
    if schema == "USER_EXPERIENCE_VERSION@1":
        if binding.get("continuous_same_session_free_questions") is not True:
            errors.append(
                f"{label}: experience version continuous_same_session_free_questions must equal true"
            )
    elif schema == ENGINEERING_CHAT_EXPERIENCE_SCHEMA:
        for field in (
            "message_history_visible",
            "new_conversation_control",
            "semantic_follow_up",
            "user_correction_updates_context",
            "summary_honors_current_context",
            "per_turn_evidence_and_review",
            "new_conversation_context_isolation",
        ):
            if binding.get(field) is not True:
                errors.append(
                    f"{label}: engineering Chat experience {field} must equal true"
                )
        if binding.get("minimum_conversation_turns") != 5:
            errors.append(
                f"{label}: engineering Chat experience minimum_conversation_turns must equal 5"
            )
        if binding.get("long_term_memory_required") is not False:
            errors.append(
                f"{label}: engineering Chat Alpha must not require long-term memory"
            )
    address = binding.get("fixed_loopback_address")
    address_match = (
        re.fullmatch(r"http://127\.0\.0\.1:([1-9][0-9]{0,4})/?", address)
        if isinstance(address, str)
        else None
    )
    if address_match is None or not (1 <= int(address_match.group(1)) <= 65535):
        errors.append(
            f"{label}: experience version fixed_loopback_address must be an explicit 127.0.0.1 HTTP address"
        )
    if schema == ENGINEERING_CHAT_EXPERIENCE_SCHEMA:
        if (
            binding.get("turn_failure_scope")
            != "current-turn-only-conversation-remains-usable"
        ):
            errors.append(
                f"{label}: engineering Chat experience must isolate a failed turn without closing the conversation"
            )
    elif (
        binding.get("question_failure_scope")
        != "current-question-only-service-remains-available"
    ):
        errors.append(
            f"{label}: experience version must isolate a bad question without stopping the service"
        )
    return errors


def validate_conversational_engineering_agent(
    manifest: dict[str, object],
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
    *,
    required: bool = False,
) -> list[str]:
    """Validate the opt-in semantic Chat and lead engineering-Agent boundary."""

    policy = manifest.get("conversational_engineering_agent")
    if policy is None:
        return [f"{label}: conversational_engineering_agent is required"] if required else []
    if not isinstance(policy, dict):
        return [f"{label}: conversational_engineering_agent must be a mapping"]

    errors: list[str] = []
    exact_values: tuple[tuple[str, object], ...] = (
        ("schema", CONVERSATIONAL_ENGINEERING_AGENT_SCHEMA),
        ("architecture_decision_ref", "SYS-ADR-018"),
        (
            "conversation_contract_ref",
            "SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION",
        ),
        ("interaction_model", "semantic-multi-turn-chat"),
        ("fixed_multi_role_content_workflow_is_target_agent", False),
        (
            "world_model_role",
            "persistent-versioned-verifiable-software-cognition",
        ),
        (
            "lead_agent_owns",
            "user-goal-hypotheses-subtasks-plan-revisions-context-selection-"
            "tool-choice-observation-interpretation-replanning-completion-and-"
            "answer-synthesis",
        ),
        (
            "control_plane_owns",
            "exact-version-authorization-read-only-tool-execution-evidence-"
            "identity-budget-and-audit",
        ),
        ("independent_reviewer_required", True),
        (
            "lead_agent_direct_repository_filesystem_shell_network_or_write_access",
            False,
        ),
        (
            "tool_families_before_direction_confirmation",
            "world-model-query-and-controlled-source-search-read",
        ),
        (
            "conversation_identity_pinned_to",
            "exact-project-revision-world-model-authority-source-profile-and-"
            "session-authority",
        ),
        (
            "turn_intent_kinds",
            "new,follow-up,correction,clarification,deepen,summary",
        ),
        (
            "context_required_fields",
            "confirmed-goal-and-constraints,referenced-entities-and-topics,"
            "open-questions,reviewed-conclusions,contested-or-superseded-"
            "conclusions,exact-provenance",
        ),
        ("application_sealed_context_projection_required", True),
        ("provider_hidden_memory_is_authority", False),
        (
            "ambiguous_reference_action",
            "clarify-before-source-or-provider-dispatch",
        ),
        ("conversation_binding_schema", "ENGINEERING_CHAT_BINDING@2"),
        (
            "conversation_input_policy_ref",
            "EMPTY_CONTEXT_REFERENT_CLARIFICATION_ZH_CN@1",
        ),
        (
            "conversation_input_policy_scope",
            "empty-context-referent-clarification-before-world-model-source-"
            "credential-or-provider",
        ),
        ("conversation_input_policy_engineering_claim_authority", "none"),
        ("user_statement_becomes_source_truth", False),
        ("prior_answer_or_review_reuse_as_fact_allowed", False),
        (
            "reused_evidence_status",
            "candidate-only-until-rebound-and-reviewed-for-current-turn",
        ),
        (
            "evidence_reuse_requires",
            "exact-revision-binding-world-model-authority-source-profile-"
            "allowlist-content-digest-and-coverage-match",
        ),
        (
            "evidence_reuse_forbidden_inputs",
            "prior-answer-authorization,prior-review-decision,prior-limitation,"
            "unsealed-tool-result,provider-memory",
        ),
        ("reused_evidence_rebound_to_current_turn_package_required", True),
        (
            "per_turn_request_evidence_answer_review_and_delivery_identity_required",
            True,
        ),
        ("new_conversation_context_isolation_required", True),
        ("failed_turn_closes_conversation", False),
        ("first_chat_canary_conversation_count", 1),
        ("first_chat_canary_turn_count", 5),
        ("new_conversation_leakage_probe_required", True),
        (
            "alpha_comparison_arms",
            "same-agent-source-only,same-agent-full-world-model-cognition-and-"
            "source,current-codex-external-baseline",
        ),
        ("knowledge_admission_from_conversation", "asynchronous-reviewed-only"),
        ("long_term_memory_before_direction_confirmation_required", False),
        ("multi_agent_before_direction_confirmation_required", False),
        ("skill_market_before_direction_confirmation_required", False),
        (
            "persistence_across_restart_before_direction_confirmation_required",
            False,
        ),
        ("full_regression_before_direction_confirmation_allowed", False),
    )
    for field, expected in exact_values:
        if policy.get(field) != expected:
            errors.append(
                f"{label}: conversational_engineering_agent.{field} must equal {expected}"
            )

    if not new_refs or policy.get("owner_slice_ref") != new_refs[0]:
        errors.append(
            f"{label}: conversational engineering Agent must belong to the first capability Slice"
        )
    chat_case_id = policy.get("chat_case_id")
    if (
        not isinstance(chat_case_id, str)
        or re.fullmatch(r"V-CHAT-[0-9]{3,}", chat_case_id) is None
        or chat_case_id not in blocking_case_ids
    ):
        errors.append(
            f"{label}: conversational engineering Agent chat_case_id must be a blocking V-CHAT-NNN Case"
        )
    if policy.get("status") not in {
        "target-not-implemented-not-qualified",
        "implemented-not-qualified",
        "qualified-candidate",
        "implemented-live-failed-remediation-local-candidate",
        "implemented-second-live-failed-leakage-pass-v2-remediation-local-candidate",
        "implemented-third-live-failed-leakage-pass-v3-remediation-local-candidate",
        "implemented-fourth-live-one-of-five-limitation-leakage-pass-v4-remediation-local-candidate",
        "implemented-fifth-live-one-of-five-limitation-leakage-pass-v5-remediation-local-candidate",
        "implemented-sixth-live-three-of-five-responses-leakage-pass-v6-remediation-local-candidate",
        "implemented-eighth-live-failed-schedule-fail-v8-local-candidate",
    }:
        errors.append(
            f"{label}: conversational_engineering_agent.status must be a closed pre-production state"
        )
    if policy.get("status") == (
        "implemented-eighth-live-failed-schedule-fail-v8-local-candidate"
    ):
        for field, expected in (
            (
                "first_live_chat_turn_result",
                "five-of-five-failed-no-answer-citation-review-or-delivery",
            ),
            ("eighth_live_chat_execution_evidence_ref", "FINDING-010-138"),
            (
                "eighth_live_chat_result_ref",
                "ITER-010-RESULT-V-CHAT-EXPERIENCE-001-PDR005-DIRECTION-CANARY",
            ),
            (
                "eighth_live_chat_turn_result",
                "one-accepted-one-reviewed-limitation-three-failed-overall-quality-fail",
            ),
            ("eighth_live_chat_dispatches_by_turn", "13,5,5,3,2"),
            (
                "eighth_live_new_conversation_probe_result",
                "pass-empty-context-clarification-zero-dispatch-no-inheritance",
            ),
            (
                "eighth_live_deepseek_schedule_verdict",
                "deepseek-scheduling-policy-fail-not-direction-acceptance-evidence",
            ),
            (
                "v7_status",
                "stopped-unaccepted-symptom-experiment-not-current-system-truth",
            ),
            (
                "current_agent_model_strategy_ref",
                "conversational-engineering-agent@8",
            ),
            (
                "current_agent_model_prompt_ref",
                "conversational-engineering-agent-no-tools-prompt@8",
            ),
            (
                "current_agent_primary_input_schema",
                "ENGINEERING_AGENT_PRIMARY_INPUT@8",
            ),
            (
                "current_agent_review_input_schema",
                "ENGINEERING_AGENT_REVIEW_INPUT@2",
            ),
            (
                "current_agent_review_output_schema",
                "engineering-agent-independent-review-proposal@2",
            ),
            ("successor_semantic_query_finding_ref", "FINDING-010-138"),
            (
                "successor_schedule_result_ref",
                "ITER-010-RESULT-V-DEEPSEEK-IDLE-001",
            ),
            (
                "deterministic_successor_canary_status",
                "clean-successor-frozen-awaiting-new-exact-grant-and-compliant-window",
            ),
            (
                "deterministic_successor_canary_source_file_budget",
                "five-turn-search-56-plus-read-1-equals-57-of-64-and-adjacent-"
                "search-56-plus-read-3-equals-59-of-64",
            ),
        ):
            if policy.get(field) != expected:
                errors.append(
                    f"{label}: conversational_engineering_agent.{field} must equal {expected}"
                )
        for field in (
            "eighth_live_chat_product_commit",
            "eighth_live_chat_product_tree",
            "eighth_live_chat_source_commit",
            "eighth_live_chat_source_tree",
            "successor_product_commit",
            "successor_product_tree",
        ):
            value = policy.get(field)
            if not isinstance(value, str) or re.fullmatch(
                r"[0-9a-f]{40}", value
            ) is None:
                errors.append(
                    f"{label}: conversational_engineering_agent.{field} must be an exact Git object"
                )
        for field in (
            "eighth_live_chat_session_authorization_digest",
            "eighth_live_chat_session_config_file_digest",
            "eighth_live_chat_terminal_receipt_digest",
        ):
            value = policy.get(field)
            if not isinstance(value, str) or re.fullmatch(
                r"sha256:[0-9a-f]{64}", value
            ) is None:
                errors.append(
                    f"{label}: conversational_engineering_agent.{field} must be an exact sha256 digest"
                )
    if policy.get("status") == "implemented-live-failed-remediation-local-candidate":
        for field, expected in (
            ("first_live_chat_execution_evidence_ref", "FINDING-010-107"),
            (
                "first_live_chat_turn_result",
                "five-of-five-failed-no-answer-citation-review-or-delivery",
            ),
            (
                "first_live_new_conversation_probe_result",
                "transcript-isolated-but-required-clarification-failed",
            ),
            ("source_search_remediation_evidence_ref", "FINDING-010-108"),
            (
                "conversation_input_clarification_remediation_evidence_ref",
                "FINDING-010-109",
            ),
            (
                "source_search_read_budget_remediation_evidence_ref",
                "FINDING-010-110",
            ),
            (
                "deterministic_successor_canary_status",
                "five-turn-and-new-conversation-pass-with-fake-model-temp-git-"
                "no-live-authority-consumed",
            ),
            (
                "deterministic_successor_canary_source_file_budget",
                "search-63-plus-read-1-equals-unchanged-total-64",
            ),
        ):
            if policy.get(field) != expected:
                errors.append(
                    f"{label}: conversational_engineering_agent.{field} must equal {expected}"
                )
        for field in (
            "first_live_chat_product_commit",
            "first_live_chat_product_tree",
            "first_live_chat_source_commit",
            "first_live_chat_source_tree",
        ):
            value = policy.get(field)
            if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{40}", value) is None:
                errors.append(
                    f"{label}: conversational_engineering_agent.{field} must be an exact Git object"
                )
        for field in (
            "first_live_chat_session_authorization_digest",
            "first_live_chat_session_config_file_digest",
            "first_live_chat_terminal_receipt_digest",
        ):
            value = policy.get(field)
            if not isinstance(value, str) or re.fullmatch(
                r"sha256:[0-9a-f]{64}", value
            ) is None:
                errors.append(
                    f"{label}: conversational_engineering_agent.{field} must be an exact sha256 digest"
                )
        authorization = manifest.get("authorization")
        first_live = (
            authorization.get("first_live_session_authorization")
            if isinstance(authorization, dict)
            else None
        )
        if not isinstance(first_live, dict) or any(
            policy.get(policy_field) != first_live.get(authorization_field)
            for policy_field, authorization_field in (
                ("first_live_chat_product_commit", "exact_product_commit"),
                ("first_live_chat_product_tree", "exact_product_tree"),
                ("first_live_chat_source_commit", "source_commit"),
                ("first_live_chat_source_tree", "source_tree"),
            )
        ):
            errors.append(
                f"{label}: first live Chat identity must match the consumed Session authorization"
            )
        authorization_ref = (
            first_live.get("authorization_ref")
            if isinstance(first_live, dict)
            else None
        )
        if (
            not isinstance(authorization_ref, str)
            or not authorization_ref.startswith("codex-user-message:")
            or policy.get("first_live_chat_session_authorization_digest")
            != authorization_ref.removeprefix("codex-user-message:")
        ):
            errors.append(
                f"{label}: first live Chat authority digest must match the consumed user receipt"
            )
    if policy.get("status") == (
        "implemented-second-live-failed-leakage-pass-v2-remediation-local-candidate"
    ):
        for field, expected in (
            ("first_live_chat_execution_evidence_ref", "FINDING-010-107"),
            (
                "first_live_chat_turn_result",
                "five-of-five-failed-no-answer-citation-review-or-delivery",
            ),
            ("second_live_chat_execution_evidence_ref", "FINDING-010-111"),
            (
                "second_live_chat_turn_result",
                "five-of-five-failed-no-answer-citation-review-or-delivery",
            ),
            ("second_live_chat_dispatches_by_turn", "6,6,7,3,2"),
            (
                "second_live_new_conversation_probe_result",
                "pass-empty-context-clarification-zero-dispatch-no-inheritance",
            ),
            ("source_search_dual_file_fuse_evidence_ref", "FINDING-010-112"),
            ("model_draft_reference_domain_evidence_ref", "FINDING-010-113"),
            (
                "current_agent_model_strategy_ref",
                "conversational-engineering-agent@2",
            ),
            (
                "current_agent_model_prompt_ref",
                "conversational-engineering-agent-no-tools-prompt@2",
            ),
            (
                "current_agent_primary_input_schema",
                "ENGINEERING_AGENT_PRIMARY_INPUT@2",
            ),
            (
                "current_dual_provider_qualification_status",
                "stale-after-model-strategy-prompt-input-change-fresh-conformance-required",
            ),
            (
                "deterministic_successor_canary_status",
                "five-turn-and-new-conversation-pass-plus-three-read-adjacent-pass-"
                "with-fake-model-temp-git-no-live-authority-consumed",
            ),
            (
                "deterministic_successor_canary_source_file_budget",
                "five-turn-search-56-plus-read-1-equals-57-of-64-and-adjacent-"
                "search-56-plus-read-3-equals-59-of-64",
            ),
        ):
            if policy.get(field) != expected:
                errors.append(
                    f"{label}: conversational_engineering_agent.{field} must equal {expected}"
                )
        for prefix in ("first", "second"):
            for suffix in (
                "product_commit",
                "product_tree",
                "source_commit",
                "source_tree",
            ):
                field = f"{prefix}_live_chat_{suffix}"
                value = policy.get(field)
                if not isinstance(value, str) or re.fullmatch(
                    r"[0-9a-f]{40}", value
                ) is None:
                    errors.append(
                        f"{label}: conversational_engineering_agent.{field} must be an exact Git object"
                    )
            for suffix in (
                "session_authorization_digest",
                "session_config_file_digest",
                "terminal_receipt_digest",
            ):
                field = f"{prefix}_live_chat_{suffix}"
                value = policy.get(field)
                if not isinstance(value, str) or re.fullmatch(
                    r"sha256:[0-9a-f]{64}", value
                ) is None:
                    errors.append(
                        f"{label}: conversational_engineering_agent.{field} must be an exact sha256 digest"
                    )
        authorization = manifest.get("authorization")
        for prefix in ("first", "second"):
            live = (
                authorization.get(f"{prefix}_live_session_authorization")
                if isinstance(authorization, dict)
                else None
            )
            if not isinstance(live, dict) or any(
                policy.get(f"{prefix}_live_chat_{policy_suffix}")
                != live.get(authorization_field)
                for policy_suffix, authorization_field in (
                    ("product_commit", "exact_product_commit"),
                    ("product_tree", "exact_product_tree"),
                    ("source_commit", "source_commit"),
                    ("source_tree", "source_tree"),
                )
            ):
                errors.append(
                    f"{label}: {prefix} live Chat identity must match the consumed Session authorization"
                )
            authorization_ref = (
                live.get("authorization_ref") if isinstance(live, dict) else None
            )
            if (
                not isinstance(authorization_ref, str)
                or not authorization_ref.startswith("codex-user-message:")
                or policy.get(f"{prefix}_live_chat_session_authorization_digest")
                != authorization_ref.removeprefix("codex-user-message:")
            ):
                errors.append(
                    f"{label}: {prefix} live Chat authority digest must match the consumed user receipt"
                )
    if policy.get("status") == (
        "implemented-third-live-failed-leakage-pass-v3-remediation-local-candidate"
    ):
        for field, expected in (
            ("first_live_chat_execution_evidence_ref", "FINDING-010-107"),
            (
                "first_live_chat_turn_result",
                "five-of-five-failed-no-answer-citation-review-or-delivery",
            ),
            (
                "first_live_new_conversation_probe_result",
                "transcript-isolated-but-required-clarification-failed",
            ),
            ("source_search_remediation_evidence_ref", "FINDING-010-108"),
            (
                "conversation_input_clarification_remediation_evidence_ref",
                "FINDING-010-109",
            ),
            (
                "source_search_read_budget_remediation_evidence_ref",
                "FINDING-010-110",
            ),
            ("second_live_chat_execution_evidence_ref", "FINDING-010-111"),
            (
                "second_live_chat_turn_result",
                "five-of-five-failed-no-answer-citation-review-or-delivery",
            ),
            ("second_live_chat_dispatches_by_turn", "6,6,7,3,2"),
            (
                "second_live_new_conversation_probe_result",
                "pass-empty-context-clarification-zero-dispatch-no-inheritance",
            ),
            ("source_search_dual_file_fuse_evidence_ref", "FINDING-010-112"),
            ("model_draft_reference_domain_evidence_ref", "FINDING-010-113"),
            ("third_live_conformance_execution_evidence_ref", "FINDING-010-114"),
            (
                "third_live_ark_conformance_result_digest",
                "sha256:bbaf5611a46d68400d0ee4da4f5994deeb8bffecbeead07b7db26b40cbe4b114",
            ),
            (
                "third_live_deepseek_conformance_result_digest",
                "sha256:5fe0a06f253a3865325738a63c00f9fd659cd96c25aa764c76a3ec2914646b6c",
            ),
            ("third_live_chat_execution_evidence_ref", "FINDING-010-115"),
            (
                "third_live_chat_turn_result",
                "five-of-five-failed-no-user-visible-answer-citation-or-delivery",
            ),
            ("third_live_chat_dispatches_by_turn", "10,8,4,4,5"),
            (
                "third_live_new_conversation_probe_result",
                "pass-empty-context-clarification-zero-dispatch-no-inheritance",
            ),
            ("model_tool_reference_domain_evidence_ref", "FINDING-010-116"),
            (
                "model_review_claim_assessment_evidence_ref",
                "FINDING-010-117",
            ),
            (
                "current_agent_model_strategy_ref",
                "conversational-engineering-agent@3",
            ),
            (
                "current_agent_model_prompt_ref",
                "conversational-engineering-agent-no-tools-prompt@3",
            ),
            (
                "current_agent_primary_input_schema",
                "ENGINEERING_AGENT_PRIMARY_INPUT@3",
            ),
            (
                "current_agent_review_input_schema",
                "ENGINEERING_AGENT_REVIEW_INPUT@2",
            ),
            (
                "current_agent_review_output_schema",
                "engineering-agent-independent-review-proposal@2",
            ),
            (
                "current_dual_provider_qualification_status",
                "stale-after-v3-strategy-prompt-input-output-change-fresh-"
                "conformance-required",
            ),
            (
                "deterministic_successor_canary_status",
                "v3-tool-copy-and-review-contract-70-of-70-pass-plus-prior-five-"
                "turn-and-three-read-canaries-no-live-authority-consumed",
            ),
            (
                "deterministic_successor_canary_source_file_budget",
                "five-turn-search-56-plus-read-1-equals-57-of-64-and-adjacent-"
                "search-56-plus-read-3-equals-59-of-64",
            ),
        ):
            if policy.get(field) != expected:
                errors.append(
                    f"{label}: conversational_engineering_agent.{field} must equal {expected}"
                )
        for prefix in ("first", "second", "third"):
            for suffix in (
                "product_commit",
                "product_tree",
                "source_commit",
                "source_tree",
            ):
                field = f"{prefix}_live_chat_{suffix}"
                value = policy.get(field)
                if not isinstance(value, str) or re.fullmatch(
                    r"[0-9a-f]{40}", value
                ) is None:
                    errors.append(
                        f"{label}: conversational_engineering_agent.{field} must be an exact Git object"
                    )
            for suffix in (
                "session_authorization_digest",
                "session_config_file_digest",
                "terminal_receipt_digest",
            ):
                field = f"{prefix}_live_chat_{suffix}"
                value = policy.get(field)
                if not isinstance(value, str) or re.fullmatch(
                    r"sha256:[0-9a-f]{64}", value
                ) is None:
                    errors.append(
                        f"{label}: conversational_engineering_agent.{field} must be an exact sha256 digest"
                    )
        authorization = manifest.get("authorization")
        for prefix in ("first", "second", "third"):
            live = (
                authorization.get(f"{prefix}_live_session_authorization")
                if isinstance(authorization, dict)
                else None
            )
            if not isinstance(live, dict) or any(
                policy.get(f"{prefix}_live_chat_{policy_suffix}")
                != live.get(authorization_field)
                for policy_suffix, authorization_field in (
                    ("product_commit", "exact_product_commit"),
                    ("product_tree", "exact_product_tree"),
                    ("source_commit", "source_commit"),
                    ("source_tree", "source_tree"),
                )
            ):
                errors.append(
                    f"{label}: {prefix} live Chat identity must match the consumed Session authorization"
                )
            authorization_ref = (
                live.get("authorization_ref") if isinstance(live, dict) else None
            )
            if (
                not isinstance(authorization_ref, str)
                or not authorization_ref.startswith("codex-user-message:")
                or policy.get(f"{prefix}_live_chat_session_authorization_digest")
                != authorization_ref.removeprefix("codex-user-message:")
            ):
                errors.append(
                    f"{label}: {prefix} live Chat authority digest must match the consumed user receipt"
                )
    if policy.get("status") == (
        "implemented-sixth-live-three-of-five-responses-leakage-pass-v6-remediation-local-candidate"
    ):
        for field, expected in (
            ("first_live_chat_execution_evidence_ref", "FINDING-010-107"),
            (
                "first_live_chat_turn_result",
                "five-of-five-failed-no-answer-citation-review-or-delivery",
            ),
            ("second_live_chat_execution_evidence_ref", "FINDING-010-111"),
            ("third_live_conformance_execution_evidence_ref", "FINDING-010-114"),
            ("third_live_chat_execution_evidence_ref", "FINDING-010-115"),
            ("model_tool_reference_domain_evidence_ref", "FINDING-010-116"),
            ("model_review_claim_assessment_evidence_ref", "FINDING-010-117"),
            ("fourth_live_conformance_execution_evidence_ref", "FINDING-010-118"),
            (
                "fourth_live_ark_conformance_result_digest",
                "sha256:ef4787881e0cd87a8642088cf1e0165e5a33bb109691965003bb14914b7c4753",
            ),
            (
                "fourth_live_deepseek_conformance_result_digest",
                "sha256:aec00111e27f329fd4291cbec01476c180e0820d1787e7e6877c2fa71e8757d9",
            ),
            ("fourth_live_chat_execution_evidence_ref", "FINDING-010-119"),
            (
                "fourth_live_chat_turn_result",
                "one-of-five-succeeded-reviewed-limitation-four-failed-no-answer-delivery",
            ),
            ("fourth_live_chat_dispatches_by_turn", "8,6,2,8,5"),
            (
                "fourth_live_new_conversation_probe_result",
                "pass-empty-context-clarification-zero-dispatch-no-inheritance",
            ),
            ("source_read_resource_domain_evidence_ref", "FINDING-010-120"),
            ("evidence_only_completion_evidence_ref", "FINDING-010-121"),
            ("artifact_session_fixture_clock_evidence_ref", "FINDING-010-122"),
            ("fifth_live_conformance_execution_evidence_ref", "FINDING-010-123"),
            (
                "fifth_live_ark_conformance_result_digest",
                "sha256:8c179dd2e7d00fb4a8177557b3716c254ccfab7911e8ed46e78df6ebd8f728cd",
            ),
            (
                "fifth_live_deepseek_conformance_result_digest",
                "sha256:a61f7eafa4d6caa42b33d54fd41386d065abb14dd0302b16f665dfb725a54e92",
            ),
            ("fifth_live_chat_execution_evidence_ref", "FINDING-010-124"),
            (
                "fifth_live_chat_turn_result",
                "one-of-five-succeeded-reviewed-limitation-four-failed-no-answer-delivery",
            ),
            ("fifth_live_chat_dispatches_by_turn", "11,8,2,5,2"),
            (
                "fifth_live_new_conversation_probe_result",
                "pass-empty-context-clarification-zero-dispatch-no-inheritance",
            ),
            ("work_state_reference_domain_evidence_ref", "FINDING-010-125"),
            ("sixth_live_conformance_execution_evidence_ref", "FINDING-010-126"),
            (
                "sixth_live_ark_conformance_result_digest",
                "sha256:b81a9f514bcc4a962732ea873e33fa61ba37a377c11848d6afddfae67a6f4c88",
            ),
            (
                "sixth_live_deepseek_conformance_result_digest",
                "sha256:a6cae82aeff8da0b318c235da918ce7982d1eaec3875a234ed49722e5ae3fedd",
            ),
            ("sixth_live_chat_execution_evidence_ref", "FINDING-010-127"),
            (
                "sixth_live_chat_turn_result",
                "three-of-five-technical-responses-two-failed-overall-quality-fail",
            ),
            ("sixth_live_chat_dispatches_by_turn", "8,3,8,7,2"),
            (
                "sixth_live_new_conversation_probe_result",
                "pass-empty-context-clarification-zero-dispatch-no-inheritance",
            ),
            ("response_tool_argument_domain_evidence_ref", "FINDING-010-128"),
            (
                "current_agent_model_strategy_ref",
                "conversational-engineering-agent@6",
            ),
            (
                "current_agent_model_prompt_ref",
                "conversational-engineering-agent-no-tools-prompt@6",
            ),
            (
                "current_agent_primary_input_schema",
                "ENGINEERING_AGENT_PRIMARY_INPUT@6",
            ),
            (
                "current_agent_review_input_schema",
                "ENGINEERING_AGENT_REVIEW_INPUT@2",
            ),
            (
                "current_agent_review_output_schema",
                "engineering-agent-independent-review-proposal@2",
            ),
            (
                "current_dual_provider_qualification_status",
                "stale-after-v6-strategy-prompt-primary-input-change-fresh-"
                "conformance-required",
            ),
            (
                "deterministic_successor_canary_status",
                "v6-current-turn-response-and-tool-argument-domain-84-of-84-pass-"
                "no-live-authority-consumed",
            ),
            (
                "deterministic_successor_canary_source_file_budget",
                "five-turn-search-56-plus-read-1-equals-57-of-64-and-adjacent-"
                "search-56-plus-read-3-equals-59-of-64",
            ),
        ):
            if policy.get(field) != expected:
                errors.append(
                    f"{label}: conversational_engineering_agent.{field} must equal {expected}"
                )
        authorization = manifest.get("authorization")
        for prefix in ("first", "second", "third", "fourth", "fifth", "sixth"):
            for suffix in (
                "product_commit",
                "product_tree",
                "source_commit",
                "source_tree",
            ):
                field = f"{prefix}_live_chat_{suffix}"
                value = policy.get(field)
                if not isinstance(value, str) or re.fullmatch(
                    r"[0-9a-f]{40}", value
                ) is None:
                    errors.append(
                        f"{label}: conversational_engineering_agent.{field} must be an exact Git object"
                    )
            for suffix in (
                "session_authorization_digest",
                "session_config_file_digest",
                "terminal_receipt_digest",
            ):
                field = f"{prefix}_live_chat_{suffix}"
                value = policy.get(field)
                if not isinstance(value, str) or re.fullmatch(
                    r"sha256:[0-9a-f]{64}", value
                ) is None:
                    errors.append(
                        f"{label}: conversational_engineering_agent.{field} must be an exact sha256 digest"
                    )
            live = (
                authorization.get(f"{prefix}_live_session_authorization")
                if isinstance(authorization, dict)
                else None
            )
            if not isinstance(live, dict) or any(
                policy.get(f"{prefix}_live_chat_{policy_suffix}")
                != live.get(authorization_field)
                for policy_suffix, authorization_field in (
                    ("product_commit", "exact_product_commit"),
                    ("product_tree", "exact_product_tree"),
                    ("source_commit", "source_commit"),
                    ("source_tree", "source_tree"),
                )
            ):
                errors.append(
                    f"{label}: {prefix} live Chat identity must match the consumed Session authorization"
                )
            authorization_ref = (
                live.get("authorization_ref") if isinstance(live, dict) else None
            )
            receipt_prefix = (
                "local-user-message-utf8:"
                if prefix in {"fifth", "sixth"}
                else "codex-user-message:"
            )
            if (
                not isinstance(authorization_ref, str)
                or not authorization_ref.startswith(receipt_prefix)
                or policy.get(f"{prefix}_live_chat_session_authorization_digest")
                != authorization_ref.removeprefix(receipt_prefix)
            ):
                errors.append(
                    f"{label}: {prefix} live Chat authority digest must match the consumed user receipt"
                )
    experience = alignment.get("experience_version_binding")
    if (
        not isinstance(experience, dict)
        or experience.get("schema") != ENGINEERING_CHAT_EXPERIENCE_SCHEMA
    ):
        errors.append(
            f"{label}: conversational engineering Agent requires ENGINEERING_CHAT_EXPERIENCE@1"
        )
    return errors


def validate_conversational_architecture_cutover(
    manifest: dict[str, object],
    label: str,
    *,
    manifest_text: str | None = None,
) -> list[str]:
    """Keep the @3 workflow auditable without authorizing it as the current Agent."""

    if not conversational_agent_cutover_active(manifest):
        return []
    errors: list[str] = []
    legacy_markers: tuple[tuple[str, str], ...] = (
        ("hybrid_evidence_path", "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3"),
        (
            "reviewer_verification_investigation",
            "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3",
        ),
        (
            "answer_hierarchy_protocol",
            "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3",
        ),
        ("answer_protocol", "ENGINEERING_QA_ADAPTIVE_INVESTIGATION@3"),
    )
    for section_name, schema in legacy_markers:
        section = manifest.get(section_name)
        if not isinstance(section, dict):
            errors.append(f"{label}: {section_name} must remain a legacy mapping")
            continue
        for field, expected in (
            ("protocol_role", "legacy-compatibility"),
            ("legacy_protocol_schema", schema),
            ("superseded_as_default_by", "SYS-ADR-018"),
            ("current_delivery_authorization_allowed", False),
            (
                "historical_result_ref",
                "ITER-010-RESULT-SLICE-001-STOP-REDIRECT",
            ),
        ):
            if section.get(field) != expected:
                errors.append(
                    f"{label}: {section_name}.{field} must equal {expected}"
                )

    readiness = manifest.get("readiness_inputs")
    if not isinstance(readiness, dict):
        return errors + [f"{label}: readiness_inputs must be a mapping"]
    for field, expected in (
        ("required_architecture_decision", "SYS-ADR-018"),
        ("current_architecture_decision", "SYS-ADR-018"),
        ("architecture_change_target", "SYS-ADR-018"),
        ("legacy_compatibility_architecture_decision", "SYS-ADR-016"),
        ("legacy_architecture_amended_by", "SYS-ADR-018"),
        (
            "answer_protocol_contract_ref",
            "SYS-CONTRACT-APPLICATION-ENGINEERING-CONVERSATION",
        ),
        (
            "legacy_answer_protocol_contract_ref",
            "SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING",
        ),
        ("current_protocol_schema", CONVERSATIONAL_ENGINEERING_AGENT_SCHEMA),
        ("legacy_protocol_schema", ENGINEERING_QA_ADAPTIVE_PROTOCOL_SCHEMA),
        ("historical_readiness_ref", "ITER-010-READINESS"),
        (
            "historical_readiness_catalog_digest",
            "sha256:26769498135692067597a1f59e0fbbc8b82502ebd5336f7fdb033a80e3baff82",
        ),
    ):
        if readiness.get(field) != expected:
            errors.append(f"{label}: readiness_inputs.{field} must equal {expected}")

    readiness_status = readiness.get("current_readiness_status")
    if readiness_status not in {
        "refresh-required-not-accepted",
        "accepted-current",
    }:
        errors.append(
            f"{label}: readiness_inputs.current_readiness_status must be a closed refresh or accepted state"
        )
    iteration_state = manifest.get("iteration")
    rework = manifest.get("rework")
    authorization = manifest.get("authorization")
    baseline = manifest.get("baseline")
    if readiness_status == "accepted-current":
        acceptance_ref = readiness.get("current_readiness_acceptance_ref")
        accepted_at = readiness.get("current_readiness_accepted_at")
        planning_commit = readiness.get("current_readiness_planning_commit")
        planning_tree = readiness.get("current_readiness_planning_tree")
        if not isinstance(acceptance_ref, str) or re.fullmatch(
            r"codex-user-message:sha256:[0-9a-f]{64}", acceptance_ref
        ) is None:
            errors.append(
                f"{label}: accepted current Readiness must bind an exact user acceptance receipt"
            )
        elif acceptance_ref != ITER010_PDR004_ACTIVATION_RECEIPT:
            errors.append(
                f"{label}: accepted current Readiness receipt must equal the exact current PDR-004 activation receipt"
            )
        if not isinstance(accepted_at, str) or re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|[+-][0-9]{2}:[0-9]{2})",
            accepted_at,
        ) is None:
            errors.append(
                f"{label}: accepted current Readiness must bind an exact acceptance timestamp"
            )
        elif accepted_at != ITER010_PDR004_ACTIVATION_TIMESTAMP:
            errors.append(
                f"{label}: accepted current Readiness timestamp must equal the exact current PDR-004 activation timestamp"
            )
        for field_name, value in (
            ("current_readiness_planning_commit", planning_commit),
            ("current_readiness_planning_tree", planning_tree),
        ):
            if not isinstance(value, str) or re.fullmatch(
                r"[0-9a-f]{40}", value
            ) is None:
                errors.append(
                    f"{label}: readiness_inputs.{field_name} must be an exact Git object"
                )
        if (
            planning_commit != ITER010_PDR004_PLANNING_COMMIT
            or planning_tree != ITER010_PDR004_PLANNING_TREE
        ):
            errors.append(
                f"{label}: accepted current Readiness must bind the exact PDR-004 planning commit/tree"
            )
        if not isinstance(baseline, dict) or (
            planning_commit != baseline.get("planning_commit")
            or planning_tree != baseline.get("planning_tree")
        ):
            errors.append(
                f"{label}: accepted current Readiness planning identity must match baseline planning_commit/tree"
            )
        if not isinstance(iteration_state, dict) or (
            iteration_state.get("status") not in ACTIVE_ITERATION_STATUSES
            or iteration_state.get("coding_input") is not True
        ):
            errors.append(
                f"{label}: accepted current Readiness requires an authorized coding iteration"
            )
        if not isinstance(rework, dict) or (
            rework.get("authorization_status")
            != "authorized-refreshed-readiness-accepted"
            or rework.get("coding_input") is not True
            or rework.get("current_reauthorization_ref") != acceptance_ref
            or rework.get("authorization_ref") != acceptance_ref
            or rework.get("authorized_at") != accepted_at
        ):
            errors.append(
                f"{label}: accepted current Readiness must match the active rework authorization"
            )
        superseded_receipts: set[str] = set()
        if isinstance(rework, dict):
            for field in (
                "user_receipt_ref",
                "historical_redirect_message_ref",
                "prior_rework_authorization_ref",
            ):
                value = rework.get(field)
                if isinstance(value, str):
                    superseded_receipts.add(value)
        if isinstance(authorization, dict):
            prior_design_refs = authorization.get("prior_design_authorization_refs")
            if isinstance(prior_design_refs, list):
                superseded_receipts.update(map(str, prior_design_refs))
            for field in (
                "docs_sync_authorization_ref",
                "planning_request_ref",
                "final_decision_ref",
                "recovery_decision_ref_receipt",
            ):
                value = authorization.get(field)
                if isinstance(value, str):
                    superseded_receipts.add(value)
            root_authorization = authorization.get(
                "slice1_needed_rights_root_authorization"
            )
            if isinstance(root_authorization, dict):
                root_authorization_ref = root_authorization.get("authorization_ref")
                if isinstance(root_authorization_ref, str):
                    superseded_receipts.add(root_authorization_ref)
        if manifest_text is not None:
            superseded_receipts.update(
                manifest_resolved_sequence_items(
                    manifest_text,
                    "authorization",
                    "prior_design_authorization_refs",
                )
                or []
            )
            superseded_receipts.update(
                manifest_resolved_nested_sequence_items(
                    manifest_text,
                    (
                        "development",
                        "slices",
                        "ITER-010-SLICE-001",
                        "prior_authorization_refs",
                    ),
                )
                or []
            )
        if isinstance(acceptance_ref, str) and acceptance_ref in superseded_receipts:
            errors.append(
                f"{label}: current Readiness acceptance must not reuse a prior, consumed, paused, or docs-only authorization receipt"
            )
        allowed_current_receipt_paths = {
            ("readiness_inputs", "current_readiness_acceptance_ref"),
            ("rework", "current_reauthorization_ref"),
            ("rework", "authorization_ref"),
            (
                "development",
                "slices",
                "ITER-010-SLICE-001",
                "authorization_ref",
            ),
            ("authorization", "authorization_ref"),
        }
        receipt_stack: list[tuple[tuple[object, ...], object]] = [((), manifest)]
        unexpected_receipt_paths: list[str] = []
        while receipt_stack:
            path, value = receipt_stack.pop()
            if isinstance(value, dict):
                receipt_stack.extend(
                    (path + (key,), nested) for key, nested in value.items()
                )
            elif isinstance(value, list):
                receipt_stack.extend(
                    (path + (index,), nested)
                    for index, nested in enumerate(value)
                )
            elif (
                isinstance(acceptance_ref, str)
                and value == acceptance_ref
                and path not in allowed_current_receipt_paths
            ):
                unexpected_receipt_paths.append(".".join(map(str, path)))
        if unexpected_receipt_paths:
            errors.append(
                f"{label}: current Readiness receipt must be new and may appear only in current acceptance/authorization fields; also found at "
                + ", ".join(sorted(unexpected_receipt_paths))
            )
        if not isinstance(authorization, dict) or (
            authorization.get("active_slice") != "ITER-010-SLICE-001"
            or authorization.get("authorization_ref") != acceptance_ref
            or authorization.get("authorized_at") != accepted_at
            or authorization.get("refreshed_readiness_required") is not False
            or authorization.get("explicit_user_reauthorization_required") is not False
        ):
            errors.append(
                f"{label}: accepted current Readiness must match the active Slice1 authorization"
            )
        external_execution_status = (
            authorization.get("external_execution_authorization_status")
            if isinstance(authorization, dict)
            else None
        )
        if not isinstance(authorization, dict) or (
            authorization.get("development_authorization_scope")
            != "slice1-product-system-code-and-local-deterministic-verification-only"
        ):
            errors.append(
                f"{label}: current development authorization must remain limited to Slice1 product/System code and local deterministic verification"
            )
        first_live_authorization = (
            authorization.get("first_live_session_authorization")
            if isinstance(authorization, dict)
            else None
        )
        second_live_authorization = (
            authorization.get("second_live_session_authorization")
            if isinstance(authorization, dict)
            else None
        )
        third_live_authorization = (
            authorization.get("third_live_session_authorization")
            if isinstance(authorization, dict)
            else None
        )
        fourth_live_authorization = (
            authorization.get("fourth_live_session_authorization")
            if isinstance(authorization, dict)
            else None
        )
        fifth_live_authorization = (
            authorization.get("fifth_live_session_authorization")
            if isinstance(authorization, dict)
            else None
        )
        sixth_live_authorization = (
            authorization.get("sixth_live_session_authorization")
            if isinstance(authorization, dict)
            else None
        )
        consumed_history = (
            authorization.get("consumed_live_session_authorization_history")
            if isinstance(authorization, dict)
            else None
        )
        expected_consumed_history = {
            "first_live_session_authorization": "FINDING-010-107",
            "second_live_session_authorization": "FINDING-010-111",
            "third_live_session_authorization": "FINDING-010-115",
            "fourth_live_session_authorization": "FINDING-010-119",
            "fifth_live_session_authorization": "FINDING-010-124",
            "sixth_live_session_authorization": "FINDING-010-127",
            "seventh_live_session_authorization": "FINDING-010-130",
            "eighth_live_session_authorization": "FINDING-010-138",
        }
        if not isinstance(consumed_history, dict):
            errors.append(
                f"{label}: consumed live Session history must retain its exact receipts"
            )
        else:
            for name, finding_ref in expected_consumed_history.items():
                receipt = consumed_history.get(name)
                if not isinstance(receipt, dict):
                    errors.append(
                        f"{label}: consumed live Session history must retain its exact receipt: {name}"
                    )
                    continue
                expected_status = (
                    "consumed-scheduling-policy-fail"
                    if name == "eighth_live_session_authorization"
                    else "consumed"
                )
                authorization_refs = (
                    (
                        receipt.get("root_authorization_ref"),
                        receipt.get("exact_execution_authorization_ref"),
                    )
                    if name == "eighth_live_session_authorization"
                    else (receipt.get("authorization_ref"),)
                )
                if (
                    receipt.get("status") != expected_status
                    or any(
                        not isinstance(reference, str)
                        or re.fullmatch(
                            r"(?:codex-user-message|local-user-message-utf8):sha256:[0-9a-f]{64}",
                            reference,
                        )
                        is None
                        for reference in authorization_refs
                    )
                    or receipt.get("excludes")
                    != "src-main-resources,credential-values,hidden,slice2,slice3,production-activation"
                    or receipt.get("execution_finding_ref") != finding_ref
                ):
                    errors.append(
                        f"{label}: {name} must remain exact, excluded and evidence-bound"
                    )
                for field in (
                    "exact_product_commit",
                    "exact_product_tree",
                    "source_commit",
                    "source_tree",
                ):
                    value = receipt.get(field)
                    if not isinstance(value, str) or re.fullmatch(
                        r"[0-9a-f]{40}", value
                    ) is None:
                        errors.append(
                            f"{label}: {name}.{field} must be an exact Git object"
                        )
            eighth = consumed_history.get("eighth_live_session_authorization")
            if not isinstance(eighth, dict) or (
                eighth.get("scheduling_finding_ref") != "FINDING-010-139"
                or eighth.get("scheduling_verdict")
                != "deepseek-scheduling-policy-fail-not-direction-acceptance-evidence"
            ):
                errors.append(
                    f"{label}: eighth live Session history must retain its scheduling failure disposition"
                )
        if (
            external_execution_status == "standing-authority-active"
            and uses_lightweight_iter010_plan(manifest)
        ):
            standing = manifest.get("public_oss_evaluation_standing_authority")
            if (
                authorization.get("external_execution_reauthorization_required")
                is not False
                or authorization.get(
                    "human_reauthorization_required_for_current_direction_canary"
                )
                is not False
                or not isinstance(standing, dict)
                or standing.get("authority_status") != "active"
                or standing.get(
                    "machine_receipt_derivation_required_per_run_turn_and_dispatch"
                )
                is not True
            ):
                errors.append(
                    f"{label}: lightweight ITER-010 standing authority must be active without repeated human approval and retain per-dispatch runtime receipts"
                )
        elif external_execution_status == "not-authorized":
            if (
                first_live_authorization is not None
                or second_live_authorization is not None
                or third_live_authorization is not None
                or fourth_live_authorization is not None
                or fifth_live_authorization is not None
                or sixth_live_authorization is not None
            ):
                errors.append(
                    f"{label}: an unexecuted external state must not contain live Session authorization receipts"
                )
        elif (
            external_execution_status
            == "first-live-session-grant-consumed-no-current-live-authority"
        ):
            if (
                authorization.get("external_execution_reauthorization_required")
                is not True
            ):
                errors.append(
                    f"{label}: consumed first live Session authority must require new exact external reauthorization"
                )
            if not isinstance(first_live_authorization, dict):
                errors.append(
                    f"{label}: consumed first live Session authority must retain its exact receipt"
                )
            else:
                authorization_ref = first_live_authorization.get("authorization_ref")
                if (
                    first_live_authorization.get("status") != "consumed"
                    or not isinstance(authorization_ref, str)
                    or re.fullmatch(
                        r"codex-user-message:sha256:[0-9a-f]{64}",
                        authorization_ref,
                    )
                    is None
                    or first_live_authorization.get("excludes")
                    != "src-main-resources,credential-values,hidden,slice2,slice3,production-activation"
                    or first_live_authorization.get("execution_finding_ref")
                    != "FINDING-010-107"
                ):
                    errors.append(
                        f"{label}: consumed first live Session authority must remain exact, excluded and evidence-bound"
                    )
                for field in (
                    "exact_product_commit",
                    "exact_product_tree",
                    "source_commit",
                    "source_tree",
                ):
                    value = first_live_authorization.get(field)
                    if not isinstance(value, str) or re.fullmatch(
                        r"[0-9a-f]{40}", value
                    ) is None:
                        errors.append(
                            f"{label}: first_live_session_authorization.{field} must be an exact Git object"
                        )
        elif external_execution_status == (
            "second-live-session-grant-consumed-no-current-live-authority"
        ):
            if (
                authorization.get("external_execution_reauthorization_required")
                is not True
            ):
                errors.append(
                    f"{label}: consumed second live Session authority must require new exact external reauthorization"
                )
            for name, live_authorization, finding_ref in (
                (
                    "first_live_session_authorization",
                    first_live_authorization,
                    "FINDING-010-107",
                ),
                (
                    "second_live_session_authorization",
                    second_live_authorization,
                    "FINDING-010-111",
                ),
            ):
                if not isinstance(live_authorization, dict):
                    errors.append(
                        f"{label}: consumed second live state must retain its exact receipt: {name}"
                    )
                    continue
                authorization_ref = live_authorization.get("authorization_ref")
                if (
                    live_authorization.get("status") != "consumed"
                    or not isinstance(authorization_ref, str)
                    or re.fullmatch(
                        r"codex-user-message:sha256:[0-9a-f]{64}",
                        authorization_ref,
                    )
                    is None
                    or live_authorization.get("excludes")
                    != "src-main-resources,credential-values,hidden,slice2,slice3,production-activation"
                    or live_authorization.get("execution_finding_ref")
                    != finding_ref
                ):
                    errors.append(
                        f"{label}: {name} must remain exact, excluded and evidence-bound"
                    )
                for field in (
                    "exact_product_commit",
                    "exact_product_tree",
                    "source_commit",
                    "source_tree",
                ):
                    value = live_authorization.get(field)
                    if not isinstance(value, str) or re.fullmatch(
                        r"[0-9a-f]{40}", value
                    ) is None:
                        errors.append(
                            f"{label}: {name}.{field} must be an exact Git object"
                        )
        elif external_execution_status == (
            "third-live-session-grant-consumed-no-current-live-authority"
        ):
            if (
                authorization.get("external_execution_reauthorization_required")
                is not True
            ):
                errors.append(
                    f"{label}: consumed third live Session authority must require new exact external reauthorization"
                )
            for name, live_authorization, finding_ref in (
                (
                    "first_live_session_authorization",
                    first_live_authorization,
                    "FINDING-010-107",
                ),
                (
                    "second_live_session_authorization",
                    second_live_authorization,
                    "FINDING-010-111",
                ),
                (
                    "third_live_session_authorization",
                    third_live_authorization,
                    "FINDING-010-115",
                ),
            ):
                if not isinstance(live_authorization, dict):
                    errors.append(
                        f"{label}: consumed third live state must retain its exact receipt: {name}"
                    )
                    continue
                authorization_ref = live_authorization.get("authorization_ref")
                if (
                    live_authorization.get("status") != "consumed"
                    or not isinstance(authorization_ref, str)
                    or re.fullmatch(
                        r"codex-user-message:sha256:[0-9a-f]{64}",
                        authorization_ref,
                    )
                    is None
                    or live_authorization.get("excludes")
                    != "src-main-resources,credential-values,hidden,slice2,slice3,production-activation"
                    or live_authorization.get("execution_finding_ref")
                    != finding_ref
                ):
                    errors.append(
                        f"{label}: {name} must remain exact, excluded and evidence-bound"
                    )
                for field in (
                    "exact_product_commit",
                    "exact_product_tree",
                    "source_commit",
                    "source_tree",
                ):
                    value = live_authorization.get(field)
                    if not isinstance(value, str) or re.fullmatch(
                        r"[0-9a-f]{40}", value
                    ) is None:
                        errors.append(
                            f"{label}: {name}.{field} must be an exact Git object"
                        )
            if not isinstance(third_live_authorization, dict) or (
                third_live_authorization.get("conformance_execution_finding_ref")
                != "FINDING-010-114"
                or third_live_authorization.get(
                    "ark_tls_supplemental_authorization_ref"
                )
                != "codex-user-message:sha256:e89640faf226ce069216ba40c71448dac0d8e09faf898aacbe74577067d540b3"
                or third_live_authorization.get(
                    "ark_tls_cap_raise_authorization_ref"
                )
                != "codex-user-message:sha256:21786af7d671472735a0cf7f064a26a7e19030b8ca6291c14f83ca1c1bfdfae1"
            ):
                errors.append(
                    f"{label}: third live Session authority must retain exact conditional Conformance and Ark TLS receipts"
                )
        elif external_execution_status == (
            "fourth-live-session-grant-consumed-no-current-live-authority"
        ):
            if (
                authorization.get("external_execution_reauthorization_required")
                is not True
            ):
                errors.append(
                    f"{label}: consumed fourth live Session authority must require new exact external reauthorization"
                )
            for name, live_authorization, finding_ref in (
                (
                    "first_live_session_authorization",
                    first_live_authorization,
                    "FINDING-010-107",
                ),
                (
                    "second_live_session_authorization",
                    second_live_authorization,
                    "FINDING-010-111",
                ),
                (
                    "third_live_session_authorization",
                    third_live_authorization,
                    "FINDING-010-115",
                ),
                (
                    "fourth_live_session_authorization",
                    fourth_live_authorization,
                    "FINDING-010-119",
                ),
            ):
                if not isinstance(live_authorization, dict):
                    errors.append(
                        f"{label}: consumed fourth live state must retain its exact receipt: {name}"
                    )
                    continue
                authorization_ref = live_authorization.get("authorization_ref")
                if (
                    live_authorization.get("status") != "consumed"
                    or not isinstance(authorization_ref, str)
                    or re.fullmatch(
                        r"codex-user-message:sha256:[0-9a-f]{64}",
                        authorization_ref,
                    )
                    is None
                    or live_authorization.get("excludes")
                    != "src-main-resources,credential-values,hidden,slice2,slice3,production-activation"
                    or live_authorization.get("execution_finding_ref")
                    != finding_ref
                ):
                    errors.append(
                        f"{label}: {name} must remain exact, excluded and evidence-bound"
                    )
                for field in (
                    "exact_product_commit",
                    "exact_product_tree",
                    "source_commit",
                    "source_tree",
                ):
                    value = live_authorization.get(field)
                    if not isinstance(value, str) or re.fullmatch(
                        r"[0-9a-f]{40}", value
                    ) is None:
                        errors.append(
                            f"{label}: {name}.{field} must be an exact Git object"
                        )
            if (
                not isinstance(fourth_live_authorization, dict)
                or fourth_live_authorization.get(
                    "conformance_execution_finding_ref"
                )
                != "FINDING-010-118"
            ):
                errors.append(
                    f"{label}: fourth live Session authority must retain exact conditional Conformance receipt"
                )
        elif external_execution_status == (
            "fifth-live-session-grant-consumed-no-current-live-authority"
        ):
            if (
                authorization.get("external_execution_reauthorization_required")
                is not True
            ):
                errors.append(
                    f"{label}: consumed fifth live Session authority must require new exact external reauthorization"
                )
            for name, live_authorization, finding_ref in (
                (
                    "first_live_session_authorization",
                    first_live_authorization,
                    "FINDING-010-107",
                ),
                (
                    "second_live_session_authorization",
                    second_live_authorization,
                    "FINDING-010-111",
                ),
                (
                    "third_live_session_authorization",
                    third_live_authorization,
                    "FINDING-010-115",
                ),
                (
                    "fourth_live_session_authorization",
                    fourth_live_authorization,
                    "FINDING-010-119",
                ),
                (
                    "fifth_live_session_authorization",
                    fifth_live_authorization,
                    "FINDING-010-124",
                ),
            ):
                if not isinstance(live_authorization, dict):
                    errors.append(
                        f"{label}: consumed fifth live state must retain its exact receipt: {name}"
                    )
                    continue
                authorization_ref = live_authorization.get("authorization_ref")
                expected_receipt_pattern = (
                    r"local-user-message-utf8:sha256:[0-9a-f]{64}"
                    if name == "fifth_live_session_authorization"
                    else r"codex-user-message:sha256:[0-9a-f]{64}"
                )
                if (
                    live_authorization.get("status") != "consumed"
                    or not isinstance(authorization_ref, str)
                    or re.fullmatch(expected_receipt_pattern, authorization_ref)
                    is None
                    or live_authorization.get("excludes")
                    != "src-main-resources,credential-values,hidden,slice2,slice3,production-activation"
                    or live_authorization.get("execution_finding_ref")
                    != finding_ref
                ):
                    errors.append(
                        f"{label}: {name} must remain exact, excluded and evidence-bound"
                    )
                for field in (
                    "exact_product_commit",
                    "exact_product_tree",
                    "source_commit",
                    "source_tree",
                ):
                    value = live_authorization.get(field)
                    if not isinstance(value, str) or re.fullmatch(
                        r"[0-9a-f]{40}", value
                    ) is None:
                        errors.append(
                            f"{label}: {name}.{field} must be an exact Git object"
                        )
            if (
                not isinstance(fifth_live_authorization, dict)
                or fifth_live_authorization.get(
                    "conformance_execution_finding_ref"
                )
                != "FINDING-010-123"
            ):
                errors.append(
                    f"{label}: fifth live Session authority must retain exact conditional Conformance receipt"
                )
        elif external_execution_status == (
            "sixth-live-session-grant-consumed-no-current-live-authority"
        ):
            if (
                authorization.get("external_execution_reauthorization_required")
                is not True
            ):
                errors.append(
                    f"{label}: consumed sixth live Session authority must require new exact external reauthorization"
                )
            for name, live_authorization, finding_ref in (
                (
                    "first_live_session_authorization",
                    first_live_authorization,
                    "FINDING-010-107",
                ),
                (
                    "second_live_session_authorization",
                    second_live_authorization,
                    "FINDING-010-111",
                ),
                (
                    "third_live_session_authorization",
                    third_live_authorization,
                    "FINDING-010-115",
                ),
                (
                    "fourth_live_session_authorization",
                    fourth_live_authorization,
                    "FINDING-010-119",
                ),
                (
                    "fifth_live_session_authorization",
                    fifth_live_authorization,
                    "FINDING-010-124",
                ),
                (
                    "sixth_live_session_authorization",
                    sixth_live_authorization,
                    "FINDING-010-127",
                ),
            ):
                if not isinstance(live_authorization, dict):
                    errors.append(
                        f"{label}: consumed sixth live state must retain its exact receipt: {name}"
                    )
                    continue
                authorization_ref = live_authorization.get("authorization_ref")
                expected_receipt_pattern = (
                    r"local-user-message-utf8:sha256:[0-9a-f]{64}"
                    if name
                    in {
                        "fifth_live_session_authorization",
                        "sixth_live_session_authorization",
                    }
                    else r"codex-user-message:sha256:[0-9a-f]{64}"
                )
                if (
                    live_authorization.get("status") != "consumed"
                    or not isinstance(authorization_ref, str)
                    or re.fullmatch(expected_receipt_pattern, authorization_ref)
                    is None
                    or live_authorization.get("excludes")
                    != "src-main-resources,credential-values,hidden,slice2,slice3,production-activation"
                    or live_authorization.get("execution_finding_ref")
                    != finding_ref
                ):
                    errors.append(
                        f"{label}: {name} must remain exact, excluded and evidence-bound"
                    )
                for field in (
                    "exact_product_commit",
                    "exact_product_tree",
                    "source_commit",
                    "source_tree",
                ):
                    value = live_authorization.get(field)
                    if not isinstance(value, str) or re.fullmatch(
                        r"[0-9a-f]{40}", value
                    ) is None:
                        errors.append(
                            f"{label}: {name}.{field} must be an exact Git object"
                        )
            if (
                not isinstance(sixth_live_authorization, dict)
                or sixth_live_authorization.get(
                    "conformance_execution_finding_ref"
                )
                != "FINDING-010-126"
            ):
                errors.append(
                    f"{label}: sixth live Session authority must retain exact conditional Conformance receipt"
                )
        else:
            errors.append(
                f"{label}: current development authorization must have no active external authority; only not-authorized or consumed live Session grants are allowed"
            )
        if not isinstance(authorization, dict) or (
            authorization.get("docs_sync_authorizes_product_code") is not False
        ):
            errors.append(
                f"{label}: docs-only synchronization receipt must not authorize product code"
            )
        development = manifest.get("development")
        slices = (
            development.get("slices")
            if isinstance(development, dict)
            else None
        )
        slice1 = (
            slices.get("ITER-010-SLICE-001")
            if isinstance(slices, dict)
            else None
        )
        if external_execution_status == (
            "sixth-live-session-grant-consumed-no-current-live-authority"
        ):
            expected_live_question_status = (
                "authorized-executed-failed-run-041-three-of-five-responses-"
                "leakage-pass-v6-remediation-local-candidate-fresh-conformance-"
                "and-new-exact-grant-required"
            )
        elif external_execution_status == (
            "fifth-live-session-grant-consumed-no-current-live-authority"
        ):
            expected_live_question_status = (
                "authorized-executed-failed-run-040-one-of-five-limitation-"
                "leakage-pass-v5-remediation-local-candidate-fresh-conformance-"
                "and-new-exact-grant-required"
            )
        elif external_execution_status == (
            "fourth-live-session-grant-consumed-no-current-live-authority"
        ):
            expected_live_question_status = (
                "authorized-executed-failed-run-038-one-of-five-limitation-"
                "leakage-pass-v4-remediation-local-candidate-fresh-conformance-"
                "and-new-exact-grant-required"
            )
        elif external_execution_status == (
            "third-live-session-grant-consumed-no-current-live-authority"
        ):
            expected_live_question_status = (
                "authorized-executed-failed-run-037-leakage-pass-v3-remediation-"
                "local-candidate-fresh-conformance-and-new-exact-grant-required"
            )
        elif external_execution_status == (
            "second-live-session-grant-consumed-no-current-live-authority"
        ):
            expected_live_question_status = (
                "authorized-executed-failed-run-036-leakage-pass-v2-remediation-"
                "local-candidate-fresh-conformance-and-new-exact-grant-required"
            )
        elif external_execution_status == (
            "first-live-session-grant-consumed-no-current-live-authority"
        ):
            expected_live_question_status = (
                "authorized-executed-failed-run-035-remediation-local-candidate-"
                "new-exact-grant-required"
            )
        else:
            expected_live_question_status = (
                "not-authorized-conversational-five-turn-canary-not-executed"
            )
        if not isinstance(slice1, dict) or (
            slice1.get("status") != "authorized"
            or slice1.get("coding_input") is not True
            or slice1.get("authorization_ref") != acceptance_ref
            or slice1.get("authorized_at") != accepted_at
            or slice1.get("live_question_status")
            != expected_live_question_status
        ):
            errors.append(
                f"{label}: current Slice1 authorization must preserve the exact unexecuted or consumed failed conversational live canary evidence state"
            )
        if isinstance(slices, dict):
            for slice_id in ("ITER-010-SLICE-002", "ITER-010-SLICE-003"):
                state = slices.get(slice_id)
                if not isinstance(state, dict) or (
                    state.get("status") != "proposed"
                    or state.get("coding_input") is not False
                    or state.get("authorization_ref") != "not-authorized"
                ):
                    errors.append(
                        f"{label}: accepted current Readiness must not authorize {slice_id}"
                    )
        root_authorization = (
            authorization.get("slice1_needed_rights_root_authorization")
            if isinstance(authorization, dict)
            else None
        )
        if not isinstance(root_authorization, dict) or (
            root_authorization.get("status")
            != "historical-consumed-not-active"
            or root_authorization.get("excludes")
            != "slice2-slice3-hidden-and-production-activation"
        ):
            errors.append(
                f"{label}: historical needed-rights grant must remain consumed and hidden/Production excluded"
            )
    elif readiness_status == "refresh-required-not-accepted":
        for field in (
            "current_readiness_acceptance_ref",
            "current_readiness_accepted_at",
            "current_readiness_planning_commit",
            "current_readiness_planning_tree",
        ):
            if field in readiness:
                errors.append(
                    f"{label}: refresh-required Readiness must not claim {field}"
                )
        if (
            not isinstance(iteration_state, dict)
            or iteration_state.get("status") != "paused"
            or iteration_state.get("coding_input") is not False
            or not isinstance(rework, dict)
            or rework.get("coding_input") is not False
            or not isinstance(authorization, dict)
            or authorization.get("active_slice") != "none"
            or authorization.get("refreshed_readiness_required") is not True
            or authorization.get("explicit_user_reauthorization_required")
            is not True
        ):
            errors.append(
                f"{label}: refresh-required Readiness requires a paused non-coding iteration with no active Slice"
            )
    for forbidden_field in (
        "amended_architecture_decision",
        "investigation_budget_status",
    ):
        if forbidden_field in readiness:
            errors.append(
                f"{label}: readiness_inputs.{forbidden_field} ambiguously presents a legacy input as current"
            )
    return errors


def validate_iter010_direction_checkpoint_policy(
    manifest: dict[str, object], label: str
) -> list[str]:
    """Freeze ITER-010's value-first checkpoints without globalizing them."""

    policy = manifest.get("experience_delivery_policy")
    if not isinstance(policy, dict):
        return [f"{label}: ITER-010 direction checkpoints require experience_delivery_policy"]

    errors: list[str] = []
    for field, expected in (
        (
            "direction_discovery_principle_ref",
            ITER010_DIRECTION_DISCOVERY_PRINCIPLE_REF,
        ),
        ("micro_checkpoint_count", 4),
        ("micro_checkpoint_order", ITER010_DIRECTION_MICRO_CHECKPOINT_ORDER),
        ("pdr004_schedule_fields_are_legacy_validator_compatibility_only", True),
        ("checkpoint_miss_action", ITER010_DIRECTION_CHECKPOINT_MISS_ACTION),
    ):
        if policy.get(field) != expected:
            errors.append(
                f"{label}: ITER-010 experience_delivery_policy.{field} must equal {expected}"
            )
    for ambiguous_field in (
        "phase",
        "hardening_unlocked",
        "hardening_unlock_decision",
        "local_checkpoint_requires_new_development_authorization",
    ):
        if ambiguous_field in policy:
            errors.append(
                f"{label}: ITER-010 experience_delivery_policy.{ambiguous_field} must not create a parallel lifecycle or authorization state"
            )
    return errors


def _manifest_nested_sequence(
    manifest: dict[str, object],
    path: tuple[str, ...],
    manifest_text: str | None,
) -> list[str] | None:
    """Resolve an exact nested sequence from an in-memory or file manifest."""

    value: object = manifest
    for key in path:
        if not isinstance(value, dict) or key not in value:
            value = None
            break
        value = value[key]
    if isinstance(value, list):
        return [str(item) for item in value]
    if manifest_text is None:
        return None
    return manifest_resolved_nested_sequence_items(manifest_text, path)


def _plan_path_is_safe(value: str) -> bool:
    """Reject broad, absolute, parent-traversing or empty plan path patterns."""

    if (
        not value
        or value in {"*", "**", "**/*"}
        or value.startswith(("/", "~"))
        or "\\" in value
    ):
        return False
    path = PurePosixPath(value.removesuffix("/**"))
    return path.as_posix() not in {"", "."} and ".." not in path.parts


def iter010_plan_action_specs() -> dict[str, dict[str, object]]:
    """Return the PDR-009 action registry as immutable-by-caller data.

    The Manifest stores the current action separately from its transition and
    locks, while future action contracts nest those two mappings.  Keeping one
    machine-owned registry here prevents a transition commit from defining its
    own permissions, paths, or successor after seeing a Result.
    """

    all_locked = {field: True for field in ITER010_PLAN_LOCK_FIELDS}

    def build(
        *,
        registry_key: str,
        action_id: str,
        kind: str,
        case_id: str,
        coding_allowed: bool,
        external_execution_allowed: bool,
        result_ref: str,
        result_path: str,
        evidence_path: str,
        produced_case_ids: tuple[str, ...],
        prerequisite_case_ids: tuple[str, ...],
        allowed_change_paths: tuple[str, ...],
        forbidden_change_paths: tuple[str, ...],
        pass_next_action_id: str,
        fail_next_action_id: str,
        invalid_next_action_id: str,
        locks: dict[str, bool],
        gate_status: str,
        required_result: dict[str, object] | tuple[dict[str, object], ...] | None,
    ) -> dict[str, object]:
        return {
            "registry_key": registry_key,
            "scalars": {
                "id": action_id,
                "owner_slice_ref": "ITER-010-SLICE-001",
                "kind": kind,
                "status": "authorized",
                "case_id": case_id,
                "coding_allowed": coding_allowed,
                "external_execution_allowed": external_execution_allowed,
                "result_ref": result_ref,
                "result_path": result_path,
                "evidence_schema": ITER010_PLAN_EVIDENCE_SCHEMA,
                "evidence_path": evidence_path,
                "evidence_verifier": ITER010_PLAN_EVIDENCE_VERIFIER,
            },
            "sequences": {
                "runner_identity_paths": ITER010_PLAN_RUNNER_IDENTITY_PATHS,
                "produced_case_ids": produced_case_ids,
                "prerequisite_case_ids": prerequisite_case_ids,
                "allowed_change_paths": allowed_change_paths,
                "forbidden_change_paths": forbidden_change_paths,
            },
            "transition": {
                "pass_next_action_id": pass_next_action_id,
                "fail_next_action_id": fail_next_action_id,
                "invalid_next_action_id": invalid_next_action_id,
            },
            "locks": locks,
            "gate_status": gate_status,
            "required_result": required_result,
        }

    def predecessor(
        result_id: str,
        result_path: str,
        evidence_path: str,
        action_ref: str,
        case_id: str,
        verdict: str,
    ) -> dict[str, object]:
        return {
            "id": result_id,
            "path": result_path,
            "evidence_path": evidence_path,
            "action_ref": action_ref,
            "verification_case_id": case_id,
            "plan_gate_verdict": verdict,
        }

    freeze_prerequisites = ITER010_DIRECTION_PREREQUISITE_CASE_IDS
    external_prerequisites = (
        ITER010_CURRENT_ACTION_CASE_ID,
        ITER010_PUBLIC_AUTHORITY_ADMISSION_CASE_ID,
        *ITER010_DIRECTION_PREREQUISITE_CASE_IDS,
    )
    recovery_spec = build(
        registry_key="user_plan_recovery",
        action_id=ITER010_PLAN_RECOVERY_ACTION_ID,
        kind="governance",
        case_id=ITER010_PLAN_RECOVERY_CASE_ID,
        coding_allowed=False,
        external_execution_allowed=False,
        result_ref=ITER010_PLAN_RECOVERY_RESULT_REF,
        result_path=ITER010_PLAN_RECOVERY_RESULT_PATH,
        evidence_path=ITER010_PLAN_RECOVERY_EVIDENCE_PATH,
        produced_case_ids=(ITER010_PLAN_RECOVERY_CASE_ID,),
        prerequisite_case_ids=(),
        allowed_change_paths=ITER010_PLAN_RECOVERY_ALLOWED_CHANGE_PATHS,
        forbidden_change_paths=ITER010_PLAN_RECOVERY_FORBIDDEN_CHANGE_PATHS,
        pass_next_action_id=ITER010_PLAN_RECOVERY_ACTION_ID,
        fail_next_action_id=ITER010_PLAN_RECOVERY_ACTION_ID,
        invalid_next_action_id=ITER010_PLAN_RECOVERY_ACTION_ID,
        locks=all_locked,
        gate_status="locked-until-direction-freeze-pass",
        required_result=None,
    )
    recovery_scalars = recovery_spec["scalars"]
    recovery_sequences = recovery_spec["sequences"]
    assert isinstance(recovery_scalars, dict)
    assert isinstance(recovery_sequences, dict)
    recovery_scalars["evidence_verifier"] = ITER010_PLAN_RECOVERY_VERIFIER
    recovery_sequences["runner_identity_paths"] = (
        ITER010_PLAN_RECOVERY_RUNNER_IDENTITY_PATHS
    )
    return {
        ITER010_PLAN_RECOVERY_ACTION_ID: recovery_spec,
        ITER010_CURRENT_ACTION_ID: build(
            registry_key="direction_freeze",
            action_id=ITER010_CURRENT_ACTION_ID,
            kind="four-arm-direction-gate-freeze",
            case_id=ITER010_CURRENT_ACTION_CASE_ID,
            coding_allowed=True,
            external_execution_allowed=False,
            result_ref=ITER010_CURRENT_ACTION_RESULT_REF,
            result_path=ITER010_CURRENT_ACTION_RESULT_PATH,
            evidence_path=ITER010_CURRENT_ACTION_EVIDENCE_PATH,
            produced_case_ids=(
                ITER010_CURRENT_ACTION_CASE_ID,
                ITER010_PUBLIC_AUTHORITY_ADMISSION_CASE_ID,
            ),
            prerequisite_case_ids=freeze_prerequisites,
            allowed_change_paths=ITER010_DIRECTION_FREEZE_ALLOWED_CHANGE_PATHS,
            forbidden_change_paths=ITER010_DIRECTION_FREEZE_FORBIDDEN_CHANGE_PATHS,
            pass_next_action_id=ITER010_PREFERRED_QUALITY_ACTION_ID,
            fail_next_action_id=ITER010_DIRECTION_FREEZE_REWORK_ACTION_ID,
            invalid_next_action_id=ITER010_CURRENT_ACTION_ID,
            locks=all_locked,
            gate_status="locked-until-direction-freeze-pass",
            required_result=None,
        ),
        ITER010_PREFERRED_QUALITY_ACTION_ID: build(
            registry_key="preferred_quality",
            action_id=ITER010_PREFERRED_QUALITY_ACTION_ID,
            kind="four-arm-direction-quality-gate",
            case_id=ITER010_DIRECTION_QUALITY_CASE_ID,
            coding_allowed=False,
            external_execution_allowed=True,
            result_ref=ITER010_PREFERRED_QUALITY_RESULT_REF,
            result_path=ITER010_PREFERRED_QUALITY_RESULT_PATH,
            evidence_path=ITER010_PREFERRED_QUALITY_EVIDENCE_PATH,
            produced_case_ids=(ITER010_DIRECTION_QUALITY_CASE_ID,),
            prerequisite_case_ids=external_prerequisites,
            allowed_change_paths=ITER010_PREFERRED_QUALITY_ALLOWED_CHANGE_PATHS,
            forbidden_change_paths=ITER010_DIRECTION_QUALITY_FORBIDDEN_CHANGE_PATHS,
            pass_next_action_id=ITER010_MINIMUM_WEB_ACTION_ID,
            fail_next_action_id=ITER010_DIRECTION_REWORK_ACTION_ID,
            invalid_next_action_id=ITER010_FALLBACK_REFREEZE_ACTION_ID,
            locks={**all_locked, "provider_dispatch": False},
            gate_status="authorized",
            required_result=predecessor(
                ITER010_CURRENT_ACTION_RESULT_REF,
                ITER010_CURRENT_ACTION_RESULT_PATH,
                ITER010_CURRENT_ACTION_EVIDENCE_PATH,
                ITER010_CURRENT_ACTION_ID,
                ITER010_CURRENT_ACTION_CASE_ID,
                "PASS",
            ),
        ),
        ITER010_FALLBACK_REFREEZE_ACTION_ID: build(
            registry_key="fallback_refreeze",
            action_id=ITER010_FALLBACK_REFREEZE_ACTION_ID,
            kind="fallback-route-batch-refreeze",
            case_id=ITER010_FALLBACK_REFREEZE_CASE_ID,
            coding_allowed=False,
            external_execution_allowed=False,
            result_ref=ITER010_FALLBACK_REFREEZE_RESULT_REF,
            result_path=ITER010_FALLBACK_REFREEZE_RESULT_PATH,
            evidence_path=ITER010_FALLBACK_REFREEZE_EVIDENCE_PATH,
            produced_case_ids=(ITER010_FALLBACK_REFREEZE_CASE_ID,),
            prerequisite_case_ids=external_prerequisites,
            allowed_change_paths=ITER010_FALLBACK_REFREEZE_ALLOWED_CHANGE_PATHS,
            forbidden_change_paths=ITER010_DIRECTION_QUALITY_FORBIDDEN_CHANGE_PATHS,
            pass_next_action_id=ITER010_FALLBACK_QUALITY_ACTION_ID,
            fail_next_action_id=ITER010_PREFERRED_QUALITY_ACTION_ID,
            invalid_next_action_id=ITER010_FALLBACK_REFREEZE_ACTION_ID,
            locks=all_locked,
            gate_status="preferred-invalid-fallback-refreeze-authorized",
            required_result=predecessor(
                ITER010_PREFERRED_QUALITY_RESULT_REF,
                ITER010_PREFERRED_QUALITY_RESULT_PATH,
                ITER010_PREFERRED_QUALITY_EVIDENCE_PATH,
                ITER010_PREFERRED_QUALITY_ACTION_ID,
                ITER010_DIRECTION_QUALITY_CASE_ID,
                "INVALID",
            ),
        ),
        ITER010_FALLBACK_QUALITY_ACTION_ID: build(
            registry_key="fallback_quality",
            action_id=ITER010_FALLBACK_QUALITY_ACTION_ID,
            kind="four-arm-direction-quality-gate",
            case_id=ITER010_DIRECTION_QUALITY_CASE_ID,
            coding_allowed=False,
            external_execution_allowed=True,
            result_ref=ITER010_FALLBACK_QUALITY_RESULT_REF,
            result_path=ITER010_FALLBACK_QUALITY_RESULT_PATH,
            evidence_path=ITER010_FALLBACK_QUALITY_EVIDENCE_PATH,
            produced_case_ids=(ITER010_DIRECTION_QUALITY_CASE_ID,),
            prerequisite_case_ids=(
                ITER010_FALLBACK_REFREEZE_CASE_ID,
                *external_prerequisites,
            ),
            allowed_change_paths=ITER010_FALLBACK_QUALITY_ALLOWED_CHANGE_PATHS,
            forbidden_change_paths=ITER010_DIRECTION_QUALITY_FORBIDDEN_CHANGE_PATHS,
            pass_next_action_id=ITER010_MINIMUM_WEB_ACTION_ID,
            fail_next_action_id=ITER010_DIRECTION_REWORK_ACTION_ID,
            invalid_next_action_id=ITER010_FALLBACK_QUALITY_ACTION_ID,
            locks={**all_locked, "provider_dispatch": False},
            gate_status="fallback-refreeze-passed-direction-quality-authorized",
            required_result=predecessor(
                ITER010_FALLBACK_REFREEZE_RESULT_REF,
                ITER010_FALLBACK_REFREEZE_RESULT_PATH,
                ITER010_FALLBACK_REFREEZE_EVIDENCE_PATH,
                ITER010_FALLBACK_REFREEZE_ACTION_ID,
                ITER010_FALLBACK_REFREEZE_CASE_ID,
                "PASS",
            ),
        ),
        ITER010_DIRECTION_FREEZE_REWORK_ACTION_ID: build(
            registry_key="direction_freeze_rework",
            action_id=ITER010_DIRECTION_FREEZE_REWORK_ACTION_ID,
            kind="four-arm-direction-gate-freeze-rework",
            case_id=ITER010_DIRECTION_FREEZE_REWORK_CASE_ID,
            coding_allowed=True,
            external_execution_allowed=False,
            result_ref=ITER010_DIRECTION_FREEZE_REWORK_RESULT_REF,
            result_path=ITER010_DIRECTION_FREEZE_REWORK_RESULT_PATH,
            evidence_path=ITER010_DIRECTION_FREEZE_REWORK_EVIDENCE_PATH,
            produced_case_ids=(ITER010_DIRECTION_FREEZE_REWORK_CASE_ID,),
            prerequisite_case_ids=freeze_prerequisites,
            allowed_change_paths=ITER010_DIRECTION_FREEZE_REWORK_ALLOWED_CHANGE_PATHS,
            forbidden_change_paths=ITER010_DIRECTION_FREEZE_FORBIDDEN_CHANGE_PATHS,
            pass_next_action_id=ITER010_CURRENT_ACTION_ID,
            fail_next_action_id=ITER010_DIRECTION_FREEZE_REWORK_ACTION_ID,
            invalid_next_action_id=ITER010_DIRECTION_FREEZE_REWORK_ACTION_ID,
            locks=all_locked,
            gate_status="locked-until-direction-freeze-pass",
            required_result=predecessor(
                ITER010_CURRENT_ACTION_RESULT_REF,
                ITER010_CURRENT_ACTION_RESULT_PATH,
                ITER010_CURRENT_ACTION_EVIDENCE_PATH,
                ITER010_CURRENT_ACTION_ID,
                ITER010_CURRENT_ACTION_CASE_ID,
                "FAIL",
            ),
        ),
        ITER010_DIRECTION_REWORK_ACTION_ID: build(
            registry_key="direction_rework",
            action_id=ITER010_DIRECTION_REWORK_ACTION_ID,
            kind="four-arm-failure-attribution",
            case_id=ITER010_DIRECTION_REWORK_CASE_ID,
            coding_allowed=False,
            external_execution_allowed=False,
            result_ref=ITER010_DIRECTION_REWORK_RESULT_REF,
            result_path=ITER010_DIRECTION_REWORK_RESULT_PATH,
            evidence_path=ITER010_DIRECTION_REWORK_EVIDENCE_PATH,
            produced_case_ids=(ITER010_DIRECTION_REWORK_CASE_ID,),
            prerequisite_case_ids=external_prerequisites,
            allowed_change_paths=ITER010_DIRECTION_REWORK_ALLOWED_CHANGE_PATHS,
            forbidden_change_paths=ITER010_DIRECTION_REWORK_FORBIDDEN_CHANGE_PATHS,
            pass_next_action_id=ITER010_RESPONSIBILITY_PLAN_ACTION_ID,
            fail_next_action_id=ITER010_DIRECTION_REWORK_ACTION_ID,
            invalid_next_action_id=ITER010_DIRECTION_REWORK_ACTION_ID,
            locks=all_locked,
            gate_status="failed-rework-attribution-authorized",
            required_result=(
                predecessor(
                    ITER010_PREFERRED_QUALITY_RESULT_REF,
                    ITER010_PREFERRED_QUALITY_RESULT_PATH,
                    ITER010_PREFERRED_QUALITY_EVIDENCE_PATH,
                    ITER010_PREFERRED_QUALITY_ACTION_ID,
                    ITER010_DIRECTION_QUALITY_CASE_ID,
                    "FAIL",
                ),
                predecessor(
                    ITER010_FALLBACK_QUALITY_RESULT_REF,
                    ITER010_FALLBACK_QUALITY_RESULT_PATH,
                    ITER010_FALLBACK_QUALITY_EVIDENCE_PATH,
                    ITER010_FALLBACK_QUALITY_ACTION_ID,
                    ITER010_DIRECTION_QUALITY_CASE_ID,
                    "FAIL",
                ),
            ),
        ),
        ITER010_MINIMUM_WEB_ACTION_ID: build(
            registry_key="minimum_web_chat",
            action_id=ITER010_MINIMUM_WEB_ACTION_ID,
            kind="minimum-existing-web-chat",
            case_id=ITER010_MINIMUM_WEB_CASE_ID,
            coding_allowed=False,
            external_execution_allowed=True,
            result_ref=ITER010_MINIMUM_WEB_RESULT_REF,
            result_path=ITER010_MINIMUM_WEB_RESULT_PATH,
            evidence_path=ITER010_MINIMUM_WEB_EVIDENCE_PATH,
            produced_case_ids=(
                ITER010_MINIMUM_WEB_CASE_ID,
                "V-CHAT-001",
                "V-CHAT-QUALITY-001",
                "V-CHAT-XD-001",
                "V-TIMEBOX-CHAT-001",
                ITER010_PUBLIC_AUTHORITY_CASE_ID,
            ),
            prerequisite_case_ids=(
                ITER010_DIRECTION_QUALITY_CASE_ID,
                *external_prerequisites,
            ),
            allowed_change_paths=ITER010_MINIMUM_WEB_ALLOWED_CHANGE_PATHS,
            forbidden_change_paths=ITER010_DIRECTION_QUALITY_FORBIDDEN_CHANGE_PATHS,
            pass_next_action_id=ITER010_USER_DIRECTION_ACTION_ID,
            fail_next_action_id=ITER010_WEB_FAILURE_ACTION_ID,
            invalid_next_action_id=ITER010_MINIMUM_WEB_ACTION_ID,
            locks={**all_locked, "web_canary": False, "provider_dispatch": False},
            gate_status="direction-quality-passed-minimum-web-authorized",
            required_result=(
                predecessor(
                    ITER010_PREFERRED_QUALITY_RESULT_REF,
                    ITER010_PREFERRED_QUALITY_RESULT_PATH,
                    ITER010_PREFERRED_QUALITY_EVIDENCE_PATH,
                    ITER010_PREFERRED_QUALITY_ACTION_ID,
                    ITER010_DIRECTION_QUALITY_CASE_ID,
                    "PASS",
                ),
                predecessor(
                    ITER010_FALLBACK_QUALITY_RESULT_REF,
                    ITER010_FALLBACK_QUALITY_RESULT_PATH,
                    ITER010_FALLBACK_QUALITY_EVIDENCE_PATH,
                    ITER010_FALLBACK_QUALITY_ACTION_ID,
                    ITER010_DIRECTION_QUALITY_CASE_ID,
                    "PASS",
                ),
            ),
        ),
        ITER010_WEB_FAILURE_ACTION_ID: build(
            registry_key="web_failure_attribution",
            action_id=ITER010_WEB_FAILURE_ACTION_ID,
            kind="governance",
            case_id=ITER010_WEB_FAILURE_CASE_ID,
            coding_allowed=False,
            external_execution_allowed=False,
            result_ref=ITER010_WEB_FAILURE_RESULT_REF,
            result_path=ITER010_WEB_FAILURE_RESULT_PATH,
            evidence_path=ITER010_WEB_FAILURE_EVIDENCE_PATH,
            produced_case_ids=(ITER010_WEB_FAILURE_CASE_ID,),
            prerequisite_case_ids=(
                ITER010_DIRECTION_QUALITY_CASE_ID,
                *external_prerequisites,
            ),
            allowed_change_paths=ITER010_WEB_FAILURE_GOVERNANCE_ALLOWED_CHANGE_PATHS,
            forbidden_change_paths=ITER010_RESPONSIBILITY_PLAN_FORBIDDEN_CHANGE_PATHS,
            pass_next_action_id=ITER010_WEB_FAILURE_ACTION_ID,
            fail_next_action_id=ITER010_WEB_FAILURE_ACTION_ID,
            invalid_next_action_id=ITER010_WEB_FAILURE_ACTION_ID,
            locks=all_locked,
            gate_status="minimum-web-failed-attribution-authorized",
            required_result=predecessor(
                ITER010_MINIMUM_WEB_RESULT_REF,
                ITER010_MINIMUM_WEB_RESULT_PATH,
                ITER010_MINIMUM_WEB_EVIDENCE_PATH,
                ITER010_MINIMUM_WEB_ACTION_ID,
                ITER010_MINIMUM_WEB_CASE_ID,
                "FAIL",
            ),
        ),
        ITER010_USER_DIRECTION_ACTION_ID: build(
            registry_key="user_direction_decision",
            action_id=ITER010_USER_DIRECTION_ACTION_ID,
            kind="governance",
            case_id=ITER010_USER_DIRECTION_CASE_ID,
            coding_allowed=False,
            external_execution_allowed=False,
            result_ref=ITER010_USER_DIRECTION_RESULT_REF,
            result_path=ITER010_USER_DIRECTION_RESULT_PATH,
            evidence_path=ITER010_USER_DIRECTION_EVIDENCE_PATH,
            produced_case_ids=(ITER010_USER_DIRECTION_CASE_ID,),
            prerequisite_case_ids=(
                ITER010_MINIMUM_WEB_CASE_ID,
                ITER010_DIRECTION_QUALITY_CASE_ID,
                *external_prerequisites,
            ),
            allowed_change_paths=ITER010_USER_DIRECTION_GOVERNANCE_ALLOWED_CHANGE_PATHS,
            forbidden_change_paths=ITER010_RESPONSIBILITY_PLAN_FORBIDDEN_CHANGE_PATHS,
            pass_next_action_id=ITER010_USER_DIRECTION_ACTION_ID,
            fail_next_action_id=ITER010_USER_DIRECTION_ACTION_ID,
            invalid_next_action_id=ITER010_USER_DIRECTION_ACTION_ID,
            locks=all_locked,
            gate_status="minimum-web-passed-user-decision-authorized",
            required_result=predecessor(
                ITER010_MINIMUM_WEB_RESULT_REF,
                ITER010_MINIMUM_WEB_RESULT_PATH,
                ITER010_MINIMUM_WEB_EVIDENCE_PATH,
                ITER010_MINIMUM_WEB_ACTION_ID,
                ITER010_MINIMUM_WEB_CASE_ID,
                "PASS",
            ),
        ),
        ITER010_RESPONSIBILITY_PLAN_ACTION_ID: build(
            registry_key="responsibility_plan",
            action_id=ITER010_RESPONSIBILITY_PLAN_ACTION_ID,
            kind="governance",
            case_id=ITER010_RESPONSIBILITY_PLAN_CASE_ID,
            coding_allowed=False,
            external_execution_allowed=False,
            result_ref=ITER010_RESPONSIBILITY_PLAN_RESULT_REF,
            result_path=ITER010_RESPONSIBILITY_PLAN_RESULT_PATH,
            evidence_path=ITER010_RESPONSIBILITY_PLAN_EVIDENCE_PATH,
            produced_case_ids=(ITER010_RESPONSIBILITY_PLAN_CASE_ID,),
            prerequisite_case_ids=(
                ITER010_DIRECTION_REWORK_CASE_ID,
                ITER010_CURRENT_ACTION_CASE_ID,
                ITER010_PUBLIC_AUTHORITY_ADMISSION_CASE_ID,
                *ITER010_DIRECTION_PREREQUISITE_CASE_IDS,
            ),
            allowed_change_paths=ITER010_RESPONSIBILITY_PLAN_ALLOWED_CHANGE_PATHS,
            forbidden_change_paths=ITER010_RESPONSIBILITY_PLAN_FORBIDDEN_CHANGE_PATHS,
            pass_next_action_id=ITER010_RESPONSIBILITY_PLAN_ACTION_ID,
            fail_next_action_id=ITER010_RESPONSIBILITY_PLAN_ACTION_ID,
            invalid_next_action_id=ITER010_RESPONSIBILITY_PLAN_ACTION_ID,
            locks=all_locked,
            gate_status="direction-failure-attributed-governance-plan-authorized",
            required_result=predecessor(
                ITER010_DIRECTION_REWORK_RESULT_REF,
                ITER010_DIRECTION_REWORK_RESULT_PATH,
                ITER010_DIRECTION_REWORK_EVIDENCE_PATH,
                ITER010_DIRECTION_REWORK_ACTION_ID,
                ITER010_DIRECTION_REWORK_CASE_ID,
                "PASS",
            ),
        ),
    }


def _exact_plan_scalar(actual: object, expected: object) -> bool:
    """Compare plan scalars without accepting bool/int equivalence."""

    return type(actual) is type(expected) and actual == expected


def _plan_canonical_json_digest(value: object) -> str:
    """Digest one model-transparent plan object using its canonical JSON form."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _validate_plan_bound_object(
    action_evidence: dict[str, object],
    object_field: str,
    digest_field: str,
    label: str,
) -> list[str]:
    """Require a complete object and a digest derived from those exact values."""

    value = action_evidence.get(object_field)
    if not isinstance(value, dict) or not value:
        return [f"{label}: {object_field} must be a non-empty object"]
    expected = _plan_canonical_json_digest(value)
    if action_evidence.get(digest_field) != expected:
        return [
            f"{label}: {digest_field} must match the canonical {object_field}"
        ]
    return []


def _validate_provider_neutral_root_input_set(
    value: object, label: str
) -> list[str]:
    """Mirror the closed provider-neutral root schema at the docs trust boundary."""

    if not isinstance(value, dict):
        return [f"{label}: provider_neutral_root_input_set must be an object"]

    errors: list[str] = []
    expected_root_keys = {"schema", "question_ids", "system_arm_ids", "entries"}
    if set(map(str, value)) != expected_root_keys:
        errors.append(
            f"{label}: provider_neutral_root_input_set must contain exactly "
            "schema, question_ids, system_arm_ids, and entries"
        )
    if value.get("schema") != "VALUE_GATE_PROVIDER_NEUTRAL_ROOT_INPUT_SET@1":
        errors.append(
            f"{label}: provider_neutral_root_input_set.schema must equal "
            "VALUE_GATE_PROVIDER_NEUTRAL_ROOT_INPUT_SET@1"
        )

    question_ids = value.get("question_ids")
    valid_question_ids = (
        isinstance(question_ids, list)
        and len(question_ids) == 3
        and all(
            isinstance(question_id, str)
            and re.fullmatch(r"Q-[A-Z0-9][A-Z0-9._-]*", question_id) is not None
            for question_id in question_ids
        )
        and len(set(question_ids)) == 3
    )
    if not valid_question_ids:
        errors.append(
            f"{label}: provider_neutral_root_input_set.question_ids must contain exactly three unique Q-* IDs"
        )

    expected_arm_ids = list(ITER010_DIRECTION_QUALITY_ARMS[:3])
    system_arm_ids = value.get("system_arm_ids")
    if system_arm_ids != expected_arm_ids:
        errors.append(
            f"{label}: provider_neutral_root_input_set.system_arm_ids must equal the exact first three direction-quality arms"
        )

    entries = value.get("entries")
    if not isinstance(entries, list):
        errors.append(
            f"{label}: provider_neutral_root_input_set.entries must be a list"
        )
        return errors

    seen_pairs: set[tuple[str, str]] = set()
    for index, entry in enumerate(entries):
        entry_label = f"{label}: provider_neutral_root_input_set.entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{entry_label} must be an object")
            continue
        if set(map(str, entry)) != {
            "question_id",
            "system_arm_id",
            "root_input_digest",
        }:
            errors.append(
                f"{entry_label} must contain exactly question_id, system_arm_id, and root_input_digest"
            )
        question_id = entry.get("question_id")
        system_arm_id = entry.get("system_arm_id")
        digest = entry.get("root_input_digest")
        if (
            not isinstance(question_id, str)
            or not valid_question_ids
            or question_id not in question_ids
        ):
            errors.append(f"{entry_label}.question_id must reference question_ids")
        if not isinstance(system_arm_id, str) or system_arm_id not in expected_arm_ids:
            errors.append(
                f"{entry_label}.system_arm_id must reference the exact system_arm_ids"
            )
        if not isinstance(digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", digest
        ) is None:
            errors.append(f"{entry_label}.root_input_digest must be an exact sha256 digest")
        if isinstance(question_id, str) and isinstance(system_arm_id, str):
            pair = (question_id, system_arm_id)
            if pair in seen_pairs:
                errors.append(
                    f"{entry_label} duplicates question_id/system_arm_id pair {pair}"
                )
            seen_pairs.add(pair)

    if valid_question_ids and system_arm_ids == expected_arm_ids:
        expected_pairs = {
            (question_id, system_arm_id)
            for question_id in question_ids
            for system_arm_id in expected_arm_ids
        }
        if seen_pairs != expected_pairs or len(entries) != len(expected_pairs):
            errors.append(
                f"{label}: provider_neutral_root_input_set.entries must be the complete question_ids x system_arm_ids Cartesian product without omissions or extras"
            )
    return errors


def _validate_iter010_action_mapping(
    manifest: dict[str, object],
    manifest_text: str | None,
    action: dict[str, object],
    spec: dict[str, object],
    path: tuple[str, ...],
    label: str,
    *,
    registered_contract: bool,
) -> tuple[list[str], dict[str, list[str]]]:
    """Validate one current or pre-registered action against an exact spec."""

    errors: list[str] = []
    scalar_spec = spec["scalars"]
    sequence_spec = spec["sequences"]
    assert isinstance(scalar_spec, dict)
    assert isinstance(sequence_spec, dict)
    expected_keys = set(scalar_spec) | set(sequence_spec)
    if registered_contract:
        expected_keys |= {"transition", "locks"}
    dotted = ".".join(path)
    if set(map(str, action)) != expected_keys:
        errors.append(
            f"{label}: {dotted} must contain exactly the frozen action fields"
        )
    for field, expected in scalar_spec.items():
        if not _exact_plan_scalar(action.get(field), expected):
            errors.append(f"{label}: {dotted}.{field} must equal {expected}")

    resolved: dict[str, list[str]] = {}
    for field, expected_items in sequence_spec.items():
        expected = list(expected_items) if isinstance(expected_items, tuple) else []
        items = _manifest_nested_sequence(
            manifest,
            (*path, str(field)),
            manifest_text,
        )
        resolved[str(field)] = items or []
        if items != expected:
            errors.append(
                f"{label}: {dotted}.{field} must be the exact frozen YAML block sequence"
            )
        if items is not None and len(items) != len(set(items)):
            errors.append(f"{label}: {dotted}.{field} must not contain duplicates")

    for field in ("allowed_change_paths", "forbidden_change_paths"):
        for value in resolved.get(field, []):
            if not _plan_path_is_safe(value):
                errors.append(f"{label}: {dotted}.{field} contains an unsafe path: {value}")
    if set(resolved.get("allowed_change_paths", [])).intersection(
        resolved.get("forbidden_change_paths", [])
    ):
        errors.append(
            f"{label}: {dotted} allowed_change_paths and forbidden_change_paths must not overlap"
        )

    if registered_contract:
        for nested_field in ("transition", "locks"):
            actual = action.get(nested_field)
            expected = spec[nested_field]
            if not isinstance(actual, dict) or not isinstance(expected, dict):
                errors.append(f"{label}: {dotted}.{nested_field} must be a mapping")
                continue
            if set(map(str, actual)) != set(expected):
                errors.append(
                    f"{label}: {dotted}.{nested_field} must contain exactly the frozen keys"
                )
            for field, expected_value in expected.items():
                if not _exact_plan_scalar(actual.get(field), expected_value):
                    errors.append(
                        f"{label}: {dotted}.{nested_field}.{field} must equal {expected_value}"
                    )
    return errors, resolved


def _validate_iter010_transition_result(
    result: Document | None,
    expected: dict[str, object],
    label: str,
    evidence_text: str | None = None,
    *,
    configured_profiles: dict[str, dict[str, object]] | None = None,
    configured_identities: Iterable[str] = (),
    fallback_plugin_ref: str | None = None,
    fallback_plugin: dict[str, object] | None = None,
) -> list[str]:
    """Require the exact predecessor Result that authorizes an action move."""

    result_id = str(expected["id"])
    if result is None:
        return [
            f"{label}: current action materialization requires exact predecessor Result {result_id}"
        ]
    errors: list[str] = []
    if _path_label(result.path) != expected["path"]:
        errors.append(
            f"{label}: predecessor Result {result_id} must be at {expected['path']}"
        )
    action_ref = expected["action_ref"]
    expected_verifier = (
        ITER010_PLAN_RECOVERY_VERIFIER
        if action_ref == ITER010_PLAN_RECOVERY_ACTION_ID
        else ITER010_PLAN_EVIDENCE_VERIFIER
    )
    for field, expected_value in (
        ("id", expected["id"]),
        ("kind", "iteration-result"),
        ("status", "sealed"),
        ("authority", "evidence"),
        ("iteration", "ITER-010"),
        ("plan_revision_ref", ITER010_PLAN_REVISION_REF),
        ("action_ref", expected["action_ref"]),
        ("verification_case_id", expected["verification_case_id"]),
        ("plan_gate_verdict", expected["plan_gate_verdict"]),
        ("evidence_schema", ITER010_PLAN_EVIDENCE_SCHEMA),
        ("evidence_verifier", expected_verifier),
        ("evidence_artifact_path", expected["evidence_path"]),
    ):
        if result.metadata.get(field) != expected_value:
            errors.append(
                f"{label}: predecessor Result {result_id} {field} must equal {expected_value}"
            )
    if result.metadata.get("plan_gate_verdict") not in {"PASS", "FAIL", "INVALID"}:
        errors.append(
            f"{label}: predecessor Result {result_id} plan_gate_verdict must be PASS, FAIL, or INVALID"
        )
    for field in (
        "evidence_artifact_digest",
        "execution_input_digest",
        "runner_identity_digest",
        "runner_receipt_digest",
        "verification_report_digest",
        "subject_digest",
    ):
        value = result.metadata.get(field)
        if not isinstance(value, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None:
            errors.append(
                f"{label}: predecessor Result {result_id} {field} must be an exact sha256 digest"
            )
    call_count = result.metadata.get("external_model_call_count")
    if not isinstance(call_count, str) or re.fullmatch(r"0|[1-9][0-9]*", call_count) is None:
        errors.append(
            f"{label}: predecessor Result {result_id} external_model_call_count must be a non-negative integer"
        )

    if evidence_text is None:
        evidence_path = REPOSITORY / str(expected["evidence_path"])
        if evidence_path.is_file():
            try:
                evidence_text = evidence_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                errors.append(
                    f"{label}: cannot read predecessor Result evidence {expected['evidence_path']}: {error}"
                )
    if evidence_text is None:
        errors.append(
            f"{label}: predecessor Result {result_id} requires evidence artifact {expected['evidence_path']}"
        )
        return errors
    actual_digest = "sha256:" + hashlib.sha256(evidence_text.encode("utf-8")).hexdigest()
    if result.metadata.get("evidence_artifact_digest") != actual_digest:
        errors.append(
            f"{label}: predecessor Result {result_id} evidence_artifact_digest must match exact artifact bytes"
        )
    try:
        artifact = json.loads(evidence_text)
    except json.JSONDecodeError:
        errors.append(
            f"{label}: predecessor Result {result_id} evidence artifact must be valid JSON"
        )
        return errors
    if not isinstance(artifact, dict):
        errors.append(
            f"{label}: predecessor Result {result_id} evidence artifact root must be an object"
        )
        return errors
    for field, expected_value in (
        ("schema", ITER010_PLAN_EVIDENCE_SCHEMA),
        ("result_id", expected["id"]),
        ("plan_revision_ref", ITER010_PLAN_REVISION_REF),
        ("action_ref", expected["action_ref"]),
        ("verification_case_id", expected["verification_case_id"]),
        ("plan_gate_verdict", expected["plan_gate_verdict"]),
        ("evidence_verifier", ITER010_PLAN_EVIDENCE_VERIFIER),
        ("evidence_artifact_path", expected["evidence_path"]),
    ):
        if artifact.get(field) != expected_value:
            errors.append(
                f"{label}: predecessor Result {result_id} evidence {field} must equal {expected_value}"
            )
    action_evidence = artifact.get("action_evidence")
    if not isinstance(action_evidence, dict):
        errors.append(
            f"{label}: predecessor Result {result_id} evidence action_evidence must be an object"
        )
        action_evidence = {}
    if action_ref in {
        ITER010_CURRENT_ACTION_ID,
        ITER010_PREFERRED_QUALITY_ACTION_ID,
        ITER010_FALLBACK_REFREEZE_ACTION_ID,
        ITER010_FALLBACK_QUALITY_ACTION_ID,
    }:
        errors.extend(
            _validate_provider_neutral_root_input_set(
                action_evidence.get("provider_neutral_root_input_set"),
                f"{label}: predecessor Result {result_id}",
            )
        )
    errors.extend(
        _configured_identity_errors(
            action_evidence.get("provider_neutral_root_input_set"),
            configured_identities,
            f"{label}: predecessor Result {result_id} provider_neutral_root_input_set",
        )
    )
    root_keys = {
        "provider_neutral_root_input_set",
        "provider_neutral_root_input_set_digest",
    }
    quality_keys = root_keys | {
        "route_role",
        "execution_profile_ref",
        "execution_profile",
        "execution_profile_digest",
        "admission_receipt",
        "admission_receipt_digest",
        "terminal_receipt",
        "terminal_receipt_digest",
        "terminal_classification",
        "mixed_execution_profile_batch",
    }
    if action_ref == ITER010_PLAN_RECOVERY_ACTION_ID:
        expected_recovery_evidence = {
            "schema": "ITER010_USER_PLAN_RECOVERY_EVIDENCE@1",
            "target_plan_revision_ref": "ITER-010-PDR-010",
            "authorization_refs": [
                "local-user-message-utf8:sha256:5ced06d2604020248c5baf69421ccbb4e5c047288b6db5b2202675c558c38cf6",
                ITER010_PLAN_RECOVERY_AUTHORIZATION_REF,
            ],
            "change_boundary": {
                "plan_governance_change_authorized": True,
                "product_code_change_authorized": False,
                "external_execution_authorized": False,
            },
        }
        if action_evidence != expected_recovery_evidence:
            errors.append(
                f"{label}: PlanRecovery action_evidence must exactly bind the authorized governance-only recovery"
            )
    elif action_ref == ITER010_CURRENT_ACTION_ID:
        if set(map(str, action_evidence)) != root_keys:
            errors.append(
                f"{label}: DirectionFreeze action_evidence must contain exactly the provider-neutral root input keys"
            )
        errors.extend(
            _validate_plan_bound_object(
                action_evidence,
                "provider_neutral_root_input_set",
                "provider_neutral_root_input_set_digest",
                f"{label}: DirectionFreeze evidence",
            )
        )
    elif action_ref in {
        ITER010_PREFERRED_QUALITY_ACTION_ID,
        ITER010_FALLBACK_QUALITY_ACTION_ID,
    }:
        expected_keys = set(quality_keys)
        expected_role = "preferred"
        evidence_name = "PreferredRouteQuality"
        if action_ref == ITER010_FALLBACK_QUALITY_ACTION_ID:
            expected_role = "fallback"
            evidence_name = "FallbackRouteQuality"
            expected_keys |= {
                "fallback_refreeze_predecessor_ref",
                "fallback_refreeze_predecessor_seal_digest",
                "admission_policy_plugin_ref",
                "admission_policy_plugin",
                "admission_policy_plugin_digest",
            }
        if set(map(str, action_evidence)) != expected_keys:
            errors.append(
                f"{label}: {evidence_name} action_evidence must contain exactly the model-transparent keys"
            )
        if action_evidence.get("route_role") != expected_role:
            errors.append(
                f"{label}: {evidence_name} route_role must equal {expected_role}"
            )
        if action_evidence.get("mixed_execution_profile_batch") is not False:
            errors.append(
                f"{label}: {evidence_name} mixed_execution_profile_batch must equal false"
            )
        if action_evidence.get("terminal_classification") not in {
            "AVAILABLE",
            "TERMINAL_UNAVAILABLE",
            "OTHER_INVALID",
        }:
            errors.append(
                f"{label}: {evidence_name} terminal_classification must be a generic terminal class"
            )
        for object_field, digest_field in (
            (
                "provider_neutral_root_input_set",
                "provider_neutral_root_input_set_digest",
            ),
            ("execution_profile", "execution_profile_digest"),
            ("admission_receipt", "admission_receipt_digest"),
            ("terminal_receipt", "terminal_receipt_digest"),
        ):
            errors.extend(
                _validate_plan_bound_object(
                    action_evidence,
                    object_field,
                    digest_field,
                    f"{label}: {evidence_name} evidence",
                )
            )
        for ref_field in ("execution_profile_ref",):
            if not isinstance(action_evidence.get(ref_field), str) or not str(
                action_evidence.get(ref_field)
            ).strip():
                errors.append(
                    f"{label}: {evidence_name} {ref_field} must be a non-empty reference"
                )
        expected_profile = (configured_profiles or {}).get(expected_role)
        if isinstance(expected_profile, dict):
            if action_evidence.get("execution_profile_ref") != expected_profile.get(
                "execution_profile_ref"
            ):
                errors.append(
                    f"{label}: {evidence_name} execution_profile_ref must equal the trusted {expected_role} execution profile ref"
                )
            if action_evidence.get("execution_profile") != expected_profile:
                errors.append(
                    f"{label}: {evidence_name} execution_profile must exactly equal the trusted {expected_role} execution profile configuration"
                )
        if action_ref == ITER010_FALLBACK_QUALITY_ACTION_ID:
            if (
                action_evidence.get("fallback_refreeze_predecessor_ref")
                != ITER010_FALLBACK_REFREEZE_RESULT_REF
            ):
                errors.append(
                    f"{label}: FallbackRouteQuality predecessor ref must equal {ITER010_FALLBACK_REFREEZE_RESULT_REF}"
                )
            seal = action_evidence.get("fallback_refreeze_predecessor_seal_digest")
            if not isinstance(seal, str) or re.fullmatch(
                r"sha256:[0-9a-f]{64}", seal
            ) is None:
                errors.append(
                    f"{label}: FallbackRouteQuality predecessor seal must be an exact sha256 digest"
                )
            errors.extend(
                _validate_plan_bound_object(
                    action_evidence,
                    "admission_policy_plugin",
                    "admission_policy_plugin_digest",
                    f"{label}: FallbackRouteQuality evidence",
                )
            )
            if action_evidence.get("admission_policy_plugin_ref") != fallback_plugin_ref:
                errors.append(
                    f"{label}: FallbackRouteQuality admission_policy_plugin_ref must equal provider_route_policy.fallback_admission_policy_plugin_ref"
                )
            if isinstance(fallback_plugin, dict) and action_evidence.get(
                "admission_policy_plugin"
            ) != fallback_plugin:
                errors.append(
                    f"{label}: FallbackRouteQuality admission_policy_plugin must exactly equal the trusted admission plugin configuration"
                )
    elif action_ref == ITER010_FALLBACK_REFREEZE_ACTION_ID:
        expected_action_keys = root_keys | {
            "preferred_invalid_predecessor_ref",
            "preferred_invalid_predecessor_seal_digest",
            "fallback_execution_profile_ref",
            "fallback_execution_profile",
            "fallback_execution_profile_digest",
            "fallback_admission_policy_plugin_ref",
            "fallback_admission_policy_plugin",
            "fallback_admission_policy_plugin_digest",
            "preferred_terminal_classification",
            "mixed_execution_profile_batch",
            "provider_dispatch_count",
            "new_human_authority_requested",
        }
        if set(map(str, action_evidence)) != expected_action_keys:
            errors.append(
                f"{label}: FallbackRouteRefreeze action_evidence must contain exactly the model-transparent keys"
            )
        for field, expected_value in (
            (
                "preferred_invalid_predecessor_ref",
                ITER010_PREFERRED_QUALITY_RESULT_REF,
            ),
            ("mixed_execution_profile_batch", False),
            ("provider_dispatch_count", 0),
            ("new_human_authority_requested", False),
        ):
            if not _exact_plan_scalar(action_evidence.get(field), expected_value):
                errors.append(
                    f"{label}: FallbackRouteRefreeze {field} must equal {expected_value}"
                )
        terminal = action_evidence.get("preferred_terminal_classification")
        if terminal not in {"TERMINAL_UNAVAILABLE", "OTHER_INVALID"}:
            errors.append(
                f"{label}: FallbackRouteRefreeze preferred_terminal_classification must identify the preferred route invalid class"
            )
        if (
            artifact.get("plan_gate_verdict") == "PASS"
            and terminal != "TERMINAL_UNAVAILABLE"
        ):
            errors.append(
                f"{label}: FallbackRouteRefreeze PASS requires TERMINAL_UNAVAILABLE"
            )
        seal = action_evidence.get("preferred_invalid_predecessor_seal_digest")
        if not isinstance(seal, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", seal
        ) is None:
            errors.append(
                f"{label}: FallbackRouteRefreeze predecessor seal must be an exact sha256 digest"
            )
        for object_field, digest_field in (
            (
                "provider_neutral_root_input_set",
                "provider_neutral_root_input_set_digest",
            ),
            ("fallback_execution_profile", "fallback_execution_profile_digest"),
            (
                "fallback_admission_policy_plugin",
                "fallback_admission_policy_plugin_digest",
            ),
        ):
            errors.extend(
                _validate_plan_bound_object(
                    action_evidence,
                    object_field,
                    digest_field,
                    f"{label}: FallbackRouteRefreeze evidence",
                )
            )
        expected_profile = (configured_profiles or {}).get("fallback")
        if isinstance(expected_profile, dict):
            if action_evidence.get(
                "fallback_execution_profile_ref"
            ) != expected_profile.get("execution_profile_ref"):
                errors.append(
                    f"{label}: FallbackRouteRefreeze fallback_execution_profile_ref must equal the trusted fallback execution profile ref"
                )
            if action_evidence.get("fallback_execution_profile") != expected_profile:
                errors.append(
                    f"{label}: FallbackRouteRefreeze fallback_execution_profile must exactly equal the trusted fallback execution profile configuration"
                )
        if (
            action_evidence.get("fallback_admission_policy_plugin_ref")
            != fallback_plugin_ref
        ):
            errors.append(
                f"{label}: FallbackRouteRefreeze fallback_admission_policy_plugin_ref must equal provider_route_policy.fallback_admission_policy_plugin_ref"
            )
        if isinstance(fallback_plugin, dict) and action_evidence.get(
            "fallback_admission_policy_plugin"
        ) != fallback_plugin:
            errors.append(
                f"{label}: FallbackRouteRefreeze fallback_admission_policy_plugin must exactly equal the trusted admission plugin configuration"
            )
    elif action_evidence:
        errors.append(f"{label}: this plan action requires empty action_evidence")
    return errors


def _iter010_required_result_options(
    required: object,
) -> tuple[dict[str, object], ...]:
    """Normalize a single predecessor or an explicit mutually exclusive set."""

    if isinstance(required, dict):
        return (required,)
    if isinstance(required, tuple) and required and all(
        isinstance(item, dict) for item in required
    ):
        return required
    return ()


def _load_iter010_required_transition_results(
    manifest: dict[str, object], manifest_path: Path, label: str
) -> tuple[dict[str, Document], dict[str, str], list[str]]:
    """Load only the predecessor Result required by the current action."""

    authoritative_manifest_path = (
        REPOSITORY
        / "docs/project/iterations/iteration-010/manifest.yaml"
    )
    if manifest_path.resolve() != authoritative_manifest_path.resolve():
        return {}, {}, []
    control = manifest.get("plan_execution_control")
    action = control.get("current_action") if isinstance(control, dict) else None
    action_id = action.get("id") if isinstance(action, dict) else None
    spec = iter010_plan_action_specs().get(str(action_id))
    required = spec.get("required_result") if isinstance(spec, dict) else None
    options = list(_iter010_required_result_options(required))
    specs = iter010_plan_action_specs()
    for quality_action_id in (
        ITER010_PREFERRED_QUALITY_ACTION_ID,
        ITER010_FALLBACK_QUALITY_ACTION_ID,
    ):
        quality_spec = specs[quality_action_id]
        scalars = quality_spec["scalars"]
        assert isinstance(scalars, dict)
        if not any(option.get("id") == scalars["result_ref"] for option in options):
            options.append(
                {
                    "id": scalars["result_ref"],
                    "path": scalars["result_path"],
                    "evidence_path": scalars["evidence_path"],
                }
            )
    results: dict[str, Document] = {}
    evidence: dict[str, str] = {}
    errors: list[str] = []
    for option in options:
        result_id = str(option["id"])
        result_path = REPOSITORY / str(option["path"])
        if not result_path.is_file():
            continue
        try:
            result, parse_errors = parse_document(result_path)
        except (OSError, UnicodeError) as error:
            errors.append(
                f"{label}: cannot read predecessor Result {result_id}: {error}"
            )
            continue
        errors.extend(parse_errors)
        if result is None:
            continue
        results[result_id] = result
        evidence_path = REPOSITORY / str(option["evidence_path"])
        if evidence_path.is_file():
            try:
                evidence[result_id] = evidence_path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as error:
                errors.append(
                    f"{label}: cannot read predecessor Result evidence {result_id}: {error}"
                )
    return results, evidence, errors


def _iter010_validated_receipt_outcomes(
    evidence_text: str | None,
    predecessor_spec: dict[str, object] | None,
    expected_verdict: str,
    label: str,
) -> tuple[dict[str, str], list[str]]:
    """Validate exact produced-Case coverage and deterministic verdict aggregation."""

    if evidence_text is None or predecessor_spec is None:
        return {}, []
    try:
        artifact = json.loads(evidence_text)
    except json.JSONDecodeError:
        return {}, []
    if not isinstance(artifact, dict):
        return {}, []
    raw_outcomes = artifact.get("case_outcomes")
    if not isinstance(raw_outcomes, list) or not raw_outcomes:
        return {}, [f"{label}: transition evidence case_outcomes must be non-empty"]
    outcomes: dict[str, str] = {}
    errors: list[str] = []
    for outcome in raw_outcomes:
        if not isinstance(outcome, dict):
            errors.append(f"{label}: transition evidence case_outcome must be a mapping")
            continue
        case_id = outcome.get("case_id")
        verdict = outcome.get("verdict")
        if not isinstance(case_id, str) or verdict not in {"PASS", "FAIL", "INVALID"}:
            errors.append(f"{label}: transition evidence case_outcome identity/verdict is invalid")
            continue
        if case_id in outcomes:
            errors.append(f"{label}: transition evidence repeats Case {case_id}")
        outcomes[case_id] = str(verdict)
    sequences = predecessor_spec.get("sequences")
    produced = (
        sequences.get("produced_case_ids", ())
        if isinstance(sequences, dict)
        else ()
    )
    if set(outcomes) != set(produced):
        errors.append(
            f"{label}: transition evidence must exactly cover predecessor produced_case_ids"
        )
    aggregate = (
        "INVALID"
        if "INVALID" in outcomes.values()
        else "FAIL"
        if "FAIL" in outcomes.values()
        else "PASS"
        if outcomes
        else None
    )
    if aggregate != expected_verdict:
        errors.append(
            f"{label}: transition evidence verdict must use INVALID > FAIL > PASS aggregation"
        )
    return outcomes, errors


def validate_iter010_plan_execution_snapshot(
    manifest: dict[str, object],
    label: str,
    *,
    manifest_text: str | None = None,
    current: Document | None = None,
    verification: Document | None = None,
    transition_results: dict[str, Document] | None = None,
    transition_evidence_artifacts: dict[str, str] | None = None,
    require_external_bindings: bool = False,
) -> list[str]:
    """Fail closed when ITER-010 drifts from the PDR-009 executable plan.

    This is deliberately a state-machine snapshot, not prose interpretation.
    It binds the current action to a pre-registered contract, its exact change
    envelope and locks, the Result needed for each transition, the four-arm
    direction gate, and the current pointer.
    """

    errors: list[str] = []
    errors.extend(validate_model_transparent_plan_routing(manifest, label))
    configured_profiles, configured_identities, fallback_plugin, _ = (
        _configured_execution_profiles(manifest, label)
    )
    fallback_profile = configured_profiles.get("fallback")
    fallback_plugin_ref = (
        fallback_profile.get("admission_policy_plugin_ref")
        if isinstance(fallback_profile, dict)
        else None
    )
    if manifest.get("schema_version") != 2:
        errors.append(f"{label}: active ITER-010 schema_version must equal 2")

    control = manifest.get("plan_execution_control")
    if not isinstance(control, dict):
        return errors + [f"{label}: plan_execution_control must be a mapping"]
    expected_control_keys = {
        "schema",
        "plan_revision_ref",
        "enforcement_mode",
        "authorization_refs",
        "current_action",
        "transition",
        "locks",
        "next_action_contracts",
    }
    if set(map(str, control)) != expected_control_keys:
        errors.append(
            f"{label}: plan_execution_control must contain exactly the frozen control keys"
        )
    for field, expected in (
        ("schema", ITER010_PLAN_EXECUTION_CONTROL_SCHEMA),
        ("plan_revision_ref", ITER010_PLAN_REVISION_REF),
        ("enforcement_mode", "fail-closed"),
    ):
        if control.get(field) != expected:
            errors.append(
                f"{label}: plan_execution_control.{field} must equal {expected}"
            )
    authorization_refs = _manifest_nested_sequence(
        manifest,
        ("plan_execution_control", "authorization_refs"),
        manifest_text,
    )
    if authorization_refs != list(ITER010_PLAN_AUTHORIZATION_REFS):
        errors.append(
            f"{label}: plan_execution_control.authorization_refs must be the exact frozen YAML block sequence"
        )

    specs = iter010_plan_action_specs()
    action = control.get("current_action")
    if not isinstance(action, dict):
        errors.append(
            f"{label}: plan_execution_control.current_action must be a mapping"
        )
        action = {}
    action_id = action.get("id")
    current_spec = specs.get(str(action_id))
    action_sequences: dict[str, list[str]] = {}
    if current_spec is None:
        errors.append(
            f"{label}: current action {action_id} is not the initial freeze or a pre-registered action contract"
        )
    else:
        action_errors, action_sequences = _validate_iter010_action_mapping(
            manifest,
            manifest_text,
            action,
            current_spec,
            ("plan_execution_control", "current_action"),
            label,
            registered_contract=False,
        )
        errors.extend(action_errors)

    recovery = manifest.get("user_plan_recovery")
    if action_id == ITER010_PLAN_RECOVERY_ACTION_ID:
        expected_recovery = {
            "schema": "USER_DIRECTED_PLAN_RECOVERY@1",
            "status": "authorized-recovery-entry-installed",
            "authorization_ref": ITER010_PLAN_RECOVERY_AUTHORIZATION_REF,
            "authorization_reusable": False,
            "trusted_base_commit": ITER010_PLAN_RECOVERY_TRUSTED_COMMIT,
            "trusted_base_tree": ITER010_PLAN_RECOVERY_TRUSTED_TREE,
            "interrupted_plan_revision_ref": ITER010_PLAN_REVISION_REF,
            "interrupted_action_id": ITER010_CURRENT_ACTION_ID,
            "recovery_action_id": ITER010_PLAN_RECOVERY_ACTION_ID,
            "recovery_case_id": ITER010_PLAN_RECOVERY_CASE_ID,
            "target_plan_revision_ref": "ITER-010-PDR-010",
            "scope": "governance-only-no-product-no-external-execution",
            "one_time_recovery": True,
            "product_code_changes_allowed": False,
            "external_execution_allowed": False,
        }
        if not isinstance(recovery, dict) or recovery != expected_recovery:
            errors.append(
                f"{label}: user_plan_recovery must exactly bind the one-time trusted recovery entry"
            )
    elif recovery is not None:
        errors.append(
            f"{label}: user_plan_recovery may be active only while its recovery action is current"
        )

    next_contracts = control.get("next_action_contracts")
    registered_specs = {
        str(spec["registry_key"]): spec
        for spec in specs.values()
        if spec["registry_key"] is not None
    }
    if not isinstance(next_contracts, dict):
        errors.append(
            f"{label}: plan_execution_control.next_action_contracts must be a mapping"
        )
        next_contracts = {}
    if set(map(str, next_contracts)) != set(registered_specs):
        errors.append(
            f"{label}: plan_execution_control.next_action_contracts must contain exactly the pre-registered action keys"
        )
    for registry_key, spec in registered_specs.items():
        contract = next_contracts.get(registry_key)
        if not isinstance(contract, dict):
            errors.append(
                f"{label}: plan_execution_control.next_action_contracts.{registry_key} must be a mapping"
            )
            continue
        contract_errors, _ = _validate_iter010_action_mapping(
            manifest,
            manifest_text,
            contract,
            spec,
            ("plan_execution_control", "next_action_contracts", registry_key),
            label,
            registered_contract=True,
        )
        errors.extend(contract_errors)

    transition = control.get("transition")
    if not isinstance(transition, dict):
        errors.append(f"{label}: plan_execution_control.transition must be a mapping")
    elif current_spec is not None:
        expected_transition = current_spec["transition"]
        assert isinstance(expected_transition, dict)
        if set(map(str, transition)) != set(expected_transition):
            errors.append(
                f"{label}: plan_execution_control.transition must contain exactly the frozen keys"
            )
        for field, expected in expected_transition.items():
            if not _exact_plan_scalar(transition.get(field), expected):
                errors.append(
                    f"{label}: plan_execution_control.transition.{field} must equal {expected}"
                )

    locks = control.get("locks")
    if not isinstance(locks, dict):
        errors.append(f"{label}: plan_execution_control.locks must be a mapping")
    elif current_spec is not None:
        expected_locks = current_spec["locks"]
        assert isinstance(expected_locks, dict)
        if set(map(str, locks)) != set(expected_locks):
            errors.append(
                f"{label}: plan_execution_control.locks must contain exactly the frozen lock keys"
            )
        for field, expected in expected_locks.items():
            if not _exact_plan_scalar(locks.get(field), expected):
                errors.append(
                    f"{label}: plan_execution_control.locks.{field} must equal {expected}"
                )

    available_results = transition_results or {}
    quality_pass_result_ids = [
        result_id
        for result_id in (
            ITER010_PREFERRED_QUALITY_RESULT_REF,
            ITER010_FALLBACK_QUALITY_RESULT_REF,
        )
        if (
            result_id in available_results
            and available_results[result_id].metadata.get("plan_gate_verdict") == "PASS"
        )
    ]
    if len(quality_pass_result_ids) > 1:
        errors.append(
            f"{label}: {ITER010_DIRECTION_QUALITY_CASE_ID} may have at most one PASS "
            "Result across the preferred and fallback quality actions"
        )

    validated_receipt_pass_cases: set[str] = set()
    if current_spec is not None:
        required_options = _iter010_required_result_options(
            current_spec["required_result"]
        )
        selected_required: dict[str, object] | None = None
        if len(required_options) == 1:
            selected_required = required_options[0]
        elif required_options:
            matching_options = [
                option
                for option in required_options
                if (
                    (result := available_results.get(str(option["id"])))
                    is not None
                    and result.metadata.get("plan_gate_verdict")
                    == option["plan_gate_verdict"]
                )
            ]
            if len(matching_options) != 1:
                errors.append(
                    f"{label}: current action requires exactly one qualifying "
                    "mutually exclusive predecessor Result"
                )
                present_options = [
                    option
                    for option in required_options
                    if str(option["id"]) in available_results
                ]
                if len(present_options) == 1:
                    selected_required = present_options[0]
            else:
                selected_required = matching_options[0]

        if selected_required is not None:
            result_id = str(selected_required["id"])
            result = available_results.get(result_id)
            evidence_text = (transition_evidence_artifacts or {}).get(result_id)
            if evidence_text is None:
                evidence_path = REPOSITORY / str(
                    selected_required["evidence_path"]
                )
                if evidence_path.is_file():
                    try:
                        evidence_text = evidence_path.read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        evidence_text = None
            result_errors = _validate_iter010_transition_result(
                result,
                selected_required,
                label,
                evidence_text,
                configured_profiles=configured_profiles,
                configured_identities=configured_identities,
                fallback_plugin_ref=(
                    fallback_plugin_ref
                    if isinstance(fallback_plugin_ref, str)
                    else None
                ),
                fallback_plugin=fallback_plugin,
            )
            errors.extend(result_errors)
            predecessor_spec = specs.get(str(selected_required["action_ref"]))
            outcomes, outcome_errors = _iter010_validated_receipt_outcomes(
                evidence_text,
                predecessor_spec,
                str(selected_required["plan_gate_verdict"]),
                label,
            )
            errors.extend(outcome_errors)
            if not result_errors and not outcome_errors:
                validated_receipt_pass_cases.update(
                    case_id
                    for case_id, verdict in outcomes.items()
                    if verdict == "PASS"
                )

    gate = manifest.get("direction_quality_gate")
    if not isinstance(gate, dict):
        errors.append(f"{label}: direction_quality_gate must be a mapping")
        gate = {}
    expected_gate_status = (
        current_spec["gate_status"]
        if current_spec is not None
        else "locked-until-direction-freeze-pass"
    )
    gate_exact_values = (
        ("schema", ITER010_DIRECTION_QUALITY_GATE_SCHEMA),
        ("case_id", ITER010_DIRECTION_QUALITY_CASE_ID),
        ("owner_slice_ref", "ITER-010-SLICE-001"),
        ("status", expected_gate_status),
        ("execution_order", ITER010_DIRECTION_MICRO_CHECKPOINT_ORDER),
        ("question_set_rule", ITER010_DIRECTION_QUESTION_SET_RULE),
        ("source_truth_owner", "independent-exact-source-ledger-not-any-model-answer"),
        ("direct_evidence_arm_is_oracle", False),
        ("current_codex_role", STRICT_CODEX_BASELINE_ROLE),
        ("current_codex_is_oracle_or_reviewer", False),
        ("first_three_arms_same_provider_model_configuration", True),
        (
            "source_only_and_world_model_arms_same_agent_prompt_tools_budget_cache_and_reviewer",
            True,
        ),
        ("outputs_sealed_before_cross_arm_disclosure", True),
        ("blind_randomized_independent_evaluation", True),
        ("absolute_quality_pass_required", True),
        ("absolute_quality_rule", ITER010_DIRECTION_ABSOLUTE_QUALITY_RULE),
        ("world_model_arm_must_not_lose_to_direct_evidence", True),
        ("world_model_arm_must_not_lose_to_source_only", True),
        ("world_model_arm_must_not_lose_to_current_codex", True),
        ("current_codex_overall_quality_margin_rule", "strictly-positive"),
        ("non_locator_world_model_contribution_required", True),
        ("all_tie_outcome", "FAIL"),
        ("cost_or_latency_can_compensate_quality", False),
        ("product_code_change_before_verdict_allowed", False),
        (
            "preferred_route_execution_profile_ref",
            "provider_route_policy.preferred_execution_profile_ref",
        ),
        (
            "fallback_route_execution_profile_ref",
            "provider_route_policy.fallback_execution_profile_ref",
        ),
        ("preferred_quality_action_id", ITER010_PREFERRED_QUALITY_ACTION_ID),
        ("preferred_quality_result_ref", ITER010_PREFERRED_QUALITY_RESULT_REF),
        ("mixed_provider_batch_allowed", False),
        ("fallback_refreeze_action_id", ITER010_FALLBACK_REFREEZE_ACTION_ID),
        ("fallback_refreeze_case_id", ITER010_FALLBACK_REFREEZE_CASE_ID),
        ("fallback_refreeze_requires_new_human_authority", False),
        ("fallback_refreeze_provider_dispatch_allowed", False),
        (
            "fallback_refreeze_action_evidence_required",
            "preferred-invalid-predecessor-seal,provider-neutral-root-input-set,"
            "fallback-execution-profile-ref-and-digest,"
            "fallback-admission-policy-plugin-ref-and-digest,no-mixed-batch,"
            "zero-provider-dispatch,no-new-human-authority",
        ),
        ("fallback_quality_action_id", ITER010_FALLBACK_QUALITY_ACTION_ID),
        ("fallback_quality_result_ref", ITER010_FALLBACK_QUALITY_RESULT_REF),
        ("fallback_allowed_only_after_refreeze_pass", True),
        (
            "fallback_admission_prerequisite_case_id",
            "V-FALLBACK-ROUTE-ADMISSION-001",
        ),
        (
            "fallback_quality_action_evidence_required",
            "fallback-refreeze-predecessor-seal,provider-neutral-root-input-set,"
            "execution-profile-ref-and-digest,admission-and-terminal-receipts,"
            "no-mixed-batch",
        ),
        ("quality_case_pass_result_cardinality", "at-most-one"),
        (
            "preferred_terminal_unavailable_action",
            "invalidate-preferred-batch-and-enter-pre-registered-fallback-refreeze",
        ),
        (
            "preferred_other_invalid_action",
            "fallback-refreeze-fails-back-to-preferred-quality",
        ),
        ("fallback_invalid_action", "fail-closed-at-fallback-quality"),
        ("dirty_v7_status", "quarantined-not-input"),
    )
    expected_gate_keys = {
        field for field, _ in gate_exact_values
    } | {"arms", "question_count", "target_product_commit", "target_product_tree"}
    if set(map(str, gate)) != expected_gate_keys:
        errors.append(
            f"{label}: direction_quality_gate must contain exactly the frozen four-arm Gate fields"
        )
    for field, expected in gate_exact_values:
        if gate.get(field) != expected:
            errors.append(
                f"{label}: direction_quality_gate.{field} must equal {expected}"
            )
    for field in ("target_product_commit", "target_product_tree"):
        value = gate.get(field)
        if not isinstance(value, str) or HEX_COMMIT_RE.fullmatch(value) is None:
            errors.append(
                f"{label}: direction_quality_gate.{field} must be an exact 40-character lowercase Git object ID"
            )
    question_count = gate.get("question_count")
    if (
        isinstance(question_count, bool)
        or not isinstance(question_count, int)
        or question_count < 3
    ):
        errors.append(
            f"{label}: direction_quality_gate.question_count must be at least 3"
        )
    arms = _manifest_nested_sequence(
        manifest,
        ("direction_quality_gate", "arms"),
        manifest_text,
    )
    if arms != list(ITER010_DIRECTION_QUALITY_ARMS):
        errors.append(
            f"{label}: direction_quality_gate.arms must equal the exact four-arm order"
        )

    public_authority = manifest.get("public_oss_evaluation_standing_authority")
    if not isinstance(public_authority, dict):
        errors.append(
            f"{label}: PDR-009 requires public_oss_evaluation_standing_authority"
        )
    else:
        expected_entry_action = (
            ITER010_PLAN_RECOVERY_ACTION_ID
            if action_id == ITER010_PLAN_RECOVERY_ACTION_ID
            else ITER010_CURRENT_ACTION_ID
        )
        expected_entry_case = (
            ITER010_PLAN_RECOVERY_CASE_ID
            if action_id == ITER010_PLAN_RECOVERY_ACTION_ID
            else ITER010_CURRENT_ACTION_CASE_ID
        )
        for field, expected in (
            ("owner_decision_ref", "ITER-010-PDR-008"),
            ("current_plan_amendment_ref", ITER010_PLAN_REVISION_REF),
            ("verification_case_id", ITER010_PUBLIC_AUTHORITY_CASE_ID),
            ("verification_status", "NOT-RUN"),
            ("independent_action_entry_allowed", False),
            ("next_execution_entry_action_id", expected_entry_action),
            ("next_execution_entry_case_id", expected_entry_case),
        ):
            if not _exact_plan_scalar(public_authority.get(field), expected):
                errors.append(
                    f"{label}: public_oss_evaluation_standing_authority.{field} "
                    f"must equal {expected}"
                )

    alignment = manifest.get("product_goal_alignment")
    blocking_case_ids = (
        _execution_manifest_sequence(
            manifest=manifest,
            manifest_text=manifest_text,
            section="product_goal_alignment",
            field="blocking_case_ids",
        )
        if isinstance(alignment, dict)
        else []
    )
    required_current_cases = {
        str(case_id)
        for spec in specs.values()
        for case_id in (
            *(
                [spec["scalars"].get("case_id")]
                if isinstance(spec.get("scalars"), dict)
                else []
            ),
            *(
                spec["sequences"].get("produced_case_ids", ())
                if isinstance(spec.get("sequences"), dict)
                else ()
            ),
        )
        if isinstance(case_id, str)
    }
    if current_spec is not None:
        scalar_spec = current_spec["scalars"]
        assert isinstance(scalar_spec, dict)
        required_current_cases.add(str(scalar_spec["case_id"]))
        if action_id not in {
            ITER010_CURRENT_ACTION_ID,
            ITER010_PLAN_RECOVERY_ACTION_ID,
        }:
            identity_digest = (
                alignment.get("mature_source_agent_identity_digest")
                if isinstance(alignment, dict)
                else None
            )
            if not isinstance(identity_digest, str) or re.fullmatch(
                r"sha256:[0-9a-f]{64}", identity_digest
            ) is None:
                errors.append(
                    f"{label}: mature_source_agent_identity_digest must be exact sha256 after the freeze action"
                )
    for case_id in sorted(required_current_cases):
        if case_id not in blocking_case_ids:
            errors.append(
                f"{label}: product_goal_alignment.blocking_case_ids must include {case_id}"
            )
        if verification is not None:
            errors.extend(validate_blocking_verification_case(verification, case_id))

    prerequisite_case_ids = action_sequences.get("prerequisite_case_ids", [])
    for case_id in prerequisite_case_ids:
        if case_id not in blocking_case_ids:
            errors.append(
                f"{label}: current action prerequisite_case_ids must reference blocking_case_ids: {case_id}"
            )
        if verification is not None:
            row = markdown_table_case_rows(verification.body, case_id)
            row_verdict = (
                blocking_case_status_verdict(row[0][6])
                if len(row) == 1 and len(row[0]) == 7
                else None
            )
            if row_verdict in {"FAIL", "INVALID"}:
                errors.append(
                    f"{verification.relative_path}: completed {case_id} must be PASS"
                )
            else:
                errors.extend(
                    validate_blocking_verification_case(
                        verification,
                        case_id,
                        require_pass=case_id not in validated_receipt_pass_cases,
                    )
                )

    alpha_binding = (
        alignment.get("alpha_agent_comparison_binding")
        if isinstance(alignment, dict)
        else None
    )
    if not isinstance(alpha_binding, dict):
        errors.append(
            f"{label}: alpha_agent_comparison_binding must retain the four-arm compatibility binding"
        )
    else:
        if alpha_binding.get("result_role") != (
            "blocking-iter010-strict-superiority-direction-gate"
        ):
            errors.append(
                f"{label}: legacy three-arm comparison cannot remain current; alpha_agent_comparison_binding.result_role must bind PDR-009"
            )
        if alpha_binding.get("case_id") != ITER010_DIRECTION_QUALITY_CASE_ID:
            errors.append(
                f"{label}: alpha_agent_comparison_binding.case_id must equal {ITER010_DIRECTION_QUALITY_CASE_ID}"
            )
        if alpha_binding.get("arms") != ",".join(ITER010_DIRECTION_QUALITY_ARMS):
            errors.append(
                f"{label}: alpha_agent_comparison_binding must use the same exact four-arm order"
            )

    if current is not None:
        expected_action_id = (
            str(action_id) if current_spec is not None else ITER010_CURRENT_ACTION_ID
        )
        expected_case_id = (
            str(action.get("case_id"))
            if current_spec is not None
            else ITER010_CURRENT_ACTION_CASE_ID
        )
        for field, expected in (
            ("plan_revision_ref", ITER010_PLAN_REVISION_REF),
            ("next_action", expected_action_id),
            ("next_action_case_id", expected_case_id),
            ("active_slice", "ITER-010-SLICE-001"),
        ):
            if current.metadata.get(field) != expected:
                errors.append(f"PROJECT-CURRENT: {field} must equal {expected}")
        if current.metadata.get("next_action") != action.get("id"):
            errors.append(
                "PROJECT-CURRENT: next_action must match plan_execution_control.current_action.id"
            )
        if current.metadata.get("next_action_case_id") != action.get("case_id"):
            errors.append(
                "PROJECT-CURRENT: next_action_case_id must match plan_execution_control.current_action.case_id"
            )
    elif require_external_bindings:
        errors.append(f"{label}: active ITER-010 plan requires PROJECT-CURRENT")
    if verification is None and require_external_bindings:
        errors.append(f"{label}: active ITER-010 plan requires Verification bindings")
    return errors


def uses_legacy_iter010_plan(manifest: dict[str, object]) -> bool:
    """Return whether the superseded PDR-009 action graph owns this snapshot.

    PDR-010 uses the repository-wide plan gate and a single long-running MVP
    experience action.  The large ITER-010-specific Freeze/Quality validator is
    retained only so historical PDR-009 snapshots remain testable; applying it
    to PDR-010 would silently restore the superseded plan.
    """

    control = manifest.get("plan_execution_control")
    return (
        isinstance(control, dict)
        and control.get("plan_revision_ref") == ITER010_PLAN_REVISION_REF
    )


def uses_lightweight_iter010_plan(manifest: dict[str, object]) -> bool:
    """Return whether the complete-experience-first PDR-010 owns this snapshot."""

    control = manifest.get("plan_execution_control")
    return (
        isinstance(control, dict)
        and control.get("plan_revision_ref")
        == ITER010_LIGHTWEIGHT_PLAN_REVISION_REF
    )


def uses_failure_handoff_iter010_plan(manifest: dict[str, object]) -> bool:
    """Return whether the truthful pre-answer failure PDR-011 owns the snapshot."""

    control = manifest.get("plan_execution_control")
    return (
        isinstance(control, dict)
        and control.get("plan_revision_ref")
        == ITER010_FAILURE_HANDOFF_PLAN_REVISION_REF
    )


def uses_post_pdr009_iter010_plan(manifest: dict[str, object]) -> bool:
    """Return whether a registered lightweight ITER-010 contract owns the snapshot."""

    return uses_lightweight_iter010_plan(
        manifest
    ) or uses_failure_handoff_iter010_plan(manifest)


def validate_iter010_lightweight_standing_authority(
    manifest: dict[str, object], label: str
) -> list[str]:
    """Freeze public-source authority and the active plan's runtime boundary."""

    if not uses_post_pdr009_iter010_plan(manifest):
        return []
    authority = manifest.get("public_oss_evaluation_standing_authority")
    if not isinstance(authority, dict):
        return [
            f"{label}: lightweight ITER-010 "
            "public_oss_evaluation_standing_authority must be a mapping"
        ]

    errors: list[str] = []
    failure_handoff = uses_failure_handoff_iter010_plan(manifest)
    standing_contract = (
        ITER010_FAILURE_HANDOFF_STANDING_AUTHORITY_EXACT_VALUES
        if failure_handoff
        else ITER010_LIGHTWEIGHT_STANDING_AUTHORITY_EXACT_VALUES
    )
    expected_values = dict(standing_contract)
    actual_fields = set(map(str, authority))
    expected_fields = set(expected_values)
    if actual_fields != expected_fields:
        missing = sorted(expected_fields - actual_fields)
        extra = sorted(actual_fields - expected_fields)
        errors.append(
            f"{label}: lightweight ITER-010 standing authority must use its closed schema"
            + (f"; missing={','.join(missing)}" if missing else "")
            + (f"; unexpected={','.join(extra)}" if extra else "")
        )
    for field, expected in standing_contract:
        if not _exact_plan_scalar(authority.get(field), expected):
            errors.append(
                f"{label}: public_oss_evaluation_standing_authority.{field} "
                f"must equal {expected}"
            )

    for field in ("source_commit", "source_tree"):
        value = authority.get(field)
        if not isinstance(value, str) or HEX_COMMIT_RE.fullmatch(value) is None:
            errors.append(
                f"{label}: public_oss_evaluation_standing_authority.{field} "
                "must be an exact 40-character lowercase Git object"
            )

    route_ref = authority.get("current_provider_route_ref")
    fallback_ref = authority.get("fallback_admission_policy_plugin_ref")
    for field, reference in (
        ("current_provider_route_ref", route_ref),
        ("fallback_admission_policy_plugin_ref", fallback_ref),
    ):
        if not isinstance(reference, str) or not isinstance(
            manifest.get(reference), dict
        ):
            errors.append(
                f"{label}: public_oss_evaluation_standing_authority.{field} "
                "must resolve to a generic Manifest policy mapping"
            )

    authorization = manifest.get("authorization")
    if not isinstance(authorization, dict):
        return errors + [
            f"{label}: lightweight ITER-010 authorization must be a mapping"
        ]
    authorization_contract = (
        ITER010_FAILURE_HANDOFF_AUTHORIZATION_STATE_EXACT_VALUES
        if failure_handoff
        else ITER010_LIGHTWEIGHT_AUTHORIZATION_STATE_EXACT_VALUES
    )
    for field, expected in authorization_contract:
        if not _exact_plan_scalar(authorization.get(field), expected):
            errors.append(
                f"{label}: lightweight ITER-010 authorization.{field} "
                f"must equal {expected}"
            )
    root_authorization_ref = authorization.get("authorization_ref")
    if not isinstance(root_authorization_ref, str) or re.fullmatch(
        r"(?:codex-user-message|local-user-message-utf8):sha256:[0-9a-f]{64}",
        root_authorization_ref,
    ) is None:
        errors.append(
            f"{label}: lightweight ITER-010 authorization.authorization_ref "
            "must preserve an exact human root-authority receipt"
        )
    return errors


def validate_iter010_lightweight_verification_semantics(
    verification: Document | None,
) -> list[str]:
    """Keep the lightweight plan enforceable without restoring the old action maze."""

    if verification is None:
        return ["ITER-010 lightweight plan requires Verification"]
    required: dict[str, dict[str, tuple[str, ...]]] = {
        ITER010_LIGHTWEIGHT_FIRST_OPERABLE_CASE_ID: {
            "Claim": ("完整浏览器主链", "可操作即交付"),
            "Frozen input / oracle": (
                "至少三 Turn 语义链",
                "完整世界模型—Agent—源码—Evidence/Citation—fresh Review—Web 责任链",
            ),
            "Expected": (
                "第一次达成即交付",
                "`requires_result=false`",
                "不移动游标",
                "不等待 Codex 比较",
            ),
        },
        ITER010_LIGHTWEIGHT_EXPERIENCE_CASE_ID: {
            "Claim": ("同一已交付候选", "最终 Result handoff"),
            "Frozen input / oracle": (
                "`V-CHAT-EXPERIENCE-001` 同一 clean candidate",
                "actual current Codex fresh baseline",
                "一次通用修复仍失败",
            ),
            "Expected": (
                "`requires_result=true`",
                "V-PREVIEW-002",
                "full regression=0",
            ),
        },
        "V-PREVIEW-002": {
            "Claim": ("完整浏览器体验", "异质问题", "current Codex"),
            "Frozen input / oracle": ("V-MVP-EXPERIENCE-001", "最早责任层"),
            "Expected": (
                "receipt 只记录方向且 action 自环",
                "`CONTINUE` 后仍需新 PDR、明确用户授权和可信父 cutover",
            ),
        },
    }
    indexes = {"Claim": 1, "Frozen input / oracle": 3, "Expected": 4}
    errors: list[str] = []
    for case_id, fields in required.items():
        rows = markdown_table_case_rows(verification.body, case_id)
        if len(rows) != 1 or len(rows[0]) != 7:
            errors.append(
                f"{verification.relative_path}: {case_id} must remain exactly once with the seven-column schema"
            )
            continue
        for field, phrases in fields.items():
            value = rows[0][indexes[field]]
            for phrase in phrases:
                if phrase not in value:
                    errors.append(
                        f"{verification.relative_path}: {case_id} {field} must preserve lightweight-plan phrase {phrase!r}"
                    )
    return errors


def validate_historical_gate_catalog(
    manifest: dict[str, object],
    blocking_case_ids: list[str],
    verification: Document | None,
    label: str,
) -> list[str]:
    """Separate immutable executed Case semantics from the current Chat gates."""

    cutover = manifest.get("critical_assumption_catalog_cutover")
    if not isinstance(cutover, dict):
        return []
    errors: list[str] = []
    historical_ids = resolved_csv_values(cutover.get("historical_case_ids"))
    reused = sorted(set(historical_ids).intersection(blocking_case_ids))
    if reused:
        errors.append(
            f"{label}: current blocking_case_ids must not reuse historical executed Cases: "
            + ", ".join(reused)
        )
    if uses_post_pdr009_iter010_plan(manifest):
        required_current_cases = {
            ITER010_LIGHTWEIGHT_EXPERIENCE_CASE_ID,
            ITER010_DIRECTION_QUALITY_CASE_ID,
            "V-CHAT-EXPERIENCE-001",
            "V-PREVIEW-002",
            "V-PUBLIC-OSS-AUTHORITY-ADMISSION-001",
        }
    elif uses_legacy_iter010_plan(manifest):
        required_current_cases = set(ITER010_CURRENT_CHAT_GATE_CASES)
    else:
        # A later plan revision must opt into its own generic/current contract;
        # absence of the PDR-010 marker must never reactivate PDR-009.
        required_current_cases = set()
    missing_current = sorted(required_current_cases - set(blocking_case_ids))
    if missing_current:
        errors.append(
            f"{label}: current blocking_case_ids must include the new Chat Gate catalog: "
            + ", ".join(missing_current)
        )
    if verification is None:
        return errors + [f"{label}: historical Gate cutover requires Verification"]
    for case_id, expected_verdict in ITER010_HISTORICAL_GATE_CASES.items():
        rows = markdown_table_case_rows(verification.body, case_id)
        if len(rows) != 1 or len(rows[0]) != 7:
            errors.append(
                f"{label}: historical Case {case_id} must remain exactly once in Verification"
            )
            continue
        verdict = blocking_case_status_verdict(rows[0][6])
        if verdict != expected_verdict:
            errors.append(
                f"{label}: historical Case {case_id} must preserve verdict {expected_verdict}"
            )
        expected_evidence = IMMUTABLE_HISTORICAL_CASE_EVIDENCE.get(
            ("ITER-010-RESULT-SLICE-001-STOP-REDIRECT", case_id)
        )
        if expected_evidence is not None and rows[0][5] != expected_evidence:
            errors.append(
                f"{label}: historical Case {case_id} must preserve its immutable Evidence"
            )
    if uses_post_pdr009_iter010_plan(manifest):
        obsolete_cases = {
            ITER010_PLAN_RECOVERY_CASE_ID,
            ITER010_CURRENT_ACTION_CASE_ID,
            ITER010_FALLBACK_REFREEZE_CASE_ID,
            "V-TIMEBOX-CHAT-001",
        }.intersection(blocking_case_ids)
        if obsolete_cases:
            errors.append(
                f"{label}: lightweight ITER-010 blocking cases must not retain superseded action cases: "
                + ", ".join(sorted(obsolete_cases))
            )
        errors.extend(validate_iter010_lightweight_verification_semantics(verification))
    elif uses_legacy_iter010_plan(manifest):
        errors.extend(
            validate_iter010_current_verification_semantics(verification, label)
        )
    return errors


def validate_iter010_current_verification_semantics(
    verification: Document | None, label: str
) -> list[str]:
    """Freeze the non-interchangeable semantics of the current ITER-010 gates."""

    if verification is None:
        return [f"{label}: current ITER-010 Gate contracts require Verification"]
    verification_label = verification.relative_path
    column_indexes = {"Claim": 1, "Frozen input / oracle": 3, "Expected": 4}
    errors: list[str] = []
    for case_id, field_contracts in (
        ITER010_CURRENT_VERIFICATION_REQUIRED_PHRASES.items()
    ):
        rows = markdown_table_case_rows(verification.body, case_id)
        if len(rows) != 1 or len(rows[0]) != 7:
            errors.append(
                f"{verification_label}: {case_id} must remain exactly once with the seven-column schema"
            )
            continue
        row = rows[0]
        for field_name, required_phrases in field_contracts.items():
            value = row[column_indexes[field_name]]
            for phrase in required_phrases:
                if phrase not in value:
                    errors.append(
                        f"{verification_label}: {case_id} {field_name} must preserve current semantic phrase {phrase!r}"
                    )
    return errors


def validate_rework_policy(
    manifest: dict[str, object], label: str, *, required: bool = False
) -> list[str]:
    """Validate the opt-in same-Slice repair policy used by new plans."""

    policy = manifest.get("rework_policy")
    if policy is None:  # Historical manifests predate this contract.
        return [f"{label}: rework_policy is required"] if required else []
    if not isinstance(policy, dict):
        return [f"{label}: rework_policy must be a mapping"]
    errors: list[str] = []
    expected = {
        "schema": "SAME_SLICE_REWORK@1",
        "failed_attempt_default_decision": "REWORK",
        "failed_attempt_blocks": "slice-promotion-only",
        "same_slice_reauthorization_allowed": True,
        "problem_report_or_review_request_implies_redirect": False,
        "redirect_bases": (
            "explicit-user-direction-change,core-architecture-falsified,"
            "precommitted-no-progress-limit-reached"
        ),
    }
    for field, value in expected.items():
        if policy.get(field) != value:
            errors.append(f"{label}: rework_policy.{field} must equal {value}")
    measure = policy.get("no_progress_measure")
    if (
        not isinstance(measure, str)
        or is_pending(measure)
        or has_unresolved_placeholder(measure)
    ):
        errors.append(
            f"{label}: rework_policy.no_progress_measure must be a resolved measurable outcome"
        )
    limit = policy.get("no_progress_attempt_limit")
    minimum_limit = 1 if policy.get("active_authorized_rework_continues") is True else 2
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < minimum_limit:
        errors.append(
            f"{label}: rework_policy.no_progress_attempt_limit must be an integer of at least {minimum_limit}"
        )
    return errors


def validate_answer_hierarchy_protocol(
    manifest: dict[str, object], label: str, *, require_frozen: bool = False
) -> list[str]:
    """Validate the optional, general answer-level and review-quality contract."""

    protocol = manifest.get("answer_hierarchy_protocol")
    if protocol is None:
        return []
    if not isinstance(protocol, dict):
        return [f"{label}: answer_hierarchy_protocol must be a mapping"]
    expected: dict[str, object] = {
        "contract_ref": "SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING",
        "direct_user_goal_answer_required": True,
        "user_visible_flow_behavior_or_impact_condition": "required-by-original-question-or-material-conclusion-checklist",
        "implementation_explanation_condition": "explicitly-requested-or-necessary-to-support-a-material-conclusion",
        "limitations_and_unknowns_condition": "evidence-gap-conflict-or-coverage-boundary-exists",
        "every_material_affirmative_claim_requires_citation": True,
        "fixed-heading-or-word-ratio-required": False,
        "material-conclusion-checklist_required": True,
        "application_acceptance_required": True,
        "shared_versioned_quality_contract_and_schema": True,
        "application_uses_accepted_question_understanding_checklist": True,
        "reviewer_reconstructs_checklist_from_immutable_original_question": True,
        "reviewer_compares_independent_and_application_checklists_for_omissions": True,
        "operational_question_checklist_required_for_start-call-use-integrate-diagnose": True,
        "component_or_dependency_inventory_satisfies_user-action-or-handoff": False,
        "finish_material_observations_required": True,
        "material_observation_kinds": "process-stage,outcome,state-change,side-effect,limitation",
        "answer_claim_material_observation_links_required": True,
        "coverage_only_limitation_empty_observation_links_allowed": True,
        "all_material_observations_default_visible_required": True,
        "reviewer_independent_evidence_observation_audit_required": True,
        "package_and_draft_observation_omissions_block_approval": True,
        "reviewer_context_and_verdict_independent": True,
        "question-project-keyword-symbol-class-method-fixture-or-oracle-routing_allowed": False,
    }
    marker_fields = {
        "protocol_role",
        "legacy_protocol_schema",
        "superseded_as_default_by",
        "current_delivery_authorization_allowed",
        "historical_result_ref",
    }
    allowed_fields = {"status", *expected}
    if protocol.get("protocol_role") == "legacy-compatibility":
        allowed_fields.update(marker_fields)
    errors = validate_exact_mapping_keys(
        protocol, allowed_fields, f"{label}: answer_hierarchy_protocol"
    )
    for field, value in expected.items():
        if protocol.get(field) != value:
            errors.append(f"{label}: answer_hierarchy_protocol.{field} must equal {value}")
    allowed_status = {"frozen"} if require_frozen else {"proposed-not-frozen", "frozen"}
    if protocol.get("status") not in allowed_status:
        errors.append(f"{label}: answer_hierarchy_protocol.status is invalid")
    if require_frozen:
        readiness = manifest.get("readiness_inputs")
        supplied = readiness.get("answer_hierarchy_protocol_digest") if isinstance(readiness, dict) else None
        expected_digest = canonical_mapping_digest(
            ENGINEERING_QA_ANSWER_HIERARCHY_SCHEMA,
            "answer_hierarchy_protocol",
            protocol,
        )
        if supplied != expected_digest:
            errors.append(f"{label}: answer_hierarchy_protocol_digest must bind the frozen protocol")
    return errors


def validate_direction_preview_answer_entry(
    alignment: dict[str, object],
    answer_protocol: dict[str, object],
    label: str,
) -> list[str]:
    """Keep the visible product identity aligned with the selected answer mode."""

    binding = alignment.get("direction_preview_binding")
    if not isinstance(binding, dict):
        return []
    expected = (
        "loopback-product-owned-engineering-qa-web"
        if is_engineering_qa_adaptive_protocol(answer_protocol)
        else "loopback-product-owned-world-model-web"
    )
    if binding.get("real_product_entry") != expected:
        return [
            f"{label}: direction preview product entry must match answer_protocol.mode as {expected}"
        ]
    return []


def required_early_evaluation_slice_refs(
    alignment: dict[str, object],
    new_refs: list[str],
    *,
    direction_preview_enabled: bool = False,
) -> set[str]:
    """Place early hardening gates after, never on, a direction preview."""

    if not direction_preview_enabled:
        return set(new_refs[:-1])
    preview_ref = resolved_direction_preview_slice_ref(alignment, new_refs)
    if preview_ref is None:
        return set(new_refs[:-1])
    checkpoint_ref = resolved_alpha_direction_slice_ref(alignment, new_refs) or preview_ref
    post_checkpoint_refs = new_refs[new_refs.index(checkpoint_ref) + 1 :]
    if len(post_checkpoint_refs) == 1:
        # A combined hardening/final Slice still owns the deferred early gates.
        return set(post_checkpoint_refs)
    return set(post_checkpoint_refs[:-1])


def direction_preview_hardening_is_deferred(
    manifest: dict[str, object],
    alignment: dict[str, object],
    new_refs: list[str],
    *,
    direction_preview_enabled: bool = False,
) -> bool:
    """Return whether the explicit preview Slice has not completed yet."""

    if not direction_preview_enabled:
        return False
    preview_ref = resolved_direction_preview_slice_ref(alignment, new_refs)
    if preview_ref is None:
        return False
    checkpoint_ref = resolved_alpha_direction_slice_ref(alignment, new_refs) or preview_ref
    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    checkpoint = slices.get(checkpoint_ref) if isinstance(slices, dict) else None
    checkpoint_status = checkpoint.get("status") if isinstance(checkpoint, dict) else None
    return checkpoint_status in {"proposed", "authorized", "in-progress", "blocked"}


def validate_early_evaluation_bindings(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
    *,
    defer_until_post_preview: bool = False,
    direction_preview_enabled: bool = False,
    adaptive_engineering_qa: bool = False,
) -> list[str]:
    """Freeze the first real falsification checkpoint before coding starts."""

    errors: list[str] = []
    expected_refs = required_early_evaluation_slice_refs(
        alignment,
        new_refs,
        direction_preview_enabled=direction_preview_enabled,
    )
    if not expected_refs:
        return errors
    preview_ref = (
        resolved_direction_preview_slice_ref(alignment, new_refs)
        if direction_preview_enabled
        else None
    )
    alpha_ref = resolved_alpha_direction_slice_ref(alignment, new_refs)
    if defer_until_post_preview and preview_ref is not None:
        preview_owned_fields: list[str] = []
        canary_bindings = alignment.get("early_hidden_canary_bindings")
        if isinstance(canary_bindings, dict):
            for binding_name, binding in canary_bindings.items():
                if isinstance(binding, dict) and binding.get("new_slice_ref") in {preview_ref, alpha_ref}:
                    preview_owned_fields.append(
                        f"early_hidden_canary_bindings.{binding_name}"
                    )
        for field in ("early_comparison_binding", "early_diagnostic_binding"):
            binding = alignment.get(field)
            if isinstance(binding, dict) and binding.get("new_slice_ref") in {preview_ref, alpha_ref}:
                preview_owned_fields.append(field)
        if preview_owned_fields:
            errors.append(
                f"{label}: direction preview Slice must not own deferred early hidden canary, comparison or diagnostic Gates: "
                + ", ".join(preview_owned_fields)
            )
        if not any(
            field in alignment
            for field in (
                "early_hidden_canary_bindings",
                "early_comparison_binding",
                "early_diagnostic_binding",
            )
        ):
            return errors
    user_held_live = (
        alignment.get("evaluation_input_mode") == USER_HELD_LIVE_EVALUATION_MODE
    )
    bindings = alignment.get("early_hidden_canary_bindings")
    if not isinstance(bindings, dict) or not bindings:
        errors.append(
            f"{label}: early_hidden_canary_bindings must cover every pre-final Slice"
        )
        return errors

    canary_by_case: dict[str, tuple[str, dict[str, object]]] = {}
    seen_refs: list[str] = []
    for binding_name, binding in bindings.items():
        if not isinstance(binding, dict):
            errors.append(
                f"{label}: early_hidden_canary_bindings.{binding_name} must be a mapping"
            )
            continue
        new_ref = binding.get("new_slice_ref")
        case_id = binding.get("case_id")
        if not isinstance(new_ref, str) or new_ref not in expected_refs:
            errors.append(
                f"{label}: early hidden canary must bind a pre-final Slice"
            )
        else:
            seen_refs.append(new_ref)
        if (
            not isinstance(case_id, str)
            or re.fullmatch(r"V-CANARY-[0-9]{3,}", case_id) is None
        ):
            errors.append(
                f"{label}: early hidden canary case_id must match V-CANARY-NNN"
            )
        elif case_id in canary_by_case:
            errors.append(f"{label}: early hidden canary Case IDs must be unique")
        else:
            if case_id not in blocking_case_ids:
                errors.append(f"{label}: early hidden canary Case must be blocking")
            if isinstance(new_ref, str):
                canary_by_case[case_id] = (new_ref, binding)
        if binding.get("evaluation_owner") not in {"independent-evaluator", "user"}:
            errors.append(
                f"{label}: early hidden canary must have an independent evaluation owner"
            )
        if binding.get("implementation_visibility") != "hidden-until-slice-code-freeze":
            errors.append(
                f"{label}: early hidden canary must remain hidden until Slice code freeze"
            )
        if binding.get("burn_rule") != (
            "product-change-between-disclosure-and-slice-result-seal-"
            "burns-canary-and-preserves-result"
        ):
            errors.append(
                f"{label}: early hidden canary must freeze the disclosure-to-Result-seal burn rule"
            )
        for field in ("project_manifest_digest", "suite_digest"):
            value = binding.get(field)
            if not (
                user_held_live and value == USER_HELD_LIVE_UNDISCLOSED
            ) and (
                not isinstance(value, str)
                or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
            ):
                errors.append(
                    f"{label}: early hidden canary {field} must be an exact sha256 digest or the closed user-held undisclosed marker"
                )

        count_fields = {
            "question_count": 3,
            "answerable_question_count": 1,
            "boundary_question_count": 2,
            "bounded_absence_question_count": 1,
            "coverage_limitation_question_count": 1,
        }
        for field, minimum in count_fields.items():
            value = binding.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                errors.append(
                    f"{label}: early hidden canary {field} must be at least {minimum}"
                )
        question_count = binding.get("question_count")
        answerable_count = binding.get("answerable_question_count")
        boundary_count = binding.get("boundary_question_count")
        if (
            isinstance(question_count, int)
            and not isinstance(question_count, bool)
            and isinstance(answerable_count, int)
            and not isinstance(answerable_count, bool)
            and isinstance(boundary_count, int)
            and not isinstance(boundary_count, bool)
            and question_count != answerable_count + boundary_count
        ):
            errors.append(
                f"{label}: early hidden canary question_count must equal answerable plus boundary counts"
            )
        negative_case_id = binding.get("negative_case_id")
        if (
            not isinstance(negative_case_id, str)
            or re.fullmatch(r"V-NEG-EARLY-[0-9]{3,}", negative_case_id) is None
            or negative_case_id not in blocking_case_ids
        ):
            errors.append(
                f"{label}: early hidden canary negative_case_id must be a blocking V-NEG-EARLY-NNN Case"
            )

    if set(seen_refs) != expected_refs or len(seen_refs) != len(set(seen_refs)):
        errors.append(
            f"{label}: early hidden canaries must bind each pre-final Slice exactly once"
        )

    comparison = alignment.get("early_comparison_binding")
    comparison_ref: str | None = None
    comparison_canary: str | None = None
    if not isinstance(comparison, dict):
        errors.append(f"{label}: early_comparison_binding must be a mapping")
    else:
        comparison_case = comparison.get("case_id")
        comparison_canary_value = comparison.get("canary_case_id")
        comparison_ref_value = comparison.get("new_slice_ref")
        if (
            not isinstance(comparison_case, str)
            or re.fullmatch(r"V-COMP-EARLY-[0-9]{3,}", comparison_case) is None
            or comparison_case not in blocking_case_ids
        ):
            errors.append(
                f"{label}: early comparison case_id must be a blocking V-COMP-EARLY-NNN Case"
            )
        if (
            not isinstance(comparison_canary_value, str)
            or comparison_canary_value not in canary_by_case
        ):
            errors.append(
                f"{label}: early comparison must reference a frozen early canary"
            )
        else:
            comparison_canary = comparison_canary_value
        if not isinstance(comparison_ref_value, str) or comparison_ref_value not in expected_refs:
            errors.append(
                f"{label}: early comparison must bind a pre-final Slice"
            )
        else:
            comparison_ref = comparison_ref_value
        if (
            comparison_canary is not None
            and comparison_ref is not None
            and canary_by_case[comparison_canary][0] != comparison_ref
        ):
            errors.append(
                f"{label}: early comparison and canary must bind the same Slice"
            )
        if comparison.get("protocol_digest_ref") != "mature_source_agent_protocol_digest":
            errors.append(
                f"{label}: early comparison protocol_digest_ref must equal mature_source_agent_protocol_digest"
            )
        if comparison.get("quality_rule") != "zero-major-error-and-no-need-claim-regression":
            errors.append(f"{label}: early comparison quality_rule is invalid")
        if comparison.get("positive_value_rule") != "precommitted-measurable-world-model-advantage-must-pass":
            errors.append(f"{label}: early comparison positive_value_rule is invalid")
        for reference_field, target_field in (
            ("positive_value_metric_ref", "positive_value_metric"),
            ("positive_value_unit_ref", "positive_value_unit"),
            ("positive_value_comparison_ref", "positive_value_comparison"),
            ("positive_value_threshold_ref", "positive_value_threshold"),
            (
                "positive_value_reuse_horizon_ref",
                "positive_value_reuse_horizon_questions",
            ),
            (
                "baseline_cache_policy_digest_ref",
                "mature_source_agent_cache_policy_digest",
            ),
            (
                "positive_value_protocol_digest_ref",
                "positive_value_protocol_digest",
            ),
        ):
            if comparison.get(reference_field) != target_field:
                errors.append(
                    f"{label}: early comparison {reference_field} must equal {target_field}"
                )
            if target_field not in alignment:
                errors.append(
                    f"{label}: early comparison referenced field is missing: {target_field}"
                )
        if "technical_adjudication_owner" in comparison:
            for field, expected in (
                (
                    "technical_adjudication_owner",
                    "independent-evaluator-not-answer-generator",
                ),
                ("product_direction_decision_owner", "user"),
                (
                    "legacy_positive_value_adjudication_owner_ref",
                    "positive_value_adjudication_owner",
                ),
            ):
                if comparison.get(field) != expected:
                    errors.append(
                        f"{label}: early comparison {field} must equal {expected}"
                    )
        elif comparison.get("positive_value_adjudication_owner_ref") != (
            "positive_value_adjudication_owner"
        ):
            errors.append(
                f"{label}: early comparison positive_value_adjudication_owner_ref "
                "must equal positive_value_adjudication_owner"
            )

    diagnostic = alignment.get("early_diagnostic_binding")
    if not isinstance(diagnostic, dict):
        errors.append(f"{label}: early_diagnostic_binding must be a mapping")
    else:
        diagnostic_case = diagnostic.get("case_id")
        diagnostic_ref = diagnostic.get("new_slice_ref")
        diagnostic_canary = diagnostic.get("canary_case_id")
        if (
            not isinstance(diagnostic_case, str)
            or re.fullmatch(r"V-DIAG-[0-9]{3,}", diagnostic_case) is None
            or diagnostic_case not in blocking_case_ids
        ):
            errors.append(
                f"{label}: early diagnostic case_id must be a blocking V-DIAG-NNN Case"
            )
        if diagnostic_canary != comparison_canary:
            errors.append(
                f"{label}: early diagnostic must reference the same canary as the comparison"
            )
        if diagnostic_ref != comparison_ref:
            errors.append(
                f"{label}: early diagnostic, comparison and canary must bind the same Slice"
            )
        expected_layer_chains = (
            {
                "source-observation-world-model-cognition-question-understanding-"
                "investigation-source-broker-retrieval-worker-evidence-ledger-"
                "question-evidence-package-answer-review-web",
                "source-observation-world-model-cognition-conversation-or-task-"
                "understanding-agent-work-state-and-plan-source-broker-retrieval-"
                "worker-evidence-ledger-question-evidence-package-answer-"
                "independent-review-web",
            }
            if adaptive_engineering_qa
            else {"source-snapshot-query-trace-draft-review-web"}
        )
        if diagnostic.get("layer_chain") not in expected_layer_chains:
            errors.append(f"{label}: early diagnostic layer_chain is invalid")
    return errors


def resolved_assumption_ids(value: object) -> list[str]:
    if isinstance(value, str):
        values = [item.strip() for item in value.split(",")]
    elif isinstance(value, list):
        values = [str(item).strip() for item in value]
    else:
        return []
    if (
        not values
        or any(re.fullmatch(r"A[1-9][0-9]*", item) is None for item in values)
        or len(values) != len(set(values))
    ):
        return []
    return values


def validate_reflection_gate_bindings(
    alignment: dict[str, object],
    new_refs: list[str],
    blocking_case_ids: list[str],
    label: str,
) -> list[str]:
    """Require one auditable reflection gate for every ITER-008+ Slice."""

    errors: list[str] = []
    bindings = alignment.get("reflection_gate_bindings")
    if not isinstance(bindings, dict) or not bindings:
        return [f"{label}: reflection_gate_bindings must be a non-empty mapping"]

    critical_assumption_ids = resolved_assumption_ids(
        alignment.get("critical_assumption_ids")
    )
    if not critical_assumption_ids:
        errors.append(
            f"{label}: critical_assumption_ids must be a non-empty unique list of A-number IDs"
        )
        critical_assumption_ids = []

    seen_cases: set[str] = set()
    seen_slices: set[str] = set()
    assumptions_by_slice: dict[str, list[str]] = {}
    expected_success_decisions = {
        reference: "ACCEPT" if index == len(new_refs) - 1 else "CONTINUE"
        for index, reference in enumerate(new_refs)
    }
    for binding_name, binding in bindings.items():
        if not isinstance(binding, dict):
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name} must be a mapping"
            )
            continue
        case_id = binding.get("case_id")
        new_slice_ref = binding.get("new_slice_ref")
        success_decision = binding.get("success_decision")
        assumption_ids = resolved_assumption_ids(binding.get("assumption_ids"))
        if "historical_owned_case_ids" in binding:
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name} cannot declare historical Case ownership"
            )
        if (
            not isinstance(case_id, str)
            or re.fullmatch(r"V-(?:REFLECT|PREVIEW)-[0-9]{3,}", case_id) is None
        ):
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name}.case_id must match V-REFLECT-NNN or a combined V-PREVIEW-NNN decision Gate"
            )
        elif case_id in seen_cases:
            errors.append(f"{label}: reflection Gate Case IDs must be unique: {case_id}")
        else:
            seen_cases.add(case_id)
            if case_id not in blocking_case_ids:
                errors.append(
                    f"{label}: reflection Gate Case must be included in blocking_case_ids: {case_id}"
                )

        if not isinstance(new_slice_ref, str) or new_slice_ref not in new_refs:
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name}.new_slice_ref must reference new_capability_slice_refs"
            )
        elif new_slice_ref in seen_slices:
            errors.append(
                f"{label}: each Slice must have exactly one reflection Gate: {new_slice_ref}"
            )
        else:
            seen_slices.add(new_slice_ref)
            expected_decision = expected_success_decisions[new_slice_ref]
            if success_decision != expected_decision:
                errors.append(
                    f"{label}: {new_slice_ref} reflection success_decision must equal {expected_decision}"
                )

        if binding.get("required_before_next_authorization_or_acceptance") is not True:
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name} must be required before next authorization or acceptance"
            )
        expected_order = [
            assumption_id
            for assumption_id in critical_assumption_ids
            if assumption_id in set(assumption_ids)
        ]
        if not assumption_ids:
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name}.assumption_ids must be non-empty"
            )
        elif (
            any(
                assumption_id not in critical_assumption_ids
                for assumption_id in assumption_ids
            )
            or assumption_ids != expected_order
        ):
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name}.assumption_ids must be an ordered subset of critical_assumption_ids"
            )
        elif isinstance(new_slice_ref, str) and new_slice_ref in new_refs:
            assumptions_by_slice[new_slice_ref] = assumption_ids
        deferred_assumptions = [
            assumption_id
            for assumption_id in critical_assumption_ids
            if assumption_id not in set(assumption_ids)
        ]
        conditional_falsifiers = binding.get("conditional_falsifier_bindings")
        if deferred_assumptions:
            if not isinstance(conditional_falsifiers, dict):
                errors.append(
                    f"{label}: reflection_gate_bindings.{binding_name} must map every deferred assumption to an early conditional falsifier"
                )
            else:
                mapped_deferred: list[str] = []
                seen_falsifier_cases: set[str] = set()
                for falsifier_name, falsifier in conditional_falsifiers.items():
                    if not isinstance(falsifier, dict):
                        errors.append(
                            f"{label}: conditional_falsifier_bindings.{falsifier_name} must be a mapping"
                        )
                        continue
                    assumption_id = falsifier.get("assumption_id")
                    falsifier_case_id = falsifier.get("case_id")
                    if assumption_id not in deferred_assumptions:
                        errors.append(
                            f"{label}: conditional falsifier assumption_id must reference a deferred critical assumption"
                        )
                    else:
                        mapped_deferred.append(str(assumption_id))
                    if (
                        not isinstance(falsifier_case_id, str)
                        or falsifier_case_id not in blocking_case_ids
                        or falsifier_case_id in seen_falsifier_cases
                    ):
                        errors.append(
                            f"{label}: conditional falsifier case_id must be a unique blocking Case"
                        )
                    else:
                        seen_falsifier_cases.add(falsifier_case_id)
                if (
                    set(mapped_deferred) != set(deferred_assumptions)
                    or len(mapped_deferred) != len(set(mapped_deferred))
                ):
                    errors.append(
                        f"{label}: conditional falsifiers must cover every deferred critical assumption exactly once"
                    )
        elif conditional_falsifiers is not None and conditional_falsifiers != {}:
            errors.append(
                f"{label}: final Slice must not define deferred conditional falsifiers"
            )
        decision_owner = binding.get("decision_owner")
        if (
            not isinstance(decision_owner, str)
            or is_pending(decision_owner)
            or is_absent_evidence(decision_owner)
            or has_unresolved_placeholder(decision_owner)
        ):
            errors.append(
                f"{label}: reflection_gate_bindings.{binding_name}.decision_owner must be resolved"
            )

    missing_slices = [reference for reference in new_refs if reference not in seen_slices]
    if missing_slices:
        errors.append(
            f"{label}: every Slice must have exactly one reflection Gate: "
            + ", ".join(missing_slices)
        )
    if len(bindings) != len(new_refs):
        errors.append(
            f"{label}: reflection_gate_bindings count must equal new_capability_slice_refs count"
        )
    previous_assumptions: set[str] = set()
    for index, reference in enumerate(new_refs):
        current_assumptions = assumptions_by_slice.get(reference, [])
        if not previous_assumptions.issubset(set(current_assumptions)):
            errors.append(
                f"{label}: {reference} reflection assumptions must retain every earlier Slice assumption"
            )
        if index == len(new_refs) - 1 and current_assumptions != critical_assumption_ids:
            errors.append(
                f"{label}: final Slice reflection assumptions must cover all critical_assumption_ids in frozen order"
            )
        previous_assumptions = set(current_assumptions)
    return errors


def validate_product_goal_alignment_manifest(
    manifest: dict[str, object], text: str, label: str, iteration: str
) -> list[str]:
    if not requires_product_goal_alignment(iteration):
        return []

    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return [f"{label}: product_goal_alignment must be a mapping from ITER-007 onward"]

    errors: list[str] = []
    errors.extend(
        validate_provider_route_policy(
            manifest,
            text,
            label,
            required=requires_provider_route_policy(iteration),
        )
    )
    errors.extend(validate_model_transparent_plan_routing(manifest, label))
    if requires_strict_codex_baseline(iteration):
        errors.extend(
            validate_strict_codex_baseline_alignment(
                alignment,
                label,
                allow_pending_identity=(
                    iteration == "ITER-010"
                    and iter010_pending_codex_identity_allowed(manifest)
                ),
            )
        )
    if requires_reflection_gate(iteration):
        catalog_digest = alignment.get("critical_assumption_catalog_digest")
        if catalog_digest != "not-frozen-proposal-only" and (
            not isinstance(catalog_digest, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", catalog_digest) is None
        ):
            errors.append(
                f"{label}: critical_assumption_catalog_digest must be the proposal-only marker or an exact sha256 digest"
            )
    evaluation_input_mode = alignment.get(
        "evaluation_input_mode", "precommitted-hidden-suite"
    )
    if evaluation_input_mode not in {
        "precommitted-hidden-suite",
        USER_HELD_LIVE_EVALUATION_MODE,
    }:
        errors.append(
            f"{label}: product_goal_alignment.evaluation_input_mode is invalid"
        )
    user_held_live = evaluation_input_mode == USER_HELD_LIVE_EVALUATION_MODE
    if user_held_live:
        input_owner = alignment.get("held_out_input_owner")
        evaluation_owner = alignment.get("held_out_evaluation_owner")
        if input_owner is None:
            if evaluation_owner != "user":
                errors.append(
                    f"{label}: legacy user-held live evaluation must use held_out_evaluation_owner user"
                )
        elif input_owner != "user" or evaluation_owner != "independent-evaluator":
            errors.append(
                f"{label}: user-held input must use held_out_input_owner user and held_out_evaluation_owner independent-evaluator"
            )
    if alignment.get("target_ref") != "SYS-PRODUCT-SUCCESS":
        errors.append(
            f"{label}: product_goal_alignment.target_ref must equal SYS-PRODUCT-SUCCESS"
        )
    for field in PRODUCT_GOAL_ALIGNMENT_MANIFEST_SCALARS:
        value = alignment.get(field)
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(
                f"{label}: product_goal_alignment.{field} must be a resolved scalar"
            )
    if alignment.get("implementation_question_visibility") != "hidden":
        errors.append(
            f"{label}: product_goal_alignment.implementation_question_visibility must equal hidden"
        )
    if (
        alignment.get("implementation_project_identity_and_source_visibility")
        != "hidden-until-product-code-freeze"
    ):
        errors.append(
            f"{label}: implementation project identity and source must remain hidden until product code freeze"
        )
    if alignment.get("supported_count_denominator") != "answerable-only":
        errors.append(
            f"{label}: supported_count_denominator must equal answerable-only"
        )
    if alignment.get("boundary_gap_counted_as_supported") is not False:
        errors.append(
            f"{label}: boundary_gap_counted_as_supported must be false"
        )
    if alignment.get("held_out_evaluation_owner") not in {
        "independent-evaluator",
        "user",
    }:
        errors.append(
            f"{label}: product_goal_alignment.held_out_evaluation_owner must equal independent-evaluator or user"
        )
    for field in PRODUCT_GOAL_ALIGNMENT_MANIFEST_DIGESTS:
        value = alignment.get(field)
        valid_user_held_value = user_held_live and value == USER_HELD_LIVE_UNDISCLOSED
        if not valid_user_held_value and (
            not isinstance(value, str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
        ):
            errors.append(
                f"{label}: product_goal_alignment.{field} must be an exact sha256 digest"
                " or the closed user-held undisclosed marker"
            )

    counts: dict[str, int] = {}
    for field in PRODUCT_GOAL_ALIGNMENT_MANIFEST_COUNTS:
        value = alignment.get(field)
        if (
            user_held_live
            and field
            in {"held_out_baseline_supported_count", "held_out_target_supported_count"}
            and value == USER_HELD_LIVE_UNMEASURED
        ):
            continue
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            errors.append(
                f"{label}: product_goal_alignment.{field} must be a non-negative integer"
            )
        else:
            counts[field] = value
    total = counts.get("held_out_question_count")
    answerable = counts.get("held_out_answerable_question_count")
    boundary = counts.get("held_out_boundary_question_count")
    without_symbol = counts.get(
        "held_out_answerable_without_symbol_count_minimum"
    )
    without_symbol_per_project = counts.get(
        "held_out_answerable_without_symbol_per_project_minimum"
    )
    baseline_supported = counts.get("held_out_baseline_supported_count")
    target_supported = counts.get("held_out_target_supported_count")
    if (
        total is not None
        and answerable is not None
        and boundary is not None
        and total != answerable + boundary
    ):
        errors.append(
            f"{label}: held_out_question_count must equal answerable plus boundary counts"
        )
    if (
        answerable is not None
        and without_symbol is not None
        and not (0 < without_symbol <= answerable)
    ):
        errors.append(
            f"{label}: held-out no-symbol minimum must be positive and no greater than answerable count"
        )
    if (
        without_symbol is not None
        and without_symbol_per_project is not None
        and not (0 < without_symbol_per_project * 2 <= without_symbol)
    ):
        errors.append(
            f"{label}: per-project no-symbol minimum must fit the two-project total minimum"
        )
    if (
        answerable is not None
        and baseline_supported is not None
        and not (0 <= baseline_supported < answerable)
    ):
        errors.append(
            f"{label}: held-out baseline supported count must be lower than answerable count"
        )
    if (
        boundary is not None
        and boundary == 0
    ):
        errors.append(
            f"{label}: held_out_boundary_question_count must be greater than zero"
        )
    live_count = counts.get("live_ad_hoc_question_count")
    live_without_symbol = counts.get(
        "live_ad_hoc_without_symbol_count_minimum"
    )
    if (
        live_count is not None
        and live_without_symbol is not None
        and not (0 < live_without_symbol <= live_count)
    ):
        errors.append(
            f"{label}: live no-symbol minimum must be positive and no greater than live question count"
        )
    if (
        answerable is not None
        and baseline_supported is not None
        and target_supported is not None
    ):
        minimum_target = min(answerable, max(baseline_supported + 4, 8))
        if not (
            baseline_supported < target_supported <= answerable
            and target_supported >= minimum_target
        ):
            errors.append(
                f"{label}: held-out target must be above baseline, no greater than answerable, "
                "and at least min(answerable, max(baseline + 4, 8))"
            )
    for field in ("cross_domain_case_count", "live_ad_hoc_question_count"):
        if counts.get(field) == 0:
            errors.append(
                f"{label}: product_goal_alignment.{field} must be greater than zero"
            )

    sequences: dict[str, list[str]] = {}
    for field in PRODUCT_GOAL_ALIGNMENT_MANIFEST_SEQUENCES:
        items = (
            manifest_resolved_sequence_items(text, "product_goal_alignment", field)
            if field in alignment
            else None
        )
        if items is None:
            errors.append(
                f"{label}: product_goal_alignment.{field} must contain at least one item"
            )
        else:
            sequences[field] = items
            if len(items) != len(set(items)):
                errors.append(
                    f"{label}: product_goal_alignment.{field} must not contain duplicate items"
                )
    cross_domain_count = counts.get("cross_domain_case_count")
    if (
        cross_domain_count is not None
        and "cross_domain_cases" in sequences
        and len(sequences["cross_domain_cases"]) != cross_domain_count
    ):
        errors.append(
            f"{label}: cross_domain_cases count must equal cross_domain_case_count"
        )
    for case_id in sequences.get("cross_domain_cases", []):
        if re.fullmatch(r"V-(?:CHAT-)?XD-[0-9]{3,}", case_id) is None:
            errors.append(
                f"{label}: cross_domain_cases item must match V-XD-NNN or V-CHAT-XD-NNN: {case_id}"
            )
    blocking_case_ids = sequences.get("blocking_case_ids", [])
    required_blocking_cases = set(sequences.get("cross_domain_cases", []))
    for field in (
        "first_product_web_checkpoint",
        "live_ad_hoc_question_checkpoint",
    ):
        value = alignment.get(field)
        if isinstance(value, str):
            required_blocking_cases.add(value)
    if requires_direction_preview(iteration):
        direction_preview_checkpoint = alignment.get("direction_preview_checkpoint")
        if isinstance(direction_preview_checkpoint, str):
            required_blocking_cases.add(direction_preview_checkpoint)
    additional_web_bindings = alignment.get("additional_web_checkpoint_bindings")
    if isinstance(additional_web_bindings, dict):
        for binding in additional_web_bindings.values():
            if isinstance(binding, dict) and isinstance(binding.get("case_id"), str):
                required_blocking_cases.add(str(binding["case_id"]))
    if not required_blocking_cases.issubset(set(blocking_case_ids)):
        errors.append(
            f"{label}: blocking_case_ids must include every cross-domain, Web and ad-hoc Case"
        )
    iteration_data = manifest.get("iteration")
    iteration_status = (
        iteration_data.get("status") if isinstance(iteration_data, dict) else None
    )
    development = manifest.get("development")
    raw_slices = development.get("slices") if isinstance(development, dict) else None
    has_rework_state = iteration_status == "paused" or (
        isinstance(raw_slices, dict)
        and any(
            isinstance(slice_state, dict)
            and any(
                field in slice_state
                for field in (
                    "project_decision_ref",
                    "rework_result_refs",
                    "rework_attempt_number",
                )
            )
            for slice_state in raw_slices.values()
        )
    )
    # Iterations written after the repair-loop contract was introduced cannot
    # opt back into the legacy three-way decision model merely by deleting the
    # rework fields after a failed attempt.  Superseded, never-executed plans
    # remain historical planning records and are validated separately.
    rework_lifecycle_required = has_rework_state or (
        isinstance(iteration_data, dict)
        and (iteration_number(iteration) or -1) >= REWORK_LIFECYCLE_START_ITERATION
        and iteration_status != "superseded"
    )
    errors.extend(validate_answer_hierarchy_protocol(manifest, label))
    errors.extend(
        validate_rework_policy(manifest, label, required=rework_lifecycle_required)
    )
    for case_id in blocking_case_ids:
        if re.fullmatch(r"V-(?:PRE-)?[A-Z0-9]+(?:-[A-Z0-9]+)*", case_id) is None:
            errors.append(
                f"{label}: blocking_case_ids item is not a valid verification case ID: {case_id}"
            )
    checkpoint_fields = [
        (
            "first_product_web_checkpoint",
            r"V-(?:ALPHA-ACCESS|CHAT-EXPERIENCE)-[0-9]{3,}"
            if conversational_agent_cutover_active(manifest)
            else r"V-WEB-[0-9]{3,}",
        ),
        ("live_ad_hoc_question_checkpoint", r"V-ADHOC-[0-9]{3,}"),
    ]
    if requires_direction_preview(iteration):
        checkpoint_fields.append(
            ("direction_preview_checkpoint", r"V-PREVIEW-[0-9]{3,}")
        )
    for field, pattern in checkpoint_fields:
        value = alignment.get(field)
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            errors.append(
                f"{label}: product_goal_alignment.{field} must be a verification case ID"
            )
    new_refs = sequences.get("new_capability_slice_refs", [])
    errors.extend(
        validate_experience_first_delivery_policy(
            manifest,
            alignment,
            new_refs,
            blocking_case_ids,
            label,
            required=requires_experience_first_delivery_policy(iteration),
            manifest_text=text,
        )
    )
    if iteration == "ITER-010":
        errors.extend(
            validate_iter010_lightweight_standing_authority(manifest, label)
        )
    errors.extend(
        validate_experience_version_binding(
            alignment,
            new_refs,
            blocking_case_ids,
            label,
            required=rework_lifecycle_required,
        )
    )
    experience_binding = alignment.get("experience_version_binding")
    chat_required = (
        isinstance(experience_binding, dict)
        and experience_binding.get("schema") == ENGINEERING_CHAT_EXPERIENCE_SCHEMA
    )
    errors.extend(
        validate_conversational_engineering_agent(
            manifest,
            alignment,
            new_refs,
            blocking_case_ids,
            label,
            required=chat_required,
        )
    )
    errors.extend(
        validate_conversational_architecture_cutover(
            manifest, label, manifest_text=text
        )
    )
    if iteration == "ITER-010" and uses_legacy_iter010_plan(manifest):
        errors.extend(validate_iter010_direction_checkpoint_policy(manifest, label))
    if requires_direction_preview(iteration):
        errors.extend(
            validate_direction_preview_binding(
                alignment,
                new_refs,
                blocking_case_ids,
                label,
            )
        )
        errors.extend(
            validate_alpha_direction_binding(
                alignment,
                new_refs,
                blocking_case_ids,
                label,
            )
        )
        if rework_lifecycle_required:
            direction_binding = alignment.get("direction_preview_binding")
            experience_binding = alignment.get("experience_version_binding")
            if isinstance(direction_binding, dict) and isinstance(
                experience_binding, dict
            ):
                if direction_binding.get("web_case_id") != experience_binding.get(
                    "case_id"
                ):
                    errors.append(
                        f"{label}: rework direction preview must use the sustained experience version Case"
                    )
                if (
                    direction_binding.get("allowed_decisions")
                    != "CONTINUE,REWORK,REDIRECT,REJECT"
                ):
                    errors.append(
                        f"{label}: rework direction preview must include CONTINUE, REWORK, REDIRECT and REJECT"
                )
        if requires_strict_codex_baseline(iteration) or chat_required:
            errors.extend(
                validate_alpha_agent_comparison_binding(
                    alignment,
                    new_refs,
                    blocking_case_ids,
                    label,
                )
            )
    if requires_reflection_gate(iteration):
        errors.extend(
            validate_reflection_gate_bindings(
                alignment,
                new_refs,
                blocking_case_ids,
                label,
            )
        )
        errors.extend(
            validate_early_evaluation_bindings(
                alignment,
                new_refs,
                blocking_case_ids,
                label,
                defer_until_post_preview=direction_preview_hardening_is_deferred(
                    manifest,
                    alignment,
                    new_refs,
                    direction_preview_enabled=requires_direction_preview(iteration),
                ),
                direction_preview_enabled=requires_direction_preview(iteration),
                adaptive_engineering_qa=(
                    isinstance(manifest.get("answer_protocol"), dict)
                    and is_engineering_qa_adaptive_protocol(
                        manifest["answer_protocol"]
                    )
                ),
            )
        )
    answer_protocol = manifest.get("answer_protocol")
    if (
        supports_engineering_qa_hybrid(iteration)
        and isinstance(answer_protocol, dict)
        and is_engineering_qa_adaptive_protocol(answer_protocol)
    ):
        errors.extend(validate_engineering_qa_adaptive_gate(manifest, label))
    errors.extend(validate_product_goal_structured_bindings(alignment, sequences, label))
    return errors


def validate_product_goal_alignment_documents(
    proposal: Document | None,
    verification: Document | None,
    iteration: str,
) -> list[str]:
    if not requires_product_goal_alignment(iteration):
        return []

    errors: list[str] = []
    if proposal is None:
        errors.append(f"{iteration}: selected iteration is missing proposal.md")
    else:
        dependencies = proposal.metadata.get("depends_on", [])
        if (
            not isinstance(dependencies, list)
            or "SYS-PRODUCT-SUCCESS" not in dependencies
        ):
            errors.append(
                f"{proposal.relative_path}: product-goal-aligned proposal must depend on SYS-PRODUCT-SUCCESS"
            )
    errors.extend(validate_product_goal_v000(verification, iteration))
    return errors


def markdown_table_case_rows(body: str, case_id: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue
        cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", stripped[1:-1])]
        if cells and cells[0] == case_id:
            rows.append(cells)
    return rows


def validate_blocking_verification_case(
    verification: Document | None,
    case_id: str,
    *,
    required_references: tuple[str, ...] = (),
    require_pass: bool = False,
    require_executed: bool = False,
    expected_evidence: str | None = None,
) -> list[str]:
    if verification is None:
        return [f"missing verification matrix for {case_id}"]
    label = verification.relative_path
    rows = markdown_table_case_rows(verification.body, case_id)
    if len(rows) != 1:
        return [f"{label}: must define exactly one {case_id} row"]
    row = rows[0]
    if len(row) != 7:
        return [f"{label}: {case_id} must use the exact seven-column schema"]

    errors: list[str] = []
    for index, field in enumerate(
        ("claim", "level", "frozen input / oracle", "expected"), start=1
    ):
        value = row[index]
        if (
            not value
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(f"{label}: {case_id} {field} must be resolved")
    strict_status = requires_reflection_gate(
        str(verification.metadata.get("iteration", ""))
    ) or require_executed
    status_verdict = blocking_case_status_verdict(row[6])
    legacy_status_tokens: set[str] = set()
    if strict_status:
        if status_verdict is None:
            errors.append(
                f"{label}: {case_id} must remain blocking and use exact PASS, FAIL, INVALID or NOT-RUN / blocking grammar"
            )
    else:
        legacy_status_tokens = set(
            re.findall(r"[A-Z]+(?:-[A-Z]+)*", row[6].upper())
        )
        if (
            "BLOCKING" not in legacy_status_tokens
            or "NON-BLOCKING" in legacy_status_tokens
        ):
            errors.append(f"{label}: {case_id} must remain blocking")
    if require_executed and status_verdict not in {"PASS", "FAIL"}:
        errors.append(
            f"{label}: {case_id} used as reflection evidence must be executed with exactly one PASS or FAIL verdict"
        )
    if require_pass or expected_evidence is not None:
        evidence = row[5]
        if (
            not evidence
            or is_pending(evidence)
            or is_absent_evidence(evidence)
            or has_unresolved_placeholder(evidence)
        ):
            errors.append(f"{label}: completed {case_id} must bind resolved evidence")
        elif expected_evidence is not None and evidence != expected_evidence:
            errors.append(
                f"{label}: completed {case_id} Evidence must equal {expected_evidence}"
            )
    if require_pass:
        passed = (
            status_verdict == "PASS"
            if strict_status
            else "PASS" in legacy_status_tokens
            and "FAIL" not in legacy_status_tokens
            and "NOT-RUN" not in legacy_status_tokens
        )
        if not passed:
            errors.append(f"{label}: completed {case_id} must be PASS")
    joined = " ".join(row[1:5])
    for reference in required_references:
        if reference not in joined:
            errors.append(
                f"{label}: {case_id} must cite cumulative capability reference {reference}"
            )
    return errors


def expected_verification_case_evidence(
    result_identifier: str, case_id: str
) -> str:
    """Return immutable historical evidence or the normal Result anchor."""

    return IMMUTABLE_HISTORICAL_CASE_EVIDENCE.get(
        (result_identifier, case_id), f"{result_identifier}#{case_id}"
    )


def blocking_case_status_verdict(value: str) -> str | None:
    """Parse only the frozen blocking status grammar, not loose word tokens."""

    normalized = value.strip().strip("*_`").strip().upper()
    match = re.fullmatch(
        r"(PASS|FAIL|INVALID|NOT-RUN)\s*/\s*(?:READINESS\s+)?BLOCKING",
        normalized,
    )
    return match.group(1) if match is not None else None


def unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Build a JSON object while rejecting duplicate keys at every depth."""

    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def non_negative_metadata_integer(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value >= 0 else None
    if isinstance(value, str) and re.fullmatch(r"0|[1-9][0-9]*", value):
        return int(value)
    return None


def strict_codex_frozen_question_count(
    alignment: dict[str, object], case_id: object
) -> int | None:
    """Resolve the precommitted question count for a strict Codex comparison."""

    raw_count: object = None
    if case_id == "V-000":
        raw_count = alignment.get("held_out_question_count")
    else:
        alpha_binding = alignment.get("alpha_agent_comparison_binding")
        if (
            isinstance(alpha_binding, dict)
            and alpha_binding.get("case_id") == case_id
        ):
            raw_count = alpha_binding.get("question_count")
        else:
            early_binding = alignment.get("early_comparison_binding")
            if (
                isinstance(early_binding, dict)
                and early_binding.get("case_id") == case_id
            ):
                canary_case_id = early_binding.get("canary_case_id")
                canary_bindings = alignment.get("early_hidden_canary_bindings")
                if isinstance(canary_bindings, dict):
                    for canary in canary_bindings.values():
                        if (
                            isinstance(canary, dict)
                            and canary.get("case_id") == canary_case_id
                        ):
                            raw_count = canary.get("question_count")
                            break
    return (
        raw_count
        if type(raw_count) is int and raw_count >= 1
        else None
    )


def validate_positive_value_result(
    result: Document,
    alignment: dict[str, object],
    label: str,
    *,
    require_pass: bool = True,
    expected_case_id: str | None = None,
) -> list[str]:
    """Validate the measured value verdict against its precommitted threshold."""

    errors: list[str] = []
    strict_codex_baseline = requires_strict_codex_baseline(
        result.metadata.get("iteration", "")
    )
    value_verdict = result.metadata.get("positive_value_verdict")
    if require_pass and value_verdict != "PASS":
        errors.append(f"{label}: positive_value_verdict must equal PASS")
    elif not require_pass and value_verdict not in {"PASS", "FAIL"}:
        errors.append(
            f"{label}: positive_value_verdict must equal PASS or FAIL for an executed early comparison"
        )
    for result_field, manifest_field in (
        ("positive_value_metric", "positive_value_metric"),
        ("positive_value_unit", "positive_value_unit"),
        ("positive_value_comparison", "positive_value_comparison"),
        ("positive_value_threshold", "positive_value_threshold"),
        (
            "positive_value_reuse_horizon_questions",
            "positive_value_reuse_horizon_questions",
        ),
        (
            "mature_source_agent_cache_policy_digest",
            "mature_source_agent_cache_policy_digest",
        ),
        (
            "mature_source_agent_protocol_digest",
            "mature_source_agent_protocol_digest",
        ),
        (
            "mature_source_agent_rubric_digest",
            "mature_source_agent_rubric_digest",
        ),
        ("positive_value_protocol_digest", "positive_value_protocol_digest"),
        (
            "positive_value_freeze_receipt_ref",
            "positive_value_freeze_receipt_ref",
        ),
    ):
        if result.metadata.get(result_field) != alignment.get(manifest_field):
            errors.append(f"{label}: {result_field} must match the frozen Manifest")
    positive_value_case_id = result.metadata.get("positive_value_case_id")
    strict_quality_gate_met: bool | None = None
    if strict_codex_baseline:
        if result.metadata.get(
            "mature_source_agent_comparison"
        ) != STRICT_CODEX_RESULT_COMPARISON:
            errors.append(
                f"{label}: mature_source_agent_comparison must equal {STRICT_CODEX_RESULT_COMPARISON}"
            )
        absolute_verdict = result.metadata.get("system_absolute_quality_verdict")
        if absolute_verdict not in {"PASS", "FAIL"}:
            errors.append(
                f"{label}: system_absolute_quality_verdict must equal PASS or FAIL"
            )
        frozen_question_count = strict_codex_frozen_question_count(
            alignment, positive_value_case_id
        )
        if frozen_question_count is None:
            errors.append(
                f"{label}: strict comparison Case must resolve an exact frozen question count"
            )
        raw_evaluated_question_count = result.metadata.get(
            "evaluated_question_count"
        )
        evaluated_question_count = (
            raw_evaluated_question_count
            if type(raw_evaluated_question_count) is int
            and raw_evaluated_question_count >= 1
            else None
        )
        if evaluated_question_count is None:
            errors.append(
                f"{label}: evaluated_question_count must be a positive integer"
            )
        elif (
            frozen_question_count is not None
            and evaluated_question_count != frozen_question_count
        ):
            errors.append(
                f"{label}: evaluated_question_count must equal the frozen question count"
            )
        count_values: dict[str, int | None] = {}
        for field in (
            "system_better_question_count",
            "tie_question_count",
            "codex_better_question_count",
            "both_fail_question_count",
            "unresolved_or_invalid_question_count",
        ):
            raw_value = result.metadata.get(field)
            value = (
                raw_value
                if type(raw_value) is int and raw_value >= 0
                else None
            )
            count_values[field] = value
            if value is None:
                errors.append(f"{label}: {field} must be a non-negative integer")
        classification_count_matches = (
            evaluated_question_count is not None
            and all(value is not None for value in count_values.values())
            and sum(
                value for value in count_values.values() if value is not None
            )
            == evaluated_question_count
        )
        if not classification_count_matches:
            errors.append(
                f"{label}: five answer-quality classification counts must sum to evaluated_question_count"
            )
        strict_quality_gate_met = (
            absolute_verdict == "PASS"
            and frozen_question_count is not None
            and evaluated_question_count == frozen_question_count
            and classification_count_matches
            and count_values["system_better_question_count"] is not None
            and count_values["system_better_question_count"] >= 1
            and count_values["codex_better_question_count"] == 0
            and count_values["both_fail_question_count"] == 0
            and count_values["unresolved_or_invalid_question_count"] == 0
        )
        if require_pass and absolute_verdict != "PASS":
            errors.append(
                f"{label}: system_absolute_quality_verdict must equal PASS for a passing comparison"
            )
        if require_pass and count_values["system_better_question_count"] in {None, 0}:
            errors.append(
                f"{label}: system_better_question_count must be at least 1 so an all-tie comparison cannot pass"
            )
        for field in (
            "codex_better_question_count",
            "both_fail_question_count",
            "unresolved_or_invalid_question_count",
        ):
            if require_pass and count_values[field] not in {None, 0}:
                errors.append(f"{label}: {field} must equal 0 for PASS")
    raw_positive_value_actual = result.metadata.get("positive_value_actual")
    positive_value_actual = (
        raw_positive_value_actual
        if type(raw_positive_value_actual) is int
        and (strict_codex_baseline or raw_positive_value_actual >= 0)
        else None
    )
    if positive_value_actual is None:
        errors.append(
            f"{label}: positive_value_actual must be an exact integer"
            if strict_codex_baseline
            else f"{label}: positive_value_actual must be a non-negative integer"
        )
    else:
        threshold = alignment.get("positive_value_threshold")
        comparison = alignment.get("positive_value_comparison")
        threshold_met: bool | None = None
        if isinstance(threshold, int) and not isinstance(threshold, bool):
            threshold_met = (
                positive_value_actual <= threshold
                if comparison == "at-most"
                else positive_value_actual >= threshold
                if comparison == "at-least"
                else None
            )
        if strict_codex_baseline and threshold_met is not None:
            threshold_met = bool(threshold_met and strict_quality_gate_met)
        if require_pass and threshold_met is False:
            errors.append(
                f"{label}: answer quality must satisfy the positive frozen margin; the frozen comparison protocol separately forbids per-question regression"
                if strict_codex_baseline
                else f"{label}: positive_value_actual does not satisfy the frozen threshold"
            )
        elif not require_pass and threshold_met is not None:
            expected_verdict = "PASS" if threshold_met else "FAIL"
            if value_verdict != expected_verdict:
                errors.append(
                    f"{label}: positive_value_verdict must match the measured frozen threshold"
                )
    positive_value_report_digest = result.metadata.get(
        "positive_value_report_digest"
    )
    if not isinstance(positive_value_report_digest, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", positive_value_report_digest
    ) is None:
        errors.append(
            f"{label}: positive_value_report_digest must be an exact sha256 digest"
        )
    if (
        not isinstance(positive_value_case_id, str)
        or expected_case_id is not None
        and positive_value_case_id != expected_case_id
    ):
        errors.append(
            f"{label}: positive_value_case_id must match the executed value Case"
        )
    adjudication_owner = result.metadata.get(
        "positive_value_adjudication_owner"
    )
    if adjudication_owner != alignment.get("positive_value_adjudication_owner"):
        errors.append(
            f"{label}: positive_value_adjudication_owner must match the frozen Manifest"
        )
    if strict_codex_baseline:
        if result.metadata.get(
            "mature_source_agent_identity_digest"
        ) != alignment.get("mature_source_agent_identity_digest"):
            errors.append(
                f"{label}: mature_source_agent_identity_digest must match the frozen Manifest"
            )
    adjudication_receipt = result.metadata.get(
        "positive_value_adjudication_receipt_ref"
    )
    adjudication_receipt_pattern = (
        r"independent-evaluator-result:sha256:[0-9a-f]{64}"
        if strict_codex_baseline
        else r"codex-user-message:sha256:[0-9a-f]{64}"
    )
    if not isinstance(adjudication_receipt, str) or re.fullmatch(
        adjudication_receipt_pattern, adjudication_receipt
    ) is None:
        errors.append(
            f"{label}: positive_value_adjudication_receipt_ref must bind an exact "
            + (
                "independent-evaluator-result digest"
                if strict_codex_baseline
                else "independent adjudication message"
            )
        )
    elif adjudication_receipt == result.metadata.get(
        "positive_value_freeze_receipt_ref"
    ):
        errors.append(
            f"{label}: positive value adjudication must use a new receipt after the frozen protocol"
        )

    expected_report_ref = f"{result.identifier}#positive-value-report"
    if result.metadata.get("positive_value_report_ref") != expected_report_ref:
        errors.append(
            f"{label}: positive_value_report_ref must equal {expected_report_ref}"
        )
    report_heading_count = len(
        re.findall(
            r"(?m)^[ ]{0,3}##[ \t]+Positive value report[ \t]*#*[ \t]*$",
            result.body,
        )
    )
    if report_heading_count != 1:
        errors.append(
            f"{label}: Result must contain exactly one Positive value report section"
        )
    report_section = markdown_section_body(result, "Positive value report")
    report_data: dict[str, object] | None = None
    if not has_substantive_markdown_content(report_section):
        errors.append(
            f"{label}: Result must contain a substantive Positive value report section"
        )
    else:
        try:
            loaded_report = json.loads(
                report_section,
                object_pairs_hook=unique_json_object,
            )
        except (json.JSONDecodeError, ValueError) as error:
            errors.append(f"{label}: Positive value report must be exact JSON: {error}")
        else:
            if not isinstance(loaded_report, dict):
                errors.append(f"{label}: positive value report must be a JSON object")
            else:
                report_data = loaded_report
                computed_digest = "sha256:" + hashlib.sha256(
                    report_section.encode("utf-8")
                ).hexdigest()
                if positive_value_report_digest != computed_digest:
                    errors.append(
                        f"{label}: positive_value_report_digest must bind the exact Positive value report section"
                    )

    if report_data is not None:
        expected_report_fields: dict[str, object] = {
            "schema": (
                "software-world-model-positive-value-report/v2"
                if strict_codex_baseline
                else "software-world-model-positive-value-report/v1"
            ),
            "result_id": result.identifier,
            "verification_case_id": positive_value_case_id,
            "metric": result.metadata.get("positive_value_metric"),
            "unit": result.metadata.get("positive_value_unit"),
            "comparison": result.metadata.get("positive_value_comparison"),
            "threshold": result.metadata.get("positive_value_threshold"),
            "actual": result.metadata.get("positive_value_actual"),
            "reuse_horizon_questions": result.metadata.get(
                "positive_value_reuse_horizon_questions"
            ),
            "mature_source_agent_protocol_digest": result.metadata.get(
                "mature_source_agent_protocol_digest"
            ),
            "mature_source_agent_rubric_digest": result.metadata.get(
                "mature_source_agent_rubric_digest"
            ),
            "mature_source_agent_cache_policy_digest": result.metadata.get(
                "mature_source_agent_cache_policy_digest"
            ),
            "positive_value_protocol_digest": result.metadata.get(
                "positive_value_protocol_digest"
            ),
            "freeze_receipt_ref": result.metadata.get(
                "positive_value_freeze_receipt_ref"
            ),
            "adjudication_owner": adjudication_owner,
            "adjudication_receipt_ref": adjudication_receipt,
        }
        if strict_codex_baseline:
            expected_report_fields.update(
                {
                    "mature_source_agent_identity_digest": result.metadata.get(
                        "mature_source_agent_identity_digest"
                    ),
                    "system_absolute_quality_verdict": result.metadata.get(
                        "system_absolute_quality_verdict"
                    ),
                    "evaluated_question_count": result.metadata.get(
                        "evaluated_question_count"
                    ),
                    "system_better_question_count": result.metadata.get(
                        "system_better_question_count"
                    ),
                    "tie_question_count": result.metadata.get(
                        "tie_question_count"
                    ),
                    "codex_better_question_count": result.metadata.get(
                        "codex_better_question_count"
                    ),
                    "both_fail_question_count": result.metadata.get(
                        "both_fail_question_count"
                    ),
                    "unresolved_or_invalid_question_count": result.metadata.get(
                        "unresolved_or_invalid_question_count"
                    ),
                }
            )
        expected_report_field_names = {
            *expected_report_fields,
            "measurement_input_digest",
        }
        if set(report_data) != expected_report_field_names:
            errors.append(
                f"{label}: positive value report must use only the exact "
                f"{'v2' if strict_codex_baseline else 'v1'} schema fields"
            )
        integer_fields = ["actual", "threshold", "reuse_horizon_questions"]
        if strict_codex_baseline:
            integer_fields.extend(
                (
                    "system_better_question_count",
                    "evaluated_question_count",
                    "tie_question_count",
                    "codex_better_question_count",
                    "both_fail_question_count",
                    "unresolved_or_invalid_question_count",
                )
            )
        for integer_field in integer_fields:
            if type(report_data.get(integer_field)) is not int:
                errors.append(
                    f"{label}: positive value report {integer_field} must be an exact JSON integer"
                )
        for field, expected in expected_report_fields.items():
            if report_data.get(field) != expected:
                errors.append(
                    f"{label}: positive value report {field} must match its frozen input or Result"
                )
        measurement_input_digest = report_data.get("measurement_input_digest")
        if not isinstance(measurement_input_digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", measurement_input_digest
        ) is None:
            errors.append(
                f"{label}: positive value report must bind an exact measurement_input_digest"
            )
    return errors


def validate_experience_delivery_result(
    result: Document,
    experience_policy: dict[str, object],
    provider_policy: dict[str, object],
    *,
    require_success: bool,
) -> list[str]:
    """Audit the first Alpha timebox and transparent Provider attempts."""

    label = result.relative_path
    errors: list[str] = []
    for field, expected in (
        ("experience_delivery_policy_schema", experience_policy.get("schema")),
        ("experience_delivery_access_case_id", experience_policy.get("access_case_id")),
        (
            "experience_delivery_timebox_case_id",
            experience_policy.get("timebox_case_id"),
        ),
        (
            "experience_delivery_quality_case_id",
            experience_policy.get("quality_case_id"),
        ),
        ("provider_route_policy_schema", provider_policy.get("schema")),
    ):
        if result.metadata.get(field) != expected:
            errors.append(f"{label}: {field} must match the frozen Manifest policy")

    started_at = result.metadata.get("experience_timebox_started_at")
    if not isinstance(started_at, str) or re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[^\s]+(?:Z|[+-][0-9]{2}:[0-9]{2})",
        started_at,
    ) is None:
        errors.append(
            f"{label}: experience_timebox_started_at must be an ISO-8601 timestamp with timezone"
        )
    else:
        try:
            datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append(
                f"{label}: experience_timebox_started_at must be a real ISO-8601 timestamp"
            )

    elapsed_at_seal = non_negative_metadata_integer(
        result.metadata.get("experience_elapsed_minutes_at_result_seal")
    )
    if elapsed_at_seal is None:
        errors.append(
            f"{label}: experience_elapsed_minutes_at_result_seal must be a non-negative integer"
        )

    milestone_values: dict[str, int | None] = {}
    for field in (
        "page_launchable_elapsed_minutes",
        "sustained_user_operable_alpha_elapsed_minutes",
    ):
        raw_value = result.metadata.get(field)
        value = non_negative_metadata_integer(raw_value)
        if value is None and raw_value != "NOT_ACHIEVED":
            errors.append(
                f"{label}: {field} must be a non-negative integer or NOT_ACHIEVED"
            )
        milestone_values[field] = value

    delivery_verdict = result.metadata.get("experience_delivery_verdict")
    access_verdict = result.metadata.get("experience_access_gate_verdict")
    quality_verdict = result.metadata.get("experience_quality_gate_verdict")
    if delivery_verdict not in {"PASS", "FAIL"}:
        errors.append(f"{label}: experience_delivery_verdict must equal PASS or FAIL")
    if access_verdict not in {"PASS", "FAIL", "NOT_RUN"}:
        errors.append(
            f"{label}: experience_access_gate_verdict must equal PASS, FAIL or NOT_RUN"
        )
    if quality_verdict not in {"PASS", "FAIL", "NOT_RUN"}:
        errors.append(
            f"{label}: experience_quality_gate_verdict must equal PASS, FAIL or NOT_RUN"
        )

    page_elapsed = milestone_values.get("page_launchable_elapsed_minutes")
    alpha_elapsed = milestone_values.get(
        "sustained_user_operable_alpha_elapsed_minutes"
    )
    if delivery_verdict == "PASS" or require_success:
        if delivery_verdict != "PASS":
            errors.append(
                f"{label}: successful Alpha Result experience_delivery_verdict must equal PASS"
            )
        if page_elapsed is None or page_elapsed > 60:
            errors.append(
                f"{label}: successful Alpha Result must make the page launchable within 60 minutes"
            )
        if alpha_elapsed is None or alpha_elapsed > 180:
            errors.append(
                f"{label}: successful Alpha Result must be user-operable within 180 minutes"
            )
        if access_verdict != "PASS":
            errors.append(
                f"{label}: successful Alpha Result experience_access_gate_verdict must equal PASS"
            )
        if quality_verdict != "PASS":
            errors.append(
                f"{label}: successful Alpha Result experience_quality_gate_verdict must equal PASS before hardening"
            )

    hard_stop_triggered = result.metadata.get("experience_hard_stop_triggered")
    if not isinstance(hard_stop_triggered, bool):
        errors.append(f"{label}: experience_hard_stop_triggered must be a boolean")
    elif (
        elapsed_at_seal is not None
        and elapsed_at_seal >= 240
        and alpha_elapsed is None
        and not hard_stop_triggered
    ):
        errors.append(
            f"{label}: missing Alpha at 240 minutes must trigger the hard stop"
        )

    bounded_counts = (
        ("pre_first_experience_qualification_count", 1),
        ("pre_first_experience_smoke_question_count", 1),
        ("same_failure_signature_maximum_retry_count", 1),
        ("maximum_consecutive_no_user_visible_increment_count", 2),
        ("fallback_provider_attempt_count", 1),
    )
    for field, upper_bound in bounded_counts:
        value = non_negative_metadata_integer(result.metadata.get(field))
        if value is None or value > upper_bound:
            errors.append(
                f"{label}: {field} must be a non-negative integer no greater than {upper_bound}"
            )
    for field in (
        "pre_first_experience_full_regression_count",
        "external_dispatch_after_required_stop_count",
        "started_question_quality_chain_truncation_count",
        "same_provider_retry_count",
        "cross_attempt_intermediate_artifact_reuse_count",
        "user_resubmission_or_new_session_count",
        "late_primary_result_overwrite_count",
        "capability_failure_misclassified_as_unavailable_count",
        "application_source_security_failure_fallback_count",
    ):
        if non_negative_metadata_integer(result.metadata.get(field)) != 0:
            errors.append(f"{label}: {field} must equal zero")
    if non_negative_metadata_integer(result.metadata.get("live_attempt_count")) is None:
        errors.append(f"{label}: live_attempt_count must be a non-negative integer")

    provider_report_digest = result.metadata.get("provider_route_report_digest")
    if not isinstance(provider_report_digest, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", provider_report_digest
    ) is None:
        errors.append(
            f"{label}: provider_route_report_digest must be an exact sha256 digest"
        )
    if result.metadata.get("iteration") == "ITER-010":
        errors.extend(
            validate_iter010_direction_checkpoint_result(
                result,
                experience_policy,
                require_success=require_success,
            )
        )
    return errors


def validate_iter010_direction_checkpoint_result(
    result: Document,
    experience_policy: dict[str, object],
    *,
    require_success: bool,
) -> list[str]:
    """Audit ITER-010 checkpoint handoffs without turning them into new stages."""

    label = result.relative_path
    errors: list[str] = []
    handoff_count = non_negative_metadata_integer(
        result.metadata.get("experience_checkpoint_handoff_count")
    )
    if handoff_count is None or not 1 <= handoff_count <= 4:
        errors.append(
            f"{label}: experience_checkpoint_handoff_count must be between one and four"
        )
    report_digest = result.metadata.get("experience_checkpoint_handoff_report_digest")
    if not isinstance(report_digest, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", report_digest
    ) is None:
        errors.append(
            f"{label}: experience_checkpoint_handoff_report_digest must be an exact sha256 digest"
        )
    completed_turns = non_negative_metadata_integer(
        result.metadata.get("completed_live_canary_turn_count")
    )
    if completed_turns is None or completed_turns > 5:
        errors.append(
            f"{label}: completed_live_canary_turn_count must be between zero and five"
        )

    milestone_values: dict[str, int | None] = {}
    for field in (
        "direction_evidence_handoff_elapsed_minutes",
        "direction_decision_elapsed_minutes",
    ):
        raw_value = result.metadata.get(field)
        value = non_negative_metadata_integer(raw_value)
        if value is None and raw_value != "NOT_ACHIEVED":
            errors.append(
                f"{label}: {field} must be a non-negative integer or NOT_ACHIEVED"
            )
        milestone_values[field] = value

    alpha_elapsed = non_negative_metadata_integer(
        result.metadata.get("sustained_user_operable_alpha_elapsed_minutes")
    )
    evidence_elapsed = milestone_values["direction_evidence_handoff_elapsed_minutes"]
    decision_elapsed = milestone_values["direction_decision_elapsed_minutes"]
    evidence_deadline = non_negative_metadata_integer(
        experience_policy.get("direction_evidence_handoff_deadline_minutes")
    )
    decision_deadline = non_negative_metadata_integer(
        experience_policy.get("direction_decision_deadline_minutes")
    )
    alpha_on_time = alpha_elapsed is not None and alpha_elapsed <= 180
    evidence_on_time = (
        evidence_deadline is not None
        and evidence_elapsed is not None
        and evidence_elapsed <= evidence_deadline
    )
    decision_on_time = (
        decision_deadline is not None
        and decision_elapsed is not None
        and decision_elapsed <= decision_deadline
    )
    if alpha_elapsed is not None and completed_turns is not None and completed_turns < 3:
        errors.append(
            f"{label}: delivered direction Alpha requires at least three completed live canary Turns"
        )
    if evidence_elapsed is not None:
        if handoff_count is not None and handoff_count < 3:
            errors.append(
                f"{label}: direction evidence requires at least three checkpoint handoffs"
            )
        if completed_turns != 5:
            errors.append(
                f"{label}: completed_live_canary_turn_count must equal five when direction evidence is handed off"
            )
        if alpha_elapsed is None or evidence_elapsed < alpha_elapsed:
            errors.append(
                f"{label}: direction evidence handoff cannot precede the direction Alpha"
            )
    if decision_elapsed is not None:
        if handoff_count != 4:
            errors.append(
                f"{label}: direction decision requires all four checkpoint handoffs"
            )
        if evidence_elapsed is None or decision_elapsed < evidence_elapsed:
            errors.append(
                f"{label}: direction decision cannot precede the direction evidence handoff"
            )
    elapsed_at_seal = non_negative_metadata_integer(
        result.metadata.get("experience_elapsed_minutes_at_result_seal")
    )
    for field, value in milestone_values.items():
        if (
            value is not None
            and elapsed_at_seal is not None
            and value > elapsed_at_seal
        ):
            errors.append(f"{label}: {field} cannot occur after Result seal")

    if not alpha_on_time:
        if (
            result.metadata.get("experience_delivery_verdict") != "FAIL"
            or evidence_elapsed is not None
            or decision_elapsed is not None
            or (handoff_count is not None and handoff_count > 2)
            or (completed_turns is not None and completed_turns > 3)
        ):
            errors.append(
                f"{label}: a missing or late direction Alpha must fail and stop before direction evidence or decision work"
            )
        if (
            elapsed_at_seal is not None
            and elapsed_at_seal >= 240
            and result.metadata.get("experience_hard_stop_triggered") is not True
        ):
            errors.append(
                f"{label}: a missing or late direction Alpha must trigger the absolute stop at 240 minutes"
            )
    if not evidence_on_time and (
        decision_elapsed is not None
        or (handoff_count is not None and handoff_count > 3)
    ):
        errors.append(
            f"{label}: missing or late direction evidence must stop before direction decision work"
        )

    claimed_continue = result.metadata.get("reflection_decision") == "CONTINUE"
    if completed_turns is not None and completed_turns < 5 and (
        result.metadata.get("experience_delivery_verdict") == "PASS"
        or result.metadata.get("experience_quality_gate_verdict") == "PASS"
    ):
        errors.append(
            f"{label}: an incomplete five-Turn canary cannot claim delivery or quality PASS"
        )
    if claimed_continue and not (
        alpha_on_time
        and evidence_on_time
        and decision_on_time
        and completed_turns == 5
        and handoff_count == 4
    ):
        errors.append(
            f"{label}: an incomplete or late direction path cannot claim PASS or CONTINUE"
        )

    if require_success:
        if (
            evidence_deadline is None
            or evidence_elapsed is None
            or evidence_elapsed > evidence_deadline
        ):
            errors.append(
                f"{label}: successful ITER-010 Result must hand off direction evidence within 360 minutes"
            )
        if (
            decision_deadline is None
            or decision_elapsed is None
            or decision_elapsed > decision_deadline
        ):
            errors.append(
                f"{label}: successful ITER-010 Result must hand off the direction decision within 480 minutes"
            )
        if handoff_count != 4:
            errors.append(
                f"{label}: successful ITER-010 Result requires four checkpoint handoffs"
            )
        if (
            result.metadata.get("reflection_gate_case_id")
            != experience_policy.get("direction_confirmation_case_id")
            or result.metadata.get("reflection_gate_status") != "PASS"
            or result.metadata.get("reflection_decision") != "CONTINUE"
            or result.metadata.get("reflection_decision_owner") != "user"
        ):
            errors.append(
                f"{label}: successful ITER-010 Result requires a PASS direction Gate and user CONTINUE decision"
            )
        decision_ref = result.metadata.get("reflection_decision_ref")
        if not isinstance(decision_ref, str) or re.fullmatch(
            r"codex-user-message:sha256:[0-9a-f]{64}", decision_ref
        ) is None:
            errors.append(
                f"{label}: successful ITER-010 Result must bind the exact user CONTINUE receipt"
            )
    return errors


def validate_product_goal_result(
    result: Document,
    iteration: str,
    manifest_path: Path,
    verification: Document,
    by_id: dict[str, Document] | None = None,
) -> list[str]:
    label = result.relative_path
    errors: list[str] = []
    expected_result_prefix = (
        f"docs/project/iterations/iteration-{iteration.removeprefix('ITER-')}/results/"
    )
    if not label.startswith(expected_result_prefix) or "/" in label.removeprefix(
        expected_result_prefix
    ):
        errors.append(f"{label}: product-goal Result must be in this iteration's results directory")
    if result.metadata.get("kind") != "iteration-result":
        errors.append(f"{label}: product-goal Result kind must be iteration-result")
    if result.metadata.get("status") != "product-goal-pass":
        errors.append(f"{label}: product-goal PASS Result status must be product-goal-pass")
    if result.metadata.get("authority") != "execution-evidence":
        errors.append(f"{label}: product-goal PASS Result authority must be execution-evidence")
    owners = result.metadata.get("owners", [])
    if not isinstance(owners, list) or "quality" not in owners:
        errors.append(f"{label}: product-goal PASS Result must be owned by quality")

    product_goal_metadata, _, _, _ = product_goal_v000_contract(iteration)
    for field, expected in {
        **product_goal_metadata,
        "product_goal_verdict": "PASS",
    }.items():
        if result.metadata.get(field) != expected:
            errors.append(f"{label}: {field} must equal {expected}")
    for field in ("product_goal_subject_digest", "product_goal_report_digest"):
        value = result.metadata.get(field)
        if not isinstance(value, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", value
        ) is None:
            errors.append(f"{label}: {field} must be an exact sha256 digest")

    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = safe_load_manifest(manifest_text)
    except (OSError, UnicodeError, SafeYamlError) as error:
        return errors + [f"{label}: cannot load product-goal Manifest: {error}"]
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return errors + [f"{label}: Manifest has no product_goal_alignment"]
    answer_protocol = manifest.get("answer_protocol")
    engineering_qa_result = requires_engineering_qa_hybrid(iteration) or (
        isinstance(answer_protocol, dict)
        and is_engineering_qa_adaptive_protocol(answer_protocol)
    )
    if engineering_qa_result:
        for field in (
            "authorized_source_retrieval_count",
            "authorized_source_retrieval_bytes",
        ):
            value = non_negative_metadata_integer(result.metadata.get(field))
            if value is None or value < 1:
                errors.append(f"{label}: {field} must be a positive integer")
        for field in (
            "answer_direct_source_access_count",
            "reviewer_direct_source_access_count",
            "repository_write_count",
            "silent_mode_fallback_count",
        ):
            value = non_negative_metadata_integer(result.metadata.get(field))
            if value != 0:
                errors.append(f"{label}: {field} must equal zero")
        package_digest = result.metadata.get(
            "question_evidence_package_manifest_digest"
        )
        if not isinstance(package_digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", package_digest
        ) is None:
            errors.append(
                f"{label}: question_evidence_package_manifest_digest must be an exact sha256 digest"
            )

    completed_case_ids = manifest_resolved_sequence_items(
        manifest_text, "product_goal_alignment", "blocking_case_ids"
    ) or []
    for case_id in completed_case_ids:
        errors.extend(
            validate_blocking_verification_case(
                verification,
                case_id,
                require_pass=True,
            )
        )

    new_slice_refs = manifest_resolved_sequence_items(
        manifest_text, "product_goal_alignment", "new_capability_slice_refs"
    ) or []
    development = manifest.get("development")
    development_slices = (
        development.get("slices") if isinstance(development, dict) else None
    )
    if not isinstance(development_slices, dict):
        development_slices = {}
    slice_result_refs: list[str] = []
    for slice_ref in new_slice_refs:
        manifest_slice = development_slices.get(slice_ref)
        slice_result_ref = (
            manifest_slice.get("result") if isinstance(manifest_slice, dict) else None
        )
        if (
            not isinstance(slice_result_ref, str)
            or is_pending(slice_result_ref)
            or is_absent_evidence(slice_result_ref)
            or has_unresolved_placeholder(slice_result_ref)
        ):
            errors.append(
                f"{label}: completed product Result requires a resolved Slice Result for {slice_ref}"
            )
            continue
        slice_result_refs.append(slice_result_ref)
        if by_id is not None:
            slice_document = by_id.get(slice_ref)
            slice_result = by_id.get(slice_result_ref)
            if slice_document is None or slice_result is None:
                errors.append(
                    f"{label}: completed product Result must aggregate existing Slice and Slice Result {slice_ref}"
                )
                continue
            case_ids = slice_document.metadata.get(
                "product_goal_slice_gate_case_ids", []
            )
            if not isinstance(case_ids, list):
                case_ids = []
            for case_id in case_ids:
                errors.extend(
                    validate_blocking_verification_case(
                        verification,
                        str(case_id),
                        require_pass=True,
                        expected_evidence=f"{slice_result_ref}#{case_id}",
                    )
                )

    for field in PRODUCT_GOAL_RESULT_DIGEST_FIELDS:
        if result.metadata.get(field) != alignment.get(field):
            errors.append(f"{label}: {field} must match the frozen Manifest")

    counts: dict[str, int] = {}
    for field in PRODUCT_GOAL_RESULT_COUNT_FIELDS:
        value = non_negative_metadata_integer(result.metadata.get(field))
        if value is None:
            errors.append(f"{label}: {field} must be a non-negative integer")
        else:
            counts[field] = value
    for result_field, manifest_field in (
        ("held_out_question_count", "held_out_question_count"),
        ("held_out_baseline_supported_count", "held_out_baseline_supported_count"),
    ):
        if result_field in counts and counts[result_field] != alignment.get(manifest_field):
            errors.append(f"{label}: {result_field} must match the frozen Manifest")
    actual = counts.get("held_out_actual_supported_count")
    answerable = alignment.get("held_out_answerable_question_count")
    target = alignment.get("held_out_target_supported_count")
    if (
        actual is not None
        and isinstance(answerable, int)
        and isinstance(target, int)
        and not (target <= actual <= answerable)
    ):
        errors.append(
            f"{label}: held_out_actual_supported_count must reach target without exceeding answerable count"
        )
    boundary_correct = counts.get("held_out_boundary_correct_gap_count")
    if boundary_correct != alignment.get("held_out_boundary_question_count"):
        errors.append(
            f"{label}: held_out_boundary_correct_gap_count must equal the frozen boundary count"
        )
    no_symbol_supported = counts.get(
        "held_out_answerable_without_symbol_supported_count"
    )
    no_symbol_minimum = alignment.get(
        "held_out_answerable_without_symbol_count_minimum"
    )
    if (
        not isinstance(no_symbol_supported, int)
        or not isinstance(no_symbol_minimum, int)
        or no_symbol_supported < no_symbol_minimum
    ):
        errors.append(
            f"{label}: held_out_answerable_without_symbol_supported_count must reach the frozen minimum"
        )
    live_no_symbol_pass = counts.get("live_ad_hoc_without_symbol_pass_count")
    live_no_symbol_minimum = alignment.get(
        "live_ad_hoc_without_symbol_count_minimum"
    )
    if (
        not isinstance(live_no_symbol_pass, int)
        or not isinstance(live_no_symbol_minimum, int)
        or live_no_symbol_pass < live_no_symbol_minimum
    ):
        errors.append(
            f"{label}: live_ad_hoc_without_symbol_pass_count must reach the frozen minimum"
        )
    for field in (
        "major_error_count",
        "source_fallback_count",
        "update_fallback_count",
        "direct_fallback_count",
    ):
        if counts.get(field) != 0:
            errors.append(f"{label}: {field} must equal zero")
    for result_field, manifest_field in (
        ("cross_domain_pass_count", "cross_domain_case_count"),
        ("live_ad_hoc_pass_count", "live_ad_hoc_question_count"),
    ):
        minimum = alignment.get(manifest_field)
        if (
            result_field in counts
            and isinstance(minimum, int)
            and counts[result_field] != minimum
        ):
            errors.append(f"{label}: {result_field} must equal the frozen Manifest count")
    expected_agent_comparison = (
        STRICT_CODEX_RESULT_COMPARISON
        if requires_strict_codex_baseline(iteration)
        else "non-regression"
    )
    if result.metadata.get("mature_source_agent_comparison") != expected_agent_comparison:
        errors.append(
            f"{label}: mature_source_agent_comparison must equal {expected_agent_comparison}"
        )
    if requires_reflection_gate(iteration):
        errors.extend(
            validate_positive_value_result(
                result,
                alignment,
                label,
                expected_case_id="V-000",
            )
        )
        adjudication_forbidden_refs: set[str] = set()
        top_authorization = manifest.get("authorization")
        if isinstance(top_authorization, dict):
            top_authorization_ref = top_authorization.get("authorization_ref")
            if isinstance(top_authorization_ref, str):
                adjudication_forbidden_refs.add(top_authorization_ref)
        for manifest_slice in development_slices.values():
            if isinstance(manifest_slice, dict):
                authorization_ref = manifest_slice.get("authorization_ref")
                if isinstance(authorization_ref, str):
                    adjudication_forbidden_refs.add(authorization_ref)
        if by_id is not None:
            for prior_slice_result_ref in slice_result_refs:
                prior_slice_result = by_id.get(prior_slice_result_ref)
                prior_decision_ref = (
                    prior_slice_result.metadata.get("reflection_decision_ref")
                    if prior_slice_result is not None
                    else None
                )
                if isinstance(prior_decision_ref, str):
                    adjudication_forbidden_refs.add(prior_decision_ref)
                prior_adjudication_ref = (
                    prior_slice_result.metadata.get(
                        "positive_value_adjudication_receipt_ref"
                    )
                    if prior_slice_result is not None
                    else None
                )
                if isinstance(prior_adjudication_ref, str):
                    adjudication_forbidden_refs.add(prior_adjudication_ref)
        if result.metadata.get(
            "positive_value_adjudication_receipt_ref"
        ) in adjudication_forbidden_refs:
            errors.append(
                f"{label}: final positive value adjudication must use a new message after all authorizations and prior Slice decisions"
            )
    if result.metadata.get("product_web_manual_verification") != "passed":
        errors.append(f"{label}: product_web_manual_verification must equal passed")

    dependencies = result.metadata.get("depends_on", [])
    required_dependencies = [
        verification.identifier,
        *new_slice_refs,
        *slice_result_refs,
    ]
    if not isinstance(dependencies, list):
        dependencies = []
    for reference in required_dependencies:
        if reference not in dependencies:
            errors.append(f"{label}: product-goal Result must depend on {reference}")
    for section in empty_required_sections(
        result, PRODUCT_GOAL_RESULT_REQUIRED_SECTIONS
    ):
        errors.append(f"{label}: product-goal Result section is missing or empty: {section}")
    return errors


def validate_product_goal_v000(
    verification: Document | None,
    iteration: str,
    *,
    require_pass: bool = False,
    by_id: dict[str, Document] | None = None,
) -> list[str]:
    if not requires_product_goal_alignment(iteration):
        return []
    if verification is None:
        return [f"{iteration}: selected iteration is missing verification-matrix.md"]

    label = verification.relative_path
    (
        product_goal_metadata,
        product_goal_claim,
        product_goal_frozen_input,
        product_goal_expected,
    ) = product_goal_v000_contract(iteration)
    for field, expected in product_goal_metadata.items():
        if verification.metadata.get(field) != expected:
            errors = [
                f"{label}: {field} must equal {expected} for the V-000 product gate"
            ]
            return errors
    rows = markdown_table_case_rows(verification.body, "V-000")
    if len(rows) != 1:
        return [f"{label}: must define exactly one V-000 row"]
    row = rows[0]
    if len(row) != 7:
        return [f"{label}: V-000 must use the exact seven-column verification schema"]

    errors: list[str] = []
    frozen_input = product_goal_frozen_input
    expected_outcome = product_goal_expected
    if (
        requires_reflection_gate(iteration)
        and not requires_engineering_qa_hybrid(iteration)
        and not requires_strict_codex_baseline(iteration)
    ):
        frozen_input += "；预提交差异化价值阈值"
        expected_outcome = (
            "支持率提高；重大错误为 0；逐题完整性不退步；差异化价值阈值 PASS；"
            "提问时 Source/Update/Direct fallback=0；同一正式 Web 可人工验证"
        )
    expected_contract = (
        product_goal_claim,
        PRODUCT_GOAL_V000_LEVEL,
        frozen_input,
        expected_outcome,
    )
    for index, (field, expected) in enumerate(
        zip(
            ("claim", "level", "frozen input / oracle", "expected"),
            expected_contract,
        ),
        start=1,
    ):
        if row[index] != expected:
            errors.append(
                f"{label}: V-000 {field} must match the product-goal contract"
            )

    strict_status = requires_reflection_gate(iteration)
    status_verdict = blocking_case_status_verdict(row[6])
    legacy_status_tokens: set[str] = set()
    if strict_status:
        if status_verdict is None:
            errors.append(
                f"{label}: V-000 status must remain blocking and use exact PASS, FAIL, INVALID or NOT-RUN / blocking grammar"
            )
    else:
        legacy_status_tokens = set(
            re.findall(r"[A-Z]+(?:-[A-Z]+)*", row[6].upper())
        )
        if (
            "BLOCKING" not in legacy_status_tokens
            or "NON-BLOCKING" in legacy_status_tokens
        ):
            errors.append(f"{label}: V-000 status must remain blocking")

    if require_pass:
        evidence = row[5]
        if (
            not evidence
            or is_pending(evidence)
            or is_absent_evidence(evidence)
            or has_unresolved_placeholder(evidence)
        ):
            errors.append(f"{label}: completed V-000 must bind resolved evidence")
        passed = (
            status_verdict == "PASS"
            if strict_status
            else "PASS" in legacy_status_tokens
            and "FAIL" not in legacy_status_tokens
            and "NOT-RUN" not in legacy_status_tokens
        )
        if not passed:
            errors.append(f"{label}: completed iteration requires V-000 PASS")
        result_id = verification.metadata.get("product_goal_result_id")
        if (
            not isinstance(result_id, str)
            or is_pending(result_id)
            or is_absent_evidence(result_id)
            or has_unresolved_placeholder(result_id)
        ):
            errors.append(f"{label}: completed V-000 must bind product_goal_result_id")
        elif by_id is not None:
            result = by_id.get(result_id)
            if (
                result is None
                or result.metadata.get("kind") != "iteration-result"
                or str(result.metadata.get("iteration", "")) != iteration
                or result.metadata.get("product_goal_gate") != "V-000"
                or result.metadata.get("product_goal_outcome")
                != product_goal_metadata["product_goal_outcome"]
                or result.metadata.get("product_goal_evaluation")
                != "independent-hidden-plus-live-ad-hoc"
                or result.metadata.get("product_goal_verdict") != "PASS"
            ):
                errors.append(
                    f"{label}: product_goal_result_id must reference a same-iteration PASS product result"
                )
            else:
                if evidence != result_id:
                    errors.append(
                        f"{label}: completed V-000 Evidence must equal product_goal_result_id"
                    )
                errors.extend(
                    validate_product_goal_result(
                        result,
                        iteration,
                        verification.path.parent / "manifest.yaml",
                        verification,
                        by_id,
                    )
                )
    return errors


def validate_goal_aligned_required_document(document: Document) -> list[str]:
    errors: list[str] = []
    if not has_substantive_body(document):
        errors.append(
            f"{document.relative_path}: selected iteration document has no substantive body"
        )
    if (
        has_unresolved_placeholder(document.metadata)
        or has_pending_marker(document.metadata)
        or has_unresolved_placeholder(document.body)
    ):
        errors.append(
            f"{document.relative_path}: selected iteration document contains unresolved template placeholders"
        )
    for section in empty_active_required_sections(document):
        errors.append(
            f"{document.relative_path}: selected iteration section is missing or empty: {section}"
        )
    return errors


def validate_product_goal_readiness_authorization(
    readiness: Document,
) -> list[str]:
    errors: list[str] = []
    for field in ("authorized_by", "authorized_at"):
        value = readiness.metadata.get(field, "")
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(f"{readiness.relative_path}: selected iteration {field} is unresolved")
    authorized_at = readiness.metadata.get("authorized_at", "")
    if isinstance(authorized_at, str) and re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|[+-][0-9]{2}:[0-9]{2})",
        authorized_at,
    ) is None:
        errors.append(
            f"{readiness.relative_path}: authorized_at must be an ISO-8601 timestamp with timezone"
        )
    elif isinstance(authorized_at, str):
        try:
            datetime.fromisoformat(authorized_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append(
                f"{readiness.relative_path}: authorized_at must be a real ISO-8601 timestamp"
            )
    for field, expected in (
        ("product_goal_alignment_verdict", "accepted"),
        ("product_goal_alignment_reviewed_by", "user"),
    ):
        if readiness.metadata.get(field) != expected:
            errors.append(f"{readiness.relative_path}: {field} must equal {expected}")
    review_ref = readiness.metadata.get("product_goal_alignment_review_ref", "")
    if not isinstance(review_ref, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", review_ref
    ) is None:
        errors.append(
            f"{readiness.relative_path}: product_goal_alignment_review_ref must bind an exact user message digest"
        )
    return errors


def validate_active_manifest(
    path: Path,
    iteration: str,
    *,
    allowed_statuses: set[str] | None = None,
    expected_status: str | None = None,
    allow_unresolved_planning: bool = False,
) -> list[str]:
    label = _path_label(path)
    try:
        manifest_text = path.read_text(encoding="utf-8")
        manifest = safe_load_manifest(manifest_text)
    except (OSError, UnicodeError, SafeYamlError) as error:
        return [f"{label}: invalid safe YAML: {error}"]

    errors: list[str] = []
    iteration_data = manifest.get("iteration")
    if not isinstance(iteration_data, dict):
        errors.append(f"{label}: iteration must be a mapping")
    else:
        manifest_iteration = iteration_data.get("id")
        if not isinstance(manifest_iteration, str) or manifest_iteration != iteration:
            errors.append(f"{label}: iteration.id must equal active iteration {iteration}")
        manifest_status = iteration_data.get("status")
        valid_statuses = ACTIVE_ITERATION_STATUSES if allowed_statuses is None else allowed_statuses
        if not isinstance(manifest_status, str) or manifest_status not in valid_statuses:
            errors.append(
                f"{label}: iteration.status must be one of "
                + ", ".join(sorted(valid_statuses))
            )
        elif expected_status is not None and manifest_status != expected_status:
            errors.append(
                f"{label}: iteration.status must match the iteration index status {expected_status}"
            )

    baseline = manifest.get("baseline")
    if not isinstance(baseline, dict):
        errors.append(f"{label}: baseline must be a mapping")
    else:
        commit = baseline.get("commit")
        if not isinstance(commit, str) or HEX_COMMIT_RE.fullmatch(commit) is None:
            errors.append(
                f"{label}: baseline.commit must be an exact 40-character lowercase Git commit"
            )

    errors.extend(
        validate_product_goal_alignment_manifest(
            manifest, manifest_text, label, iteration
        )
    )
    if iteration == "ITER-010" and uses_legacy_iter010_plan(manifest):
        transition_results, transition_evidence, transition_result_errors = (
            _load_iter010_required_transition_results(manifest, path, label)
        )
        errors.extend(transition_result_errors)
        errors.extend(
            validate_iter010_plan_execution_snapshot(
                manifest,
                label,
                manifest_text=manifest_text,
                transition_results=transition_results,
                transition_evidence_artifacts=transition_evidence,
            )
        )

    if not allow_unresolved_planning and (
        has_unresolved_placeholder(manifest_text)
        or has_pending_marker(manifest)
        or MANIFEST_PENDING_RE.search(manifest_text)
    ):
        errors.append(f"{label}: contains unresolved template placeholders")
    return errors


def _execution_manifest_sequence(
    *,
    manifest: dict[str, object],
    manifest_text: str | None,
    section: str,
    field: str,
) -> list[str]:
    """Resolve a scalar sequence for the execution-readiness gate.

    ``safe_load_manifest`` deliberately validates block sequences without
    materializing their values.  File-backed validation therefore resolves
    those values from the already validated inert text, while unit callers may
    continue to provide an ordinary in-memory list.
    """

    section_value = manifest.get(section)
    if isinstance(section_value, dict):
        direct = section_value.get(field)
        if isinstance(direct, list):
            return [str(item) for item in direct]
    if manifest_text is None:
        return []
    return manifest_resolved_sequence_items(manifest_text, section, field) or []


def canonical_fileset_digest(
    schema: str,
    paths: list[str],
    *,
    repository: Path | None = None,
) -> str:
    """Digest a canonical, repository-relative ordered fileset."""

    root = REPOSITORY if repository is None else repository
    entries: list[dict[str, object]] = []
    for relative in paths:
        payload = (root / relative).read_bytes()
        entries.append(
            {
                "path": relative,
                "size": len(payload),
                "sha256": "sha256:" + hashlib.sha256(payload).hexdigest(),
            }
        )
    encoded = json.dumps(
        {"schema": schema, "entries": entries},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def canonical_raw_component_set_digest(
    paths: tuple[Path, ...],
) -> str:
    """Match a protocol that binds an ordered list of raw component digests."""

    raw_digests = [
        "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    ]
    encoded = json.dumps(
        raw_digests,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def canonical_mapping_digest(
    schema: str, field: str, value: dict[str, object]
) -> str:
    """Bind a frozen manifest mapping without relying on YAML presentation."""

    encoded = json.dumps(
        {"schema": schema, field: value},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def validate_exact_mapping_keys(
    value: dict[str, object], expected: set[str], label: str
) -> list[str]:
    """Fail closed when a frozen protocol silently drops or invents fields."""

    errors: list[str] = []
    missing = sorted(expected.difference(value))
    extra = sorted(set(value).difference(expected))
    if missing:
        errors.append(f"{label}: missing exact fields: {', '.join(missing)}")
    if extra:
        errors.append(f"{label}: unexpected fields: {', '.join(extra)}")
    return errors


def validate_engineering_qa_question_evidence_package_classes(
    package_classes: dict[str, object], label: str
) -> list[str]:
    """Separate affirmative support from retained boundary and audit evidence."""

    section_label = f"{label}: question_evidence_package_classes"
    errors = validate_exact_mapping_keys(
        package_classes,
        {
            "support_and_citation",
            "retained_non_support",
            "single_package_identity",
            "seal_confers_truth",
            "status",
        },
        section_label,
    )
    support = package_classes.get("support_and_citation")
    retained = package_classes.get("retained_non_support")
    if not isinstance(support, dict):
        errors.append(f"{section_label}.support_and_citation must be a mapping")
    else:
        errors.extend(
            validate_exact_mapping_keys(
                support,
                {
                    "admission",
                    "affirmative_claim_support_allowed",
                    "claim_citation_allowed",
                },
                f"{section_label}.support_and_citation",
            )
        )
        expected_support: dict[str, object] = {
            "admission": "modality-context-coverage-and-support-validated-only",
            "affirmative_claim_support_allowed": True,
            "claim_citation_allowed": True,
        }
        for field, expected in expected_support.items():
            if support.get(field) != expected:
                errors.append(
                    f"{section_label}.support_and_citation.{field} must equal {expected}"
                )
    if not isinstance(retained, dict):
        errors.append(f"{section_label}.retained_non_support must be a mapping")
    else:
        errors.extend(
            validate_exact_mapping_keys(
                retained,
                {
                    "required_entry_kinds",
                    "retention",
                    "affirmative_claim_support_allowed",
                    "affirmative_claim_citation_allowed",
                    "labeled_boundary_or_audit_reference_allowed",
                },
                f"{section_label}.retained_non_support",
            )
        )
        expected_retained: dict[str, object] = {
            "required_entry_kinds": (
                "boundary,audit-gap,failure,partial,conflict,unknown,"
                "rejected-decision-and-resource-receipt"
            ),
            "retention": "mandatory-in-ledger-and-current-sealed-package",
            "affirmative_claim_support_allowed": False,
            "affirmative_claim_citation_allowed": False,
            "labeled_boundary_or_audit_reference_allowed": True,
        }
        for field, expected in expected_retained.items():
            if retained.get(field) != expected:
                errors.append(
                    f"{section_label}.retained_non_support.{field} must equal {expected}"
                )
    for field, expected in (
        ("single_package_identity", True),
        ("seal_confers_truth", False),
        ("status", "frozen"),
    ):
        if package_classes.get(field) != expected:
            errors.append(f"{section_label}.{field} must equal {expected}")
    return errors


def engineering_qa_hardening_slice_ref(manifest: dict[str, object]) -> str | None:
    """Resolve the first engineering-hardening Slice after all feedback checkpoints."""

    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(slices, dict) or not isinstance(alignment, dict):
        return None
    refs = [str(reference) for reference in slices]
    preview_binding = alignment.get("direction_preview_binding")
    preview_ref = (
        preview_binding.get("new_slice_ref")
        if isinstance(preview_binding, dict)
        else None
    )
    checkpoint = resolved_alpha_direction_slice_ref(alignment, refs) or preview_ref
    if checkpoint not in refs:
        return None
    index = refs.index(checkpoint)
    return refs[index + 1] if index + 1 < len(refs) else None


def engineering_qa_hardening_has_started(manifest: dict[str, object]) -> bool:
    """Return true only when the resolved hardening Slice has started."""

    hardening_ref = engineering_qa_hardening_slice_ref(manifest)
    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    hardening = slices.get(hardening_ref) if isinstance(slices, dict) else None
    return not isinstance(hardening, dict) or hardening.get("status") != "proposed"


def _engineering_qa_new_freeze_receipt_errors(
    value: object,
    alignment: dict[str, object],
    field_label: str,
    *,
    hardening_authorization_ref: object,
    hardening_ref: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(value, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", value
    ) is None:
        errors.append(f"{field_label} must bind an exact new user freeze receipt")
    elif value == alignment.get("positive_value_freeze_receipt_ref"):
        errors.append(
            f"{field_label} must not reuse positive_value_freeze_receipt_ref"
        )
    if value != hardening_authorization_ref:
        authorization_label = (
            "the current Slice 002"
            if hardening_ref == "ITER-010-SLICE-002"
            else hardening_ref
        )
        errors.append(
            f"{field_label} must equal {authorization_label} authorization_ref"
        )
    return errors


def validate_engineering_qa_reviewer_verification_investigation(
    verification: dict[str, object],
    answer_protocol: dict[str, object],
    alignment: dict[str, object],
    label: str,
    *,
    hardening_started: bool,
    hardening_authorization_ref: object,
    hardening_ref: str = "ITER-010-SLICE-002",
) -> list[str]:
    """Freeze an independent multi-step reviewer verification investigation."""

    section_label = f"{label}: reviewer_verification_investigation"
    expected_keys = {
        "role",
        "context",
        "inputs",
        "reviewer_operation_proposal_allowed",
        "adaptive_multi_step_required",
        "prior_verification_result_must_drive_next_step",
        "application_source_broker_worker_route_required",
        "direct_source_filesystem_shell_network_credential_or_tool_access",
        "returns_to_initial_investigation_model",
        "creates_new_ledger_revision_package_answer_and_review",
        "slice_001_preview_upper_bound",
        "slice_001_bound_scope",
        "hardening_fixed_round_upper_bound_allowed",
        "hardening_package_revision_fuse",
        "hardening_model_call_fuse",
        "hardening_source_broker_operation_fuse",
        "hardening_source_byte_fuse",
        "hardening_wall_time_fuse",
        "hardening_no_progress_fuse",
        "answerable_fuse_exhaustion_outcome",
        "boundary_fuse_exhaustion_outcome",
        "hardening_protocol_status",
        "hardening_authorization_status",
        "hardening_protocol_digest",
        "hardening_freeze_receipt_ref",
        "status",
    }
    if verification.get("protocol_role") == "legacy-compatibility":
        expected_keys.update(
            {
                "protocol_role",
                "legacy_protocol_schema",
                "superseded_as_default_by",
                "current_delivery_authorization_allowed",
                "historical_result_ref",
            }
        )
    errors = validate_exact_mapping_keys(verification, expected_keys, section_label)
    expected_values: dict[str, object] = {
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
        "slice_001_bound_scope": (
            "direction-preview-only-not-a-permanent-protocol-round-cap"
        ),
        "hardening_fixed_round_upper_bound_allowed": False,
        "answerable_fuse_exhaustion_outcome": "fail",
        "boundary_fuse_exhaustion_outcome": (
            "independently-reviewed-honest-limitation-or-fail"
        ),
        "status": "frozen-slice-001-preview-boundary",
    }
    for field, expected in expected_values.items():
        if verification.get(field) != expected:
            errors.append(f"{section_label}.{field} must equal {expected}")

    preview_bound = answer_protocol.get(
        "slice_001_reviewer_verification_investigation_upper_bound"
    )
    if preview_bound != verification.get("slice_001_preview_upper_bound"):
        errors.append(
            f"{section_label}.slice_001_preview_upper_bound must match "
            "answer_protocol.slice_001_reviewer_verification_investigation_upper_bound"
        )

    fuse_fields = (
        "hardening_package_revision_fuse",
        "hardening_model_call_fuse",
        "hardening_source_broker_operation_fuse",
        "hardening_source_byte_fuse",
        "hardening_wall_time_fuse",
        "hardening_no_progress_fuse",
    )
    hardening_ordinal = hardening_ref.rsplit("-", 1)[-1]
    proposed_fuse = (
        "must-be-presealed-positive-high-safety-bound-before-slice-"
        f"{hardening_ordinal}-authorization"
    )
    if not hardening_started:
        for field in fuse_fields:
            if verification.get(field) != proposed_fuse:
                errors.append(
                    f"{section_label}.{field} must remain the explicit proposed fuse marker before hardening authorization"
                )
        for field, expected in (
            (
                "hardening_protocol_status",
                "proposed-not-frozen-requires-new-user-receipt-before-slice-"
                + hardening_ordinal,
            ),
            ("hardening_authorization_status", ENGINEERING_QA_NOT_AUTHORIZED),
            ("hardening_protocol_digest", ENGINEERING_QA_NOT_AUTHORIZED),
            ("hardening_freeze_receipt_ref", ENGINEERING_QA_NOT_AUTHORIZED),
        ):
            if verification.get(field) != expected:
                errors.append(f"{section_label}.{field} must equal {expected}")
        return errors

    numeric_fuses: dict[str, int] = {}
    for field in fuse_fields:
        value = verification.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            errors.append(
                f"{section_label}.{field} must be an exact positive integer before hardening authorization"
            )
        else:
            numeric_fuses[field] = value
    model_calls = numeric_fuses.get("hardening_model_call_fuse")
    if model_calls is not None and model_calls < 2:
        errors.append(
            f"{section_label}.hardening_model_call_fuse must be at least 2 for multi-step verification"
        )
    revisions = numeric_fuses.get("hardening_package_revision_fuse")
    if revisions is not None and revisions < 2:
        errors.append(
            f"{section_label}.hardening_package_revision_fuse must be at least 2 so hardening is not a permanent one-round protocol"
        )
    if verification.get("hardening_protocol_status") != "frozen":
        errors.append(f"{section_label}.hardening_protocol_status must equal frozen")
    if verification.get("hardening_authorization_status") != "user-authorized":
        errors.append(
            f"{section_label}.hardening_authorization_status must equal user-authorized"
        )
    errors.extend(
        _engineering_qa_new_freeze_receipt_errors(
            verification.get("hardening_freeze_receipt_ref"),
            alignment,
            f"{section_label}.hardening_freeze_receipt_ref",
            hardening_authorization_ref=hardening_authorization_ref,
            hardening_ref=hardening_ref,
        )
    )
    frozen_protocol = {
        field: verification.get(field) for field in fuse_fields
    }
    actual_digest = canonical_mapping_digest(
        ENGINEERING_QA_REVIEWER_VERIFICATION_SCHEMA,
        "hardening_fuses",
        frozen_protocol,
    )
    if verification.get("hardening_protocol_digest") != actual_digest:
        errors.append(
            f"{section_label}.hardening_protocol_digest must bind the exact hardening fuses"
        )

    answer_attempts = answer_protocol.get("answer_attempt_upper_bound")
    rewrite_bound = answer_protocol.get("same_package_targeted_rewrite_upper_bound")
    if (
        isinstance(answer_attempts, int)
        and not isinstance(answer_attempts, bool)
        and isinstance(rewrite_bound, int)
        and not isinstance(rewrite_bound, bool)
        and revisions is not None
        and answer_attempts < 1 + rewrite_bound + revisions
    ):
        errors.append(
            f"{section_label}: answer_attempt_upper_bound must cover one new answer per allowed package revision"
        )
    hard_call_bound = answer_protocol.get(
        "hard_safety_model_call_upper_bound_per_question"
    )
    initial_investigation = answer_protocol.get("investigation_model_call_upper_bound")
    review_attempts = answer_protocol.get("review_attempt_upper_bound")
    question_calls = answer_protocol.get("question_understanding_model_call_upper_bound")
    if all(
        isinstance(value, int) and not isinstance(value, bool)
        for value in (
            hard_call_bound,
            initial_investigation,
            model_calls,
            answer_attempts,
            review_attempts,
            question_calls,
        )
    ):
        minimum_calls = (
            question_calls
            + initial_investigation
            + model_calls
            + answer_attempts
            + review_attempts
        )
        if hard_call_bound < minimum_calls:
            errors.append(
                f"{section_label}: hard_safety_model_call_upper_bound_per_question must reserve every verification investigation call, answer and comprehensive/challenge review"
            )
    return errors


def validate_engineering_qa_ablation(
    ablation: dict[str, object],
    alignment: dict[str, object],
    label: str,
    *,
    hardening_started: bool,
    hardening_authorization_ref: object,
    hardening_ref: str = "ITER-010-SLICE-002",
    final_ref: str = "ITER-010-SLICE-003",
) -> list[str]:
    """Freeze a fair ablation or retain it as explicitly disabled history."""

    section_label = f"{label}: engineering_qa_ablation"
    if ablation.get("schema") == CONVERSATIONAL_AGENT_ABLATION_SCHEMA:
        alpha_binding = alignment.get("alpha_agent_comparison_binding")
        pdr009_historical = isinstance(alpha_binding, dict) and (
            alpha_binding.get("case_id") == ITER010_DIRECTION_QUALITY_CASE_ID
            and alpha_binding.get("result_role")
            == "blocking-iter010-strict-superiority-direction-gate"
        )
        pdr010_lightweight = isinstance(alpha_binding, dict) and (
            alpha_binding.get("result_role")
            == "post-experience-strict-superiority-direction-evidence"
        )
        expected_keys = {
            "schema",
            "status",
            "authorization_required_before",
            "authorization_ref",
            "frozen_protocol_digest",
            "full_cognition_system_arm",
            "source_only_system_arm",
            "current_codex_external_baseline_arm",
            "system_arm_shared_runtime",
            "shared_evaluation_inputs",
            "forced_runtime_identity_across_all_three_arms",
            "technical_adjudication_owner",
            "product_direction_decision_owner",
            "quality_gate",
            "gain_gate",
            "cost_dimensions",
            "modeling_cost_accounting",
            "proposed_reuse_horizon_questions",
            "slice_001_required",
            "slice_001_case_id",
            "slice_002_case_id",
            "slice_003_case_id",
        }
        if pdr009_historical:
            expected_keys.update(
                {
                    "legacy_validator_compatibility_only",
                    "current_use_allowed",
                    "superseded_by_case_id",
                }
            )
        errors = validate_exact_mapping_keys(ablation, expected_keys, section_label)
        arm_expectations: dict[str, dict[str, object]] = {
            "full_cognition_system_arm": {
                "agent_runtime": "shared-system-arm-runtime",
                "cognition_input": "full-exact-world-model-cognition-context",
                "source_access": "controlled-read-only-source-tools",
            },
            "source_only_system_arm": {
                "agent_runtime": "shared-system-arm-runtime",
                "cognition_input": "none",
                "source_access": "controlled-read-only-source-tools",
            },
            "current_codex_external_baseline_arm": {
                "runtime": (
                    "preserve-actual-model-reasoning-tools-permissions-and-budget"
                ),
                "cognition_input": "none",
                "role": "external-baseline-not-oracle-not-reviewer",
            },
        }
        for arm, expected in arm_expectations.items():
            supplied = ablation.get(arm)
            if not isinstance(supplied, dict):
                errors.append(f"{section_label}.{arm} must be a mapping")
                continue
            errors.extend(
                validate_exact_mapping_keys(
                    supplied, set(expected), f"{section_label}.{arm}"
                )
            )
            for field, expected_value in expected.items():
                if supplied.get(field) != expected_value:
                    errors.append(
                        f"{section_label}.{arm}.{field} must equal {expected_value}"
                    )
        for field, expected in (
            (
                "authorization_required_before",
                "ITER-010-SLICE-002"
                if pdr010_lightweight
                else "ITER-010-SLICE-001-live-comparison",
            ),
            (
                "system_arm_shared_runtime",
                "same-lead-agent-model-tools-permissions-budget-cache-policy-and-state",
            ),
            (
                "shared_evaluation_inputs",
                "same-exact-revision-questions-authorized-source-scope-output-constraints-and-blind-rubric",
            ),
            ("forced_runtime_identity_across_all_three_arms", False),
            (
                "technical_adjudication_owner",
                "independent-evaluator-not-answer-generator",
            ),
            ("product_direction_decision_owner", "user"),
            (
                "quality_gate",
                "each-arm-zero-major-error-boundary-correct-and-full-cognition-no-material-claim-regression",
            ),
            (
                "gain_gate",
                "full-cognition-must-have-precommitted-quality-or-normalized-cost-gain-versus-source-only-system-arm",
            ),
            (
                "cost_dimensions",
                "source-bytes-source-broker-operations-model-tokens-wall-time-provider-cost-and-world-model-build-update-storage-cost",
            ),
            (
                "modeling_cost_accounting",
                "exact-world-model-build-update-storage-and-provider-cost-amortized-over-frozen-reuse-horizon",
            ),
            ("slice_001_required", False if pdr010_lightweight else True),
            (
                "slice_001_case_id",
                ENGINEERING_QA_NOT_AUTHORIZED
                if pdr010_lightweight
                else "V-COMP-ALPHA-001",
            ),
            ("slice_002_case_id", "V-COMP-EARLY-002"),
            ("slice_003_case_id", "V-COMP-001"),
        ):
            if ablation.get(field) != expected:
                errors.append(f"{section_label}.{field} must equal {expected}")
        reuse_horizon = ablation.get("proposed_reuse_horizon_questions")
        if type(reuse_horizon) is not int or reuse_horizon < 1:
            errors.append(
                f"{section_label}.proposed_reuse_horizon_questions must be a positive integer"
            )
        if pdr009_historical:
            for field, expected in (
                ("status", "proposed-not-authorized"),
                ("authorization_ref", ENGINEERING_QA_NOT_AUTHORIZED),
                ("frozen_protocol_digest", ENGINEERING_QA_NOT_AUTHORIZED),
                ("legacy_validator_compatibility_only", True),
                ("current_use_allowed", False),
                ("superseded_by_case_id", ITER010_DIRECTION_QUALITY_CASE_ID),
            ):
                if ablation.get(field) != expected:
                    errors.append(f"{section_label}.{field} must equal {expected}")
        elif not hardening_started:
            for field, expected in (
                ("status", "proposed-not-authorized"),
                ("authorization_ref", ENGINEERING_QA_NOT_AUTHORIZED),
                ("frozen_protocol_digest", ENGINEERING_QA_NOT_AUTHORIZED),
            ):
                if ablation.get(field) != expected:
                    errors.append(f"{section_label}.{field} must equal {expected}")
        else:
            if ablation.get("status") != "frozen":
                errors.append(f"{section_label}.status must equal frozen before hardening")
            authorization_ref = ablation.get("authorization_ref")
            if not isinstance(authorization_ref, str) or re.fullmatch(
                r"codex-user-message:sha256:[0-9a-f]{64}", authorization_ref
            ) is None:
                errors.append(
                    f"{section_label}.authorization_ref must bind an exact user receipt before hardening"
                )
            frozen_protocol = {
                field: value
                for field, value in ablation.items()
                if field not in {"status", "authorization_ref", "frozen_protocol_digest"}
            }
            expected_digest = canonical_mapping_digest(
                CONVERSATIONAL_AGENT_ABLATION_SCHEMA,
                "engineering_qa_ablation",
                frozen_protocol,
            )
            if ablation.get("frozen_protocol_digest") != expected_digest:
                errors.append(
                    f"{section_label}.frozen_protocol_digest must bind the exact conversational three-arm protocol"
                )
        return errors

    hardening_case_field = f"slice_{hardening_ref.rsplit('-', 1)[-1]}_case_id"
    final_case_field = f"slice_{final_ref.rsplit('-', 1)[-1]}_case_id"
    expected_keys = {
        "status",
        "authorization_required_before",
        "authorization_ref",
        "frozen_protocol_digest",
        "full_cognition_arm",
        "locator_only_or_empty_arm",
        "mature_source_agent_arm",
        "controlled_inputs",
        "quality_gate",
        "locator_control_quality_failure_effect",
        "gain_gate",
        "proposed_quality_gain_threshold",
        "proposed_non_locator_cost_ratio_threshold_ppm",
        "cost_dimensions",
        "modeling_cost_accounting",
        "proposed_reuse_horizon_questions",
        "slice_001_required",
        hardening_case_field,
        final_case_field,
    }
    errors = validate_exact_mapping_keys(ablation, expected_keys, section_label)
    arm_expectations: dict[str, dict[str, object]] = {
        "full_cognition_arm": {
            "cognition_input": "full-exact-world-model-cognition-context",
            "investigation_chain": (
                "shared-adaptive-investigation-source-broker-worker-ledger-package-answer-review"
            ),
        },
        "locator_only_or_empty_arm": {
            "cognition_input": (
                "predeclared-locator-only-projection-or-canonical-empty-when-no-locator-exists"
            ),
            "investigation_chain": "same-as-full-cognition-arm",
        },
        "mature_source_agent_arm": {
            "protocol_ref": "mature_source_agent_protocol_digest",
            "cognition_input": "none",
            "investigation_chain": "frozen-mature-source-agent",
        },
    }
    for arm, expected in arm_expectations.items():
        value = ablation.get(arm)
        if not isinstance(value, dict):
            errors.append(f"{section_label}.{arm} must be a mapping")
            continue
        errors.extend(
            validate_exact_mapping_keys(value, set(expected), f"{section_label}.{arm}")
        )
        for field, expected_value in expected.items():
            if value.get(field) != expected_value:
                errors.append(
                    f"{section_label}.{arm}.{field} must equal {expected_value}"
                )

    expected_scalars: dict[str, object] = {
        "authorization_required_before": f"{hardening_ref}-coding-or-execution",
        "controlled_inputs": (
            "same-exact-revision-model-questions-model-call-and-resource-budget-"
            "cache-policy-and-state-rubric-and-evaluator"
        ),
        "quality_gate": (
            "full-cognition-and-mature-source-agent-zero-major-error-boundary-correct-"
            "and-full-cognition-no-material-claim-regression-versus-mature-source-agent"
        ),
        "locator_control_quality_failure_effect": (
            "may-prove-quality-gain-but-cannot-lower-full-cognition-acceptance-threshold"
        ),
        "gain_gate": (
            "full-cognition-must-have-precommitted-quality-gain-or-precommitted-"
            "normalized-non-locator-investigation-cost-gain-versus-locator-only-or-empty-arm"
        ),
        "proposed_quality_gain_threshold": (
            "at-least-one-predeclared-material-checklist-gain-with-no-regression"
        ),
        "cost_dimensions": (
            "source-bytes-source-broker-operations-model-tokens-wall-time-provider-cost-"
            "and-world-model-build-update-storage-cost"
        ),
        "modeling_cost_accounting": (
            "exact-world-model-build-update-storage-and-provider-cost-amortized-over-"
            "frozen-reuse-horizon"
        ),
        "slice_001_required": False,
    }
    for field, expected in expected_scalars.items():
        if ablation.get(field) != expected:
            errors.append(f"{section_label}.{field} must equal {expected}")
    cost_ratio = ablation.get("proposed_non_locator_cost_ratio_threshold_ppm")
    if (
        isinstance(cost_ratio, bool)
        or not isinstance(cost_ratio, int)
        or not 1 <= cost_ratio < 1_000_000
    ):
        errors.append(
            f"{section_label}.proposed_non_locator_cost_ratio_threshold_ppm must be between 1 and 999999"
        )
    reuse_horizon = ablation.get("proposed_reuse_horizon_questions")
    if (
        isinstance(reuse_horizon, bool)
        or not isinstance(reuse_horizon, int)
        or reuse_horizon < 1
    ):
        errors.append(
            f"{section_label}.proposed_reuse_horizon_questions must be a positive integer"
        )
    for field, pattern in (
        (hardening_case_field, r"V-COMP-EARLY-[0-9]{3,}"),
        (final_case_field, r"V-COMP-[0-9]{3,}"),
    ):
        value = ablation.get(field)
        if not isinstance(value, str) or re.fullmatch(pattern, value) is None:
            errors.append(f"{section_label}.{field} must match {pattern}")

    if not hardening_started:
        for field, expected in (
            ("status", "proposed-not-authorized"),
            ("authorization_ref", ENGINEERING_QA_NOT_AUTHORIZED),
            ("frozen_protocol_digest", ENGINEERING_QA_NOT_AUTHORIZED),
        ):
            if ablation.get(field) != expected:
                errors.append(f"{section_label}.{field} must equal {expected}")
        return errors

    if ablation.get("status") != "frozen":
        errors.append(f"{section_label}.status must equal frozen before hardening")
    errors.extend(
        _engineering_qa_new_freeze_receipt_errors(
            ablation.get("authorization_ref"),
            alignment,
            f"{section_label}.authorization_ref",
            hardening_authorization_ref=hardening_authorization_ref,
            hardening_ref=hardening_ref,
        )
    )
    frozen_protocol = {
        field: value
        for field, value in ablation.items()
        if field not in {"status", "authorization_ref", "frozen_protocol_digest"}
    }
    actual_digest = canonical_mapping_digest(
        ENGINEERING_QA_ABLATION_SCHEMA,
        "engineering_qa_ablation",
        frozen_protocol,
    )
    if ablation.get("frozen_protocol_digest") != actual_digest:
        errors.append(
            f"{section_label}.frozen_protocol_digest must bind the exact three-arm protocol"
        )
    return errors


def validate_engineering_qa_adaptive_gate(
    manifest: dict[str, object], label: str
) -> list[str]:
    """Validate the three adaptive engineering-QA planning and hardening gates."""

    errors: list[str] = []
    alignment = manifest.get("product_goal_alignment")
    answer_protocol = manifest.get("answer_protocol")
    hybrid = manifest.get("hybrid_evidence_path")
    alignment = alignment if isinstance(alignment, dict) else {}
    answer_protocol = answer_protocol if isinstance(answer_protocol, dict) else {}
    hardening_started = engineering_qa_hardening_has_started(manifest)
    hardening_ref = engineering_qa_hardening_slice_ref(manifest)
    hardening_authorization_ref: object = None
    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    refs = [str(reference) for reference in slices] if isinstance(slices, dict) else []
    if isinstance(slices, dict) and isinstance(hardening_ref, str):
        hardening_slice = slices.get(hardening_ref)
        if isinstance(hardening_slice, dict):
            hardening_authorization_ref = hardening_slice.get("authorization_ref")
    if hardening_ref is None:
        errors.append(f"{label}: engineering QA hardening Slice cannot be resolved")
        hardening_ref = "unresolved-hardening-slice"

    package_classes = manifest.get("question_evidence_package_classes")
    if not isinstance(package_classes, dict):
        errors.append(
            f"{label}: question_evidence_package_classes must be a mapping"
        )
    else:
        errors.extend(
            validate_engineering_qa_question_evidence_package_classes(
                package_classes, label
            )
        )
        if isinstance(hybrid, dict):
            if (
                hybrid.get("question_evidence_package_role")
                != "sealed-two-partition-support-citation-and-boundary-audit-set-not-truth-authority"
            ):
                errors.append(
                    f"{label}: hybrid_evidence_path.question_evidence_package_role must bind the two-partition package"
                )
            if hybrid.get("package_seal_confers_truth") is not False:
                errors.append(
                    f"{label}: hybrid_evidence_path.package_seal_confers_truth must remain false"
                )

    reviewer_verification = manifest.get("reviewer_verification_investigation")
    if not isinstance(reviewer_verification, dict):
        errors.append(
            f"{label}: reviewer_verification_investigation must be a mapping"
        )
    else:
        errors.extend(
            validate_engineering_qa_reviewer_verification_investigation(
                reviewer_verification,
                answer_protocol,
                alignment,
                label,
                hardening_started=hardening_started,
                hardening_authorization_ref=hardening_authorization_ref,
                hardening_ref=hardening_ref,
            )
        )

    ablation = manifest.get("engineering_qa_ablation")
    if not isinstance(ablation, dict):
        errors.append(f"{label}: engineering_qa_ablation must be a mapping")
    else:
        errors.extend(
            validate_engineering_qa_ablation(
                ablation,
                alignment,
                label,
                hardening_started=hardening_started,
                hardening_authorization_ref=hardening_authorization_ref,
                hardening_ref=hardening_ref,
                final_ref=refs[-1] if refs else "unresolved-final-slice",
            )
        )
    return errors


def validate_engineering_qa_answer_protocol_execution_readiness(
    answer_protocol: dict[str, object], label: str
) -> list[str]:
    """Freeze adaptive investigation, evidence sealing, answer and review bounds."""

    errors: list[str] = []
    if answer_protocol.get("schema") != ENGINEERING_QA_ADAPTIVE_PROTOCOL_SCHEMA:
        errors.append(
            f"{label}: answer_protocol.schema must equal "
            f"{ENGINEERING_QA_ADAPTIVE_PROTOCOL_SCHEMA}"
        )
    if (
        answer_protocol.get("contract_ref")
        != "SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING"
    ):
        errors.append(
            f"{label}: answer_protocol.contract_ref must equal "
            "SYS-CONTRACT-APPLICATION-ENGINEERING-QUESTION-ANSWERING"
        )
    if not is_engineering_qa_adaptive_protocol(answer_protocol):
        errors.append(
            f"{label}: answer_protocol.mode must equal "
            f"{ENGINEERING_QA_ADAPTIVE_PROTOCOL_MODE}"
        )

    required_question_fields = (
        "user-goal,audience,requested-abstraction-level,"
        "material-conclusion-checklist,evidence-needs,response-language-and-constraints"
    )
    if (
        answer_protocol.get("question_understanding_required_fields")
        != required_question_fields
    ):
        errors.append(
            f"{label}: answer_protocol.question_understanding_required_fields must "
            "freeze the user goal, audience, abstraction level, material-conclusion "
            "checklist, evidence needs, response language and constraints"
        )

    positive_integer_fields = (
        "question_understanding_model_call_upper_bound",
        "investigation_model_call_upper_bound",
        "max_investigation_steps_per_question",
        "slice_001_reviewer_verification_investigation_upper_bound",
        "max_source_broker_operations_per_question",
        "max_source_files_per_question",
        "max_source_bytes_per_question",
        "max_repository_document_bytes_per_question",
        "max_build_configuration_bytes_per_question",
        "max_test_bytes_per_question",
        "max_world_model_result_bytes_per_question",
        "max_sealed_evidence_package_bytes_per_question",
        "max_support_items_per_question",
        "max_evidence_ledger_bytes_per_question",
        "max_wall_time_milliseconds_per_question",
        "initial_answer_model_calls",
        "independent_review_model_calls_per_authorizable_draft",
        "final_answer_role_call_reserve",
        "same_package_targeted_rewrite_upper_bound",
        "answer_attempt_upper_bound",
        "review_attempt_upper_bound",
        "provider_output_complete-replacement_upper_bound_per_stage",
        "hard_safety_model_call_upper_bound_per_question",
    )
    numeric_fields: dict[str, int] = {}
    for field in positive_integer_fields:
        value = answer_protocol.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            errors.append(
                f"{label}: answer_protocol.{field} must be a positive frozen integer upper bound"
            )
        else:
            numeric_fields[field] = value

    exact_numeric_values = {
        "question_understanding_model_call_upper_bound": 1,
        "slice_001_reviewer_verification_investigation_upper_bound": 1,
        "initial_answer_model_calls": 1,
        "independent_review_model_calls_per_authorizable_draft": 2,
        "final_answer_role_call_reserve": 3,
        "same_package_targeted_rewrite_upper_bound": 1,
    }
    for field, expected in exact_numeric_values.items():
        value = numeric_fields.get(field)
        if value is not None and value != expected:
            errors.append(
                f"{label}: answer_protocol.{field} must equal {expected}"
            )
    for field in (
        "investigation_model_call_upper_bound",
        "max_investigation_steps_per_question",
    ):
        value = numeric_fields.get(field)
        if value is not None and value < 2:
            errors.append(
                f"{label}: answer_protocol.{field} must be at least 2 for adaptive result-driven investigation"
            )
    investigation_calls_bound = numeric_fields.get(
        "investigation_model_call_upper_bound"
    )
    investigation_steps_bound = numeric_fields.get(
        "max_investigation_steps_per_question"
    )
    if (
        investigation_calls_bound is not None
        and investigation_steps_bound is not None
        and investigation_steps_bound < investigation_calls_bound
    ):
        errors.append(
            f"{label}: answer_protocol.max_investigation_steps_per_question must cover every allowed investigation model call"
        )

    answer_attempts = numeric_fields.get("answer_attempt_upper_bound")
    rewrite_bound = numeric_fields.get("same_package_targeted_rewrite_upper_bound")
    verification_bound = numeric_fields.get(
        "slice_001_reviewer_verification_investigation_upper_bound"
    )
    initial_answer_calls = numeric_fields.get("initial_answer_model_calls")
    if (
        answer_attempts is not None
        and rewrite_bound is not None
        and verification_bound is not None
        and initial_answer_calls is not None
        and answer_attempts
        < initial_answer_calls + rewrite_bound + verification_bound
    ):
        errors.append(
            f"{label}: answer_protocol.answer_attempt_upper_bound must cover at least "
            "the initial answer, the allowed same-package targeted rewrite and the "
            "Slice 001 new answer after reviewer verification investigation"
        )
    review_attempts = numeric_fields.get("review_attempt_upper_bound")
    if (
        review_attempts is not None
        and answer_attempts is not None
        and review_attempts < answer_attempts + 1
    ):
        errors.append(
            f"{label}: answer_protocol.review_attempt_upper_bound must cover "
            "every answer attempt plus the final evidence-boundary challenge"
        )
    hard_call_bound = numeric_fields.get(
        "hard_safety_model_call_upper_bound_per_question"
    )
    question_calls = numeric_fields.get(
        "question_understanding_model_call_upper_bound"
    )
    investigation_calls = numeric_fields.get(
        "investigation_model_call_upper_bound"
    )
    if all(
        value is not None
        for value in (
            hard_call_bound,
            question_calls,
            investigation_calls,
            answer_attempts,
            review_attempts,
        )
    ):
        minimum_core_calls = (
            question_calls
            + investigation_calls
            + answer_attempts
            + review_attempts
        )
        if hard_call_bound < minimum_core_calls:
            errors.append(
                f"{label}: answer_protocol.hard_safety_model_call_upper_bound_per_question "
                "must cover question understanding, adaptive investigation, every "
                "answer attempt and every independent review"
            )

    for field in (
        "upfront_complete_retrieval_plan_required",
        "sealed_package_mutation_allowed",
        "quality_checklist_reduction_due_to_remaining_calls_allowed",
        "evidence_requirement_reduction_due_to_remaining_calls_allowed",
        "review_skipping_due_to_remaining_calls_allowed",
        "reviewer_verification_returns_to_initial_investigation_model",
        "reviewer_verification_fixed_round_cap_after_slice_001_allowed",
        "question_or_project_keyword_symbol_class_method_fixture_or_oracle_special_routing_allowed",
        "provider_request_retries_allowed",
        "provider_switch_after_dispatch_allowed",
        "provider_finish_parent-evidence-references-returned-by-provider",
        "provider_review_returns-independent-decision-or-verification-request",
        "reviewer_draft-only-scope-expansion-may-trigger-new-evidence-investigation",
        "reviewer_evidence_boundary_projection_is-semantic-verdict",
        "configuration_placeholder_proves_concrete_runtime_value",
        "caller-import-or-registration-proves-unmounted-fields-validation-or-output",
    ):
        if answer_protocol.get(field) is not False:
            errors.append(f"{label}: answer_protocol.{field} must be false")
    for field in (
        "investigation_proposal_must_consider_prior_results",
        "source_broker_policy_compilation_required",
        "evidence_ledger_append_only",
        "question_evidence_package_sealed_after_investigation",
        "finish_material_observations_required",
        "material_observation_identity_application_owned",
        "answer_claim_material_observation_and_evidence_closure_required",
        "reviewer_independent_package_and_draft_observation_audit_required",
        "safety_budget_reserves_answer-comprehensive-review-and-challenge-review",
        "reviewer_more_evidence_requires_specific_verifiable_gap",
        "reviewer_verification_request_requires_application_and_source_broker_revalidation",
        "reviewer_verification_uses_independent_fresh_context_adaptive_investigation",
        "reviewer_verification_creates_new_ledger_revision",
        "reviewer_verification_creates_new_package",
        "new_answer_after_new_package_required",
        "same_package_rewrite_requires_specific_reviewer_finding",
        "independent_rereview_after_any_answer_or_package_change_required",
        "deterministic_grounding_authorization_revision-allowlist-and-package-seal_checks",
        "reviewer_rewrite-finding-requires-current-package-entry-ids",
        "reviewer_missing-evidence-finding-requires-material-checklist-class-and-need",
        "answer_rewrite_preserves_every-supported-material-observation",
        "challenge_review_non-passing-disposition-requires-finding-on-exact-challenged-claim",
        "challenge_review_shared-finding-code-requires-claim-in-every-bound-challenge",
        "verification-successor-may-reuse-predecessor-support",
        "reviewer_original-question-fulfillment-scan-required",
        "challenge_review_specialized-disposition-kind-match-required",
        "reviewer_full-content-material-effect-application-observations-projected",
        "challenge_review_material-effect-layer-binding-application-verified",
    ):
        if answer_protocol.get(field) is not True:
            errors.append(f"{label}: answer_protocol.{field} must be true")
    expected_structured_protocol_values = {
        "provider_finish_disposition_shape": (
            "single-outcome-tagged-finish-dispositions-array"
        ),
        "provider_finish_disposition_partition": (
            "one-list-covers-each-checklist-item-exactly-once"
        ),
        "provider_finish_parent-evidence-reference-derivation": (
            "trusted-stable-first-occurrence-union-of-child-observation-references"
        ),
        "provider_review_finding-remediation-vocabulary": (
            "rewrite-with-existing-evidence,investigate-missing-evidence,"
            "reject-unrecoverable"
        ),
        "reviewer_action-and-verification-request-derivation": (
            "application-owned-reject-then-missing-evidence-then-rewrite-"
            "then-empty-approved"
        ),
        "review_focus_order": (
            "comprehensive-then-evidence-boundary-challenge"
        ),
        "reviewer_evidence_boundary_challenge_projection": (
            "cited-configuration-placeholders-plus-claim-status-literals-"
            "absent-from-cited-content-plus-mentioned-same-application-types-"
            "without-mounted-implementation-plus-cited-full-content-java-entry-"
            "material-effect-scans-plus-original-question-fulfillment-scan"
        ),
        "answer_material_observation_coverage_contract": (
            "exact-id-statement-kind-checklist-and-required-evidence-entry-"
            "table-before-large-role-inputs"
        ),
        "reviewer_full-content-material-effect-scan-unit": (
            "each-cited-full-content-java-entry"
        ),
        "reviewer_full-content-material-effect-categories": (
            "persistence-write,audit-write,cache-mutation,notification,"
            "external-interaction"
        ),
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
        "reviewer_original-question-fulfillment-dimensions": (
            "direct-user-goal,ordered-user-actions,input-output-handoffs,"
            "known-unknown-boundary,material-outcomes"
        ),
        "challenge_review_disposition_vocabulary": (
            "within-evidence-boundary,draft-exceeds-evidence-boundary,"
            "draft-omits-material-effect,draft-omits-material-requirement"
        ),
        "package-material-effect-observation-omission-remediation": (
            "successor-gap-delta-with-predecessor-support-reuse"
        ),
    }
    for field, expected in expected_structured_protocol_values.items():
        if answer_protocol.get(field) != expected:
            errors.append(
                f"{label}: answer_protocol.{field} must equal {expected}"
            )
    if (
        answer_protocol.get("resource_exhaustion_behavior")
        != "answerable-fail-boundary-limitation-only-if-independently-approved-otherwise-fail-closed"
    ):
        errors.append(
            f"{label}: answer_protocol.resource_exhaustion_behavior must equal "
            "answerable-fail-boundary-limitation-only-if-independently-approved-otherwise-fail-closed"
        )

    legacy_fields = (
        "planner_model_calls",
        "draft_model_calls",
        "independent_reviewer_model_calls",
        "exact_total_model_calls_per_question",
        "initial_retrieval_rounds",
        "targeted_reretrieval_round_upper_bound",
        "reviewer_verification_request_round_upper_bound",
        "max_retrieval_steps_per_round",
        "max_investigation_steps",
        "max_investigation_model_calls",
        "planner_model_call_upper_bound",
        "total_model_call_upper_bound_per_question",
        "independent_review_model_calls_per_attempt",
        "safety_budget_reserves_independent_review",
        "max_query_bytes_per_step",
        "max_result_bytes_per_step",
        "max_total_query_bytes_per_question",
        "max_total_result_bytes_per_question",
        "max_trace_bytes_per_question",
        "targeted_reretrieval_requires_specific_reviewer_evidence_gap",
        "reseal_after_targeted_reretrieval_required",
        "independent_rereview_after_any_rewrite_or_reseal_required",
        "reviewer_verification_uses_source_broker",
        "budget_exhaustion_behavior",
        "deterministic_schema_grounding_and_authorization_checks",
        "retries_allowed",
    )
    for field in legacy_fields:
        if field in answer_protocol:
            errors.append(
                f"{label}: engineering QA answer_protocol.{field} is a legacy field"
            )
    if answer_protocol.get("status") != "frozen":
        errors.append(f"{label}: answer_protocol.status must equal frozen")
    return errors


def validate_engineering_qa_hybrid_evidence_execution_readiness(
    source_scope: dict[str, object],
    hybrid_evidence_path: dict[str, object],
    answer_protocol: dict[str, object],
    label: str,
) -> list[str]:
    """Keep adaptive source investigation isolated and evidence-backed."""

    errors: list[str] = []
    expected_source_values: dict[str, object] = {
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
    for field, expected in expected_source_values.items():
        if source_scope.get(field) != expected:
            errors.append(
                f"{label}: source_scope.{field} must equal {expected} for ENGINEERING_QA"
            )

    expected_hybrid_values: dict[str, object] = {
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
    for field, expected in expected_hybrid_values.items():
        if hybrid_evidence_path.get(field) != expected:
            errors.append(
                f"{label}: hybrid_evidence_path.{field} must equal {expected}"
            )
    for field in (
        "world_model_retrieval_hint_or_candidate_reduction_only",
        "retrieval_plan_inputs",
        "model_role",
        "fact_authority",
    ):
        if field in hybrid_evidence_path:
            errors.append(
                f"{label}: adaptive hybrid_evidence_path.{field} is a replaced field"
            )

    errors.extend(
        validate_engineering_qa_answer_protocol_execution_readiness(
            answer_protocol, label
        )
    )
    return errors


def validate_answer_protocol_execution_readiness(
    answer_protocol: dict[str, object], label: str, iteration: str
) -> list[str]:
    """Validate the frozen answer protocol without reviving an earlier pipeline."""

    engineering_qa_mode = is_engineering_qa_adaptive_protocol(answer_protocol)
    if requires_engineering_qa_hybrid(iteration) and not engineering_qa_mode:
        return [
            f"{label}: ITER-010 answer_protocol.mode must equal "
            f"{ENGINEERING_QA_ADAPTIVE_PROTOCOL_MODE}"
        ]
    if engineering_qa_mode:
        if not supports_engineering_qa_hybrid(iteration):
            return [
                f"{label}: engineering QA answer_protocol is supported only from ITER-010"
            ]
        return validate_engineering_qa_answer_protocol_execution_readiness(
            answer_protocol, label
        )

    errors: list[str] = []
    if requires_reflection_gate(iteration):
        if (
            answer_protocol.get("mode")
            != "bounded-result-driven-world-model-investigation"
        ):
            errors.append(
                f"{label}: answer_protocol.mode must equal bounded-result-driven-world-model-investigation"
            )
        numeric_fields: dict[str, int] = {}
        for field in (
            "max_investigation_steps",
            "max_investigation_model_calls",
            "planner_model_call_upper_bound",
            "total_model_call_upper_bound_per_question",
            "max_query_bytes_per_step",
            "max_result_bytes_per_step",
            "max_total_query_bytes_per_question",
            "max_total_result_bytes_per_question",
            "max_wall_time_milliseconds_per_question",
            "max_support_items_per_question",
            "max_trace_bytes_per_question",
        ):
            value = answer_protocol.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                errors.append(
                    f"{label}: answer_protocol.{field} must be a positive frozen integer"
                )
            else:
                numeric_fields[field] = value
        for field in (
            "max_investigation_steps",
            "max_investigation_model_calls",
            "planner_model_call_upper_bound",
        ):
            value = numeric_fields.get(field)
            if value is not None and value < 2:
                errors.append(
                    f"{label}: answer_protocol.{field} must be at least 2 so a result can drive a later investigation decision"
                )
        planner_upper_bound = numeric_fields.get("planner_model_call_upper_bound")
        investigation_call_bound = numeric_fields.get(
            "max_investigation_model_calls"
        )
        if (
            planner_upper_bound is not None
            and investigation_call_bound is not None
            and planner_upper_bound != investigation_call_bound
        ):
            errors.append(
                f"{label}: planner_model_call_upper_bound must equal max_investigation_model_calls"
            )
        total_upper_bound = numeric_fields.get(
            "total_model_call_upper_bound_per_question"
        )
        if (
            total_upper_bound is not None
            and planner_upper_bound is not None
            and total_upper_bound != planner_upper_bound + 2
        ):
            errors.append(
                f"{label}: total_model_call_upper_bound_per_question must equal planner upper bound plus one Draft and one Review call"
            )
        for per_step_field, total_field in (
            ("max_query_bytes_per_step", "max_total_query_bytes_per_question"),
            ("max_result_bytes_per_step", "max_total_result_bytes_per_question"),
        ):
            per_step = numeric_fields.get(per_step_field)
            total = numeric_fields.get(total_field)
            if per_step is not None and total is not None and total < per_step:
                errors.append(
                    f"{label}: answer_protocol.{total_field} must be at least {per_step_field}"
                )
        if (
            answer_protocol.get("budget_exhaustion_behavior")
            != "fail-closed-with-explicit-limitation"
        ):
            errors.append(
                f"{label}: answer_protocol.budget_exhaustion_behavior must equal fail-closed-with-explicit-limitation"
            )
        for field in (
            "planner_model_calls",
            "exact_total_model_calls_per_question",
        ):
            if field in answer_protocol:
                errors.append(
                    f"{label}: ITER-008+ answer_protocol must not use legacy fixed-call field {field}"
                )
    else:
        for field, expected in {
            "planner_model_calls": 1,
            "draft_model_calls": 1,
            "independent_reviewer_model_calls": 1,
            "exact_total_model_calls_per_question": 3,
        }.items():
            if answer_protocol.get(field) != expected:
                errors.append(
                    f"{label}: answer_protocol.{field} must equal {expected}"
                )
    for field in ("draft_model_calls", "independent_reviewer_model_calls"):
        if answer_protocol.get(field) != 1:
            errors.append(f"{label}: answer_protocol.{field} must equal 1")
    if (
        answer_protocol.get(
            "deterministic_schema_grounding_and_authorization_checks"
        )
        is not True
    ):
        errors.append(f"{label}: answer_protocol deterministic checks must be true")
    if answer_protocol.get("retries_allowed") is not False:
        errors.append(f"{label}: answer_protocol.retries_allowed must be false")
    if answer_protocol.get("status") != "frozen":
        errors.append(f"{label}: answer_protocol.status must equal frozen")
    return errors


def validate_positive_value_execution_readiness(
    alignment: dict[str, object],
    label: str,
    iteration: object = "",
    *,
    manifest: dict[str, object] | None = None,
) -> list[str]:
    """Require a precommitted, replayable value comparison before coding."""

    errors: list[str] = []
    for field in ("positive_value_metric", "positive_value_unit"):
        value = alignment.get(field)
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(
                f"{label}: product_goal_alignment.{field} must be frozen before Slice execution"
            )
    if alignment.get("positive_value_comparison") not in {"at-most", "at-least"}:
        errors.append(
            f"{label}: positive_value_comparison must equal at-most or at-least before Slice execution"
        )
    positive_value_threshold = alignment.get("positive_value_threshold")
    if (
        isinstance(positive_value_threshold, bool)
        or not isinstance(positive_value_threshold, int)
        or positive_value_threshold < 0
    ):
        errors.append(
            f"{label}: positive_value_threshold must be a non-negative integer before Slice execution"
        )
    reuse_horizon = alignment.get("positive_value_reuse_horizon_questions")
    if (
        isinstance(reuse_horizon, bool)
        or not isinstance(reuse_horizon, int)
        or reuse_horizon < 1
    ):
        errors.append(
            f"{label}: positive_value_reuse_horizon_questions must be a positive integer before Slice execution"
        )
    for field in (
        "mature_source_agent_protocol_digest",
        "mature_source_agent_rubric_digest",
        "mature_source_agent_cache_policy_digest",
        "positive_value_protocol_digest",
    ):
        digest = alignment.get(field)
        if not isinstance(digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", digest
        ) is None:
            errors.append(
                f"{label}: {field} must be an exact sha256 digest before Slice execution"
            )
    freeze_receipt = alignment.get("positive_value_freeze_receipt_ref")
    if not isinstance(freeze_receipt, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", freeze_receipt
    ) is None:
        errors.append(
            f"{label}: positive_value_freeze_receipt_ref must bind an exact user message before Slice execution"
        )
    if alignment.get("positive_value_adjudication_owner") not in {
        "user",
        "independent-evaluator",
    }:
        errors.append(
            f"{label}: positive_value_adjudication_owner must be frozen as user or independent-evaluator before Slice execution"
        )
    if requires_strict_codex_baseline(iteration):
        errors.extend(
            validate_strict_codex_baseline_alignment(
                alignment,
                label,
                allow_pending_identity=(
                    iteration_number(iteration) == 10
                    and iter010_pending_codex_identity_allowed(manifest)
                ),
            )
        )
    return errors


def validate_alpha_staged_execution_inputs(
    manifest: dict[str, object],
    alignment: dict[str, object],
    new_refs: list[str],
    label: str,
    iteration: object = "",
) -> list[str]:
    """Defer Alpha-only corpora and hidden/comparison freezes until their Slice."""

    alpha_ref = resolved_alpha_direction_slice_ref(alignment, new_refs)
    if alpha_ref is None:
        return []
    errors: list[str] = []
    development = manifest.get("development")
    slices = development.get("slices") if isinstance(development, dict) else None
    alpha_slice = slices.get(alpha_ref) if isinstance(slices, dict) else None
    alpha_started = not isinstance(alpha_slice, dict) or alpha_slice.get("status") != "proposed"
    alpha_corpus = alignment.get("alpha_visible_development_corpus_digest")
    if alpha_started:
        if not isinstance(alpha_corpus, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", alpha_corpus) is None:
            errors.append(f"{label}: alpha_visible_development_corpus_digest must be exact once Alpha starts")
    elif alpha_corpus != (
        "not-frozen-requires-slice-" + alpha_ref.rsplit("-", 1)[-1] + "-authorization"
    ):
        errors.append(f"{label}: alpha_visible_development_corpus_digest must remain deferred before Alpha")

    hardening_ref = engineering_qa_hardening_slice_ref(manifest)
    hardening_started = engineering_qa_hardening_has_started(manifest)
    readiness = manifest.get("readiness_inputs")
    readiness = readiness if isinstance(readiness, dict) else {}
    hardening_ordinal = (
        hardening_ref.rsplit("-", 1)[-1] if isinstance(hardening_ref, str) else "unknown"
    )
    strict_codex_baseline = requires_strict_codex_baseline(iteration)
    if not hardening_started:
        deferred_value = (
            "not-frozen-requires-new-user-receipt-before-slice-" + hardening_ordinal
        )
        if strict_codex_baseline:
            errors.extend(
                validate_positive_value_execution_readiness(
                    alignment, label, iteration, manifest=manifest
                )
            )
        else:
            for field in (
                "positive_value_metric",
                "positive_value_unit",
                "positive_value_comparison",
                "positive_value_threshold",
                "positive_value_reuse_horizon_questions",
            ):
                if alignment.get(field) != deferred_value:
                    errors.append(f"{label}: {field} must remain deferred before hardening")
        if readiness.get("hidden_freeze_protocol_digest") != f"pending-until-slice-{hardening_ordinal}-freeze":
            errors.append(f"{label}: hidden_freeze_protocol_digest must remain deferred before hardening")
        if readiness.get("hidden_freeze_receipt_ref") != ENGINEERING_QA_NOT_AUTHORIZED:
            errors.append(f"{label}: hidden_freeze_receipt_ref must remain not-authorized before hardening")
        return errors

    errors.extend(
        validate_positive_value_execution_readiness(
            alignment, label, iteration, manifest=manifest
        )
    )
    hidden_digest = readiness.get("hidden_freeze_protocol_digest")
    if not isinstance(hidden_digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", hidden_digest) is None:
        errors.append(f"{label}: hidden_freeze_protocol_digest must be exact once hardening starts")
    hardening_slice = slices.get(hardening_ref) if isinstance(slices, dict) else None
    authorization_ref = hardening_slice.get("authorization_ref") if isinstance(hardening_slice, dict) else None
    errors.extend(
        _engineering_qa_new_freeze_receipt_errors(
            readiness.get("hidden_freeze_receipt_ref"),
            alignment,
            f"{label}: hidden_freeze_receipt_ref",
            hardening_authorization_ref=authorization_ref,
            hardening_ref=hardening_ref or "unresolved-hardening-slice",
        )
    )
    return errors


def validate_product_goal_execution_readiness(
    manifest: dict[str, object],
    label: str,
    iteration: str,
    by_id: dict[str, Document],
    new_refs: list[str],
    verification: Document | None,
    *,
    manifest_text: str | None = None,
    verify_current_contract_fileset: bool = True,
) -> list[str]:
    """Validate inputs that must be frozen before the first product Slice runs."""

    errors: list[str] = []
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return errors
    user_held_live = (
        alignment.get("evaluation_input_mode") == USER_HELD_LIVE_EVALUATION_MODE
    )

    if requires_reflection_gate(iteration):
        proposal = by_id.get(f"{iteration}-PROPOSAL")
        (
            catalog_digest,
            assumption_expectations,
            historical_catalog_digest,
            _,
            catalog_errors,
        ) = critical_assumption_catalogs(
            proposal,
            manifest,
            label,
        )
        errors.extend(catalog_errors)
        supplied_catalog_digest = alignment.get(
            "critical_assumption_catalog_digest"
        )
        if supplied_catalog_digest != catalog_digest:
            errors.append(
                f"{label}: critical_assumption_catalog_digest must match the exact current assumption catalog"
            )
        critical_assumption_ids = resolved_assumption_ids(
            alignment.get("critical_assumption_ids")
        )
        if critical_assumption_ids != list(assumption_expectations):
            errors.append(
                f"{label}: critical_assumption_ids must exactly match the current assumption catalog order"
            )
        readiness = by_id.get(f"{iteration}-READINESS")
        iteration_data = manifest.get("iteration")
        paused_cutover = (
            conversational_agent_cutover_active(manifest)
            and isinstance(iteration_data, dict)
            and iteration_data.get("status") == "paused"
        )
        expected_readiness_catalog = (
            historical_catalog_digest if paused_cutover else catalog_digest
        )
        if readiness is None or readiness.metadata.get(
            "critical_assumption_catalog_digest"
        ) != expected_readiness_catalog:
            errors.append(
                f"{label}: Readiness must bind the catalog applicable to its historical or current authorization"
            )

    blocking_case_ids = _execution_manifest_sequence(
        manifest=manifest,
        manifest_text=manifest_text,
        section="product_goal_alignment",
        field="blocking_case_ids",
    )
    readiness_case_ids = _execution_manifest_sequence(
        manifest=manifest,
        manifest_text=manifest_text,
        section="product_goal_alignment",
        field="readiness_blocking_case_ids",
    )
    if not readiness_case_ids:
        errors.append(
            f"{label}: readiness_blocking_case_ids must be a non-empty sequence before Slice execution"
        )
    else:
        if set(readiness_case_ids).intersection(blocking_case_ids):
            errors.append(
                f"{label}: readiness_blocking_case_ids must remain separate from Slice-owned blocking_case_ids"
            )
        for case_id in readiness_case_ids:
            errors.extend(
                validate_blocking_verification_case(
                    verification, case_id, require_pass=True
                )
            )

    if requires_strict_codex_baseline(iteration):
        errors.extend(
            validate_positive_value_execution_readiness(
                alignment, label, iteration, manifest=manifest
            )
        )

    defer_early_evaluation = direction_preview_hardening_is_deferred(
        manifest,
        alignment,
        new_refs,
        direction_preview_enabled=requires_direction_preview(iteration),
    )
    alpha_ref = resolved_alpha_direction_slice_ref(alignment, new_refs)
    if alpha_ref is not None:
        errors.extend(
            validate_alpha_staged_execution_inputs(
                manifest, alignment, new_refs, label, iteration
            )
        )
    elif (
        requires_reflection_gate(iteration)
        and len(new_refs) > 1
        and not defer_early_evaluation
    ):
        errors.extend(
            validate_positive_value_execution_readiness(
                alignment, label, iteration, manifest=manifest
            )
        )

    source_scope = manifest.get("source_scope")
    if not isinstance(source_scope, dict):
        errors.append(f"{label}: source_scope must be a mapping before Slice execution")
        source_scope = {}
    for field in ("provider", "content_kind", "contract_ref"):
        value = source_scope.get(field)
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(f"{label}: source_scope.{field} must be resolved")
    if source_scope.get("question_or_suite_driven_update_allowed") is not False:
        errors.append(
            f"{label}: source_scope.question_or_suite_driven_update_allowed must be false"
        )
    source_digest = source_scope.get("authorized_software_sources_digest")
    if source_digest != alignment.get("authorized_software_sources_digest"):
        errors.append(
            f"{label}: source_scope.authorized_software_sources_digest must match product_goal_alignment"
        )
    source_case_ids = _execution_manifest_sequence(
        manifest=manifest,
        manifest_text=manifest_text,
        section="source_scope",
        field="verification_case_ids",
    )
    if not source_case_ids:
        errors.append(
            f"{label}: source_scope.verification_case_ids must bind update-without-question Cases"
        )
    else:
        if not set(source_case_ids).issubset(set(blocking_case_ids)):
            errors.append(
                f"{label}: source_scope verification Cases must be blocking Cases"
            )
        for case_id in source_case_ids:
            errors.extend(validate_blocking_verification_case(verification, case_id))

    answer_protocol = manifest.get("answer_protocol")
    if not isinstance(answer_protocol, dict):
        errors.append(f"{label}: answer_protocol must be a mapping before Slice execution")
        answer_protocol = {}
    engineering_qa_mode = is_engineering_qa_adaptive_protocol(answer_protocol)
    chat_mode = conversational_agent_cutover_active(manifest)
    if chat_mode:
        errors.extend(
            validate_conversational_architecture_cutover(
                manifest, label, manifest_text=manifest_text
            )
        )
        if iteration == "ITER-010" and uses_legacy_iter010_plan(manifest):
            errors.extend(
                validate_iter010_direction_checkpoint_policy(manifest, label)
            )
        errors.extend(
            validate_conversational_engineering_agent(
                manifest,
                alignment,
                new_refs,
                blocking_case_ids,
                label,
                required=True,
            )
        )
    elif requires_engineering_qa_hybrid(iteration) or engineering_qa_mode:
        hybrid_evidence_path = manifest.get("hybrid_evidence_path")
        if not isinstance(hybrid_evidence_path, dict):
            errors.append(
                f"{label}: hybrid_evidence_path must be a mapping before ENGINEERING_QA Slice execution"
            )
            hybrid_evidence_path = {}
        errors.extend(
            validate_engineering_qa_hybrid_evidence_execution_readiness(
                source_scope,
                hybrid_evidence_path,
                answer_protocol,
                label,
            )
        )
        if engineering_qa_mode and not supports_engineering_qa_hybrid(iteration):
            errors.append(
                f"{label}: engineering QA hybrid evidence is supported only from ITER-010"
            )
    else:
        errors.extend(
            validate_answer_protocol_execution_readiness(
                answer_protocol, label, iteration
            )
        )
    if requires_direction_preview(iteration) and not chat_mode:
        errors.extend(
            validate_direction_preview_answer_entry(
                alignment, answer_protocol, label
            )
        )

    readiness_inputs = manifest.get("readiness_inputs")
    if not isinstance(readiness_inputs, dict):
        errors.append(f"{label}: readiness_inputs must be a mapping before Slice execution")
        readiness_inputs = {}
    if chat_mode:
        architecture_decision = readiness_inputs.get(
            "required_architecture_decision"
        )
        if architecture_decision != "SYS-ADR-018":
            errors.append(
                f"{label}: conversational Agent required_architecture_decision must equal SYS-ADR-018"
            )
        target_decision = (
            by_id.get(architecture_decision)
            if isinstance(architecture_decision, str)
            else None
        )
        if (
            target_decision is None
            or target_decision.metadata.get("kind") != "system-decision"
            or target_decision.metadata.get("status") != "accepted"
            or target_decision.metadata.get("authority") != "normative"
        ):
            errors.append(
                f"{label}: conversational Agent architecture decision must resolve to an accepted normative system-decision"
            )
    elif engineering_qa_mode:
        errors.extend(
            validate_answer_hierarchy_protocol(manifest, label, require_frozen=True)
        )
        architecture_decision = readiness_inputs.get(
            "required_architecture_decision"
        )
        if architecture_decision != "SYS-ADR-016":
            errors.append(
                f"{label}: ENGINEERING_QA required_architecture_decision must equal SYS-ADR-016"
            )
        target_decision = (
            by_id.get(architecture_decision)
            if isinstance(architecture_decision, str)
            else None
        )
        if (
            target_decision is None
            or target_decision.metadata.get("kind") != "system-decision"
            or target_decision.metadata.get("status") != "accepted"
            or target_decision.metadata.get("authority") != "normative"
        ):
            errors.append(
                f"{label}: ENGINEERING_QA architecture decision must resolve to an accepted normative system-decision"
            )
        protocol_schema = answer_protocol.get("schema")
        supplied_budget_digest = readiness_inputs.get(
            "investigation_budget_digest"
        )
        if isinstance(protocol_schema, str):
            actual_budget_digest = canonical_mapping_digest(
                protocol_schema, "answer_protocol", answer_protocol
            )
            if supplied_budget_digest != actual_budget_digest:
                errors.append(
                    f"{label}: investigation_budget_digest must bind the exact ENGINEERING_QA answer_protocol"
                )
    contract_ids = _execution_manifest_sequence(
        manifest=manifest,
        manifest_text=manifest_text,
        section="readiness_inputs",
        field="required_system_contract_refs",
    )
    if not contract_ids:
        errors.append(
            f"{label}: readiness_inputs.required_system_contract_refs must be non-empty"
        )
    else:
        if len(contract_ids) != len(set(contract_ids)):
            errors.append(f"{label}: required_system_contract_refs must be unique")

    named_contract_fields = (
        "source_semantics_contract_ref",
        "implementation_query_contract_ref",
        "no_payload_contract_ref",
        "answer_protocol_contract_ref",
    )
    for field in named_contract_fields:
        reference = readiness_inputs.get(field)
        if not isinstance(reference, str) or reference not in contract_ids:
            errors.append(
                f"{label}: readiness_inputs.{field} must reference required_system_contract_refs"
            )
    current_answer_contract = (
        readiness_inputs.get("answer_protocol_contract_ref")
        if chat_mode
        else answer_protocol.get("contract_ref")
    )
    for reference in (source_scope.get("contract_ref"), current_answer_contract):
        if not isinstance(reference, str) or reference not in contract_ids:
            errors.append(
                f"{label}: source and answer protocol Contracts must be listed in required_system_contract_refs"
            )

    contract_set_schema = readiness_inputs.get("system_contract_set_schema")
    expected_contract_set_schema = f"{iteration}-SYSTEM-CONTRACT-SET@1"
    if contract_set_schema != expected_contract_set_schema:
        errors.append(
            f"{label}: system_contract_set_schema must equal {expected_contract_set_schema}"
        )
    contract_set_paths = _execution_manifest_sequence(
        manifest=manifest,
        manifest_text=manifest_text,
        section="readiness_inputs",
        field="system_contract_set_paths",
    )
    contract_set_paths_valid = True
    if not contract_set_paths:
        errors.append(f"{label}: system_contract_set_paths must be non-empty")
        contract_set_paths_valid = False
    elif len(contract_set_paths) != len(set(contract_set_paths)):
        errors.append(f"{label}: system_contract_set_paths must be unique")
        contract_set_paths_valid = False
    elif contract_set_paths != sorted(contract_set_paths):
        errors.append(
            f"{label}: system_contract_set_paths must use canonical lexical order"
        )
        contract_set_paths_valid = False

    system_root = (REPOSITORY / "docs/system").resolve()
    if contract_set_paths_valid:
        for relative in contract_set_paths:
            parsed = PurePosixPath(relative)
            target = REPOSITORY / relative
            canonical = (
                relative == parsed.as_posix()
                and not parsed.is_absolute()
                and all(part not in {"", ".", ".."} for part in parsed.parts)
            )
            try:
                target.resolve().relative_to(system_root)
            except (OSError, ValueError):
                canonical = False
            if (
                not canonical
                or target.is_symlink()
                or not target.is_file()
            ):
                errors.append(
                    f"{label}: system Contract set path is invalid: {relative}"
                )
                contract_set_paths_valid = False

    supplied_contract_set_digest = readiness_inputs.get(
        "system_contract_set_digest"
    )
    if (
        verify_current_contract_fileset
        and contract_set_paths_valid
        and contract_set_schema == expected_contract_set_schema
    ):
        actual_contract_set_digest = canonical_fileset_digest(
            expected_contract_set_schema,
            contract_set_paths,
        )
        if supplied_contract_set_digest != actual_contract_set_digest:
            errors.append(
                f"{label}: system_contract_set_digest does not match the exact fileset"
            )
    elif not isinstance(supplied_contract_set_digest, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", supplied_contract_set_digest
    ) is None:
        errors.append(
            f"{label}: historical system_contract_set_digest must remain an exact sha256 digest"
        )

    for reference in contract_ids:
        target = by_id.get(reference)
        in_system_root = False
        if target is not None:
            try:
                target.path.resolve().relative_to(system_root)
                in_system_root = True
            except ValueError:
                pass
        if (
            target is None
            or not in_system_root
            or target.metadata.get("kind") != "system-contract"
            or target.metadata.get("status") != "current"
            or target.metadata.get("authority") != "normative"
        ):
            errors.append(
                f"{label}: readiness Contract must resolve to a current normative system-contract: {reference}"
            )
        elif contract_set_paths_valid:
            try:
                contract_path = target.path.resolve().relative_to(
                    REPOSITORY.resolve()
                ).as_posix()
            except ValueError:
                contract_path = ""
            if contract_path not in contract_set_paths:
                errors.append(
                    f"{label}: required Contract is absent from system_contract_set_paths: {reference}"
                )

    frontend = readiness_inputs.get("java_frontend")
    if not isinstance(frontend, dict):
        errors.append(f"{label}: readiness_inputs.java_frontend must be a mapping")
        frontend = {}
    expected_frontend_fields = {
        "artifact_ref",
        "version",
        "runtime_version",
        "grammar_version",
        "language_abi",
        "license_ref",
        "runtime_license_digest",
        "grammar_license_digest",
        "runtime_fileset_digest",
        "grammar_fileset_digest",
        "offline_artifact_digest",
        "canonicalization_oracle_digest",
        "information_preservation_oracle_digest",
        "information_boundary_oracle_digest",
        "legacy_calls_consistency_oracle_digest",
        "readiness_oracle_result_digest",
        "readiness_oracle_result_path",
    }
    if set(frontend) != expected_frontend_fields:
        errors.append(f"{label}: java_frontend fields must match the frozen schema")
    for field in (
        "artifact_ref",
        "version",
        "runtime_version",
        "grammar_version",
        "license_ref",
    ):
        value = frontend.get(field)
        if (
            not isinstance(value, str)
            or is_pending(value)
            or is_absent_evidence(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(f"{label}: java_frontend.{field} must be resolved")
    language_abi = frontend.get("language_abi")
    if (
        isinstance(language_abi, bool)
        or not isinstance(language_abi, int)
        or language_abi < 1
    ):
        errors.append(f"{label}: java_frontend.language_abi must be positive")
    for field in (
        "runtime_license_digest",
        "grammar_license_digest",
        "runtime_fileset_digest",
        "grammar_fileset_digest",
        "offline_artifact_digest",
        "canonicalization_oracle_digest",
        "information_preservation_oracle_digest",
        "information_boundary_oracle_digest",
        "legacy_calls_consistency_oracle_digest",
        "readiness_oracle_result_digest",
        "system_contract_set_digest",
    ):
        value = (
            frontend.get(field)
            if field
            != "system_contract_set_digest"
            else readiness_inputs.get(field)
        )
        if not isinstance(value, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", value
        ) is None:
            errors.append(f"{label}: {field} must be an exact sha256 digest")
    result_path = frontend.get("readiness_oracle_result_path")
    if (
        not isinstance(result_path, str)
        or PurePosixPath(result_path).is_absolute()
        or result_path != PurePosixPath(result_path).as_posix()
        or any(
            part in {"", ".", ".."}
            for part in PurePosixPath(result_path).parts
        )
    ):
        errors.append(
            f"{label}: readiness_oracle_result_path must be repository-relative"
        )

    if iteration == "ITER-007":
        hidden_components = tuple(
            REPOSITORY
            / "validation/structure_world_model_iteration_007"
            / name
            for name in (
                "hidden_freeze_protocol.json",
                "hidden_freeze.py",
                "hidden_freeze_lifecycle.py",
            )
        )
        if all(path.is_file() and not path.is_symlink() for path in hidden_components):
            actual_hidden_digest = canonical_raw_component_set_digest(
                hidden_components
            )
            if (
                readiness_inputs.get("hidden_freeze_protocol_digest")
                != actual_hidden_digest
            ):
                errors.append(
                    f"{label}: hidden_freeze_protocol_digest does not match its public components"
                )
        else:
            errors.append(f"{label}: hidden-freeze protocol components are unavailable")
    elif alpha_ref is None:
        hidden_digest = readiness_inputs.get("hidden_freeze_protocol_digest")
        if not isinstance(hidden_digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", hidden_digest
        ) is None:
            errors.append(f"{label}: hidden_freeze_protocol_digest must be an exact sha256 digest")
    visible_corpus_digest = alignment.get("visible_development_corpus_digest")
    if not isinstance(visible_corpus_digest, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", visible_corpus_digest
    ) is None:
        errors.append(
            f"{label}: visible_development_corpus_digest must be an exact sha256 digest"
        )

    readiness = by_id.get(f"{iteration}-READINESS")
    readiness_dependencies = (
        readiness.metadata.get("depends_on", []) if readiness is not None else []
    )
    if not isinstance(readiness_dependencies, list):
        readiness_dependencies = []
    for reference in contract_ids:
        if reference not in readiness_dependencies:
            errors.append(
                f"{label}: accepted Readiness must depend on frozen Contract {reference}"
            )
    if new_refs:
        first_slice = by_id.get(new_refs[0])
        first_dependencies = (
            first_slice.metadata.get("depends_on", []) if first_slice is not None else []
        )
        if not isinstance(first_dependencies, list) or f"{iteration}-READINESS" not in first_dependencies:
            errors.append(
                f"{label}: first executable Slice must depend on accepted Readiness"
            )

    canary_bindings = alignment.get("early_hidden_canary_bindings")
    expected_canary_refs = required_early_evaluation_slice_refs(
        alignment,
        new_refs,
        direction_preview_enabled=requires_direction_preview(iteration),
    )
    canary_refs: list[str] = []
    canary_cases: list[str] = []
    if defer_early_evaluation:
        expected_canary_refs = set()
    if expected_canary_refs and not isinstance(canary_bindings, dict):
        errors.append(
            f"{label}: early_hidden_canary_bindings must cover every pre-final Slice"
        )
    elif not defer_early_evaluation and isinstance(canary_bindings, dict):
        for binding_name, binding in canary_bindings.items():
            if not isinstance(binding, dict):
                errors.append(
                    f"{label}: early_hidden_canary_bindings.{binding_name} must be a mapping"
                )
                continue
            new_ref = binding.get("new_slice_ref")
            case_id = binding.get("case_id")
            if not isinstance(new_ref, str) or new_ref not in expected_canary_refs:
                errors.append(
                    f"{label}: early hidden canary must bind a pre-final Slice"
                )
            else:
                canary_refs.append(new_ref)
            if not isinstance(case_id, str) or re.fullmatch(
                r"V-CANARY-[0-9]{3,}", case_id
            ) is None:
                errors.append(
                    f"{label}: early hidden canary case_id must match V-CANARY-NNN"
                )
            else:
                canary_cases.append(case_id)
                if case_id not in blocking_case_ids:
                    errors.append(
                        f"{label}: early hidden canary Case must be blocking"
                    )
                bound_slice = by_id.get(new_ref) if isinstance(new_ref, str) else None
                slice_gate_cases = (
                    bound_slice.metadata.get("product_goal_slice_gate_case_ids", [])
                    if bound_slice is not None
                    else []
                )
                if not isinstance(slice_gate_cases, list) or case_id not in {
                    str(item) for item in slice_gate_cases
                }:
                    errors.append(
                        f"{label}: early hidden canary Case must be owned by its bound Slice"
                    )
            if binding.get("evaluation_owner") not in {"independent-evaluator", "user"}:
                errors.append(
                    f"{label}: early hidden canary must have an independent evaluation owner"
                )
            if binding.get("implementation_visibility") != "hidden-until-slice-code-freeze":
                errors.append(
                    f"{label}: early hidden canary must remain hidden until Slice code freeze"
                )
            if binding.get("burn_rule") != (
                "product-change-between-disclosure-and-slice-result-seal-"
                "burns-canary-and-preserves-result"
            ):
                errors.append(
                    f"{label}: early hidden canary must freeze the disclosure-to-Result-seal burn rule"
                )
            for field in ("project_manifest_digest", "suite_digest"):
                value = binding.get(field)
                valid_user_held_value = (
                    user_held_live and value == USER_HELD_LIVE_UNDISCLOSED
                )
                if not valid_user_held_value and (
                    not isinstance(value, str)
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", value) is None
                ):
                    errors.append(
                        f"{label}: early hidden canary {field} must be an exact sha256 digest"
                        " or the closed user-held undisclosed marker"
                    )
        if set(canary_refs) != expected_canary_refs or len(canary_refs) != len(set(canary_refs)):
            errors.append(
                f"{label}: early hidden canaries must bind each pre-final Slice exactly once"
            )
        if len(canary_cases) != len(set(canary_cases)):
            errors.append(f"{label}: early hidden canary Case IDs must be unique")

    return errors


def validate_product_goal_reference_targets(
    manifest_path: Path,
    iteration: str,
    by_id: dict[str, Document],
    *,
    require_execution_slice_sequence: bool = False,
    require_completed_slice_sequence: bool = False,
    require_rejected_slice_sequence: bool = False,
    require_paused_slice_sequence: bool = False,
    require_superseded_slice_sequence: bool = False,
    verification: Document | None = None,
) -> list[str]:
    if not requires_product_goal_alignment(iteration):
        return []
    label = _path_label(manifest_path)
    try:
        text = manifest_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return []
    try:
        manifest = safe_load_manifest(text)
    except SafeYamlError:
        return []
    alignment = manifest.get("product_goal_alignment")
    if not isinstance(alignment, dict):
        return []

    errors: list[str] = []
    if requires_reflection_gate(iteration):
        errors.extend(
            validate_planned_assumption_catalog(
                by_id.get(f"{iteration}-PROPOSAL"),
                manifest,
                label,
            )
        )
    capability_path_ref = alignment.get("capability_path_ref")
    if isinstance(capability_path_ref, str):
        capability_path = by_id.get(capability_path_ref)
        if (
            capability_path is None
            or capability_path.metadata.get("kind") != "roadmap-milestone"
            or capability_path.metadata.get("authority") != "planning-only"
        ):
            errors.append(
                f"{label}: capability_path_ref must reference a planning-only roadmap milestone"
            )
        else:
            capability_step = alignment.get("capability_path_step")
            registered_steps = set(
                re.findall(
                    r"(?m)^\|\s*`(step-[a-z0-9-]+)`\s*\|",
                    capability_path.body,
                )
            )
            if (
                not isinstance(capability_step, str)
                or capability_step not in registered_steps
            ):
                errors.append(
                    f"{label}: capability_path_step must reference a registered Step ID in {capability_path_ref}"
                )

    predecessor_refs = manifest_resolved_sequence_items(
        text, "product_goal_alignment", "predecessor_result_refs"
    ) or []
    current_number = iteration_number(iteration)
    for reference in predecessor_refs:
        target = by_id.get(reference)
        target_number = iteration_number(
            "" if target is None else target.metadata.get("iteration", "")
        )
        valid_acceptance = (
            target is not None
            and target.metadata.get("kind") == "iteration-acceptance"
            and str(target.metadata.get("status", "")) in FINAL_ITERATION_STATUSES
        )
        valid_failed_redirect = (
            target is not None
            and target.metadata.get("kind") == "iteration-result"
            and target.metadata.get("status") == "failed-preserved"
        )
        if not (
            (valid_acceptance or valid_failed_redirect)
            and current_number is not None
            and target_number is not None
            and target_number < current_number
        ):
            errors.append(
                f"{label}: predecessor_result_refs item must reference an earlier Acceptance or failed-preserved Result: {reference}"
            )

    accepted_refs = manifest_resolved_sequence_items(
        text, "product_goal_alignment", "accepted_capability_refs"
    ) or []
    if not set(accepted_refs).issubset(set(predecessor_refs)):
        errors.append(
            f"{label}: accepted_capability_refs must be included in predecessor_result_refs"
        )
    for reference in accepted_refs:
        target = by_id.get(reference)
        current_number = iteration_number(iteration)
        target_number = iteration_number(
            "" if target is None else target.metadata.get("iteration", "")
        )
        valid_prior_acceptance = (
            target is not None
            and target.metadata.get("kind") == "iteration-acceptance"
            and str(target.metadata.get("status", "")) in FINAL_ITERATION_STATUSES
            and current_number is not None
            and target_number is not None
            and target_number < current_number
        )
        if valid_prior_acceptance:
            target_iteration = str(target.metadata.get("iteration", ""))
            target_index = by_id.get(f"{target_iteration}-INDEX")
            if (
                target_index is not None
                and target_index.metadata.get("kind") == "iteration-index"
                and str(target_index.metadata.get("status", "")) == "rejected"
            ):
                valid_prior_acceptance = False
        if not valid_prior_acceptance:
            errors.append(
                f"{label}: accepted_capability_refs item must reference an earlier accepted iteration: {reference}"
            )

    new_refs = manifest_resolved_sequence_items(
        text, "product_goal_alignment", "new_capability_slice_refs"
    ) or []
    experience_delivery_policy = manifest.get("experience_delivery_policy")
    if (
        isinstance(experience_delivery_policy, dict)
        and isinstance(
            experience_delivery_policy.get("historical_pre_policy_result_refs"),
            dict,
        )
    ):
        experience_delivery_policy["historical_pre_policy_result_refs"] = (
            manifest_resolved_sequence_items(
                text,
                "experience_delivery_policy",
                "historical_pre_policy_result_refs",
            )
            or []
        )
    development = manifest.get("development")
    raw_slices = development.get("slices") if isinstance(development, dict) else None
    if isinstance(raw_slices, dict):
        for reference in new_refs:
            state = raw_slices.get(reference)
            if not isinstance(state, dict):
                continue
            for sequence_field in (
                "rework_result_refs",
                "prior_authorization_refs",
            ):
                if not isinstance(state.get(sequence_field), dict):
                    continue
                resolved_items = manifest_resolved_nested_sequence_items(
                    text,
                    ("development", "slices", reference, sequence_field),
                )
                if resolved_items is not None:
                    state[sequence_field] = resolved_items
    if require_execution_slice_sequence:
        errors.extend(
            validate_product_goal_execution_readiness(
                manifest,
                label,
                iteration,
                by_id,
                new_refs,
                verification,
                manifest_text=text,
                verify_current_contract_fileset=not (
                    require_completed_slice_sequence
                    or require_rejected_slice_sequence
                    or require_paused_slice_sequence
                ),
            )
        )
    if require_superseded_slice_sequence:
        errors.extend(
            validate_superseded_iteration_plan(
                new_refs,
                by_id,
                manifest,
                label,
            )
        )
    cross_cases = manifest_resolved_sequence_items(
        text, "product_goal_alignment", "cross_domain_cases"
    ) or []
    cases_by_new_ref: dict[str, list[str]] = {reference: [] for reference in new_refs}
    slice_gate_cases_by_ref: dict[str, list[str]] = {}
    bindings = alignment.get("cross_domain_bindings")
    if isinstance(bindings, dict):
        for binding in bindings.values():
            if not isinstance(binding, dict):
                continue
            case_id = binding.get("case_id")
            new_ref = binding.get("new_slice_ref")
            if (
                isinstance(case_id, str)
                and case_id in cross_cases
                and isinstance(new_ref, str)
                and new_ref in cases_by_new_ref
            ):
                cases_by_new_ref[new_ref].append(case_id)
    for reference in new_refs:
        target = by_id.get(reference)
        if (
            target is None
            or target.metadata.get("kind") != "development-slice"
            or str(target.metadata.get("iteration", "")) != iteration
        ):
            errors.append(
                f"{label}: new_capability_slice_refs item must reference a development slice in {iteration}: {reference}"
            )
            continue

        accepted_metadata = target.metadata.get(
            "product_goal_accepted_capability_refs", []
        )
        cross_metadata = target.metadata.get("product_goal_cross_domain_case_ids", [])
        slice_gate_metadata = target.metadata.get("product_goal_slice_gate_case_ids", [])
        if target.metadata.get("product_goal_gate") != "V-000":
            errors.append(f"{target.relative_path}: product_goal_gate must equal V-000")
        if not isinstance(accepted_metadata, list) or set(accepted_metadata) != set(
            accepted_refs
        ):
            errors.append(
                f"{target.relative_path}: product_goal_accepted_capability_refs must match the Manifest"
            )
        if not isinstance(cross_metadata, list) or set(cross_metadata) != set(
            cases_by_new_ref.get(reference, [])
        ):
            errors.append(
                f"{target.relative_path}: product_goal_cross_domain_case_ids must match the Manifest"
            )
        if not isinstance(slice_gate_metadata, list) or not slice_gate_metadata:
            errors.append(
                f"{target.relative_path}: product_goal_slice_gate_case_ids must be non-empty"
            )
            slice_gate_cases_by_ref[reference] = []
        else:
            slice_gate_cases_by_ref[reference] = [str(item) for item in slice_gate_metadata]
        dependencies = target.metadata.get("depends_on", [])
        if not isinstance(dependencies, list):
            dependencies = []
        for required_dependency in (f"{iteration}-PROPOSAL", *accepted_refs):
            if required_dependency not in dependencies:
                errors.append(
                    f"{target.relative_path}: cumulative product slice must depend on {required_dependency}"
                )

    blocking_case_ids = manifest_resolved_sequence_items(
        text, "product_goal_alignment", "blocking_case_ids"
    ) or []
    errors.extend(
        validate_historical_gate_catalog(
            manifest,
            blocking_case_ids,
            verification,
            label,
        )
    )
    reflection_by_slice: dict[str, dict[str, object]] = {}
    if requires_reflection_gate(iteration):
        errors.extend(
            validate_reflection_gate_bindings(
                alignment, new_refs, blocking_case_ids, label
            )
        )
        reflection_by_slice = reflection_gate_bindings_by_slice(alignment)
    assigned_gate_cases = [
        case_id
        for reference in new_refs
        for case_id in slice_gate_cases_by_ref.get(reference, [])
    ]
    if (
        len(assigned_gate_cases) != len(set(assigned_gate_cases))
        or set(assigned_gate_cases) != set(blocking_case_ids)
    ):
        errors.append(
            f"{label}: Slice gate Case IDs must uniquely partition blocking_case_ids"
        )
    for reference in new_refs:
        target = by_id.get(reference)
        if target is None:
            continue
        owned = set(slice_gate_cases_by_ref.get(reference, []))
        required_owned = set(cases_by_new_ref.get(reference, []))
        experience_delivery_policy = manifest.get("experience_delivery_policy")
        delivery_owner_ref = resolved_sustained_alpha_slice_ref(
            alignment, new_refs
        )
        if (
            isinstance(experience_delivery_policy, dict)
            and reference == delivery_owner_ref
        ):
            for field in (
                "access_case_id",
                "timebox_case_id",
                "quality_case_id",
            ):
                delivery_case = experience_delivery_policy.get(field)
                if isinstance(delivery_case, str):
                    required_owned.add(delivery_case)
        experience_binding = alignment.get("experience_version_binding")
        if (
            isinstance(experience_binding, dict)
            and experience_binding.get("new_slice_ref") == reference
        ):
            experience_case = experience_binding.get("case_id")
            if isinstance(experience_case, str):
                required_owned.add(experience_case)
        conversational_agent = manifest.get("conversational_engineering_agent")
        if (
            isinstance(conversational_agent, dict)
            and conversational_agent.get("owner_slice_ref") == reference
            and isinstance(conversational_agent.get("chat_case_id"), str)
        ):
            required_owned.add(str(conversational_agent["chat_case_id"]))
        direction_preview_binding = alignment.get("direction_preview_binding")
        if (
            isinstance(direction_preview_binding, dict)
            and direction_preview_binding.get("new_slice_ref") == reference
        ):
            direction_preview_case = direction_preview_binding.get("case_id")
            if isinstance(direction_preview_case, str):
                required_owned.add(direction_preview_case)
                if (
                    target.metadata.get(
                        "product_goal_direction_preview_checkpoint_id"
                    )
                    != direction_preview_case
                ):
                    errors.append(
                        f"{target.relative_path}: product_goal_direction_preview_checkpoint_id must match the owned Manifest binding"
                    )
        if requires_reflection_gate(iteration):
            reflection_binding = reflection_by_slice.get(reference)
            reflection_case = (
                reflection_binding.get("case_id")
                if isinstance(reflection_binding, dict)
                else None
            )
            if not isinstance(reflection_case, str):
                errors.append(
                    f"{target.relative_path}: Slice is missing its Manifest reflection Gate binding"
                )
            else:
                required_owned.add(reflection_case)
                if (
                    target.metadata.get("product_goal_reflection_gate_case_id")
                    != reflection_case
                ):
                    errors.append(
                        f"{target.relative_path}: product_goal_reflection_gate_case_id must match the owned Manifest binding"
                    )
            if isinstance(reflection_binding, dict):
                conditional_falsifiers = reflection_binding.get(
                    "conditional_falsifier_bindings"
                )
                if isinstance(conditional_falsifiers, dict):
                    for conditional_falsifier in conditional_falsifiers.values():
                        if not isinstance(conditional_falsifier, dict):
                            continue
                        conditional_case = conditional_falsifier.get("case_id")
                        if isinstance(conditional_case, str):
                            required_owned.add(conditional_case)
            early_canary_bindings = alignment.get("early_hidden_canary_bindings")
            if isinstance(early_canary_bindings, dict):
                for early_binding in early_canary_bindings.values():
                    if (
                        isinstance(early_binding, dict)
                        and early_binding.get("new_slice_ref") == reference
                    ):
                        for field in ("case_id", "negative_case_id"):
                            early_case = early_binding.get(field)
                            if isinstance(early_case, str):
                                required_owned.add(early_case)
            for early_field in (
                "alpha_agent_comparison_binding",
                "early_comparison_binding",
                "early_diagnostic_binding",
            ):
                early_binding = alignment.get(early_field)
                if (
                    isinstance(early_binding, dict)
                    and early_binding.get("new_slice_ref") == reference
                    and isinstance(early_binding.get("case_id"), str)
                ):
                    required_owned.add(str(early_binding["case_id"]))
        web_case = target.metadata.get("product_goal_web_checkpoint_id")
        if isinstance(web_case, str):
            required_owned.add(web_case)
        if reference == alignment.get("live_ad_hoc_checkpoint_binding", {}).get(
            "new_slice_ref"
        ):
            ad_hoc_case = target.metadata.get(
                "product_goal_live_ad_hoc_checkpoint_id"
            )
            if isinstance(ad_hoc_case, str):
                required_owned.add(ad_hoc_case)
        if not required_owned.issubset(owned):
            errors.append(
                f"{target.relative_path}: Slice gate Cases must include its owned cross-domain, Web, ad-hoc, experience access/timebox/quality, Alpha Agent comparison, early-evaluation, conditional-falsifier and reflection Cases"
            )

    checkpoint_bindings: list[tuple[str, dict[str, object]]] = []
    for metadata_field, binding_field in (
        (
            "product_goal_direction_preview_checkpoint_id",
            "direction_preview_binding",
        ),
        ("product_goal_web_checkpoint_id", "web_checkpoint_binding"),
        ("product_goal_live_ad_hoc_checkpoint_id", "live_ad_hoc_checkpoint_binding"),
    ):
        binding = alignment.get(binding_field)
        if isinstance(binding, dict):
            checkpoint_bindings.append((metadata_field, binding))
    additional_web_bindings = alignment.get("additional_web_checkpoint_bindings")
    if isinstance(additional_web_bindings, dict):
        checkpoint_bindings.extend(
            ("product_goal_web_checkpoint_id", binding)
            for binding in additional_web_bindings.values()
            if isinstance(binding, dict)
        )

    for metadata_field, binding in checkpoint_bindings:
        owner_ref = binding.get("new_slice_ref")
        owner = by_id.get(owner_ref) if isinstance(owner_ref, str) else None
        expected_case = binding.get("case_id")
        if owner is not None and owner.metadata.get(metadata_field) != expected_case:
            errors.append(
                f"{owner.relative_path}: {metadata_field} must match the owned Manifest binding"
            )

    if require_execution_slice_sequence:
        errors.extend(
            validate_product_goal_slice_sequence(
                new_refs,
                by_id,
                label,
                manifest=manifest,
                verification=verification,
                require_completed=require_completed_slice_sequence,
                require_rejected=require_rejected_slice_sequence,
                require_paused=require_paused_slice_sequence,
            )
        )

    for case_id in blocking_case_ids:
        errors.extend(validate_blocking_verification_case(verification, case_id))
    return errors


def validate_slice_reflection_result(
    target: Document,
    result: Document,
    binding: dict[str, object] | None,
    manifest_slice: dict[str, object],
    verification: Document | None,
    label: str,
    *,
    blocked: bool,
    assumption_expectations: dict[str, str] | None = None,
    assumption_catalog_digest: str | None = None,
    rework_policy: dict[str, object] | None = None,
    enforce_manifest_decision: bool = True,
) -> list[str]:
    errors: list[str] = []
    reflection_catalog_required = requires_reflection_gate(
        str(target.metadata.get("iteration", ""))
    )
    if reflection_catalog_required and (
        not isinstance(assumption_expectations, dict)
        or not assumption_expectations
    ):
        errors.append(
            f"{label}: {target.identifier} reflection validation requires the frozen assumption catalog"
        )
    if reflection_catalog_required and (
        not isinstance(assumption_catalog_digest, str)
        or re.fullmatch(r"sha256:[0-9a-f]{64}", assumption_catalog_digest) is None
    ):
        errors.append(
            f"{label}: {target.identifier} reflection validation requires an exact critical_assumption_catalog_digest"
        )
    if not isinstance(binding, dict):
        return [f"{label}: {target.identifier} is missing its reflection Gate binding"]
    case_id = binding.get("case_id")
    if not isinstance(case_id, str):
        return [f"{label}: {target.identifier} reflection Gate has no valid case_id"]
    if result.metadata.get("reflection_gate_case_id") != case_id:
        errors.append(
            f"{label}: {target.identifier} Result reflection_gate_case_id must equal {case_id}"
        )
    if result.metadata.get("reflection_gate_status") != "PASS":
        errors.append(
            f"{label}: {target.identifier} Result reflection_gate_status must equal PASS"
        )
    if (
        assumption_catalog_digest is not None
        and result.metadata.get("critical_assumption_catalog_digest")
        != assumption_catalog_digest
    ):
        errors.append(
            f"{label}: {target.identifier} Result must bind the frozen critical_assumption_catalog_digest"
        )
    if result.metadata.get("reflection_decision_owner") != binding.get(
        "decision_owner"
    ):
        errors.append(
            f"{label}: {target.identifier} Result reflection_decision_owner must match the Manifest binding"
        )
    decision_ref = result.metadata.get("reflection_decision_ref")
    if not isinstance(decision_ref, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", decision_ref
    ) is None:
        errors.append(
            f"{label}: {target.identifier} Result reflection_decision_ref must bind an exact user message digest"
        )
    if result.metadata.get("reflection_issue_class") not in REFLECTION_ISSUE_CLASSES:
        errors.append(
            f"{label}: {target.identifier} Result reflection_issue_class is invalid"
        )
    if result.metadata.get("reflection_issue_scope") not in REFLECTION_ISSUE_SCOPES:
        errors.append(
            f"{label}: {target.identifier} Result reflection_issue_scope is invalid"
        )
    if blocked and result.metadata.get("reflection_issue_class") == "none":
        errors.append(
            f"{label}: blocked {target.identifier} reflection_issue_class must identify the failure class"
        )
    if blocked and result.metadata.get("reflection_issue_scope") == "none":
        errors.append(
            f"{label}: blocked {target.identifier} reflection_issue_scope must identify individual or systemic impact"
        )
    report_digest = result.metadata.get("reflection_report_digest")
    valid_report_digest = isinstance(report_digest, str) and re.fullmatch(
        r"sha256:[0-9a-f]{64}", report_digest
    ) is not None
    if not valid_report_digest:
        errors.append(
            f"{label}: {target.identifier} Result reflection_report_digest must be an exact sha256 digest"
        )
    decision = result.metadata.get("reflection_decision")
    if blocked:
        if decision not in {"REWORK", "REDIRECT", "REJECT"}:
            errors.append(
                f"{label}: non-success {target.identifier} reflection_decision must equal REWORK, REDIRECT or REJECT"
            )
    elif decision != binding.get("success_decision"):
        errors.append(
            f"{label}: completed {target.identifier} reflection_decision must equal its Manifest success_decision"
        )
    if rework_policy is not None and decision == "REDIRECT":
        redirect_basis = result.metadata.get("reflection_redirect_basis")
        if redirect_basis not in {
            "explicit-user-direction-change",
            "core-architecture-falsified",
            "precommitted-no-progress-limit-reached",
        }:
            errors.append(
                f"{label}: {target.identifier} REDIRECT must bind an allowed explicit redirect basis"
            )
        elif redirect_basis == "core-architecture-falsified" and (
            result.metadata.get("reflection_issue_class") != "architecture"
            or result.metadata.get("reflection_issue_scope") != "systemic"
        ):
            errors.append(
                f"{label}: {target.identifier} core-architecture REDIRECT requires an architecture/systemic diagnosis"
            )
        elif redirect_basis == "precommitted-no-progress-limit-reached":
            attempt = result.metadata.get("rework_attempt_number")
            limit = rework_policy.get("no_progress_attempt_limit")
            history = manifest_slice.get("rework_result_refs")
            history_count = len(history) if isinstance(history, list) else 0
            if (
                isinstance(attempt, bool)
                or not isinstance(attempt, int)
                or isinstance(limit, bool)
                or not isinstance(limit, int)
                or attempt < limit
            ):
                errors.append(
                    f"{label}: {target.identifier} no-progress REDIRECT must reach the precommitted attempt limit"
                )
            if not isinstance(attempt, bool) and isinstance(attempt, int) and (
                not isinstance(history, list)
                or not history
                or attempt != history_count
            ):
                errors.append(
                    f"{label}: {target.identifier} no-progress REDIRECT attempt must equal its complete failed-Result history count"
                )
            progress = result.metadata.get("rework_progress_measure")
            if progress != rework_policy.get("no_progress_measure"):
                errors.append(
                    f"{label}: {target.identifier} no-progress REDIRECT must bind the frozen no_progress_measure"
                )
    if rework_policy is not None and decision == "REWORK":
        attempt = result.metadata.get("rework_attempt_number")
        if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
            errors.append(
                f"{label}: {target.identifier} REWORK must record a positive rework_attempt_number"
            )
        progress = result.metadata.get("rework_progress_measure")
        if (
            not isinstance(progress, str)
            or is_pending(progress)
            or has_unresolved_placeholder(progress)
        ):
            errors.append(
                f"{label}: {target.identifier} REWORK must record its measurable progress outcome"
            )
    if enforce_manifest_decision and manifest_slice.get("reflection_decision") != decision:
        errors.append(
            f"{label}: development.slices.{target.identifier}.reflection_decision must match its Result"
        )
    reflection_heading_count = len(
        re.findall(
            r"(?m)^[ ]{0,3}##[ \t]+Architecture reflection and continuation decision[ \t]*#*[ \t]*$",
            result.body,
        )
    )
    if reflection_heading_count != 1:
        errors.append(
            f"{label}: {target.identifier} Result must contain exactly one Architecture reflection and continuation decision section"
        )
    section = markdown_section_body(
        result, "Architecture reflection and continuation decision"
    )
    if (
        section is not None
        and valid_report_digest
        and report_digest
        != "sha256:" + hashlib.sha256(section.encode("utf-8")).hexdigest()
    ):
        errors.append(
            f"{label}: {target.identifier} Result reflection_report_digest must bind the exact reflection section"
        )
    if not has_substantive_markdown_content(section):
        errors.append(
            f"{label}: {target.identifier} Result must contain a substantive Architecture reflection and continuation decision section"
        )
    else:
        assumption_verdicts: dict[str, str] = {}
        owned_case_ids = {
            str(item)
            for item in target.metadata.get("product_goal_slice_gate_case_ids", [])
        }
        historical_owned_case_ids = binding.get("historical_owned_case_ids")
        if isinstance(historical_owned_case_ids, list):
            owned_case_ids.update(str(item) for item in historical_owned_case_ids)
        for subsection_name in REFLECTION_RESULT_REQUIRED_SUBSECTIONS:
            subsection = markdown_subsection_body(section, subsection_name)
            if not has_substantive_markdown_content(subsection):
                errors.append(
                    f"{label}: {target.identifier} reflection subsection is missing or empty: {subsection_name}"
                )
        due_assumption_ids = resolved_assumption_ids(binding.get("assumption_ids"))
        assumption_ids = list(due_assumption_ids)
        triggered_falsifier_cases: dict[str, str] = {}
        conditional_falsifiers = binding.get("conditional_falsifier_bindings")
        if blocked and isinstance(conditional_falsifiers, dict):
            for conditional_falsifier in conditional_falsifiers.values():
                if not isinstance(conditional_falsifier, dict):
                    continue
                conditional_assumption = conditional_falsifier.get("assumption_id")
                conditional_case = conditional_falsifier.get("case_id")
                if not isinstance(conditional_assumption, str) or not isinstance(
                    conditional_case, str
                ):
                    continue
                conditional_rows = (
                    markdown_table_case_rows(verification.body, conditional_case)
                    if verification is not None
                    else []
                )
                conditional_verdict = (
                    blocking_case_status_verdict(conditional_rows[0][6])
                    if len(conditional_rows) == 1
                    and len(conditional_rows[0]) == 7
                    else None
                )
                if conditional_verdict == "FAIL":
                    assumption_ids.append(conditional_assumption)
                    triggered_falsifier_cases[
                        conditional_assumption
                    ] = conditional_case
        if assumption_ids:
            for assumption_id in assumption_ids:
                rows = markdown_table_case_rows(section, str(assumption_id))
                if len(rows) != 1 or len(rows[0]) != 5:
                    errors.append(
                        f"{label}: {target.identifier} must record exactly one five-column verdict row for {assumption_id}"
                    )
                    continue
                row = rows[0]
                if assumption_expectations is not None:
                    expected_statement = assumption_expectations.get(assumption_id)
                    if expected_statement is None or row[1] != expected_statement:
                        errors.append(
                            f"{label}: {target.identifier} {assumption_id} Expected must exactly match the frozen Proposal assumption statement"
                        )
                for column_name, value in zip(
                    ("expected", "evidence", "impact"),
                    (row[1], row[2], row[4]),
                    strict=True,
                ):
                    if (
                        not value
                        or is_pending(value)
                        or is_absent_evidence(value)
                        or has_unresolved_placeholder(value)
                    ):
                        errors.append(
                            f"{label}: {target.identifier} {assumption_id} {column_name} must be resolved"
                        )
                normalized_verdict = row[3].upper()
                if normalized_verdict not in REFLECTION_ASSUMPTION_VERDICTS:
                    errors.append(
                        f"{label}: {target.identifier} {assumption_id} verdict must be SUPPORTED, FALSIFIED or UNRESOLVED"
                    )
                else:
                    assumption_verdicts[assumption_id] = normalized_verdict
                evidence_case_ids = [
                    item.strip().strip("`") for item in row[2].split(",")
                ]
                triggered_case = triggered_falsifier_cases.get(assumption_id)
                if triggered_case is not None and (
                    normalized_verdict not in {"FALSIFIED", "UNRESOLVED"}
                    or triggered_case not in evidence_case_ids
                ):
                    errors.append(
                        f"{label}: {target.identifier} triggered early falsifier {triggered_case} requires a FALSIFIED or UNRESOLVED {assumption_id} row citing that Case"
                    )
                if (
                    not evidence_case_ids
                    or len(evidence_case_ids) != len(set(evidence_case_ids))
                    or any(
                        re.fullmatch(
                            r"V-(?:PRE-)?[A-Z0-9]+(?:-[A-Z0-9]+)*", item
                        )
                        is None
                        for item in evidence_case_ids
                    )
                ):
                    errors.append(
                        f"{label}: {target.identifier} {assumption_id} exact evidence must be unique Verification Case IDs"
                    )
                else:
                    evidence_has_fail = False
                    for evidence_case_id in evidence_case_ids:
                        if (
                            evidence_case_id == case_id
                            or evidence_case_id.startswith("V-REFLECT-")
                        ):
                            errors.append(
                                f"{label}: {target.identifier} {assumption_id} must not use a reflection Case as self-evidence"
                            )
                            continue
                        if evidence_case_id not in owned_case_ids:
                            errors.append(
                                f"{label}: {target.identifier} {assumption_id} evidence Case must be owned by the Slice: {evidence_case_id}"
                            )
                            continue
                        if verification is not None:
                            evidence_rows = markdown_table_case_rows(
                                verification.body, evidence_case_id
                            )
                            if len(evidence_rows) == 1 and len(evidence_rows[0]) == 7:
                                evidence_status_verdict = (
                                    blocking_case_status_verdict(
                                        evidence_rows[0][6]
                                    )
                                )
                                if evidence_status_verdict == "FAIL":
                                    evidence_has_fail = True
                        errors.extend(
                            validate_blocking_verification_case(
                                verification,
                                evidence_case_id,
                                require_pass=not blocked,
                                require_executed=True,
                                expected_evidence=expected_verification_case_evidence(
                                    result.identifier, evidence_case_id
                                ),
                            )
                        )
                    if (
                        blocked
                        and normalized_verdict in {"FALSIFIED", "UNRESOLVED"}
                        and not evidence_has_fail
                    ):
                        errors.append(
                            f"{label}: {target.identifier} {assumption_id} {normalized_verdict} must bind at least one executed FAIL Case"
                        )
        decision_subsection = markdown_subsection_body(
            section, "Decision and rationale"
        )
        body_decisions = (
            re.findall(
                r"(?m)^[ ]{0,3}Decision:\s*(CONTINUE|ACCEPT|REWORK|REDIRECT|REJECT)\s*$",
                decision_subsection,
            )
            if decision_subsection is not None
            else []
        )
        if len(body_decisions) != 1:
            errors.append(
                f"{label}: {target.identifier} reflection Decision and rationale must contain exactly one Decision line"
            )
        elif body_decisions[0] != decision:
            errors.append(
                f"{label}: {target.identifier} reflection body Decision must match Result metadata and Manifest"
            )
        all_body_decisions = re.findall(
            r"(?m)^[ ]{0,3}Decision:\s*(CONTINUE|ACCEPT|REWORK|REDIRECT|REJECT)\s*$",
            section,
        )
        if len(all_body_decisions) != 1:
            errors.append(
                f"{label}: {target.identifier} exact reflection section must contain exactly one Decision line in total"
            )
        decision_owner_subsection = decision_subsection or ""
        body_decision_owners = re.findall(
            r"(?m)^[ ]{0,3}Decision owner:\s*(\S(?:.*\S)?)\s*$",
            decision_owner_subsection,
        )
        if len(body_decision_owners) != 1:
            errors.append(
                f"{label}: {target.identifier} reflection Decision and rationale must contain exactly one Decision owner line"
            )
        elif body_decision_owners[0] != result.metadata.get(
            "reflection_decision_owner"
        ):
            errors.append(
                f"{label}: {target.identifier} reflection body Decision owner must match Result metadata and Manifest"
            )
        all_body_decision_owners = re.findall(
            r"(?m)^[ ]{0,3}Decision owner:\s*(\S(?:.*\S)?)\s*$",
            section,
        )
        if len(all_body_decision_owners) != 1:
            errors.append(
                f"{label}: {target.identifier} exact reflection section must contain exactly one Decision owner line in total"
            )
        body_decision_refs = re.findall(
            r"(?m)^[ ]{0,3}Decision ref:\s*(codex-user-message:sha256:[0-9a-f]{64})\s*$",
            decision_subsection or "",
        )
        all_body_decision_refs = re.findall(
            r"(?m)^[ ]{0,3}Decision ref:\s*(codex-user-message:sha256:[0-9a-f]{64})\s*$",
            section,
        )
        if len(body_decision_refs) != 1 or len(all_body_decision_refs) != 1:
            errors.append(
                f"{label}: {target.identifier} exact reflection section must contain exactly one Decision ref line in the decision subsection"
            )
        elif body_decision_refs[0] != decision_ref:
            errors.append(
                f"{label}: {target.identifier} reflection body Decision ref must match Result metadata"
            )
        if decision in {"CONTINUE", "ACCEPT"} and due_assumption_ids and any(
            assumption_verdicts.get(assumption_id) != "SUPPORTED"
            for assumption_id in due_assumption_ids
        ):
            errors.append(
                f"{label}: {target.identifier} {decision} requires every bound critical assumption verdict to be SUPPORTED"
            )
        if blocked and not any(
            assumption_verdicts.get(assumption_id) in {"FALSIFIED", "UNRESOLVED"}
            for assumption_id in assumption_ids
        ):
            errors.append(
                f"{label}: blocked {target.identifier} requires at least one FALSIFIED or UNRESOLVED assumption backed by an executed FAIL Case"
            )
    errors.extend(
        validate_blocking_verification_case(
            verification,
            case_id,
            require_pass=True,
            expected_evidence=expected_verification_case_evidence(
                result.identifier, case_id
            ),
        )
    )
    return errors


def validate_paused_rework_slice(
    target: Document,
    manifest_slice: dict[str, object],
    by_id: dict[str, Document],
    reflection_binding: dict[str, object] | None,
    verification: Document | None,
    label: str,
    *,
    assumption_expectations: dict[str, str] | None = None,
    assumption_catalog_digest: str | None = None,
    rework_policy: dict[str, object] | None = None,
) -> list[str]:
    """Validate a non-coding same-Slice REWORK state without rewriting history."""

    errors: list[str] = []
    iteration = str(target.metadata.get("iteration", ""))
    result_ref = manifest_slice.get("result")
    result = by_id.get(result_ref) if isinstance(result_ref, str) else None
    result_dependencies = (
        result.metadata.get("depends_on", [])
        if result is not None and isinstance(result.metadata.get("depends_on", []), list)
        else []
    )
    valid_result = not (
        result is None
        or result.metadata.get("kind") != "iteration-result"
        or str(result.metadata.get("iteration", "")) != iteration
        or result.metadata.get("status") != "failed-preserved"
        or result.metadata.get("authority") != "execution-evidence"
        or target.identifier not in result_dependencies
        or f"{iteration}-VERIFICATION" not in result_dependencies
    )
    if not valid_result:
        errors.append(
            f"{label}: paused {target.identifier} must preserve same-iteration failed execution evidence"
        )
    else:
        assert result is not None
        freeze_digest = manifest_slice.get("product_code_freeze_digest")
        if not isinstance(freeze_digest, str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", freeze_digest
        ) is None:
            errors.append(
                f"{label}: paused {target.identifier} must bind an exact product_code_freeze_digest"
            )
        elif result.metadata.get("product_code_freeze_digest") != freeze_digest:
            errors.append(
                f"{label}: paused {target.identifier} must preserve the failed Result product code freeze"
            )
        errors.extend(
            validate_slice_reflection_result(
                target,
                result,
                reflection_binding,
                manifest_slice,
                verification,
                label,
                blocked=True,
                assumption_expectations=assumption_expectations,
                assumption_catalog_digest=assumption_catalog_digest,
                rework_policy=None,
                enforce_manifest_decision=False,
            )
        )
        if (
            manifest_slice.get("historical_reflection_decision")
            != result.metadata.get("reflection_decision")
            or manifest_slice.get("historical_reflection_decision_ref")
            != result.metadata.get("reflection_decision_ref")
        ):
            errors.append(
                f"{label}: paused {target.identifier} must preserve the historical Result decision and receipt separately from REWORK"
            )

    if manifest_slice.get("reflection_decision") != "REWORK":
        errors.append(
            f"{label}: paused {target.identifier} reflection_decision must equal REWORK"
        )
    decision_ref = manifest_slice.get("reflection_decision_ref")
    if not isinstance(decision_ref, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", decision_ref
    ) is None:
        errors.append(
            f"{label}: paused {target.identifier} must bind an exact REWORK decision receipt"
        )

    errors.extend(
        validate_rework_result_history(target, manifest_slice, by_id, label)
    )
    rework_refs = manifest_slice.get("rework_result_refs")
    if not isinstance(rework_refs, list) or not rework_refs or rework_refs[-1] != result_ref:
        errors.append(
            f"{label}: paused {target.identifier} must retain its failed Result as the latest rework prerequisite"
        )
    attempt = manifest_slice.get("rework_attempt_number")
    progress = manifest_slice.get("rework_progress_measure")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        errors.append(
            f"{label}: paused {target.identifier} must record a positive rework_attempt_number"
        )
    if (
        not isinstance(progress, str)
        or is_pending(progress)
        or has_unresolved_placeholder(progress)
    ):
        errors.append(
            f"{label}: paused {target.identifier} must freeze a measurable rework progress measure"
        )
    if isinstance(rework_policy, dict):
        limit = rework_policy.get("no_progress_attempt_limit")
        if (
            isinstance(attempt, int)
            and not isinstance(attempt, bool)
            and isinstance(limit, int)
            and not isinstance(limit, bool)
            and attempt > limit
        ):
            errors.append(
                f"{label}: paused {target.identifier} rework attempt cannot exceed the frozen no-progress limit without a direction review"
            )

    project_decision_ref = manifest_slice.get("project_decision_ref")
    project_decision = (
        by_id.get(project_decision_ref)
        if isinstance(project_decision_ref, str)
        else None
    )
    project_dependencies = (
        project_decision.metadata.get("depends_on", [])
        if project_decision is not None
        and isinstance(project_decision.metadata.get("depends_on", []), list)
        else []
    )
    if (
        project_decision is None
        or project_decision.metadata.get("kind") != "project-decision"
        or str(project_decision.metadata.get("iteration", "")) != iteration
        or project_decision.metadata.get("status") not in {"accepted", "completed"}
        or project_decision.metadata.get("decision") != "REWORK"
        or project_decision.metadata.get("decision_ref") != decision_ref
        or project_decision.metadata.get("coding_input") not in {False, "false"}
        or result_ref not in project_dependencies
        or project_decision.metadata.get("decision_ref")
        == (result.metadata.get("reflection_decision_ref") if result is not None else None)
    ):
        errors.append(
            f"{label}: paused {target.identifier} must bind an accepted non-coding REWORK project decision that preserves its failed Result"
        )
    return errors


def validate_historical_rework_result_integrity(
    target: Document,
    result: Document,
    label: str,
    *,
    expected_product_freeze: object = None,
    expected_reflection_digest: object = None,
) -> list[str]:
    """Recompute the immutable digests for every failed attempt in a repair loop."""

    errors: list[str] = []
    product_freeze = result.metadata.get("product_code_freeze_digest")
    if not isinstance(product_freeze, str) or re.fullmatch(
        r"sha256:[0-9a-f]{64}", product_freeze
    ) is None:
        errors.append(
            f"{label}: historical {result.identifier} must bind an exact product_code_freeze_digest"
        )
    elif expected_product_freeze is not None and product_freeze != expected_product_freeze:
        errors.append(
            f"{label}: historical {result.identifier} product code freeze must match the frozen rework history"
        )

    report_digest = result.metadata.get("reflection_report_digest")
    valid_report_digest = isinstance(report_digest, str) and re.fullmatch(
        r"sha256:[0-9a-f]{64}", report_digest
    ) is not None
    if not valid_report_digest:
        errors.append(
            f"{label}: historical {result.identifier} must bind an exact reflection_report_digest"
        )
    elif (
        expected_reflection_digest is not None
        and report_digest != expected_reflection_digest
    ):
        errors.append(
            f"{label}: historical {result.identifier} reflection digest must match the frozen rework history"
        )

    heading_count = len(
        re.findall(
            r"(?m)^[ ]{0,3}##[ \t]+Architecture reflection and continuation decision[ \t]*#*[ \t]*$",
            result.body,
        )
    )
    section = markdown_section_body(
        result, "Architecture reflection and continuation decision"
    )
    if heading_count != 1 or not has_substantive_markdown_content(section):
        errors.append(
            f"{label}: historical {result.identifier} must retain one substantive reflection section"
        )
    elif valid_report_digest and report_digest != "sha256:" + hashlib.sha256(
        section.encode("utf-8")
    ).hexdigest():
        errors.append(
            f"{label}: historical {result.identifier} reflection_report_digest must bind the exact reflection section"
        )

    decision = result.metadata.get("reflection_decision")
    if decision not in {"REWORK", "REDIRECT", "REJECT"}:
        errors.append(
            f"{label}: historical {result.identifier} must retain its failed reflection decision"
        )
    decision_ref = result.metadata.get("reflection_decision_ref")
    if not isinstance(decision_ref, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", decision_ref
    ) is None:
        errors.append(
            f"{label}: historical {result.identifier} must retain an exact reflection decision receipt"
        )
    return errors


def validate_rework_result_history(
    target: Document,
    manifest_slice: dict[str, object],
    by_id: dict[str, Document],
    label: str,
) -> list[str]:
    """Preserve prior failed attempts when the same Slice is reauthorized."""

    refs = manifest_slice.get("rework_result_refs")
    history_required = any(
        field in manifest_slice
        for field in (
            "project_decision_ref",
            "rework_attempt_number",
            "rework_prerequisite_result",
        )
    )
    if refs is None:
        return (
            [
                f"{label}: development.slices.{target.identifier}.rework_result_refs is required for same-Slice reauthorization"
            ]
            if history_required
            else []
        )
    if not isinstance(refs, list):
        return [
            f"{label}: development.slices.{target.identifier}.rework_result_refs must be a sequence"
        ]
    normalized = [str(item) for item in refs]
    errors: list[str] = []
    if len(normalized) != len(set(normalized)):
        errors.append(
            f"{label}: development.slices.{target.identifier}.rework_result_refs must be unique"
        )
    attempt = manifest_slice.get("rework_attempt_number")
    if (
        isinstance(attempt, bool)
        or not isinstance(attempt, int)
        or attempt != len(normalized)
    ):
        errors.append(
            f"{label}: development.slices.{target.identifier}.rework_attempt_number must equal the complete failed-Result history count"
        )

    history_freezes = manifest_slice.get("rework_history_freezes")
    if len(normalized) > 1 and (
        not isinstance(history_freezes, dict)
        or set(history_freezes) != set(normalized)
    ):
        errors.append(
            f"{label}: multi-attempt {target.identifier} must freeze every Result product and reflection digest"
        )
        history_freezes = None

    iteration = str(target.metadata.get("iteration", ""))
    for reference in normalized:
        result = by_id.get(reference)
        dependencies = (
            result.metadata.get("depends_on", [])
            if result is not None
            and isinstance(result.metadata.get("depends_on", []), list)
            else []
        )
        if (
            result is None
            or result.metadata.get("kind") != "iteration-result"
            or result.metadata.get("status") != "failed-preserved"
            or str(result.metadata.get("iteration", "")) != iteration
            or target.identifier not in dependencies
            or f"{iteration}-VERIFICATION" not in dependencies
        ):
            errors.append(
                f"{label}: rework_result_refs item must preserve a failed attempt for the same Slice: {reference}"
            )
            continue
        freeze_entry = (
            history_freezes.get(reference)
            if isinstance(history_freezes, dict)
            else None
        )
        if len(normalized) > 1 and not isinstance(freeze_entry, dict):
            errors.append(
                f"{label}: multi-attempt {target.identifier} is missing frozen digests for {reference}"
            )
            freeze_entry = {}
        errors.extend(
            validate_historical_rework_result_integrity(
                target,
                result,
                label,
                expected_product_freeze=(
                    freeze_entry.get("product_code_freeze_digest")
                    if isinstance(freeze_entry, dict)
                    else None
                ),
                expected_reflection_digest=(
                    freeze_entry.get("reflection_report_digest")
                    if isinstance(freeze_entry, dict)
                    else None
                ),
            )
        )
    expected_prerequisite = normalized[-1] if normalized else "none"
    if manifest_slice.get("rework_prerequisite_result") != expected_prerequisite:
        errors.append(
            f"{label}: development.slices.{target.identifier}.rework_prerequisite_result must equal {expected_prerequisite}"
        )
    return errors


def validate_rework_authorization_receipt(
    target: Document,
    manifest_slice: dict[str, object],
    by_id: dict[str, Document],
    label: str,
) -> list[str]:
    """Require a new authorization after both the failed attempt and REWORK decision."""

    rework_refs = manifest_slice.get("rework_result_refs")
    if not isinstance(rework_refs, list) or not rework_refs:
        return []
    errors: list[str] = []
    forbidden_receipts: set[str] = set()
    iteration = str(target.metadata.get("iteration", ""))
    readiness = by_id.get(f"{iteration}-READINESS")
    current_readiness_authorization = (
        readiness.metadata.get("product_goal_alignment_review_ref")
        if readiness is not None
        else None
    )
    combined_readiness_authorization = (
        manifest_slice.get("authorization_combines_current_readiness_acceptance")
        is True
    )
    if (
        isinstance(current_readiness_authorization, str)
        and not combined_readiness_authorization
    ):
        forbidden_receipts.add(current_readiness_authorization)
    project_decision_ref = manifest_slice.get("project_decision_ref")
    project_decision = (
        by_id.get(project_decision_ref)
        if isinstance(project_decision_ref, str)
        else None
    )
    if project_decision is not None and isinstance(
        project_decision.metadata.get("decision_ref"), str
    ):
        forbidden_receipts.add(str(project_decision.metadata["decision_ref"]))
    for rework_ref in rework_refs:
        prior_result = by_id.get(str(rework_ref))
        if prior_result is not None and isinstance(
            prior_result.metadata.get("reflection_decision_ref"), str
        ):
            forbidden_receipts.add(
                str(prior_result.metadata["reflection_decision_ref"])
            )
        if prior_result is not None and isinstance(
            prior_result.metadata.get("slice_authorization_ref"), str
        ):
            forbidden_receipts.add(str(prior_result.metadata["slice_authorization_ref"]))

    prior_authorizations = manifest_slice.get("prior_authorization_refs")
    if (
        not isinstance(prior_authorizations, list)
        or len(prior_authorizations) != len(rework_refs)
        or len(prior_authorizations) != len(set(map(str, prior_authorizations)))
        or any(
            not isinstance(reference, str)
            or re.fullmatch(r"codex-user-message:sha256:[0-9a-f]{64}", reference)
            is None
            for reference in prior_authorizations
        )
    ):
        errors.append(
            f"{label}: reauthorized {target.identifier} must freeze one unique prior authorization receipt per failed Result"
        )
        prior_authorizations = []
    historical_initial_authorization = (
        readiness.metadata.get("historical_product_goal_alignment_review_ref")
        if readiness is not None
        else None
    )
    if not isinstance(historical_initial_authorization, str):
        first_rework_result = by_id.get(str(rework_refs[0]))
        historical_initial_authorization = (
            first_rework_result.metadata.get("slice_authorization_ref")
            if first_rework_result is not None
            else None
        )
    if (
        isinstance(historical_initial_authorization, str)
        and prior_authorizations
        and prior_authorizations[0] != historical_initial_authorization
    ):
        errors.append(
            f"{label}: reauthorized {target.identifier} must preserve its initial Readiness authorization as the first prior receipt"
        )
    for index, rework_ref in enumerate(rework_refs[1:], start=1):
        prior_result = by_id.get(str(rework_ref))
        expected_authorization = (
            prior_authorizations[index]
            if index < len(prior_authorizations)
            else None
        )
        if (
            prior_result is None
            or prior_result.metadata.get("slice_authorization_ref")
            != expected_authorization
        ):
            errors.append(
                f"{label}: reauthorized {target.identifier} must bind every later failed Result to its frozen prior authorization receipt"
            )

    authorization_ref = manifest_slice.get("authorization_ref")
    if not isinstance(authorization_ref, str) or re.fullmatch(
        r"codex-user-message:sha256:[0-9a-f]{64}", authorization_ref
    ) is None:
        errors.append(
            f"{label}: reauthorized {target.identifier} must bind an exact new user authorization receipt"
        )
    elif authorization_ref in forbidden_receipts or authorization_ref in set(
        map(str, prior_authorizations)
    ):
        errors.append(
            f"{label}: reauthorized {target.identifier} must use a new user authorization receipt after the failed Result and REWORK decision"
        )
    if combined_readiness_authorization and (
        not isinstance(current_readiness_authorization, str)
        or authorization_ref != current_readiness_authorization
    ):
        errors.append(
            f"{label}: combined Readiness acceptance and Slice reauthorization must use the same exact user receipt"
        )
    return errors


def rework_project_decision_refs_for_slice(
    target: Document, by_id: dict[str, Document]
) -> set[str]:
    """Return accepted REWORK decisions whose preserved Result belongs to this Slice."""

    iteration = str(target.metadata.get("iteration", ""))
    references: set[str] = set()
    for document in by_id.values():
        if (
            document.metadata.get("kind") != "project-decision"
            or str(document.metadata.get("iteration", "")) != iteration
            or document.metadata.get("decision") != "REWORK"
            or document.metadata.get("status") not in {"accepted", "completed"}
        ):
            continue
        dependencies = document.metadata.get("depends_on", [])
        if not isinstance(dependencies, list):
            continue
        for dependency in dependencies:
            result = by_id.get(str(dependency))
            result_dependencies = (
                result.metadata.get("depends_on", [])
                if result is not None
                and isinstance(result.metadata.get("depends_on", []), list)
                else []
            )
            if (
                result is not None
                and result.metadata.get("kind") == "iteration-result"
                and target.identifier in result_dependencies
            ):
                references.add(document.identifier)
                break
    return references


def validate_superseded_iteration_plan(
    new_refs: list[str],
    by_id: dict[str, Document],
    manifest: dict[str, object],
    label: str,
) -> list[str]:
    """Ensure a pre-execution replacement cannot hide authorized or completed work."""

    errors: list[str] = []
    iteration_data = manifest.get("iteration")
    iteration = (
        str(iteration_data.get("id")) if isinstance(iteration_data, dict) else ""
    )
    development = manifest.get("development")
    raw_slices = development.get("slices") if isinstance(development, dict) else None
    if not isinstance(raw_slices, dict):
        return [f"{label}: superseded iteration must preserve its planned Slice mapping"]
    if set(raw_slices) != set(new_refs):
        errors.append(
            f"{label}: superseded iteration Slice mapping must exactly match new_capability_slice_refs"
        )
    for reference in new_refs:
        target = by_id.get(reference)
        state = raw_slices.get(reference)
        if (
            target is None
            or target.metadata.get("kind") != "development-slice"
            or str(target.metadata.get("iteration", "")) != iteration
            or target.metadata.get("status") != "proposed"
            or target.metadata.get("authority") != "proposed-development"
            or is_true(target.metadata.get("coding_input", ""))
        ):
            errors.append(
                f"{label}: superseded pre-execution Slice must remain proposed and non-coding: {reference}"
            )
        if not isinstance(state, dict):
            errors.append(
                f"{label}: superseded iteration is missing planned Slice state: {reference}"
            )
            continue
        expected = {
            "status": "proposed",
            "coding_input": False,
            "result": "not-executed",
            "product_code_freeze_digest": "not-executed",
            "authorized_by": "not-authorized",
            "authorized_at": "not-authorized",
            "authorization_ref": "not-authorized",
        }
        for field, value in expected.items():
            if state.get(field) != value:
                errors.append(
                    f"{label}: superseded {reference} {field} must equal {value}"
                )
    authorization = manifest.get("authorization")
    if not isinstance(authorization, dict) or authorization.get("active_slice") != "none":
        errors.append(
            f"{label}: superseded iteration must have authorization.active_slice none"
        )
    if not isinstance(authorization, dict) or (
        authorization.get("authorized_by"),
        authorization.get("authorized_at"),
        authorization.get("authorization_ref"),
    ) not in {
        ("pending", "pending", "pending"),
        ("not-authorized", "not-authorized", "not-authorized"),
    }:
        errors.append(
            f"{label}: superseded pre-execution iteration must retain an unresolved top-level authorization"
        )
    if not isinstance(iteration_data, dict) or is_true(
        iteration_data.get("coding_input", "")
    ):
        errors.append(
            f"{label}: superseded pre-execution iteration must remain non-coding"
        )
    for document in by_id.values():
        if str(document.metadata.get("iteration", "")) != iteration:
            continue
        kind = document.metadata.get("kind")
        if kind not in {"iteration-result", "iteration-acceptance"}:
            continue
        if (
            document.metadata.get("authority") == "execution-evidence"
            or document.metadata.get("status")
            in {"accepted", "completed", "failed-preserved"}
            or kind == "iteration-acceptance"
        ):
            errors.append(
                f"{label}: superseded pre-execution iteration must not contain execution or accepted Result evidence: {document.identifier}"
            )
    return errors


def validate_product_goal_slice_sequence(
    new_refs: list[str],
    by_id: dict[str, Document],
    label: str,
    *,
    manifest: dict[str, object] | None = None,
    verification: Document | None = None,
    require_completed: bool = False,
    require_rejected: bool = False,
    require_paused: bool = False,
) -> list[str]:
    """Require an active, paused, or terminal sequential-development state."""

    errors: list[str] = []
    slices: list[Document] = []
    for reference in new_refs:
        target = by_id.get(reference)
        if target is None or target.metadata.get("kind") != "development-slice":
            continue
        slices.append(target)
    if len(slices) != len(new_refs):
        return errors

    statuses = [str(item.metadata.get("status", "")) for item in slices]
    development_slices: dict[str, object] = {}
    if manifest is not None:
        development = manifest.get("development")
        if isinstance(development, dict):
            raw_slices = development.get("slices")
            if isinstance(raw_slices, dict):
                development_slices = raw_slices
    alignment = manifest.get("product_goal_alignment") if manifest is not None else None
    raw_rework_policy = manifest.get("rework_policy") if manifest is not None else None
    rework_policy = raw_rework_policy if isinstance(raw_rework_policy, dict) else None
    raw_experience_policy = (
        manifest.get("experience_delivery_policy") if manifest is not None else None
    )
    experience_policy = (
        raw_experience_policy if isinstance(raw_experience_policy, dict) else None
    )
    raw_provider_policy = (
        manifest.get("provider_route_policy") if manifest is not None else None
    )
    provider_policy = (
        raw_provider_policy if isinstance(raw_provider_policy, dict) else None
    )
    historical_pre_policy_result_refs: set[str] = set()
    if experience_policy is not None:
        raw_historical_refs = experience_policy.get(
            "historical_pre_policy_result_refs"
        )
        if isinstance(raw_historical_refs, list):
            historical_pre_policy_result_refs = {
                str(reference) for reference in raw_historical_refs
            }
            owner_slice_ref = experience_policy.get("owner_slice_ref")
            for reference in historical_pre_policy_result_refs:
                historical_result = by_id.get(reference)
                historical_dependencies = (
                    historical_result.metadata.get("depends_on", [])
                    if historical_result is not None
                    and isinstance(
                        historical_result.metadata.get("depends_on", []), list
                    )
                    else []
                )
                if (
                    historical_result is None
                    or historical_result.metadata.get("kind") != "iteration-result"
                    or historical_result.metadata.get("status") != "failed-preserved"
                    or owner_slice_ref not in historical_dependencies
                    or "experience_delivery_policy_schema"
                    in historical_result.metadata
                ):
                    errors.append(
                        f"{label}: historical pre-policy experience Result "
                        f"{reference} must be a failed-preserved Result for the owner "
                        "Slice without successor-policy audit fields"
                    )
    early_canary_by_slice: dict[str, dict[str, object]] = {}
    early_comparison_by_slice: dict[str, dict[str, object]] = {}
    reflection_by_slice: dict[str, dict[str, object]] = {}
    if isinstance(alignment, dict):
        reflection_by_slice = reflection_gate_bindings_by_slice(alignment)
        canary_bindings = alignment.get("early_hidden_canary_bindings")
        if isinstance(canary_bindings, dict):
            for binding in canary_bindings.values():
                if not isinstance(binding, dict):
                    continue
                new_slice_ref = binding.get("new_slice_ref")
                if isinstance(new_slice_ref, str):
                    early_canary_by_slice[new_slice_ref] = binding
        comparison_binding = alignment.get("early_comparison_binding")
        if isinstance(comparison_binding, dict):
            new_slice_ref = comparison_binding.get("new_slice_ref")
            if isinstance(new_slice_ref, str):
                early_comparison_by_slice[new_slice_ref] = comparison_binding
        alpha_comparison_binding = alignment.get("alpha_agent_comparison_binding")
        if isinstance(alpha_comparison_binding, dict):
            new_slice_ref = alpha_comparison_binding.get("new_slice_ref")
            if isinstance(new_slice_ref, str):
                if new_slice_ref in early_comparison_by_slice:
                    errors.append(
                        f"{label}: a Slice cannot own both Alpha and hidden Agent comparison bindings"
                    )
                else:
                    early_comparison_by_slice[new_slice_ref] = alpha_comparison_binding
    assumption_catalog_digest: str | None = None
    assumption_expectations: dict[str, str] | None = None
    historical_assumption_catalog_digest: str | None = None
    historical_assumption_expectations: dict[str, str] | None = None
    historical_result_ref: str | None = None
    if slices and requires_reflection_gate(
        str(slices[0].metadata.get("iteration", ""))
    ):
        proposal_id = f"{slices[0].metadata.get('iteration')}-PROPOSAL"
        if manifest is not None:
            (
                assumption_catalog_digest,
                parsed_assumption_expectations,
                historical_assumption_catalog_digest,
                parsed_historical_expectations,
                catalog_errors,
            ) = critical_assumption_catalogs(
                by_id.get(proposal_id), manifest, label
            )
            cutover = manifest.get("critical_assumption_catalog_cutover")
            if isinstance(cutover, dict) and isinstance(
                cutover.get("historical_result_ref"), str
            ):
                historical_result_ref = str(cutover["historical_result_ref"])
        else:
            (
                assumption_catalog_digest,
                parsed_assumption_expectations,
                catalog_errors,
            ) = critical_assumption_catalog(by_id.get(proposal_id))
            historical_assumption_catalog_digest = assumption_catalog_digest
            parsed_historical_expectations = parsed_assumption_expectations
        errors.extend(catalog_errors)
        assumption_expectations = parsed_assumption_expectations
        historical_assumption_expectations = parsed_historical_expectations
        if not isinstance(alignment, dict) or alignment.get(
            "critical_assumption_catalog_digest"
        ) != assumption_catalog_digest:
            errors.append(
                f"{label}: critical_assumption_catalog_digest must match the exact current assumption catalog"
            )
        critical_assumption_ids = (
            resolved_assumption_ids(alignment.get("critical_assumption_ids"))
            if isinstance(alignment, dict)
            else []
        )
        if critical_assumption_ids != list(parsed_assumption_expectations):
            errors.append(
                f"{label}: critical_assumption_ids must exactly match the current assumption catalog order"
            )

    def reflection_inputs_for_result(
        slice_ref: str, result_ref: object
    ) -> tuple[dict[str, object] | None, dict[str, str] | None, str | None]:
        binding = reflection_by_slice.get(slice_ref)
        if result_ref != historical_result_ref:
            return binding, assumption_expectations, assumption_catalog_digest
        historical_binding = dict(binding) if isinstance(binding, dict) else None
        if historical_binding is not None and historical_assumption_expectations:
            historical_result = (
                by_id.get(historical_result_ref)
                if isinstance(historical_result_ref, str)
                else None
            )
            historical_case_id = (
                historical_result.metadata.get("reflection_gate_case_id")
                if historical_result is not None
                else None
            )
            if isinstance(historical_case_id, str):
                historical_binding["case_id"] = historical_case_id
            historical_binding["historical_owned_case_ids"] = list(
                ITER010_HISTORICAL_GATE_CASES
            )
            current_ids = resolved_assumption_ids(
                historical_binding.get("assumption_ids")
            )
            historical_binding["assumption_ids"] = ",".join(
                assumption_id
                for assumption_id in current_ids
                if assumption_id in historical_assumption_expectations
            )
            conditional = historical_binding.get("conditional_falsifier_bindings")
            if isinstance(conditional, dict):
                historical_binding["conditional_falsifier_bindings"] = {
                    "cross_project_generalization": {
                        "assumption_id": "A4",
                        "case_id": "V-XD-001",
                    },
                    "final_quality_and_value": {
                        "assumption_id": "A5",
                        "case_id": "V-ANSWER-001",
                    },
                }
        return (
            historical_binding,
            historical_assumption_expectations,
            historical_assumption_catalog_digest,
        )
    completed_result_refs = [
        manifest_slice.get("result")
        for target, status in zip(slices, statuses, strict=True)
        if status == "completed"
        and isinstance(
            (manifest_slice := development_slices.get(target.identifier)), dict
        )
        and isinstance(manifest_slice.get("result"), str)
    ]
    if len(completed_result_refs) != len(set(completed_result_refs)):
        errors.append(
            f"{label}: each completed Slice must bind a unique Slice Result"
        )
    active_indexes = [
        index for index, status in enumerate(statuses) if status in ACTIVE_SLICE_STATUSES
    ]
    blocked_indexes = [
        index for index, status in enumerate(statuses) if status == "blocked"
    ]
    paused_indexes = [
        index for index, status in enumerate(statuses) if status == "paused"
    ]
    terminal_mode_count = sum(
        bool(item) for item in (require_completed, require_rejected, require_paused)
    )
    if terminal_mode_count > 1:
        errors.append(
            f"{label}: iteration cannot be completed, rejected and paused at the same time"
        )
    elif require_completed:
        if any(status != "completed" for status in statuses):
            errors.append(
                f"{label}: completed iteration requires every new capability slice to be completed"
            )
    elif require_rejected:
        if len(blocked_indexes) != 1:
            errors.append(
                f"{label}: rejected iteration requires exactly one blocked new capability slice"
            )
        else:
            blocked_index = blocked_indexes[0]
            if any(status != "completed" for status in statuses[:blocked_index]):
                errors.append(
                    f"{label}: slices before the blocked slice must be completed in Manifest order"
                )
            if any(status != "proposed" for status in statuses[blocked_index + 1 :]):
                errors.append(
                    f"{label}: slices after the blocked slice must remain proposed"
                )
        if active_indexes:
            errors.append(f"{label}: rejected iteration must not have an active slice")
    elif require_paused:
        if len(paused_indexes) != 1:
            errors.append(
                f"{label}: paused iteration requires exactly one paused new capability slice"
            )
        else:
            paused_index = paused_indexes[0]
            if any(status != "completed" for status in statuses[:paused_index]):
                errors.append(
                    f"{label}: slices before the paused slice must be completed in Manifest order"
                )
            if any(status != "proposed" for status in statuses[paused_index + 1 :]):
                errors.append(
                    f"{label}: slices after the paused slice must remain proposed"
                )
        if active_indexes or blocked_indexes:
            errors.append(
                f"{label}: paused iteration must not have an active or rejected slice"
            )
    elif paused_indexes:
        errors.append(
            f"{label}: a paused Slice requires the iteration index and Manifest to be paused"
        )
    elif len(active_indexes) != 1:
        errors.append(
            f"{label}: execution requires exactly one authorized/in-progress new capability slice"
        )
    else:
        active_index = active_indexes[0]
        if any(status != "completed" for status in statuses[:active_index]):
            errors.append(
                f"{label}: slices before the active slice must be completed in Manifest order"
            )
        if any(status != "proposed" for status in statuses[active_index + 1 :]):
            errors.append(
                f"{label}: slices after the active slice must remain proposed"
            )

    if manifest is not None:
        authorization = manifest.get("authorization")
        if not isinstance(authorization, dict):
            errors.append(f"{label}: authorization must be a mapping")
        else:
            expected_active_slice = (
                "none"
                if require_completed
                or require_rejected
                or require_paused
                or len(active_indexes) != 1
                else slices[active_indexes[0]].identifier
            )
            if authorization.get("active_slice") != expected_active_slice:
                errors.append(
                    f"{label}: authorization.active_slice must equal the unique active Slice or none after completion"
                )
            readiness = by_id.get(
                f"{slices[0].metadata.get('iteration')}-READINESS"
            )
            if readiness is not None:
                for manifest_field, readiness_field in (
                    ("authorized_by", "authorized_by"),
                    ("authorized_at", "authorized_at"),
                    ("authorization_ref", "product_goal_alignment_review_ref"),
                ):
                    if authorization.get(manifest_field) != readiness.metadata.get(
                        readiness_field
                    ):
                        errors.append(
                            f"{label}: authorization.{manifest_field} must match the accepted Readiness"
                        )

    seen_authorization_refs: set[str] = set()
    decision_forbidden_refs: set[str] = set()
    seen_reflection_decision_refs: set[str] = set()
    top_authorized_at_value: datetime | None = None
    previous_slice_authorized_at: datetime | None = None
    if isinstance(alignment, dict):
        positive_value_freeze_receipt = alignment.get(
            "positive_value_freeze_receipt_ref"
        )
        if isinstance(positive_value_freeze_receipt, str) and re.fullmatch(
            r"codex-user-message:sha256:[0-9a-f]{64}",
            positive_value_freeze_receipt,
        ) is not None:
            decision_forbidden_refs.add(positive_value_freeze_receipt)
    if manifest is not None:
        top_authorization = manifest.get("authorization")
        top_authorization_ref = (
            top_authorization.get("authorization_ref")
            if isinstance(top_authorization, dict)
            else None
        )
        if isinstance(top_authorization_ref, str) and re.fullmatch(
            r"codex-user-message:sha256:[0-9a-f]{64}", top_authorization_ref
        ) is not None:
            decision_forbidden_refs.add(top_authorization_ref)
        top_authorized_at = (
            top_authorization.get("authorized_at")
            if isinstance(top_authorization, dict)
            else None
        )
        if isinstance(top_authorized_at, str):
            try:
                top_authorized_at_value = datetime.fromisoformat(
                    top_authorized_at.replace("Z", "+00:00")
                )
            except ValueError:
                top_authorized_at_value = None
    for index, target in enumerate(slices):
        reflection_result: Document | None = None
        status = statuses[index]
        authority = target.metadata.get("authority")
        coding_input_value = target.metadata.get("coding_input", "")
        coding_input = is_true(coding_input_value)
        if (
            require_rejected
            and str(coding_input_value).strip().lower() != "false"
        ):
            errors.append(
                f"{target.relative_path}: rejected iteration slices must use coding_input false"
            )
        if status == "proposed" and (
            authority != "proposed-development" or coding_input
        ):
            errors.append(
                f"{target.relative_path}: proposed slice must use proposed-development with coding_input false"
            )
        elif status in ACTIVE_SLICE_STATUSES and (
            authority != "current-development" or not coding_input
        ):
            errors.append(
                f"{target.relative_path}: active slice must use current-development with coding_input true"
            )
        elif status == "completed" and (
            authority != "historical-development" or coding_input
        ):
            errors.append(
                f"{target.relative_path}: completed slice must use historical-development with coding_input false"
            )
        elif status == "blocked" and (
            authority != "development-evidence" or coding_input
        ):
            errors.append(
                f"{target.relative_path}: blocked slice must use development-evidence with coding_input false"
            )
        elif status == "paused" and (
            authority not in {"development-evidence", "project-decision"}
            or coding_input
        ):
            errors.append(
                f"{target.relative_path}: paused slice must use non-coding evidence or project-decision authority"
            )
        elif status not in {
            "proposed",
            "authorized",
            "in-progress",
            "completed",
            "blocked",
            "paused",
        }:
            errors.append(
                f"{target.relative_path}: slice status is invalid for sequential development"
            )

        manifest_slice = development_slices.get(target.identifier)
        if isinstance(manifest_slice, dict) and status in {
            "authorized",
            "in-progress",
            "completed",
            "blocked",
            "paused",
        }:
            if manifest_slice.get("authorized_by") != "user":
                errors.append(
                    f"{label}: {status} {target.identifier} authorized_by must equal user"
                )
            authorized_at = manifest_slice.get("authorized_at")
            if not isinstance(authorized_at, str) or re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:Z|[+-][0-9]{2}:[0-9]{2})",
                authorized_at,
            ) is None:
                errors.append(
                    f"{label}: {status} {target.identifier} authorized_at must be an ISO-8601 timestamp with timezone"
                )
            else:
                try:
                    authorized_at_value = datetime.fromisoformat(
                        authorized_at.replace("Z", "+00:00")
                    )
                except ValueError:
                    errors.append(
                        f"{label}: {status} {target.identifier} authorized_at must be a real ISO-8601 timestamp"
                    )
                else:
                    if (
                        top_authorized_at_value is not None
                        and authorized_at_value < top_authorized_at_value
                    ):
                        errors.append(
                            f"{label}: {target.identifier} authorization cannot precede Readiness authorization"
                        )
                    if (
                        previous_slice_authorized_at is not None
                        and authorized_at_value <= previous_slice_authorized_at
                    ):
                        errors.append(
                            f"{label}: Slice authorization timestamps must be strictly increasing"
                        )
                    previous_slice_authorized_at = authorized_at_value
            authorization_ref = manifest_slice.get("authorization_ref")
            if not isinstance(authorization_ref, str) or re.fullmatch(
                r"codex-user-message:sha256:[0-9a-f]{64}", authorization_ref
            ) is None:
                errors.append(
                    f"{label}: {status} {target.identifier} authorization_ref must bind an exact user message digest"
                )
            elif authorization_ref in seen_authorization_refs:
                errors.append(
                    f"{label}: {target.identifier} must use a new user authorization message after the prior Slice reflection"
                )
            else:
                seen_authorization_refs.add(authorization_ref)
                decision_forbidden_refs.add(authorization_ref)

        if manifest is not None and not isinstance(manifest_slice, dict):
            errors.append(
                f"{label}: development.slices must define {target.identifier}"
            )
        elif isinstance(manifest_slice, dict):
            slice_rework_decisions = rework_project_decision_refs_for_slice(
                target, by_id
            )
            if slice_rework_decisions:
                if manifest_slice.get("project_decision_ref") not in slice_rework_decisions:
                    errors.append(
                        f"{label}: {target.identifier} must retain its irreversible REWORK project decision"
                    )
                if not isinstance(
                    manifest_slice.get("rework_result_refs"), list
                ) or not manifest_slice.get("rework_result_refs"):
                    errors.append(
                        f"{label}: {target.identifier} must retain all failed rework Results"
                    )
                elif status in {"blocked", "completed"}:
                    errors.extend(
                        validate_rework_result_history(
                            target,
                            manifest_slice,
                            by_id,
                            label,
                        )
                    )
            if manifest_slice.get("status") != status:
                errors.append(
                    f"{label}: development.slices.{target.identifier}.status must match the Slice document"
                )
            manifest_coding_input = manifest_slice.get("coding_input")
            if isinstance(manifest_coding_input, bool):
                manifest_coding = manifest_coding_input
            else:
                manifest_coding = is_true(manifest_coding_input)
            if manifest_coding != coding_input:
                errors.append(
                    f"{label}: development.slices.{target.identifier}.coding_input must match the Slice document"
                )
            if (
                require_rejected
                and str(manifest_coding_input).strip().lower() != "false"
            ):
                errors.append(
                    f"{label}: rejected development.slices.{target.identifier}.coding_input must be false"
                )

            if status == "proposed":
                for field in ("result", "authorized_by", "authorized_at", "authorization_ref"):
                    if manifest_slice.get(field) != (
                        "not-executed" if field == "result" else "not-authorized"
                    ):
                        errors.append(
                            f"{label}: proposed {target.identifier} {field} must remain unresolved without fabricating authorization"
                        )
                if manifest_slice.get("product_code_freeze_digest") != "not-executed":
                    errors.append(
                        f"{label}: proposed {target.identifier} product_code_freeze_digest must be not-executed"
                    )
                if (
                    requires_reflection_gate(target.metadata.get("iteration", ""))
                    and manifest_slice.get("reflection_decision") != "not-executed"
                ):
                    errors.append(
                        f"{label}: proposed {target.identifier} reflection_decision must be not-executed"
                    )
                if requires_reflection_gate(target.metadata.get("iteration", "")):
                    expected_prerequisite = (
                        "none-first-slice" if index == 0 else "not-executed"
                    )
                    if (
                        manifest_slice.get("reflection_prerequisite_result")
                        != expected_prerequisite
                    ):
                        errors.append(
                            f"{label}: proposed {target.identifier} reflection_prerequisite_result must equal {expected_prerequisite}"
                        )
            elif status in ACTIVE_SLICE_STATUSES:
                iteration_state = manifest.get("iteration") if manifest is not None else None
                manifest_rework_required = (
                    isinstance(iteration_state, dict)
                    and iteration_state.get("current_decision") == "REWORK"
                ) or bool(slice_rework_decisions)
                if manifest_rework_required:
                    project_decision_ref = manifest_slice.get("project_decision_ref")
                    project_decision = (
                        by_id.get(project_decision_ref)
                        if isinstance(project_decision_ref, str)
                        else None
                    )
                    if (
                        project_decision is None
                        or project_decision.metadata.get("kind") != "project-decision"
                        or project_decision.metadata.get("decision") != "REWORK"
                        or project_decision_ref not in slice_rework_decisions
                    ):
                        errors.append(
                            f"{label}: reauthorized {target.identifier} must retain its REWORK project decision"
                        )
                    if not isinstance(manifest_slice.get("rework_result_refs"), list) or not manifest_slice.get("rework_result_refs"):
                        errors.append(
                            f"{label}: reauthorized {target.identifier} must retain all failed rework Results"
                        )
                errors.extend(
                    validate_rework_result_history(
                        target,
                        manifest_slice,
                        by_id,
                        label,
                    )
                )
                errors.extend(
                    validate_rework_authorization_receipt(
                        target,
                        manifest_slice,
                        by_id,
                        label,
                    )
                )
                result_ref = manifest_slice.get("result")
                if result_ref not in {"not-executed", "in-progress"}:
                    errors.append(
                        f"{label}: active {target.identifier} result must be not-executed or in-progress"
                    )
                freeze_digest = manifest_slice.get("product_code_freeze_digest")
                if freeze_digest != "not-executed" and (
                    not isinstance(freeze_digest, str)
                    or re.fullmatch(r"sha256:[0-9a-f]{64}", freeze_digest) is None
                ):
                    errors.append(
                        f"{label}: active {target.identifier} product_code_freeze_digest must be not-executed or an exact sha256 digest"
                    )
                if (
                    requires_reflection_gate(target.metadata.get("iteration", ""))
                    and manifest_slice.get("reflection_decision")
                    not in {"not-executed", "in-progress"}
                ):
                    errors.append(
                        f"{label}: active {target.identifier} reflection_decision must be not-executed or in-progress"
                    )
                if (
                    requires_reflection_gate(target.metadata.get("iteration", ""))
                    and index == 0
                    and manifest_slice.get("reflection_prerequisite_result")
                    != "none-first-slice"
                ):
                    errors.append(
                        f"{label}: first active Slice reflection_prerequisite_result must equal none-first-slice"
                    )
            elif status == "blocked":
                result_ref = manifest_slice.get("result")
                result = by_id.get(result_ref) if isinstance(result_ref, str) else None
                reflection_result = result
                dependencies: list[object] = []
                if result is not None and isinstance(
                    result.metadata.get("depends_on", []), list
                ):
                    dependencies = result.metadata.get("depends_on", [])  # type: ignore[assignment]
                if (
                    result is None
                    or result.metadata.get("kind") != "iteration-result"
                    or str(result.metadata.get("iteration", ""))
                    != str(target.metadata.get("iteration", ""))
                    or result.metadata.get("status") != "failed-preserved"
                    or result.metadata.get("authority") != "execution-evidence"
                    or target.identifier not in dependencies
                    or f"{target.metadata.get('iteration')}-VERIFICATION"
                    not in dependencies
                ):
                    errors.append(
                        f"{label}: blocked {target.identifier} must bind same-iteration failed-preserved execution evidence that depends on the Slice and Verification"
                    )
                else:
                    freeze_digest = manifest_slice.get("product_code_freeze_digest")
                    if not isinstance(freeze_digest, str) or re.fullmatch(
                        r"sha256:[0-9a-f]{64}", freeze_digest
                    ) is None:
                        errors.append(
                            f"{label}: blocked {target.identifier} must bind an exact product_code_freeze_digest"
                        )
                    elif result.metadata.get("product_code_freeze_digest") != freeze_digest:
                        errors.append(
                            f"{label}: blocked {target.identifier} Result must bind its exact product code freeze"
                        )
                    comparison_binding = early_comparison_by_slice.get(
                        target.identifier
                    )
                    comparison_case = (
                        comparison_binding.get("case_id")
                        if isinstance(comparison_binding, dict)
                        else None
                    )
                    comparison_rows = (
                        markdown_table_case_rows(verification.body, comparison_case)
                        if verification is not None
                        and isinstance(comparison_case, str)
                        else []
                    )
                    comparison_verdict = (
                        blocking_case_status_verdict(comparison_rows[0][6])
                        if len(comparison_rows) == 1
                        and len(comparison_rows[0]) == 7
                        else None
                    )
                    if (
                        isinstance(alignment, dict)
                        and comparison_verdict in {"PASS", "FAIL"}
                    ):
                        errors.extend(
                            validate_positive_value_result(
                                result,
                                alignment,
                                label,
                                require_pass=False,
                                expected_case_id=str(comparison_case),
                            )
                        )
                    if requires_reflection_gate(
                        target.metadata.get("iteration", "")
                    ):
                        (
                            result_binding,
                            result_assumptions,
                            result_catalog_digest,
                        ) = reflection_inputs_for_result(
                            target.identifier,
                            manifest_slice.get("result"),
                        )
                        errors.extend(
                            validate_slice_reflection_result(
                                target,
                                result,
                                result_binding,
                                manifest_slice,
                                verification,
                                label,
                                blocked=True,
                                assumption_expectations=result_assumptions,
                                assumption_catalog_digest=result_catalog_digest,
                                rework_policy=rework_policy,
                            )
                        )
            elif status == "paused":
                (
                    paused_binding,
                    paused_assumptions,
                    paused_catalog_digest,
                ) = reflection_inputs_for_result(
                    target.identifier,
                    manifest_slice.get("result"),
                )
                errors.extend(
                    validate_paused_rework_slice(
                        target,
                        manifest_slice,
                        by_id,
                        paused_binding,
                        verification,
                        label,
                        assumption_expectations=paused_assumptions,
                        assumption_catalog_digest=paused_catalog_digest,
                        rework_policy=rework_policy,
                    )
                )
                comparison_binding = early_comparison_by_slice.get(
                    target.identifier
                )
                comparison_case = (
                    comparison_binding.get("case_id")
                    if isinstance(comparison_binding, dict)
                    else None
                )
                result_ref = manifest_slice.get("result")
                result = by_id.get(result_ref) if isinstance(result_ref, str) else None
                comparison_rows = (
                    markdown_table_case_rows(verification.body, comparison_case)
                    if verification is not None
                    and isinstance(comparison_case, str)
                    else []
                )
                comparison_verdict = (
                    blocking_case_status_verdict(comparison_rows[0][6])
                    if len(comparison_rows) == 1
                    and len(comparison_rows[0]) == 7
                    else None
                )
                if (
                    result is not None
                    and isinstance(alignment, dict)
                    and comparison_verdict in {"PASS", "FAIL"}
                ):
                    errors.extend(
                        validate_positive_value_result(
                            result,
                            alignment,
                            label,
                            require_pass=False,
                            expected_case_id=str(comparison_case),
                        )
                    )
            elif status == "completed":
                result_ref = manifest_slice.get("result")
                result = by_id.get(result_ref) if isinstance(result_ref, str) else None
                reflection_result = result
                dependencies: list[object] = []
                if result is not None and isinstance(
                    result.metadata.get("depends_on", []), list
                ):
                    dependencies = result.metadata.get("depends_on", [])  # type: ignore[assignment]
                if (
                    result is None
                    or result.metadata.get("kind") != "iteration-result"
                    or str(result.metadata.get("iteration", ""))
                    != str(target.metadata.get("iteration", ""))
                    or result.metadata.get("status") not in {"accepted", "completed"}
                    or result.metadata.get("authority") != "execution-evidence"
                    or target.identifier not in dependencies
                    or f"{target.metadata.get('iteration')}-VERIFICATION" not in dependencies
                ):
                    errors.append(
                        f"{label}: completed {target.identifier} must bind accepted execution evidence that depends on the Slice and Verification"
                    )
                else:
                    freeze_digest = manifest_slice.get("product_code_freeze_digest")
                    if not isinstance(freeze_digest, str) or re.fullmatch(
                        r"sha256:[0-9a-f]{64}", freeze_digest
                    ) is None:
                        errors.append(
                            f"{label}: completed {target.identifier} must bind an exact product_code_freeze_digest"
                        )
                    elif result.metadata.get("product_code_freeze_digest") != freeze_digest:
                        errors.append(
                            f"{label}: completed {target.identifier} Result must bind its exact product code freeze"
                        )

                    canary_binding = early_canary_by_slice.get(target.identifier)
                    if canary_binding is not None:
                        for result_field, binding_field in (
                            ("canary_project_manifest_digest", "project_manifest_digest"),
                            ("canary_suite_digest", "suite_digest"),
                        ):
                            if result.metadata.get(result_field) != canary_binding.get(
                                binding_field
                            ):
                                errors.append(
                                    f"{label}: completed {target.identifier} Result {result_field} must match its frozen canary"
                                )
                        disclosure_receipt = result.metadata.get(
                            "canary_disclosure_receipt_digest"
                        )
                        if not isinstance(disclosure_receipt, str) or re.fullmatch(
                            r"sha256:[0-9a-f]{64}", disclosure_receipt
                        ) is None:
                            errors.append(
                                f"{label}: completed {target.identifier} Result must bind an exact canary disclosure receipt"
                            )
                        if result.metadata.get(
                            "canary_product_change_before_result_seal_count"
                        ) != 0:
                            errors.append(
                                f"{label}: completed {target.identifier} disclosure-to-Result-seal product change count must equal zero"
                            )
                        if result.metadata.get(
                            "canary_capsule_consumption_status"
                        ) != "CONSUMED_AFTER_RESULT_SEAL":
                            errors.append(
                                f"{label}: completed {target.identifier} must consume its canary after the Result seal"
                            )

                    if (
                        target.identifier in early_comparison_by_slice
                        and isinstance(alignment, dict)
                    ):
                        comparison_case = early_comparison_by_slice[
                            target.identifier
                        ].get("case_id")
                        errors.extend(
                            validate_positive_value_result(
                                result,
                                alignment,
                                label,
                                expected_case_id=(
                                    str(comparison_case)
                                    if isinstance(comparison_case, str)
                                    else None
                                ),
                            )
                        )

                    if requires_reflection_gate(
                        target.metadata.get("iteration", "")
                    ):
                        (
                            result_binding,
                            result_assumptions,
                            result_catalog_digest,
                        ) = reflection_inputs_for_result(
                            target.identifier,
                            manifest_slice.get("result"),
                        )
                        errors.extend(
                            validate_slice_reflection_result(
                                target,
                                result,
                                result_binding,
                                manifest_slice,
                                verification,
                                label,
                                blocked=False,
                                assumption_expectations=result_assumptions,
                                assumption_catalog_digest=result_catalog_digest,
                                rework_policy=rework_policy,
                            )
                        )

                if result is not None and verification is not None:
                    case_ids = target.metadata.get("product_goal_slice_gate_case_ids", [])
                    if not isinstance(case_ids, list):
                        case_ids = []
                    for case_id in dict.fromkeys(case_ids):
                        errors.extend(
                            validate_blocking_verification_case(
                                verification,
                                str(case_id),
                                require_pass=True,
                                expected_evidence=expected_verification_case_evidence(
                                    result.identifier, str(case_id)
                                ),
                            )
                        )

            if (
                status in {"blocked", "paused", "completed"}
                and experience_policy is not None
                and provider_policy is not None
                and target.identifier == experience_policy.get("owner_slice_ref")
                and isinstance(manifest_slice, dict)
            ):
                delivery_result_ref = manifest_slice.get("result")
                delivery_result = (
                    by_id.get(delivery_result_ref)
                    if isinstance(delivery_result_ref, str)
                    else None
                )
                if delivery_result is None:
                    errors.append(
                        f"{label}: {target.identifier} must bind an experience-first delivery Result"
                    )
                elif not (
                    status == "paused"
                    and delivery_result_ref in historical_pre_policy_result_refs
                    and experience_policy.get(
                        "historical_results_do_not_satisfy_experience_gate"
                    )
                    is True
                ):
                    errors.extend(
                        validate_experience_delivery_result(
                            delivery_result,
                            experience_policy,
                            provider_policy,
                            require_success=status == "completed",
                        )
                    )

            if (
                requires_reflection_gate(target.metadata.get("iteration", ""))
                and status in {"completed", "blocked"}
                and reflection_result is not None
            ):
                if target.identifier in early_comparison_by_slice:
                    adjudication_receipt = reflection_result.metadata.get(
                        "positive_value_adjudication_receipt_ref"
                    )
                    if adjudication_receipt in decision_forbidden_refs or (
                        adjudication_receipt in seen_reflection_decision_refs
                    ):
                        errors.append(
                            f"{label}: {target.identifier} positive value adjudication must use a new message after prior authorizations and decisions"
                        )
                reflection_decision_ref = reflection_result.metadata.get(
                    "reflection_decision_ref"
                )
                if isinstance(reflection_decision_ref, str) and re.fullmatch(
                    r"codex-user-message:sha256:[0-9a-f]{64}",
                    reflection_decision_ref,
                ) is not None:
                    if reflection_decision_ref in decision_forbidden_refs:
                        errors.append(
                            f"{label}: {target.identifier} reflection_decision_ref must use a new user message after all prior authorizations"
                        )
                    if reflection_decision_ref in seen_reflection_decision_refs:
                        errors.append(
                            f"{label}: each Slice reflection_decision_ref must be unique"
                        )
                    seen_reflection_decision_refs.add(reflection_decision_ref)
                    decision_forbidden_refs.add(reflection_decision_ref)
                adjudication_receipt = reflection_result.metadata.get(
                    "positive_value_adjudication_receipt_ref"
                )
                if isinstance(adjudication_receipt, str) and re.fullmatch(
                    r"(?:codex-user-message|independent-evaluator-result):sha256:[0-9a-f]{64}",
                    adjudication_receipt,
                ) is not None:
                    decision_forbidden_refs.add(adjudication_receipt)

        if index > 0:
            dependencies = target.metadata.get("depends_on", [])
            if not isinstance(dependencies, list) or new_refs[index - 1] not in dependencies:
                errors.append(
                    f"{target.relative_path}: sequential slice must depend on {new_refs[index - 1]}"
                )
            if (
                requires_reflection_gate(target.metadata.get("iteration", ""))
                and status != "proposed"
                and isinstance(manifest_slice, dict)
            ):
                previous_slice_ref = new_refs[index - 1]
                previous_manifest_slice = development_slices.get(previous_slice_ref)
                previous_result_ref = (
                    previous_manifest_slice.get("result")
                    if isinstance(previous_manifest_slice, dict)
                    else None
                )
                if (
                    not isinstance(previous_result_ref, str)
                    or is_pending(previous_result_ref)
                    or is_absent_evidence(previous_result_ref)
                    or previous_result_ref in {"not-executed", "in-progress"}
                ):
                    errors.append(
                        f"{label}: {target.identifier} requires the prior Slice exact reflection Result before authorization"
                    )
                else:
                    if (
                        manifest_slice.get("reflection_prerequisite_result")
                        != previous_result_ref
                    ):
                        errors.append(
                            f"{label}: {target.identifier} reflection_prerequisite_result must equal {previous_result_ref}"
                        )
                    if (
                        not isinstance(dependencies, list)
                        or previous_result_ref not in dependencies
                    ):
                        errors.append(
                            f"{target.relative_path}: authorized follow-up Slice must depend on prior reflection Result {previous_result_ref}"
                        )
                    previous_result = by_id.get(previous_result_ref)
                    if (
                        previous_result is None
                        or previous_result.metadata.get("reflection_gate_status")
                        != "PASS"
                        or previous_result.metadata.get("reflection_decision")
                        != "CONTINUE"
                    ):
                        errors.append(
                            f"{label}: {target.identifier} prior reflection Result must be PASS with decision CONTINUE"
                        )
                    elif manifest_slice.get("authorization_ref") != (
                        previous_result.metadata.get("reflection_decision_ref")
                    ):
                        errors.append(
                            f"{label}: {target.identifier} authorization_ref must equal the prior reflection decision_ref"
                        )
    return errors


def validate_product_goal_alignment_state(documents: list[Document]) -> list[str]:
    """Enforce the product-goal gate when an ITER-007+ proposal is selected."""

    errors: list[str] = []
    documents_by_path = {document.path: document for document in documents}
    documents_by_id = {document.identifier: document for document in documents}
    iteration_directories: dict[str, Path] = {}
    for document in documents:
        expected = iteration_from_document_path(document.path)
        if expected is not None:
            iteration_directories.setdefault(
                expected,
                REPOSITORY
                / "docs/project/iterations"
                / f"iteration-{expected.removeprefix('ITER-')}",
            )

    for iteration, directory in sorted(iteration_directories.items()):
        if not requires_product_goal_alignment(iteration):
            continue
        proposal = documents_by_path.get(directory / "proposal.md")
        readiness = documents_by_path.get(directory / "readiness-review.md")
        verification = documents_by_path.get(directory / "verification-matrix.md")
        index = documents_by_path.get(directory / "README.md")
        slice_candidates = [
            document
            for document in documents
            if document.path.parent == directory / "development-design"
            and document.path.name != "README.md"
        ]
        acceptances = [
            document
            for document in documents
            if document.path.parent == directory / "results"
            and document.metadata.get("kind") == "iteration-acceptance"
            and str(document.metadata.get("status", "")) in FINAL_ITERATION_STATUSES
        ]

        proposal_selected = proposal is not None and str(
            proposal.metadata.get("status", "")
        ) in GOAL_ALIGNED_PROPOSAL_STATUSES
        readiness_selected = readiness is not None and str(
            readiness.metadata.get("status", "")
        ) in GOAL_ALIGNED_READINESS_STATUSES
        iteration_selected = index is not None and str(
            index.metadata.get("status", "")
        ) in GOAL_ALIGNED_ITERATION_STATUSES
        iteration_rejected = (
            index is not None
            and str(index.metadata.get("status", "")) == "rejected"
        )
        iteration_paused = (
            index is not None
            and str(index.metadata.get("status", "")) == "paused"
        )
        iteration_superseded = (
            index is not None
            and str(index.metadata.get("status", "")) == "superseded"
        )
        selected_slices = [
            document
            for document in slice_candidates
            if str(document.metadata.get("status", ""))
            in GOAL_ALIGNED_SLICE_STATUSES
        ]
        selected = bool(
            proposal_selected
            or readiness_selected
            or iteration_selected
            or selected_slices
            or acceptances
        )
        if not selected:
            if requires_reflection_gate(iteration):
                for planned_document in (
                    *(item for item in (proposal, readiness) if item is not None),
                    *slice_candidates,
                ):
                    kind = str(planned_document.metadata.get("kind", ""))
                    for section in empty_required_sections(
                        planned_document,
                        REFLECTION_GATE_REQUIRED_SECTIONS.get(kind, ()),
                    ):
                        errors.append(
                            f"{planned_document.relative_path}: planned reflection section is missing or empty: {section}"
                        )
                errors.extend(
                    validate_product_goal_alignment_documents(
                        proposal, verification, iteration
                    )
                )
                manifest = directory / "manifest.yaml"
                if not manifest.exists():
                    errors.append(
                        f"{iteration}: proposed reflection-gated iteration is missing manifest.yaml"
                    )
                else:
                    label = _path_label(manifest)
                    try:
                        manifest_text = manifest.read_text(encoding="utf-8")
                        manifest_data = safe_load_manifest(manifest_text)
                    except (OSError, UnicodeError, SafeYamlError) as error:
                        errors.append(
                            f"{label}: proposed reflection-gated Manifest cannot be loaded: {error}"
                        )
                    else:
                        errors.extend(
                            validate_product_goal_alignment_manifest(
                                manifest_data,
                                manifest_text,
                                label,
                                iteration,
                            )
                        )
                        errors.extend(
                            validate_product_goal_reference_targets(
                                manifest,
                                iteration,
                                documents_by_id,
                                verification=verification,
                            )
                        )
            continue

        if iteration_rejected:
            if (
                str(index.metadata.get("coding_input", "")).strip().lower()
                != "false"
            ):
                errors.append(
                    f"{index.relative_path}: rejected iteration must use coding_input false"
                )
            if acceptances:
                errors.append(
                    f"{index.relative_path}: rejected iteration must not have an accepted/completed Acceptance"
                )
        if iteration_paused:
            if str(index.metadata.get("coding_input", "")).strip().lower() != "false":
                errors.append(
                    f"{index.relative_path}: paused iteration must use coding_input false"
                )
            if acceptances:
                errors.append(
                    f"{index.relative_path}: paused iteration must not have an accepted/completed Acceptance"
                )
        if iteration_superseded:
            if str(index.metadata.get("coding_input", "")).strip().lower() != "false":
                errors.append(
                    f"{index.relative_path}: superseded iteration must use coding_input false"
                )
            if acceptances:
                errors.append(
                    f"{index.relative_path}: superseded iteration must not have an accepted/completed Acceptance"
                )

        for required_document, expected_kind in (
            (proposal, "iteration-proposal"),
            (readiness, "iteration-readiness"),
            (verification, "iteration-verification"),
            (index, "iteration-index"),
        ):
            if (
                required_document is not None
                and required_document.metadata.get("kind") != expected_kind
            ):
                errors.append(
                    f"{required_document.relative_path}: expected kind {expected_kind}"
                )
        for slice_document in selected_slices:
            if slice_document.metadata.get("kind") != "development-slice":
                errors.append(
                    f"{slice_document.relative_path}: selected slice must have kind development-slice"
                )

        errors.extend(
            validate_product_goal_alignment_documents(
                proposal, verification, iteration
            )
        )
        if proposal is not None:
            if not proposal_selected and not (
                iteration_superseded
                and str(proposal.metadata.get("status", ""))
                in {"proposed", "superseded"}
            ):
                errors.append(
                    f"{proposal.relative_path}: selected iteration proposal must be accepted/authorized/completed"
                )
            errors.extend(validate_goal_aligned_required_document(proposal))

        requires_readiness = bool(
            readiness_selected or iteration_selected or selected_slices or acceptances
        ) and not iteration_superseded
        if requires_readiness:
            if readiness is None:
                errors.append(f"{iteration}: selected iteration is missing readiness-review.md")
            else:
                if not readiness_selected:
                    errors.append(
                        f"{readiness.relative_path}: selected iteration readiness must be accepted/authorized/completed"
                    )
                errors.extend(validate_goal_aligned_required_document(readiness))
                errors.extend(
                    validate_product_goal_readiness_authorization(readiness)
                )
            if verification is not None:
                errors.extend(validate_goal_aligned_required_document(verification))

        if index is not None and iteration_selected:
            errors.extend(validate_goal_aligned_required_document(index))
        for slice_document in selected_slices:
            errors.extend(validate_goal_aligned_required_document(slice_document))

        manifest = directory / "manifest.yaml"
        if not manifest.exists():
            errors.append(f"{iteration}: selected iteration is missing manifest.yaml")
        else:
            allowed_statuses = (
                GOAL_ALIGNED_ITERATION_STATUSES
                if requires_readiness
                else GOAL_ALIGNED_ITERATION_STATUSES | {"proposed"}
            )
            errors.extend(
                validate_active_manifest(
                    manifest,
                    iteration,
                    allowed_statuses=allowed_statuses,
                    expected_status=(
                        "rejected"
                        if iteration_rejected
                        else "paused"
                        if iteration_paused
                        else "superseded"
                        if iteration_superseded
                        else None
                    ),
                    allow_unresolved_planning=iteration_superseded,
                )
            )
            errors.extend(
                validate_product_goal_reference_targets(
                    manifest,
                    iteration,
                    documents_by_id,
                    require_execution_slice_sequence=requires_readiness,
                    require_completed_slice_sequence=(
                        not iteration_rejected
                        and bool(
                            acceptances
                            or (
                                index is not None
                                and str(index.metadata.get("status", ""))
                                in FINAL_ITERATION_STATUSES
                            )
                        )
                    ),
                    require_rejected_slice_sequence=iteration_rejected,
                    require_paused_slice_sequence=iteration_paused,
                    require_superseded_slice_sequence=iteration_superseded,
                    verification=verification,
                )
            )
            if requires_readiness:
                try:
                    manifest_text = manifest.read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    manifest_text = ""
                for reference in manifest_resolved_sequence_items(
                    manifest_text,
                    "product_goal_alignment",
                    "new_capability_slice_refs",
                ) or []:
                    target = documents_by_id.get(reference)
                    if (
                        target is not None
                        and target.metadata.get("kind") == "development-slice"
                        and str(target.metadata.get("iteration", "")) == iteration
                    ):
                        errors.extend(validate_goal_aligned_required_document(target))
    return errors


def validate_dependency_cycles(by_id: dict[str, Document]) -> list[str]:
    errors: list[str] = []
    state: dict[str, int] = {}
    stack: list[str] = []

    def is_prior_result_lineage(source: Document, target: Document) -> bool:
        """Ignore only the registered PDR-010 governance chronology edge.

        A generic ``newer PDR -> any older sealed Result`` exemption lets an
        arbitrary Result hide a real two-node cycle.  The only historical
        document that lacks a generic ``action_kind`` marker but is already
        trusted as a governance predecessor is the exact PDR-009 plan-recovery
        Result.  Bind every available identity field instead of inferring that
        role merely from revision numbers.
        """

        source_dependencies = source.metadata.get("depends_on")
        target_dependencies = target.metadata.get("depends_on")
        return (
            source.identifier == ITER010_LIGHTWEIGHT_PLAN_REVISION_REF
            and source.metadata.get("kind") == "project-decision"
            and source.metadata.get("iteration") == "ITER-010"
            and source.metadata.get("decision") == "REWORK"
            and source.metadata.get("rework_strategy")
            == "COMPLETE_MVP_EXPERIENCE_FIRST"
            and isinstance(source_dependencies, list)
            and ITER010_PLAN_RECOVERY_RESULT_REF in source_dependencies
            and target.identifier == ITER010_PLAN_RECOVERY_RESULT_REF
            and target.metadata.get("kind") == "iteration-result"
            and target.metadata.get("status") == "sealed"
            and target.metadata.get("iteration") == "ITER-010"
            and target.metadata.get("plan_revision_ref")
            == ITER010_PLAN_REVISION_REF
            and target.metadata.get("action_ref")
            == ITER010_PLAN_RECOVERY_ACTION_ID
            and target.metadata.get("verification_case_id")
            == ITER010_PLAN_RECOVERY_CASE_ID
            and isinstance(target_dependencies, list)
            and ITER010_PLAN_REVISION_REF in target_dependencies
        )

    def visit(identifier: str) -> None:
        mark = state.get(identifier, 0)
        if mark == 2:
            return
        if mark == 1:
            start = stack.index(identifier)
            errors.append("dependency cycle: " + " -> ".join(stack[start:] + [identifier]))
            return
        state[identifier] = 1
        stack.append(identifier)
        dependencies = by_id[identifier].metadata.get("depends_on", [])
        if isinstance(dependencies, list):
            for dependency in dependencies:
                if dependency in by_id:
                    if is_prior_result_lineage(
                        by_id[identifier], by_id[dependency]
                    ):
                        continue
                    visit(dependency)
        stack.pop()
        state[identifier] = 2

    for identifier in sorted(by_id):
        visit(identifier)
    return errors


def _validate_finding_target(
    document: Document,
    classification: str,
    target: str,
    by_id: dict[str, Document],
) -> list[str]:
    errors: list[str] = []
    label = document.relative_path
    target_document = by_id.get(target)

    if classification == "local-implementation":
        references: list[str] = []
        for field in ("code", "tests"):
            value = document.metadata.get(field, [])
            if isinstance(value, list):
                references.extend(str(item) for item in value)
        if target not in references:
            errors.append(
                f"{label}: local-implementation target must be one code/tests reference"
            )
        else:
            resolved = (REPOSITORY / target).resolve()
            try:
                resolved.relative_to(REPOSITORY)
            except ValueError:
                errors.append(f"{label}: local-implementation target escapes repository")
            else:
                if not resolved.exists():
                    errors.append(
                        f"{label}: local-implementation target does not exist: {target}"
                    )
        return errors

    if target_document is None:
        return [f"{label}: finding target is not an existing document ID: {target}"]

    target_kind = str(target_document.metadata.get("kind", ""))
    target_iteration = str(target_document.metadata.get("iteration", ""))
    finding_iteration = str(document.metadata.get("iteration", ""))
    if classification == "iteration-design":
        if target_kind not in {"development-slice", "project-decision"}:
            errors.append(
                f"{label}: iteration-design target must be a development-slice or project-decision"
            )
        elif target_iteration != finding_iteration:
            errors.append(f"{label}: iteration-design target belongs to another iteration")
    elif classification == "system-contract":
        if (
            not target_document.relative_path.startswith("docs/system/")
            or target_kind.endswith("-index")
        ):
            errors.append(
                f"{label}: system-contract target must be a non-index System document"
            )
    elif classification == "verification":
        is_system_quality = (
            target_document.relative_path.startswith("docs/system/")
            and target_kind == "system-quality"
        )
        is_iteration_verification = (
            target_kind == "iteration-verification"
            and target_iteration == finding_iteration
        )
        if not (is_system_quality or is_iteration_verification):
            errors.append(
                f"{label}: verification target must be System Quality or this "
                "iteration's Verification Matrix"
            )
    elif classification == "roadmap":
        if target_kind != "roadmap-candidate":
            errors.append(f"{label}: roadmap target must be a roadmap-candidate")
    return errors


def validate_findings(
    documents: list[Document],
    by_id: dict[str, Document],
    iteration_indexes: dict[str, Document],
) -> list[str]:
    errors: list[str] = []
    allowed_classifications = FINDING_CLASSIFICATIONS | {"unclassified"}

    for document in documents:
        if document.metadata.get("kind") != "implementation-finding":
            continue
        label = document.relative_path
        status = str(document.metadata.get("status", ""))
        iteration = document.metadata.get("iteration", "")
        classification = document.metadata.get("classification", "")
        disposition = document.metadata.get("disposition", "")
        target = document.metadata.get("target", "")

        if not isinstance(iteration, str) or not iteration:
            errors.append(f"{label}: finding is missing iteration")
            iteration = ""
        elif iteration not in iteration_indexes:
            errors.append(f"{label}: finding references unknown iteration: {iteration}")

        if status not in {"open", "dispositioned", "rejected", "superseded"}:
            errors.append(f"{label}: invalid finding status: {status}")
        if not isinstance(classification, str) or classification not in allowed_classifications:
            errors.append(f"{label}: invalid finding classification: {classification}")
        if classification == "invalid" and status != "rejected":
            errors.append(f"{label}: invalid classification requires rejected status")
        if classification == "unclassified" and status != "open":
            errors.append(f"{label}: closed finding must be classified")
        if not isinstance(disposition, str):
            errors.append(f"{label}: disposition must be a single scalar")
        if not isinstance(target, str):
            errors.append(f"{label}: target must be a single scalar")

        if status == "dispositioned":
            if classification not in FINDING_CLASSIFICATIONS - {"invalid"}:
                errors.append(f"{label}: dispositioned finding has invalid classification")
            if not isinstance(disposition, str) or is_pending(disposition):
                errors.append(f"{label}: dispositioned finding has pending disposition")
            if not isinstance(target, str) or is_pending(target):
                errors.append(f"{label}: dispositioned finding has pending target")
            elif isinstance(classification, str):
                errors.extend(
                    _validate_finding_target(document, classification, target, by_id)
                )
        elif status == "open":
            if (
                isinstance(target, str)
                and not is_pending(target)
                and classification in FINDING_CLASSIFICATIONS - {"invalid"}
            ):
                errors.extend(
                    _validate_finding_target(document, classification, target, by_id)
                )
        elif status == "rejected":
            if classification != "invalid":
                errors.append(f"{label}: rejected finding classification must be invalid")
            if not isinstance(disposition, str) or is_pending(disposition):
                errors.append(f"{label}: rejected finding has pending disposition")
            if not isinstance(target, str) or target.strip().lower() != "none":
                errors.append(f"{label}: rejected finding target must be the scalar none")
        elif status == "superseded":
            superseded_by = document.metadata.get("superseded_by", "")
            if not isinstance(superseded_by, str):
                errors.append(f"{label}: superseded_by must be a single scalar")
            elif is_pending(superseded_by):
                errors.append(f"{label}: superseded finding is missing superseded_by")
            elif superseded_by == document.identifier:
                errors.append(f"{label}: superseded_by cannot reference the finding itself")
            else:
                replacement = by_id.get(superseded_by)
                if (
                    replacement is None
                    or replacement.metadata.get("kind") != "implementation-finding"
                ):
                    errors.append(
                        f"{label}: superseded_by must reference an existing Finding"
                    )
                elif replacement.metadata.get("iteration") != iteration:
                    errors.append(
                        f"{label}: superseded_by must reference a Finding in the same iteration"
                    )
    return errors


def validate_completed_acceptance(
    document: Document,
    verification: Document | None = None,
    by_id: dict[str, Document] | None = None,
) -> list[str]:
    errors: list[str] = []
    for field in ("id", "iteration", *COMPLETED_ACCEPTANCE_FIELDS):
        value = document.metadata.get(field)
        if (
            not isinstance(value, str)
            or is_pending(value)
            or has_unresolved_placeholder(value)
        ):
            errors.append(
                f"{document.relative_path}: completed acceptance field '{field}' "
                "is pending or a placeholder"
            )
    baseline_commit = document.metadata.get("baseline_commit")
    if (
        isinstance(baseline_commit, str)
        and not is_pending(baseline_commit)
        and HEX_COMMIT_RE.fullmatch(baseline_commit) is None
    ):
        errors.append(
            f"{document.relative_path}: completed acceptance baseline_commit must "
            "be an exact 40-character lowercase Git commit"
        )
    required_sections = COMPLETED_ACCEPTANCE_SECTIONS
    if requires_product_goal_alignment(document.metadata.get("iteration", "")):
        required_sections += PRODUCT_GOAL_ALIGNMENT_ACCEPTANCE_SECTIONS
        product_goal_body = markdown_section_body(
            document, "Product-goal delta and cumulative evidence"
        )
        if product_goal_body is not None and any(
            placeholder in product_goal_body
            for placeholder in PRODUCT_GOAL_ACCEPTANCE_PLACEHOLDERS
        ):
            errors.append(
                f"{document.relative_path}: completed acceptance contains unresolved product-goal placeholders"
            )
        errors.extend(
            validate_product_goal_v000(
                verification,
                str(document.metadata.get("iteration", "")),
                require_pass=True,
                by_id=by_id,
            )
        )
        if verification is not None and by_id is not None:
            result_id = verification.metadata.get("product_goal_result_id")
            result = by_id.get(result_id) if isinstance(result_id, str) else None
            if result is not None and document.metadata.get(
                "subject_identity"
            ) != result.metadata.get("product_goal_subject_digest"):
                errors.append(
                    f"{document.relative_path}: acceptance subject_identity must equal the product Result subject digest"
                )
            try:
                manifest = safe_load_manifest(
                    (verification.path.parent / "manifest.yaml").read_text(
                        encoding="utf-8"
                    )
                )
            except (OSError, UnicodeError, SafeYamlError):
                manifest = {}
            baseline = manifest.get("baseline")
            if isinstance(baseline, dict) and document.metadata.get(
                "baseline_commit"
            ) != baseline.get("commit"):
                errors.append(
                    f"{document.relative_path}: acceptance baseline_commit must equal the product-goal Manifest baseline"
                )
    for section in empty_required_sections(document, required_sections):
        errors.append(
            f"{document.relative_path}: completed acceptance section is missing or empty: {section}"
        )
    return errors


def validate(documents: list[Document]) -> list[str]:
    errors: list[str] = []
    by_id: dict[str, Document] = {}

    for document in documents:
        identifier = document.identifier
        if not identifier:
            errors.append(f"{document.relative_path}: empty id")
        elif identifier in by_id:
            errors.append(
                f"duplicate id {identifier}: {by_id[identifier].relative_path}, {document.relative_path}"
            )
        else:
            by_id[identifier] = document

    for document in documents:
        dependencies = document.metadata.get("depends_on", [])
        if isinstance(dependencies, list):
            for dependency in dependencies:
                if dependency not in by_id:
                    errors.append(f"{document.relative_path}: unknown dependency id: {dependency}")
                if dependency == document.identifier:
                    errors.append(f"{document.relative_path}: self dependency: {dependency}")
                if (
                    document.relative_path.startswith("docs/system/")
                    and dependency in by_id
                    and not by_id[dependency].relative_path.startswith("docs/system/")
                ):
                    errors.append(
                        f"{document.relative_path}: system document depends on project document: {dependency}"
                    )

        for field in ("code", "tests"):
            references = document.metadata.get(field, [])
            if not isinstance(references, list):
                continue
            for reference in references:
                if not (REPOSITORY / reference).exists():
                    errors.append(f"{document.relative_path}: missing {field} reference: {reference}")

        relative = document.path.relative_to(DOCS).as_posix()
        errors.extend(validate_iteration_document_identity(document))
        if relative.startswith("system/") and document.metadata.get("authority") not in {
            "normative",
            "operational",
        }:
            errors.append(
                f"{document.relative_path}: system authority must be normative or operational"
            )
        if relative.startswith("project/roadmap/"):
            if document.metadata.get("authority") != "planning-only":
                errors.append(f"{document.relative_path}: roadmap authority must be planning-only")
            if str(document.metadata.get("coding_input", "")).lower() != "false":
                errors.append(f"{document.relative_path}: roadmap coding_input must be false")

        errors.extend(validate_links(document))

    errors.extend(validate_product_goal_alignment_state(documents))

    for path in PLAIN_LINK_FILES:
        if not path.exists():
            errors.append(f"missing navigation document: {path.relative_to(REPOSITORY)}")
        else:
            errors.extend(validate_markdown_links(path, path.read_text(encoding="utf-8")))

    open_findings: dict[str, list[str]] = {}
    accepted_iterations: set[str] = set()
    iteration_indexes: dict[str, Document] = {}
    acceptance_by_iteration: dict[str, list[Document]] = {}
    verification_by_iteration: dict[str, Document] = {}
    for document in documents:
        kind = document.metadata.get("kind")
        status = str(document.metadata.get("status", ""))
        iteration = str(document.metadata.get("iteration", ""))
        expected_iteration = iteration_from_document_path(document.path)
        iteration_key = expected_iteration or iteration
        if kind == "iteration-index" and iteration:
            if iteration in iteration_indexes:
                errors.append(
                    f"{document.relative_path}: duplicate iteration index for {iteration}"
                )
            else:
                iteration_indexes[iteration] = document
        if kind == "implementation-finding" and status == "open":
            open_findings.setdefault(iteration, []).append(document.identifier)
        if kind == "iteration-acceptance" and status in {"accepted", "completed"}:
            accepted_iterations.add(iteration_key)
        if kind == "iteration-acceptance" and iteration:
            acceptance_by_iteration.setdefault(iteration_key, []).append(document)
        if kind == "iteration-verification" and iteration_key:
            if iteration_key in verification_by_iteration:
                errors.append(
                    f"{document.relative_path}: duplicate verification matrix for {iteration_key}"
                )
            else:
                verification_by_iteration[iteration_key] = document

    for iteration, acceptances in acceptance_by_iteration.items():
        for acceptance in acceptances:
            if str(acceptance.metadata.get("status", "")) in FINAL_ITERATION_STATUSES:
                errors.extend(
                    validate_completed_acceptance(
                        acceptance,
                        verification_by_iteration.get(iteration),
                        by_id,
                    )
                )

    errors.extend(validate_findings(documents, by_id, iteration_indexes))

    for iteration in sorted(accepted_iterations):
        if open_findings.get(iteration):
            errors.append(
                f"{iteration}: accepted/completed with open findings: "
                + ", ".join(sorted(open_findings[iteration]))
            )

    for iteration, index in sorted(iteration_indexes.items()):
        if str(index.metadata.get("status", "")) not in FINAL_ITERATION_STATUSES:
            continue
        accepted = [
            document
            for document in acceptance_by_iteration.get(iteration, [])
            if str(document.metadata.get("status", "")) in FINAL_ITERATION_STATUSES
        ]
        if not accepted:
            errors.append(
                f"{index.relative_path}: completed iteration has no accepted/completed acceptance"
            )

    current = by_id.get("PROJECT-CURRENT")
    if current is None:
        errors.append("missing PROJECT-CURRENT document")
    else:
        active_iteration = str(current.metadata.get("active_iteration", ""))
        active_slice = str(current.metadata.get("active_slice", ""))
        if active_iteration == "none" and active_slice != "none":
            errors.append("PROJECT-CURRENT: active_slice must be none when active_iteration is none")
        if active_iteration != "none":
            current_dependencies = current.metadata.get("depends_on", [])
            if isinstance(current_dependencies, list):
                if active_iteration not in current_dependencies:
                    errors.append("PROJECT-CURRENT: active iteration must be in depends_on")
                if active_slice not in current_dependencies:
                    errors.append("PROJECT-CURRENT: active slice must be in depends_on")
            iteration_document = by_id.get(active_iteration)
            if iteration_document is None or iteration_document.metadata.get("kind") != "iteration-index":
                errors.append(
                    "PROJECT-CURRENT: active_iteration must be an existing iteration-index ID"
                )
            slice_document = by_id.get(active_slice)
            if slice_document is None or slice_document.metadata.get("kind") != "development-slice":
                errors.append(
                    "PROJECT-CURRENT: active_slice must be an existing development-slice ID"
                )
            if iteration_document is not None and iteration_document.metadata.get("kind") == "iteration-index":
                iteration = str(iteration_document.metadata.get("iteration", ""))
                if not iteration:
                    errors.append("PROJECT-CURRENT: active iteration index is missing iteration")
                elif iteration_number(iteration) is None:
                    errors.append(
                        "PROJECT-CURRENT: active iteration must match ITER followed by at least three digits"
                    )
                if str(iteration_document.metadata.get("status", "")) not in ACTIVE_ITERATION_STATUSES:
                    errors.append("PROJECT-CURRENT: active iteration is not authorized/in-progress")
                if not is_true(iteration_document.metadata.get("coding_input", "")):
                    errors.append("PROJECT-CURRENT: active iteration coding_input must be true")

                if slice_document is not None and slice_document.metadata.get("kind") == "development-slice":
                    if str(slice_document.metadata.get("iteration", "")) != iteration:
                        errors.append("PROJECT-CURRENT: active slice belongs to another iteration")
                    if str(slice_document.metadata.get("status", "")) not in ACTIVE_SLICE_STATUSES:
                        errors.append("PROJECT-CURRENT: active slice is not authorized/in-progress")
                    if slice_document.metadata.get("authority") != "current-development":
                        errors.append("PROJECT-CURRENT: active slice authority must be current-development")
                    if not is_true(slice_document.metadata.get("coding_input", "")):
                        errors.append("PROJECT-CURRENT: active slice coding_input must be true")

                iteration_directory = iteration_document.path.parent
                required_paths = {
                    Path("proposal.md"): "iteration-proposal",
                    Path("verification-matrix.md"): "iteration-verification",
                    Path("readiness-review.md"): "iteration-readiness",
                    Path("development-design/README.md"): "development-design-index",
                    Path("findings/README.md"): "iteration-findings-index",
                }
                documents_by_path = {document.path: document for document in documents}
                active_required_documents: list[Document] = [iteration_document]
                if (
                    slice_document is not None
                    and slice_document.metadata.get("kind") == "development-slice"
                ):
                    active_required_documents.append(slice_document)
                for relative_path, expected_kind in required_paths.items():
                    required_path = iteration_directory / relative_path
                    required_document = documents_by_path.get(required_path)
                    if required_document is None:
                        errors.append(
                            f"PROJECT-CURRENT: active iteration is missing {required_path.relative_to(REPOSITORY)}"
                        )
                        continue
                    if required_document.metadata.get("kind") != expected_kind:
                        errors.append(
                            f"{required_document.relative_path}: expected kind {expected_kind}"
                        )
                    if str(required_document.metadata.get("iteration", "")) != iteration:
                        errors.append(
                            f"{required_document.relative_path}: iteration does not match active iteration"
                        )
                    active_required_documents.append(required_document)

                for required_document in {
                    document.path: document for document in active_required_documents
                }.values():
                    if not has_substantive_body(required_document):
                        errors.append(
                            f"{required_document.relative_path}: active required "
                            "document has no substantive body"
                        )
                    if (
                        has_unresolved_placeholder(required_document.metadata)
                        or has_pending_marker(required_document.metadata)
                        or has_unresolved_placeholder(required_document.body)
                    ):
                        errors.append(
                            f"{required_document.relative_path}: active required "
                            "document contains unresolved template placeholders"
                        )
                    for section in empty_active_required_sections(required_document):
                        errors.append(
                            f"{required_document.relative_path}: active required "
                            f"section is missing or empty: {section}"
                        )

                proposal = documents_by_path.get(iteration_directory / "proposal.md")
                if proposal is not None and str(proposal.metadata.get("status", "")) not in ACCEPTED_PROPOSAL_STATUSES:
                    errors.append("PROJECT-CURRENT: active iteration proposal is not accepted")

                if requires_product_goal_alignment(iteration):
                    verification = documents_by_path.get(
                        iteration_directory / "verification-matrix.md"
                    )
                    errors.extend(
                        validate_product_goal_alignment_documents(
                            proposal, verification, iteration
                        )
                    )
                    manifest_path = iteration_directory / "manifest.yaml"
                    try:
                        manifest_text = manifest_path.read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        manifest_text = ""
                    manifest_slice_refs = manifest_resolved_sequence_items(
                        manifest_text,
                        "product_goal_alignment",
                        "new_capability_slice_refs",
                    ) or []
                    active_product_slices = [
                        document
                        for reference in manifest_slice_refs
                        if (document := by_id.get(reference)) is not None
                        and str(document.metadata.get("status", ""))
                        in ACTIVE_SLICE_STATUSES
                    ]
                    if (
                        len(active_product_slices) != 1
                        or active_product_slices[0].identifier != active_slice
                    ):
                        errors.append(
                            "PROJECT-CURRENT: active_slice must equal the unique active "
                            "product-goal Slice in Manifest order"
                        )

                readiness = documents_by_path.get(iteration_directory / "readiness-review.md")
                if readiness is not None:
                    if str(readiness.metadata.get("status", "")) not in ACCEPTED_READINESS_STATUSES:
                        errors.append("PROJECT-CURRENT: active iteration readiness is not accepted")
                    if is_pending(readiness.metadata.get("authorized_by", "")):
                        errors.append("PROJECT-CURRENT: readiness authorized_by is pending")
                    if is_pending(readiness.metadata.get("authorized_at", "")):
                        errors.append("PROJECT-CURRENT: readiness authorized_at is pending")

                manifest = iteration_directory / "manifest.yaml"
                if not manifest.exists():
                    errors.append(
                        f"PROJECT-CURRENT: active iteration is missing {manifest.relative_to(REPOSITORY)}"
                    )
                else:
                    errors.extend(validate_active_manifest(manifest, iteration))
                    if iteration == "ITER-010":
                        try:
                            manifest_text = manifest.read_text(encoding="utf-8")
                            manifest_data = safe_load_manifest(manifest_text)
                        except (OSError, UnicodeError, SafeYamlError) as error:
                            errors.append(
                                f"{manifest.relative_to(REPOSITORY)}: cannot bind executable plan: {error}"
                            )
                        else:
                            errors.extend(
                                validate_model_transparent_governance_templates(
                                    manifest_data,
                                    manifest.relative_to(REPOSITORY).as_posix(),
                                )
                            )
                            if uses_legacy_iter010_plan(manifest_data):
                                errors.extend(
                                    validate_iter010_plan_execution_snapshot(
                                        manifest_data,
                                        manifest.relative_to(REPOSITORY).as_posix(),
                                        manifest_text=manifest_text,
                                        current=current,
                                        verification=documents_by_path.get(
                                            iteration_directory
                                            / "verification-matrix.md"
                                        ),
                                        transition_results=by_id,
                                        require_external_bindings=True,
                                    )
                                )

    errors.extend(validate_dependency_cycles(by_id))
    return sorted(set(errors))


def render_outputs(documents: list[Document]) -> dict[Path, str]:
    ordered = sorted(documents, key=lambda document: document.identifier)
    catalog = [
        {
            "id": document.identifier,
            "kind": document.metadata["kind"],
            "status": document.metadata["status"],
            "authority": document.metadata["authority"],
            "owners": document.metadata["owners"],
            "derived_from": document.metadata.get("derived_from", []),
            "path": document.relative_path,
        }
        for document in ordered
    ]
    dependencies = {
        document.identifier: document.metadata["depends_on"] for document in ordered
    }
    traceability = {
        document.identifier: {
            "path": document.relative_path,
            "code": document.metadata["code"],
            "tests": document.metadata["tests"],
        }
        for document in ordered
        if document.metadata["code"] or document.metadata["tests"]
    }

    current = next((doc for doc in ordered if doc.identifier == "PROJECT-CURRENT"), None)
    active_iteration = "unknown" if current is None else current.metadata.get("active_iteration", "unknown")
    active_slice = "unknown" if current is None else current.metadata.get("active_slice", "unknown")
    worktree_status = "unknown" if current is None else current.metadata.get("worktree_status", "unknown")
    strategy_relation = "unknown" if current is None else current.metadata.get("strategy_relation", "unknown")
    live_model_path = "unknown" if current is None else current.metadata.get("live_model_path", "unknown")
    context_lines = [
        "# Generated current context",
        "",
        "> Derived from current document front matter. Do not edit manually or treat as normative.",
        "",
        f"- Active iteration: `{active_iteration}`",
        f"- Active slice: `{active_slice}`",
        f"- Worktree status: `{worktree_status}`",
        f"- Strategy relation: `{strategy_relation}`",
        f"- Live model path: `{live_model_path}`",
        "- Normative source: `docs/system/`",
        "- Current development source: `docs/project/current.md`",
        "- Roadmap authority: planning-only",
        "- Archive authority: historical",
        "",
        "## Agent reading route",
        "",
        "1. Read `docs/project/current.md` and stop if it does not authorize development.",
        "2. If active, read only the named Iteration and Development Slice inputs.",
        "3. Follow their exact System IDs; use `catalog.json` to resolve paths.",
        "4. Record implementation discoveries under the active Iteration before changing System truth.",
        "",
        "## Stable entry points",
        "",
    ]
    by_identifier = {document.identifier: document for document in ordered}
    entry_ids = (
        "PROJECT-CURRENT",
        "SYS-PRODUCT-VISION",
        "SYS-ARCH-INVARIANTS",
        "SYS-CONTRACT-INDEX",
        "SYS-QUALITY-INDEX",
        "PROJECT-GOVERNANCE-ITERATION-LIFECYCLE",
        "PROJECT-GOVERNANCE-IMPLEMENTATION-FEEDBACK",
    )
    for identifier in entry_ids:
        document = by_identifier.get(identifier)
        if document is not None:
            context_lines.append(
                f"- `{document.identifier}` — `{document.metadata['authority']}` — `{document.relative_path}`"
            )
    context_lines.extend(
        [
            "",
            "The complete document catalog, dependency graph, and code/test traceability are in the adjacent JSON files.",
            "",
        ]
    )

    return {
        GENERATED / "catalog.json": json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        GENERATED / "dependency-graph.json": json.dumps(dependencies, ensure_ascii=False, indent=2) + "\n",
        GENERATED / "traceability.json": json.dumps(traceability, ensure_ascii=False, indent=2) + "\n",
        GENERATED / "current-context.md": "\n".join(context_lines),
    }


def generate(outputs: dict[Path, str]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")


def check_generated(outputs: dict[Path, str]) -> list[str]:
    errors: list[str] = []
    for path, expected in outputs.items():
        if not path.exists():
            errors.append(f"missing generated file: {path.relative_to(REPOSITORY)}")
        elif path.read_text(encoding="utf-8") != expected:
            errors.append(f"stale generated file: {path.relative_to(REPOSITORY)}")
    return errors


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "check"
    if command not in {"check", "generate"}:
        print("usage: python3 scripts/docs.py [check|generate]", file=sys.stderr)
        return 2

    documents, errors = load_documents()
    errors.extend(validate(documents))
    if errors:
        for error in sorted(set(errors)):
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    outputs = render_outputs(documents)
    if command == "generate":
        generate(outputs)
        print(f"generated {len(outputs)} files from {len(documents)} current documents")
        return 0

    errors = check_generated(outputs)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print("run: python3 scripts/docs.py generate", file=sys.stderr)
        return 1
    print(f"documentation check passed: {len(documents)} current documents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
