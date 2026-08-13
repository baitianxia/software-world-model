from __future__ import annotations

from contextlib import closing
from io import StringIO
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import unittest

from software_world_model.cross_cutting import (
    CorrelationRef,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    StableId,
    canonical_json_bytes,
)
from software_world_model.infrastructure import SqliteDatabase
from software_world_model.infrastructure.file_read_set_catalog import (
    FileReadSetCatalogStore,
    RootedStructureReadBundleStore,
)
from software_world_model.interface.cli import main as management_main
from software_world_model.interface.read_set_catalog_cli import (
    build_parser as source_off_parser,
    main as source_off_main,
)
from software_world_model.interface.runtime import ApplicationRuntime
from tests.test_maven_structure_cli import (
    MODULE_POM,
    ROOT_POM,
    ROOT_POM_WITHOUT_MODULES,
)


class _FailOrderedBundleOnce:
    def __init__(self, delegate: object) -> None:
        self._delegate = delegate
        self._failed = False

    def publish_snapshot(self, **values: object):
        return self._delegate.publish_snapshot(**values)

    def open_read_session(self, **values: object):
        return self._delegate.open_read_session(**values)

    def build_snapshot_bundle(self, **values: object):
        return self._delegate.build_snapshot_bundle(**values)

    def build_ordered_bundle(self, **values: object):
        if not self._failed:
            self._failed = True
            raise DomainError(
                ErrorCode.INVALID_ARGUMENT,
                "simulated ordered Bundle failure",
                {"reason_code": "SIMULATED_BUNDLE_FAILURE"},
            )
        return self._delegate.build_ordered_bundle(**values)


class _InterruptOrderedBundleOnce:
    def __init__(self, delegate: object) -> None:
        self._delegate = delegate
        self._failed = False

    def publish_snapshot(self, **values: object):
        return self._delegate.publish_snapshot(**values)

    def open_read_session(self, **values: object):
        return self._delegate.open_read_session(**values)

    def build_snapshot_bundle(self, **values: object):
        return self._delegate.build_snapshot_bundle(**values)

    def build_ordered_bundle(self, **values: object):
        if not self._failed:
            self._failed = True
            raise PermissionError("simulated uncertain Bundle I/O interruption")
        return self._delegate.build_ordered_bundle(**values)


class _FailCatalogReceiptOnce:
    def __init__(self, delegate: object) -> None:
        self._delegate = delegate
        self._failed = False

    def __getattr__(self, name: str):
        return getattr(self._delegate, name)

    def save_catalog_publication(self, publication: object):
        if not self._failed:
            self._failed = True
            raise OSError("simulated crash after Catalog pointer publication")
        return self._delegate.save_catalog_publication(publication)


class _MoveCurrentBeforeWorkspacePublication:
    def __init__(self, delegate: object) -> None:
        self._delegate = delegate
        self._moved = False

    def publish_snapshot(self, **values: object):
        if not self._moved:
            self._moved = True
            competing = dict(values)
            competing["idempotency_key"] = IdempotencyKey(
                "competing-publication-moves-current"
            )
            self._delegate.publish_snapshot(**competing)
        return self._delegate.publish_snapshot(**values)

    def open_read_session(self, **values: object):
        return self._delegate.open_read_session(**values)

    def build_snapshot_bundle(self, **values: object):
        return self._delegate.build_snapshot_bundle(**values)

    def build_ordered_bundle(self, **values: object):
        return self._delegate.build_ordered_bundle(**values)


class MavenWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.database = self.root / "state.sqlite3"
        self.bundle_root = self.root / "bundles"
        self.catalog_root = self.root / "catalog"
        self.repository = self.root / "repository"
        (self.repository / "module-a").mkdir(parents=True)
        (self.repository / "pom.xml").write_text(ROOT_POM, encoding="utf-8")
        (self.repository / "module-a" / "pom.xml").write_text(
            MODULE_POM, encoding="utf-8"
        )
        self._git("init", "-q")
        self._git("config", "user.email", "workspace@example.com")
        self._git("config", "user.name", "Workspace Test")
        self._git("add", ".")
        self._git("commit", "-q", "-m", "r1")
        self.r1 = self._git("rev-parse", "HEAD")
        self.producer_commit = "0" * 40
        self.producer_tree = "1" * 40
        code, registered = self._management(
            "register-maven-workspace",
            "--idempotency-key",
            "workspace-register",
            "--source-target",
            str(self.repository),
            "--display-name",
            "Maven Workspace Fixture",
            "--canonical-system-key",
            "fixture:maven-workspace",
            "--root-pom",
            "pom.xml",
            "--actor",
            "test",
            "--correlation-ref",
            "workspace-register",
        )
        self.assertEqual(code, 0, registered)
        self.workspace_id = registered["workspace"]["workspace_id"]

    def _git(self, *arguments: str) -> str:
        return subprocess.run(
            ("git", "-C", str(self.repository), *arguments),
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout.strip()

    def _runtime_options(self) -> dict[str, object]:
        return {
            "bundle_root": self.bundle_root,
            "catalog_root": self.catalog_root,
            "producer_commit": self.producer_commit,
            "producer_tree": self.producer_tree,
        }

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

    def _source_off(self, *arguments: str) -> tuple[int, str, str]:
        output = StringIO()
        errors = StringIO()
        code = source_off_main(
            [
                "--catalog-root",
                str(self.catalog_root),
                "--bundle-root",
                str(self.bundle_root),
                *arguments,
            ],
            stdout=output,
            stderr=errors,
        )
        return code, output.getvalue(), errors.getvalue()

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

    def _commit_r2(self) -> str:
        (self.repository / "pom.xml").write_text(
            ROOT_POM_WITHOUT_MODULES, encoding="utf-8"
        )
        self._git("add", "pom.xml")
        self._git("commit", "-q", "-m", "r2 removes module-a")
        return self._git("rev-parse", "HEAD")

    def _manifest_path(self) -> Path:
        pointer = json.loads((self.catalog_root / "current.json").read_bytes())
        digest = pointer["catalog_digest"].split(":", 1)[1]
        return (
            self.catalog_root
            / "manifests"
            / pointer["catalog_id"]
            / f"{pointer['revision']:020d}-{digest}.json"
        )

    def test_workspace_registration_is_idempotent_and_rejects_key_reuse(self) -> None:
        arguments = (
            "register-maven-workspace",
            "--idempotency-key",
            "workspace-register",
            "--source-target",
            str(self.repository),
            "--display-name",
            "Maven Workspace Fixture",
            "--canonical-system-key",
            "fixture:maven-workspace",
            "--root-pom",
            "pom.xml",
            "--actor",
            "test",
            "--correlation-ref",
            "workspace-register",
        )
        code, replay = self._management(*arguments)
        self.assertEqual(code, 0, replay)
        self.assertEqual(replay["workspace"]["workspace_id"], self.workspace_id)

        changed = list(arguments)
        changed[changed.index("Maven Workspace Fixture")] = "Changed Display Name"
        code, error = self._management(*changed)
        self.assertEqual(code, 2)
        self.assertEqual(error["error"], "IDEMPOTENCY_MISMATCH")

    def test_r1_r2_restart_and_source_off_views_use_dynamic_catalog(self) -> None:
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM app_structure_read_sessions"
                ).fetchone()[0],
                0,
            )
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM app_snapshot_read_sessions"
                ).fetchone()[0],
                0,
            )
            self.assertIsNone(
                connection.execute(
                    "SELECT name FROM sqlite_master WHERE name = 'app_tasks'"
                ).fetchone()
            )

        first = self._update(self.r1, "workspace-r1")
        replay = self._update(self.r1, "workspace-r1")
        self.assertEqual(replay["attempt"]["attempt_id"], first["attempt"]["attempt_id"])
        self.assertEqual(replay["version"]["version_id"], first["version"]["version_id"])
        self.assertEqual(first["workflow"], "MAVEN_WORKSPACE_FULL_REBUILD@1")
        self.assertTrue(first["manual_zero_question_update"])
        self.assertEqual(first["execution_metrics"]["source_calls"], 3)
        self.assertGreater(first["execution_metrics"]["source_bytes"], 0)
        self.assertGreaterEqual(
            first["execution_metrics"]["snapshot_elapsed_milliseconds"], 0
        )
        self.assertEqual(first["version"]["availability"], "QUERYABLE")
        self.assertIsNone(first["comparison_read_set"])

        r2 = self._commit_r2()
        code, mismatch = self._management(
            "update-maven-workspace",
            "--workspace-id",
            self.workspace_id,
            "--repository-revision",
            r2,
            "--idempotency-key",
            "workspace-r1",
            "--correlation-ref",
            "workspace-r1-mismatch",
        )
        self.assertEqual(code, 2)
        self.assertEqual(mismatch["error"], "IDEMPOTENCY_MISMATCH")
        second = self._update(r2, "workspace-r2")
        self.assertEqual(second["version"]["ordinal"], 2)
        self.assertEqual(second["version"]["availability"], "QUERYABLE")
        self.assertIsNotNone(second["comparison_read_set"])
        self.assertEqual(len(second["catalog"]["entries"]), 3)

        first_owner = first["snapshot_owner_result"]
        second_owner = second["snapshot_owner_result"]
        first_system = next(
            item for item in first_owner["entities"] if item["entity_type"] == "SOFTWARE_SYSTEM"
        )
        second_system = next(
            item for item in second_owner["entities"] if item["entity_type"] == "SOFTWARE_SYSTEM"
        )
        self.assertEqual(first_system["root_id"], second_system["root_id"])
        self.assertNotEqual(first_system["state_id"], second_system["state_id"])
        self.assertTrue(second_owner["deletions"]["removed_members"])
        self.assertEqual(
            second_owner["snapshot"]["previous_snapshot_id"],
            first["version"]["snapshot_id"],
        )

        code, versions = self._management(
            "list-maven-workspace-versions", "--workspace-id", self.workspace_id
        )
        self.assertEqual(code, 0, versions)
        self.assertEqual(
            [item["repository_revision"] for item in versions["versions"]],
            [self.r1, r2],
        )
        code, read_sets = self._management(
            "list-read-sets", "--workspace-id", self.workspace_id
        )
        self.assertEqual(code, 0, read_sets)
        self.assertEqual(len(read_sets["read_sets"]), 3)

        manifest_bytes = self._manifest_path().read_bytes()
        self.assertNotIn(str(self.repository).encode("utf-8"), manifest_bytes)
        self.assertNotIn(str(self.database).encode("utf-8"), manifest_bytes)
        document = json.loads(manifest_bytes)
        keys: set[str] = set()

        def collect(value: object) -> None:
            if isinstance(value, dict):
                keys.update(value)
                for nested in value.values():
                    collect(nested)
            elif isinstance(value, list):
                for nested in value:
                    collect(nested)

        collect(document)
        self.assertFalse(
            {
                "entities",
                "relations",
                "facts",
                "evidence",
                "artifact_payload",
                "source_payload",
                "repository_locator",
                "database_path",
            }
            & keys
        )

        # Make the original management inputs unavailable before starting a
        # process whose parser has no database or Source option.
        self.database.rename(self.root / "state.unmounted")
        self.repository.rename(self.root / "repository.unmounted")
        parser_options = {
            option
            for action in source_off_parser()._actions
            for option in action.option_strings
        }
        self.assertNotIn("--database", parser_options)
        self.assertNotIn("--source-target", parser_options)

        code, output, errors = self._source_off("list-read-sets")
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(len(json.loads(output)["read_sets"]), 3)

        r1_read_set = first["single_read_set"]["read_set_id"]
        r1_snapshot = first["version"]["snapshot_id"]
        system_root = first_system["root_id"]
        system_state = first_system["state_id"]
        module = next(
            item
            for item in first_owner["entities"]
            if item["entity_type"] == "MAVEN_MODULE"
        )

        commands = (
            (
                r1_read_set,
                "candidates",
                "--snapshot-id",
                r1_snapshot,
                "--mention",
                "module-a",
            ),
            (
                r1_read_set,
                "inventory",
                "--system-snapshot-id",
                r1_snapshot,
                "--system-root-id",
                system_root,
                "--system-state-id",
                system_state,
            ),
            (
                r1_read_set,
                "neighborhood",
                "--entity-snapshot-id",
                r1_snapshot,
                "--entity-root-id",
                system_root,
                "--entity-state-id",
                system_state,
                "--direction",
                "OUTGOING",
                "--predicate",
                "DEPENDS_ON",
            ),
            (
                r1_read_set,
                "path-exists",
                "--source-snapshot-id",
                r1_snapshot,
                "--source-root-id",
                system_root,
                "--source-state-id",
                system_state,
                "--target-snapshot-id",
                r1_snapshot,
                "--target-root-id",
                module["root_id"],
                "--target-state-id",
                module["state_id"],
                "--predicate",
                "DEPENDS_ON",
            ),
            (
                second["comparison_read_set"]["read_set_id"],
                "diff",
                "--base-snapshot-id",
                r1_snapshot,
                "--target-snapshot-id",
                second["version"]["snapshot_id"],
            ),
        )
        expected_operations = (
            "ENTITY_CANDIDATES",
            "CHILD_MODULE_INVENTORY",
            "DIRECT_NEIGHBORHOOD",
            "PATH_EXISTS",
            "ORDERED_SNAPSHOT_DIFF",
        )
        for command, expected in zip(commands, expected_operations):
            code, output, errors = self._source_off(
                "view", "--read-set-id", command[0], "--", *command[1:]
            )
            self.assertEqual((code, errors), (0, ""), (command, errors))
            self.assertEqual(json.loads(output)["operation"], expected)

    def test_catalog_pointer_receipt_locator_bundle_and_directory_tamper_fail_closed(self) -> None:
        first = self._update(self.r1, "workspace-r1-tamper")
        manifest = self._manifest_path()
        original_manifest = manifest.read_bytes()

        def rejected() -> None:
            code, output, errors = self._source_off("verify-current")
            self.assertEqual(code, 2)
            self.assertEqual(output, "")
            self.assertTrue(json.loads(errors)["error"])

        document = json.loads(original_manifest)
        document["producer_commit"] = "2" * 40
        manifest.write_bytes(canonical_json_bytes(document))
        rejected()
        manifest.write_bytes(original_manifest)

        document = json.loads(original_manifest)
        document["entries"][0]["ordered_receipt"]["receipt_id"] = (
            "read_bundle_receipt_" + "f" * 32
        )
        manifest.write_bytes(canonical_json_bytes(document))
        rejected()
        manifest.write_bytes(original_manifest)

        document = json.loads(original_manifest)
        document["entries"][0]["bundle_locator"] = "../outside"
        manifest.write_bytes(canonical_json_bytes(document))
        rejected()
        manifest.write_bytes(original_manifest)

        pointer_path = self.catalog_root / "current.json"
        original_pointer = pointer_path.read_bytes()
        pointer = json.loads(original_pointer)
        pointer["catalog_digest"] = "sha256:" + "0" * 64
        pointer_path.write_bytes(canonical_json_bytes(pointer))
        rejected()
        pointer_path.write_bytes(original_pointer)

        registration = first["single_read_set"]
        snapshot_locator = next(
            item["locator"]
            for item in registration["file_manifest"]
            if item["role"] == "SNAPSHOT"
        )
        snapshot_path = self.bundle_root / snapshot_locator
        original_bundle = snapshot_path.read_bytes()
        snapshot_path.write_bytes(original_bundle + b" ")
        rejected()
        snapshot_path.write_bytes(original_bundle)

        bundle_directory = self.bundle_root / registration["bundle_locator"]
        extra = bundle_directory / "extra.json"
        extra.write_text("{}", encoding="utf-8")
        rejected()
        extra.unlink()

        symlink = bundle_directory / "linked.json"
        symlink.symlink_to(snapshot_path)
        rejected()
        symlink.unlink()

        code, output, errors = self._source_off("verify-current")
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(json.loads(output)["status"], "VERIFIED")

        files = RootedStructureReadBundleStore(self.bundle_root)
        store = FileReadSetCatalogStore(self.catalog_root, files)
        current_pointer = store.read_pointer()
        assert current_pointer is not None
        current_catalog = store.read_catalog(current_pointer, verify_files=True)
        with self.assertRaises(DomainError) as conflict:
            store.publish(current_catalog, expected=None)
        self.assertEqual(conflict.exception.code, ErrorCode.REVISION_CONFLICT)
        self.assertEqual(
            conflict.exception.details["reason_code"],
            "READ_SET_CATALOG_CAS_CONFLICT",
        )

    def test_bundle_failure_is_visible_and_same_attempt_resumes_after_restart(self) -> None:
        first = self._update(self.r1, "workspace-r1-recovery")
        r2 = self._commit_r2()
        attempt_id: StableId
        with SqliteDatabase(self.database) as database:
            runtime = ApplicationRuntime(database, **self._runtime_options())
            assert runtime.maven_workspaces is not None
            runtime.maven_workspaces._operations = _FailOrderedBundleOnce(  # type: ignore[attr-defined]
                runtime.maven_workspaces._operations  # type: ignore[attr-defined]
            )
            with self.assertRaises(DomainError) as caught:
                runtime.update_maven_workspace(
                    workspace_id=StableId(self.workspace_id),
                    repository_revision=r2,
                    idempotency_key=IdempotencyKey("workspace-r2-recovery"),
                    correlation_ref=CorrelationRef("workspace-r2-recovery"),
                )
            self.assertEqual(
                caught.exception.details["workspace_attempt_state"],
                "READ_BUNDLE_UNAVAILABLE",
            )
            attempt_id = StableId(
                str(caught.exception.details["workspace_attempt_id"])
            )
            attempt = runtime.get_maven_workspace_attempt(attempt_id)
            self.assertEqual(attempt.state.value, "READ_BUNDLE_UNAVAILABLE")
            self.assertEqual(
                [(item.name.value, item.outcome.value) for item in attempt.steps],
                [
                    ("SNAPSHOT_PUBLICATION", "SUCCEEDED"),
                    ("SINGLE_READ_SET", "FAILED"),
                ],
            )
            versions = runtime.list_maven_workspace_versions(
                StableId(self.workspace_id)
            )
            self.assertEqual(
                [item.availability.value for item in versions],
                ["QUERYABLE", "READ_BUNDLE_UNAVAILABLE"],
            )

        code, output, errors = self._source_off("list-read-sets")
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(len(json.loads(output)["read_sets"]), 1)
        self.assertEqual(
            json.loads(output)["read_sets"][0]["read_set_id"],
            first["single_read_set"]["read_set_id"],
        )

        with SqliteDatabase(self.database) as database:
            runtime = ApplicationRuntime(database, **self._runtime_options())
            resumed = runtime.resume_maven_workspace(
                attempt_id=attempt_id,
                correlation_ref=CorrelationRef("workspace-r2-resume"),
            )
            self.assertEqual(resumed.attempt.state.value, "SUCCEEDED")
            self.assertEqual(resumed.version.availability.value, "QUERYABLE")
            self.assertEqual(len(resumed.catalog.entries), 3)
            self.assertEqual(
                sum(
                    item.name.value == "SNAPSHOT_PUBLICATION"
                    and item.outcome.value == "SUCCEEDED"
                    for item in resumed.attempt.steps
                ),
                1,
            )
            self.assertEqual(
                [
                    item.outcome.value
                    for item in resumed.attempt.steps
                    if item.name.value == "SINGLE_READ_SET"
                ],
                ["FAILED", "SUCCEEDED"],
            )

    def test_uncertain_bundle_io_is_pending_while_version_is_unavailable(self) -> None:
        first = self._update(self.r1, "workspace-r1-io-pending")
        r2 = self._commit_r2()
        with SqliteDatabase(self.database) as database:
            runtime = ApplicationRuntime(database, **self._runtime_options())
            assert runtime.maven_workspaces is not None
            runtime.maven_workspaces._operations = _InterruptOrderedBundleOnce(  # type: ignore[attr-defined]
                runtime.maven_workspaces._operations  # type: ignore[attr-defined]
            )
            with self.assertRaises(DomainError) as caught:
                runtime.update_maven_workspace(
                    workspace_id=StableId(self.workspace_id),
                    repository_revision=r2,
                    idempotency_key=IdempotencyKey("workspace-r2-io-pending"),
                    correlation_ref=CorrelationRef("workspace-r2-io-pending"),
                )
            self.assertEqual(caught.exception.code, ErrorCode.OUTCOME_PENDING)
            self.assertEqual(
                caught.exception.details["workspace_attempt_state"],
                "OUTCOME_PENDING",
            )
            attempt_id = StableId(
                str(caught.exception.details["workspace_attempt_id"])
            )
            attempt = runtime.get_maven_workspace_attempt(attempt_id)
            self.assertEqual(
                [(item.name.value, item.outcome.value) for item in attempt.steps],
                [
                    ("SNAPSHOT_PUBLICATION", "SUCCEEDED"),
                    ("SINGLE_READ_SET", "OUTCOME_PENDING"),
                ],
            )
            versions = runtime.list_maven_workspace_versions(
                StableId(self.workspace_id)
            )
            self.assertEqual(
                [item.availability.value for item in versions],
                ["QUERYABLE", "READ_BUNDLE_UNAVAILABLE"],
            )
            self.assertEqual(
                versions[0].single_read_set_id.value,
                first["single_read_set"]["read_set_id"],
            )

        with SqliteDatabase(self.database) as database:
            runtime = ApplicationRuntime(database, **self._runtime_options())
            resumed = runtime.resume_maven_workspace(
                attempt_id=attempt_id,
                correlation_ref=CorrelationRef("workspace-r2-io-resume"),
            )
            self.assertEqual(resumed.attempt.state.value, "SUCCEEDED")
            self.assertEqual(resumed.attempt.attempt_id, attempt_id)
            self.assertEqual(
                sum(
                    item.name.value == "SNAPSHOT_PUBLICATION"
                    and item.outcome.value == "SUCCEEDED"
                    for item in resumed.attempt.steps
                ),
                1,
            )

    def test_catalog_pointer_crash_reconciles_before_a_later_publication(self) -> None:
        self._update(self.r1, "workspace-r1-catalog-recovery")
        r2 = self._commit_r2()
        attempt_id: StableId
        with SqliteDatabase(self.database) as database:
            runtime = ApplicationRuntime(database, **self._runtime_options())
            assert runtime.read_set_catalog is not None
            runtime.read_set_catalog._repository = _FailCatalogReceiptOnce(  # type: ignore[attr-defined]
                runtime.read_set_catalog._repository  # type: ignore[attr-defined]
            )
            with self.assertRaises(DomainError) as caught:
                runtime.update_maven_workspace(
                    workspace_id=StableId(self.workspace_id),
                    repository_revision=r2,
                    idempotency_key=IdempotencyKey("workspace-r2-catalog-recovery"),
                    correlation_ref=CorrelationRef("workspace-r2-catalog-recovery"),
                )
            self.assertEqual(caught.exception.code, ErrorCode.OUTCOME_PENDING)
            attempt_id = StableId(
                str(caught.exception.details["workspace_attempt_id"])
            )
            pointer_before = json.loads(
                (self.catalog_root / "current.json").read_bytes()
            )
            self.assertEqual(pointer_before["revision"], 2)

        with SqliteDatabase(self.database) as database:
            runtime = ApplicationRuntime(database, **self._runtime_options())
            later_workspace = runtime.register_maven_workspace(
                idempotency_key=IdempotencyKey("catalog-recovery-later-workspace"),
                source_target=str(self.repository),
                display_name="Catalog Recovery Later Workspace",
                canonical_system_key="fixture:catalog-recovery-later",
                root_pom="pom.xml",
                actor="test",
                correlation_ref=CorrelationRef("catalog-recovery-later-register"),
            )
            later = runtime.update_maven_workspace(
                workspace_id=later_workspace.workspace_id,
                repository_revision=self.r1,
                idempotency_key=IdempotencyKey("catalog-recovery-later-r1"),
                correlation_ref=CorrelationRef("catalog-recovery-later-r1"),
            )
            self.assertEqual(later.catalog.revision.value, 3)
            resumed = runtime.resume_maven_workspace(
                attempt_id=attempt_id,
                correlation_ref=CorrelationRef("workspace-r2-catalog-resume"),
            )
            self.assertEqual(resumed.attempt.state.value, "SUCCEEDED")
            self.assertEqual(resumed.catalog.revision.value, 3)
            self.assertEqual(len(resumed.catalog.entries), 4)
            pointer_after = json.loads(
                (self.catalog_root / "current.json").read_bytes()
            )
            self.assertEqual(pointer_after["revision"], 3)
        with closing(sqlite3.connect(self.database)) as connection:
            self.assertEqual(
                [
                    row[0]
                    for row in connection.execute(
                        "SELECT revision FROM app_read_set_catalog_publications ORDER BY revision"
                    )
                ],
                [1, 2, 3],
            )

    def test_stale_expected_current_creates_no_workspace_version_or_read_set(self) -> None:
        first = self._update(self.r1, "workspace-r1-stale-current")
        r2 = self._commit_r2()
        with SqliteDatabase(self.database) as database:
            runtime = ApplicationRuntime(database, **self._runtime_options())
            assert runtime.maven_workspaces is not None
            runtime.maven_workspaces._operations = (  # type: ignore[attr-defined]
                _MoveCurrentBeforeWorkspacePublication(
                    runtime.maven_workspaces._operations  # type: ignore[attr-defined]
                )
            )
            with self.assertRaises(DomainError) as caught:
                runtime.update_maven_workspace(
                    workspace_id=StableId(self.workspace_id),
                    repository_revision=r2,
                    idempotency_key=IdempotencyKey("workspace-r2-stale-current"),
                    correlation_ref=CorrelationRef("workspace-r2-stale-current"),
                )
            self.assertEqual(caught.exception.code, ErrorCode.REVISION_CONFLICT)
            self.assertEqual(
                caught.exception.details["workspace_attempt_state"], "FAILED"
            )
            attempt = runtime.get_maven_workspace_attempt(
                StableId(str(caught.exception.details["workspace_attempt_id"]))
            )
            self.assertEqual(
                [(item.name.value, item.outcome.value) for item in attempt.steps],
                [("SNAPSHOT_PUBLICATION", "FAILED")],
            )
            versions = runtime.list_maven_workspace_versions(
                StableId(self.workspace_id)
            )
            self.assertEqual(len(versions), 1)
            self.assertEqual(versions[0].snapshot_id.value, first["version"]["snapshot_id"])
            self.assertEqual(versions[0].availability.value, "QUERYABLE")
            self.assertEqual(len(runtime.list_read_sets(StableId(self.workspace_id))), 1)

        code, output, errors = self._source_off("list-read-sets")
        self.assertEqual((code, errors), (0, ""))
        self.assertEqual(len(json.loads(output)["read_sets"]), 1)


