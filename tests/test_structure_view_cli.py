from __future__ import annotations

from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from software_world_model.application_services.structure_read_bundle import (
    StructureOrderedReadBundle,
    StructureSnapshotBundleReference,
)
from software_world_model.cross_cutting import canonical_json_bytes
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.interface.structure_view_cli import build_parser, main
from tests import test_structure_view as _view_tests


class StructureViewCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.view_fixture = _view_tests.StructureViewTests(methodName="runTest")
        self.view_fixture.setUp()
        self.addCleanup(self.view_fixture.doCleanups)
        self.store = FileStructureReadBundleStore()
        self.a_path = self.base / "a.json"
        self.b_path = self.base / "b.json"
        stored_a = self.store.write_snapshot(
            str(self.a_path), self.view_fixture.a[1]
        )
        stored_b = self.store.write_snapshot(
            str(self.b_path), self.view_fixture.b[1]
        )
        self.envelope = StructureOrderedReadBundle.create(
            session=self.view_fixture.session,
            snapshots=tuple(
                StructureSnapshotBundleReference(
                    ordinal=ordinal,
                    snapshot_id=bundle.snapshot_id,
                    snapshot_binding_digest=binding.digest,
                    snapshot_manifest_digest=binding.snapshot_manifest_digest,
                    bundle_digest=bundle.digest,
                    file_digest=stored.file_digest,
                )
                for ordinal, (binding, bundle, stored) in enumerate(
                    zip(
                        self.view_fixture.session.snapshots,
                        (self.view_fixture.a[1], self.view_fixture.b[1]),
                        (stored_a, stored_b),
                    )
                )
            ),
        )
        self.envelope_path = self.base / "ordered.json"
        self.store.write_ordered(str(self.envelope_path), self.envelope)

    def _invoke(
        self,
        command: list[str],
        *,
        bundles: tuple[Path, ...] | None = None,
        result_path: Path | str | None = None,
        envelope_path: Path | None = None,
    ):
        selected = bundles or (self.a_path, self.b_path)
        argv = ["--ordered-envelope", str(envelope_path or self.envelope_path)]
        for path in selected:
            argv.extend(("--snapshot-bundle", str(path)))
        if result_path is not None:
            argv.extend(("--result-path", str(result_path)))
        argv.extend(command)
        stdout = StringIO()
        stderr = StringIO()
        exit_code = main(argv, stdout=stdout, stderr=stderr)
        return exit_code, stdout.getvalue(), stderr.getvalue()

    @staticmethod
    def _entity(bundle, label: str):
        matches = tuple(
            item
            for item in bundle.entities
            if item.state.state_payload_fields["label"] == label
        )
        if len(matches) != 1:
            raise AssertionError(f"expected one Entity labelled {label}")
        return matches[0]

    def _selector(self, prefix: str, bundle, label: str) -> list[str]:
        entity = self._entity(bundle, label)
        return [
            f"--{prefix}-snapshot-id",
            bundle.snapshot_id.value,
            f"--{prefix}-root-id",
            entity.root_id.value,
            f"--{prefix}-state-id",
            entity.state_id.value,
        ]

    def test_parser_has_only_bundle_inputs_and_no_connected_runtime_port(self) -> None:
        parser = build_parser()
        options = {
            option
            for action in parser._actions
            for option in action.option_strings
        }
        self.assertIn("--ordered-envelope", options)
        self.assertIn("--snapshot-bundle", options)
        self.assertNotIn("--database", options)
        self.assertNotIn("--source", options)
        self.assertNotIn("--runtime", options)

    def test_candidates_preserve_ambiguity_as_a_sealed_limitation(self) -> None:
        snapshot_id = self.view_fixture.a[0].snapshot_id.value
        exit_code, stdout, stderr = self._invoke(
            [
                "candidates",
                "--snapshot-id",
                snapshot_id,
                "--mention",
                "common-lib",
            ]
        )
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            canonical_json_bytes(json.loads(stdout)).decode("utf-8"), stdout
        )
        payload = json.loads(stdout)
        self.assertEqual(payload["operation"], "ENTITY_CANDIDATES")
        self.assertEqual(payload["payload"]["resolution_status"], "AMBIGUOUS")
        self.assertEqual(payload["payload"]["candidate_count"], 2)
        self.assertEqual(payload["limitations"], ["ENTITY_RESOLUTION_AMBIGUOUS"])

    def test_inventory_accepts_caller_exact_ref_and_neighborhood_uses_same_call_candidate(self) -> None:
        bundle = self.view_fixture.a[1]
        exit_code, stdout, stderr = self._invoke(
            ["inventory", *self._selector("system", bundle, "mall")]
        )
        self.assertEqual((exit_code, stderr), (0, ""))
        inventory = json.loads(stdout)
        self.assertEqual(inventory["operation"], "CHILD_MODULE_INVENTORY")
        self.assertEqual(inventory["payload"]["module_count"], 6)

        exit_code, stdout, stderr = self._invoke(
            [
                "neighborhood",
                "--entity-snapshot-id",
                bundle.snapshot_id.value,
                "--entity-mention",
                "admin",
                "--direction",
                "OUTGOING",
                "--predicate",
                "DEPENDS_ON",
            ]
        )
        self.assertEqual((exit_code, stderr), (0, ""))
        neighborhood = json.loads(stdout)
        self.assertEqual(neighborhood["operation"], "DIRECT_NEIGHBORHOOD")
        self.assertEqual(len(neighborhood["payload"]["relations"]), 1)

    def test_dependent_operation_returns_candidate_limitation_instead_of_guessing(self) -> None:
        bundle = self.view_fixture.a[1]
        exit_code, stdout, stderr = self._invoke(
            [
                "neighborhood",
                "--entity-snapshot-id",
                bundle.snapshot_id.value,
                "--entity-mention",
                "common-lib",
            ]
        )
        self.assertEqual(exit_code, 3)
        self.assertEqual(stderr, "")
        payload = json.loads(stdout)
        self.assertEqual(payload["operation"], "ENTITY_CANDIDATES")
        self.assertEqual(payload["payload"]["resolution_status"], "AMBIGUOUS")
        self.assertNotEqual(payload["operation"], "DIRECT_NEIGHBORHOOD")

    def test_path_operations_support_exact_and_unique_candidate_arguments(self) -> None:
        a_bundle = self.view_fixture.a[1]
        command = [
            "path-exists",
            *self._selector("source", a_bundle, "admin"),
            *self._selector("target", a_bundle, "search"),
        ]
        exit_code, stdout, stderr = self._invoke(command)
        self.assertEqual((exit_code, stderr), (0, ""))
        result = json.loads(stdout)
        self.assertEqual(result["operation"], "PATH_EXISTS")
        self.assertFalse(result["payload"]["exists"])
        self.assertTrue(result["payload"]["negative_conclusion_supported"])

        b_bundle = self.view_fixture.b[1]
        exit_code, stdout, stderr = self._invoke(
            [
                "all-simple-paths",
                "--source-snapshot-id",
                b_bundle.snapshot_id.value,
                "--source-mention",
                "admin",
                "--target-snapshot-id",
                b_bundle.snapshot_id.value,
                "--target-mention",
                "common",
            ]
        )
        self.assertEqual((exit_code, stderr), (0, ""))
        paths = json.loads(stdout)
        self.assertEqual(paths["operation"], "ALL_SIMPLE_PATHS")
        self.assertEqual(paths["payload"]["path_count"], 2)

    def test_diff_and_mounting_preserve_caller_declared_order(self) -> None:
        a_id = self.view_fixture.a[0].snapshot_id.value
        b_id = self.view_fixture.b[0].snapshot_id.value
        command = [
            "diff",
            "--base-snapshot-id",
            a_id,
            "--target-snapshot-id",
            b_id,
        ]
        exit_code, stdout, stderr = self._invoke(command)
        self.assertEqual((exit_code, stderr), (0, ""))
        result = json.loads(stdout)
        self.assertEqual(result["snapshot_ids"], [a_id, b_id])
        self.assertEqual(result["payload"]["base_ordinal"], 0)
        self.assertEqual(result["payload"]["target_ordinal"], 1)

        exit_code, stdout, stderr = self._invoke(
            command,
            bundles=(self.b_path, self.a_path),
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(
            json.loads(stderr)["details"]["reason_code"],
            "READ_BUNDLE_LOADED_REFERENCE_MISMATCH",
        )

        exit_code, stdout, stderr = self._invoke(
            [
                "diff",
                "--base-snapshot-id",
                b_id,
                "--target-snapshot-id",
                a_id,
            ]
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(
            json.loads(stderr)["details"]["reason_code"],
            "VIEW_DIFF_ORDER_INVALID",
        )

    def test_explicit_result_path_is_new_canonical_file_and_rejects_unsafe_paths(self) -> None:
        result_path = self.base / "result.json"
        command = [
            "candidates",
            "--snapshot-id",
            self.view_fixture.a[0].snapshot_id.value,
            "--mention",
            "admin",
        ]
        exit_code, stdout, stderr = self._invoke(
            command, result_path=result_path
        )
        self.assertEqual((exit_code, stdout, stderr), (0, "", ""))
        encoded = result_path.read_bytes()
        self.assertEqual(canonical_json_bytes(json.loads(encoded)), encoded)

        exit_code, stdout, stderr = self._invoke(
            command, result_path=result_path
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(
            json.loads(stderr)["details"]["reason_code"],
            "VIEW_CLI_RESULT_PATH_UNAVAILABLE",
        )

        traversal = str(self.base / "child" / ".." / "traversal.json")
        exit_code, stdout, stderr = self._invoke(
            command, result_path=traversal
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(
            json.loads(stderr)["details"]["reason_code"],
            "VIEW_CLI_RESULT_PATH_NONCANONICAL",
        )

    def test_bundle_symlink_is_rejected_without_fallback(self) -> None:
        envelope_link = self.base / "ordered-link.json"
        envelope_link.symlink_to(self.envelope_path)
        exit_code, stdout, stderr = self._invoke(
            [
                "candidates",
                "--snapshot-id",
                self.view_fixture.a[0].snapshot_id.value,
                "--mention",
                "admin",
            ],
            envelope_path=envelope_link,
        )
        self.assertEqual(exit_code, 2)
        self.assertEqual(stdout, "")
        error = json.loads(stderr)
        self.assertEqual(error["error"], "INVALID_ARGUMENT")
        self.assertIn("reason_code", error["details"])


if __name__ == "__main__":
    unittest.main()
