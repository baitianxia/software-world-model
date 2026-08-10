from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import unittest

from software_world_model.application_services.citation_projection import (
    CitationObservationBroker,
    CitationProjector,
)
from software_world_model.application_services.knowledge_use import TaskBoundary
from software_world_model.application_services.maven_structure import (
    evaluate_maven_reactor,
)
from software_world_model.application_services.structure_read_bundle import (
    StructureOrderedReadBundle,
    StructureSnapshotBundleReference,
    StructureSnapshotReadBundle,
)
from software_world_model.application_services.structure_read_session import (
    StructureReadPurpose,
    StructureReadSessionService,
)
from software_world_model.application_services.structure_view import (
    EntityResolutionStatus,
    StructureEntityArgument,
    StructureViewResult,
    StructureViewService,
)
from software_world_model.cross_cutting import (
    IdempotencyKey,
    Revision,
    StableId,
    canonical_json_bytes,
)
from software_world_model.infrastructure.file_structure_read_bundle import (
    FileStructureReadBundleStore,
)
from software_world_model.infrastructure.file_citation_observation_store import (
    FileCitationObservationStoreReader,
    FileCitationObservationStoreWriter,
)
from software_world_model.infrastructure.sqlite_database import SqliteDatabase
from software_world_model.infrastructure.sqlite_structure_knowledge_repository import (
    SqliteStructureKnowledgeRepository,
)
from software_world_model.infrastructure.sqlite_structure_read_session_repository import (
    SqliteStructureReadSessionRepository,
)
from software_world_model.knowledge_engine.structure import (
    EntityType,
    RelationPredicate,
)
from software_world_model.knowledge_engine.structure_publication import (
    StructureEvidenceMetadata,
)
from tests import test_iteration_003_fixture as _identity_fixture_tests
from tests import test_iteration_003_g1_integration as _g1_integration
from tests import test_maven_structure as _maven_structure_tests
from tests import test_structure_publication as _publication_tests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ISOLATION_ROOT = (
    PROJECT_ROOT
    / "validation"
    / "structure_world_model_iteration_003"
    / "isolation"
)