class MavenCoverageCopyTests(unittest.TestCase):
    def test_browser_and_dataset_copy_match_the_formal_structure_schema(self) -> None:
        project = Path(__file__).resolve().parents[1]
        product_copy = (
            project
            / "src/software_world_model/interface/world_model_browser_ui.py"
        ).read_text(encoding="utf-8")
        dataset_copy = (
            project
            / "validation/structure_world_model_iteration_004/interactive_browser.py"
        ).read_text(encoding="utf-8")
        dynamic_copy = (
            project / "src/software_world_model/interface/world_model_http.py"
        ).read_text(encoding="utf-8")
        self.assertIn("reactor 子模块成员关系", dataset_copy)
        self.assertIn("POM-local 直接内部依赖", dataset_copy)
        self.assertIn("Coverage 由所选 Read Set 的 Profile 决定", product_copy)
        self.assertIn("Maven reactor child membership", dynamic_copy)
        self.assertIn("plugins, properties", dynamic_copy)
        self.assertIn("Java type and declared-method membership", dynamic_copy)
        self.assertIn("runtime dispatch, reflection", dynamic_copy)
        self.assertNotIn("模块、依赖、插件、属性、父子结构", dataset_copy)
        self.assertNotIn("模块、依赖、插件、属性及 A/B", product_copy)


if __name__ == "__main__":
    unittest.main()
