from __future__ import annotations

from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

from validation.structure_world_model_iteration_003.isolation import probe_worker
from validation.structure_world_model_iteration_003.isolation import run_isolation
from validation.structure_world_model_iteration_003.isolation import workload_worker


class IsolationFixture:
    def __init__(self, temporary: str) -> None:
        self.root = Path(temporary).resolve(strict=True)
        self.stage = self.root / "stage"
        self.answer_package = self.stage / "answer" / "package"
        self.answer_bundles = self.stage / "answer" / "bundles"
        self.answer_output = self.stage / "answer" / "output"
        self.projector_package = self.stage / "projector" / "package"
        self.projector_input = self.stage / "projector" / "input"
        self.projector_store = self.stage / "projector" / "store"
        self.projector_output = self.stage / "projector" / "output"
        self.forbidden = self.root / "forbidden"
        self.repository = self.root / "repository"
        for directory in (
            self.answer_package,
            self.answer_bundles,
            self.answer_output,
            self.projector_package,
            self.projector_input,
            self.projector_store,
            self.projector_output,
            self.forbidden,
            self.repository / ".git",
        ):
            directory.mkdir(parents=True, exist_ok=True)

        (self.answer_package / "answer_main.py").write_text(
            'print("{\\\"schema\\\":\\\"sealed-result@1\\\"}")\n',
            encoding="utf-8",
        )
        (self.answer_package / "package-canary.txt").write_text(
            "answer package\n", encoding="utf-8"
        )
        (self.answer_bundles / "read-set-a-b.json").write_text(
            '{"snapshots":["A1","B","A2"]}\n', encoding="utf-8"
        )
        (self.projector_package / "projector_main.py").write_text(
            'print("{\\\"schema\\\":\\\"structure-view@1\\\"}")\n',
            encoding="utf-8",
        )
        (self.projector_package / "package-canary.txt").write_text(
            "projector package\n", encoding="utf-8"
        )
        (self.projector_store / "observations.json").write_text(
            '{"allowlisted":true}\n', encoding="utf-8"
        )
        (self.forbidden / "evidence.txt").write_text(
            "must be denied\n", encoding="utf-8"
        )
        self.database = self.forbidden / "authority.sqlite3"
        with sqlite3.connect(self.database) as connection:
            connection.execute("CREATE TABLE authority (value TEXT NOT NULL)")
            connection.execute("INSERT INTO authority VALUES ('forbidden')")
        (self.repository / ".git" / "HEAD").write_text(
            "ref: refs/heads/main\n", encoding="utf-8"
        )

    def configuration(self) -> dict[str, object]:
        return {
            "schema": run_isolation.CONFIG_SCHEMA,
            "stage_root": str(self.stage),
            "python_executable": str(Path(sys.executable).resolve(strict=True)),
            "source_remote": {"host": "source.example.invalid", "port": 443},
            "public_endpoint": {"host": "1.1.1.1", "port": 443},
            "dns_host": "dns.example.invalid",
            "forbidden": {
                "file": str(self.forbidden / "evidence.txt"),
                "sqlite": str(self.database),
                "git_root": str(self.repository),
                "git_marker": str(self.repository / ".git" / "HEAD"),
            },
            "answer": {
                "package_root": str(self.answer_package),
                "bundle_root": str(self.answer_bundles),
                "output_root": str(self.answer_output),
                "package_canary": str(self.answer_package / "package-canary.txt"),
                "bundle_canary": str(self.answer_bundles / "read-set-a-b.json"),
                "sealed_result": str(self.answer_output / "sealed-result.json"),
                "workload": {
                    "entrypoint": "answer_main.py",
                    "argv": [],
                    "stdout_output": "sealed-result.json",
                    "expected_outputs": ["sealed-result.json"],
                },
            },
            "projector": {
                "package_root": str(self.projector_package),
                "sealed_result": str(self.projector_input / "sealed-result.json"),
                "store_root": str(self.projector_store),
                "store_allowlist": ["observations.json"],
                "output_root": str(self.projector_output),
                "package_canary": str(
                    self.projector_package / "package-canary.txt"
                ),
                "store_canary": str(self.projector_store / "observations.json"),
                "workload": {
                    "entrypoint": "projector_main.py",
                    "argv": [],
                    "stdout_output": "structure-view.json",
                    "expected_outputs": ["structure-view.json"],
                },
            },
            "timeout_seconds": 30,
        }


