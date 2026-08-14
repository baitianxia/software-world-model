from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.docs import safe_load_manifest
from validation.structure_world_model_iteration_007 import hidden_freeze
from validation.structure_world_model_iteration_007 import hidden_freeze_lifecycle


_PUBLIC_TEST_SECRET = b"public-test-vector-secret-only!!"
_REPOSITORY = Path(__file__).resolve().parents[1]
_MANIFEST = _REPOSITORY / "docs/project/iterations/iteration-007/manifest.yaml"


def _frozen_receipt(
    *,
    baseline_supported: int = 3,
    generation: int = 1,
    secret: bytes = _PUBLIC_TEST_SECRET,
) -> dict[str, object]:
    generations = {
        label: generation for label in hidden_freeze.COMMITMENT_DOMAINS
    }
    commitments = {
        label: hidden_freeze.commit_hidden_payload(
            secret,
            label,
            {"public_test_vector": label},
            generation=generations[label],
        )
        for label in hidden_freeze.COMMITMENT_DOMAINS
    }
    public_digests = {
        label: hidden_freeze.public_commitment_digest(
            label, commitment, generation=generations[label]
        )
        for label, commitment in commitments.items()
    }
    core: dict[str, object] = {
        "schema": hidden_freeze.RECEIPT_SCHEMA,
        "status": "FROZEN",
        "protocol_digest": hidden_freeze.protocol_digest(),
        "holder": {
            "role": "INDEPENDENT_EVALUATOR",
            "implementation_actor": "ROOT_IMPLEMENTATION_AGENT",
            "holder_identity_digest": "sha256:" + "9" * 64,
            "storage_isolation": "EXTERNAL_EVALUATOR_OWNED_ACL",
            "assurance_ceiling": "EXTERNAL_ACL_ATTESTED",
            "isolation_evidence_status": "EXTERNAL_ATTESTATION_PRESENT",
            "isolation_evidence_digest": "sha256:" + "a" * 64,
            "repository_validator_assurance": "SCHEMA_AND_BINDING_ONLY",
            "cross_turn_recovery": True,
            "implementation_principal_access": "DENIED",
            "shared_surfaces_hidden_payload_touched": {
                "agent_messages": False,
                "process_argv": False,
                "stdout_or_stderr": False,
                "tmp_filesystem": False,
                "var_filesystem": False,
                "workspace_filesystem": False,
            },
        },
        "generations": generations,
        "commitment_scheme": {
            "algorithm": "HMAC-SHA-256",
            "secret_entropy_bits_minimum": 256,
            "secret_generation": "CSPRNG_UNIQUE_PER_FREEZE",
            "domain_separated": True,
            "secret_storage": "EVALUATOR_OWNED_EXTERNAL_ONLY",
            "secret_disclosed": False,
        },
        "commitments": commitments,
        "public_digests": public_digests,
        "counts": {
            "canary_001_project_count": 1,
            "canary_001_answerable_count": 1,
            "canary_001_without_symbol_count": 1,
            "canary_001_cross_domain_count": 1,
            "canary_002_project_count": 1,
            "canary_002_answerable_count": 1,
            "canary_002_without_symbol_count": 1,
            "held_out_project_count": 2,
            "held_out_question_count": 16,
            "held_out_answerable_count": 12,
            "held_out_boundary_count": 4,
            "held_out_without_symbol_count": 6,
            "held_out_without_symbol_per_project_minimum": 2,
        },
        "baseline": {
            "accepted_commit": hidden_freeze.ACCEPTED_BASELINE_COMMIT,
            "accepted_tree": hidden_freeze.ACCEPTED_BASELINE_TREE,
            "execution_status": "EXECUTED_ON_ACCEPTED_BASELINE",
            "execution_evidence": "EVALUATOR_ATTESTED_COMMITTED_RESULT",
            "supported_answerable_count": baseline_supported,
            "target_supported_count": hidden_freeze.target_supported_count(
                baseline_supported
            ),
            "target_formula": "min(12,max(baseline_supported+4,8))",
            "mature_source_agent_protocol_status": "FROZEN",
        },
        "assertions": {
            "canary_001_real_java_project": True,
            "canary_001_answerable_without_symbol": True,
            "canary_001_combines_legacy_calls_and_new_semantics": True,
            "canary_002_real_java_project": True,
            "canary_002_common_java_boundary": True,
            "canary_002_answerable_without_symbol": True,
            "held_out_real_java_maven_projects": True,
            "held_out_projects_not_used_for_implementation": True,
            "held_out_each_project_has_two_without_symbol": True,
            "held_out_four_question_classes_covered": True,
            "boundary_questions_source_insufficient_by_oracle": True,
            "canaries_and_held_out_mutually_distinct": True,
            "canaries_not_reused_as_held_out": True,
            "question_or_suite_driven_update_allowed": False,
            "burn_rule_frozen": True,
        },
        "disclosure": {
            "implementation_visibility": "HIDDEN_UNTIL_APPLICABLE_CODE_FREEZE",
            "canary_001": "NOT_DISCLOSED",
            "canary_002": "NOT_DISCLOSED",
            "held_out": "NOT_DISCLOSED",
            "hidden_content_in_receipt": False,
        },
        "production_activation": "NOT_EXECUTED",
    }
    return hidden_freeze._seal_receipt(core)


