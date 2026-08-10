from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from software_world_model.application_services.citation_projection import (
    CitationObservationBroker,
    CitationProjector,
)
from software_world_model.application_services.knowledge_use import TaskBoundary
from software_world_model.application_services.structure_read_bundle import (
    StructureOrderedReadBundle,
    StructureBundleUpstreamEntityRecord,
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
    DomainError,
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
    CoverageRoot,
    EntityRecord,
    EntityRoot,
    EntityState,
    EntityType,
    ExactUpstreamEntity,
    ObservationModality,
    PublicationMode,
    RelationFactRecord,
    RelationFactRoot,
    RelationFactState,
    RelationPredicate,
)
from software_world_model.knowledge_engine.structure_publication import (
    StructureEvidenceMetadata,
)
from tests import test_structure_publication as _publication_tests


class StructureViewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = _publication_tests.StructurePublicationTests(methodName="runTest")
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.a = self._publish_graph("a", security=False, expected=None)
        self.b = self._publish_graph(
            "b", security=True, expected=self.a[0].snapshot_id
        )
        repository = SqliteStructureReadSessionRepository(self.fixture.database)
        sessions = StructureReadSessionService(
            repository,
            self.fixture.repository,
            self.fixture.scopes,
            clock=self.fixture.clock,
        )
        boundary = TaskBoundary.create(
            task_id=StableId("task_" + "7" * 32),
            task_revision=Revision(1),
            scope_id=self.fixture.scope.scope_id,
            purpose=StructureReadPurpose.SNAPSHOT_COMPARISON.value,
            classification="INTERNAL",
        )
        self.session = sessions.open_ordered(
            scope_id=self.fixture.scope.scope_id,
            scope_revision=self.fixture.scope.definition_revision,
            task_boundary=boundary,
            caller_ref="structure-view-test",
            snapshot_ids=(self.a[0].snapshot_id, self.b[0].snapshot_id),
            idempotency_key=IdempotencyKey("structure-view-a-b"),
        )
        self.a_file_digest = digest_of({"file": "a"})
        self.b_file_digest = digest_of({"file": "b"})
        self.envelope = StructureOrderedReadBundle.create(
            session=self.session,
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
                        self.session.snapshots,
                        (self.a[1], self.b[1]),
                        (self.a_file_digest, self.b_file_digest),
                    )
                )
            ),
        )
        self.service = StructureViewService(
            self.envelope,
            (
                (self.a[1], self.a_file_digest),
                (self.b[1], self.b_file_digest),
            ),
        )

    def test_entity_candidates_are_case_preserving_typed_and_never_guess(self) -> None:
        ambiguous = self.service.entity_candidates(
            snapshot_id=self.a[0].snapshot_id,
            mention=" common-lib ",
        )
        self.assertEqual(
            ambiguous.payload["resolution_status"],
            EntityResolutionStatus.AMBIGUOUS.value,
        )
        self.assertEqual(ambiguous.payload["candidate_count"], 2)
        self.assertEqual(ambiguous.limitations, ("ENTITY_RESOLUTION_AMBIGUOUS",))
        with self.assertRaises(DomainError):
            StructureEntityArgument.from_unique_candidate(ambiguous)

        unique = self.service.entity_candidates(
            snapshot_id=self.a[0].snapshot_id,
            mention="common-lib",
            canonical_ga="org.example.shared:common-lib",
        )
        self.assertEqual(
            unique.payload["resolution_status"], EntityResolutionStatus.UNIQUE.value
        )
        argument = StructureEntityArgument.from_unique_candidate(unique)
        neighborhood = self.service.direct_neighborhood(entity=argument)
        self.assertEqual(
            neighborhood.operation, StructureViewOperation.DIRECT_NEIGHBORHOOD
        )
        self.assertEqual(neighborhood.snapshot_ids, (self.a[0].snapshot_id,))

        case_mismatch = self.service.entity_candidates(
            snapshot_id=self.a[0].snapshot_id,
            mention="Common-Lib",
        )
        self.assertEqual(
            case_mismatch.payload["resolution_status"],
            EntityResolutionStatus.ZERO.value,
        )

        shared = next(
            item
            for item in self.a[1].entities
            if item.root.entity_type is EntityType.MAVEN_MODULE
            and item.state.state_payload_fields["module_path"]
            == "shared/common-lib"
        )
        for public_identity_or_display in (
            shared.root_id.value,
            "org.example.shared:common-lib",
            "org.example.shared:common-lib:1.0.0",
            "shared/common-lib",
        ):
            matched = self.service.entity_candidates(
                snapshot_id=self.a[0].snapshot_id,
                mention=public_identity_or_display,
                entity_type=EntityType.MAVEN_MODULE,
            )
            self.assertEqual(
                matched.payload["resolution_status"],
                EntityResolutionStatus.UNIQUE.value,
            )
            self.assertEqual(
                matched.payload["candidates"][0]["entity_root_id"],
                shared.root_id.value,
            )
        for exact_qualifier in (
            {"exact_root_id": shared.root_id},
            {"canonical_ga": "org.example.shared:common-lib"},
            {"canonical_gav": "org.example.shared:common-lib:1.0.0"},
        ):
            matched = self.service.entity_candidates(
                snapshot_id=self.a[0].snapshot_id,
                mention="common-lib",
                entity_type=EntityType.MAVEN_MODULE,
                **exact_qualifier,
            )
            self.assertEqual(
                matched.payload["resolution_status"],
                EntityResolutionStatus.UNIQUE.value,
            )
            self.assertEqual(
                matched.payload["candidates"][0]["entity_root_id"],
                shared.root_id.value,
            )

        system = next(
            item
            for item in self.a[1].entities
            if item.root.entity_type is EntityType.SOFTWARE_SYSTEM
        )
        forbidden_mentions = (
            (
                shared.state.state_payload_fields["source_revision"],
                EntityType.MAVEN_MODULE,
            ),
            (shared.root.owning_scope_id.value, EntityType.MAVEN_MODULE),
            (
                system.state.state_payload_fields["source_binding_id"],
                EntityType.SOFTWARE_SYSTEM,
            ),
        )
        for provenance, entity_type in forbidden_mentions:
            result = self.service.entity_candidates(
                snapshot_id=self.a[0].snapshot_id,
                mention=provenance,
                entity_type=entity_type,
            )
            self.assertEqual(
                result.payload["resolution_status"],
                EntityResolutionStatus.ZERO.value,
            )

    def test_candidate_proof_is_session_bound_and_rebuilt_before_use(self) -> None:
        unique = self.service.entity_candidates(
            snapshot_id=self.a[0].snapshot_id,
            mention="admin",
        )
        argument = StructureEntityArgument.from_unique_candidate(unique)
        tampered = replace(
            argument,
            candidate_result=replace(
                unique,
                digest=Digest("sha256:" + "f" * 64),
            ),
        )
        with self.assertRaises(DomainError) as raised:
            self.service.direct_neighborhood(entity=tampered)
        self.assertEqual(
            raised.exception.details["reason_code"],
            "VIEW_CANDIDATE_PROOF_MISMATCH",
        )
        other_session = replace(
            argument,
            session_id=StableId("structure_read_session_" + "9" * 32),
        )
        with self.assertRaises(DomainError) as raised:
            self.service.direct_neighborhood(entity=other_session)
        self.assertEqual(
            raised.exception.details["reason_code"],
            "VIEW_ENTITY_ARGUMENT_SESSION_MISMATCH",
        )

    def test_inventory_and_neighborhood_keep_typed_relation_modality(self) -> None:
        system = self._exact(self.a[1], "mall")
        inventory = self.service.child_module_inventory(system=system)
        self.assertEqual(inventory.payload["module_count"], 6)
        self.assertEqual(
            inventory.payload["relation_modality"],
            ObservationModality.RECURSIVE_REACTOR_MEMBERSHIP.value,
        )
        self.assertEqual(inventory.completeness, StructureViewCompleteness.COMPLETE)
        self.assertTrue(inventory.evidence_allowlist)

        admin = self._exact(self.a[1], "admin")
        outgoing = self.service.direct_neighborhood(
            entity=admin,
            direction=NeighborhoodDirection.OUTGOING,
            predicate=RelationPredicate.DEPENDS_ON,
        )
        self.assertEqual(len(outgoing.payload["relations"]), 1)
        relation = outgoing.payload["relations"][0]
        self.assertEqual(relation["predicate"], RelationPredicate.DEPENDS_ON.value)
        self.assertEqual(
            relation["observation_modality"],
            ObservationModality.POM_LOCAL_DECLARED_INTERNAL_DEPENDENCY.value,
        )

    def test_paths_distinguish_zero_multiple_and_truncated_results(self) -> None:
        a_admin = self._exact(self.a[1], "admin")
        a_common = self._exact(self.a[1], "common")
        a_search = self._exact(self.a[1], "search")
        a_paths = self.service.all_simple_paths(
            source=a_admin,
            target=a_common,
        )
        self.assertEqual(a_paths.payload["path_count"], 1)
        self.assertFalse(a_paths.truncated)

        exact_limit = self.service.all_simple_paths(
            source=a_admin,
            target=a_common,
            max_paths=1,
        )
        self.assertEqual(exact_limit.payload["path_count"], 1)
        self.assertFalse(exact_limit.truncated)

        b_admin = self._exact(self.b[1], "admin")
        b_common = self._exact(self.b[1], "common")
        b_paths = self.service.all_simple_paths(
            source=b_admin,
            target=b_common,
        )
        self.assertEqual(b_paths.payload["path_count"], 2)
        self.assertFalse(b_paths.truncated)

        over_limit = self.service.all_simple_paths(
            source=b_admin,
            target=b_common,
            max_paths=1,
        )
        self.assertEqual(over_limit.payload["path_count"], 1)
        self.assertTrue(over_limit.truncated)
        self.assertEqual(over_limit.completeness, StructureViewCompleteness.PARTIAL)

        expansion_limited = self.service.all_simple_paths(
            source=b_admin,
            target=b_common,
            max_expansions=1,
        )
        self.assertEqual(expansion_limited.payload["path_count"], 0)
        self.assertEqual(expansion_limited.payload["expansions"], 1)
        self.assertTrue(expansion_limited.truncated)
        self.assertFalse(
            expansion_limited.payload["negative_conclusion_supported"]
        )

        absent = self.service.path_exists(source=a_admin, target=a_search)
        self.assertFalse(absent.payload["exists"])
        self.assertTrue(absent.payload["negative_conclusion_supported"])
        self.assertEqual(absent.completeness, StructureViewCompleteness.COMPLETE)
        self.assertTrue(
            any(item.member_kind == "COVERAGE" for item in absent.support_map)
        )
        self.assertEqual(
            absent.coverage[0]["completeness"], "COMPLETE"
        )

        limited = self.service.path_exists(
            source=a_admin,
            target=a_common,
            max_depth=1,
        )
        self.assertFalse(limited.payload["exists"])
        self.assertTrue(limited.truncated)
        self.assertFalse(limited.payload["negative_conclusion_supported"])
        self.assertEqual(limited.completeness, StructureViewCompleteness.PARTIAL)

    def test_coverage_gaps_are_partial_and_cannot_support_negative_paths(self) -> None:
        fixture, service, bundle, system, module = self._generic_coverage_view(
            marker="c",
            covered_entity_types=tuple(EntityType),
            covered_relation_predicates=(RelationPredicate.CONTAINS_MODULE,),
            include_module=True,
        )
        try:
            source = StructureEntityArgument.caller_exact_ref(
                service=service,
                snapshot_id=bundle.snapshot_id,
                entity_root_id=system.root_id,
                entity_state_id=system.state_id,
            )
            target = StructureEntityArgument.caller_exact_ref(
                service=service,
                snapshot_id=bundle.snapshot_id,
                entity_root_id=module.root_id,
                entity_state_id=module.state_id,
            )
            results = (
                service.path_exists(source=source, target=target),
                service.all_simple_paths(source=source, target=target),
                service.direct_neighborhood(
                    entity=source,
                    predicate=RelationPredicate.DEPENDS_ON,
                ),
            )
            for result in results:
                self.assertEqual(
                    result.completeness, StructureViewCompleteness.PARTIAL
                )
                self.assertIn(
                    "VIEW_RELATION_PREDICATE_COVERAGE_INSUFFICIENT",
                    result.limitations,
                )
                self.assertEqual(
                    result.coverage[0]["covered_relation_predicates"],
                    (RelationPredicate.CONTAINS_MODULE.value,),
                )
            for result in results[:2]:
                self.assertFalse(result.payload["negative_conclusion_supported"])

            inventory = service.child_module_inventory(system=source)
            self.assertEqual(
                inventory.completeness, StructureViewCompleteness.COMPLETE
            )
            self.assertEqual(inventory.payload["module_count"], 1)
        finally:
            fixture.tearDown()

    def test_candidate_outside_entity_coverage_cannot_become_unique(self) -> None:
        fixture, service, bundle, _system, _module = self._generic_coverage_view(
            marker="d",
            covered_entity_types=(EntityType.SOFTWARE_SYSTEM,),
            covered_relation_predicates=(),
            include_module=False,
        )
        try:
            result = service.entity_candidates(
                snapshot_id=bundle.snapshot_id,
                mention="missing-module",
                entity_type=EntityType.MAVEN_MODULE,
            )
            self.assertEqual(
                result.payload["resolution_status"],
                EntityResolutionStatus.INCOMPLETE_COVERAGE.value,
            )
            self.assertEqual(result.completeness, StructureViewCompleteness.PARTIAL)
            self.assertIn(
                "VIEW_ENTITY_TYPE_COVERAGE_INSUFFICIENT",
                result.limitations,
            )
            self.assertEqual(
                result.coverage[0]["covered_entity_types"],
                (EntityType.SOFTWARE_SYSTEM.value,),
            )
            with self.assertRaises(DomainError):
                StructureEntityArgument.from_unique_candidate(result)
        finally:
            fixture.tearDown()

    def test_ordered_diff_separates_membership_from_state_change(self) -> None:
        result = self.service.ordered_snapshot_diff(
            base_snapshot_id=self.a[0].snapshot_id,
            target_snapshot_id=self.b[0].snapshot_id,
        )
        entities = result.payload["entities"]
        relations = result.payload["relations"]
        self.assertEqual(entities["counts"]["added"], 1)
        self.assertEqual(entities["counts"]["removed"], 0)
        self.assertEqual(entities["counts"]["state_changed"], 7)
        self.assertEqual(relations["counts"]["added"], 3)
        self.assertEqual(relations["counts"]["removed"], 0)
        self.assertEqual(relations["counts"]["state_changed"], 8)
        self.assertEqual(result.snapshot_ids, (self.a[0].snapshot_id, self.b[0].snapshot_id))
        result.require_valid()

        with self.assertRaises(DomainError) as raised:
            self.service.ordered_snapshot_diff(
                base_snapshot_id=self.b[0].snapshot_id,
                target_snapshot_id=self.a[0].snapshot_id,
            )
        self.assertEqual(raised.exception.details["reason_code"], "VIEW_DIFF_ORDER_INVALID")

    def test_view_has_no_repository_source_or_payload_port(self) -> None:
        self.assertFalse(hasattr(self.service, "repository"))
        self.assertFalse(hasattr(self.service, "source"))
        self.assertFalse(hasattr(self.service, "database"))
        result = self.service.entity_candidates(
            snapshot_id=self.a[0].snapshot_id,
            mention="admin",
        )
        encoded = repr(result.canonical_value())
        self.assertNotIn("pom-a", encoded)
        self.assertNotIn("pom-b", encoded)
        self.assertNotIn("excerpt", result.payload)

    def test_sealed_result_allows_one_way_citation_projection(self) -> None:
        result = self.service.child_module_inventory(
            system=self._exact(self.a[1], "mall")
        )
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory).resolve() / "citation-store"
            materialization = CitationObservationBroker(
                self.fixture.repository,
                FileCitationObservationStoreWriter(store),
            ).materialize(result)
            projection = CitationProjector(
                FileCitationObservationStoreReader(store)
            ).project(materialization.seal)
        self.assertEqual(projection.result_id, result.result_id)
        self.assertEqual(projection.store_id, materialization.receipt.store_id)
        self.assertEqual(
            tuple(item.evidence_id for item in projection.citations),
            result.evidence_allowlist,
        )

    def test_upstream_entity_is_candidate_path_endpoint_and_exact_support(self) -> None:
        service, bundle, local, upstream, relation = self._upstream_view()
        self.assertNotIn(upstream.root_id, {item.root_id for item in bundle.entities})
        self.assertEqual(
            tuple(item.entity.root_id for item in bundle.upstream_entity_records),
            (upstream.root_id,),
        )

        target_candidates = service.entity_candidates(
            snapshot_id=bundle.snapshot_id,
            mention="common",
            entity_type="MAVEN_MODULE",
        )
        self.assertEqual(
            target_candidates.payload["resolution_status"],
            EntityResolutionStatus.UNIQUE.value,
        )
        self.assertEqual(target_candidates.payload["candidate_count"], 1)
        candidate_support = tuple(
            item
            for item in target_candidates.support_map
            if item.member_kind == "ENTITY" and item.root_id == upstream.root_id
        )
        self.assertEqual(len(candidate_support), 1)
        self.assertEqual(
            candidate_support[0].snapshot_id,
            bundle.upstream_entity_records[0].snapshot_id,
        )
        for provenance in (
            local.state.state_payload_fields["source_revision"],
            upstream.state.state_payload_fields["source_revision"],
            upstream.root.owning_scope_id.value,
        ):
            provenance_result = service.entity_candidates(
                snapshot_id=bundle.snapshot_id,
                mention=provenance,
                entity_type=EntityType.MAVEN_MODULE,
            )
            self.assertEqual(
                provenance_result.payload["resolution_status"],
                EntityResolutionStatus.ZERO.value,
            )

        source_candidates = service.entity_candidates(
            snapshot_id=bundle.snapshot_id,
            mention="consumer",
            entity_type="MAVEN_MODULE",
        )
        path = service.all_simple_paths(
            source=StructureEntityArgument.from_unique_candidate(source_candidates),
            target=StructureEntityArgument.from_unique_candidate(target_candidates),
        )
        self.assertEqual(path.payload["path_count"], 1)
        self.assertEqual(
            path.payload["paths"][0]["entity_root_ids"],
            (local.root_id.value, upstream.root_id.value),
        )
        self.assertEqual(
            path.payload["paths"][0]["relation_root_ids"],
            (relation.root_id.value,),
        )
        entity_support = {
            item.root_id: item
            for item in path.support_map
            if item.member_kind == "ENTITY"
        }
        self.assertEqual(entity_support[local.root_id].snapshot_id, bundle.snapshot_id)
        self.assertEqual(
            entity_support[upstream.root_id].snapshot_id,
            bundle.upstream_entity_records[0].snapshot_id,
        )
        path.require_valid()

    def test_bundle_rejects_local_and_upstream_entity_root_overlap(self) -> None:
        _service, bundle, local, _upstream, _relation = self._upstream_view()
        overlapping = StructureBundleUpstreamEntityRecord(
            snapshot_id=bundle.upstream_entity_records[0].snapshot_id,
            entity=local,
        )

        with self.assertRaises(DomainError) as raised:
            StructureSnapshotReadBundle.create(
                snapshot=bundle.snapshot,
                coverages=bundle.coverages,
                entities=bundle.entities,
                relation_facts=bundle.relation_facts,
                literal_facts=bundle.literal_facts,
                upstream_entity_records=(
                    *bundle.upstream_entity_records,
                    overlapping,
                ),
                evidence_metadata=bundle.evidence_metadata,
            )

        self.assertEqual(
            raised.exception.details["reason_code"],
            "READ_BUNDLE_UPSTREAM_LOCAL_OVERLAP",
        )

    def _upstream_view(self):
        revision = "c" * 40
        evidence = self.fixture.evidence("c")
        local = self._module(
            evidence,
            revision,
            group_id="org.example.local",
            artifact_id="consumer",
            path="consumer",
        )
        upstream = next(
            item
            for item in self.b[1].entities
            if item.state.state_payload_fields["label"] == "common"
        )
        relation = self._dependency(evidence, revision, local, upstream)
        coverage = self.fixture.coverage(
            self.fixture.coverage_root("maven", maven=True),
            evidence,
            revision,
            (local, relation),
        )
        batch = self.fixture.batch(
            evidence=evidence,
            entities=(local,),
            relations=(relation,),
            coverage=coverage,
            mode=PublicationMode.REPLACE_COVERAGE,
            upstream=(
                ExactUpstreamEntity(
                    snapshot_id=self.b[0].snapshot_id,
                    entity=upstream,
                ),
            ),
        )
        receipt = self.fixture.publish(
            batch,
            key="view-upstream",
            expected=self.b[0].snapshot_id,
        )
        upstream_record = StructureBundleUpstreamEntityRecord(
            snapshot_id=self.b[0].snapshot_id,
            entity=upstream,
        )
        bundle = StructureSnapshotReadBundle.create(
            snapshot=receipt.snapshot,
            coverages=(coverage,),
            entities=(local,),
            relation_facts=(relation,),
            literal_facts=(),
            upstream_entity_records=(upstream_record,),
            evidence_metadata=(
                StructureEvidenceMetadata.from_evidence(evidence),
                *self.b[1].evidence_metadata,
            ),
        )

        sessions = StructureReadSessionService(
            SqliteStructureReadSessionRepository(self.fixture.database),
            self.fixture.repository,
            self.fixture.scopes,
            clock=self.fixture.clock,
        )
        session = sessions.open_ordered(
            scope_id=self.fixture.scope.scope_id,
            scope_revision=self.fixture.scope.definition_revision,
            task_boundary=TaskBoundary.create(
                task_id=StableId("task_" + "8" * 32),
                task_revision=Revision(1),
                scope_id=self.fixture.scope.scope_id,
                purpose=StructureReadPurpose.EXACT_SNAPSHOT.value,
                classification="INTERNAL",
            ),
            caller_ref="structure-view-upstream-test",
            snapshot_ids=(bundle.snapshot_id,),
            idempotency_key=IdempotencyKey("structure-view-upstream"),
        )
        file_digest = digest_of({"file": "upstream"})
        binding = session.snapshots[0]
        envelope = StructureOrderedReadBundle.create(
            session=session,
            snapshots=(
                StructureSnapshotBundleReference(
                    ordinal=0,
                    snapshot_id=bundle.snapshot_id,
                    snapshot_binding_digest=binding.digest,
                    snapshot_manifest_digest=binding.snapshot_manifest_digest,
                    bundle_digest=bundle.digest,
                    file_digest=file_digest,
                ),
            ),
        )
        service = StructureViewService(envelope, ((bundle, file_digest),))
        return service, bundle, local, upstream, relation

    def _generic_coverage_view(
        self,
        *,
        marker: str,
        covered_entity_types: tuple[EntityType, ...],
        covered_relation_predicates: tuple[RelationPredicate, ...],
        include_module: bool,
    ):
        fixture = _publication_tests.StructurePublicationTests(
            methodName="runTest"
        )
        fixture.setUp()
        try:
            revision = marker * 40
            evidence = fixture.evidence(marker)
            system = fixture.system(evidence, revision)
            module = (
                fixture.module(evidence, revision, "partial-module")
                if include_module
                else None
            )
            relations = (
                (
                    fixture.relation(
                        evidence,
                        revision,
                        system,
                        module,
                        schema_ref=fixture.generic_schema_ref,
                    ),
                )
                if module is not None
                else ()
            )
            entities = (system,) if module is None else (system, module)
            root = CoverageRoot.create(
                owning_scope_id=fixture.scope.scope_id,
                source_binding_id=fixture.binding,
                logical_reactor_root=f"{marker}/pom.xml",
                profile_ref="TEST_STRUCTURE@1",
                schema_ref=fixture.generic_schema_ref,
                schema_digest=fixture.generic_schema_digest,
                maven_evaluation_context_ref="TEST-EVALUATION@1",
                maven_evaluation_context_digest=digest_of({"evaluation": 1}),
                covered_entity_types=covered_entity_types,
                covered_relation_predicates=covered_relation_predicates,
                canonicalization_ref="TEST-CANONICALIZATION@1",
                canonicalization_digest=digest_of({"canonicalization": 1}),
                coverage_root_ref=f"TEST_PARTIAL_COVERAGE@{marker}",
            )
            coverage = fixture.coverage(
                root,
                evidence,
                revision,
                (*entities, *relations),
            )
            batch = fixture.batch(
                evidence=evidence,
                entities=entities,
                relations=relations,
                coverage=coverage,
                mode=PublicationMode.REPLACE_COVERAGE,
            )
            receipt = fixture.publish(
                batch,
                key=f"partial-view-{marker}",
                expected=None,
            )
            bundle = StructureSnapshotReadBundle.create(
                snapshot=receipt.snapshot,
                coverages=(coverage,),
                entities=entities,
                relation_facts=relations,
                literal_facts=(),
                upstream_entity_records=(),
                evidence_metadata=(
                    StructureEvidenceMetadata.from_evidence(evidence),
                ),
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
                    task_id=StableId("task_" + marker * 32),
                    task_revision=Revision(1),
                    scope_id=fixture.scope.scope_id,
                    purpose=StructureReadPurpose.EXACT_SNAPSHOT.value,
                    classification="INTERNAL",
                ),
                caller_ref=f"coverage-view-{marker}",
                snapshot_ids=(bundle.snapshot_id,),
                idempotency_key=IdempotencyKey(f"coverage-view-{marker}"),
            )
            file_digest = digest_of({"file": f"coverage-{marker}"})
            envelope = StructureOrderedReadBundle.create(
                session=session,
                snapshots=(
                    StructureSnapshotBundleReference(
                        ordinal=0,
                        snapshot_id=bundle.snapshot_id,
                        snapshot_binding_digest=session.snapshots[0].digest,
                        snapshot_manifest_digest=(
                            session.snapshots[0].snapshot_manifest_digest
                        ),
                        bundle_digest=bundle.digest,
                        file_digest=file_digest,
                    ),
                ),
            )
            service = StructureViewService(envelope, ((bundle, file_digest),))
            return fixture, service, bundle, system, module
        except Exception:
            fixture.tearDown()
            raise

    def _publish_graph(
        self,
        marker: str,
        *,
        security: bool,
        expected: StableId | None,
    ):
        revision = marker * 40
        evidence = self.fixture.evidence(marker)
        system = self.fixture.system(evidence, revision)
        modules = {
            name: self.fixture.module(evidence, revision, name)
            for name in ("admin", "common", "mbg", "search")
        }
        modules["shared"] = self._module(
            evidence,
            revision,
            group_id="org.example.shared",
            artifact_id="common-lib",
            path="shared/common-lib",
        )
        modules["legacy"] = self._module(
            evidence,
            revision,
            group_id="org.example.legacy",
            artifact_id="common-lib",
            path="legacy/common-lib",
        )
        if security:
            modules["security"] = self.fixture.module(evidence, revision, "security")
        contains = tuple(
            self.fixture.relation(evidence, revision, system, module)
            for module in modules.values()
        )
        dependencies = [
            self._dependency(evidence, revision, modules["admin"], modules["mbg"]),
            self._dependency(evidence, revision, modules["mbg"], modules["common"]),
        ]
        if security:
            dependencies.extend(
                (
                    self._dependency(
                        evidence,
                        revision,
                        modules["admin"],
                        modules["security"],
                    ),
                    self._dependency(
                        evidence,
                        revision,
                        modules["security"],
                        modules["common"],
                    ),
                )
            )
        relations = (*contains, *dependencies)
        entities = (system, *modules.values())
        coverage = self.fixture.coverage(
            self.fixture.coverage_root("maven", maven=True),
            evidence,
            revision,
            (*entities, *relations),
        )
        batch = self.fixture.batch(
            evidence=evidence,
            entities=entities,
            relations=relations,
            coverage=coverage,
            mode=PublicationMode.REPLACE_COVERAGE,
        )
        receipt = self.fixture.publish(
            batch,
            key=f"view-{marker}",
            expected=expected,
        )
        bundle = StructureSnapshotReadBundle.create(
            snapshot=receipt.snapshot,
            coverages=(coverage,),
            entities=entities,
            relation_facts=relations,
            literal_facts=(),
            upstream_entity_records=(),
            evidence_metadata=(StructureEvidenceMetadata.from_evidence(evidence),),
        )
        return receipt.snapshot, bundle

    def _module(
        self,
        evidence,
        revision: str,
        *,
        group_id: str,
        artifact_id: str,
        path: str,
    ) -> EntityRecord:
        root = EntityRoot.maven_module(
            owning_scope_id=self.fixture.scope.scope_id,
            effective_group_id=group_id,
            artifact_id=artifact_id,
        )
        return EntityRecord(
            root,
            EntityState.create(
                root=root,
                state_payload_fields={
                    "effective_version": "1.0.0",
                    "packaging": "jar",
                    "module_path": path,
                    "label": artifact_id,
                    "source_revision": revision,
                    "evidence_references": (evidence.evidence_id,),
                },
            ),
        )

    def _dependency(
        self,
        evidence,
        revision: str,
        subject: EntityRecord,
        target: EntityRecord,
    ) -> RelationFactRecord:
        root = RelationFactRoot.create(
            owning_scope_id=self.fixture.scope.scope_id,
            subject=subject.root.ref,
            predicate=RelationPredicate.DEPENDS_ON,
            object=target.root.ref,
            observation_modality=ObservationModality.POM_LOCAL_DECLARED_INTERNAL_DEPENDENCY,
        )
        group_id = target.root.root_fields["effective_group_id"]
        artifact_id = target.root.root_fields["artifact_id"]
        version = target.state.state_payload_fields["effective_version"]
        return RelationFactRecord(
            root,
            RelationFactState.create(
                root=root,
                subject_state=subject.state,
                object_state=target.state,
                source_revision=revision,
                knowledge_context_digest=digest_of({"revision": revision}),
                evidence_references=(evidence.evidence_id,),
                predicate_state_payload_fields={
                    "declared_dependency_gav_expression": f"{group_id}:{artifact_id}:{version}",
                    "resolved_dependency_gav": f"{group_id}:{artifact_id}:{version}",
                    "scope": "compile",
                    "type": "jar",
                    "classifier": None,
                    "optional": False,
                },
            ),
        )

    def _exact(
        self, bundle: StructureSnapshotReadBundle, label: str
    ) -> StructureEntityArgument:
        matches = tuple(
            item
            for item in bundle.entities
            if item.state.state_payload_fields["label"] == label
        )
        self.assertEqual(len(matches), 1)
        return StructureEntityArgument.caller_exact_ref(
            service=self.service,
            snapshot_id=bundle.snapshot_id,
            entity_root_id=matches[0].root_id,
            entity_state_id=matches[0].state_id,
        )


if __name__ == "__main__":
    unittest.main()
