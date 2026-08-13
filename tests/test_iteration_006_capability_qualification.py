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
    JAVA_WORLD_MODEL_EVALUATION_METRIC_CONTRACT,
    JAVA_WORLD_MODEL_PROPOSAL_CONTRACT,
    java_world_model_capability_registry,
    world_model_answer_prompt_program_digest,
    world_model_answer_strategy_implementation_digest,
    world_model_answer_output_contract_digest,
)
from software_world_model.ai_infrastructure.java_model_egress_qualification import (
    JAVA_CAPABILITY_CLOSED_RESULT_SCHEMA,
    load_java_gateway_qualification_binding,
)
from software_world_model.cross_cutting import Digest, digest_of
from validation.structure_world_model_iteration_006.capability import evaluator
from validation.structure_world_model_iteration_006.capability import freeze
from validation.structure_world_model_iteration_006.capability import cli as capability_cli
from validation.structure_world_model_iteration_006.capability.authorize import (
    create_authorization,
)
from validation.structure_world_model_iteration_006.capability.manifest import (
    PINNED_ORACLE_FILE_DIGEST,
    PINNED_ORACLE_REF,
    PINNED_SUITE_FILE_DIGEST,
    PINNED_SUITE_REF,
    build_evaluation_definition,
    case_pairs,
    load_capability_inputs,
    sealed_case_input,
)


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
        "project_name_branch_count": 0,
        "self_review_count": 0,
        "observed_events": [],
        "model_input_item_ids": [
            "instruction",
            "sealed-case-input",
            "qualification",
        ],
    }


def _inputs(case, oracle_case, normalized=None):
    sealed = sealed_case_input(case)
    case_input_digest = digest_of(sealed).value
    expected = oracle_case["expected_normalized_result"]
    normalized = copy.deepcopy(expected if normalized is None else normalized)
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
            "case_input_digest": case_input_digest,
            "projection_fields": case["projection_fields"],
            "expected_normalized_result": expected,
            "forbidden_events": oracle_case["forbidden_events"],
        },
    }
    result_core = {
        "schema": evaluator.RESULT_SCHEMA,
        "suite_ref": PINNED_SUITE_REF,
        "suite_digest": PINNED_SUITE_FILE_DIGEST,
        "case_id": case["case_id"],
        "capability": case["capability"],
        "case_input_digest": case_input_digest,
        "normalized_result": normalized,
        "normalized_result_digest": evaluator._digest(normalized),
        "operation_audit": _audit(),
    }
    return _document(packet_core), _document(result_core)