def _reseal(receipt: dict[str, object]) -> dict[str, object]:
    return hidden_freeze._seal_receipt(
        {key: value for key, value in receipt.items() if key != "document_digest"}
    )


class Iteration007HiddenFreezeTests(unittest.TestCase):
    def test_blocked_receipt_is_safe_and_does_not_pass_v_pre_004(self) -> None:
        receipt = hidden_freeze.build_blocked_receipt()

        result = hidden_freeze.evaluate_public_receipt(receipt)

        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["v_pre_004"], "NOT_PASS")
        self.assertFalse(result["hidden_payload_materialized"])
        self.assertNotIn("commitments", receipt)

        manifest = safe_load_manifest(_MANIFEST.read_text(encoding="utf-8"))
        readiness_inputs = manifest["readiness_inputs"]
        external_inputs = manifest["external_inputs"]
        self.assertIsInstance(readiness_inputs, dict)
        self.assertIsInstance(external_inputs, dict)
        hidden_evaluation = external_inputs["hidden_evaluation"]
        self.assertIsInstance(hidden_evaluation, dict)
        self.assertEqual(
            readiness_inputs["hidden_freeze_protocol_digest"],
            hidden_freeze.protocol_digest(),
        )
        self.assertEqual(
            hidden_evaluation["public_blocked_receipt_digest"],
            receipt["document_digest"],
        )

    def test_frozen_receipt_exposes_only_closed_public_bindings(self) -> None:
        receipt = _frozen_receipt()

        result = hidden_freeze.evaluate_public_receipt(receipt)
        bindings = result["manifest_bindings"]

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["v_pre_004"], "PASS")
        self.assertEqual(bindings["held_out_baseline_supported_count"], 3)
        self.assertEqual(bindings["held_out_target_supported_count"], 8)
        self.assertEqual(bindings["held_out_question_count"], 16)

    def test_commitments_are_keyed_and_domain_separated(self) -> None:
        payload = {"public_test_vector": "same"}

        first = hidden_freeze.commit_hidden_payload(
            _PUBLIC_TEST_SECRET, "canary_001_suite", payload
        )
        second = hidden_freeze.commit_hidden_payload(
            _PUBLIC_TEST_SECRET, "canary_002_suite", payload
        )
        other_key = hidden_freeze.commit_hidden_payload(
            b"another-public-test-vector-key!!",
            "canary_001_suite",
            payload,
        )

        self.assertNotEqual(first, second)
        self.assertNotEqual(first, other_key)
        self.assertTrue(first.startswith("hmac-sha256:"))
        self.assertTrue(
            hidden_freeze.verify_hidden_payload_opening(
                _PUBLIC_TEST_SECRET,
                "canary_001_suite",
                payload,
                first,
            )
        )
        self.assertFalse(
            hidden_freeze.verify_hidden_payload_opening(
                _PUBLIC_TEST_SECRET,
                "canary_002_suite",
                payload,
                first,
            )
        )

    def test_unknown_field_that_could_carry_hidden_content_is_rejected(self) -> None:
        receipt = _frozen_receipt()
        receipt["project_name"] = "forbidden"
        receipt = _reseal(receipt)

        with self.assertRaisesRegex(hidden_freeze.HiddenFreezeFailure, "unknown"):
            hidden_freeze.validate_public_receipt(receipt)

    def test_plain_unkeyed_digest_cannot_replace_a_commitment(self) -> None:
        receipt = _frozen_receipt()
        commitments = dict(receipt["commitments"])
        commitments["held_out_suite"] = "sha256:" + "b" * 64
        receipt["commitments"] = commitments
        receipt = _reseal(receipt)

        with self.assertRaisesRegex(hidden_freeze.HiddenFreezeFailure, "commitment"):
            hidden_freeze.validate_public_receipt(receipt)

    def test_unverified_isolation_cannot_pass(self) -> None:
        receipt = _frozen_receipt()
        holder = dict(receipt["holder"])
        holder["cross_turn_recovery"] = False
        receipt["holder"] = holder
        receipt = _reseal(receipt)

        with self.assertRaisesRegex(hidden_freeze.HiddenFreezeFailure, "cross_turn"):
            hidden_freeze.validate_public_receipt(receipt)

    def test_reasoned_or_miscalculated_baseline_cannot_pass(self) -> None:
        receipt = _frozen_receipt(baseline_supported=5)
        baseline = dict(receipt["baseline"])
        baseline["execution_status"] = "REASONED"
        baseline["target_supported_count"] = 9
        receipt["baseline"] = baseline
        receipt = _reseal(receipt)

        with self.assertRaisesRegex(hidden_freeze.HiddenFreezeFailure, "execution_status"):
            hidden_freeze.validate_public_receipt(receipt)

    def test_public_receipt_loader_requires_canonical_json(self) -> None:
        receipt = _frozen_receipt()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "receipt.json"
            path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")

            with self.assertRaisesRegex(hidden_freeze.HiddenFreezeFailure, "canonical"):
                hidden_freeze.load_public_receipt(path)

    def test_product_code_freeze_covers_and_rechecks_public_fileset(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        commitment = _frozen_receipt()

        code_freeze = hidden_freeze_lifecycle.build_product_code_freeze_receipt(
            repository=repository,
            capsule="CANARY_001",
            commitment_receipt=commitment,
            external_evaluation_harness_digest="sha256:" + "c" * 64,
        )

        hidden_freeze_lifecycle.validate_code_freeze_chain(
            repository=repository,
            commitment_receipt=commitment,
            code_freeze_receipt=code_freeze,
        )
        self.assertTrue(all(code_freeze["freeze_scope"].values()))

    def test_disclosure_chain_requires_one_sealed_attempt_after_freeze(self) -> None:
        repository = Path(__file__).resolve().parents[1]
        commitment = _frozen_receipt()
        code_freeze = hidden_freeze_lifecycle.build_product_code_freeze_receipt(
            repository=repository,
            capsule="CANARY_001",
            commitment_receipt=commitment,
            external_evaluation_harness_digest="sha256:" + "d" * 64,
        )
        disclosure = hidden_freeze_lifecycle._seal(
            hidden_freeze_lifecycle.DISCLOSURE_SCHEMA,
            {
                "schema": hidden_freeze_lifecycle.DISCLOSURE_SCHEMA,
                "status": "DISCLOSED",
                "protocol_digest": hidden_freeze.protocol_digest(),
                "capsule": "CANARY_001",
                "generation": 1,
                "commitment_receipt_digest": commitment["document_digest"],
                "code_freeze_receipt_digest": code_freeze["document_digest"],
                "opening_evidence_digest": "sha256:" + "e" * 64,
                "opening_verification": "PASS",
                "authorization_status": "AUTHORIZED_AFTER_CODE_FREEZE",
                "first_exposure_sequence": 1,
                "pre_exposure_shared_surface_count": 0,
                "attempt_count": 1,
                "execution_seal": "SEALED_SINGLE_ATTEMPT",
                "result_status": "FAIL",
                "result_digest": "sha256:" + "f" * 64,
                "pre_execution_freeze_recheck": "PASS",
                "post_execution_freeze_recheck": "PASS",
                "post_exposure_product_change_count": 0,
                "result_seal_status": "SEALED_BEFORE_NEXT_PRODUCT_CHANGE",
                "capsule_consumption_status": "CONSUMED_AFTER_RESULT_SEAL",
                "burn_status": "NOT_BURNED",
                "production_activation": "NOT_EXECUTED",
            },
        )

        hidden_freeze_lifecycle.validate_disclosure_chain(
            repository=repository,
            commitment_receipt=commitment,
            code_freeze_receipt=code_freeze,
            disclosure_receipt=disclosure,
        )

    def test_burn_requires_new_generation_and_replaced_capsule(self) -> None:
        burned = _frozen_receipt()
        replacement = _frozen_receipt(
            generation=2,
            secret=b"replacement-public-test-key!!!!!",
        )
        burn = hidden_freeze_lifecycle._seal(
            hidden_freeze_lifecycle.BURN_SCHEMA,
            {
                "schema": hidden_freeze_lifecycle.BURN_SCHEMA,
                "status": "BURNED",
                "protocol_digest": hidden_freeze.protocol_digest(),
                "capsule": "HELD_OUT",
                "generation": 1,
                "commitment_receipt_digest": burned["document_digest"],
                "code_freeze_receipt_digest": "NOT_AVAILABLE",
                "disclosure_receipt_digest": "NOT_AVAILABLE",
                "trigger": "EARLY_DISCLOSURE",
                "original_result_preservation": "NO_RESULT_AVAILABLE",
                "original_result_digest": "NOT_AVAILABLE",
                "replacement_rule": (
                    "REPLACE_TWO_PROJECTS_COMPLETE_SUITE_BASELINE_AND_TARGET"
                ),
                "minimum_next_generation": 2,
                "production_activation": "NOT_EXECUTED",
            },
        )

        hidden_freeze_lifecycle.validate_replacement_after_burn(
            burned_commitment_receipt=burned,
            replacement_commitment_receipt=replacement,
            burn_receipt=burn,
        )


if __name__ == "__main__":
    unittest.main()
