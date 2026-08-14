from __future__ import annotations

from io import StringIO
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from software_world_model.infrastructure.file_read_set_catalog import (
    FileReadSetCatalogStore,
    RootedStructureReadBundleStore,
)
from software_world_model.interface.cli import main as management_main


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = (
    REPOSITORY_ROOT
    / "validation"
    / "structure_world_model_iteration_007"
    / "fixtures"
    / "development"
)
JAVA_SEMANTICS_PROFILE = "JAVA_SOURCE_SEMANTICS@1"
FROZEN_GIT_DATE = "2000-01-01T00:00:00+00:00"


class JavaSourceSemanticsWorkspaceTests(unittest.TestCase):
    """Exercise exact Git -> Update -> no-payload Bundle for ITER-007."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.database = self.root / "authority.sqlite3"
        self.bundle_root = self.root / "bundles"
        self.catalog_root = self.root / "catalog"
        self.repository = self.root / "repository"
        shutil.copytree(FIXTURE_ROOT, self.repository)
        self.git_environment = {
            **os.environ,
            "GIT_AUTHOR_DATE": FROZEN_GIT_DATE,
            "GIT_COMMITTER_DATE": FROZEN_GIT_DATE,
        }
        self._git("init", "-q", "--object-format=sha1")
        self._git("config", "user.email", "semantics-workspace@example.com")
        self._git("config", "user.name", "Semantics Workspace Test")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "visible-development")
        self.revision = self._git("rev-parse", "HEAD")

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
                "6" * 40,
                "--producer-tree",
                "7" * 40,
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

    def test_workspace_update_publishes_restartable_no_payload_bundle(self) -> None:
        code, registered = self._management(
            "register-maven-workspace",
            "--idempotency-key",
            "java-semantics-register",
            "--source-target",
            str(self.repository),
            "--display-name",
            "Java Source Semantics Fixture",
            "--canonical-system-key",
            "fixture:java-source-semantics",
            "--source-root",
            "src/main/java",
            "--knowledge-profile",
            JAVA_SEMANTICS_PROFILE,
            "--actor",
            "test",
            "--correlation-ref",
            "java-semantics-register",
        )
        self.assertEqual(code, 0, registered)
        workspace_id = registered["workspace"]["workspace_id"]

        code, updated = self._management(
            "update-maven-workspace",
            "--workspace-id",
            workspace_id,
            "--repository-revision",
            self.revision,
            "--idempotency-key",
            "java-semantics-update",
            "--correlation-ref",
            "java-semantics-update",
        )
        self.assertEqual(code, 0, updated)
        self.assertEqual(updated["workflow"], "STRUCTURE_WORKSPACE_FULL_REBUILD@1")
        self.assertEqual(updated["version"]["availability"], "QUERYABLE")
        owner = updated["snapshot_owner_result"]
        self.assertEqual(owner["coverage"]["profile_ref"], JAVA_SEMANTICS_PROFILE)
        report = owner["java_semantics_report"]
        self.assertTrue(report["complete"])
        self.assertEqual(report["source_file_count"], 1)
        self.assertEqual(report["method_count"], 3)
        self.assertEqual(report["state_slot_count"], 1)
        self.assertEqual(report["implementation_atom_count"], 8)
        self.assertEqual(report["legacy_call_relation_count"], 2)

        bundle_store = RootedStructureReadBundleStore(self.bundle_root)
        catalog_store = FileReadSetCatalogStore(self.catalog_root, bundle_store)
        pointer = catalog_store.read_pointer()
        self.assertIsNotNone(pointer)
        catalog = catalog_store.read_catalog(pointer, verify_files=True)
        entry = catalog.entries[-1]
        self.assertEqual(
            entry.snapshot_bindings[0].coverages[0].profile_ref,
            JAVA_SEMANTICS_PROFILE,
        )
        snapshot_file = next(
            item for item in entry.file_manifest if item.role.value == "SNAPSHOT"
        )
        bundle, file_digest = bundle_store.read_snapshot(snapshot_file.locator)
        self.assertEqual(file_digest, snapshot_file.file_digest)
        self.assertEqual(bundle.coverages[0].root.profile_ref, JAVA_SEMANTICS_PROFILE)
        self.assertEqual(
            sum(
                item.root.entity_type.value == "JAVA_IMPLEMENTATION_ATOM"
                for item in bundle.entities
            ),
            8,
        )
        serialized = json.dumps(bundle.document(), ensure_ascii=False, sort_keys=True)
        self.assertNotIn("if (!credentialsValid)", serialized)
        self.assertNotIn("多字节字符只用于验证", serialized)
        self.assertNotIn("return issueSession()", serialized)

        read_set_id = updated["single_read_set"]["read_set_id"]
        snapshot_id = updated["version"]["snapshot_id"]
        hidden_database = self.root / "authority.unmounted"
        hidden_repository = self.root / "repository.unmounted"
        self.database.rename(hidden_database)
        self.repository.rename(hidden_repository)
        try:
            code, candidates, errors = self._source_off(
                "view",
                "--read-set-id",
                read_set_id,
                "--",
                "implementation-candidates",
                "--snapshot-id",
                snapshot_id,
                "--search-term",
                "credentials",
                "--limit",
                "10",
            )
            self.assertEqual((code, errors), (0, ""), errors)
            self.assertEqual(candidates["payload"]["candidate_count"], 1)
            method = candidates["payload"]["candidates"][0]["method"]

            code, implementation, errors = self._source_off(
                "view",
                "--read-set-id",
                read_set_id,
                "--",
                "method-implementation",
                "--method-snapshot-id",
                snapshot_id,
                "--method-root-id",
                method["root_id"],
                "--method-state-id",
                method["state_id"],
            )
            self.assertEqual((code, errors), (0, ""), errors)
            self.assertEqual(implementation["payload"]["query_status"], "SUPPORTED")
            self.assertEqual(
                len(implementation["payload"]["ordered_atoms"]),
                6,
            )
            self.assertEqual(len(implementation["payload"]["legacy_calls"]), 2)
        finally:
            hidden_database.rename(self.database)
            hidden_repository.rename(self.repository)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