class Iteration003G2IsolationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.fixture = IsolationFixture(self.temporary.name)

    def test_policies_are_default_deny_and_role_specific(self) -> None:
        answer = run_isolation.ANSWER_PROFILE.read_text(encoding="utf-8")
        projector = run_isolation.PROJECTOR_PROFILE.read_text(encoding="utf-8")
        for policy in (answer, projector):
            self.assertIn("(deny default)", policy)
            self.assertIn("(deny network*)", policy)
            self.assertIn("(deny process-fork)", policy)
            self.assertNotIn("(allow network", policy)
            self.assertNotIn('(subpath "/Users")', policy)
            self.assertNotIn('(subpath "/")', policy)
        self.assertIn('(subpath (param "BUNDLE_ROOT"))', answer)
        self.assertNotIn("STORE_ROOT", answer)
        self.assertNotIn("SEALED_RESULT", answer)
        self.assertIn('(literal (param "SEALED_RESULT"))', projector)
        self.assertIn('(subpath (param "STORE_ROOT"))', projector)
        self.assertNotIn("BUNDLE_ROOT", projector)

    def test_plan_is_explicitly_non_executed_and_contains_separate_children(self) -> None:
        config = run_isolation.parse_config(self.fixture.configuration())
        plan = run_isolation.build_plan(config)

        self.assertEqual(plan["isolation_status"], "NOT_EXECUTED")
        self.assertEqual(plan["v007_gate_status"], "NOT_EVALUATED")
        self.assertFalse(plan["os_enforcement"]["executed"])
        self.assertEqual(plan["claim_scope"], run_isolation.CLAIM_SCOPE)
        for role, profile in (
            ("answer", run_isolation.ANSWER_PROFILE),
            ("projector", run_isolation.PROJECTOR_PROFILE),
        ):
            commands = plan["commands"][role]
            self.assertEqual(set(commands), {"probe", "workload"})
            self.assertNotEqual(commands["probe"], commands["workload"])
            for command in commands.values():
                self.assertEqual(command[0], "/usr/bin/sandbox-exec")
                self.assertIn("-f", command)
                self.assertIn(str(profile), command)
                self.assertIn(str(Path(sys.executable).resolve(strict=True)), command)
                self.assertIn("-I", command)
                self.assertIn("-S", command)
                self.assertIn("-B", command)
                self.assertIn("--role", command)
                self.assertIn(role, command)
            self.assertTrue(any(item.endswith("probe_worker.py") for item in commands["probe"]))
            self.assertTrue(
                any(item.endswith("workload_worker.py") for item in commands["workload"])
            )
        self.assertEqual(
            plan["capability_profiles"]["answer"]["profile_parameters"][
                "PYTHON_EXECUTABLE"
            ],
            str(Path(sys.executable).resolve(strict=True)),
        )

    def test_probe_inventory_covers_every_required_denial(self) -> None:
        common = {
            "source_remote",
            "public_ip",
            "dns",
            "tcp",
            "unix_socket",
            "out_of_allowlist_open",
            "sqlite",
            "git_repository",
        }
        self.assertEqual(
            set(probe_worker.required_probes("answer")),
            common | {"answer_to_projector"},
        )
        self.assertEqual(
            set(probe_worker.required_probes("projector")),
            common | {"projector_to_answer"},
        )
        self.assertEqual(
            set(run_isolation.OUTER_PROCESS_PROBES),
            {
                "python_control",
                "process_fork",
                "git_process_exec",
                "subprocess_exec",
            },
        )

    def test_synthetic_worker_report_is_not_an_os_pass(self) -> None:
        required = list(probe_worker.required_probes("answer"))
        synthetic = {
            "schema": probe_worker.REPORT_SCHEMA,
            "role": "answer",
            "nonce": "synthetic",
            "pid": 123,
            "status": "PASS",
            "required_probes": required,
            "probes": [
                {"name": name, "outcome": "DENIED"} for name in required
            ],
            "authorized_access": [
                {"name": name, "outcome": "PASS"}
                for name in ("package_read", "bundle_read", "result_output_write")
            ],
        }
        self.assertFalse(
            run_isolation.worker_report_is_os_pass(
                synthetic,
                role="answer",
                nonce="synthetic",
                os_enforced=False,
            )
        )

    def test_probe_report_is_closed_and_cannot_include_workload_claim(self) -> None:
        required = list(probe_worker.required_probes("answer"))
        report = {
            "schema": probe_worker.REPORT_SCHEMA,
            "role": "answer",
            "nonce": "real-run",
            "pid": 123,
            "status": "PASS",
            "required_probes": required,
            "probes": [
                {
                    "name": name,
                    "outcome": "DENIED",
                    "exception": {"type": "PermissionError", "message": "denied"},
                }
                for name in required
            ],
            "authorized_access": [
                {"name": name, "outcome": "PASS"}
                for name in ("package_read", "bundle_read", "result_output_write")
            ],
        }
        self.assertTrue(
            run_isolation.worker_report_is_os_pass(
                report,
                role="answer",
                nonce="real-run",
                os_enforced=True,
            )
        )
        report["workload"] = {"status": "PASS"}
        self.assertFalse(
            run_isolation.worker_report_is_os_pass(
                report,
                role="answer",
                nonce="real-run",
                os_enforced=True,
            )
        )

    def test_both_product_workloads_are_mandatory(self) -> None:
        for role in ("answer", "projector"):
            value = deepcopy(self.fixture.configuration())
            value[role]["workload"] = None
            with self.assertRaisesRegex(
                run_isolation.ConfigurationError, "required for an executed G2 run"
            ):
                run_isolation.parse_config(value)

    def test_closed_output_manifest_rejects_undeclared_file(self) -> None:
        config = run_isolation.parse_config(self.fixture.configuration())
        output = self.fixture.answer_output / "sealed-result.json"
        output.write_text('{"status":"PASS"}\n', encoding="utf-8")
        manifest = run_isolation._tree_manifest(self.fixture.answer_output)
        evidence = {
            "worker_report": {
                "workload": {
                    "outputs": manifest,
                    "stdout_digest": manifest[0]["digest"],
                }
            }
        }
        report, passed = run_isolation._closed_output_manifest(
            config, "answer", evidence
        )
        self.assertTrue(passed, report)

        (self.fixture.answer_output / "undeclared.txt").write_text(
            "must fail\n", encoding="utf-8"
        )
        report, passed = run_isolation._closed_output_manifest(
            config, "answer", evidence
        )
        self.assertFalse(passed)
        self.assertFalse(report["paths_exact"])

    def test_closed_output_manifest_rejects_undeclared_empty_directory(self) -> None:
        config = run_isolation.parse_config(self.fixture.configuration())
        output = self.fixture.answer_output / "sealed-result.json"
        output.write_text('{"status":"PASS"}\n', encoding="utf-8")
        manifest = run_isolation._tree_manifest(self.fixture.answer_output)
        evidence = {
            "worker_report": {
                "workload": {
                    "outputs": manifest,
                    "stdout_digest": manifest[0]["digest"],
                }
            }
        }
        (self.fixture.answer_output / "undeclared").mkdir()

        report, passed = run_isolation._closed_output_manifest(
            config, "answer", evidence
        )

        self.assertFalse(passed)
        self.assertTrue(report["file_paths_exact"])
        self.assertFalse(report["directories_exact"])
        self.assertFalse(report["paths_exact"])

    def test_sanitized_environment_is_closed_and_records_values(self) -> None:
        environment = run_isolation._sanitized_environment(self.fixture.answer_output)
        self.assertEqual(
            environment,
            {
                "TMPDIR": str(self.fixture.answer_output),
                "PATH": "/usr/bin:/bin",
                "LANG": "C",
                "LC_ALL": "C",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONHASHSEED": "0",
                "PYTHONNOUSERSITE": "1",
            },
        )

    def test_normal_workload_audit_counts_forbidden_sqlite_network_and_process(self) -> None:
        config = run_isolation.parse_config(self.fixture.configuration())
        audit = workload_worker._OperationAudit(
            run_isolation._workload_audit_policy(config, "answer")
        )
        audit.hook("open", (str(self.fixture.answer_bundles / "read-set-a-b.json"), "r", 0))
        self.assertEqual(audit.payload()["status"], "PASS")

        audit.hook("sqlite3.connect", (str(self.fixture.database),))
        audit.hook("socket.connect", (None,))
        audit.hook("subprocess.Popen", ("/usr/bin/true",))
        report = audit.payload()
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(
            report["prohibited_counts"]["authority_database_operations"], 1
        )
        self.assertEqual(report["prohibited_counts"]["evidence_store_operations"], 1)
        self.assertEqual(
            report["prohibited_counts"]["out_of_allowlist_file_operations"], 1
        )
        self.assertEqual(report["prohibited_counts"]["network_operations"], 1)
        self.assertEqual(report["prohibited_counts"]["process_operations"], 1)

    def test_worker_report_pid_must_match_popen_observation(self) -> None:
        self.assertTrue(
            run_isolation._report_pid_matches_launcher({"pid": 4321}, 4321)
        )
        self.assertFalse(
            run_isolation._report_pid_matches_launcher({"pid": 4322}, 4321)
        )
        self.assertFalse(
            run_isolation._report_pid_matches_launcher({"pid": True}, 1)
        )

    def test_forbidden_target_inside_allowlisted_root_is_rejected(self) -> None:
        value = self.fixture.configuration()
        value["forbidden"]["file"] = str(
            self.fixture.answer_package / "package-canary.txt"
        )
        with self.assertRaisesRegex(
            run_isolation.ConfigurationError, "accidentally authorized"
        ):
            run_isolation.parse_config(value)

    def test_store_physical_inventory_must_exactly_match_allowlist(self) -> None:
        (self.fixture.projector_store / "not-allowlisted.json").write_text(
            "{}\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(
            run_isolation.ConfigurationError, "physical inventory"
        ):
            run_isolation.parse_config(self.fixture.configuration())

    def test_store_physical_inventory_rejects_unallowlisted_empty_directory(self) -> None:
        (self.fixture.projector_store / "not-allowlisted").mkdir()
        with self.assertRaisesRegex(
            run_isolation.ConfigurationError, "physical inventory"
        ):
            run_isolation.parse_config(self.fixture.configuration())

    def test_declared_parent_directories_are_allowed(self) -> None:
        nested_store = self.fixture.projector_store / "nested"
        nested_store.mkdir()
        nested_observations = nested_store / "observations.json"
        (self.fixture.projector_store / "observations.json").replace(
            nested_observations
        )
        nested_output = self.fixture.answer_output / "nested"
        nested_output.mkdir()
        value = self.fixture.configuration()
        value["projector"]["store_allowlist"] = ["nested/observations.json"]
        value["projector"]["store_canary"] = str(nested_observations)
        value["answer"]["sealed_result"] = str(
            nested_output / "sealed-result.json"
        )
        value["answer"]["workload"]["stdout_output"] = (
            "nested/sealed-result.json"
        )
        value["answer"]["workload"]["expected_outputs"] = [
            "nested/sealed-result.json"
        ]

        config = run_isolation.parse_config(value)

        self.assertEqual(
            config.projector.store_allowlist, ("nested/observations.json",)
        )

    def test_symlink_in_staged_input_is_rejected(self) -> None:
        link = self.fixture.answer_bundles / "alias.json"
        try:
            link.symlink_to(self.fixture.answer_bundles / "read-set-a-b.json")
        except OSError as exc:
            self.skipTest(f"symlinks unavailable: {exc}")
        with self.assertRaisesRegex(
            run_isolation.ConfigurationError, "non-regular file|filesystem alias"
        ):
            run_isolation.parse_config(self.fixture.configuration())

    def test_workload_path_escape_is_rejected(self) -> None:
        value = deepcopy(self.fixture.configuration())
        value["answer"]["workload"]["entrypoint"] = "../forbidden.py"
        with self.assertRaisesRegex(run_isolation.ConfigurationError, "canonical"):
            run_isolation.parse_config(value)

    def test_plan_cli_emits_only_non_executed_evidence(self) -> None:
        config_path = self.fixture.root / "isolation-config.json"
        config_path.write_text(
            json.dumps(self.fixture.configuration()), encoding="utf-8"
        )
        output = StringIO()
        with redirect_stdout(output):
            code = run_isolation.main(("plan", "--config", str(config_path)))
        self.assertEqual(code, 0)
        emitted = json.loads(output.getvalue())
        self.assertEqual(emitted["isolation_status"], "NOT_EXECUTED")
        self.assertEqual(emitted["v007_gate_status"], "NOT_EVALUATED")


if __name__ == "__main__":
    unittest.main()
