from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

from software_world_model.ai_infrastructure.java_model_egress_qualification import (
    JAVA_MODEL_EGRESS_POLICY_FILE_DIGEST,
)
from software_world_model.cross_cutting import Digest, canonical_json_bytes, digest_of
from software_world_model.interface import world_model_runtime


class WorldModelEvaluationGrantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    @staticmethod
    def _write_document(
        path: Path,
        schema: str,
        core: dict[str, object],
    ) -> dict[str, object]:
        document = {
            **core,
            "document_digest": digest_of([schema, core]).value,
        }
        path.write_bytes(canonical_json_bytes(document))
        return document

    @staticmethod
    def _reference(
        path: Path,
        *,
        document_digest: str | None = None,
    ) -> dict[str, str]:
        reference = {
            "path": str(path.resolve(strict=True)),
            "raw_sha256": world_model_runtime._raw_sha256_file(path),
        }
        if document_digest is not None:
            reference["document_digest"] = document_digest
        return reference

    def _grant(self) -> tuple[Path, Path]:
        commit = "a" * 40
        tree = "b" * 40
        stage = self.root / "candidate-stage"
        packages = stage / "packages"
        entrypoint_hashes: dict[str, str] = {}
        for role, relative in world_model_runtime._ROLE_ENTRYPOINTS.items():
            entrypoint = packages / role / relative
            entrypoint.parent.mkdir(parents=True)
            entrypoint.write_text(f"# exact {role} candidate\n", encoding="utf-8")
            entrypoint_hashes[role] = world_model_runtime._raw_sha256_file(
                entrypoint
            )

        gateway_input = stage / "gateway-input"
        gateway_input.mkdir()
        gateway_hashes: dict[str, str] = {}
        for name in sorted(world_model_runtime._GATEWAY_INPUT_FILES):
            path = gateway_input / name
            if name == "g3b-freeze.json":
                path.write_bytes(
                    canonical_json_bytes(
                        {"schema": world_model_runtime._LEGACY_GATEWAY_FREEZE_SCHEMA}
                    )
                )
            else:
                path.write_text(f"exact {name}\n", encoding="utf-8")
            gateway_hashes[name] = world_model_runtime._raw_sha256_file(path)

        stage_digest = digest_of(world_model_runtime._tree_manifest(stage)).value
        launcher_hashes = {
            label: world_model_runtime._raw_sha256_file(path)
            for label, path in world_model_runtime._launcher_files().items()
        }
        launcher_manifest_digest = digest_of(
            ["SWM-WORLD-MODEL-LAUNCHER-MANIFEST@1", launcher_hashes]
        ).value

        evaluator = self.root / "independent-evaluator.py"
        evaluator.write_text("# independent evaluator\n", encoding="utf-8")
        evaluator_digest = world_model_runtime._sha256_file(evaluator)

        suite_schema = "SWM-WORLD-MODEL-HELD-OUT-SUITE@2"
        suite_path = self.root / "held-out-suite.json"
        suite = self._write_document(
            suite_path,
            suite_schema,
            {
                "schema": suite_schema,
                "environment": "EVALUATION_ONLY",
                "evaluation_subject_commit": commit,
                "evaluation_subject_tree": tree,
                "sealed_before_world_model_results": True,
                "world_model_result_count_at_seal": 0,
                "controlled_direct_result_count_at_seal": 0,
                "mature_source_agent_result_count_at_seal": 0,
                "comparison_surfaces": [
                    "WORLD_MODEL",
                    "CONTROLLED_DIRECT",
                    "MATURE_SOURCE_AGENT",
                ],
                "comparison_protocols": {"sealed": True},
                "source_closures": {"sealed": True},
                "cases": [],
                "production_activation": "NOT_EXECUTED",
            },
        )

        qualification_schema = (
            "SWM-WORLD-MODEL-DETERMINISTIC-QUALIFICATION@1"
        )
        qualification_path = self.root / "deterministic-qualification.json"
        qualification = self._write_document(
            qualification_path,
            qualification_schema,
            {
                "schema": qualification_schema,
                "status": "PASS",
                "evaluation_subject_status": "CANDIDATE",
                "implementation_commit": commit,
                "implementation_tree": tree,
                "stage_manifest_digest": stage_digest,
                "launcher_manifest_digest": launcher_manifest_digest,
                "held_out_suite_digest": suite["document_digest"],
                "independent_evaluator_digest": evaluator_digest,
                "focused_tests_pass": True,
                "candidate_answer_package_tests_pass": True,
                "deterministic_product_probe_pass": True,
                "deterministic_product_probe_digest": (
                    "sha256:" + "e" * 64
                ),
                "full_regression_pass": True,
                "docs_check_pass": True,
                "external_model_called": False,
                "production_activation": "NOT_EXECUTED",
            },
        )

        oracle = self.root / "product-oracle.json"
        oracle.write_bytes(canonical_json_bytes({"sealed": True}))
        baseline = self.root / "baseline-results.json"
        baseline.write_bytes(canonical_json_bytes({"result_count": 0}))

        disclosure_schema = (
            "SWM-WORLD-MODEL-DISCLOSURE-AUTHORIZATION@1"
        )
        disclosure_core = {
            "status": "AUTHORIZED",
            "authorized_by": "user",
            "authorized_at": "2026-08-11T21:00:00+08:00",
            "authorization_ref": "unit-test-explicit-authorization",
            "payload_boundary": (
                "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
            ),
        }
        disclosure = {
            **disclosure_core,
            "document_digest": digest_of(
                [disclosure_schema, disclosure_core]
            ).value,
        }
        grant_core = {
            "schema": world_model_runtime.GRANT_SCHEMA,
            "environment": "EVALUATION_ONLY",
            "live_dispatch_authorized": True,
            "disclosure_authorization": disclosure,
            "evaluation_subject": {
                "status": "CANDIDATE",
                "commit": commit,
                "tree": tree,
                "stage_root": str(stage.resolve(strict=True)),
                "stage_manifest_digest": stage_digest,
                "deterministic_qualification": self._reference(
                    qualification_path,
                    document_digest=str(qualification["document_digest"]),
                ),
                "held_out_suite": self._reference(
                    suite_path,
                    document_digest=str(suite["document_digest"]),
                ),
                "independent_evaluator": self._reference(evaluator),
                "gateway_input_sha256": gateway_hashes,
                "role_entrypoint_sha256": entrypoint_hashes,
            },
            "provider": dict(world_model_runtime._EXPECTED_PROVIDER),
            "launcher_files": launcher_hashes,
            "forbidden_inputs": {
                "product_oracle": self._reference(oracle),
                "baseline_result": self._reference(baseline),
                "independent_evaluator": self._reference(evaluator),
            },
            "production_activation": "NOT_EXECUTED",
        }
        grant = {
            **grant_core,
            "document_digest": digest_of(
                [world_model_runtime.GRANT_SCHEMA, grant_core]
            ).value,
        }
        grant_path = self.root / "evaluation-grant.json"
        grant_path.write_bytes(canonical_json_bytes(grant))
        return grant_path, qualification_path

    def test_exact_candidate_grant_loads_without_dispatch(self) -> None:
        grant_path, _ = self._grant()

        grant = world_model_runtime._load_evaluation_grant(grant_path)

        self.assertEqual(grant.product_commit, "a" * 40)
        self.assertEqual(grant.product_tree, "b" * 40)
        self.assertEqual(grant.stage_root, self.root / "candidate-stage")
        self.assertEqual(
            grant.authorization_ref,
            "unit-test-explicit-authorization",
        )

    def test_candidate_grant_rejects_qualification_tamper(self) -> None:
        grant_path, qualification_path = self._grant()
        qualification_path.write_bytes(
            qualification_path.read_bytes() + b"\n"
        )

        with self.assertRaisesRegex(ValueError, "digest drifted"):
            world_model_runtime._load_evaluation_grant(grant_path)

    def test_java_provider_qualification_is_derived_from_gateway_freeze(self) -> None:
        gateway_input = self.root / "java-gateway-input"
        gateway_input.mkdir()
        qualification_digest = Digest("sha256:" + "1" * 64)
        qualification_document_digest = Digest("sha256:" + "2" * 64)
        closed_result_digest = Digest("sha256:" + "3" * 64)
        for name in ("qualification.json", "closed-result.json", "egress-policy.json"):
            (gateway_input / name).write_bytes(b"sealed by mocked loader")
        binding = SimpleNamespace(
            capability_qualification_ref=(
                "capability-evaluation:evaluation_result_" + "4" * 32
            ),
            capability_qualification_digest=qualification_digest,
            qualification_document_digest=qualification_document_digest,
            closed_capability_result_digest=closed_result_digest,
        )
        permission_digest = "sha256:" + "5" * 64
        core = {
            "schema": world_model_runtime._JAVA_GATEWAY_FREEZE_SCHEMA,
            "freeze_ref": "ITER-006-JAVA-PRODUCT-GATEWAY-CANDIDATE@1",
            "environment": "EVALUATION_ONLY",
            "strategy_ref": "model-snapshot-first-world-model-answer@1.1.0",
            "prompt_ref": "snapshot-first-world-model-proposal-prompt@4",
            "proposal_vocabulary_ref": (
                "world-model-authority-proposal-vocabulary@2"
            ),
            "capability_qualification_document_digest": (
                qualification_document_digest.value
            ),
            "closed_capability_result_digest": closed_result_digest.value,
            "egress_policy_digest": JAVA_MODEL_EGRESS_POLICY_FILE_DIGEST,
            "conformance_result_ref": "CC-ARK-CHAT-NO-TOOLS-001:sealed",
            "conformance_result_digest": world_model_runtime._EXPECTED_PROVIDER[
                "conformance_digest"
            ],
            "permission_digest": permission_digest,
            "production_activation": "NOT_EXECUTED",
        }
        freeze = {
            **core,
            "document_digest": digest_of(
                [world_model_runtime._JAVA_GATEWAY_FREEZE_SCHEMA, core]
            ).value,
        }
        (gateway_input / "g3b-freeze.json").write_bytes(
            canonical_json_bytes(freeze)
        )

        with mock.patch(
            "software_world_model.ai_infrastructure.java_model_egress_qualification."
            "load_java_gateway_qualification_binding",
            return_value=binding,
        ):
            provider, qualification = (
                world_model_runtime._provider_binding_for_gateway_input(
                    gateway_input
                )
            )

        self.assertEqual(
            provider["qualification_digest"], qualification_digest.value
        )
        assert qualification is not None
        self.assertEqual(
            qualification["java_gateway_freeze_digest"],
            freeze["document_digest"],
        )


if __name__ == "__main__":
    unittest.main()
