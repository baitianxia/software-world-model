from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
from unittest import TestCase

from software_world_model.application_services.citation_projection import (
    CitationObservationBroker,
    CitationProjector,
)
from software_world_model.application_services.java_static_call import (
    JavaSourceEvidenceMetadata,
    JavaStaticCallError,
    JavaStaticCallInput,
    evaluate_java_static_calls,
)
from software_world_model.application_services.knowledge_use import TaskBoundary
from software_world_model.application_services.maven_structure import GitEntryMetadata
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
    NeighborhoodDirection,
    StructureEntityArgument,
    StructureViewCompleteness,
    StructureViewOperation,
    StructureViewService,
)
from software_world_model.cross_cutting import (
    Digest,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.infrastructure.sqlite_structure_read_session_repository import (
    SqliteStructureReadSessionRepository,
)
from software_world_model.infrastructure.file_citation_observation_store import (
    FileCitationObservationStoreReader,
    FileCitationObservationStoreWriter,
)
from software_world_model.knowledge_engine.structure import (
    CoverageMemberKind,
    EntityType,
    ObservationModality,
    PublicationMode,
    RelationPredicate,
    StructureEvidence,
)
from software_world_model.knowledge_engine.structure_authority import (
    StructureSchemaDefinition,
)
from software_world_model.knowledge_engine.structure_publication import (
    StructureEvidenceMetadata,
)
from tests import test_structure_publication as _publication_tests


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_ROOT = (
    REPOSITORY_ROOT / "validation" / "structure_world_model_iteration_006"
)
FIXTURE_ROOT = VALIDATION_ROOT / "fixtures"
SOURCE_ROOT = "src/main/java"
SCOPE_ID = StableId("scope_11111111111111111111111111111111")
SOURCE_BINDING_ID = StableId("binding_22222222222222222222222222222222")


def _stable(kind: str, value: str) -> StableId:
    suffix = hashlib.sha256(value.encode("utf-8")).hexdigest()[-32:]
    return StableId(f"{kind}_{suffix}")


def _content_digest(payload: bytes) -> Digest:
    return Digest(f"sha256:{hashlib.sha256(payload).hexdigest()}")


def _fixture_input(
    name: str,
    *,
    scope_id: StableId = SCOPE_ID,
    source_binding_id: StableId = SOURCE_BINDING_ID,
) -> JavaStaticCallInput:
    revision_root = FIXTURE_ROOT / name
    pairs = tuple(
        (path.relative_to(revision_root).as_posix(), path.read_bytes())
        for path in sorted(revision_root.rglob("*.java"))
    )
    source_context_id = _stable("source_context", name)
    entries = {
        path: GitEntryMetadata(
            mode="100644",
            object_type="blob",
            object_id=hashlib.sha1(payload).hexdigest(),
        )
        for path, payload in pairs
    }
    source_evidence = {
        path: JavaSourceEvidenceMetadata(
            artifact_id=_stable("source_artifact", f"{name}:{path}"),
            source_context_id=source_context_id,
            artifact_content_digest=_content_digest(payload),
            locator=path,
        )
        for path, payload in pairs
    }
    tree_excerpt = "\n".join(
        json.dumps(
            {
                "is_symlink": metadata.is_symlink,
                "mode": metadata.mode,
                "object_id": metadata.object_id,
                "path": path,
                "type": metadata.object_type,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for path, metadata in sorted(entries.items())
    )
    tree_payload = tree_excerpt.encode("utf-8")
    tree_evidence = StructureEvidence.create(
        artifact_id=_stable("source_artifact", f"tree:{name}"),
        source_context_id=source_context_id,
        byte_start=0,
        byte_end=len(tree_payload),
        locator=f"git-tree:{name}:all",
        excerpt=tree_excerpt,
        artifact_content_digest=_content_digest(tree_payload),
    )
    return JavaStaticCallInput(
        owning_scope_id=scope_id,
        source_binding_id=source_binding_id,
        source_revision=name,
        knowledge_context_digest=digest_of(
            {"source_revision": name, "profile": "java-static-call"}
        ),
        source_bytes=dict(pairs),
        git_entries=entries,
        source_evidence=source_evidence,
        tree_evidence=(tree_evidence,),
        logical_source_root=SOURCE_ROOT,
    )


def _replace_source(
    value: JavaStaticCallInput,
    path: str,
    payload: bytes,
) -> JavaStaticCallInput:
    source_bytes = {**value.source_bytes, path: payload}
    git_entries = {
        **value.git_entries,
        path: replace(
            value.git_entries[path],
            object_id=hashlib.sha1(payload).hexdigest(),
        ),
    }
    source_evidence = {
        **value.source_evidence,
        path: replace(
            value.source_evidence[path],
            artifact_content_digest=_content_digest(payload),
        ),
    }
    return replace(
        value,
        source_bytes=source_bytes,
        git_entries=git_entries,
        source_evidence=source_evidence,
        tree_evidence=(_rebuilt_tree_evidence(value, git_entries),),
    )


def _rebuilt_tree_evidence(
    value: JavaStaticCallInput,
    git_entries: dict[str, GitEntryMetadata],
) -> StructureEvidence:
    tree_excerpt = "\n".join(
        json.dumps(
            {
                "is_symlink": metadata.is_symlink,
                "mode": metadata.mode,
                "object_id": metadata.object_id,
                "path": item_path,
                "type": metadata.object_type,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for item_path, metadata in sorted(git_entries.items())
    )
    tree_payload = tree_excerpt.encode("utf-8")
    previous_tree = value.tree_evidence[0]
    return StructureEvidence.create(
        artifact_id=previous_tree.artifact_id,
        source_context_id=previous_tree.source_context_id,
        byte_start=0,
        byte_end=len(tree_payload),
        locator=previous_tree.locator,
        excerpt=tree_excerpt,
        artifact_content_digest=_content_digest(tree_payload),
    )


def _type_name(record: object) -> str:
    return str(record.root.root_fields["qualified_name"])


def _method_signature(record: object) -> str:
    fields = record.root.root_fields
    parameters = ",".join(str(value) for value in fields["parameter_types"])
    return (
        f"{fields['declaring_type_qualified_name']}#"
        f"{fields['method_name']}({parameters})"
    )


def _call_set(result: object) -> set[tuple[str, str]]:
    signatures = {
        record.root_id: _method_signature(record) for record in result.methods
    }
    return {
        (
            signatures[relation.root.subject.entity_root_id],
            signatures[relation.root.object.entity_root_id],
        )
        for relation in result.relations
        if relation.root.predicate is RelationPredicate.CALLS
    }


def _source_evidence(result: object) -> list[dict[str, str]]:
    return [
        {"locator": item.locator, "excerpt": item.excerpt}
        for item in sorted(result.evidence, key=lambda value: value.locator)
        if ";kind=java-" in item.locator
    ]


def _snapshot_bundle(repository: object, snapshot_id: StableId) -> StructureSnapshotReadBundle:
    snapshot = repository.get_snapshot(snapshot_id)
    entities = tuple(
        repository.get_entity(snapshot.snapshot_id, member.root_id)
        for member in snapshot.members
        if member.kind is CoverageMemberKind.ENTITY
    )
    relations = tuple(
        repository.get_relation_fact(snapshot.snapshot_id, member.root_id)
        for member in snapshot.members
        if member.kind is CoverageMemberKind.RELATION_FACT
    )
    coverages = tuple(
        repository.get_coverage(
            snapshot.snapshot_id, binding.coverage_root_id
        )
        for binding in snapshot.coverages
    )
    evidence_ids = {
        reference
        for record in (*entities, *relations)
        for reference in record.state.evidence_references
    }
    evidence_ids.update(
        reference
        for coverage in coverages
        for reference in coverage.state.evidence_references
    )
    return StructureSnapshotReadBundle.create(
        snapshot=snapshot,
        coverages=coverages,
        entities=entities,
        relation_facts=relations,
        literal_facts=(),
        upstream_entity_records=(),
        evidence_metadata=tuple(
            repository.get_evidence_metadata(item)
            for item in sorted(evidence_ids, key=lambda value: value.value)
        ),
    )


class JavaStaticCallEvaluatorTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.oracle = json.loads(
            (VALIDATION_ROOT / "oracle.json").read_text(encoding="utf-8")
        )["revisions"]

    def test_r1_matches_independent_oracle_and_ignores_comment_and_string_decoys(
        self,
    ) -> None:
        result = evaluate_java_static_calls(_fixture_input("r1"))
        expected = self.oracle["r1"]

        self.assertEqual({_type_name(item) for item in result.types}, set(expected["types"]))
        self.assertEqual(
            {_method_signature(item) for item in result.methods},
            set(expected["methods"]),
        )
        self.assertEqual(_call_set(result), {tuple(item) for item in expected["calls"]})
        self.assertEqual(_source_evidence(result), expected["evidence"])
        self.assertEqual(result.report.call_site_count, 3)
        self.assertEqual(result.report.call_relation_count, 3)
        self.assertNotIn(
            (
                "com.acme.flow.FlowService#start(String)",
                "com.acme.flow.FlowService#finish(String)",
            ),
            _call_set(result),
        )
        self.assertEqual(
            {item.root.entity_type for item in result.entities},
            {EntityType.JAVA_TYPE, EntityType.JAVA_METHOD},
        )
        self.assertEqual(
            {item.root.predicate for item in result.relations},
            {RelationPredicate.DECLARES_METHOD, RelationPredicate.CALLS},
        )
        self.assertEqual(
            {
                item.root.observation_modality
                for item in result.relations
                if item.root.predicate is RelationPredicate.CALLS
            },
            {ObservationModality.JAVA_SOURCE_STATIC_CALL},
        )
        self.assertEqual(result.batch.publication_mode, PublicationMode.REPLACE_COVERAGE)
        self.assertEqual(
            {item.kind for item in result.complete_member_manifest.members},
            {CoverageMemberKind.ENTITY, CoverageMemberKind.RELATION_FACT},
        )
        result.batch.require_admissible()

    def test_r2_changes_membership_without_changing_surviving_roots(self) -> None:
        r1 = evaluate_java_static_calls(_fixture_input("r1"))
        r2 = evaluate_java_static_calls(_fixture_input("r2"))

        self.assertEqual(
            {_method_signature(item) for item in r2.methods},
            set(self.oracle["r2"]["methods"]),
        )
        self.assertEqual(_call_set(r2), {tuple(item) for item in self.oracle["r2"]["calls"]})
        self.assertEqual(_source_evidence(r2), self.oracle["r2"]["evidence"])
        r1_roots = {_method_signature(item): item.root_id for item in r1.methods}
        r2_roots = {_method_signature(item): item.root_id for item in r2.methods}
        for signature in set(r1_roots) & set(r2_roots):
            self.assertEqual(r1_roots[signature], r2_roots[signature])
        self.assertEqual(r2.report.method_count, 5)
        self.assertEqual(r2.report.call_site_count, 4)

    def test_ambiguous_name_and_arity_rejects_the_complete_candidate(self) -> None:
        with self.assertRaises(JavaStaticCallError) as caught:
            evaluate_java_static_calls(_fixture_input("r3-unsupported"))

        self.assertEqual(
            caught.exception.reason_code,
            self.oracle["r3-unsupported"]["reason_code"],
        )
        self.assertIn("FlowService.java#bytes=", caught.exception.locator)

    def test_unresolved_in_scope_call_rejects_the_complete_candidate(self) -> None:
        value = _fixture_input("r1")
        path = next(item for item in value.source_bytes if item.endswith("FlowService.java"))
        payload = value.source_bytes[path].replace(
            b"Audit.record(input);",
            b"missing(input);",
        )

        with self.assertRaises(JavaStaticCallError) as caught:
            evaluate_java_static_calls(_replace_source(value, path, payload))

        self.assertEqual(
            caught.exception.reason_code,
            "JAVA_CALL_TARGET_UNRESOLVED",
        )

    def test_variable_receiver_rejects_the_complete_candidate(self) -> None:
        value = _fixture_input("r1")
        path = next(item for item in value.source_bytes if item.endswith("FlowService.java"))
        payload = value.source_bytes[path].replace(
            b"Audit.record(input);",
            b"audit.record(input);",
        )

        with self.assertRaises(JavaStaticCallError) as caught:
            evaluate_java_static_calls(_replace_source(value, path, payload))

        self.assertEqual(
            caught.exception.reason_code,
            "JAVA_CALL_RECEIVER_UNSUPPORTED",
        )

    def test_truncated_source_rejects_the_complete_candidate(self) -> None:
        value = _fixture_input("r1")
        path = next(item for item in value.source_bytes if item.endswith("FlowService.java"))
        payload = value.source_bytes[path].rstrip()[:-1] + b"\n"

        with self.assertRaises(JavaStaticCallError) as caught:
            evaluate_java_static_calls(_replace_source(value, path, payload))

        self.assertEqual(
            caught.exception.reason_code,
            "JAVA_DELIMITER_UNBALANCED",
        )

    def test_source_content_digest_tamper_fails_closed(self) -> None:
        value = _fixture_input("r1")
        path = sorted(value.source_evidence)[0]
        metadata = value.source_evidence[path]
        tampered = {
            **value.source_evidence,
            path: replace(metadata, artifact_content_digest=Digest("sha256:" + "0" * 64)),
        }

        with self.assertRaises(JavaStaticCallError) as caught:
            evaluate_java_static_calls(replace(value, source_evidence=tampered))

        self.assertEqual(
            caught.exception.reason_code,
            "JAVA_SOURCE_CONTENT_DIGEST_MISMATCH",
        )

    def test_tree_evidence_must_match_exact_git_metadata(self) -> None:
        value = _fixture_input("r1")
        path = sorted(value.git_entries)[0]
        tampered_entries = {
            **value.git_entries,
            path: replace(value.git_entries[path], object_id="f" * 40),
        }

        with self.assertRaises(JavaStaticCallError) as caught:
            evaluate_java_static_calls(replace(value, git_entries=tampered_entries))

        self.assertEqual(caught.exception.reason_code, "JAVA_TREE_EVIDENCE_MISMATCH")

    def test_symlink_source_entry_rejects_the_complete_candidate(self) -> None:
        value = _fixture_input("r1")
        path = sorted(value.git_entries)[0]
        entries = {
            **value.git_entries,
            path: replace(value.git_entries[path], mode="120000"),
        }

        with self.assertRaises(JavaStaticCallError) as caught:
            evaluate_java_static_calls(
                replace(
                    value,
                    git_entries=entries,
                    tree_evidence=(_rebuilt_tree_evidence(value, entries),),
                )
            )

        self.assertEqual(
            caught.exception.reason_code,
            "JAVA_SOURCE_ENTRY_UNSUPPORTED",
        )


class JavaBehaviorViewTests(TestCase):
    def setUp(self) -> None:
        self.fixture = _publication_tests.StructurePublicationTests(
            methodName="runTest"
        )
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.fixture.registry.register(
            definition=StructureSchemaDefinition.java_static_call_graph(),
            idempotency_key=IdempotencyKey("register-java-static-call-schema"),
            proposal_ref="ITER-006-PROPOSAL",
            review_ref="ITER-006-READINESS",
            registered_by="test",
            reason="ITER-006 frozen Java definition",
        )
        self.evaluation = evaluate_java_static_calls(
            _fixture_input(
                "r1",
                scope_id=self.fixture.scope.scope_id,
                source_binding_id=self.fixture.binding,
            )
        )
        receipt = self.fixture.publish(
            self.evaluation.batch,
            key="java-view-r1",
            expected=None,
        )
        repository = self.fixture.repository
        snapshot = repository.get_snapshot(receipt.snapshot.snapshot_id)
        self.bundle = _snapshot_bundle(repository, snapshot.snapshot_id)
        r2_evaluation = evaluate_java_static_calls(
            _fixture_input(
                "r2",
                scope_id=self.fixture.scope.scope_id,
                source_binding_id=self.fixture.binding,
            )
        )
        r2_receipt = self.fixture.publish(
            r2_evaluation.batch,
            key="java-view-r2",
            expected=snapshot.snapshot_id,
        )
        self.r2_bundle = _snapshot_bundle(
            repository, r2_receipt.snapshot.snapshot_id
        )
        sessions = StructureReadSessionService(
            SqliteStructureReadSessionRepository(self.fixture.database),
            repository,
            self.fixture.scopes,
            clock=self.fixture.clock,
        )
        session = sessions.open_ordered(
            scope_id=self.fixture.scope.scope_id,
            scope_revision=self.fixture.scope.definition_revision,
            task_boundary=TaskBoundary.create(
                task_id=StableId("task_" + "6" * 32),
                task_revision=Revision(1),
                scope_id=self.fixture.scope.scope_id,
                purpose=StructureReadPurpose.EXACT_SNAPSHOT.value,
                classification="INTERNAL",
            ),
            caller_ref="java-behavior-view-test",
            snapshot_ids=(snapshot.snapshot_id,),
            idempotency_key=IdempotencyKey("java-view-read-session"),
        )
        file_digest = digest_of({"file": "java-r1-bundle"})
        binding = session.snapshots[0]
        envelope = StructureOrderedReadBundle.create(
            session=session,
            snapshots=(
                StructureSnapshotBundleReference(
                    ordinal=0,
                    snapshot_id=snapshot.snapshot_id,
                    snapshot_binding_digest=binding.digest,
                    snapshot_manifest_digest=binding.snapshot_manifest_digest,
                    bundle_digest=self.bundle.digest,
                    file_digest=file_digest,
                ),
            ),
        )
        self.service = StructureViewService(
            envelope, ((self.bundle, file_digest),)
        )
        ordered_session = sessions.open_ordered(
            scope_id=self.fixture.scope.scope_id,
            scope_revision=self.fixture.scope.definition_revision,
            task_boundary=TaskBoundary.create(
                task_id=StableId("task_" + "7" * 32),
                task_revision=Revision(1),
                scope_id=self.fixture.scope.scope_id,
                purpose=StructureReadPurpose.SNAPSHOT_COMPARISON.value,
                classification="INTERNAL",
            ),
            caller_ref="java-behavior-ordered-view-test",
            snapshot_ids=(self.bundle.snapshot_id, self.r2_bundle.snapshot_id),
            idempotency_key=IdempotencyKey("java-ordered-view-read-session"),
        )
        r2_file_digest = digest_of({"file": "java-r2-bundle"})
        ordered_envelope = StructureOrderedReadBundle.create(
            session=ordered_session,
            snapshots=tuple(
                StructureSnapshotBundleReference(
                    ordinal=ordinal,
                    snapshot_id=bundle.snapshot_id,
                    snapshot_binding_digest=binding.digest,
                    snapshot_manifest_digest=binding.snapshot_manifest_digest,
                    bundle_digest=bundle.digest,
                    file_digest=bundle_digest,
                )
                for ordinal, (binding, bundle, bundle_digest) in enumerate(
                    zip(
                        ordered_session.snapshots,
                        (self.bundle, self.r2_bundle),
                        (file_digest, r2_file_digest),
                        strict=True,
                    )
                )
            ),
        )
        self.ordered_service = StructureViewService(
            ordered_envelope,
            (
                (self.bundle, file_digest),
                (self.r2_bundle, r2_file_digest),
            ),
        )

    def _argument(
        self, mention: str, entity_type: EntityType
    ) -> StructureEntityArgument:
        candidates = self.service.entity_candidates(
            snapshot_id=self.bundle.snapshot_id,
            mention=mention,
            entity_type=entity_type,
        )
        self.assertEqual(
            candidates.payload["resolution_status"],
            EntityResolutionStatus.UNIQUE.value,
        )
        self.assertEqual(
            candidates.completeness, StructureViewCompleteness.COMPLETE
        )
        return StructureEntityArgument.from_unique_candidate(candidates)

    def test_source_off_inventory_neighborhood_and_call_path(self) -> None:
        flow = self._argument("FlowService", EntityType.JAVA_TYPE)
        inventory = self.service.declared_method_inventory(java_type=flow)
        self.assertEqual(
            inventory.operation,
            StructureViewOperation.DECLARED_METHOD_INVENTORY,
        )
        self.assertEqual(inventory.payload["method_count"], 3)
        self.assertEqual(
            inventory.payload["relation_modality"],
            ObservationModality.JAVA_SOURCE_DECLARATION.value,
        )
        self.assertEqual(inventory.profile_refs, ("JAVA_STATIC_CALL_GRAPH@1",))

        start = self._argument(
            "com.acme.flow.FlowService#start(String)", EntityType.JAVA_METHOD
        )
        outgoing = self.service.direct_neighborhood(
            entity=start,
            direction=NeighborhoodDirection.OUTGOING,
            predicate=RelationPredicate.CALLS,
        )
        self.assertEqual(len(outgoing.payload["relations"]), 2)
        self.assertEqual(
            {item["observation_modality"] for item in outgoing.payload["relations"]},
            {ObservationModality.JAVA_SOURCE_STATIC_CALL.value},
        )
        with tempfile.TemporaryDirectory() as directory:
            writer = FileCitationObservationStoreWriter(
                Path(directory).resolve() / "java-citations"
            )
            materialization = CitationObservationBroker(
                self.fixture.repository,
                writer,
            ).materialize(outgoing)
            projection = CitationProjector(
                FileCitationObservationStoreReader(writer.root)
            ).project(materialization.seal)
        self.assertEqual(
            tuple(item.evidence_id for item in projection.citations),
            outgoing.evidence_allowlist,
        )
        self.assertTrue(
            any(
                ";kind=java-static-call-site" in item.locator
                and item.observation == "Audit.record(input)"
                for item in projection.citations
            )
        )

        finish = self._argument(
            "com.acme.flow.FlowService#finish(String)", EntityType.JAVA_METHOD
        )
        path = self.service.path_exists(
            source=start,
            target=finish,
            predicate=RelationPredicate.CALLS,
        )
        self.assertTrue(path.payload["exists"])
        self.assertEqual(len(path.payload["path"]["relation_root_ids"]), 2)
        self.assertEqual(path.completeness, StructureViewCompleteness.COMPLETE)
        self.assertNotIn("Audit.record(input)", repr(path.canonical_value()))

    def test_unqualified_candidate_query_uses_profile_coverage_not_global_enums(
        self,
    ) -> None:
        result = self.service.entity_candidates(
            snapshot_id=self.bundle.snapshot_id,
            mention="FlowService",
        )
        self.assertEqual(
            result.payload["resolution_status"],
            EntityResolutionStatus.UNIQUE.value,
        )
        self.assertEqual(result.completeness, StructureViewCompleteness.COMPLETE)

    def test_source_off_ordered_diff_uses_java_profile_members(self) -> None:
        result = self.ordered_service.ordered_snapshot_diff(
            base_snapshot_id=self.bundle.snapshot_id,
            target_snapshot_id=self.r2_bundle.snapshot_id,
        )

        self.assertEqual(result.operation, StructureViewOperation.ORDERED_SNAPSHOT_DIFF)
        self.assertEqual(result.payload["entities"]["counts"]["added"], 1)
        self.assertEqual(result.payload["relations"]["counts"]["added"], 3)
        self.assertEqual(result.payload["relations"]["counts"]["removed"], 1)
        self.assertEqual(result.profile_refs, ("JAVA_STATIC_CALL_GRAPH@1",))