class Iteration006CapabilityQualificationTests(unittest.TestCase):
    def test_gateway_binding_requires_exact_pass_valid_java_result(self):
        proof_core = {
            "proof_ref": (
                "capability-evaluation:evaluation_result_"
                "11111111111111111111111111111111"
            ),
            "capability_id": "world-model-authority-proposal",
            "capability_contract_version": "1.1.0",
            "strategy_id": "model-snapshot-first-world-model-answer",
            "strategy_version": "1.1.0",
            "result_ref": "evaluation_result_11111111111111111111111111111111",
            "validity_ref": "evaluation_validity_22222222222222222222222222222222@1",
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
        definition = {
            "capability_id": "world-model-authority-proposal",
            "capability_contract_version": "1.1.0",
            "strategy_id": "model-snapshot-first-world-model-answer",
            "strategy_version": "1.1.0",
            "implementation_digest": (
                world_model_answer_strategy_implementation_digest(
                    JAVA_WORLD_MODEL_PROPOSAL_CONTRACT
                ).value
            ),
            "prompt_program_digest": world_model_answer_prompt_program_digest(
                JAVA_WORLD_MODEL_PROPOSAL_CONTRACT
            ).value,
            "output_schema_digest": world_model_answer_output_contract_digest().value,
            "metric_contract_digest": digest_of(
                JAVA_WORLD_MODEL_EVALUATION_METRIC_CONTRACT
            ).value,
            "threshold_ref": "all-eight-java-required-cases-exact-pass@1",
            "cases": [{"case_id": item} for item in range(8)],
        }
        closed_core = {
            "schema": JAVA_CAPABILITY_CLOSED_RESULT_SCHEMA,
            "suite_digest": PINNED_SUITE_FILE_DIGEST,
            "oracle_digest": PINNED_ORACLE_FILE_DIGEST,
            "definition": definition,
            "result": {
                "result_id": proof_core["result_ref"],
                "conclusion": "PASS",
                "passed_case_ids": [str(item) for item in range(8)],
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
            "required_case_count": 8,
            "provider_request_count": 8,
            "production_activation": "NOT_EXECUTED",
        }
        closed = {**closed_core, "document_digest": digest_of(closed_core).value}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            qualification_path = root / "qualification.json"
            closed_path = root / "closed.json"
            qualification_path.write_text(
                json.dumps(qualification), encoding="utf-8"
            )
            closed_path.write_text(
                json.dumps(closed), encoding="utf-8"
            )

            binding = load_java_gateway_qualification_binding(
                qualification_path=qualification_path,
                closed_result_path=closed_path,
            )

            self.assertEqual(binding.capability_qualification_ref, proof["proof_ref"])
            self.assertEqual(
                binding.capability_qualification_digest.value, proof["digest"]
            )

    def test_zero_provider_freeze_and_single_result_path_authorization(self):
        identity = {
            "baseline_commit": "a" * 40,
            "baseline_tree": "b" * 40,
            "worktree_state": "UNCOMMITTED_CANDIDATE",
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
                mock.patch.object(freeze, "_candidate_identity", return_value=identity),
                mock.patch.object(
                    freeze,
                    "load_ark_chat_conformance_qualification",
                    return_value=conformance,
                ),
            ):
                freeze_path, request_path, frozen = freeze.create_freeze(
                    output_directory=root / "freeze",
                    conformance_result_path=conformance_path,
                    created_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
                )

            self.assertFalse(frozen["external_model_called"])
            self.assertEqual(
                frozen["dispatch_contract"]["status"],
                "HELD_AWAITING_EXACT_USER_AUTHORIZATION",
            )
            self.assertTrue(freeze_path.is_file())
            self.assertTrue(request_path.is_file())
            message_digest = "sha256:" + "f" * 64
            authorization = create_authorization(
                freeze_path=freeze_path,
                output_path=root / "authorization.json",
                result_directory=root / "result-run-001",
                authorized_at="2026-08-12T12:00:00+08:00",
                authorization_ref=f"codex-user-message:{message_digest}",
                authorization_message_digest=message_digest,
            )

            self.assertEqual(authorization["status"], "AUTHORIZED")
            self.assertEqual(authorization["planned_provider_call_count"], 8)
            self.assertFalse(authorization["run_003_grant_reused"])

    def test_dispatch_cli_rejects_missing_authorization_without_transport(self):
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

    def test_pinned_suite_covers_all_roles_and_keeps_oracle_separate(self):
        suite, oracle = load_capability_inputs()

        self.assertEqual(len(suite["cases"]), 8)
        self.assertEqual(len(oracle["cases"]), 8)
        self.assertNotIn("expected_normalized_result", repr(suite["cases"]))
        method_case = suite["cases"][1]
        self.assertEqual(
            method_case["available_operations"],
            list(JAVA_WORLD_MODEL_PROPOSAL_CONTRACT.available_operations),
        )
        self.assertEqual(
            oracle["cases"][1]["expected_normalized_result"]["operations"][0][
                "operation"
            ],
            "declared_method_inventory",
        )

    def test_java_definition_binds_new_contract_without_mutating_legacy(self):
        suite, oracle = load_capability_inputs()
        definition = build_evaluation_definition(
            suite,
            oracle,
            conformance_result_ref="CC-ARK-CHAT-NO-TOOLS-001:sha256:" + "1" * 64,
            provider_configuration_fingerprint=Digest("sha256:" + "2" * 64),
            actual_model_fingerprint="glm-5.2",
            adapter_version="openai-chat-completions-no-tools@8",
            exact_candidate_checkpoint_ref="working-tree:sha256:" + "3" * 64,
            environment_ref="iter-006-java-capability-evaluation@1",
            reference_strategy_ref="standalone-stdlib-evaluator@1",
            resource_policy_ref="one-call-no-retry@1",
            valid_for_seconds=604800,
        )

        self.assertEqual(definition.strategy_version, "1.1.0")
        self.assertEqual(definition.capability_contract_version, "1.1.0")
        self.assertEqual(len(definition.cases), 8)
        self.assertEqual(
            definition.implementation_digest,
            world_model_answer_strategy_implementation_digest(
                JAVA_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )
        self.assertEqual(
            definition.prompt_program_digest,
            world_model_answer_prompt_program_digest(
                JAVA_WORLD_MODEL_PROPOSAL_CONTRACT
            ),
        )
        self.assertEqual(
            definition.metric_contract_digest,
            digest_of(JAVA_WORLD_MODEL_EVALUATION_METRIC_CONTRACT),
        )
        registry = java_world_model_capability_registry()
        strategy = registry.resolve_strategy(
            definition.strategy_id, definition.strategy_version
        )
        self.assertEqual(strategy.implementation_digest, definition.implementation_digest)

    def test_independent_evaluator_passes_all_eight_exact_cases(self):
        suite, oracle = load_capability_inputs()

        conclusions = []
        for case, oracle_case in case_pairs(suite, oracle):
            packet, result = _inputs(case, oracle_case)
            review = evaluator.evaluate(packet, result)
            conclusions.append(review["conclusion"])
            self.assertEqual(review["evaluated_strategy_import_count"], 0)
            self.assertEqual(review["product_import_count"], 0)

        self.assertEqual(conclusions, ["PASS"] * 8)

    def test_method_inventory_substitution_fails_even_with_empty_audit_events(self):
        suite, oracle = load_capability_inputs()
        case, oracle_case = case_pairs(suite, oracle)[1]
        substituted = {
            "operations": [
                {"operation": "inventory", "snapshot": "snapshot_java_left"},
                {"operation": "inventory", "snapshot": "snapshot_java_right"},
            ]
        }
        packet, result = _inputs(case, oracle_case, substituted)

        review = evaluator.evaluate(packet, result)

        self.assertEqual(review["conclusion"], "FAIL")
        self.assertIn(
            "INVENTORY_OPERATION_SUBSTITUTED",
            review["forbidden_events_observed"],
        )


if __name__ == "__main__":
    unittest.main()
