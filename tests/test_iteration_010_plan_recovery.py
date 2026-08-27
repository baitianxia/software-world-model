from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


RUNNER = (
    Path(__file__).resolve().parents[1]
    / "validation"
    / "iteration_010_plan_recovery"
    / "value_gate"
    / "runner.py"
)
SPEC = importlib.util.spec_from_file_location("iteration_010_plan_recovery", RUNNER)
assert SPEC is not None and SPEC.loader is not None
recovery = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = recovery
SPEC.loader.exec_module(recovery)

RUNNER_IDENTITY_DIGEST = "sha256:" + "a" * 64


def evidence(case_id: str = recovery.RECOVERY_CASE_ID) -> dict[str, object]:
    return recovery.build_evidence(case_id, RUNNER_IDENTITY_DIGEST)


def run_raw(raw: bytes) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, "-I", "-S", str(RUNNER), "verify-plan-evidence"],
        input=raw,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class Iteration010PlanRecoveryTests(unittest.TestCase):
    def assert_rejected(self, artifact: dict[str, object]) -> None:
        with self.assertRaises(recovery.EvidenceError):
            recovery.validate_evidence(artifact)

    def test_recovery_and_activation_identities_are_both_closed_and_valid(self) -> None:
        for case_id, plan_revision_ref in (
            (recovery.RECOVERY_CASE_ID, "ITER-010-PDR-009"),
            (recovery.ACTIVATION_CASE_ID, "ITER-010-PDR-010"),
        ):
            with self.subTest(case_id=case_id):
                artifact = evidence(case_id)
                live = recovery.validate_evidence(artifact)
                self.assertEqual(artifact["plan_revision_ref"], plan_revision_ref)
                self.assertEqual(live["verification_case_id"], case_id)
                self.assertEqual(live["plan_gate_verdict"], "PASS")
                self.assertEqual(live["external_model_call_count"], 0)
                self.assertEqual(set(live), recovery.LIVE_FIELDS)

    def test_isolated_cli_reads_raw_bytes_and_emits_only_nine_fields(self) -> None:
        artifact = evidence(recovery.ACTIVATION_CASE_ID)
        completed = run_raw(recovery.canonical_json_bytes(artifact))
        self.assertEqual(completed.returncode, 0, completed.stderr.decode())
        self.assertEqual(completed.stderr, b"")
        live = json.loads(completed.stdout)
        self.assertEqual(set(live), recovery.LIVE_FIELDS)
        self.assertEqual(live, recovery.validate_evidence(artifact))

    def test_raw_json_rejects_duplicates_invalid_numbers_and_non_objects(self) -> None:
        valid = recovery.canonical_json_bytes(evidence())
        samples = (
            b'{"schema":"first","schema":"second"}',
            b'{"value":NaN}',
            b"[]",
            b"\xff",
            valid + b"{}",
        )
        for raw in samples:
            with self.subTest(raw=raw[:40]):
                completed = run_raw(raw)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, b"")
                self.assertEqual(completed.stderr, b"")

    def test_every_object_is_closed(self) -> None:
        mutations = []
        for location in (
            (),
            ("action_evidence",),
            ("action_evidence", "change_boundary"),
            ("execution_counters",),
            ("runner_receipt",),
            ("case_outcomes", 0),
        ):
            artifact = evidence()
            target: object = artifact
            for item in location:
                target = target[item]  # type: ignore[index]
            assert isinstance(target, dict)
            target["unexpected"] = True
            mutations.append((location, artifact))
        for location, artifact in mutations:
            with self.subTest(location=location):
                self.assert_rejected(artifact)

    def test_both_exact_authorization_refs_are_required_in_order(self) -> None:
        mutations = (
            [],
            [recovery.PLAN_CHANGE_AUTHORIZATION_REF],
            [recovery.RECOVERY_AUTHORIZATION_REF],
            list(reversed(recovery.AUTHORIZATION_REFS)),
            [
                recovery.PLAN_CHANGE_AUTHORIZATION_REF,
                "local-user-message-utf8:sha256:" + "b" * 64,
            ],
        )
        for refs in mutations:
            artifact = evidence()
            artifact["action_evidence"]["authorization_refs"] = refs  # type: ignore[index]
            artifact["subject_digest"] = recovery.canonical_digest(
                artifact["action_evidence"]
            )
            with self.subTest(refs=refs):
                self.assert_rejected(artifact)

    def test_recovery_cannot_grant_product_or_external_authority(self) -> None:
        for field in (
            "product_code_change_authorized",
            "external_execution_authorized",
        ):
            artifact = evidence()
            boundary = artifact["action_evidence"]["change_boundary"]  # type: ignore[index]
            boundary[field] = True
            artifact["subject_digest"] = recovery.canonical_digest(
                artifact["action_evidence"]
            )
            with self.subTest(field=field):
                self.assert_rejected(artifact)
        artifact = evidence()
        artifact["action_evidence"]["change_boundary"][  # type: ignore[index]
            "plan_governance_change_authorized"
        ] = False
        self.assert_rejected(artifact)

    def test_all_execution_counters_are_exact_integer_zero(self) -> None:
        for field in recovery.COUNTER_KEYS:
            for invalid in (1, False, "0", -1):
                artifact = evidence()
                artifact["execution_counters"][field] = invalid  # type: ignore[index]
                with self.subTest(field=field, invalid=invalid):
                    self.assert_rejected(artifact)

    def test_case_identity_cannot_cross_plan_revisions(self) -> None:
        for field, invalid in (
            ("verification_case_id", "V-NOT-REGISTERED-001"),
            ("plan_revision_ref", "ITER-010-PDR-010"),
            ("result_id", "ITER-010-RESULT-V-PDR010-ACTIVATION-001"),
            (
                "evidence_artifact_path",
                "docs/project/iterations/iteration-010/results/evidence/"
                "v-pdr010-activation-001.json",
            ),
            ("action_ref", "ITER-010-ACTION-DIRECTION-FREEZE-001"),
            ("plan_gate_verdict", "FAIL"),
        ):
            artifact = evidence()
            artifact[field] = invalid
            with self.subTest(field=field):
                self.assert_rejected(artifact)

    def test_every_internal_digest_is_recomputed(self) -> None:
        mutations = (
            "execution_input_digest",
            "runner_identity_digest",
            "runner_receipt_digest",
            "verification_report_digest",
            "subject_digest",
        )
        for field in mutations:
            artifact = evidence()
            artifact[field] = "sha256:" + "f" * 64
            with self.subTest(field=field):
                self.assert_rejected(artifact)

    def test_receipt_and_case_outcome_are_exactly_bound(self) -> None:
        mutations: list[dict[str, object]] = []

        artifact = evidence()
        artifact["runner_receipt"]["completed"] = False  # type: ignore[index]
        artifact["runner_receipt_digest"] = recovery.canonical_digest(
            artifact["runner_receipt"]
        )
        mutations.append(artifact)

        artifact = evidence()
        artifact["case_outcomes"][0]["evidence_digest"] = (  # type: ignore[index]
            "sha256:" + "c" * 64
        )
        artifact["verification_report_digest"] = recovery.canonical_digest(
            artifact["case_outcomes"]
        )
        mutations.append(artifact)

        artifact = evidence()
        artifact["case_outcomes"].append(  # type: ignore[union-attr]
            copy.deepcopy(artifact["case_outcomes"][0])  # type: ignore[index]
        )
        artifact["verification_report_digest"] = recovery.canonical_digest(
            artifact["case_outcomes"]
        )
        mutations.append(artifact)

        for artifact in mutations:
            with self.subTest(artifact=artifact):
                self.assert_rejected(artifact)


if __name__ == "__main__":
    unittest.main()
