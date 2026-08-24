from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

from scripts.docs import safe_load_manifest
from validation.structure_world_model_iteration_007 import readiness_oracle


REPOSITORY = Path(__file__).resolve().parents[1]
MANIFEST = (
    REPOSITORY / "docs/project/iterations/iteration-007/manifest.yaml"
)


class Iteration007ReadinessOracleTests(unittest.TestCase):
    def test_frontend_and_no_payload_oracles_are_reproducible(self) -> None:
        result = readiness_oracle.evaluate()

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["canonicalization"]["status"], "PASS")
        self.assertEqual(result["information_preservation"]["status"], "PASS")
        self.assertEqual(result["information_boundary"]["status"], "PASS")
        self.assertEqual(result["legacy_calls_consistency"]["status"], "PASS")
        self.assertEqual(result["canonicalization"]["record_count"], 12)
        self.assertEqual(
            result["canonicalization"]["jdk_identity"],
            {"javac_version": "javac 21.0.8", "source_release": "17"},
        )
        self.assertEqual(result["information_boundary"]["deliberate_leak_count"], 6)
        self.assertEqual(
            result["information_boundary"]["deliberate_leaks_rejected"], 6
        )
        self.assertEqual(result["legacy_calls_consistency"]["call_count"], 2)
        self.assertEqual(result["legacy_calls_consistency"]["call_site_count"], 3)
        self.assertEqual(result["legacy_calls_consistency"]["support_count"], 3)
        rendered = (
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        result_digest = "sha256:" + hashlib.sha256(rendered).hexdigest()
        self.assertEqual(
            result_digest,
            "sha256:0c946655de2b6daadf670d7c0a9f5f57b11f7a0ba04fde53a1f8940338f09f2f",
        )
        self.assertEqual(
            result["visible_development_corpus_digest"],
            "sha256:601849dae8d3e48479f0d9127e23dd2cad27d283e09562550f22443b7868b0aa",
        )
        self.assertEqual(
            result["canonicalization"]["oracle_fileset_digest"],
            "sha256:edfb7ead08c137a9f47e37571de0d9b8f3ee7417278c84ed186a043c271122ff",
        )
        self.assertEqual(
            result["information_preservation"]["oracle_fileset_digest"],
            "sha256:1751646fcdebd64798495a2b29811acc8bf058c37cf41e549201e876e498f67c",
        )
        self.assertEqual(
            result["information_boundary"]["oracle_fileset_digest"],
            "sha256:5699efa859e716e208279675bb452a133c8ae87d6742cfc19b66f1626762b6a4",
        )
        self.assertEqual(
            result["legacy_calls_consistency"]["oracle_fileset_digest"],
            "sha256:f1242a198afdf4d3cec425f1c715c094578cfaa9a70ed7798094afaf26b240f3",
        )

        manifest = safe_load_manifest(MANIFEST.read_text(encoding="utf-8"))
        alignment = manifest["product_goal_alignment"]
        readiness_inputs = manifest["readiness_inputs"]
        self.assertIsInstance(alignment, dict)
        self.assertIsInstance(readiness_inputs, dict)
        frontend = readiness_inputs["java_frontend"]
        self.assertIsInstance(frontend, dict)
        self.assertEqual(
            alignment["visible_development_corpus_digest"],
            result["visible_development_corpus_digest"],
        )
        self.assertEqual(
            frontend["offline_artifact_digest"],
            result["frontend"]["offline_artifact_digest"],
        )
        self.assertEqual(
            frontend["canonicalization_oracle_digest"],
            result["canonicalization"]["oracle_fileset_digest"],
        )
        self.assertEqual(
            frontend["information_preservation_oracle_digest"],
            result["information_preservation"]["oracle_fileset_digest"],
        )
        self.assertEqual(
            frontend["information_boundary_oracle_digest"],
            result["information_boundary"]["oracle_fileset_digest"],
        )
        self.assertEqual(
            frontend["legacy_calls_consistency_oracle_digest"],
            result["legacy_calls_consistency"]["oracle_fileset_digest"],
        )
        self.assertEqual(frontend["readiness_oracle_result_digest"], result_digest)
        result_path = REPOSITORY / str(frontend["readiness_oracle_result_path"])
        self.assertEqual(result_path.read_bytes(), rendered)
        # ITER-007 is historical evidence. Its input digest binds the contract
        # bytes that existed at readiness time, not today's current documents.
        self.assertEqual(
            readiness_inputs["system_contract_set_schema"],
            "ITER-007-SYSTEM-CONTRACT-SET@1",
        )
        self.assertEqual(
            readiness_inputs["system_contract_set_digest"],
            "sha256:5857ee235478c5e2b8f4d516dfdfcc99b4c6503e827b7ca23fbc5ae2a864e355",
        )

    def test_canonical_reference_shape_cannot_smuggle_source(self) -> None:
        source = readiness_oracle.JAVA_SOURCE.read_bytes()

        single_ref = readiness_oracle._reference_projection()
        single_ref["method_ref"] = "a" + source.hex() + "#m()"
        with self.assertRaises(RuntimeError):
            readiness_oracle._assert_no_payload(single_ref, source.decode("utf-8"))

        distributed = json.loads(
            json.dumps(readiness_oracle._reference_projection())
        )
        chunks = [source[index : index + 30] for index in range(0, len(source), 30)]
        distributed["atoms"].extend(
            {
                "atom_ref": f"atom:call:{ordinal + 6}",
                "kind": "CALL_SITE",
                "target_method_ref": "a" + chunk.hex() + "#m()",
                "source_order": ordinal + 6,
                "support_refs": ["support:4"],
            }
            for ordinal, chunk in enumerate(chunks)
        )
        with self.assertRaises(RuntimeError):
            readiness_oracle._assert_no_payload(distributed, source.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
