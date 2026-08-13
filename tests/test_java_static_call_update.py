from __future__ import annotations

from contextlib import closing
from io import StringIO
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from software_world_model.interface.cli import main as management_main
from software_world_model.interface.world_model_runtime import (
    _outer_reachability,
)
from software_world_model.infrastructure.file_read_set_catalog import (
    FileReadSetCatalogStore,
    RootedStructureReadBundleStore,
)
from software_world_model.interface.world_model_http import (
    DynamicCatalogWorldModelRunner,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "validation"
    / "structure_world_model_iteration_006"
    / "fixtures"
)
JAVA_PROFILE = "JAVA_STATIC_CALL_GRAPH@1"
FROZEN_GIT_DATE = "2000-01-01T00:00:00+00:00"


class JavaStaticCallWorkspaceTests(unittest.TestCase):
    """Exercise the exact Git -> Update -> Bundle -> Source-off View chain."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.database = self.root / "authority.sqlite3"
        self.bundle_root = self.root / "bundles"
        self.catalog_root = self.root / "catalog"
        self.repository = self.root / "repository"
        self.repository.mkdir()
        self._install_fixture("r1")
        self.git_environment = {
            **os.environ,
            "GIT_AUTHOR_DATE": FROZEN_GIT_DATE,
            "GIT_COMMITTER_DATE": FROZEN_GIT_DATE,
        }
        self.oracle = json.loads(
            (
                REPOSITORY_ROOT
                / "validation"
                / "structure_world_model_iteration_006"
                / "oracle.json"
            ).read_text(encoding="utf-8")
        )["revisions"]
        self._git("init", "-q", "--object-format=sha1")
        self._git("config", "user.email", "java-workspace@example.com")
        self._git("config", "user.name", "Java Workspace Test")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "r1")
        self.r1 = self._git("rev-parse", "HEAD")
        self._assert_frozen_revision("r1", self.r1)
        self.producer_commit = "6" * 40
        self.producer_tree = "7" * 40

        code, registered = self._management(
            "register-maven-workspace",
            "--idempotency-key",
            "java-workspace-register",
            "--source-target",
            str(self.repository),
            "--display-name",
            "Java Static Call Fixture",
            "--canonical-system-key",
            "fixture:java-static-call",
            "--source-root",
            "src/main/java",
            "--knowledge-profile",
            JAVA_PROFILE,
            "--actor",
            "test",
            "--correlation-ref",
            "java-workspace-register",
        )
        self.assertEqual(code, 0, registered)
        self.assertEqual(
            registered["workspace"]["knowledge_profile_ref"], JAVA_PROFILE
        )
        self.assertEqual(
            registered["workspace"]["source_root"], "src/main/java"
        )
        self.workspace_id = registered["workspace"]["workspace_id"]
        self.scope_id = registered["workspace"]["scope"]["id"]

    def _install_fixture(self, name: str) -> None:
        source = self.repository / "src"
        if source.exists():
            shutil.rmtree(source)
        shutil.copytree(FIXTURE_ROOT / name / "src", source)

    def _commit_fixture(self, name: str) -> str:
        self._install_fixture(name)
        self._git("add", "-A")
        self._git("commit", "-q", "-m", name)
        revision = self._git("rev-parse", "HEAD")
        self._assert_frozen_revision(name, revision)
        return revision

    def _assert_frozen_revision(self, name: str, revision: str) -> None:
        expected = self.oracle[name]
        self.assertEqual(revision, expected["git_commit"])
        self.assertEqual(
            self._git("rev-parse", f"{revision}^{{tree}}"),
            expected["git_tree"],
        )

    def _git(self, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            env=self.git_environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    def _management(self, *arguments: str) -> tuple[int, dict[str, object]]:
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
                self.producer_commit,
                "--producer-tree",
                self.producer_tree,
                *arguments,
            ],
            stdout=output,
        )
        return code, json.loads(output.getvalue())

    def _source_off(self, *arguments: str) -> tuple[int, dict[str, object], str]:
        completed = subprocess.run(
            (
                sys.executable,
                "-m",
                "software_world_model.interface.read_set_catalog_cli",
                "--catalog-root",
                str(self.catalog_root),
                "--bundle-root",
                str(self.bundle_root),
                *arguments,
            ),
            cwd=REPOSITORY_ROOT,
            env=os.environ,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        document = json.loads(completed.stdout) if completed.stdout else {}
        return completed.returncode, document, completed.stderr

    def _update(self, revision: str, key: str) -> dict[str, object]:
        code, result = self._management(
            "update-maven-workspace",
            "--workspace-id",
            self.workspace_id,
            "--repository-revision",
            revision,
            "--idempotency-key",
            key,
            "--correlation-ref",
            key,
        )
        self.assertEqual(code, 0, result)
        return result

    @staticmethod
    def _method_signature(entity: dict[str, object]) -> str:
        fields = entity["root_fields"]
        parameters = ",".join(fields["parameter_types"])
        return (
            f"{fields['declaring_type_qualified_name']}#"
            f"{fields['method_name']}({parameters})"
        )

    def _view(
        self, read_set_id: str, *arguments: str
    ) -> dict[str, object]:
        code, result, errors = self._source_off(
            "view", "--read-set-id", read_set_id, "--", *arguments
        )
        self.assertEqual((code, errors), (0, ""), (arguments, errors))
        return result

    def test_r1_r2_r3_atomic_update_and_source_off_behavior_views(self) -> None:
        first = self._update(self.r1, "java-workspace-r1")
        self.assertEqual(
            first["workflow"], "STRUCTURE_WORKSPACE_FULL_REBUILD@1"
        )
        self.assertEqual(first["version"]["availability"], "QUERYABLE")
        self.assertIsNone(first["comparison_read_set"])
        first_owner = first["snapshot_owner_result"]
        self.assertEqual(first_owner["coverage"]["profile_ref"], JAVA_PROFILE)
        self.assertTrue(first_owner["java_report"]["complete"])
        self.assertEqual(first_owner["java_report"]["source_file_count"], 2)
        self.assertEqual(first_owner["java_report"]["type_count"], 2)
        self.assertEqual(first_owner["java_report"]["method_count"], 4)
        self.assertEqual(first_owner["java_report"]["call_relation_count"], 3)
        self.assertEqual(first_owner["dependencies"], [])
        self.assertEqual(first_owner["exclusions"], [])

        r2 = self._commit_fixture("r2")
        second = self._update(r2, "java-workspace-r2")
        self.assertEqual(second["version"]["ordinal"], 2)
        self.assertIsNotNone(second["comparison_read_set"])
        second_owner = second["snapshot_owner_result"]
        self.assertEqual(second_owner["java_report"]["method_count"], 5)
        first_methods = {
            self._method_signature(item): item
            for item in first_owner["entities"]
            if item["entity_type"] == "JAVA_METHOD"
        }
        second_methods = {
            self._method_signature(item): item
            for item in second_owner["entities"]
            if item["entity_type"] == "JAVA_METHOD"
        }
        for signature in set(first_methods) & set(second_methods):
            self.assertEqual(
                first_methods[signature]["root_id"],
                second_methods[signature]["root_id"],
            )

        r3 = self._commit_fixture("r3-unsupported")
        code, rejected = self._management(
            "update-maven-workspace",
            "--workspace-id",
            self.workspace_id,
            "--repository-revision",
            r3,
            "--idempotency-key",
            "java-workspace-r3",
            "--correlation-ref",
            "java-workspace-r3",
        )
        self.assertEqual(code, 2, rejected)
        self.assertEqual(
            rejected["details"]["reason_code"],
            "JAVA_CALL_TARGET_AMBIGUOUS",
        )
        code, versions = self._management(
            "list-maven-workspace-versions", "--workspace-id", self.workspace_id
        )
        self.assertEqual(code, 0, versions)
        self.assertEqual(
            [item["repository_revision"] for item in versions["versions"]],
            [self.r1, r2],
        )

        files = RootedStructureReadBundleStore(self.bundle_root)
        store = FileReadSetCatalogStore(self.catalog_root, files)
        pointer = store.read_pointer()
        self.assertIsNotNone(pointer)
        catalog = store.read_catalog(pointer, verify_files=True)
        java_dataset = DynamicCatalogWorldModelRunner._dataset(
            pointer, catalog.entries[-1]
        )
        self.assertEqual(java_dataset["profile_refs"], [JAVA_PROFILE])
        self.assertIn("Java static-call", java_dataset["description"])
        self.assertIn("runtime dispatch", java_dataset["coverage"])

        first_snapshot = first["version"]["snapshot_id"]
        second_snapshot = second["version"]["snapshot_id"]
        first_read_set = first["single_read_set"]["read_set_id"]
        comparison_read_set = second["comparison_read_set"]["read_set_id"]
        flow_type = next(
            item
            for item in first_owner["entities"]
            if item["entity_type"] == "JAVA_TYPE"
            and item["state_fields"]["simple_name"] == "FlowService"
        )
        start = first_methods["com.acme.flow.FlowService#start(String)"]
        finish = first_methods["com.acme.flow.FlowService#finish(String)"]

        with closing(sqlite3.connect(self.database)) as connection:
            authority_before = {
                "current": connection.execute(
                    "SELECT current_snapshot_id, current_revision "
                    "FROM knw_structure_snapshot_roots WHERE scope_id = ?",
                    (self.scope_id,),
                ).fetchone(),
                "update_attempts": connection.execute(
                    "SELECT COUNT(*) FROM app_maven_structure_update_attempts"
                ).fetchone()[0],
                "workspace_attempts": connection.execute(
                    "SELECT COUNT(*) FROM app_maven_workspace_attempts"
                ).fetchone()[0],
                "source_operations": connection.execute(
                    "SELECT COUNT(*) FROM src_operation_roots"
                ).fetchone()[0],
            }
        outer, forbidden = _outer_reachability(self.database)
        workspace_probe = outer["workspaces"][0]
        self.assertEqual(workspace_probe["knowledge_profile_ref"], JAVA_PROFILE)
        self.assertTrue(workspace_probe["source_probe"].endswith("Audit.java"))
        self.assertEqual(forbidden["source_0000"], Path(workspace_probe["source_probe"]))

        hidden_database = self.root / "authority.unmounted"
        hidden_repository = self.root / "repository.unmounted"
        self.database.rename(hidden_database)
        self.repository.rename(hidden_repository)
        try:
            methods = self._view(
                first_read_set,
                "methods",
                "--java-type-snapshot-id",
                first_snapshot,
                "--java-type-root-id",
                flow_type["root_id"],
                "--java-type-state-id",
                flow_type["state_id"],
            )
            self.assertEqual(methods["operation"], "DECLARED_METHOD_INVENTORY")
            self.assertEqual(methods["payload"]["method_count"], 3)

            neighborhood = self._view(
                first_read_set,
                "neighborhood",
                "--entity-snapshot-id",
                first_snapshot,
                "--entity-root-id",
                start["root_id"],
                "--entity-state-id",
                start["state_id"],
                "--direction",
                "OUTGOING",
                "--predicate",
                "CALLS",
            )
            self.assertEqual(neighborhood["operation"], "DIRECT_NEIGHBORHOOD")
            self.assertEqual(len(neighborhood["payload"]["relations"]), 2)

            path = self._view(
                first_read_set,
                "path-exists",
                "--source-snapshot-id",
                first_snapshot,
                "--source-root-id",
                start["root_id"],
                "--source-state-id",
                start["state_id"],
                "--target-snapshot-id",
                first_snapshot,
                "--target-root-id",
                finish["root_id"],
                "--target-state-id",
                finish["state_id"],
                "--predicate",
                "CALLS",
            )
            self.assertTrue(path["payload"]["exists"])
            self.assertEqual(
                len(path["payload"]["path"]["relation_root_ids"]), 2
            )

            diff = self._view(
                comparison_read_set,
                "diff",
                "--base-snapshot-id",
                first_snapshot,
                "--target-snapshot-id",
                second_snapshot,
            )
            self.assertEqual(diff["operation"], "ORDERED_SNAPSHOT_DIFF")
            self.assertEqual(diff["payload"]["entities"]["counts"]["added"], 1)
            # One DECLARES_METHOD fact plus two CALLS facts are new in R2.
            self.assertEqual(diff["payload"]["relations"]["counts"]["added"], 3)
            self.assertEqual(diff["payload"]["relations"]["counts"]["removed"], 1)
        finally:
            hidden_database.rename(self.database)
            hidden_repository.rename(self.repository)

        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(
                {
                    "current": connection.execute(
                        "SELECT current_snapshot_id, current_revision "
                        "FROM knw_structure_snapshot_roots WHERE scope_id = ?",
                        (self.scope_id,),
                    ).fetchone(),
                    "update_attempts": connection.execute(
                        "SELECT COUNT(*) FROM app_maven_structure_update_attempts"
                    ).fetchone()[0],
                    "workspace_attempts": connection.execute(
                        "SELECT COUNT(*) FROM app_maven_workspace_attempts"
                    ).fetchone()[0],
                    "source_operations": connection.execute(
                        "SELECT COUNT(*) FROM src_operation_roots"
                    ).fetchone()[0],
                },
                authority_before,
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