class Iteration003G2MallIntegrationTests(unittest.TestCase):
    """Exercise the frozen mall A1 -> B -> A2 graph through no-payload files."""

    _FORBIDDEN_PAYLOAD_KEYS = {
        "artifact_bytes",
        "excerpt",
        "observation",
        "provider_input",
        "source_bytes",
    }

    def setUp(self) -> None:
        self.fixture = _g1_integration.Iteration003G1MallIntegrationTests(
            methodName="runTest"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.base = Path(self.fixture.temporary.name).resolve() / "g2"
        self.base.mkdir()
        self.bundle_directory = self.base / "bundles"
        self.bundle_directory.mkdir()

    def test_frozen_mall_read_bundles_drive_source_off_views_and_citations(
        self,
    ) -> None:
        revision_a = self.fixture.oracle["repository"]["revision_a"]
        revision_b = self.fixture.oracle["repository"]["revision_b"]
        a1 = self.fixture._successful_cli(
            *self.fixture._build_arguments(
                revision_a,
                key="iter-003-g2-mall-a1",
            )
        )
        b = self.fixture._successful_cli(
            *self.fixture._build_arguments(
                revision_b,
                key="iter-003-g2-mall-b",
                expected_current=a1["snapshot"]["snapshot_id"],
            )
        )
        a2 = self.fixture._successful_cli(
            *self.fixture._build_arguments(
                revision_a,
                key="iter-003-g2-mall-a2",
                expected_current=b["snapshot"]["snapshot_id"],
            )
        )

        session_ab = self._open_ordered_session(
            name="a1-b",
            task_marker="4",
            snapshot_ids=(
                a1["snapshot"]["snapshot_id"],
                b["snapshot"]["snapshot_id"],
            ),
        )
        session_ba2 = self._open_ordered_session(
            name="b-a2",
            task_marker="5",
            snapshot_ids=(
                b["snapshot"]["snapshot_id"],
                a2["snapshot"]["snapshot_id"],
            ),
        )

        snapshot_receipts = {
            name: self._export_snapshot_bundle(name, result["snapshot"]["snapshot_id"])
            for name, result in (("a1", a1), ("b", b), ("a2", a2))
        }
        ordered_receipts = {
            "a1-b": self._export_ordered_bundle("a1-b", session_ab["session_id"]),
            "b-a2": self._export_ordered_bundle("b-a2", session_ba2["session_id"]),
        }
        identity_bundles = self._export_identity_bundle_set()

        authority_counts_before = self._authority_counts()
        store = FileStructureReadBundleStore()
        loaded = {
            name: store.read_snapshot(receipt["stored_bundle"]["locator"])
            for name, receipt in snapshot_receipts.items()
        }
        envelope_ab, _ = store.read_ordered(
            ordered_receipts["a1-b"]["stored_bundle"]["locator"]
        )
        envelope_ba2, _ = store.read_ordered(
            ordered_receipts["b-a2"]["stored_bundle"]["locator"]
        )
        view_ab = StructureViewService(envelope_ab, (loaded["a1"], loaded["b"]))
        view_ba2 = StructureViewService(envelope_ba2, (loaded["b"], loaded["a2"]))

        self.assertFalse(hasattr(view_ab, "database"))
        self.assertFalse(hasattr(view_ab, "repository"))
        self.assertFalse(hasattr(view_ab, "source"))

        results: dict[str, StructureViewResult] = {}
        inventory_a1 = self._inventory(
            view_ab,
            StableId(a1["snapshot"]["snapshot_id"]),
            results,
            "inventory-a1",
        )
        inventory_b = self._inventory(
            view_ab,
            StableId(b["snapshot"]["snapshot_id"]),
            results,
            "inventory-b",
        )
        inventory_a2 = self._inventory(
            view_ba2,
            StableId(a2["snapshot"]["snapshot_id"]),
            results,
            "inventory-a2",
        )
        self.assertEqual(inventory_a1.payload["module_count"], 6)
        self.assertEqual(inventory_b.payload["module_count"], 7)
        self.assertEqual(inventory_a2.payload["module_count"], 6)
        self.assertEqual(
            self._inventory_gavs(inventory_a1),
            set(self.fixture.oracle["revision_a_oracle"]["reactor_child_module_gavs"]),
        )
        self.assertEqual(
            self._inventory_gavs(inventory_b),
            set(self.fixture.oracle["revision_b_oracle"]["reactor_child_module_gavs"]),
        )
        self.assertEqual(
            self._inventory_gavs(inventory_a2),
            self._inventory_gavs(inventory_a1),
        )

        paths_a1 = self._all_paths(
            view_ab,
            loaded["a1"][0],
            source="mall-admin",
            target="mall-common",
            results=results,
            name="paths-a1-admin-common",
        )
        paths_b = self._all_paths(
            view_ab,
            loaded["b"][0],
            source="mall-admin",
            target="mall-common",
            results=results,
            name="paths-b-admin-common",
        )
        paths_a2 = self._all_paths(
            view_ba2,
            loaded["a2"][0],
            source="mall-admin",
            target="mall-common",
            results=results,
            name="paths-a2-admin-common",
        )
        self.assertEqual(paths_a1.payload["path_count"], 1)
        self.assertEqual(paths_b.payload["path_count"], 2)
        self.assertEqual(paths_a2.payload["path_count"], 1)
        self.assertEqual(
            self._path_artifact_ids(loaded["a1"][0], paths_a1),
            self.fixture.oracle["revision_a_oracle"][
                "admin_to_common_all_simple_paths"
            ],
        )
        self.assertEqual(
            self._path_artifact_ids(loaded["b"][0], paths_b),
            self.fixture.oracle["revision_b_oracle"][
                "admin_to_common_all_simple_paths"
            ],
        )
        self.assertEqual(
            self._path_artifact_ids(loaded["a2"][0], paths_a2),
            self._path_artifact_ids(loaded["a1"][0], paths_a1),
        )

        zero_path = self._path_exists(
            view_ab,
            loaded["b"][0],
            source="mall-admin",
            target="mall-search",
            results=results,
            name="zero-path-b-admin-search",
        )
        root_negative = self._path_exists(
            view_ab,
            loaded["b"][0],
            source="mall",
            target="mall-security",
            source_type=EntityType.SOFTWARE_SYSTEM,
            results=results,
            name="root-negative-b-security",
        )
        for negative in (zero_path, root_negative):
            self.assertFalse(negative.payload["exists"])
            self.assertTrue(negative.payload["negative_conclusion_supported"])
            self.assertFalse(negative.truncated)

        diff_ab = view_ab.ordered_snapshot_diff(
            base_snapshot_id=StableId(a1["snapshot"]["snapshot_id"]),
            target_snapshot_id=StableId(b["snapshot"]["snapshot_id"]),
        )
        diff_ba2 = view_ba2.ordered_snapshot_diff(
            base_snapshot_id=StableId(b["snapshot"]["snapshot_id"]),
            target_snapshot_id=StableId(a2["snapshot"]["snapshot_id"]),
        )
        results["diff-a1-b"] = diff_ab
        results["diff-b-a2"] = diff_ba2
        self.assertEqual(
            diff_ab.payload["entities"]["counts"],
            {"added": 1, "removed": 0, "state_changed": 7, "unchanged": 0},
        )
        self.assertEqual(
            diff_ab.payload["relations"]["counts"],
            {"added": 3, "removed": 0, "state_changed": 11, "unchanged": 0},
        )
        self.assertEqual(
            diff_ba2.payload["entities"]["counts"],
            {"added": 0, "removed": 1, "state_changed": 7, "unchanged": 0},
        )
        self.assertEqual(
            diff_ba2.payload["relations"]["counts"],
            {"added": 0, "removed": 3, "state_changed": 11, "unchanged": 0},
        )

        payload_audit = self._assert_no_payload(
            {
                "snapshot_bundles": {
                    name: json.loads(
                        Path(receipt["stored_bundle"]["locator"]).read_bytes()
                    )
                    for name, receipt in snapshot_receipts.items()
                },
                "ordered_envelopes": {
                    name: json.loads(
                        Path(receipt["stored_bundle"]["locator"]).read_bytes()
                    )
                    for name, receipt in ordered_receipts.items()
                },
                "identity_snapshot_bundles": [
                    json.loads(Path(path).read_bytes())
                    for path in identity_bundles["snapshot_paths"]
                ],
                "identity_ordered_envelope": json.loads(
                    Path(identity_bundles["ordered_path"]).read_bytes()
                ),
                "view_results": {
                    name: self._view_payload(result)
                    for name, result in results.items()
                },
                "identity_results": identity_bundles["results"],
            }
        )

        citation_report = self._materialize_and_project_citations(inventory_b)
        authority_counts_after = self._authority_counts()
        self.assertEqual(authority_counts_before["knw_structure_snapshots"], 3)
        self.assertGreater(authority_counts_before["src_operation_roots"], 0)
        self.assertEqual(authority_counts_after, authority_counts_before)

        summary = {
            "schema": "iteration-003-g2-mall-source-off@1",
            "snapshots": {
                "a1": a1["snapshot"]["snapshot_id"],
                "b": b["snapshot"]["snapshot_id"],
                "a2": a2["snapshot"]["snapshot_id"],
            },
            "sessions": {
                "a1-b": session_ab,
                "b-a2": session_ba2,
            },
            "snapshot_bundle_receipts": snapshot_receipts,
            "ordered_bundle_receipts": ordered_receipts,
            "identity_bundles": identity_bundles,
            "views": {
                name: self._view_payload(result)
                for name, result in results.items()
            },
            "citation": citation_report,
            "payload_audit": payload_audit,
            "authority_counts": {
                "before_offline_queries": authority_counts_before,
                "after_offline_queries_and_citation_projection": authority_counts_after,
                "unchanged": authority_counts_after == authority_counts_before,
            },
        }
        self._write_report("g2-mall-source-off-summary.json", summary)
        self._stage_isolation_if_requested(
            snapshot_receipts=snapshot_receipts,
            ordered_receipts=ordered_receipts,
            identity_bundles=identity_bundles,
            summary=summary,
        )

    def _open_ordered_session(
        self,
        *,
        name: str,
        task_marker: str,
        snapshot_ids: tuple[str, str],
    ) -> dict[str, object]:
        arguments = [
            "open-structure-read-session",
            "--scope-id",
            self.fixture.scope_id,
            "--scope-revision",
            "1",
            "--task-id",
            "task_" + task_marker * 32,
            "--task-revision",
            "1",
            "--caller-ref",
            "iter-003-g2-test",
            "--classification",
            "INTERNAL",
            "--idempotency-key",
            f"iter-003-g2-session-{name}",
        ]
        for snapshot_id in snapshot_ids:
            arguments.extend(("--snapshot-id", snapshot_id))
        session = self.fixture._successful_cli(*arguments)
        self.assertEqual(
            [item["snapshot_id"] for item in session["snapshots"]],
            list(snapshot_ids),
        )
        self.assertEqual(session["order"], "CALLER_DECLARED")
        return session

    def _export_snapshot_bundle(
        self, name: str, snapshot_id: str
    ) -> dict[str, object]:
        destination = self.bundle_directory / f"{name}.snapshot.json"
        receipt = self.fixture._successful_cli(
            "build-structure-snapshot-read-bundle",
            "--snapshot-id",
            snapshot_id,
            "--idempotency-key",
            f"iter-003-g2-bundle-{name}",
            "--destination",
            str(destination),
        )
        self.assertEqual(receipt["kind"], "SNAPSHOT")
        self.assertEqual(receipt["snapshot_ids"], [snapshot_id])
        self.assertEqual(receipt["stored_bundle"]["locator"], str(destination))
        return receipt

    def _export_ordered_bundle(
        self, name: str, session_id: str
    ) -> dict[str, object]:
        destination = self.bundle_directory / f"{name}.ordered.json"
        receipt = self.fixture._successful_cli(
            "build-structure-ordered-read-bundle",
            "--session-id",
            session_id,
            "--idempotency-key",
            f"iter-003-g2-ordered-{name}",
            "--destination",
            str(destination),
        )
        self.assertEqual(receipt["kind"], "ORDERED_READ_SET")
        self.assertEqual(receipt["session_id"], session_id)
        self.assertEqual(receipt["stored_bundle"]["locator"], str(destination))
        return receipt

    def _export_identity_bundle_set(self) -> dict[str, object]:
        fixture = _publication_tests.StructurePublicationTests(
            methodName="runTest"
        )
        fixture.setUp()
        try:
            oracle_path = _maven_structure_tests.FIXTURE_ROOT / "oracle.json"
            oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
            self.assertEqual(
                oracle["fixture_id"],
                "maven-identity-anti-name-stitch@1",
            )
            fixture_digest = _identity_fixture_tests._fixture_digest()
            self.assertEqual(
                fixture_digest,
                _identity_fixture_tests.FIXTURE_DIGEST,
            )

            evaluated = []
            for revision in ("identity-a", "identity-b"):
                evaluator_input = replace(
                    _maven_structure_tests._fixture_input(
                        "valid",
                        source_revision=revision,
                    ),
                    owning_scope_id=fixture.scope.scope_id,
                    source_binding_id=fixture.binding,
                )
                result = evaluate_maven_reactor(evaluator_input)
                result.batch.require_admissible()
                self.assertTrue(result.report.complete)
                self._assert_identity_oracle(result, oracle)
                evaluated.append(result)

            receipt_a = fixture.publish(
                evaluated[0].batch,
                key="g2-frozen-identity-a",
                expected=None,
            )
            receipt_b = fixture.publish(
                evaluated[1].batch,
                key="g2-frozen-identity-b",
                expected=receipt_a.snapshot.snapshot_id,
            )
            bundle_a = self._identity_snapshot_bundle(
                receipt_a.snapshot,
                evaluated[0],
            )
            bundle_b = self._identity_snapshot_bundle(
                receipt_b.snapshot,
                evaluated[1],
            )
            self.assertEqual(
                {item.root_id for item in bundle_a.entities},
                {item.root_id for item in bundle_b.entities},
            )
            self.assertTrue(
                all(
                    left.state_id != right.state_id
                    for left, right in zip(bundle_a.entities, bundle_b.entities)
                )
            )

            sessions = StructureReadSessionService(
                SqliteStructureReadSessionRepository(fixture.database),
                fixture.repository,
                fixture.scopes,
                clock=fixture.clock,
            )
            session = sessions.open_ordered(
                scope_id=fixture.scope.scope_id,
                scope_revision=fixture.scope.definition_revision,
                task_boundary=TaskBoundary.create(
                    task_id=StableId("task_" + "6" * 32),
                    task_revision=Revision(1),
                    scope_id=fixture.scope.scope_id,
                    purpose=StructureReadPurpose.SNAPSHOT_COMPARISON.value,
                    classification="INTERNAL",
                ),
                caller_ref="iter-003-g2-frozen-identity",
                snapshot_ids=(
                    receipt_a.snapshot.snapshot_id,
                    receipt_b.snapshot.snapshot_id,
                ),
                idempotency_key=IdempotencyKey(
                    "iter-003-g2-frozen-identity-session"
                ),
            )
            store = FileStructureReadBundleStore()
            a_path = self.bundle_directory / "identity-a.snapshot.json"
            b_path = self.bundle_directory / "identity-b.snapshot.json"
            ordered_path = self.bundle_directory / "identity-a-b.ordered.json"
            stored_a = store.write_snapshot(str(a_path), bundle_a)
            stored_b = store.write_snapshot(str(b_path), bundle_b)
            loaded = (
                store.read_snapshot(str(a_path)),
                store.read_snapshot(str(b_path)),
            )
            envelope = StructureOrderedReadBundle.create(
                session=session,
                snapshots=tuple(
                    StructureSnapshotBundleReference(
                        ordinal=ordinal,
                        snapshot_id=bundle.snapshot_id,
                        snapshot_binding_digest=binding.digest,
                        snapshot_manifest_digest=binding.snapshot_manifest_digest,
                        bundle_digest=bundle.digest,
                        file_digest=file_digest,
                    )
                    for ordinal, (binding, bundle, file_digest) in enumerate(
                        zip(
                            session.snapshots,
                            (bundle_a, bundle_b),
                            (stored_a.file_digest, stored_b.file_digest),
                        )
                    )
                ),
            )
            envelope.verify_snapshot_bundles(loaded)
            stored_ordered = store.write_ordered(str(ordered_path), envelope)
            service = StructureViewService(envelope, loaded)
            ambiguous = service.entity_candidates(
                snapshot_id=bundle_a.snapshot_id,
                mention="common-lib",
                entity_type=EntityType.MAVEN_MODULE,
            )
            shared = service.entity_candidates(
                snapshot_id=bundle_a.snapshot_id,
                mention="common-lib",
                entity_type=EntityType.MAVEN_MODULE,
                canonical_ga="org.example.shared:common-lib",
            )
            legacy = service.entity_candidates(
                snapshot_id=bundle_a.snapshot_id,
                mention="common-lib",
                entity_type=EntityType.MAVEN_MODULE,
                canonical_ga="org.example.legacy:common-lib",
            )
            self.assertEqual(
                ambiguous.payload["resolution_status"],
                EntityResolutionStatus.AMBIGUOUS.value,
            )
            self.assertEqual(ambiguous.payload["candidate_count"], 2)
            for result in (shared, legacy):
                self.assertEqual(
                    result.payload["resolution_status"],
                    EntityResolutionStatus.UNIQUE.value,
                )
                self.assertEqual(result.payload["candidate_count"], 1)
            candidate_gas = {
                item["canonical_ga"] for item in ambiguous.payload["candidates"]
            }
            answer_oracle = oracle["valid"]["billing_common_lib_answer"]
            self.assertEqual(
                candidate_gas,
                {
                    answer_oracle["actual_target_ga"],
                    answer_oracle["other_same_artifact_ga"],
                },
            )
            billing = service.entity_candidates(
                snapshot_id=bundle_a.snapshot_id,
                mention="billing",
                entity_type=EntityType.MAVEN_MODULE,
                canonical_ga=answer_oracle["source_ga"],
            )
            self.assertEqual(
                billing.payload["resolution_status"],
                EntityResolutionStatus.UNIQUE.value,
            )
            billing_argument = StructureEntityArgument.from_unique_candidate(billing)
            shared_path = service.path_exists(
                source=billing_argument,
                target=StructureEntityArgument.from_unique_candidate(shared),
            )
            legacy_path = service.path_exists(
                source=billing_argument,
                target=StructureEntityArgument.from_unique_candidate(legacy),
            )
            self.assertTrue(shared_path.payload["exists"])
            self.assertFalse(legacy_path.payload["exists"])
            self.assertTrue(legacy_path.payload["negative_conclusion_supported"])
            return {
                "fixture_semantics": "maven-identity-anti-name-stitch@1",
                "fixture": {
                    "path": str(
                        _maven_structure_tests.FIXTURE_ROOT.relative_to(PROJECT_ROOT)
                    ),
                    "digest": f"sha256:{fixture_digest}",
                    "digest_input": "sha256-of-sorted-per-file-sha256-lines",
                    "oracle_path": str(oracle_path.relative_to(PROJECT_ROOT)),
                    "oracle_sha256": f"sha256:{sha256(oracle_path.read_bytes()).hexdigest()}",
                },
                "g1_output": {
                    "profile_ref": evaluated[0].coverage.root.profile_ref,
                    "schema_ref": evaluated[0].coverage.root.schema_ref,
                    "a_complete": evaluated[0].report.complete,
                    "b_complete": evaluated[1].report.complete,
                    "a_entity_count": len(evaluated[0].entities),
                    "a_relation_count": len(evaluated[0].relations),
                    "a_module_gas": sorted(self._identity_module_gas(evaluated[0])),
                    "a_dependency_edges": self._identity_dependency_edges(
                        evaluated[0]
                    ),
                    "oracle_alignment": "PASS",
                },
                "snapshot_ids": [
                    bundle_a.snapshot_id.value,
                    bundle_b.snapshot_id.value,
                ],
                "snapshot_paths": [str(a_path), str(b_path)],
                "ordered_path": str(ordered_path),
                "stored": {
                    "a_bundle_digest": stored_a.bundle_digest.value,
                    "a_file_digest": stored_a.file_digest.value,
                    "b_bundle_digest": stored_b.bundle_digest.value,
                    "b_file_digest": stored_b.file_digest.value,
                    "ordered_bundle_digest": stored_ordered.bundle_digest.value,
                    "ordered_file_digest": stored_ordered.file_digest.value,
                },
                "results": {
                    "common-lib-ambiguous": self._view_payload(ambiguous),
                    "common-lib-shared-exact-ga": self._view_payload(shared),
                    "common-lib-legacy-exact-ga": self._view_payload(legacy),
                    "billing-unique": self._view_payload(billing),
                    "billing-to-shared-path": self._view_payload(shared_path),
                    "billing-to-legacy-path": self._view_payload(legacy_path),
                },
            }
        finally:
            fixture.tearDown()

    def _identity_snapshot_bundle(self, snapshot, result):
        return StructureSnapshotReadBundle.create(
            snapshot=snapshot,
            coverages=(result.coverage,),
            entities=result.entities,
            relation_facts=result.relations,
            literal_facts=(),
            upstream_entity_records=(),
            evidence_metadata=tuple(
                StructureEvidenceMetadata.from_evidence(item)
                for item in result.evidence
            ),
        )

    def _assert_identity_oracle(
        self,
        result,
        oracle: dict[str, object],
    ) -> None:
        expected = oracle["valid"]
        self.assertEqual(
            self._identity_module_gas(result),
            set(expected["reactor_modules"]),
        )
        self.assertEqual(
            sum(
                item.root.predicate is RelationPredicate.CONTAINS_MODULE
                for item in result.relations
            ),
            expected["contains_module_count"],
        )
        expected_edges = {
            (item["source"], item["target"])
            for item in (
                *expected["root_project_internal_depends_on"],
                *expected["internal_depends_on"],
            )
        }
        self.assertEqual(
            set(map(tuple, self._identity_dependency_edges(result))),
            expected_edges,
        )
        forbidden_edges = {
            (item["source"], item["target"])
            for item in expected["forbidden_internal_edges"]
        }
        self.assertFalse(
            set(map(tuple, self._identity_dependency_edges(result)))
            & forbidden_edges
        )

    @staticmethod
    def _identity_module_gas(result) -> set[str]:
        return {
            f"{item.root.root_fields['effective_group_id']}:{item.root.root_fields['artifact_id']}"
            for item in result.modules
        }

    @staticmethod
    def _identity_dependency_edges(result) -> list[list[str]]:
        ga_by_root = {}
        for item in result.entities:
            root_fields = item.root.root_fields
            state_fields = item.state.state_payload_fields
            group_id = (
                root_fields["effective_group_id"]
                if "effective_group_id" in root_fields
                else state_fields["effective_group_id"]
            )
            artifact_id = (
                root_fields["artifact_id"]
                if "artifact_id" in root_fields
                else state_fields["artifact_id"]
            )
            ga_by_root[item.root_id] = f"{group_id}:{artifact_id}"
        return sorted(
            [
                ga_by_root[item.root.subject.entity_root_id],
                ga_by_root[item.root.object.entity_root_id],
            ]
            for item in result.relations
            if item.root.predicate is RelationPredicate.DEPENDS_ON
        )

    def _inventory(
        self,
        service: StructureViewService,
        snapshot_id: StableId,
        results: dict[str, StructureViewResult],
        name: str,
    ) -> StructureViewResult:
        system = self._unique_argument(
            service,
            snapshot_id,
            "mall",
            entity_type=EntityType.SOFTWARE_SYSTEM,
            results=results,
            name=f"candidate-{name}-system",
        )
        result = service.child_module_inventory(system=system)
        results[name] = result
        return result

    def _all_paths(
        self,
        service: StructureViewService,
        bundle,
        *,
        source: str,
        target: str,
        results: dict[str, StructureViewResult],
        name: str,
    ) -> StructureViewResult:
        source_argument = self._unique_argument(
            service,
            bundle.snapshot_id,
            source,
            entity_type=EntityType.MAVEN_MODULE,
            results=results,
            name=f"candidate-{name}-source",
        )
        target_argument = self._unique_argument(
            service,
            bundle.snapshot_id,
            target,
            entity_type=EntityType.MAVEN_MODULE,
            results=results,
            name=f"candidate-{name}-target",
        )
        result = service.all_simple_paths(
            source=source_argument,
            target=target_argument,
            predicate=RelationPredicate.DEPENDS_ON,
        )
        results[name] = result
        return result

    def _path_exists(
        self,
        service: StructureViewService,
        bundle,
        *,
        source: str,
        target: str,
        results: dict[str, StructureViewResult],
        name: str,
        source_type: EntityType = EntityType.MAVEN_MODULE,
    ) -> StructureViewResult:
        source_argument = self._unique_argument(
            service,
            bundle.snapshot_id,
            source,
            entity_type=source_type,
            results=results,
            name=f"candidate-{name}-source",
        )
        target_argument = self._unique_argument(
            service,
            bundle.snapshot_id,
            target,
            entity_type=EntityType.MAVEN_MODULE,
            results=results,
            name=f"candidate-{name}-target",
        )
        result = service.path_exists(
            source=source_argument,
            target=target_argument,
            predicate=RelationPredicate.DEPENDS_ON,
        )
        results[name] = result
        return result

    def _unique_argument(
        self,
        service: StructureViewService,
        snapshot_id: StableId,
        mention: str,
        *,
        entity_type: EntityType,
        results: dict[str, StructureViewResult],
        name: str,
    ) -> StructureEntityArgument:
        result = service.entity_candidates(
            snapshot_id=snapshot_id,
            mention=mention,
            entity_type=entity_type,
        )
        results[name] = result
        self.assertEqual(
            result.payload["resolution_status"],
            EntityResolutionStatus.UNIQUE.value,
        )
        self.assertEqual(result.payload["candidate_count"], 1)
        return StructureEntityArgument.from_unique_candidate(result)

    @staticmethod
    def _inventory_gavs(result: StructureViewResult) -> set[str]:
        return {item["canonical_gav"] for item in result.payload["modules"]}

    @staticmethod
    def _path_artifact_ids(bundle, result: StructureViewResult) -> list[list[str]]:
        artifact_by_root = {
            item.root_id.value: item.root.root_fields["artifact_id"]
            for item in bundle.entities
            if item.root.entity_type is EntityType.MAVEN_MODULE
        }
        return sorted(
            [artifact_by_root[root_id] for root_id in path["entity_root_ids"]]
            for path in result.payload["paths"]
        )

    def _assert_no_payload(self, value: object) -> dict[str, object]:
        keys: set[str] = set()

        def collect(item: object) -> None:
            if isinstance(item, Mapping):
                keys.update(item)
                for nested in item.values():
                    collect(nested)
            elif isinstance(item, (list, tuple)):
                for nested in item:
                    collect(nested)

        collect(value)
        forbidden = sorted(keys & self._FORBIDDEN_PAYLOAD_KEYS)
        self.assertEqual(forbidden, [])
        self.assertIn("excerpt_digest", keys)
        return {
            "forbidden_keys": sorted(self._FORBIDDEN_PAYLOAD_KEYS),
            "found_forbidden_keys": forbidden,
            "evidence_excerpt_digest_present": "excerpt_digest" in keys,
            "status": "PASS",
        }

    @staticmethod
    def _view_payload(result: StructureViewResult) -> dict[str, object]:
        return json.loads(canonical_json_bytes(result.canonical_value()))

    def _authority_counts(self) -> dict[str, int]:
        tables = (
            "knw_structure_snapshot_roots",
            "knw_structure_snapshots",
            "knw_structure_snapshot_members",
            "knw_structure_snapshot_coverages",
            "knw_structure_evidence",
            "src_operation_roots",
            "src_operation_revisions",
            "src_operation_authorities",
            "src_observations",
        )
        connection = sqlite3.connect(self.fixture.database)
        try:
            return {
                table: connection.execute(
                    f'SELECT COUNT(*) FROM "{table}"'
                ).fetchone()[0]
                for table in tables
            }
        finally:
            connection.close()

    def _materialize_and_project_citations(
        self, result: StructureViewResult
    ) -> dict[str, object]:
        citation_store = self.base / "citation-store"
        with SqliteDatabase(self.fixture.database) as database:
            owner = SqliteStructureKnowledgeRepository(database)
            materialization = CitationObservationBroker(
                owner,
                FileCitationObservationStoreWriter(citation_store),
            ).materialize(result)
        projection = CitationProjector(
            FileCitationObservationStoreReader(citation_store)
        ).project(materialization.seal)
        self.citation_store = citation_store
        self.citation_seal = materialization.seal

        receipt = materialization.receipt
        self.assertEqual(projection.result_id, result.result_id)
        self.assertEqual(materialization.seal.view_digest, result.digest)
        self.assertEqual(projection.result_digest, materialization.seal.digest)
        self.assertEqual(projection.store_id, receipt.store_id)
        self.assertEqual(
            tuple(item.evidence_id for item in projection.citations),
            result.evidence_allowlist,
        )
        self.assertEqual(len(projection.citations), receipt.observation_count)
        self.assertTrue(all(item.observation for item in projection.citations))
        return {
            "source_view_result_id": result.result_id.value,
            "source_view_digest": result.digest.value,
            "seal_digest": materialization.seal.digest.value,
            "allowlist_digest": materialization.seal.allowlist_digest.value,
            "store_id": receipt.store_id.value,
            "store_manifest_digest": receipt.manifest_digest.value,
            "observation_count": receipt.observation_count,
            "projection_digest": projection.digest.value,
            "citations": [
                {
                    "evidence_id": item.evidence_id.value,
                    "artifact_id": item.artifact_id.value,
                    "source_context_id": item.source_context_id.value,
                    "locator": item.locator,
                    "byte_start": item.byte_start,
                    "byte_end": item.byte_end,
                    "excerpt_digest": item.excerpt_digest.value,
                    "evidence_digest": item.evidence_digest.value,
                    "observation": item.observation,
                    "digest": item.digest.value,
                }
                for item in projection.citations
            ],
        }

    def _stage_isolation_if_requested(
        self,
        *,
        snapshot_receipts: dict[str, dict[str, object]],
        ordered_receipts: dict[str, dict[str, object]],
        identity_bundles: dict[str, object],
        summary: dict[str, object],
    ) -> None:
        configured = os.environ.get("ITER003_G2_STAGE_DIR")
        if configured is None:
            return
        stage_root = Path(configured)
        if (
            not stage_root.is_absolute()
            or stage_root.resolve(strict=False) != stage_root
            or stage_root.exists()
        ):
            raise AssertionError(
                "ITER003_G2_STAGE_DIR must be a new canonical absolute path"
            )
        stage_root.mkdir()
        answer_package = stage_root / "answer" / "package"
        answer_bundles = stage_root / "answer" / "bundles"
        answer_output = stage_root / "answer" / "output"
        projector_package = stage_root / "projector" / "package"
        projector_input = stage_root / "projector" / "input"
        projector_store = stage_root / "projector" / "store"
        projector_output = stage_root / "projector" / "output"
        for directory in (
            answer_package,
            answer_bundles,
            answer_output,
            projector_package,
            projector_input,
            projector_output,
        ):
            directory.mkdir(parents=True)

        ignore = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
        for package_root, workload_name in (
            (answer_package, "answer_workload.py"),
            (projector_package, "projector_workload.py"),
        ):
            shutil.copytree(
                PROJECT_ROOT / "src" / "software_world_model",
                package_root / "software_world_model",
                ignore=ignore,
            )
            shutil.copy2(ISOLATION_ROOT / workload_name, package_root / workload_name)

        staged_bundles: dict[str, Path] = {}
        for name, receipt in sorted(snapshot_receipts.items()):
            source = Path(receipt["stored_bundle"]["locator"])
            target = answer_bundles / f"{name}.snapshot.json"
            shutil.copy2(source, target)
            staged_bundles[name] = target
        for name, receipt in sorted(ordered_receipts.items()):
            source = Path(receipt["stored_bundle"]["locator"])
            target = answer_bundles / f"{name}.ordered.json"
            shutil.copy2(source, target)
            staged_bundles[name] = target
        identity_paths = tuple(Path(item) for item in identity_bundles["snapshot_paths"])
        for label, source in zip(("identity-a", "identity-b"), identity_paths):
            target = answer_bundles / f"{label}.snapshot.json"
            shutil.copy2(source, target)
            staged_bundles[label] = target
        identity_ordered = answer_bundles / "identity-a-b.ordered.json"
        shutil.copy2(Path(identity_bundles["ordered_path"]), identity_ordered)
        staged_bundles["identity-a-b"] = identity_ordered

        shutil.copytree(self.citation_store, projector_store)
        store_allowlist = sorted(
            path.relative_to(projector_store).as_posix()
            for path in projector_store.rglob("*")
            if path.is_file()
        )

        evidence_root = stage_root.parent
        forbidden_database = evidence_root / "g2-authority-with-evidence.sqlite3"
        if forbidden_database.exists():
            raise AssertionError("G2 forbidden authority DB target already exists")
        shutil.copy2(self.fixture.database, forbidden_database)
        config_path = evidence_root / "isolation-config.json"
        if config_path.exists():
            raise AssertionError("G2 isolation config target already exists")

        answer_query_report = answer_output / "query-report.json"
        answer_seal = answer_output / "sealed-result.json"
        projector_seal = projector_input / "sealed-result.json"
        projection_output = projector_output / "citation-projection.json"
        config = {
            "schema": "iteration-003-g2-isolation-config@1",
            "stage_root": str(stage_root),
            "python_executable": str(Path(sys.executable).resolve(strict=True)),
            "source_remote": {"host": "github.com", "port": 443},
            "public_endpoint": {"host": "1.1.1.1", "port": 443},
            "dns_host": "example.com",
            "forbidden": {
                "file": str(_g1_integration.MALL_REPOSITORY / "pom.xml"),
                "sqlite": str(forbidden_database),
                "git_root": str(_g1_integration.MALL_REPOSITORY),
                "git_marker": str(
                    _g1_integration.MALL_REPOSITORY / ".git" / "HEAD"
                ),
            },
            "answer": {
                "package_root": str(answer_package),
                "bundle_root": str(answer_bundles),
                "output_root": str(answer_output),
                "package_canary": str(answer_package / "answer_workload.py"),
                "bundle_canary": str(staged_bundles["a1"]),
                "sealed_result": str(answer_seal),
                "workload": {
                    "entrypoint": "answer_workload.py",
                    "argv": [
                        "--a1-b-envelope",
                        str(staged_bundles["a1-b"]),
                        "--b-a2-envelope",
                        str(staged_bundles["b-a2"]),
                        "--a1-bundle",
                        str(staged_bundles["a1"]),
                        "--b-bundle",
                        str(staged_bundles["b"]),
                        "--a2-bundle",
                        str(staged_bundles["a2"]),
                        "--identity-envelope",
                        str(staged_bundles["identity-a-b"]),
                        "--identity-a-bundle",
                        str(staged_bundles["identity-a"]),
                        "--identity-b-bundle",
                        str(staged_bundles["identity-b"]),
                        "--query-report-output",
                        str(answer_query_report),
                        "--citation-seal-output",
                        str(answer_seal),
                    ],
                    "stdout_output": "workload-stdout.json",
                    "expected_outputs": [
                        "workload-stdout.json",
                        "query-report.json",
                        "sealed-result.json",
                    ],
                },
            },
            "projector": {
                "package_root": str(projector_package),
                "sealed_result": str(projector_seal),
                "store_root": str(projector_store),
                "store_allowlist": store_allowlist,
                "output_root": str(projector_output),
                "package_canary": str(
                    projector_package / "projector_workload.py"
                ),
                "store_canary": str(projector_store / "manifest.json"),
                "workload": {
                    "entrypoint": "projector_workload.py",
                    "argv": [
                        "--sealed-result",
                        str(projector_seal),
                        "--store",
                        str(projector_store),
                        "--projection-output",
                        str(projection_output),
                    ],
                    "stdout_output": "workload-stdout.json",
                    "expected_outputs": [
                        "workload-stdout.json",
                        "citation-projection.json",
                    ],
                },
            },
            "timeout_seconds": 120,
        }
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (evidence_root / "staging-summary.json").write_text(
            json.dumps(
                {
                    "schema": "iteration-003-g2-staging-summary@1",
                    "isolation_config": str(config_path),
                    "stage_root": str(stage_root),
                    "connected_summary": summary,
                    "citation_seal_digest": self.citation_seal.digest.value,
                    "store_allowlist": store_allowlist,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

    def _write_report(self, name: str, payload: dict[str, object]) -> None:
        configured = os.environ.get("ITER003_G2_REPORT_DIR")
        if configured is None:
            return
        report_directory = Path(configured)
        report_directory.mkdir(parents=True, exist_ok=True)
        (report_directory / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
