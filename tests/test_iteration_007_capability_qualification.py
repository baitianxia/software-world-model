from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

from software_world_model.ai_infrastructure import (
    JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_METRIC_CONTRACT,
    JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT,
    java_source_semantics_world_model_capability_registry,
    java_source_semantics_world_model_output_contract_digest,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
)
from software_world_model.cross_cutting import Digest, digest_of
from software_world_model.ai_infrastructure.java_source_semantics_model_egress_qualification import (
    JAVA_SOURCE_SEMANTICS_CAPABILITY_CLOSED_RESULT_SCHEMA,
    load_java_source_semantics_gateway_qualification_binding,
)
from validation.structure_world_model_iteration_007.capability import evaluator
from validation.structure_world_model_iteration_007.capability import cli as capability_cli
from validation.structure_world_model_iteration_007.capability import freeze
from validation.structure_world_model_iteration_007.capability.authorize import (
    create_authorization,
)
from validation.structure_world_model_iteration_007.capability.manifest import (
    PINNED_ORACLE_FILE_DIGEST,
    PINNED_ORACLE_REF,
    PINNED_SUITE_FILE_DIGEST,
    PINNED_SUITE_REF,
    build_evaluation_definition,
    case_pairs,
    load_capability_inputs,
    sealed_case_input,
)


_PLAN_TERMS = {
    "WM-JSS-CE-PLAN-ZH-001": ["credentials", "failure", "session"],
    "WM-JSS-CE-PLAN-EN-002": ["token", "invalid", "account"],
    "WM-JSS-CE-PLAN-ORDER-003": ["order", "audit", "return"],
    "WM-JSS-CE-PLAN-BOUNDARY-004": ["performance"],
}
_DRAFT_ANSWERS = {
    "WM-JSS-CE-DRAFT-SUPPORTED-005": (
        "凭据无效时会记录失败并抛出异常；成功路径会创建会话并返回调用结果。"
    ),
    "WM-JSS-CE-DRAFT-GAP-006": "没有实现候选，当前存在知识缺口。",
    "WM-JSS-CE-DRAFT-LIMITATION-007": "存在多个候选且不唯一，当前无法选择具体实现。",
    "WM-JSS-CE-DRAFT-DIRECTION-008": "先校验，再保存，最后返回结果。",
}


def _document(core: dict[str, object]) -> dict[str, object]:
    return {**core, "document_digest": evaluator._document_digest(core)}


def _audit() -> dict[str, object]:
    return {
        "model_call_count": 1,
        "hidden_retry_count": 0,
        "product_oracle_read_count": 0,
        "product_suite_read_count": 0,
        "repository_read_count": 0,
        "source_access_count": 0,
        "evidence_payload_access_count": 0,
        "project_dictionary_access_count": 0,
        "project_name_branch_count": 0,
        "self_review_count": 0,
        "observed_events": [],
        "model_input_item_ids": [
            "instruction",
            "sealed-case-input",
            "qualification",
        ],
    }


def _passing_result(case, oracle_case) -> dict[str, object]:
    normalized = copy.deepcopy(oracle_case["expected_normalized_result"])
    capability = case["capability"]
    if capability == "IMPLEMENTATION_QUERY_PLANNING":
        normalized["search_terms"] = _PLAN_TERMS[case["case_id"]]
    elif capability == "IMPLEMENTATION_ANSWER_DRAFTING":
        normalized["answer"] = _DRAFT_ANSWERS[case["case_id"]]
    elif "finding_codes" not in normalized:
        normalized["finding_codes"] = list(
            case["semantic_constraints"]["required_finding_codes"]
        )
    return normalized


def _inputs(case, oracle_case, normalized=None):
    sealed = sealed_case_input(case)
    input_digest = digest_of(sealed).value
    value = copy.deepcopy(
        _passing_result(case, oracle_case)
        if normalized is None
        else normalized
    )
    packet_core = {
        "schema": evaluator.PACKET_SCHEMA,
        "suite_ref": PINNED_SUITE_REF,
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "oracle_ref": PINNED_ORACLE_REF,
        "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
        "case": {
            "case_id": case["case_id"],
            "capability": case["capability"],
            "sealed_input": sealed,
            "case_input_digest": input_digest,
            "projection_fields": case["projection_fields"],
            "semantic_constraints": case["semantic_constraints"],
            "expected_normalized_result": oracle_case[
                "expected_normalized_result"
            ],
            "forbidden_events": oracle_case["forbidden_events"],
        },
    }
    result_core = {
        "schema": evaluator.RESULT_SCHEMA,
        "suite_ref": PINNED_SUITE_REF,
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "case_id": case["case_id"],
        "capability": case["capability"],
        "case_input_digest": input_digest,
        "normalized_result": value,
        "normalized_result_digest": evaluator._digest(value),
        "operation_audit": _audit(),
    }
    return _document(packet_core), _document(result_core)


