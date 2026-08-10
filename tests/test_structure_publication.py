from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from software_world_model.cross_cutting import (
    CorrelationRef,
    Digest,
    DomainError,
    ErrorCode,
    IdempotencyKey,
    Revision,
    StableId,
    digest_of,
)
from software_world_model.infrastructure.sqlite_database import SqliteDatabase
from software_world_model.infrastructure.sqlite_scope_repository import (
    SqliteKnowledgeScopeRepository,
)
from software_world_model.infrastructure.sqlite_structure_knowledge_repository import (
    SqliteStructureKnowledgeRepository,
)
from software_world_model.knowledge_engine.scope import (
    KnowledgeScopeService,
    ScopeType,
)
from software_world_model.knowledge_engine.structure import (
    CompleteMemberManifest,
    CoverageRecord,
    CoverageRoot,
    CoverageState,
    EntityRecord,
    EntityRoot,
    EntityState,
    ExactUpstreamEntity,
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
    StructureEvidence,
    StructureKnowledgeBatch,
)
from software_world_model.knowledge_engine.structure_publication import (
    ApplicationAcceptanceDecision,
    StructureApplicationAcceptance,
    StructurePublicationService,
    structure_batch_digest,
)
from software_world_model.knowledge_engine.structure_authority import (
    StructureAdmissionFinding,
    StructureAdmissionService,
    StructureSchemaAdoptionMode,
    StructureSchemaAvailabilityStatus,
    StructureSchemaDefinition,
    StructureSchemaDependency,
    StructureSchemaRegistryService,
    StructureVerificationCandidate,
    StructureVerificationResult,
    StructureVerifierAssessmentOutcome,
    StructureVerifierAssessmentService,
    structure_admission_decision_digest,
)


class StepClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 8, 10, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(microseconds=1)
        return current


class FixedTestStructureVerifier:
    """Test composition-root verifier; only this port owns verified material."""

    def __init__(self) -> None:
        self._results: dict[str, StructureVerificationResult] = {}

    def expect(
        self, candidate_ref: str, result: StructureVerificationResult
    ) -> None:
        self._results[candidate_ref] = result

    def verify(
        self, candidate: StructureVerificationCandidate
    ) -> StructureVerificationResult:
        try:
            return self._results[candidate.candidate_ref]
        except KeyError as error:
            raise AssertionError(
                f"no independent verifier result for {candidate.candidate_ref}"
            ) from error


class FixedStructureArtifactUseProofVerifier:
    """Payload-free test double for the Knowledge-side Source proof port."""

    def __init__(self) -> None:
        self._proofs: dict[StableId, tuple[Digest, str, Digest]] = {}

    def issue(self, candidate_ref: str, candidate_digest: Digest):
        proof_digest = digest_of(
            ["TEST_ARTIFACT_USE_CONFIRMATION@1", candidate_ref, candidate_digest]
        )
        proof_id = StableId(
            "artifact_use_" + proof_digest.value.removeprefix("sha256:")[-32:]
        )
        self._proofs[proof_id] = (proof_digest, candidate_ref, candidate_digest)
        return proof_id, proof_digest

    def forget(self, confirmation_id: StableId) -> None:
        self._proofs.pop(confirmation_id, None)

    def verify_structure_candidate_use(
        self,
        *,
        confirmation_id: StableId,
        expected_confirmation_digest: Digest,
        candidate_ref: str,
        candidate_digest: Digest,
    ) -> None:
        if self._proofs.get(confirmation_id) != (
            expected_confirmation_digest,
            candidate_ref,
            candidate_digest,
        ):
            raise DomainError(
                ErrorCode.AUTHORITY_RECORD_INCONSISTENT,
                "Artifact use proof does not authorize this Structure candidate",
                {"reason_code": "TEST_ARTIFACT_USE_PROOF_MISMATCH"},
            )


class StructurePublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.database = SqliteDatabase()
        self.clock = StepClock()
        self.scopes = KnowledgeScopeService(
            SqliteKnowledgeScopeRepository(self.database), clock=self.clock
        )
        self.scope = self.scopes.create_scope(
            scope_type=ScopeType.SYSTEM,
            metadata={"display_name": "Structure test"},
            idempotency_key=IdempotencyKey("structure-test-scope"),
            actor="test",
            reason="Structure publication",
            correlation_ref=CorrelationRef("structure-publication"),
        )
        self.binding = StableId("binding_" + "2" * 32)
        self.repository = SqliteStructureKnowledgeRepository(self.database)
        self.generic_schema_ref = "TEST-STRUCTURE@1"
        self.generic_schema_digest = digest_of({"schema": self.generic_schema_ref})
        self.registry = StructureSchemaRegistryService(
            self.repository, clock=self.clock
        )
        self.registry.register(
            definition=StructureSchemaDefinition.create(
                schema_ref=self.generic_schema_ref,
                schema_digest=self.generic_schema_digest,
            ),
            idempotency_key=IdempotencyKey("register-generic-structure-schema"),
            proposal_ref="proposal:test-generic-structure@1",
            review_ref="review:test-generic-structure@1",
            registered_by="test",
            reason="publication fixtures",
        )
        self.registry.register(
            definition=StructureSchemaDefinition.maven_reactor_structure(),
            idempotency_key=IdempotencyKey("register-maven-structure-schema"),
            proposal_ref="ITER-003-PROPOSAL",
            review_ref="ITER-003-READINESS",
            registered_by="test",
            reason="ITER-003 frozen definition",
        )
        self.verifier_ref = "structure-admission-verifier:test@1"
        self.verifier_authority = (
            self.repository.register_structure_verifier_authority(
                verifier_ref=self.verifier_ref
            )
        )
        self.verifier = FixedTestStructureVerifier()
        self.artifact_use_proofs = FixedStructureArtifactUseProofVerifier()
        self.assessments = StructureVerifierAssessmentService(
            self.repository,
            self.verifier,
            verifier_authority=self.verifier_authority,
            clock=self.clock,
        )
        self.admissions = StructureAdmissionService(
            self.repository,
            self.scopes,
            self.artifact_use_proofs,
            verifier_authority=self.verifier_authority,
            clock=self.clock,
        )
        self.service = StructurePublicationService(
            self.repository,
            self.scopes,
            self.artifact_use_proofs,
            verifier_authority=self.verifier_authority,
            clock=self.clock,
        )

    def tearDown(self) -> None:
        self.database.close()

    def evidence(self, marker: str) -> StructureEvidence:
        excerpt = f"pom-{marker}"
        return StructureEvidence.create(
            artifact_id=StableId("source_artifact_" + marker[0] * 32),
            source_context_id=StableId("source_context_" + marker[-1] * 32),
            byte_start=0,
            byte_end=len(excerpt.encode("utf-8")),
            locator=f"{marker}/pom.xml:1",
            excerpt=excerpt,
            artifact_content_digest=digest_of({"pom": marker}),
        )

    def system(
        self, evidence: StructureEvidence, revision: str, *, key: str = "mall"
    ) -> EntityRecord:
        root = EntityRoot.software_system(
            owning_scope_id=self.scope.scope_id,
            canonical_system_key=f"https://example.invalid/{key}.git",
        )
        return EntityRecord(
            root,
            EntityState.create(
                root=root,
                state_payload_fields={
                    "label": key,
                    "effective_group_id": "org.example",
                    "artifact_id": key,
                    "effective_version": "1.0.0",
                    "packaging": "pom",
                    "source_binding_id": self.binding,
                    "source_revision": revision,
                    "root_pom_locator": "pom.xml",
                    "evidence_references": (evidence.evidence_id,),
                },
            ),
        )

    def module(
        self,
        evidence: StructureEvidence,
        revision: str,
        artifact_id: str,
    ) -> EntityRecord:
        root = EntityRoot.maven_module(
            owning_scope_id=self.scope.scope_id,
            effective_group_id="org.example",
            artifact_id=artifact_id,
        )
        return EntityRecord(
            root,
            EntityState.create(
                root=root,
                state_payload_fields={
                    "effective_version": "1.0.0",
                    "packaging": "jar",
                    "module_path": artifact_id,
                    "label": artifact_id,
                    "source_revision": revision,
                    "evidence_references": (evidence.evidence_id,),
                },
            ),
        )

    def relation(
        self,
        evidence: StructureEvidence,
        revision: str,
        subject: EntityRecord,
        object_record: EntityRecord,
        *,
        schema_ref: str | None = None,
    ) -> RelationFactRecord:
        root = RelationFactRoot.create(
            owning_scope_id=self.scope.scope_id,
            subject=subject.root.ref,
            predicate=RelationPredicate.CONTAINS_MODULE,
            object=object_record.root.ref,
            observation_modality=ObservationModality.RECURSIVE_REACTOR_MEMBERSHIP,
            schema_ref=schema_ref or "MAVEN-REACTOR-STRUCTURE@1.0.0",
        )
        return RelationFactRecord(
            root,
            RelationFactState.create(
                root=root,
                subject_state=subject.state,
                object_state=object_record.state,
                source_revision=revision,
                knowledge_context_digest=digest_of({"revision": revision}),
                evidence_references=(evidence.evidence_id,),
                predicate_state_payload_fields={
                    "module_declaration_path": "pom.xml#/project/modules/module[1]"
                },
            ),
        )

    def coverage_root(self, marker: str, *, maven: bool) -> CoverageRoot:
        if maven:
            return CoverageRoot.create(
                owning_scope_id=self.scope.scope_id,
                source_binding_id=self.binding,
                logical_reactor_root="pom.xml",
            )
        return CoverageRoot.create(
            owning_scope_id=self.scope.scope_id,
            source_binding_id=self.binding,
            logical_reactor_root=f"{marker}/pom.xml",
            profile_ref="TEST_STRUCTURE@1",
            schema_ref=self.generic_schema_ref,
            schema_digest=self.generic_schema_digest,
            maven_evaluation_context_ref="TEST-EVALUATION@1",
            maven_evaluation_context_digest=digest_of({"evaluation": 1}),
            canonicalization_ref="TEST-CANONICALIZATION@1",
            canonicalization_digest=digest_of({"canonicalization": 1}),
            coverage_root_ref=f"TEST_STRUCTURE_COVERAGE@{marker}",
        )

    def coverage(
        self,
        root: CoverageRoot,
        evidence: StructureEvidence,
        revision: str,
        manifest_records: tuple[
            EntityRecord | RelationFactRecord | LiteralFactRecord, ...
        ],
    ) -> CoverageRecord:
        manifest = CompleteMemberManifest.create(
            tuple(record.coverage_member for record in manifest_records)
        )
        return CoverageRecord(
            root,
            CoverageState.create(
                root=root,
                source_revision=revision,
                knowledge_context_digest=digest_of({"revision": revision}),
                complete_member_manifest=manifest,
                evidence_references=(evidence.evidence_id,),
            ),
        )

    def batch(
        self,
        *,
        evidence: StructureEvidence,
        entities: tuple[EntityRecord, ...],
        relations: tuple[RelationFactRecord, ...],
        coverage: CoverageRecord,
        mode: PublicationMode,
        literals: tuple[LiteralFactRecord, ...] = (),
        upstream: tuple[ExactUpstreamEntity, ...] = (),
    ) -> StructureKnowledgeBatch:
        return StructureKnowledgeBatch.admit(
            evidence=(evidence,),
            entities=entities,
            relation_facts=relations,
            literal_facts=literals,
            coverage=coverage,
            publication_mode=mode,
            exact_upstream_entities=upstream,
        )

    def accept(self, **arguments):
        verifier_ref = arguments.pop("verifier_ref")
        self.assertEqual(verifier_ref, self.verifier_ref)
        candidate_ref = arguments["candidate_ref"]
        candidate_digest = arguments["candidate_digest"]
        batch = arguments["batch"]
        provenance_digest = arguments["provenance_digest"]
        admission_key = arguments["idempotency_key"]
        proof_id, proof_digest = self.artifact_use_proofs.issue(
            candidate_ref, candidate_digest
        )
        self.verifier.expect(
            candidate_ref,
            StructureVerificationResult(
                verified_candidate_digest=candidate_digest,
                verified_evaluation_digest=candidate_digest,
                verified_report_digest=candidate_digest,
                verified_batch=batch,
            ),
        )
        assessment = self.assessments.assess(
            candidate_ref=candidate_ref,
            candidate_digest=candidate_digest,
            candidate_evaluation_digest=candidate_digest,
            candidate_report_digest=candidate_digest,
            candidate_batch=batch,
            provenance_digest=provenance_digest,
            verification_context_digest=digest_of(
                {"test_verifier_context": admission_key.value}
            ),
            artifact_use_confirmation_id=proof_id,
            artifact_use_confirmation_digest=proof_digest,
            idempotency_key=IdempotencyKey(
                f"assessment:{admission_key.value}"
            ),
        )
        return self.admissions.accept(assessment=assessment, **arguments)

    def reject(self, **arguments):
        verifier_ref = arguments.pop("verifier_ref")
        self.assertEqual(verifier_ref, self.verifier_ref)
        findings = arguments.pop("findings")
        candidate_ref = arguments["candidate_ref"]
        candidate_digest = arguments["candidate_digest"]
        batch = arguments["batch"]
        provenance_digest = arguments["provenance_digest"]
        admission_key = arguments["idempotency_key"]
        proof_id, proof_digest = self.artifact_use_proofs.issue(
            candidate_ref, candidate_digest
        )
        self.verifier.expect(
            candidate_ref,
            StructureVerificationResult(
                verified_candidate_digest=candidate_digest,
                verified_evaluation_digest=candidate_digest,
                verified_report_digest=candidate_digest,
                verified_batch=batch,
                findings=findings,
            ),
        )
        assessment = self.assessments.assess(
            candidate_ref=candidate_ref,
            candidate_digest=candidate_digest,
            candidate_evaluation_digest=candidate_digest,
            candidate_report_digest=candidate_digest,
            candidate_batch=batch,
            provenance_digest=provenance_digest,
            verification_context_digest=digest_of(
                {"test_verifier_context": admission_key.value}
            ),
            artifact_use_confirmation_id=proof_id,
            artifact_use_confirmation_digest=proof_digest,
            idempotency_key=IdempotencyKey(
                f"assessment:{admission_key.value}"
            ),
        )
        return self.admissions.reject(assessment=assessment, **arguments)

    def publish(
        self,
        batch: StructureKnowledgeBatch,
        *,
        key: str,
        expected: StableId | None,
        report_marker: str | None = None,
    ):
        admission = self.accept(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=expected,
            candidate_ref=f"candidate:{key}",
            candidate_digest=digest_of({"candidate": key, "batch": batch}),
            batch=batch,
            provenance_digest=digest_of({"provenance": key}),
            verifier_ref="structure-admission-verifier:test@1",
            idempotency_key=IdempotencyKey(f"admission:{key}"),
            caller_ref="test",
            classification="INTERNAL",
        )
        acceptance = StructureApplicationAcceptance.pass_for(
            batch,
            acceptance_ref=f"application:{key}",
            report_digest=digest_of({"complete_build_report": report_marker or key}),
        )
        return self.service.publish(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=expected,
            idempotency_key=IdempotencyKey(key),
            batch=batch,
            admission=admission,
            application_acceptance=acceptance,
            caller_ref="test",
            classification="INTERNAL",
        )

    def maven_batch(self, marker: str, modules: tuple[str, ...]):
        revision = marker * 40
        evidence = self.evidence(marker)
        system = self.system(evidence, revision)
        children = tuple(self.module(evidence, revision, name) for name in modules)
        relations = tuple(
            self.relation(evidence, revision, system, child) for child in children
        )
        records = (system, *children, *relations)
        coverage = self.coverage(
            self.coverage_root("maven", maven=True),
            evidence,
            revision,
            records,
        )
        batch = self.batch(
            evidence=evidence,
            entities=(system, *children),
            relations=relations,
            coverage=coverage,
            mode=PublicationMode.REPLACE_COVERAGE,
        )
        return batch, system, children, relations

    def test_initial_publication_round_trips_typed_endpoints_and_evidence(self) -> None:
        batch, system, children, relations = self.maven_batch("a", ("common",))
        receipt = self.publish(batch, key="initial", expected=None)

        snapshot = receipt.snapshot
        self.assertEqual(snapshot.snapshot_revision, Revision(1))
        self.assertEqual(
            snapshot.schema_adoption_mode, StructureSchemaAdoptionMode.INITIAL
        )
        self.assertEqual(receipt.admission_id.kind, "structure_admission")
        admission = self.admissions.get_admission(receipt.admission_id)
        assessment = self.admissions.get_assessment(
            admission.verifier_assessment_id
        )
        self.assertEqual(
            admission.artifact_use_confirmation_id,
            assessment.artifact_use_confirmation_id,
        )
        self.assertEqual(
            admission.artifact_use_confirmation_digest,
            assessment.artifact_use_confirmation_digest,
        )
        registration = self.registry.get_registration(snapshot.schema_ref)
        availability = self.registry.get_availability(snapshot.schema_ref)
        self.assertEqual(admission.schema_registration_digest, registration.digest)
        self.assertEqual(admission.schema_availability_digest, availability.digest)
        self.assertEqual(snapshot.schema_registration_digest, registration.digest)
        self.assertEqual(snapshot.schema_availability_digest, availability.digest)
        self.assertEqual(len(snapshot.members), 3)
        stored_relation = self.repository.get_relation_fact(
            snapshot.snapshot_id, relations[0].root_id
        )
        self.assertEqual(stored_relation, relations[0])
        self.assertEqual(stored_relation.root.subject, system.root.ref)
        self.assertEqual(stored_relation.root.object, children[0].root.ref)
        self.assertEqual(
            self.repository.get_entity(snapshot.snapshot_id, system.root_id), system
        )
        full_evidence = self.service.get_evidence(batch.evidence[0].evidence_id)
        metadata = self.service.get_evidence_metadata(full_evidence.evidence_id)
        self.assertEqual(full_evidence.excerpt, "pom-a")
        self.assertEqual(metadata.locator, "a/pom.xml:1")
        self.assertFalse(hasattr(metadata, "excerpt"))

        with self.database.read() as connection:
            entity_root_count = connection.execute(
                "SELECT COUNT(*) FROM knw_structure_entity_roots"
            ).fetchone()[0]
            entity_state_count = connection.execute(
                "SELECT COUNT(*) FROM knw_structure_entity_states"
            ).fetchone()[0]
            legacy_tables = connection.execute(
                """SELECT COUNT(*) FROM sqlite_schema
                   WHERE type = 'table' AND name IN
                   ('knw_entities', 'knw_facts', 'knw_snapshots')"""
            ).fetchone()[0]
        self.assertEqual(entity_root_count, 2)
        self.assertEqual(entity_state_count, 2)
        self.assertEqual(legacy_tables, 0)

    def test_public_admission_rejects_unpersisted_artifact_use_proof(self) -> None:
        batch, _, _, _ = self.maven_batch("c", ("common",))
        candidate_ref = "candidate:unpersisted-artifact-proof"
        candidate_digest = digest_of(
            {"candidate": "unpersisted-artifact-proof", "batch": batch}
        )
        provenance_digest = digest_of(
            {"provenance": "unpersisted-artifact-proof"}
        )
        self.verifier.expect(
            candidate_ref,
            StructureVerificationResult(
                verified_candidate_digest=candidate_digest,
                verified_evaluation_digest=candidate_digest,
                verified_report_digest=candidate_digest,
                verified_batch=batch,
            ),
        )
        forged_proof_id = StableId("artifact_use_" + "f" * 32)
        forged_proof_digest = digest_of({"forged": "artifact-use-proof"})
        assessment = self.assessments.assess(
            candidate_ref=candidate_ref,
            candidate_digest=candidate_digest,
            candidate_evaluation_digest=candidate_digest,
            candidate_report_digest=candidate_digest,
            candidate_batch=batch,
            provenance_digest=provenance_digest,
            verification_context_digest=digest_of(
                {"verification_context": "unpersisted-artifact-proof"}
            ),
            artifact_use_confirmation_id=forged_proof_id,
            artifact_use_confirmation_digest=forged_proof_digest,
            idempotency_key=IdempotencyKey(
                "assessment:unpersisted-artifact-proof"
            ),
        )

        with self.assertRaises(DomainError) as raised:
            self.admissions.accept(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=None,
                candidate_ref=candidate_ref,
                candidate_digest=candidate_digest,
                batch=batch,
                provenance_digest=provenance_digest,
                assessment=assessment,
                idempotency_key=IdempotencyKey(
                    "admission:unpersisted-artifact-proof"
                ),
                caller_ref="test",
                classification="INTERNAL",
            )

        self.assertEqual(
            raised.exception.details["reason_code"],
            "TEST_ARTIFACT_USE_PROOF_MISMATCH",
        )
        self.assertIsNone(self.service.current_snapshot(self.scope.scope_id))

    def test_publication_rechecks_artifact_use_proof_before_current(self) -> None:
        batch, _, _, _ = self.maven_batch("d", ("common",))
        admission = self.accept(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=None,
            candidate_ref="candidate:publisher-proof-reread",
            candidate_digest=digest_of(
                {"candidate": "publisher-proof-reread", "batch": batch}
            ),
            batch=batch,
            provenance_digest=digest_of(
                {"provenance": "publisher-proof-reread"}
            ),
            verifier_ref=self.verifier_ref,
            idempotency_key=IdempotencyKey("admission:publisher-proof-reread"),
            caller_ref="test",
            classification="INTERNAL",
        )
        self.artifact_use_proofs.forget(
            admission.artifact_use_confirmation_id
        )
        acceptance = StructureApplicationAcceptance.pass_for(
            batch,
            acceptance_ref="application:publisher-proof-reread",
            report_digest=digest_of({"report": "publisher-proof-reread"}),
        )

        with self.assertRaises(DomainError) as raised:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=None,
                idempotency_key=IdempotencyKey("publish:publisher-proof-reread"),
                batch=batch,
                admission=admission,
                application_acceptance=acceptance,
                caller_ref="test",
                classification="INTERNAL",
            )

        self.assertEqual(
            raised.exception.details["reason_code"],
            "TEST_ARTIFACT_USE_PROOF_MISMATCH",
        )
        self.assertIsNone(self.service.current_snapshot(self.scope.scope_id))

    def test_replacement_a_b_a_deletes_only_current_and_preserves_history(self) -> None:
        batch_a, _, children_a, _ = self.maven_batch("a", ("common",))
        first = self.publish(batch_a, key="a1", expected=None)
        batch_b, _, children_b, _ = self.maven_batch(
            "b", ("common", "security")
        )
        second = self.publish(
            batch_b, key="b", expected=first.snapshot.snapshot_id
        )
        batch_a2, _, children_a2, _ = self.maven_batch("a", ("common",))
        third = self.publish(
            batch_a2, key="a2", expected=second.snapshot.snapshot_id
        )

        self.assertEqual(len(first.snapshot.members), 3)
        self.assertEqual(len(second.snapshot.members), 5)
        self.assertEqual(len(third.snapshot.members), 3)
        self.assertEqual(children_a[0].root_id, children_b[0].root_id)
        self.assertNotEqual(children_a[0].state_id, children_b[0].state_id)
        self.assertEqual(children_a[0].state_id, children_a2[0].state_id)
        self.assertEqual(
            self.repository.get_snapshot(second.snapshot.snapshot_id),
            second.snapshot,
        )
        self.assertIsNotNone(
            self.repository.get_entity(
                second.snapshot.snapshot_id, children_b[1].root_id
            )
        )
        with self.assertRaises(DomainError):
            self.repository.get_entity(
                third.snapshot.snapshot_id, children_b[1].root_id
            )

    def test_enrich_rejects_different_state_and_idempotency_is_exact(self) -> None:
        evidence_a = self.evidence("a")
        entity_a = self.module(evidence_a, "a" * 40, "alpha")
        root = self.coverage_root("enrich", maven=False)
        batch_a = self.batch(
            evidence=evidence_a,
            entities=(entity_a,),
            relations=(),
            coverage=self.coverage(root, evidence_a, "a" * 40, (entity_a,)),
            mode=PublicationMode.ENRICH,
        )
        first = self.publish(batch_a, key="enrich-a", expected=None)
        replay = self.publish(batch_a, key="enrich-a", expected=None)
        self.assertEqual(replay.publication_id, first.publication_id)

        evidence_c = self.evidence("c")
        entity_c = self.module(evidence_c, "c" * 40, "beta")
        union_batch = self.batch(
            evidence=evidence_c,
            entities=(entity_c,),
            relations=(),
            coverage=self.coverage(
                root,
                evidence_c,
                "c" * 40,
                (entity_a, entity_c),
            ),
            mode=PublicationMode.ENRICH,
        )
        union = self.publish(
            union_batch,
            key="enrich-union",
            expected=first.snapshot.snapshot_id,
        )
        self.assertEqual(len(union.snapshot.members), 2)

        evidence_b = self.evidence("b")
        entity_b = self.module(evidence_b, "b" * 40, "alpha")
        batch_b = self.batch(
            evidence=evidence_b,
            entities=(entity_b,),
            relations=(),
            coverage=self.coverage(
                root, evidence_b, "b" * 40, (entity_b, entity_c)
            ),
            mode=PublicationMode.ENRICH,
        )
        with self.assertRaises(DomainError) as conflict:
            self.publish(
                batch_b,
                key="enrich-state-conflict",
                expected=union.snapshot.snapshot_id,
            )
        self.assertEqual(
            conflict.exception.details["reason_code"], "ENRICH_STATE_CONFLICT"
        )
        self.assertEqual(
            self.service.current_snapshot(self.scope.scope_id), union.snapshot
        )

        with self.assertRaises(DomainError) as mismatch:
            self.publish(batch_b, key="enrich-a", expected=None)
        self.assertEqual(mismatch.exception.code, ErrorCode.IDEMPOTENCY_MISMATCH)
        with self.assertRaises(DomainError) as stale:
            self.publish(batch_b, key="stale-current", expected=None)
        self.assertEqual(stale.exception.code, ErrorCode.REVISION_CONFLICT)

    def test_literal_fact_root_and_state_round_trip_without_text_reinterpretation(self) -> None:
        evidence = self.evidence("d")
        system = self.system(evidence, "d" * 40)
        root = LiteralFactRoot.create(
            owning_scope_id=self.scope.scope_id,
            schema_ref=self.generic_schema_ref,
            subject=system.root.ref,
            predicate="HAS_BUILD_LABEL",
            object=LiteralObject(LiteralType.STRING, "release"),
            observation_modality="POM_TEXT@1",
        )
        literal = LiteralFactRecord(
            root,
            LiteralFactState.create(
                root=root,
                subject_state=system.state,
                source_revision="d" * 40,
                knowledge_context_digest=digest_of({"revision": "d" * 40}),
                evidence_references=(evidence.evidence_id,),
            ),
        )
        coverage_root = self.coverage_root("literal", maven=False)
        batch = self.batch(
            evidence=evidence,
            entities=(system,),
            relations=(),
            literals=(literal,),
            coverage=self.coverage(
                coverage_root,
                evidence,
                "d" * 40,
                (system, literal),
            ),
            mode=PublicationMode.REPLACE_COVERAGE,
        )
        receipt = self.publish(batch, key="literal", expected=None)

        stored = self.repository.get_literal_fact(
            receipt.snapshot.snapshot_id, literal.root_id
        )
        self.assertEqual(stored, literal)
        self.assertEqual(stored.root.object.literal_type, LiteralType.STRING)
        self.assertEqual(stored.root.object.value, "release")

    def test_enrich_union_overlap_and_replacement_preserve_other_coverage(self) -> None:
        evidence_a = self.evidence("a")
        first_entity = self.module(evidence_a, "a" * 40, "alpha")
        first_root = self.coverage_root("first", maven=False)
        first_batch = self.batch(
            evidence=evidence_a,
            entities=(first_entity,),
            relations=(),
            coverage=self.coverage(
                first_root, evidence_a, "a" * 40, (first_entity,)
            ),
            mode=PublicationMode.ENRICH,
        )
        first = self.publish(first_batch, key="first-coverage", expected=None)

        evidence_b = self.evidence("b")
        second_entity = self.module(evidence_b, "b" * 40, "beta")
        second_root = self.coverage_root("second", maven=False)
        second_batch = self.batch(
            evidence=evidence_b,
            entities=(second_entity,),
            relations=(),
            coverage=self.coverage(
                second_root, evidence_b, "b" * 40, (second_entity,)
            ),
            mode=PublicationMode.ENRICH,
        )
        second = self.publish(
            second_batch,
            key="second-coverage",
            expected=first.snapshot.snapshot_id,
        )
        self.assertEqual(len(second.snapshot.members), 2)

        overlap_coverage = self.coverage(
            second_root,
            evidence_a,
            "c" * 40,
            (first_entity, second_entity),
        )
        overlap_batch = self.batch(
            evidence=evidence_a,
            entities=(first_entity,),
            relations=(),
            coverage=overlap_coverage,
            mode=PublicationMode.ENRICH,
        )
        with self.assertRaises(DomainError) as overlap:
            self.publish(
                overlap_batch,
                key="overlap",
                expected=second.snapshot.snapshot_id,
            )
        self.assertEqual(
            overlap.exception.details["reason_code"],
            "COVERAGE_OWNERSHIP_OVERLAP",
        )

        empty_replacement = self.batch(
            evidence=evidence_a,
            entities=(),
            relations=(),
            coverage=self.coverage(first_root, evidence_a, "d" * 40, ()),
            mode=PublicationMode.REPLACE_COVERAGE,
        )
        third = self.publish(
            empty_replacement,
            key="replace-first-empty",
            expected=second.snapshot.snapshot_id,
        )
        self.assertEqual(
            tuple(member.root_id for member in third.snapshot.members),
            (second_entity.root_id,),
        )
        self.assertEqual(
            self.repository.owner_of(
                third.snapshot.snapshot_id, second_entity.root_id
            ),
            second_root.coverage_root_id,
        )

    def test_inherited_relation_becoming_dangling_rolls_back_current(self) -> None:
        evidence_a = self.evidence("a")
        system = self.system(evidence_a, "a" * 40)
        module = self.module(evidence_a, "a" * 40, "alpha")
        entity_coverage_root = self.coverage_root("entities", maven=False)
        entity_batch = self.batch(
            evidence=evidence_a,
            entities=(system, module),
            relations=(),
            coverage=self.coverage(
                entity_coverage_root,
                evidence_a,
                "a" * 40,
                (system, module),
            ),
            mode=PublicationMode.ENRICH,
        )
        first = self.publish(entity_batch, key="entities", expected=None)

        evidence_b = self.evidence("b")
        relation = self.relation(
            evidence_b,
            "b" * 40,
            system,
            module,
            schema_ref=self.generic_schema_ref,
        )
        relation_coverage_root = self.coverage_root("relations", maven=False)
        relation_batch = self.batch(
            evidence=evidence_b,
            entities=(),
            relations=(relation,),
            coverage=self.coverage(
                relation_coverage_root,
                evidence_b,
                "b" * 40,
                (relation,),
            ),
            mode=PublicationMode.ENRICH,
            upstream=(
                ExactUpstreamEntity(first.snapshot.snapshot_id, system),
                ExactUpstreamEntity(first.snapshot.snapshot_id, module),
            ),
        )
        second = self.publish(
            relation_batch, key="relation", expected=first.snapshot.snapshot_id
        )

        removal_batch = self.batch(
            evidence=evidence_a,
            entities=(system,),
            relations=(),
            coverage=self.coverage(
                entity_coverage_root, evidence_a, "c" * 40, (system,)
            ),
            mode=PublicationMode.REPLACE_COVERAGE,
        )
        with self.assertRaises(DomainError) as dangling:
            self.publish(
                removal_batch,
                key="dangling-removal",
                expected=second.snapshot.snapshot_id,
            )
        self.assertEqual(
            dangling.exception.details["reason_code"],
            "DANGLING_RELATION_ENDPOINT",
        )
        self.assertEqual(
            self.service.current_snapshot(self.scope.scope_id), second.snapshot
        )

    def test_persisted_admission_is_independent_and_exact(self) -> None:
        batch_a, _, _, _ = self.maven_batch("a", ("common",))
        current = self.publish(batch_a, key="admission-base", expected=None)
        batch_b, _, _, _ = self.maven_batch("b", ("common", "security"))
        admission = self.accept(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=current.snapshot.snapshot_id,
            candidate_ref="candidate:admission-b",
            candidate_digest=digest_of({"candidate": "admission-b"}),
            batch=batch_b,
            provenance_digest=digest_of({"source_operations": "admission-b"}),
            verifier_ref="structure-admission-verifier:test@1",
            idempotency_key=IdempotencyKey("admission:exact-b"),
            caller_ref="test",
            classification="INTERNAL",
        )
        self.assertEqual(
            self.admissions.get_admission(admission.admission_id), admission
        )
        acceptance = StructureApplicationAcceptance.pass_for(
            batch_b,
            acceptance_ref="application:admission-b",
            report_digest=digest_of({"report": "admission-b"}),
        )

        rejected = self.reject(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=current.snapshot.snapshot_id,
            candidate_ref="candidate:admission-b-rejected",
            candidate_digest=digest_of({"candidate": "admission-b-rejected"}),
            batch=batch_b,
            provenance_digest=digest_of({"source_operations": "admission-b"}),
            verifier_ref="structure-admission-verifier:test@1",
            findings=(
                StructureAdmissionFinding(
                    "SEMANTIC_REVIEW_REJECTED", "independent verifier rejected closure"
                ),
            ),
            idempotency_key=IdempotencyKey("admission:reject-b"),
            caller_ref="test",
            classification="INTERNAL",
        )
        with self.assertRaises(DomainError) as rejected_error:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=current.snapshot.snapshot_id,
                idempotency_key=IdempotencyKey("publish:rejected-admission"),
                batch=batch_b,
                admission=rejected,
                application_acceptance=acceptance,
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            rejected_error.exception.details["reason_code"], "ADMISSION_NOT_ACCEPT"
        )

        tampered = replace(
            admission, candidate_digest=digest_of({"candidate": "tampered"})
        )
        with self.assertRaises(DomainError) as tamper_error:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=current.snapshot.snapshot_id,
                idempotency_key=IdempotencyKey("publish:tampered-admission"),
                batch=batch_b,
                admission=tampered,
                application_acceptance=acceptance,
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            tamper_error.exception.details["reason_code"],
            "ADMISSION_DECISION_DIGEST_MISMATCH",
        )

        missing_id = StableId("structure_admission_" + "f" * 32)
        missing = replace(
            admission,
            admission_id=missing_id,
            digest=structure_admission_decision_digest(
                admission_id=missing_id,
                outcome=admission.outcome,
                candidate_ref=admission.candidate_ref,
                candidate_digest=admission.candidate_digest,
                batch_digest=admission.batch_digest,
                closure_digest=admission.closure_digest,
                read_set_digest=admission.read_set_digest,
                scope_id=admission.scope_id,
                expected_scope_revision=admission.expected_scope_revision,
                scope_assertion_digest=admission.scope_assertion_digest,
                expected_current_snapshot_id=admission.expected_current_snapshot_id,
                schema_ref=admission.schema_ref,
                schema_digest=admission.schema_digest,
                schema_registration_digest=admission.schema_registration_digest,
                schema_availability_digest=admission.schema_availability_digest,
                knowledge_context_digest=admission.knowledge_context_digest,
                upstream_digest=admission.upstream_digest,
                provenance_digest=admission.provenance_digest,
                artifact_use_confirmation_id=(
                    admission.artifact_use_confirmation_id
                ),
                artifact_use_confirmation_digest=(
                    admission.artifact_use_confirmation_digest
                ),
                verifier_assessment_id=admission.verifier_assessment_id,
                verifier_assessment_digest=admission.verifier_assessment_digest,
                verifier_authority_id=admission.verifier_authority_id,
                verifier_ref=admission.verifier_ref,
                findings=admission.findings,
                decided_at=admission.decided_at,
            ),
        )
        with self.assertRaises(DomainError) as missing_error:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=current.snapshot.snapshot_id,
                idempotency_key=IdempotencyKey("publish:missing-admission"),
                batch=batch_b,
                admission=missing,
                application_acceptance=acceptance,
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            missing_error.exception.details["reason_code"], "ADMISSION_NOT_PERSISTED"
        )

        with self.assertRaises(DomainError) as mismatch_error:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=current.snapshot.snapshot_id,
                idempotency_key=IdempotencyKey("publish:mismatched-admission"),
                batch=batch_a,
                admission=admission,
                application_acceptance=StructureApplicationAcceptance.pass_for(
                    batch_a,
                    acceptance_ref="application:mismatch",
                    report_digest=digest_of({"report": "mismatch"}),
                ),
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            mismatch_error.exception.details["reason_code"],
            "ADMISSION_CLOSURE_MISMATCH",
        )
        self.assertEqual(
            self.service.current_snapshot(self.scope.scope_id), current.snapshot
        )

        published = self.service.publish(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=current.snapshot.snapshot_id,
            idempotency_key=IdempotencyKey("publish:exact-admission"),
            batch=batch_b,
            admission=admission,
            application_acceptance=acceptance,
            caller_ref="test",
            classification="INTERNAL",
        )
        self.assertEqual(published.admission_id, admission.admission_id)
        self.assertEqual(
            published.snapshot.schema_adoption_mode,
            StructureSchemaAdoptionMode.UNCHANGED,
        )

    def test_public_admission_cannot_self_certify_forged_partial_closure(self) -> None:
        full_batch, system, children, relations = self.maven_batch(
            "f", ("common", "security")
        )
        evidence = full_batch.evidence[0]
        partial_relations = relations[:1]
        partial_batch = self.batch(
            evidence=evidence,
            entities=(system, *children),
            relations=partial_relations,
            coverage=self.coverage(
                full_batch.coverage.root,
                evidence,
                "f" * 40,
                (system, *children, *partial_relations),
            ),
            mode=PublicationMode.REPLACE_COVERAGE,
        )
        candidate_ref = "candidate:forged-partial-closure"
        candidate_digest = digest_of({"candidate": "forged-partial-closure"})
        provenance_digest = digest_of({"provenance": "forged-partial-closure"})
        verification_context_digest = digest_of(
            {"verification_context": "forged-partial-closure"}
        )
        proof_id, proof_digest = self.artifact_use_proofs.issue(
            candidate_ref, candidate_digest
        )

        attacker_verifier = FixedTestStructureVerifier()
        attacker_verifier.expect(
            candidate_ref,
            StructureVerificationResult(
                verified_candidate_digest=candidate_digest,
                verified_evaluation_digest=candidate_digest,
                verified_report_digest=candidate_digest,
                verified_batch=partial_batch,
            ),
        )
        cloned_capability = replace(self.verifier_authority)
        cloned_capability_assessments = StructureVerifierAssessmentService(
            self.repository,
            attacker_verifier,
            verifier_authority=cloned_capability,
            clock=self.clock,
        )
        with self.assertRaises(DomainError) as cloned_capability_error:
            cloned_capability_assessments.assess(
                candidate_ref=candidate_ref,
                candidate_digest=candidate_digest,
                candidate_evaluation_digest=candidate_digest,
                candidate_report_digest=candidate_digest,
                candidate_batch=partial_batch,
                provenance_digest=provenance_digest,
                verification_context_digest=verification_context_digest,
                artifact_use_confirmation_id=proof_id,
                artifact_use_confirmation_digest=proof_digest,
                idempotency_key=IdempotencyKey(
                    "assessment:cloned-verifier-capability"
                ),
            )
        self.assertEqual(
            cloned_capability_error.exception.details["reason_code"],
            "VERIFIER_AUTHORITY_CAPABILITY_INVALID",
        )
        attacker_authority = self.repository.register_structure_verifier_authority(
            verifier_ref=self.verifier_ref
        )
        attacker_assessments = StructureVerifierAssessmentService(
            self.repository,
            attacker_verifier,
            verifier_authority=attacker_authority,
            clock=self.clock,
        )
        forged_assessment = attacker_assessments.assess(
            candidate_ref=candidate_ref,
            candidate_digest=candidate_digest,
            candidate_evaluation_digest=candidate_digest,
            candidate_report_digest=candidate_digest,
            candidate_batch=partial_batch,
            provenance_digest=provenance_digest,
            verification_context_digest=verification_context_digest,
            artifact_use_confirmation_id=proof_id,
            artifact_use_confirmation_digest=proof_digest,
            idempotency_key=IdempotencyKey("assessment:forged-self-certification"),
        )
        self.assertEqual(
            forged_assessment.outcome, StructureVerifierAssessmentOutcome.PASS
        )
        self.assertEqual(forged_assessment.verifier_ref, self.verifier_ref)
        self.assertNotEqual(
            forged_assessment.verifier_authority_id,
            self.verifier_authority.authority_id,
        )
        self.assertEqual(
            self.admissions.get_assessment(forged_assessment.assessment_id),
            forged_assessment,
        )
        with self.assertRaises(DomainError) as untrusted:
            self.admissions.accept(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=None,
                candidate_ref=candidate_ref,
                candidate_digest=candidate_digest,
                batch=partial_batch,
                provenance_digest=provenance_digest,
                assessment=forged_assessment,
                idempotency_key=IdempotencyKey("admission:forged-self-certification"),
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            untrusted.exception.details["reason_code"],
            "VERIFIER_AUTHORITY_MISMATCH",
        )
        attacker_admissions = StructureAdmissionService(
            self.repository,
            self.scopes,
            self.artifact_use_proofs,
            verifier_authority=attacker_authority,
            clock=self.clock,
        )
        with self.assertRaises(DomainError) as direct_bypass:
            attacker_admissions.accept(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=None,
                candidate_ref=candidate_ref,
                candidate_digest=candidate_digest,
                batch=partial_batch,
                provenance_digest=provenance_digest,
                assessment=forged_assessment,
                idempotency_key=IdempotencyKey(
                    "admission:direct-forged-self-certification"
                ),
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            direct_bypass.exception.details["reason_code"],
            "VERIFIER_ADMISSION_AUTHORITY_DENIED",
        )

        verified_digest = digest_of({"candidate": "independent-full-closure"})
        self.verifier.expect(
            candidate_ref,
            StructureVerificationResult(
                verified_candidate_digest=verified_digest,
                verified_evaluation_digest=verified_digest,
                verified_report_digest=verified_digest,
                verified_batch=full_batch,
            ),
        )
        assessment = self.assessments.assess(
            candidate_ref=candidate_ref,
            candidate_digest=candidate_digest,
            candidate_evaluation_digest=candidate_digest,
            candidate_report_digest=candidate_digest,
            candidate_batch=partial_batch,
            provenance_digest=provenance_digest,
            verification_context_digest=verification_context_digest,
            artifact_use_confirmation_id=proof_id,
            artifact_use_confirmation_digest=proof_digest,
            idempotency_key=IdempotencyKey("assessment:independent-rebuild"),
        )
        self.assertEqual(assessment.outcome, StructureVerifierAssessmentOutcome.FAIL)
        self.assertIn(
            "CLOSURE_DIGEST_MISMATCH", {finding.code for finding in assessment.findings}
        )
        with self.assertRaises(DomainError):
            self.admissions.accept(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=None,
                candidate_ref=candidate_ref,
                candidate_digest=candidate_digest,
                batch=partial_batch,
                provenance_digest=provenance_digest,
                assessment=assessment,
                idempotency_key=IdempotencyKey("admission:independent-rebuild"),
                caller_ref="test",
                classification="INTERNAL",
            )

        self.assertFalse(hasattr(self.admissions, "assess"))
        with self.database.read() as connection:
            admission_count = connection.execute(
                "SELECT COUNT(*) FROM knw_structure_admissions"
            ).fetchone()[0]
        self.assertEqual(admission_count, 0)
        self.assertIsNone(self.service.current_snapshot(self.scope.scope_id))

    def test_schema_deprecation_between_admission_and_publish_fails_closed(self) -> None:
        batch_a, _, _, _ = self.maven_batch("a", ("common",))
        first = self.publish(batch_a, key="schema-history-a", expected=None)
        adoption_before = self.registry.get_adoption(self.scope.scope_id)
        self.assertIsNotNone(adoption_before)
        batch_b, _, _, _ = self.maven_batch("b", ("common", "security"))
        admission = self.accept(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=first.snapshot.snapshot_id,
            candidate_ref="candidate:before-deprecation",
            candidate_digest=digest_of({"candidate": "before-deprecation"}),
            batch=batch_b,
            provenance_digest=digest_of({"provenance": "before-deprecation"}),
            verifier_ref="structure-admission-verifier:test@1",
            idempotency_key=IdempotencyKey("admission:before-deprecation"),
            caller_ref="test",
            classification="INTERNAL",
        )
        available = self.registry.get_availability(batch_b.coverage.root.schema_ref)
        deprecated = self.registry.deprecate(
            schema_ref=batch_b.coverage.root.schema_ref,
            schema_digest=batch_b.coverage.root.schema_digest,
            expected_availability_revision=available.availability_revision,
            idempotency_key=IdempotencyKey("deprecate-maven-schema"),
            changed_by="test",
            reason="concurrent availability loss",
        )
        self.assertEqual(
            deprecated.status, StructureSchemaAvailabilityStatus.DEPRECATED
        )
        self.assertEqual(
            self.registry.get_availability(
                batch_b.coverage.root.schema_ref, Revision(1)
            ),
            available,
        )
        with self.assertRaises(DomainError) as unavailable:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=first.snapshot.snapshot_id,
                idempotency_key=IdempotencyKey("publish:after-deprecation"),
                batch=batch_b,
                admission=admission,
                application_acceptance=StructureApplicationAcceptance.pass_for(
                    batch_b,
                    acceptance_ref="application:after-deprecation",
                    report_digest=digest_of({"report": "after-deprecation"}),
                ),
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            unavailable.exception.details["reason_code"], "SCHEMA_NOT_AVAILABLE"
        )
        self.assertEqual(
            self.admissions.get_admission(admission.admission_id), admission
        )
        self.assertEqual(
            self.service.current_snapshot(self.scope.scope_id), first.snapshot
        )
        self.assertEqual(
            self.service.get_snapshot(first.snapshot.snapshot_id), first.snapshot
        )
        self.assertEqual(self.registry.get_adoption(self.scope.scope_id), adoption_before)

    def test_persisted_admission_row_tamper_keeps_current(self) -> None:
        batch_a, _, _, _ = self.maven_batch("a", ("common",))
        first = self.publish(batch_a, key="admission-row-base", expected=None)
        batch_b, _, _, _ = self.maven_batch("b", ("common", "security"))
        admission = self.accept(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=first.snapshot.snapshot_id,
            candidate_ref="candidate:persisted-row-tamper",
            candidate_digest=digest_of({"candidate": "persisted-row-tamper"}),
            batch=batch_b,
            provenance_digest=digest_of({"provenance": "persisted-row-tamper"}),
            verifier_ref="structure-admission-verifier:test@1",
            idempotency_key=IdempotencyKey("admission:persisted-row-tamper"),
            caller_ref="test",
            classification="INTERNAL",
        )
        with self.database.transaction() as connection:
            connection.execute(
                """UPDATE knw_structure_admissions SET admission_digest = ?
                   WHERE admission_id = ?""",
                (
                    digest_of({"tampered_admission": True}).value,
                    admission.admission_id.value,
                ),
            )
        with self.assertRaises(DomainError) as tampered:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=first.snapshot.snapshot_id,
                idempotency_key=IdempotencyKey("publish:persisted-row-tamper"),
                batch=batch_b,
                admission=admission,
                application_acceptance=StructureApplicationAcceptance.pass_for(
                    batch_b,
                    acceptance_ref="application:persisted-row-tamper",
                    report_digest=digest_of({"report": "persisted-row-tamper"}),
                ),
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            tampered.exception.details["reason_code"],
            "ADMISSION_DECISION_DIGEST_MISMATCH",
        )
        self.assertEqual(
            self.service.current_snapshot(self.scope.scope_id), first.snapshot
        )
        self.assertEqual(
            self.service.get_snapshot(first.snapshot.snapshot_id), first.snapshot
        )

    def test_publisher_rejects_tampered_verifier_assessment(self) -> None:
        batch, _, _, _ = self.maven_batch("a", ("common",))
        admission = self.accept(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=None,
            candidate_ref="candidate:assessment-tamper",
            candidate_digest=digest_of({"candidate": "assessment-tamper"}),
            batch=batch,
            provenance_digest=digest_of({"provenance": "assessment-tamper"}),
            verifier_ref="structure-admission-verifier:test@1",
            idempotency_key=IdempotencyKey("admission:assessment-tamper"),
            caller_ref="test",
            classification="INTERNAL",
        )
        with self.database.transaction() as connection:
            connection.execute(
                """UPDATE knw_structure_verifier_assessments
                   SET assessment_digest = ? WHERE assessment_id = ?""",
                (
                    digest_of({"tampered_assessment": True}).value,
                    admission.verifier_assessment_id.value,
                ),
            )
        with self.assertRaises(DomainError) as tampered:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=None,
                idempotency_key=IdempotencyKey("publish:assessment-tamper"),
                batch=batch,
                admission=admission,
                application_acceptance=StructureApplicationAcceptance.pass_for(
                    batch,
                    acceptance_ref="application:assessment-tamper",
                    report_digest=digest_of({"report": "assessment-tamper"}),
                ),
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            tampered.exception.details["reason_code"],
            "VERIFIER_ASSESSMENT_DIGEST_MISMATCH",
        )
        self.assertIsNone(self.service.current_snapshot(self.scope.scope_id))

    def test_publisher_rejects_missing_verifier_assessment(self) -> None:
        batch, _, _, _ = self.maven_batch("a", ("common",))
        admission = self.accept(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=None,
            candidate_ref="candidate:assessment-missing",
            candidate_digest=digest_of({"candidate": "assessment-missing"}),
            batch=batch,
            provenance_digest=digest_of({"provenance": "assessment-missing"}),
            verifier_ref="structure-admission-verifier:test@1",
            idempotency_key=IdempotencyKey("admission:assessment-missing"),
            caller_ref="test",
            classification="INTERNAL",
        )
        # Simulate storage corruption that bypassed SQLite's normal FK fence.
        with self.database.read() as connection:
            connection.execute("PRAGMA foreign_keys = OFF")
            try:
                connection.execute(
                    """DELETE FROM knw_structure_verifier_assessments
                       WHERE assessment_id = ?""",
                    (admission.verifier_assessment_id.value,),
                )
            finally:
                connection.execute("PRAGMA foreign_keys = ON")
        with self.assertRaises(DomainError) as missing:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=None,
                idempotency_key=IdempotencyKey("publish:assessment-missing"),
                batch=batch,
                admission=admission,
                application_acceptance=StructureApplicationAcceptance.pass_for(
                    batch,
                    acceptance_ref="application:assessment-missing",
                    report_digest=digest_of({"report": "assessment-missing"}),
                ),
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            missing.exception.details["reason_code"],
            "VERIFIER_ASSESSMENT_NOT_PERSISTED",
        )
        self.assertIsNone(self.service.current_snapshot(self.scope.scope_id))

    def test_schema_change_wrong_digest_and_registry_tamper_keep_history(self) -> None:
        evidence_a = self.evidence("a")
        entity_a = self.module(evidence_a, "a" * 40, "alpha")
        root_a = self.coverage_root("schema-a", maven=False)
        batch_a = self.batch(
            evidence=evidence_a,
            entities=(entity_a,),
            relations=(),
            coverage=self.coverage(root_a, evidence_a, "a" * 40, (entity_a,)),
            mode=PublicationMode.REPLACE_COVERAGE,
        )
        first = self.publish(batch_a, key="schema-a", expected=None)

        wrong_digest_root = CoverageRoot.create(
            owning_scope_id=self.scope.scope_id,
            source_binding_id=self.binding,
            logical_reactor_root="wrong-digest/pom.xml",
            profile_ref="TEST_STRUCTURE@1",
            schema_ref=self.generic_schema_ref,
            schema_digest=digest_of({"schema": "wrong-candidate-digest"}),
            maven_evaluation_context_ref="TEST-EVALUATION@1",
            maven_evaluation_context_digest=digest_of({"evaluation": 1}),
            canonicalization_ref="TEST-CANONICALIZATION@1",
            canonicalization_digest=digest_of({"canonicalization": 1}),
            coverage_root_ref="TEST_STRUCTURE_WRONG_DIGEST_COVERAGE@1",
        )
        wrong_digest_batch = self.batch(
            evidence=evidence_a,
            entities=(entity_a,),
            relations=(),
            coverage=self.coverage(
                wrong_digest_root, evidence_a, "a" * 40, (entity_a,)
            ),
            mode=PublicationMode.REPLACE_COVERAGE,
        )
        with self.assertRaises(DomainError) as wrong_digest:
            self.accept(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=first.snapshot.snapshot_id,
                candidate_ref="candidate:wrong-schema-digest",
                candidate_digest=digest_of({"candidate": "wrong-schema-digest"}),
                batch=wrong_digest_batch,
                provenance_digest=digest_of({"provenance": "wrong-schema-digest"}),
                verifier_ref="structure-admission-verifier:test@1",
                idempotency_key=IdempotencyKey("admission:wrong-schema-digest"),
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            wrong_digest.exception.details["reason_code"],
            "ADMISSION_SCHEMA_DIGEST_MISMATCH",
        )
        self.assertEqual(
            self.service.current_snapshot(self.scope.scope_id), first.snapshot
        )

        alt_ref = "TEST-STRUCTURE-ALT@1"
        alt_digest = digest_of({"schema": alt_ref})
        self.registry.register(
            definition=StructureSchemaDefinition.create(
                schema_ref=alt_ref, schema_digest=alt_digest
            ),
            idempotency_key=IdempotencyKey("register-alt-structure-schema"),
            proposal_ref="proposal:test-alt-structure@1",
            review_ref="review:test-alt-structure@1",
            registered_by="test",
            reason="schema change counterexample",
        )
        evidence_b = self.evidence("b")
        entity_b = self.module(evidence_b, "b" * 40, "alpha")
        root_b = CoverageRoot.create(
            owning_scope_id=self.scope.scope_id,
            source_binding_id=self.binding,
            logical_reactor_root="schema-alt/pom.xml",
            profile_ref="TEST_STRUCTURE_ALT@1",
            schema_ref=alt_ref,
            schema_digest=alt_digest,
            maven_evaluation_context_ref="TEST-EVALUATION@1",
            maven_evaluation_context_digest=digest_of({"evaluation": 1}),
            canonicalization_ref="TEST-CANONICALIZATION@1",
            canonicalization_digest=digest_of({"canonicalization": 1}),
            coverage_root_ref="TEST_STRUCTURE_ALT_COVERAGE@1",
        )
        batch_b = self.batch(
            evidence=evidence_b,
            entities=(entity_b,),
            relations=(),
            coverage=self.coverage(root_b, evidence_b, "b" * 40, (entity_b,)),
            mode=PublicationMode.REPLACE_COVERAGE,
        )
        admission_b = self.accept(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=first.snapshot.snapshot_id,
            candidate_ref="candidate:schema-change",
            candidate_digest=digest_of({"candidate": "schema-change"}),
            batch=batch_b,
            provenance_digest=digest_of({"provenance": "schema-change"}),
            verifier_ref="structure-admission-verifier:test@1",
            idempotency_key=IdempotencyKey("admission:schema-change"),
            caller_ref="test",
            classification="INTERNAL",
        )
        with self.assertRaises(DomainError) as schema_change:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=first.snapshot.snapshot_id,
                idempotency_key=IdempotencyKey("publish:schema-change"),
                batch=batch_b,
                admission=admission_b,
                application_acceptance=StructureApplicationAcceptance.pass_for(
                    batch_b,
                    acceptance_ref="application:schema-change",
                    report_digest=digest_of({"report": "schema-change"}),
                ),
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            schema_change.exception.details["reason_code"],
            "SCHEMA_EVOLUTION_UNSUPPORTED",
        )

        with self.assertRaises(DomainError) as immutable:
            self.registry.register(
                definition=StructureSchemaDefinition.create(
                    schema_ref=self.generic_schema_ref,
                    schema_digest=digest_of({"schema": "wrong"}),
                ),
                idempotency_key=IdempotencyKey("register-generic-wrong-digest"),
                proposal_ref="proposal:test-generic-structure@1",
                review_ref="review:test-generic-structure@1",
                registered_by="test",
                reason="immutability fault",
            )
        self.assertEqual(
            immutable.exception.details["reason_code"],
            "SCHEMA_REGISTRATION_IMMUTABILITY_VIOLATION",
        )

        evidence_c = self.evidence("c")
        entity_c = self.module(evidence_c, "c" * 40, "alpha")
        batch_c = self.batch(
            evidence=evidence_c,
            entities=(entity_c,),
            relations=(),
            coverage=self.coverage(root_a, evidence_c, "c" * 40, (entity_c,)),
            mode=PublicationMode.REPLACE_COVERAGE,
        )
        admission_c = self.accept(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=first.snapshot.snapshot_id,
            candidate_ref="candidate:registry-tamper",
            candidate_digest=digest_of({"candidate": "registry-tamper"}),
            batch=batch_c,
            provenance_digest=digest_of({"provenance": "registry-tamper"}),
            verifier_ref="structure-admission-verifier:test@1",
            idempotency_key=IdempotencyKey("admission:registry-tamper"),
            caller_ref="test",
            classification="INTERNAL",
        )
        with self.database.transaction() as connection:
            connection.execute(
                """UPDATE knw_structure_schema_registrations
                   SET registration_digest = ? WHERE schema_ref = ?""",
                (digest_of({"tampered": True}).value, self.generic_schema_ref),
            )
        with self.assertRaises(DomainError) as tampered_registry:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=first.snapshot.snapshot_id,
                idempotency_key=IdempotencyKey("publish:registry-tamper"),
                batch=batch_c,
                admission=admission_c,
                application_acceptance=StructureApplicationAcceptance.pass_for(
                    batch_c,
                    acceptance_ref="application:registry-tamper",
                    report_digest=digest_of({"report": "registry-tamper"}),
                ),
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            tampered_registry.exception.details["reason_code"],
            "SCHEMA_REGISTRATION_DIGEST_MISMATCH",
        )
        self.assertEqual(
            self.service.current_snapshot(self.scope.scope_id), first.snapshot
        )
        self.assertEqual(
            self.service.get_snapshot(first.snapshot.snapshot_id), first.snapshot
        )

    def test_schema_dependency_and_system_scope_eligibility_fail_closed(self) -> None:
        with self.assertRaises(DomainError) as same_authority:
            self.registry.register(
                definition=StructureSchemaDefinition.create(
                    schema_ref="UNREVIEWED-STRUCTURE@1",
                    schema_digest=digest_of({"schema": "unreviewed"}),
                ),
                idempotency_key=IdempotencyKey("register-unreviewed-schema"),
                proposal_ref="schema-authority:same",
                review_ref="schema-authority:same",
                registered_by="test",
                reason="identity separation fault",
            )
        self.assertEqual(
            same_authority.exception.details["reason_code"],
            "SCHEMA_AUTHORITY_IDENTITIES_NOT_SEPARATE",
        )
        missing_dependency = StructureSchemaDependency(
            schema_ref="MISSING-STRUCTURE@1",
            schema_digest=digest_of({"schema": "missing"}),
        )
        with self.assertRaises(DomainError) as missing:
            self.registry.register(
                definition=StructureSchemaDefinition.create(
                    schema_ref="DEPENDENT-STRUCTURE@1",
                    schema_digest=digest_of({"schema": "dependent"}),
                    dependencies=(missing_dependency,),
                ),
                idempotency_key=IdempotencyKey("register-missing-dependency"),
                proposal_ref="proposal:test-dependent-structure@1",
                review_ref="review:test-dependent-structure@1",
                registered_by="test",
                reason="dependency closure fault",
            )
        self.assertEqual(
            missing.exception.details["reason_code"], "SCHEMA_NOT_REGISTERED"
        )

        shared_scope = self.scopes.create_scope(
            scope_type=ScopeType.SHARED_COMPONENT,
            metadata={"display_name": "Shared"},
            idempotency_key=IdempotencyKey("shared-structure-scope"),
            actor="test",
            reason="scope eligibility fault",
            correlation_ref=CorrelationRef("shared-structure"),
        )
        batch, _, _, _ = self.maven_batch("a", ("common",))
        with self.assertRaises(DomainError) as wrong_scope:
            self.accept(
                scope_id=shared_scope.scope_id,
                expected_scope_revision=shared_scope.definition_revision,
                expected_current_snapshot_id=None,
                candidate_ref="candidate:shared",
                candidate_digest=digest_of({"candidate": "shared"}),
                batch=batch,
                provenance_digest=digest_of({"provenance": "shared"}),
                verifier_ref="structure-admission-verifier:test@1",
                idempotency_key=IdempotencyKey("admission:shared"),
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(wrong_scope.exception.code, ErrorCode.SCOPE_ASSERTION_INVALID)
        self.assertIsNone(self.service.current_snapshot(shared_scope.scope_id))

    def test_application_report_scope_and_retirement_are_authority_gates(self) -> None:
        batch, _, _, _ = self.maven_batch("a", ("common",))
        admission = self.accept(
            scope_id=self.scope.scope_id,
            expected_scope_revision=self.scope.definition_revision,
            expected_current_snapshot_id=None,
            candidate_ref="candidate:application-gates",
            candidate_digest=digest_of({"candidate": "application-gates"}),
            batch=batch,
            provenance_digest=digest_of({"provenance": "application-gates"}),
            verifier_ref="structure-admission-verifier:test@1",
            idempotency_key=IdempotencyKey("admission:application-gates"),
            caller_ref="test",
            classification="INTERNAL",
        )
        acceptance = StructureApplicationAcceptance.pass_for(
            batch,
            acceptance_ref="application:tamper",
            report_digest=digest_of({"report": "valid"}),
        )
        tampered = replace(
            acceptance, report_digest=digest_of({"report": "tampered"})
        )
        with self.assertRaises(DomainError) as report_error:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=None,
                idempotency_key=IdempotencyKey("tampered-report"),
                batch=batch,
                admission=admission,
                application_acceptance=tampered,
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            report_error.exception.details["reason_code"],
            "APPLICATION_ACCEPTANCE_DIGEST_MISMATCH",
        )
        self.assertIsNone(self.service.current_snapshot(self.scope.scope_id))
        self.assertIsNone(self.registry.get_adoption(self.scope.scope_id))

        failed = StructureApplicationAcceptance.decide(
            acceptance_ref="application:failed",
            decision=ApplicationAcceptanceDecision.FAIL,
            batch_digest=structure_batch_digest(batch),
            report_digest=digest_of({"report": "failed"}),
        )
        with self.assertRaises(DomainError):
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=None,
                idempotency_key=IdempotencyKey("failed-acceptance"),
                batch=batch,
                admission=admission,
                application_acceptance=failed,
                caller_ref="test",
                classification="INTERNAL",
            )

        revised = self.scopes.update_scope_metadata(
            scope_id=self.scope.scope_id,
            expected_revision=self.scope.definition_revision,
            metadata={"display_name": "revised"},
            idempotency_key=IdempotencyKey("revise-scope"),
            actor="test",
            reason="stale assertion test",
            correlation_ref=CorrelationRef("revise-structure-scope"),
        )
        with self.assertRaises(DomainError) as stale:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=self.scope.definition_revision,
                expected_current_snapshot_id=None,
                idempotency_key=IdempotencyKey("stale-scope"),
                batch=batch,
                admission=admission,
                application_acceptance=acceptance,
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(stale.exception.code, ErrorCode.REVISION_CONFLICT)

        retired = self.scopes.retire_scope(
            scope_id=self.scope.scope_id,
            expected_revision=revised.definition_revision,
            idempotency_key=IdempotencyKey("retire-scope"),
            actor="test",
            reason="retired assertion test",
            correlation_ref=CorrelationRef("retire-structure-scope"),
        )
        with self.assertRaises(DomainError) as retired_error:
            self.service.publish(
                scope_id=self.scope.scope_id,
                expected_scope_revision=retired.definition_revision,
                expected_current_snapshot_id=None,
                idempotency_key=IdempotencyKey("retired-scope"),
                batch=batch,
                admission=admission,
                application_acceptance=acceptance,
                caller_ref="test",
                classification="INTERNAL",
            )
        self.assertEqual(
            retired_error.exception.code, ErrorCode.SCOPE_ASSERTION_INVALID
        )
        self.assertIsNone(self.service.current_snapshot(self.scope.scope_id))


if __name__ == "__main__":
    unittest.main()
