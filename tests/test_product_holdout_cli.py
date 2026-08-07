from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from software_world_model.application_services import QualificationProof
from software_world_model.cross_cutting import DomainError, digest_of
from validation.product_holdout_iteration_002 import (
    HoldoutAnswerPath,
    HoldoutPathResult,
    SealedAnswerClaim,
    build_task_input,
    load_holdout_suite,
    save_path_result,
)
from validation.product_holdout_iteration_002.cli import (
    QUALIFICATION_DOCUMENT_SCHEMA,
    _runtime_database_path,
    load_qualification_proof,
    main,
)


class ProductHoldoutCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.workspace = Path(__file__).resolve().parents[1]
        self.suite = load_holdout_suite()
        self.task_input = build_task_input(
            self.suite, task_id=self.suite["tasks"][0]["task_id"]
        )

    def result(self, path: HoldoutAnswerPath) -> HoldoutPathResult:
        return HoldoutPathResult.create(
            result_ref=f"result:{path.value.lower()}",
            run_id=f"run:{path.value.lower()}",
            path=path,
            origin=f"origin:{path.value.lower()}",
            implementation_digest=digest_of({"path": path.value}),
            task_input=self.task_input,
            answer="Bounded answer.",
            claims=(SealedAnswerClaim("Bounded answer.", ("source:1",)),),
            actual_model_fingerprint="glm-5.2",
            provider_request_ids=(f"provider:{path.value.lower()}",),
            model_call_count=1,
            source_action_count=1,
            source_byte_count=100,
            input_tokens=100,
            output_tokens=20,
            usage_complete=True,
        )

    def test_verify_inputs_command_is_offline_and_reports_sealed_counts(self) -> None:
        output = StringIO()

        exit_code = main(
            ("verify-inputs", "--workspace-root", str(self.workspace)),
            stdout=output,
        )
        payload = json.loads(output.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["repository_count"], 2)
        self.assertEqual(payload["task_count"], 6)
        self.assertFalse(payload["external_model_called"])

    def test_seal_pair_command_uses_only_persisted_path_results(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            direct = save_path_result(
                self.result(HoldoutAnswerPath.DIRECT),
                task_input=self.task_input,
                result_directory=directory,
            )
            world = save_path_result(
                self.result(HoldoutAnswerPath.WORLD_ASSISTED),
                task_input=self.task_input,
                result_directory=directory,
            )
            output = StringIO()

            exit_code = main(
                (
                    "seal-pair",
                    "--direct-result",
                    str(direct),
                    "--system-result",
                    str(world),
                    "--result-directory",
                    directory,
                ),
                stdout=output,
            )
            payload = json.loads(output.getvalue())

            self.assertEqual(exit_code, 0)
            self.assertEqual(payload["status"], "SEALED")
            self.assertTrue(payload["independent_review_ready"])
            self.assertTrue(Path(payload["pair_path"]).is_file())

            prepared_output = StringIO()
            self.assertEqual(
                main(
                    (
                        "prepare-review",
                        "--pair",
                        payload["pair_path"],
                        "--result-directory",
                        directory,
                    ),
                    stdout=prepared_output,
                ),
                0,
            )
            prepared = json.loads(prepared_output.getvalue())
            template = json.loads(
                Path(prepared["review_draft_path"]).read_text(encoding="utf-8")
            )
            self.assertFalse(prepared["judgement_recorded"])
            self.assertEqual(
                [item["dimension"] for item in template["assessments"]],
                self.suite["tasks"][0]["acceptance_dimensions"],
            )

    def test_qualification_file_loader_rejects_document_tampering(self) -> None:
        core = {
            "proof_ref": "capability-evaluation:result",
            "capability_id": "capability",
            "capability_contract_version": "1",
            "strategy_id": "strategy",
            "strategy_version": "1",
            "result_ref": "evaluation_result_00000000000000000000000000000001",
            "validity_ref": "evaluation_validity_00000000000000000000000000000001@1",
            "qualification_kind": "CAPABILITY_EVALUATION",
        }
        proof = QualificationProof(**core, digest=digest_of(core))
        document_core = {
            "schema": QUALIFICATION_DOCUMENT_SCHEMA,
            "proof": {**proof.core(), "digest": proof.digest.value},
        }
        document = {
            **document_core,
            "document_digest": digest_of(document_core).value,
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "qualification.json"
            path.write_text(json.dumps(document), encoding="utf-8")
            self.assertEqual(load_qualification_proof(path), proof)

            document["proof"]["strategy_version"] = "changed"
            path.write_text(json.dumps(document), encoding="utf-8")
            with self.assertRaises(DomainError):
                load_qualification_proof(path)

    def test_runtime_database_is_stable_per_run_and_isolated_between_runs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            first_arguments = SimpleNamespace(
                result_directory=directory,
                run_id="acceptance-run-1",
            )
            second_arguments = SimpleNamespace(
                result_directory=directory,
                run_id="acceptance-run-2",
            )

            first = _runtime_database_path(
                first_arguments,
                task_input=self.task_input,
                path="system",
            )
            first_replay = _runtime_database_path(
                first_arguments,
                task_input=self.task_input,
                path="system",
            )
            second = _runtime_database_path(
                second_arguments,
                task_input=self.task_input,
                path="system",
            )

        self.assertEqual(first, first_replay)
        self.assertNotEqual(first, second)
        self.assertNotIn("acceptance-run", first.name)


if __name__ == "__main__":
    unittest.main()