class Iteration007CapabilityQualificationTests(unittest.TestCase):
    def test_gateway_binding_requires_exact_twelve_case_pass(self):
        proof_core = {
            "proof_ref": (
                "capability-evaluation:evaluation_result_"
                "11111111111111111111111111111111"
            ),
            "capability_id": "world-model-authority-proposal",
            "capability_contract_version": "1.2.2",
            "strategy_id": "model-snapshot-first-world-model-answer",
            "strategy_version": "1.2.2",
            "result_ref": "evaluation_result_11111111111111111111111111111111",
            "validity_ref": (
                "evaluation_validity_22222222222222222222222222222222@1"
            ),
            "qualification_kind": "CAPABILITY_EVALUATION",
        }
        proof = {**proof_core, "digest": digest_of(proof_core).value}
        qualification_core = {
            "schema": "swm.capability-qualification-proof@1",
            "proof": proof,
        }
        qualification = {
            **qualification_core,
            "document_digest": digest_of(qualification_core).value,
        }
        contract = JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
        definition = {
            "capability_id": "world-model-authority-proposal",
            "capability_contract_version": "1.2.2",
            "strategy_id": "model-snapshot-first-world-model-answer",
            "strategy_version": "1.2.2",
            "implementation_digest": (
                world_model_answer_strategy_implementation_digest(contract).value
            ),
            "prompt_program_digest": (
                world_model_answer_prompt_program_digest(contract).value
            ),
            "output_schema_digest": (
                java_source_semantics_world_model_output_contract_digest(
                    contract
                ).value
            ),
            "metric_contract_digest": digest_of(
                JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_METRIC_CONTRACT
            ).value,
            "threshold_ref": (
                "all-twelve-java-source-semantics-required-cases-exact-pass@1"
            ),
            "cases": [{"case_id": str(item)} for item in range(12)],
        }
        closed_core = {
            "schema": JAVA_SOURCE_SEMANTICS_CAPABILITY_CLOSED_RESULT_SCHEMA,
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
            "definition": definition,
            "result": {
                "result_id": proof_core["result_ref"],
                "conclusion": "PASS",
                "passed_case_ids": [str(item) for item in range(12)],
                "failed_case_ids": [],
                "inconclusive_case_ids": [],
            },
            "validity": {
                "status": "VALID",
                "valid_until": (
                    datetime.now(timezone.utc) + timedelta(days=1)
                ).isoformat(),
            },
            "qualification": proof,
            "closed_result_status": "PASS_VALID",
            "failure_count": 0,
            "unknown_count": 0,
            "required_case_count": 12,
            "provider_request_count": 12,
            "production_activation": "NOT_EXECUTED",
        }
        closed = {
            **closed_core,
            "document_digest": digest_of(closed_core).value,
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            qualification_path = root / "qualification.json"
            closed_path = root / "closed.json"
            qualification_path.write_text(
                json.dumps(qualification),
                encoding="utf-8",
            )
            closed_path.write_text(json.dumps(closed), encoding="utf-8")

            binding = load_java_source_semantics_gateway_qualification_binding(
                qualification_path=qualification_path,
                closed_result_path=closed_path,
            )

        self.assertEqual(binding.capability_qualification_ref, proof["proof_ref"])
        self.assertEqual(
            binding.capability_qualification_digest.value,
            proof["digest"],
        )

    def test_zero_provider_freeze_requires_a_post_freeze_single_use_grant(self):
        identity = {
            "baseline_commit": "a" * 40,
            "baseline_tree": "b" * 40,
            "worktree_state": "UNCOMMITTED_CANDIDATE",
            "identity_scope": (
                "EXACT_UNCOMMITTED_PRODUCT_VALIDATION_AND_TEST_CLOSURE@1"
            ),
            "changed_path_count": 1,
            "worktree_manifest_digest": "sha256:" + "c" * 64,
            "paths": [
                {
                    "path": "src/example.py",
                    "state": "PRESENT",
                    "size": 1,
                    "sha256": "d" * 64,
                }
            ],
        }
        conformance = SimpleNamespace(
            result_ref="CC-ARK-CHAT-NO-TOOLS-001:sha256:" + "e" * 64,
            result_digest=Digest("sha256:" + "e" * 64),
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            conformance_path = root / "conformance.json"
            conformance_path.write_text("{}", encoding="utf-8")
            with (
                mock.patch.object(
                    freeze,
                    "_candidate_identity",
                    return_value=identity,
                ),
                mock.patch.object(
                    freeze,
                    "load_ark_chat_conformance_qualification",
                    return_value=conformance,
                ),
            ):
                freeze_path, request_path, frozen = freeze.create_freeze(
                    output_directory=root / "freeze",
                    conformance_result_path=conformance_path,
                    created_at=datetime(2026, 8, 13, tzinfo=timezone.utc),
                )

            self.assertFalse(frozen["external_model_called"])
            self.assertEqual(
                frozen["dispatch_contract"]["planned_provider_call_count"],
                12,
            )
            self.assertTrue(freeze_path.is_file())
            self.assertTrue(request_path.is_file())
            message_digest = "sha256:" + "f" * 64
            authorization = create_authorization(
                freeze_path=freeze_path,
                output_path=root / "authorization.json",
                result_directory=root / "result-run-001",
                authorized_at="2026-08-13T08:00:01Z",
                authorization_ref=f"codex-user-message:{message_digest}",
                authorization_message_digest=message_digest,
            )

            self.assertEqual(authorization["status"], "AUTHORIZED")
            self.assertEqual(authorization["planned_provider_call_count"], 12)
            self.assertFalse(authorization["iter_006_grant_reused"])

    def test_dispatch_rejects_missing_authorization_without_transport(self):
        transport = mock.Mock()
        with mock.patch.object(
            capability_cli,
            "_verify_freeze",
            return_value={
                "schema": freeze.FREEZE_SCHEMA,
                "document_digest": "sha256:" + "1" * 64,
            },
        ):
            code = capability_cli.main(
                [
                    "run",
                    "--freeze",
                    "/not/read/in-this-test",
                    "--authorization",
                    "/missing/authorization.json",
                    "--conformance-result",
                    "/not/read/in-this-test",
                ],
                environment={},
                transport=transport,
            )

        self.assertEqual(code, 2)
        transport.assert_not_called()

    def test_pinned_suite_has_four_cases_per_role_and_hides_oracle(self):
        suite, oracle = load_capability_inputs()

        self.assertEqual(len(suite["cases"]), 12)
        self.assertEqual(len(oracle["cases"]), 12)
        self.assertNotIn("expected_normalized_result", repr(suite["cases"]))
        roles = [case["capability"] for case in suite["cases"]]
        self.assertEqual(
            {role: roles.count(role) for role in set(roles)},
            {
                "IMPLEMENTATION_QUERY_PLANNING": 4,
                "IMPLEMENTATION_ANSWER_DRAFTING": 4,
                "IMPLEMENTATION_ANSWER_REVIEW": 4,
            },
        )
        self.assertEqual(
            suite["cases"][0]["available_operations"],
            list(
                JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations
            ),
        )

    def test_definition_binds_exact_source_semantics_contract(self):
        suite, oracle = load_capability_inputs()
        definition = build_evaluation_definition(
            suite,
            oracle,
            conformance_result_ref="CC-ARK-CHAT-NO-TOOLS-001:sha256:" + "1" * 64,
            provider_configuration_fingerprint=Digest("sha256:" + "2" * 64),
            actual_model_fingerprint="glm-5.2",
            adapter_version="openai-chat-completions-no-tools@8",
            exact_candidate_checkpoint_ref="working-tree:sha256:" + "3" * 64,
            environment_ref="iter-007-source-semantics-evaluation@1",
            reference_strategy_ref="standalone-stdlib-evaluator@1",
            resource_policy_ref="one-call-no-retry@1",
            valid_for_seconds=604800,
        )

        self.assertEqual(definition.strategy_version, "1.2.2")
        self.assertEqual(definition.capability_contract_version, "1.2.2")
        self.assertEqual(len(definition.cases), 12)
        self.assertEqual(
            definition.implementation_digest,
            world_model_answer_strategy_implementation_digest(
                JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )
        self.assertEqual(
            definition.prompt_program_digest,
            world_model_answer_prompt_program_digest(
                JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )
        self.assertEqual(
            definition.output_schema_digest,
            java_source_semantics_world_model_output_contract_digest(
                JAVA_SOURCE_SEMANTICS_FIXED_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )
        self.assertEqual(
            definition.metric_contract_digest,
            digest_of(
                JAVA_SOURCE_SEMANTICS_WORLD_MODEL_EVALUATION_METRIC_CONTRACT
            ),
        )
        registry = java_source_semantics_world_model_capability_registry()
        strategy = registry.resolve_strategy(
            definition.strategy_id,
            definition.strategy_version,
        )
        self.assertEqual(
            strategy.implementation_digest,
            definition.implementation_digest,
        )

    def test_independent_evaluator_passes_all_twelve_contract_cases(self):
        suite, oracle = load_capability_inputs()

        conclusions = []
        for case, oracle_case in case_pairs(suite, oracle):
            packet, result = _inputs(case, oracle_case)
            review = evaluator.evaluate(packet, result)
            conclusions.append(review["conclusion"])
            self.assertEqual(review["evaluated_strategy_import_count"], 0)
            self.assertEqual(review["product_import_count"], 0)

        self.assertEqual(conclusions, ["PASS"] * 12)

    def test_planning_omitted_feature_concept_fails(self):
        suite, oracle = load_capability_inputs()
        case, oracle_case = case_pairs(suite, oracle)[0]
        normalized = _passing_result(case, oracle_case)
        normalized["search_terms"] = ["credentials"]
        packet, result = _inputs(case, oracle_case, normalized)

        review = evaluator.evaluate(packet, result)

        self.assertEqual(review["conclusion"], "FAIL")
        self.assertIn("FEATURE_CONCEPT_OMITTED", review["derived_events"])

    def test_draft_reversed_source_order_fails(self):
        suite, oracle = load_capability_inputs()
        case, oracle_case = case_pairs(suite, oracle)[7]
        normalized = _passing_result(case, oracle_case)
        normalized["answer"] = "先返回，再保存，最后校验。"
        packet, result = _inputs(case, oracle_case, normalized)

        review = evaluator.evaluate(packet, result)

        self.assertEqual(review["conclusion"], "FAIL")
        self.assertIn("SOURCE_ORDER_CHANGED", review["forbidden_events_observed"])

    def test_draft_order_uses_a_monotonic_alias_sequence(self):
        suite, oracle = load_capability_inputs()
        case, oracle_case = case_pairs(suite, oracle)[7]
        normalized = _passing_result(case, oracle_case)
        normalized["answer"] = (
            "保存前先调用 validate 校验，随后调用 persist 持久化，最后返回结果。"
        )
        packet, result = _inputs(case, oracle_case, normalized)

        review = evaluator.evaluate(packet, result)

        self.assertEqual(review["conclusion"], "PASS")
        self.assertNotIn("SOURCE_ORDER_CHANGED", review["derived_events"])

    def test_review_cannot_approve_a_fault_marker(self):
        suite, oracle = load_capability_inputs()
        case, oracle_case = case_pairs(suite, oracle)[9]
        normalized = _passing_result(case, oracle_case)
        normalized["decision"] = "APPROVE"
        normalized["finding_codes"] = []
        packet, result = _inputs(case, oracle_case, normalized)

        review = evaluator.evaluate(packet, result)

        self.assertEqual(review["conclusion"], "FAIL")
        self.assertIn("APPROVED_FAULTY_DRAFT", review["forbidden_events_observed"])
        self.assertIn("FAULT_OMITTED", review["forbidden_events_observed"])

    def test_evaluator_is_standalone_stdlib_source(self):
        source = Path(evaluator.__file__).read_text(encoding="utf-8")

        self.assertNotIn("software_world_model", source)
        self.assertNotIn("world_model_product", source)


if __name__ == "__main__":
    unittest.main()
