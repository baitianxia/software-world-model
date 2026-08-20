from __future__ import annotations

from contextlib import redirect_stderr
from io import BytesIO, StringIO
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from software_world_model.cross_cutting import (
    Digest,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.infrastructure.file_read_set_catalog import (
    FileReadSetCatalogStore,
    RootedStructureReadBundleStore,
)
from software_world_model.interface.cli import main as management_main
from software_world_model.interface.world_model_browser import (
    PublicRunnerError,
    WorldModelBrowserApplication,
)
from software_world_model.interface.world_model_http import (
    AuthorityState,
    DynamicCatalogWorldModelRunner,
    SqliteAuthorityStateProbe,
    _entrypoint as world_model_entrypoint,
    main as world_model_main,
)
from software_world_model.interface.world_model_runtime import (
    GRANT_SCHEMA,
    SealedWorldModelExecutor,
)
from software_world_model.interface import world_model_runtime
from tests.test_maven_structure_cli import MODULE_POM, ROOT_POM


_RESULT_ID = "structure_view_result_" + "a" * 32
_DIGEST = "sha256:" + "b" * 64
_COMMIT = "c" * 40
_TREE = "d" * 40


class _Executor:
    def __init__(
        self,
        *,
        provider_call_count: int = 1,
        dispatch_policy: str = "ONE_CALL_PER_QUESTION_NO_HIDDEN_RETRY",
    ) -> None:
        self.executions = []
        self.citations = []
        self.provider_call_count = provider_call_count
        self.dispatch_policy = dispatch_policy

    def health(self):
        return {
            "status": "ready",
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "evaluation_subject_status": "CANDIDATE",
            "evaluation_subject_commit": _COMMIT,
            "evaluation_subject_tree": _TREE,
            "evaluation_grant_digest": _DIGEST,
            "deterministic_qualification_digest": _DIGEST,
            "held_out_suite_digest": _DIGEST,
            "independent_evaluator_digest": _DIGEST,
            "startup_preflight_digest": _DIGEST,
            "startup_receipt_digest": _DIGEST,
            "stage_manifest_digest": _DIGEST,
            "launcher_manifest_digest": _DIGEST,
            "provider_subject_digest": _DIGEST,
            "gateway_authorization_receipt_digest": _DIGEST,
            "dispatch_policy": self.dispatch_policy,
            "production_activation": "NOT_EXECUTED",
        }

    def execute(self, *, request_id, read_set, question):
        self.executions.append((request_id, read_set, question))
        registration = read_set.registration
        return {
            "request_id": request_id,
            "read_set_id": registration.read_set_id.value,
            "question": question,
            "mode": "WORLD_MODEL",
            "environment": "EVALUATION_ONLY",
            "evaluation_subject_status": "CANDIDATE",
            "evaluation_subject_commit": _COMMIT,
            "evaluation_subject_tree": _TREE,
            "page_digest": _DIGEST,
            "page": {
                "mode": "WORLD_MODEL",
                "environment": "EVALUATION_ONLY",
                "evaluation_only": True,
                "implementation_commit": _COMMIT,
                "request": {"original_question": question},
                "read_binding": {
                    "read_set_digest": registration.read_set_digest.value,
                    "snapshots": [
                        {"snapshot_id": item.snapshot_id.value}
                        for item in registration.snapshot_bindings
                    ],
                },
                "answer": {"body": "verified", "claims": []},
                "authority_chain": {
                    "stages": [{"stage": f"STAGE_{index}"} for index in range(10)]
                },
            },
            "citations": [
                {
                    "result_id": _RESULT_ID,
                    "seal_digest": _DIGEST,
                    "projection_digest": _DIGEST,
                    "url": (
                        f"/v1/world-model/requests/{request_id}/"
                        f"citations/{_RESULT_ID}"
                    ),
                }
            ],
            "execution": {
                "attempt_count": 1,
                "provider_call_count": self.provider_call_count,
                "network_operation_count": self.provider_call_count,
                "selective_retry_count": 0,
                "source_access_count": 0,
                "evidence_payload_access_count": 0,
            },
            "production_activation": "NOT_EXECUTED",
        }

    def citation(self, *, request_id, result_id):
        self.citations.append((request_id, result_id))
        return {
            "request_id": request_id,
            "result_id": result_id,
            "seal_digest": _DIGEST,
            "projection_digest": _DIGEST,
            "environment": "EVALUATION_ONLY",
            "network_operation_count": 0,
            "answer_return_port": False,
            "citation_projection": {"citations": []},
            "production_activation": "NOT_EXECUTED",
        }


class _ChangingProbe:
    def __init__(self) -> None:
        self.value = 0

    def capture(self):
        self.value += 1
        return AuthorityState(
            digest=Digest("sha256:" + f"{self.value:064x}"),
            update_attempt_count=self.value,
            bundle_receipt_count=0,
            source_operation_revision_count=0,
            current_snapshot_count=0,
        )


class _FailingExecutor(_Executor):
    def execute(self, *, request_id, read_set, question):
        raise RuntimeError("deterministic executor failure")


class _WrongIdentityExecutor(_Executor):
    def execute(self, *, request_id, read_set, question):
        result = dict(
            super().execute(
                request_id=request_id,
                read_set=read_set,
                question=question,
            )
        )
        result["evaluation_subject_tree"] = "e" * 40
        return result


class DynamicWorldModelHttpTests(unittest.TestCase):
    def test_health_accepts_bounded_four_to_six_dispatch_policy(self) -> None:
        health = _Executor().health()
        health["dispatch_policy"] = (
            "FOUR_TO_SIX_ORDERED_CALLS_PER_QUESTION_NO_HIDDEN_RETRY"
        )

        self.assertEqual(
            DynamicCatalogWorldModelRunner._validated_health(health),
            health,
        )

    def test_result_call_count_follows_bounded_startup_dispatch_policy(self) -> None:
        policy = "FOUR_TO_SIX_ORDERED_CALLS_PER_QUESTION_NO_HIDDEN_RETRY"
        for provider_call_count in (4, 5, 6):
            with self.subTest(provider_call_count=provider_call_count):
                runner = DynamicCatalogWorldModelRunner(
                    catalog_store=self.catalog_store,
                    bundle_store=self.bundle_store,
                    executor=_Executor(
                        provider_call_count=provider_call_count,
                        dispatch_policy=policy,
                    ),
                    authority_probe=self.probe,
                )
                result = runner.ask(
                    request_id=f"wm-bounded-{provider_call_count}",
                    dataset_id=self.read_set_id,
                    question="列出所有 reactor 子模块。",
                )
                self.assertEqual(
                    result["execution"]["provider_call_count"],
                    provider_call_count,
                )

        invalid = DynamicCatalogWorldModelRunner(
            catalog_store=self.catalog_store,
            bundle_store=self.bundle_store,
            executor=_Executor(provider_call_count=3, dispatch_policy=policy),
            authority_probe=self.probe,
        )
        with self.assertRaises(PublicRunnerError) as raised:
            invalid.ask(
                request_id="wm-bounded-invalid",
                dataset_id=self.read_set_id,
                question="列出所有 reactor 子模块。",
            )
        self.assertEqual(raised.exception.code, "WORLD_MODEL_RESULT_INVALID")

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.database = self.root / "authority.sqlite3"
        self.catalog_root = self.root / "catalog"
        self.bundle_root = self.root / "bundles"
        self.repository = self.root / "repository"
        (self.repository / "module-a").mkdir(parents=True)
        (self.repository / "pom.xml").write_text(ROOT_POM, encoding="utf-8")
        (self.repository / "module-a" / "pom.xml").write_text(
            MODULE_POM, encoding="utf-8"
        )
        self._git("init", "-q")
        self._git("config", "user.email", "world-model-http@example.com")
        self._git("config", "user.name", "World Model HTTP Test")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "r1")
        self.revision = self._git("rev-parse", "HEAD")
        registered = self._management(
            "register-maven-workspace",
            "--idempotency-key",
            "http-workspace-register",
            "--source-target",
            str(self.repository),
            "--display-name",
            "Dynamic HTTP Fixture",
            "--canonical-system-key",
            "fixture:dynamic-http",
            "--root-pom",
            "pom.xml",
            "--actor",
            "test",
            "--correlation-ref",
            "http-workspace-register",
        )
        self.workspace_id = registered["workspace"]["workspace_id"]
        self._management(
            "update-maven-workspace",
            "--workspace-id",
            self.workspace_id,
            "--repository-revision",
            self.revision,
            "--idempotency-key",
            "http-r1",
            "--correlation-ref",
            "http-r1",
        )
        self.bundle_store = RootedStructureReadBundleStore(self.bundle_root)
        self.catalog_store = FileReadSetCatalogStore(
            self.catalog_root, self.bundle_store
        )
        self.probe = SqliteAuthorityStateProbe(self.database)
        self.executor = _Executor()
        self.runner = DynamicCatalogWorldModelRunner(
            catalog_store=self.catalog_store,
            bundle_store=self.bundle_store,
            executor=self.executor,
            authority_probe=self.probe,
        )
        self.read_set_id = self.runner.datasets()[0]["read_set_id"]

    def _git(self, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    def _management(self, *arguments: str):
        output = StringIO()
        code = management_main(
            [
                "--database",
                str(self.database),
                "--bundle-root",
                str(self.bundle_root),
                "--catalog-root",
                str(self.catalog_root),
                "--producer-commit",
                "0" * 40,
                "--producer-tree",
                "1" * 40,
                *arguments,
            ],
            stdout=output,
        )
        value = json.loads(output.getvalue())
        self.assertEqual(code, 0, value)
        return value

    def _publish_second_revision(self) -> str:
        root = ROOT_POM.replace(
            "<modules><module>module-a</module></modules>",
            "<modules><module>module-a</module><module>module-b</module></modules>",
        )
        (self.repository / "pom.xml").write_text(root, encoding="utf-8")
        (self.repository / "module-b").mkdir()
        (self.repository / "module-b" / "pom.xml").write_text(
            MODULE_POM.replace(
                "<artifactId>module-a</artifactId>",
                "<artifactId>module-b</artifactId>",
            ),
            encoding="utf-8",
        )
        self._git("add", ".")
        self._git("commit", "-q", "-m", "r2")
        revision = self._git("rev-parse", "HEAD")
        self._management(
            "update-maven-workspace",
            "--workspace-id",
            self.workspace_id,
            "--repository-revision",
            revision,
            "--idempotency-key",
            "http-r2",
            "--correlation-ref",
            "http-r2",
        )
        return revision

    @staticmethod
    def _http(application, method: str, path: str, payload=None):
        body = json.dumps(payload).encode("utf-8") if payload is not None else b""
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        response = b"".join(
            application(
                {
                    "REQUEST_METHOD": method,
                    "PATH_INFO": path,
                    "CONTENT_TYPE": "application/json" if payload is not None else "",
                    "CONTENT_LENGTH": str(len(body)),
                    "wsgi.input": BytesIO(body),
                },
                start_response,
            )
        )
        try:
            value = json.loads(response)
        except json.JSONDecodeError:
            value = response.decode("utf-8")
        return captured["status"], value

    def test_catalog_datasets_disclose_exact_read_identity_without_paths(self) -> None:
        datasets = self.runner.datasets()
        self.assertEqual(len(datasets), 1)
        dataset = datasets[0]
        self.assertEqual(dataset["id"], self.read_set_id)
        self.assertEqual(dataset["workspace_id"], self.workspace_id)
        self.assertEqual(dataset["source_revisions"], [self.revision])
        self.assertEqual(dataset["profile_refs"], ["MAVEN_REACTOR_STRUCTURE@1"])
        self.assertTrue(dataset["read_only"])
        encoded = json.dumps(dataset)
        self.assertNotIn(str(self.repository), encoded)
        self.assertNotIn(str(self.database), encoded)
        self.assertNotIn("pom.xml", encoded)

    def test_question_uses_exact_bundle_and_preserves_all_authority_state(self) -> None:
        before = self.probe.capture()
        result = self.runner.ask(
            request_id="wm-dynamic-1",
            dataset_id=self.read_set_id,
            question="列出所有 reactor 子模块。",
        )
        after = self.probe.capture()

        self.assertEqual(before, after)
        self.assertEqual(result["read_set_id"], self.read_set_id)
        self.assertTrue(result["authority_fence"]["unchanged"])
        self.assertEqual(result["catalog_binding"]["catalog_digest"], result["read_set"]["catalog_digest"])
        _, resolved, _ = self.executor.executions[0]
        self.assertEqual(resolved.registration.read_set_id.value, self.read_set_id)
        self.assertTrue(resolved.ordered_bundle.is_file())
        self.assertEqual(len(resolved.snapshot_bundles), 1)
        self.assertFalse(hasattr(resolved, "repository_locator"))

        citation = self.runner.citation(
            request_id="wm-dynamic-1", result_id=_RESULT_ID
        )
        self.assertEqual(citation["result_id"], _RESULT_ID)
        self.assertEqual(citation["network_operation_count"], 0)

    def test_ordered_read_set_is_discovered_after_catalog_refresh(self) -> None:
        second_revision = self._publish_second_revision()

        ordered = next(
            item for item in self.runner.datasets()
            if item["snapshot_count"] == 2
        )
        self.assertEqual(
            ordered["source_revisions"],
            [self.revision, second_revision],
        )
        self.assertEqual(ordered["modality"], "ORDERED_COMPARISON")
        result = self.runner.ask(
            request_id="wm-ordered-r1-r2",
            dataset_id=ordered["read_set_id"],
            question="比较两个 exact Snapshot 的 reactor 模块变化。",
        )

        self.assertEqual(result["read_set_id"], ordered["read_set_id"])
        _, resolved, _ = self.executor.executions[0]
        self.assertEqual(len(resolved.snapshot_bundles), 2)
        self.assertEqual(
            [item.snapshot_id.value for item in resolved.registration.snapshot_bindings],
            ordered["snapshot_ids"],
        )

    def test_product_http_contract_requires_read_set_id_only(self) -> None:
        application = WorldModelBrowserApplication(
            self.runner, selector_field="read_set_id"
        )
        status, result = self._http(
            application,
            "POST",
            "/v1/world-model/questions",
            {
                "request_id": "wm-http-1",
                "read_set_id": self.read_set_id,
                "question": "列出所有模块。",
            },
        )
        self.assertEqual(status, "200 OK")
        self.assertEqual(result["read_set_id"], self.read_set_id)

        legacy_status, legacy = self._http(
            application,
            "POST",
            "/v1/world-model/questions",
            {
                "request_id": "wm-http-2",
                "dataset_id": self.read_set_id,
                "question": "列出所有模块。",
            },
        )
        self.assertEqual(legacy_status, "400 Bad Request")
        self.assertEqual(legacy["error"], "INVALID_ARGUMENT")

        extra_status, _ = self._http(
            application,
            "POST",
            "/v1/world-model/questions",
            {
                "request_id": "wm-http-3",
                "read_set_id": self.read_set_id,
                "question": "列出所有模块。",
                "repository_path": str(self.repository),
            },
        )
        self.assertEqual(extra_status, "400 Bad Request")

        script_status, script = self._http(
            application, "GET", "/assets/world-model.js"
        )
        self.assertEqual(script_status, "200 OK")
        self.assertIn('const selectorField="read_set_id"', script)

    def test_question_fails_closed_if_authority_fence_changes(self) -> None:
        runner = DynamicCatalogWorldModelRunner(
            catalog_store=self.catalog_store,
            bundle_store=self.bundle_store,
            executor=_Executor(),
            authority_probe=_ChangingProbe(),
        )
        with self.assertRaises(PublicRunnerError) as raised:
            runner.ask(
                request_id="wm-mutates",
                dataset_id=self.read_set_id,
                question="列出模块。",
            )
        self.assertEqual(raised.exception.code, "QUESTION_MUTATED_AUTHORITY")

    def test_authority_drift_takes_precedence_over_executor_failure(self) -> None:
        runner = DynamicCatalogWorldModelRunner(
            catalog_store=self.catalog_store,
            bundle_store=self.bundle_store,
            executor=_FailingExecutor(),
            authority_probe=_ChangingProbe(),
        )
        with self.assertRaises(PublicRunnerError) as raised:
            runner.ask(
                request_id="wm-failure-and-drift",
                dataset_id=self.read_set_id,
                question="列出模块。",
            )
        self.assertEqual(raised.exception.code, "QUESTION_MUTATED_AUTHORITY")

    def test_result_identity_must_match_the_startup_subject(self) -> None:
        runner = DynamicCatalogWorldModelRunner(
            catalog_store=self.catalog_store,
            bundle_store=self.bundle_store,
            executor=_WrongIdentityExecutor(),
            authority_probe=self.probe,
        )
        with self.assertRaises(PublicRunnerError) as raised:
            runner.ask(
                request_id="wm-wrong-tree",
                dataset_id=self.read_set_id,
                question="列出模块。",
            )
        self.assertEqual(raised.exception.code, "WORLD_MODEL_RESULT_INVALID")

    def test_unknown_read_set_and_reused_request_fail_closed(self) -> None:
        with self.assertRaises(PublicRunnerError) as missing:
            self.runner.ask(
                request_id="wm-missing",
                dataset_id="read_set_" + "f" * 32,
                question="列出模块。",
            )
        self.assertEqual(missing.exception.code, "READ_SET_NOT_FOUND")

        self.runner.ask(
            request_id="wm-once",
            dataset_id=self.read_set_id,
            question="列出模块。",
        )
        with self.assertRaises(PublicRunnerError) as reused:
            self.runner.ask(
                request_id="wm-once",
                dataset_id=self.read_set_id,
                question="再次列出模块。",
            )
        self.assertEqual(reused.exception.code, "REQUEST_ID_CONFLICT")

    def test_live_executor_rejects_missing_disclosure_before_network(self) -> None:
        authorization_core = {
            "status": "NOT_AUTHORIZED",
            "authorized_by": "user",
            "authorized_at": "2026-08-11T19:32:39+08:00",
            "authorization_ref": "user-message:continue-development-only",
            "payload_boundary": (
                "ORIGINAL_QUESTION_AND_NO_PAYLOAD_PUBLISHED_STRUCTURE"
            ),
        }
        authorization = {
            **authorization_core,
            "document_digest": digest_of(
                [
                    "SWM-WORLD-MODEL-DISCLOSURE-AUTHORIZATION@1",
                    authorization_core,
                ]
            ).value,
        }
        core = {
            "schema": GRANT_SCHEMA,
            "environment": "EVALUATION_ONLY",
            "live_dispatch_authorized": False,
            "disclosure_authorization": authorization,
            "evaluation_subject": {},
            "provider": {},
            "launcher_files": {},
            "forbidden_inputs": {},
            "production_activation": "NOT_EXECUTED",
        }
        grant = {
            **core,
            "document_digest": digest_of([GRANT_SCHEMA, core]).value,
        }
        grant_path = self.root / "unauthorized-grant.json"
        grant_path.write_bytes(canonical_json_bytes(grant))
        with patch(
            "software_world_model.interface.world_model_runtime._provision_provider_socket"
        ) as provision:
            with self.assertRaises(PublicRunnerError) as raised:
                SealedWorldModelExecutor.from_grant(
                    grant_path=grant_path,
                    authority_database=self.database,
                    session_root=self.root / "blocked-session",
                    socket_root=self.root / "blocked-sockets",
                    timeout_seconds=30,
                )
        self.assertEqual(raised.exception.code, "LIVE_DISPATCH_NOT_AUTHORIZED")
        provision.assert_not_called()
        self.assertFalse((self.root / "blocked-session").exists())

        stderr = StringIO()
        with redirect_stderr(stderr):
            exit_code = world_model_entrypoint(
                [
                    "--database", str(self.database),
                    "--catalog-root", str(self.catalog_root),
                    "--bundle-root", str(self.bundle_root),
                    "--evaluation-grant", str(grant_path),
                    "--session-root", str(self.root / "blocked-session"),
                    "--socket-root", str(self.root / "blocked-sockets"),
                ]
            )
        self.assertEqual(exit_code, 1)
        self.assertEqual(
            json.loads(stderr.getvalue())["error"],
            "LIVE_DISPATCH_NOT_AUTHORIZED",
        )
        self.assertFalse((self.root / "blocked-session").exists())

    def test_cli_rejects_non_loopback_before_loading_grant(self) -> None:
        with self.assertRaises(ValueError):
            world_model_main(
                [
                    "--database", str(self.database),
                    "--catalog-root", str(self.catalog_root),
                    "--bundle-root", str(self.bundle_root),
                    "--evaluation-grant", str(self.root / "missing.json"),
                    "--host", "0.0.0.0",
                ]
            )

    def test_runtime_rejects_symlink_capabilities_and_citation_traversal(self) -> None:
        target = self.root / "target.json"
        target.write_text("{}", encoding="utf-8")
        link = self.root / "target-link.json"
        link.symlink_to(target)
        with self.assertRaises(ValueError):
            world_model_runtime._canonical_file(link, "test capability")

        run_root = self.root / "projection-run"
        run_root.mkdir()
        seals = self.root / "citation-seals"
        seals.mkdir()
        with self.assertRaisesRegex(RuntimeError, "not a basename"):
            world_model_runtime._project_all_citations(
                run_root=run_root,
                answer_summary={
                    "citation_seals": [
                        {
                            "file_name": "../target.json",
                            "file_digest": _DIGEST,
                        }
                    ]
                },
                citation_seals=seals,
                authority_database=self.database,
                packages={},
                forbidden={},
                runtime={},
                timeout_seconds=1,
            )

    def test_product_runtime_has_no_validation_import_or_fixed_dataset(self) -> None:
        interface_root = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "software_world_model"
            / "interface"
        )
        for name in ("world_model_http.py", "world_model_runtime.py"):
            source = (interface_root / name).read_text(encoding="utf-8")
            self.assertNotIn("from validation", source)
            self.assertNotIn("import validation", source)
            self.assertNotIn("ORDERED_A_B", source)
            self.assertNotIn('"EXACT_B"', source)
            self.assertNotIn("EXACT_FIXTURE_VALID", source)
            self.assertNotIn("validation-projects/mall", source)


if __name__ == "__main__":
    unittest.main()
