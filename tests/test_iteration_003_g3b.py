from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.cross_cutting import digest_of
from validation.structure_world_model_iteration_003.g3b import evaluate_results
from validation.structure_world_model_iteration_003.g3b import role_worker
from validation.structure_world_model_iteration_003.g3b import run_g3b


PROJECT_ROOT = Path(__file__).resolve().parents[1]
G3B_ROOT = (
    PROJECT_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "g3b"
)


class Iteration003G3bTests(unittest.TestCase):
    def test_disclosure_freeze_digest_and_production_exclusion_are_exact(self):
        freeze = json.loads(
            (G3B_ROOT / "input-freeze-1.0.0.json").read_text(encoding="utf-8")
        )
        core = {key: value for key, value in freeze.items() if key != "document_digest"}
        self.assertEqual(freeze["document_digest"], digest_of(core).value)
        self.assertTrue(freeze["disclosure"]["confirmed"])
        self.assertFalse(freeze["disclosure"]["repeat_confirmation_required"])
        self.assertFalse(freeze["disclosure"]["production_activation_included"])
        self.assertEqual(freeze["activation"]["production_activation"], "NOT_EXECUTED")

    def test_gateway_profile_denies_every_new_public_connection(self):
        gateway = (G3B_ROOT / "gateway.sb").read_text(encoding="utf-8")
        answer = (G3B_ROOT / "answer.sb").read_text(encoding="utf-8")
        projector = (G3B_ROOT / "projector.sb").read_text(encoding="utf-8")
        self.assertNotIn("(allow network-outbound\n    (remote", gateway)
        self.assertIn("already-connected, peer-pinned TCP socket", gateway)
        self.assertIn('(literal (param "GATEWAY_SOCKET"))', answer)
        self.assertIn("(deny network*)", projector)

    def test_profile_parameters_are_closed_and_do_not_expose_provider_host(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve().joinpath(
                "var",
                "iteration-003",
                "g3b",
                "implementation-checkpoint",
                "dispatch",
                "runs",
                "001-case",
                "answer",
            )
            root.mkdir(parents=True)
            paths = {}
            for name in ("package", "input", "output", "socket"):
                path = root / name
                path.mkdir()
                paths[name] = path
            runtime = run_g3b._runtime_capabilities()
            parameters = run_g3b._profile_parameters(
                role="gateway",
                package_root=paths["package"],
                input_root=paths["input"],
                output_root=paths["output"],
                socket_root=paths["socket"],
                gateway_socket=paths["socket"] / "gateway.sock",
                runtime=runtime,
            )
        self.assertEqual(parameters["SOCKET_ROOT"], str(paths["socket"]))
        self.assertNotIn("PROVIDER_HOST_PORT", parameters)
        self.assertEqual(
            len([key for key in parameters if key.startswith("ANCESTOR_")]),
            run_g3b.ANCESTOR_PARAMETER_COUNT,
        )
        self.assertEqual(run_g3b.ANCESTOR_PARAMETER_COUNT, 64)
        for profile_name in ("answer.sb", "gateway.sb", "projector.sb"):
            profile = (G3B_ROOT / profile_name).read_text(encoding="utf-8")
            self.assertIn('(literal (param "ANCESTOR_63"))', profile)

    def test_normal_operation_audit_distinguishes_exact_unix_route(self):
        policy = {
            "allowed_read_roots": ["/allowed"],
            "allowed_read_files": [],
            "allowed_write_roots": ["/output"],
            "allowed_write_files": [],
            "allowed_network": {
                "unix_connect": ["/socket/gateway.sock"],
                "unix_bind": [],
                "provider_connect": [],
            },
            "forbidden_categories": {
                name: []
                for name in (
                    "source_operations",
                    "git_operations",
                    "evidence_payload_reads",
                    "authority_database_operations",
                    "evidence_store_operations",
                    "other_role_operations",
                    "product_oracle_operations",
                    "baseline_result_operations",
                )
            },
        }
        audit = role_worker._OperationAudit(policy)
        audit.active = True
        audit.hook("socket.connect", (object(), "/socket/gateway.sock"))
        audit.hook("socket.connect", (object(), ("8.8.8.8", 443)))
        value = audit.payload()
        self.assertEqual(value["allowed_network_operations"]["unix_connect"], 1)
        self.assertEqual(
            value["prohibited_counts"]["out_of_allowlist_network_operations"],
            1,
        )
        self.assertEqual(value["status"], "FAIL")

    def test_direct_baseline_p95_reproduces_the_sealed_result(self):
        terminals = evaluate_results._baseline_terminals("direct")
        values = [
            float(item["executor_elapsed_milliseconds"])
            for item in terminals.values()
        ]
        self.assertEqual(len(values), 55)
        self.assertAlmostEqual(evaluate_results._p95(values), 101502.3109587)
        self.assertEqual(
            sum(item["status"] == "SUCCESS" for item in terminals.values()),
            15,
        )

    def test_quality_comparators_are_sealed_before_product_results(self):
        plan = json.loads(
            (
                evaluate_results.BASELINES
                / "operator"
                / "product-plan.json"
            ).read_text(encoding="utf-8")
        )
        comparison = evaluate_results.build_baseline_comparison_preflight(
            product_plan=plan,
            mall=json.loads(
                evaluate_results.MALL_ORACLE.read_text(encoding="utf-8")
            ),
            identity=json.loads(
                evaluate_results.IDENTITY_ORACLE.read_text(encoding="utf-8")
            ),
            generation=json.loads(
                (
                    evaluate_results.BASELINES
                    / "evaluator"
                    / "generation-report.json"
                ).read_text(encoding="utf-8")
            ),
        )
        self.assertEqual(
            comparison["document_digest"],
            "sha256:de42d96e678fca44376d54dbdb0a6956a365322844df5942c25d61850d58fabd",
        )
        self.assertEqual(comparison["run_count"], 55)
        self.assertEqual(comparison["direct_success_count"], 15)
        self.assertEqual(comparison["direct_failure_count"], 40)
        self.assertEqual(comparison["mature_success_count"], 55)
        self.assertFalse(comparison["product_result_visible_at_seal"])

    def test_provider_socket_supervisor_environment_has_no_credential(self):
        environment = run_g3b._provisioner_environment()
        self.assertNotIn("ARK_API_KEY", environment)
        self.assertEqual(
            set(environment),
            {
                "TMPDIR",
                "PATH",
                "LANG",
                "LC_ALL",
                "TZ",
                "PYTHONDONTWRITEBYTECODE",
                "PYTHONHASHSEED",
                "PYTHONNOUSERSITE",
            },
        )
        self.assertEqual(
            run_g3b._provider_address_scope("198.18.0.26"),
            "EXECUTOR_SYNTHETIC_EXTERNAL",
        )
        self.assertEqual(
            run_g3b._provider_address_scope("8.8.8.8"),
            "PUBLIC_UNICAST",
        )
        for value in ("127.0.0.1", "10.0.0.1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                run_g3b._provider_address_scope(value)


if __name__ == "__main__":
    unittest.main()
