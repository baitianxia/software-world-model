from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "plan_gate.py"
WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "plan-compliance.yml"
LOCAL_HOOK = Path(__file__).resolve().parents[1] / ".githooks" / "plan-pre-commit"
SPEC = importlib.util.spec_from_file_location("plan_gate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
plan_gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = plan_gate
SPEC.loader.exec_module(plan_gate)


AUTH_9 = "codex-user-message:sha256:" + "9" * 64
AUTH_10 = "codex-user-message:sha256:" + "a" * 64
PDR_9 = "ITER-010-PDR-009"
PDR_10 = "ITER-010-PDR-010"
PDR_11 = "ITER-010-PDR-011"
PDR_8 = "ITER-010-PDR-008"
PDR_11_10 = "ITER-011-PDR-010"

ACTION_FREEZE = "ITER-010-ACTION-DIRECTION-FREEZE-001"
ACTION_QUALITY = "ITER-010-ACTION-DIRECTION-QUALITY-PREFERRED-001"
ACTION_FALLBACK_REFREEZE = "ITER-010-ACTION-DIRECTION-FALLBACK-REFREEZE-001"
ACTION_FALLBACK_QUALITY = "ITER-010-ACTION-DIRECTION-QUALITY-FALLBACK-001"
ACTION_FREEZE_REWORK = "ITER-010-ACTION-DIRECTION-FREEZE-REWORK-001"
ACTION_DIRECTION_REWORK = "ITER-010-ACTION-DIRECTION-REWORK-001"
ACTION_MINIMUM_WEB = "ITER-010-ACTION-MINIMUM-WEB-CHAT-001"
ACTION_WEB_FAILURE = "ITER-010-ACTION-WEB-FAILURE-ATTRIBUTION-001"
ACTION_USER_DECISION = "ITER-010-ACTION-USER-DIRECTION-DECISION-001"
ACTION_RESPONSIBILITY = "ITER-010-ACTION-RESPONSIBILITY-PLAN-001"

CASE_FREEZE = "V-DIRECTION-FREEZE-001"
CASE_QUALITY = "V-DIRECTION-QUALITY-001"
CASE_FALLBACK_REFREEZE = "V-DIRECTION-FALLBACK-REFREEZE-001"
CASE_FREEZE_REWORK = "V-DIRECTION-FREEZE-REWORK-001"
CASE_DIRECTION_REWORK = "V-DIRECTION-REWORK-001"
CASE_MINIMUM_WEB = "V-CHAT-EXPERIENCE-001"
CASE_WEB_FAILURE = "V-WEB-FAILURE-ATTRIBUTION-001"
CASE_USER_DECISION = "V-PREVIEW-002"
CASE_RESPONSIBILITY = "V-RESPONSIBILITY-PLAN-001"
CASE_ADMISSION = plan_gate.PUBLIC_SOURCE_AUTHORITY_CASE_ID

ITERATION_RESULTS = "docs/project/iterations/iteration-010/results"
MANIFEST_PATH = "docs/project/iterations/iteration-010/manifest.yaml"
CURRENT_PATH = "docs/project/current.md"
RUNNER_PATH = "validation/structure_world_model_iteration_010/value_gate/runner.py"
RUNNER_TEST_PATH = "tests/test_iteration_010_value_gate.py"
PREFERRED_PROFILE_REF = "runtime-config:preferred-qualified-profile"
FALLBACK_PROFILE_REF = "runtime-config:fallback-qualified-profile"
FALLBACK_PLUGIN_REF = "policy-plugin:fallback-admission@1"
PREFERRED_PROVIDER_IDENTITY = "nebula47"
FALLBACK_PROVIDER_IDENTITY = "quartz93"
PREFERRED_MODEL_IDENTITY = "helios58x"
FALLBACK_MODEL_IDENTITY = "orion62y"
TEST_CONFIGURED_IDENTITIES = (
    PREFERRED_PROVIDER_IDENTITY,
    PREFERRED_MODEL_IDENTITY,
    FALLBACK_PROVIDER_IDENTITY,
    FALLBACK_MODEL_IDENTITY,
)
PREFERRED_PROFILE = {
    "execution_profile_ref": PREFERRED_PROFILE_REF,
    "provider_identity": PREFERRED_PROVIDER_IDENTITY,
    "model_identity": PREFERRED_MODEL_IDENTITY,
}
FALLBACK_PROFILE = {
    "execution_profile_ref": FALLBACK_PROFILE_REF,
    "provider_identity": FALLBACK_PROVIDER_IDENTITY,
    "model_identity": FALLBACK_MODEL_IDENTITY,
    "admission_policy_plugin_ref": FALLBACK_PLUGIN_REF,
}
FALLBACK_PLUGIN = {
    "schema": "ROUTE_ADMISSION_POLICY_PLUGIN@1",
    "policy_revision": "fallback-admission@1",
}


def route_configuration() -> dict[str, object]:
    return {
        "provider_route_policy": {
            "schema": plan_gate.PROVIDER_ROUTE_POLICY_SCHEMA,
            "preferred_execution_profile_ref": PREFERRED_PROFILE_REF,
            "fallback_execution_profile_ref": FALLBACK_PROFILE_REF,
            "preference_order": ["preferred", "fallback"],
            "availability_owner": "provider-availability-boundary",
            "required_fallback_verdict": (
                plan_gate.PREFERRED_PROFILE_UNAVAILABLE_VERDICT
            ),
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
            "fallback_eligible_outcomes": [
                plan_gate.PREFERRED_PROFILE_UNAVAILABLE_OUTCOME
            ],
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
        },
        "execution_profile_configurations": {
            "schema": plan_gate.EXECUTION_PROFILE_CONFIGURATION_SCHEMA,
            "preferred": copy.deepcopy(PREFERRED_PROFILE),
            "fallback": copy.deepcopy(FALLBACK_PROFILE),
        },
        FALLBACK_PLUGIN_REF: copy.deepcopy(FALLBACK_PLUGIN),
    }


def configured_gate_result(
    result: dict[str, object] | None,
    action_value: dict[str, object],
    plan_revision_ref: object,
    evidence_text: str | bytes | None,
    runner_files: dict[str, str] | None = None,
) -> tuple[str | None, dict[str, str], list[str]]:
    return plan_gate.validate_gate_result(
        result,
        action_value,
        plan_revision_ref,
        evidence_text,
        runner_files,
        TEST_CONFIGURED_IDENTITIES,
    )


def verifier_runner_source(mutation: str = "") -> str:
    return """import json
import sys


def main():
    if sys.argv != [sys.argv[0], "verify-plan-evidence"]:
        return 2
    artifact = json.loads(sys.stdin.buffer.read().decode("utf-8"))
    counters = artifact["execution_counters"]
    result = {
        "evidence_verifier": artifact["evidence_verifier"],
        "action_ref": artifact["action_ref"],
        "verification_case_id": artifact["verification_case_id"],
        "plan_gate_verdict": artifact["plan_gate_verdict"],
        "execution_input_digest": artifact["execution_input_digest"],
        "runner_identity_digest": artifact["runner_identity_digest"],
        "verification_report_digest": artifact["verification_report_digest"],
        "subject_digest": artifact["subject_digest"],
        "external_model_call_count": counters["external_model_call_count"],
    }
    __MUTATION__
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""".replace("__MUTATION__", mutation or "pass")


RUNNER_FILES = {
    RUNNER_PATH: verifier_runner_source(),
    RUNNER_TEST_PATH: "# deterministic runner contract tests\n",
}


def digest(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def result_ref(case_id: str) -> str:
    return "ITER-010-RESULT-" + case_id


def slug(case_id: str) -> str:
    return case_id.lower().replace("_", "-")


def result_path(case_id: str) -> str:
    return f"{ITERATION_RESULTS}/{slug(case_id)}.md"


def evidence_path(case_id: str) -> str:
    return f"{ITERATION_RESULTS}/{slug(case_id)}.evidence.json"


def locks(*, provider_dispatch: bool = True, web_canary: bool = True) -> dict[str, bool]:
    values = {field: True for field in plan_gate.LOCK_KEYS}
    values["provider_dispatch"] = provider_dispatch
    values["web_canary"] = web_canary
    return values


def action(
    identifier: str,
    case_id: str,
    kind: str,
    *,
    coding_allowed: bool = False,
    external_execution_allowed: bool = False,
    produced_case_ids: list[str] | None = None,
    prerequisite_case_ids: list[str] | None = None,
) -> dict[str, object]:
    return {
        "id": identifier,
        "owner_slice_ref": "ITER-010-SLICE-001",
        "kind": kind,
        "status": "authorized",
        "case_id": case_id,
        "coding_allowed": coding_allowed,
        "external_execution_allowed": external_execution_allowed,
        "result_ref": result_ref(case_id),
        "result_path": result_path(case_id),
        "evidence_schema": plan_gate.EVIDENCE_SCHEMA,
        "evidence_path": evidence_path(case_id),
        "evidence_verifier": f"PLAN-GATE-{slug(case_id).upper()}@1",
        "runner_identity_paths": [RUNNER_PATH, RUNNER_TEST_PATH],
        "produced_case_ids": produced_case_ids or [case_id],
        "prerequisite_case_ids": prerequisite_case_ids or [],
        "allowed_change_paths": [
            CURRENT_PATH,
            MANIFEST_PATH,
            result_path(case_id),
            evidence_path(case_id),
            f"{ITERATION_RESULTS}/README.md",
            "docs/project/iterations/iteration-010/findings/README.md",
            "docs/project/iterations/iteration-010/findings/FINDING-010-999.md",
            "docs/project/iterations/iteration-010/decisions/PDR-010.md",
            RUNNER_PATH,
            RUNNER_TEST_PATH,
        ],
        "forbidden_change_paths": [
            "src/software_world_model/**",
            "tests/test_conversational_engineering_model.py",
        ],
    }


def contract(
    action_value: dict[str, object],
    *,
    pass_next: str,
    fail_next: str,
    invalid_next: str,
    lock_values: dict[str, bool] | None = None,
) -> dict[str, object]:
    return {
        **copy.deepcopy(action_value),
        "transition": {
            "pass_next_action_id": pass_next,
            "fail_next_action_id": fail_next,
            "invalid_next_action_id": invalid_next,
        },
        "locks": copy.deepcopy(lock_values or locks()),
    }


def registered_contracts() -> dict[str, dict[str, object]]:
    freeze = action(
        ACTION_FREEZE,
        CASE_FREEZE,
        "four-arm-direction-gate-freeze",
        coding_allowed=True,
        produced_case_ids=[CASE_FREEZE, CASE_ADMISSION],
    )
    quality = action(
        ACTION_QUALITY,
        CASE_QUALITY,
        "four-arm-direction-quality-gate",
        external_execution_allowed=True,
        prerequisite_case_ids=[CASE_FREEZE, CASE_ADMISSION],
    )
    freeze_rework = action(
        ACTION_FREEZE_REWORK,
        CASE_FREEZE_REWORK,
        "four-arm-direction-gate-freeze-rework",
        coding_allowed=True,
    )
    direction_rework = action(
        ACTION_DIRECTION_REWORK,
        CASE_DIRECTION_REWORK,
        "four-arm-failure-attribution",
        prerequisite_case_ids=[CASE_FREEZE],
    )
    minimum_web = action(
        ACTION_MINIMUM_WEB,
        CASE_MINIMUM_WEB,
        "minimum-web-chat",
        external_execution_allowed=True,
        prerequisite_case_ids=[CASE_QUALITY, CASE_ADMISSION],
    )
    web_failure = action(ACTION_WEB_FAILURE, CASE_WEB_FAILURE, "governance")
    user_decision = action(
        ACTION_USER_DECISION,
        CASE_USER_DECISION,
        "governance",
        prerequisite_case_ids=[CASE_MINIMUM_WEB],
    )
    responsibility = action(
        ACTION_RESPONSIBILITY,
        CASE_RESPONSIBILITY,
        "governance",
        prerequisite_case_ids=[CASE_DIRECTION_REWORK],
    )
    return {
        "direction_freeze": contract(
            freeze,
            pass_next=ACTION_QUALITY,
            fail_next=ACTION_FREEZE_REWORK,
            invalid_next=ACTION_FREEZE,
        ),
        "direction_quality": contract(
            quality,
            pass_next=ACTION_MINIMUM_WEB,
            fail_next=ACTION_DIRECTION_REWORK,
            invalid_next=ACTION_QUALITY,
            lock_values=locks(provider_dispatch=False),
        ),
        "direction_freeze_rework": contract(
            freeze_rework,
            pass_next=ACTION_FREEZE,
            fail_next=ACTION_FREEZE_REWORK,
            invalid_next=ACTION_FREEZE_REWORK,
        ),
        "direction_rework": contract(
            direction_rework,
            pass_next=ACTION_RESPONSIBILITY,
            fail_next=ACTION_DIRECTION_REWORK,
            invalid_next=ACTION_DIRECTION_REWORK,
        ),
        "minimum_web_chat": contract(
            minimum_web,
            pass_next=ACTION_USER_DECISION,
            fail_next=ACTION_WEB_FAILURE,
            invalid_next=ACTION_MINIMUM_WEB,
            lock_values=locks(provider_dispatch=False, web_canary=False),
        ),
        "web_failure_attribution": contract(
            web_failure,
            pass_next=ACTION_WEB_FAILURE,
            fail_next=ACTION_WEB_FAILURE,
            invalid_next=ACTION_WEB_FAILURE,
        ),
        "user_direction_decision": contract(
            user_decision,
            pass_next=ACTION_USER_DECISION,
            fail_next=ACTION_USER_DECISION,
            invalid_next=ACTION_USER_DECISION,
        ),
        "responsibility_plan": contract(
            responsibility,
            pass_next=ACTION_RESPONSIBILITY,
            fail_next=ACTION_RESPONSIBILITY,
            invalid_next=ACTION_RESPONSIBILITY,
        ),
    }


def contract_by_id(
    contracts: dict[str, dict[str, object]], identifier: str
) -> dict[str, object]:
    return next(value for value in contracts.values() if value["id"] == identifier)


def manifest(
    *, current_action_id: str = ACTION_FREEZE, pdr: str = PDR_9
) -> dict[str, object]:
    contracts = registered_contracts()
    current_contract = contract_by_id(contracts, current_action_id)
    return {
        "schema_version": 2,
        **route_configuration(),
        "development": {
            "slices": {
                "ITER-010-SLICE-001": {
                    "status": "authorized",
                    "coding_input": True,
                },
                "ITER-010-SLICE-002": {
                    "status": "proposed",
                    "coding_input": False,
                },
            }
        },
        "plan_execution_control": {
            "schema": plan_gate.CONTROL_SCHEMA,
            "plan_revision_ref": pdr,
            "enforcement_mode": "fail-closed",
            "authorization_refs": [AUTH_9 if pdr == PDR_9 else AUTH_10],
            "current_action": {
                field: copy.deepcopy(current_contract[field])
                for field in plan_gate.ACTION_KEYS
            },
            "transition": copy.deepcopy(current_contract["transition"]),
            "locks": copy.deepcopy(current_contract["locks"]),
            "next_action_contracts": contracts,
        },
    }


def iter010_value_gate_manifest(
    *, current_action_id: str = ACTION_FREEZE
) -> dict[str, object]:
    candidate = manifest()
    control = candidate["plan_execution_control"]
    assert isinstance(control, dict)
    contracts = control["next_action_contracts"]
    assert isinstance(contracts, dict)

    freeze = contract_by_id(contracts, ACTION_FREEZE)
    preferred = contract_by_id(contracts, ACTION_QUALITY)
    freeze["evidence_verifier"] = plan_gate.ITER010_VALUE_GATE_VERIFIER
    preferred["evidence_verifier"] = plan_gate.ITER010_VALUE_GATE_VERIFIER
    preferred["transition"]["invalid_next_action_id"] = ACTION_FALLBACK_REFREEZE

    fallback_refreeze = action(
        ACTION_FALLBACK_REFREEZE,
        CASE_FALLBACK_REFREEZE,
        "fallback-route-batch-refreeze",
        prerequisite_case_ids=[CASE_FREEZE, CASE_QUALITY],
    )
    fallback_refreeze["evidence_verifier"] = plan_gate.ITER010_VALUE_GATE_VERIFIER
    contracts["fallback_refreeze"] = contract(
        fallback_refreeze,
        pass_next=ACTION_FALLBACK_QUALITY,
        fail_next=ACTION_QUALITY,
        invalid_next=ACTION_FALLBACK_REFREEZE,
    )

    fallback_quality = action(
        ACTION_FALLBACK_QUALITY,
        CASE_QUALITY,
        "four-arm-direction-quality-gate",
        external_execution_allowed=True,
        prerequisite_case_ids=[CASE_FREEZE, CASE_FALLBACK_REFREEZE],
    )
    fallback_quality["result_ref"] = (
        "ITER-010-RESULT-V-DIRECTION-QUALITY-FALLBACK-001"
    )
    fallback_quality["result_path"] = (
        f"{ITERATION_RESULTS}/v-direction-quality-fallback-001.md"
    )
    fallback_quality["evidence_path"] = (
        f"{ITERATION_RESULTS}/v-direction-quality-fallback-001.evidence.json"
    )
    fallback_quality["allowed_change_paths"] = [
        CURRENT_PATH,
        MANIFEST_PATH,
        str(fallback_quality["result_path"]),
        str(fallback_quality["evidence_path"]),
    ]
    fallback_quality["evidence_verifier"] = plan_gate.ITER010_VALUE_GATE_VERIFIER
    contracts["fallback_quality"] = contract(
        fallback_quality,
        pass_next=ACTION_MINIMUM_WEB,
        fail_next=ACTION_DIRECTION_REWORK,
        invalid_next=ACTION_FALLBACK_QUALITY,
        lock_values=locks(provider_dispatch=False),
    )

    current_contract = contract_by_id(contracts, current_action_id)
    control["current_action"] = {
        field: copy.deepcopy(current_contract[field]) for field in plan_gate.ACTION_KEYS
    }
    control["transition"] = copy.deepcopy(current_contract["transition"])
    control["locks"] = copy.deepcopy(current_contract["locks"])
    return candidate


def current_metadata(
    *, action_id: str = ACTION_FREEZE, pdr: str = PDR_9
) -> dict[str, object]:
    action_value = contract_by_id(registered_contracts(), action_id)
    return {
        "active_iteration": "ITER-010-INDEX",
        "active_slice": "ITER-010-SLICE-001",
        "plan_revision_ref": pdr,
        "next_action": action_id,
        "next_action_case_id": action_value["case_id"],
    }


def documents(*, include_revision_10: bool = False) -> dict[str, dict[str, object]]:
    values: dict[str, dict[str, object]] = {
        PDR_9: {
            "id": PDR_9,
            "kind": "project-decision",
            "status": "accepted",
            "depends_on": ["FINDING-010-141"],
            "decision_ref": AUTH_9,
        },
        "FINDING-010-141": {
            "id": "FINDING-010-141",
            "kind": "implementation-finding",
        },
    }
    if include_revision_10:
        values.update(
            {
                PDR_10: {
                    "id": PDR_10,
                    "kind": "project-decision",
                    "status": "accepted",
                    "depends_on": [
                        "FINDING-010-142",
                        result_ref(CASE_RESPONSIBILITY),
                    ],
                    "decision_ref": AUTH_10,
                },
                "FINDING-010-142": {
                    "id": "FINDING-010-142",
                    "kind": "implementation-finding",
                },
            }
        )
    return values


def cases(
    *, admission_verdict: str = "NOT-RUN", freeze_verdict: str = "NOT-RUN"
) -> dict[str, list[plan_gate.VerificationCase]]:
    values: dict[str, list[plan_gate.VerificationCase]] = {}
    for registered in registered_contracts().values():
        case_id = str(registered["case_id"])
        verdict = freeze_verdict if case_id == CASE_FREEZE else "NOT-RUN"
        evidence = "sealed-existing-evidence" if verdict == "PASS" else "not-executed"
        values[case_id] = [plan_gate.VerificationCase(case_id, evidence, verdict)]
    admission_evidence = (
        "sealed-admission-evidence" if admission_verdict == "PASS" else "not-executed"
    )
    values[CASE_ADMISSION] = [
        plan_gate.VerificationCase(CASE_ADMISSION, admission_evidence, admission_verdict)
    ]
    return values


def gate_bundle(
    action_value: dict[str, object],
    verdict: str = "PASS",
    *,
    outcome_verdicts: dict[str, str] | None = None,
    counters: dict[str, int] | None = None,
    runner_files: dict[str, str] | None = None,
    pdr: str = PDR_9,
    action_evidence: dict[str, object] | None = None,
) -> tuple[dict[str, object], str]:
    runner_values = runner_files or RUNNER_FILES
    runner_digest, runner_errors = plan_gate._runner_identity_digest(
        action_value["runner_identity_paths"], runner_values
    )
    assert runner_digest is not None and not runner_errors
    execution_input_digest = digest("input:" + str(action_value["id"]))
    subject_digest = digest("subject:" + str(action_value["id"]))
    runner_receipt = {
        "runner_id": action_value["evidence_verifier"],
        "runner_identity_digest": runner_digest,
        "execution_input_digest": execution_input_digest,
        "exit_code": 0,
        "completed": True,
    }
    outcomes = [
        {
            "case_id": case_id,
            "verdict": (outcome_verdicts or {}).get(case_id, verdict),
            "evidence_ref": f"sealed://{slug(case_id)}",
            "evidence_digest": digest("evidence:" + case_id),
        }
        for case_id in action_value["produced_case_ids"]
    ]
    execution_counters = {field: 0 for field in plan_gate.EXECUTION_COUNTER_KEYS}
    execution_counters.update(counters or {})
    report_digest = plan_gate._canonical_json_digest(outcomes)
    runner_receipt_digest = plan_gate._canonical_json_digest(runner_receipt)
    artifact = {
        "schema": action_value["evidence_schema"],
        "result_id": action_value["result_ref"],
        "plan_revision_ref": pdr,
        "action_ref": action_value["id"],
        "verification_case_id": action_value["case_id"],
        "plan_gate_verdict": verdict,
        "evidence_verifier": action_value["evidence_verifier"],
        "evidence_artifact_path": action_value["evidence_path"],
        "execution_input_digest": execution_input_digest,
        "runner_identity_digest": runner_digest,
        "runner_receipt_digest": runner_receipt_digest,
        "verification_report_digest": report_digest,
        "subject_digest": subject_digest,
        "action_evidence": copy.deepcopy(action_evidence or {}),
        "execution_counters": execution_counters,
        "runner_receipt": runner_receipt,
        "case_outcomes": outcomes,
    }
    evidence_text = json.dumps(
        artifact, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    result = {
        "id": action_value["result_ref"],
        "kind": "iteration-result",
        "status": "sealed",
        "authority": "evidence",
        "iteration": "ITER-010",
        "plan_revision_ref": pdr,
        "action_ref": action_value["id"],
        "verification_case_id": action_value["case_id"],
        "plan_gate_verdict": verdict,
        "evidence_schema": action_value["evidence_schema"],
        "evidence_verifier": action_value["evidence_verifier"],
        "evidence_artifact_path": action_value["evidence_path"],
        "evidence_artifact_digest": "sha256:"
        + hashlib.sha256(evidence_text.encode("utf-8")).hexdigest(),
        "execution_input_digest": execution_input_digest,
        "runner_identity_digest": runner_digest,
        "runner_receipt_digest": runner_receipt_digest,
        "verification_report_digest": report_digest,
        "subject_digest": subject_digest,
        "external_model_call_count": execution_counters["external_model_call_count"],
    }
    return result, evidence_text


def freeze_action_evidence(root_input: dict[str, object]) -> dict[str, object]:
    return {
        "provider_neutral_root_input_set": copy.deepcopy(root_input),
        "provider_neutral_root_input_set_digest": plan_gate._canonical_json_digest(
            root_input
        ),
    }


def provider_neutral_root_input(
    question_ids: tuple[str, str, str],
) -> dict[str, object]:
    system_arm_ids = list(plan_gate.PROVIDER_NEUTRAL_SYSTEM_ARM_IDS)
    return {
        "schema": plan_gate.PROVIDER_NEUTRAL_ROOT_INPUT_SCHEMA,
        "question_ids": list(question_ids),
        "system_arm_ids": system_arm_ids,
        "entries": [
            {
                "question_id": question_id,
                "system_arm_id": system_arm_id,
                "root_input_digest": digest(
                    f"root-input:{question_id}:{system_arm_id}"
                ),
            }
            for question_id in question_ids
            for system_arm_id in system_arm_ids
        ],
    }


def quality_action_evidence(
    *,
    route_role: str,
    root_input: dict[str, object],
    execution_profile_ref: str,
    execution_profile: dict[str, object],
    terminal_classification: str,
    fallback_refreeze_predecessor_ref: str | None = None,
    fallback_refreeze_predecessor_seal_digest: str | None = None,
    admission_policy_plugin_ref: str | None = None,
    admission_policy_plugin: dict[str, object] | None = None,
) -> dict[str, object]:
    admission_receipt = {
        "schema": "ROUTE_ADMISSION_RECEIPT@1",
        "route_role": route_role,
        "admitted": terminal_classification == "AVAILABLE",
    }
    terminal_receipt = {
        "schema": "ROUTE_TERMINAL_RECEIPT@1",
        "route_role": route_role,
        "classification": terminal_classification,
    }
    evidence: dict[str, object] = {
        **freeze_action_evidence(root_input),
        "route_role": route_role,
        "execution_profile_ref": execution_profile_ref,
        "execution_profile": copy.deepcopy(execution_profile),
        "execution_profile_digest": plan_gate._canonical_json_digest(
            execution_profile
        ),
        "admission_receipt": admission_receipt,
        "admission_receipt_digest": plan_gate._canonical_json_digest(
            admission_receipt
        ),
        "terminal_receipt": terminal_receipt,
        "terminal_receipt_digest": plan_gate._canonical_json_digest(
            terminal_receipt
        ),
        "terminal_classification": terminal_classification,
        "mixed_execution_profile_batch": False,
    }
    if route_role == "fallback":
        assert fallback_refreeze_predecessor_ref is not None
        assert fallback_refreeze_predecessor_seal_digest is not None
        assert admission_policy_plugin_ref is not None
        assert admission_policy_plugin is not None
        evidence.update(
            {
                "fallback_refreeze_predecessor_ref": fallback_refreeze_predecessor_ref,
                "fallback_refreeze_predecessor_seal_digest": (
                    fallback_refreeze_predecessor_seal_digest
                ),
                "admission_policy_plugin_ref": admission_policy_plugin_ref,
                "admission_policy_plugin": copy.deepcopy(admission_policy_plugin),
                "admission_policy_plugin_digest": plan_gate._canonical_json_digest(
                    admission_policy_plugin
                ),
            }
        )
    return evidence


def fallback_refreeze_action_evidence(
    *,
    root_input: dict[str, object],
    preferred_result_ref: str,
    preferred_seal_digest: str,
    fallback_execution_profile: dict[str, object],
    fallback_admission_policy_plugin_ref: str,
    fallback_admission_policy_plugin: dict[str, object],
) -> dict[str, object]:
    return {
        **freeze_action_evidence(root_input),
        "preferred_invalid_predecessor_ref": preferred_result_ref,
        "preferred_invalid_predecessor_seal_digest": preferred_seal_digest,
        "fallback_execution_profile_ref": FALLBACK_PROFILE_REF,
        "fallback_execution_profile": copy.deepcopy(fallback_execution_profile),
        "fallback_execution_profile_digest": plan_gate._canonical_json_digest(
            fallback_execution_profile
        ),
        "fallback_admission_policy_plugin_ref": (
            fallback_admission_policy_plugin_ref
        ),
        "fallback_admission_policy_plugin": copy.deepcopy(
            fallback_admission_policy_plugin
        ),
        "fallback_admission_policy_plugin_digest": plan_gate._canonical_json_digest(
            fallback_admission_policy_plugin
        ),
        "preferred_terminal_classification": "TERMINAL_UNAVAILABLE",
        "mixed_execution_profile_batch": False,
        "provider_dispatch_count": 0,
        "new_human_authority_requested": False,
    }


def receipt_documents(
    result: dict[str, object], *, path_override: str | None = None
) -> dict[str, dict[str, object]]:
    values = documents()
    metadata = copy.deepcopy(result)
    metadata["__path__"] = path_override or str(result["evidence_artifact_path"]).replace(
        ".evidence.json", ".md"
    )
    values[str(result["id"])] = metadata
    return values


class ParsingTests(unittest.TestCase):
    def test_yaml_parser_materializes_scalar_lists(self) -> None:
        parsed = plan_gate.load_safe_yaml(
            """schema_version: 2
plan_execution_control:
  prerequisite_case_ids:
    - V-A-001
    - V-B-001
"""
        )
        control = parsed["plan_execution_control"]
        assert isinstance(control, dict)
        self.assertEqual(control["prerequisite_case_ids"], ["V-A-001", "V-B-001"])

    def test_evidence_json_rejects_duplicate_keys(self) -> None:
        with self.assertRaisesRegex(plan_gate.PlanGateError, "duplicate key"):
            plan_gate._load_evidence_json('{"schema":"a","schema":"b"}')

    def test_document_scan_collects_authority_from_markdown_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            docs = repository / "docs"
            docs.mkdir()
            (docs / "history.md").write_text(
                f"# History\n\nThis authority was already consumed: {AUTH_10}.\n",
                encoding="utf-8",
            )
            documents_found, authority_refs, blob_digests, errors = (
                plan_gate._document_metadata(repository, "WORKTREE")
            )
        self.assertEqual(errors, [])
        self.assertEqual(documents_found, {})
        self.assertEqual(authority_refs, frozenset({AUTH_10}))
        self.assertEqual(blob_digests, {})

    def test_document_scan_collects_authority_from_yaml_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            docs = repository / "docs"
            docs.mkdir()
            (docs / "manifest.yaml").write_text(
                f"historical_authority_record: {AUTH_10}\n",
                encoding="utf-8",
            )
            documents_found, authority_refs, blob_digests, errors = (
                plan_gate._document_metadata(repository, "WORKTREE")
            )
        self.assertEqual(errors, [])
        self.assertEqual(documents_found, {})
        self.assertEqual(authority_refs, frozenset({AUTH_10}))
        self.assertEqual(blob_digests, {})


class SnapshotTests(unittest.TestCase):
    def test_complete_closed_action_graph_snapshot_passes(self) -> None:
        self.assertEqual(
            plan_gate.validate_snapshot(
                manifest(),
                current_metadata=current_metadata(),
                verification_cases=cases(),
                documents=documents(),
            ),
            [],
        )

    def test_not_ready_metadata_closes_coding_and_external_execution(self) -> None:
        metadata = current_metadata()
        metadata["readiness_status"] = "NOT_READY"
        candidate = manifest()
        control = candidate["plan_execution_control"]
        assert isinstance(control, dict)
        current_action = control["current_action"]
        contracts = control["next_action_contracts"]
        assert isinstance(current_action, dict)
        assert isinstance(contracts, dict)
        registered_action = contracts["direction_freeze"]
        assert isinstance(registered_action, dict)
        for action_value in (current_action, registered_action):
            action_value["coding_allowed"] = True
            action_value["external_execution_allowed"] = True
        errors = plan_gate.validate_snapshot(
            candidate,
            current_metadata=metadata,
            verification_cases=cases(),
            documents=documents(),
        )
        self.assertTrue(
            any("must forbid product code changes" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("must forbid external execution" in error for error in errors),
            errors,
        )

    def test_route_policy_rejects_concrete_provider_or_model_identity_inputs(
        self,
    ) -> None:
        for field, value in (
            ("primary_provider", PREFERRED_PROVIDER_IDENTITY),
            ("preferred_model_identity", PREFERRED_MODEL_IDENTITY),
        ):
            with self.subTest(field=field):
                candidate = manifest()
                policy = candidate["provider_route_policy"]
                assert isinstance(policy, dict)
                policy[field] = value

                errors = plan_gate.validate_snapshot(
                    candidate,
                    current_metadata=current_metadata(),
                    verification_cases=cases(),
                    documents=documents(),
                )

                self.assertTrue(
                    any(
                        "provider_route_policy" in error
                        and "concrete Provider/model identity input" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_action_branch_rejects_even_unconfigured_concrete_identity_field(
        self,
    ) -> None:
        candidate = manifest()
        control = candidate["plan_execution_control"]
        assert isinstance(control, dict)
        transition = control["transition"]
        assert isinstance(transition, dict)
        transition["provider_identity"] = "unconfigured-provider"

        errors = plan_gate.validate_snapshot(
            candidate,
            current_metadata=current_metadata(),
            verification_cases=cases(),
            documents=documents(),
        )

        self.assertTrue(
            any(
                "plan_execution_control.transition.provider_identity" in error
                and "concrete Provider/model identity input" in error
                for error in errors
            ),
            errors,
        )

    def test_fallback_eligibility_is_only_trusted_preferred_availability_verdict(
        self,
    ) -> None:
        mutations = (
            (
                "fallback_eligible_outcomes",
                ["structured-output-invalid"],
            ),
            ("structured_output_invalid_allows_fallback", True),
            ("model_review_rejected_allows_fallback", True),
            (
                "raw_http_or_outcome_without_availability_verdict_allows_fallback",
                True,
            ),
            ("required_fallback_verdict", "MODEL_REVIEW_REJECTED"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                candidate = manifest()
                policy = candidate["provider_route_policy"]
                assert isinstance(policy, dict)
                policy[field] = value

                errors = plan_gate.validate_snapshot(
                    candidate,
                    current_metadata=current_metadata(),
                    verification_cases=cases(),
                    documents=documents(),
                )

                self.assertTrue(
                    any(
                        f"provider_route_policy.{field} must equal" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_branch_cannot_treat_output_or_review_failure_as_fallback_input(
        self,
    ) -> None:
        for outcome in (
            "STRUCTURED_OUTPUT_INVALID",
            "MODEL_REVIEW_REJECTED",
            "PROVIDER_HTTP_ERROR",
            "PROVIDER_OUTCOME_UNKNOWN",
        ):
            with self.subTest(outcome=outcome):
                candidate = manifest()
                candidate["direction_quality_gate"] = {
                    "fallback_branch_input": outcome,
                }

                errors = plan_gate.validate_snapshot(
                    candidate,
                    current_metadata=current_metadata(),
                    verification_cases=cases(),
                    documents=documents(),
                )

                self.assertTrue(
                    any(
                        "direction_quality_gate must not branch fallback" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_configured_preferred_identity_is_forbidden_in_plan_control(self) -> None:
        candidate = manifest()
        control = candidate["plan_execution_control"]
        assert isinstance(control, dict)
        current_action = control["current_action"]
        contracts = control["next_action_contracts"]
        assert isinstance(current_action, dict) and isinstance(contracts, dict)
        current_action["allowed_change_paths"].append("validation/nebula47/**")
        contract_by_id(contracts, ACTION_FREEZE)["allowed_change_paths"].append(
            "validation/nebula47/**"
        )

        errors = plan_gate.validate_snapshot(
            candidate,
            current_metadata=current_metadata(),
            verification_cases=cases(),
            documents=documents(),
        )

        self.assertTrue(
            any(
                "plan_execution_control" in error
                and f"configured Provider/model identity {PREFERRED_PROVIDER_IDENTITY}" in error
                for error in errors
            ),
            errors,
        )

    def test_configured_fallback_identity_is_forbidden_in_direction_gate(self) -> None:
        candidate = manifest()
        candidate["direction_quality_gate"] = {
            "route_diagnostic_label": FALLBACK_PROVIDER_IDENTITY
        }

        errors = plan_gate.validate_snapshot(
            candidate,
            current_metadata=current_metadata(),
            verification_cases=cases(),
            documents=documents(),
        )

        self.assertTrue(
            any(
                "direction_quality_gate" in error
                and f"configured Provider/model identity {FALLBACK_PROVIDER_IDENTITY}" in error
                for error in errors
            ),
            errors,
        )

    def test_configured_model_identity_is_forbidden_in_action_graph(self) -> None:
        candidate = manifest()
        control = candidate["plan_execution_control"]
        assert isinstance(control, dict)
        current_action = control["current_action"]
        contracts = control["next_action_contracts"]
        assert isinstance(current_action, dict) and isinstance(contracts, dict)
        leaked_path = f"validation/{PREFERRED_MODEL_IDENTITY}/**"
        current_action["allowed_change_paths"].append(leaked_path)
        contract_by_id(contracts, ACTION_FREEZE)["allowed_change_paths"].append(
            leaked_path
        )

        errors = plan_gate.validate_snapshot(
            candidate,
            current_metadata=current_metadata(),
            verification_cases=cases(),
            documents=documents(),
        )

        self.assertTrue(
            any(
                "plan_execution_control" in error
                and f"configured Provider/model identity {PREFERRED_MODEL_IDENTITY}" in error
                for error in errors
            ),
            errors,
        )

    def test_plan_control_requires_provider_route_policy(self) -> None:
        candidate = manifest()
        del candidate["provider_route_policy"]

        errors = plan_gate.validate_snapshot(
            candidate,
            current_metadata=current_metadata(),
            verification_cases=cases(),
            documents=documents(),
        )

        self.assertTrue(
            any("provider_route_policy must be a mapping" in error for error in errors),
            errors,
        )

    def test_new_action_receipt_fields_are_all_required(self) -> None:
        candidate = manifest()
        for field in (
            "evidence_schema",
            "evidence_path",
            "evidence_verifier",
            "runner_identity_paths",
            "produced_case_ids",
        ):
            broken = copy.deepcopy(candidate)
            broken_control = broken["plan_execution_control"]
            assert isinstance(broken_control, dict)
            broken_action = broken_control["current_action"]
            assert isinstance(broken_action, dict)
            del broken_action[field]
            errors = plan_gate.validate_snapshot(
                broken,
                current_metadata=current_metadata(),
                verification_cases=cases(),
                documents=documents(),
            )
            self.assertTrue(any(field in error for error in errors), (field, errors))

    def test_return_target_must_be_pre_registered(self) -> None:
        candidate = manifest()
        control = candidate["plan_execution_control"]
        assert isinstance(control, dict)
        contracts = control["next_action_contracts"]
        assert isinstance(contracts, dict)
        del contracts["direction_freeze"]
        errors = plan_gate.validate_snapshot(
            candidate,
            current_metadata=current_metadata(),
            verification_cases=cases(),
            documents=documents(),
        )
        self.assertTrue(any("action graph target" in error for error in errors), errors)

    def test_graph_must_include_a_fully_locked_governance_action(self) -> None:
        candidate = manifest()
        control = candidate["plan_execution_control"]
        assert isinstance(control, dict)
        contracts = control["next_action_contracts"]
        assert isinstance(contracts, dict)
        for value in contracts.values():
            assert isinstance(value, dict)
            if value["kind"] == "governance":
                value["kind"] = "manual-review"
        errors = plan_gate.validate_snapshot(
            candidate,
            current_metadata=current_metadata(),
            verification_cases=cases(),
            documents=documents(),
        )
        self.assertTrue(any("governance plan-revision action" in error for error in errors), errors)

    def test_current_pointer_and_locks_must_match_registered_contract(self) -> None:
        candidate = manifest()
        control = candidate["plan_execution_control"]
        assert isinstance(control, dict)
        lock_values = control["locks"]
        assert isinstance(lock_values, dict)
        lock_values["provider_dispatch"] = False
        errors = plan_gate.validate_snapshot(
            candidate,
            current_metadata=current_metadata(action_id=ACTION_FREEZE_REWORK),
            verification_cases=cases(),
            documents=documents(),
        )
        self.assertTrue(any("current locks" in error for error in errors), errors)
        self.assertTrue(any("next_action" in error for error in errors), errors)


class EvidenceReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.action = contract_by_id(registered_contracts(), ACTION_FREEZE)

    def test_digest_bound_evidence_and_runner_identity_pass(self) -> None:
        result, evidence = gate_bundle(self.action)
        verdict, outcomes, errors = configured_gate_result(
            result, self.action, PDR_9, evidence, RUNNER_FILES
        )
        self.assertEqual(verdict, "PASS")
        self.assertEqual(outcomes, {CASE_FREEZE: "PASS", CASE_ADMISSION: "PASS"})
        self.assertEqual(errors, [])

    def test_self_consistent_json_fails_when_trusted_verifier_does_not_run(self) -> None:
        broken_runner_files = dict(RUNNER_FILES)
        broken_runner_files[RUNNER_PATH] = "raise SystemExit(3)\n"
        result, evidence = gate_bundle(
            self.action,
            runner_files=broken_runner_files,
        )
        _, _, errors = configured_gate_result(
            result,
            self.action,
            PDR_9,
            evidence,
            broken_runner_files,
        )
        self.assertTrue(any("exited with status 3" in error for error in errors), errors)

    def test_live_verifier_must_match_verdict_and_report_digest(self) -> None:
        mutations = {
            "plan_gate_verdict": 'result["plan_gate_verdict"] = "FAIL"',
            "verification_report_digest": (
                'result["verification_report_digest"] = "sha256:' + "f" * 64 + '"'
            ),
        }
        for field, mutation in mutations.items():
            with self.subTest(field=field):
                runner_files = dict(RUNNER_FILES)
                runner_files[RUNNER_PATH] = verifier_runner_source(mutation)
                result, evidence = gate_bundle(
                    self.action,
                    runner_files=runner_files,
                )
                _, _, errors = configured_gate_result(
                    result,
                    self.action,
                    PDR_9,
                    evidence,
                    runner_files,
                )
                self.assertTrue(
                    any(field in error and "stdout" in error for error in errors),
                    errors,
                )

    def test_live_verifier_rejects_unregistered_output_fields(self) -> None:
        runner_files = dict(RUNNER_FILES)
        runner_files[RUNNER_PATH] = verifier_runner_source(
            'result["unregistered_claim"] = "PASS"'
        )
        result, evidence = gate_bundle(self.action, runner_files=runner_files)

        _verdict, _outcomes, errors = configured_gate_result(
            result,
            self.action,
            PDR_9,
            evidence,
            runner_files,
        )

        self.assertTrue(any("unexpected fields" in error for error in errors), errors)

    def test_live_verifier_rejects_boolean_or_float_call_counts(self) -> None:
        for mutation in (
            'result["external_model_call_count"] = True',
            'result["external_model_call_count"] = 1.0',
        ):
            with self.subTest(mutation=mutation):
                runner_files = dict(RUNNER_FILES)
                runner_files[RUNNER_PATH] = verifier_runner_source(mutation)
                result, evidence = gate_bundle(self.action, runner_files=runner_files)

                _verdict, _outcomes, errors = configured_gate_result(
                    result,
                    self.action,
                    PDR_9,
                    evidence,
                    runner_files,
                )

                self.assertTrue(
                    any("external_model_call_count" in error for error in errors),
                    errors,
                )

    def test_evidence_digest_uses_exact_crlf_bytes(self) -> None:
        result, evidence = gate_bundle(self.action)
        raw_evidence = ("{\r\n" + evidence[1:]).encode("utf-8")
        result["evidence_artifact_digest"] = "sha256:" + hashlib.sha256(
            raw_evidence
        ).hexdigest()
        _, _, errors = configured_gate_result(
            result,
            self.action,
            PDR_9,
            raw_evidence,
            RUNNER_FILES,
        )
        self.assertEqual(errors, [])

    def test_action_specific_evidence_envelope_is_mandatory(self) -> None:
        result, evidence = gate_bundle(self.action)
        artifact = json.loads(evidence)
        artifact.pop("action_evidence")
        evidence = json.dumps(artifact, sort_keys=True, separators=(",", ":"))
        result["evidence_artifact_digest"] = "sha256:" + hashlib.sha256(
            evidence.encode("utf-8")
        ).hexdigest()

        _verdict, _outcomes, errors = configured_gate_result(
            result,
            self.action,
            PDR_9,
            evidence,
            RUNNER_FILES,
        )

        self.assertTrue(any("action_evidence" in error for error in errors), errors)

    def test_minimal_handwritten_frontmatter_cannot_pass(self) -> None:
        minimal = {
            "id": self.action["result_ref"],
            "plan_revision_ref": PDR_9,
            "action_ref": self.action["id"],
            "verification_case_id": self.action["case_id"],
            "plan_gate_verdict": "PASS",
        }
        verdict, errors = plan_gate.validate_result_for_transition(
            minimal, manifest()["plan_execution_control"]  # type: ignore[arg-type]
        )
        self.assertEqual(verdict, "PASS")
        self.assertTrue(any("missing fields" in error for error in errors), errors)
        self.assertTrue(any("evidence artifact is missing" in error for error in errors), errors)

    def test_exact_artifact_byte_digest_detects_tampering(self) -> None:
        result, evidence = gate_bundle(self.action)
        _, _, errors = configured_gate_result(
            result, self.action, PDR_9, evidence + " ", RUNNER_FILES
        )
        self.assertTrue(any("exact artifact bytes" in error for error in errors), errors)

    def test_canonical_report_and_runner_identity_are_recomputed(self) -> None:
        result, evidence = gate_bundle(self.action)
        result["verification_report_digest"] = digest("forged-report")
        changed_runner = dict(RUNNER_FILES)
        changed_runner[RUNNER_PATH] += "# changed after receipt\n"
        _, _, errors = configured_gate_result(
            result, self.action, PDR_9, evidence, changed_runner
        )
        self.assertTrue(any("canonical case_outcomes" in error for error in errors), errors)
        self.assertTrue(any("protected runner files" in error for error in errors), errors)

    def test_result_and_evidence_bind_exact_action_identity(self) -> None:
        result, evidence = gate_bundle(self.action)
        result["action_ref"] = ACTION_QUALITY
        _, _, errors = configured_gate_result(
            result, self.action, PDR_9, evidence, RUNNER_FILES
        )
        self.assertTrue(any("action_ref" in error for error in errors), errors)

    def test_non_external_action_requires_zero_external_counters(self) -> None:
        result, evidence = gate_bundle(
            self.action, counters={"credential_resolution_count": 1}
        )
        _, _, errors = configured_gate_result(
            result, self.action, PDR_9, evidence, RUNNER_FILES
        )
        self.assertTrue(any("zero external execution counters" in error for error in errors), errors)

    def test_exact_failure_handoff_allows_historical_external_reconciliation(self) -> None:
        handoff = action(
            plan_gate.ITER010_MVP_LIGHT_EXPERIENCE_ACTION_ID,
            plan_gate.ITER010_MVP_LIGHT_EXPERIENCE_CASE_ID,
            "mvp-failure-handoff",
        )
        handoff["evidence_verifier"] = plan_gate.ITER010_MVP_LIGHT_VERIFIER
        counters = {
            "external_model_call_count": 19,
            "provider_dispatch_count": 19,
            "credential_resolution_count": 19,
            "tls_attempt_count": 19,
            "http_dispatch_count": 19,
        }
        result, evidence = gate_bundle(
            handoff,
            counters=counters,
            pdr=PDR_11,
            action_evidence={
                "schema": plan_gate.ITER010_MVP_LIGHT_FAILURE_PACKET_SCHEMA
            },
        )

        _, _, errors = configured_gate_result(
            result, handoff, PDR_11, evidence, RUNNER_FILES
        )

        self.assertEqual([], errors)

    def test_failure_handoff_counter_exception_is_schema_and_regression_closed(self) -> None:
        handoff = action(
            plan_gate.ITER010_MVP_LIGHT_EXPERIENCE_ACTION_ID,
            plan_gate.ITER010_MVP_LIGHT_EXPERIENCE_CASE_ID,
            "mvp-failure-handoff",
        )
        handoff["evidence_verifier"] = plan_gate.ITER010_MVP_LIGHT_VERIFIER
        for packet_schema, full_regression_count, expected_error in (
            ("UNRELATED_PACKET@1", 0, "zero external execution counters"),
            (
                plan_gate.ITER010_MVP_LIGHT_FAILURE_PACKET_SCHEMA,
                1,
                "full_regression_run_count equal to zero",
            ),
        ):
            with self.subTest(
                packet_schema=packet_schema,
                full_regression_count=full_regression_count,
            ):
                result, evidence = gate_bundle(
                    handoff,
                    counters={
                        "external_model_call_count": 19,
                        "provider_dispatch_count": 19,
                        "credential_resolution_count": 19,
                        "tls_attempt_count": 19,
                        "http_dispatch_count": 19,
                        "full_regression_run_count": full_regression_count,
                    },
                    pdr=PDR_11,
                    action_evidence={"schema": packet_schema},
                )

                _, _, errors = configured_gate_result(
                    result, handoff, PDR_11, evidence, RUNNER_FILES
                )

                self.assertTrue(
                    any(expected_error in error for error in errors), errors
                )

    def test_external_pass_requires_positive_model_provider_and_http_counts(self) -> None:
        external_action = contract_by_id(registered_contracts(), ACTION_QUALITY)
        required_positive = (
            "external_model_call_count",
            "provider_dispatch_count",
            "http_dispatch_count",
        )
        for missing_field in required_positive:
            with self.subTest(missing_field=missing_field):
                counters = {field: 1 for field in required_positive}
                counters[missing_field] = 0
                result, evidence = gate_bundle(external_action, counters=counters)
                _, _, errors = configured_gate_result(
                    result, external_action, PDR_9, evidence, RUNNER_FILES
                )
                self.assertTrue(
                    any(missing_field in error and "positive" in error for error in errors),
                    errors,
                )

    def test_external_pass_forbids_full_regression(self) -> None:
        external_action = contract_by_id(registered_contracts(), ACTION_QUALITY)
        result, evidence = gate_bundle(
            external_action,
            counters={
                "external_model_call_count": 1,
                "provider_dispatch_count": 1,
                "http_dispatch_count": 1,
                "full_regression_run_count": 1,
            },
        )
        _, _, errors = configured_gate_result(
            result, external_action, PDR_9, evidence, RUNNER_FILES
        )
        self.assertTrue(any("full_regression_run_count" in error for error in errors), errors)

    def test_external_pass_accepts_positive_dispatches_without_full_regression(self) -> None:
        external_action = contract_by_id(registered_contracts(), ACTION_QUALITY)
        result, evidence = gate_bundle(
            external_action,
            counters={
                "external_model_call_count": 1,
                "provider_dispatch_count": 1,
                "http_dispatch_count": 1,
            },
        )
        _, _, errors = configured_gate_result(
            result, external_action, PDR_9, evidence, RUNNER_FILES
        )
        self.assertEqual(errors, [])

    def test_verdict_uses_invalid_then_fail_then_pass_aggregation(self) -> None:
        result, evidence = gate_bundle(
            self.action,
            "PASS",
            outcome_verdicts={CASE_ADMISSION: "FAIL"},
        )
        _, _, errors = configured_gate_result(
            result, self.action, PDR_9, evidence, RUNNER_FILES
        )
        self.assertTrue(any("INVALID > FAIL > PASS" in error for error in errors), errors)

        invalid_result, invalid_evidence = gate_bundle(
            self.action,
            "INVALID",
            outcome_verdicts={CASE_FREEZE: "INVALID", CASE_ADMISSION: "FAIL"},
        )
        _, _, invalid_errors = configured_gate_result(
            invalid_result, self.action, PDR_9, invalid_evidence, RUNNER_FILES
        )
        self.assertEqual(invalid_errors, [])

    def test_outcomes_exactly_cover_pre_registered_produced_cases(self) -> None:
        result, evidence = gate_bundle(self.action)
        artifact = json.loads(evidence)
        artifact["case_outcomes"] = artifact["case_outcomes"][:1]
        artifact["verification_report_digest"] = plan_gate._canonical_json_digest(
            artifact["case_outcomes"]
        )
        evidence = json.dumps(artifact, sort_keys=True, separators=(",", ":"))
        result["verification_report_digest"] = artifact["verification_report_digest"]
        result["evidence_artifact_digest"] = "sha256:" + hashlib.sha256(
            evidence.encode("utf-8")
        ).hexdigest()
        _, _, errors = configured_gate_result(
            result, self.action, PDR_9, evidence, RUNNER_FILES
        )
        self.assertTrue(any("exactly cover" in error for error in errors), errors)


class Iter010ActionEvidenceBindingTests(unittest.TestCase):
    ROOT_INPUT = provider_neutral_root_input(
        ("Q-LOGIN-FLOW", "Q-ORDER-FLOW", "Q-FAILURE-FLOW")
    )
    OTHER_ROOT_INPUT = provider_neutral_root_input(
        ("Q-STRUCTURE", "Q-BEHAVIOR", "Q-BOUNDARY")
    )
    PREFERRED_PROFILE = {
        "execution_profile_ref": PREFERRED_PROFILE_REF,
        "provider_identity": PREFERRED_PROVIDER_IDENTITY,
        "model_identity": PREFERRED_MODEL_IDENTITY,
    }
    FALLBACK_PROFILE = {
        "execution_profile_ref": FALLBACK_PROFILE_REF,
        "provider_identity": FALLBACK_PROVIDER_IDENTITY,
        "model_identity": FALLBACK_MODEL_IDENTITY,
        "admission_policy_plugin_ref": FALLBACK_PLUGIN_REF,
    }
    FALLBACK_PLUGIN_REF = "policy-plugin:fallback-admission@1"
    FALLBACK_PLUGIN = {
        "schema": "ROUTE_ADMISSION_POLICY_PLUGIN@1",
        "policy_revision": "fallback-admission@1",
    }

    def action_for(
        self, candidate: dict[str, object], action_id: str
    ) -> dict[str, object]:
        control = candidate["plan_execution_control"]
        assert isinstance(control, dict)
        contracts = control["next_action_contracts"]
        assert isinstance(contracts, dict)
        return contract_by_id(contracts, action_id)

    def trusted_receipts(
        self,
        *receipts: tuple[dict[str, object], dict[str, object], str],
    ) -> tuple[
        dict[str, dict[str, object]],
        dict[str, str],
        dict[str, str],
    ]:
        receipt_docs = documents()
        artifacts: dict[str, str] = {}
        blob_digests: dict[str, str] = {}
        for source_action, result, evidence in receipts:
            result_id = str(result["id"])
            metadata = copy.deepcopy(result)
            metadata["__path__"] = source_action["result_path"]
            receipt_docs[result_id] = metadata
            artifacts[result_id] = evidence
            blob_digests[result_id] = plan_gate._canonical_json_digest(result)
        return receipt_docs, artifacts, blob_digests

    def assert_locally_valid(
        self,
        action_value: dict[str, object],
        result: dict[str, object],
        evidence: str,
    ) -> None:
        _verdict, _outcomes, errors = configured_gate_result(
            result,
            action_value,
            PDR_9,
            evidence,
            RUNNER_FILES,
        )
        self.assertEqual(errors, [])

    def cross_action_errors(
        self,
        candidate: dict[str, object],
        target_evidence: str,
        receipt_docs: dict[str, dict[str, object]],
        artifacts: dict[str, str],
        blob_digests: dict[str, str],
    ) -> list[str]:
        control = candidate["plan_execution_control"]
        assert isinstance(control, dict)
        current_action = control["current_action"]
        assert isinstance(current_action, dict)
        return plan_gate._validate_iter010_cross_action_bindings(
            candidate,
            control,
            current_action,
            target_evidence,
            receipt_docs,
            blob_digests,
            artifacts,
            RUNNER_FILES,
        )

    def test_canonical_digest_placeholder_cannot_bind_freeze_root_input(self) -> None:
        candidate = iter010_value_gate_manifest()
        freeze = self.action_for(candidate, ACTION_FREEZE)
        action_evidence = freeze_action_evidence(self.ROOT_INPUT)
        action_evidence["provider_neutral_root_input_set_digest"] = digest(
            "unbound-placeholder"
        )
        result, evidence = gate_bundle(
            freeze,
            action_evidence=action_evidence,
        )

        _verdict, _outcomes, errors = configured_gate_result(
            result,
            freeze,
            PDR_9,
            evidence,
            RUNNER_FILES,
        )

        self.assertTrue(
            any(
                "provider_neutral_root_input_set_digest" in error
                and "must match canonical" in error
                for error in errors
            ),
            errors,
        )

    def test_provider_neutral_root_input_rejects_provider_and_model_identities(self) -> None:
        candidate = iter010_value_gate_manifest()
        freeze = self.action_for(candidate, ACTION_FREEZE)
        for identity in (
            PREFERRED_PROVIDER_IDENTITY,
            FALLBACK_MODEL_IDENTITY,
        ):
            with self.subTest(identity=identity):
                root_input = copy.deepcopy(self.ROOT_INPUT)
                root_input["route_hint"] = identity
                result, evidence = gate_bundle(
                    freeze,
                    action_evidence=freeze_action_evidence(root_input),
                )

                _verdict, _outcomes, errors = configured_gate_result(
                    result,
                    freeze,
                    PDR_9,
                    evidence,
                    RUNNER_FILES,
                )

                self.assertTrue(
                    any(
                        "provider_neutral_root_input_set" in error
                        and f"configured Provider/model identity {identity}" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_provider_neutral_root_input_rejects_unknown_route_control_fields(self) -> None:
        candidate = iter010_value_gate_manifest()
        freeze = self.action_for(candidate, ACTION_FREEZE)
        for field in (
            "provider_identity",
            "model_identity",
            "provider_route",
            "execution_profile",
            "admission_plugin",
        ):
            with self.subTest(field=field):
                root_input = copy.deepcopy(self.ROOT_INPUT)
                root_input[field] = "attacker-controlled-route-value"
                result, evidence = gate_bundle(
                    freeze,
                    action_evidence=freeze_action_evidence(root_input),
                )

                _verdict, _outcomes, errors = configured_gate_result(
                    result,
                    freeze,
                    PDR_9,
                    evidence,
                    RUNNER_FILES,
                )

                self.assertTrue(
                    any(
                        "provider_neutral_root_input_set has unexpected fields"
                        in error
                        and field in error
                        for error in errors
                    ),
                    errors,
                )

    def test_provider_neutral_root_input_requires_complete_cartesian_product(self) -> None:
        candidate = iter010_value_gate_manifest()
        freeze = self.action_for(candidate, ACTION_FREEZE)
        root_input = copy.deepcopy(self.ROOT_INPUT)
        entries = root_input["entries"]
        assert isinstance(entries, list)
        entries.pop()
        result, evidence = gate_bundle(
            freeze,
            action_evidence=freeze_action_evidence(root_input),
        )

        _verdict, _outcomes, errors = configured_gate_result(
            result,
            freeze,
            PDR_9,
            evidence,
            RUNNER_FILES,
        )

        self.assertTrue(
            any("Cartesian product" in error for error in errors),
            errors,
        )

    def test_iter010_result_validation_requires_trusted_route_identities(self) -> None:
        candidate = iter010_value_gate_manifest()
        freeze = self.action_for(candidate, ACTION_FREEZE)
        result, evidence = gate_bundle(
            freeze,
            action_evidence=freeze_action_evidence(self.ROOT_INPUT),
        )

        _verdict, _outcomes, errors = plan_gate.validate_gate_result(
            result,
            freeze,
            PDR_9,
            evidence,
            RUNNER_FILES,
        )

        self.assertTrue(
            any(
                "requires trusted configured Provider/model identities" in error
                for error in errors
            ),
            errors,
        )

    def test_later_quality_cannot_replace_trusted_freeze_root_input(self) -> None:
        candidate = iter010_value_gate_manifest(current_action_id=ACTION_QUALITY)
        freeze = self.action_for(candidate, ACTION_FREEZE)
        preferred = self.action_for(candidate, ACTION_QUALITY)
        freeze_result, freeze_evidence = gate_bundle(
            freeze,
            action_evidence=freeze_action_evidence(self.ROOT_INPUT),
        )
        receipt_docs, artifacts, blob_digests = self.trusted_receipts(
            (freeze, freeze_result, freeze_evidence)
        )
        preferred_result, preferred_evidence = gate_bundle(
            preferred,
            "INVALID",
            action_evidence=quality_action_evidence(
                route_role="preferred",
                root_input=self.OTHER_ROOT_INPUT,
                execution_profile_ref=PREFERRED_PROFILE_REF,
                execution_profile=self.PREFERRED_PROFILE,
                terminal_classification="TERMINAL_UNAVAILABLE",
            ),
        )
        self.assert_locally_valid(preferred, preferred_result, preferred_evidence)

        errors = self.cross_action_errors(
            candidate,
            preferred_evidence,
            receipt_docs,
            artifacts,
            blob_digests,
        )

        self.assertTrue(
            any(
                "provider_neutral_root_input_set" in error
                and "trusted Freeze Result" in error
                for error in errors
            ),
            errors,
        )

    def test_refreeze_rejects_wrong_trusted_preferred_result_seal(self) -> None:
        candidate = iter010_value_gate_manifest(
            current_action_id=ACTION_FALLBACK_REFREEZE
        )
        freeze = self.action_for(candidate, ACTION_FREEZE)
        preferred = self.action_for(candidate, ACTION_QUALITY)
        refreeze = self.action_for(candidate, ACTION_FALLBACK_REFREEZE)
        freeze_result, freeze_evidence = gate_bundle(
            freeze,
            action_evidence=freeze_action_evidence(self.ROOT_INPUT),
        )
        preferred_result, preferred_evidence = gate_bundle(
            preferred,
            "INVALID",
            action_evidence=quality_action_evidence(
                route_role="preferred",
                root_input=self.ROOT_INPUT,
                execution_profile_ref=PREFERRED_PROFILE_REF,
                execution_profile=self.PREFERRED_PROFILE,
                terminal_classification="TERMINAL_UNAVAILABLE",
            ),
        )
        receipt_docs, artifacts, blob_digests = self.trusted_receipts(
            (freeze, freeze_result, freeze_evidence),
            (preferred, preferred_result, preferred_evidence),
        )
        refreeze_result, refreeze_evidence = gate_bundle(
            refreeze,
            action_evidence=fallback_refreeze_action_evidence(
                root_input=self.ROOT_INPUT,
                preferred_result_ref=str(preferred["result_ref"]),
                preferred_seal_digest=digest("wrong-trusted-predecessor-seal"),
                fallback_execution_profile=self.FALLBACK_PROFILE,
                fallback_admission_policy_plugin_ref=self.FALLBACK_PLUGIN_REF,
                fallback_admission_policy_plugin=self.FALLBACK_PLUGIN,
            ),
        )
        self.assert_locally_valid(refreeze, refreeze_result, refreeze_evidence)

        errors = self.cross_action_errors(
            candidate,
            refreeze_evidence,
            receipt_docs,
            artifacts,
            blob_digests,
        )

        self.assertTrue(
            any(
                "preferred_invalid_predecessor_seal_digest" in error
                and "trusted preferred Result seal" in error
                for error in errors
            ),
            errors,
        )

    def test_fallback_quality_must_reuse_refrozen_profile_and_plugin(self) -> None:
        candidate = iter010_value_gate_manifest(
            current_action_id=ACTION_FALLBACK_QUALITY
        )
        freeze = self.action_for(candidate, ACTION_FREEZE)
        refreeze = self.action_for(candidate, ACTION_FALLBACK_REFREEZE)
        fallback = self.action_for(candidate, ACTION_FALLBACK_QUALITY)
        freeze_result, freeze_evidence = gate_bundle(
            freeze,
            action_evidence=freeze_action_evidence(self.ROOT_INPUT),
        )
        refreeze_result, refreeze_evidence = gate_bundle(
            refreeze,
            action_evidence=fallback_refreeze_action_evidence(
                root_input=self.ROOT_INPUT,
                preferred_result_ref=str(
                    self.action_for(candidate, ACTION_QUALITY)["result_ref"]
                ),
                preferred_seal_digest=digest("locally-valid-preferred-seal"),
                fallback_execution_profile=self.FALLBACK_PROFILE,
                fallback_admission_policy_plugin_ref=self.FALLBACK_PLUGIN_REF,
                fallback_admission_policy_plugin=self.FALLBACK_PLUGIN,
            ),
        )
        self.assert_locally_valid(refreeze, refreeze_result, refreeze_evidence)
        receipt_docs, artifacts, blob_digests = self.trusted_receipts(
            (freeze, freeze_result, freeze_evidence),
            (refreeze, refreeze_result, refreeze_evidence),
        )
        refreeze_result_ref = str(refreeze["result_ref"])
        refreeze_seal = plan_gate._plan_result_seal_digest(
            refreeze_result_ref,
            refreeze_result,
            blob_digests[refreeze_result_ref],
            refreeze_evidence.encode("utf-8"),
        )
        mismatch_cases = {
            "execution_profile": (
                {"schema": "ROUTE_EXECUTION_PROFILE@1", "revision": "different"},
                self.FALLBACK_PLUGIN,
            ),
            "admission_policy_plugin": (
                self.FALLBACK_PROFILE,
                {
                    "schema": "ROUTE_ADMISSION_POLICY_PLUGIN@1",
                    "policy_revision": "different",
                },
            ),
        }
        for mismatched_field, (profile, plugin) in mismatch_cases.items():
            with self.subTest(mismatched_field=mismatched_field):
                fallback_result, fallback_evidence = gate_bundle(
                    fallback,
                    action_evidence=quality_action_evidence(
                        route_role="fallback",
                        root_input=self.ROOT_INPUT,
                        execution_profile_ref=FALLBACK_PROFILE_REF,
                        execution_profile=profile,
                        terminal_classification="AVAILABLE",
                        fallback_refreeze_predecessor_ref=refreeze_result_ref,
                        fallback_refreeze_predecessor_seal_digest=refreeze_seal,
                        admission_policy_plugin_ref=self.FALLBACK_PLUGIN_REF,
                        admission_policy_plugin=plugin,
                    ),
                    counters={
                        "external_model_call_count": 1,
                        "provider_dispatch_count": 1,
                        "http_dispatch_count": 1,
                    },
                )
                self.assert_locally_valid(fallback, fallback_result, fallback_evidence)

                errors = self.cross_action_errors(
                    candidate,
                    fallback_evidence,
                    receipt_docs,
                    artifacts,
                    blob_digests,
                )

                self.assertTrue(
                    any(
                        f"cross-action evidence {mismatched_field}" in error
                        and "trusted Refreeze Result" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_refreeze_rejects_untrusted_profile_and_plugin_objects(self) -> None:
        candidate = iter010_value_gate_manifest(
            current_action_id=ACTION_FALLBACK_REFREEZE
        )
        freeze = self.action_for(candidate, ACTION_FREEZE)
        preferred = self.action_for(candidate, ACTION_QUALITY)
        refreeze = self.action_for(candidate, ACTION_FALLBACK_REFREEZE)
        freeze_result, freeze_evidence = gate_bundle(
            freeze,
            action_evidence=freeze_action_evidence(self.ROOT_INPUT),
        )
        preferred_result, preferred_evidence = gate_bundle(
            preferred,
            "INVALID",
            action_evidence=quality_action_evidence(
                route_role="preferred",
                root_input=self.ROOT_INPUT,
                execution_profile_ref=PREFERRED_PROFILE_REF,
                execution_profile=self.PREFERRED_PROFILE,
                terminal_classification="TERMINAL_UNAVAILABLE",
            ),
        )
        receipt_docs, artifacts, blob_digests = self.trusted_receipts(
            (freeze, freeze_result, freeze_evidence),
            (preferred, preferred_result, preferred_evidence),
        )
        preferred_result_ref = str(preferred["result_ref"])
        preferred_seal = plan_gate._plan_result_seal_digest(
            preferred_result_ref,
            preferred_result,
            blob_digests[preferred_result_ref],
            preferred_evidence.encode("utf-8"),
        )
        mismatch_cases = {
            "fallback_execution_profile": (
                {
                    **self.FALLBACK_PROFILE,
                    "model_identity": "untrusted-model-object",
                },
                self.FALLBACK_PLUGIN,
            ),
            "fallback_admission_policy_plugin": (
                self.FALLBACK_PROFILE,
                {
                    **self.FALLBACK_PLUGIN,
                    "policy_revision": "untrusted-plugin-object",
                },
            ),
        }
        for field, (profile, plugin) in mismatch_cases.items():
            with self.subTest(field=field):
                refreeze_result, refreeze_evidence = gate_bundle(
                    refreeze,
                    action_evidence=fallback_refreeze_action_evidence(
                        root_input=self.ROOT_INPUT,
                        preferred_result_ref=preferred_result_ref,
                        preferred_seal_digest=preferred_seal,
                        fallback_execution_profile=profile,
                        fallback_admission_policy_plugin_ref=self.FALLBACK_PLUGIN_REF,
                        fallback_admission_policy_plugin=plugin,
                    ),
                )
                self.assert_locally_valid(
                    refreeze,
                    refreeze_result,
                    refreeze_evidence,
                )

                errors = self.cross_action_errors(
                    candidate,
                    refreeze_evidence,
                    receipt_docs,
                    artifacts,
                    blob_digests,
                )

                self.assertTrue(
                    any(
                        f"cross-action evidence {field}" in error
                        and "trusted" in error
                        for error in errors
                    ),
                    errors,
                )


class ExternalAdmissionTests(unittest.TestCase):
    def test_validated_freeze_receipt_unlocks_external_quality_and_admission(self) -> None:
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        result, evidence = gate_bundle(freeze_action)
        self.assertEqual(
            plan_gate.validate_snapshot(
                manifest(current_action_id=ACTION_QUALITY),
                current_metadata=current_metadata(action_id=ACTION_QUALITY),
                verification_cases=cases(),
                documents=receipt_documents(result),
                result_evidence_artifacts={str(result["id"]): evidence},
                runner_files=RUNNER_FILES,
            ),
            [],
        )

    def test_plain_pass_metadata_without_evidence_cannot_unlock_external_action(self) -> None:
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        result, _ = gate_bundle(freeze_action)
        errors = plan_gate.validate_snapshot(
            manifest(current_action_id=ACTION_QUALITY),
            current_metadata=current_metadata(action_id=ACTION_QUALITY),
            verification_cases=cases(),
            documents=receipt_documents(result),
            runner_files=RUNNER_FILES,
        )
        self.assertTrue(any("must be PASS" in error for error in errors), errors)

    def test_matrix_text_pass_cannot_replace_machine_receipt_for_admission(self) -> None:
        errors = plan_gate.validate_snapshot(
            manifest(current_action_id=ACTION_QUALITY),
            current_metadata=current_metadata(action_id=ACTION_QUALITY),
            verification_cases=cases(
                admission_verdict="PASS",
                freeze_verdict="PASS",
            ),
            documents=documents(),
            runner_files=RUNNER_FILES,
        )
        self.assertTrue(
            any(CASE_ADMISSION in error and "must be PASS" in error for error in errors),
            errors,
        )

    def test_external_action_must_name_admission_as_prerequisite(self) -> None:
        candidate = manifest(current_action_id=ACTION_QUALITY)
        control = candidate["plan_execution_control"]
        assert isinstance(control, dict)
        current_action = control["current_action"]
        contracts = control["next_action_contracts"]
        assert isinstance(current_action, dict) and isinstance(contracts, dict)
        current_action["prerequisite_case_ids"] = [CASE_FREEZE]
        contract_by_id(contracts, ACTION_QUALITY)["prerequisite_case_ids"] = [CASE_FREEZE]
        errors = plan_gate.validate_snapshot(
            candidate,
            current_metadata=current_metadata(action_id=ACTION_QUALITY),
            verification_cases=cases(freeze_verdict="PASS"),
            documents=documents(),
        )
        self.assertTrue(any(CASE_ADMISSION in error for error in errors), errors)

    def test_explicit_matrix_fail_overrides_a_valid_receipt(self) -> None:
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        result, evidence = gate_bundle(freeze_action)
        errors = plan_gate.validate_snapshot(
            manifest(current_action_id=ACTION_QUALITY),
            current_metadata=current_metadata(action_id=ACTION_QUALITY),
            verification_cases=cases(admission_verdict="FAIL"),
            documents=receipt_documents(result),
            result_evidence_artifacts={str(result["id"]): evidence},
            runner_files=RUNNER_FILES,
        )
        self.assertTrue(any(CASE_ADMISSION in error and "must be PASS" in error for error in errors), errors)

    def test_result_at_wrong_markdown_path_cannot_satisfy_prerequisite(self) -> None:
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        result, evidence = gate_bundle(freeze_action)
        errors = plan_gate.validate_snapshot(
            manifest(current_action_id=ACTION_QUALITY),
            current_metadata=current_metadata(action_id=ACTION_QUALITY),
            verification_cases=cases(),
            documents=receipt_documents(
                result, path_override=f"{ITERATION_RESULTS}/forged-result.md"
            ),
            result_evidence_artifacts={str(result["id"]): evidence},
            runner_files=RUNNER_FILES,
        )
        self.assertTrue(errors, "Result outside action.result_path must not be trusted")


class SharedQualityReceiptTests(unittest.TestCase):
    def bundles(
        self, preferred_verdict: str, fallback_verdict: str
    ) -> tuple[
        dict[str, object],
        dict[str, dict[str, object]],
        dict[str, str],
    ]:
        candidate = manifest()
        control = candidate["plan_execution_control"]
        assert isinstance(control, dict)
        contracts = control["next_action_contracts"]
        assert isinstance(contracts, dict)
        preferred_action = contract_by_id(contracts, ACTION_QUALITY)
        fallback_action = action(
            "ITER-010-ACTION-DIRECTION-QUALITY-FALLBACK-001",
            CASE_QUALITY,
            "four-arm-direction-quality-gate",
            external_execution_allowed=True,
            prerequisite_case_ids=[CASE_FREEZE, CASE_ADMISSION],
        )
        fallback_action["result_ref"] = (
            "ITER-010-RESULT-V-DIRECTION-QUALITY-FALLBACK-001"
        )
        fallback_action["result_path"] = (
            f"{ITERATION_RESULTS}/v-direction-quality-fallback-001.md"
        )
        fallback_action["evidence_path"] = (
            f"{ITERATION_RESULTS}/v-direction-quality-fallback-001.evidence.json"
        )
        fallback_action["allowed_change_paths"] = [
            CURRENT_PATH,
            MANIFEST_PATH,
            str(fallback_action["result_path"]),
            str(fallback_action["evidence_path"]),
        ]
        contracts["fallback_quality"] = contract(
            fallback_action,
            pass_next=ACTION_MINIMUM_WEB,
            fail_next=ACTION_DIRECTION_REWORK,
            invalid_next=str(fallback_action["id"]),
            lock_values=locks(provider_dispatch=False),
        )

        positive_counters = {
            "external_model_call_count": 1,
            "provider_dispatch_count": 1,
            "http_dispatch_count": 1,
        }
        preferred_result, preferred_evidence = gate_bundle(
            preferred_action,
            preferred_verdict,
            counters=positive_counters if preferred_verdict == "PASS" else None,
        )
        fallback_result, fallback_evidence = gate_bundle(
            fallback_action,
            fallback_verdict,
            counters=positive_counters if fallback_verdict == "PASS" else None,
        )
        result_documents = documents()
        for result, source_action in (
            (preferred_result, preferred_action),
            (fallback_result, fallback_action),
        ):
            metadata = copy.deepcopy(result)
            metadata["__path__"] = source_action["result_path"]
            result_documents[str(result["id"])] = metadata
        return (
            control,
            result_documents,
            {
                str(preferred_result["id"]): preferred_evidence,
                str(fallback_result["id"]): fallback_evidence,
            },
        )

    def test_preferred_invalid_and_fallback_pass_resolve_one_quality_receipt(self) -> None:
        control, result_documents, artifacts = self.bundles("INVALID", "PASS")
        self.assertEqual(
            plan_gate._resolved_pass(
                cases(),
                CASE_QUALITY,
                "shared quality Case",
                documents=result_documents,
                plan_revision_ref=PDR_9,
                control=control,
                result_evidence_artifacts=artifacts,
                runner_files=RUNNER_FILES,
            ),
            [],
        )

    def test_two_quality_pass_receipts_fail_closed(self) -> None:
        control, result_documents, artifacts = self.bundles("PASS", "PASS")
        errors = plan_gate._resolved_pass(
            cases(),
            CASE_QUALITY,
            "shared quality Case",
            documents=result_documents,
            plan_revision_ref=PDR_9,
            control=control,
            result_evidence_artifacts=artifacts,
            runner_files=RUNNER_FILES,
        )
        self.assertTrue(any("multiple exact PASS Results" in error for error in errors), errors)


class PathTests(unittest.TestCase):
    def test_forbidden_path_wins_over_allowed_path(self) -> None:
        current_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        current_action["allowed_change_paths"].append("src/software_world_model/")
        errors = plan_gate.validate_changed_paths(
            current_action, ["src/software_world_model/ai_infrastructure/model.py"]
        )
        self.assertEqual(len(errors), 1, errors)
        self.assertIn("forbidden", errors[0])

    def test_bootstrap_rejects_product_and_arbitrary_test_validation_code(self) -> None:
        errors = plan_gate.validate_bootstrap_paths(
            [
                "src/software_world_model/application_services/answer.py",
                "tests/test_conversational_engineering_model.py",
                "validation/unregistered_product_runner.py",
            ]
        )
        self.assertTrue(any("forbidden" in error for error in errors), errors)
        self.assertEqual(sum("not allowed" in error for error in errors), 3, errors)


class TransitionTests(unittest.TestCase):
    @staticmethod
    def _current_manifest() -> dict[str, object]:
        path = (
            plan_gate.REPOSITORY
            / "docs/project/iterations/iteration-010/manifest.yaml"
        )
        return plan_gate.load_safe_yaml(path.read_text(encoding="utf-8"))

    def test_lightweight_handoff_binds_actual_trusted_parent(self) -> None:
        action = {
            "evidence_verifier": plan_gate.ITER010_MVP_LIGHT_VERIFIER,
            "id": plan_gate.ITER010_MVP_LIGHT_EXPERIENCE_ACTION_ID,
            "case_id": plan_gate.ITER010_MVP_LIGHT_EXPERIENCE_CASE_ID,
        }
        evidence = json.dumps(
            {
                "action_evidence": {
                    "handoff_parent_identity": {
                        "commit": "a" * 40,
                        "tree": "b" * 40,
                    }
                }
            }
        )
        self.assertEqual(
            [],
            plan_gate._validate_lightweight_handoff_parent_binding(
                action, evidence, "a" * 40, "b" * 40
            ),
        )

    def test_lightweight_handoff_rejects_claimed_non_parent_commit_and_tree(self) -> None:
        action = {
            "evidence_verifier": plan_gate.ITER010_MVP_LIGHT_VERIFIER,
            "id": plan_gate.ITER010_MVP_LIGHT_EXPERIENCE_ACTION_ID,
            "case_id": plan_gate.ITER010_MVP_LIGHT_EXPERIENCE_CASE_ID,
        }
        evidence = json.dumps(
            {
                "action_evidence": {
                    "handoff_parent_identity": {
                        "commit": "e" * 40,
                        "tree": "f" * 40,
                    }
                }
            }
        )
        errors = plan_gate._validate_lightweight_handoff_parent_binding(
            action, evidence, "a" * 40, "b" * 40
        )
        self.assertEqual(2, len(errors), errors)
        self.assertTrue(any("actual trusted parent commit" in error for error in errors))
        self.assertTrue(any("actual trusted parent tree" in error for error in errors))

    def test_failure_handoff_recovery_root_is_exact(self) -> None:
        recovery = {
            "schema": plan_gate.ITER010_FAILURE_HANDOFF_RECOVERY_SCHEMA,
            "status": "authorized-recovery-root-installed",
            "authorization_ref": (
                plan_gate.ITER010_FAILURE_HANDOFF_RECOVERY_AUTHORIZATION_REF
            ),
            "authorization_reusable": False,
            "trusted_base_commit": (
                plan_gate.ITER010_FAILURE_HANDOFF_RECOVERY_BASE_COMMIT
            ),
            "trusted_base_tree": (
                plan_gate.ITER010_FAILURE_HANDOFF_RECOVERY_BASE_TREE
            ),
            "interrupted_plan_revision_ref": "ITER-010-PDR-010",
            "interrupted_action_id": (
                plan_gate.ITER010_MVP_LIGHT_EXPERIENCE_ACTION_ID
            ),
            "target_plan_revision_ref": (
                plan_gate.ITER010_FAILURE_HANDOFF_RECOVERY_TARGET_REVISION
            ),
            "scope": "governance-only-failure-handoff-contract-recovery",
            "old_gate_compliance_claimed": False,
            "product_code_changes_allowed": False,
            "external_execution_allowed": False,
            "one_time_recovery": True,
        }
        manifest_value = {
            "mvp_failure_handoff_recovery": recovery,
            "plan_execution_control": {
                "plan_revision_ref": (
                    plan_gate.ITER010_FAILURE_HANDOFF_RECOVERY_TARGET_REVISION
                ),
                "authorization_refs": [
                    plan_gate.ITER010_FAILURE_HANDOFF_RECOVERY_AUTHORIZATION_REF
                ],
                "current_action": {
                    "id": plan_gate.ITER010_MVP_LIGHT_EXPERIENCE_ACTION_ID,
                    "case_id": plan_gate.ITER010_MVP_LIGHT_EXPERIENCE_CASE_ID,
                    "kind": "mvp-failure-handoff",
                    "evidence_verifier": plan_gate.ITER010_MVP_LIGHT_VERIFIER,
                    "coding_allowed": False,
                    "external_execution_allowed": False,
                },
                "locks": {field: True for field in plan_gate.LOCK_KEYS},
            },
        }
        self.assertEqual(
            plan_gate._failure_handoff_recovery_errors(manifest_value), []
        )
        recovery["old_gate_compliance_claimed"] = True
        errors = plan_gate._failure_handoff_recovery_errors(manifest_value)
        self.assertTrue(any("old_gate_compliance_claimed" in error for error in errors), errors)

        recovery["old_gate_compliance_claimed"] = False
        del manifest_value["mvp_failure_handoff_recovery"]
        missing_errors = plan_gate._failure_handoff_recovery_errors(manifest_value)
        self.assertTrue(
            any("requires mvp_failure_handoff_recovery" in error for error in missing_errors),
            missing_errors,
        )

    def test_lightweight_user_direction_does_not_require_candidate_identity(self) -> None:
        action = {
            "evidence_verifier": plan_gate.ITER010_MVP_LIGHT_VERIFIER,
            "id": "ITER-010-ACTION-USER-DIRECTION-DECISION-001",
            "case_id": "V-PREVIEW-002",
        }
        self.assertEqual(
            [],
            plan_gate._validate_lightweight_handoff_parent_binding(
                action,
                json.dumps({"action_evidence": {"schema": "direction-record"}}),
                "a" * 40,
                "b" * 40,
            ),
        )

    def validate_freeze_transition(self, verdict: str) -> list[str]:
        next_action = {
            "PASS": ACTION_QUALITY,
            "FAIL": ACTION_FREEZE_REWORK,
            "INVALID": ACTION_FREEZE,
        }[verdict]
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        result, evidence = gate_bundle(freeze_action, verdict)
        return plan_gate.validate_transition(
            manifest(),
            manifest(current_action_id=next_action),
            [
                CURRENT_PATH,
                MANIFEST_PATH,
                str(freeze_action["result_path"]),
                str(freeze_action["evidence_path"]),
            ],
            base_current_metadata=current_metadata(),
            target_current_metadata=current_metadata(action_id=next_action),
            base_verification_cases=cases(),
            target_verification_cases=cases(),
            base_documents=documents(),
            target_documents=receipt_documents(result),
            target_result_metadata=result,
            target_result_evidence_artifacts={str(result["id"]): evidence},
            target_result_evidence_text=evidence,
            base_runner_files=RUNNER_FILES,
            target_runner_files=RUNNER_FILES,
        )

    def test_pass_fail_invalid_follow_only_pre_registered_branches(self) -> None:
        self.assertEqual(self.validate_freeze_transition("PASS"), [])
        self.assertEqual(self.validate_freeze_transition("FAIL"), [])
        self.assertEqual(self.validate_freeze_transition("INVALID"), [])

    def test_runner_change_cannot_self_sign_result_in_same_transition(self) -> None:
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        changed_runner_files = dict(RUNNER_FILES)
        changed_runner_files[RUNNER_PATH] += "# candidate-only change\n"
        result, evidence = gate_bundle(
            freeze_action,
            runner_files=changed_runner_files,
        )
        errors = plan_gate.validate_transition(
            manifest(),
            manifest(current_action_id=ACTION_QUALITY),
            [
                CURRENT_PATH,
                MANIFEST_PATH,
                RUNNER_PATH,
                str(freeze_action["result_path"]),
                str(freeze_action["evidence_path"]),
            ],
            base_current_metadata=current_metadata(),
            target_current_metadata=current_metadata(action_id=ACTION_QUALITY),
            base_verification_cases=cases(),
            target_verification_cases=cases(),
            base_documents=documents(),
            target_documents=receipt_documents(result),
            target_result_metadata=result,
            target_result_evidence_artifacts={str(result["id"]): evidence},
            target_result_evidence_text=evidence,
            base_runner_files=RUNNER_FILES,
            target_runner_files=changed_runner_files,
        )
        self.assertTrue(
            any("must be committed before" in error for error in errors),
            errors,
        )

    def test_target_runner_is_not_executed_by_trusted_transition_gate(self) -> None:
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        result, evidence = gate_bundle(freeze_action)
        target_runner_files = dict(RUNNER_FILES)
        target_runner_files[RUNNER_PATH] = "raise SystemExit(99)\n"
        receipt_docs = receipt_documents(result)
        artifacts = {str(result["id"]): evidence}
        errors = plan_gate.validate_transition(
            manifest(current_action_id=ACTION_QUALITY),
            manifest(current_action_id=ACTION_QUALITY),
            [RUNNER_PATH],
            base_current_metadata=current_metadata(action_id=ACTION_QUALITY),
            target_current_metadata=current_metadata(action_id=ACTION_QUALITY),
            base_verification_cases=cases(),
            target_verification_cases=cases(),
            base_documents=receipt_docs,
            target_documents=receipt_docs,
            base_result_evidence_artifacts=artifacts,
            target_result_evidence_artifacts=artifacts,
            base_runner_files=RUNNER_FILES,
            target_runner_files=target_runner_files,
        )
        self.assertEqual(errors, [])

    def test_preexisting_runner_can_sign_result_in_later_transition(self) -> None:
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        preexisting_runner_files = dict(RUNNER_FILES)
        preexisting_runner_files[RUNNER_PATH] += "# committed before execution\n"
        result, evidence = gate_bundle(
            freeze_action,
            runner_files=preexisting_runner_files,
        )
        errors = plan_gate.validate_transition(
            manifest(),
            manifest(current_action_id=ACTION_QUALITY),
            [
                CURRENT_PATH,
                MANIFEST_PATH,
                str(freeze_action["result_path"]),
                str(freeze_action["evidence_path"]),
            ],
            base_current_metadata=current_metadata(),
            target_current_metadata=current_metadata(action_id=ACTION_QUALITY),
            base_verification_cases=cases(),
            target_verification_cases=cases(),
            base_documents=documents(),
            target_documents=receipt_documents(result),
            target_result_metadata=result,
            target_result_evidence_artifacts={str(result["id"]): evidence},
            target_result_evidence_text=evidence,
            base_runner_files=preexisting_runner_files,
            target_runner_files=preexisting_runner_files,
        )
        self.assertEqual(errors, [])

    def test_result_and_evidence_must_change_together(self) -> None:
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        result, evidence = gate_bundle(freeze_action)
        errors = plan_gate.validate_transition(
            manifest(),
            manifest(current_action_id=ACTION_QUALITY),
            [CURRENT_PATH, MANIFEST_PATH, str(freeze_action["result_path"])],
            base_current_metadata=current_metadata(),
            target_current_metadata=current_metadata(action_id=ACTION_QUALITY),
            base_verification_cases=cases(),
            target_verification_cases=cases(),
            base_documents=documents(),
            target_documents=receipt_documents(result),
            target_result_metadata=result,
            target_result_evidence_artifacts={str(result["id"]): evidence},
            target_result_evidence_text=evidence,
            base_runner_files=RUNNER_FILES,
            target_runner_files=RUNNER_FILES,
        )
        self.assertTrue(errors, "transition must not consume unchanged evidence")

    def test_candidate_cannot_widen_paths_and_use_them_in_same_revision(self) -> None:
        target = manifest()
        control = target["plan_execution_control"]
        assert isinstance(control, dict)
        control["plan_revision_ref"] = PDR_10
        control["authorization_refs"] = [AUTH_10]
        current_action = control["current_action"]
        contracts = control["next_action_contracts"]
        assert isinstance(current_action, dict) and isinstance(contracts, dict)
        current_action["allowed_change_paths"].append("src/software_world_model/new.py")
        contract_by_id(contracts, ACTION_FREEZE)["allowed_change_paths"].append(
            "src/software_world_model/new.py"
        )
        errors = plan_gate.validate_transition(
            manifest(),
            target,
            [MANIFEST_PATH, "src/software_world_model/new.py"],
            base_current_metadata=current_metadata(),
            target_current_metadata=current_metadata(pdr=PDR_10),
            base_verification_cases=cases(),
            target_verification_cases=cases(),
            base_documents=documents(),
            target_documents=documents(include_revision_10=True),
            base_runner_files=RUNNER_FILES,
            target_runner_files=RUNNER_FILES,
        )
        self.assertTrue(any("not allowed" in error for error in errors), errors)

    def test_transition_cannot_rewrite_pre_registered_target_contract(self) -> None:
        target = manifest(current_action_id=ACTION_QUALITY)
        control = target["plan_execution_control"]
        assert isinstance(control, dict)
        current_action = control["current_action"]
        contracts = control["next_action_contracts"]
        assert isinstance(current_action, dict) and isinstance(contracts, dict)
        current_action["allowed_change_paths"].append("src/software_world_model/**")
        contract_by_id(contracts, ACTION_QUALITY)["allowed_change_paths"].append(
            "src/software_world_model/**"
        )
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        result, evidence = gate_bundle(freeze_action)
        errors = plan_gate.validate_transition(
            manifest(),
            target,
            [CURRENT_PATH, MANIFEST_PATH, str(freeze_action["result_path"]), str(freeze_action["evidence_path"])],
            base_current_metadata=current_metadata(),
            target_current_metadata=current_metadata(action_id=ACTION_QUALITY),
            base_verification_cases=cases(),
            target_verification_cases=cases(),
            base_documents=documents(),
            target_documents=receipt_documents(result),
            target_result_metadata=result,
            target_result_evidence_artifacts={str(result["id"]): evidence},
            target_result_evidence_text=evidence,
            base_runner_files=RUNNER_FILES,
            target_runner_files=RUNNER_FILES,
        )
        self.assertTrue(any("preserve pre-registered contracts" in error for error in errors), errors)

    def test_action_transition_and_plan_revision_are_separate(self) -> None:
        target = manifest(current_action_id=ACTION_QUALITY, pdr=PDR_10)
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        result, evidence = gate_bundle(freeze_action)
        errors = plan_gate.validate_transition(
            manifest(),
            target,
            [CURRENT_PATH, MANIFEST_PATH, str(freeze_action["result_path"]), str(freeze_action["evidence_path"])],
            base_current_metadata=current_metadata(),
            target_current_metadata=current_metadata(action_id=ACTION_QUALITY, pdr=PDR_10),
            base_verification_cases=cases(),
            target_verification_cases=cases(),
            base_documents=documents(),
            target_documents=documents(include_revision_10=True),
            target_result_metadata=result,
            target_result_evidence_artifacts={str(result["id"]): evidence},
            target_result_evidence_text=evidence,
            base_runner_files=RUNNER_FILES,
            target_runner_files=RUNNER_FILES,
        )
        self.assertTrue(any("must be separate" in error for error in errors), errors)

    def test_route_profile_and_plugin_rewrites_require_plan_revision(self) -> None:
        mutations = {}

        route_target = manifest()
        route_configurations = route_target["execution_profile_configurations"]
        assert isinstance(route_configurations, dict)
        fallback_profile = route_configurations["fallback"]
        assert isinstance(fallback_profile, dict)
        replacement_plugin_ref = "policy-plugin:replacement-admission@1"
        fallback_profile["admission_policy_plugin_ref"] = replacement_plugin_ref
        route_target[replacement_plugin_ref] = {
            "schema": "ROUTE_ADMISSION_POLICY_PLUGIN@1",
            "policy_revision": "replacement-admission@1",
        }
        mutations["route"] = route_target

        profile_target = manifest()
        profile_policy = profile_target["provider_route_policy"]
        profile_configurations = profile_target["execution_profile_configurations"]
        assert isinstance(profile_policy, dict)
        assert isinstance(profile_configurations, dict)
        preferred_profile = profile_configurations["preferred"]
        assert isinstance(preferred_profile, dict)
        replacement_profile_ref = "runtime-config:replacement-preferred-profile"
        profile_policy["preferred_execution_profile_ref"] = replacement_profile_ref
        preferred_profile["execution_profile_ref"] = replacement_profile_ref
        mutations["profile"] = profile_target

        plugin_target = manifest()
        plugin = plugin_target[FALLBACK_PLUGIN_REF]
        assert isinstance(plugin, dict)
        plugin["policy_revision"] = "replacement-policy@2"
        mutations["plugin"] = plugin_target

        for scope, target in mutations.items():
            with self.subTest(scope=scope):
                errors = plan_gate.validate_transition(
                    manifest(),
                    target,
                    [MANIFEST_PATH],
                    base_current_metadata=current_metadata(),
                    target_current_metadata=current_metadata(),
                    base_verification_cases=cases(),
                    target_verification_cases=cases(),
                    base_documents=documents(),
                    target_documents=documents(),
                    base_runner_files=RUNNER_FILES,
                    target_runner_files=RUNNER_FILES,
                )

                self.assertTrue(
                    any(
                        "plan semantics" in error
                        and "revision" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_action_transition_cannot_carry_route_profile_or_plugin_rewrite(self) -> None:
        freeze_action = contract_by_id(registered_contracts(), ACTION_FREEZE)
        result, evidence = gate_bundle(freeze_action)
        mutations = {}

        route_target = manifest(current_action_id=ACTION_QUALITY)
        route_configurations = route_target["execution_profile_configurations"]
        assert isinstance(route_configurations, dict)
        fallback_profile = route_configurations["fallback"]
        assert isinstance(fallback_profile, dict)
        replacement_plugin_ref = "policy-plugin:replacement-admission@1"
        fallback_profile["admission_policy_plugin_ref"] = replacement_plugin_ref
        route_target[replacement_plugin_ref] = {
            "schema": "ROUTE_ADMISSION_POLICY_PLUGIN@1",
            "policy_revision": "replacement-admission@1",
        }
        mutations["route"] = route_target

        profile_target = manifest(current_action_id=ACTION_QUALITY)
        profile_policy = profile_target["provider_route_policy"]
        profile_configurations = profile_target["execution_profile_configurations"]
        assert isinstance(profile_policy, dict)
        assert isinstance(profile_configurations, dict)
        preferred_profile = profile_configurations["preferred"]
        assert isinstance(preferred_profile, dict)
        replacement_profile_ref = "runtime-config:replacement-preferred-profile"
        profile_policy["preferred_execution_profile_ref"] = replacement_profile_ref
        preferred_profile["execution_profile_ref"] = replacement_profile_ref
        mutations["profile"] = profile_target

        plugin_target = manifest(current_action_id=ACTION_QUALITY)
        plugin = plugin_target[FALLBACK_PLUGIN_REF]
        assert isinstance(plugin, dict)
        plugin["policy_revision"] = "replacement-policy@2"
        mutations["plugin"] = plugin_target

        for scope, target in mutations.items():
            with self.subTest(scope=scope):
                errors = plan_gate.validate_transition(
                    manifest(),
                    target,
                    [
                        CURRENT_PATH,
                        MANIFEST_PATH,
                        str(freeze_action["result_path"]),
                        str(freeze_action["evidence_path"]),
                    ],
                    base_current_metadata=current_metadata(),
                    target_current_metadata=current_metadata(action_id=ACTION_QUALITY),
                    base_verification_cases=cases(),
                    target_verification_cases=cases(),
                    base_documents=documents(),
                    target_documents=receipt_documents(result),
                    target_result_metadata=result,
                    target_result_evidence_artifacts={str(result["id"]): evidence},
                    target_result_evidence_text=evidence,
                    base_runner_files=RUNNER_FILES,
                    target_runner_files=RUNNER_FILES,
                )

                self.assertTrue(
                    any(
                        "action transition must preserve route" in error
                        for error in errors
                    ),
                    errors,
                )

    def test_protected_gate_files_require_governance_revision(self) -> None:
        errors = plan_gate.validate_transition(
            manifest(),
            manifest(),
            ["scripts/plan_gate.py"],
            base_current_metadata=current_metadata(),
            target_current_metadata=current_metadata(),
            base_verification_cases=cases(),
            target_verification_cases=cases(),
            base_documents=documents(),
            target_documents=documents(),
            base_runner_files=RUNNER_FILES,
            target_runner_files=RUNNER_FILES,
        )
        self.assertTrue(any("require a governance action" in error for error in errors), errors)


class GovernanceRevisionTests(unittest.TestCase):
    def revision_states(
        self,
    ) -> tuple[dict[str, object], dict[str, object], dict[str, object], str]:
        base = manifest(current_action_id=ACTION_RESPONSIBILITY)
        target = copy.deepcopy(base)
        target_control = target["plan_execution_control"]
        assert isinstance(target_control, dict)
        target_control["plan_revision_ref"] = PDR_10
        target_control["authorization_refs"] = [AUTH_10]
        target_contracts = target_control["next_action_contracts"]
        assert isinstance(target_contracts, dict)
        contract_by_id(target_contracts, ACTION_QUALITY)["allowed_change_paths"].append(
            f"{ITERATION_RESULTS}/quality-governance-note.md"
        )
        target_action = target_control["current_action"]
        assert isinstance(target_action, dict)
        target_action["prerequisite_case_ids"] = []
        contract_by_id(target_contracts, ACTION_RESPONSIBILITY)[
            "prerequisite_case_ids"
        ] = []
        governance_action = contract_by_id(registered_contracts(), ACTION_RESPONSIBILITY)
        result, evidence = gate_bundle(governance_action)
        return base, target, result, evidence

    def validate_revision_states(
        self,
        base: dict[str, object],
        target: dict[str, object],
        result: dict[str, object],
        evidence: str,
        *,
        include_base_result: bool,
        target_documents: dict[str, dict[str, object]],
        base_document_additions: dict[str, dict[str, object]] | None = None,
        base_document_authorization_refs: set[str] | None = None,
    ) -> list[str]:
        base_documents = documents()
        base_documents.update(copy.deepcopy(base_document_additions or {}))
        direction_action = contract_by_id(
            registered_contracts(), ACTION_DIRECTION_REWORK
        )
        direction_result, direction_evidence = gate_bundle(direction_action)
        base_documents.update(receipt_documents(direction_result))
        base_artifacts: dict[str, str] = {
            str(direction_result["id"]): direction_evidence
        }
        if include_base_result:
            base_documents.update(receipt_documents(result))
            base_artifacts[str(result["id"])] = evidence
        complete_target_documents = copy.deepcopy(target_documents)
        complete_target_documents.update(copy.deepcopy(base_document_additions or {}))
        complete_target_documents.update(receipt_documents(direction_result))
        if include_base_result:
            complete_target_documents.update(receipt_documents(result))
        target_control = target["plan_execution_control"]
        assert isinstance(target_control, dict)
        target_pdr = str(target_control["plan_revision_ref"])
        target_action = target_control["current_action"]
        assert isinstance(target_action, dict)
        return plan_gate.validate_transition(
            base,
            target,
            [MANIFEST_PATH],
            base_current_metadata=current_metadata(action_id=ACTION_RESPONSIBILITY),
            target_current_metadata=current_metadata(
                action_id=str(target_action["id"]), pdr=target_pdr
            ),
            base_verification_cases=cases(),
            target_verification_cases=cases(),
            base_documents=base_documents,
            target_documents=complete_target_documents,
            base_document_authorization_refs=base_document_authorization_refs,
            base_result_evidence_artifacts=base_artifacts,
            target_result_evidence_artifacts=base_artifacts,
            base_runner_files=RUNNER_FILES,
            target_runner_files=RUNNER_FILES,
        )

    def validate_revision(self, *, include_base_result: bool) -> list[str]:
        base, target, result, evidence = self.revision_states()
        return self.validate_revision_states(
            base,
            target,
            result,
            evidence,
            include_base_result=include_base_result,
            target_documents=documents(include_revision_10=True),
        )

    def test_governance_revision_requires_preexisting_base_pass_receipt(self) -> None:
        errors = self.validate_revision(include_base_result=False)
        self.assertTrue(any("previously sealed PASS Result" in error for error in errors), errors)

    def test_governance_revision_with_preexisting_base_pass_receipt_passes(self) -> None:
        self.assertEqual(self.validate_revision(include_base_result=True), [])

    def test_governance_revision_may_replace_the_work_plan_action(self) -> None:
        base, target, result, evidence = self.revision_states()
        target_control = target["plan_execution_control"]
        assert isinstance(target_control, dict)
        target_contracts = target_control["next_action_contracts"]
        assert isinstance(target_contracts, dict)
        replacement_contract = contract_by_id(
            target_contracts, ACTION_FREEZE_REWORK
        )
        replacement = plan_gate._action_fields(replacement_contract)
        target_control["current_action"] = replacement
        target_control["transition"] = copy.deepcopy(
            replacement_contract["transition"]
        )
        target_control["locks"] = copy.deepcopy(replacement_contract["locks"])
        self.assertEqual(
            self.validate_revision_states(
                base,
                target,
                result,
                evidence,
                include_base_result=True,
                target_documents=documents(include_revision_10=True),
            ),
            [],
        )

    def test_governance_revision_rejects_pdr_sequence_rollback(self) -> None:
        base, target, result, evidence = self.revision_states()
        target_control = target["plan_execution_control"]
        assert isinstance(target_control, dict)
        target_control["plan_revision_ref"] = PDR_8
        target_documents = documents(include_revision_10=True)
        pdr = target_documents.pop(PDR_10)
        pdr["id"] = PDR_8
        target_documents[PDR_8] = pdr
        errors = self.validate_revision_states(
            base,
            target,
            result,
            evidence,
            include_base_result=True,
            target_documents=target_documents,
        )
        self.assertTrue(any("strictly greater" in error for error in errors), errors)

    def test_governance_revision_rejects_cross_iteration_pdr(self) -> None:
        base, target, result, evidence = self.revision_states()
        target_control = target["plan_execution_control"]
        assert isinstance(target_control, dict)
        target_control["plan_revision_ref"] = PDR_11_10
        target_documents = documents(include_revision_10=True)
        pdr = target_documents.pop(PDR_10)
        pdr["id"] = PDR_11_10
        target_documents[PDR_11_10] = pdr
        errors = self.validate_revision_states(
            base,
            target,
            result,
            evidence,
            include_base_result=True,
            target_documents=target_documents,
        )
        self.assertTrue(any("base iteration" in error for error in errors), errors)

    def test_governance_revision_requires_base_result_dependency(self) -> None:
        base, target, result, evidence = self.revision_states()
        target_documents = documents(include_revision_10=True)
        target_documents[PDR_10]["depends_on"] = ["FINDING-010-142"]
        errors = self.validate_revision_states(
            base,
            target,
            result,
            evidence,
            include_base_result=True,
            target_documents=target_documents,
        )
        self.assertTrue(any("sealed Result ref" in error for error in errors), errors)

    def test_governance_revision_rejects_reused_decision_ref(self) -> None:
        base, target, result, evidence = self.revision_states()
        target_control = target["plan_execution_control"]
        assert isinstance(target_control, dict)
        target_control["authorization_refs"] = [AUTH_9]
        target_documents = documents(include_revision_10=True)
        target_documents[PDR_10]["decision_ref"] = AUTH_9
        errors = self.validate_revision_states(
            base,
            target,
            result,
            evidence,
            include_base_result=True,
            target_documents=target_documents,
        )
        self.assertTrue(any("new and absent" in error for error in errors), errors)

    def test_governance_revision_rejects_authority_used_by_older_pdr(self) -> None:
        base, target, result, evidence = self.revision_states()
        historical_pdr = {
            PDR_8: {
                "id": PDR_8,
                "kind": "project-decision",
                "status": "accepted",
                "depends_on": ["FINDING-010-140"],
                "decision_ref": AUTH_10,
            },
            "FINDING-010-140": {
                "id": "FINDING-010-140",
                "kind": "implementation-finding",
            },
        }
        errors = self.validate_revision_states(
            base,
            target,
            result,
            evidence,
            include_base_result=True,
            target_documents=documents(include_revision_10=True),
            base_document_additions=historical_pdr,
        )
        self.assertTrue(
            any("trusted base documents" in error for error in errors),
            errors,
        )

    def test_governance_revision_rejects_authority_hidden_in_arbitrary_metadata(self) -> None:
        base, target, result, evidence = self.revision_states()
        historical_document = {
            "FINDING-010-140": {
                "id": "FINDING-010-140",
                "kind": "implementation-finding",
                "historical_note": f"already consumed {AUTH_10} for old work",
                "historical_values": [
                    "unrelated value",
                    {"nested": "still unrelated"},
                ],
            },
        }
        errors = self.validate_revision_states(
            base,
            target,
            result,
            evidence,
            include_base_result=True,
            target_documents=documents(include_revision_10=True),
            base_document_additions=historical_document,
        )
        self.assertTrue(
            any("trusted base documents" in error for error in errors),
            errors,
        )

    def test_governance_revision_rejects_authority_found_in_document_body(self) -> None:
        base, target, result, evidence = self.revision_states()
        errors = self.validate_revision_states(
            base,
            target,
            result,
            evidence,
            include_base_result=True,
            target_documents=documents(include_revision_10=True),
            base_document_authorization_refs={AUTH_10},
        )
        self.assertTrue(
            any("trusted base documents" in error for error in errors),
            errors,
        )

    def test_governance_revision_rejects_authority_found_only_in_base_manifest(self) -> None:
        base, target, result, evidence = self.revision_states()
        historical_record = {"note": f"already used {AUTH_10}"}
        base["historical_authority_record"] = historical_record
        target["historical_authority_record"] = copy.deepcopy(historical_record)
        errors = self.validate_revision_states(
            base,
            target,
            result,
            evidence,
            include_base_result=True,
            target_documents=documents(include_revision_10=True),
        )
        self.assertTrue(
            any("trusted base documents" in error for error in errors),
            errors,
        )

    def test_governance_revision_rejects_same_authority_digest_under_new_scheme(self) -> None:
        base, target, result, evidence = self.revision_states()
        target_ref = "local-user-message-utf8:sha256:" + "a" * 64
        target_control = target["plan_execution_control"]
        assert isinstance(target_control, dict)
        target_control["authorization_refs"] = [target_ref]
        target_documents = documents(include_revision_10=True)
        target_documents[PDR_10]["decision_ref"] = target_ref
        errors = self.validate_revision_states(
            base,
            target,
            result,
            evidence,
            include_base_result=True,
            target_documents=target_documents,
            base_document_additions={
                "FINDING-010-140": {
                    "id": "FINDING-010-140",
                    "kind": "implementation-finding",
                    "historical_ref": AUTH_10,
                }
            },
        )
        self.assertTrue(
            any("under any authority scheme" in error for error in errors),
            errors,
        )

    def test_exact_one_time_recovery_evidence_may_pre_register_pdr010_decision(self) -> None:
        base_action = {
            "id": plan_gate.ITER010_PLAN_RECOVERY_ACTION_ID,
            "kind": "governance",
            "case_id": plan_gate.ITER010_PLAN_RECOVERY_CASE_ID,
            "result_ref": plan_gate.ITER010_PLAN_RECOVERY_RESULT_ID,
            "evidence_verifier": plan_gate.ITER010_PLAN_RECOVERY_VERIFIER,
        }
        base_control = {
            "plan_revision_ref": plan_gate.ITER010_PLAN_RECOVERY_BASE_REVISION,
            "authorization_refs": [AUTH_9],
        }
        target_control = {
            "plan_revision_ref": plan_gate.ITER010_PLAN_RECOVERY_TARGET_REVISION,
            "authorization_refs": [
                plan_gate.ITER010_PLAN_CHANGE_AUTHORIZATION_REF,
                plan_gate.ITER010_PLAN_RECOVERY_AUTHORIZATION_REF,
            ],
        }
        target_documents = {
            plan_gate.ITER010_PLAN_RECOVERY_TARGET_REVISION: {
                "id": plan_gate.ITER010_PLAN_RECOVERY_TARGET_REVISION,
                "depends_on": [plan_gate.ITER010_PLAN_RECOVERY_RESULT_ID],
                "decision_ref": plan_gate.ITER010_PLAN_CHANGE_AUTHORIZATION_REF,
            }
        }
        action_evidence = {
            "schema": "ITER010_USER_PLAN_RECOVERY_EVIDENCE@1",
            "target_plan_revision_ref": (
                plan_gate.ITER010_PLAN_RECOVERY_TARGET_REVISION
            ),
            "authorization_refs": [
                plan_gate.ITER010_PLAN_CHANGE_AUTHORIZATION_REF,
                plan_gate.ITER010_PLAN_RECOVERY_AUTHORIZATION_REF,
            ],
            "change_boundary": {
                "plan_governance_change_authorized": True,
                "product_code_change_authorized": False,
                "external_execution_authorized": False,
            },
        }
        artifact = {
            "result_id": plan_gate.ITER010_PLAN_RECOVERY_RESULT_ID,
            "plan_revision_ref": plan_gate.ITER010_PLAN_RECOVERY_BASE_REVISION,
            "action_ref": plan_gate.ITER010_PLAN_RECOVERY_ACTION_ID,
            "verification_case_id": plan_gate.ITER010_PLAN_RECOVERY_CASE_ID,
            "plan_gate_verdict": "PASS",
            "evidence_verifier": plan_gate.ITER010_PLAN_RECOVERY_VERIFIER,
            "action_evidence": action_evidence,
        }

        errors = plan_gate._validate_plan_revision_lineage(
            {},
            base_control,
            target_control,
            base_action,
            {},
            target_documents,
            {plan_gate.ITER010_PLAN_CHANGE_AUTHORIZATION_REF},
            {
                plan_gate.ITER010_PLAN_RECOVERY_RESULT_ID: json.dumps(artifact)
            },
        )
        self.assertEqual(errors, [])

        widened = copy.deepcopy(artifact)
        widened["action_evidence"]["change_boundary"][  # type: ignore[index]
            "external_execution_authorized"
        ] = True
        errors = plan_gate._validate_plan_revision_lineage(
            {},
            base_control,
            target_control,
            base_action,
            {},
            target_documents,
            {plan_gate.ITER010_PLAN_CHANGE_AUTHORIZATION_REF},
            {
                plan_gate.ITER010_PLAN_RECOVERY_RESULT_ID: json.dumps(widened)
            },
        )
        self.assertTrue(
            any("trusted base documents" in error for error in errors), errors
        )

    def test_non_governance_action_cannot_revise_plan(self) -> None:
        target = manifest(pdr=PDR_10)
        target_control = target["plan_execution_control"]
        assert isinstance(target_control, dict)
        target_contracts = target_control["next_action_contracts"]
        assert isinstance(target_contracts, dict)
        contract_by_id(target_contracts, ACTION_QUALITY)["allowed_change_paths"].append(
            f"{ITERATION_RESULTS}/quality-governance-note.md"
        )
        errors = plan_gate.validate_transition(
            manifest(),
            target,
            [MANIFEST_PATH],
            base_current_metadata=current_metadata(),
            target_current_metadata=current_metadata(pdr=PDR_10),
            base_verification_cases=cases(),
            target_verification_cases=cases(),
            base_documents=documents(),
            target_documents=documents(include_revision_10=True),
            base_runner_files=RUNNER_FILES,
            target_runner_files=RUNNER_FILES,
        )
        self.assertTrue(any("base current action to be governance" in error for error in errors), errors)


class CliAndBootstrapTests(unittest.TestCase):
    def test_trusted_parent_gate_precedes_all_candidate_python_and_tests(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        trusted = workflow.index("Validate every commit with its trusted parent gate")
        for candidate_step in (
            "Run isolated plan-gate tests",
            "Run documentation-gate tests",
            "Run active deterministic value-gate tests when present",
            "Validate pre-registered documentation contracts",
            "Validate current plan snapshot",
        ):
            self.assertLess(trusted, workflow.index(candidate_step), candidate_step)
        self.assertIn("PR_HEAD_SHA", workflow)
        self.assertIn("git rev-list --reverse --topo-order", workflow)
        self.assertIn("does not have exactly one parent", workflow)
        self.assertIn("is not the previous trusted node", workflow)
        self.assertNotIn("--first-parent", workflow)
        self.assertNotIn("cp scripts/plan_gate.py", workflow)

    def test_local_hook_validates_the_index_with_the_trusted_head_gate(self) -> None:
        hook = LOCAL_HOOK.read_text(encoding="utf-8")
        self.assertIn("git write-tree", hook)
        self.assertIn('git show "$TRUSTED_HEAD:scripts/plan_gate.py"', hook)
        self.assertIn('--base "$TRUSTED_HEAD" --target "$INDEX_TREE"', hook)
        self.assertIn("GIT_NO_REPLACE_OBJECTS=1", hook)
        self.assertIn("MERGE_HEAD", hook)
        self.assertNotIn("python3 scripts/plan_gate.py", hook)

    def test_diff_defaults_to_worktree_candidate(self) -> None:
        args = plan_gate._argument_parser().parse_args(["diff", "--base", "HEAD"])
        self.assertEqual(args.target, "WORKTREE")

    def test_bootstrap_transition_is_fail_closed_for_product_source(self) -> None:
        base = {"schema_version": 1, "development": manifest()["development"]}
        errors = plan_gate.validate_transition(
            base,
            manifest(),
            [MANIFEST_PATH, "src/software_world_model/feature.py"],
            target_current_metadata=current_metadata(),
            target_verification_cases=cases(),
            target_documents=documents(),
        )
        self.assertTrue(any("src/software_world_model" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
