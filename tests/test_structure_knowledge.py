from __future__ import annotations

from dataclasses import replace
import unittest

from software_world_model.cross_cutting import (
    CanonicalizationError,
    Digest,
    DomainError,
    StableId,
    canonical_json_bytes,
    digest_of,
)
from software_world_model.knowledge_engine.structure import (
    CanonicalFields,
    CompleteMemberManifest,
    CoverageRecord,
    CoverageRoot,
    CoverageState,
    EntityRecord,
    EntityRef,
    EntityRoot,
    EntityState,
    EntityType,
    ExactUpstreamEntity,
    FactKind,
    LiteralFactRecord,
    LiteralFactRoot,
    LiteralFactState,
    LiteralObject,
    LiteralType,
    ObservationModality,
    PublicationMode,
    RelationFactRecord,
    RelationFactRoot,
    RelationFactState,
    RelationPredicate,
    RootStateIdentity,
    StructureEvidence,
    StructureKnowledgeBatch,
    compare_root_state,
)


class StructureKnowledgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scope = StableId("scope_" + "1" * 32)
        self.binding = StableId("binding_" + "2" * 32)
        self.artifact = StableId("source_artifact_" + "3" * 32)
        self.source_context = StableId("source_context_" + "4" * 32)
        self.context_a = digest_of({"revision": "a" * 40})
        self.context_b = digest_of({"revision": "b" * 40})
        self.artifact_digest = digest_of({"pom": "root"})
        self.evidence = StructureEvidence.create(
            artifact_id=self.artifact,
            source_context_id=self.source_context,
            byte_start=0,
            byte_end=3,
            locator="pom.xml:1",
            excerpt="pom",
            artifact_content_digest=self.artifact_digest,
        )

    def system_record(self, revision: str = "a" * 40) -> EntityRecord:
        root = EntityRoot.software_system(
            owning_scope_id=self.scope,
            canonical_system_key="https://example.invalid/mall.git",
        )
        state = EntityState.create(
            root=root,
            state_payload_fields={
                "label": "mall" if revision.startswith("a") else "mall renamed",
                "effective_group_id": "com.example",
                "artifact_id": "mall",
                "effective_version": "1.0.0" if revision.startswith("a") else "2.0.0",
                "packaging": "pom",
                "source_binding_id": self.binding,
                "source_revision": revision,
                "root_pom_locator": "pom.xml" if revision.startswith("a") else "root/pom.xml",
                "evidence_references": (self.evidence.evidence_id,),
            },
        )
        return EntityRecord(root, state)

    def module_record(
        self,
        artifact_id: str = "mall-common",
        revision: str = "a" * 40,
        *,
        evidence_id: StableId | None = None,
    ) -> EntityRecord:
        root = EntityRoot.maven_module(
            owning_scope_id=self.scope,
            effective_group_id="com.example",
            artifact_id=artifact_id,
        )
        state = EntityState.create(
            root=root,
            state_payload_fields={
                "effective_version": "1.0.0" if revision.startswith("a") else "2.0.0",
                "packaging": "jar",
                "module_path": artifact_id if revision.startswith("a") else f"moved/{artifact_id}",
                "label": artifact_id if revision.startswith("a") else f"{artifact_id} renamed",
                "source_revision": revision,
                "evidence_references": (evidence_id or self.evidence.evidence_id,),
            },
        )
        return EntityRecord(root, state)

    def contains_record(
        self,
        system: EntityRecord,
        module: EntityRecord,
        revision: str = "a" * 40,
    ) -> RelationFactRecord:
        root = RelationFactRoot.create(
            owning_scope_id=self.scope,
            subject=system.root.ref,
            predicate=RelationPredicate.CONTAINS_MODULE,
            object=module.root.ref,
            observation_modality=ObservationModality.RECURSIVE_REACTOR_MEMBERSHIP,
        )
        state = RelationFactState.create(
            root=root,
            subject_state=system.state,
            object_state=module.state,
            source_revision=revision,
            knowledge_context_digest=(
                self.context_a if revision.startswith("a") else self.context_b
            ),
            evidence_references=(self.evidence.evidence_id,),
            predicate_state_payload_fields={
                "module_declaration_path": "pom.xml#/project/modules/module[1]"
            },
        )
        return RelationFactRecord(root, state)

    def coverage_record(
        self,
        records: tuple[EntityRecord | RelationFactRecord | LiteralFactRecord, ...],
        revision: str = "a" * 40,
    ) -> CoverageRecord:
        root = CoverageRoot.create(
            owning_scope_id=self.scope,
            source_binding_id=self.binding,
            logical_reactor_root="pom.xml",
        )
        manifest = CompleteMemberManifest.create(
            tuple(record.coverage_member for record in records)
        )
        state = CoverageState.create(
            root=root,
            source_revision=revision,
            knowledge_context_digest=(
                self.context_a if revision.startswith("a") else self.context_b
            ),
            complete_member_manifest=manifest,
            evidence_references=(self.evidence.evidence_id,),
        )
        return CoverageRecord(root, state)

    @staticmethod
    def reason(error: DomainError) -> str:
        return str(error.details["reason_code"])

    def test_frozen_codec_vector_and_entity_root_identity_formula(self) -> None:
        vector = {"b": "x", "a": [None, True, 1, "é"]}
        self.assertEqual(
            canonical_json_bytes(vector).hex(),
            "7b2261223a5b6e756c6c2c747275652c312c22c3a9225d2c2262223a2278227d",
        )
        self.assertEqual(
            digest_of(vector).value,
            "sha256:899ea295a979d29180c4f75f77f2bd3167292651574ac6b7106a78f9fa1c9f58",
        )
        root = EntityRoot.maven_module(
            owning_scope_id=self.scope,
            effective_group_id="com.example",
            artifact_id="mall-common",
        )
        expected = digest_of(
            [
                "ENTITY_ROOT",
                "MAVEN_MODULE",
                "MAVEN_MODULE@1",
                CanonicalFields(
                    {
                        "owning_scope_id": self.scope.value,
                        "effective_group_id": "com.example",
                        "artifact_id": "mall-common",
                    }
                ),
            ]
        )
        self.assertEqual(root.allocation_key_digest, expected)
        self.assertEqual(root.entity_root_id.value, f"entity_root_{expected.value[-32:]}")
        with self.assertRaises(CanonicalizationError):
            CanonicalFields({"not_allowed": 1.5})

    def test_domain_nfc_normalization_precedes_identity_codec(self) -> None:
        decomposed = EntityRoot.maven_module(
            owning_scope_id=self.scope,
            effective_group_id="org.example",
            artifact_id="cafe\u0301",
        )
        composed = EntityRoot.maven_module(
            owning_scope_id=self.scope,
            effective_group_id="org.example",
            artifact_id="caf\u00e9",
        )
        self.assertEqual(decomposed, composed)

    def test_entity_root_is_stable_while_revision_bound_state_changes(self) -> None:
        state_a = self.module_record(revision="a" * 40)
        state_b = self.module_record(revision="b" * 40)
        self.assertEqual(state_a.root_id, state_b.root_id)
        self.assertNotEqual(state_a.state_id, state_b.state_id)
        self.assertEqual(
            compare_root_state(state_a, state_b),
            RootStateIdentity.SAME_ROOT_DIFFERENT_STATE,
        )
        replay = self.module_record(revision="a" * 40)
        self.assertEqual(
            compare_root_state(state_a, replay), RootStateIdentity.SAME_ROOT_SAME_STATE
        )

    def test_relation_root_is_stable_while_endpoint_states_and_context_change(self) -> None:
        system_a = self.system_record("a" * 40)
        module_a = self.module_record(revision="a" * 40)
        relation_a = self.contains_record(system_a, module_a, "a" * 40)
        system_b = self.system_record("b" * 40)
        module_b = self.module_record(revision="b" * 40)
        relation_b = self.contains_record(system_b, module_b, "b" * 40)
        self.assertEqual(relation_a.root_id, relation_b.root_id)
        self.assertNotEqual(relation_a.state_id, relation_b.state_id)
        self.assertEqual(
            compare_root_state(relation_a, relation_b),
            RootStateIdentity.SAME_ROOT_DIFFERENT_STATE,
        )
        self.assertIs(relation_a.root.fact_kind, FactKind.RELATION)
        self.assertEqual(relation_a.root.subject, system_a.root.ref)
        self.assertEqual(relation_a.root.object, module_a.root.ref)

    def test_relation_and_literal_shapes_cannot_be_mixed(self) -> None:
        system = self.system_record()
        module = self.module_record()
        literal = LiteralObject(LiteralType.STRING, "mall")
        with self.assertRaises(DomainError) as relation_error:
            RelationFactRoot.create(
                owning_scope_id=self.scope,
                subject=system.root.ref,
                predicate=RelationPredicate.CONTAINS_MODULE,
                object=literal,  # type: ignore[arg-type]
                observation_modality=ObservationModality.RECURSIVE_REACTOR_MEMBERSHIP,
            )
        self.assertEqual(
            self.reason(relation_error.exception), "RELATION_ENDPOINT_NOT_ENTITY_REF"
        )
        with self.assertRaises(DomainError) as literal_error:
            LiteralFactRoot.create(
                owning_scope_id=self.scope,
                schema_ref="LITERAL-SCHEMA@1",
                subject=system.root.ref,
                predicate="HAS_NAME",
                object=module.root.ref,  # type: ignore[arg-type]
                observation_modality="POM_TEXT@1",
            )
        self.assertEqual(self.reason(literal_error.exception), "LITERAL_FACT_SHAPE_INVALID")
        with self.assertRaises(DomainError):
            LiteralObject(LiteralType.INTEGER, True)

    def test_literal_fact_schema_must_match_coverage_schema(self) -> None:
        system = self.system_record()
        literal_root = LiteralFactRoot.create(
            owning_scope_id=self.scope,
            schema_ref="OTHER-LITERAL-SCHEMA@1",
            subject=system.root.ref,
            predicate="HAS_FLAG",
            object=LiteralObject(LiteralType.BOOLEAN, True),
            observation_modality="DECLARED@1",
        )
        literal = LiteralFactRecord(
            literal_root,
            LiteralFactState.create(
                root=literal_root,
                subject_state=system.state,
                source_revision="a" * 40,
                knowledge_context_digest=self.context_a,
                evidence_references=(self.evidence.evidence_id,),
            ),
        )
        coverage_root = CoverageRoot.create(
            owning_scope_id=self.scope,
            source_binding_id=self.binding,
            logical_reactor_root="pom.xml",
            profile_ref="LITERAL-PROFILE@1",
            schema_ref="LITERAL-SCHEMA@1",
            schema_digest=digest_of({"schema": "LITERAL-SCHEMA@1"}),
            maven_evaluation_context_ref="LITERAL-EVALUATION@1",
            maven_evaluation_context_digest=digest_of({"evaluation": 1}),
            covered_entity_types=(EntityType.SOFTWARE_SYSTEM,),
            covered_relation_predicates=(),
            canonicalization_ref="LITERAL-CANONICALIZATION@1",
            canonicalization_digest=digest_of({"canonicalization": 1}),
            coverage_root_ref="LITERAL-COVERAGE@1",
        )
        coverage = CoverageRecord(
            coverage_root,
            CoverageState.create(
                root=coverage_root,
                source_revision="a" * 40,
                knowledge_context_digest=self.context_a,
                complete_member_manifest=CompleteMemberManifest.create(
                    (system.coverage_member, literal.coverage_member)
                ),
                evidence_references=(self.evidence.evidence_id,),
            ),
        )

        with self.assertRaises(DomainError) as error:
            StructureKnowledgeBatch.admit(
                evidence=(self.evidence,),
                entities=(system,),
                relation_facts=(),
                literal_facts=(literal,),
                coverage=coverage,
                publication_mode=PublicationMode.REPLACE_COVERAGE,
            )

        self.assertEqual(self.reason(error.exception), "FACT_SCHEMA_MISMATCH")

    def test_predicate_endpoint_types_and_modality_are_schema_checked(self) -> None:
        system = self.system_record()
        module = self.module_record()
        with self.assertRaises(DomainError) as error:
            RelationFactRoot.create(
                owning_scope_id=self.scope,
                subject=module.root.ref,
                predicate=RelationPredicate.CONTAINS_MODULE,
                object=module.root.ref,
                observation_modality=ObservationModality.RECURSIVE_REACTOR_MEMBERSHIP,
            )
        self.assertEqual(self.reason(error.exception), "RELATION_SCHEMA_MISMATCH")
        with self.assertRaises(DomainError) as wrong_modality:
            RelationFactRoot.create(
                owning_scope_id=self.scope,
                subject=system.root.ref,
                predicate=RelationPredicate.DEPENDS_ON,
                object=module.root.ref,
                observation_modality=ObservationModality.RECURSIVE_REACTOR_MEMBERSHIP,
            )
        self.assertEqual(self.reason(wrong_modality.exception), "RELATION_SCHEMA_MISMATCH")

    def test_admission_accepts_exact_typed_endpoint_and_evidence_closure(self) -> None:
        system = self.system_record()
        module = self.module_record()
        relation = self.contains_record(system, module)
        coverage = self.coverage_record((system, module, relation))
        batch = StructureKnowledgeBatch.admit(
            evidence=(self.evidence,),
            entities=(system, module),
            relation_facts=(relation,),
            coverage=coverage,
            publication_mode=PublicationMode.REPLACE_COVERAGE,
        )
        self.assertEqual(batch.entities, (system, module))
        self.assertEqual(batch.evidence, (self.evidence,))
        self.assertEqual(
            coverage.state.complete_member_manifest.members,
            tuple(sorted(
                (system.coverage_member, module.coverage_member, relation.coverage_member),
                key=lambda item: (item.kind.value, item.root_id.value, item.state_id.value),
            )),
        )

    def test_admission_rejects_dangling_and_ambiguous_endpoints(self) -> None:
        system = self.system_record()
        module = self.module_record()
        relation = self.contains_record(system, module)
        dangling_coverage = self.coverage_record((system, relation))
        with self.assertRaises(DomainError) as dangling:
            StructureKnowledgeBatch.admit(
                evidence=(self.evidence,),
                entities=(system,),
                relation_facts=(relation,),
                coverage=dangling_coverage,
                publication_mode=PublicationMode.REPLACE_COVERAGE,
            )
        self.assertEqual(self.reason(dangling.exception), "DANGLING_RELATION_ENDPOINT")

        coverage = self.coverage_record((system, module, relation))
        with self.assertRaises(DomainError) as ambiguous:
            StructureKnowledgeBatch.admit(
                evidence=(self.evidence,),
                entities=(system, module),
                relation_facts=(relation,),
                coverage=coverage,
                publication_mode=PublicationMode.REPLACE_COVERAGE,
                exact_upstream_entities=(
                    ExactUpstreamEntity(
                        StableId("knowledge_snapshot_" + "5" * 32), module
                    ),
                ),
            )
        self.assertEqual(self.reason(ambiguous.exception), "AMBIGUOUS_RELATION_ENDPOINT")

    def test_admission_rejects_multiple_states_for_same_root(self) -> None:
        system = self.system_record()
        module_a = self.module_record(revision="a" * 40)
        module_b = self.module_record(revision="b" * 40)
        coverage = self.coverage_record((system, module_a))
        with self.assertRaises(DomainError) as error:
            StructureKnowledgeBatch.admit(
                evidence=(self.evidence,),
                entities=(system, module_a, module_b),
                relation_facts=(),
                coverage=coverage,
                publication_mode=PublicationMode.REPLACE_COVERAGE,
            )
        self.assertEqual(self.reason(error.exception), "MULTIPLE_STATES_FOR_ROOT")

    def test_maven_schema_rejects_literal_fact_and_enrich_mode(self) -> None:
        system = self.system_record()
        literal_root = LiteralFactRoot.create(
            owning_scope_id=self.scope,
            schema_ref="MAVEN-REACTOR-STRUCTURE@1.0.0",
            subject=system.root.ref,
            predicate="HAS_LABEL",
            object=LiteralObject(LiteralType.STRING, "mall"),
            observation_modality="POM_TEXT@1",
        )
        literal_state = LiteralFactState.create(
            root=literal_root,
            subject_state=system.state,
            source_revision="a" * 40,
            knowledge_context_digest=self.context_a,
            evidence_references=(self.evidence.evidence_id,),
        )
        literal = LiteralFactRecord(literal_root, literal_state)
        coverage = self.coverage_record((system, literal))
        with self.assertRaises(DomainError) as literal_error:
            StructureKnowledgeBatch.admit(
                evidence=(self.evidence,),
                entities=(system,),
                relation_facts=(),
                literal_facts=(literal,),
                coverage=coverage,
                publication_mode=PublicationMode.REPLACE_COVERAGE,
            )
        self.assertEqual(self.reason(literal_error.exception), "LITERAL_FACT_NOT_ALLOWED")
        no_literal_coverage = self.coverage_record((system,))
        with self.assertRaises(DomainError) as mode_error:
            StructureKnowledgeBatch.admit(
                evidence=(self.evidence,),
                entities=(system,),
                relation_facts=(),
                coverage=no_literal_coverage,
                publication_mode=PublicationMode.ENRICH,
            )
        self.assertEqual(self.reason(mode_error.exception), "PUBLICATION_MODE_MISMATCH")

    def test_coverage_root_is_stable_and_state_binds_revision_and_manifest(self) -> None:
        system_a = self.system_record("a" * 40)
        module_a = self.module_record(revision="a" * 40)
        coverage_a = self.coverage_record((system_a, module_a), "a" * 40)
        system_b = self.system_record("b" * 40)
        module_b = self.module_record(revision="b" * 40)
        coverage_b = self.coverage_record((system_b, module_b), "b" * 40)
        self.assertEqual(coverage_a.root_id, coverage_b.root_id)
        self.assertNotEqual(coverage_a.state_id, coverage_b.state_id)
        self.assertEqual(
            compare_root_state(coverage_a, coverage_b),
            RootStateIdentity.SAME_ROOT_DIFFERENT_STATE,
        )
        self.assertEqual(
            set(coverage_a.root.root_fields),
            {
                "owning_scope_id",
                "profile_ref",
                "schema_ref",
                "schema_digest",
                "source_binding_id",
                "logical_reactor_root",
                "maven_evaluation_context_ref",
                "maven_evaluation_context_digest",
                "covered_entity_types",
                "covered_relation_predicates",
                "canonicalization_ref",
                "canonicalization_digest",
            },
        )
        self.assertNotIn("source_revision", coverage_a.root.root_fields)
        self.assertNotIn("evidence_references", coverage_a.root.root_fields)

    def test_default_maven_coverage_is_not_derived_from_generic_enum_members(self) -> None:
        root = CoverageRoot.create(
            owning_scope_id=self.scope,
            source_binding_id=self.binding,
            logical_reactor_root="pom.xml",
        )

        self.assertEqual(
            root.covered_entity_types,
            (EntityType.MAVEN_MODULE, EntityType.SOFTWARE_SYSTEM),
        )
        self.assertEqual(
            root.covered_relation_predicates,
            (RelationPredicate.CONTAINS_MODULE, RelationPredicate.DEPENDS_ON),
        )
        self.assertNotIn(EntityType.JAVA_TYPE, root.covered_entity_types)
        self.assertNotIn(RelationPredicate.CALLS, root.covered_relation_predicates)

    def test_evidence_is_canonical_and_all_state_refs_must_resolve(self) -> None:
        replay = StructureEvidence.create(
            artifact_id=self.artifact,
            source_context_id=self.source_context,
            byte_start=0,
            byte_end=3,
            locator="pom.xml:1",
            excerpt="pom",
            artifact_content_digest=self.artifact_digest,
        )
        self.assertEqual(replay, self.evidence)
        self.assertEqual(replay.observation, "pom")
        with self.assertRaises(DomainError) as invalid_range:
            StructureEvidence.create(
                artifact_id=self.artifact,
                source_context_id=self.source_context,
                byte_start=0,
                byte_end=2,
                locator="pom.xml:1",
                excerpt="pom",
                artifact_content_digest=self.artifact_digest,
            )
        self.assertEqual(self.reason(invalid_range.exception), "EVIDENCE_RANGE_INVALID")

        missing = StableId("evidence_" + "9" * 32)
        system = self.system_record()
        module = self.module_record(evidence_id=missing)
        coverage = self.coverage_record((system, module))
        with self.assertRaises(DomainError) as dangling:
            StructureKnowledgeBatch.admit(
                evidence=(self.evidence,),
                entities=(system, module),
                relation_facts=(),
                coverage=coverage,
                publication_mode=PublicationMode.REPLACE_COVERAGE,
            )
        self.assertEqual(self.reason(dangling.exception), "EVIDENCE_REFERENCE_DANGLING")

    def test_tampered_identity_is_rejected(self) -> None:
        record = self.module_record()
        with self.assertRaises(DomainError) as error:
            replace(
                record.root,
                allocation_key_digest=Digest("sha256:" + "0" * 64),
            )
        self.assertEqual(self.reason(error.exception), "ENTITY_ROOT_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
